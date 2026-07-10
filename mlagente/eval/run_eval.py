"""
==============================================================================
 ETAPA 5 DEL PIPELINE: EVALUACION - EXPERIMENTOS DEL AGENTE
==============================================================================

Corre el agente sobre el set de preguntas (eval/preguntas.json) bajo
distintas configuraciones y mide las metricas de la rubrica:

    - tasa de exito (respuesta correcta vs ground truth)
    - pasos promedio del loop ReAct
    - llamadas a herramientas promedio
    - errores de herramienta
    - tiempo promedio por pregunta

Experimentos:
    exp1  ¿Que modelo conviene?        3 modelos, mismo prompt
    exp2  ¿Aportan las herramientas?   agente vs LLM solo (con/sin resumen)
    exp3  ¿Importa el prompt?          detallado vs sin_formato vs minimo

Ejecucion:
    python eval/run_eval.py --exp exp1            # un experimento
    python eval/run_eval.py --exp all             # los tres
    python eval/run_eval.py --exp exp1 --quick    # solo 8 preguntas (humo)

Genera en eval/resultados/: un JSON detallado por configuracion,
resumen_<exp>.csv y grafico_<exp>.png (tabla y grafico comparativos).
==============================================================================
"""

import argparse
import json
import os
import re
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agente.agente import AgenteSismos  # noqa: E402

CARPETA = os.path.dirname(os.path.abspath(__file__))
RESULTADOS = os.path.join(CARPETA, "resultados")

# --------------------------------------------------------------------------
#  Configuraciones de cada experimento
# --------------------------------------------------------------------------
EXPERIMENTOS = {
    "exp1": {
        "titulo": "Experimento 1: comparacion de modelos",
        "configs": {
            "flash-lite": {"modelo": "gemini-3.1-flash-lite"},
            "flash-preview": {"modelo": "gemini-3-flash-preview"},
            "3.5-flash": {"modelo": "gemini-3.5-flash"},
        },
    },
    "exp2": {
        "titulo": "Experimento 2: ¿aportan las herramientas?",
        "configs": {
            "con-herramientas": {},
            "llm-con-resumen": {"usar_herramientas": False},
            "llm-sin-resumen": {"usar_herramientas": False,
                                "incluir_resumen": False},
        },
    },
    "exp3": {
        "titulo": "Experimento 3: ¿importa el prompt de sistema?",
        "configs": {
            "detallado": {"prompt": "detallado"},
            "sin-formato": {"prompt": "sin_formato"},
            "minimo": {"prompt": "minimo"},
        },
    },
}

PAUSA_ENTRE_PREGUNTAS = 2   # seg; respeta el limite por minuto del tier gratis
MAX_ERRORES_API_SEGUIDOS = 5    # tras esto se declara la config "no disponible"


# --------------------------------------------------------------------------
#  Verificacion de respuestas contra el ground truth
# --------------------------------------------------------------------------
def extraer_numeros(texto):
    """Extrae numeros del texto normalizando '1,428' (miles) y '4,12' (coma decimal)."""
    numeros = []
    for m in re.finditer(r"-?\d[\d.,]*", texto):
        s = m.group()
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):      # 1,428 o 1,428.5
            s = s.replace(",", "")
        elif re.fullmatch(r"-?\d+,\d{1,2}", s):                  # 4,12 decimal
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
        s = s.rstrip(".")
        try:
            numeros.append(float(s))
        except ValueError:
            pass
    return numeros


def es_correcta(item, respuesta, metricas):
    if item["tipo"] == "grafico":
        return len(metricas.get("graficos", [])) > 0
    if item["tipo"] == "texto":
        return item["esperado"].lower() in respuesta.lower()
    # numero: alguna cifra de la respuesta dentro de la tolerancia
    tol = max(item.get("tolerancia", 0.0), abs(item["esperado"]) * 1e-9)
    return any(abs(n - item["esperado"]) <= tol
               for n in extraer_numeros(respuesta))


# --------------------------------------------------------------------------
#  Ejecucion de una configuracion sobre todas las preguntas
# --------------------------------------------------------------------------
def correr_config(nombre, kwargs, preguntas):
    print(f"\n--- configuracion: {nombre}  {kwargs} ---")
    agente = AgenteSismos(**kwargs)
    filas = []
    errores_seguidos = 0
    for item in preguntas:
        # fail-fast: si el modelo esta caido (429/503 sostenido) no tiene
        # sentido seguir reintentando pregunta por pregunta
        if errores_seguidos >= MAX_ERRORES_API_SEGUIDOS:
            filas.append({
                "id": item["id"], "tipo": item["tipo"],
                "pregunta": item["pregunta"], "esperado": item["esperado"],
                "respuesta": "", "correcta": False, "pasos": 0,
                "n_llamadas": 0, "errores_herramienta": 0, "tiempo_s": 0.0,
                "error_api": "modelo no disponible (fail-fast)",
            })
            continue
        t0 = time.time()
        try:
            salida = agente.preguntar(item["pregunta"])   # sin historial: episodios independientes
            respuesta = salida["respuesta"]
            met = salida["metricas"]
            correcta = es_correcta(item, respuesta, met)
            error_api = None
            errores_seguidos = 0
        except Exception as e:
            errores_seguidos += 1
            respuesta, correcta, error_api = "", False, f"{type(e).__name__}: {e}"
            met = {"pasos": 0, "n_llamadas": 0, "errores_herramienta": 0,
                   "tiempo_s": round(time.time() - t0, 2), "llamadas": []}
        filas.append({
            "id": item["id"], "tipo": item["tipo"],
            "pregunta": item["pregunta"], "esperado": item["esperado"],
            "respuesta": respuesta, "correcta": correcta,
            "pasos": met["pasos"], "n_llamadas": met["n_llamadas"],
            "errores_herramienta": met["errores_herramienta"],
            "tiempo_s": met["tiempo_s"], "error_api": error_api,
        })
        marca = "OK " if correcta else "MAL"
        print(f"  [{marca}] p{item['id']:02d} ({met['tiempo_s']:5.1f}s, "
              f"{met['n_llamadas']} tools) {item['pregunta'][:60]}")
        time.sleep(PAUSA_ENTRE_PREGUNTAS)
    return filas


def resumen_config(nombre, filas):
    df = pd.DataFrame(filas)
    return {
        "configuracion": nombre,
        "n_preguntas": len(df),
        "tasa_exito_%": round(100 * df["correcta"].mean(), 1),
        "pasos_prom": round(df["pasos"].mean(), 2),
        "llamadas_prom": round(df["n_llamadas"].mean(), 2),
        "errores_herramienta": int(df["errores_herramienta"].sum()),
        "errores_api": int(df["error_api"].notna().sum()),
        "tiempo_prom_s": round(df["tiempo_s"].mean(), 2),
    }


def graficar_resumen(exp, df_resumen):
    fig, ejes = plt.subplots(1, 3, figsize=(12, 3.8))
    for eje, col, titulo in zip(
            ejes,
            ["tasa_exito_%", "llamadas_prom", "tiempo_prom_s"],
            ["Tasa de exito (%)", "Llamadas a herramientas (prom)",
             "Tiempo por pregunta (s)"]):
        eje.bar(df_resumen["configuracion"], df_resumen[col], color="#4C72B0")
        eje.set_title(titulo, fontsize=10)
        eje.tick_params(axis="x", rotation=15, labelsize=8)
        eje.grid(alpha=0.3, axis="y")
        if col == "tasa_exito_%":
            eje.set_ylim(0, 100)
    fig.suptitle(EXPERIMENTOS[exp]["titulo"])
    fig.tight_layout()
    ruta = os.path.join(RESULTADOS, f"grafico_{exp}.png")
    fig.savefig(ruta, dpi=120)
    plt.close(fig)
    print(f"grafico -> {ruta}")


def correr_experimento(exp, preguntas):
    print("=" * 70)
    print(EXPERIMENTOS[exp]["titulo"])
    print("=" * 70)
    resumenes = []
    for nombre, kwargs in EXPERIMENTOS[exp]["configs"].items():
        filas = correr_config(nombre, kwargs, preguntas)
        with open(os.path.join(RESULTADOS, f"{exp}_{nombre}.json"),
                  "w", encoding="utf-8") as f:
            json.dump(filas, f, ensure_ascii=False, indent=2)
        resumenes.append(resumen_config(nombre, filas))

    df = pd.DataFrame(resumenes)
    print("\n" + df.to_string(index=False))
    df.to_csv(os.path.join(RESULTADOS, f"resumen_{exp}.csv"), index=False)
    graficar_resumen(exp, df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", default="all",
                        choices=[*EXPERIMENTOS, "all"])
    parser.add_argument("--quick", action="store_true",
                        help="solo 8 preguntas (prueba de humo)")
    args = parser.parse_args()

    with open(os.path.join(CARPETA, "preguntas.json"), encoding="utf-8") as f:
        preguntas = json.load(f)
    if args.quick:
        # muestra pequena pero variada: 6 numericas/texto + 2 de grafico
        preguntas = preguntas[:6] + [p for p in preguntas
                                     if p["tipo"] == "grafico"][:2]

    os.makedirs(RESULTADOS, exist_ok=True)
    experimentos = list(EXPERIMENTOS) if args.exp == "all" else [args.exp]
    for exp in experimentos:
        correr_experimento(exp, preguntas)


if __name__ == "__main__":
    main()
