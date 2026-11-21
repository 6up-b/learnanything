"""The named predicates over attempt facts (``learnloop.attempts.fact_predicates``) equal the readers' own.

Every value on the attempt matrix equals the verbatim copy of the reader's expression
(``tests/attempt_predicate_helpers.py``), and a kernel moved from a reader is the reader's expression node for node,
its row reads mapped onto the facts fields it reads instead (AST identity).
The grader's contexts can reach none of it: no grading module imports the facts or the predicates, and neither
context type has a field for them.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import itertools
from pathlib import Path

from learnloop.attempts import fact_predicates as P
from learnloop.attempts.ai_contracts import GradingContext
from learnloop.attempts.blind_grading import BlindGradingContext, blind_grading_context
from learnloop.attempts.facts import submitted_facts
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.learner.lesson_weight import COLD_ATTEMPT_TYPES

from tests.attempt_predicate_helpers import (
    BASE_SOURCES, CAP_HINTS, CAP_MAPS, MATRIX, SCANS, base_canonical, base_cap_value, base_card_assisted,
    base_coldness, base_history_assisted, base_intervention, base_lesson_cold, base_primed_only, base_teacher_cold,
    base_teacher_kind,
)

ROOT = Path(__file__).resolve().parents[1]


def _facts(row):
    return submitted_facts(attempt_type=row["attempt_type"], hints_used=row["hints_used"], primed=row["primed"],
                           correctness=row["correctness"])


# -- values ------------------------------------------------------------------------------------------------------


def test_every_predicate_equals_its_readers_expression_on_the_matrix():
    for row in MATRIX:
        facts = _facts(row)
        assert P.counts_as_assisted(facts) == base_canonical(row), row
        assert P.recorded_counts_as_assisted(facts, None) == base_canonical(row), row
        assert P.intervention_assisted(facts) == base_intervention(row), row
        assert P.diagnoser_assisted(facts) == base_history_assisted(row["attempt_type"], row["hints_used"]), row
        assert P.diagnoser_cold_unassisted(facts) == (
            not base_history_assisted(row["attempt_type"], row["hints_used"]) and not bool(row["primed"])), row
        assert P.unhelped_cold_type(facts) == base_teacher_cold(row), row
        assert P.graded_cold_check(facts, COLD_ATTEMPT_TYPES) == base_lesson_cold(row), row
        assert P.teacher_attempt_kind(facts) == base_teacher_kind(row), row
        assert P.hinted_or_primed(facts) == base_card_assisted(row), row
        assert P.primed_only(facts) == base_primed_only(row), row
        for scan in SCANS:
            assert P.unassisted_for_coldness(facts, scan) == base_coldness(dict(row), scan), (row, scan)


def test_the_recorded_classification_reaches_the_projections_assisted():
    recorded = ({"contamination_class": "repair_activity"}, {"contamination_class": "pure_diagnostic"},
                {"contamination_class": "verification", "near_clone": True}, {})
    for row, stored, status in itertools.product(MATRIX[::7], recorded, (None, "verified", "unverified")):
        expected = resolve_attempt_activity_policy(
            attempt_type=row["attempt_type"], hints_used=row["hints_used"], primed=row["primed"], recorded=stored,
            reference_status=status).counts_as_assisted
        assert P.recorded_counts_as_assisted(_facts(row), stored, status) == expected


def test_the_fsrs_cap_lookup_keeps_key_coercion_and_fallback():
    maps = (*CAP_MAPS, {1: 2, "3": 4}, {"2": "good", 5: "again"}, {None: "good", "1.5": "hard"})
    for mapping, hints in itertools.product(maps, (*CAP_HINTS, -1)):
        assert P.fsrs_cap_value(mapping, hints) == base_cap_value(mapping, hints), (mapping, hints)
        facts = submitted_facts(attempt_type="independent_attempt", hints_used=hints)
        assert P.fsrs_rating_cap(facts, mapping) == base_cap_value(mapping, hints)


# -- the moved kernels, node for node ----------------------------------------------------------------------------

_FIELDS = {"attempt_type": "produced_as", "hints_used": "hints_used", "primed": "primed",
           "correctness": "correctness"}
_NAMES = {"ASSISTED_ATTEMPT_TYPES": "DIAGNOSER_ASSISTED_TYPES", "_COLD_TYPES": "cold_types",
          "COLD_ATTEMPT_TYPES": "cold_types"}


def _facts_field(key: str) -> ast.Attribute:
    return ast.Attribute(value=ast.Name(id="facts", ctx=ast.Load()), attr=_FIELDS[key], ctx=ast.Load())


class _ToFacts(ast.NodeTransformer):
    """A reader's row reads (``row["k"]``, ``row.get("k")``, a local named for the column) as facts reads."""

    def __init__(self, row_names: tuple[str, ...], local_names: tuple[str, ...] = ()) -> None:
        self.row_names, self.local_names = row_names, local_names

    def visit_Subscript(self, node):
        if (isinstance(node.value, ast.Name) and node.value.id in self.row_names
                and isinstance(node.slice, ast.Constant) and node.slice.value in _FIELDS):
            return _facts_field(node.slice.value)
        return self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        if (isinstance(func, ast.Attribute) and func.attr == "get" and isinstance(func.value, ast.Name)
                and func.value.id in self.row_names and node.args and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in _FIELDS):
            return _facts_field(node.args[0].value)
        if isinstance(func, ast.Name) and func.id == "_cold":
            return ast.Call(func=ast.Name(id="unhelped_cold_type", ctx=ast.Load()),
                            args=[ast.Name(id="facts", ctx=ast.Load())], keywords=[])
        return self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.local_names:
            return _facts_field(node.id)
        if node.id in _NAMES and node.id not in self.row_names:
            return ast.Name(id=_NAMES[node.id], ctx=node.ctx)
        return node


def _dump(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=False, include_attributes=False)


PREDICATES = ROOT / "src" / "learnloop" / "attempts" / "fact_predicates.py"


def _kernel(name: str) -> ast.FunctionDef:
    """The predicate's definition as parsed from its module's file."""

    for node in ast.parse(PREDICATES.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"no predicate {name}")


def _body(function: ast.FunctionDef) -> list[ast.stmt]:
    body = list(function.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]  # the docstring
    return body


def _returned(name: str) -> ast.expr:
    (statement,) = _body(_kernel(name))
    assert isinstance(statement, ast.Return)
    return statement.value


def test_the_moved_expression_kernels_are_the_readers_expressions():
    for name, rows, locals_ in (("diagnoser_assisted", (), ("hints_used", "attempt_type")),
                                ("unhelped_cold_type", ("row",), ()), ("graded_cold_check", ("row",), ()),
                                ("teacher_attempt_kind", ("row",), ()), ("hinted_or_primed", ("row",), ()),
                                ("primed_only", ("row",), ())):
        old = _ToFacts(rows, locals_).visit(ast.parse(BASE_SOURCES[name], mode="eval").body)
        assert _dump(old) == _dump(_returned(name)), name
    # The comparison is not vacuous: two different readers' expressions differ.
    assert _dump(_returned("primed_only")) != _dump(_returned("hinted_or_primed"))


def test_the_moved_function_kernel_is_the_readers_function():
    old = ast.parse(BASE_SOURCES["fsrs_cap_value"]).body[0]
    new = _kernel("fsrs_cap_value")
    assert [arg.arg for arg in old.args.args] == [arg.arg for arg in new.args.args]
    assert [_dump(statement) for statement in _body(old)] == [_dump(statement) for statement in _body(new)]


# -- the grader sees none of it -----------------------------------------------------------------------------------

GRADER_MODULES = ("ai_contracts", "blind_grading", "grading", "grading_support", "grading_admission",
                  "grade_resolution", "grader_calibration", "regrade", "stuck")
FACT_MODULES = {"learnloop.attempts.facts", "learnloop.attempts.fact_predicates"}
FACT_TYPES = ("AttemptFacts", "HelpFact", "QuestionFact", "RevealFact", "FieldCoverage")


def _imports(path: Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
            out.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
    return out


def test_no_grading_module_imports_the_facts_or_their_predicates():
    for name in GRADER_MODULES:
        path = ROOT / "src" / "learnloop" / "attempts" / f"{name}.py"
        assert not (_imports(path) & FACT_MODULES), name


def test_the_grading_contexts_have_no_field_for_the_facts():
    for context in (BlindGradingContext, GradingContext):
        for field in dataclasses.fields(context):
            annotation = str(field.type)
            assert not any(kind in annotation for kind in FACT_TYPES), (context.__name__, field.name)
            assert not any(token in field.name for token in ("facts", "assist", "reveal")), field.name
    parameters = inspect.signature(blind_grading_context).parameters
    assert not any("fact" in name for name in parameters)
