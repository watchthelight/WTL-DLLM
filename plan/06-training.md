---
title: "phase 06 — training + gate g1"
author: "<wtl>"
project: wtl-dllm
phase: 6
tags: [plan, training, gate]
---

# Phase 06 — Trainer & Gate G1 (coherence)

`dllm/train/`. This phase carries the project's headline risk: both documented prior laptop attempts produced gibberish. G1 exists to find out which world we're in, honestly and early.

## Story 1 — `dllm/train/trainer.py`

- CLI: `python -m dllm.train --preset gpu-10m --level 1 --steps 20000 --mode diffusion|ar --data frozen|fresh --run-name <name>`.
- AdamW β=(0.9,0.95), wd 0.1, lr from config (default 3e-4; expose `--lr`), warmup 3%, cosine to 10% of peak, grad clip 1.0.
- Precision: bf16 autocast iff `env.json` says bf16 supported; else fp32. Never fp16+scaler (not worth the failure modes here).
- EMA decay **0.995** (NOT 0.9999 — the dossier's trap: at short runs a 0.9999 EMA is still mostly init noise). Keep raw and EMA weights; checkpoints store both.
- Checkpoint every 1000 steps + at end → `runs/ckpt/<run-name>/step{N}.pt` (model, ema, optimizer, step, config, vocab hash). `--resume` works.
- Metrics JSONL per 50 steps: loss, lr, tokens/s, elapsed, VRAM if CUDA. Tokens/s over time doubles as the thermal-throttle log.
- Every 1000 steps: sample 8 generations (greedy, steps=canvas) into the metrics file — watching quality evolve is the point of the whole project.
- Long runs: launch via background task mechanism; monitor via the metrics file; never block a foreground call for hours.

## Story 2 — smoke test `tests/test_train_smoke.py`

- 60 steps, cpu-5m preset, tiny synthetic corpus, both modes. Asserts: runs, loss at step 60 < loss at step 5, checkpoint loads back, resume continues step count.

## Story 3 — the G1 runs

- Build L1 frozen corpus (200k samples) if not present.
- Train **diffusion mainline** on the probe-recommended preset. Budget: whatever the hardware gives overnight-class wall-clock; judge from the metrics, not the clock — stop when loss plateaus or samples look done.
- Train **AR twin**: same preset, same data, same step budget.
- (Fresh-data arm postponed to phase 08 ablations — G1 is frozen-corpus only.)

## Story 4 — Gate G1 evaluation

- 200 held-out L1 prompts (`{a}{op}{b}=` given as protected prompt, answer region masked). Diffusion model, greedy, steps=canvas.
- **Well-formed** = output parses as digits then `[EOS]` then `[PAD]`s (correctness NOT required at this gate).
- G1 passes at ≥95% well-formed. Report *both* models' well-formed rate AND raw accuracy in `docs/results/g1.md` — table, eval config annotated, honest prose (humanized), sample outputs good and bad.
- **If G1 fails:** 3 retries max, one variable per retry, logged in g1.md: (1) lr → 1e-4, (2) preset one size up or down per loss behavior, (3) 3× steps. Still failing → **pivot**: write `experiments/fallback-encoder/` — fine-tune `distilbert-base-uncased` with variable mask rate on the L1 corpus (the gumran recipe, <100 lines; tokenizer caveat: DistilBERT WordPiece chunks digits — document the expected arithmetic penalty). Fallback becomes the demo path; mainline continues as documented experiment. g1.md states the outcome in its first line.

## Phase close

Commits throughout (trainer, smoke, configs, g1.md, journal entry on how the runs actually went). G1 verdict stated to user in one line. → `plan/07-sampling.md`.
