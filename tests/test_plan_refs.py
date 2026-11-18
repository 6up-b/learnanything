"""The plan's offer and stop names live in one standard-library leaf (``learnloop.plan_refs``) that every layer reads,
and the two offer predicates refuse the other's argument instead of answering False."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from learnloop import plan_refs
from learnloop.daily_plan import lesson_offer
from learnloop.daily_plan import types as plan_types
from learnloop.db.stores import router_suggestions
from learnloop.followup_serve import workflow
from learnloop.router import decisions, plan_log
from learnloop.router_objective import types as objective_types

REPO = Path(__file__).resolve().parent.parent


def test_the_strings_keep_their_bytes_and_every_layer_reads_the_leafs():
    assert (plan_refs.LESSON_OFFER_SUBTYPE, plan_refs.LESSON_OFFER_PREFIX, plan_refs.STOP_FOR_TODAY) == (
        "lesson_offer", "lesson_offer:", "stop_for_today")
    for name in ("LESSON_OFFER_SUBTYPE", "LESSON_OFFER_PREFIX", "STOP_FOR_TODAY"):
        assert getattr(objective_types, name) is getattr(plan_refs, name)
        assert getattr(plan_types, name) is getattr(plan_refs, name)
    assert objective_types.is_offer_subtype is plan_refs.is_offer_subtype
    assert plan_log.OFFER_PREFIX is router_suggestions.OFFER_REF_PREFIX is workflow.LESSON_REF_PREFIX \
        is plan_refs.LESSON_OFFER_PREFIX
    assert plan_log.STOP_REF is decisions.STOP_REF is plan_refs.STOP_FOR_TODAY


def test_the_leaf_imports_nothing_but_the_standard_library():
    tree = ast.parse((REPO / "src/learnloop/plan_refs.py").read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imported <= {"__future__"}, imported


def test_the_lesson_offer_predicate_takes_a_candidate_and_refuses_a_subtype():
    assert lesson_offer.is_offer(SimpleNamespace(subtype="lesson_offer")) is True
    assert lesson_offer.is_offer(SimpleNamespace(subtype=None)) is False
    assert lesson_offer.is_offer(SimpleNamespace()) is False
    with pytest.raises(TypeError):
        lesson_offer.is_offer("lesson_offer")


def test_the_subtype_predicate_takes_a_subtype_and_refuses_a_candidate():
    assert plan_refs.is_offer_subtype("lesson_offer") is True
    assert plan_refs.is_offer_subtype("reading") is False
    assert plan_refs.is_offer_subtype(None) is False
    with pytest.raises(TypeError):
        plan_refs.is_offer_subtype(SimpleNamespace(subtype="lesson_offer"))  # type: ignore[arg-type]


def test_why_reads_the_offer_prefix_without_loading_numpy():
    probe = ("import sys, learnloop.why.reader; "
             "print(sorted(n for n in ('numpy', 'learnloop.scheduling.fsrs', 'learnloop.router_objective.types') "
             "if n in sys.modules))")
    out = subprocess.run([sys.executable, "-c", probe], check=True, capture_output=True, text=True, cwd=REPO)
    assert out.stdout.strip() == "[]", out.stdout
