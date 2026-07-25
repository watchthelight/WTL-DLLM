---
title: "phase 04 — data engine"
author: "<wtl>"
project: wtl-dllm
phase: 4
tags: [plan, data, generator]
---

# Phase 04 — Data Engine

`dllm/data/`. Everything the model ever sees is generated here. Determinism and train/eval separation are the whole point — sloppy data invalidates every result downstream.

## Story 1 — `dllm/data/generator.py`

- One seeded `MathGen(seed, level)` class, `sample() -> str` producing canonical strings:
  - L1: `47+58=105` · `82-19=63` (operands 1–2 digits, results non-negative)
  - L2: `12*7=84` · `84/7=12` (division exact by construction)
  - L3: `1847+2596=4443` · `703-458=245` (3–4 digit, carries/borrows guaranteed present in ≥50% of samples) · `3+4*5=23` (two-op precedence)
  - L4: `7x+3=52,x=7` (a in 2–12, integer x in 1–99, format exactly `{a}x{+|-}{b}={c},x={x}` — comma separator, space is not in the vocab)
  - L5: `3,7,25:46=25+3*7` (3–4 given numbers, target reachable by construction, `+ - *` only, answer is one valid expression)
- Character-level vocabulary: digits `0-9`, ops `+ - * / = x , :`, specials `[PAD] [MASK] [BOS] [EOS]`. Emit `runs/data/vocab.json` (ordered list; specials first). No letters beyond `x`.
- Canvas lengths (pad with `[PAD]` after `[EOS]`): L1 12 · L2 12 · L3 16 · L4 16 · L5 32. Document in module docstring.
- Perturbation function for eval sets: shift operand digit distributions to held-out ranges + resample templates with disjoint seeds (definition: an eval string may never appear in train — enforced, not hoped).

## Story 2 — corpus builder `dllm/data/build.py`

- CLI: `python -m dllm.data.build --level 1 --n 200000 --seed 1 --out runs/data/` → writes `train_l1.jsonl`, `eval_l1.jsonl` (2k), `eval_l1_perturbed.jsonl` (2k) per the architecture's JSONL schema.
- **Frozen mode** (default): fixed file, fixed seed. **Fresh mode**: `FreshSampler(level, seed)` iterator for the trainer that never repeats a seed epoch-to-epoch (the research's fresh-data arm).
- Leakage check built in: exact-string intersection of train vs both eval sets must be 0; builder fails loudly otherwise.

## Story 3 — `dllm/data/stats.py`

- Prints: sample count, unique ratio, length histogram, digit distribution, carry frequency (L3), answer-magnitude histogram. Writes `docs/results/data_stats_l{n}.md` when run with `--report`.

## Story 4 — tests `tests/test_data.py`

- Same seed → identical corpus (hash the first 1k samples).
- Every generated string round-trips through the vocab (no unknown chars).
- Division always exact (L2); x always integer (L4); L5 target always reachable (evaluate the emitted expression).
- Leakage check catches a planted duplicate (negative test).
- Perturbed eval distributions differ measurably from train (operand-range assertion).

## Phase close

All committed story-by-story, pytest green, L1 corpus actually built and stats reported. One-line status. → `plan/05-model.md`.
