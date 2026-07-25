# wtl-dllm · dllm/data/build.py
# what: build frozen corpora (train/eval/eval_perturbed jsonl) + vocab.json, with a hard leakage check
# by:   <wtl> watchthelight
# tags: data, corpus

import argparse
import hashlib
import json
from pathlib import Path

from .generator import CANVAS, VOCAB, MathGen

ROOT = Path(__file__).resolve().parents[2]


def is_heldout(s: str) -> bool:
    """Deterministic 10% instance holdout — full digit coverage, never trained on.
    md5, not hash(): python randomizes str hashes per process."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 10 == 0


def build_level(level: int, n_train: int, n_eval: int, seed: int, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)

    def emit(gen: MathGen, n: int, split: str, keep=None, max_tries=None):
        rows, seen, tries = [], set(), 0
        cap = max_tries or n * 200
        while len(rows) < n and tries < cap:
            tries += 1
            s = gen.sample()
            if keep is not None and not keep(s):
                continue
            rows.append({"text": s, "level": level, "split": split})
            seen.add(s)
        if len(rows) < n:
            raise SystemExit(f"{split}: only {len(rows)}/{n} after {tries} tries")
        return rows, seen

    # three eval flavors, three different claims:
    #   eval           — train distribution, may overlap train: memorization + format
    #   eval_heldout   — unseen instances, full digit coverage (md5 holdout): the
    #                    standard generalization claim, G2's headline
    #   eval_perturbed — censored digit bands (operands ending 8/9 never trained):
    #                    extrapolation stress test, expected hard
    train, train_set = emit(MathGen(seed, level), n_train, "train", keep=lambda s: not is_heldout(s))
    ev, _ = emit(MathGen(seed + 1, level), n_eval, "eval", keep=lambda s: not is_heldout(s))
    evh, evh_set = emit(MathGen(seed + 3, level), n_eval, "eval_heldout", keep=is_heldout)
    evp, evp_set = emit(MathGen(seed + 2, level, perturbed=True), n_eval, "eval_perturbed")

    for name, other in [("heldout", evh_set), ("perturbed", evp_set)]:
        leak = train_set & other
        if leak:
            raise SystemExit(f"leakage: {len(leak)} {name} strings in train, e.g. {sorted(leak)[:3]}")

    for name, rows in [("train", train), ("eval", ev), ("eval_heldout", evh), ("eval_perturbed", evp)]:
        with open(out / f"{name}_l{level}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    (out / "vocab.json").write_text(json.dumps(VOCAB, indent=2) + "\n")
    return {"level": level, "train": len(train), "eval": len(ev),
            "eval_heldout": len(evh), "eval_perturbed": len(evp),
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
