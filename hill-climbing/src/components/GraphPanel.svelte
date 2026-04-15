<script>
  import { hillClimbing } from '../lib/hillClimbing.js';
  import { DEFAULT_GRAPH, makeGraphProblem } from '../lib/graphProblem.js';
  import TreeVisualizer from './TreeVisualizer.svelte';

  const graph = DEFAULT_GRAPH;

  let startRoute = $state([...graph.labels.map((_, i) => i)]);
  let result = $state(null);

  function shuffle() {
    const arr = [...startRoute];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    startRoute = arr;
    result = null;
  }

  function run() {
    const problem = makeGraphProblem(graph, [...startRoute]);
    result = hillClimbing(problem);
  }

  function fmt(route) {
    return route.map(i => graph.labels[i]).join('');
  }

  function fmtLong(route) {
    return route.map(i => graph.labels[i]).join('-');
  }
</script>

<section class="panel">
  <header>
    <h2>Problema de Grafo</h2>
    <p class="subtitle">Encuentra la ruta de menor costo (swap-2 vecinos)</p>
  </header>

  <!-- cost matrix -->
  <div class="matrix-wrap">
    <table class="matrix">
      <thead>
        <tr>
          <th></th>
          {#each graph.labels as l}<th>{l}</th>{/each}
        </tr>
      </thead>
      <tbody>
        {#each graph.costs as row, i}
          <tr>
            <th>{graph.labels[i]}</th>
            {#each row as c, j}
              <td class:diag={i === j}>{c}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <div class="controls">
    <div class="route-display">
      <span class="label">Ruta inicial:</span>
      <code>{fmtLong(startRoute)}</code>
    </div>
    <div class="btn-group">
      <button onclick={shuffle}>Aleatorizar</button>
      <button class="primary" onclick={run}>Ejecutar</button>
    </div>
  </div>

  {#if result}
    <div class="result-bar">
      <span>Ruta final: <strong>{fmtLong(result.path[result.path.length - 1].state)}</strong></span>
      <span class="badge">Costo: {result.finalCost}</span>
    </div>

    <TreeVisualizer
      tree={result.tree}
      path={result.path}
      formatState={fmt}
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

  /* matrix */
  .matrix-wrap { overflow-x: auto; }
  .matrix {
    border-collapse: collapse;
    font-size: 0.8rem;
    margin: 0 auto;
    font-variant-numeric: tabular-nums;
  }
  .matrix th {
    padding: 6px 14px;
    font-weight: 600;
    color: #6366f1;
    background: #f5f3ff;
  }
  .matrix td {
    padding: 6px 14px;
    text-align: center;
    border: 1px solid #e5e7eb;
    color: #374151;
  }
  .diag { background: #f3f4f6; color: #9ca3af; }

  /* controls */
  .controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }
  .route-display {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
  }
  .route-display .label { color: #6b7280; }
  .route-display code {
    background: #f3f4f6;
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: #1f2937;
  }

  .btn-group { display: flex; gap: 8px; }
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
  button:hover { background: #f9fafb; border-color: #9ca3af; }
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
