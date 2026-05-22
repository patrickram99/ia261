// @ts-nocheck
// MLP de tamaño fijo. Genoma = vector plano de pesos (incluye sesgos).
// Arquitectura por defecto: 5 -> 6 -> 3
//   - 5 entradas: distObstaculo, anchoObst, altoObst, yDino, velJuego  (todas normalizadas en [0,1])
//   - 6 ocultas con activacion tanh
//   - 3 salidas (logits): nada / saltar / agacharse -> argmax

export const NN_LAYERS = [5, 6, 3];

// Cantidad total de pesos: para cada capa (n_in -> n_out) hay n_in*n_out pesos + n_out sesgos.
export function weightsCount(layers = NN_LAYERS) {
  let n = 0;
  for (let i = 0; i < layers.length - 1; i++) {
    n += layers[i] * layers[i + 1] + layers[i + 1];
  }
  return n;
}

// Muestra ~ N(0,1) por Box-Muller. Lo usamos para Xavier y para mutaciones gaussianas.
export function randn() {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Inicializacion Xavier/Glorot: w ~ N(0, sqrt(2 / fan_in)).
// Justificacion: mantiene la varianza de las activaciones en rangos utiles para tanh,
// y aporta diversidad inicial sin saturar la red.
export function xavierInit(layers = NN_LAYERS) {
  const w = new Float32Array(weightsCount(layers));
  let idx = 0;
  for (let l = 0; l < layers.length - 1; l++) {
    const fanIn = layers[l];
    const std = Math.sqrt(2 / fanIn);
    const nWeights = layers[l] * layers[l + 1];
    for (let k = 0; k < nWeights; k++) w[idx++] = randn() * std;
    // Sesgos arrancan en 0.
    for (let k = 0; k < layers[l + 1]; k++) w[idx++] = 0;
  }
  return w;
}

// Forward pass: recibe el vector plano de pesos y el input.
// Devuelve el indice (argmax) de la salida -> es la accion discreta.
export function forwardArgmax(weights, input, layers = NN_LAYERS) {
  let act = input;
  let idx = 0;
  for (let l = 0; l < layers.length - 1; l++) {
    const nIn = layers[l];
    const nOut = layers[l + 1];
    const next = new Float32Array(nOut);
    for (let j = 0; j < nOut; j++) {
      let s = 0;
      for (let i = 0; i < nIn; i++) s += act[i] * weights[idx + j * nIn + i];
      next[j] = s;
    }
    idx += nIn * nOut;
    // sesgos
    for (let j = 0; j < nOut; j++) next[j] += weights[idx++];
    // activacion: tanh en la capa oculta, lineal en la de salida
    if (l < layers.length - 2) {
      for (let j = 0; j < nOut; j++) next[j] = Math.tanh(next[j]);
    }
    act = next;
  }
  let best = 0;
  for (let j = 1; j < act.length; j++) if (act[j] > act[best]) best = j;
  return best;
}

// Serializacion para guardar/cargar el mejor genoma como JSON.
export function serialize(weights, meta = {}) {
  return JSON.stringify({
    version: 1,
    layers: NN_LAYERS,
    weights: Array.from(weights),
    ...meta,
  });
}

export function deserialize(json) {
  const obj = typeof json === 'string' ? JSON.parse(json) : json;
  if (!obj.weights) throw new Error('JSON invalido: falta "weights".');
  return new Float32Array(obj.weights);
}
