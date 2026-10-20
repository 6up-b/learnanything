"""Adaptive difficulty AD2+AD3, fix round 8: AD reads items, attempts, questions, reading receipts,
presentations and reveals only through its material view (spec A8; Codex verify F19-F27).

The boundary is structural (``adaptive_difficulty/material_view.py``): this test fails when any
module under ``adaptive_difficulty/``, the plan's AD slot (``daily_plan/ad_slot.py``), the
commissioned path of ``content/authoring/practice_generation.py`` or the sidecar's AD handlers
reads a raw reader directly. The allowlist is explicit and short.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
AD = ROOT / "learnloop" / "adaptive_difficulty"

#: Raw readers AD may reach only through the view.
RAW_CALLS = {"load_attempt_rows", "held_out_items", "held_out_material", "held_out_item_ids",
             "get_reader_authored_question", "load_authoritative_observation_ledger"}
RAW_ATTRIBUTES = {"practice_items"}
RAW_TABLES = ("practice_attempts", "reader_authored_questions", "plan_presentations", "reveal_events",
              "practice_item_snapshots", "ad_reading_opportunities")
_READ = re.compile(r"\b(?:FROM|JOIN)\s+(" + "|".join(RAW_TABLES) + r")\b", re.IGNORECASE)

#: Where a raw reader is allowed: the view itself; the predicate it reads (which must see every
#: item to decide what is held out); data_check's descriptive whole-vault inventory (no forecast,
#: prompt, selection or commission reads it); and the background preparation queue's scheduling
#: (its keys are item revisions to prepare; each run reads them back through its own view and
#: reports a withheld one ``protected``, never quoting it).
ALLOWED_MODULES = {"material_view.py", "protection.py", "data_check.py"}
ALLOWED_FUNCTIONS = {("background.py", "schedule_item_preparation"), ("background.py", "changed_revisions"),
                     ("background.py", "schedule_new_revisions")}


def _docstrings(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(
                    first.value.value, str):
                ids.add(id(first.value))
    return ids


def _function_spans(tree: ast.AST) -> list[tuple[str, int, int]]:
    return [(node.name, node.lineno, node.end_lineno or node.lineno) for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _violations(path: Path, *, only: set[str] | None = None) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = _docstrings(tree)
    spans = _function_spans(tree)

    def owner(line: int) -> str | None:
        inside = [(name, start, end) for name, start, end in spans if start <= line <= end]
        return min(inside, key=lambda span: span[2] - span[1])[0] if inside else None

    found = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        what = None
        if isinstance(node, ast.Attribute) and node.attr in RAW_ATTRIBUTES:
            what = f".{node.attr}"
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in RAW_CALLS:
                what = f"{name}()"
            elif name == "getattr" and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) \
                    and node.args[1].value in RAW_ATTRIBUTES:
                what = f"getattr(..., {node.args[1].value!r})"
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            match = _READ.search(node.value)
            if match:
                what = f"SQL read of {match.group(1)}"
        if what is None or line is None:
            continue
        function = owner(line)
        if only is not None and function not in only:
            continue
        if (path.name, function) in ALLOWED_FUNCTIONS:
            continue
        where = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
        found.append(f"{where}:{line} ({function}): {what}")
    return found


def test_ad_reads_items_attempts_and_questions_only_through_its_material_view():
    """Every module of the AD package, the plan's AD slot and the sidecar's AD handlers read no raw
    item, attempt, Reader-question, reading-receipt, presentation, reveal or snapshot reader, and
    never compute the held-out predicate themselves (fix round 8's structural ruling)."""

    violations: list[str] = []
    for path in sorted(AD.glob("*.py")):
        if path.name in ALLOWED_MODULES:
            continue
        violations += _violations(path)
    violations += _violations(ROOT / "learnloop" / "daily_plan" / "ad_slot.py")
    violations += _violations(ROOT / "learnloop_sidecar" / "handlers" / "adaptive_difficulty.py")
    assert violations == [], "\n".join(violations)


def test_the_commissioned_generation_path_reads_through_the_view():
    """The commissioned branch of the generation path (its AD view and waypoint) reads no raw
    reader; the predecessor's shared helpers read the vault only when no AD view is given."""

    path = ROOT / "learnloop" / "content" / "authoring" / "practice_generation.py"
    assert _violations(path, only={"_ad_material_view", "_ad_commissioned_rung"}) == []
    source = path.read_text(encoding="utf-8")
    for helper in ("_active_practice_item_counts", "_active_surface_families", "_active_evidence_facet_unions"):
        body = source[source.index(f"def {helper}("):]
        body = body[:body.index("\ndef ", 1)]
        assert "items if items is not None else vault.practice_items.values()" in body, helper


def test_the_allowlist_is_short_and_every_entry_exists():
    assert ALLOWED_MODULES == {"material_view.py", "protection.py", "data_check.py"}
    for name in ALLOWED_MODULES:
        assert (AD / name).exists(), name
    background = (AD / "background.py").read_text(encoding="utf-8")
    for module, function in ALLOWED_FUNCTIONS:
        assert module == "background.py" and f"def {function}(" in background, function


def test_the_scan_catches_a_raw_reader(tmp_path):
    """The check itself works: a module reading the item map or attempts directly is reported."""

    probe = tmp_path / "_probe_for_test.py"
    probe.write_text('def leak(vault, connection):\n'
                     '    """FROM practice_attempts in a docstring is fine."""\n'
                     '    items = vault.practice_items\n'
                     '    return connection.execute("SELECT * FROM practice_attempts")\n', encoding="utf-8")
    found = _violations(probe)
    assert len(found) == 2 and any(".practice_items" in v for v in found) and any("practice_attempts" in v
                                                                                for v in found)
