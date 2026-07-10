"""
==============================================================================
 ETAPA 2 DEL PIPELINE: ANALISIS EXPLORATORIO DE DATOS (EDA)
==============================================================================

Explora el catalogo de sismos reportados del IGP (data/sismos_igp.csv):

    - estadisticas descriptivas y valores faltantes
    - distribucion de magnitudes y profundidades
    - evolucion temporal (sismos por anio)
    - departamentos con mas sismos reportados
    - mapa de dispersion lat/lon coloreado por magnitud

Las figuras se guardan en web/static/eda/ para mostrarlas en el README
y en la presentacion.

Ejecucion:
    python eda.py
==============================================================================
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(CARPETA, "data", "sismos_igp.csv")
SALIDA = os.path.join(CARPETA, "web", "static", "eda")

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3})


def cargar():
    df = pd.read_csv(CSV, parse_dates=["fecha_hora"])
    return df


def resumen_texto(df):
    print("=" * 70)
    print(f"Filas: {len(df)}  |  Columnas: {len(df.columns)}")
    print(f"Rango temporal: {df['fecha_hora'].min()}  a  {df['fecha_hora'].max()}")
    print("\n--- Estadisticas descriptivas (numericas) ---")
    print(df[["magnitud", "profundidad", "latitud", "longitud"]].describe().round(2))
    print("\n--- Valores faltantes ---")
    faltantes = df.isna().sum()
    print(faltantes[faltantes > 0])
    print("\nNota: 'departamento' es nulo cuando 'referencia' usa el formato")
    print("antiguo (2012-2015) sin sufijo ' - Departamento'.")
    print("\n--- Correlacion magnitud vs profundidad ---")
    print(df[["magnitud", "profundidad"]].corr().round(3))
    print("=" * 70)


def graficas(df):
    os.makedirs(SALIDA, exist_ok=True)

    # 1. distribucion de magnitudes -----------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["magnitud"], bins=30, color="#4C72B0", edgecolor="white")
    ax.set(xlabel="Magnitud (M)", ylabel="Frecuencia",
           title="Distribucion de magnitudes (IGP, sismos reportados)")
    fig.tight_layout(); fig.savefig(f"{SALIDA}/magnitudes.png"); plt.close(fig)

    # 2. distribucion de profundidades --------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["profundidad"], bins=40, color="#DD8452", edgecolor="white")
    ax.set(xlabel="Profundidad (km)", ylabel="Frecuencia",
           title="Distribucion de profundidades")
    fig.tight_layout(); fig.savefig(f"{SALIDA}/profundidades.png"); plt.close(fig)

    # 3. sismos por anio ------------------------------------------------------
    por_anio = df.groupby("anio").size()
    fig, ax = plt.subplots(figsize=(8, 4))
    por_anio.plot(kind="bar", ax=ax, color="#55A868")
    ax.set(xlabel="Anio", ylabel="Sismos reportados",
           title="Sismos reportados por anio")
    fig.tight_layout(); fig.savefig(f"{SALIDA}/por_anio.png"); plt.close(fig)

    # 4. top departamentos ----------------------------------------------------
    top = df["departamento"].value_counts().head(10).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    top.plot(kind="barh", ax=ax, color="#C44E52")
    ax.set(xlabel="Sismos reportados", title="Top 10 departamentos")
    fig.tight_layout(); fig.savefig(f"{SALIDA}/departamentos.png"); plt.close(fig)

    # 5. mapa lat/lon coloreado por magnitud ----------------------------------
    fig, ax = plt.subplots(figsize=(6, 7))
    sc = ax.scatter(df["longitud"], df["latitud"], c=df["magnitud"],
                    s=8, cmap="YlOrRd", alpha=0.6)
    fig.colorbar(sc, ax=ax, label="Magnitud")
    ax.set(xlabel="Longitud", ylabel="Latitud",
           title="Epicentros de sismos en Peru (2012-presente)")
    fig.tight_layout(); fig.savefig(f"{SALIDA}/mapa.png"); plt.close(fig)

    print(f"5 figuras guardadas en {SALIDA}")


if __name__ == "__main__":
    df = cargar()
    resumen_texto(df)
    graficas(df)
