"""The tables AD's code can name while an AD operation is open (the reachable-reads audit).

The AD guard refuses a read of an unclassified table in every scope (``protected_tables``), and the
refusal makes AD unavailable for the whole operation. Which tables a run happens to read depends on
the data: a branch the test vaults never take (field's serving attribution reading
``scheduler_offer_receipts`` for a learner pick, 2026-10-27) is refused only on the vault that takes
it. So this helper records every function of ``learnloop`` that runs while an operation is open
(:class:`Reached`, a profiler) and names, statically, every table any of them can read, on any of
its branches: a table named after ``FROM`` or ``JOIN`` in one of its string constants (its nested
functions' and lambdas' included), or a string constant (or a module-level string it names) that
is exactly a table's name (a table name a statement is composed with). A table so named that the
registry has not classified is a latent denial.
"""

from __future__ import annotations

import inspect
import re
import sys
import threading
import types
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SRC = Path(__file__).resolve().parents[1] / "src" / "learnloop"
#: The guard's own registry and enforcement name tables to classify them, never to read them.
REGISTRY = frozenset({
    SRC / "adaptive_difficulty" / "operation.py",
    SRC / "adaptive_difficulty" / "protected_tables.py",
    SRC / "adaptive_difficulty" / "column_classes.py",
})
_READ = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


class Reached:
    """Every ``learnloop`` function called while an AD operation is open, with its module globals."""

    def __init__(self) -> None:
        self.functions: dict[types.CodeType, Mapping[str, Any]] = {}
        #: The reached functions that ran at least once outside the rules' scopes (where only a
        #: neutral table's metadata, AD's own writes and the named carve-outs are readable).
        self.unruled: set[types.CodeType] = set()

    def _profile(self, frame: Any, event: str, _arg: Any) -> None:
        if event != "call":
            return
        code = frame.f_code
        if code in self.unruled:
            return
        from learnloop.adaptive_difficulty import operation as O

        if O.current() is None or not code.co_filename.startswith(str(SRC)):
            return
        self.functions.setdefault(code, frame.f_globals)
        if O._IN_RULES.get() is None:
            self.unruled.add(code)

    @contextmanager
    def recording(self) -> Iterator["Reached"]:
        previous, previous_thread = sys.getprofile(), threading.getprofile()
        sys.setprofile(self._profile)
        threading.setprofile(self._profile)
        try:
            yield self
        finally:
            sys.setprofile(previous)
            threading.setprofile(previous_thread)

    def named_tables(self, tables: Iterable[str], *, unruled: bool = False) -> dict[str, set[str]]:
        """table -> the reached functions (``module:qualname``) that name it (``unruled``: only the
        functions that ran outside the rules' scopes)."""

        known = set(tables)
        out: dict[str, set[str]] = {}
        for code, module_globals in self.functions.items():
            if unruled and code not in self.unruled:
                continue
            if Path(code.co_filename) in REGISTRY or not _function(code):
                continue
            where = f"{module_globals.get('__name__', code.co_filename)}:{code.co_qualname}"
            for table in (_read(code, known) if unruled else _named(code, module_globals, known)):
                out.setdefault(table, set()).add(where)
        return out


def _function(code: types.CodeType) -> bool:
    """A function's body (a lambda's, a comprehension's), not a module's or a class's: importing a
    module inside an operation runs its body, which defines every function in it, called or not."""

    return bool(code.co_flags & inspect.CO_OPTIMIZED)


def _strings(code: types.CodeType) -> Iterator[str]:
    for constant in code.co_consts:
        if isinstance(constant, str):
            yield constant
        elif isinstance(constant, types.CodeType) and _function(constant):
            yield from _strings(constant)
        elif isinstance(constant, (tuple, frozenset)):
            yield from (item for item in constant if isinstance(item, str))


def _names(code: types.CodeType) -> Iterator[str]:
    yield from code.co_names
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType) and _function(constant):
            yield from _names(constant)


def _named(code: types.CodeType, module_globals: Mapping[str, Any], known: set[str]) -> set[str]:
    found: set[str] = set()
    for text in _strings(code):
        if text in known:
            found.add(text)
        found.update(match for match in _READ.findall(text) if match in known)
    for name in _names(code):
        value = module_globals.get(name)
        if isinstance(value, str) and value in known:
            found.add(value)
    return found


def _read(code: types.CodeType, known: set[str]) -> set[str]:
    """The tables a function's own SQL reads (after FROM or JOIN), on any of its branches."""

    return {match for text in _strings(code) for match in _READ.findall(text) if match in known}


def schema_tables(sqlite_path: Path) -> set[str]:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(sqlite_path)) as connection:
        return {str(row[0]) for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'")}
