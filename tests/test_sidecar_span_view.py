"""Sidecar contract for Open-in-source (spec_source_ingestion_v2 §9.2)."""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION
from learnloop.content.sources.source_library import register_source_revision
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))
_MD = "# Vectors\nA vector is an element of a vector space.\n\n# Exercises\nProblem 1. Prove it.\n"


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _seed(sqlite_path: Path) -> tuple[str, str]:
    repo = Repository(sqlite_path)
    reg = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri="file:///book.md",
        raw_bytes=_MD.encode(), original_uri="file:///book.md", clock=_CLOCK,
    )
    ir = markdown_to_ir(_MD, title="Book", extractor_name="text")
    request_hash = extraction_request_hash(
        revision_id=reg.revision_id, extractor="text", extractor_version="1", ir_schema_version=IR_SCHEMA_VERSION
    )
    repo.insert_extraction_run(
        id="ext_sv", revision_id=reg.revision_id, extractor="text", extractor_version="1",
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=_CLOCK,
    )
    repo.persist_document_ir("ext_sv", ir)
    repo.complete_extraction_run("ext_sv", extraction_result_hash=extraction_result_hash(request_hash, ir), clock=_CLOCK)
    span_id = ir.blocks[0].span_id
    return "ext_sv", span_id


def test_get_span_view_registered_and_records_exposure(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    extraction_id, span_id = _seed(paths.sqlite_path)

    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_span_view",
             "params": {"extractionId": extraction_id, "spanId": span_id,
                        "context": "provenance", "entityType": "facet", "entityId": "facet_x"}},
        ]
    )
    init = results[0]["result"]
    assert "get_span_view" in init["capabilities"]["methods"]
    view = results[1]["result"]["spanView"]
    assert view["spanId"] == span_id
    assert view["locatorScheme"] == "block_span_v1"
    assert view["viewerMode"] in {"pdf_text", "text_anchor"}

    # EVERY view recorded a source_exposure event.
    events = Repository(paths.sqlite_path).source_exposure_events(extraction_id=extraction_id, span_id=span_id)
    assert len(events) == 1
    assert events[0]["context"] == "provenance"
    assert events[0]["entity_id"] == "facet_x"


def test_get_span_view_typed_error(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    extraction_id, _span = _seed(paths.sqlite_path)
    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_span_view",
             "params": {"extractionId": extraction_id, "spanId": "s_missing"}},
        ]
    )
    assert results[1]["error"]["data"]["code"] == "span_not_found"
