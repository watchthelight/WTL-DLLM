---
title: "phase 03 — architecture"
author: "<wtl>"
project: wtl-dllm
phase: 3
tags: [plan, bmad, architecture]
---

# Phase 03 — Architecture (BMAD: Architect)

One document: `docs/architecture.md`. It fixes every interface so phases 04–10 never have to negotiate with each other.

## Story 1 — write `docs/architecture.md`

**Dataflow (mermaid diagram):**
`dllm/data generator → corpus files (runs/data/) → dllm/train trainer → checkpoints (runs/ckpt/) → dllm/model sampler → dllm/serve WS server → ui (browser)`
plus `dllm/eval` reading checkpoints + corpus, writing `docs/results/`.

**Component contracts (specify these exactly in the doc):**

1. **Corpus format** — JSONL: `{"text": "47+58=105", "level": 1, "split": "train|eval|eval_perturbed"}`. Tokenizer vocab emitted by datagen as `runs/data/vocab.json`: list of single-char tokens (digits atomic, ops, letters used by templates) + specials `[PAD] [MASK] [BOS] [EOS]`. Canvas = fixed per level (document the table, e.g. L1: 12 tokens; L5: 32).
2. **Model config presets** (dataclass in code, table in doc):
   | preset | d_model | layers | heads | ctx | ~params |
   |---|---|---|---|---|---|
   | cpu-5m | 256 | 6 | 8 | 64 | ~5M |
   | gpu-10m | 320 | 8 | 8 | 96 | ~10M |
   | gpu-17m | 448 | 8 | 8 | 128 | ~19M |
   | gpu-30m | 512 | 10 | 8 | 128 | ~32M |
   Pick default from `docs/results/env.json` (probe recommendation).
3. **Objective** — absorbing-state masked diffusion, LLaDA GUIDELINES recipe: per sequence `t ~ U(0,1)`, `p_mask = (1-ε)t + ε`, `ε = 1e-3`; mask each token i.i.d. with prob `p_mask`; loss = cross-entropy on masked positions only, each divided by `p_mask`, mean over batch. Antithetic t-sampling flag (pair t with 1−t within a batch). No time embedding anywhere (RADD/MDLM/MD4 proof — dossier).
4. **AR twin** — same trunk, `causal=True` flag switches attention mask + standard next-token CE. Twin trains with identical tokenizer/data/step budget. Purpose: every result ships as a diffusion-vs-AR pair (research mandate).
5. **Frame schema** (sampler → server → UI, one JSON object per denoise step):
   ```json
   {"step": 3, "total_steps": 12, "tokens": ["4","7","+","[MASK]","[MASK]"], "committed": [true, true, true, false, false], "conf": [0.98, 0.97, 0.99, 0.0, 0.0], "just_committed": [2], "done": false}
   ```
   Final frame adds `{"done": true, "answer": "105", "verdict": "correct|wrong|n/a"}`.
6. **Server API** — `GET /api/info` (model name, preset, params, device, levels); `WS /ws/generate` accepts `{level|prompt, canvas_len, steps, ordering, temperature, throttle_ms, infill: {prefix, suffix, hole_len}|null, seed|null}` and streams frames.
7. **UI** — Svelte 5 + Vite SPA, no SSR; talks only to localhost server; port **7311** for the server, Vite default 5173 for dev.

**Decision log (short rationale each, dossier-cited):** absorbing over uniform/hybrid noise (mature tooling; hybrid = stretch goal); char/digit-atomic tokenizer (BPE digit-chunking hurts arithmetic); fixed short canvases over block diffusion (block = later milestone); SDPA over flash-attn (Windows); Svelte hand-rolled CSS over component libraries (methodology port); external answer checker over self-correction (frozen commits are frozen).

**Risk register (from dossier Failure Modes, one line + mitigation each):** gibberish risk → G1 gate + pivot; EMA trap → 0.995 and eval raw+EMA both; confidence miscalibration → ordering ablation; thermal throttling → log tokens/s over time; eval self-deception → perturbed-by-construction holdouts; Windows toolchain → SDPA-only, deps pinned.

## Story 2 — config skeletons

Create `dllm/config.py`: preset dataclasses matching the table (model dims, training defaults: AdamW β=(0.9, 0.95), wd 0.1, lr 3e-4, warmup 3%, cosine decay to 10%, clip 1.0, EMA 0.995, batch sizes per preset). Unit-testable (`tests/test_config.py`: presets instantiate, param estimate function within 15%).

## Phase close

Doc + config committed (separate commits), tests green, headers present. One-line status. → `plan/04-data.md`.
