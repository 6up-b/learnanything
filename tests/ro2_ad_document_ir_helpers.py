"""What other test files use from ``tests/test_ro2_ad_document_ir.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3


SERVED = "2026-10-12T09:00:00Z"


def _textbook_with_span_question(tmp_path, version: str):
    """The textbook fake, one LO citing a span of ``ext_text`` in its provenance, and a Reader question
    anchored to that span (``span:ext_text/<span>``, as the Reader writes it)."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from tests.helpers import set_algorithm_version
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    unit, span_ids = next(iter(spans.items()))
    span = span_ids[-1]
    lo_path = paths.learning_object_path("linear-algebra", "lo_matrices")
    lo = read_yaml(lo_path)
    provenance = dict(lo.get("provenance") or {})
    provenance["source_refs"] = [*(provenance.get("source_refs") or []), {
        "ref_type": "canonical_source", "ref_id": "src_text", "source_id": "src_text", "extraction_id": "ext_text",
        "locator": f"span:ext_text/{span}", "span_ids": [span]}]
    lo["provenance"] = provenance
    write_yaml(lo_path, lo)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, note_id, question_md, answer_status, answered_at, resolution, "
            "created_at) VALUES ('qe_span', 'reader', ?, 'Why does this hold?', 'answered', ?, 'open', ?)",
            (f"span:ext_text/{span}", "2026-10-11T09:05:00Z", "2026-10-11T09:00:00Z"))
    return paths, repository, "ext_text", span, unit
