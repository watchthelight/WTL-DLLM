# wtl-dllm · dllm/serve/app.py
# what: fastapi bridge — sampler frames out over a websocket, localhost only, port 7311
# by:   <wtl> watchthelight
# tags: serve, websocket, api

import argparse
import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dllm.data.generator import CANVAS, MathGen, prompt_len
from dllm.eval.checker import grade
from dllm.serve.stub import stub_frames

ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(title="wtl-dllm")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

STATE: dict = {"stub": True, "model": None, "tok": None, "ck": None, "device": "cpu"}


class GenRequest(BaseModel):
    level: int | None = Field(default=None, ge=1, le=5)
    prompt: str | None = None
    canvas_len: int | None = None
    steps: int | None = Field(default=None, ge=1, le=64)
    ordering: str = "confidence"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    throttle_ms: int = Field(default=0, ge=0, le=2000)
    seed: int | None = None
    infill: dict | None = None  # {prefix, suffix, hole_len}


def load_real(ckpt_path: Path):
    import torch

    from dllm.eval.harness import load_ckpt
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tok, ck = load_ckpt(ckpt_path, weights="raw", device=device)
    STATE.update(stub=False, model=model, tok=tok, ck=ck, device=device,
                 ckpt_name=ckpt_path.parent.name, ckpt_step=ck["step"])


@app.get("/api/info")
def info():
    if STATE["stub"]:
        return {"model": "stub", "preset": "stub", "params": 0, "device": "none",
                "levels": sorted(CANVAS), "ckpt_step": 0, "vocab_size": 22}
    m, ck = STATE["model"], STATE["ck"]
    return {"model": STATE["ckpt_name"], "preset": ck["preset"],
            "params": m.param_count(), "device": STATE["device"],
            "levels": sorted(CANVAS), "ckpt_step": ck["step"],
            "vocab_size": len(STATE["tok"].vocab)}


@app.get("/api/levels")
def levels():
    out = {}
    for lv in sorted(CANVAS):
        ex = MathGen(99, lv).sample()
        out[lv] = {"canvas": CANVAS[lv], "example": ex,
                   "prompt": ex[: prompt_len(ex, lv)]}
    return out


async def _stream(ws: WebSocket, req: GenRequest):
    if STATE["stub"]:
        problem, frames = stub_frames(req.level or 1, seed=req.seed or 0, steps=req.steps)
        level = req.level or 1
        for f in frames:
            if f.get("done"):
                f["verdict"] = grade(problem, f.get("answer", ""), level)
            await ws.send_text(json.dumps(f))
            if req.throttle_ms:
                await asyncio.sleep(req.throttle_ms / 1000)
        return

    from dllm.model.sampler import generate, infill
    tok = STATE["tok"]
    loop = asyncio.get_event_loop()

    if req.infill:
        pre = [tok.t2i[c] for c in req.infill["prefix"]]
        suf = [tok.t2i[c] for c in req.infill["suffix"]]
        _, frames = await loop.run_in_executor(None, lambda: infill(
            STATE["model"], tok, pre, suf, req.infill["hole_len"],
            steps=req.steps, ordering=req.ordering, temperature=req.temperature,
            seed=req.seed))
        problem, level = None, None
    else:
        level = req.level or 1
        if req.prompt is not None:
            problem, text = None, req.prompt
        else:
            problem = MathGen(req.seed if req.seed is not None else 0, level).sample()
            text = problem[: prompt_len(problem, level)]
        canvas = req.canvas_len or CANVAS[level]
        prompt_ids = [tok.t2i[c] for c in text]
        _, frames = await loop.run_in_executor(None, lambda: generate(
            STATE["model"], tok, prompt_ids, canvas, steps=req.steps,
            ordering=req.ordering, temperature=req.temperature, seed=req.seed))

    for f in frames:
        if f.get("done"):
            # sampler's answer is the full decoded canvas; grade only the region
            # the model actually generated
            full = f.get("answer", "")
            if problem:
                plen = prompt_len(problem, level)
                f["answer"] = full[plen:]
                f["verdict"] = grade(problem, f["answer"], level)
            else:
                f["answer"] = full[len(text):] if not req.infill else full
                f["verdict"] = "n/a"
        await ws.send_text(json.dumps(f))
        if req.throttle_ms:
            await asyncio.sleep(req.throttle_ms / 1000)


@app.websocket("/ws/generate")
async def ws_generate(ws: WebSocket):
    await ws.accept()
    try:
        raw = await ws.receive_text()
        try:
            req = GenRequest.model_validate_json(raw)
            await _stream(ws, req)
        except Exception as e:  # validation or generation failure -> one error frame
            await ws.send_text(json.dumps({"error": str(e)}))
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except RuntimeError:
            pass


def main():
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", type=Path, default=os.environ.get("WTL_CKPT"))
    ap.add_argument("--stub", action="store_true")
    ap.add_argument("--port", type=int, default=7311)
    args = ap.parse_args()
    if not args.stub and args.ckpt:
        load_real(Path(args.ckpt))
        print(f"loaded {args.ckpt}")
    else:
        print("serving STUB model — no checkpoint loaded")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
