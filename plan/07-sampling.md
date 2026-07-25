---
title: "phase 07 — sampler"
author: "<wtl>"
project: wtl-dllm
phase: 7
tags: [plan, sampler, inference]
---

# Phase 07 — Sampler

`dllm/model/sampler.py`. The decoder is a genuinely new subsystem (no AR analogue) and it feeds the UI — every step emits a frame. Honesty rule baked into the code: once a token commits, it never changes; the frames must reflect that.

## Story 1 — the loop

`generate(model, tokenizer, prompt_ids, canvas_len, steps=None, ordering="confidence", temperature=0.0, seed=None, capture=True) -> (ids, frames)`

- Canvas = prompt (protected, pre-committed) + masked answer region. `steps` default = number of masked positions (research: math tolerates the fewest shortcuts; steps≈length is the honest default).
- Per step: forward pass → probs over masked positions → score each masked position by the active **ordering**:
  - `random` — uniform (control arm; may beat confidence at tiny scale per dossier)
  - `confidence` — max prob
  - `margin` — top1 − top2
  - `entropy` — negative entropy
- Commit count per step: cosine schedule over remaining masks (MaskGIT lineage — few early, many late), always ≥1.
- Token choice: temperature 0 → argmax (math default). If temperature > 0: Gumbel noise in **float64** (the float32 Gumbel bug from the dossier — comment it in code).
- Frame capture per step, exactly the architecture schema: tokens (decoded), committed bools, conf floats (0.0 for still-masked), `just_committed` indices, done flag; final frame carries decoded answer.
- `torch.no_grad()`, works on CPU and CUDA, seeded RNG isolated from global state.

## Story 2 — infill mode

`infill(model, tokenizer, prefix_ids, suffix_ids, hole_len, **kw)` — prefix and suffix pre-committed, hole masked, same loop. This is the mechanism demo the evidence actually supports (bidirectional conditioning; AR structurally can't). Example target: `18+[MASK][MASK]=45` → `27`.

## Story 3 — semi-AR block stub

`generate_blockwise(..., block_len)` — left-to-right over blocks, diffusion within block. STUB ONLY: implement the signature + naive loop, mark clearly as a later milestone (dossier: don't spend risk budget here now). No UI exposure yet.

## Story 4 — tests `tests/test_sampler.py`

- Determinism: same seed → identical frame sequence (both temp 0 and temp 0.7).
- Monotonic commitment: committed set only grows; a committed token id never changes across frames (assert over all steps — this is the honesty invariant).
- Prompt protection: prompt tokens present and committed from frame 0.
- steps=1 (all-at-once) and steps=masked-count both terminate with zero masks.
- Infill: prefix/suffix untouched, hole filled.
- Ordering flag actually changes commit order on a fixed toy model.

## Phase close

Committed story-by-story, pytest green, one manual run against the G1 checkpoint with frames printed as text (mini terminal visualization — a taste of phase 10). One-line status. → `plan/08-eval.md`.
