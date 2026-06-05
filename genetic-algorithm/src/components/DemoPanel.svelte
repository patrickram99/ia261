<script>
  import { onMount, onDestroy } from 'svelte';
  import { forwardArgmax, deserialize } from '../lib/neuralNet.js';
  import {
    WORLD,
    createWorld,
    stepWorld,
    createDino,
    stepDino,
    observe,
  } from '../lib/dinoGame.js';

  let genome = $state(null);
  let canvas = $state(null);
  let ctx = null;
  let dino = null;
  let world = null;
  let rafId = null;
  let dinoImg = null;
  let dinoImgReady = false;
  let running = $state(false);
  let score = $state(0);
  let cleared = $state(0);
  let runs = $state([]);          // historial de corridas {frames, cleared}
  let errorMsg = $state('');

  onMount(() => {
    ctx = canvas.getContext('2d');

    // Sprite del dino (mismo que en Entrenamiento).
    const img = new Image();
    img.onload = () => {
      dinoImg = img;
      dinoImgReady = true;
      if (world && dino) drawFrame();
    };
    img.onerror = () => {
      dinoImg = null;
      dinoImgReady = false;
    };
    img.src = '/dino.ico';

    drawIdle();
    loadDefaultGenome();
  });

  async function loadDefaultGenome() {
    try {
      const res = await fetch('/dino-genome-gen1.json');
      if (!res.ok) return;
      const json = await res.json();
      genome = deserialize(json);
      errorMsg = '';
      reset();
    } catch (err) {
      // Si no esta disponible, queda en idle esperando upload manual.
    }
  }

  onDestroy(() => {
    if (rafId) cancelAnimationFrame(rafId);
  });

  function onFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        genome = deserialize(reader.result);
        errorMsg = '';
        reset();
      } catch (err) {
        errorMsg = 'JSON invalido: ' + err.message;
      }
    };
    reader.readAsText(file);
  }

  function reset() {
    cancelLoop();
    running = false;
    if (!genome) return;
    const seed = (Math.random() * 2 ** 31) | 0;
    world = createWorld(seed);
    dino = createDino(genome, 0);
    score = 0;
    cleared = 0;
    drawFrame();
  }

  function start() {
    if (!genome || running) return;
    if (!world || !dino || !dino.alive) reset();
    running = true;
    rafId = requestAnimationFrame(loop);
  }

  function loop() {
    if (!running) return;
    stepWorld(world);
    const obs = observe(world, dino);
    const action = forwardArgmax(dino.weights, obs);
    stepDino(world, dino, action);
    score = dino.framesAlive;
    cleared = dino.obstaclesCleared;

    if (!dino.alive) {
      running = false;
      runs = [...runs, { frames: dino.framesAlive, cleared: dino.obstaclesCleared }].slice(-10);
      drawFrame();
      return;
    }

    drawFrame();
    rafId = requestAnimationFrame(loop);
  }

  function cancelLoop() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  function drawIdle() {
    if (!ctx) return;
    ctx.clearRect(0, 0, WORLD.width, WORLD.height);
    ctx.fillStyle = '#f1f5f9';
    ctx.fillRect(0, 0, WORLD.width, WORLD.height);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '14px Inter, system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('Carga un genoma JSON para iniciar la demo.', WORLD.width / 2, WORLD.height / 2);
  }

  function drawFrame() {
    const W = WORLD.width;
    const H = WORLD.height;
    ctx.clearRect(0, 0, W, H);

    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, '#fef3c7');
    grd.addColorStop(1, '#fef9e8');
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    // suelo
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(0, WORLD.groundY);
    ctx.lineTo(W, WORLD.groundY);
    ctx.stroke();

    ctx.fillStyle = '#cbd5e1';
    const off = (world ? world.distance : 0) % 40;
    for (let x = -off; x < W; x += 40) ctx.fillRect(x, WORLD.groundY + 6, 12, 2);

    if (!world || !dino) return;

    for (const o of world.obstacles) {
      if (o.x > W) break;
      if (o.x + o.w < 0) continue;
      if (o.kind <= 1) {
        ctx.fillStyle = '#16a34a';
        ctx.fillRect(o.x, o.y, o.w, o.h);
        ctx.fillRect(o.x - 3, o.y + o.h * 0.3, 4, o.h * 0.35);
        ctx.fillRect(o.x + o.w - 1, o.y + o.h * 0.45, 4, o.h * 0.3);
      } else {
        ctx.fillStyle = '#475569';
        ctx.beginPath();
        ctx.moveTo(o.x + o.w / 2, o.y);
        ctx.lineTo(o.x + o.w, o.y + o.h / 2);
        ctx.lineTo(o.x + o.w / 2, o.y + o.h);
        ctx.lineTo(o.x, o.y + o.h / 2);
        ctx.closePath();
        ctx.fill();
        ctx.fillRect(o.x - 6, o.y + o.h / 2 - 1, 6, 3);
        ctx.fillRect(o.x + o.w, o.y + o.h / 2 - 1, 6, 3);
      }
    }

    // Dino: usa sprite si esta cargado; sino fallback poligonal.
    const x = WORLD.dinoX;
    const y = dino.y;
    const w = WORLD.dinoW;
    const h = dino.h;

    ctx.save();
    if (dinoImgReady && dinoImg) {
      // Tinte rojo cuando murio (overlay tras dibujar el sprite).
      ctx.globalAlpha = dino.alive ? 1 : 0.55;
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(dinoImg, x, y, w, h);
      if (!dino.alive) {
        ctx.globalCompositeOperation = 'source-atop';
        ctx.fillStyle = 'rgba(220, 38, 38, 0.45)';
        ctx.fillRect(x, y, w, h);
      }
    } else {
      ctx.fillStyle = dino.alive ? '#dc2626' : '#9ca3af';
      ctx.strokeStyle = dino.alive ? '#7f1d1d' : '#6b7280';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x, y + h * 0.4);
      ctx.lineTo(x + w * 0.2, y + h * 0.1);
      ctx.lineTo(x + w * 0.85, y + h * 0.05);
      ctx.lineTo(x + w, y + h * 0.5);
      ctx.lineTo(x + w * 0.9, y + h);
      ctx.lineTo(x + w * 0.1, y + h);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, y + h * 0.4);
      ctx.lineTo(x - 8, y + h * 0.25);
      ctx.lineTo(x, y + h * 0.6);
      ctx.closePath();
      ctx.fill();
      const hx = x + w * 0.78;
      const hy = y + (dino.ducking ? h * 0.1 : -h * 0.15);
      ctx.fillRect(hx, hy, w * 0.35, h * 0.35);
      ctx.fillStyle = '#fff';
      ctx.fillRect(hx + w * 0.18, hy + h * 0.08, 3, 3);
    }
    ctx.restore();

    // marcador
    ctx.fillStyle = 'rgba(17, 24, 39, 0.78)';
    ctx.fillRect(8, 8, 200, 48);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px Inter, system-ui';
    ctx.textAlign = 'left';
    ctx.fillText(`Frames: ${score}`, 16, 26);
    ctx.fillText(`Obstaculos esquivados: ${cleared}`, 16, 46);
    if (!dino.alive) {
      ctx.fillStyle = 'rgba(220, 38, 38, 0.92)';
      ctx.fillRect(W / 2 - 60, H / 2 - 18, 120, 36);
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 14px Inter, system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('GAME OVER', W / 2, H / 2 + 5);
    }
  }
</script>

<div class="demo">
  <div class="upload">
    <label class="file-btn">
      <input type="file" accept=".json,application/json" onchange={onFile} />
      Cargar genoma (JSON)
    </label>
    {#if genome}
      <span class="ok">Genoma cargado: {genome.length} pesos</span>
    {/if}
    {#if errorMsg}
      <span class="err">{errorMsg}</span>
    {/if}
  </div>

  <canvas bind:this={canvas} width={WORLD.width} height={WORLD.height}></canvas>

  <div class="controls">
    <button class="primary" onclick={start} disabled={!genome || running}>Correr</button>
    <button onclick={reset} disabled={!genome}>Reset (nueva seed)</button>
  </div>

  {#if runs.length > 0}
    <div class="runs">
      <h4>Ultimas corridas</h4>
      <ul>
        {#each runs.slice().reverse() as r, i}
          <li>
            <span class="idx">#{runs.length - i}</span>
            <span>frames = <b>{r.frames}</b></span>
            <span>obstaculos = <b>{r.cleared}</b></span>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>

<style>
  .demo { display: flex; flex-direction: column; gap: 16px; }
  .upload {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }
  .file-btn {
    padding: 8px 16px;
    background: #6366f1;
    color: #fff;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }
  .file-btn input { display: none; }
  .ok { color: #16a34a; font-size: 0.8rem; font-weight: 600; }
  .err { color: #dc2626; font-size: 0.8rem; }

  canvas {
    width: 100%;
    height: auto;
    max-width: 800px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    background: #fff;
    display: block;
  }

  .controls { display: flex; gap: 8px; }
  .controls button {
    padding: 7px 14px;
    border: 1px solid #e5e7eb;
    background: #fff;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.8rem;
    color: #374151;
  }
  .controls button.primary {
    background: #6366f1; color: #fff; border-color: #6366f1;
  }
  .controls button:disabled { opacity: 0.5; cursor: not-allowed; }

  .runs {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 12px 16px;
  }
  .runs h4 {
    font-size: 0.8rem;
    color: #334155;
    margin-bottom: 8px;
  }
  .runs ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .runs li {
    display: flex;
    gap: 16px;
    font-size: 0.78rem;
    color: #475569;
  }
  .idx { color: #94a3b8; min-width: 30px; }
</style>
