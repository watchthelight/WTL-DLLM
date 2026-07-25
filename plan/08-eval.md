---
title: "phase 08 — eval + gate g2"
author: "<wtl>"
project: wtl-dllm
phase: 8
tags: [plan, eval, gate, ablation]
---

# Phase 08 — Eval Harness & Gate G2 (accuracy)

`dllm/eval/`. Every number this project ever claims comes from here, with its eval config attached. The dossier documented a field-wide pattern of inflated math numbers (MMaDA's wrong headline, config-dependent GSM8K swings, perturbation collapse) — this harness is the local antidote.

## Story 1 — `dllm/eval/checker.py`

- Parses model output for the answer segment (after `=` / after `x=` / expression for L5), numeric exact-match; L5: evaluate the expression, check it hits the target using only the given numbers. Returns `correct | wrong | malformed`.
- Unit tests incl. adversarial cases (leading zeros, `[PAD]` garbage after `[EOS]`, empty answer).

## Story 2 — `dllm/eval/harness.py`

- CLI: `python -m dllm.eval --ckpt <path> --level 1 --split eval|eval_perturbed --steps N --ordering X --temperature T`.
- Outputs: accuracy, well-formed rate, malformed examples (first 10), per-position error heatmap data (which answer digit fails most). Writes `docs/results/eval_<run>_<config>.json` + appends a row to `docs/results/results.md` — **every row carries: checkpoint, level, split, steps, ordering, temperature, seed, date.** No bare numbers anywhere in the repo.

## Story 3 — ablations `dllm/eval/ablate.py`

- Grid: orderings {random, confidence, margin, entropy} × steps {canvas, canvas/2, canvas/4} on L1 perturbed. CSV + a short honest write-up in `docs/results/ablation_ordering.md` (does confidence beat random at this scale? the dossier says unknown — this answers it locally).
- AR twin: same eval prompts, greedy decode, same checker → side-by-side table. This comparison ships in the README later; it must exist here first.
- Fresh-vs-frozen arm: train one additional diffusion run with `--data fresh` at the G1 budget, eval both. One-paragraph finding (the dossier's data-constrained debate, tested locally at toy scale — report direction only, no grand claims).

## Story 4 — Gate G2

- Headline metric: **L1 perturbed exact-match, steps=canvas, ordering=best-from-ablation, temp 0**.
- Target ≥90%. Whatever the true number is, it goes verbatim in `docs/results/g2.md` first line, with the config string. If <90%: one tuning iteration (data volume up ×2 OR steps budget up — pick from the error heatmap evidence), re-eval once, then accept and scope claims accordingly. If accuracy is strong, proceed to L2/L3 training runs (same trainer, next levels) as time allows and record per-level results; L4/L5 are optional stretch — attempt only if L1–L3 land ≥80%.
- g2.md: table of all levels attempted, diffusion vs AR twin, honest prose. No cherry-picking; malformed rate reported next to accuracy.

## Phase close

Commits per story, results docs in place, journal entry. G2 verdict to user in one line (the real number). → `plan/09-serve.md`.
