"""What other test files use from ``tests/test_causal_factor_deferral.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault


LO_ID = "lo_svd_definition"
ITEM_A = "pi_diag_transpose_a"
ITEM_B = "pi_diag_transpose_b"
STATEMENT = "the learner does not recall which factor is transposed"
DIAG_REF = {
    "kind": "facet_capability",
    "facet_id": "recall",
    "capability": "retrieval",
}


def _clock(**delta) -> FrozenClock:
    return FrozenClock(NOW + timedelta(**delta))


def _write_diag_item(paths, item_id: str, prompt: str) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": [
                "diagnostic_probe",
                "independent_attempt",
                "dont_know",
            ],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": prompt,
            "expected_answer": "V",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "correctness",
                        "points": 4,
                        "description": "Correct selection.",
                    }
                ],
                "fatal_errors": [],
            },
            "created_at": "2026-05-19T12:00:00Z",
            "updated_at": "2026-05-19T12:00:00Z",
        },
    )


def _vault(tmp_path):
    from learnloop.substrate.state_sync import sync_vault_state
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    # The promotion-discipline path under test (`_normalize_compositional`) runs only in canonical-state vaults, which
    # the head is.
    _write_diag_item(paths, ITEM_A, "Which SVD factor is transposed?")
    _write_diag_item(paths, ITEM_B, "In U S V^T, which factor carries the T?")
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=_clock())
    return vault, repository


def _failed_diagnostic(vault, repository, *, attempt_id, item_id, clock):
    """A failed diagnostic administration, through the live post-attempt path.

    `apply_attempt` materializes the causal episode (opening the repair-lane
    factor); `evaluate_attempt_intervention_followup` is the seam the sidecar
    drives next, and it is where normalization (and therefore the deferral
    sweep and any promotion) runs.
    """

    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U",
                attempt_type="diagnostic_probe",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0.0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Named an untransposed factor.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": now_iso,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The learner named an untransposed factor.",
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="recall_omission",
                        target_criterion_ids=["correctness"],
                        is_misconception=True,
                        misconception_statement=STATEMENT,
                        candidate_causes=[
                            {
                                "statement": STATEMENT,
                                "cause_scope": "learner_state",
                                "target_ref": DIAG_REF,
                            }
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
                feedback_md="Check which factor carries the transpose.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "restate_transpose_rule",
                        "rationale": "Re-establish which factor is transposed.",
                        "target_refs": [DIAG_REF],
                        "expected_minutes": 3.0,
                    }
                ],
            ),
        ),
        clock=clock,
    )
    evaluate_attempt_intervention_followup(
        vault, repository, result=result, clock=clock
    )
    return result


def _open_factor(repository, attempt_id):
    factors = repository.unresolved_cause_factors_for_attempt(attempt_id)
    assert len(factors) == 1, factors
    return factors[0]


def _factor_repair_class(factor) -> tuple[str, list[str]]:
    concrete = [
        cause
        for cause in factor["candidate_causes"]
        if not cause.get("open_set") and cause.get("hypothesis_id")
    ]
    repair_class_ids = [
        str(cause["repair_class_id"])
        for cause in concrete
        if cause.get("repair_class_id")
    ]
    assert repair_class_ids
    return repair_class_ids[0], [str(cause["hypothesis_id"]) for cause in concrete]
