from __future__ import annotations

import pytest

from learnloop.codex.schemas import AuthoringProposalItem, SourceRef
from learnloop.services.proposals import evaluate_review_policy
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def _item(**overrides) -> AuthoringProposalItem:
    data = {
        "client_item_id": "c1",
        "item_type": "learning_object",
        "operation": "create",
        "proposed_entity_id": "lo_new",
        "source_ref_ids": ["src"],
        "rationale": "because",
        "review_route": "auto_apply",
        "payload": {"title": "New LO", "subjects": ["linear-algebra"], "concept_id": "x", "summary": "s"},
    }
    data.update(overrides)
    return AuthoringProposalItem.model_validate(data)


def _practice_item(**overrides) -> AuthoringProposalItem:
    data = {
        "client_item_id": "pi_new",
        "item_type": "practice_item",
        "operation": "create",
        "proposed_entity_id": "pi_svd_generated",
        "source_ref_ids": ["src"],
        "rationale": "Generated because no direct source exercise was available.",
        "review_route": "auto_apply",
        "payload": {
            "learning_object_id": "lo_svd_definition",
            "practice_mode": "short_answer",
            "prompt": "What does SVD produce?",
            "expected_answer": "Singular values and orthogonal factors.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Names the factors."}],
                "fatal_errors": [],
            },
            "tags": ["generated"],
        },
    }
    data.update(overrides)
    return AuthoringProposalItem.model_validate(data)


def test_reject_route_stays_reject(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    assert evaluate_review_policy(_item(review_route="reject"), loaded) == "reject"


def test_low_risk_create_can_auto_apply(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    assert evaluate_review_policy(_item(), loaded) == "auto_apply"


def test_manual_context_auto_apply_route_still_requires_review(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _item(source_ref_ids=["manual"])
    assert (
        evaluate_review_policy(
            item,
            loaded,
            source_refs=[SourceRef(ref_type="manual_context", ref_id="manual")],
        )
        == "review_required"
    )


def test_modification_requires_review(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _item(
        operation="update",
        proposed_entity_id=None,
        target={"entity_type": "learning_object", "entity_id": "lo_svd_definition"},
    )
    assert evaluate_review_policy(item, loaded) == "review_required"


def test_id_collision_requires_review(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _item(proposed_entity_id="lo_svd_definition")
    assert evaluate_review_policy(item, loaded) == "review_required"


def test_missing_source_refs_requires_review(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    assert evaluate_review_policy(_item(source_ref_ids=[]), loaded) == "review_required"


def test_create_requires_proposed_or_payload_id():
    with pytest.raises(ValueError, match="proposed_entity_id"):
        _item(proposed_entity_id=None)


def test_concept_changes_are_not_auto_applied(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _item(item_type="concept", payload={"title": "C", "type": "concept"})
    assert evaluate_review_policy(item, loaded) == "review_required"


def test_source_grounded_existing_concept_edge_can_auto_apply(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _item(
        item_type="concept_edge",
        proposed_entity_id=None,
        payload={
            "source_concept_id": "singular_value_decomposition",
            "target_concept_id": "singular_value_decomposition",
            "relation_type": "related",
        },
    )
    assert evaluate_review_policy(item, loaded) == "auto_apply"


def test_generated_practice_item_missing_audit_requires_review(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)

    assert evaluate_review_policy(_practice_item(), loaded) == "review_required"


def test_generated_practice_item_passed_audit_can_auto_apply(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _practice_item(
        audit={
            "audit_type": "deterministic_validator",
            "status": "passed",
            "summary": "Expected answer normalized successfully.",
            "validator_name": "short-answer-normalizer",
        }
    )

    assert evaluate_review_policy(item, loaded) == "auto_apply"


def test_generated_practice_item_failed_audit_requires_review(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _practice_item(
        audit={
            "audit_type": "deterministic_validator",
            "status": "failed",
            "summary": "Expected answer did not match generated solution.",
        }
    )

    assert evaluate_review_policy(item, loaded) == "review_required"
