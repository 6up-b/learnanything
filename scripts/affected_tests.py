"""The test files a change is likely to affect, chosen from the import graph (refactor step A6).

A per-step gate runs these instead of the whole suite. It is a pre-filter, not the
guarantee: the landing gate still runs the whole suite minus ``arc_close``, and
the arc-close gate runs the rest. The rule, in order:

1. **Full suite** when a changed path is one every test depends on, or one this
   script can't trace: ``tests/conftest.py`` and the modules it names in an import
   (the ones it patches for the fast lane), ``tests/helpers.py``,
   ``tests/connection_reuse.py``, ``pyproject.toml``, ``uv.lock``,
   ``migrations/``, the tracked fixtures under ``fixtures/``, or a non-Python file
   under ``src/`` with no module in its directory or any directory above it. Also
   a deleted (or renamed-away) ``.py`` module under ``src/`` or ``tests/``: the
   graph is read from the files that exist, so the imports of it that would now
   fail are gone from it too.
2. A changed ``.py`` module under ``src/`` or ``tests/``: the test files that
   import it, through at most ``--depth`` other ``src`` modules (default 1: the
   tests that import it, and the tests that import a module importing it). Test
   helper modules (``tests/*.py`` not named ``test_*``) are glue, so passing
   through one costs nothing.
3. A changed non-Python file under ``src/`` (a prompt, a doctrine page, a static
   asset): treated as a change to the modules in the nearest directory holding
   any, which is where the code that reads it lives.
4. Any other changed file (docs, scripts, apps, ``tests/*.json``): the test files
   whose text names its path or its file name. None is a valid answer: a doc-only
   change runs no pytest (the vault validators are their own gate step).

**Why a depth and not the whole closure.** The packages are tightly knit: through
``db.repositories``, ``config`` and ``tests/helpers.py`` nearly every module
reaches nearly every test, so the full reverse closure of the median module is
70% of the suite's seconds. Measured on main ``9a623e3d9c``'s JUnit over all 1,285
``src`` modules: depth 0 selects a median of 16 test seconds (90th percentile
551), depth 1 a median of 865 (90th percentile 4,015), depth 2 a median of 2,844.
Depth 1 is the default because it is about 1-2 minutes at ``-n 6`` for most
modules; pass ``--depth 2`` for a change to a widely used module's behaviour.

Imports are read from the source (``ast``), function-local ones included, plus any
string constant naming a module (``importlib.import_module("learnloop.x")``,
``monkeypatch.setattr("learnloop.x.y", ...)``, ``"learnloop.x:attr"``) or its source
path (``"src/learnloop/x.py"``: ``params/parameter_registry.py``'s ``MODULE_INVENTORY``
names the modules it imports and reads that way, and source guards in ``tests/``
name the files they scan). Importing ``a.b.c`` also runs
``a`` and ``a.b``, so a package's ``__init__.py`` is imported by everything under
it.

Output, one per line and sorted: the selected test files, or the single line
``tests`` when the rule falls back to the whole suite (the reason goes to stderr),
so the output can always be passed to pytest. Nothing selected prints nothing and
exits 0; don't hand pytest an empty list, which runs the whole suite. From bash:

    mapfile -t paths < <(uv run python scripts/affected_tests.py --base main)
    [ ${#paths[@]} -gt 0 ] && uv run pytest -m "not arc_close" -n 6 "${paths[@]}"

Deterministic: the same tree, changed paths and depth give the same list. Only
tracked and untracked-but-not-ignored files are read; nothing is imported or run.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ("learnloop", "learnloop_sidecar", "learnloop_mobile", "learnloop_mcp")

#: Paths every test depends on (exact files, or a directory prefix ending in "/").
FULL_TRIGGERS = (
    "tests/conftest.py",
    "tests/helpers.py",
    "tests/connection_reuse.py",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "migrations/",
    "fixtures/",
)


def _git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line]


def changed_paths(base: str) -> list[str]:
    """Committed changes since the merge base with ``base``, plus staged, unstaged and untracked ones.

    ``--no-renames``: with rename detection (git's default) a moved file lists only its new
    path, and the old one, which other files may still import, would never be seen."""

    paths = set(_git("diff", "--name-only", "--no-renames", f"{base}...HEAD"))
    paths |= set(_git("diff", "--name-only", "--no-renames", "HEAD"))
    paths |= set(_git("ls-files", "--others", "--exclude-standard"))
    return sorted(paths)


def module_name(path: str) -> str | None:
    """``src/learnloop/a/b.py`` -> ``learnloop.a.b``; ``tests/x.py`` -> ``tests.x``; packages drop ``__init__``."""

    if not path.endswith(".py"):
        return None
    parts = Path(path).with_suffix("").parts
    if parts[:1] == ("src",) and len(parts) > 1 and parts[1] in PACKAGES:
        parts = parts[1:]
    elif parts[:1] != ("tests",):
        return None
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _python_files() -> list[str]:
    tracked = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", "src", "tests")
    return sorted(p for p in tracked if p.endswith(".py") and (ROOT / p).is_file())


def _parents(name: str) -> list[str]:
    parts = name.split(".")
    return [".".join(parts[:i]) for i in range(1, len(parts))]


class Graph:
    """Module -> the modules it imports, over ``src``'s four packages and ``tests``."""

    def __init__(self) -> None:
        self.files = _python_files()
        self.path_of = {module_name(p): p for p in self.files}
        self.path_of.pop(None, None)
        self.modules = set(self.path_of)
        self.imports: dict[str, set[str]] = {}
        for name, path in self.path_of.items():
            self.imports[name] = self._read(name, path)
        self.importers: dict[str, set[str]] = defaultdict(set)
        for name, deps in self.imports.items():
            for dep in deps:
                self.importers[dep].add(name)

    def _known(self, dotted: str) -> list[str]:
        """``dotted`` and its parents that are modules here (``a.b.attr`` names ``a.b`` and ``a``)."""

        found = [p for p in [*_parents(dotted), dotted] if p in self.modules]
        return found

    def _named_by_string(self, value: str) -> list[str]:
        """The modules a string constant names: a dotted name (``"learnloop.x"``, ``"learnloop.x.y:attr"``),
        or a source path (``"src/learnloop/x.py"``, ``"learnloop/x.py"``), which is how path registries such
        as ``params/parameter_registry.py``'s ``MODULE_INVENTORY`` name the modules they import and read,
        and how source guards in ``tests/`` name the files they scan."""

        if value.endswith(".py") and "/" in value:
            path = value.removeprefix("./")
            return [m for m in (module_name(path), module_name(f"src/{path}")) if m in self.modules]
        if value.split(".", 1)[0] in (*PACKAGES, "tests"):
            return self._known(value.partition(":")[0])
        return []

    def _read(self, name: str, path: str) -> set[str]:
        try:
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        except (SyntaxError, UnicodeDecodeError):
            return set()
        package = name if path.endswith("__init__.py") else name.rpartition(".")[0]
        deps: set[str] = set(_parents(name))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.update(self._known(alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    anchor = package.split(".")
                    anchor = anchor[: len(anchor) - (node.level - 1)] if node.level > 1 else anchor
                    base = ".".join([*anchor, node.module] if node.module else anchor)
                else:
                    base = node.module or ""
                deps.update(self._known(base))
                for alias in node.names:
                    deps.update(self._known(f"{base}.{alias.name}"))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and "." in node.value \
                    and not any(c.isspace() for c in node.value):
                deps.update(self._named_by_string(node.value))
        deps.discard(name)
        return deps

    def tests_reaching(self, roots: set[str], depth: int) -> set[str]:
        """Test modules importing one of ``roots`` through at most ``depth`` other ``src`` modules; a test helper
        module on the way costs nothing (rule 2)."""

        best = dict.fromkeys(roots, 0)
        frontier = sorted(roots)
        found: set[str] = set(m for m in roots if _is_test_module(m))
        while frontier:
            following: list[str] = []
            for module in frontier:
                for importer in sorted(self.importers.get(module, ())):
                    if _is_test_module(importer):
                        found.add(importer)
                        continue
                    cost = best[module] + (0 if importer.startswith("tests") else 1)
                    if cost > depth or best.get(importer, depth + 1) <= cost:
                        continue
                    best[importer] = cost
                    following.append(importer)
            frontier = following
        return found


def _is_test_module(name: str) -> bool:
    return name.startswith("tests.") and name.rsplit(".", 1)[-1].startswith("test_")


def _is_test_file(path: str) -> bool:
    return path.startswith("tests/") and Path(path).name.startswith("test_") and path.endswith(".py")


def select(changed: list[str], graph: Graph | None = None, *, depth: int = 1) -> dict:
    """``{"mode": "full" | "selected", "reasons": [...], "tests": [...]}`` for these changed paths."""

    graph = graph or Graph()
    conftest_deps = graph.imports.get("tests.conftest", set())
    reasons: list[str] = []
    roots: set[str] = set()
    named: set[str] = set()
    for path in changed:
        if any(path == t or (t.endswith("/") and path.startswith(t)) for t in FULL_TRIGGERS):
            reasons.append(f"{path}: every test depends on it")
            continue
        name = module_name(path)
        if name is not None:
            if name not in graph.modules:
                # Deleted (or renamed away). The graph is read from the files that exist, so the
                # imports of it that survive were dropped with it, and they are exactly what breaks.
                reasons.append(f"{path}: deleted, and the graph no longer holds what imported it")
                continue
            if name in conftest_deps:
                reasons.append(f"{path}: tests/conftest.py imports it, so every test does")
                continue
            roots.add(name)
            continue
        if path.startswith("src/"):
            siblings: set[str | None] = set()
            directory = Path(path).parent
            while not siblings and len(directory.parts) > 2:
                siblings = {module_name(p) for p in graph.files if Path(p).parent == directory}
                siblings.discard(None)
                directory = directory.parent
            if not siblings:
                reasons.append(f"{path}: no module near it reads it, so this script can't trace it")
                continue
            if siblings & conftest_deps:
                reasons.append(f"{path}: read beside a module tests/conftest.py imports")
                continue
            roots |= siblings
            continue
        named.add(path)
    if reasons:
        return {"mode": "full", "reasons": reasons, "tests": ["tests"]}
    selected = {graph.path_of[m] for m in graph.tests_reaching(roots, depth) if m in graph.path_of}
    selected |= {p for p in changed if _is_test_file(p) and (ROOT / p).is_file()}
    if named:
        needles = {n: {n, Path(n).name} for n in named}
        for path in graph.files:
            if not _is_test_file(path) or path in selected:
                continue
            text = (ROOT / path).read_text(encoding="utf-8", errors="replace")
            if any(any(needle in text for needle in variants) for variants in needles.values()):
                selected.add(path)
    return {"mode": "selected", "reasons": [], "tests": sorted(selected)}


def junit_seconds(junit: Path, tests: list[str]) -> float:
    """The selected files' test seconds in a JUnit XML (an estimate of the per-step gate's cost)."""

    wanted = {Path(t).with_suffix("").as_posix().replace("/", ".") for t in tests}
    every = tests == ["tests"]
    return round(sum(float(case.get("time") or 0) for case in ET.parse(junit).iter("testcase")
                     if every or (case.get("classname") or "") in wanted), 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--base", default="main", help="compare against the merge base with this ref (default main)")
    parser.add_argument("--files", nargs="*", help="these changed paths instead of git's")
    parser.add_argument("--depth", type=int, default=1, help="src modules a test may import it through (default 1)")
    parser.add_argument("--json", action="store_true", help="print the decision as JSON")
    parser.add_argument("--junit", type=Path, help="a JUnit XML to estimate the selection's test seconds from")
    args = parser.parse_args(argv)
    changed = sorted(set(args.files)) if args.files is not None else changed_paths(args.base)
    result = select(changed, depth=args.depth)
    result["changed"] = changed
    if args.junit:
        result["estimated_test_seconds"] = junit_seconds(args.junit, result["tests"])
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    for reason in result["reasons"]:
        print(f"full suite: {reason}", file=sys.stderr)
    if not result["tests"]:
        print("no test file is affected", file=sys.stderr)
    for path in result["tests"]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
