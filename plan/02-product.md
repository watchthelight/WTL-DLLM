---
title: "phase 02 — brief + prd"
author: "<wtl>"
project: wtl-dllm
phase: 2
tags: [plan, bmad, product]
---

# Phase 02 — Product (BMAD: Analyst + PM)

Two documents. Written like a sharp human PM wrote them — humanize rules, specific numbers, no filler. Source of truth for claims: `research/supersearch-dllm-dossier.md` (cite it inline where a decision leans on evidence).

## Story 1 — `docs/brief.md`

Sections: the itch (why build this), what exists (LLaDA/Dream at 8B — unrunnable locally for training; tiny-diffusion at 10.7M — no math; nothing occupies "laptop-trained + math + watchable"), the bet (domain restriction substitutes for scale — TinyStories; masked diffusion = generative BERT — 4-group convergence), the honest risk paragraph (0-for-2 prior laptop attempts, gibberish is a real possible outcome, that's why gates exist), what done looks like (three gates, one demo). ≤ 700 words.

## Story 2 — `docs/prd.md`

**Product:** a local app. Left: controls. Center: a token canvas where a math answer denoises live. Background: square starfield with mouse parallax. Everything runs on this machine.

**Task ladder (the entire model scope):**
- **L1** single-op arithmetic: `a+b=`, `a-b=` (a,b ≤ 2 digits, non-negative results)
- **L2** `a*b=`, `a/b=` (exact division only)
- **L3** multi-digit add/sub with carries (3–4 digits) + two-op expressions with precedence `a+b*c=`
- **L4** solve for x: `ax+b=c` (integer solutions)
- **L5** countdown-style: `use 3,7,25 to make 46:` → expression
All problems machine-generated, fixed answer formats, symbolic only — **no word problems, ever** (evidence: transfer failure documented in dossier).

**Features with acceptance criteria:**
1. Data engine — seeded, leveled, frozen + fresh modes, perturbed eval disjoint from train (string-exact check). AC: `pytest tests/test_data*` green; leakage check 0 overlaps.
2. Model + objective — bidirectional transformer presets 5M/10M/17M/30M, masked-diffusion loss, AR twin sharing the trunk. AC: unit tests green; param counts within 15% of preset names.
3. Trainer — resumable, JSONL metrics, works CPU-only and on the GPU preset from `env.json`. AC: smoke run completes; loss decreases on smoke corpus.
4. Sampler — 4 orderings, temp-0 default, frame capture, infill. AC: determinism test green.
5. Eval — exact-match on perturbed holdouts, per-level table, AR-twin side-by-side. AC: harness runs end-to-end on a smoke checkpoint.
6. Server — WS streaming of per-step frames. AC: stub-model websocket test green.
7. UI — starfield + denoise board + controls, OLED alpine/sage, reduced-motion support. AC: `npm run build` clean; live demo renders frames from server.

**Non-goals (verbatim into the doc):** speed claims of any kind; self-correction claims; word problems; length generalization beyond trained digit counts; serving anyone but localhost.

**Success = gates:** G1 coherence, G2 accuracy (≥90% L1 perturbed target — report truth), G3 live E2E demo.

## Phase close

Both docs committed (separate commits), headers/frontmatter present, humanized (read them once aloud-in-your-head; kill anything that sounds like a press release). One-line status. → `plan/03-architecture.md`.
