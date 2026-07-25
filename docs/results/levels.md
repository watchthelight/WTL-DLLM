---
title: "per-level results"
author: "<wtl>"
project: wtl-dllm
tags: [results, levels]
---

# Per-level results

Same 10M trunk, same recipe, one model per level per objective. 20k steps each, ~13 min per run on the RTX 5070 Laptop. All rows: full 2,000-problem splits, steps = masked count, ordering = confidence, temperature 0; configs in the ledger.

| level | task | model | heldout | perturbed |
|---|---|---|---|---|
| L1 | 2-digit add/sub | diffusion | 1.000 | 0.258 |
| L1 | | ar twin | 0.999 | 0.092 |
| L2 | multiply / exact divide | diffusion | 0.215 | 0.000 |
| L2 | | ar twin | 0.215 | 0.000 |
| L3 | 3–4 digit carries, precedence | diffusion | 0.960 | 0.807 |
| L3 | | ar twin | 0.974 | 0.795 |

Well-formed: 1.000 in every cell. The models never babble; they only differ in whether the digits are right.

## What the spread says

**L3 is the vindication of the algorithm story.** Multi-digit addition/subtraction generalizes to unseen instances at 96–97%, and — the surprise — holds ~80% even on the censored-digit stress split that demolished L1. The likely mechanism: band censorship only constrains an operand's *final* digit, and L3's longer numbers let 8s and 9s appear freely in every other position, so the model learns the full digit algebra everywhere except one position and mostly bridges the gap. Carrying is an algorithm; algorithms transfer.

**L2 is the memorization ceiling, measured.** 21.5% heldout for *both* architectures — suspiciously identical, and the explanation is structural: multiplication facts you haven't seen aren't derivable from pattern, so the reachable heldout score is whatever commutativity (`7*12` trained → `12*7` answerable) and division-inverse pairs give you. Both objectives find exactly that. Perturbed L2 is 0.000 flat: `8*9` was never trained and nothing bridges to it. A 10M model does not invent multiplication.

**The diffusion-vs-AR gap is regime-dependent.** The dramatic 3× extrapolation edge lives at L1 (0.258 vs 0.092) and compresses to a statistical tie at L3 (0.807 vs 0.795, with AR ahead 0.974 vs 0.960 on heldout). One seed per cell — treat every gap smaller than a few points as noise. The honest claim: masked diffusion matched or beat its AR twin on every hard split here, decisively so exactly once.

Infill (mix-objective model, L1): 200/200 equation-valid operand fills on heldout problems, with heldout solve accuracy intact at 1.000 — capability added at no measured cost, after the `--prompt-mode mix` fix documented in the journal.
