---
title: "pawtropolis ui methodology — recon report"
author: "<wtl>"
project: wtl-dllm
tags: [research, ui, design]
---

# Pawtropolis UI Methodology — Recon Report

> Extracted 2026-07-25 from a local checkout of the pawtropolis-tech repo (`..\pawtropolis-tech`), https://pawtropolis.tech (live, verified via Playwright), and reactbits.dev (props personally verified).
> Purpose: source methodology for the WTL-DLLM visualizer UI (dark alpine/sage, OLED, square/starry, parallax, mouse occlusion).

## A. Stack Summary

Repo: monorepo; root = Discord bot (discord.js 14, fastify, better-sqlite3, canvas). **Web UI lives entirely in `web/`.**

From `web/package.json`:
- **Svelte ^5.55.8** (runes: `$props/$state/$derived/$effect`), **SvelteKit ^2.60.1**, **@sveltejs/adapter-node ^5.5.4** (out: `build`), **Vite ^7.3.3**
- **Tailwind CSS ^4.2.1** via `@tailwindcss/vite` — but Tailwind is nearly vestigial: `@import "tailwindcss"` in app.css, occasional utilities. ~95% of styling is **hand-written CSS custom properties + component-scoped `<style>` blocks**. No tailwind.config; the design system is a token vocabulary in `app.css`.
- **GSAP ^3.14.2** (used minimally — one reveal component), **culori ^4.0.2** (OKLCH→hex gamut-safe), **lucide-svelte ^0.577.0** (icons, strokeWidth 1.75, active 2.1), d3, mermaid, marked, @sentry/sveltekit, web-push
- Fonts self-hosted via **@fontsource**: figtree/quicksand/hanken-grotesk/fredoka/inter (all Variable) + space-mono 400/700
- Scaffolded with `npx sv@0.12.4 create --template minimal --types ts`

Key architecture: root `web/src/routes/+layout.svelte` mounts `<Starfield />` once globally (skipped on `/observatory`); pages render over it because layout backgrounds are `transparent`.

## B. Starfield Implementation

**File: `web\src\lib\components\layout\Starfield.svelte`** (188 lines — read verbatim when rebuilding). Canvas-based, NOT divs. One fixed full-viewport `<canvas class="starfield" aria-hidden="true">`, CSS: `position:fixed; inset:0; z-index:-1; pointer-events:none`. Note: **stars are round dots (`ctx.arc`), not squares** — the "square" identity comes from the UI chrome (D below), not the starfield.

Per-theme palettes (RGB triplets):
```js
'observatory-dark':  { star: [232,240,230] /*#e8f0e6*/, accent: [150,200,165] /*#96c8a5*/, count: 120 },
'observatory-light': { star: [120,110,90],  accent: [90,130,100],  count: 120 },
legacy:              { star: [180,190,220], accent: [150,170,230], count: 70 }
```
3 depth layers, assigned round-robin `i % 3`:
```js
const LAYERS = [
  { parallax: 0.25, speed: 0.12, size: 0.7 },
  { parallax: 0.5,  speed: 0.22, size: 1.0 },
  { parallax: 1.0,  speed: 0.36, size: 1.4 }
];
```
Star generation (`buildStars`): count = `round(pal.count * density)` (density user-tunable 0.4–1.6×); `x,y` uniform random; radius `LAYERS[layer].size * (0.6 + rnd*0.8)` → 0.42–1.96px; `baseA = 0.25 + rnd*0.55`; twinkle freq `tw = 0.4 + rnd*1.1` rad/s; `phase = rnd*2π`; `tinted = Math.random() < 0.14` (14% get the sage accent color).

Draw loop (every rAF):
```js
cx.clearRect(0,0,w,h);
curX += (pointerX - curX) * 0.04;            // lerp factor 0.04
const time = t * 0.001;
// per star:
const a  = clamp01(s.baseA + Math.sin(time * s.tw + s.phase) * 0.18);  // twinkle amplitude ±0.18
const px = s.x + curX * L.parallax * 26;     // max ±26px shift on nearest layer
cx.arc(px, py, s.r, 0, Math.PI*2); cx.fillStyle = `rgba(${r},${g},${b},${a})`;
```
Drift (per frame, before draw): `s.x -= L.speed * speedMult * 0.6; s.y += L.speed * speedMult * 0.5` — slow **down-left drift**, toroidal wrap at ±2px margins. `speedMult` user-tunable 0.4–1.8×.

Pointer input: `pointerX = (e.clientX/w - 0.5) * 2` (normalized −1..1 from viewport center), listener `{ passive: true }`.

Resize: `dpr = Math.min(devicePixelRatio, 2)`; canvas sized `w*dpr`, `setTransform(dpr,0,0,dpr,0,0)`; rebuilds stars.

Reduced motion: one static `draw(0)`, no rAF loop, no pointermove listener. Theme changes: `MutationObserver` on `html[data-theme]` swaps palette + rebuilds. Runtime tuning: custom window event `paw:starfield` re-reads `localStorage['paw-star-density'/'paw-star-speed']` (dispatched by ThemePanel sliders, ranges density 0.4–1.6 step 0.1, speed 0.4–1.8 step 0.1).

## C. Parallax + Mouse Effects

**Parallax is mouse-based only. Zero scroll parallax anywhere.** The layered parallax math is entirely inside the starfield loop above (layer.parallax × 26px, lerp 0.04).

**Tilt action — `web\src\lib\actions\tilt.ts`** (37 lines):
```ts
const max = opts?.max ?? 5;                       // max 5deg
const px = (e.clientX - r.left) / r.width;        // 0..1 within card
const rx = (0.5 - py) * max * 2;
const ry = (px - 0.5) * max * 2;
node.style.transform = `perspective(700px) rotateX(${rx}deg) rotateY(${ry}deg)`;
node.style.setProperty('--mx', `${px * 100}%`);
node.style.setProperty('--my', `${py * 100}%`);
node.style.setProperty('--glare', '1');           // leave → transform:'' , --glare:0
```
Fully disabled under `prefersReducedMotion()`.

**Cursor-proximity glare — `web\src\routes\dashboard\+page.svelte` lines 304–312.** Each metric card contains `<span class="metric-glare">`:
```css
.metric { overflow: hidden; transform-style: preserve-3d;
  transition: transform 120ms var(--ease-out), border-color var(--duration-fast) var(--ease-smooth); }
.metric-glare {
  position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
  opacity: var(--glare, 0);
  transition: opacity var(--duration-fast) var(--ease-smooth);   /* 150ms */
  background: radial-gradient(220px at var(--mx,50%) var(--my,50%),
              oklch(78% var(--sage-c) var(--sage-h) / 0.14), transparent 60%);
}
```
Exact falloff: **220px radius, sage at 14% alpha, transparent by the 60% stop**, fading 150ms. This is the "mouse occlusion" effect: CSS vars driven by JS pointermove, gradient painted by compositor.

**Hover vocabulary** (consistent everywhere): border-color → `var(--sage)` or `var(--line-strong)` + `translateY(-1px)` (hero) / `translateY(-2px)` (DataCard, skipped under reduced motion) / `translateX(1px)` (nav items). DataCard hover raises shadow one tier via inline style on mouseenter, gated by `matchMedia('(hover: hover)')`.

**Shared floating hover glow — `web\src\routes\dashboard\reviews\+layout.svelte`**: one absolute `.queue-glow` overlay div repositioned to the hovered card's rect (`getBoundingClientRect`, recomputed on scroll) with `transition: top/left/width/height 100ms ease` — the shadow slides between cards instead of popping. Desktop only.

**Status pulse — ConnectionIndicator**: `@keyframes glow-pulse { box-shadow 0 0 2px → 0 0 6px var(--dot-color) }` 1.5s infinite, reconnecting state only, disabled under reduced motion.

## D. Theme Tokens

**Source of truth: `web\src\app.css`** (341 lines). All colors are **OKLCH with a single seed hue** `--sage-h: 152` and chroma `--sage-c: 0.075` — the entire palette derives from those two numbers. Hex values are culori conversions (source is pure OKLCH):

| Token | oklch (source) | hex (computed) |
|---|---|---|
| --void | `oklch(15.5% 0.012 152)` | #090e0a |
| --void-deep | `oklch(12% 0.014 152)` | #030704 |
| --surface | `oklch(20.5% 0.013 152)` | #131914 |
| --surface-2 | `oklch(24.5% 0.015 152)` | #1b231d |
| --surface-3 | `oklch(28.5% 0.016 152)` | #242c26 |
| --ink | `oklch(93% 0.014 110)` | #e8e9de |
| --ink-2 | `oklch(75% 0.016 140)` | #a9b1a7 |
| --ink-3 | `oklch(60% 0.014 150)` | #7b837c |
| --ink-faint | `oklch(48% 0.012 150)` | #59605a |
| --line | `oklch(33% 0.014 152)` | #303832 |
| --line-soft | `oklch(27% 0.012 152)` | #222824 |
| --line-strong | `oklch(46% 0.02 152)` | #505b53 |
| --sage | `oklch(78% 0.075 152)` | #94c6a0 |
| --sage-bright | `oklch(85% 0.095 152)` | #9ee0af |
| --sage-deep | `oklch(58% 0.085 152)` | #528961 |
| --sage-soft | `oklch(30% 0.041 152)` | #1d3423 |
| --sage-fill | `oklch(24% 0.03 152)` | #142318 |
| --on-sage | `oklch(17% 0.02 152)` | #09120b |
| --good | `oklch(74% 0.09 150)` | #81bb8d |
| --warn | `oklch(78% 0.1 78)` | #dbb06b |
| --danger | `oklch(70% 0.11 32)` | #da8473 |
| --info | `oklch(74% 0.07 220)` | #77b6ca |
| --brand-magenta | `oklch(65% 0.25 330)` | #dc3dd5 |
| --brand-cyan | `oklch(70% 0.15 200)` | #00b9c3 |

Starfield colors: #e8f0e6 (86% of stars), #96c8a5 (14% tinted).

**Radii — the square signature:** `--radius: 2px; --radius-pill: 2px; --radius-sm: 2px; --radius-md: 2px; --radius-lg: 2px` — every token is 2px in Observatory. (Legacy theme: 12/999/6/12/16.) Win95 `/observatory` page goes full 0. Square reinforced by: square avatars, square icon wells, and the **tick-rule motif** — a 6px square rotated 45° as a section-divider node (`::before` rotated square + uppercase mono label + `::after` dashed 1px hairline).

**Shadows — "flat by design":**
```css
--shadow / -sm / -md: 0 1px 0 oklch(100% 0 0 / 0.03);   /* single hairline top highlight */
--shadow-lg:          0 2px 0 oklch(100% 0 0 / 0.04);   /* no bloom, no blur */
```
Depth from 1px borders (3 line weights) + surface steps, not shadows. Exceptions: toasts/FAB use real drop shadows (`0 4px 24px oklch(0% 0 0/0.4)`).

**Fonts:** `--font-head`/`--font-body`: `"Figtree Variable", system-ui, sans-serif`; `--font-mono`: `"Space Mono", "Courier New", monospace`. Body: 0.9375rem / 1.6, antialiased. Type idioms: **mono uppercase eyebrows** 0.58–0.66rem, letter-spacing 0.12–0.18em; page titles `clamp(1.5rem,3vw,2rem)` w600 ls −0.02em; splash 3rem w800 ls −0.03em; stat numbers 2–2.5rem w700 `font-variant-numeric: tabular-nums`.

**Spacing:** `--space-card: clamp(14px,2.5vw,24px)`; `--space-section: clamp(16px,3vw,28px)`.

**Motion tokens:** `--ease-spring: cubic-bezier(0.34,1.56,0.64,1)`; `--ease-smooth: cubic-bezier(0.4,0,0.2,1)`; `--ease-out: cubic-bezier(0.22,0.61,0.36,1)`; durations 150/250/400ms. Hard rule from the file header: *"Theme swaps must be instant: nothing here transitions background-color or color on :root or body. Animate only transform, border-color, and opacity."*

**Grain texture:** `.paper::after` overlay, `url(/grain.svg)` tiled 180px, `opacity: 0.6`, `mix-blend-mode: overlay`. grain.svg = `<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>`.

**Theming machinery:** `data-theme` attr on `<html>`; inline pre-hydration localStorage script in app.html + SSR cookie injection in hooks.server.ts (no first-paint flash). Sage hue personalized from Discord accent color via sRGB→Oklab hue extraction, avatar fallback (16×16 canvas sample, chroma²-weighted circular mean), triadic companions (+120°/+240°), culori `clampChroma` gamut-safe.

**OLED adaptation for WTL-DLLM:** `--void` is 15.5% lightness (#090e0a), not true black → set `--void: oklch(0% 0 0)` (#000) and keep surfaces at 18–28% lightness; starfield sits on the void so it gains contrast for free.

## E. Performance Patterns

1. **Canvas, not DOM, for the ambient layer** — 1 canvas, ≤192 arcs/frame, single rAF, `z-index:-1`.
2. **DPR capped at 2.**
3. **Transform/opacity/border-color-only transitions**; theme switching instant (no repaint storm).
4. **prefers-reduced-motion, three layers deep:** global CSS kill; SSR-safe JS helper; every animated component checks it (starfield → static frame; tilt → disabled; CountUp → jump to final; StatNumber reel → no transition).
5. **Passive pointermove** + per-frame lerp (0.04) instead of per-event work.
6. `will-change: transform` used exactly once (StatNumber digit reel).
7. **backdrop-filter sparingly** (drawer backdrop blur(2px); sidebar recipe: `color-mix(in oklch, var(--void) 78%, transparent)` + blur(6px)).
8. GSAP confined to one micro component (SpringReveal: opacity 0→1, y 10→0, 0.3s power2.out); motion constants: SPRINGS `elastic.out(1,0.5)` / `back.out(1.7)`, DURATIONS STAGGER 30 / FEEDBACK 150 / COUNTER 400 ms.
9. Mobile: 44px touch targets, 16px inputs, swipe thresholds (>100px, angle <25°), `100dvh` with fallback.
10. Extreme case: public `/observatory` page is zero-JS, zero-webfont, zero-image (server-rendered SVG/CSS charts, 3 requests).
11. Build ships .br/.gz precompressed; `data-sveltekit-preload-data="hover"`.

## F. Live-Site Observations (2026-07-25)

- Computed styles on `/changelog` match local source verbatim (theme attr, oklch bg, 2px radii, sage tokens, hairline shadows, starfield canvas present at z −1).
- Production `/` auto-navigates to Discord OAuth after ~5–6s; dashboard auth-gated — tilt/glare verified from source only, not live.
- `theme-color` meta is `#c850c0` (legacy magenta) — mismatched with sage theme, also in local repo.

## G. reactbits.dev Verified Components

Catalog: Text Animations (23), Animations (32), Components (40), Backgrounds (44). Best fits, props verified:

1. **Galaxy** (backgrounds) — WebGL starfield: `density`, `starSpeed`, `hueShift` (default 140, near sage), `twinkleIntensity`, `glowIntensity`, `mouseInteraction`, **`mouseRepulsion` + `repulsionStrength`** (built-in occlusion), `transparent`, `disableAnimation`.
2. **Dot Grid** (backgrounds) — `dotSize` 16, `gap` 32, `proximity` 150px cursor radius, click shockwave, inertia.
3. **Pixel Snow** (backgrounds) — **`variant: "square"` default**, `density` 0.3, `direction` 125°, `depthFade` 8 — closest ready-made square-star drift.
4. **Spotlight Card** (components) — cursor-following radial gradient; same pattern as pawtropolis `.metric-glare`.
5. **Glare Hover** (animations) — `glareAngle` −45, `glareSize` 250%, 650ms; `borderRadius` prop (set 0).
6. **Decrypted Text** (text) — scramble→resolve; `speed` 50ms, `sequential`, `revealDirection`, `animateOn` — direct visual metaphor for token denoising.
7. Name-verified extras: Particles, Grid Scan, Ripple Grid, Letter Glitch, Faulty Terminal, Scrambled Text, Count Up, Star Border, Pixel Card, Pixel Trail, Electric Border, Dark Veil, Aurora, Hyperspeed, Target Cursor.

Caveat: React components (WebGL/OGL/GSAP-heavy) — for a Svelte visualizer, **port the math/patterns, not the components**; WebGL backgrounds cost more than pawtropolis's 2D canvas.

## H. Reusable Recipe — Rebuilding Fresh

1. **Token layer first:** one CSS file, everything OKLCH derived from seed `--accent-h` + `--accent-c`; neutrals get tiny chroma (0.012–0.016) at the same hue. Retheme = change two numbers. WTL-DLLM: hue 152, `--void: oklch(0% 0 0)` (OLED), surfaces 18–28%.
2. **Square system:** every radius token 2px (or 0). Tick-rule motif: rotated 6px square + uppercase mono label + dashed hairline.
3. **Flat depth:** hairline top-highlight shadows; hierarchy from 1px borders (3 weights) + 3 surface steps. Accent = 3px left border / `inset 2px 0 0` for active states.
4. **Starfield:** port Section B constants wholesale. For square stars swap `ctx.arc` → `ctx.fillRect(px-r, py-r, r*2, r*2)`; everything else unchanged.
5. **Occlusion/glare:** pointermove sets `--mx/--my/--glare`; overlay paints `radial-gradient(220px …accent/0.14, transparent 60%)`, 150ms opacity. Optional 5° `perspective(700px)` tilt. Gate on reduced-motion + `(hover: hover)`.
6. **Type:** one variable sans + Space Mono for eyebrows/labels/digits. Eyebrow: mono 0.6rem uppercase tracking 0.12–0.18em. `tabular-nums` on numbers. Negative tracking on big headings.
7. **Grain:** 180px feTurbulence tile, opacity 0.6, overlay blend, surfaces only.
8. **Motion discipline:** 3 durations (150/250/400ms), 3 easings, transform/opacity/border-color only, instant theme swap, reduced-motion gates everywhere, mount reveals opacity+y(10px) ~300ms stagger 30ms.
9. **Shell:** sidebar + transparent main over starfield; tick-rule sections, not nested boxes; cards = surface + 1px line-soft + `--space-card`.
10. **Theme boot:** `data-theme` + pre-hydration inline script (no flash).
11. **Frame budget:** background fixed cost (~120 arcs + clearRect); denoise animation on its own layer; CountUp pattern (`1-(1-t)^3`, ~850ms) and slot-reel digit strips (translateY, will-change, mask-image fade) for counters.

## I. Other Load-Bearing Details

- **A11y:** `:focus-visible { outline: 2px solid var(--sage); outline-offset: 2px }`; canvas aria-hidden; role/tabindex/Enter+Space on clickable divs; thin 6px scrollbars.
- **Persistence:** consent-gated cookies + localStorage dual-write. Keys: `paw-theme`, `paw-font`, `paw-sage-h/c`, `paw-star-density/speed`.
- **Personalization as a feature:** ThemePanel drawer exposes theme/font/hue (90–320°)/chroma (0.02–0.16)/star density/drift — all live, all persisted. Token system proven fully swappable (same components reskin to Win95 without markup changes).
- No sound, no easter eggs in web/src.
- **Unverified:** service-worker origin; dashboard tilt/glare live behavior (auth gate); Dot Field props.
