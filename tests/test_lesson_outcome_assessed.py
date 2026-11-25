"""Review round 3 (FR3-4, FR3-17): a lesson outcome is an answer mastery learned from, and a malformed mastery record
is a labelled gap.

FR3-4: a verified alternative with every criterion unassessed has ``correctness`` 1, no review hold and a mastery
record that says it was not applied. From mvp-0.76 it resolves no lesson check: the one outcome reader
(``lesson_weight.qualifying_outcomes``) reads the record, so the fit, the retained-forecast report and the router's
miss-cause learning all advance to the next assessed cold answer. Below the tag every reader is unchanged.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import LESSON_WEIGHT_FACTS_ALGORITHM_VERSION, OUTCOME_FIXES_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.learner import lesson_weight as LW
from learnloop.vault.loader import load_vault

from tests.helpers import set_algorithm_version
from tests.teacher_fakes import build_teacher_vault
from tests.teacher_te1_review_fixes_helpers import _lesson_with_check

T = datetime(2026, 11, 1, 9, tzinfo=UTC)
UNASSESSED_ID, ASSESSED_ID = "01ZZZZZZZZZZZZZZZZZZZZZZZA", "01ZZZZZZZZZZZZZZZZZZZZZZZB"


def _answer(paths, repository, item_id, points, *, attempt_id, when, unverified=()):
    """A cold answer through the shared attempt step; ``unverified``: the criteria the valid-alternative gate left
    unassessed (all of them: correctness 1 from the verified answer, no hold, no mastery update)."""

    from learnloop.attempts.attempts import (
        ApplyAttemptInput,
        AttemptDraft,
        ResolvedGrade,
        apply_attempt,
        calculate_rubric_score,
    )
    from learnloop.attempts.grading import resolved_rubric

    vault = load_vault(paths.root)
    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    criterion = {"correctness": float(points)}
    stamp = when.isoformat().replace("+00:00", "Z")
    return apply_attempt(vault, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt"),
        attempt_id=attempt_id,
        grade=ResolvedGrade(
            rubric_score=calculate_rubric_score(rubric, criterion, []), criterion_points=criterion,
            evidence_rows=[{"id": f"ge_{attempt_id}", "criterion_id": "correctness", "points_awarded": float(points),
                            "evidence": "graded", "notes": None, "local_grader_id": None, "grader_tier": 3,
                            "created_at": stamp}],
            error_attributions=[], grader_confidence=1.0, confidence=3, manual_review_reason=None),
        grading_source="codex", unverified_criterion_ids=tuple(unverified)), clock=FrozenClock(when))


@pytest.mark.parametrize("version, resolver", [
    (OUTCOME_FIXES_ALGORITHM_VERSION, ASSESSED_ID),
    (LESSON_WEIGHT_FACTS_ALGORITHM_VERSION, UNASSESSED_ID),
])
def test_an_unapplied_answer_resolves_no_lesson_check_from_the_tag(tmp_path, version, resolver):
    """FR3-4 (failed before at the tag: the unassessed answer resolved the check as a success in all three readers)."""

    from learnloop.evsi_calibration import forecast_report as FR

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    _lesson_with_check(paths, repository, at=T, retained=0.8)
    _answer(paths, repository, "pi_eig_2", 4, attempt_id=UNASSESSED_ID, when=T + timedelta(days=1),
            unverified=("correctness",))
    _answer(paths, repository, "pi_eig_1", 0, attempt_id=ASSESSED_ID, when=T + timedelta(days=2))
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        record = LW.mastery_applications(connection, [UNASSESSED_ID])[UNASSESSED_ID]
        attempt = connection.execute("SELECT correctness FROM practice_attempts WHERE id = ?",
                                     (UNASSESSED_ID,)).fetchone()
    assert attempt[0] == 1.0 and record is not None and record.applied is False
    with repository.connection() as connection:
        outcomes = LW.qualifying_outcomes(connection, ["lo_eigen"], T.isoformat().replace("+00:00", "Z"),
                                          order=LW.outcome_order(version, fit=True), algorithm_version=version)
    assert outcomes[0]["id"] == resolver
    fitted = [entry for entry in LW.replay_state(vault, repository).trace if entry["kind"] == "pool_update"][0]
    assert fitted["resolving_attempt_id"] == resolver
    with repository.connection() as connection:
        key, inputs, created = connection.execute(
            "SELECT receipt_key, inputs_json, created_at FROM forecast_receipts "
            "WHERE kind = 'lesson_step_retained'").fetchone()
        resolution = FR.resolve_lesson_step(FR._Ledgers(connection, vault),
                                            {"receipt_key": key, "inputs": json.loads(inputs), "created_at": created})
    assert resolution["attempt_id"] == resolver


@pytest.mark.parametrize("malformation", [
    "json_set(payload_json, '$.mastery_application.observed_at', json('null'))",
    "json_remove(payload_json, '$.mastery_application.prior.last_evidence_at')",
    "json_set(payload_json, '$.mastery_application.applied', 'yes')",
    "json_set(payload_json, '$.mastery_application.observation_weight', 'NaN')",
])
def test_a_malformed_application_record_is_a_labelled_gap(tmp_path, malformation):
    """FR3-17 (failed before: a null instant became the string "None" and the trajectory raised; a missing evidence
    clock read as a recorded null clock and passed the chain): an incomplete or malformed record is no record, so the
    fit takes the labelled first-order form."""

    from tests.teacher_te1_review_fixes_helpers import _cold

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    with repository.connection() as connection:
        connection.execute(f"UPDATE attempt_debug_payloads SET payload_json = {malformation} WHERE attempt_id = ?",
                           (outcome.attempt_id,))
        connection.commit()
        assert LW.mastery_applications(connection, [outcome.attempt_id])[outcome.attempt_id] is None
    (update,) = [entry for entry in LW.replay_state(load_vault(paths.root), repository).trace
                 if entry["kind"] == "weight_update"]
    assert update["detail"]["likelihood"] == "first_order"
    assert update["detail"]["trajectory_inputs"][-1]["outcome_record_missing"] is True


def _unapplied_record(attempt_id: str, at: str) -> str:
    """A well-formed mastery record of an answer mastery did not apply (the shape ``mastery_application_facts``
    writes)."""

    state = {"mu": 0.0, "P": 1.0, "last_evidence_at": None}
    return json.dumps({"mastery_application": {
        "applied": False, "observed_at": at, "prior": state, "posterior": state, "score": None, "item_a": 1.0,
        "item_b": 0.0, "observation_weight": 0.0, "interpretation_variance": 0.0, "primed": False,
        "variance_floor": None}})


@pytest.mark.parametrize(("version", "expected"), [
    (OUTCOME_FIXES_ALGORITHM_VERSION, ("att_assessed", 0.0)),
    (LESSON_WEIGHT_FACTS_ALGORITHM_VERSION, ("att_unapplied", 1.0)),  # below the tag: the unapplied answer resolves
])
def test_the_routers_miss_cause_learning_credits_no_lesson_with_an_unapplied_answer(tmp_path, version, expected):
    """FR3-4, end to end on the router: a router-offered lesson, then a first cold answer mastery did not apply
    (correctness 1) and, a day later, an assessed miss on another item. From the tag the offer's outcome is the miss,
    so the lesson is not credited with a success (below it the unapplied answer resolved the offer as a success)."""

    from learnloop.db.repositories import Repository
    from learnloop.router_objective import miss_cause as MC

    from tests.daily_plan_fakes import NOW as CLOCK_NOW
    from tests.daily_plan_fakes import iso
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    def at(days, minutes=0.0):
        return iso(CLOCK_NOW - timedelta(days=days) + timedelta(minutes=minutes))

    frozen = {"status": "diagnosed", "p_gap": 0.0, "p_slip": 1.0, "p_unknown": 0.0}
    detail = {"lesson_offer": {"learning_object_id": "lo_a", "miss_cause": frozen, "mass": {"mean": 0.5},
                               "card": {"candidates": [{"predicted_success": 0.4}]}}}
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions (id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, "
            "log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, propensity, "
            "propensity_kind, detail_json, created_at) VALUES ('rd1', 'k', 'plan_block', 'desktop', 'live', 'p', ?, "
            "'v1', 'h', '[]', '[]', 0, 'lesson_offer:lo_a', 0.5, 'exact', ?, ?)", (version, json.dumps(detail), at(4)))
        connection.execute(
            "INSERT INTO lessons (id, driver, origin, origin_ref, entry, goal_text, learning_object_ids_json, "
            "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, goal_json, close_reason) VALUES "
            "('les1', 'desktop', 'router', 'rd1', 'learning_object', 'g', '[\"lo_a\"]', 'd', 'b', ?, ?, ?, '{}', "
            "'learner_stop')", (version, at(4, 1), at(4, 20)))
        for sequence, (attempt_id, item_id, correctness, when) in enumerate(
                (("att_unapplied", "pi_new", 1.0, at(3)), ("att_assessed", "pi_other", 0.0, at(2))), start=1):
            connection.execute(
                "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
                "correctness, primed, hints_used, created_at) VALUES (?, ?, 'lo_a', 'short_answer', "
                "'independent_attempt', ?, 0, 0, ?)", (attempt_id, item_id, correctness, when))
            connection.execute("INSERT INTO attempt_application_order(sequence, attempt_id, basis, algorithm_version, "
                               "recorded_at) VALUES (?, ?, 'applied', ?, ?)", (sequence, attempt_id, version, when))
        connection.execute("INSERT INTO attempt_debug_payloads(attempt_id, payload_json, algorithm_version, created_at) "
                           "VALUES (?, ?, ?, ?)", ("att_unapplied", _unapplied_record("att_unapplied", at(3)), version,
                                                   at(3)))
        connection.commit()
    with repository.connection() as connection:
        (row,) = MC._offer_rows(connection, vault.config, iso(CLOCK_NOW))
    assert (row["outcome_attempt_id"], row["y"]) == expected
