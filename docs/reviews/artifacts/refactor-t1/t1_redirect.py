"""Point importers of a helper's re-exported names at the module that defines them; drop the re-export."""
import ast, json, re
from collections import defaultdict
from pathlib import Path
T = Path("tests")
redir = {}  # (helper module, name) -> origin module
for e in json.loads(Path("fixtures-local/t1/reexports.json").read_text()):
    full = re.search(r"`([\w.]+)` imported", e["message"]).group(1)
    origin, _, name = full.rpartition(".")
    redir[("tests." + Path(e["filename"]).stem, name)] = origin

def fmt(mod, parts, indent):
    one = f"{indent}from {mod} import {', '.join(parts)}"
    if len(one) <= 110:
        return one
    return f"{indent}from {mod} import (\n" + "".join(f"{indent}    {p},\n" for p in parts) + f"{indent})"

for path in sorted(T.glob("*.py")):
    src = path.read_text(); lines = src.splitlines(keepends=True)
    edits = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and any((node.module, a.name) in redir for a in node.names):
            keep, moved = [], defaultdict(list)
            for a in node.names:
                p = a.name + (f" as {a.asname}" if a.asname else "")
                o = redir.get((node.module, a.name))
                (moved[o].append(p) if o else keep.append(p))
            seg = "".join(lines[node.lineno - 1: node.end_lineno])
            comment = re.search(r"#.*$", seg.splitlines()[0]) if node.lineno == node.end_lineno else None
            if "#" in seg and not comment:
                print("COMMENT IN MULTILINE", path, node.lineno); continue
            c = ("  " + comment.group(0)) if comment else ""
            indent = " " * node.col_offset
            out = []
            if keep:
                out.append(fmt(node.module, keep, indent) + c)
            for o, ps in moved.items():
                out.append(fmt(o, ps, indent) + ("" if keep else c))
            edits.append((node.lineno, node.end_lineno, "\n".join(out) + "\n"))
    for lo, hi, text in sorted(edits, reverse=True):
        print(f"{path}:{lo}: {''.join(lines[lo-1:hi]).strip()} -> {text.strip()}")
        lines[lo - 1:hi] = [text]
    if edits:
        path.write_text("".join(lines))
