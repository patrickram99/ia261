/* ==========================================================================
   SismoAgente - logica del chat
   ==========================================================================
   - envia la pregunta a POST /api/chat con el modelo elegido
   - pinta la respuesta, los graficos generados y la traza de herramientas
     (pasos, llamadas, tiempo) que devuelve el agente
   ========================================================================== */

const mensajes = document.getElementById("mensajes");
const formulario = document.getElementById("formulario");
const entrada = document.getElementById("entrada");
const btnEnviar = document.getElementById("btn-enviar");
const selectModelo = document.getElementById("modelo");
const btnReset = document.getElementById("btn-reset");

/* Quita las imagenes markdown del texto (los graficos se pintan aparte). */
function limpiarTexto(texto) {
  return texto.replace(/!\[[^\]]*\]\([^)]*\)/g, "").trim();
}

function agregarMensaje(rol, texto) {
  const msg = document.createElement("div");
  msg.className = `msg ${rol}`;
  const burbuja = document.createElement("div");
  burbuja.className = "burbuja";
  burbuja.textContent = texto;
  msg.appendChild(burbuja);
  mensajes.appendChild(msg);
  mensajes.scrollTop = mensajes.scrollHeight;
  return burbuja;
}

function agregarGraficos(burbuja, rutas) {
  for (const ruta of rutas) {
    const img = document.createElement("img");
    img.src = ruta + "?t=" + Date.now();   // evitar cache del navegador
    img.className = "grafico";
    img.alt = "grafico generado por el agente";
    burbuja.appendChild(img);
  }
}

function agregarTraza(burbuja, metricas, modelo) {
  const traza = document.createElement("details");
  traza.className = "traza";
  const resumen = document.createElement("summary");
  resumen.textContent =
    `🔧 ${metricas.n_llamadas} herramienta(s) · ${metricas.pasos} paso(s) · ` +
    `${metricas.tiempo_s}s · ${modelo}` +
    (metricas.errores_herramienta ? ` · ⚠ ${metricas.errores_herramienta} error(es)` : "");
  traza.appendChild(resumen);
  for (const ll of metricas.llamadas) {
    const linea = document.createElement("code");
    const args = JSON.stringify(ll.argumentos);
    linea.textContent = `${ll.herramienta}(${args === "{}" ? "" : args})`;
    traza.appendChild(linea);
  }
  burbuja.appendChild(traza);
}

async function enviar(evento) {
  evento.preventDefault();
  const texto = entrada.value.trim();
  if (!texto) return;

  agregarMensaje("usuario", texto);
  entrada.value = "";
  btnEnviar.disabled = true;

  const espera = agregarMensaje("agente", "");
  espera.parentElement.classList.add("escribiendo");

  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje: texto, modelo: selectModelo.value }),
    });
    const datos = await r.json();
    espera.parentElement.classList.remove("escribiendo");

    if (!r.ok) {
      espera.textContent = `⚠ Error: ${datos.error || r.statusText}`;
      return;
    }
    espera.textContent = limpiarTexto(datos.respuesta) || "(sin texto)";
    if (datos.metricas.graficos.length) {
      agregarGraficos(espera, datos.metricas.graficos);
    }
    agregarTraza(espera, datos.metricas, datos.modelo);
  } catch (e) {
    espera.parentElement.classList.remove("escribiendo");
    espera.textContent = `⚠ Error de red: ${e.message}`;
  } finally {
    btnEnviar.disabled = false;
    entrada.focus();
    mensajes.scrollTop = mensajes.scrollHeight;
  }
}

async function reiniciar() {
  await fetch("/api/reset", { method: "POST" });
  // conservar solo el mensaje de bienvenida
  while (mensajes.children.length > 1) mensajes.removeChild(mensajes.lastChild);
}

formulario.addEventListener("submit", enviar);
btnReset.addEventListener("click", reiniciar);
entrada.focus();
