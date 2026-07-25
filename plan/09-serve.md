---
title: "phase 09 — server"
author: "<wtl>"
project: wtl-dllm
phase: 9
tags: [plan, server, websocket]
---

# Phase 09 — Server

`dllm/serve/`. Thin bridge: sampler frames → WebSocket → browser. Localhost only. Port **7311**.

## Story 1 — deps + app

- Install into the env: `fastapi`, `uvicorn[standard]`, `websockets`, `pydantic`. Pin versions in a `requirements.txt` at repo root (torch line included, matching what's installed). Commit.
- `dllm/serve/app.py`:
  - `GET /api/info` → `{model: <run-name>, preset, params, device, levels: [1..5 available], ckpt_step, vocab_size}`.
  - `GET /api/levels` → per-level metadata (canvas_len, example prompt) so the UI never hardcodes.
  - `WS /ws/generate`: accepts one JSON request per the architecture contract (`level|prompt`, `canvas_len`, `steps`, `ordering`, `temperature`, `throttle_ms`, `infill`, `seed`), validates with pydantic, streams every frame as JSON text, sleeps `throttle_ms` between frames (default 0; the UI drives playback speed), closes after the final frame. Errors → one `{error: msg}` frame, close.
  - Checkpoint path via `--ckpt` CLI arg or `WTL_CKPT` env var; model loaded once at startup on the probed device; `--stub` flag loads the stub model instead.
  - CORS: allow `http://localhost:5173` only.

## Story 2 — stub model

- `dllm/serve/stub.py`: fake model + sampler producing deterministic plausible frames for any request (reveals a canned answer over N steps). Purpose: UI development (phase 10) never waits on training, and server tests don't need torch checkpoints.

## Story 3 — tests `tests/test_serve.py`

- FastAPI TestClient + websocket: request on stub → correct frame count, schema-valid frames (validate every key), final frame has `done`/`answer`/`verdict`, throttle honored approximately, bad request → error frame.

## Story 4 — run it

- `python -m dllm.serve --stub` → hit `/api/info`, run one WS generation via a tiny python client script, confirm frames. Then once with the real G1 checkpoint. Journal note on real per-step latency (this number sets the UI's animation budget; at ~10M params expect single-digit ms per step on GPU, tens on CPU — record the truth).

## Phase close

Commits per story, pytest green, latency number recorded. One-line status. → `plan/10-ui.md`.
