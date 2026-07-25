# wtl-dllm · dllm/data/stats.py
# what: corpus stats — counts, uniqueness, lengths, digit + carry distribution
# by:   <wtl> watchthelight
# tags: data, stats

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def analyze(path: Path) -> dict:
    texts = [json.loads(l)["text"] for l in path.read_text().splitlines()]
    lengths = Counter(len(t) for t in texts)
    digits = Counter(c for t in texts for c in t if c.isdigit())
    carries = 0
    for t in texts:
        if "+" in t and "=" in t and "*" not in t:
            left = t.split("=")[0]
            try:
                a, b = left.split("+")
                carries += any(int(x) + int(y) >= 10 for x, y in zip(a[::-1], b[::-1]))
            except ValueError:
                pass
    return {
        "file": path.name,
        "n": len(texts),
        "unique": len(set(texts)),
        "unique_ratio": round(len(set(texts)) / max(len(texts), 1), 4),
        "len_min": min(lengths), "len_max": max(lengths),
        "digit_dist": {d: digits[d] for d in sorted(digits)},
        "carry_rate_in_additions": round(carries / max(sum(1 for t in texts if "+" in t and "*" not in t), 1), 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, required=True)
    ap.add_argument("--dir", type=Path, default=ROOT / "runs" / "data")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    reports = [analyze(args.dir / f"{name}_l{args.level}.jsonl")
               for name in ("train", "eval", "eval_perturbed")]
    text = json.dumps(reports, indent=2)
    print(text)
    if args.report:
        md = ROOT / "docs" / "results" / f"data_stats_l{args.level}.md"
        body = "\n".join([
            "---", f'title: "data stats — level {args.level}"', 'author: "<wtl>"',
            "project: wtl-dllm", "tags: [results, data]", "---", "",
            f"# Level {args.level} corpus", "", "```json", text, "```", "",
        ])
        md.write_text(body)
        print(f"-> wrote {md}")


if __name__ == "__main__":
    main()
