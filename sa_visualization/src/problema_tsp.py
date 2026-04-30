"""
Problema 2: Traveling Salesman Problem (TSP)
=============================================
Dado un conjunto de ciudades, encontrar la ruta más corta
que visita todas y regresa al origen.
"""

import random
import math


def generar_ciudades(n, seed=42):
    """Genera n ciudades aleatorias en un cuadrado 100x100."""
    rnd = random.Random(seed)
    return [(rnd.uniform(0, 100), rnd.uniform(0, 100)) for _ in range(n)]


def distancia(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def costo_tsp(ruta, ciudades):
    """Distancia total recorrida (incluye regreso al origen)."""
    total = 0.0
    for i in range(len(ruta)):
        a = ciudades[ruta[i]]
        b = ciudades[ruta[(i + 1) % len(ruta)]]
        total += distancia(a, b)
    return total


def estado_inicial_tsp(n, seed=None):
    """Permutación aleatoria de las n ciudades."""
    if seed is not None:
        random.seed(seed)
    ruta = list(range(n))
    random.shuffle(ruta)
    return ruta


def vecino_tsp_2opt(ruta):
    """
    Operador 2-opt: invierte un segmento de la ruta.
    Es el operador clásico para TSP.
    """
    nueva = list(ruta)
    n = len(nueva)
    i = random.randint(0, n - 2)
    j = random.randint(i + 1, n - 1)
    nueva[i:j + 1] = reversed(nueva[i:j + 1])
    return nueva
