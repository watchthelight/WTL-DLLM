---
title: "conventions"
author: "<wtl>"
project: wtl-dllm
tags: [docs, conventions, headers]
---

# Conventions

Small rules, applied everywhere. The point: a stranger (or a graph tool) can sort any file in this repo by reading its first five lines.

## File headers

Every source file starts with a compact header. Code files use the language's comment syntax:

```python
# wtl-dllm · dllm/model/sampler.py
# what: maskgit-style unmasking loop with frame capture
# why:  the ui replays these frames; determinism matters
# by:   <wtl> watchthelight
# tags: sampler, inference
```

```ts
// wtl-dllm · ui/src/lib/ws.ts
// what: websocket client store for denoise frames
// by:   <wtl> watchthelight
// tags: ui, websocket
```

Svelte and CSS use `/* ... */` blocks with the same lines.

Rules:
- Line 1: `wtl-dllm · <repo-relative-path>` — exact path, forward slashes.
- `what:` one line, plain words.
- `why:` one line, only when the reason isn't obvious. Skip it otherwise.
- `by:` always exactly `<wtl> watchthelight`.
- `tags:` one to four, lowercase, comma-separated.
- Five lines max. No dates, no versions, no license text in headers.

Markdown files carry YAML frontmatter instead, with at least `title`, `author: "<wtl>"`, `project: wtl-dllm`, and `tags: [...]`.

Exempt: LICENSE, .gitignore, .gitattributes, lockfiles, generated assets, data files (json/csv/jsonl), and everything under `research/raw/`.

`scripts/lint_headers.py` enforces all of this. Run it before you call anything done.

## Commits

Conventional style with scopes, lowercase, imperative: `feat(data): seeded level generator`, `fix(sampler): clamp commit count on last step`, `chore(sync): regenerate results index`. Small commits, one concern each. No AI attribution of any kind — this repo is authored by watchthelight.

## Naming

Storage keys, events, and CSS custom things use the `wtl-` prefix (`wtl-theme`, `wtl-star-density`, event `wtl:starfield`). Python modules stay plain and short. Nothing cute borrowed from other projects.
