# Clustering — Segmentación de clientes (aprendizaje no supervisado)

Proyecto de *clustering* sobre el dataset **Mall Customer Segmentation Data**
(Kaggle, 200 clientes), con una **visualización web interactiva**.

Se implementan y comparan los tres algoritmos de agrupamiento clásicos:

| Algoritmo | Idea | Implementación |
|-----------|------|----------------|
| **K-Means** | k centroides que minimizan la inercia (algoritmo de Lloyd) | *desde cero* (numpy) **y** scikit-learn |
| **Clustering jerárquico** | fusiona los clusters más cercanos → dendrograma (enlace Ward) | scikit-learn + scipy |
| **DBSCAN** | agrupa por densidad, descubre el nº de clusters y marca *outliers* | scikit-learn |

> **Nota sobre “KNN”.** KNN (*K-Nearest Neighbors*) es un algoritmo **supervisado**
> de clasificación, no un método de clustering. El algoritmo de agrupamiento
> análogo, basado en `k` prototipos, es **K-Means**, que es el que se implementa aquí.

## Dataset

`data/Mall_Customers.csv` — origen: Kaggle, *Mall Customer Segmentation Data*.
Columnas: `CustomerID, Genre, Age, Annual Income (k$), Spending Score (1-100)`.
La segmentación usa por defecto **ingreso anual** y **spending score** (2D → visualizable).

## Estructura

```
mlclustering/
├── clustering.py         # lógica de los 3 algoritmos (numpy + sklearn) + métricas
├── app.py                # servidor Flask con la API REST y la web
├── requirements.txt
├── data/
│   └── Mall_Customers.csv
└── web/
    ├── templates/index.html
    └── static/  (style.css, app.js, plotly.min.js)
```

## Uso

```bash
pip install -r requirements.txt

# 1) Reporte comparativo por consola (métricas de los 3 algoritmos + codo)
python clustering.py

# 2) Visualización web interactiva
python app.py
#   -> abrir http://127.0.0.1:5000
```

## La visualización

Dashboard interactivo (Flask + Plotly) donde puedes:

- Cambiar de algoritmo con pestañas (K-Means / Jerárquico / DBSCAN).
- Ajustar hiperparámetros en vivo:
  - K-Means: `k` y la implementación (numpy “desde cero” vs scikit-learn).
  - Jerárquico: nº de clusters de corte y tipo de *linkage*.
  - DBSCAN: `eps` y `min_samples`.
- Ver, para cada configuración:
  - **Scatter** de los clusters con sus centroides (y el ruido en gris en DBSCAN).
  - **Métricas**: nº de clusters, coeficiente de **silueta**, inercia/iteraciones, outliers.
  - **Gráfica de apoyo** para elegir hiperparámetros: método del **codo** (K-Means),
    **dendrograma** (jerárquico) y curva **k-dist** (DBSCAN).
  - **Silueta por punto**, agrupada por cluster.

## Métricas de referencia (parámetros por defecto)

| Algoritmo | Config | Clusters | Silueta |
|-----------|--------|:--------:|:-------:|
| K-Means (numpy y sklearn coinciden) | k=5 | 5 | 0.555 |
| Jerárquico (Ward) | k=5 | 5 | 0.554 |
| DBSCAN | eps=0.4, min_samples=5 | 4 (+15 ruido) | 0.478 |

El **método del codo** y la **silueta** coinciden en que `k=5` es la mejor
segmentación para este dataset (5 perfiles de cliente bien diferenciados).
