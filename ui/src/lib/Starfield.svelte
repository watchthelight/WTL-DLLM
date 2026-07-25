<!-- wtl-dllm · ui/src/lib/Starfield.svelte -->
<script lang="ts">
  /* what: square-star canvas at z -1 — 3 parallax layers, twinkle, slow drift
     why:  ported methodology; fillRect instead of arc is the one deliberate departure
     by:   <wtl> watchthelight
     tags: ui, starfield, canvas */
  import { onMount } from "svelte";
  import { prefersReducedMotion } from "./motion";

  const LAYERS = [
    { parallax: 0.25, speed: 0.12, size: 0.7 },
    { parallax: 0.5, speed: 0.22, size: 1.0 },
    { parallax: 1.0, speed: 0.36, size: 1.4 },
  ];
  const STAR = [232, 240, 230];
  const ACCENT = [150, 200, 165];
  const COUNT = 120;

  let canvas: HTMLCanvasElement;

  onMount(() => {
    const cx = canvas.getContext("2d")!;
    let w = 0,
      h = 0,
      pointerX = 0,
      curX = 0,
      raf = 0;
    let stars: {
      x: number; y: number; r: number; layer: number;
      baseA: number; tw: number; phase: number; tinted: boolean;
    }[] = [];

    const density = () => Number(localStorage.getItem("wtl-star-density") ?? 1);
    const speedMult = () => Number(localStorage.getItem("wtl-star-speed") ?? 1);

    function build() {
      stars = Array.from({ length: Math.round(COUNT * density()) }, (_, i) => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: LAYERS[i % 3].size * (0.6 + Math.random() * 0.8),
        layer: i % 3,
        baseA: 0.25 + Math.random() * 0.55,
        tw: 0.4 + Math.random() * 1.1,
        phase: Math.random() * Math.PI * 2,
        tinted: Math.random() < 0.14,
      }));
    }

    function resize() {
      const dpr = Math.min(devicePixelRatio, 2);
      w = innerWidth;
      h = innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      cx.setTransform(dpr, 0, 0, dpr, 0, 0);
      build();
    }

    function draw(t: number) {
      cx.clearRect(0, 0, w, h);
      curX += (pointerX - curX) * 0.04;
      const time = t * 0.001;
      const sm = speedMult();
      for (const s of stars) {
        const L = LAYERS[s.layer];
        s.x -= L.speed * sm * 0.6;
        s.y += L.speed * sm * 0.5;
        if (s.x < -2) s.x = w + 2;
        if (s.y > h + 2) s.y = -2;
        const a = Math.max(0, Math.min(1, s.baseA + Math.sin(time * s.tw + s.phase) * 0.18));
        const [r, g, b] = s.tinted ? ACCENT : STAR;
        const px = s.x + curX * L.parallax * 26;
        cx.fillStyle = `rgba(${r},${g},${b},${a})`;
        cx.fillRect(px - s.r, s.y - s.r, s.r * 2, s.r * 2);
      }
      raf = requestAnimationFrame(draw);
    }

    const onPointer = (e: PointerEvent) => {
      pointerX = (e.clientX / w - 0.5) * 2;
    };
    const onTune = () => build();

    resize();
    addEventListener("resize", resize);
    if (prefersReducedMotion()) {
      draw(0);
      cancelAnimationFrame(raf);
    } else {
      addEventListener("pointermove", onPointer, { passive: true });
      raf = requestAnimationFrame(draw);
    }
    addEventListener("wtl:starfield", onTune);

    return () => {
      cancelAnimationFrame(raf);
      removeEventListener("resize", resize);
      removeEventListener("pointermove", onPointer);
      removeEventListener("wtl:starfield", onTune);
    };
  });
</script>

<canvas bind:this={canvas} class="starfield" aria-hidden="true"></canvas>

<style>
  .starfield {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
  }
</style>
