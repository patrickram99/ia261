"""
Visualización: Hill Climbing vs Simulated Annealing en TSP
============================================================
Genera GIF mostrando cómo evoluciona la ruta en cada algoritmo.
"""

import os
import sys
import math
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

sys.path.insert(0, os.path.dirname(__file__))
from problema_tsp import (
    generar_ciudades, costo_tsp, estado_inicial_tsp, vecino_tsp_2opt
)


def hc_traza_tsp(estado_inicial, ciudades, max_iter=3000):
    actual = estado_inicial
    costo_actual = costo_tsp(actual, ciudades)
    traza = [(list(actual), costo_actual)]
    for _ in range(max_iter):
        v = vecino_tsp_2opt(actual)
        cv = costo_tsp(v, ciudades)
        if cv < costo_actual:
            actual, costo_actual = v, cv
        traza.append((list(actual), costo_actual))
    return traza


def sa_traza_tsp(estado_inicial, ciudades,
                 T_inicial=100.0, T_final=0.1, alpha=0.995, iter_por_T=15):
    actual = estado_inicial
    costo_actual = costo_tsp(actual, ciudades)
    mejor, mejor_costo = list(actual), costo_actual
    traza = [(list(actual), costo_actual)]
    T = T_inicial
    while T > T_final:
        for _ in range(iter_por_T):
            v = vecino_tsp_2opt(actual)
            cv = costo_tsp(v, ciudades)
            d = cv - costo_actual
            if d < 0 or random.random() < math.exp(-d / T):
                actual, costo_actual = v, cv
                if costo_actual < mejor_costo:
                    mejor, mejor_costo = list(actual), costo_actual
            traza.append((list(actual), costo_actual))
        T *= alpha
    return traza


def animar_tsp(ciudades, traza_hc, traza_sa, salida, frames=60):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"Hill Climbing vs Simulated Annealing — TSP ({len(ciudades)} ciudades)",
                 fontsize=14, fontweight="bold")

    cx = [c[0] for c in ciudades]
    cy = [c[1] for c in ciudades]

    elementos = []
    for ax, titulo in zip(axes, ["Hill Climbing", "Simulated Annealing"]):
        ax.scatter(cx, cy, c="black", s=40, zorder=3)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.set_title(titulo)
        ax.set_aspect("equal")
        linea, = ax.plot([], [], "-o", color="red",
                         markersize=4, linewidth=1.5)
        texto = ax.text(0.02, 0.97, "", transform=ax.transAxes,
                        verticalalignment="top",
                        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
                        fontsize=9)
        elementos.append((linea, texto))

    def submuestrear(traza, n):
        if len(traza) <= n:
            return traza
        idx = np.linspace(0, len(traza) - 1, n).astype(int)
        return [traza[i] for i in idx]

    t_hc = submuestrear(traza_hc, frames)
    t_sa = submuestrear(traza_sa, frames)
    trazas = [t_hc, t_sa]

    def update(frame):
        out = []
        for (linea, texto), traza in zip(elementos, trazas):
            ruta, costo = traza[frame]
            xs = [ciudades[i][0] for i in ruta] + [ciudades[ruta[0]][0]]
            ys = [ciudades[i][1] for i in ruta] + [ciudades[ruta[0]][1]]
            linea.set_data(xs, ys)
            texto.set_text(f"Iter: {frame}\nDistancia: {costo:.2f}")
            out.extend([linea, texto])
        return out

    anim = FuncAnimation(fig, update, frames=frames, blit=False, interval=80)
    writer = PillowWriter(fps=12)
    anim.save(salida, writer=writer)
    plt.close(fig)
    print(f"  GIF guardado: {salida}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)

    n = 25
    ciudades = generar_ciudades(n, seed=42)

    random.seed(13)
    inicial = estado_inicial_tsp(n)

    print(f"TSP con {n} ciudades")
    print(f"Costo inicial: {costo_tsp(inicial, ciudades):.2f}")

    print("Ejecutando HC...")
    random.seed(13)
    t_hc = hc_traza_tsp(list(inicial), ciudades, max_iter=3000)
    print(f"  HC final: {t_hc[-1][1]:.2f}")

    print("Ejecutando SA...")
    random.seed(13)
    t_sa = sa_traza_tsp(list(inicial), ciudades,
                        T_inicial=100.0, T_final=0.1,
                        alpha=0.995, iter_por_T=15)
    print(f"  SA final: {t_sa[-1][1]:.2f}")

    print("Generando animación...")
    animar_tsp(ciudades, t_hc, t_sa,
               os.path.join(out_dir, "tsp_hc_vs_sa.gif"),
               frames=60)
    print("Listo.")
