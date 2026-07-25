<!-- wtl-dllm · ui/src/lib/TickRule.svelte -->
<script lang="ts">
  /* what: section divider — rotated 6px square, mono label, dashed hairline
     by:   <wtl> watchthelight
     tags: ui, chrome */
  let { label = "" }: { label?: string } = $props();
</script>

<div class="tick-rule" role="separator">
  <span class="tick"></span>
  <span class="eyebrow">{label}</span>
  <span class="rule"></span>
</div>

<style>
  .tick-rule {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: var(--space-section) 0 12px;
  }
  .tick {
    width: 6px;
    height: 6px;
    background: var(--sage-deep);
    transform: rotate(45deg);
    flex: none;
  }
  .rule {
    flex: 1;
    border-top: 1px dashed var(--line);
  }
</style>
