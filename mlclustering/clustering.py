"""
==============================================================================
 CLUSTERING (APRENDIZAJE NO SUPERVISADO)
 K-Means  |  Clustering Jerarquico (Agglomerative)  |  DBSCAN
==============================================================================

Base de datos (Kaggle): "Mall Customer Segmentation Data"
    Archivo: data/Mall_Customers.csv   (200 clientes)
    Columnas: CustomerID, Genre, Age, Annual Income (k$), Spending Score (1-100)

Problema de clustering (NO supervisado):
    Segmentar a los clientes de un centro comercial en grupos ("clusters")
    con comportamiento de compra similar, SIN usar ninguna etiqueta previa.

    Atributos usados (features):  Annual Income (k$), Spending Score (1-100)
    (tambien se puede incluir Age; por defecto usamos las 2 clasicas para
     poder visualizar los grupos en un plano 2D).

Nota sobre "KNN":
    KNN (K-Nearest Neighbors) es un algoritmo SUPERVISADO de clasificacion,
    no un metodo de clustering. El algoritmo de clustering analogo, basado en
    "k" centros/prototipos, es K-MEANS, que es el que se implementa aqui.

Este archivo contiene, para K-Means:
    1) Implementacion "desde cero" usando SOLO numpy.
    2) Implementacion equivalente usando scikit-learn.
Y para Jerarquico / DBSCAN usa scikit-learn + scipy (dendrograma).

------------------------------------------------------------------------------
 FUNDAMENTO MATEMATICO (resumen)
------------------------------------------------------------------------------

1) ESTANDARIZACION
   Las variables tienen escalas distintas (ingreso 15-137, score 1-99). Todos
   los metodos usan distancias, por lo que ESTANDARIZAMOS cada atributo a
   media 0 y desviacion 1:
        z = (x - media) / desviacion

2) K-MEANS
   Busca k centroides que minimicen la inercia (suma de distancias al cuadrado
   de cada punto a su centroide mas cercano):
        J = SUM_i  || x_i - c_{a(i)} ||^2
   Algoritmo de Lloyd (se repite hasta converger):
        (a) Asignacion : cada punto va al centroide mas cercano.
        (b) Actualizacion: cada centroide = media de sus puntos.
   La eleccion de k se apoya en el "metodo del codo" (inercia vs k) y en el
   coeficiente de silueta.

3) CLUSTERING JERARQUICO (Agglomerative, enlace Ward)
   Empieza con cada punto como su propio cluster y en cada paso fusiona los
   dos clusters mas cercanos. El criterio "Ward" fusiona los pares que menos
   aumentan la varianza intra-cluster. El resultado se resume en un DENDROGRAMA;
   cortando el arbol a cierta altura se obtiene el numero de clusters.

4) DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
   Agrupa por densidad. Dos hiperparametros:
        eps      : radio de vecindad.
        min_samples: nº minimo de puntos para formar una region densa.
   Clasifica cada punto como:
        - nucleo (core): tiene >= min_samples vecinos dentro de eps.
        - borde        : cae dentro de eps de un nucleo pero no es nucleo.
        - ruido (-1)   : no pertenece a ningun cluster (outlier).
   Ventaja: descubre solo el nº de clusters, formas arbitrarias y outliers.

5) EVALUACION (sin etiquetas)
   - Inercia (solo K-Means).
   - Coeficiente de SILUETA en [-1, 1]: mide cuan compacto y separado esta
     cada punto respecto de su cluster vs el vecino mas cercano. Mayor = mejor.
==============================================================================
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.neighbors import NearestNeighbors
from scipy.cluster.hierarchy import linkage, dendrogram

# Ruta al dataset (relativa a este archivo, funciona desde cualquier cwd)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "Mall_Customers.csv")

# Atributos por defecto para la segmentacion (2D -> visualizable)
DEFAULT_FEATURES = ["Annual Income (k$)", "Spending Score (1-100)"]


# ==========================================================================
#  CARGA Y PREPARACION DE DATOS
# ==========================================================================
def load_data(features=None):
    """Carga el CSV, selecciona atributos y los estandariza.

    Devuelve un dict con:
        df        : DataFrame original completo
        features  : lista de columnas usadas
        X_raw     : matriz (n, d) en la escala original
        X         : matriz (n, d) estandarizada (media 0, desv 1)
        scaler    : StandardScaler ajustado (para invertir la escala)
    """
    features = features or DEFAULT_FEATURES
    df = pd.read_csv(DATA_PATH)
    X_raw = df[features].to_numpy(dtype=float)
    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)
    return {
        "df": df,
        "features": features,
        "X_raw": X_raw,
        "X": X,
        "scaler": scaler,
    }


# ==========================================================================
#  1) K-MEANS "DESDE CERO" (solo numpy) -- algoritmo de Lloyd
# ==========================================================================
class KMeansScratch:
    """K-Means implementado a mano para dejar clara la mecanica interna."""

    def __init__(self, k=5, max_iter=300, tol=1e-6, seed=42):
        self.k = k
        self.max_iter = max_iter
        self.tol = tol
        self.seed = seed
        self.centroids_ = None
        self.labels_ = None
        self.inertia_ = None
        self.n_iter_ = 0

    def _init_kpp(self, X):
        """Inicializacion tipo k-means++ (centroides iniciales dispersos)."""
        rng = np.random.default_rng(self.seed)
        n = X.shape[0]
        centroids = [X[rng.integers(n)]]
        for _ in range(1, self.k):
            # distancia^2 de cada punto al centroide ya elegido mas cercano
            d2 = np.min(
                [np.sum((X - c) ** 2, axis=1) for c in centroids], axis=0
            )
            probs = d2 / d2.sum()
            centroids.append(X[rng.choice(n, p=probs)])
        return np.array(centroids)

    def fit(self, X):
        X = np.asarray(X, dtype=float)
        self.centroids_ = self._init_kpp(X)
        for it in range(self.max_iter):
            # (a) ASIGNACION: distancia de cada punto a cada centroide
            #     dist[i, j] = || x_i - c_j ||
            dist = np.linalg.norm(X[:, None, :] - self.centroids_[None, :, :], axis=2)
            labels = np.argmin(dist, axis=1)
            # (b) ACTUALIZACION: cada centroide = media de sus puntos
            new_centroids = np.array([
                X[labels == j].mean(axis=0) if np.any(labels == j)
                else self.centroids_[j]           # si un cluster queda vacio, se mantiene
                for j in range(self.k)
            ])
            shift = np.linalg.norm(new_centroids - self.centroids_)
            self.centroids_ = new_centroids
            self.n_iter_ = it + 1
            if shift < self.tol:                  # convergio
                break
        self.labels_ = labels
        self.inertia_ = float(
            np.sum((X - self.centroids_[labels]) ** 2)
        )
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        dist = np.linalg.norm(X[:, None, :] - self.centroids_[None, :, :], axis=2)
        return np.argmin(dist, axis=1)


# ==========================================================================
#  ALGORITMOS (envoltorios que devuelven resultados listos para graficar)
# ==========================================================================
def _metrics(X, labels):
    """Calcula silueta ignorando el caso degenerado (< 2 clusters reales)."""
    mask = labels != -1                      # DBSCAN marca ruido como -1
    uniq = set(labels[mask].tolist())
    if len(uniq) < 2 or mask.sum() < 3:
        return {"silhouette": None, "silhouette_per_point": None}
    sil = float(silhouette_score(X[mask], labels[mask]))
    per_point = np.full(len(labels), np.nan)
    per_point[mask] = silhouette_samples(X[mask], labels[mask])
    # los puntos de ruido (DBSCAN) quedan como NaN -> los pasamos a None,
    # porque NaN no es JSON valido y romperia el fetch en el navegador.
    per_point_json = [None if np.isnan(v) else float(v) for v in per_point]
    return {
        "silhouette": sil,
        "silhouette_per_point": per_point_json,
    }


def run_kmeans(data, k=5, implementation="sklearn"):
    """Ejecuta K-Means (sklearn o 'from scratch') y devuelve resultados."""
    X = data["X"]
    if implementation == "scratch":
        model = KMeansScratch(k=k).fit(X)
        labels = model.labels_
        inertia = model.inertia_
        centroids_std = model.centroids_
        n_iter = model.n_iter_
    else:
        model = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        labels = model.labels_
        inertia = float(model.inertia_)
        centroids_std = model.cluster_centers_
        n_iter = int(model.n_iter_)
    # centroides de vuelta a la escala original (para mostrarlos)
    centroids_raw = data["scaler"].inverse_transform(centroids_std)
    out = {
        "algo": "kmeans",
        "implementation": implementation,
        "k": k,
        "labels": labels.astype(int).tolist(),
        "inertia": inertia,
        "n_iter": n_iter,
        "centroids": centroids_raw.tolist(),
        "n_clusters": int(len(set(labels.tolist()))),
        "n_noise": 0,
    }
    out.update(_metrics(X, labels))
    return out


def run_hierarchical(data, k=5, linkage_method="ward"):
    """Clustering jerarquico aglomerativo (corta el arbol en k clusters)."""
    X = data["X"]
    model = AgglomerativeClustering(n_clusters=k, linkage=linkage_method).fit(X)
    labels = model.labels_
    # centroide de cada cluster (media) en escala original, para referencia
    centroids_raw = np.array([
        data["X_raw"][labels == j].mean(axis=0) for j in range(k)
    ])
    out = {
        "algo": "hierarchical",
        "linkage": linkage_method,
        "k": k,
        "labels": labels.astype(int).tolist(),
        "centroids": centroids_raw.tolist(),
        "n_clusters": int(len(set(labels.tolist()))),
        "n_noise": 0,
    }
    out.update(_metrics(X, labels))
    return out


def run_dbscan(data, eps=0.5, min_samples=5):
    """DBSCAN por densidad. Descubre el nº de clusters y marca outliers (-1)."""
    X = data["X"]
    model = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    labels = model.labels_
    uniq = sorted(set(labels.tolist()))
    n_clusters = len([u for u in uniq if u != -1])
    n_noise = int(np.sum(labels == -1))
    # centroide de cada cluster real (excluye ruido)
    centroids_raw = [
        data["X_raw"][labels == j].mean(axis=0).tolist()
        for j in uniq if j != -1
    ]
    out = {
        "algo": "dbscan",
        "eps": eps,
        "min_samples": min_samples,
        "labels": labels.astype(int).tolist(),
        "centroids": centroids_raw,
        "n_clusters": n_clusters,
        "n_noise": n_noise,
    }
    out.update(_metrics(X, labels))
    return out


# ==========================================================================
#  HERRAMIENTAS DE APOYO PARA LA VISUALIZACION WEB
# ==========================================================================
def elbow_curve(data, k_min=1, k_max=10):
    """Metodo del codo: inercia y silueta para un rango de k (K-Means)."""
    X = data["X"]
    ks, inertias, sils = [], [], []
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        ks.append(k)
        inertias.append(float(km.inertia_))
        sils.append(float(silhouette_score(X, km.labels_)) if k >= 2 else None)
    return {"k": ks, "inertia": inertias, "silhouette": sils}


def dendrogram_data(data, linkage_method="ward", truncate=0):
    """Genera la estructura del dendrograma (para dibujarlo en el navegador)."""
    Z = linkage(data["X"], method=linkage_method)
    kwargs = {"no_plot": True}
    if truncate:
        kwargs.update(truncate_mode="lastp", p=truncate)
    dd = dendrogram(Z, **kwargs)
    return {
        "icoord": dd["icoord"],
        "dcoord": dd["dcoord"],
        "leaves": dd["leaves"],
        "color_list": dd["color_list"],
    }


def kdist_curve(data, min_samples=5):
    """Curva k-dist (ordenada) para elegir 'eps' de DBSCAN.

    La distancia al k-esimo vecino mas cercano, ordenada de menor a mayor,
    presenta un 'codo': ese valor es un buen candidato para eps.
    """
    X = data["X"]
    nn = NearestNeighbors(n_neighbors=min_samples).fit(X)
    dists, _ = nn.kneighbors(X)
    kth = np.sort(dists[:, -1])          # distancia al k-esimo vecino, ordenada
    return {"index": list(range(len(kth))), "kdist": kth.tolist()}


# ==========================================================================
#  EJECUCION DIRECTA: imprime un reporte comparativo por consola
# ==========================================================================
def _fmt(v):
    return "  n/a" if v is None else f"{v:6.3f}"


def main():
    data = load_data()
    n = len(data["df"])
    print("=" * 70)
    print(" SEGMENTACION DE CLIENTES  -  Mall Customer Segmentation (Kaggle)")
    print("=" * 70)
    print(f" Registros: {n} | Atributos: {', '.join(data['features'])}")
    print("-" * 70)

    # K-Means: comparamos implementacion propia vs sklearn con k=5
    km_scratch = run_kmeans(data, k=5, implementation="scratch")
    km_sklearn = run_kmeans(data, k=5, implementation="sklearn")
    print(" K-MEANS (k=5)")
    print(f"   desde cero : inercia={km_scratch['inertia']:.2f}"
          f"  silueta={_fmt(km_scratch['silhouette'])}"
          f"  iters={km_scratch['n_iter']}")
    print(f"   sklearn    : inercia={km_sklearn['inertia']:.2f}"
          f"  silueta={_fmt(km_sklearn['silhouette'])}"
          f"  iters={km_sklearn['n_iter']}")

    # Jerarquico
    hc = run_hierarchical(data, k=5)
    print(" JERARQUICO (Ward, k=5)")
    print(f"   clusters={hc['n_clusters']}  silueta={_fmt(hc['silhouette'])}")

    # DBSCAN
    db = run_dbscan(data, eps=0.4, min_samples=5)
    print(" DBSCAN (eps=0.4, min_samples=5)")
    print(f"   clusters={db['n_clusters']}  ruido={db['n_noise']}"
          f"  silueta={_fmt(db['silhouette'])}")

    print("-" * 70)
    print(" Metodo del codo (inercia por k):")
    elbow = elbow_curve(data, 1, 10)
    for k, inertia, sil in zip(elbow["k"], elbow["inertia"], elbow["silhouette"]):
        print(f"   k={k:2d}  inercia={inertia:8.2f}  silueta={_fmt(sil)}")
    print("=" * 70)
    print(" Para la visualizacion interactiva ejecuta:  python app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
