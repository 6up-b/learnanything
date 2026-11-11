"""What other test files use from ``tests/test_data_capture_codex_rereview.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.data_capture import reading_exposures as RE


def _count(env, table):
    with env.repository.connection() as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _complete_section(env, extraction="x", section="sec"):
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO reader_section_progress(extraction_id, section_id, completed_at, updated_at) VALUES (?,?,?,?)",
            (extraction, section, env.now_iso(), env.now_iso()))


def _map_sections(monkeypatch, lo):
    monkeypatch.setattr(RE, "_section_los", lambda _vault, _repo, _extraction, _section: [lo])


def _other_item(env, objective):
    lo = objective["learning_object_id"]
    return next(item.id for item in env.vault.practice_items.values()
                if item.learning_object_id == lo and item.id != objective["practice_item_id"])
