---
title: "journal — the perturbed wall, and fixing the eval design"
author: "<wtl>"
project: wtl-dllm
tags: [journal, eval, findings]
---

# 2026-07-25 — the perturbed wall

G1 passed clean — 100% well-formed, 100% accurate, both architectures, in-distribution. Then the perturbed split delivered the day's education: **8–11% accuracy**, with well-formedness intact at 99.4%. The model learned the format perfectly and the arithmetic only where it had seen the digits.

Two findings worth keeping:

1. **Random ordering beat confidence ordering** on the hard split (11.2% vs 8.4% at 8 steps). The research dossier flagged exactly this risk — tiny-model confidence calibration is bad enough that confidence-guided unmasking can lose to a coin flip. It does, here, measurably.

2. **My perturbed split was measuring the wrong thing.** I built leakage-proof eval by banding operand last digits (train gets 0–7, perturbed gets 8–9). Airtight, yes — but it means the model has *never seen an operand ending in 8 or 9*. That split doesn't ask "can you solve new problems?", it asks "can you extrapolate to censored digits?" — which is a known open research problem (digit/length generalization), not a fair capability bar for a 10M model. Worse, L1's instance space (~20k strings) is nearly exhausted by the corpus, so there was no honest "unseen instance" eval at all.

Fix: a third split. `eval_heldout` — a deterministic md5-based 10% instance holdout with full digit coverage. Train never touches those strings (enforced, checked), but every digit appears everywhere in training. That's the standard generalization claim and the new G2 headline. The band split stays in the harness as the extrapolation stress test it actually is, and its collapse is a *result*, not an embarrassment.

Retraining both models on the rebuilt corpus. PRD gets a dated amendment.
