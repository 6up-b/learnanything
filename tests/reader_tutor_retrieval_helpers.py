"""What other test files use from ``tests/test_reader_tutor_retrieval.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ids import new_ulid


NOW = "2026-10-19T10:00:00Z"


def _bound_session(repository, item_id: str) -> str:
    session_id = "wbs_" + new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "extraction_id, span_ids_json, source_visible, created_at, updated_at) "
            "VALUES (?, ?, 'Solve it', 'bound', 'reader', 'work_through', 'ext_text', '[\"t3\"]', 1, ?, ?)",
            (session_id, item_id, NOW, NOW))
        connection.commit()
    return session_id


def _workbench_steps(repository, item_id: str, steps: list[str]) -> str:
    session_id = _bound_session(repository, item_id)
    with repository.connection() as connection:
        for index, body in enumerate(steps, start=1):
            connection.execute(
                "INSERT INTO workbench_steps (id, session_id, ordinal, kind, body_md, client_idempotency_key, "
                "created_at) VALUES (?, ?, ?, 'step', ?, ?, ?)",
                ("wst_" + new_ulid(), session_id, float(index), body, f"k{index}", NOW))
        connection.commit()
    return session_id


def _quote_of(span_key: tuple[str, str], *, edit: str | None = None):
    def excerpt(context):
        for span in context["source_spans"]:
            if (span["extraction_id"], span["span_id"]) == span_key and span["relation"] != "selected_text":
                text = span["text"] if edit is None else span["text"].replace("sign", edit)
                return {"extraction_id": span_key[0], "span_id": span_key[1], "quote": text}
        return {"extraction_id": span_key[0], "span_id": span_key[1], "quote": "a passage it was never given"}
    return excerpt
