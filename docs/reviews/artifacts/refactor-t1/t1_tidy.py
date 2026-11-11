"""Collapse the blank-line runs that pruning left in a file's leading import block (only there)."""
import ast
from pathlib import Path
changed = Path("fixtures-local/t1/f401files.txt").read_text().split()
n = 0
for name in sorted(set(changed)):
    p = Path(name)
    if p.suffix != ".py" or not p.exists():
        continue
    src = p.read_text(); lines = src.splitlines(keepends=True)
    body = ast.parse(src).body
    start = 0
    k = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        start = body[0].end_lineno; k = 1
    end = None
    for node in body[k:]:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = node.end_lineno
            continue
        break
    if end is None:
        continue
    out = lines[:start]
    region = lines[start:end]
    # no run of two or more blank lines inside the block (a single one after the docstring stays as it was)
    tidy = []
    for line in region:
        if not line.strip() and tidy and not tidy[-1].strip():
            continue
        tidy.append(line)
    out += tidy + lines[end:]
    new = "".join(out)
    if new != src:
        ast.parse(new)
        p.write_text(new); n += 1
print("tidied", n)
