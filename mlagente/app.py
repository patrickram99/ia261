"""
==============================================================================
 ETAPA 6 DEL PIPELINE: APP WEB DE CHAT CON EL AGENTE  (Flask)
==============================================================================

Interfaz de chat para el agente analista de sismos del IGP:

    - el usuario pregunta en lenguaje natural
    - el agente (Gemini + herramientas) responde con cifras reales,
      mostrando la traza de herramientas invocadas y los graficos generados
    - selector de modelo para comparar en vivo (Experimento 1)

Ejecucion:
    python app.py
    -> abre http://127.0.0.1:5000 en el navegador

Toda la logica del agente vive en agente/; aqui solo se sirve la interfaz.
==============================================================================
"""

from flask import Flask, jsonify, render_template, request

from agente.agente import MODELO_DEFECTO, AgenteSismos
from agente.herramientas import obtener_esquema

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
)

MODELOS = [
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
]

# Cache de agentes por modelo e historial de la conversacion actual.
# (App de un solo usuario: suficiente para la demo del curso.)
_agentes = {}
_historial = []


def get_agente(modelo):
    if modelo not in _agentes:
        _agentes[modelo] = AgenteSismos(modelo=modelo)
    return _agentes[modelo]


@app.route("/")
def index():
    esquema = obtener_esquema()
    return render_template(
        "index.html",
        modelos=MODELOS,
        modelo_defecto=MODELO_DEFECTO,
        n_sismos=esquema["filas"],
        rango=[f[:10] for f in esquema["rango_fechas"]],
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    global _historial
    datos = request.get_json(force=True)
    pregunta = (datos.get("mensaje") or "").strip()
    modelo = datos.get("modelo") or MODELO_DEFECTO
    if not pregunta:
        return jsonify({"error": "mensaje vacio"}), 400

    try:
        salida = get_agente(modelo).preguntar(pregunta, historial=_historial)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502

    _historial = salida["historial"]
    return jsonify({
        "respuesta": salida["respuesta"],
        "metricas": salida["metricas"],
        "modelo": modelo,
    })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Borra el historial para empezar una conversacion nueva."""
    global _historial
    _historial = []
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
