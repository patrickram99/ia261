<script>
  import { onMount, onDestroy } from 'svelte';
  import { NN_LAYERS, forwardArgmax, serialize } from '../lib/neuralNet.js';
  import {
    WORLD,
    createWorld,
    stepWorld,
    createDino,
    stepDino,
    observe,
  } from '../lib/dinoGame.js';
  import {
    initPopulation,
    nextGeneration,
    diversity,
  } from '../lib/geneticAlgorithm.js';
  import { DEFAULT_HYPER, HYPER_LIMITS } from '../lib/presets.js';
  import FitnessChart from './FitnessChart.svelte';

  // Hiperparametros reactivos (bindeados a sliders).
  let popSize = $state(DEFAULT_HYPER.populationSize);
  let tournamentK = $state(DEFAULT_HYPER.tournamentK);
  let crossoverProb = $state(DEFAULT_HYPER.crossoverProb);
  let mutationProb = $state(DEFAULT_HYPER.mutationProb);
  let mutationSigma = $state(DEFAULT_HYPER.mutationSigma);
  let elitism = $state(DEFAULT_HYPER.elitism);

  // Velocidad de simulacion: 1, 2, 5, 10, o "turbo" (sin render).
  let speed = $state(1);

  // Estado del entrenamiento.
  let running = $state(false);
  let generation = $state(0);
  let aliveCount = $state(0);
  let bestFitness = $state(0);
  let avgFitness = $state(0);
  let populationDiversity = $state(0);
  let history = $state([]);          // [{ gen, best, avg, div }]
  let bestGenomeEver = $state(null); // mejor de TODA la corrida
  let bestFitnessEver = $state(0);

  let canvas = $state(null);
  let ctx = null;

  // Sprite del dino (carga desde /public/dino.ico). Si no carga, hay fallback poligonal.
  let dinoImg = null;
  let dinoImgReady = false;

  // Estructuras internas (no reactivas para evitar overhead).
  let population = null;
  let dinos = null;
  let world = null;
  let seed = 0;
  let rafId = null;

  onMount(() => {
    ctx = canvas.getContext('2d');

    // Cargar el sprite del dino. Si falla (404 o formato incompatible)
    // se usa el dibujo poligonal como fallback.
    const img = new Image();
    img.onload = () => {
      dinoImg = img;
      dinoImgReady = true;
      drawFrame();
    };
    img.onerror = () => {
      dinoImg = null;
      dinoImgReady = false;
    };
    img.src = '/dino.ico';

    resetAll();
    drawFrame();
  });

  onDestroy(() => {
    if (rafId) cancelAnimationFrame(rafId);
  });

  function resetAll() {
    cancelLoop();
    running = false;
    generation = 0;
    bestFitness = 0;
    avgFitness = 0;
    populationDiversity = 0;
    history = [];
    bestGenomeEver = null;
    bestFitnessEver = 0;
    population = initPopulation(popSize);
    startGeneration();
    drawFrame();
  }

  function startGeneration() {
    seed = (Math.random() * 2 ** 31) | 0;
    world = createWorld(seed);
    dinos = population.map((w, i) => createDino(w, i));
    aliveCount = dinos.length;
  }

  // Avanza un frame del mundo y de todos los dinos vivos.
  function tickFrame() {
    stepWorld(world);
    let alive = 0;
    for (const d of dinos) {
      if (!d.alive) continue;
      const obs = observe(world, d);
      const action = forwardArgmax(d.weights, obs);
      stepDino(world, d, action);
      if (d.alive) alive++;
    }
    aliveCount = alive;
    return alive;
  }

  // Termina la generacion: calcula fitness, llama al GA, arranca la siguiente.
  function finishGeneration() {
    const fits = dinos.map(d => d.fitness);
    const div = diversity(population);
    const result = nextGeneration(population, fits, {
      tournamentK,
      crossoverProb,
      mutationProb,
      mutationSigma,
      elitism,
    });
    population = result.population;
    bestFitness = result.bestFitness;
    avgFitness = result.avgFitness;
    populationDiversity = div;

    if (result.bestFitness > bestFitnessEver) {
      bestFitnessEver = result.bestFitness;
      bestGenomeEver = result.bestGenome;
    }

    history = [
      ...history,
      { gen: generation, best: result.bestFitness, avg: result.avgFitness, div },
    ].slice(-200); // limitar tamaño

    generation++;
    startGeneration();
  }

  // Si el usuario cambio el tamaño de poblacion, lo aplicamos en el siguiente reset.
  function applyPopSize() {
    if (population && population.length !== popSize) {
      // recortar o extender (con Xavier) para no perder progreso completo.
      if (popSize < population.length) {
        // mantener los primeros (suelen ser los de mayor fitness recientes).
        population = population.slice(0, popSize);
      } else {
        const extra = initPopulation(popSize - population.length);
        population = [...population, ...extra];
      }
    }
  }

  function loop() {
    if (!running) return;

    if (speed === 'turbo') {
      // Sin render. Ejecutar tantas generaciones como entren en ~30ms.
      const t0 = performance.now();
      while (performance.now() - t0 < 30) {
        while (tickFrame() > 0 && world.frame < WORLD.frameCap) {}
        finishGeneration();
        applyPopSize();
      }
    } else {
      // Avanzar 'speed' frames por animation frame.
      const steps = speed;
      for (let s = 0; s < steps; s++) {
        const alive = tickFrame();
        if (alive === 0) {
          finishGeneration();
          applyPopSize();
          break;
        }
      }
      drawFrame();
    }

    rafId = requestAnimationFrame(loop);
  }

  function start() {
    if (running) return;
    running = true;
    rafId = requestAnimationFrame(loop);
  }

  function pause() {
    running = false;
    cancelLoop();
    drawFrame();
  }

  function cancelLoop() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  function downloadBest() {
    const genome = bestGenomeEver || (population && population[0]);
    if (!genome) return;
    const json = serialize(genome, {
      fitness: bestFitnessEver,
      generation,
      timestamp: new Date().toISOString(),
    });
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dino-genome-gen${generation}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ----- RENDER -----

  function drawFrame() {
    if (!ctx) return;
    const W = WORLD.width;
    const H = WORLD.height;
    ctx.clearRect(0, 0, W, H);

    // cielo
    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, '#eef2ff');
    grd.addColorStop(1, '#f8fafc');
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    // suelo
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(0, WORLD.groundY);
    ctx.lineTo(W, WORLD.groundY);
    ctx.stroke();

    // marcas de suelo (pseudo-piedras), se desplazan con la distancia
    ctx.fillStyle = '#cbd5e1';
    const off = (world ? world.distance : 0) % 40;
    for (let x = -off; x < W; x += 40) {
      ctx.fillRect(x, WORLD.groundY + 6, 12, 2);
    }

    if (!world || !dinos) return;

    // obstaculos
    for (const o of world.obstacles) {
      if (o.x > W) break;
      if (o.x + o.w < 0) continue;
      drawObstacle(o);
    }

    // dinos vivos (semi-transparentes) + lider (opaco)
    let leader = null;
    for (const d of dinos) {
      if (!d.alive) continue;
      if (!leader || d.fitness > leader.fitness) leader = d;
    }
    for (const d of dinos) {
      if (!d.alive) continue;
      drawDino(d, d === leader);
    }

    // overlay
    ctx.fillStyle = 'rgba(17, 24, 39, 0.78)';
    ctx.fillRect(8, 8, 200, 64);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 11px Inter, system-ui';
    ctx.textAlign = 'left';
    ctx.fillText(`Generacion: ${generation}`, 16, 24);
    ctx.fillText(`Vivos: ${aliveCount} / ${dinos.length}`, 16, 40);
    ctx.fillText(`Best: ${bestFitness.toFixed(0)}  |  Avg: ${avgFitness.toFixed(0)}`, 16, 56);
    ctx.fillText(`Diversidad: ${populationDiversity.toFixed(3)}`, 16, 70);
  }

  function drawObstacle(o) {
    if (o.kind === 0 || o.kind === 1) {
      // cactus (rectangulo verde con "brazos")
      ctx.fillStyle = '#16a34a';
      ctx.fillRect(o.x, o.y, o.w, o.h);
      ctx.fillRect(o.x - 3, o.y + o.h * 0.3, 4, o.h * 0.35);
      ctx.fillRect(o.x + o.w - 1, o.y + o.h * 0.45, 4, o.h * 0.3);
    } else {
      // pajaro (rombo gris con alas)
      ctx.fillStyle = '#475569';
      ctx.beginPath();
      ctx.moveTo(o.x + o.w / 2, o.y);
      ctx.lineTo(o.x + o.w, o.y + o.h / 2);
      ctx.lineTo(o.x + o.w / 2, o.y + o.h);
      ctx.lineTo(o.x, o.y + o.h / 2);
      ctx.closePath();
      ctx.fill();
      // alas
      ctx.fillRect(o.x - 6, o.y + o.h / 2 - 1, 6, 3);
      ctx.fillRect(o.x + o.w, o.y + o.h / 2 - 1, 6, 3);
    }
  }

  // Dibuja un dino. Si el sprite cargo, usa la imagen; si no, fallback poligonal.
  // El "lider" se ve opaco con halo; el resto se ve translucido para visualizar
  // toda la poblacion corriendo en paralelo.
  function drawDino(d, isLeader) {
    const x = WORLD.dinoX;
    const y = d.y;
    const w = WORLD.dinoW;
    const h = d.h;

    ctx.save();

    if (dinoImgReady && dinoImg) {
      // Halo indigo detras del lider para destacarlo entre la masa.
      if (isLeader) {
        ctx.fillStyle = 'rgba(99, 102, 241, 0.35)';
        ctx.beginPath();
        ctx.ellipse(x + w / 2, y + h / 2, w * 0.85, h * 0.65, 0, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = isLeader ? 1 : 0.22;
      // imageSmoothingEnabled = false ayuda con sprites pequeños (mantiene pixel art crisp).
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(dinoImg, x, y, w, h);
    } else {
      // Fallback: dibujo poligonal original.
      if (isLeader) {
        ctx.fillStyle = '#6366f1';
        ctx.strokeStyle = '#312e81';
        ctx.lineWidth = 1.5;
      } else {
        ctx.fillStyle = 'rgba(99, 102, 241, 0.18)';
        ctx.strokeStyle = 'rgba(49, 46, 129, 0.25)';
        ctx.lineWidth = 1;
      }
      ctx.beginPath();
      ctx.moveTo(x, y + h * 0.4);
      ctx.lineTo(x + w * 0.2, y + h * 0.1);
      ctx.lineTo(x + w * 0.85, y + h * 0.05);
      ctx.lineTo(x + w, y + h * 0.5);
      ctx.lineTo(x + w * 0.9, y + h);
      ctx.lineTo(x + w * 0.1, y + h);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, y + h * 0.4);
      ctx.lineTo(x - 8, y + h * 0.25);
      ctx.lineTo(x, y + h * 0.6);
      ctx.closePath();
      ctx.fill();
      const hx = x + w * 0.78;
      const hy = y + (d.ducking ? h * 0.1 : -h * 0.15);
      ctx.fillRect(hx, hy, w * 0.35, h * 0.35);
      if (isLeader) {
        ctx.fillStyle = '#fff';
        ctx.fillRect(hx + w * 0.18, hy + h * 0.08, 3, 3);
      }
    }
    ctx.restore();
  }
</script>

<div class="layout">
  <!-- pista -->
  <div class="track">
    <canvas bind:this={canvas} width={WORLD.width} height={WORLD.height}></canvas>
    <div class="track-controls">
      {#if !running}
        <button class="primary" onclick={start}>Iniciar</button>
      {:else}
        <button class="warn" onclick={pause}>Pausar</button>
      {/if}
      <button onclick={resetAll}>Reset</button>
      <div class="speed-group">
        <span>Velocidad:</span>
        {#each [1, 2, 5, 10, 'turbo'] as s}
          <button
            class:active={speed === s}
            onclick={() => (speed = s)}
            class="speed-btn"
          >{s === 'turbo' ? 'Turbo' : s + 'x'}</button>
        {/each}
      </div>
      <button class="ghost" onclick={downloadBest} disabled={!bestGenomeEver}>
        Descargar mejor genoma
      </button>
    </div>
  </div>

  <!-- panel de sliders -->
  <div class="sliders">
    <h3>Hiperparametros</h3>

    <div class="slider">
      <label>Tamaño poblacion <code>{popSize}</code></label>
      <input
        type="range"
        min={HYPER_LIMITS.populationSize.min}
        max={HYPER_LIMITS.populationSize.max}
        step={HYPER_LIMITS.populationSize.step}
        bind:value={popSize}
      />
      <small>Mas grande = mas diversidad, mas lento.</small>
    </div>

    <div class="slider">
      <label>Tamaño torneo k <code>{tournamentK}</code></label>
      <input
        type="range"
        min={HYPER_LIMITS.tournamentK.min}
        max={HYPER_LIMITS.tournamentK.max}
        step={HYPER_LIMITS.tournamentK.step}
        bind:value={tournamentK}
      />
      <small>Alto = intensificacion (presion selectiva fuerte).</small>
    </div>

    <div class="slider">
      <label>Prob. crossover <code>{crossoverProb.toFixed(2)}</code></label>
      <input
        type="range"
        min={HYPER_LIMITS.crossoverProb.min}
        max={HYPER_LIMITS.crossoverProb.max}
        step={HYPER_LIMITS.crossoverProb.step}
        bind:value={crossoverProb}
      />
      <small>Frecuencia de combinar pesos de 2 padres.</small>
    </div>

    <div class="slider">
      <label>Prob. mutacion (por peso) <code>{mutationProb.toFixed(2)}</code></label>
      <input
        type="range"
        min={HYPER_LIMITS.mutationProb.min}
        max={HYPER_LIMITS.mutationProb.max}
        step={HYPER_LIMITS.mutationProb.step}
        bind:value={mutationProb}
      />
      <small>Alta = diversificacion, baja = intensificacion.</small>
    </div>

    <div class="slider">
      <label>σ mutacion gaussiana <code>{mutationSigma.toFixed(2)}</code></label>
      <input
        type="range"
        min={HYPER_LIMITS.mutationSigma.min}
        max={HYPER_LIMITS.mutationSigma.max}
        step={HYPER_LIMITS.mutationSigma.step}
        bind:value={mutationSigma}
      />
      <small>Magnitud del salto al mutar un peso.</small>
    </div>

    <div class="slider">
      <label>Elitismo <code>{elitism}</code></label>
      <input
        type="range"
        min={HYPER_LIMITS.elitism.min}
        max={HYPER_LIMITS.elitism.max}
        step={HYPER_LIMITS.elitism.step}
        bind:value={elitism}
      />
      <small>Garantiza que el mejor nunca empeore.</small>
    </div>
  </div>
</div>

<div class="chart-block">
  <h3>Fitness por generacion</h3>
  <FitnessChart {history} />
</div>

<style>
  .layout {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 20px;
    margin-bottom: 20px;
  }
  @media (max-width: 880px) {
    .layout { grid-template-columns: 1fr; }
  }

  .track canvas {
    width: 100%;
    height: auto;
    max-width: 800px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    background: #fff;
    display: block;
  }

  .track-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-top: 12px;
  }
  .track-controls button {
    padding: 7px 14px;
    border: 1px solid #e5e7eb;
    background: #fff;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.8rem;
    color: #374151;
  }
  .track-controls button.primary {
    background: #6366f1; color: #fff; border-color: #6366f1;
  }
  .track-controls button.warn {
    background: #f59e0b; color: #fff; border-color: #f59e0b;
  }
  .track-controls button.ghost {
    background: #f1f5f9; color: #475569; border: none; margin-left: auto;
  }
  .track-controls button:disabled { opacity: 0.5; cursor: not-allowed; }

  .speed-group {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: 8px;
    font-size: 0.75rem;
    color: #64748b;
  }
  .speed-btn { padding: 5px 9px !important; font-size: 0.72rem !important; }
  .speed-btn.active {
    background: #6366f1 !important; color: #fff !important; border-color: #6366f1 !important;
  }

  .sliders {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .sliders h3 {
    font-size: 0.85rem;
    color: #334155;
    margin-bottom: 4px;
  }
  .slider label {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 4px;
  }
  .slider code {
    background: #e0e7ff;
    color: #4338ca;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
  }
  .slider input[type=range] {
    width: 100%;
    accent-color: #6366f1;
  }
  .slider small {
    font-size: 0.68rem;
    color: #94a3b8;
    margin-top: 2px;
    display: block;
  }

  .chart-block {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
  }
  .chart-block h3 {
    font-size: 0.85rem;
    color: #334155;
    margin-bottom: 12px;
  }
</style>
