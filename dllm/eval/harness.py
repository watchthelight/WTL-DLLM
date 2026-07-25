# wtl-dllm · dllm/eval/harness.py
# what: run a checkpoint over an eval split, report accuracy + well-formed rate with full config
# why:  every number this repo claims comes from here, config attached, no exceptions
# by:   <wtl> watchthelight
# tags: eval, harness

import argparse
import json
from datetime import date
from pathlib import Path

import torch

from dllm.config import PRESETS
from dllm.data.generator import CANVAS, prompt_len
from dllm.eval.checker import grade
from dllm.model import Tokenizer, Transformer
from dllm.model.sampler import generate

ROOT = Path(__file__).resolve().parents[2]


def load_ckpt(path: Path, weights: str = "raw", device: str = "cpu"):
    ck = torch.load(path, map_location=device, weights_only=False)
    tok = Tokenizer(ck["vocab"])
    model = Transformer(PRESETS[ck["preset"]], len(tok), causal=(ck["mode"] == "ar")).to(device)
    state = ck["ema"] if weights == "ema" else ck["model"]
    model.load_state_dict({k: v.to(device) for k, v in state.items()})
    model.eval()
    return model, tok, ck


@torch.no_grad()
def ar_generate(model, tok, prompt_ids, canvas_len):
    """Greedy left-to-right for the twin."""
    device = next(model.parameters()).device
    ids = torch.tensor(prompt_ids, dtype=torch.long, device=device)
    while ids.shape[0] < canvas_len:
        nxt = model(ids[None])[0, -1].argmax()
        ids = torch.cat([ids, nxt[None]])
    return ids.tolist()


def run_eval(ckpt: Path, level: int, split: str, steps=None, ordering="confidence",
             temperature=0.0, seed=0, limit=None, weights="raw",
             data_dir: Path = None) -> dict:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tok, ck = load_ckpt(ckpt, weights=weights, device=device)
    data_dir = data_dir or ROOT / "runs" / "data"
    rows = [json.loads(l) for l in (data_dir / f"{split}_l{level}.jsonl").read_text().splitlines()]
    if limit:
        rows = rows[:limit]
    canvas = CANVAS[level]

    counts = {"correct": 0, "wrong": 0, "malformed": 0}
    bad_examples = []
    for i, r in enumerate(rows):
        text = r["text"]
        plen = prompt_len(text, level)
        prompt_ids = [tok.t2i[c] for c in text[:plen]]
        if ck["mode"] == "ar":
            out_ids = ar_generate(model, tok, prompt_ids, canvas)
        else:
            out_ids, _ = generate(model, tok, prompt_ids, canvas, steps=steps,
                                  ordering=ordering, temperature=temperature,
                                  seed=seed + i, capture=False)
        answer = tok.decode(out_ids)[plen:]
        verdict = grade(text, answer, level)
        counts[verdict] += 1
        if verdict != "correct" and len(bad_examples) < 10:
            bad_examples.append({"problem": text, "generated": answer, "verdict": verdict})

    n = len(rows)
    result = {
        "ckpt": str(ckpt.relative_to(ROOT)), "mode": ck["mode"], "weights": weights,
        "level": level, "split": split, "n": n,
        "steps": steps if steps is not None else "canvas",
        "ordering": ordering if ck["mode"] != "ar" else "left-to-right",
        "temperature": temperature, "seed": seed, "date": date.today().isoformat(),
        "accuracy": round(counts["correct"] / n, 4),
        "wellformed": round((counts["correct"] + counts["wrong"]) / n, 4),
        "counts": counts, "bad_examples": bad_examples,
    }
    return result


def append_results_row(result: dict):
    md = ROOT / "docs" / "results" / "results.md"
    if not md.exists():
        md.write_text("\n".join([
            "---", 'title: "results ledger"', 'author: "<wtl>"', "project: wtl-dllm",
            "tags: [results, ledger]", "---", "",
            "# Results ledger", "",
            "Every number with its full config. Append-only.", "",
            "| date | ckpt | mode | weights | level | split | n | steps | ordering | temp | seed | accuracy | wellformed |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|", "",
        ]))
    row = ("| {date} | {ckpt} | {mode} | {weights} | L{level} | {split} | {n} | {steps} | "
           "{ordering} | {temperature} | {seed} | {accuracy} | {wellformed} |").format(**result)
    with open(md, "a") as f:
        f.write(row + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", type=Path, required=True)
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--split", default="eval_perturbed",
                    choices=["eval", "eval_perturbed"])
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--ordering", default="confidence")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--weights", default="raw", choices=["raw", "ema"])
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()

    result = run_eval(args.ckpt, args.level, args.split, args.steps, args.ordering,
                      args.temperature, args.seed, args.limit, args.weights)
    print(json.dumps(result, indent=2))
    out = ROOT / "docs" / "results" / f"eval_{args.ckpt.parent.name}_{args.split}_l{args.level}_{args.weights}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    if not args.no_ledger:
        append_results_row(result)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
