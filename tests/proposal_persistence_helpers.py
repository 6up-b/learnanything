"""What other test files use from ``tests/test_proposal_persistence.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.proposals.ai_contracts import AuthoringContext
from learnloop.content.proposals.ai_contracts import AuthoringProposal

from tests.structured_ai import StructuredClientFake


def _generated_practice_proposal_payload(payload_overrides: dict) -> dict:
    payload = {
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "prompt": "Name one use of SVD.",
        "expected_answer": "Low-rank approximation.",
        "retrieval_demand": 0.8,
        "transfer_distance": 0.2,
        "scaffold_level": 0.0,
        "surface_family": "svd-application",
        "repair_targets": ["application"],
        "tags": ["generated"],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
            "fatal_errors": [],
        },
    }
    payload.update(payload_overrides)
    return {
        "summary": "Generated source-linked practice metadata",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "pi_generated_metadata",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_generated_metadata",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Generated because no direct source exercise was available.",
                "review_route": "auto_apply",
                "audit": {
                    "audit_type": "deterministic_validator",
                    "status": "passed",
                    "summary": "Expected answer normalized successfully.",
                    "validator_name": "short-answer-normalizer",
                    "validator_version": "1",
                },
                "payload": payload,
            }
        ],
    }


class _QueueAuthoringClient(StructuredClientFake):
    def __init__(self, proposals: list[AuthoringProposal]):
        self.proposals = list(proposals)
        self.contexts: list[AuthoringContext] = []

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        self.contexts.append(context)
        return self.proposals.pop(0)

    def run_grading_proposal(self, context):  # pragma: no cover
        raise NotImplementedError
