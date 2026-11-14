"""What other test files use from ``tests/test_durable_promotion_arms.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)

from tests.helpers import NOW, NOW_ISO
from tests.km2_write_path_helpers import SHARED


CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
#: One criterion, one measurement target -> a failure names exactly ONE cause and
#: opens no unresolved-cause factor. This is the shape arm (d) can act on.
SINGLE_ITEM = "pi_svd_define_001"
STATEMENT = "The learner treats Sigma as the eigenvalue matrix of A."
REF = {"kind": "facet_capability", "facet_id": SHARED, "capability": "retrieval"}


def _verified_repair() -> dict:
    """A repair the deterministic verifier can PROVE.

    `expected_answer` on every `build_shared_facet_vault` item is the literal
    ``"An answer."``, so an `exact_match` request against a repaired answer of
    the same string is a genuine `verified` — the CAS/exact-match adapter decides
    it, not this fixture.
    """

    return {
        "practice_mode": "targeted_review",
        "operator": "restate_definition",
        "rationale": "Name Sigma as singular values.",
        "target_refs": [REF],
        "expected_minutes": 2.0,
        "answer_reveal_budget": 0.4,
        "verification_request": {"kind": "exact_match"},
        "repaired_trace": {
            "learner_work_prefix": "Sigma holds ",
            "repair_insertion_point": {
                "anchor_kind": "span",
                "criterion_id": "correctness",
                "quote": "eigenvalues",
            },
            "minimal_edit": "singular values",
            "regenerated_work": "",
            "repaired_answer_md": "An answer.",
            "changed_latent_claims": ["Sigma holds singular values"],
            "changed_checkpoint_ids": [],
        },
    }


def _failure(
    vault,
    repository,
    *,
    attempt_id: str,
    item_id: str = SINGLE_ITEM,
    criterion: str = "correctness",
    points: float = 0.0,
    rubric_score: int = 0,
    repairs: list[dict] | None = None,
    postdictive_claims: list[dict] | None = None,
    abstain: bool = False,
):
    """One real graded miss, diagnosed as a learner-state cause (or abstained)."""

    attribution = GradeAttribution(
        error_type="wrong_method",
        severity=0.7,
        evidence="Sigma is not the eigenvalue matrix of A.",
        is_misconception=not abstain,
        misconception_statement=None if abstain else STATEMENT,
        resolution_status="abstained" if abstain else "unresolved",
        abstention_reason=(
            "no facet in the vocabulary names this confusion" if abstain else None
        ),
        cause_scope="unknown" if abstain else "learner_state",
        operation=None if abstain else "wrong_method",
        first_divergence=(
            None
            if abstain
            else {
                "anchor_kind": "span",
                "criterion_id": criterion,
                "quote": "eigenvalues",
            }
        ),
        candidate_causes=(
            []
            if abstain
            else [
                {
                    "statement": STATEMENT,
                    "cause_scope": "learner_state",
                    "target_ref": REF,
                }
            ]
        ),
        postdictive_claims=list(postdictive_claims or []),
    )
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="Sigma holds eigenvalues.",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=rubric_score,
                criterion_points={criterion: points},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": criterion,
                        "points_awarded": float(points),
                        "evidence": "Sigma was called the eigenvalue matrix.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[attribution],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Sigma holds singular values.",
                repair_suggestions=list(
                    repairs if repairs is not None else [_verified_repair()]
                ),
            ),
        ),
        clock=CLOCK,
    )
