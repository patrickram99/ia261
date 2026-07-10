"""
==============================================================================
 ETAPA 4 DEL PIPELINE: TECNICA DE IA - AGENTE LLM CON HERRAMIENTAS (ReAct)
==============================================================================

Loop ReAct manual sobre la API de Gemini con function calling:

    pregunta -> Gemini decide: ¿responder o llamar una herramienta?
             -> se ejecuta la herramienta y se le devuelve el resultado
             -> se repite hasta obtener la respuesta final (tope MAX_PASOS)

El loop es manual (no automatic function calling) para poder medir las
metricas que pide la rubrica: pasos, llamadas a herramientas, errores,
tiempo.

Uso por CLI (smoke test):
    python -m agente.agente "¿Cual fue el sismo de mayor magnitud en 2024?"
==============================================================================
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from . import herramientas as H
from .prompts import PROMPTS, PROMPT_SIN_HERRAMIENTAS

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), ".env"))

# El modelo por defecto puede cambiarse sin tocar codigo (variable de
# entorno GEMINI_MODELO), util si un modelo se satura el dia de la demo.
MODELO_DEFECTO = os.environ.get("GEMINI_MODELO", "gemini-3.1-flash-lite")
MAX_PASOS = 10
MAX_REINTENTOS = 4          # ante 429/503 (cuota o alta demanda)


class AgenteSismos:
    """Agente analista del catalogo sismico del IGP."""

    def __init__(self, modelo=MODELO_DEFECTO, prompt="detallado",
                 usar_herramientas=True, incluir_resumen=True):
        self.cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.modelo = modelo
        self.usar_herramientas = usar_herramientas

        if usar_herramientas:
            self.system = PROMPTS[prompt]
            self.tools = [types.Tool(function_declarations=H.DECLARACIONES)]
        else:
            # Experimento 2: "LLM solo", sin herramientas. Con
            # incluir_resumen recibe un resumen del dataset en el prompt;
            # sin el, solo conoce el esquema (configuracion mas debil).
            resumen = (self._resumen_dataset() if incluir_resumen
                       else "(resumen no disponible)")
            self.system = PROMPT_SIN_HERRAMIENTAS.format(resumen=resumen)
            self.tools = None

    @staticmethod
    def _resumen_dataset():
        esquema = H.obtener_esquema()
        return (f"Resumen del dataset: {esquema['filas']} sismos, "
                f"fechas {esquema['rango_fechas']}, "
                f"magnitud {esquema['rango_magnitud']}, "
                f"profundidad (km) {esquema['rango_profundidad_km']}, "
                f"departamentos: {', '.join(esquema['departamentos'])}.")

    # ------------------------------------------------------------------
    #  Llamada al modelo con reintentos (la API gratuita devuelve 429 por
    #  cuota por minuto y 503 en picos de demanda)
    # ------------------------------------------------------------------
    def _generar(self, contenidos):
        for intento in range(MAX_REINTENTOS + 1):
            try:
                return self.cliente.models.generate_content(
                    model=self.modelo,
                    contents=contenidos,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system,
                        tools=self.tools,
                        temperature=0.1,
                    ),
                )
            except errors.APIError as e:
                if e.code in (429, 503) and intento < MAX_REINTENTOS:
                    time.sleep(2 ** (intento + 1))
                    continue
                raise

    # ------------------------------------------------------------------
    #  LOOP ReAct
    # ------------------------------------------------------------------
    def preguntar(self, pregunta, historial=None):
        """
        Responde una pregunta. Devuelve un dict con la respuesta, las
        metricas del episodio y el historial actualizado (para chat
        multi-turno).
        """
        contenidos = list(historial) if historial else []
        contenidos.append(types.Content(
            role="user", parts=[types.Part.from_text(text=pregunta)]))

        metricas = {"pasos": 0, "llamadas": [], "errores_herramienta": 0,
                    "graficos": []}
        inicio = time.time()
        respuesta_final = ""

        for _ in range(MAX_PASOS):
            metricas["pasos"] += 1
            respuesta = self._generar(contenidos)

            candidato = respuesta.candidates[0]
            llamadas = [p.function_call for p in candidato.content.parts
                        if p.function_call] if candidato.content.parts else []

            if not llamadas:
                respuesta_final = respuesta.text or ""
                contenidos.append(candidato.content)
                break

            # -- ejecutar cada herramienta pedida y devolver el resultado --
            contenidos.append(candidato.content)
            partes_respuesta = []
            for fc in llamadas:
                argumentos = dict(fc.args) if fc.args else {}
                resultado = H.ejecutar(fc.name, argumentos)
                metricas["llamadas"].append(
                    {"herramienta": fc.name, "argumentos": argumentos})
                if isinstance(resultado, dict):
                    if "error" in resultado:
                        metricas["errores_herramienta"] += 1
                    if resultado.get("ruta"):
                        metricas["graficos"].append(resultado["ruta"])
                partes_respuesta.append(types.Part.from_function_response(
                    name=fc.name, response=resultado))
            contenidos.append(types.Content(role="user",
                                            parts=partes_respuesta))
        else:
            respuesta_final = ("No pude llegar a una respuesta en "
                               f"{MAX_PASOS} pasos.")

        metricas["tiempo_s"] = round(time.time() - inicio, 2)
        metricas["n_llamadas"] = len(metricas["llamadas"])
        return {"respuesta": respuesta_final, "metricas": metricas,
                "historial": contenidos}


# ---------------------------------------------------------------------------
#  Smoke test por CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    pregunta = " ".join(sys.argv[1:]) or \
        "¿Cual fue el sismo de mayor magnitud registrado y donde ocurrio?"
    agente = AgenteSismos()
    salida = agente.preguntar(pregunta)
    print("PREGUNTA :", pregunta)
    print("RESPUESTA:", salida["respuesta"])
    print("METRICAS :", json.dumps({k: v for k, v in salida["metricas"].items()
                                    if k != "historial"},
                                   ensure_ascii=False, indent=2))
