from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.services.proposals import authoring_context_hash, authoring_context_stats, build_authoring_context
from learnloop.vault.loader import add_note, add_subject, load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault


def test_authoring_context_is_deterministic_and_hashable(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(vault_root, "linear-algebra", "note_svd", "SVD", "SVD factorizes matrices.", clock=FrozenClock(NOW))
    loaded = load_vault(vault_root)

    first = build_authoring_context(loaded, subjects=["linear-algebra"])
    second = build_authoring_context(loaded, subjects=["linear-algebra"])

    assert first == second
    assert authoring_context_hash(first) == authoring_context_hash(second)
    note_ids = [note["id"] for note in first.notes]
    assert "note_svd" in note_ids
    assert "manual_svd" not in first.source_ids
    assert "lo_svd_definition" in [lo["id"] for lo in first.learning_objects]


def test_authoring_context_filters_by_subject(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_subject(vault_root, "calculus", "Calculus", clock=FrozenClock(NOW))
    add_note(vault_root, "calculus", "note_calc", "Limits", "Limits and derivatives.", clock=FrozenClock(NOW))
    loaded = load_vault(vault_root)

    context = build_authoring_context(loaded, subjects=["calculus"])

    note_ids = [note["id"] for note in context.notes]
    assert note_ids == ["note_calc"]
    assert context.subjects == ["calculus"]
    # The linear-algebra Learning Object is out of scope when filtering to calculus.
    assert all(lo["id"] != "lo_svd_definition" for lo in context.learning_objects)


def test_authoring_context_includes_explicit_source_refs(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    loaded = load_vault(vault_root)

    context = build_authoring_context(
        loaded,
        source_refs=[{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        instructions="Focus on definitions.",
    )

    assert "manual_svd" in context.source_ids
    assert context.instructions == "Focus on definitions."


def test_authoring_context_stats_report_request_size(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    loaded = load_vault(vault_root)

    stats = authoring_context_stats(build_authoring_context(loaded, subjects=["linear-algebra"]))

    assert stats["counts"]["learning_objects"] == 1
    assert stats["counts"]["practice_items"] == 1
    assert stats["chars"]["output_schema"] > 0
    assert stats["chars"]["prompt_plus_schema"] >= stats["chars"]["output_schema"]
    assert stats["approx_tokens"]["prompt_plus_schema"] > 0


def test_authoring_context_carries_focus_concepts_and_facets(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    loaded = load_vault(vault_root)

    context = build_authoring_context(
        loaded,
        subjects=["linear-algebra"],
        focus_concepts=["singular_value_decomposition"],
        focus_facets=["recall"],
    )

    assert context.focus_concepts == ["singular_value_decomposition"]
    assert context.focus_facets == ["recall"]
    unfocused = build_authoring_context(loaded, subjects=["linear-algebra"])
    assert unfocused.focus_concepts == []
    assert unfocused.focus_facets == []
    assert authoring_context_hash(context) != authoring_context_hash(unfocused)


def test_authoring_context_includes_blueprint_facets_before_items_exist(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(lo_path)
    payload["blueprints"] = [
        {
            "id": "bp_svd",
            "recipes": [
                {
                    "id": "recipe_svd",
                    "all_of": [
                        {
                            "facet": "facet_svd_structure",
                            "capability": "schema_interpretation",
                        }
                    ],
                }
            ],
        }
    ]
    write_yaml(lo_path, payload)

    context = build_authoring_context(load_vault(paths.root), subjects=["linear-algebra"])
    lo = next(entry for entry in context.learning_objects if entry["id"] == "lo_svd_definition")

    assert lo["existing_evidence_facets"] == ["facet_svd_structure", "recall"]
