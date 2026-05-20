from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.client import AuthoringContext
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.patches import PatchApplicationError
from learnloop.services.proposals import (
    accept_items,
    edit_proposal_item,
    generate_authoring_proposal,
    persist_authoring_proposal,
)
from learnloop.vault.loader import add_note, load_vault

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


def test_canonical_source_refs_flow_into_learning_object_provenance(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "canonical_svd",
        "Canonical SVD",
        "SVD is a matrix factorization.",
        source_type="canonical_source",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Canonical extraction",
            "source_refs": [{"ref_type": "canonical_source", "ref_id": "note_canonical_svd"}],
            "items": [
                {
                    "client_item_id": "lo_canonical",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_canonical",
                    "source_ref_ids": ["note_canonical_svd"],
                    "rationale": "Extract the canonical definition.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Canonical SVD definition",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "definition",
                        "summary": "SVD is a matrix factorization.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    accept_items(vault_root, patch_id)

    learning_object = load_vault(vault_root).learning_objects["lo_svd_canonical"]
    assert learning_object.provenance.origin == "canonical_extract"
    assert learning_object.provenance.source_refs[0].ref_type == "canonical_source"
    assert learning_object.provenance.source_refs[0].ref_id == "note_canonical_svd"


def test_source_grounded_auto_apply_accepts_low_risk_create(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "svd_extract",
        "SVD extract",
        "SVD supports low-rank approximation.",
        clock=FrozenClock(NOW),
    )
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Auto apply source extraction",
            "source_refs": [{"ref_type": "note", "ref_id": "note_svd_extract"}],
            "items": [
                {
                    "client_item_id": "lo_auto",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_auto",
                    "source_ref_ids": ["note_svd_extract"],
                    "rationale": "Direct extraction from note.",
                    "review_route": "auto_apply",
                    "payload": {
                        "title": "SVD low-rank use",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "application",
                        "summary": "SVD supports low-rank approximation.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["decision"] == "accepted"
    assert item["applied_change_batch_id"]
    assert "lo_svd_auto" in load_vault(vault_root).learning_objects


def test_unresolved_source_ref_is_persisted_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Bad source",
            "source_refs": [{"ref_type": "canonical_source", "ref_id": "missing_source"}],
            "items": [
                {
                    "client_item_id": "lo_bad_source",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_bad_source",
                    "source_ref_ids": ["missing_source"],
                    "rationale": "Unresolved source should not apply.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Bad source LO",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "definition",
                        "summary": "Unverified.",
                    },
                }
            ],
        }
    )

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["unresolved_source_ref:missing_source"]
    with pytest.raises(PatchApplicationError):
        accept_items(vault_root, patch_id)


def test_edit_proposal_item_updates_payload_and_refreshes_duplicate_validation(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Duplicate then edit",
            "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
            "items": [
                {
                    "client_item_id": "lo_edit",
                    "item_type": "learning_object",
                    "operation": "create",
                    "proposed_entity_id": "lo_svd_definition",
                    "source_ref_ids": ["manual_svd"],
                    "rationale": "Needs learner edit.",
                    "review_route": "review_required",
                    "payload": {
                        "title": "Edited SVD use",
                        "subjects": ["linear-algebra"],
                        "concept_id": "singular_value_decomposition",
                        "knowledge_type": "application",
                        "summary": "SVD supports compression.",
                    },
                }
            ],
        }
    )
    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    repository = Repository(vault_root / "state.sqlite")
    item = repository.proposal_items(patch_id)[0]
    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["duplicate_id:lo_svd_definition"]

    edited_payload = {
        **item["payload"],
        "id": "lo_svd_compression",
        "title": "SVD compression",
    }
    edited = edit_proposal_item(vault_root, patch_id, item["id"], edited_payload, clock=FrozenClock(NOW))

    assert edited["validation_status"] == "valid"
    assert edited["validation_errors"] == []
    assert edited["edited_payload"]["id"] == "lo_svd_compression"
    accept_items(vault_root, patch_id, [item["id"]])
    loaded = load_vault(vault_root)
    assert "lo_svd_compression" in loaded.learning_objects
    assert loaded.learning_objects["lo_svd_compression"].title == "SVD compression"


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
