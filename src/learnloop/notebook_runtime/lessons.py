"""A Teacher lesson whose medium is a marimo notebook (spec §11.2): where its notebook is, and its commit points.

**Where the notebook is.** A lesson's notebook is the vault file ``notebooks/lessons/<lesson id>.py`` (notebooks
live in the vault as ``.py`` files, NA §5.3). Its presence is what makes the lesson's medium ``notebook``: no column
records it and nothing writes it yet. Authoring lesson notebooks is the teacher half of NA4 (``nb_request`` and
its durable job, teacher v2 §10), which is not built; that job is what would write this file.

**Commit points and held cells.** Until NA's SDK declares them (``ll.commit`` and ``ll.reveal``, NA §6), the
notebook's own structure does: a cell whose name starts with ``commit`` is a commit point, a cell shipped with
``disabled=True`` is held, and each held cell is released by the nearest commit point above it (held cells above
every commit point are released by none). A commit is the learner setting a value on one of the commit cell's own
controls, seen by the host on its way to the kernel; the sidecar releases the held cells (``notebook.release``)
only after that, and never in a review (a closed lesson). Nothing about a commit is recorded as evidence: commits
as evidence are NA's host-owned commit (§6.3), not this.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

#: The vault folder of lesson notebooks, one ``<lesson id>.py`` per lesson.
LESSON_NOTEBOOKS = Path("notebooks") / "lessons"
#: A commit point's cell name starts with this.
COMMIT_PREFIX = "commit"

_LESSON_ID = re.compile(r"^[A-Za-z0-9_-]{1,200}$")


def lesson_notebook_path(vault_root: Path, lesson_id: str) -> str | None:
    """The lesson's notebook relative to the vault (posix), or None when the lesson has none."""

    if not _LESSON_ID.match(lesson_id):
        return None
    relative = LESSON_NOTEBOOKS / f"{lesson_id}.py"
    path = Path(vault_root) / relative
    return relative.as_posix() if path.is_file() else None


def _is_cell(decorator: ast.expr) -> tuple[bool, bool]:
    """(a marimo cell decorator, it holds the cell)."""

    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if not (isinstance(target, ast.Attribute) and target.attr == "cell"):
        return False, False
    held = isinstance(decorator, ast.Call) and any(
        keyword.arg == "disabled" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
        for keyword in decorator.keywords)
    return True, held


def lesson_contract(source: bytes) -> dict[str, Any]:
    """``{"points": [{"name", "held"}], "held": [...]}`` read from the notebook's cells, in order."""

    try:
        tree = ast.parse(source.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return {"points": [], "held": []}
    points: list[dict[str, Any]] = []
    held: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        marks = [_is_cell(decorator) for decorator in node.decorator_list]
        if not any(is_cell for is_cell, _held in marks):
            continue
        if any(is_held for _cell, is_held in marks):
            held.append(node.name)
            if points:
                points[-1]["held"].append(node.name)
        elif node.name.startswith(COMMIT_PREFIX):
            points.append({"name": node.name, "held": []})
    return {"points": points, "held": held}


def committed_value(value: Any) -> bool:
    """A control's value that says the learner answered (an empty form or field is not a commit)."""

    return value not in (None, "", [], {}, False)


__all__ = ["COMMIT_PREFIX", "LESSON_NOTEBOOKS", "committed_value", "lesson_contract", "lesson_notebook_path"]
