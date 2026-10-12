"""Learner-field outcome rows for split-vault (Slice 1 M2) attempts.

The field (Slice A F1) reads the grading-epoch ledger (``grading_evidence``)
and raw grades. M2 keeps that contract: blind grades write evidence through the
same apply path, a blind regrade appends a new epoch (and re-queues the
diagnosis), and a diagnosis writes no evidence. PF-c's unverified criteria are
the one new shape: they must write no negative evidence, in the field as in
the canonical projection. Fakes only; no network.
"""

from __future__ import annotations

from learnloop.attempts.regrade import regrade_attempt
from learnloop.field.outcomes import data_check, load_attempt_rows, load_facet_rows
from learnloop.substrate.canonical_projection import UNVERIFIED_CRITERION_BLOCK

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, drain_jobs, split_vault, submit
from tests.test_grading_support import _ZeroWithoutAttribution

# A different route to the reference's final answer: PF-c's final-answer check
# verifies it, so an unlocated mark-down is recorded unverified.
VERIFYING_ANSWER = "A different route.\nFinal answer: U Sigma V^T"


class _ZeroEverythingWithoutAttribution(ReviewFakeClient):
    """Marks every criterion down to zero, naming no error at all."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [row.model_copy(update={"points_awarded": 0.0}) for row in result.criterion_evidence]
        return result.model_copy(
            update={"criterion_evidence": evidence, "rubric_score": 0, "error_attributions": []}
        )


class _SetupOnly(ReviewFakeClient):
    """Full ``setup`` points; ``result`` fails at a quoted (located) error."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 2.0}) if row.criterion_id == "setup" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(
            update={"criterion_evidence": evidence, "rubric_score": int(sum(row.points_awarded for row in evidence))}
        )


def _rows(repository, vault, attempt_id):
    with repository.connection() as connection:
        attempts = [
            row
            for row in load_attempt_rows(connection, vault, legacy_fallback="current_content")
            if row.attempt_id == attempt_id
        ]
        facets = {
            row.facet_id: row.outcome
            for row in load_facet_rows(connection, vault, legacy_fallback="current_content")
            if row.attempt_id == attempt_id
        }
    return attempts, facets


def test_an_unverified_pfc_criterion_is_unassessed_in_the_field(tmp_path):
    """The final answer verifies and the grader zeroes ``result`` without
    locating an error. The field must not read that shortfall as a failure:
    the attempt is measured on ``setup`` alone. A located failure on the same
    item still reads as one."""

    _paths, vault, repository = split_vault(tmp_path)
    unverified = submit(vault, repository, _ZeroWithoutAttribution(), answer=VERIFYING_ANSWER)
    located = submit(vault, repository, _SetupOnly())

    attempts, facets = _rows(repository, vault, unverified.attempt_id)
    assert [row.outcome for row in attempts] == [1.0]
    assert attempts[0].effective_mass > 0
    assert facets and all(outcome == 1.0 for outcome in facets.values())

    attempts, facets = _rows(repository, vault, located.attempt_id)
    assert [row.outcome for row in attempts] == [0.5]
    assert min(facets.values()) < 1.0

    with repository.connection() as connection:
        report = data_check(connection, vault, legacy_fallback="current_content")
    assert report["pf_c_unverified_attempts"] == 1


def test_an_attempt_with_only_unverified_criteria_has_no_outcome_row(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, _ZeroEverythingWithoutAttribution(), answer=VERIFYING_ANSWER)

    attempts, facets = _rows(repository, vault, result.attempt_id)
    assert attempts == [] and facets == {}
    with repository.connection() as connection:
        report = data_check(connection, vault, legacy_fallback="current_content")
    assert report["attempts_without_outcome_row"][UNVERIFIED_CRITERION_BLOCK] == 1


def test_blind_grades_diagnoses_and_regrades_keep_the_epoch_contract(tmp_path):
    """A blind grade derives the same field rows a joint grade of the same
    evidence does; its diagnosis changes nothing; a blind regrade that still
    leaves a failure re-queues the diagnosis and the field follows the new
    epoch."""

    _jpaths, joint_vault, joint_repository = split_vault(tmp_path / "joint", version="mvp-0.9")
    joint = submit(joint_vault, joint_repository, ReviewFakeClient())
    joint_rows = _rows(joint_repository, joint_vault, joint.attempt_id)

    _paths, vault, repository = split_vault(tmp_path / "split")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    assert repository.latest_blind_grade_record(result.attempt_id) is not None
    blind_rows = _rows(repository, vault, result.attempt_id)
    assert [row.outcome for row in blind_rows[0]] == [row.outcome for row in joint_rows[0]] == [0.0]
    assert blind_rows[1] == joint_rows[1]

    assert [outcome.status for outcome in drain_jobs(vault, repository, client)] == ["completed"]
    assert _rows(repository, vault, result.attempt_id) == blind_rows

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=_SetupOnly(), grading_source="ai", clock=None)
    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record["supersedes_id"] is not None
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id, kind="diagnose", states=("queued",))
    attempts, facets = _rows(repository, vault, result.attempt_id)
    assert [row.outcome for row in attempts] == [0.5]
    assert facets != blind_rows[1]

    assert [outcome.status for outcome in drain_jobs(vault, repository, client)] == ["completed"]
    assert _rows(repository, vault, result.attempt_id) == (attempts, facets)
