---
title: "phase 05 — model + objective"
author: "<wtl>"
project: wtl-dllm
phase: 5
tags: [plan, model, diffusion, transformer]
---

# Phase 05 — Model & Objective

`dllm/model/`. The research's core finding, restated so it's never lost: this model is a bidirectional transformer trained with weighted masked cross-entropy. No time embeddings, no score matching, no SDE machinery. Five changes off nanoGPT.

## Story 1 — `dllm/model/tokenizer.py`

- Loads `runs/data/vocab.json`. `encode(str) -> list[int]`, `decode(ids) -> str`, special-token ids as properties. Char-level, digits atomic. Round-trip test.

## Story 2 — `dllm/model/transformer.py`

- Pre-norm transformer: token embedding (NO positional embedding table — RoPE in attention), `torch.nn.functional.scaled_dot_product_attention`, RoPE applied to q/k, GELU MLP (4× expansion), final LayerNorm, untied output head (tiny vocab makes tying pointless).
- Constructor takes the preset dataclass from `dllm/config.py` + `causal: bool = False`. `causal=True` builds the AR twin: identical trunk, causal attention mask. One model file, two behaviors — this twinning is a research mandate, not a convenience.
- No `[MASK]`-specific machinery in the trunk; the mask token is just vocab.
- `param_count()` helper; assert within 15% of preset label in tests.

## Story 3 — `dllm/model/objective.py`

The exact recipe (LLaDA GUIDELINES; dossier-verified):
```python
t = torch.rand(B)                      # per sequence
p_mask = (1 - EPS) * t + EPS           # EPS = 1e-3
mask = torch.rand(B, L) < p_mask[:, None]
noisy = torch.where(mask, MASK_ID, x)
logits = model(noisy)
loss = (F.cross_entropy(logits[mask], x[mask], reduction="none") / p_mask.expand(B, L)[mask]).sum() / (B * L)
```
- Never mask `[PAD]` positions after `[EOS]`? NO — mask everywhere within canvas (padding is part of the learned format; the model must learn to emit `[EOS]`+`[PAD]`), but exclude `[BOS]`.
- Antithetic flag: second half of batch uses `1 - t` of the first half.
- SFT-style prompt protection: `objective(..., prompt_len)` never masks positions `< prompt_len` (used from phase 06 on — the question is the prompt, the answer is what diffuses).
- AR twin loss: standard shifted next-token CE, same signature.
- 1% of training batches: replace canvas with a random shorter length (research: helps variable-length behavior).

## Story 4 — tests `tests/test_model.py`, `tests/test_objective.py`

- Forward shapes for all presets (CPU, batch 2).
- Loss finite at t→0 (ε floor prevents div-by-zero) and t→1 (all masked).
- Zero-masked-tokens batch: loss is 0/skipped, no NaN.
- Prompt protection: gradient of prompt positions' embeddings is zero when protected.
- Causal flag: with causal=True, logits at position i don't change when future tokens change (probe test).
- Determinism: fixed seed → identical loss twice.

## Phase close

Committed story-by-story, pytest green. One-line status. → `plan/06-training.md`.
