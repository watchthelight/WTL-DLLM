# wtl-dllm

A small masked-diffusion language model, built from scratch to run on one laptop, plus a web UI that shows the denoising live. The whole build is driven by the phase files in `plan/` — `plan/00-begin.md` is the law of the land; read it before touching anything.

Three rules that never bend:

- Commits are authored by watchthelight <admin@watchthelight.org>, nothing and nobody else — no co-author lines, no tool attribution.
- Small commits, one concern each, conventional style with scopes.
- Every source file gets the five-line header from `docs/conventions.md`.

Research backing every design call lives in `research/` — the dossier for the model side, the recon doc for the UI side. When a detail seems arbitrary, it probably isn't; check there first.
