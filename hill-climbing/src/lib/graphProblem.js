// Problema tipo grafo / TSP.
// Busca la ruta con menor costo total.
// Los vecinos son intercambios de dos posiciones.

// Matriz base de 5 nodos.
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

// Costo total de la ruta cerrada.
export function routeCost(route, costs) {
  let total = 0;
  for (let i = 0; i < route.length - 1; i++) {
    total += costs[route[i]][route[i + 1]];
  }
  total += costs[route[route.length - 1]][route[0]]; // regreso
  return total;
}

// Todos los vecinos por intercambio.
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

// Construye el problema para el motor genérico.
export function makeGraphProblem(graph = DEFAULT_GRAPH, startRoute = null) {
  const initial = startRoute || graph.labels.map((_, i) => i);
  function cost(route) {
    return routeCost(route, graph.costs);
  }

  return {
    initial,
    cost,
    neighbors: swapNeighbors,
    minimize: true,
  };
}
