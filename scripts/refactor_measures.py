"""The refactor's success measures (docs/specs/refactor_strategy_v3.md §6), one way.

S0 and Z2 both run this script, so the "before" and "after" are counted the
same way. Three kinds of measure:

- computed from the checkout (the default, a few seconds): sizes, module and
  file counts, the plumbing counts, version-literal and tag-gate counts;
- timed (``--timed``): the serial, ``-n 8`` and durability suite times, and step A6's two gates (``landing``, ``arc_close``). These
  take machine time, so they run only when asked, and the exact commands are
  printed either way;
- manual: measures that need judgment or the owner. Listed with their procedure.

Only tracked files are read (``git ls-files``), so a gitignored
``fixtures-local/`` or a stray vault never enters a count. Nothing here opens a
database or makes a model call. Run it under an empty ``HOME`` and config dir:

    uv run python scripts/refactor_measures.py --json out.json --markdown out.md
"""

from __future__ import annotations

import argparse
import ast
import importlib
import io
import os
import json
import re
import shlex
import subprocess
import sys
import time
import tokenize
import tomllib
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("src/learnloop", "src/learnloop_sidecar", "src/learnloop_mobile", "src/learnloop_mcp")
TAG = re.compile(r"mvp-0\.(\d+)")
UPGRADE_FAMILY = re.compile(r"(upgrade|successor)")


# -- files ---------------------------------------------------------------------


def tracked(*prefixes: str, suffix: str | None = None) -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", *prefixes],
        check=True, capture_output=True,
    ).stdout.decode()
    paths = [ROOT / p for p in out.split("\0") if p]
    # A tracked file deleted in the working tree is not part of this checkout.
    return [p for p in paths if p.is_file() and (suffix is None or p.suffix == suffix)]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# -- per-file Python facts -----------------------------------------------------

_SKIP_TOKENS = {
    tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
    tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER,
}


def _string_statement_lines(tree: ast.AST) -> set[int]:
    """Lines of string-only expression statements: docstrings and the bare
    triple-quoted blocks used as comments. Not code by the map's definition."""

    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return lines


def python_facts(path: Path, text: str | None = None, tree: ast.AST | None = None) -> dict:
    """Raw and code lines, statements, functions, long functions, comment lines
    (and those naming a stage artifact), and the ``mvp-0.N`` literals by where
    they sit (comment / docstring or multi-line string / code string). Same
    definitions as the map's §1 sweep. ``text`` and ``tree`` let a caller that
    already parsed the file share the parse."""

    text = read(path) if text is None else text
    facts = {"raw": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
             "code": 0, "statements": 0, "functions": 0, "long_functions": [],
             "comments": 0, "stage_comments": 0,
             "tags": {"comment": 0, "docstring": 0, "code": 0}}
    try:
        tree = tree or ast.parse(text)
    except SyntaxError:
        return facts
    doc_lines = _string_statement_lines(tree)
    code_lines: set[int] = set()
    fstring_triple: list[bool] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        tokens = []
    for tok in tokens:
        kind = tok.type
        if kind == tokenize.COMMENT:
            facts["tags"]["comment"] += len(TAG.findall(tok.string))
            facts["comments"] += 1
            facts["stage_comments"] += bool(STAGE_COMMENT.search(NOQA.sub("", tok.string)))
            continue
        if kind == getattr(tokenize, "FSTRING_START", -1):
            fstring_triple.append(tok.string.rstrip().endswith(('"""', "'''")))
        elif kind == getattr(tokenize, "FSTRING_END", -1) and fstring_triple:
            fstring_triple.pop()
        if kind == tokenize.STRING or kind == getattr(tokenize, "FSTRING_MIDDLE", -1):
            hits = len(TAG.findall(tok.string))
            if hits:
                if kind == tokenize.STRING:
                    body = tok.string.lstrip("rRbBuUfF")
                    multi = body.startswith(('"""', "'''"))
                else:
                    multi = bool(fstring_triple and fstring_triple[-1])
                where = "docstring" if multi or tok.start[0] in doc_lines else "code"
                facts["tags"][where] += hits
        if kind in _SKIP_TOKENS:
            continue
        for line in range(tok.start[0], tok.end[0] + 1):
            if line not in doc_lines:
                code_lines.add(line)
    facts["code"] = len(code_lines)
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            facts["statements"] += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            facts["functions"] += 1
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > 100:
                facts["long_functions"].append((node.name, node.lineno, length))
    return facts


# -- version sets and tag gates ------------------------------------------------


def _version_set_values(src_files: list[Path]) -> tuple[dict[str, frozenset], set[str], list[str]]:
    """Every module-level ``*_VERSIONS`` set of algorithm tags in ``src`` and
    its value, read by importing the module that defines it; and the names of
    ``*_VERSIONS`` sets that hold something else (prompt or schema versions),
    which aren't tag gates. Names defined twice with different values are left
    out and reported."""

    values: dict[str, frozenset] = {}
    other: set[str] = set()
    clash: set[str] = set()
    problems: list[str] = []
    for path in src_files:
        tree = ast.parse(read(path))
        names = []
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            names += [t.id for t in targets if isinstance(t, ast.Name) and t.id.endswith("_VERSIONS")]
        if not names:
            continue
        module = rel(path)[len("src/"):-len(".py")].replace("/", ".").removesuffix(".__init__")
        try:
            mod = importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - a count, not a gate: report and go on
            problems.append(f"import {module}: {type(exc).__name__}")
            continue
        for name in names:
            value = getattr(mod, name, None)
            if not isinstance(value, (set, frozenset, tuple, list)):
                continue
            value = frozenset(str(v) for v in value)
            if not value or not all(TAG.fullmatch(v) for v in value):
                other.add(name)
                continue
            if name in values and values[name] != value:
                clash.add(name)
            values.setdefault(name, value)
    for name in clash:
        values.pop(name, None)
        problems.append(f"{name} has two different definitions; its gates are not classified")
    return values, other - set(values), problems


def _gate_target(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name) and node.id.endswith("_VERSIONS"):
        return node.id
    if isinstance(node, ast.Attribute) and node.attr.endswith("_VERSIONS"):
        return node.attr
    return None


def tag_gates(src_files: list[Path], floor: str) -> dict:
    """``x in X_VERSIONS`` / ``not in`` sites in ``src``. A gate is constant at
    the floor when every tag from the floor to the latest is in the set (or none
    is): on a vault at or above the floor, its other branch can't run. The
    paired-with-a-kill-switch split is not counted; it needs reading (§6)."""

    from learnloop.algorithm_versions import SUCCESSOR_CHAIN

    chain = list(SUCCESSOR_CHAIN)
    if floor not in chain:
        return {"error": f"floor {floor} is not in SUCCESSOR_CHAIN"}
    live = set(chain[chain.index(floor):])
    values, other, problems = _version_set_values(src_files)
    total = constant = unknown = 0
    varying_sites: list[str] = []
    constant_sites: list[str] = []
    for path in src_files:
        text = read(path)
        if "_VERSIONS" not in text:
            continue
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Compare):
                continue
            for op, right in zip(node.ops, node.comparators, strict=True):
                if not isinstance(op, (ast.In, ast.NotIn)):
                    continue
                name = _gate_target(right)
                if name is None or name in other:
                    continue
                total += 1
                value = values.get(name)
                if value is None:
                    unknown += 1
                elif live <= value or not (live & value):
                    constant += 1
                    constant_sites.append(f"{rel(path)}:{node.lineno} {name}")
                else:
                    varying_sites.append(f"{rel(path)}:{node.lineno} {name}")
    return {
        "floor": floor, "latest": chain[-1], "chain_length": len(chain),
        "version_sets": len(values), "gates": total, "constant_at_floor": constant,
        "varying": len(varying_sites), "unclassified": unknown,
        "varying_sites": varying_sites, "constant_sites": constant_sites, "problems": problems,
    }


# -- test plumbing -------------------------------------------------------------


def _frozen_set_assertions(tree: ast.AST) -> int:
    """``X_VERSIONS == frozenset({...})`` (or a set literal): a pin every new
    tag edits (test-suite audit §7)."""

    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(isinstance(op, ast.Eq) for op in node.ops):
            continue
        sides = [node.left, *node.comparators]
        if not any(_gate_target(s) for s in sides):
            continue
        for side in sides:
            literal = side.args[0] if (
                isinstance(side, ast.Call) and isinstance(side.func, ast.Name)
                and side.func.id in {"frozenset", "set"} and side.args
            ) else side
            if isinstance(literal, (ast.Set, ast.List, ast.Tuple)) and any(
                isinstance(e, ast.Constant) and isinstance(e.value, str) and TAG.fullmatch(e.value)
                for e in literal.elts
            ):
                count += 1
                break
    return count


def _latest_pin(tree: ast.AST) -> bool:
    """``LATEST == "mvp-0.N"`` or ``SUCCESSOR_CHAIN[-1] == "mvp-0.N"``."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left, *node.comparators]
        names_latest = any(
            (isinstance(s, ast.Name) and s.id == "LATEST")
            or (isinstance(s, ast.Attribute) and s.attr == "LATEST")
            or (isinstance(s, ast.Subscript) and isinstance(s.value, (ast.Name, ast.Attribute))
                and getattr(s.value, "id", getattr(s.value, "attr", "")) == "SUCCESSOR_CHAIN")
            for s in sides
        )
        literal = any(isinstance(s, ast.Constant) and isinstance(s.value, str) and TAG.fullmatch(s.value) for s in sides)
        if names_latest and literal:
            return True
    return False


def test_plumbing(test_files: list[Path], floor: str, latest: str) -> dict:
    floor_n, latest_n = int(TAG.fullmatch(floor).group(1)), int(TAG.fullmatch(latest).group(1))
    out = Counter()
    frozen_files: list[str] = []
    for path in test_files:
        text = read(path)
        tags = {int(m) for m in TAG.findall(text)}
        if tags:
            out["files_naming_any_tag"] += 1
        if any(n >= floor_n for n in tags):
            out["files_naming_a_tag_at_or_above_floor"] += 1
        if latest_n in tags:
            out["files_naming_the_latest_tag"] += 1
        if "DEFAULTS_SNAPSHOT_BY_ALGORITHM" in text or "defaults_fingerprint_for_version" in text:
            out["files_reading_defaults_digests"] += 1
        if "LEGACY_DEFAULT_CONFIG_TEXT" in text:
            out["files_reading_legacy_default_config_text"] += 1
        uses_vault = "create_basic_vault" in text
        if uses_vault:
            out["files_using_create_basic_vault"] += 1
            if not tags and not re.search(r"algorithm_version|\bLATEST\b|SUCCESSOR_CHAIN", text):
                out["of_those_naming_no_version"] += 1
        if not path.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        n = _frozen_set_assertions(tree)
        if n:
            out["frozen_version_set_assertions"] += n
            frozen_files.append(rel(path))
        if _latest_pin(tree):
            out["files_with_a_latest_pin"] += 1
    out["files_with_frozen_version_sets"] = len(frozen_files)
    return dict(out)


def head_fixture_refs() -> dict:
    """Files naming the current head fixture's directory: each one is edited
    at every migration (A2). An old head named in a comment isn't counted."""

    heads = sorted(p.name for p in (ROOT / "fixtures").glob("migration_head*") if p.is_dir())
    names = re.compile("|".join(re.escape(h) + r"\b" for h in heads) or r"(?!)")
    files = tracked("tests", "scripts", "docs/learnloop-architecture-vault/_scripts")
    by_root = Counter()
    lines = 0
    for path in files:
        if path.suffix not in {".py", ".toml", ".json", ".md", ".txt", ".sql"}:
            continue
        hits = sum(1 for line in read(path).splitlines() if names.search(line))
        if hits:
            by_root["tests" if rel(path).startswith("tests/") else "scripts"] += 1
            lines += hits
    fixture_files = tracked(*(f"fixtures/{h}" for h in heads)) if heads else []
    return {"head_fixtures": heads, "head_fixture_files": len(fixture_files),
            "files_naming_head_path": sum(by_root.values()), "test_files": by_root["tests"],
            "script_files": by_root["scripts"], "lines": lines}


def generated_notes() -> dict:
    notes = tracked("docs/learnloop-architecture-vault", suffix=".md")
    generated = stamped = 0
    for path in notes:
        head = read(path)[:4000]
        if not head.startswith("---"):
            continue
        front = head.split("\n---", 1)[0]
        if re.search(r"^generated:\s*true\s*$", front, re.M):
            generated += 1
            if re.search(r"^source_commit:", front, re.M):
                stamped += 1
    return {"vault_notes": len(notes), "generated_notes": generated,
            "generated_notes_with_commit_stamps": stamped}


def defaults_digests() -> dict:
    out: dict = {}
    try:
        from learnloop.config import template
        out["defaults_digests"] = len(getattr(template, "DEFAULTS_SNAPSHOT_BY_ALGORITHM", {}) or {})
    except Exception as exc:  # noqa: BLE001
        out["defaults_digests_error"] = type(exc).__name__
    try:
        from learnloop.config.schema import AlgorithmsConfig
        out["algorithms_config_default_tag"] = AlgorithmsConfig.model_fields["algorithm_version"].default
    except Exception as exc:  # noqa: BLE001
        out["algorithms_config_default_error"] = type(exc).__name__
    return out


def repository_methods() -> int:
    tree = ast.parse(read(ROOT / "src/learnloop/db/repositories.py"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Repository":
            return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in node.body)
    return -1


def import_contracts() -> int:
    data = tomllib.loads(read(ROOT / "pyproject.toml"))
    return len(data.get("tool", {}).get("importlinter", {}).get("contracts", []))


# -- structure: what the refactor removes and must not let back ----------------

# A comment that names a stage artifact: a ruling, Codex, a review or fix round, a landing, or an F-/R-number
# ("review F3", "R12"). It matches the comment token's text, so a string holding "round 2" is not counted. The
# `noqa:` code list is cut first because F401 and F403 are lint codes, not findings.
STAGE_COMMENT = re.compile(
    r"\b(?:rulings?|ruled|codex|rounds?[ -]?\d+|fix[ -]rounds?|landings?|landed)\b|(?-i:\b[FR]-?\d{1,2}\b)",
    re.IGNORECASE,
)
NOQA = re.compile(r"noqa:[^#]*", re.IGNORECASE)
# A test file named for the pass that produced it, not for the behaviour it checks: a fix round (`_fix_round4`,
# `_fix10`, `_fix_r5`), a review pass (`codex_review`, `rereview`, `_review_fixes`, `_review_r3`), a final
# verification, a ruling, or a landing (`_landing`, `_close_fixes`). A stage id alone (`test_ro4_value.py`) is not
# matched: those name a feature's owner, and the behaviour they check is still the file's subject.
STAGE_TEST_NAME = re.compile(
    r"^test_.*(?:fix_?r(?:ound)?\d|_fix\d+|_rounds?\d*(?:_|\.py)|_r\d+(?:_|\.py)|rereview|codex_(?:re)?review|codex_verify"
    r"|final_(?:round|verify)|rulings?(?:_|\.py)|_fixes\.py$|landing|close_fixes|review_regressions"
    r"|review(?:\d|_r\d|_round|_fixes))"
)
CLOCK_ATTRS = {("datetime", "now"), ("datetime", "utcnow"), ("date", "today"), ("time", "time")}
CLOCK_MODULE = "learnloop.clock"
SERVING_ROOTS = ("learnloop_sidecar", "learnloop_mobile", "learnloop_mcp")
TERMINAL_ROOTS = ("learnloop.cli", "learnloop.tui")


def module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT / "src").with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _type_checking_guard(test: ast.expr) -> bool | None:
    """True for `TYPE_CHECKING` / `typing.TYPE_CHECKING`, False for its `not`, None for anything else."""

    if isinstance(test, ast.Name):
        return True if test.id == "TYPE_CHECKING" else None
    if isinstance(test, ast.Attribute):
        return True if test.attr == "TYPE_CHECKING" and isinstance(test.value, ast.Name) else None
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        inner = _type_checking_guard(test.operand)
        return None if inner is None else not inner
    return None


class _Imports(ast.NodeVisitor):
    """Import edges (top level apart from function-local) and wall-clock reads of one module."""

    def __init__(self, name: str, is_package: bool, modules: set[str]) -> None:
        self.name, self.is_package, self.modules = name, is_package, modules
        self.depth = 0
        self.top: set[str] = set()
        self.local: set[str] = set()
        self.clock = Counter()

    def _nearest(self, dotted: str) -> str | None:
        while dotted and dotted not in self.modules:
            dotted = dotted.rpartition(".")[0]
        return dotted or None

    def _targets(self, node: ast.Import | ast.ImportFrom) -> list[str]:
        if isinstance(node, ast.Import):
            return [t for a in node.names if (t := self._nearest(a.name))]
        base = node.module or ""
        if node.level:
            package = self.name if self.is_package else self.name.rpartition(".")[0]
            for _ in range(node.level - 1):
                package = package.rpartition(".")[0]
            base = f"{package}.{base}" if base else package
        found = []
        for alias in node.names:
            # `from pkg import mod` imports the submodule when there is one, else the package.
            target = f"{base}.{alias.name}" if f"{base}.{alias.name}" in self.modules else self._nearest(base)
            if target:
                found.append(target)
        return found

    def _record(self, node: ast.Import | ast.ImportFrom) -> None:
        edges = self.local if self.depth else self.top
        edges.update(t for t in self._targets(node) if t != self.name)

    visit_Import = visit_ImportFrom = _record

    def visit_If(self, node: ast.If) -> None:
        # Only the bare guard (`TYPE_CHECKING`, `typing.TYPE_CHECKING`) or its negation decides a branch: an import
        # under the guard never runs, so it is no edge, while the else and an `if not TYPE_CHECKING:` body do run.
        # Any other condition that merely mentions the name (`A or TYPE_CHECKING`) can run either branch.
        guard = _type_checking_guard(node.test)
        if guard is None:
            self.generic_visit(node)
            return
        for child in node.orelse if guard else node.body:
            self.visit(child)

    def _function(self, node: ast.AST) -> None:
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    visit_FunctionDef = visit_AsyncFunctionDef = _function

    def visit_Attribute(self, node: ast.Attribute) -> None:
        owner = node.value
        owner_name = owner.id if isinstance(owner, ast.Name) else owner.attr if isinstance(owner, ast.Attribute) else None
        if (owner_name, node.attr) in CLOCK_ATTRS:
            self.clock[f"{owner_name}.{node.attr}"] += 1
        elif (owner_name, node.attr) == ("time", "monotonic"):
            self.clock["time.monotonic"] += 1
        self.generic_visit(node)


def strongly_connected(edges: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's components of size > 1, largest first. Iterative: the graph is deeper than the recursion limit allows."""

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    out: list[list[str]] = []
    for root in sorted(edges):
        if root in index:
            continue
        work = [(root, iter(sorted(edges.get(root, ()))))]
        index[root] = low[root] = len(index)
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            for child in children:
                if child not in edges:
                    continue
                if child not in index:
                    index[child] = low[child] = len(index)
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(edges.get(child, ())))))
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    component = []
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        component.append(member)
                        if member == node:
                            break
                    if len(component) > 1:
                        out.append(sorted(component))
    return sorted(out, key=len, reverse=True)


def reachable(roots: list[str], edges: dict[str, set[str]]) -> set[str]:
    """Modules importing from ``roots`` can run; importing ``a.b.c`` runs ``a`` and ``a.b`` first."""

    seen: set[str] = set()
    todo = [r for r in roots if r in edges]
    while todo:
        module = todo.pop()
        if module in seen:
            continue
        seen.add(module)
        parts = module.split(".")
        todo.extend(p for i in range(1, len(parts)) if (p := ".".join(parts[:i])) in edges)
        todo.extend(edges[module])
    return seen


def lean_facts(text: str, tree: ast.AST) -> dict:
    """The few ``python_facts`` the ratchets read, without tokenizing every file: raw lines, long functions, and the
    stage-artifact comments. A file whose text never matches ``STAGE_COMMENT`` has none, so only the rest are tokenized."""

    facts = {"raw": text.count("\n") + (0 if text.endswith("\n") or not text else 1), "long_functions": [],
             "comments": None, "stage_comments": 0}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > 100:
                facts["long_functions"].append((node.name, node.lineno, length))
    if STAGE_COMMENT.search(text):
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.COMMENT and STAGE_COMMENT.search(NOQA.sub("", tok.string)):
                    facts["stage_comments"] += 1
        except (tokenize.TokenError, SyntaxError):
            pass
    return facts


def file_record(path: Path, modules: frozenset[str], lean: bool = False) -> dict:
    """Everything the sweep needs from one src file, from one parse: its facts, import edges and clock reads."""

    text = read(path)
    tree = ast.parse(text)
    visitor = _Imports(module_name(path), path.name == "__init__.py", modules)
    visitor.visit(tree)
    facts = lean_facts(text, tree) if lean else python_facts(path, text, tree)
    return {"facts": facts, "top": visitor.top, "local": visitor.local, "clock": visitor.clock}


def sweep_files(src_files: list[Path], parallel: bool = True) -> dict[Path, dict]:
    """``file_record`` for every file. The command-line run spreads the full ``python_facts`` over up to 8 processes
    (parsing and tokenizing 1,300 files is ~17 s on one core); the test calls ``structure_sweep`` for the serial lean path."""

    modules = frozenset(module_name(p) for p in src_files)
    workers = max(1, min(8, os.cpu_count() or 1))
    if not parallel or workers == 1:
        return {p: file_record(p, modules, lean=not parallel) for p in src_files}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return dict(zip(src_files, pool.map(file_record, src_files, [modules] * len(src_files), chunksize=16), strict=True))


def structure(src_files: list[Path], records: dict[Path, dict]) -> dict:
    """The structure measures (M0), from ``sweep_files``' records."""

    file_facts = {p: r["facts"] for p, r in records.items()}
    names = {module_name(p): p for p in src_files}
    modules = set(names)
    top = {name: records[path]["top"] for name, path in names.items()}
    local = {name: records[path]["local"] for name, path in names.items()}
    clock = Counter()
    clock_files: dict[str, int] = {}
    for name, path in names.items():
        if name != CLOCK_MODULE:
            clock.update(records[path]["clock"])
            clock_files[name] = sum(v for k, v in records[path]["clock"].items() if k != "time.monotonic")
    every = {m: top[m] | local[m] for m in modules}
    components = strongly_connected(every)
    largest = components[0] if components else []
    lines = {name: file_facts[path]["raw"] for name, path in names.items()}
    local_only = {m: local[m] - top[m] for m in modules}

    serving = reachable([m for m in modules if m.startswith(SERVING_ROOTS)], every)
    terminal = reachable([m for m in modules if m.startswith(TERMINAL_ROOTS)], every)
    terminal_only = terminal - serving
    unreached = modules - serving - terminal

    root_dir = ROOT / "src" / "learnloop"
    root_files = sorted(p.stem for p in src_files if p.parent == root_dir and p.name not in {"__init__.py", "__main__.py"})
    # `content` holds modules only in a subpackage, so a package is any first-level directory with a source file below it.
    packages = sorted({p.relative_to(root_dir).parts[0] for p in src_files if p.parent != root_dir and p.is_relative_to(root_dir)})

    over_200 = sorted(
        f"{rel(path)} {name}" for path in src_files
        for name, _line, length in file_facts[path]["long_functions"] if length > 200
    )
    stage_by_file = {rel(p): f["stage_comments"] for p, f in file_facts.items() if f["stage_comments"]}
    stage_tests = sorted(p.name for p in tracked("tests", suffix=".py") if STAGE_TEST_NAME.match(p.name))

    schema = ast.parse(read(ROOT / "src/learnloop/config/schema.py"))
    enabled = sum(
        isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and "enabled" in n.target.id
        and ast.unparse(n.annotation) == "bool"
        for n in ast.walk(schema)
    )
    golden = ROOT / "tests" / "goldens" / "effective_defaults.toml"
    golden_lines = read(golden).splitlines() if golden.is_file() else []
    set_keys = sum(1 for line in golden_lines if line and not line.startswith("#"))
    null_keys = sum(1 for line in golden_lines if line.startswith("# ") and line.endswith(" = null"))

    return {
        "import_component": {
            "modules": len(largest), "lines": sum(lines[m] for m in largest), "members": largest,
            "next_components": [len(c) for c in components[1:5]],
        },
        "modules_in_a_cycle": sum(len(c) for c in components),
        "function_local_only_edges": sum(len(v) for v in local_only.values()),
        "modules_with_a_function_local_only_edge": sum(1 for v in local_only.values() if v),
        "first_level_names": {
            "packages": len(packages), "root_modules": len(root_files),
            "root_modules_not_upgrade": sum(1 for n in root_files if not n.endswith("_upgrade")),
            "root_module_names": root_files,
        },
        "functions_over_200_lines": over_200,
        "stage_comments": {
            "comment_lines": None if any(f["comments"] is None for f in file_facts.values())
            else sum(f["comments"] for f in file_facts.values()),
            "naming_a_stage_artifact": sum(stage_by_file.values()), "by_file": stage_by_file,
            "regex": STAGE_COMMENT.pattern,
        },
        "stage_test_files": {"count": len(stage_tests), "names": stage_tests, "regex": STAGE_TEST_NAME.pattern},
        "wall_clock_reads_outside_clock_py": {
            "datetime_now": clock["datetime.now"], "datetime_utcnow": clock["datetime.utcnow"],
            "date_today": clock["date.today"], "time_time": clock["time.time"],
            "total": sum(clock[k] for k in ("datetime.now", "datetime.utcnow", "date.today", "time.time")),
            "modules": sum(1 for v in clock_files.values() if v), "time_monotonic": clock["time.monotonic"],
        },
        "serving_reach": {
            "terminal_only_modules": len(terminal_only), "terminal_only_lines": sum(lines[m] for m in terminal_only),
            "unreached_modules": len(unreached), "unreached_lines": sum(lines[m] for m in unreached),
        },
        "config": {
            "enabled_booleans_in_schema": enabled,
            "effective_default_keys": set_keys + null_keys, "effective_default_keys_unset": null_keys,
        },
    }


def structure_sweep() -> dict:
    """``structure`` over the tracked src files, serial and lean: one parse each, tokenizing only files that may hold a
    stage comment. The test calls this (inside xdist workers, so no processes) and imports no learnloop."""

    src_files = tracked(*PACKAGES, suffix=".py")
    return structure(src_files, sweep_files(src_files, parallel=False))


# -- the computed sweep --------------------------------------------------------


def computed(floor: str) -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    src_files = tracked(*PACKAGES, suffix=".py")
    totals = Counter()
    tag_where = Counter()
    long_fns: list[tuple[str, str, int, int]] = []
    per_file_raw: dict[str, int] = {}
    records = sweep_files(src_files)
    for path in src_files:
        f = records[path]["facts"]
        per_file_raw[rel(path)] = f["raw"]
        for key in ("raw", "code", "statements", "functions"):
            totals[key] += f[key]
        tag_where.update(f["tags"])
        long_fns += [(rel(path), name, line, n) for name, line, n in f["long_functions"]]
    over200 = sorted((n, f"{p}:{line} {name}") for p, name, line, n in long_fns if n > 200)
    root_upgrades = [p for p in src_files if re.fullmatch(r"src/learnloop/[a-z0-9_]+_upgrade\.py", rel(p))]
    all_upgrades = [p for p in src_files if "upgrade" in p.name]
    test_files = tracked("tests", suffix=".py")
    family = [p for p in test_files if p.name.startswith("test_") and UPGRADE_FAMILY.search(p.name)]
    gates = tag_gates(src_files, floor)
    latest = gates.get("latest") or floor
    return {
        "size": {
            "python_files": len(src_files),
            "src_learnloop_files": sum(1 for p in src_files if rel(p).startswith("src/learnloop/")),
            "raw_lines": totals["raw"], "code_lines": totals["code"],
            "statements": totals["statements"], "functions": totals["functions"],
            "functions_over_100_lines": len(long_fns),
            "functions_over_200_lines": len(over200),
            "longest_functions": [s for _, s in sorted(over200, reverse=True)[:10]],
            "config_template_lines": per_file_raw.get("src/learnloop/config/template.py"),
            "config_schema_lines": per_file_raw.get("src/learnloop/config/schema.py"),
            "test_python_files": len(test_files),
            "test_files_named_test_": sum(1 for p in test_files if p.name.startswith("test_")),
            "test_lines": sum(read(p).count("\n") for p in test_files),
            "migrations": len(tracked("migrations", suffix=".sql")),
        },
        "rules": {
            "root_upgrade_modules": len(root_upgrades),
            "all_upgrade_modules": len(all_upgrades),
            "upgrade_module_lines": sum(per_file_raw[rel(p)] for p in all_upgrades),
            "repository_methods": repository_methods(),
            "tag_literals": dict(tag_where),
            "tag_gates": gates,
            "import_linter_contracts": import_contracts(),
        },
        "structure": structure(src_files, records),
        "plumbing": {
            "head_fixture": head_fixture_refs(),
            **defaults_digests(),
            **generated_notes(),
            "tests": test_plumbing(test_files, floor, latest),
            "upgrade_and_successor_test_files": len(family),
            "upgrade_and_successor_test_lines": sum(read(p).count("\n") for p in family),
        },
    }


# -- timed ---------------------------------------------------------------------

TIMED = {
    # The audit's -n 8 figures were taken in a 10 GB scope; serial and
    # durability fit in 5 GB. Keep these identical at S0 and Z2.
    "serial": ("5G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider"]),
    "n8": ("10G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "--dist", "worksteal"]),
    "durability": ("5G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-m", "durability"]),
    # Step A6's two gates, which split n8's tests between them: every landing runs "landing", each arc's close runs
    # "arc_close". n8 stays the whole suite, so S0 and Z2 compare like with like.
    "landing": ("10G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "--dist", "worksteal",
                        "-m", "not arc_close"]),
    "arc_close": ("10G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "--dist", "worksteal",
                          "-m", "arc_close"]),
}


def timed_command(name: str, junit: Path) -> list[str]:
    memory, cmd = TIMED[name]
    return ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={memory}",
            "-p", "MemorySwapMax=1G", *cmd, f"--junitxml={junit}"]


def junit_seconds(junit: Path) -> dict:
    """Test seconds in all, and the upgrade-and-successor family's share."""

    total = family = 0.0
    tests = 0
    for case in ET.parse(junit).iter("testcase"):
        seconds = float(case.get("time") or 0)
        total += seconds
        tests += 1
        if UPGRADE_FAMILY.search((case.get("classname") or "").rsplit(".", 1)[-1]):
            family += seconds
    return {"tests": tests, "test_seconds": round(total, 1), "upgrade_family_seconds": round(family, 1),
            "upgrade_family_share": round(family / total, 4) if total else None}


def run_timed(names: list[str], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in names:
        junit = out_dir / f"{name}.xml"
        cmd = timed_command(name, junit)
        print(f"running {name}: {shlex.join(cmd)}", file=sys.stderr)
        start = time.monotonic()
        code = subprocess.run(cmd, cwd=ROOT).returncode
        results[name] = {"command": shlex.join(cmd), "exit_code": code,
                         "wall_seconds": round(time.monotonic() - start, 1)}
        if junit.is_file():
            results[name].update(junit_seconds(junit))
    return results


# -- manual --------------------------------------------------------------------

MANUAL = [
    ("Time to locate (§6)", "A fresh agent gets only a symptom, the vault and `why`; record minutes and files opened. "
     "Symptoms: (1) dormant or resolved learning objects still served (docs/reviews/daily-loop-bugs.md §2); "
     "(2) choosing a help style changed nothing (docs/reviews/owner-capture-2026-10-25-fixes.md B2); "
     "(3) the scheduler offer does not belong to this item/session (same, B4); (4) a router decision that fell back "
     "to a rule: which model failed and how; (5) where to change the mixing rule, an objective term, a route, a threshold."),
    ("The four real cases", "tests/test_why_cases.py passes; tests/test_why_real_cases.py passes on the owner's fresh "
     "backup copy (backup-API copy under fixtures-local/why-cases/); a no-code reader answers from `why`'s output."),
    ("`why` coverage", "`learnloop why` answers the latest decision, an attempt, a block and a figure with chosen, "
     "alternatives, losers' reasons, inputs, decider, versions, seed, next."),
    ("Silent sites S1-S15", "Each has a fail-first test, or a line in ADR-017 saying why not."),
    ("Decisions with no record", "B8's inventory lists none unexplained."),
    ("What a change costs", "On a scratch branch at Z2, make each §6 sample change and count files edited "
     "(git diff --stat); 'today' figures are in the strategy's §6 and the map's §9."),
    ("Next right after feedback; connection opens per job", "The router speed harness on large backup-API copies "
     "(docs/reviews/router-speed2.md, method and pinned week), against mvp-0.49 by the same method."),
    ("Decision values at a fixed draw count", "P-draw: byte-identical across each speed step."),
    ("Kill switches at or below the floor", "Read D7's list; count the switches whose tag is at or below the floor."),
    ("Tag gates paired with a kill switch", "Read each site in the JSON's `constant_sites`; the split isn't syntactic."),
    ("Database size", "The owner reports each live vault's state.sqlite size before and after each drop (private; "
     "kept in fixtures-local/, never committed)."),
    ("Removed list", "Z2's report names every removed feature."),
]


# -- output --------------------------------------------------------------------


def markdown(report: dict) -> str:
    c = report.get("computed", {})
    size, rules, plumb = c.get("size", {}), c.get("rules", {}), c.get("plumbing", {})
    gates = rules.get("tag_gates", {})
    tags = rules.get("tag_literals", {})
    head = plumb.get("head_fixture", {})
    tests = plumb.get("tests", {})
    st = c.get("structure", {})
    comp, names, comments = st.get("import_component", {}), st.get("first_level_names", {}), st.get("stage_comments", {})
    clock, reach, cfg = st.get("wall_clock_reads_outside_clock_py", {}), st.get("serving_reach", {}), st.get("config", {})
    structure_rows = [
        ("Largest import component: modules (lines); next components",
         f"{comp.get('modules')} ({comp.get('lines')}); {comp.get('next_components')}"),
        ("Modules in any import cycle", st.get("modules_in_a_cycle")),
        ("Import edges only inside functions; modules with one",
         f"{st.get('function_local_only_edges')}; {st.get('modules_with_a_function_local_only_edge')}"),
        ("First-level names in `src/learnloop`: packages; root modules; root modules not `*_upgrade`",
         f"{names.get('packages')}; {names.get('root_modules')}; {names.get('root_modules_not_upgrade')}"),
        ("Functions over 200 lines", len(st.get("functions_over_200_lines", []))),
        ("Comment lines naming a stage artifact (of all comment lines)",
         f"{comments.get('naming_a_stage_artifact')} ({comments.get('comment_lines')})"),
        ("Test files named for a stage or fix round", st.get("stage_test_files", {}).get("count")),
        ("Wall-clock reads outside `clock.py`: total (now / utcnow / today / time); `time.monotonic`",
         f"{clock.get('total')} ({clock.get('datetime_now')} / {clock.get('datetime_utcnow')} / "
         f"{clock.get('date_today')} / {clock.get('time_time')}); {clock.get('time_monotonic')}"),
        ("Reachable only from `cli` and `tui`: modules (lines); reachable from nothing",
         f"{reach.get('terminal_only_modules')} ({reach.get('terminal_only_lines')}); "
         f"{reach.get('unreached_modules')} ({reach.get('unreached_lines')})"),
        ("`enabled` booleans in `config/schema.py`; effective config leaves (unset)",
         f"{cfg.get('enabled_booleans_in_schema')}; {cfg.get('effective_default_keys')} ({cfg.get('effective_default_keys_unset')})"),
    ]
    rows = [
        ("Python files, all four packages", size.get("python_files")),
        ("Raw lines; code lines", f"{size.get('raw_lines')}; {size.get('code_lines')}"),
        ("Statements; functions", f"{size.get('statements')}; {size.get('functions')}"),
        ("Functions over 100 lines; over 200", f"{size.get('functions_over_100_lines')}; {size.get('functions_over_200_lines')}"),
        ("`config/template.py`; `config/schema.py` lines", f"{size.get('config_template_lines')}; {size.get('config_schema_lines')}"),
        ("Root `*_upgrade.py`; all upgrade modules (lines)",
         f"{rules.get('root_upgrade_modules')}; {rules.get('all_upgrade_modules')} ({rules.get('upgrade_module_lines')})"),
        ("`Repository` methods", rules.get("repository_methods")),
        ("`mvp-0.N` literals: code / docstring / comment", f"{tags.get('code')} / {tags.get('docstring')} / {tags.get('comment')}"),
        (f"Tag gates: constant at {gates.get('floor')} / all (varying, unclassified)",
         f"{gates.get('constant_at_floor')} / {gates.get('gates')} ({gates.get('varying')}, {gates.get('unclassified')})"),
        ("Latest tag; chain length", f"{gates.get('latest')}; {gates.get('chain_length')}"),
        ("Import-linter contracts", rules.get("import_linter_contracts")),
        ("Head fixture; its tracked files", f"{', '.join(head.get('head_fixtures', []))}; {head.get('head_fixture_files')}"),
        ("Files naming the head path: tests + scripts (lines)",
         f"{head.get('test_files')} + {head.get('script_files')} ({head.get('lines')})"),
        ("Frozen defaults digests; test files reading them",
         f"{plumb.get('defaults_digests')}; {tests.get('files_reading_defaults_digests')}"),
        ("Frozen `*_VERSIONS` set assertions (files)",
         f"{tests.get('frozen_version_set_assertions')} ({tests.get('files_with_frozen_version_sets')})"),
        ("Test files with a latest pin", tests.get("files_with_a_latest_pin")),
        ("Test files naming the latest tag; a tag at or above the floor; any tag",
         f"{tests.get('files_naming_the_latest_tag')}; {tests.get('files_naming_a_tag_at_or_above_floor')}; {tests.get('files_naming_any_tag')}"),
        ("Default test vault's tag; files using it; of those naming no version",
         f"{plumb.get('algorithms_config_default_tag')}; {tests.get('files_using_create_basic_vault')}; {tests.get('of_those_naming_no_version')}"),
        ("Upgrade and successor test files (lines)",
         f"{plumb.get('upgrade_and_successor_test_files')} ({plumb.get('upgrade_and_successor_test_lines')})"),
        ("Vault notes; generated; generated with commit stamps",
         f"{plumb.get('vault_notes')}; {plumb.get('generated_notes')}; {plumb.get('generated_notes_with_commit_stamps')}"),
        ("Test Python files (named `test_*`); lines",
         f"{size.get('test_python_files')} ({size.get('test_files_named_test_')}); {size.get('test_lines')}"),
        ("Migrations", size.get("migrations")),
    ]
    lines = [f"# Refactor measures at `{report['commit']}`", "",
             f"Computed {report['generated_at']}. Floor {gates.get('floor')}.", "",
             "| Measure | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in rows]
    lines += ["", "## Structure", "", "| Measure | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in structure_rows]
    lines += ["", "## Timed", ""]
    timed = report.get("timed")
    if timed:
        lines += ["| Run | Wall s | Exit | Tests | Test s | Upgrade family share |", "|---|---:|---:|---:|---:|---:|"]
        for name, r in timed.items():
            lines.append(f"| {name} | {r.get('wall_seconds')} | {r.get('exit_code')} | {r.get('tests')} | "
                         f"{r.get('test_seconds')} | {r.get('upgrade_family_share')} |")
    else:
        lines.append("Not run (pass `--timed`). The commands:")
    lines += ["", "```"] + report["timed_commands"] + ["```", "", "## Manual", ""]
    lines += [f"- **{name}.** {how}" for name, how in MANUAL]
    if gates.get("problems"):
        lines += ["", "## Problems", ""] + [f"- {p}" for p in gates["problems"]]
    return "\n".join(lines) + "\n"


def _oldest_supported() -> str:
    """The floor the code enforces: a gate is constant when every tag a vault can be opened at takes it."""

    sys.path.insert(0, str(ROOT / "src"))
    from learnloop.algorithm_versions import OLDEST_SUPPORTED

    return OLDEST_SUPPORTED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--floor", default=None,
                        help="oldest tag a live vault holds (default: algorithm_versions.OLDEST_SUPPORTED)")
    parser.add_argument("--json", type=Path, help="write the JSON report here (default: stdout)")
    parser.add_argument("--markdown", type=Path, help="write the Markdown table here")
    parser.add_argument("--timed", default="", help="comma list of serial,n8,durability,landing,arc_close: run those suites (machine time)")
    parser.add_argument("--timed-dir", type=Path, default=ROOT / "fixtures-local" / "refactor-measures",
                        help="where timed runs write their JUnit XML (gitignored by default)")
    args = parser.parse_args(argv)
    names = [n for n in args.timed.split(",") if n]
    unknown = [n for n in names if n not in TIMED]
    if unknown:
        parser.error(f"unknown timed run(s): {', '.join(unknown)}")
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=10", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
                                check=True, capture_output=True, text=True).stdout.strip())
    report = {
        "commit": commit + ("+dirty" if dirty else ""),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "computed": computed(args.floor or _oldest_supported()),
        "timed_commands": [f"{n}: {shlex.join(timed_command(n, args.timed_dir / f'{n}.xml'))}" for n in TIMED],
        "timed": run_timed(names, args.timed_dir) if names else None,
        "manual": [{"measure": name, "procedure": how} for name, how in MANUAL],
    }
    text = json.dumps(report, indent=2, sort_keys=False)
    if args.json:
        args.json.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.markdown:
        args.markdown.write_text(markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
