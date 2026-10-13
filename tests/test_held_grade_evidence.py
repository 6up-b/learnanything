"""A grade held for review is no evidence anywhere (held-grade-evidence).

A proof grade the route check held for review (mvp-0.17, re-review F9:
nothing assessed and nothing validated) is the grader's own, provisional
score. One predicate decides it (``outcome_contract.grade_is_held``: the
latest blind record holds it AND nothing in the attempt's current evidence is
assessed), evaluated in flight by the attempt step and over the ledger by
``learnloop.held_grades``; every reader of an attempt's score, correctness,
success or failure routes through one of the two.

The fail-first tests below pin the eleven defects an independent Codex
verification found (job 20261013-051715-m5ErbP); the guard at the end fails if
a held grade's score reaches any listed reader. Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
    calculate_rubric_score,
    unverified_attribution_json,
)
from learnloop.attempts.blind_grading import BlindErrorAttribution
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.proof_check import (
    PROOF_CHECK_VERSION,
    PROOF_ROUTE_REVIEW_REASON,
    apply_proof_route_gate,
)
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.jobs import diagnosis_status
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW, grade_held_for_review
from learnloop.substrate.canonical_projection import (
    UNASSESSED_INTERPRETATION,
    UNVERIFIED_INTERPRETATION_KEY,
    held_for_review_attempts,
    pfc_assessments,
    unassessed_evidence_row,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.split_live_helpers import ReadyRuntime, drain_jobs, split_vault, submit
from tests.test_proof_route_check import (  # noqa: F401 - ``checker`` is a fixture
    ALTERNATIVE,
    ANSWER,
    CLOCK,
    ITEM,
    RUBRIC,
    VERSION,
    CheckerFake,
    DivergentUnlocatedGrader,
    _check,
    _first_scheduled_attempt,
    _proposal,
    _schedule,
    _support,
    checker,
)

#: ``outcome_contract.HOLD_KEPT_FROM_KEY`` (spelled out so this module imports
#: on the commit before the fix, where the fail-first run read it).
HOLD_KEPT_FROM_KEY = "hold_kept_from"


def held_attempt_ids(repository, attempt_ids=None) -> frozenset[str]:
    """The ledger's held set (``learnloop.held_grades``), through the name the
    merge composed (``canonical_projection.held_for_review_attempts``)."""

    with repository.connection() as connection:
        return held_for_review_attempts(connection, attempt_ids)


def attempt_grade_held(repository, attempt_id) -> bool:
    return attempt_id in held_attempt_ids(repository, (attempt_id,))


#: Checker verdicts that hold a divergent, unlocated grade (re-review F9).
HOLDING = {"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}
#: Checker verdicts that validate the route (release).
VALIDATING = {"setup": {"verdict": "established"}, "result": {"verdict": "established"}}


def _iso(when) -> str:
    return when.isoformat().replace("+00:00", "Z")


def _held_support(rubric) -> dict:
    every = sorted(criterion.id for criterion in rubric.criteria)
    return {
        "proof_route_check": {
            "status": "checked", "applied": True, "held_for_review": True,
            "version": PROOF_CHECK_VERSION, "unverified_criterion_ids": every,
            "unlocated_criterion_ids": every,
        },
        "unverified_criterion_ids": every,
        "valid_alternative_gate_applied": True,
        "valid_alternative_gate": {"final_answer": False, "proof_route": True},
        "assessed_shortfall": False,
        UNVERIFIED_INTERPRETATION_KEY: UNASSESSED_INTERPRETATION,
    }


def _held_apply(
    vault, repository, item_id, points, *, attempt_id, when, attempt_type="independent_attempt",
    presentation_id=None, answer_confidence=None, record=True, error_attributions=(),
):
    """A held grade through the shared attempt step, as the live door hands it
    (every criterion unassessed, the grader's own score, ``grade_held_for_review``),
    then its blind record (written after the step, as the live door does)."""

    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    every = tuple(sorted(criterion.id for criterion in rubric.criteria))
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="a route of my own",
                attempt_type=attempt_type, probe_presentation_id=presentation_id,
                answer_confidence=answer_confidence,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, dict(points), []),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid,
                        "points_awarded": float(value), "evidence": "grader", "notes": None,
                        "local_grader_id": "test", "grader_tier": 3, "created_at": _iso(when),
                        "attribution_json": unverified_attribution_json(),
                    }
                    for cid, value in points.items()
                ],
                error_attributions=list(error_attributions),
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=PROOF_ROUTE_REVIEW_REASON,
                feedback_md="held",
            ),
            grading_source="ai",
            unverified_criterion_ids=every,
            grade_held_for_review=True,
        ),
        clock=FrozenClock(when),
    )
    if record:
        repository.insert_blind_grade_record(
            attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="blind-test",
            output_schema_version="BlindGradingProposal", context_hash=f"ctx-{attempt_id}",
            record={
                "practice_item_id": item_id, "rubric_score": result.rubric_score,
                "max_points": rubric.max_points,
                "criteria": [{"criterion_id": cid, "points_awarded": value} for cid, value in points.items()],
                "error_attributions": [], "fatal_errors": [],
                "grading_support": _held_support(rubric),
            },
            clock=FrozenClock(when),
        )
    return result


def _graded_apply(
    vault, repository, item_id, points, *, attempt_id, when, answer_confidence=None, error_attributions=(),
):
    """An ordinary (assessed) model grade through the shared attempt step."""

    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="an answer",
                attempt_type="independent_attempt", answer_confidence=answer_confidence,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=calculate_rubric_score(rubric, dict(points), []),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid,
                        "points_awarded": float(value), "evidence": "grader", "notes": None,
                        "local_grader_id": "test", "grader_tier": 3, "created_at": _iso(when),
                    }
                    for cid, value in points.items()
                ],
                error_attributions=list(error_attributions),
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
                feedback_md="graded",
            ),
            grading_source="ai",
        ),
        clock=FrozenClock(when),
    )


T = CLOCK.now()


# -- THE predicate ---------------------------------------------------------------------------


def test_the_predicate_is_the_record_and_the_current_evidence():
    from learnloop import held_grades
    from learnloop.outcome_contract import grade_is_held
    from learnloop.substrate import canonical_projection

    # One predicate: the merge's name is the leaf's function.
    assert canonical_projection.held_for_review_attempts is held_grades.held_for_review_attempts
    held = {"proof_route_check": {"status": "checked", "held_for_review": True, "version": PROOF_CHECK_VERSION}}
    assert grade_held_for_review(held)
    # A failed regrade check keeps the hold it replaced (F2), named.
    kept = {"proof_route_check": {"status": "unavailable", "held_for_review": True,
                                  "version": PROOF_CHECK_VERSION, HOLD_KEPT_FROM_KEY: "bgr_1"}}
    assert grade_held_for_review(kept)
    assert not grade_held_for_review({"proof_route_check": {"status": "unavailable", "held_for_review": True}})
    assert grade_is_held(record_held=True, anything_assessed=False)
    assert not grade_is_held(record_held=True, anything_assessed=True)
    assert not grade_is_held(record_held=False, anything_assessed=False)


# -- F1: a blank criterion id ------------------------------------------------------------------


def _blank_attribution(**update):
    values = {
        "error_type": "conceptual_slip", "evidence": "the route does not prove the claim",
        "validity_scope": "valid_measurement", "target_criterion_ids": [""],
    }
    values.update(update)
    return BlindErrorAttribution(**values)


@pytest.mark.parametrize(
    "attribution",
    [
        {"target_criterion_ids": [""]},
        {"target_criterion_ids": ["   "]},
        {"target_criterion_ids": ["no_such_criterion"]},
    ],
    ids=["blank", "whitespace", "unknown"],
)
def test_f1_a_blank_or_unknown_criterion_id_names_no_criterion(attribution):
    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}, [_blank_attribution(**attribution)]), rubric=RUBRIC,
        learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "established"}, result={"verdict": "cannot_tell"}),
        final_answer_status="undecidable", divergent_route=True,
    )
    assert gate.restored == ("setup",) and gate.unlocated == ("result",)
    assert [row.validity_scope for row in gate.proposal.error_attributions] == ["grader_interpretation"]
    assert gate.assessed_shortfall is False


class BlankIdGrader(DivergentUnlocatedGrader):
    """``DivergentUnlocatedGrader`` plus an unquoted attribution whose only
    criterion id is blank (the wire model accepts it)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        return result.model_copy(update={"error_attributions": [_blank_attribution()]})


def test_f1_live_a_blank_criterion_id_keeps_no_shortfall_and_queues_no_diagnosis(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "cannot_tell"}}))
    result = submit(vault, repository, BlankIdGrader(), answer=ALTERNATIVE)
    support = _support(repository, result.attempt_id)
    assert support["proof_route_check"]["held_for_review"] is False  # setup was validated
    assert support["assessed_shortfall"] is False
    [stored] = repository.latest_blind_grade_record(result.attempt_id)["record"]["error_attributions"]
    assert stored["validity_scope"] == "grader_interpretation"
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"


def test_f1_the_shortfall_is_recomputed_over_the_validated_grade():
    from learnloop.attempts.proof_check import revalidated_support

    support = {
        "proof_route_check": {"status": "checked", "applied": True, "assessed_shortfall": True},
        "unverified_criterion_ids": ["result"], "assessed_shortfall": True,
        "valid_alternative_gate_applied": True,
    }
    # Validation dropped the only in-force attribution: nothing assessed fell short.
    record = {"criteria": [{"criterion_id": "setup", "points_awarded": 2.0},
                           {"criterion_id": "result", "points_awarded": 0.0}],
              "error_attributions": [], "fatal_errors": []}
    assert revalidated_support(support, record, RUBRIC)["assessed_shortfall"] is False
    kept = {**record, "error_attributions": [{"validity_scope": "valid_measurement"}]}
    assert revalidated_support(support, kept, RUBRIC)["assessed_shortfall"] is True
    # A gate that did not apply is left alone.
    untouched = {**support, "proof_route_check": {"status": "unavailable", "applied": False}}
    assert revalidated_support(untouched, record, RUBRIC)["assessed_shortfall"] is True


# -- F2: a failed check never releases a hold ---------------------------------------------------


def _held_live(vault, repository, checker):
    _first_scheduled_attempt(vault, repository, checker)
    checker(CheckerFake(verdicts=HOLDING))
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=T + timedelta(days=3))
    assert attempt_grade_held(repository, held.attempt_id)
    return held


@pytest.mark.parametrize("clarified", [False, True], ids=["regrade", "clarification"])
def test_f2_a_regrade_whose_check_fails_keeps_the_hold(tmp_path, checker, clarified):
    from tests.test_pfc_unassessed_readers import _field_outcomes

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    held = _held_live(vault, repository, checker)
    before = _schedule(repository)
    prior_record = repository.latest_blind_grade_record(held.attempt_id)
    checker(CheckerFake(verdicts=VALIDATING, fail_purposes=("proof_route_check",)))
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(held.attempt_id),
        runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=4)),
        clarification_exchange=(
            {"question_md": "Which V?", "answer_md": "From A^T A.", "criterion_id": "setup",
             "reason": "method_ambiguity"} if clarified else None
        ),
    )
    proof = _support(repository, held.attempt_id)["proof_route_check"]
    assert proof["status"] == "unavailable" and proof["held_for_review"] is True
    assert proof[HOLD_KEPT_FROM_KEY] == prior_record["id"]
    assert attempt_grade_held(repository, held.attempt_id)
    attempt = repository.fetch_practice_attempt(held.attempt_id)
    assert attempt["rubric_score"] == 0 and attempt["manual_review_reason"] == PROOF_ROUTE_REVIEW_REASON
    rows = repository.fetch_grading_evidence(held.attempt_id)
    assert rows and all(unassessed_evidence_row(row.attribution_json) for row in rows)
    # Nothing validated the regrade: the schedule, the facets and the
    # diagnosis queue are as they were.
    assert _schedule(repository) == before
    assert _field_outcomes(vault, repository, held.attempt_id) == {}
    # The regrade re-queues the diagnosis; the job finds nothing to explain.
    drain_jobs(vault, repository, DivergentUnlocatedGrader(), clock=FrozenClock(T + timedelta(days=4)))
    assert diagnosis_status(repository, held.attempt_id)["status"] == "not_needed"
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _schedule(repository) == before


# -- F3: certification cold probes abstain on a held grade ---------------------------------------


@pytest.mark.parametrize("points", [0.0, 4.0], ids=["held_zero", "held_full"])
def test_f3_a_held_cold_probe_abstains_from_certification_validation(tmp_path, points):
    from learnloop.attempts.coldness_receipt import record_certification_administration_snapshot
    from learnloop.goals.certification_cold_probe import (
        false_certification_rate,
        resolve_cold_probe_parameters,
        schedule_certification_cold_probes,
    )
    from tests.helpers import NOW
    from tests.test_certification_cold_probe import HELD_OUT_ITEM, _certify, _tasks

    _paths, vault, repository, _certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    task = _tasks(repository)[0]
    parameters = resolve_cold_probe_parameters(repository)
    due = NOW + timedelta(days=parameters.horizon_days)
    record_certification_administration_snapshot(vault, repository, task=task, clock=FrozenClock(due))
    result = _held_apply(vault, repository, HELD_OUT_ITEM, {"correctness": points},
                         attempt_id="att_held_probe", when=due)
    outcome = repository.certification_cold_probe_outcome_for_attempt(result.attempt_id)
    assert outcome["verdict"] == "indeterminate"
    assert outcome["indeterminate_reason"] == "grade_unavailable"
    assert outcome["success"] is None and outcome["correctness"] is None
    rate = false_certification_rate(repository)
    assert rate.denominator == 0 and rate.rate is None and not rate.available


# -- F4: a validating regrade supersedes the held rows -------------------------------------------


def test_f4_a_validating_regrade_leaves_no_stale_unassessed_row(tmp_path, checker):
    from tests.test_pfc_unassessed_readers import _field_outcomes

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    held = _held_live(vault, repository, checker)
    checker(CheckerFake(verdicts=VALIDATING))
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(held.attempt_id),
        runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=5)),
    )
    rows = repository.fetch_grading_evidence(held.attempt_id)
    assert sorted(row.criterion_id for row in rows) == ["result", "setup"]
    assert not any(unassessed_evidence_row(row.attribution_json) for row in rows)
    assert not attempt_grade_held(repository, held.attempt_id)
    with repository.connection() as connection:
        assert pfc_assessments(connection, [held.attempt_id]) == {}
    # Every projection reads the released grade the same way, replay included.
    outcomes = _field_outcomes(vault, repository, held.attempt_id)
    assert outcomes and set(outcomes.values()) == {1.0}
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _field_outcomes(vault, repository, held.attempt_id) == outcomes
    with repository.connection() as connection:
        assert pfc_assessments(connection, [held.attempt_id]) == {}
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 4


# -- F5: an adjudication releases the post-attempt suppression -----------------------------------


def test_f5_an_adjudication_releases_the_follow_up_suppression(tmp_path, checker):
    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
    from learnloop.attempts.post_attempt import run_post_attempt_pipeline

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository, checker)
    checker(CheckerFake(verdicts=HOLDING))
    when = T + timedelta(days=3)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=when, pipeline=False)
    assert attempt_grade_held(repository, held.attempt_id)
    revision = append_adjudication_evidence_revision(
        repository, attempt_id=held.attempt_id, resolved_fraction=1.0, adjudication_id="adj-f5",
        adjudicator_source="human_owner", rationale="valid route", vault=vault,
        clock=FrozenClock(when + timedelta(hours=1)),
    )
    assert revision["status"] == "revised"
    assert not attempt_grade_held(repository, held.attempt_id)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    outcome = run_post_attempt_pipeline(vault, repository, result=held, clock=FrozenClock(when))
    assert GRADE_HELD_FOR_REVIEW not in outcome.notes


# -- F6: datasets ---------------------------------------------------------------------------------


def test_f6_the_dataset_exports_no_held_score_as_observed(tmp_path):
    from learnloop.substrate.dataset import outcome_records

    paths, vault, repository = split_vault(tmp_path, version=VERSION)
    source = _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0},
                           attempt_id="att_source", when=T)
    held = _held_apply(vault, repository, ITEM, {"setup": 0.0, "result": 0.0},
                       attempt_id="att_held", when=T + timedelta(days=3))
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO coldness_receipts(id, lane, stage, source_attempt_id, cold_attempt_id, "
            "dimensions_json, derived_json, telemetry_coverage_json, receipt_version, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("cr_held", "repair_cold_retry", "final", source.attempt_id, held.attempt_id, "{}",
             json.dumps({"qualifies_as_cold_retrieval": True, "outcome": "indeterminate"}), "{}",
             "test", _iso(T + timedelta(days=3))),
        )
        connection.commit()
    connection = connect(paths.sqlite_path)
    try:
        records = {row["source_attempt_id"]: row for row in outcome_records(connection)}
    finally:
        connection.close()
    r_next = records[source.attempt_id]["R_next"]
    assert r_next["outcome_attempt_id"] == held.attempt_id
    assert r_next["status"] == GRADE_HELD_FOR_REVIEW and r_next["value"] is None
    assert GRADE_HELD_FOR_REVIEW in r_next["retention_exclusions"]
    [cold] = [row for row in records[source.attempt_id]["R_cold"] if row.get("receipt_id") == "cr_held"]
    assert cold["status"] == GRADE_HELD_FOR_REVIEW and cold["value"] is None


# -- F7: exam calibration ------------------------------------------------------------------------


def test_f7_exam_calibration_reads_no_held_outcome(tmp_path, monkeypatch):
    from learnloop.goals.exam_calibration import calibration_report

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    held = _held_apply(vault, repository, ITEM, {"setup": 0.0, "result": 0.0},
                       attempt_id="att_held", when=T, answer_confidence=4)
    monkeypatch.setattr(repository, "all_exam_predictions", lambda: [{
        "session_id": "s1", "practice_item_id": ITEM, "predicted_correctness": 0.8,
        "facet_projection": {"compute": {"projected_recall": 0.9}},
    }])
    monkeypatch.setattr(repository, "exam_answers", lambda session_id: [
        {"practice_item_id": ITEM, "attempt_id": held.attempt_id},
    ])
    monkeypatch.setattr(repository, "calibration_duel_pairs", lambda: [{
        "attempt_id": held.attempt_id, "answer_confidence": 4, "correctness": 0.0,
        "model_predicted_correctness": 0.7,
    }])
    report = calibration_report(vault, repository)
    assert report["items"]["n"] == 0
    assert report["facets"]["n"] == 0 and report["facets"]["by_facet"] == {}
    assert report["duel"]["n"] == 0
    # The held answer is not a graded attempt in the confidence denominator.
    graded = repository.answer_confidence_presence()["graded_attempts"]
    assert report["duel"]["confidence_eligible"] == graded - 1


# -- F8: the FSRS fitter --------------------------------------------------------------------------


def test_f8_the_fsrs_fitter_never_fits_a_review_that_never_happened(tmp_path):
    from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS
    from learnloop.scheduling.fsrs_fitting import review_log_loss
    from learnloop.scheduling.review_log import reconstruct_review_log, review_log_from_attempts

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_ok", when=T)
    _held_apply(vault, repository, ITEM, {"setup": 0.0, "result": 0.0},
                attempt_id="att_held", when=T + timedelta(days=3))
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0},
                  attempt_id="att_after", when=T + timedelta(days=9))
    log = reconstruct_review_log(vault, repository)
    [observation] = [o for o in log.sequences[ITEM] if o.attempt_id == "att_held"]
    assert observation.applies_review is False
    # The held provisional score is invisible to the fitter.
    rows = [dict(row) for row in repository.list_all_attempts()]
    loss = []
    for score in (0, 4):
        changed = [{**row, "rubric_score": score} if row["id"] == "att_held" else row for row in rows]
        replayed = review_log_from_attempts(vault, changed, held_attempt_ids={"att_held"})
        loss.append(review_log_loss(replayed, FSRS6_DEFAULT_WEIGHTS, min_elapsed_days=0.0))
    assert loss[0] == loss[1]
    assert review_log_loss(log, FSRS6_DEFAULT_WEIGHTS, min_elapsed_days=0.0) == loss[0]


# -- F9, F10: the failure streak and item quality ---------------------------------------------------


def test_f9_f10_held_grades_build_no_failure_streak_and_move_no_item_quality(tmp_path):
    from learnloop.diagnosis.followups import current_same_item_failure_streak

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_ok", when=T)
    quality = repository.practice_item_quality_state(ITEM)
    assert current_same_item_failure_streak(repository, ITEM) == 0
    for index in (1, 2):
        _held_apply(vault, repository, ITEM, {"setup": 0.0, "result": 0.0},
                    attempt_id=f"att_held_{index}", when=T + timedelta(days=index))
    assert current_same_item_failure_streak(repository, ITEM) == 0
    assert repository.practice_item_quality_state(ITEM) == quality
    # The same through replay.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert repository.practice_item_quality_state(ITEM).evidence_count == quality.evidence_count
    assert repository.practice_item_quality_state(ITEM).bad_item_suspicion == quality.bad_item_suspicion


# -- F11: probe observations ---------------------------------------------------------------------


def test_f11_a_held_probe_answer_moves_no_episode_posterior(tmp_path):
    from learnloop.diagnosis.probe_episodes import enter_episode, episode_posterior
    from tests.test_probe_episodes import CLOCK as PROBE_CLOCK
    from tests.test_probe_episodes import ITEM_ID, LO_ID, _commit, _setup

    _root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=PROBE_CLOCK)
    prior = episode_posterior(loaded, repository, episode).posterior
    presentation = _commit(loaded, repository, episode)
    probe = _held_apply(loaded, repository, ITEM_ID, {"correctness": 0.0}, attempt_id="att_held_probe",
                        when=PROBE_CLOCK.now(), attempt_type="diagnostic_probe",
                        presentation_id=presentation.id)
    observation = repository.probe_observation_for_attempt(probe.attempt_id)
    assert observation is not None  # the presentation was answered
    assert observation.updates_belief is False and observation.eligible_for_completion is False
    assert observation.realized_information_gain == 0.0
    assert observation.posterior_after == observation.posterior_before
    assert (observation.grader_channel or {}).get("observed_outcome") is None
    after = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert after.posterior == prior and after.qualifying_observations == 0
    # An incidental held answer (no presentation) moves nothing either.
    _held_apply(loaded, repository, ITEM_ID, {"correctness": 0.0}, attempt_id="att_held_incidental",
                when=PROBE_CLOCK.now() + timedelta(minutes=5))
    assert episode_posterior(loaded, repository, repository.probe_episode(episode.id)).posterior == prior


# -- the guard: no listed reader reads a held grade's score -----------------------------------------


def _readers():
    """Every reader of attempt scores the guard compares, by name. Each maps
    (vault, repository, paths) to a plain value; the guard requires it to be
    the same whatever provisional score the held grade carries."""

    from learnloop.diagnosis.followups import current_same_item_failure_streak
    from learnloop.diagnosis.scoreboard import cold_success_trajectories
    from learnloop.goals.exam_calibration import calibration_report
    from learnloop.learner.calibration import difficulty_miscalibration_flags
    from learnloop.placement.state import load_answers
    from learnloop.scheduling.evaluation import _coverage_section, _retention_section
    from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS
    from learnloop.scheduling.fsrs_fitting import review_log_loss
    from learnloop.scheduling.review_log import reconstruct_review_log
    from learnloop.substrate.data_quality import data_quality_report
    from learnloop.substrate.dataset import outcome_records
    from learnloop.tutor.question_signal import _base_failure_rate
    from tests.test_pfc_unassessed_readers import _field_outcomes
    from tests.test_proof_route_check import _projection

    def schedule(vault, repository, paths):
        state = repository.practice_item_state(ITEM)
        return (state.difficulty, state.stability, state.due_at)

    def mastery(vault, repository, paths):
        state = repository.mastery_state("lo_svd_compute")
        return (round(state.logit_mean, 12), round(state.logit_variance, 12))

    def item_quality(vault, repository, paths):
        state = repository.practice_item_quality_state(ITEM)
        return (state.bad_item_suspicion, state.evidence_count, tuple(state.suspicion_reasons))

    def failure_streak(vault, repository, paths):
        return current_same_item_failure_streak(repository, ITEM)

    def active_errors(vault, repository, paths):
        return sorted(event.error_type for event in repository.active_errors_by_learning_object("lo_svd_compute"))

    def later_attempt(vault, repository, paths):
        surprise = repository.latest_attempt_surprise("att_after") or {}
        debug = repository.attempt_debug_payload("att_after") or {}
        return (
            surprise.get("surprise_direction"), surprise.get("predictive_surprise"),
            debug.get("bad_item_suspicion"), json.dumps(debug.get("severity_traces"), sort_keys=True),
            json.dumps(debug.get("familiarity_trace"), sort_keys=True),
        )

    def facet_projection(vault, repository, paths):
        return _projection(repository)

    def field(vault, repository, paths):
        return sorted(_field_outcomes(vault, repository, "att_held").items())

    def fsrs_fitter(vault, repository, paths):
        return review_log_loss(reconstruct_review_log(vault, repository), FSRS6_DEFAULT_WEIGHTS, min_elapsed_days=0.0)

    def retention_evaluation(vault, repository, paths):
        section = _retention_section(vault, repository, bins=5)
        return json.dumps(section, sort_keys=True, default=str)

    def prediction_coverage(vault, repository, paths):
        return json.dumps(_coverage_section(repository), sort_keys=True, default=str)

    def dataset(vault, repository, paths):
        connection = connect(paths.sqlite_path)
        try:
            return json.dumps(outcome_records(connection), sort_keys=True, default=str)
        finally:
            connection.close()

    def data_quality(vault, repository, paths):
        return json.dumps(data_quality_report(paths.sqlite_path)["retention_labels"], sort_keys=True)

    def exam_calibration(vault, repository, paths):
        return json.dumps(calibration_report(vault, repository)["duel"], sort_keys=True)

    def item_difficulty(vault, repository, paths):
        return [flag.as_dict() if hasattr(flag, "as_dict") else repr(flag)
                for flag in difficulty_miscalibration_flags(vault, repository, min_attempts=1, threshold=0.0)]

    def placement(vault, repository, paths):
        with repository.connection() as connection:
            answers = load_answers(connection)
        return sorted(
            (answer.attempt_id, answer.unassessed, answer.is_miss, answer.clean_correct)
            for answers_for_lo in answers.values() for answer in answers_for_lo
        )

    def cold_success(vault, repository, paths):
        return sorted(repr(row) for row in cold_success_trajectories(repository))

    def question_signal(vault, repository, paths):
        return _base_failure_rate(repository)

    return {
        "fsrs_schedule": schedule,
        "mastery": mastery,
        "item_quality": item_quality,
        "failure_streak": failure_streak,
        "active_errors": active_errors,
        "later_attempt_surprise_severity_familiarity": later_attempt,
        "facet_projection_certification": facet_projection,
        "learner_field": field,
        "fsrs_fitter": fsrs_fitter,
        "retention_evaluation": retention_evaluation,
        "prediction_coverage": prediction_coverage,
        "dataset_outcomes": dataset,
        "data_quality_report": data_quality,
        "exam_calibration_duel": exam_calibration,
        "item_difficulty_calibration": item_difficulty,
        "placement": placement,
        "cold_success_scoreboard": cold_success,
        "question_signal_base_rate": question_signal,
    }


@pytest.fixture(scope="module")
def held_worlds(tmp_path_factory):
    """Two vaults identical but for the provisional score a held grade carries
    (0/4 with an error claim, 4/4 without), each followed by one ordinary
    failed answer with a located error on the same item: the readers of
    recent failures, streaks, item quality, error severity and familiarity
    all look back across the held grade."""

    base = tmp_path_factory.mktemp("held-guard")
    paths, vault, repository = split_vault(base / "seed", version=VERSION)
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_ok",
                  when=T, answer_confidence=4)
    from learnloop.attempts.attempts import GradeAttribution

    claim = GradeAttribution(
        error_type="conceptual_slip", severity=0.7, evidence="the grader's unlocated claim",
        is_misconception=False, target_evidence_families=["compute"], target_criterion_ids=["result"],
        cause_scope="grader_interpretation",
    )
    located = GradeAttribution(
        error_type="conceptual_slip", severity=0.6, evidence="a located slip",
        is_misconception=False, target_evidence_families=["compute"], target_criterion_ids=["result"],
        cause_scope="learner_state",
    )
    worlds = {}
    for name, points, claims in (
        ("zero", {"setup": 0.0, "result": 0.0}, [claim]),
        ("full", {"setup": 2.0, "result": 2.0}, []),
    ):
        root = base / name
        copy_tree_with_databases(paths.root, root)
        world_vault = load_vault(root)
        world_repository = Repository(root / paths.sqlite_path.relative_to(paths.root))
        _held_apply(world_vault, world_repository, ITEM, points, attempt_id="att_held",
                    when=T + timedelta(days=3), answer_confidence=2, error_attributions=claims)
        _graded_apply(world_vault, world_repository, ITEM, {"setup": 0.0, "result": 0.0},
                      attempt_id="att_after", when=T + timedelta(days=6), answer_confidence=3,
                      error_attributions=[located])
        world_paths = type("Paths", (), {"root": root, "sqlite_path": world_repository.sqlite_path})
        worlds[name] = (world_vault, world_repository, world_paths)
    return worlds


@pytest.mark.parametrize("reader", sorted(_readers()))
def test_guard_no_listed_reader_reads_a_held_grades_score(held_worlds, reader):
    read = _readers()[reader]
    zero, full = (read(*held_worlds[name]) for name in ("zero", "full"))
    assert zero == full, f"{reader} reads the provisional score of a grade held for review"


def test_guard_the_worlds_hold_the_grade(held_worlds):
    for _vault, repository, _paths in held_worlds.values():
        assert held_attempt_ids(repository) == {"att_held"}
        assert repository.fetch_practice_attempt("att_held")["error_type"] is None
        assert repository.error_events_for_attempt("att_held") == []
