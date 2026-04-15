/**
 * Steepest-Ascent/Descent Hill Climbing
 *
 * Generic engine — receives a problem definition object:
 *   { initial, cost(state), neighbors(state), minimize }
 *
 * Returns the full search tree and the path chosen.
 */
export function hillClimbing({ initial, cost, neighbors, minimize = true }) {
  const better = minimize ? (a, b) => a < b : (a, b) => a > b;

  const rootCost = cost(initial);
  const tree = [];          // every iteration's expansion
  const path = [{ state: initial, cost: rootCost }];

  let current = initial;
  let currentCost = rootCost;

  while (true) {
    const nbrs = neighbors(current);
    const evaluated = nbrs.map(s => ({ state: s, cost: cost(s) }));

    // find the steepest neighbor
    let best = null;
    for (const n of evaluated) {
      if (!best || better(n.cost, best.cost)) best = n;
    }

    tree.push({
      parent: { state: current, cost: currentCost },
      children: evaluated,
      chosen: best,
    });

    // stop at local optimum
    if (!best || !better(best.cost, currentCost)) break;

    current = best.state;
    currentCost = best.cost;
    path.push({ state: current, cost: currentCost });
  }

  return { path, tree, finalCost: currentCost };
}
