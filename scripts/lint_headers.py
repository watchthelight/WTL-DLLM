# wtl-dllm · scripts/lint_headers.py
# what: enforce the five-line file header grammar from docs/conventions.md
# by:   <wtl> watchthelight
# tags: scripts, lint

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", ".venv", "node_modules", "runs", "__pycache__", ".pytest_cache", "dist"}
SKIP_FILES = {"LICENSE", ".gitignore", ".gitattributes", "README.md", "CLAUDE.md",
              "package-lock.json", "uv.lock", "requirements.txt"}
SKIP_SUFFIX = {".json", ".jsonl", ".csv", ".png", ".gif", ".svg", ".ico", ".lock",
               ".toml", ".cfg", ".txt", ".ps1", ".html"}
SKIP_TREES = {("research", "raw")}

CODE_EXT = {".py": "#", ".ts": "//", ".js": "//", ".mjs": "//"}
BLOCK_EXT = {".svelte", ".css"}

FIRST = re.compile(r"^wtl-dllm · [\w./\-]+$")
BY = re.compile(r"^by:\s+<wtl> watchthelight$")


def check_code(path, prefix):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    head = [l[len(prefix):].strip() for l in lines[:6] if l.strip().startswith(prefix)]
    return validate(head)


def check_block(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lead = []
    if path.suffix == ".svelte":
        # svelte: path line rides the opening html comment, the rest sits in a
        # block comment at the top of <script>
        mm = re.match(r"\s*<!--\s*(.*?)\s*-->", text, re.S)
        if mm:
            lead = [mm.group(1).strip()]
            text = text[mm.end():]
        text = re.sub(r"^\s*<script[^>]*>\s*", "", text, count=1)
    m = re.match(r"\s*/\*(.*?)\*/", text, re.S)
    if not m:
        return "missing /* header */ block"
    head = lead + [l.strip() for l in m.group(1).strip().splitlines()]
    return validate(head)


def check_md(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return "missing yaml frontmatter"
    fm = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    for key in ("title", 'author: "<wtl>"', "project: wtl-dllm", "tags"):
        if key not in fm:
            return f"frontmatter missing {key.split(':')[0]}"
    return None


def validate(head):
    if not head or not FIRST.match(head[0]):
        return "line 1 must be 'wtl-dllm · <path>'"
    if not any(l.startswith("what:") for l in head):
        return "missing what:"
    if not any(BY.match(l) for l in head):
        return "missing/incorrect by: line"
    if len(head) > 5:
        return "header longer than 5 lines"
    return None


def main():
    bad = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if any(parts[:len(t)] == t for t in SKIP_TREES):
            continue
        if rel.name in SKIP_FILES or path.suffix in SKIP_SUFFIX:
            continue
        err = None
        if path.suffix in CODE_EXT:
            err = check_code(path, CODE_EXT[path.suffix])
        elif path.suffix in BLOCK_EXT:
            err = check_block(path)
        elif path.suffix == ".md":
            err = check_md(path)
        if err:
            bad.append((rel, err))
    for rel, err in bad:
        print(f"{rel}: {err}")
    print(f"\n{len(bad)} violation(s)" if bad else "headers clean")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
