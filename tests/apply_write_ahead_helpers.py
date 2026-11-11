"""What other test files use from ``tests/test_apply_write_ahead.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository

from tests.helpers import NOW_ISO


LO_ID = "lo_svd_applications"
PI_ID = "pi_svd_applications_001"
_LO_PAYLOAD = {
    "id": LO_ID,
    "title": "SVD applications",
    "subjects": ["linear-algebra"],
    "concept_id": "singular_value_decomposition",
    "knowledge_type": "application",
    "summary": "SVD can be used for low-rank approximation.",
    "provenance": {
        "origin": "codex_proposal",
        "source_refs": [
            {
                "ref_type": "canonical_source",
                "ref_id": "src_axler",
                "source_id": "src_axler",
                "revision_id": "rev_axler_1",
                "locator": "block_span:p12",
                "locator_scheme": "block_span_v1",
                "relation": "primary",
                "span_hash": "sha256:deadbeef",
            }
        ],
    },
}
_PI_PAYLOAD = {
    "id": PI_ID,
    "learning_object_id": LO_ID,
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
}


def _seed_agent(repository: Repository, agent_id: str) -> None:
    repository.insert_agent_run(
        {
            "id": agent_id,
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
            "status": "completed",
            "completed_at": NOW_ISO,
        }
    )


def _seed_lo_and_pi_proposal(repository: Repository, patch_id: str = "patch_wa") -> None:
    _seed_agent(repository, f"agent_{patch_id}")
    repository.persist_proposal_batch(
        {
            "id": patch_id,
            "agent_run_id": f"agent_{patch_id}",
            "purpose": "authoring",
            "source_refs": [],
            "summary": "Create SVD LO + item",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "item_lo",
                "client_item_id": "client_lo",
                "item_type": "learning_object",
                "operation": "create",
                "payload": _LO_PAYLOAD,
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            },
            {
                "id": "item_pi",
                "client_item_id": "client_pi",
                "item_type": "practice_item",
                "operation": "create",
                "payload": _PI_PAYLOAD,
                "depends_on_client_item_ids": ["client_lo"],
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            },
        ],
    )
