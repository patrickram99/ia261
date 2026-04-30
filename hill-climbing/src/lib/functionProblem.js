// Maximización de una función simple en 1D.
// f(x) = -(x-3)^2 + 25.
// Dominio entero de 0 a 10.

export const F_LABEL = 'f(x) = -(x-3)² + 25';

export function f(x) {
  return -((x - 3) ** 2) + 25;
}

export function makeFunctionProblem(start = 0) {
  function neighbors(x) {
    const result = [];
    const left = x - 1;
    const right = x + 1;

    if (left >= 0 && left <= 10) {
      result.push(left);
    }

    if (right >= 0 && right <= 10) {
      result.push(right);
    }

    return result;
  }

  return {
    initial: start,
    cost: f,
    neighbors,
    minimize: false, // maximizar
  };
}
