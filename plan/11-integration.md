---
title: "phase 11 — integration + gate g3"
author: "<wtl>"
project: wtl-dllm
phase: 11
tags: [plan, integration, gate, readme]
---

# Phase 11 — Integration & Gate G3 (the live demo)

Everything real, wired together, on this machine.

## Story 1 — real end-to-end

- Server with the best checkpoint from phase 08 (not the stub). UI dev build against it.
- Run every level that trained, plus infill mode, plus at least one wrong answer (find one via the eval malformed/wrong examples — watching it confidently commit a wrong digit is part of the honest demo).
- Measure: server per-step latency, browser frame time during playback (devtools MCP performance trace if available). Record both in `docs/results/e2e-latency.md`. If playback stutters: fix the render path (cell updates must be class/style toggles only, no layout thrash), not by hiding steps.

## Story 2 — `scripts/run.ps1`

- One command: activates the env, starts the server (real ckpt if present, else `--stub` with a loud banner), starts Vite dev server, prints the URL. `-Build` flag serves `ui/dist` via the FastAPI static mount instead of Vite. Clean Ctrl+C teardown of both processes.
- Test both paths. Commit.

## Story 3 — README rewrite (the repo's face)

Replace the stub. Sections, humanized, first person allowed:
1. What this is — two paragraphs, plain. A tiny diffusion language model, trained from scratch on a laptop, that you watch solve arithmetic by unmasking tokens. Why diffusion, in one honest sentence (bidirectional, order-free, and mostly: you can *see* it).
2. Screenshot (from G3 run) + a short GIF if tooling allows (optional, don't burn hours).
3. The honest numbers — the G1/G2 tables (diffusion vs AR twin, perturbed evals, configs attached). Include the negative findings; they're the credibility.
4. How it works — 10 lines: mask ratio t, weighted CE, unmasking loop; link `docs/architecture.md` and the dossier for depth.
5. Run it — `scripts\run.ps1`, requirements, hardware notes from `env.json`.
6. What it doesn't do — the honesty rails as user-facing prose (no speed claims, no self-correction, no word problems, digits-trained-only).
7. The research — one paragraph pointing at `research/` (this repo carries its own literature review; say so plainly).
8. License — MIT, watchthelight.

## Story 4 — Gate G3 + journal

- G3 checklist, each item verified live: server starts clean · UI connects · L1 denoise animates smoothly · ordering switch visibly changes commit order · infill fills a hole · verdict badge matches the checker · starfield parallax + glare working · reduced-motion honored (toggle OS setting or emulate) · `run.ps1` works from a cold shell.
- `docs/journal/` entry: what integration actually broke and how it got fixed (humanized, specific).

## Phase close

Commits per story. G3 verdict one line to user. → `plan/12-ship.md`.
