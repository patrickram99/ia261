"""
Visualización: Hill Climbing vs Simulated Annealing en Rastrigin 2D
====================================================================
Genera GIFs animados mostrando cómo cada algoritmo explora la función.
"""

import os
import sys
import math
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

sys.path.insert(0, os.path.dirname(__file__))
from algorithms import hill_climbing, simulated_annealing
from problema_funcion import rastrigin, estado_inicial_rastrigin, vecino_rastrigin, LIMITE


# ----------------------------------------------------------------------
# Variantes que GUARDAN cada estado visitado para animar después
# ----------------------------------------------------------------------
def hc_traza(estado_inicial, vecino_fn, costo_fn, max_iter=2000):
    actual = estado_inicial
    costo_actual = costo_fn(actual)
    traza = [(list(actual), costo_actual)]
    for _ in range(max_iter):
        v = vecino_fn(actual)
        cv = costo_fn(v)
        if cv < costo_actual:
            actual, costo_actual = v, cv
        traza.append((list(actual), costo_actual))
    return traza


def sa_traza(estado_inicial, vecino_fn, costo_fn,
             T_inicial=10.0, T_final=0.01, alpha=0.99, iter_por_T=10):
    actual = estado_inicial
    costo_actual = costo_fn(actual)
    mejor, mejor_costo = actual, costo_actual
    traza = [(list(actual), costo_actual)]
    T = T_inicial
    while T > T_final:
        for _ in range(iter_por_T):
            v = vecino_fn(actual)
            cv = costo_fn(v)
            d = cv - costo_actual
            if d < 0 or random.random() < math.exp(-d / T):
                actual, costo_actual = v, cv
                if costo_actual < mejor_costo:
                    mejor, mejor_costo = actual, costo_actual
            traza.append((list(actual), costo_actual))
        T *= alpha
    return traza


# ----------------------------------------------------------------------
# Generar superficie Rastrigin para fondo
# ----------------------------------------------------------------------
def generar_superficie(resolucion=120):
    x = np.linspace(-LIMITE, LIMITE, resolucion)
    y = np.linspace(-LIMITE, LIMITE, resolucion)
    X, Y = np.meshgrid(x, y)
    Z = 10 * 2 + (X**2 - 10 * np.cos(2 * np.pi * X)) + \
                  (Y**2 - 10 * np.cos(2 * np.pi * Y))
    return X, Y, Z


# ----------------------------------------------------------------------
# Animación lado a lado
# ----------------------------------------------------------------------
def animar_comparacion(traza_hc, traza_sa, salida, frames=60):
    X, Y, Z = generar_superficie()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Hill Climbing vs Simulated Annealing — Rastrigin 2D",
                 fontsize=14, fontweight="bold")

    titulos = ["Hill Climbing", "Simulated Annealing"]
    trazas = [traza_hc, traza_sa]

    artists = []
    for ax, titulo in zip(axes, titulos):
        ax.contourf(X, Y, Z, levels=30, cmap="viridis", alpha=0.85)
        ax.contour(X, Y, Z, levels=15, colors="white",
                   linewidths=0.3, alpha=0.4)
        ax.plot(0, 0, marker="*", markersize=18,
                color="gold", markeredgecolor="black",
                label="Mínimo global", zorder=5)
        ax.set_xlim(-LIMITE, LIMITE)
        ax.set_ylim(-LIMITE, LIMITE)
        ax.set_title(titulo)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend(loc="upper right", fontsize=9)

    # Inicializar líneas y puntos
    elementos = []
    for ax in axes:
        linea, = ax.plot([], [], "-", color="red", linewidth=1.2, alpha=0.7)
        punto, = ax.plot([], [], "o", color="red",
                         markersize=8, markeredgecolor="black")
        texto = ax.text(0.02, 0.97, "", transform=ax.transAxes,
                        verticalalignment="top",
                        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
                        fontsize=9)
        elementos.append((linea, punto, texto))

    # Submuestrear las trazas para tener `frames` cuadros
    def submuestrear(traza, n):
        if len(traza) <= n:
            return traza
        idx = np.linspace(0, len(traza) - 1, n).astype(int)
        return [traza[i] for i in idx]

    traza_hc_s = submuestrear(traza_hc, frames)
    traza_sa_s = submuestrear(traza_sa, frames)
    trazas_s = [traza_hc_s, traza_sa_s]

    def update(frame):
        out = []
        for (linea, punto, texto), traza in zip(elementos, trazas_s):
            historia = traza[: frame + 1]
            xs = [p[0][0] for p in historia]
            ys = [p[0][1] for p in historia]
            linea.set_data(xs, ys)
            punto.set_data([xs[-1]], [ys[-1]])
            costo = historia[-1][1]
            texto.set_text(f"Iter: {frame}\nCosto: {costo:.3f}")
            out.extend([linea, punto, texto])
        return out

    anim = FuncAnimation(fig, update, frames=frames, blit=False, interval=80)
    writer = PillowWriter(fps=12)
    anim.save(salida, writer=writer)
    plt.close(fig)
    print(f"  GIF guardado: {salida}")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)

    random.seed(7)
    inicial = estado_inicial_rastrigin(2)
    print("Estado inicial:", inicial)

    print("Ejecutando HC...")
    random.seed(7)
    t_hc = hc_traza(list(inicial), vecino_rastrigin, rastrigin, max_iter=2000)
    print(f"  HC final: x={t_hc[-1][0]}  costo={t_hc[-1][1]:.4f}")

    print("Ejecutando SA...")
    random.seed(7)
    t_sa = sa_traza(list(inicial), vecino_rastrigin, rastrigin,
                    T_inicial=10.0, T_final=0.01, alpha=0.97, iter_por_T=8)
    print(f"  SA final: x={t_sa[-1][0]}  costo={t_sa[-1][1]:.4f}")

    print("Generando animación...")
    animar_comparacion(t_hc, t_sa,
                       os.path.join(out_dir, "rastrigin_hc_vs_sa.gif"),
                       frames=60)
    print("Listo.")
