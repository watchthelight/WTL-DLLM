# wtl-dllm · dllm/eval/ablate.py
# what: ordering x steps grid on the perturbed split — does confidence beat random at 10m?
# why:  the literature only knows the answer at 7-8b; this measures it here
# by:   <wtl> watchthelight
# tags: eval, ablation

import argparse
import csv
import json
from pathlib import Path

from dllm.eval.harness import ROOT, run_eval
from dllm.model.sampler import ORDERINGS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", type=Path, required=True)
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--canvas-steps", type=int, required=True,
                    help="the canvas-length step count for this level (full budget)")
    args = ap.parse_args()

    grid_steps = sorted({args.canvas_steps, max(args.canvas_steps // 2, 1),
                         max(args.canvas_steps // 4, 1)}, reverse=True)
    rows = []
    for ordering in ORDERINGS:
        for steps in grid_steps:
            r = run_eval(args.ckpt, args.level, "eval_perturbed", steps=steps,
                         ordering=ordering, limit=args.limit)
            rows.append({"ordering": ordering, "steps": steps,
                         "accuracy": r["accuracy"], "wellformed": r["wellformed"]})
            print(f"{ordering:>10} @ {steps:>2} steps -> acc {r['accuracy']:.3f}  wf {r['wellformed']:.3f}")

    out_csv = ROOT / "docs" / "results" / f"ablation_ordering_l{args.level}.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ordering", "steps", "accuracy", "wellformed"])
        w.writeheader()
        w.writerows(rows)

    best = max(rows, key=lambda r: r["accuracy"])
    summary = {"ckpt": str(args.ckpt), "level": args.level, "limit": args.limit,
               "best": best, "grid": rows}
    (ROOT / "docs" / "results" / f"ablation_ordering_l{args.level}.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    print(f"\nbest: {best}")
    print(f"-> {out_csv}")


if __name__ == "__main__":
    main()
