"""
Comparativa: HC vs SA con diferentes tamaños de n
==================================================
Genera tablas y gráficas comparando:
  - Calidad de la solución
  - Tiempo de ejecución
  - Convergencia
"""

import os
import sys
import random
import statistics
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from algorithms import hill_climbing, simulated_annealing
from problema_funcion import rastrigin, estado_inicial_rastrigin, vecino_rastrigin
from problema_tsp import (
    generar_ciudades, costo_tsp, estado_inicial_tsp, vecino_tsp_2opt
)


REPETICIONES = 5  # cada experimento se repite varias veces


def experimento_rastrigin(n_dims):
    """Compara HC vs SA en Rastrigin para una dimensión dada."""
    res_hc, res_sa = [], []
    t_hc_total, t_sa_total = 0, 0
    for r in range(REPETICIONES):
        seed = 1000 + r
        random.seed(seed)
        x0 = estado_inicial_rastrigin(n_dims)

        random.seed(seed)
        _, c_hc, _, t_hc = hill_climbing(
            list(x0), vecino_rastrigin, rastrigin, max_iter=3000
        )
        res_hc.append(c_hc)
        t_hc_total += t_hc

        random.seed(seed)
        _, c_sa, _, t_sa = simulated_annealing(
            list(x0), vecino_rastrigin, rastrigin,
            T_inicial=50.0, T_final=0.001, alpha=0.97, iter_por_T=15
        )
        res_sa.append(c_sa)
        t_sa_total += t_sa

    return {
        "hc_mean": statistics.mean(res_hc),
        "hc_std": statistics.stdev(res_hc) if len(res_hc) > 1 else 0,
        "sa_mean": statistics.mean(res_sa),
        "sa_std": statistics.stdev(res_sa) if len(res_sa) > 1 else 0,
        "hc_time": t_hc_total / REPETICIONES,
        "sa_time": t_sa_total / REPETICIONES,
    }


def experimento_tsp(n):
    res_hc, res_sa = [], []
    t_hc_total, t_sa_total = 0, 0
    ciudades = generar_ciudades(n, seed=42)
    costo_fn = lambda r: costo_tsp(r, ciudades)

    for r in range(REPETICIONES):
        seed = 1000 + r
        random.seed(seed)
        x0 = estado_inicial_tsp(n)

        random.seed(seed)
        _, c_hc, _, t_hc = hill_climbing(
            list(x0), vecino_tsp_2opt, costo_fn, max_iter=3000
        )
        res_hc.append(c_hc)
        t_hc_total += t_hc

        random.seed(seed)
        _, c_sa, _, t_sa = simulated_annealing(
            list(x0), vecino_tsp_2opt, costo_fn,
            T_inicial=100.0, T_final=0.1, alpha=0.995, iter_por_T=15
        )
        res_sa.append(c_sa)
        t_sa_total += t_sa

    return {
        "hc_mean": statistics.mean(res_hc),
        "hc_std": statistics.stdev(res_hc) if len(res_hc) > 1 else 0,
        "sa_mean": statistics.mean(res_sa),
        "sa_std": statistics.stdev(res_sa) if len(res_sa) > 1 else 0,
        "hc_time": t_hc_total / REPETICIONES,
        "sa_time": t_sa_total / REPETICIONES,
    }


def grafica_comparacion(ns, resultados, titulo, ylabel_costo, salida):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    hc_means = [r["hc_mean"] for r in resultados]
    sa_means = [r["sa_mean"] for r in resultados]
    hc_std = [r["hc_std"] for r in resultados]
    sa_std = [r["sa_std"] for r in resultados]
    hc_times = [r["hc_time"] for r in resultados]
    sa_times = [r["sa_time"] for r in resultados]

    ax = axes[0]
    ax.errorbar(ns, hc_means, yerr=hc_std, marker="o",
                label="Hill Climbing", color="#d62728", capsize=4, linewidth=2)
    ax.errorbar(ns, sa_means, yerr=sa_std, marker="s",
                label="Simulated Annealing", color="#1f77b4", capsize=4, linewidth=2)
    ax.set_xlabel("Tamaño de n")
    ax.set_ylabel(ylabel_costo)
    ax.set_title(f"{titulo} — Calidad de la solución")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(ns, hc_times, marker="o", label="Hill Climbing",
            color="#d62728", linewidth=2)
    ax.plot(ns, sa_times, marker="s", label="Simulated Annealing",
            color="#1f77b4", linewidth=2)
    ax.set_xlabel("Tamaño de n")
    ax.set_ylabel("Tiempo (s)")
    ax.set_title(f"{titulo} — Tiempo de ejecución")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.suptitle(f"Comparativa HC vs SA — {titulo}",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(salida, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Gráfica: {salida}")


def imprimir_tabla(ns, resultados, problema):
    print(f"\n--- Resultados {problema} ---")
    print(f"{'n':>4} | {'HC mean':>10} | {'SA mean':>10} | "
          f"{'HC time':>9} | {'SA time':>9} | Ganador")
    print("-" * 70)
    for n, r in zip(ns, resultados):
        ganador = "SA" if r["sa_mean"] < r["hc_mean"] else "HC"
        print(f"{n:>4} | {r['hc_mean']:>10.3f} | {r['sa_mean']:>10.3f} | "
              f"{r['hc_time']:>9.3f} | {r['sa_time']:>9.3f} | {ganador}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)

    print("\n========== RASTRIGIN ==========")
    ns_r = [2, 5, 10, 20, 30]
    res_r = [experimento_rastrigin(n) for n in ns_r]
    imprimir_tabla(ns_r, res_r, "Rastrigin")
    grafica_comparacion(ns_r, res_r, "Rastrigin",
                        "Costo (menor = mejor)",
                        os.path.join(out_dir, "comparativa_rastrigin.png"))

    print("\n========== TSP ==========")
    ns_t = [10, 20, 30, 50, 80]
    res_t = [experimento_tsp(n) for n in ns_t]
    imprimir_tabla(ns_t, res_t, "TSP")
    grafica_comparacion(ns_t, res_t, "TSP",
                        "Distancia total",
                        os.path.join(out_dir, "comparativa_tsp.png"))

    # Guardar resultados como CSV para referencia
    with open(os.path.join(out_dir, "resultados.csv"), "w") as f:
        f.write("problema,n,hc_mean,hc_std,sa_mean,sa_std,hc_time,sa_time\n")
        for n, r in zip(ns_r, res_r):
            f.write(f"rastrigin,{n},{r['hc_mean']:.4f},{r['hc_std']:.4f},"
                    f"{r['sa_mean']:.4f},{r['sa_std']:.4f},"
                    f"{r['hc_time']:.4f},{r['sa_time']:.4f}\n")
        for n, r in zip(ns_t, res_t):
            f.write(f"tsp,{n},{r['hc_mean']:.4f},{r['hc_std']:.4f},"
                    f"{r['sa_mean']:.4f},{r['sa_std']:.4f},"
                    f"{r['hc_time']:.4f},{r['sa_time']:.4f}\n")
    print(f"\nCSV guardado: {os.path.join(out_dir, 'resultados.csv')}")
)
