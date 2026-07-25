# wtl-dllm · dllm/train/trainer.py
# what: single-gpu trainer for the diffusion model and its ar twin
# why:  resumable, metrics on disk, samples logged — the run should explain itself later
# by:   <wtl> watchthelight
# tags: train, loop

import argparse
import json
import math
import time
from pathlib import Path

import torch

from dllm.config import PRESETS, TrainDefaults, default_preset
from dllm.data.build import is_heldout
from dllm.data.generator import CANVAS, MathGen, prompt_len
from dllm.model import Tokenizer, Transformer
from dllm.model.objective import ar_loss, diffusion_loss

ROOT = Path(__file__).resolve().parents[2]


class FreshBatcher:
    """Never-repeating stream for --data fresh; skips heldout instances so the
    eval_heldout claim survives fresh sampling too."""

    def __init__(self, level: int, tok: Tokenizer, seed: int):
        self.gen = MathGen(seed * 7919, level)
        self.level, self.tok = level, tok
        self.canvas = CANVAS[level]

    def batch(self, n: int, device):
        texts = []
        while len(texts) < n:
            s = self.gen.sample()
            if not is_heldout(s):
                texts.append(s)
        ids = torch.tensor([self.tok.encode(t, canvas=self.canvas) for t in texts],
                           dtype=torch.long, device=device)
        plens = torch.tensor([prompt_len(t, self.level) for t in texts],
                             dtype=torch.long, device=device)
        return ids, plens


def load_corpus(level: int, tok: Tokenizer, data_dir: Path):
    rows = [json.loads(l) for l in (data_dir / f"train_l{level}.jsonl").read_text().splitlines()]
    canvas = CANVAS[level]
    ids = torch.tensor([tok.encode(r["text"], canvas=canvas) for r in rows], dtype=torch.long)
    plens = torch.tensor([prompt_len(r["text"], level) for r in rows], dtype=torch.long)
    return ids, plens


class EMA:
    def __init__(self, model, decay):
        self.decay = decay
        self.shadow = {k: v.detach().clone().float() for k, v in model.state_dict().items()}

    @torch.no_grad()
    def update(self, model):
        for k, v in model.state_dict().items():
            s = self.shadow[k]
            s.mul_(self.decay).add_(v.detach().float(), alpha=1 - self.decay)

    def state_dict(self):
        return self.shadow


def lr_at(step, total, cfg: TrainDefaults):
    warm = max(int(total * cfg.warmup_frac), 10)
    if step < warm:
        return cfg.lr * step / warm
    frac = (step - warm) / max(total - warm, 1)
    floor = cfg.lr * cfg.min_lr_frac
    return floor + 0.5 * (cfg.lr - floor) * (1 + math.cos(math.pi * frac))


@torch.no_grad()
def sample_greedy(model, tok, prompts, canvas, device):
    """Quick unmask-all-at-once-then-iterate preview; the real sampler comes in phase 07.
    Iterative: each round commit the single highest-confidence masked position."""
    model.eval()
    outs = []
    for p in prompts:
        ids = torch.tensor([tok.t2i[c] for c in p], dtype=torch.long, device=device)
        canvas_ids = torch.full((canvas,), tok.mask_id, dtype=torch.long, device=device)
        canvas_ids[: len(ids)] = ids
        masked = canvas_ids == tok.mask_id
        while masked.any():
            logits = model(canvas_ids[None])[0]
            probs = logits.softmax(-1)
            conf, pick = probs.max(-1)
            conf[~masked] = -1
            j = int(conf.argmax())
            canvas_ids[j] = pick[j]
            masked[j] = False
        outs.append(tok.decode_raw(canvas_ids.tolist()))
    model.train()
    return ["".join(t if len(t) == 1 else ("·" if t == "[PAD]" else f"<{t[1:-1]}>") for t in o) for o in outs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", default=None)
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--steps", type=int, default=20_000)
    ap.add_argument("--mode", choices=["diffusion", "ar"], default="diffusion")
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--data-dir", type=Path, default=ROOT / "runs" / "data")
    ap.add_argument("--data", choices=["frozen", "fresh"], default="frozen")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    cfg = TrainDefaults()
    preset = PRESETS[args.preset] if args.preset else default_preset()
    lr = args.lr or cfg.lr
    run = args.run_name or f"{args.mode}-l{args.level}-{preset.name}"
    out = ROOT / "runs" / "ckpt" / run
    out.mkdir(parents=True, exist_ok=True)
    metrics_path = out / "metrics.jsonl"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_bf16 = device == "cuda" and torch.cuda.is_bf16_supported()
    torch.manual_seed(args.seed)

    tok = Tokenizer.from_file(args.data_dir / "vocab.json")
    fresh = FreshBatcher(args.level, tok, args.seed) if args.data == "fresh" else None
    if fresh is None:
        data, plens = load_corpus(args.level, tok, args.data_dir)
        data, plens = data.to(device), plens.to(device)
    canvas = CANVAS[args.level]

    model = Transformer(preset, len(tok), causal=(args.mode == "ar")).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, betas=cfg.betas, weight_decay=cfg.weight_decay)
    ema = EMA(model, cfg.ema_decay)
    start = 0

    last = sorted(out.glob("step*.pt"))
    if args.resume and last:
        ck = torch.load(last[-1], map_location=device, weights_only=False)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        ema.shadow = ck["ema"]
        start = ck["step"]
        print(f"resumed {run} at step {start}")

    n = 0 if fresh else data.shape[0]
    gen = torch.Generator(device=device).manual_seed(args.seed + start)
    eval_prompts = None
    t0 = time.time()
    model.train()

    for step in range(start + 1, args.steps + 1):
        for g in opt.param_groups:
            g["lr"] = lr_at(step, args.steps, cfg) * (lr / cfg.lr)
        if fresh:
            x, pl = fresh.batch(preset.batch_size, device)
        else:
            idx = torch.randint(0, n, (preset.batch_size,), device=device, generator=gen)
            x, pl = data[idx], plens[idx]
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=use_bf16):
            loss = (diffusion_loss(model, x, prompt_lens=pl, antithetic=True, generator=gen)
                    if args.mode == "diffusion" else ar_loss(model, x, prompt_lens=pl))
        if loss is None:
            continue
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
        opt.step()
        ema.update(model)

        if step % cfg.log_every == 0:
            toks_s = preset.batch_size * canvas * cfg.log_every / max(time.time() - t0, 1e-9)
            rec = {"step": step, "loss": round(float(loss), 5), "lr": round(opt.param_groups[0]["lr"], 8),
                   "tok_s": int(toks_s), "elapsed_s": int(time.time() - t0)}
            if device == "cuda":
                rec["vram_gb"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
            with open(metrics_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            t0 = time.time()

        if step % cfg.sample_every == 0 and args.mode == "diffusion":
            if eval_prompts is None:
                texts = [json.loads(l)["text"] for l in
                         (args.data_dir / f"eval_l{args.level}.jsonl").read_text().splitlines()[:4]]
                eval_prompts = [t[: prompt_len(t, args.level)] for t in texts]
            outs = sample_greedy(model, tok, eval_prompts, canvas, device)
            with open(metrics_path, "a") as f:
                f.write(json.dumps({"step": step, "samples": outs}) + "\n")

        if step % cfg.ckpt_every == 0 or step == args.steps:
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                        "ema": ema.state_dict(), "step": step,
                        "preset": preset.name, "mode": args.mode, "level": args.level,
                        "vocab": tok.vocab},
                       out / f"step{step:07d}.pt")

    print(f"done: {run} at step {args.steps}, ckpts in {out}")


if __name__ == "__main__":
    main()
