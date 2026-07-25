<!-- wtl-dllm · ui/src/lib/DenoiseBoard.svelte -->
<script lang="ts">
  /* what: the centerpiece — token cells resolving from masked to committed, replayable
     why:  frozen means frozen; a committed cell never changes, same as the sampler
     by:   <wtl> watchthelight
     tags: ui, board */
  import { session } from "./ws.svelte";

  const frame = $derived(session.current);

  function cellClass(i: number): string {
    if (!frame) return "cell masked";
    if (!frame.committed[i]) return "cell masked";
    const fresh = frame.just_committed.includes(i);
    const c = frame.conf[i];
    const given = c === 1.0;
    if (given) return "cell prompt";
    const bin = c < 0.3 ? "low" : c < 0.7 ? "mid" : "high";
    return `cell committed ${bin}${fresh ? " fresh" : ""}`;
  }

  function cellText(i: number): string {
    if (!frame) return "·";
    const t = frame.tokens[i];
    if (t === "[MASK]") return "·";
    if (t === "[PAD]") return "";
    if (t === "[EOS]") return "⌐";
    return t;
  }
</script>

<div class="board mono num" aria-label="denoising canvas">
  {#if frame}
    {#each frame.tokens as _, i (i)}
      <span class={cellClass(i)}>{cellText(i)}</span>
    {/each}
  {:else}
    <span class="hint">pick a task and hit run — tokens resolve here, one step at a time</span>
  {/if}
</div>

{#if frame}
  <div class="strip">
    <span class="eyebrow num">step {frame.step}/{frame.total_steps}</span>
    <input
      class="scrub"
      type="range"
      min="0"
      max={session.frames.length - 1}
      value={session.playhead}
      oninput={(e) => session.scrub(Number(e.currentTarget.value))}
      aria-label="scrub through steps"
    />
    <button class="ghost" onclick={() => (session.playing ? session.pause() : session.play())}>
      {session.playing ? "pause" : "play"}
    </button>
    {#if session.last?.done && session.playhead === session.frames.length - 1}
      <span class="verdict {session.last.verdict}">{session.last.verdict}</span>
    {/if}
  </div>
{/if}

<style>
  .board {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: var(--space-card);
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    min-height: 84px;
    align-items: center;
  }
  .cell {
    width: 42px;
    height: 52px;
    display: grid;
    place-items: center;
    font-size: 1.4rem;
    border: 1px solid var(--line-soft);
    border-radius: var(--radius);
    background: var(--surface-2);
    color: var(--ink-faint);
    transition:
      color var(--dur-slow) var(--ease-smooth),
      border-color var(--dur-fast) var(--ease-smooth),
      transform var(--dur-fast) var(--ease-spring);
  }
  .cell.prompt {
    background: var(--surface);
    color: var(--ink);
    border-color: var(--line);
  }
  .cell.committed {
    background: var(--surface);
    color: var(--ink);
  }
  .cell.committed.low { color: var(--warn); }
  .cell.committed.mid { color: var(--sage-deep); }
  .cell.committed.high { color: var(--sage-bright); }
  .cell.fresh {
    transform: scale(1.06);
    border-color: var(--line-strong);
  }
  .hint {
    color: var(--ink-3);
    font-family: var(--font-body);
    font-size: 0.85rem;
    padding: 8px;
  }
  .strip {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 10px;
  }
  .scrub {
    flex: 1;
    accent-color: var(--sage);
  }
  .ghost {
    background: none;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 4px 12px;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    cursor: pointer;
    transition: border-color var(--dur-fast) var(--ease-smooth), transform var(--dur-fast) var(--ease-out);
  }
  .ghost:hover {
    border-color: var(--sage);
    transform: translateY(-1px);
  }
  .verdict {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 3px 10px;
    border: 1px solid var(--line);
    border-radius: var(--radius);
  }
  .verdict.correct { color: var(--good); border-color: var(--good); }
  .verdict.wrong { color: var(--danger); border-color: var(--danger); }
</style>
