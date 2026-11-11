"""What other test files use from ``tests/test_tutor_promotion_service.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.tutor.ai_contracts import PromotionAnalysis
from learnloop.db.repositories import Repository

from tests.structured_ai import StructuredClientFake


class _AnalysisClient(StructuredClientFake):
    """Provides Step-0 analysis only (no authoring provider available)."""

    provider_name = "codex"
    provider_type = "test"
    model = "test-model"

    def __init__(self, analysis: PromotionAnalysis):
        self._analysis = analysis
        self.analysis_contexts: list = []

    def run_promotion_analysis(self, context) -> PromotionAnalysis:
        self.analysis_contexts.append(context)
        return self._analysis

    def run_authoring_proposal(self, context) -> AuthoringProposal:
        raise AIProviderUnavailable("analysis-only test transport has no authoring backend")


def _insert_event(repository: Repository, event_id: str, **overrides) -> str:
    payload = {
        "id": event_id,
        "context": "practice",
        "practice_item_id": "pi_svd_define_001",
        "question_md": "Why must U have orthonormal columns?",
        "answer_md": "What property of the factors would guarantee that? Consider U^T U.",
        "answer_status": "answered",
    }
    payload.update(overrides)
    return repository.insert_question_event(payload)


def _attach_proposal(*, item_id="pi_svd_promoted_001", tags=None, review_route="auto_apply"):
    """A valid attach-to-existing-LO practice item that can auto-apply with grounding."""

    payload = {
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "prompt": "State the property of U's columns that the definition guarantees.",
        "expected_answer": "The columns of U are orthonormal.",
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "criterion_facet_weights": {"correctness": {"recall": 1.0}},
        "retrieval_demand": 0.8,
        "transfer_distance": 0.2,
        "scaffold_level": 0.0,
        "surface_family": "svd-property",
        "repair_targets": ["recall"],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "States orthonormality."}],
            "fatal_errors": [],
        },
    }
    if tags is not None:
        payload["tags"] = tags
    return AuthoringProposal.model_validate(
        {
            "summary": "Promote tutor probe to practice.",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_source"}],
            "items": [
                {
                    "client_item_id": "pi_promoted",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": item_id,
                    "source_ref_ids": ["note_svd_source"],
                    "rationale": 'Derived from the tutor probe "Consider U^T U."',
                    "review_route": review_route,
                    "audit": {
                        "audit_type": "deterministic_validator",
                        "status": "passed",
                        "summary": "Expected answer normalized.",
                        "validator_name": "short-answer-normalizer",
                        "validator_version": "1",
                    },
                    "payload": payload,
                }
            ],
        }
    )
