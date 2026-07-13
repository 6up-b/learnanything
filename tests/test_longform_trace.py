"""Long-form structured trace tests (spec_probe_eig_redesign.md §8.2, §16 tests 23/24)."""

from __future__ import annotations

from learnloop.services.longform_trace import (
    OUTCOME_CORRECT,
    OUTCOME_INVALID,
    OUTCOME_UNASSESSABLE,
    OUTCOME_UNASSESSED,
    TraceObligation,
    assess_trace,
    classify_trace_outcome,
    obligations_from_bindings,
    outcomes_from_grading_evidence,
)


def _chain(count: int) -> list[TraceObligation]:
    """A strictly dependent chain ob_1 <- ob_2 <- ... <- ob_count."""

    return [
        TraceObligation(
            id=f"ob_{index}",
            criterion_id=f"crit_{index}",
            depends_on=(f"ob_{index - 1}",) if index > 1 else (),
        )
        for index in range(1, count + 1)
    ]


# --- §16 test 23: bounded task evidence mass --------------------------------------


def test_eight_dependent_obligations_cannot_exceed_task_mass():
    obligations = _chain(8)
    outcomes = {obligation.id: OUTCOME_CORRECT for obligation in obligations}
    trace = assess_trace(obligations, outcomes, total_task_evidence_mass=1.0)

    assert trace.assessable_mass <= 1.0 + 1e-9
    assert abs(trace.assessable_mass - 1.0) < 1e-9  # all 8 assessed, splitting one task
    for entry in trace.obligations:
        assert abs(entry.evidence_share - 1.0 / 8) < 1e-9


def test_mass_stays_bounded_with_partial_failure():
    obligations = _chain(8)
    outcomes = {obligation.id: OUTCOME_CORRECT for obligation in obligations}
    outcomes["ob_3"] = OUTCOME_INVALID
    trace = assess_trace(obligations, outcomes, total_task_evidence_mass=1.0)

    # Prefix (2) + the invalid step itself carry mass; dependents carry none.
    assert trace.assessable_mass <= 1.0 + 1e-9
    assert abs(trace.assessable_mass - 3.0 / 8) < 1e-9


# --- §16 test 24: correct prefix + dependent downstream unassessable ----------------


def test_first_error_preserves_prefix_and_marks_dependents_unassessable():
    obligations = _chain(5)
    outcomes = {
        "ob_1": OUTCOME_CORRECT,
        "ob_2": OUTCOME_CORRECT,
        "ob_3": OUTCOME_INVALID,
        "ob_4": OUTCOME_CORRECT,  # graded, but its premise (ob_3) is wrong
        "ob_5": OUTCOME_INVALID,
    }
    trace = assess_trace(obligations, outcomes, total_task_evidence_mass=1.0)

    assert trace.first_invalid_id == "ob_3"
    assert trace.correct_prefix_ids == ("ob_1", "ob_2")
    assert trace.unassessable_ids == ("ob_4", "ob_5")
    by_id = {entry.id: entry for entry in trace.obligations}
    assert by_id["ob_1"].outcome == OUTCOME_CORRECT and by_id["ob_1"].evidence_share > 0
    assert by_id["ob_2"].outcome == OUTCOME_CORRECT and by_id["ob_2"].evidence_share > 0
    assert by_id["ob_3"].outcome == OUTCOME_INVALID and by_id["ob_3"].evidence_share > 0
    assert by_id["ob_4"].outcome == OUTCOME_UNASSESSABLE and by_id["ob_4"].evidence_share == 0.0
    assert by_id["ob_5"].outcome == OUTCOME_UNASSESSABLE and by_id["ob_5"].evidence_share == 0.0


def test_independent_obligation_after_first_error_stays_assessable():
    obligations = [
        TraceObligation(id="ob_a", criterion_id="a"),
        TraceObligation(id="ob_b", criterion_id="b", depends_on=("ob_a",)),
        TraceObligation(id="ob_c", criterion_id="c"),  # independent of ob_a
    ]
    outcomes = {"ob_a": OUTCOME_INVALID, "ob_b": OUTCOME_CORRECT, "ob_c": OUTCOME_CORRECT}
    trace = assess_trace(obligations, outcomes, total_task_evidence_mass=1.0)

    assert trace.first_invalid_id == "ob_a"
    assert trace.unassessable_ids == ("ob_b",)
    by_id = {entry.id: entry for entry in trace.obligations}
    assert by_id["ob_c"].outcome == OUTCOME_CORRECT and by_id["ob_c"].evidence_share > 0
    assert trace.correct_prefix_ids == ()  # nothing correct before the first error


def test_ungraded_obligation_carries_no_evidence():
    obligations = _chain(3)
    outcomes = {"ob_1": OUTCOME_CORRECT}  # ob_2 / ob_3 never graded
    trace = assess_trace(obligations, outcomes, total_task_evidence_mass=1.0)

    by_id = {entry.id: entry for entry in trace.obligations}
    assert by_id["ob_2"].outcome == OUTCOME_UNASSESSED and by_id["ob_2"].evidence_share == 0.0
    assert trace.first_invalid_id is None
    assert abs(trace.assessable_mass - 1.0 / 3) < 1e-9


# --- Grading-evidence bridge and deterministic classifier ---------------------------


class _Evidence:
    def __init__(self, criterion_id: str, points_awarded: float, superseded_at=None):
        self.criterion_id = criterion_id
        self.points_awarded = points_awarded
        self.superseded_at = superseded_at


def test_outcomes_from_grading_evidence_thresholds_and_supersession():
    obligations = [
        TraceObligation(id="ob_1", criterion_id="a"),
        TraceObligation(id="ob_2", criterion_id="b"),
        TraceObligation(id="ob_3", criterion_id="c"),
    ]
    rows = [
        _Evidence("a", 1.0),
        _Evidence("b", 0.0),
        _Evidence("c", 1.0, superseded_at="2026-01-01T00:00:00Z"),
    ]
    outcomes = outcomes_from_grading_evidence(obligations, rows, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert outcomes == {"ob_1": OUTCOME_CORRECT, "ob_2": OUTCOME_INVALID, "ob_3": OUTCOME_UNASSESSED}


def test_classifier_maps_selection_failure_to_wrong_strategy():
    obligations = [
        TraceObligation(id="ob_strategy", criterion_id="strategy_selection", kind="selection"),
        TraceObligation(id="ob_setup", criterion_id="setup", depends_on=("ob_strategy",)),
    ]
    alphabet = (
        "correct_strategy_complete",
        "correct_strategy_execution_slip",
        "wrong_strategy_selected",
        "no_strategy",
        "hedge",
        "unanswered",
    )
    trace = assess_trace(
        obligations,
        {"ob_strategy": OUTCOME_INVALID, "ob_setup": OUTCOME_CORRECT},
        total_task_evidence_mass=1.0,
    )
    assert classify_trace_outcome(trace, obligations, alphabet) == "wrong_strategy_selected"

    complete = assess_trace(
        obligations,
        {"ob_strategy": OUTCOME_CORRECT, "ob_setup": OUTCOME_CORRECT},
        total_task_evidence_mass=1.0,
    )
    assert classify_trace_outcome(complete, obligations, alphabet) == "correct_strategy_complete"

    slip = assess_trace(
        obligations,
        {"ob_strategy": OUTCOME_CORRECT, "ob_setup": OUTCOME_INVALID},
        total_task_evidence_mass=1.0,
    )
    assert classify_trace_outcome(slip, obligations, alphabet) == "correct_strategy_execution_slip"

    empty = assess_trace(obligations, {}, total_task_evidence_mass=1.0)
    assert classify_trace_outcome(empty, obligations, alphabet) == "unanswered"


def test_obligations_from_bindings_roundtrip():
    bindings = {
        "obligations": [
            {"id": "ob_1", "criterion_id": "a", "depends_on": [], "kind": "selection"},
            {"id": "ob_2", "criterion_id": "b", "depends_on": ["ob_1"]},
        ]
    }
    obligations = obligations_from_bindings(bindings)
    assert [o.id for o in obligations] == ["ob_1", "ob_2"]
    assert obligations[0].kind == "selection"
    assert obligations[1].depends_on == ("ob_1",)
    assert obligations_from_bindings({}) == []
    assert obligations_from_bindings(None) == []
