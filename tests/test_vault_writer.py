from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.vault.loader import add_subject, load_vault
from learnloop.vault.writer import (
    VaultWriterError,
    upsert_concept,
    upsert_concept_edge,
    upsert_error_type,
    upsert_learning_object,
    upsert_practice_item,
)
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_writer_preserves_unknown_keys_and_timestamps(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                "singular_value_decomposition": {
                    "title": "Old title",
                    "type": "procedure",
                    "aliases": [],
                    "description": "Old.",
                    "tags": [],
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "source_note": "keep me",
                }
            },
            "file_note": "also keep",
        },
    )

    upsert_concept(
        vault_root,
        "singular_value_decomposition",
        {
            "title": "Singular Value Decomposition",
            "type": "procedure",
            "aliases": ["SVD"],
            "description": "Matrix factorization.",
            "tags": [],
        },
        clock=FrozenClock(NOW),
    )
    data = read_yaml(paths.concepts_path)

    concept = data["concepts"]["singular_value_decomposition"]
    assert data["file_note"] == "also keep"
    assert concept["source_note"] == "keep me"
    assert concept["created_at"] == "2026-01-01T00:00:00Z"
    assert concept["updated_at"] == NOW_ISO
    assert load_vault(vault_root).concepts["singular_value_decomposition"].title == "Singular Value Decomposition"


def test_writer_upserts_graph_error_lo_and_practice_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)

    upsert_concept(vault_root, "eigendecomposition", {"title": "Eigendecomposition", "type": "procedure"}, clock=FrozenClock(NOW))
    upsert_concept_edge(
        vault_root,
        {
            "id": "edge_svd_eigen",
            "relation_type": "confusable_with",
            "source": "singular_value_decomposition",
            "target": "eigendecomposition",
            "strength": 0.8,
        },
        clock=FrozenClock(NOW),
    )
    upsert_error_type(
        vault_root,
        {
            "id": "confused_with_eigendecomposition",
            "title": "Confuses SVD with eigendecomposition",
            "related_concepts": ["singular_value_decomposition", "eigendecomposition"],
            "severity_default": 0.8,
            "is_misconception": True,
        },
        clock=FrozenClock(NOW),
    )
    lo_path = upsert_learning_object(
        vault_root,
        {
            "id": "lo_svd_shapes",
            "title": "SVD factor shapes",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "fact",
            "summary": "The factors have dimensions that depend on the input matrix.",
        },
        clock=FrozenClock(NOW),
    )
    pi_path = upsert_practice_item(
        vault_root,
        {
            "id": "pi_svd_shapes_001",
            "learning_object_id": "lo_svd_shapes",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "State the dimensions of U, Sigma, and V^T for an m by n matrix.",
            "expected_answer": "U is m by m, Sigma is m by n, and V^T is n by n in full SVD.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct dimensions."}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )

    loaded = load_vault(vault_root)

    assert paths.relations_path.exists()
    assert loaded.edges[0].id == "edge_svd_eigen"
    assert loaded.error_types["confused_with_eigendecomposition"].severity_default == 0.8
    assert lo_path == paths.learning_object_path("linear-algebra", "lo_svd_shapes")
    assert pi_path == paths.practice_item_path("linear-algebra", "pi_svd_shapes_001")
    assert "lo_svd_shapes" in loaded.learning_objects
    assert "pi_svd_shapes_001" in loaded.practice_items


def test_writer_refuses_implicit_entity_moves(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_subject(vault_root, "calculus", "Calculus", clock=FrozenClock(NOW))

    with pytest.raises(VaultWriterError, match="Refusing to move"):
        upsert_learning_object(
            vault_root,
            {
                "id": "lo_svd_definition",
                "title": "Moved SVD definition",
                "subjects": ["calculus"],
                "concept": "singular_value_decomposition",
                "knowledge_type": "definition",
                "summary": "Should not move implicitly.",
            },
            clock=FrozenClock(NOW),
        )
