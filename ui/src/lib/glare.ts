// wtl-dllm · ui/src/lib/glare.ts
// what: pointer-occlusion glare + optional 5deg tilt as a svelte action
// why:  css vars driven by pointermove; the gradient is painted by the compositor
// by:   <wtl> watchthelight
// tags: ui, action, glare

import { hasHover, prefersReducedMotion } from "./motion";

export function glare(node: HTMLElement, opts?: { tilt?: boolean; max?: number }) {
  if (prefersReducedMotion() || !hasHover()) return {};
  const max = opts?.max ?? 5;
  const tilt = opts?.tilt ?? false;

  function move(e: PointerEvent) {
    const r = node.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    if (tilt) {
      const rx = (0.5 - py) * max * 2;
      const ry = (px - 0.5) * max * 2;
      node.style.transform = `perspective(700px) rotateX(${rx}deg) rotateY(${ry}deg)`;
    }
    node.style.setProperty("--mx", `${px * 100}%`);
    node.style.setProperty("--my", `${py * 100}%`);
    node.style.setProperty("--glare", "1");
  }
  function leave() {
    node.style.transform = "";
    node.style.setProperty("--glare", "0");
  }

  node.addEventListener("pointermove", move, { passive: true });
  node.addEventListener("pointerleave", leave);
  return {
    destroy() {
      node.removeEventListener("pointermove", move);
      node.removeEventListener("pointerleave", leave);
    },
  };
}
