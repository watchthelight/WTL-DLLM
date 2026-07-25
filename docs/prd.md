---
title: "prd"
author: "<wtl>"
project: wtl-dllm
tags: [docs, product, requirements]
---

# PRD

One local app. Left rail: controls. Center: a token canvas where a math answer denoises in real time. Behind everything: a square starfield with mouse parallax. Nothing leaves the machine.

## Task ladder

The model's entire world, all machine-generated, all symbolic. No word problems — ever. (The research record shows small-model math transfer failing exactly there; see the dossier.)

| Level | Task | Example |
|---|---|---|
| L1 | single-op add/sub, operands ≤ 2 digits, results ≥ 0 | `47+58=105` |
| L2 | multiply / exact divide | `12*7=84` · `84/7=12` |
| L3 | 3–4 digit add/sub with carries, two-op precedence | `1847+2596=4443` · `3+4*5=23` |
| L4 | solve for x, integer solutions | `7x+3=52,x=7` |
| L5 | countdown: reach target from given numbers | `3,7,25:46=25+3*7` |

Fixed answer formats, fixed canvas length per level, `[EOS]` then `[PAD]` termination.

## Features and acceptance

1. **Data engine** — seeded leveled generator, frozen and fresh corpus modes, perturbed eval sets disjoint from train. AC: data tests green; string-exact leakage check reports zero overlaps.
2. **Model + objective** — bidirectional transformer (presets 5M/10M/17M/30M), masked-diffusion loss per the LLaDA recipe, AR twin on the same trunk behind a `causal` flag. AC: unit tests green; param counts within 15% of preset names.
3. **Trainer** — resumable, JSONL metrics, runs on CPU and on the probed GPU preset. AC: smoke run completes with decreasing loss.
4. **Sampler** — four unmasking orderings, temperature 0 default, per-step frame capture, infill mode. AC: determinism test green; committed tokens never change (enforced by test).
5. **Eval** — exact-match checker, per-level accuracy on perturbed holdouts, AR-twin side-by-side, ordering ablation. AC: harness runs end-to-end on a smoke checkpoint; every reported number carries its eval config.
6. **Server** — FastAPI, WebSocket streaming one frame per denoise step, localhost only, port 7311. AC: stub-model websocket test green.
7. **UI** — Svelte 5, OLED alpine/sage tokens, square starfield with parallax and pointer occlusion, denoise board with confidence-binned commits, reduced-motion support. AC: `npm run build` clean; live frames render from the server.

## Non-goals

Speed claims of any kind. Self-correction claims (committed tokens are frozen and the UI shows that truthfully). Word problems. Digit lengths beyond training ranges. Serving anything beyond localhost.

## Success

- **G1 coherence** — ≥95% well-formed outputs on 200 held-out L1 prompts, reported next to the AR twin's number.
- **G2 accuracy** — target ≥90% exact-match on L1 *perturbed* eval; the real number ships regardless. L2/L3 attempted if L1 lands; L4/L5 stretch.
- **G3 demo** — the full loop live on this machine, smooth, honest.
