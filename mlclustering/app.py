"""
==============================================================================
 APP WEB DE VISUALIZACION DE CLUSTERING  (Flask)
==============================================================================

Dashboard interactivo para explorar los tres algoritmos de clustering sobre
el dataset "Mall Customer Segmentation" (Kaggle):

    - K-Means            (con implementacion propia o sklearn, k ajustable)
    - Clustering Jerarquico (Agglomerative + dendrograma)
    - DBSCAN             (eps y min_samples ajustables, detecta outliers)

Ademas expone graficas de apoyo para elegir hiperparametros:
    - Metodo del codo + silueta (para k de K-Means)
    - Dendrograma (para el jerarquico)
    - Curva k-dist (para eps de DBSCAN)

Ejecucion:
    python app.py
    -> abre http://127.0.0.1:5000  en el navegador

Toda la logica de clustering vive en clustering.py; aqui solo se sirve la
interfaz y se exponen los datos como JSON via una pequena API REST.
==============================================================================
"""

from flask import Flask, render_template, jsonify, request

import clustering as C

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
)

# El dataset es pequeno (200 filas): se carga una sola vez al arrancar.
DATA = C.load_data()


# --------------------------------------------------------------------------
#  PAGINA PRINCIPAL
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------------------------------
#  API: puntos crudos del dataset (para el scatter base)
# --------------------------------------------------------------------------
@app.route("/api/dataset")
def api_dataset():
    df = DATA["df"]
    fx, fy = DATA["features"]
    return jsonify({
        "features": DATA["features"],
        "x": df[fx].tolist(),
        "y": df[fy].tolist(),
        "age": df["Age"].tolist(),
        "genre": df["Genre"].tolist(),
        "ids": df["CustomerID"].tolist(),
        "n": int(len(df)),
    })


# --------------------------------------------------------------------------
#  API: ejecutar un algoritmo de clustering con sus parametros
# --------------------------------------------------------------------------
@app.route("/api/cluster")
def api_cluster():
    algo = request.args.get("algo", "kmeans")
    if algo == "kmeans":
        k = int(request.args.get("k", 5))
        impl = request.args.get("impl", "sklearn")
        result = C.run_kmeans(DATA, k=k, implementation=impl)
    elif algo == "hierarchical":
        k = int(request.args.get("k", 5))
        linkage_method = request.args.get("linkage", "ward")
        result = C.run_hierarchical(DATA, k=k, linkage_method=linkage_method)
    elif algo == "dbscan":
        eps = float(request.args.get("eps", 0.4))
        min_samples = int(request.args.get("min_samples", 5))
        result = C.run_dbscan(DATA, eps=eps, min_samples=min_samples)
    else:
        return jsonify({"error": f"algoritmo desconocido: {algo}"}), 400
    return jsonify(result)


# --------------------------------------------------------------------------
#  API: graficas de apoyo para elegir hiperparametros
# --------------------------------------------------------------------------
@app.route("/api/elbow")
def api_elbow():
    return jsonify(C.elbow_curve(DATA, 1, 10))


@app.route("/api/dendrogram")
def api_dendrogram():
    linkage_method = request.args.get("linkage", "ward")
    return jsonify(C.dendrogram_data(DATA, linkage_method=linkage_method))


@app.route("/api/kdist")
def api_kdist():
    min_samples = int(request.args.get("min_samples", 5))
    return jsonify(C.kdist_curve(DATA, min_samples=min_samples))


if __name__ == "__main__":
    print("=" * 60)
    print(" Servidor de visualizacion de clustering")
    print(" Abre en el navegador:  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
