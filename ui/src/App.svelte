<!-- wtl-dllm · ui/src/App.svelte -->
<script lang="ts">
  /* what: shell — rail, board, controls over the starfield
     by:   <wtl> watchthelight
     tags: ui, shell */
  import { onMount } from "svelte";
  import Controls from "./lib/Controls.svelte";
  import DenoiseBoard from "./lib/DenoiseBoard.svelte";
  import Starfield from "./lib/Starfield.svelte";
  import TickRule from "./lib/TickRule.svelte";
  import { session } from "./lib/ws.svelte";

  onMount(() => session.loadMeta());

  const modelLine = $derived(
    session.info
      ? `${session.info.model} · ${(Number(session.info.params) / 1e6).toFixed(1)}m params · ${session.info.device}`
      : "connecting…"
  );
</script>

<Starfield />

<div class="shell">
  <aside class="rail">
    <div class="brand">
      <span class="tick"></span>
      <h1>wtl-dllm</h1>
    </div>
    <p class="sub">a tiny diffusion language model, live</p>
    <div class="meta mono">{modelLine}</div>
    <div class="spacer"></div>
    <footer class="mono">built by watchthelight · mit</footer>
  </aside>

  <main>
    <TickRule label="denoise" />
    <section class="card">
      <DenoiseBoard />
    </section>

    <TickRule label="controls" />
    <section class="card">
      <Controls />
    </section>
  </main>
</div>

<style>
  .shell {
    display: grid;
    grid-template-columns: 15rem 1fr;
    min-height: 100dvh;
    max-width: 1100px;
    margin: 0 auto;
  }
  .rail {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: var(--space-section);
    border-right: 1px solid var(--line-soft);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .tick {
    width: 8px;
    height: 8px;
    background: var(--sage);
    transform: rotate(45deg);
  }
  h1 {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0;
  }
  .sub {
    color: var(--ink-2);
    font-size: 0.82rem;
    margin: 0;
  }
  .meta {
    font-size: 0.62rem;
    color: var(--ink-3);
    margin-top: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .spacer {
    flex: 1;
  }
  footer {
    font-size: 0.6rem;
    color: var(--ink-faint);
    text-transform: uppercase;
    letter-spacing: 0.12em;
  }
  main {
    padding: 0 var(--space-section) var(--space-section);
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: var(--space-card);
  }
  @media (max-width: 720px) {
    .shell {
      grid-template-columns: 1fr;
    }
    .rail {
      border-right: none;
      border-bottom: 1px solid var(--line-soft);
    }
  }
</style>
