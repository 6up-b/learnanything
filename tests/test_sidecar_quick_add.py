"""Sidecar contract for Quick add (spec_source_ingestion_v2 §1)."""

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
from learnloop.ingest.resolution import resolve_source
from learnloop.ingest.source_library import register_source_revision
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))
_MD = "# Vectors\nA vector is an element of a vector space.\n\n# Exercises\nProblem 1. Prove it.\n"


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


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


def test_plan_quick_add_registered_and_single_confirmation(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    md = tmp_path / "book.md"
    md.write_text(_MD)
    _seed_extraction(paths.sqlite_path, str(md))

    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "plan_quick_add",
             "params": {"source": str(md), "subjectId": "linear-algebra"}},
        ]
    )
    init = results[0]["result"]
    assert "plan_quick_add" in init["capabilities"]["methods"]
    assert "confirm_quick_add" in init["capabilities"]["methods"]

    plan = results[1]["result"]["plan"]
    assert plan["extractionId"] == "ext_qa"
    assert plan["suggestedRole"] == "reference"
    assert plan["roleAmbiguous"] is True  # textfile category proceeds flagged
    assert plan["selectedUnitIds"]
    # The state machine surfaces exactly one confirmation checkpoint.
    assert plan["confirmation"]["id"] == "quick_add_confirm"  # a value, not camelized
    assert plan["confirmation"]["requiresExternalAi"] is True


def test_plan_quick_add_requires_import_when_not_extracted(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "plan_quick_add",
             "params": {"source": "https://arxiv.org/abs/2401.00001", "subjectId": "linear-algebra"}},
        ]
    )
    error = results[1]["error"]["data"]
    assert error["code"] == "quick_add_requires_import"
    assert error["retryable"] is True


def test_confirm_quick_add_unknown_subject_typed_error(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    md = tmp_path / "book.md"
    md.write_text(_MD)
    _seed_extraction(paths.sqlite_path, str(md))
    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "confirm_quick_add",
             "params": {
                 "source": str(md),
                 "subjectId": "no-such-subject",
                 "inventoryOutputTokens": 45_000,
             }},
        ]
    )
    # 45k is accepted by the request schema; validation reaches the handler and
    # reports the deliberately unknown subject instead of generic Invalid params.
    assert results[1]["error"]["data"]["code"] == "unknown_subject"
