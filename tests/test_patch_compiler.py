from __future__ import annotations

import pytest

from learnloop.services.patches import PatchApplicationError, compile_proposal_item
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_concept_edge

from tests.helpers import create_basic_vault


def _item(item_type: str, operation: str, payload: dict, *, target_entity_id=None) -> dict:
    return {
        "id": "ppi_test",
        "item_type": item_type,
        "operation": operation,
        "payload": payload,
        "edited_payload": None,
        "target_entity_id": target_entity_id,
        "validation_status": "valid",
    }


def _vault(tmp_path):
    return load_vault(create_basic_vault(tmp_path / "vault").root)


def test_compile_concept_create(tmp_path):
    vault = _vault(tmp_path)
    compiled = compile_proposal_item(
        vault, _item("concept", "create", {"id": "new_concept", "title": "New", "type": "concept"})
    )
    assert compiled.entity_type == "concept"
    assert compiled.entity_id == "new_concept"
    assert compiled.event_type == "created"
    # Compilation is pure: nothing is written to the vault yet.
    assert "new_concept" not in vault.concepts


def test_compile_learning_object_can_introduce_concept(tmp_path):
    vault = _vault(tmp_path)
    payload = {
        "id": "lo_new",
        "title": "New",
        "subjects": ["linear-algebra"],
        "concept_id": "missing_concept",
        "knowledge_type": "conceptual",
        "summary": "s",
    }
    compiled = compile_proposal_item(vault, _item("learning_object", "create", payload))

    assert compiled.entity_type == "learning_object"
    assert compiled.entity_id == "lo_new"


def test_compile_practice_item_requires_known_learning_object(tmp_path):
    vault = _vault(tmp_path)
    payload = {
        "id": "pi_new",
        "learning_object_id": "lo_missing",
        "practice_mode": "short_answer",
        "prompt": "p",
        "expected_answer": "a",
    }
    with pytest.raises(PatchApplicationError):
        compile_proposal_item(vault, _item("practice_item", "create", payload))


def test_compile_concept_edge_validates_endpoints(tmp_path):
    vault = _vault(tmp_path)
    good = compile_proposal_item(
        vault,
        _item(
            "concept_edge",
            "create",
            {
                "source": "singular_value_decomposition",
                "target": "singular_value_decomposition",
                "relation_type": "related",
            },
        ),
    )
    assert good.entity_type == "concept_edge"

    with pytest.raises(PatchApplicationError):
        compile_proposal_item(
            vault,
            _item(
                "concept_edge",
                "create",
                {"source": "missing", "target": "singular_value_decomposition", "relation_type": "related"},
            ),
        )


def test_compile_concept_edge_update_preserves_existing_endpoints(tmp_path):
    vault_root = create_basic_vault(tmp_path / "vault").root
    upsert_concept_edge(
        vault_root,
        {
            "id": "edge_existing",
            "source": "singular_value_decomposition",
            "target": "singular_value_decomposition",
            "relation_type": "related",
            "strength": 0.4,
        },
    )
    vault = load_vault(vault_root)

    compiled = compile_proposal_item(
        vault,
        _item("concept_edge", "update", {"strength": 0.8}, target_entity_id="edge_existing"),
    )

    assert compiled.entity_type == "concept_edge"
    assert compiled.entity_id == "edge_existing"


def test_compile_rubric_targets_existing_practice_item(tmp_path):
    vault = _vault(tmp_path)
    payload = {
        "target_practice_item_id": "pi_svd_define_001",
        "max_points": 4,
        "criteria": [{"id": "correctness", "points": 4, "description": "c"}],
        "fatal_errors": [],
    }
    compiled = compile_proposal_item(vault, _item("rubric", "update", payload))
    assert compiled.entity_type == "rubric"
    assert compiled.entity_id == "pi_svd_define_001"


def test_compile_error_type_create(tmp_path):
    vault = _vault(tmp_path)
    compiled = compile_proposal_item(
        vault,
        _item("error_type", "create", {"id": "new_error", "title": "New error", "severity_default": 0.5}),
    )
    assert compiled.entity_type == "error_type"
    assert compiled.event_type == "created"
