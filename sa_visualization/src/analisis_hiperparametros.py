"""
Análisis de hiperparámetros de Simulated Annealing
====================================================
Estudia el efecto de:
  1. Temperatura inicial (T_inicial)
  2. Factor de enfriamiento (alpha)
  3. Iteraciones por temperatura (iter_por_T)

Se usa TSP con n=30 ciudades como caso de estudio.
"""

import os
import sys
import random
import statistics
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from algorithms import simulated_annealing
from problema_tsp import (
    generar_ciudades, costo_tsp, estado_inicial_tsp, vecino_tsp_2opt
)


N_CIUDADES = 30
REPETICIONES = 5
ciudades = generar_ciudades(N_CIUDADES, seed=42)
costo_fn = lambda r: costo_tsp(r, ciudades)


def evaluar(T_inicial=100.0, T_final=0.1, alpha=0.995, iter_por_T=15):
    costos = []
    tiempos = []
    for r in range(REPETICIONES):
        random.seed(2000 + r)
        x0 = estado_inicial_tsp(N_CIUDADES)
        random.seed(2000 + r)
        _, c, _, t = simulated_annealing(
            list(x0), vecino_tsp_2opt, costo_fn,
            T_inicial=T_inicial, T_final=T_final,
            alpha=alpha, iter_por_T=iter_por_T,
        )
        costos.append(c)
        tiempos.append(t)
    return statistics.mean(costos), statistics.stdev(costos), \
           statistics.mean(tiempos)


def graficar(xs, ys_costo, ys_costo_std, ys_tiempo, xlabel, titulo, salida):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ax.errorbar(xs, ys_costo, yerr=ys_costo_std,
                marker="o", color="#1f77b4", capsize=4, linewidth=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Distancia (mejor solución)")
    ax.set_title(f"Efecto en la calidad")
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(xs, ys_tiempo, marker="s", color="#2ca02c", linewidth=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Tiempo (s)")
    ax.set_title(f"Efecto en el tiempo")
    ax.grid(alpha=0.3)

    fig.suptitle(titulo, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(salida, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Gráfica: {salida}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)

    # 1) Temperatura inicial
    print("\n--- Temperatura inicial ---")
    Ts = [1, 5, 20, 50, 100, 200, 500]
    means, stds, times = [], [], []
    for T in Ts:
        m, s, t = evaluar(T_inicial=T)
        means.append(m); stds.append(s); times.append(t)
        print(f"  T_inicial={T:>5}  costo={m:.2f} ± {s:.2f}  t={t:.3f}s")
    graficar(Ts, means, stds, times,
             "Temperatura inicial",
             "Hiperparámetro: Temperatura inicial",
             os.path.join(out_dir, "hiper_temperatura_inicial.png"))

    # 2) Factor de enfriamiento
    print("\n--- Factor de enfriamiento (alpha) ---")
    alphas = [0.80, 0.90, 0.95, 0.97, 0.99, 0.995, 0.999]
    means, stds, times = [], [], []
    for a in alphas:
        m, s, t = evaluar(alpha=a)
        means.append(m); stds.append(s); times.append(t)
        print(f"  alpha={a:>5}  costo={m:.2f} ± {s:.2f}  t={t:.3f}s")
    graficar(alphas, means, stds, times,
             "Alpha (factor de enfriamiento)",
             "Hiperparámetro: Factor de enfriamiento",
             os.path.join(out_dir, "hiper_alpha.png"))

    # 3) Iteraciones por temperatura
    print("\n--- Iteraciones por temperatura ---")
    iters = [1, 5, 10, 15, 25]
    means, stds, times = [], [], []
    for it in iters:
        m, s, t = evaluar(iter_por_T=it)
        means.append(m); stds.append(s); times.append(t)
        print(f"  iter_por_T={it:>3}  costo={m:.2f} ± {s:.2f}  t={t:.3f}s")
    graficar(iters, means, stds, times,
             "Iteraciones por nivel de T",
             "Hiperparámetro: Iteraciones por temperatura",
             os.path.join(out_dir, "hiper_iter_por_T.png"))

    print("\nListo.")
