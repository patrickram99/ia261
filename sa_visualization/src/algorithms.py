"""
Implementación de Hill Climbing y Simulated Annealing
======================================================
Algoritmos genéricos que reciben:
  - estado_inicial: cualquier representación
  - vecino_fn(estado): genera un estado vecino
  - costo_fn(estado): retorna el costo (menor = mejor)
"""

import math
import random
import time


def hill_climbing(estado_inicial, vecino_fn, costo_fn, max_iter=10000):
    """
    Hill Climbing simple: solo acepta mejoras.
    Retorna: (mejor_estado, mejor_costo, historial_costos, tiempo)
    """
    inicio = time.time()
    actual = estado_inicial
    costo_actual = costo_fn(actual)
    historial = [costo_actual]

    for _ in range(max_iter):
        vecino = vecino_fn(actual)
        costo_vecino = costo_fn(vecino)

        # Solo aceptar si mejora (asume minimización)
        if costo_vecino < costo_actual:
            actual = vecino
            costo_actual = costo_vecino

        historial.append(costo_actual)

    tiempo = time.time() - inicio
    return actual, costo_actual, historial, tiempo


def simulated_annealing(
    estado_inicial,
    vecino_fn,
    costo_fn,
    T_inicial=100.0,
    T_final=0.01,
    alpha=0.995,
    iter_por_T=20,
):
    """
    Simulated Annealing.
    Acepta peores soluciones con probabilidad exp(-delta/T).

    Hiperparámetros:
      - T_inicial: temperatura inicial (mayor = más exploración)
      - T_final: temperatura final (criterio de parada)
      - alpha: factor de enfriamiento (0 < alpha < 1)
      - iter_por_T: iteraciones por cada nivel de temperatura

    Retorna: (mejor_estado, mejor_costo, historial_costos, tiempo)
    """
    inicio = time.time()
    actual = estado_inicial
    costo_actual = costo_fn(actual)
    mejor = actual
    mejor_costo = costo_actual
    historial = [costo_actual]

    T = T_inicial
    while T > T_final:
        for _ in range(iter_por_T):
            vecino = vecino_fn(actual)
            costo_vecino = costo_fn(vecino)
            delta = costo_vecino - costo_actual

            # Aceptar si mejora o con probabilidad exp(-delta/T)
            if delta < 0 or random.random() < math.exp(-delta / T):
                actual = vecino
                costo_actual = costo_vecino

                if costo_actual < mejor_costo:
                    mejor = actual
                    mejor_costo = costo_actual

            historial.append(costo_actual)

        T *= alpha  # Enfriamiento geométrico

    tiempo = time.time() - inicio
    return mejor, mejor_costo, historial, tiempo
