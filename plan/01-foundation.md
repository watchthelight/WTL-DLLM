---
title: "phase 01 — foundation"
author: "<wtl>"
project: wtl-dllm
phase: 1
tags: [plan, git, scaffold, conventions]
---

# Phase 01 — Foundation

Repo birth, identity, conventions, scaffold, GitHub. Micro-commits start here: this phase alone should produce 15+ commits.

## Story 1 — git + identity + voice

- `git init` in the repo root (this folder). Default branch `main`.
- Repo-local config: `git config user.name "watchthelight"` and `git config user.email "admin@watchthelight.org"`. Verify with `git config user.name`. Do NOT touch global config.
- Sample the voice: `git -C ..\pawtropolis-tech log --oneline -60`. Note message length, casing, phrasing habits. Your commits mimic that voice for the rest of the project.
- Acceptance: `git log` empty, config correct, voice notes absorbed.

## Story 2 — scaffold + ignore + license

- Create the tree (empty dirs get `.gitkeep` only where needed):
  ```
  plan/  research/  docs/  docs/results/  docs/journal/
  dllm/  dllm/data/  dllm/model/  dllm/train/  dllm/eval/  dllm/serve/
  ui/  scripts/  tests/  runs/
  ```
- `.gitignore`: `runs/` (except `.gitkeep`), `__pycache__/`, `.venv/`, `*.pt`, `*.ckpt`, `node_modules/`, `ui/dist/`, `.pytest_cache/`, `*.egg-info/`, `.DS_Store`, `Thumbs.db`, `docs/results/env.json` stays COMMITTED (do not ignore).
- `LICENSE`: MIT, copyright 2026 watchthelight.
- Commits: scaffold, gitignore, license — separate commits.

## Story 3 — `docs/conventions.md` (the header grammar)

Write this spec verbatim into the doc (it is what `lint_headers.py` enforces and what graphify will parse later):

**Code files** (py/ts/js/svelte/css — use the language's line-comment syntax; svelte/css use `/* ... */` block):
```
# wtl-dllm · dllm/model/sampler.py
# what: maskgit-style unmasking loop with frame capture
# why:  the ui replays these frames; determinism matters
# by:   <wtl> watchthelight
# tags: sampler, inference
```
Rules: line 1 = `wtl-dllm · <repo-relative-path>`; `what:` one line; `why:` one line (only when non-obvious — may be omitted); `by:` always exactly `<wtl> watchthelight`; `tags:` 1–4 lowercase comma-separated. Max 5 lines. No dates, no version numbers, no license boilerplate in headers.

**Markdown files**: YAML frontmatter with at minimum `title`, `author: "<wtl>"`, `project: wtl-dllm`, `tags: [...]`.

**Exempt:** LICENSE, .gitignore, lockfiles, generated assets, `research/raw/*`, JSON/CSV data files.

Commit the doc.

## Story 4 — `CLAUDE.md`

Short (≤25 lines), humanized. Contents: what this repo is (one paragraph), pointer to `plan/00-begin.md` as the law of the land, the three non-negotiables restated in one line each (watchthelight-only commits, tiny commits, headers), and where research lives. No corporate tone.

## Story 5 — `README.md` stub

A stub that reads human: project name, one-sentence what ("a small diffusion language model you can watch think — trained from scratch on this laptop"), an honest "status: building" line, license line. Full rewrite happens in phase 11 — keep the stub under 20 lines. Humanize rules apply.

## Story 6 — `scripts/probe_env.py`

Probes the machine and writes `docs/results/env.json` + prints a summary:
- Python version; torch present? version, `torch.cuda.is_available()`, device name, VRAM total (via `torch.cuda.get_device_properties`), bf16 support (`torch.cuda.is_bf16_supported()`), CPU count, RAM (via `psutil` if present else skip gracefully).
- Must run cleanly even with NO torch installed (report "torch: not installed" and still write the JSON).
- Prints a preset recommendation: no CUDA → `cpu-5m`; VRAM < 9 GB → `gpu-10m`; ≥ 9 GB → `gpu-17m` (with `gpu-30m` noted as optional).
- Run it. Commit script + the produced `env.json`.

## Story 7 — `scripts/lint_headers.py`

Walks the repo (respecting the exempt list from conventions), validates headers per the grammar, prints violations with paths, exit code 1 on any violation. Include `--fix-dry` flag that only lists what it *would* flag. Test it on the current tree (plan/ and docs/ files should pass; fix any that don't). Commit.

## Story 8 — environment setup

- Python env: `uv venv && uv pip install ...` if `uv --version` works, else `python -m venv .venv` + pip. Install now: `torch` (CUDA wheel if story 6 found a GPU, else CPU wheel), `pytest`, `numpy`. (fastapi/uvicorn/websockets arrive in phase 09.)
- Record exact install commands in `docs/journal/` first entry (dated, humanized, short).
- Commit journal entry (env itself is gitignored).

## Story 9 — GitHub

- Check `gh auth status`. If not authenticated: tell the user to run `! gh auth login`, and WAIT for them — this is one of the two legitimate pauses. Local commits are already safe meanwhile.
- `gh repo create WTL-DLLM --public --source . --remote origin --push`. If the name is taken under the account, ask the user; do not pick a different name silently.
- Verify: `gh repo view --json url,visibility`. Public. Push everything.
- Commit any stragglers, push again.

## Phase close

Acceptance: repo public on GitHub, ≥15 commits, all files headered, lint passes, env.json committed, python env importable (`python -c "import torch"`). One-line status to user. → `plan/02-product.md`.
