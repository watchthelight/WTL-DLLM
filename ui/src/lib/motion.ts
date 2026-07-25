// wtl-dllm · ui/src/lib/motion.ts
// what: reduced-motion + hover-capability gates every animated thing checks
// by:   <wtl> watchthelight
// tags: ui, motion

export function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function hasHover(): boolean {
  return window.matchMedia("(hover: hover)").matches;
}
