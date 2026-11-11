"""What other test files use from ``tests/test_ux_phase1_round2_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.sources.source_outline import resolve_extraction_id

from tests.ux_phase1_add_source_helpers import _draining_ctx, call
from tests.ux_phase1_support import fresh_library, grant_consent, write_book


def _added_book(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    return root, ctx, source_id, resolve_extraction_id(ctx.repository, source_id)


_WORDS = " ".join(f"word{i}" for i in range(240))
_BOOK_WITH_CONTENTS = "\n\n".join(
    [
        "# Contents",
        "1 Vectors. 2 Matrices. 3 Maps. " + _WORDS,
        "# 1 Vectors",
        _WORDS,
        "# 2 Matrices",
        _WORDS + "\n\n" + _WORDS,
        "# 3 Maps",
        _WORDS,
    ]
) + "\n"


def _seed_book(paths) -> str:
    import json
    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.content.sources.source_library import register_source_revision
    from learnloop.db.repositories import Repository
    from learnloop.ingest.extractors.normalizers import markdown_to_ir
    from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
    from learnloop.ingest.ir import IR_SCHEMA_VERSION

    clock = FrozenClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))
    repo = Repository(paths.sqlite_path)
    registered = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri="file:///book.md", raw_bytes=_BOOK_WITH_CONTENTS.encode(),
        original_uri="file:///book.md", clock=clock,
    )
    ir = markdown_to_ir(_BOOK_WITH_CONTENTS, title="Book", extractor_name="text")
    request_hash = extraction_request_hash(
        revision_id=registered.revision_id, extractor="text", extractor_version="1", ir_schema_version=IR_SCHEMA_VERSION
    )
    repo.insert_extraction_run(
        id="ext_book", revision_id=registered.revision_id, extractor="text", extractor_version="1",
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=clock,
    )
    repo.persist_document_ir("ext_book", ir)
    repo.complete_extraction_run("ext_book", extraction_result_hash=extraction_result_hash(request_hash, ir), clock=clock)
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO synthesis_manifests(id, manifest_hash, extraction_ids_json, brief_json, created_at) VALUES (?, ?, ?, ?, ?)",
            ("man_1", "hash_1", json.dumps(["ext_book"]), json.dumps({"practice_items": "as_you_read"}), "2026-10-01T09:00:00Z"),
        )
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) "
            "VALUES ('run_1', 'man_1', 'bootstrap', 'completed', ?, ?)",
            ("2026-10-01T09:00:00Z", "2026-10-01T09:05:00Z"),
        )
        connection.commit()
    return "ext_book"


def _section_ids(repo, extraction_id):
    """Section ids by label (Markdown labels are heading slugs)."""

    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir(extraction_id))
    return {str(row["label"]): str(row["id"]) for row in rows}


def _imported_book(tmp_path):
    """A book imported through Ingest (no automatic build)."""

    root = fresh_library(tmp_path)
    ctx = _draining_ctx(root)
    call(ctx, "start_import_batch", {"sources": [str(write_book(tmp_path))]})
    card = call(ctx, "get_source_library", {})["sources"][0]
    return root, ctx, card
