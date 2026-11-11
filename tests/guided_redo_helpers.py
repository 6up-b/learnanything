"""What other test files use from ``tests/test_guided_redo.py``, kept here because a test file never
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


ITEM = "pi_svd_define_001"


def failed_attempt_with_repair(
    vault,
    repository,
    attempt_id: str,
    *,
    item_id: str = ITEM,
    primed: bool = False,
    clock=None,
):
    """A wrong attempt whose grade carries one repair suggestion with a
    preserved-prefix repaired trace — the raw material of the redo."""

    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U Sigma Q",
                primed=primed,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Q was used where Q transpose was required.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement="Treats Q and Q transpose as identical.",
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                        first_divergence={
                            "anchor_kind": "span",
                            "criterion_id": "correctness",
                            "quote": "Q",
                        },
                        candidate_causes=[
                            {
                                "statement": "Treats Q and Q transpose as identical.",
                                "cause_scope": "learner_state",
                                "target_ref": {
                                    "kind": "facet_capability",
                                    "facet_id": "recall",
                                    "capability": "retrieval",
                                },
                            }
                        ],
                        postdictive_claims=[
                            {"criterion_id": "correctness", "must": "not_full_credit"}
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "insert_transpose",
                        "rationale": "Preserve the factorization and repair only the transpose.",
                        "target_refs": [
                            {
                                "kind": "facet_capability",
                                "facet_id": "recall",
                                "capability": "retrieval",
                            }
                        ],
                        "expected_minutes": 2.0,
                        "answer_reveal_budget": 0.5,
                        "repaired_trace": {
                            "learner_work_prefix": "U Sigma ",
                            "repair_insertion_point": {
                                "anchor_kind": "span",
                                "criterion_id": "correctness",
                                "quote": "Q",
                                "char_start": 8,
                                "char_end": 9,
                            },
                            "minimal_edit": "replace Q with Q^T",
                            "regenerated_work": "",
                            "repaired_answer_md": "U Sigma Q^T",
                            "changed_latent_claims": [
                                "the right singular-vector factor is transposed"
                            ],
                            "changed_checkpoint_ids": [],
                        },
                    }
                ],
            ),
        ),
        clock=clock or FrozenClock(NOW),
    )
