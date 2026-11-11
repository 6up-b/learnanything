"""C1 step-0 scan: name-based reference counts for Repository methods and top-level defs.

Counts every identifier-shaped token in every text file under the roots (code, strings,
comments alike), so it over-approximates reach: a candidate is a name whose only
occurrence is its own definition (or whose other occurrences are all in tests).
Writes JSON to argv[1].
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.cwd()
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SKIP_DIRS = {"__pycache__", "node_modules", "fixtures-local", ".venv", "target", "dist", ".git"}
TEXT_EXT = {".py", ".ts", ".tsx", ".js", ".mjs", ".rs", ".json", ".toml", ".html", ".txt", ".cfg", ".ini", ".sql", ".yaml", ".yml"}

ROOTS = {
    "src": [ROOT / "src"],
    "tests": [ROOT / "tests"],
    "scripts": [ROOT / "scripts", ROOT / "docs/learnloop-architecture-vault/_scripts"],
    "apps": [ROOT / "apps"],
    "config": [ROOT / "pyproject.toml"],
}


def files(paths):
    for p in paths:
        if p.is_file():
            yield p
            continue
        for f in p.rglob("*"):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            if f.is_file() and f.suffix in TEXT_EXT:
                yield f


def main() -> None:
    counts: dict[str, Counter] = defaultdict(Counter)  # name -> area -> count
    where: dict[str, list] = defaultdict(list)
    for area, paths in ROOTS.items():
        for f in files(paths):
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = str(f.relative_to(ROOT))
            for m in TOKEN.finditer(text):
                name = m.group(0)
                counts[name][area] += 1
                if len(where[name]) < 40:
                    where[name].append(rel)

    out = {"repository": [], "toplevel": []}
    repo_path = ROOT / "src/learnloop/db/repositories.py"
    tree = ast.parse(repo_path.read_text())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Repository":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("__"):
                        continue
                    start = min([item.lineno] + [d.lineno for d in item.decorator_list])
                    c = counts[item.name]
                    out["repository"].append({
                        "name": item.name, "line": start, "end": item.end_lineno,
                        "lines": item.end_lineno - start + 1,
                        "decorators": [ast.unparse(d) for d in item.decorator_list],
                        "src": c["src"], "tests": c["tests"], "scripts": c["scripts"],
                        "apps": c["apps"], "config": c["config"],
                        "where": sorted(set(where[item.name])),
                    })

    for f in sorted((ROOT / "src/learnloop").rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        rel = str(f.relative_to(ROOT))
        try:
            t = ast.parse(f.read_text())
        except SyntaxError:
            continue
        for node in t.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name.startswith("__"):
                continue
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            c = counts[node.name]
            out["toplevel"].append({
                "file": rel, "name": node.name, "line": start, "end": node.end_lineno,
                "lines": node.end_lineno - start + 1,
                "kind": type(node).__name__,
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "src": c["src"], "tests": c["tests"], "scripts": c["scripts"],
                "apps": c["apps"], "config": c["config"],
                "where": sorted(set(where[node.name])),
            })
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
