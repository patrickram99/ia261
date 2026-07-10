"""
==============================================================================
 HERRAMIENTAS DEL AGENTE (function calling)
==============================================================================

Tres herramientas que Gemini puede invocar sobre el catalogo sismico:

    1. obtener_esquema()          -> columnas, tipos, rangos y ejemplos
    2. consultar_datos(expresion) -> evalua una expresion de pandas sobre df
                                     en un entorno restringido
    3. graficar(...)              -> genera un PNG con matplotlib y devuelve
                                     su ruta para mostrarlo en el chat

Cada herramienta devuelve SIEMPRE un dict serializable a JSON; los errores
se devuelven como {"error": "..."} para que el agente pueda autocorregirse.
==============================================================================
"""

import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(CARPETA, "data", "sismos_igp.csv")
CARPETA_CHARTS = os.path.join(CARPETA, "web", "static", "charts")

MAX_FILAS = 30          # tope de filas devueltas al modelo
MAX_CHARS = 4000        # tope de caracteres del resultado

_df = None
_contador_graficos = 0


def get_df():
    """Carga el dataset una sola vez (cache de modulo)."""
    global _df
    if _df is None:
        _df = pd.read_csv(CSV, parse_dates=["fecha_hora"])
    return _df


# ---------------------------------------------------------------------------
#  1. OBTENER ESQUEMA
# ---------------------------------------------------------------------------
def obtener_esquema():
    """Describe el dataset: columnas, tipos, rangos y filas de ejemplo."""
    df = get_df()
    return {
        "filas": len(df),
        "columnas": {c: str(t) for c, t in df.dtypes.items()},
        "rango_fechas": [str(df["fecha_hora"].min()), str(df["fecha_hora"].max())],
        "rango_magnitud": [float(df["magnitud"].min()), float(df["magnitud"].max())],
        "rango_profundidad_km": [float(df["profundidad"].min()),
                                 float(df["profundidad"].max())],
        "departamentos": sorted(df["departamento"].dropna().unique().tolist()),
        "valores_tipo_profundidad": ["superficial", "intermedio", "profundo"],
        "ejemplo": df.tail(2).astype(str).to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
#  2. CONSULTAR DATOS (expresion pandas en entorno restringido)
# ---------------------------------------------------------------------------
_PROHIBIDO = re.compile(
    r"(__|\bimport\b|\bopen\b|\beval\b|\bexec\b|\bos\b|\bsys\b|"
    r"\bto_csv\b|\bto_pickle\b|\bread_\w+\b|\bquit\b|\bexit\b)"
)


def consultar_datos(expresion):
    """Evalua UNA expresion de pandas sobre `df` y devuelve el resultado."""
    if _PROHIBIDO.search(expresion):
        return {"error": "Expresion no permitida: solo operaciones de "
                         "lectura sobre df con pd/np."}
    df = get_df()
    # builtins seguros de solo lectura; todo lo demas queda bloqueado
    seguros = {n: __builtins__[n] if isinstance(__builtins__, dict)
               else getattr(__builtins__, n)
               for n in ("len", "round", "min", "max", "sum", "abs",
                         "sorted", "str", "int", "float", "range", "list",
                         "dict", "set", "tuple", "zip", "enumerate")}
    entorno = {"df": df, "pd": pd, "np": np, "__builtins__": seguros}
    try:
        resultado = eval(expresion, entorno)  # noqa: S307 - entorno restringido
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

    # --- serializar el resultado de forma compacta -------------------------
    if isinstance(resultado, pd.DataFrame):
        if len(resultado) > MAX_FILAS:
            texto = (resultado.head(MAX_FILAS).to_string()
                     + f"\n... ({len(resultado)} filas en total, se muestran {MAX_FILAS})")
        else:
            texto = resultado.to_string()
    elif isinstance(resultado, pd.Series):
        if len(resultado) > MAX_FILAS:
            texto = (resultado.head(MAX_FILAS).to_string()
                     + f"\n... ({len(resultado)} valores en total)")
        else:
            texto = resultado.to_string()
    else:
        texto = str(resultado)

    return {"resultado": texto[:MAX_CHARS]}


# ---------------------------------------------------------------------------
#  3. GRAFICAR
# ---------------------------------------------------------------------------
def graficar(tipo, columna_x, columna_y=None, agregacion="count",
             filtro=None, titulo=None):
    """
    Genera un grafico PNG y devuelve su ruta relativa (para la web).

    tipo        : 'barras' | 'lineas' | 'histograma' | 'dispersion'
    columna_x   : columna del eje X (o la unica columna en histograma)
    columna_y   : columna a agregar (opcional; si falta se cuentan filas)
    agregacion  : 'count' | 'sum' | 'mean' | 'max' | 'min'
    filtro      : expresion para df.query(), ej. "anio == 2024" (opcional)
    titulo      : titulo del grafico (opcional)
    """
    global _contador_graficos
    df = get_df()

    try:
        if filtro:
            df = df.query(filtro)
        if df.empty:
            return {"error": "El filtro no dejo ninguna fila."}
        if columna_x not in df.columns:
            return {"error": f"Columna inexistente: {columna_x}"}
        if columna_y and columna_y not in df.columns:
            return {"error": f"Columna inexistente: {columna_y}"}

        fig, ax = plt.subplots(figsize=(7.5, 4.2))

        if tipo == "histograma":
            ax.hist(df[columna_x].dropna(), bins=30,
                    color="#4C72B0", edgecolor="white")
            ax.set_ylabel("Frecuencia")
        elif tipo == "dispersion":
            if not columna_y:
                return {"error": "dispersion requiere columna_y"}
            ax.scatter(df[columna_x], df[columna_y], s=10, alpha=0.5,
                       color="#4C72B0")
            ax.set_ylabel(columna_y)
        else:  # barras o lineas sobre datos agregados
            if columna_y:
                serie = df.groupby(columna_x)[columna_y].agg(agregacion)
            else:
                serie = df.groupby(columna_x).size()
            if pd.api.types.is_numeric_dtype(df[columna_x]):
                serie = serie.sort_index()
            else:
                serie = serie.sort_values(ascending=False).head(15)
            estilo = "bar" if tipo == "barras" else "line"
            serie.plot(kind=estilo, ax=ax, color="#4C72B0")
            ax.set_ylabel(f"{agregacion}({columna_y})" if columna_y else "conteo")

        ax.set_xlabel(columna_x)
        ax.set_title(titulo or f"{tipo} de {columna_x}")
        ax.grid(alpha=0.3)
        fig.tight_layout()

        os.makedirs(CARPETA_CHARTS, exist_ok=True)
        _contador_graficos += 1
        nombre = f"chart_{os.getpid()}_{_contador_graficos}.png"
        fig.savefig(os.path.join(CARPETA_CHARTS, nombre))
        plt.close(fig)

        return {"ok": True,
                "ruta": f"/static/charts/{nombre}",
                "descripcion": f"Grafico '{titulo or tipo}' generado."}
    except Exception as e:
        plt.close("all")
        return {"error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
#  Declaraciones para Gemini (function calling) y despachador
# ---------------------------------------------------------------------------
DECLARACIONES = [
    {
        "name": "obtener_esquema",
        "description": ("Devuelve el esquema del dataset de sismos: columnas, "
                        "tipos, rangos, lista de departamentos y filas de "
                        "ejemplo. Usar primero si hay dudas sobre los datos."),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "consultar_datos",
        "description": ("Evalua UNA expresion de pandas sobre el DataFrame "
                        "`df` (con pd y np disponibles) y devuelve el "
                        "resultado como texto. Solo lectura."),
        "parameters": {
            "type": "object",
            "properties": {
                "expresion": {
                    "type": "string",
                    "description": ("Expresion de pandas, ej.: "
                                    "df[df['anio']==2024]['magnitud'].max()"),
                }
            },
            "required": ["expresion"],
        },
    },
    {
        "name": "graficar",
        "description": ("Genera un grafico PNG (barras, lineas, histograma o "
                        "dispersion) y devuelve su ruta para mostrarlo al "
                        "usuario."),
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string",
                         "enum": ["barras", "lineas", "histograma", "dispersion"]},
                "columna_x": {"type": "string"},
                "columna_y": {"type": "string"},
                "agregacion": {"type": "string",
                               "enum": ["count", "sum", "mean", "max", "min"]},
                "filtro": {"type": "string",
                           "description": "expresion df.query(), ej. \"anio == 2024\""},
                "titulo": {"type": "string"},
            },
            "required": ["tipo", "columna_x"],
        },
    },
]

FUNCIONES = {
    "obtener_esquema": obtener_esquema,
    "consultar_datos": consultar_datos,
    "graficar": graficar,
}


def ejecutar(nombre, argumentos):
    """Despacha una llamada de funcion del modelo a la herramienta real."""
    if nombre not in FUNCIONES:
        return {"error": f"Herramienta desconocida: {nombre}"}
    try:
        return FUNCIONES[nombre](**(argumentos or {}))
    except TypeError as e:
        return {"error": f"Argumentos invalidos: {e}"}
