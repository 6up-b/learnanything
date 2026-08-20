from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.curriculum.concepts import merge_concepts
from learnloop.ops.doctor import run_doctor
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_markdown_with_frontmatter, read_yaml, write_markdown_with_frontmatter, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault


def test_merge_concepts_rewrites_vault_references(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_duplicate_svd_concept(paths)

    result = merge_concepts(vault_root, "singular_value_decomposition", "svd")

    loaded = load_vault(vault_root)
    assert "svd" not in loaded.concepts
    canonical = loaded.concepts["singular_value_decomposition"]
    assert "svd" in canonical.aliases
    assert "SVD alias" in canonical.aliases
    assert loaded.learning_objects["lo_svd_alias"].concept == "singular_value_decomposition"
    assert loaded.learning_objects["lo_svd_alias"].prerequisites == ["singular_value_decomposition"]
    assert loaded.learning_objects["lo_svd_alias"].confusables == ["singular_value_decomposition"]
    assert loaded.goals[0].facet_scope.concepts == ["singular_value_decomposition"]
    assert loaded.error_types["conceptual_slip"].related_concepts == ["singular_value_decomposition"]
    assert loaded.notes["note_svd_alias"].related_concepts == ["singular_value_decomposition"]
    assert all(edge.source != "svd" and edge.target != "svd" for edge in loaded.edges)
    assert all(edge.source != edge.target for edge in loaded.edges)

    graph = read_yaml(paths.subject_graph_path("linear-algebra"))
    assert graph["additional_concepts_in_scope"] == ["singular_value_decomposition"]
    assert graph["subject_ordering_hints"] == ["singular_value_decomposition"]
    metadata, _body = read_markdown_with_frontmatter(paths.note_path("linear-algebra", "note_svd_alias"))
    assert metadata["related_concepts"] == ["singular_value_decomposition"]
    assert "concepts/concepts.yaml" in result.changed_files
    assert result.change_batch_id is not None

    repository = Repository(paths.sqlite_path)
    assert repository.content_events_for_entity("concept", "singular_value_decomposition")
    assert repository.content_events_for_entity("concept", "svd")


def test_merge_concepts_dry_run_does_not_write(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_duplicate_svd_concept(paths)

    result = merge_concepts(vault_root, "singular_value_decomposition", "svd", dry_run=True)

    assert result.dry_run is True
    assert result.change_batch_id is None
    assert "svd" in load_vault(vault_root).concepts


def test_doctor_reports_concept_merge_candidates(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_duplicate_svd_concept(paths)

    report = run_doctor(vault_root)

    issues = [issue for issue in report.issues if issue.code.startswith("concept:merge_candidate")]
    assert issues
    assert issues[0].details["canonical_concept_id"] == "svd"
    assert issues[0].details["duplicate_concept_id"] == "singular_value_decomposition"


def test_merge_concepts_cli_json(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_duplicate_svd_concept(paths)

    result = CliRunner().invoke(
        app,
        [
            "merge-concepts",
            "singular_value_decomposition",
            "svd",
            "--vault",
            str(vault_root),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["merge"]["canonical_id"] == "singular_value_decomposition"
    assert "svd" not in load_vault(vault_root).concepts


def _add_duplicate_svd_concept(paths) -> None:
    concepts = read_yaml(paths.concepts_path)
    concepts["concepts"]["svd"] = {
        "title": "SVD alias",
        "type": "procedure",
        "aliases": ["Singular Value Decomposition"],
        "description": "Matrix factorization.",
        "tags": ["alias"],
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    concepts["concepts"]["matrix_factorization"] = {
        "title": "Matrix Factorization",
        "type": "concept",
        "aliases": [],
        "description": None,
        "tags": [],
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    write_yaml(paths.concepts_path, concepts)
    write_yaml(
        paths.relations_path,
        {
            "schema_version": 1,
            "edges": [
                {
                    "id": "edge_svd_self",
                    "relation_type": "related",
                    "source": "svd",
                    "target": "singular_value_decomposition",
                    "strength": 0.8,
                    "rationale": "Duplicate aliases.",
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
                {
                    "id": "edge_svd_factorization",
                    "relation_type": "part_of",
                    "source": "svd",
                    "target": "matrix_factorization",
                    "strength": 0.9,
                    "rationale": "SVD is a matrix factorization.",
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
            ],
        },
    )
    goals = read_yaml(paths.goals_path)
    goals["goals"][0]["facet_scope"]["concepts"] = ["singular_value_decomposition", "svd"]
    write_yaml(paths.goals_path, goals)
    errors = read_yaml(paths.error_types_path)
    errors["error_types"][0]["related_concepts"] = ["singular_value_decomposition", "svd"]
    write_yaml(paths.error_types_path, errors)
    graph = read_yaml(paths.subject_graph_path("linear-algebra"))
    graph["additional_concepts_in_scope"] = ["svd"]
    graph["subject_ordering_hints"] = ["svd", "singular_value_decomposition"]
    write_yaml(paths.subject_graph_path("linear-algebra"), graph)
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_alias"),
        {
            "schema_version": 1,
            "id": "lo_svd_alias",
            "title": "SVD alias",
            "subjects": ["linear-algebra"],
            "concept": "svd",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "Duplicate SVD LO.",
            "prerequisites": ["svd"],
            "confusables": ["singular_value_decomposition", "svd"],
            "difficulty_prior": 0.5,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_markdown_with_frontmatter(
        paths.note_path("linear-algebra", "note_svd_alias"),
        {
            "schema_version": 1,
            "id": "note_svd_alias",
            "subjects": ["linear-algebra"],
            "related_los": [],
            "related_concepts": ["svd"],
            "source_type": "learner_note",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        "# SVD alias\n\nNotes.\n",
    )
