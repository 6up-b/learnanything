from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.services.proposals import authoring_context_hash, build_authoring_context
from learnloop.vault.loader import add_note, add_subject, load_vault

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
