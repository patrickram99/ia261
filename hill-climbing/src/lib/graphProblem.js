/**
 * Graph / TSP-like problem.
 * Given a cost matrix, find the route (permutation) with minimum total cost.
 * Neighbors: all possible swaps of two positions.
 */

/** Default 5-node cost matrix (symmetric) */
export const DEFAULT_GRAPH = {
  labels: ['A', 'B', 'C', 'D', 'E'],
  costs: [
    [0,  10, 15, 20, 25],
    [10,  0, 35, 25, 30],
    [15, 35,  0, 30, 20],
    [20, 25, 30,  0, 15],
    [25, 30, 20, 15,  0],
  ],
};

/** Total route cost (closed loop) */
export function routeCost(route, costs) {
  let total = 0;
  for (let i = 0; i < route.length - 1; i++) {
    total += costs[route[i]][route[i + 1]];
  }
  total += costs[route[route.length - 1]][route[0]]; // return
  return total;
}

/** All swap-2 neighbors */
export function swapNeighbors(route) {
  const result = [];
  for (let i = 0; i < route.length - 1; i++) {
    for (let j = i + 1; j < route.length; j++) {
      const copy = [...route];
      [copy[i], copy[j]] = [copy[j], copy[i]];
      result.push(copy);
    }
  }
  return result;
}

/** Build a problem definition for the generic engine */
export function makeGraphProblem(graph = DEFAULT_GRAPH, startRoute = null) {
  const initial = startRoute || graph.labels.map((_, i) => i);
  return {
    initial,
    cost: (route) => routeCost(route, graph.costs),
    neighbors: swapNeighbors,
    minimize: true,
  };
}
