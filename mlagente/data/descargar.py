"""
==============================================================================
 ETAPA 1 y 3 DEL PIPELINE: OBTENCION Y PREPROCESAMIENTO DE DATOS
==============================================================================

Descarga el catalogo de sismos reportados por el Instituto Geofisico del
Peru (IGP) desde su API publica y lo consolida en un unico CSV limpio.

Fuente     : API publica del IGP - https://ultimosismo.igp.gob.pe
             endpoint: /api/ultimo-sismo/ajaxb/<anio>
Cobertura  : sismos reportados (percibidos por la poblacion) 2012 - presente
Licencia   : datos publicos del Estado Peruano (IGP)

Preprocesamiento aplicado:
    - combina fecha_local + hora_local en un solo datetime
    - convierte latitud/longitud/magnitud/profundidad a numerico
    - extrae el departamento desde el campo "referencia"
    - deriva anio, mes y la clasificacion de profundidad usada en
      sismologia (superficial < 60 km, intermedio 60-300 km, profundo > 300)
    - elimina registros sin magnitud o sin coordenadas

Ejecucion:
    python data/descargar.py
    -> genera data/sismos_igp.csv
==============================================================================
"""

import difflib
import os
import re
import sys
import time
import unicodedata

import pandas as pd
import requests

API = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{anio}"
ANIO_INICIO = 2012          # primer anio con datos en la API
CARPETA = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(CARPETA, "sismos_igp.csv")


def descargar_anio(anio):
    """Descarga la lista de sismos de un anio; [] si el anio no existe."""
    r = requests.get(API.format(anio=anio), timeout=30)
    r.raise_for_status()
    datos = r.json()
    if not isinstance(datos, list):        # {"error": "..."} para anios sin datos
        return []
    return datos


# Los 24 departamentos del Peru + Callao: se usa como lista canonica para
# normalizar el texto libre de "referencia" (tiene typos, puntos y tildes
# inconsistentes: "Arequiupa", "Lima.", "Apurimac"/"Apurímac", etc.)
DEPARTAMENTOS = [
    "Amazonas", "Ancash", "Apurimac", "Arequipa", "Ayacucho", "Cajamarca",
    "Callao", "Cusco", "Huancavelica", "Huanuco", "Ica", "Junin",
    "La Libertad", "Lambayeque", "Lima", "Loreto", "Madre De Dios",
    "Moquegua", "Pasco", "Piura", "Puno", "San Martin", "Tacna", "Tumbes",
    "Ucayali",
]


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def extraer_departamento(referencia):
    """
    El campo referencia tiene la forma:
        "81 km al SO de Huarmey, Huarmey - Ancash"
    El departamento es lo que va despues del ultimo "-" (a veces tambien
    "Provincia, Departamento"). El texto libre trae typos y tildes
    inconsistentes, asi que se normaliza contra la lista canonica con
    emparejamiento aproximado (difflib); lo que no calza se descarta.
    """
    if not isinstance(referencia, str) or "-" not in referencia:
        return None
    depto = referencia.rsplit("-", 1)[-1].strip()
    if "," in depto:                       # "... - Provincia, Departamento"
        depto = depto.rsplit(",", 1)[-1].strip()
    depto = _sin_tildes(depto).rstrip(".").strip().title()
    if not depto or len(depto) > 30 or re.search(r"\d", depto):
        return None
    # residuos de direccion ("So De Pinchollo") no son departamentos
    if re.match(r"^(N|S|E|O|Ne|No|Se|So|Este|Oeste|Norte|Sur) De ", depto):
        return None
    match = difflib.get_close_matches(depto, DEPARTAMENTOS, n=1, cutoff=0.8)
    return match[0] if match else None


def limpiar(df):
    """Aplica el preprocesamiento descrito en la cabecera."""
    # --- tipos numericos -------------------------------------------------
    for col in ("latitud", "longitud", "magnitud", "profundidad"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- fecha y hora locales -> datetime --------------------------------
    fecha = pd.to_datetime(df["fecha_local"], errors="coerce", utc=True)
    hora = pd.to_datetime(df["hora_local"], errors="coerce", utc=True)
    df["fecha_hora"] = fecha.dt.normalize() + (hora - hora.dt.normalize())
    df["fecha_hora"] = df["fecha_hora"].dt.tz_localize(None)

    # --- columnas derivadas ----------------------------------------------
    df["anio"] = df["fecha_hora"].dt.year
    df["mes"] = df["fecha_hora"].dt.month
    df["hora"] = df["fecha_hora"].dt.hour
    df["departamento"] = df["referencia"].apply(extraer_departamento)
    df["tipo_profundidad"] = pd.cut(
        df["profundidad"],
        bins=[-1, 60, 300, 10_000],
        labels=["superficial", "intermedio", "profundo"],
    )

    # --- filtrado de registros invalidos ----------------------------------
    antes = len(df)
    df = df.dropna(subset=["magnitud", "latitud", "longitud", "fecha_hora"])
    print(f"  registros eliminados por nulos criticos: {antes - len(df)}")

    # --- outliers de coordenadas -------------------------------------------
    # Algunos registros tienen lat/lon intercambiadas o erroneas. Se filtra
    # con una caja generosa alrededor de Peru (incluye sismos fronterizos
    # y oceanicos cercanos).
    antes = len(df)
    caja = df["latitud"].between(-25, 3) & df["longitud"].between(-85, -65)
    df = df[caja]
    print(f"  registros eliminados por coordenadas fuera de rango: {antes - len(df)}")

    columnas = [
        "codigo", "fecha_hora", "anio", "mes", "hora",
        "latitud", "longitud", "profundidad", "tipo_profundidad",
        "magnitud", "referencia", "departamento", "intensidad",
    ]
    return df[columnas].sort_values("fecha_hora").reset_index(drop=True)


def main():
    anio_final = pd.Timestamp.now().year
    registros = []
    print(f"Descargando sismos del IGP ({ANIO_INICIO}-{anio_final})...")
    for anio in range(ANIO_INICIO, anio_final + 1):
        try:
            datos = descargar_anio(anio)
        except requests.RequestException as e:
            print(f"  {anio}: ERROR {e} (se omite)")
            continue
        print(f"  {anio}: {len(datos)} sismos")
        registros.extend(datos)
        time.sleep(0.3)                    # cortesia con el servidor

    if not registros:
        sys.exit("No se descargo ningun registro; revisar conexion/API.")

    df = pd.DataFrame(registros)
    df = limpiar(df)
    df.to_csv(SALIDA, index=False)
    print(f"\nOK -> {SALIDA}")
    print(f"   {len(df)} filas x {len(df.columns)} columnas")
    print(f"   rango: {df['fecha_hora'].min()} a {df['fecha_hora'].max()}")


if __name__ == "__main__":
    main()
