<script>
  import TrainingPanel from './components/TrainingPanel.svelte';
  import DemoPanel from './components/DemoPanel.svelte';
  import AboutPanel from './components/AboutPanel.svelte';

  let tab = $state('training');
</script>

<div class="app">
  <nav>
    <div class="brand">
      <span class="logo">GA</span>
      <span class="title">Dino GA &mdash; Neuroevolucion</span>
    </div>
    <div class="tabs">
      <button class:active={tab === 'training'} onclick={() => tab = 'training'}>
        Entrenamiento
      </button>
      <button class:active={tab === 'demo'} onclick={() => tab = 'demo'}>
        Demo
      </button>
      <button class:active={tab === 'about'} onclick={() => tab = 'about'}>
        Acerca de
      </button>
    </div>
  </nav>

  <main>
    {#if tab === 'training'}
      <TrainingPanel />
    {:else if tab === 'demo'}
      <DemoPanel />
    {:else}
      <AboutPanel />
    {/if}
  </main>

  <footer>IA261 &mdash; Algoritmo Genetico aplicado al Dino Runner</footer>
</div>

<style>
  .app {
    max-width: 1080px;
    margin: 0 auto;
    padding: 24px 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 28px;
  }
  .brand { display: flex; align-items: center; gap: 10px; }
  .logo {
    display: grid;
    place-items: center;
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    font-weight: 800;
    font-size: 0.8rem;
    letter-spacing: -0.5px;
  }
  .title {
    font-weight: 700;
    font-size: 1rem;
    color: #111827;
  }

  .tabs {
    display: flex;
    gap: 4px;
    background: #f1f5f9;
    padding: 3px;
    border-radius: 10px;
  }
  .tabs button {
    padding: 7px 18px;
    border: none;
    border-radius: 8px;
    background: transparent;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    color: #64748b;
    transition: all 0.15s;
  }
  .tabs button.active {
    background: #fff;
    color: #6366f1;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }

  main {
    flex: 1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 28px 24px;
  }

  footer {
    text-align: center;
    padding: 20px 0 4px;
    font-size: 0.75rem;
    color: #9ca3af;
  }
</style>
