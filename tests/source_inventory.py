"""Session-lifetime source/AST inventory for independent architecture assertions.

Consumers only visit these trees; mutation would invalidate another assertion.
Synthetic snippets use the same parser and remain distinct cached entries.
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
