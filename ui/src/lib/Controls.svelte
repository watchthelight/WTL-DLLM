<!-- wtl-dllm · ui/src/lib/Controls.svelte -->
<script lang="ts">
  /* what: task + sampler controls; honest microcopy, ctrl+enter runs
     by:   <wtl> watchthelight
     tags: ui, controls */
  import { session } from "./ws.svelte";

  let level = $state(1);
  let ordering = $state("confidence");
  let temperature = $state(0);
  let steps = $state<number | "">("");
  let seed = $state<number | "">("");
  let infillMode = $state(false);
  let infPrefix = $state("18+");
  let infSuffix = $state("=45");
  let infHole = $state(2);

  const orderings = ["confidence", "margin", "entropy", "random"];

  export function run() {
    if (infillMode) {
      session.run({
        infill: { prefix: infPrefix, suffix: infSuffix, hole_len: infHole },
        ordering,
        temperature,
        ...(steps !== "" && { steps: Number(steps) }),
        ...(seed !== "" && { seed: Number(seed) }),
      });
    } else {
      session.run({
        level,
        ordering,
        temperature,
        ...(steps !== "" && { steps: Number(steps) }),
        ...(seed !== "" && { seed: Number(seed) }),
      });
    }
  }

  function onKey(e: KeyboardEvent) {
    if (e.ctrlKey && e.key === "Enter") run();
  }
</script>

<svelte:window onkeydown={onKey} />

<div class="panel">
  <label class="row">
    <span class="eyebrow">task</span>
    <select bind:value={infillMode} disabled={session.status === "streaming"}>
      <option value={false}>solve</option>
      <option value={true}>infill</option>
    </select>
  </label>

  {#if !infillMode}
    <label class="row">
      <span class="eyebrow">level</span>
      <select bind:value={level}>
        {#each Object.entries(session.levels ?? {}) as [lv, meta] (lv)}
          <option value={Number(lv)}>L{lv} — {meta.example}</option>
        {/each}
      </select>
    </label>
  {:else}
    <div class="infill mono">
      <input bind:value={infPrefix} aria-label="prefix" />
      <input type="number" min="1" max="8" bind:value={infHole} aria-label="hole length" class="hole" />
      <input bind:value={infSuffix} aria-label="suffix" />
    </div>
    <p class="note">the blank in the middle gets filled from both sides — the one trick left-to-right models can't do</p>
  {/if}

  <label class="row">
    <span class="eyebrow">ordering</span>
    <select bind:value={ordering}>
      {#each orderings as o (o)}<option value={o}>{o}</option>{/each}
    </select>
  </label>
  <p class="note">which masked spot gets filled next</p>

  <label class="row">
    <span class="eyebrow">temp</span>
    <input type="number" min="0" max="2" step="0.1" bind:value={temperature} />
  </label>
  <p class="note">0 = deterministic; this model does math, keep it 0</p>

  <label class="row">
    <span class="eyebrow">steps</span>
    <input type="number" min="1" max="64" bind:value={steps} placeholder="auto" />
  </label>

  <label class="row">
    <span class="eyebrow">seed</span>
    <input type="number" bind:value={seed} placeholder="random" />
  </label>

  <label class="row">
    <span class="eyebrow">playback</span>
    <input type="range" min="0" max="500" step="20" bind:value={session.speedMs} />
    <span class="num note">{session.speedMs}ms</span>
  </label>

  <button class="run" onclick={run} disabled={session.status === "streaming"}>
    run <span class="kbd">ctrl+enter</span>
  </button>

  {#if session.errorMsg}
    <p class="err">{session.errorMsg}</p>
  {/if}
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .row {
    display: grid;
    grid-template-columns: 64px 1fr auto;
    align-items: center;
    gap: 10px;
  }
  select,
  input {
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: var(--radius);
    padding: 6px 8px;
    font-size: 0.85rem;
    transition: border-color var(--dur-fast) var(--ease-smooth);
    accent-color: var(--sage);
  }
  input[type="range"] {
    padding: 0;
    background: none;
    border: none;
  }
  select:hover,
  input:hover {
    border-color: var(--line-strong);
  }
  .infill {
    display: grid;
    grid-template-columns: 1fr 64px 1fr;
    gap: 6px;
  }
  .hole {
    text-align: center;
  }
  .note {
    margin: 0;
    font-size: 0.72rem;
    color: var(--ink-3);
  }
  .err {
    margin: 0;
    font-size: 0.78rem;
    color: var(--danger);
  }
  .run {
    margin-top: 8px;
    background: var(--sage-fill);
    border: 1px solid var(--sage-deep);
    border-radius: var(--radius);
    color: var(--sage-bright);
    padding: 9px;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    cursor: pointer;
    transition: border-color var(--dur-fast) var(--ease-smooth), transform var(--dur-fast) var(--ease-out);
  }
  .run:hover:enabled {
    border-color: var(--sage);
    transform: translateY(-1px);
  }
  .run:disabled {
    opacity: 0.5;
    cursor: default;
  }
  .kbd {
    color: var(--ink-3);
    font-size: 0.65rem;
    margin-left: 6px;
  }
</style>
