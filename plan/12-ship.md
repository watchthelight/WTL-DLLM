---
title: "phase 12 — ship"
author: "<wtl>"
project: wtl-dllm
phase: 12
tags: [plan, release, audit]
---

# Phase 12 — Ship

Audits, push, tag, done. Nothing new gets built here; things get verified and released.

## Story 1 — header audit

- `python scripts/lint_headers.py` → zero violations. Fix any stragglers (each fix its own commit, e.g. "header pass on eval module").

## Story 2 — humanize audit

- Invoke the **humanize skill** in audit mode over: `README.md`, `docs/brief.md`, `docs/prd.md`, `docs/architecture.md`, all `docs/results/*.md` prose, all UI-visible strings (grep `ui/src` for user-facing text).
- Fix every flagged pattern. Commit per file or logical group ("de-slop readme", "prd wording pass").

## Story 3 — commit-log audit

- `git log --format='%an %ae'` → every commit is `watchthelight admin@watchthelight.org`. Any stray identity → STOP and report to user before any history surgery (do not rewrite history unprompted).
- `git log --grep` sweep for AI tells: `Co-Authored`, `Claude`, `generated`, `AI`, `assistant`, robot emoji. Must be zero hits (message text).
- Read the last 60 messages as a human would: consistent voice, small steps, believable rhythm. Note the verdict in the journal.

## Story 4 — release

- Everything committed, `git status` clean. Push.
- Tag: `git tag -a v0.1.0 -m "first light"` + push tag.
- `gh repo view --json url,visibility,description` — confirm public. Set repo description via `gh repo edit --description` (humanized one-liner, e.g. "a tiny diffusion language model you can watch do arithmetic — trained on a laptop") and topics: `diffusion`, `language-model`, `pytorch`, `svelte`, `from-scratch`.
- TODO cleanup: all tasks completed or explicitly closed with a note.

## Story 5 — the final summary (the ONLY long-form chat output of the whole run)

≤ 8 lines to the user:
- repo URL
- G1 / G2 / G3 verdicts with the real numbers
- model size, training wall-clock, hardware used
- how to launch (`scripts\run.ps1`)
- one honest sentence on what it can't do
- anything that pivoted or failed, named plainly

Then stop. No essay, no recap of the journey — the repo speaks for itself.
