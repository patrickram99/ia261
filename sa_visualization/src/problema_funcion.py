"""
Problema 1: Optimización de Función Rastrigin
==============================================
La función Rastrigin tiene MUCHOS mínimos locales.
Mínimo global en (0, 0, ..., 0) con valor 0.

f(x) = A*n + sum(x_i^2 - A*cos(2*pi*x_i))   con A=10
Dominio: [-5.12, 5.12]^n
"""

import random
import math


A = 10
LIMITE = 5.12


def rastrigin(x):
    """f(x) — minimización"""
    n = len(x)
    return A * n + sum(xi**2 - A * math.cos(2 * math.pi * xi) for xi in x)


def estado_inicial_rastrigin(n, seed=None):
    if seed is not None:
        random.seed(seed)
    return [random.uniform(-LIMITE, LIMITE) for _ in range(n)]


def vecino_rastrigin(x, paso=0.3):
    """Genera vecino perturbando una coordenada aleatoria."""
    nuevo = list(x)
    i = random.randint(0, len(x) - 1)
    nuevo[i] += random.uniform(-paso, paso)
    # Mantener dentro del dominio
    nuevo[i] = max(-LIMITE, min(LIMITE, nuevo[i]))
    return nuevo
