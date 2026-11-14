"""The grade application's pure core, from plain values: no vault on disk, no database, no clock.

``grade_scope`` decides what a grade assessed and its coverage; ``grade_application`` turns that, the learner's prior
state and the other reads (``GradeReads``) into every row the attempt writes. Each case below is one kind of grade
the attempt step applies, built in memory and checked on the application's fields. The bits of each field on a real
vault are pinned by ``tests/test_grade_application_golden.py``; this file pins what the arithmetic decides.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptPriorState,
    AttemptValidationError,
    GradeAttribution,
    GradeInputs,
    GradeReads,
    ResolvedGrade,
    grade_application,
    grade_scope,
)
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import PracticeItemState
from learnloop.learner.facet_diagnostics import BreadthReads, LoCoverageReads
from learnloop.learner.mastery import initial_mastery_state
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS
from learnloop.vault.models import ErrorType, HintPolicy, LearningObject, PracticeItem, Rubric, RubricCriterion

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-06-01T12:00:00Z"
STAMP = "2026-05-01T00:00:00Z"
FACETS = ("setup_facet", "result_facet")
CONFIG = LearnLoopConfig(algorithms={"algorithm_version": LATEST_ALGORITHM_VERSION})
RUBRIC = Rubric(criteria=[
    RubricCriterion(id="setup", points=2, description="Sets up A^T A."),
    RubricCriterion(id="result", points=2, description="States U Sigma V^T."),
])
ITEM = PracticeItem(
    id="pi_core", learning_object_id="lo_core", practice_mode="constructed_response",
    attempt_types_allowed=["independent_attempt", "hinted_attempt"],
    evidence_facets=list(FACETS), evidence_weights={"setup_facet": 0.5, "result_facet": 0.5},
    criterion_facet_weights={"setup": {"setup_facet": 1.0}, "result": {"result_facet": 1.0}},
    prompt="Decompose A.", expected_answer="U Sigma V^T", grading_rubric=RUBRIC, surface_family="matrix_symbolic",
    hint_policy=HintPolicy(max_useful_hints=1, fsrs_rating_cap_by_hint={1: "hard"},
                           mastery_alpha_dampening_by_hint={1: 0.6}, coverage_surface_dampening_by_hint={1: 0.8}),
    created_at=STAMP, updated_at=STAMP,
)
LO = LearningObject(
    id="lo_core", title="SVD", subjects=["linear-algebra"], concept="svd", knowledge_type="procedure",
    summary="The singular value decomposition.", created_at=STAMP, updated_at=STAMP,
)
ERROR_TYPES = {
    "conceptual_slip": ErrorType(id="conceptual_slip", title="Slip", severity_default=0.4, created_at=STAMP,
                                 updated_at=STAMP),
    "retrieval_failure": ErrorType(id="retrieval_failure", title="Not recalled", severity_default=0.5,
                                   created_at=STAMP, updated_at=STAMP),
}


def _grade(points, *, attributions=(), evidence_rows=None, confidence=1.0) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=int(sum(points.values())),
        criterion_points=dict(points),
        evidence_rows=[
            {"id": f"ge_{cid}", "criterion_id": cid, "points_awarded": float(value), "evidence": "test"}
            for cid, value in points.items()
        ] if evidence_rows is None else evidence_rows,
        error_attributions=list(attributions),
        grader_confidence=confidence,
        confidence=3,
        manual_review_reason=None,
    )


def _inputs(points=None, *, draft=None, grade=None, **fields) -> GradeInputs:
    return GradeInputs(
        attempt_id="att_core",
        draft=AttemptDraft(**{"practice_item_id": ITEM.id, "learner_answer_md": "A^T A, then U Sigma V^T", **(draft or {})}),
        item=ITEM,
        learning_object=LO,
        rubric=RUBRIC,
        grade=grade or _grade(points if points is not None else {"setup": 2, "result": 2}),
        subject="linear-algebra",
        observed_at=NOW,
        now_iso=NOW_ISO,
        config=CONFIG,
        facet_aliases={},
        error_types=ERROR_TYPES,
        facet_uncertainty_on=False,
        **fields,
    )


def _prior(*, recent=(), item_state=None) -> AttemptPriorState:
    return AttemptPriorState(
        mastery=initial_mastery_state(LO.id, LATEST_ALGORITHM_VERSION, STAMP),
        active_errors=[],
        practice_item_state=item_state,
        practice_item_quality_state=None,
        recent_learning_object_attempts=list(recent),
        recent_practice_item_attempts=[row for row in recent if row["practice_item_id"] == ITEM.id],
        aggregate_facet_recall={facet: None for facet in FACETS},
        item_facet_recall={facet: None for facet in FACETS},
        facet_uncertainty={facet: None for facet in FACETS},
    )


def _apply(inputs: GradeInputs, *, prior=None, ids=None, grading_evidence=None):
    scope = grade_scope(inputs)
    kept = 0 if scope.held else len(inputs.grade.error_attributions)
    reads = GradeReads(
        prior_state=prior or _prior(),
        interpretation_variance=0.0,
        recorded_mass=None,
        lo_coverage=LoCoverageReads(required=set(FACETS), open_uncertainties={}),
        breadth=BreadthReads(frontier=set(), authored=False, required=set(FACETS), recall_states=[]),
        fsrs_weights=FSRS6_DEFAULT_WEIGHTS,
        reference_status="not_applicable",
        error_event_ids=list(ids) if ids is not None else [f"err_{index}" for index in range(kept)],
        grading_evidence=grading_evidence,
    )
    return scope, grade_application(inputs, scope, reads)


def _slip(**fields) -> GradeAttribution:
    return GradeAttribution(error_type="conceptual_slip", severity=0.6, evidence="V not transposed", **fields)


# -- one case per kind of grade ----------------------------------------------------------------------------------


def test_an_independent_full_credit_answer_raises_mastery_and_schedules_the_item():
    scope, application = _apply(_inputs())

    assert scope.correctness == 1.0 and not scope.held and not scope.nothing_assessed
    assert set(scope.coverage.covered_facets) == set(FACETS)
    record = application.attempt_record
    assert (record["attempt_type"], record["correctness"], record["error_type"]) == ("independent_attempt", 1.0, None)
    assert record["created_at"] == NOW_ISO and record["subject"] == "linear-algebra"
    assert application.mastery_state.logit_mean > 0.0
    assert application.mastery_state.evidence_count == 1
    assert application.result.fsrs_rating in {"good", "easy"}
    assert application.practice_item_state.due_at > NOW_ISO
    assert application.practice_item_state.stability is not None
    assert application.error_events == [] and application.quality_state is not None
    assert application.attempt_debug_payload["facet_outcomes"] == {"setup_facet": 1.0, "result_facet": 1.0}
    assert application.surprise_record["attempt_id"] == "att_core"
    assert application.fsrs_review["skipped"] is None


def test_a_hinted_answer_counts_for_less_than_an_independent_one():
    _scope, independent = _apply(_inputs())
    _scope, hinted = _apply(_inputs(draft={"attempt_type": "hinted_attempt", "hints_used": 1}))

    assert hinted.attempt_record["hints_used"] == 1
    assert hinted.result.fsrs_rating == "hard"
    assert hinted.attempt_debug_payload["reliability_trace"]["hint_mastery_factor"] == 0.6
    assert hinted.attempt_debug_payload["coverage_trace"]["coverage_modifiers"]["hint_surface_factor"] == 0.8
    assert 0.0 < hinted.mastery_state.logit_mean < independent.mastery_state.logit_mean


def test_a_primed_success_shifts_the_items_difficulty_and_barely_moves_mastery():
    _scope, independent = _apply(_inputs())
    _scope, primed = _apply(_inputs(draft={"primed": True}))

    debug = primed.attempt_debug_payload
    assert primed.attempt_record["primed"] is True and debug["primed"] is True
    assert debug["priming_b_offset"] == CONFIG.mastery.irt.priming_b_offset
    assert independent.attempt_debug_payload["priming_b_offset"] is None
    assert 0.0 <= primed.mastery_state.logit_mean < independent.mastery_state.logit_mean


def test_i_dont_know_is_a_failure_with_its_error_event():
    attribution = GradeAttribution(error_type="retrieval_failure", severity=0.5)
    scope, application = _apply(_inputs(
        draft={"attempt_type": "dont_know", "learner_answer_md": ""},
        grade=_grade({"setup": 0, "result": 0}, attributions=[attribution]),
    ))

    assert scope.correctness == 0.0
    assert application.result.fsrs_rating == "again"
    assert application.mastery_state.logit_mean < 0.0
    [event] = application.error_events
    assert (event["id"], event["error_type"], event["status"]) == ("err_0", "retrieval_failure", "active")
    assert 0.0 < event["severity"] <= 1.0
    assert application.attempt_record["error_type"] == "retrieval_failure"
    assert application.result.error_event_ids == ["err_0"]


def test_a_stuck_answer_is_recorded_as_stuck_and_still_counts():
    scope, application = _apply(_inputs(
        {"setup": 1, "result": 0}, draft={"declared_stuck": True, "learner_answer_md": "A^T A, then stopped."},
    ))

    assert application.attempt_record["declared_stuck"] is True
    assert scope.correctness == 0.25
    modifiers = application.attempt_debug_payload["coverage_trace"]["coverage_modifiers"]
    assert "response_engagement_factor" in modifiers
    assert application.result.mastery_trace is not None


def test_a_held_grade_is_no_evidence_and_leaves_the_schedule_as_it_was():
    due = (NOW + timedelta(days=3)).isoformat().replace("+00:00", "Z")
    previous = PracticeItemState(
        practice_item_id=ITEM.id, difficulty=5.0, stability=4.0, retrievability=0.9, due_at=due, active=True,
        content_hash="h", last_attempt_at=STAMP, updated_at=STAMP,
    )
    prior = _prior(item_state=previous)
    scope, application = _apply(
        _inputs({"setup": 0, "result": 0}, grade=_grade({"setup": 0, "result": 0}, attributions=[_slip()]),
                unassessed_criterion_ids=("setup", "result"), grade_held_for_review=True),
        prior=prior,
    )

    assert scope.held and scope.nothing_assessed
    assert application.grade_held is True
    assert application.mastery_state == prior.mastery and application.result.mastery_trace is None
    assert application.error_events == [] and application.quality_state is None
    assert application.practice_item_state.due_at == due
    assert application.fsrs_review["skipped"] == "held"
    assert application.result.surprise_direction == "none"
    assert application.attempt_debug_payload["grade_held_for_review"] is True


def test_an_unassessed_criterion_leaves_its_facet_out_of_the_evidence():
    scope, application = _apply(_inputs({"setup": 2, "result": 0}, unassessed_criterion_ids=("result",)))

    assert scope.unassessed == frozenset({"result"}) and not scope.nothing_assessed
    assert scope.criterion_points == {"setup": 2}
    assert application.attempt_debug_payload["unassessed_criteria"] == ["result"]
    assert set(application.attempt_debug_payload["covered_facets"]) == {"setup_facet"}


def test_the_firewall_strips_an_attribution_aimed_at_a_passed_criterion():
    grade = _grade({"setup": 2, "result": 0}, attributions=[
        _slip(target_criterion_ids=["setup"], resolution_status="resolved"),
        _slip(target_criterion_ids=["result"], resolution_status="resolved"),
    ])
    _scope, application = _apply(_inputs(grade=grade))

    events = application.attempt_debug_payload["causal_attribution"]["firewall_events"]
    assert [(event["kind"], event["target"]) for event in events] == [("passed_criterion_write_blocked", "setup")]
    assert [event["repair_plan"].get("target_criterion_ids") for event in application.error_events] == [
        None, ["result"],
    ]


def test_a_replayed_regrade_reads_the_stored_evidence_rows_and_keeps_its_event_ids():
    """Replay passes no evidence rows on the grade: the uncertainty layer reads the attempt's stored rows, and the
    error events keep the ids they were first written under."""

    stored = [{"id": "ge_stored", "criterion_id": "result", "points_awarded": 1.0, "evidence": "regraded"}]
    grade = _grade({"setup": 2, "result": 1}, attributions=[_slip(target_criterion_ids=["result"])], evidence_rows=[])
    _scope, application = _apply(_inputs(grade=grade), ids=["err_first_written"], grading_evidence=stored)

    assert application.evidence_rows == []
    assert application.attempt_record["correctness"] == 0.75
    assert [event["id"] for event in application.error_events] == ["err_first_written"]


def test_an_event_id_count_that_drifts_from_the_kept_attributions_fails_loudly():
    with pytest.raises(ValueError):
        _apply(_inputs(grade=_grade({"setup": 2, "result": 0}, attributions=[_slip()])), ids=[])


def test_an_adjudicated_correction_replays_at_the_corrected_points():
    """An adjudication lands as a new evidence revision; replay reads its points as the grade."""

    _scope, original = _apply(_inputs({"setup": 2, "result": 2}))
    _scope, corrected = _apply(_inputs(grade=_grade({"setup": 1, "result": 1}, evidence_rows=[])),
                               grading_evidence=[])

    assert corrected.attempt_record["correctness"] == 0.5
    assert corrected.mastery_state.logit_mean < original.mastery_state.logit_mean


def test_a_grade_whose_contract_is_unrecorded_keeps_its_recorded_correctness_and_is_held():
    scope, application = _apply(_inputs(grade_contract_unrecorded=True, unrecorded_correctness=0.5))

    assert scope.correctness == 0.5 and scope.held and scope.nothing_assessed
    assert application.grade_contract_unrecorded is True
    with pytest.raises(AttemptValidationError):
        grade_scope(_inputs(grade_contract_unrecorded=True, unrecorded_correctness=1.5))


def test_a_repeat_on_the_same_surface_group_is_discounted():
    earlier = (NOW - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    recent = [{
        "id": "att_earlier", "practice_item_id": ITEM.id, "learning_object_id": LO.id,
        "attempt_type": "independent_attempt", "correctness": 1.0, "evidence_facets": list(FACETS),
        "created_at": earlier, "error_type": None, "hints_used": 0, "primed": False,
    }]
    _scope, first = _apply(_inputs())
    _scope, repeat = _apply(_inputs(), prior=_prior(recent=recent))

    assert first.attempt_debug_payload["familiarity_trace"]["independent_evidence_discount"] == 1.0
    assert repeat.attempt_debug_payload["familiarity_trace"]["independent_evidence_discount"] < 1.0
    assert repeat.mastery_state.logit_mean < first.mastery_state.logit_mean


# -- the core is pure ---------------------------------------------------------------------------------------------


def test_the_core_reads_no_database_clock_or_id_stream(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("the core reached the outside world")

    from learnloop.attempts import attempts as attempts_module
    from learnloop.clock import SystemClock

    for name in ("connect", "new_ulid", "utc_now_iso", "load_attempt_prior_state", "lesson_check_mass",
                 "resolve_fsrs_weights", "read_lo_coverage", "read_breadth", "_attempt_reference_status",
                 "_interpretation_variance", "_resolve_attempt_target"):
        monkeypatch.setattr(attempts_module, name, refuse)
    monkeypatch.setattr(SystemClock, "now", refuse)
    grade = _grade({"setup": 2, "result": 0}, attributions=[_slip(target_criterion_ids=["result"])])
    first = _apply(_inputs(grade=grade))
    second = _apply(_inputs(grade=grade))

    assert first == second


def test_the_core_leaves_its_inputs_as_they_were():
    inputs, prior = _inputs(grade=_grade({"setup": 2, "result": 0}, attributions=[_slip()])), _prior()
    before = (repr(inputs), repr(prior))
    _apply(inputs, prior=prior)

    assert (repr(inputs), repr(prior)) == before
