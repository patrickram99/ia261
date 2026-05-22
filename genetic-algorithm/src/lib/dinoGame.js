// @ts-nocheck
// Motor del juego "Dino Runner" en 2D. Diseñado para correr cientos de
// individuos en paralelo sobre la MISMA secuencia de obstaculos (misma seed).

// Dimensiones de la pista (en pixeles del canvas).
export const WORLD = {
  width: 800,
  height: 240,
  groundY: 200,         // y del suelo
  dinoX: 80,            // x fijo del dino
  dinoW: 28,
  dinoH: 40,
  duckH: 24,            // alto cuando se agacha
  gravity: 0.7,
  jumpV: -13.5,         // velocidad vertical inicial al saltar
  vBase: 6,             // velocidad inicial del juego (px/frame)
  vMax: 14,             // velocidad maxima
  vAccel: 0.0015,       // aceleracion por frame
  obstacleMinGap: 230,
  obstacleMaxGap: 480,
  frameCap: 10000,
};

// Generador pseudoaleatorio determinista (mulberry32) para que toda la poblacion
// vea EXACTAMENTE la misma secuencia de obstaculos en una generacion -> fairness.
export function makeRng(seed) {
  let s = seed >>> 0;
  return function rng() {
    s |= 0; s = (s + 0x6D2B79F5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Crea un obstaculo: cactus bajo (tipo 0), cactus alto (1), o pajaro (2).
// El pajaro vuela a alturas variables (bajo -> hay que agacharse).
function spawnObstacle(x, rng) {
  const r = rng();
  if (r < 0.45) {
    return { kind: 0, x, y: WORLD.groundY - 28, w: 16, h: 28 };
  } else if (r < 0.8) {
    return { kind: 1, x, y: WORLD.groundY - 44, w: 22, h: 44 };
  } else {
    // pajaro: altura variable. Si es bajo -> agacharse.
    const lowFlying = rng() < 0.5;
    const birdH = 18;
    const y = lowFlying ? WORLD.groundY - 24 : WORLD.groundY - 60;
    return { kind: 2, x, y, w: 30, h: birdH };
  }
}

// Estado del juego compartido entre todos los dinos de una generacion.
export function createWorld(seed) {
  const rng = makeRng(seed);
  const obstacles = [];
  // Pre-generamos una secuencia larga (por si la simulacion dura mucho).
  let x = WORLD.width + 100;
  for (let i = 0; i < 200; i++) {
    obstacles.push(spawnObstacle(x, rng));
    x += WORLD.obstacleMinGap + rng() * (WORLD.obstacleMaxGap - WORLD.obstacleMinGap);
  }
  return {
    frame: 0,
    speed: WORLD.vBase,
    distance: 0,       // suma de speed por frame -> usado para mover obstaculos
    obstacles,
  };
}

// Avanza el mundo (no a los dinos): mueve obstaculos hacia la izquierda y acelera.
export function stepWorld(world) {
  world.frame++;
  world.speed = Math.min(WORLD.vMax, world.speed + WORLD.vAccel);
  world.distance += world.speed;
  for (const o of world.obstacles) o.x -= world.speed;
}

// Crea un dino vivo con su genoma asociado.
export function createDino(weightsRef, id) {
  return {
    id,
    weights: weightsRef,
    alive: true,
    y: WORLD.groundY - WORLD.dinoH,
    vy: 0,
    ducking: false,
    onGround: true,
    h: WORLD.dinoH,
    framesAlive: 0,
    obstaclesCleared: 0,
    nextObstIdx: 0,
    wastedJumps: 0,
    fitness: 0,
  };
}

// Devuelve el primer obstaculo aun NO superado (su borde derecho a la derecha del dino).
function nextObstacle(world, dino) {
  while (dino.nextObstIdx < world.obstacles.length) {
    const o = world.obstacles[dino.nextObstIdx];
    if (o.x + o.w >= WORLD.dinoX) return o;
    // este ya quedo atras -> dino lo paso
    dino.obstaclesCleared++;
    dino.nextObstIdx++;
  }
  return null;
}

// Observacion normalizada que se le entrega a la red neuronal.
export function observe(world, dino) {
  const o = nextObstacle(world, dino);
  if (!o) {
    return new Float32Array([1, 0, 0, (WORLD.groundY - dino.h - dino.y) / 200, world.speed / WORLD.vMax]);
  }
  const dist = Math.max(0, o.x - WORLD.dinoX);
  return new Float32Array([
    Math.min(1, dist / 500),                       // distancia horizontal normalizada
    o.w / 40,                                      // ancho
    o.h / 60,                                      // alto
    (WORLD.groundY - dino.h - dino.y) / 200,       // altura del dino sobre el suelo
    world.speed / WORLD.vMax,                      // velocidad del juego
  ]);
}

// Aplica una accion al dino y luego avanza la fisica de UN frame.
// action: 0=nada, 1=saltar, 2=agacharse
export function stepDino(world, dino, action) {
  if (!dino.alive) return;
  // Reset agachado al final del frame anterior.
  dino.ducking = false;
  dino.h = WORLD.dinoH;

  if (action === 1 && dino.onGround) {
    dino.vy = WORLD.jumpV;
    dino.onGround = false;
  } else if (action === 2 && dino.onGround) {
    dino.ducking = true;
    dino.h = WORLD.duckH;
  }

  // Penalizar saltos "inutiles": si salta pero no hay obstaculo cerca.
  if (action === 1 && dino.onGround === false && dino.vy === WORLD.jumpV) {
    const o = nextObstacle(world, dino);
    if (!o || o.x - WORLD.dinoX > 250) dino.wastedJumps++;
  }

  // Fisica vertical.
  dino.vy += WORLD.gravity;
  dino.y += dino.vy;
  if (dino.y + dino.h >= WORLD.groundY) {
    dino.y = WORLD.groundY - dino.h;
    dino.vy = 0;
    dino.onGround = true;
  }

  dino.framesAlive++;

  // Colision: AABB del dino contra el proximo obstaculo (si esta solapando en X).
  const o = nextObstacle(world, dino);
  if (o && o.x < WORLD.dinoX + WORLD.dinoW && o.x + o.w > WORLD.dinoX) {
    const dinoTop = dino.y;
    const dinoBot = dino.y + dino.h;
    if (dinoBot > o.y && dinoTop < o.y + o.h) {
      dino.alive = false;
    }
  }

  if (dino.framesAlive >= WORLD.frameCap) {
    dino.alive = false;
  }

  // Fitness incremental: frames + bonus por obstaculos esquivados - penalizacion.
  dino.fitness = dino.framesAlive + 50 * dino.obstaclesCleared - 0.1 * dino.wastedJumps;
}
