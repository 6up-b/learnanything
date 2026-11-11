"""What other test files use from ``tests/test_daily_plan_reading.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import learnloop.clock as clock_module
from learnloop.clock import FrozenClock
from learnloop.content.sources.source_library import register_source_revision
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION


DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
_SECTION_ONE = " ".join(f"word{i}" for i in range(1200))  # 10 minutes at 120 wpm
_SECTION_TWO = " ".join(f"term{i}" for i in range(3000))  # 25 minutes
_MD = f"# Vectors\n{_SECTION_ONE}\n\n# Matrices\n{_SECTION_TWO}\n"


class _Clock:
    def __init__(self, monkeypatch, start):
        self.moment = start
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: self.moment)

    def advance(self, **delta):
        self.moment += timedelta(**delta)


def _seed_as_you_read(paths, *, brief_mode="as_you_read") -> str:
    clock = FrozenClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))
    repo = Repository(paths.sqlite_path)
    registered = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri="file:///book.md", raw_bytes=_MD.encode(),
        original_uri="file:///book.md", clock=clock,
    )
    ir = markdown_to_ir(_MD, title="Book", extractor_name="text")
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
            ("man_1", "hash_1", json.dumps(["ext_book"]), json.dumps({"practice_items": brief_mode}), "2026-10-01T09:00:00Z"),
        )
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) VALUES ('run_1', 'man_1', 'bootstrap', 'completed', ?, ?)",
            ("2026-10-01T09:00:00Z", "2026-10-01T09:05:00Z"),
        )
        connection.commit()
    return "ext_book"


def _sections(repo, extraction_id):
    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir(extraction_id))
    return rows
