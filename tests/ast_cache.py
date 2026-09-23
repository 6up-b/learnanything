"""Per-session cache of source text, parsed ASTs, and file listings for static tests.

Entries are keyed by path (or by source string for ASTs) and live for the whole
pytest session, which is sound because no test edits files under src/.
Consumers only visit the trees; mutating one would corrupt every later assertion
that reads the same file. Synthetic snippets use the same parser and are cached
as their own entries.
"""
import ast
from functools import cache
from pathlib import Path


@cache
def source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@cache
def source_ast(source: str) -> ast.Module:
    return ast.parse(source)


@cache
def python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))
