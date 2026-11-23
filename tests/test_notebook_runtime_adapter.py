"""The notebook runtime's one adapter: every private marimo interface it relies on still holds in the installed,
pinned marimo. A pin bump that moves one fails here, by name, not in a learner's notebook."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from learnloop.notebook_runtime import adapter

RUNTIME = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "notebook_runtime"


def test_every_private_marimo_interface_the_runtime_relies_on_holds():
    pytest.importorskip("marimo")
    assert adapter.interface_problems() == []


def test_the_installed_marimo_is_the_pinned_one():
    pytest.importorskip("marimo")
    assert adapter.installed_version() == adapter.pinned_version() is not None


def test_only_the_adapter_names_marimo():
    """The other runtime modules reach marimo only through the adapter (its constants and its launcher)."""

    for path in RUNTIME.glob("*.py"):
        if path.name == "adapter.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else (
                [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            assert not any(name == "marimo" or name.startswith("marimo.") for name in names), path.name
        assert "/api/kernel" not in path.read_text(encoding="utf-8"), path.name


def test_the_adapter_imports_only_the_standard_library_at_its_top():
    """The sandbox mounts this one file as the launcher, and marimo's spawn kernel re-executes it."""

    import sys

    tree = ast.parse((RUNTIME / "adapter.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] in sys.stdlib_module_names for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module == "__future__" or (node.module or "").split(".")[0] in sys.stdlib_module_names
    guard = tree.body[-1]
    assert isinstance(guard, ast.If) and "__main__" in ast.unparse(guard.test)
