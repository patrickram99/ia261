// @ts-nocheck
// Hiperparametros por defecto del algoritmo genetico.
export const DEFAULT_HYPER = {
  populationSize: 80,
  tournamentK: 3,
  crossoverProb: 0.8,
  mutationProb: 0.05,   // probabilidad por peso
  mutationSigma: 0.2,
  elitism: 2,
};

// Limites para los sliders.
export const HYPER_LIMITS = {
  populationSize: { min: 20, max: 200, step: 10 },
  tournamentK:    { min: 2,  max: 7,   step: 1 },
  crossoverProb:  { min: 0,  max: 1,   step: 0.05 },
  mutationProb:   { min: 0,  max: 0.5, step: 0.01 },
  mutationSigma:  { min: 0.05, max: 0.8, step: 0.05 },
  elitism:        { min: 0,  max: 10,  step: 1 },
};
