"""What other test files use from ``tests/test_sources_merge_composition.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing

from learnloop.db.connection import connect


def _exam_span(repository) -> str:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' AND text LIKE 'Exam question%'"
        ).fetchone()
    assert row is not None
    return str(row[0])
