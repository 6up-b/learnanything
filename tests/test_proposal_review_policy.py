from __future__ import annotations

from learnloop.codex.schemas import AuthoringProposalItem
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


def test_reject_route_stays_reject(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    assert evaluate_review_policy(_item(review_route="reject"), loaded) == "reject"


def test_low_risk_create_can_auto_apply(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    assert evaluate_review_policy(_item(), loaded) == "auto_apply"


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


def test_concept_changes_are_not_auto_applied(tmp_path):
    loaded = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = _item(item_type="concept", payload={"title": "C", "type": "concept"})
    assert evaluate_review_policy(item, loaded) == "review_required"
