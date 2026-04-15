<script>
  /** @type {{ tree: Array, path: Array, formatState: (s:any)=>string }} */
  let { tree = [], path = [], formatState = String } = $props();

  /* ── layout constants ── */
  const NW = 64;       // node width
  const NH = 38;       // node height
  const GAP_X = 6;     // horizontal gap between siblings
  const GAP_Y = 56;    // vertical gap between levels
  const PAD = 20;      // canvas padding

  /* ── compute layout ── */
  const layout = $derived.by(() => {
    if (!tree.length) return { nodes: [], edges: [], width: 0, height: 0 };

    const pathStrs = new Set(path.map(p => JSON.stringify(p.state)));
    const nodes = [];
    const edges = [];
    let uid = 0;

    // root
    const root = tree[0].parent;
    const rootId = uid++;
    nodes.push({
      id: rootId, label: formatState(root.state), cost: root.cost,
      x: 0, y: PAD,
      isPath: pathStrs.has(JSON.stringify(root.state)),
      isChosen: false, level: 0,
    });

    // map level -> parentNodeId for quick lookup
    const levelParent = [rootId];

    for (let lvl = 0; lvl < tree.length; lvl++) {
      const { children, chosen } = tree[lvl];
      const parentId = levelParent[lvl];
      const parentNode = nodes[parentId];
      const count = children.length;

      // compute children row width to center under parent
      const rowW = count * NW + (count - 1) * GAP_X;
      const startX = parentNode.x + NW / 2 - rowW / 2;
      const cy = parentNode.y + NH + GAP_Y;

      let chosenId = null;
      for (let i = 0; i < count; i++) {
        const ch = children[i];
        const cId = uid++;
        const isChosen = chosen && JSON.stringify(ch.state) === JSON.stringify(chosen.state);
        const onPath = pathStrs.has(JSON.stringify(ch.state));

        nodes.push({
          id: cId, label: formatState(ch.state), cost: ch.cost,
          x: startX + i * (NW + GAP_X), y: cy,
          isPath: onPath && isChosen,
          isChosen, level: lvl + 1,
        });

        edges.push({ from: parentId, to: cId, isPath: isChosen && onPath });
        if (isChosen) chosenId = cId;
      }

      if (chosenId !== null) levelParent[lvl + 1] = chosenId;
    }

    // normalise: shift everything so minX = PAD
    const minX = Math.min(...nodes.map(n => n.x));
    const shift = PAD - minX;
    for (const n of nodes) n.x += shift;

    const maxX = Math.max(...nodes.map(n => n.x));
    const maxY = Math.max(...nodes.map(n => n.y));

    return {
      nodes, edges,
      width: maxX + NW + PAD,
      height: maxY + NH + PAD,
    };
  });
</script>

{#if layout.nodes.length}
  <h3 class="tree-title">Arbol de busqueda</h3>
  <div class="tree-wrap">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 {layout.width} {layout.height}"
      style="min-width:{layout.width}px; height:{layout.height}px;"
    >
      <defs>
        <linearGradient id="pathGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#6366f1" />
          <stop offset="100%" stop-color="#8b5cf6" />
        </linearGradient>
      </defs>

      <!-- edges -->
      {#each layout.edges as e}
        {@const from = layout.nodes[e.from]}
        {@const to = layout.nodes[e.to]}
        <line
          x1={from.x + NW / 2} y1={from.y + NH}
          x2={to.x + NW / 2}   y2={to.y}
          class="edge" class:edge-path={e.isPath}
        />
      {/each}

      <!-- nodes -->
      {#each layout.nodes as n}
        <g class="node" class:node-path={n.isPath} class:node-chosen={n.isChosen && !n.isPath}>
          <rect x={n.x} y={n.y} width={NW} height={NH} rx="10" />
          <text x={n.x + NW / 2} y={n.y + 17} class="lbl">{n.label}</text>
          <text x={n.x + NW / 2} y={n.y + 33} class="cost">c={n.cost}</text>
        </g>
      {/each}
    </svg>
  </div>
{:else}
  <p class="empty">Ejecuta el algoritmo para ver el arbol.</p>
{/if}

<style>
  .tree-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .tree-wrap {
    overflow-x: auto;
    padding: 12px 0;
    border: 1px solid #f3f4f6;
    border-radius: 12px;
    background: #fafbfc;
  }
  svg { display: block; margin: 0 auto; }

  .edge {
    stroke: #e5e7eb;
    stroke-width: 1.5;
  }
  .edge-path {
    stroke: url(#pathGrad);
    stroke-width: 2.5;
  }

  .node rect {
    fill: #ffffff;
    stroke: #e5e7eb;
    stroke-width: 1.5;
  }
  .node-chosen rect {
    stroke: #c7d2fe;
    stroke-width: 2;
    fill: #f5f3ff;
  }
  .node-path rect {
    fill: #6366f1;
    stroke: #4f46e5;
    stroke-width: 2;
  }

  .lbl, .cost {
    text-anchor: middle;
    font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
    pointer-events: none;
  }
  .lbl { font-size: 11px; font-weight: 600; fill: #1f2937; }
  .cost { font-size: 9px; fill: #9ca3af; }

  .node-path .lbl { fill: #fff; }
  .node-path .cost { fill: #c7d2fe; }

  .empty {
    text-align: center;
    color: #9ca3af;
    padding: 48px 0;
    font-style: italic;
  }
</style>
