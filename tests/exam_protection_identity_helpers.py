"""What other test files use from ``tests/test_exam_protection_identity.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository

from tests.reread_safety_helpers import _exam_reading_b, _persist


def _cached_inventory(repo: Repository, inventory_id: str, extraction_id: str, unit_id: str, spans, *,
                      profile: str = "combined", semantic_hash: str | None = None, prompt_version: str = "p",
                      model: str = "f", usage: str = '{"calls": 1}') -> None:
    """A cache row a model run of an older build wrote (no ledger row beside it)."""

    import json

    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_unit_inventories(id, source_revision_id, extraction_id, unit_id, unit_semantic_hash, "
            "inventory_profile, inventory_schema_version, prompt_version, provider, model, inventory_json, usage_json, "
            "created_at) VALUES (?, 'rev_x', ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, '2026-10-14T09:00:00Z')",
            (inventory_id, extraction_id, unit_id, semantic_hash or f"sha256:{inventory_id}", profile, prompt_version,
             model, model, json.dumps({"assessment_signals": [{"held_out": True, "span_ids": list(spans)}]}), usage))
        connection.commit()


def _older_build_with_membership(exam_book, member, *, profile: str = "combined") -> None:
    """A vault an older build wrote: no ledger (migration 204 not applied), a
    cache row with a held-out signal on A's Exam unit, and B read; the book's
    membership in ``source_sets.yaml`` is ``member`` (None: no set)."""

    from learnloop.vault.writer import upsert_source_set

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    with repo.connection() as connection:
        connection.execute("DROP TRIGGER source_held_out_signal_marks_no_update")
        connection.execute("DROP TABLE source_held_out_signal_marks")
        connection.execute("DELETE FROM schema_migrations WHERE version = 204")
        connection.commit()
    _cached_inventory(repo, "inv_q", "extXA", "u1", ["x1"], profile=profile)
    if member is not None:
        upsert_source_set(root, {"id": "set_x", "subject_id": "linear-algebra", "title": "Exam prep",
                                 "members": [member]})


_EXAM_MEMBER = {"source_id": "src_x", "revision_id": "rev_x", "default_role": "exam", "scope": []}
