"""
==============================================================================
 GENERADOR DEL SET DE EVALUACION
==============================================================================

Construye eval/preguntas.json: ~30 preguntas en lenguaje natural cuya
respuesta esperada se CALCULA desde el propio CSV (ground truth), de modo
que el set siempre este sincronizado con los datos descargados.

Tipos de pregunta:
    - "numero"  : la respuesta correcta es una cifra (con tolerancia)
    - "texto"   : la respuesta debe contener una cadena (ej. un departamento)
    - "grafico" : se considera exito si el agente genero un grafico

Ejecucion:
    python eval/generar_preguntas.py
==============================================================================
"""

import json
import os

import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(os.path.dirname(CARPETA), "data", "sismos_igp.csv")
SALIDA = os.path.join(CARPETA, "preguntas.json")


def main():
    df = pd.read_csv(CSV, parse_dates=["fecha_hora"])
    ultimo_anio_completo = int(df["anio"].max()) - 1   # el anio en curso esta incompleto

    def num(pregunta, valor, tolerancia=0.0):
        return {"tipo": "numero", "pregunta": pregunta,
                "esperado": round(float(valor), 4), "tolerancia": tolerancia}

    def txt(pregunta, valor):
        return {"tipo": "texto", "pregunta": pregunta, "esperado": str(valor)}

    def graf(pregunta):
        return {"tipo": "grafico", "pregunta": pregunta, "esperado": None}

    por_anio = df.groupby("anio").size()
    por_depto = df.groupby("departamento").size().sort_values(ascending=False)
    anios_completos = por_anio.drop(index=int(df["anio"].max()))

    preguntas = [
        # --- conteos y agregados globales ---------------------------------
        num("¿Cuántos sismos hay registrados en total en el dataset?", len(df)),
        num("¿Cuál es la magnitud máxima registrada en todo el catálogo?",
            df["magnitud"].max()),
        num("¿Cuál es la magnitud mínima registrada?", df["magnitud"].min()),
        num("¿Cuál es la magnitud promedio de todos los sismos? Responde con 2 decimales.",
            df["magnitud"].mean(), 0.05),
        num("¿Cuál es la profundidad máxima registrada en kilómetros?",
            df["profundidad"].max()),
        num("¿Cuál es la profundidad promedio en kilómetros de todos los sismos? Responde con 1 decimal.",
            df["profundidad"].mean(), 0.5),
        num("¿Cuántos sismos tienen magnitud mayor o igual a 7.0?",
            (df["magnitud"] >= 7).sum()),
        num("¿Cuántos sismos de tipo superficial hay?",
            (df["tipo_profundidad"] == "superficial").sum()),
        num("¿Cuántos sismos de tipo profundo (más de 300 km) hay?",
            (df["tipo_profundidad"] == "profundo").sum()),
        num("¿Cuántos departamentos distintos aparecen en el dataset?",
            df["departamento"].nunique()),

        # --- filtros temporales --------------------------------------------
        num(f"¿Cuántos sismos hubo en el año {ultimo_anio_completo}?",
            por_anio[ultimo_anio_completo]),
        num("¿Cuántos sismos hubo en el año 2020?", por_anio[2020]),
        num("¿Cuántos sismos hubo entre 2020 y 2022, inclusive?",
            df["anio"].between(2020, 2022).sum()),
        num("Sin contar el año actual (aún incompleto), ¿en qué año se reportaron más sismos?",
            anios_completos.idxmax()),
        num("Sin contar el año actual, ¿en qué año se reportaron menos sismos?",
            anios_completos.idxmin()),
        num(f"¿Cuál fue la magnitud máxima en el año {ultimo_anio_completo}?",
            df.loc[df["anio"] == ultimo_anio_completo, "magnitud"].max()),
        num("¿A qué hora del día (0-23) se han reportado más sismos?",
            df.groupby("hora").size().idxmax()),

        # --- por departamento ----------------------------------------------
        txt("¿Qué departamento tiene la mayor cantidad de sismos reportados?",
            por_depto.index[0]),
        txt("¿Cuál es el segundo departamento con más sismos reportados?",
            por_depto.index[1]),
        num("¿Cuántos sismos se han reportado en el departamento de Arequipa?",
            por_depto["Arequipa"]),
        num("¿Cuántos sismos se han reportado en el departamento de Lima?",
            por_depto["Lima"]),
        num("¿Cuál es la profundidad promedio de los sismos en Tacna? Responde con 1 decimal.",
            df.loc[df["departamento"] == "Tacna", "profundidad"].mean(), 1.0),
        num("¿Cuál es la magnitud promedio de los sismos en Ica? Responde con 2 decimales.",
            df.loc[df["departamento"] == "Ica", "magnitud"].mean(), 0.05),
        num(f"¿Cuál fue la magnitud máxima en Arequipa durante {ultimo_anio_completo}?",
            df.loc[(df["departamento"] == "Arequipa")
                   & (df["anio"] == ultimo_anio_completo), "magnitud"].max()),
        # solo entre filas con departamento conocido (el max global de 2019
        # usa el formato antiguo de referencia, sin departamento)
        txt("Entre los sismos con departamento identificado, ¿en qué departamento ocurrió el de mayor magnitud?",
            df.dropna(subset=["departamento"])
              .sort_values("magnitud").iloc[-1]["departamento"]),

        # --- combinadas ------------------------------------------------------
        num("De los sismos con magnitud mayor o igual a 6, ¿cuál es su profundidad promedio en km? Responde con 1 decimal.",
            df.loc[df["magnitud"] >= 6, "profundidad"].mean(), 1.0),
        num("¿Cuántos sismos superficiales hubo en Lima?",
            ((df["departamento"] == "Lima")
             & (df["tipo_profundidad"] == "superficial")).sum()),

        # --- graficos ---------------------------------------------------------
        graf("Muéstrame un gráfico de barras con la cantidad de sismos por año."),
        graf("Genera un histograma de las magnitudes de los sismos."),
        graf("Grafica los 10 departamentos con más sismos reportados."),
        graf("Muéstrame un gráfico de dispersión entre profundidad y magnitud."),
    ]

    for i, p in enumerate(preguntas, 1):
        p["id"] = i

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(preguntas, f, ensure_ascii=False, indent=2)
    print(f"OK -> {SALIDA} ({len(preguntas)} preguntas)")


if __name__ == "__main__":
    main()
