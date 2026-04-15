<script>
  import { hillClimbing } from '../lib/hillClimbing.js';
  import { makeFunctionProblem, f, F_LABEL } from '../lib/functionProblem.js';
  import TreeVisualizer from './TreeVisualizer.svelte';

  let start = $state(0);
  let result = $state(null);

  function run() {
    result = hillClimbing(makeFunctionProblem(start));
  }
</script>

<section class="panel">
  <header>
    <h2>Funcion Matematica</h2>
    <p class="subtitle">Maximizar {F_LABEL} &mdash; dominio entero [0, 10]</p>
  </header>

  <!-- f(x) bar chart -->
  <div class="chart">
    {#each Array(11) as _, x}
      {@const val = f(x)}
      {@const h = Math.max(0, val + 10)}
      <div class="bar-col">
        <span class="bar-val">{val}</span>
        <div class="bar" style="height:{h * 2.5}px"
             class:highlight={result && result.path[result.path.length - 1].state === x}
        ></div>
        <span class="bar-lbl">{x}</span>
      </div>
    {/each}
  </div>

  <div class="controls">
    <label class="slider-label">
      x inicial =
      <input type="range" min="0" max="10" bind:value={start} />
      <code>{start}</code>
    </label>
    <button class="primary" onclick={run}>Ejecutar</button>
  </div>

  {#if result}
    <div class="result-bar">
      <span>Optimo encontrado: <strong>x = {result.path[result.path.length - 1].state}</strong></span>
      <span class="badge">f(x) = {result.finalCost}</span>
    </div>

    <TreeVisualizer
      tree={result.tree}
      path={result.path}
      formatState={(x) => `x=${x}`}
    />
  {/if}
</section>

<style>
  .panel { display: flex; flex-direction: column; gap: 20px; }

  header h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
    margin: 0;
  }
  .subtitle {
    color: #6b7280;
    font-size: 0.85rem;
    margin: 2px 0 0;
  }

  /* bar chart */
  .chart {
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 6px;
    padding: 12px 0;
  }
  .bar-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
  .bar {
    width: 30px;
    background: #e0e7ff;
    border-radius: 6px 6px 0 0;
    transition: all 0.3s;
  }
  .bar.highlight { background: #6366f1; }
  .bar-val { font-size: 0.65rem; color: #9ca3af; }
  .bar-lbl { font-size: 0.7rem; color: #6b7280; font-weight: 600; }

  /* controls */
  .controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }
  .slider-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    color: #374151;
  }
  .slider-label code {
    background: #f3f4f6;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
  }
  input[type="range"] {
    accent-color: #6366f1;
  }
  button {
    padding: 8px 18px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background: #fff;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    color: #374151;
  }
  button.primary {
    background: #6366f1;
    color: #fff;
    border-color: #6366f1;
  }
  button.primary:hover { background: #4f46e5; }

  /* result */
  .result-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    font-size: 0.875rem;
    color: #166534;
  }
  .badge {
    background: #16a34a;
    color: #fff;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }
</style>
