"""What other test files use from ``tests/test_diagnostic_augmentation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.attempts.ai_contracts import GradingProposal

from tests.structured_ai import JointGraderAlsoBlind, StructuredClientFake


def _proposal(
    attempt_id: str,
    *,
    cause: str = "confuses SVD with an eigendecomposition",
    anchor_kind: str = "whole_answer",
    cause_scope: str | None = "learner_state",
) -> GradingProposal:
    """``cause_scope=None`` omits the field, as a grader that never scoped it would."""

    proposal = GradingProposal.model_validate(
        {
            "diagnosis_md": f"The trace {cause}.",
            "repair_suggestions": [
                {
                    "repaired_trace": {
                        "learner_work_prefix": "",
                        "minimal_edit": "restore V transpose",
                        "repaired_answer_md": "A = U Sigma V transpose",
                        "changed_latent_claims": ["right factor omitted"],
                        "changed_checkpoint_ids": [],
                    },
                    "practice_mode": "short_answer",
                    "rationale": "Restore the omitted factor.",
                    "operator": "restore_factor",
                    "target_refs": [
                        {"kind": "criterion", "criterion_id": "correctness"}
                    ],
                    "preserve_refs": [],
                }
            ],
            "attempt_id": attempt_id,
            "practice_item_id": "pi_svd_define_001",
            "rubric_score": 0,
            "criterion_evidence": [
                {
                    "criterion_id": "correctness",
                    "points_awarded": 0,
                    "evidence": "The right factor is absent.",
                }
            ],
            "fatal_errors": [],
            "error_attributions": [
                {
                    "error_type": "conceptual_slip",
                    "severity": 0.7,
                    "evidence": cause,
                    "is_misconception": True,
                    "misconception_statement": cause,
                    "target_criterion_ids": ["correctness"],
                    "resolution_status": "resolved",
                    **(
                        {"cause_scope": cause_scope}
                        if cause_scope is not None
                        else {}
                    ),
                    "target_ref": {
                        "kind": "criterion",
                        "criterion_id": "correctness",
                    },
                    "operation": "restore_factor",
                    "first_divergence": {
                        "anchor_kind": anchor_kind,
                        "criterion_id": "correctness",
                    },
                }
            ],
            "grader_confidence": 0.8,
            "manual_review_recommended": False,
        }
    )
    assert proposal.error_attributions[0].cause_scope == cause_scope
    return proposal


class _SequenceDiagnostician(JointGraderAlsoBlind, StructuredClientFake):
    provider_name = "diagnostician"
    model = "claude-4"

    def __init__(self, proposals):
        self.proposals = list(proposals)
        self.contexts = []

    def run_grading_proposal(self, context):
        self.contexts.append(context)
        proposal = self.proposals.pop(0)
        return proposal(context) if callable(proposal) else proposal


def fail_after_the_joint_grade_commits(patch) -> None:
    """Make a model grading raise once its grade (with its receipt and grading
    record) has committed: a later step that fails. Before Q14 a failing
    Phase-C receipt stood in for this; the receipt is now written in the
    grading transaction, so it rolls the grade back instead.

    Both doors are patched: the joint grading of an unsplit vault and the blind
    grading of a split one (the head's), each of which commits its grade in one
    transaction before the caller's later steps."""

    from learnloop.attempts import attempts

    for name in ("_complete_joint_graded_attempt", "_complete_blind_graded_attempt"):
        original = getattr(attempts, name)

        def committed_then_failed(*args, _original=original, **kwargs):
            _original(*args, **kwargs)
            raise ValueError("interrupted after the grade committed")

        patch.setattr(attempts, name, committed_then_failed)
