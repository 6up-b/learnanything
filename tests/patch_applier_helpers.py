"""What other test files use from ``tests/test_patch_applier.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository

from tests.helpers import NOW_ISO


def _seed_agent_and_proposal(repository: Repository, *, validation_status: str = "valid") -> None:
    repository.insert_agent_run(
        {
            "id": "agent_run_authoring_1",
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
            "status": "completed",
            "completed_at": NOW_ISO,
        }
    )
    repository.persist_proposal_batch(
        {
            "id": "patch_authoring_1",
            "agent_run_id": "agent_run_authoring_1",
            "purpose": "authoring",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd"}],
            "summary": "Create SVD application practice",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "proposal_item_lo",
                "client_item_id": "client_lo",
                "item_type": "learning_object",
                "operation": "create",
                "payload": {
                    "id": "lo_svd_applications",
                    "title": "SVD applications",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD can be used for low-rank approximation.",
                },
                "validation_status": validation_status,
                "validation_errors": ["bad"] if validation_status == "invalid" else [],
                "created_at": NOW_ISO,
            },
            {
                "id": "proposal_item_pi",
                "client_item_id": "client_pi",
                "item_type": "practice_item",
                "operation": "create",
                "payload": {
                    "id": "pi_svd_applications_001",
                    "learning_object_id": "lo_svd_applications",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "evidence_facets": ["application"],
                    "evidence_weights": {"application": 1.0},
                    "prompt": "Name one use of SVD.",
                    "expected_answer": "Low-rank approximation is one use.",
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names a real use."}],
                        "fatal_errors": [],
                    },
                },
                "validation_status": validation_status,
                "validation_errors": ["bad"] if validation_status == "invalid" else [],
                "created_at": NOW_ISO,
            },
        ],
    )
