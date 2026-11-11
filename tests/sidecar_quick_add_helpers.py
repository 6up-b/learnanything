"""What other test files use from ``tests/test_sidecar_quick_add.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION
from learnloop.ingest.resolution import resolve_source
from learnloop.content.sources.source_library import register_source_revision


_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))
_MD = "# Vectors\nA vector is an element of a vector space.\n\n# Exercises\nProblem 1. Prove it.\n"


def _seed_extraction(sqlite_path: Path, source: str) -> str:
    """Register a source whose canonical URI matches what resolve_source(source)
    produces, so acquisition preview finds it as already-imported."""

    repo = Repository(sqlite_path)
    resolved = resolve_source(source)
    reg = register_source_revision(
        repo, acquisition_kind=resolved.category, canonical_uri=resolved.source,
        raw_bytes=_MD.encode(), original_uri=source, clock=_CLOCK,
    )
    ir = markdown_to_ir(_MD, title="Book", extractor_name="text")
    request_hash = extraction_request_hash(
        revision_id=reg.revision_id, extractor="text", extractor_version="1", ir_schema_version=IR_SCHEMA_VERSION
    )
    repo.insert_extraction_run(
        id="ext_qa", revision_id=reg.revision_id, extractor="text", extractor_version="1",
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=_CLOCK,
    )
    repo.persist_document_ir("ext_qa", ir)
    repo.complete_extraction_run("ext_qa", extraction_result_hash=extraction_result_hash(request_hash, ir), clock=_CLOCK)
    return "ext_qa"
