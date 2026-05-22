<script>
  // Grafico de fitness: best (azul) y avg (gris) por generacion.
  let { history = [] } = $props();

  let canvas = $state(null);

  // Redibujar cada vez que cambia el historial.
  $effect(() => {
    if (!canvas) return;
    draw(history);
  });

  function draw(h) {
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    const padL = 36, padR = 8, padT = 12, padB = 22;

    ctx.clearRect(0, 0, W, H);
    // fondo
    ctx.fillStyle = '#fafbff';
    ctx.fillRect(0, 0, W, H);

    if (h.length === 0) {
      ctx.fillStyle = '#9ca3af';
      ctx.font = '12px Inter, system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Sin datos aun. Inicia el entrenamiento.', W / 2, H / 2);
      return;
    }

    const maxF = Math.max(...h.map(p => p.best), 10);
    const minF = 0;
    const n = h.length;

    // grilla horizontal y eje y
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, system-ui';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const y = padT + (H - padT - padB) * i / 4;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(W - padR, y);
      ctx.stroke();
      const v = Math.round(maxF - (maxF - minF) * i / 4);
      ctx.fillText(String(v), padL - 4, y + 3);
    }

    // eje x: ticks cada ~5 generaciones
    ctx.textAlign = 'center';
    const tickStep = Math.max(1, Math.ceil(n / 8));
    for (let i = 0; i < n; i += tickStep) {
      const x = padL + (W - padL - padR) * (n === 1 ? 0 : i / (n - 1));
      ctx.fillText(String(h[i].gen), x, H - padB + 12);
    }

    const xAt = (i) => padL + (W - padL - padR) * (n === 1 ? 0 : i / (n - 1));
    const yAt = (v) => padT + (H - padT - padB) * (1 - (v - minF) / (maxF - minF || 1));

    // linea avg
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    h.forEach((p, i) => {
      const x = xAt(i), y = yAt(p.avg);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // linea best
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.beginPath();
    h.forEach((p, i) => {
      const x = xAt(i), y = yAt(p.best);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // leyenda
    ctx.font = '11px Inter, system-ui';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#6366f1';
    ctx.fillRect(W - 110, padT, 10, 2);
    ctx.fillStyle = '#374151';
    ctx.fillText('best', W - 96, padT + 5);
    ctx.fillStyle = '#94a3b8';
    ctx.fillRect(W - 60, padT, 10, 2);
    ctx.fillStyle = '#374151';
    ctx.fillText('promedio', W - 46, padT + 5);
  }
</script>

<canvas bind:this={canvas} width="780" height="180"></canvas>

<style>
  canvas {
    width: 100%;
    height: auto;
    max-width: 780px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    display: block;
  }
</style>
