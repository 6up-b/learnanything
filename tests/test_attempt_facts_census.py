"""The attempt-facts census (``tests/fixtures/attempt_facts_census.toml``) stays true to the tree.

Each row names a reader (``path::qualname``) that decides whether an attempt was assisted, cold, primed, eligible
or independent, the predicate it applies and its owner. The checks: the reader exists and reads what the row says;
an ``adapted`` reader names its predicate of ``learnloop.attempts.fact_predicates``; every predicate a row names is
one; every predicate is some row's; and every function that names one of the predicate authorities below is a row,
so a new reader of one cannot arrive unnamed.
"""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path
import tomllib

from learnloop.attempts import fact_predicates as P

ROOT = Path(__file__).resolve().parents[1]
CENSUS = Path(__file__).resolve().parent / "fixtures" / "attempt_facts_census.toml"
STATUSES = {"adapted", "delegated", "named", "not_adapted"}
PURPOSES = {"assisted", "cold", "primed", "eligible", "independent", "research_cold", "help_timing", "category",
            "fsrs_cap"}
PREDICATES = {name for name in P.__all__ if callable(getattr(P, name))}
#: The names that mark a reader of an attempt's assistance or coldness: the owners' predicates and type sets, the
#: coldness receipt's claim, and the named predicates themselves.
AUTHORITIES = frozenset({
    "attempt_counts_as_assisted", "classify_attempt_activity", "resolve_attempt_activity_policy", "is_assisted",
    "counts_as_assisted", "UNAIDED_TYPES", "ASSISTED_ATTEMPT_TYPES", "LEGACY_ASSISTED_ATTEMPT_TYPES",
    "COLD_ATTEMPT_TYPES", "CLEAN_ATTEMPT_TYPES", "GRADED_RETRIEVAL_TYPES", "INDEPENDENT_ATTEMPT_TYPES",
    "QUALIFYING_ATTEMPT_TYPES", "ELIGIBLE_TYPES", "fsrs_rating_for_attempt", "help_timing", "_unassisted",
    "_qualifies_for_field_memory_retrieval", "_passes_intervention_coldness_checks", "_attempt_is_assisted",
    "qualifies_as_cold_retrieval", *PREDICATES,
})
#: Where the authorities are defined rather than read: the facts, the predicates, and the policy's record type.
NOT_READERS = frozenset({
    "src/learnloop/causal_activity_policy.py::CausalActivityPolicy.as_dict",
})
DEFINING_MODULES = ("src/learnloop/attempts/fact_predicates.py", "src/learnloop/attempts/facts.py")


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
    """The function's own nodes: a nested function or class is its own row."""

    out, stack = [], list(ast.iter_child_nodes(function))
    while stack:
        node = stack.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        out.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return out


def _named(function: ast.AST) -> set[str]:
    nodes = _own_nodes(function)
    return ({node.id for node in nodes if isinstance(node, ast.Name)}
            | {node.attr for node in nodes if isinstance(node, ast.Attribute)})


def _strings(function: ast.AST) -> list[str]:
    return [node.value for node in _own_nodes(function) if isinstance(node, ast.Constant)
            and isinstance(node.value, str)]


def _reads(function: ast.AST, token: str) -> bool:
    return token in _named(function) or any(token in text for text in _strings(function))


def test_every_row_is_well_formed_and_its_reader_reads_what_it_says():
    rows = _rows()
    assert rows
    callers = [row["caller"] for row in rows]
    assert len(callers) == len(set(callers)), "a reader listed twice"
    for row in rows:
        assert row["status"] in STATUSES, row
        assert row["purpose"] in PURPOSES, row
        assert row["evidence"] and row["owner"], row
        if row["status"] == "not_adapted":
            assert row.get("why"), row
        else:
            assert row.get("proof"), row
        path, _, qualname = row["caller"].partition("::")
        functions = _functions(path)
        assert qualname in functions, f"{row['caller']} does not exist"
        assert _reads(functions[qualname], row["reads"]), f"{row['caller']} does not read {row['reads']}"


def test_an_adapted_reader_names_its_predicate_and_every_predicate_named_is_one():
    for row in _rows():
        if row["predicate"]:
            assert row["predicate"] in PREDICATES, row
        if row["status"] == "adapted":
            path, _, qualname = row["caller"].partition("::")
            assert row["predicate"] in _named(_functions(path)[qualname]), row["caller"]


def test_every_predicate_is_some_readers():
    named = {row["predicate"] for row in _rows()}
    assert PREDICATES - named == set()


def test_every_proof_exists():
    for row in _rows():
        proof = row.get("proof")
        if not proof:
            continue
        path, _, name = proof.partition("::")
        assert (ROOT / path).exists(), proof
        if name:
            assert name in _functions(path), proof


def _authority_readers() -> set[str]:
    found = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative in DEFINING_MODULES:
            continue
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in AUTHORITIES):
            continue
        for qualname, function in _functions(relative).items():
            if (_named(function) & AUTHORITIES) or any(
                    text in AUTHORITIES for text in _strings(function)):
                found.add(f"{relative}::{qualname}")
    return found - NOT_READERS


def test_every_reader_of_an_authority_is_in_the_census():
    listed = {row["caller"] for row in _rows()}
    missing = sorted(_authority_readers() - listed)
    assert not missing, (f"assistance/coldness readers missing from {CENSUS.name}: {missing}. Add a row naming the "
                         "predicate it applies and its owner.")


def test_the_ledger_ids_a_row_names_are_the_records():
    record = (ROOT / "docs" / "reviews" / "ep0-attempt-facts.md").read_text(encoding="utf-8")
    for row in _rows():
        if row.get("ledger"):
            assert f"| {row['ledger']} |" in record, row
