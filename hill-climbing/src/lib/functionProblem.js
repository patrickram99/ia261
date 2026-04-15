/**
 * Simple 1-D function maximization.
 * f(x) = -(x-3)^2 + 25   (parabola, max at x=3, f(3)=25)
 * Domain: integers in [0, 10]. Neighbors: x-1, x+1.
 */

export const F_LABEL = 'f(x) = -(x-3)² + 25';

export function f(x) {
  return -((x - 3) ** 2) + 25;
}

export function makeFunctionProblem(start = 0) {
  return {
    initial: start,
    cost: f,
    neighbors: (x) => [x - 1, x + 1].filter(v => v >= 0 && v <= 10),
    minimize: false, // maximize
  };
}
