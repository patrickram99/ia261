# Dino GA — Neuroevolución con Algoritmo Genético

Algoritmo genético que entrena una red neuronal para jugar **Dino Runner**. Curso IA261.

## Integrantes

- Patrick Andres Ramirez Santos
- Maria Fernanda Adira Pinazo Vera
- Rodrigo Cesar Ancori Tacca

## Cómo correr

```bash
npm install
npm run dev
```

Abrir la URL que muestra Vite (típicamente `http://localhost:5173`).

---

## Lenguaje utilizado

Se eligió **JavaScript (Svelte + Vite)** porque la consigna permite cualquier lenguaje y JS corre nativo en el navegador: se puede **visualizar la simulación en tiempo real** (canvas), graficar el fitness por generación y compartir el resultado sin instalar nada. Toda la lógica del GA y la red neuronal está escrita a mano, sin librerías de ML.

## Formulación del problema

- **Problema:** un agente debe sobrevivir el mayor tiempo posible esquivando cactus y pájaros en el Dino Runner.
- **Solución (individuo):** una **red neuronal MLP fija** de arquitectura `5 → 6 → 3` (tanh oculto, argmax en la salida). El **genoma** es el vector plano de **todos los pesos y sesgos** como `Float32Array`. No hay topología variable: el GA solo optimiza pesos (neuroevolución de pesos).
- **Entradas (5):** distancia al próximo obstáculo, ancho y alto del obstáculo, altura del dino sobre el suelo, velocidad del juego — todas normalizadas a `[0,1]`.
- **Salidas (3):** `nada / saltar / agacharse` (argmax sobre los logits).
- **Fitness:** `framesAlive + 50 · obstáculosEsquivados − 0.1 · saltosInútiles`.
  - El término de frames recompensa sobrevivir.
  - El bono por obstáculos esquivados evita que el GA se quede en óptimos locales triviales (quedarse quieto).
  - La penalización por saltos inútiles desincentiva la política "saltar siempre".
- **Fairness:** todos los individuos de una misma generación juegan **exactamente la misma secuencia de obstáculos** (PRNG mulberry32 con seed fija por generación). Así el fitness es comparable entre individuos.

## Operadores del GA y fundamentación

Implementados en [src/lib/geneticAlgorithm.js](src/lib/geneticAlgorithm.js).

| Etapa | Método elegido | Por qué |
|---|---|---|
| **Inicialización** | **Xavier/Glorot** `N(0, √(2/fan_in))` | Mantiene la varianza de las activaciones en rangos útiles para `tanh` (no se satura) y da diversidad genética desde la generación 0 sin caos extremo. Mejor que `U(-1,1)` que tiende a saturar `tanh`. |
| **Selección** | **Torneo de tamaño k** | No requiere normalizar fitness (a diferencia de la ruleta, que falla con fitness negativos o muy dispares). Con un solo parámetro `k` se regula la presión selectiva: `k=2` favorece exploración, `k=7` favorece explotación. |
| **Crossover** | **Uniforme por gen** | En neuroevolución los pesos **no tienen orden semántico** (no es una ruta TSP donde la posición importa). El crossover de 1 punto introduce un sesgo posicional artificial; el uniforme trata cada peso como un gen independiente y mezcla mejor "subredes" de ambos padres. |
| **Mutación** | **Gaussiana por peso** con `σ` ajustable | Para genomas reales es el estándar. `σ` chico → ajustes finos (intensificación local); `σ` grande → saltos largos (diversificación). La probabilidad por peso (no por individuo) evita destruir hijos enteros. |
| **Reemplazo** | **Generacional con elitismo** | El elitismo garantiza que el mejor fitness **nunca empeore** entre generaciones. Sin él, una mala generación puede perder a la mejor solución por azar. |

## Problemas enfrentados: intensificación vs diversificación

Durante el desarrollo aparecieron los dos problemas clásicos del GA:

1. **Convergencia prematura (poca diversificación).**
   La población colapsaba en generaciones tempranas: todos los dinos aprendían a "saltar siempre" y se estancaban. Lo detectamos midiendo la **desviación estándar promedio por gen** (ver `diversity()` en `geneticAlgorithm.js`) y observando que caía a casi cero.
   **Mitigación:**
   - Reducir `k` del torneo (de 7 a 3–4) → menos presión selectiva.
   - Subir `σ` de la mutación (de 0.05 a 0.15–0.25) → saltos más amplios.
   - Mantener elitismo bajo (1–2 individuos) → el resto de la población explora.
   - Penalizar saltos inútiles en el fitness → rompe el atractor "saltar siempre".

2. **Falta de explotación (mucho ruido, no afina).**
   Con `σ` alta y `k` baja, los buenos individuos no llegaban a refinarse: la mutación destruía sus pesos. El mejor fitness oscilaba sin tendencia clara.
   **Mitigación:**
   - Subir `k` del torneo cuando se ve estancamiento → presión selectiva más fuerte.
   - Bajar `σ` gradualmente conforme avanza el entrenamiento (estrategia tipo simulated annealing aplicada a la mutación).
   - Aumentar elitismo a 2–3 → preservar a los mejores mientras el resto explora.

La UI expone estos hiperparámetros (`tournamentK`, `mutationSigma`, `mutationProb`, `elitism`, `crossoverProb`) para poder **balancear exploración/explotación en vivo** durante la corrida y ver el efecto en el gráfico de fitness.

## Estructura del proyecto

```
src/
├── lib/
│   ├── neuralNet.js          # MLP, Xavier, forward pass
│   ├── geneticAlgorithm.js   # Operadores del GA
│   ├── dinoGame.js           # Motor del juego (física, obstáculos, fitness)
│   └── presets.js            # Conjuntos de hiperparámetros sugeridos
├── components/               # UI (Svelte): entrenamiento, demo, gráficos
└── App.svelte
```
