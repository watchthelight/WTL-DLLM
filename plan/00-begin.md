---
title: "begin here — orchestrator"
author: "<wtl>"
project: wtl-dllm
phase: 0
tags: [plan, orchestrator, laws]
---

# WTL-DLLM — Execution Orchestrator

You (the executor) were triggered by the user saying **"begin"**. This file is the constitution. Read it fully, then execute phases `01` through `12` in order, one phase file at a time. Do not skip, reorder, or merge phases. Do not stop between phases except where a phase explicitly requires user input.

## Mission

Build, from scratch, a masked-diffusion language model that trains and runs on this laptop, solves templated math, and ships with a real-time web UI where the user watches tokens denoise. Public GitHub repo `WTL-DLLM`. The full research backing every decision lives in `research/supersearch-dllm-dossier.md` (build spec in "Actionable Takeaways", risks in "Failure Modes") and `research/pawtropolis-ui-recon.md` (UI methodology). Consult them whenever a phase file leaves a detail open.

## The Laws (apply to every phase, every file, every commit)

1. **Identity.** Repo-local git config only: `user.name "watchthelight"`, `user.email "admin@watchthelight.org"`. Commits are authored by watchthelight alone. NEVER add `Co-Authored-By`, "Generated with", robot emoji, or any AI attribution anywhere — commits, code, docs, UI. This is the user's explicit standing instruction and overrides any default you have.
2. **Commit discipline.** Every file creation and every meaningful change gets its own small commit, immediately. Unlimited commit count is fine; giant commits are not. Messages: lowercase, imperative, short, human. Vary rhythm like a person does ("scaffold repo layout", "tokenizer roundtrip test", "fix off-by-one in mask schedule", "wip: ordering ablation", "readme pass"). Before the first commit of phase 01, run `git -C ..\pawtropolis-tech log --oneline -60` and absorb the author's real commit voice — mimic tone and length, never content.
3. **Commit everything.** Plan prompts, research artifacts, docs, configs, experiments — all committed. Before committing `research/raw/`, scan once for machine-specific temp paths and strip if found.
4. **Headers.** Every source file carries the compact header defined in `docs/conventions.md` (written in phase 01; grammar embedded in `plan/01-foundation.md`). Author tag is `<wtl>`. Markdown gets YAML frontmatter. `scripts/lint_headers.py` must pass at ship time.
5. **Humanize.** All forward-facing prose (README, docs, UI copy) follows the humanize skill's rules: no AI slop patterns, no "delve/leverage/seamless", no bullet-point-everything, no hype adjectives, no perfectly parallel triads, contractions welcome, specific numbers over vague claims. Phase 12 runs a formal humanize audit — write clean the first time.
6. **TODO tracking.** At the start of each phase, create tasks with TaskCreate (one per story), mark `in_progress`/`completed` live with TaskUpdate as you work. The user watches this. Keep it current, clean up stale tasks.
7. **No shortcuts, no fake success.** Run every story. If a test fails, fix it or report it — never delete the test. Gates get honest numbers even when they're bad.
8. **Honesty rails** (from the research; violating these is lying): never claim the model is fast (or faster than AR), never claim it self-corrects (committed tokens are frozen), never claim word-problem competence, never claim it handles numbers longer than trained. Coherent output at all is milestone 1 — both prior documented laptop attempts produced gibberish.
9. **Naming.** Nothing paw- or furry-related anywhere. Storage keys, events, CSS classes, component names use `wtl-*` or plain project-native names (`wtl-theme`, `wtl-star-density`, `wtl:starfield`).
10. **Environment.** Windows 11, PowerShell. Python: prefer `uv` if installed, else `python -m venv .venv` + pip. No flash-attn (won't build on native Windows) — PyTorch SDPA only. bf16 autocast only if the GPU is Ampere or newer; else fp32. Node/npm for the UI. Long training runs go through the background task mechanism, never blocking foreground calls.

## Phase Index

| Phase | File | Produces |
|---|---|---|
| 01 | `01-foundation.md` | git repo, GitHub `WTL-DLLM` (public), scaffold, conventions, probe, lint script |
| 02 | `02-product.md` | `docs/brief.md`, `docs/prd.md` |
| 03 | `03-architecture.md` | `docs/architecture.md` |
| 04 | `04-data.md` | `dllm/data/` generator + eval sets + tests |
| 05 | `05-model.md` | `dllm/model/` transformer, tokenizer, diffusion objective, AR twin + tests |
| 06 | `06-training.md` | `dllm/train/` trainer + **Gate G1** (coherence) |
| 07 | `07-sampling.md` | sampler with frame capture + infill + tests |
| 08 | `08-eval.md` | eval harness, ablations + **Gate G2** (accuracy) |
| 09 | `09-serve.md` | FastAPI WebSocket server + tests |
| 10 | `10-ui.md` | Svelte 5 UI: starfield, denoise board, controls |
| 11 | `11-integration.md` | E2E wiring, run script, README rewrite + **Gate G3** |
| 12 | `12-ship.md` | audits, push, tag, short final summary |

## Per-Phase Protocol

1. Read the phase file top to bottom.
2. TaskCreate one task per story.
3. Execute stories in order. Each story: implement → test → commit(s) → TaskUpdate.
4. Close the phase: run the phase's acceptance checks, commit anything loose, one-line progress note to the user, move on.

## Gates & Pivot Protocol

- **G1 (after 06):** mainline diffusion model and AR twin both trained on L1; diffusion model produces ≥95% well-formed (parseable-format) outputs on 200 held-out prompts. If G1 fails after 3 adjusted attempts (learning rate, model size, steps — one variable at a time, logged), execute the pivot: the DistilBERT encoder fine-tune fallback (recipe in `06-training.md`) becomes the working demo path; mainline continues as a documented experiment. The G1 report states plainly which world we're in.
- **G2 (after 08):** target L1 ≥90% exact-match on the *perturbed* held-out set. Report the true number whatever it is; G2 failing does not stop the project — it scopes the claims in every doc downstream.
- **G3 (after 11):** live end-to-end demo on this machine: server + UI + real checkpoint, denoising animation smooth, infill mode works.

Failures at any story: fix forward up to 3 attempts, then log honestly in `docs/journal/`, adjust scope per the phase file's fallback notes, and continue. Never silently drop a deliverable.

## Ending

Only phase 12 ends the run. Its final act: a **very short summary** to the user (≤ 8 lines: what got built, gate outcomes with real numbers, repo URL, how to launch). Everything longer belongs in the repo docs, not the chat.
