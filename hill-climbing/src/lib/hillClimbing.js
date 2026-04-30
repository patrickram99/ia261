// @ts-nocheck
// Motor genérico de hill climbing por ascenso/descenso más pronunciado.
export function hillClimbing({ initial, cost, neighbors, minimize = true }) {
  // Comparación para modo de minimización.
  function betterForMin(a, b) {
    return a < b;
  }

  // Comparación para modo de maximización.
  function betterForMax(a, b) {
    return a > b;
  }

  const better = minimize ? betterForMin : betterForMax;

  const rootCost = cost(initial);
  const tree = [];          // expansión de cada iteración
  const path = [{ state: initial, cost: rootCost }];

  let current = initial;
  let currentCost = rootCost;

  while (true) {
    const nbrs = neighbors(current);
    const evaluated = [];
    for (const s of nbrs) {
      evaluated.push({ state: s, cost: cost(s) });
    }

    // Buscar el vecino más prometedor.
    let best = null;
    for (const n of evaluated) {
      if (!best || better(n.cost, best.cost)) best = n;
    }

    tree.push({
      parent: { state: current, cost: currentCost },
      children: evaluated,
      chosen: best,
    });

    // Detenerse en el óptimo local.
    if (!best || !better(best.cost, currentCost)) break;

    current = best.state;
    currentCost = best.cost;
    path.push({ state: current, cost: currentCost });
  }

  return { path, tree, finalCost: currentCost };
}
