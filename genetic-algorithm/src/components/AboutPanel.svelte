<script>
  // Informe in-app: formulacion, fitness, operadores, intensificacion vs diversificacion.
</script>

<article class="doc">
  <h2>Dino que aprende a saltar con Neuroevolucion</h2>
  <p class="lead">
    Una poblacion de redes neuronales pequeñas controla a un Dino corredor. La evolucion
    selecciona, recombina y muta los pesos durante varias generaciones. No hay backpropagation:
    el "aprendizaje" emerge del algoritmo genetico.
  </p>

  <h3>1. Formulacion del problema</h3>
  <p>
    En cada frame el Dino observa el entorno y debe decidir entre <b>nada</b>, <b>saltar</b> o
    <b>agacharse</b>. Si choca con un obstaculo muere. Buscamos la politica (vector de pesos) que
    maximiza la supervivencia.
  </p>

  <h3>2. Representacion de la solucion (genoma)</h3>
  <p>
    Cada individuo es un MLP fijo <code>5 → 6 → 3</code>:
  </p>
  <ul>
    <li><b>5 entradas</b> normalizadas en [0,1]: distancia al proximo obstaculo, ancho, alto, altura del dino, velocidad del juego.</li>
    <li><b>6 ocultas</b> con activacion tanh.</li>
    <li><b>3 salidas</b> (logits): argmax determina la accion.</li>
  </ul>
  <p>
    El genoma es un <code>Float32Array</code> con <b>57 pesos</b> (incluye sesgos). Es un vector
    plano de numeros reales: ideal para crossover uniforme y mutacion gaussiana.
  </p>

  <h3>3. Funcion de fitness</h3>
  <p class="formula">
    <code>fitness = framesSobrevividos + 50 × obstaculosEsquivados − 0.1 × saltosInutiles</code>
  </p>
  <p>
    El termino principal incentiva sobrevivir. El bonus de obstaculos esquivados acelera el
    aprendizaje (sin el, dinos que "se quedan parados" sin morir tendrian fitness similar a los
    que esquivan algo). La penalizacion por saltos inutiles evita la estrategia trivial de
    "saltar siempre".
  </p>

  <h3>4. Operadores del Algoritmo Genetico</h3>

  <h4>4.1 Inicializacion (Xavier/Glorot)</h4>
  <p>
    Cada peso se muestrea de <code>N(0, √(2/fan_in))</code>, sesgos en 0. Esto mantiene las
    activaciones de tanh en su zona util y aporta diversidad inicial sin caos.
  </p>

  <h4>4.2 Seleccion por Torneo</h4>
  <p>
    Tomamos <b>k</b> individuos al azar y nos quedamos con el de mayor fitness. <b>k</b> regula
    la presion selectiva:
  </p>
  <ul>
    <li><b>k = 2</b> → seleccion suave, mas exploracion (diversificacion).</li>
    <li><b>k = 7</b> → seleccion fuerte, mas explotacion (intensificacion).</li>
  </ul>
  <p>
    Ventaja sobre la ruleta: no requiere normalizar fitness ni manejar valores negativos.
  </p>

  <h4>4.3 Crossover Uniforme</h4>
  <p>
    Para cada peso, con probabilidad 0.5 se toma del padre A o del padre B. Justificacion:
    los pesos NO tienen orden semantico (a diferencia de una ruta TSP), por lo que un crossover
    de 1 punto introduce sesgo posicional artificial. El uniforme trata cada peso como gen
    independiente y mezcla mejor "subredes" de ambos padres.
  </p>

  <h4>4.4 Mutacion Gaussiana</h4>
  <p>
    Para cada peso, con probabilidad <code>p</code> sumamos <code>N(0, σ)</code>. Es la mutacion
    estandar en evolucion de pesos reales: permite ajustes finos (σ chico → intensificacion local)
    o saltos amplios (σ grande → diversificacion).
  </p>

  <h4>4.5 Elitismo</h4>
  <p>
    Los <b>top-K</b> individuos pasan intactos a la siguiente generacion. Garantiza monotonia del
    mejor fitness (nunca empeora). Con elitismo = 0, una mala "tirada" de torneo puede destruir
    al mejor individuo.
  </p>

  <h3>5. Intensificacion vs Diversificacion</h3>
  <p>
    Los sliders de la pestaña <b>Entrenamiento</b> exponen ambos extremos. La siguiente tabla
    resume el efecto de cada parametro:
  </p>
  <table>
    <thead><tr><th>Slider</th><th>Subir → Intensifica</th><th>Subir → Diversifica</th></tr></thead>
    <tbody>
      <tr><td>Tamaño torneo k</td><td><b>✓</b></td><td></td></tr>
      <tr><td>Prob. mutacion</td><td></td><td><b>✓</b></td></tr>
      <tr><td>σ mutacion</td><td></td><td><b>✓</b></td></tr>
      <tr><td>Elitismo</td><td><b>✓</b></td><td></td></tr>
      <tr><td>Tamaño poblacion</td><td></td><td><b>✓</b></td></tr>
    </tbody>
  </table>

  <h3>6. Problemas enfrentados</h3>

  <h4>6.1 Convergencia prematura</h4>
  <p>
    Sintoma: el fitness se estanca despues de pocas generaciones y todos los dinos saltan a la
    vez (mueren juntos). Causa: presion selectiva alta + mutacion muy baja + elitismo alto.
  </p>
  <p>
    <b>Solucion:</b> bajar <code>k</code> a 2-3, subir <code>p_mut</code> a 0.10-0.15, bajar
    elitismo a 1-2. El indicador "Diversidad" en el HUD ayuda a detectar el problema: si cae a
    valores muy bajos (&lt; 0.05), la poblacion esta colapsando.
  </p>

  <h4>6.2 No-convergencia</h4>
  <p>
    Sintoma: el fitness oscila sin tendencia clara. Causa: mutacion enorme (σ = 0.8, p = 0.5),
    elitismo 0.
  </p>
  <p>
    <b>Solucion:</b> subir elitismo a 2-4, bajar σ a 0.15-0.25, mantener p_mut alrededor de 0.05.
  </p>

  <h4>6.3 Estrategia degenerada "saltar siempre"</h4>
  <p>
    En las primeras versiones el fitness era solo <code>frames vividos</code>. Los dinos
    descubrian que saltar continuamente daba inmunidad contra cactus bajos. La penalizacion
    por saltos inutiles en la formula de fitness arregla esto y fuerza estrategias mas adaptativas.
  </p>

  <h4>6.4 Fairness entre individuos</h4>
  <p>
    Si cada dino enfrenta una secuencia de obstaculos distinta, el ranking por fitness es ruidoso.
    Solucion: toda la poblacion ve la <b>misma seed</b> de obstaculos por generacion (PRNG
    mulberry32 deterministico).
  </p>

  <h3>7. Sobre la fairness entre generaciones</h3>
  <p>
    La seed cambia entre generaciones para evitar overfitting a una secuencia particular. La
    pestaña <b>Demo</b> permite cargar el mejor genoma y correrlo con seeds nuevas para validar
    que generaliza.
  </p>

  <hr />
  <p class="footer-note">
    Stack: Svelte 5 + Vite 8 + Canvas 2D, sin dependencias externas para el algoritmo. Codigo en
    <code>src/lib/</code> (neuralNet, dinoGame, geneticAlgorithm) y componentes en
    <code>src/components/</code>.
  </p>
</article>

<style>
  .doc {
    max-width: 740px;
    margin: 0 auto;
    color: #1f2937;
    line-height: 1.65;
  }
  .doc h2 {
    font-size: 1.5rem;
    color: #111827;
    margin-bottom: 8px;
  }
  .doc h3 {
    font-size: 1.1rem;
    color: #312e81;
    margin-top: 24px;
    margin-bottom: 8px;
  }
  .doc h4 {
    font-size: 0.95rem;
    color: #4338ca;
    margin-top: 14px;
    margin-bottom: 4px;
  }
  .doc p { margin-bottom: 10px; font-size: 0.9rem; }
  .lead {
    background: #eef2ff;
    border-left: 3px solid #6366f1;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem !important;
    color: #312e81;
  }
  .formula {
    background: #f1f5f9;
    padding: 10px 14px;
    border-radius: 8px;
    text-align: center;
    font-family: ui-monospace, monospace;
  }
  .doc ul {
    padding-left: 22px;
    margin-bottom: 10px;
    font-size: 0.9rem;
  }
  .doc ul li { margin-bottom: 3px; }
  .doc code {
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 0.85em;
    color: #4338ca;
  }
  .doc table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    margin: 10px 0;
  }
  .doc table th, .doc table td {
    border: 1px solid #e5e7eb;
    padding: 6px 10px;
    text-align: left;
  }
  .doc table thead {
    background: #f1f5f9;
  }
  .doc hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 28px 0 16px;
  }
  .footer-note {
    color: #6b7280;
    font-size: 0.8rem !important;
  }
</style>
