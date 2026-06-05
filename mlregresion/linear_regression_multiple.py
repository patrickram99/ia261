# -*- coding: utf-8 -*-
"""
Regresion lineal multiple con Numpy.

Adaptacion del codigo original de regresion lineal simple ( h(x) = w*x )
a un modelo con varias variables de entrada:

    h(x) = w0 + w1*x1 + w2*x2 + w3*x3

Base de datos (y = 1 + 2x1 + x2 + 2x3):

    x1  x2  x3   y
     1   2   6   17
     2   3   7   22
     3   4   6   23
     4   5   7   28
     5   6   6   29
     6   7   7   34
     7   8   6   35

La base de datos se guarda en 'dataset.csv' y tambien se deja
hardcodeada aqui mismo.
"""

import csv
import os
import numpy as np

# ---------------------------------------------------------------------------
# 1) Base de datos hardcodeada
# ---------------------------------------------------------------------------
DATA = [
    # x1, x2, x3,  y
    [1, 2, 6, 17],
    [2, 3, 7, 22],
    [3, 4, 6, 23],
    [4, 5, 7, 28],
    [5, 6, 6, 29],
    [6, 7, 7, 34],
    [7, 8, 6, 35],
]

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.csv")


def guardar_csv(path=CSV_PATH):
    """Escribe la base de datos hardcodeada en un archivo CSV."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x1", "x2", "x3", "y"])
        writer.writerows(DATA)
    print(f"CSV guardado en: {path}")


def cargar_csv(path=CSV_PATH):
    """Lee la base de datos desde el CSV y devuelve X (m,3) e Y (m,)."""
    datos = np.genfromtxt(path, delimiter=",", skip_header=1, dtype=np.float32)
    X = datos[:, :3]   # x1, x2, x3
    Y = datos[:, 3]    # y
    return X, Y


# ---------------------------------------------------------------------------
# 2) Modelo:  h(x) = w0 + w1*x1 + w2*x2 + w3*x3
# ---------------------------------------------------------------------------
def forward(X, w):
    # X tiene una columna de unos al inicio (para el bias w0)
    return X @ w


def loss(y, y_pred):
    return ((y - y_pred) ** 2).mean() / 2


# gradiente del MSE:  dJ/dw = 1/m * X^T (h(x) - y)
def gradient(X, y, y_pred):
    m = len(y)
    return (X.T @ (y_pred - y)) / m


# ---------------------------------------------------------------------------
# 3) Entrenamiento (gradiente descendiente)
# ---------------------------------------------------------------------------
def main():
    # Generamos / actualizamos el CSV y luego lo leemos
    guardar_csv()
    X_raw, Y = cargar_csv()

    m = X_raw.shape[0]

    # Normalizacion (estandarizacion) de las variables para que el
    # gradiente descendiente converja de forma estable.
    mu = X_raw.mean(axis=0)
    sigma = X_raw.std(axis=0)
    X_norm = (X_raw - mu) / sigma

    # Agregamos columna de unos para el termino independiente w0
    X = np.hstack([np.ones((m, 1), dtype=np.float32), X_norm])

    # Pesos iniciales: [w0, w1, w2, w3]
    w = np.zeros(X.shape[1], dtype=np.float32)

    # Hiperparametros
    learning_rate = 0.1
    n_iters = 1000

    print("Prediccion antes de entrenar:", forward(X, w))

    for epoch in range(n_iters):
        y_pred = forward(X, w)          # forward pass
        l = loss(Y, y_pred)             # costo
        dw = gradient(X, Y, y_pred)     # gradientes
        w -= learning_rate * dw         # actualizar pesos

        if epoch % 100 == 0:
            print(f"epoch {epoch+1:4d}: loss = {l:.6f}, w = {np.round(w, 3)}")

    # -------------------------------------------------------------------
    # 4) Resultados
    # -------------------------------------------------------------------
    y_pred = forward(X, w)
    print("\n--- Resultados (espacio normalizado) ---")
    print("Pesos w0..w3:", np.round(w, 4))

    # Convertir los pesos al espacio original (variables sin normalizar)
    #   h = w0 + sum( wi * (xi - mu_i)/sigma_i )
    #     = (w0 - sum(wi*mu_i/sigma_i)) + sum( (wi/sigma_i) * xi )
    w_orig = w[1:] / sigma
    b_orig = w[0] - np.sum(w[1:] * mu / sigma)
    print("\n--- Modelo en variables originales ---")
    print(f"y = {b_orig:.3f} + {w_orig[0]:.3f}*x1 + {w_orig[1]:.3f}*x2 + {w_orig[2]:.3f}*x3")
    print("(Referencia esperada: y = 1 + 2*x1 + 1*x2 + 2*x3)")

    print("\nY real     :", Y)
    print("Y predicho :", np.round(y_pred, 3))

    # Prediccion de un caso nuevo, por ejemplo x1=8, x2=9, x3=7
    nuevo = np.array([8, 9, 7], dtype=np.float32)
    nuevo_norm = (nuevo - mu) / sigma
    nuevo_x = np.hstack([[1.0], nuevo_norm])
    print(f"\nPrediccion para x1=8, x2=9, x3=7 -> {forward(nuevo_x, w):.3f}")


if __name__ == "__main__":
    main()
