"""The evidence-cutoff census (``tests/fixtures/evidence_cutoff_census.toml``) stays true to the tree.

Each row names a caller (``path::qualname``) that cuts learner evidence by time and the preset of
``learnloop.db.evidence_cutoff`` it follows. The checks: the caller exists and makes the call the row names; a
row marked ``adapted`` names the cutoff module in its own body; a proof names an existing test; and every function
that asks the attempt availability predicate (``attempt_time_sql``, ``known_at``) or builds a router closure
(``Closure.at``, ``Closure.through``) is a row, so a new time-cut reader cannot arrive unnamed.
"""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path
import tomllib

from learnloop.db import evidence_cutoff as EC

ROOT = Path(__file__).resolve().parents[1]
CENSUS = Path(__file__).resolve().parent / "fixtures" / "evidence_cutoff_census.toml"
STATUSES = {"adapted", "named", "no_preset", "not_a_cutoff"}
#: What a reader that states its preset names from the cutoff module.
CUTOFF_NAMES = frozenset(EC.__all__) | {"history_v1", "corrected_before", "closure_through", "closure_at",
                                         "ad_replay", "completed_by", "as_known_at"}


def _rows() -> list[dict]:
    return tomllib.loads(CENSUS.read_text(encoding="utf-8"))["reader"]


@cache
def _functions(path: str) -> dict[str, ast.AST]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    out: dict[str, ast.AST] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                out[prefix + child.name] = child
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            else:
                visit(child, prefix)

    visit(tree, "")
    return out


def _own_nodes(function: ast.AST) -> list[ast.AST]:
    """The function's own nodes: a nested function or class is its own row (a lambda is not)."""

    out, stack = [], list(ast.iter_child_nodes(function))
    while stack:
        node = stack.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        out.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return out


def _called(function: ast.AST) -> set[str]:
    names = set()
    for node in _own_nodes(function):
        if isinstance(node, ast.Call):
            func = node.func
            names.add(func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", ""))
    return names


def _named(function: ast.AST) -> set[str]:
    return {node.id for node in _own_nodes(function) if isinstance(node, ast.Name)} | {
        node.attr for node in _own_nodes(function) if isinstance(node, ast.Attribute)}


def test_every_row_is_well_formed_and_its_caller_makes_the_call():
    rows = _rows()
    assert rows
    callers = [row["caller"] for row in rows]
    assert len(callers) == len(set(callers)), "a caller listed twice"
    for row in rows:
        assert row["status"] in STATUSES, row
        if row["status"] in ("adapted", "named"):
            assert row["preset"] in EC.PRESETS, row
        else:
            assert row["preset"] == "", row
        if row["status"] == "no_preset":
            assert row.get("differs"), row
        assert row["evidence"], row
        path, _, qualname = row["caller"].partition("::")
        functions = _functions(path)
        assert qualname in functions, f"{row['caller']} does not exist"
        assert row["calls"] in _called(functions[qualname]), f"{row['caller']} makes no call to {row['calls']}"


def test_an_adapted_reader_names_the_cutoff_module():
    for row in _rows():
        if row["status"] != "adapted":
            continue
        path, _, qualname = row["caller"].partition("::")
        assert _named(_functions(path)[qualname]) & CUTOFF_NAMES, row["caller"]


def test_every_proof_exists():
    for row in _rows():
        proof = row.get("proof")
        if not proof:
            assert row["status"] == "no_preset", row
            continue
        path, _, name = proof.partition("::")
        assert (ROOT / path).exists(), proof
        if name:
            assert name in _functions(path), proof


def _time_cut_callers() -> set[str]:
    """Every function under ``src/`` that asks the availability predicate or builds a closure."""

    found = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in ("attempt_time_sql", "known_at", "Closure.")):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative == "src/learnloop/db/attempt_availability.py":
            continue  # the predicate itself
        for qualname, function in _functions(relative).items():
            for node in _own_nodes(function):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                closure = (name in ("at", "through") and isinstance(func, ast.Attribute)
                           and ((isinstance(func.value, ast.Name) and func.value.id == "Closure")
                                or (isinstance(func.value, ast.Attribute) and func.value.attr == "Closure")))
                if name in ("attempt_time_sql", "known_at") or closure:
                    found.add(f"{relative}::{qualname}")
    return found


def test_every_time_cut_caller_is_in_the_census():
    listed = {row["caller"] for row in _rows()}
    missing = sorted(_time_cut_callers() - listed)
    assert not missing, (f"time-cut readers missing from {CENSUS.name}: {missing}. Add a row naming the preset it "
                         "follows (or no_preset with how it differs).")


def test_the_census_names_every_preset_but_the_unread_ones():
    """``current`` and ``as_known_at`` have no reader yet (no read applies historical corrections); every other
    preset reproduces at least one adapted reader."""

    adapted = {row["preset"] for row in _rows() if row["status"] == "adapted"}
    assert adapted == set(EC.PRESETS) - {EC.CURRENT, EC.AS_KNOWN_AT}
