# wtl-dllm · dllm/data/build.py
# what: build frozen corpora (train/eval/eval_perturbed jsonl) + vocab.json, with a hard leakage check
# by:   <wtl> watchthelight
# tags: data, corpus

import argparse
import json
from pathlib import Path

from .generator import CANVAS, VOCAB, MathGen

ROOT = Path(__file__).resolve().parents[2]


def build_level(level: int, n_train: int, n_eval: int, seed: int, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)

    def emit(gen: MathGen, n: int, split: str):
        rows, seen = [], set()
        for _ in range(n):
            s = gen.sample()
            rows.append({"text": s, "level": level, "split": split})
            seen.add(s)
        return rows, seen

    # eval draws the train distribution and MAY overlap train strings — at
    # small levels the discrete space is nearly exhausted, so this split
    # measures memorization+format. eval_perturbed is the honest
    # generalization number: operand bands disjoint from train by
    # construction, verified below.
    train, train_set = emit(MathGen(seed, level), n_train, "train")
    ev, _ = emit(MathGen(seed + 1, level), n_eval, "eval")
    evp, evp_set = emit(MathGen(seed + 2, level, perturbed=True), n_eval, "eval_perturbed")

    leak = train_set & evp_set
    if leak:
        raise SystemExit(f"leakage: {len(leak)} perturbed-eval strings appear in train, e.g. {sorted(leak)[:3]}")

    for name, rows in [("train", train), ("eval", ev), ("eval_perturbed", evp)]:
        with open(out / f"{name}_l{level}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    (out / "vocab.json").write_text(json.dumps(VOCAB, indent=2) + "\n")
    return {"level": level, "train": len(train), "eval": len(ev), "eval_perturbed": len(evp),
            "unique_train": len(train_set), "canvas": CANVAS[level]}


class FreshSampler:
    """Endless stream for --data fresh runs; reseeds every epoch so nothing repeats."""

    def __init__(self, level: int, seed: int):
        self.level, self.seed, self.epoch = level, seed, 0
        self._gen = MathGen(seed * 1000, level)

    def __iter__(self):
        return self

    def __next__(self) -> str:
        return self._gen.sample()

    def next_epoch(self):
        self.epoch += 1
        self._gen = MathGen(self.seed * 1000 + self.epoch, self.level)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, required=True)
    ap.add_argument("--n", type=int, default=200_000)
    ap.add_argument("--n-eval", type=int, default=2_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, default=ROOT / "runs" / "data")
    args = ap.parse_args()
    info = build_level(args.level, args.n, args.n_eval, args.seed, args.out)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
