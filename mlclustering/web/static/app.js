/* ==========================================================================
   Logica del dashboard: pide datos a la API Flask y dibuja con Plotly.
   ========================================================================== */

// Paleta de colores para clusters (ruido = gris)
const PALETTE = [
  "#38bdf8", "#f472b6", "#4ade80", "#fbbf24", "#a78bfa",
  "#fb7185", "#34d399", "#60a5fa", "#f59e0b", "#c084fc",
];
const NOISE_COLOR = "#64748b";

const PLOT_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#e2e8f0", size: 12 },
  margin: { l: 55, r: 20, t: 20, b: 50 },
  legend: { bgcolor: "rgba(0,0,0,0)" },
};
const PLOT_CONFIG = { responsive: true, displayModeBar: false };

let dataset = null;          // puntos crudos (x, y, age, genre...)
let currentAlgo = "kmeans";

// ---------------------------------------------------------------- utilidades
function colorFor(label) {
  return label === -1 ? NOISE_COLOR : PALETTE[label % PALETTE.length];
}
function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ------------------------------------------------------------ lee parametros
function currentParams() {
  if (currentAlgo === "kmeans") {
    return {
      k: document.getElementById("k-slider").value,
      impl: document.getElementById("impl-select").value,
    };
  }
  if (currentAlgo === "hierarchical") {
    return {
      k: document.getElementById("hk-slider").value,
      linkage: document.getElementById("linkage-select").value,
    };
  }
  return {
    eps: document.getElementById("eps-slider").value,
    min_samples: document.getElementById("ms-slider").value,
  };
}

// ------------------------------------------------------------ tarjetas metricas
function renderMetrics(res) {
  const box = document.getElementById("metrics");
  const cards = [];
  const sil = res.silhouette == null ? "n/a" : res.silhouette.toFixed(3);
  cards.push(["Clusters", res.n_clusters]);
  cards.push(["Coef. silueta", sil]);
  if (res.algo === "kmeans") {
    cards.push(["Inercia", res.inertia.toFixed(1)]);
    cards.push(["Iteraciones", res.n_iter]);
    cards.push(["Implementacion", res.implementation === "scratch" ? "numpy" : "sklearn"]);
  } else if (res.algo === "hierarchical") {
    cards.push(["Enlace", res.linkage]);
  } else if (res.algo === "dbscan") {
    cards.push(["Ruido (outliers)", res.n_noise]);
    cards.push(["eps", res.eps]);
    cards.push(["min_samples", res.min_samples]);
  }
  box.innerHTML = cards.map(([label, value]) => `
    <div class="metric">
      <div class="value">${value}</div>
      <div class="label">${label}</div>
    </div>`).join("");
}

// ------------------------------------------------------------ scatter clusters
function renderScatter(res) {
  const [fx, fy] = dataset.features;
  const labels = res.labels;
  const groups = {};
  labels.forEach((lab, i) => {
    (groups[lab] = groups[lab] || { x: [], y: [], text: [] });
    groups[lab].x.push(dataset.x[i]);
    groups[lab].y.push(dataset.y[i]);
    groups[lab].text.push(
      `Cliente ${dataset.ids[i]}<br>Edad ${dataset.age[i]} &middot; ${dataset.genre[i]}`
    );
  });

  const traces = Object.keys(groups)
    .sort((a, b) => a - b)
    .map((lab) => {
      const L = parseInt(lab, 10);
      return {
        x: groups[lab].x,
        y: groups[lab].y,
        text: groups[lab].text,
        mode: "markers",
        type: "scatter",
        name: L === -1 ? "Ruido" : `Cluster ${L}`,
        marker: { color: colorFor(L), size: 9, line: { color: "#0f172a", width: .5 } },
        hovertemplate: `%{text}<br>${fx}: %{x}<br>${fy}: %{y}<extra></extra>`,
      };
    });

  // centroides (K-Means / jerarquico) como X grandes
  if (res.centroids && res.centroids.length) {
    traces.push({
      x: res.centroids.map((c) => c[0]),
      y: res.centroids.map((c) => c[1]),
      mode: "markers",
      type: "scatter",
      name: "Centroides",
      marker: { color: "#f8fafc", size: 16, symbol: "x", line: { width: 2 } },
      hovertemplate: `Centroide<br>${fx}: %{x:.1f}<br>${fy}: %{y:.1f}<extra></extra>`,
    });
  }

  const layout = Object.assign({}, PLOT_LAYOUT, {
    xaxis: { title: fx, gridcolor: "#334155" },
    yaxis: { title: fy, gridcolor: "#334155" },
    showlegend: true,
  });
  Plotly.react("scatter", traces, layout, PLOT_CONFIG);
}

// ------------------------------------------------------------ silueta por punto
function renderSilhouette(res) {
  const div = document.getElementById("silhouette");
  if (!res.silhouette_per_point) {
    Plotly.purge(div);
    div.innerHTML = "<p class='hint'>La silueta necesita al menos 2 clusters validos.</p>";
    return;
  }
  // Si venimos del mensaje de aviso (un <p> suelto), limpiamos ese texto.
  // OJO: no vaciar innerHTML cuando ya hay un grafico Plotly, porque eso
  // corrompe su estado interno y Plotly.react dejaria de dibujar.
  if (div.querySelector("p")) div.innerHTML = "";
  // ordena puntos por cluster y luego por valor de silueta
  const idx = res.labels.map((lab, i) => i)
    .filter((i) => res.labels[i] !== -1 && !isNaN(res.silhouette_per_point[i]))
    .sort((a, b) =>
      res.labels[a] - res.labels[b] ||
      res.silhouette_per_point[a] - res.silhouette_per_point[b]);

  const trace = {
    x: idx.map((_, pos) => pos),
    y: idx.map((i) => res.silhouette_per_point[i]),
    type: "bar",
    marker: { color: idx.map((i) => colorFor(res.labels[i])) },
    hovertemplate: "silueta: %{y:.3f}<extra></extra>",
  };
  const layout = Object.assign({}, PLOT_LAYOUT, {
    height: 240,
    xaxis: { title: "clientes (ordenados por cluster)", showticklabels: false, gridcolor: "#334155" },
    yaxis: { title: "silueta", gridcolor: "#334155", zerolinecolor: "#64748b" },
    shapes: res.silhouette == null ? [] : [{
      type: "line", x0: 0, x1: idx.length, y0: res.silhouette, y1: res.silhouette,
      line: { color: "#fbbf24", width: 1.5, dash: "dash" },
    }],
    annotations: res.silhouette == null ? [] : [{
      x: idx.length, y: res.silhouette, xanchor: "right", yanchor: "bottom",
      text: `promedio ${res.silhouette.toFixed(3)}`, showarrow: false,
      font: { color: "#fbbf24", size: 11 },
    }],
  });
  Plotly.react(div, [trace], layout, PLOT_CONFIG);
}

// ------------------------------------------------------------ graficas de apoyo
async function renderAux() {
  const title = document.getElementById("aux-title");
  const hint = document.getElementById("aux-hint");
  const div = "aux";

  if (currentAlgo === "kmeans") {
    title.textContent = "Metodo del codo + silueta";
    hint.textContent = "El 'codo' de la inercia y el maximo de la silueta sugieren el mejor k.";
    const e = await getJSON("/api/elbow");
    const t1 = { x: e.k, y: e.inertia, name: "Inercia", mode: "lines+markers",
      line: { color: "#38bdf8" }, yaxis: "y" };
    const t2 = { x: e.k, y: e.silhouette, name: "Silueta", mode: "lines+markers",
      line: { color: "#fbbf24" }, yaxis: "y2" };
    const layout = Object.assign({}, PLOT_LAYOUT, {
      xaxis: { title: "k", gridcolor: "#334155", dtick: 1 },
      yaxis: { title: "inercia", gridcolor: "#334155" },
      yaxis2: { title: "silueta", overlaying: "y", side: "right", showgrid: false },
      legend: { orientation: "h", y: 1.15 },
    });
    Plotly.react(div, [t1, t2], layout, PLOT_CONFIG);

  } else if (currentAlgo === "hierarchical") {
    title.textContent = "Dendrograma";
    hint.textContent = "Cortar el arbol horizontalmente define el numero de clusters.";
    const linkage = document.getElementById("linkage-select").value;
    const d = await getJSON(`/api/dendrogram?linkage=${linkage}`);
    const traces = d.icoord.map((xs, i) => ({
      x: xs, y: d.dcoord[i], mode: "lines", type: "scatter",
      line: { color: "#818cf8", width: 1 }, hoverinfo: "skip", showlegend: false,
    }));
    const layout = Object.assign({}, PLOT_LAYOUT, {
      xaxis: { showticklabels: false, gridcolor: "#334155", title: "clientes" },
      yaxis: { title: "distancia de fusion", gridcolor: "#334155" },
    });
    Plotly.react(div, traces, layout, PLOT_CONFIG);

  } else {
    title.textContent = "Curva k-dist (elegir eps)";
    hint.textContent = "El 'codo' de esta curva es un buen valor para eps.";
    const ms = document.getElementById("ms-slider").value;
    const kd = await getJSON(`/api/kdist?min_samples=${ms}`);
    const eps = parseFloat(document.getElementById("eps-slider").value);
    const trace = { x: kd.index, y: kd.kdist, mode: "lines",
      line: { color: "#4ade80" }, name: "k-dist" };
    const layout = Object.assign({}, PLOT_LAYOUT, {
      xaxis: { title: "puntos ordenados", gridcolor: "#334155" },
      yaxis: { title: "dist. al k-esimo vecino", gridcolor: "#334155" },
      shapes: [{ type: "line", x0: 0, x1: kd.index.length, y0: eps, y1: eps,
        line: { color: "#fbbf24", width: 1.5, dash: "dash" } }],
      annotations: [{ x: 0, y: eps, xanchor: "left", yanchor: "bottom",
        text: `eps = ${eps}`, showarrow: false, font: { color: "#fbbf24", size: 11 } }],
    });
    Plotly.react(div, [trace], layout, PLOT_CONFIG);
  }
}

// ------------------------------------------------------------ ciclo principal
async function update() {
  const params = currentParams();
  const qs = new URLSearchParams(Object.assign({ algo: currentAlgo }, params));
  const res = await getJSON(`/api/cluster?${qs.toString()}`);
  renderMetrics(res);
  renderScatter(res);
  renderSilhouette(res);
  await renderAux();
}
const updateDebounced = debounce(update, 120);

// ------------------------------------------------------------ eventos de UI
function switchAlgo(algo) {
  currentAlgo = algo;
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.algo === algo));
  ["kmeans", "hierarchical", "dbscan"].forEach((a) =>
    document.getElementById(`params-${a}`).classList.toggle("hidden", a !== algo));
  update();
}

function wireEvents() {
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchAlgo(t.dataset.algo)));

  // K-Means
  const kS = document.getElementById("k-slider");
  kS.addEventListener("input", () => {
    document.getElementById("k-val").textContent = kS.value; updateDebounced();
  });
  document.getElementById("impl-select").addEventListener("change", update);

  // Jerarquico
  const hkS = document.getElementById("hk-slider");
  hkS.addEventListener("input", () => {
    document.getElementById("hk-val").textContent = hkS.value; updateDebounced();
  });
  document.getElementById("linkage-select").addEventListener("change", update);

  // DBSCAN
  const epsS = document.getElementById("eps-slider");
  epsS.addEventListener("input", () => {
    document.getElementById("eps-val").textContent = parseFloat(epsS.value).toFixed(2);
    updateDebounced();
  });
  const msS = document.getElementById("ms-slider");
  msS.addEventListener("input", () => {
    document.getElementById("ms-val").textContent = msS.value; updateDebounced();
  });
}

// ------------------------------------------------------------ arranque
(async function init() {
  dataset = await getJSON("/api/dataset");
  wireEvents();
  await update();
})();
