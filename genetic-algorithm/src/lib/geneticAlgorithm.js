// @ts-nocheck
// Operadores del algoritmo genetico para neuroevolucion de pesos de la red.
// El genoma es un Float32Array. Los individuos se evaluan jugando el Dino Runner.

import { xavierInit, weightsCount, randn, NN_LAYERS } from './neuralNet.js';

// 1) INICIALIZACION DE POBLACION (Xavier/Glorot)
// Justificacion: para una red con activacion tanh, pesos N(0, sqrt(2/fan_in))
// mantienen la varianza de las activaciones y evitan saturacion. Tambien aportan
// diversidad genetica desde la generacion 0 sin caos extremo.
export function initPopulation(size, layers = NN_LAYERS) {
  const pop = new Array(size);
  for (let i = 0; i < size; i++) pop[i] = xavierInit(layers);
  return pop;
}

// 2) SELECCION POR TORNEO
// Justificacion: el torneo NO requiere normalizar fitness (a diferencia de la
// ruleta) y permite controlar la presion selectiva con un solo parametro k:
//   k = 2  -> seleccion suave, mas exploracion (diversificacion)
//   k = 7  -> seleccion fuerte, mas explotacion (intensificacion)
export function tournamentSelect(population, fitness, k) {
  let bestIdx = -1;
  let bestFit = -Infinity;
  for (let i = 0; i < k; i++) {
    const idx = Math.floor(Math.random() * population.length);
    if (fitness[idx] > bestFit) {
      bestFit = fitness[idx];
      bestIdx = idx;
    }
  }
  return population[bestIdx];
}

// 3) CROSSOVER UNIFORME POR GEN
// Justificacion: en neuroevolucion, los pesos NO tienen un orden semantico
// (no es como una ruta TSP donde la posicion importa). El crossover de 1 punto
// introduce un sesgo posicional artificial. El uniforme trata cada peso como un
// gen independiente y mezcla mejor "subredes" de ambos padres.
export function uniformCrossover(parentA, parentB, crossoverProb) {
  // crossoverProb es la probabilidad GLOBAL de que ocurra crossover.
  // Si no ocurre, el hijo clona a parentA.
  if (Math.random() > crossoverProb) {
    return new Float32Array(parentA);
  }
  const child = new Float32Array(parentA.length);
  for (let i = 0; i < parentA.length; i++) {
    child[i] = Math.random() < 0.5 ? parentA[i] : parentB[i];
  }
  return child;
}

// 4) MUTACION GAUSSIANA POR PESO
// Justificacion: para genomas de reales, la mutacion gaussiana es estandar.
// Permite ajustes finos (sigma chico -> intensificacion local) o saltos grandes
// (sigma grande -> diversificacion). La probabilidad por peso evita destruir
// individuos completos: solo unos pocos genes mutan por descendiente.
export function gaussianMutate(genome, mutationProb, sigma) {
  for (let i = 0; i < genome.length; i++) {
    if (Math.random() < mutationProb) {
      genome[i] += randn() * sigma;
    }
  }
  return genome;
}

// 5) REEMPLAZO GENERACIONAL CON ELITISMO
// Justificacion: el elitismo garantiza monotonia del mejor fitness (nunca empeora).
// Con elitism=0 el algoritmo puede "perder" buenas soluciones por mala suerte.
// Con elitism muy alto, la poblacion se homogeniza rapido -> convergencia prematura.
export function nextGeneration(population, fitness, hyper) {
  const { tournamentK, crossoverProb, mutationProb, mutationSigma, elitism } = hyper;
  const N = population.length;

  // Ordenar indices por fitness descendente.
  const order = fitness
    .map((f, i) => [f, i])
    .sort((a, b) => b[0] - a[0])
    .map(([, i]) => i);

  const next = new Array(N);

  // Copiar elite tal cual.
  for (let i = 0; i < elitism && i < N; i++) {
    next[i] = new Float32Array(population[order[i]]);
  }

  // Llenar el resto con torneo + crossover + mutacion.
  for (let i = elitism; i < N; i++) {
    const a = tournamentSelect(population, fitness, tournamentK);
    const b = tournamentSelect(population, fitness, tournamentK);
    const child = uniformCrossover(a, b, crossoverProb);
    gaussianMutate(child, mutationProb, mutationSigma);
    next[i] = child;
  }

  return {
    population: next,
    bestIdx: order[0],
    bestFitness: fitness[order[0]],
    avgFitness: fitness.reduce((s, f) => s + f, 0) / N,
    bestGenome: new Float32Array(population[order[0]]),
  };
}

// Helper: diversidad poblacional (desviacion estandar promedio por gen).
// Util para mostrar al usuario si la poblacion esta colapsando (signo de convergencia prematura).
export function diversity(population) {
  const L = population[0].length;
  const N = population.length;
  let totalStd = 0;
  for (let g = 0; g < L; g++) {
    let mean = 0;
    for (let i = 0; i < N; i++) mean += population[i][g];
    mean /= N;
    let v = 0;
    for (let i = 0; i < N; i++) {
      const d = population[i][g] - mean;
      v += d * d;
    }
    totalStd += Math.sqrt(v / N);
  }
  return totalStd / L;
}
