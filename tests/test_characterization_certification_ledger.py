"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior; these tests document reality, not desired behavior. When P0.x intentionally changes behavior, update these tests in the same commit and note the change.

Pins the current certification / evidence-mass behavior of the KM2 canonical
projection and its ledger query:

  * evidence mass is a pure function of attempt type (+ config) ONLY — grader
    confidence / grade provenance have no channel into it,
  * the ``canonical_observation_ledger`` row shape carries no grader_confidence,
    no raw grade-event reference, and no calibration-lineage fields,
  * a deferred regrade that supersedes grading evidence and rewrites
    ``points_awarded`` DOES change what the projection computes — the projection
    reads the current (mutable, non-superseded) grading evidence as
    authoritative rather than folding an immutable raw-grade-event history.
"""

from __future__ import annotations

import inspect

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.evidence import attempt_evidence_mass
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version

ITEM_ID = "pi_svd_define_001"
FACET = "recall"


def _mvp07_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _attempt(vault, repository, *, points, confidence):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(
            criterion_points={"correctness": points}, fatal_errors=[], confidence=confidence
        ),
        clock=FrozenClock(NOW),
    )


def _cells(repository):
    return {
        (c.facet_id, c.capability): (
            round(c.direct_positive_mass, 9),
            round(c.direct_negative_mass, 9),
            round(c.embedded_positive_mass, 9),
            round(c.embedded_negative_mass, 9),
            round(c.certification_credit, 9),
        )
        for c in repository.facet_capability_evidence_all()
    }


# ---------------------------------------------------------------------------
# 1. Evidence mass derives from attempt type ONLY.
# ---------------------------------------------------------------------------


def test_evidence_mass_signature_has_no_confidence_channel():
    """The mass primitive's only inputs are attempt_type + config.

    There is literally no parameter through which grader confidence or grade
    provenance could reach the mass computation.
    """

    params = list(inspect.signature(attempt_evidence_mass).parameters)
    assert params == ["attempt_type", "config"]


def test_evidence_mass_is_pure_function_of_attempt_type(tmp_path):
    vault, _repository = _mvp07_vault(tmp_path)
    cfg = vault.config.evidence
    # Same attempt type -> byte-identical mass, every call.
    mass_a = attempt_evidence_mass("independent_attempt", cfg)
    mass_b = attempt_evidence_mass("independent_attempt", cfg)
    assert mass_a == mass_b
    # And it is exactly the config entry for that attempt type (no other input).
    assert mass_a == cfg.attempt_types["independent_attempt"].evidence_mass


def test_projection_mass_identical_across_grader_confidence(tmp_path):
    """Two runs identical except self-grade confidence -> identical projected mass.

    Confidence is stored as manual-review reason / learner_confidence label only;
    it never reaches grading_evidence.points_awarded, so the projection cannot
    see it.
    """

    high_vault, high_repo = _mvp07_vault(tmp_path / "high")
    _attempt(high_vault, high_repo, points=4, confidence=4)
    project_canonical_facet_state(high_vault, high_repo)

    low_vault, low_repo = _mvp07_vault(tmp_path / "low")
    _attempt(low_vault, low_repo, points=4, confidence=1)
    project_canonical_facet_state(low_vault, low_repo)

    assert _cells(high_repo) == _cells(low_repo)
    # Sanity: there IS a demonstrated cell (the comparison is not vacuous).
    assert _cells(high_repo)


# ---------------------------------------------------------------------------
# 2. Ledger row shape carries no confidence / raw-grade / calibration lineage.
# ---------------------------------------------------------------------------


def test_ledger_row_shape_excludes_confidence_and_calibration_lineage(tmp_path):
    vault, repository = _mvp07_vault(tmp_path)
    _attempt(vault, repository, points=4, confidence=4)

    ledger = repository.canonical_observation_ledger()
    assert ledger
    row = ledger[0]

    # The attempt-level row keys are exactly the projection's inputs: attempt
    # identity/type/timing + evidence. No grader confidence, no raw grade-event
    # reference, no calibration lineage.
    assert set(row) == {
        "attempt_id",
        "practice_item_id",
        "learning_object_id",
        "attempt_type",
        "practice_mode",
        "hints_used",
        "created_at",
        "evidence",
    }
    forbidden = {
        "grader_confidence",
        "confidence",
        "grade_event_id",
        "raw_grade_event_id",
        "calibration_version",
        "calibration_lineage",
        "grader_calibration_id",
    }
    assert forbidden.isdisjoint(row)

    # Evidence rows carry only per-criterion attribution inputs — no grader
    # confidence and no calibration fields either.
    assert row["evidence"]
    evidence_row = row["evidence"][0]
    assert set(evidence_row) == {
        "criterion_id",
        "points_awarded",
        "attribution_json",
        "correlation_group",
        "recipe_id",
        "observation_id",
        "grading_revision",
        "assessment_contract_version_id",
    }
    assert forbidden.isdisjoint(evidence_row)


# ---------------------------------------------------------------------------
# 3. Deferred regrade rewrites of grading evidence change the projection.
# ---------------------------------------------------------------------------


def test_regrade_of_grading_evidence_changes_projection(tmp_path):
    """The projection reads the current (non-superseded) grading evidence as
    authoritative: superseding it with a lower score changes the projected mass.

    This pins the deficiency that the projection folds over the mutable current
    grading-evidence cache, not an append-only immutable raw-grade-event history.
    """

    vault, repository = _mvp07_vault(tmp_path)
    result = _attempt(vault, repository, points=4, confidence=4)
    project_canonical_facet_state(vault, repository)
    before = _cells(repository)
    assert before  # full-marks attempt certified some positive mass

    # A deferred regrade: supersede the tier-1 self-grade and land a lower score.
    original = repository.fetch_grading_evidence(result.attempt_id)[0]
    new_evidence_id = "regrade_ev_1"
    repository.insert_regrade_evidence(
        attempt_id=result.attempt_id,
        new_evidence_rows=[
            {
                "id": new_evidence_id,
                "criterion_id": original.criterion_id,
                "points_awarded": 1.0,  # was 4.0 -> now below the failure threshold
                "grader_tier": 1,
                "created_at": NOW_ISO,
                "observation_id": f"{result.attempt_id}:{original.criterion_id}:1",
                "grading_revision": 1,
                "assessment_contract_version_id": original.assessment_contract_version_id,
            }
        ],
        superseded_by_evidence_id=new_evidence_id,
        clock=FrozenClock(NOW),
    )

    project_canonical_facet_state(vault, repository)
    after = _cells(repository)

    # The projection is NOT invariant to the regrade: rewriting the summary
    # (points_awarded) changed what it computed.
    assert after != before
