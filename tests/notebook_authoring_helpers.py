"""Project-authored notebooks and boundary scanning for the offline checker."""
from __future__ import annotations

import ast
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import tempfile

import pytest


@contextmanager
def external_report_directory():
    base = Path(tempfile.gettempdir()).resolve()
    if base.is_relative_to(Path(__file__).resolve().parents[1]):
        pytest.skip('report path tests require a temporary directory outside the checkout')
    with tempfile.TemporaryDirectory(prefix='notebook-check-', dir=base) as name:
        yield Path(name)


def notebook(*cells: tuple[str, str]) -> str:
    header = 'import marimo\n\n__generated_with = "0.25.2"\napp = marimo.App()\n'
    return header + ''.join(
        f'\n@app.cell\ndef {name}():\n' + ''.join(f'    {line}\n' for line in code.splitlines())
        + '    return\n' for name, code in cells
    ) + '\nif __name__ == "__main__":\n    app.run()\n'


def import_targets(source: str, module: str, *, package: bool = False) -> set[str]:
    """Include local/relative imports and literal dynamic targets, including aliases."""
    targets = set()
    parent = module if package else module.rpartition('.')[0]
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            name = '.' * node.level + (node.module or '')
            base = importlib.util.resolve_name(name, parent) if node.level else name
            targets.add(base)
            targets.update(f'{base}.{alias.name}' for alias in node.names)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # Literal targets remain visible when import_module/__import__ is aliased.
            targets.add(node.value)
    return targets


def module_name(path: Path, src: Path) -> str:
    parts = path.relative_to(src).with_suffix('').parts
    return '.'.join(parts[:-1] if parts[-1] == '__init__' else parts)
