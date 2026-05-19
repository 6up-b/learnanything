from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.client import AuthoringContext
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.patches import PatchApplicationError
from learnloop.services.proposals import accept_items, generate_authoring_proposal, persist_authoring_proposal

from tests.helpers import NOW, create_basic_vault


class _FakeAuthoringClient:
    def __init__(self, proposal: AuthoringProposal):
        self.proposal = proposal

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        return self.proposal

    def run_grading_proposal(self, context):  # pragma: no cover
        raise NotImplementedError


def test_generate_persists_one_item_per_proposal_item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_two_item_payload())
    patch_id = generate_authoring_proposal(vault_root, _FakeAuthoringClient(proposal), clock=FrozenClock(NOW))

    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert len(items) == 2
    assert {item["item_type"] for item in items} == {"learning_object", "practice_item"}
    assert all(item["decision"] == "pending" for item in items)


def test_reject_route_item_is_persisted_invalid_and_not_applied(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_reject_payload())
    patch_id = persist_authoring_proposal(vault_root, proposal, provider="import", clock=FrozenClock(NOW))

    repository = Repository(vault_root / "state.sqlite")
    items = repository.proposal_items(patch_id)
    assert len(items) == 1
    assert items[0]["validation_status"] == "invalid"
    assert items[0]["decision"] == "pending"

    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def _two_item_payload() -> dict:
    return {
        "summary": "Two-item proposal",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "lo_1",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_svd_imported",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Add LO.",
                "review_route": "review_required",
                "payload": {
                    "title": "Imported SVD use",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD compresses matrices.",
                },
            },
            {
                "client_item_id": "pi_1",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_imported_001",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Practice it.",
                "review_route": "review_required",
                "payload": {
                    "learning_object_id": "lo_svd_imported",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "Use of SVD?",
                    "expected_answer": "Low-rank approximation.",
                    "evidence_facets": ["application"],
                    "evidence_weights": {"application": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names a use."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }


def _reject_payload() -> dict:
    return {
        "summary": "Rejected proposal",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": "lo_bad",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_rejected",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Low quality.",
                "review_route": "reject",
                "payload": {
                    "title": "Rejected LO",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "summary": "x",
                },
            }
        ],
    }
