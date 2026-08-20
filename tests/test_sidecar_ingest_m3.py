"""Sidecar contract for ING M3: outline, unit selection, acquisition preview,
build plan, and consent-gated extraction repair (spec_source_ingestion_v2 §5.7)."""

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
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _seed_extraction(sqlite_path: Path) -> tuple[str, str]:
    repo = Repository(sqlite_path)
    reg = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri="file:///book.md", raw_bytes=_MD.encode(), original_uri="file:///book.md", clock=_CLOCK
    )
    ir = markdown_to_ir(_MD, title="Book", extractor_name="text")
    request_hash = extraction_request_hash(
        revision_id=reg.revision_id, extractor="text", extractor_version="1", ir_schema_version=IR_SCHEMA_VERSION
    )
    repo.insert_extraction_run(
        id="ext_sc", revision_id=reg.revision_id, extractor="text", extractor_version="1",
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, status="running", clock=_CLOCK,
    )
    repo.persist_document_ir("ext_sc", ir)
    repo.complete_extraction_run("ext_sc", extraction_result_hash=extraction_result_hash(request_hash, ir), clock=_CLOCK)
    return reg.revision_id, "ext_sc"


def test_get_source_outline_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _revision_id, extraction_id = _seed_extraction(paths.sqlite_path)

    outline = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_source_outline", "params": {"extractionRef": extraction_id}},
        ]
    )[1]["result"]

    assert outline["extractionId"] == extraction_id
    assert outline["unitCount"] >= 2
    assert outline["units"][0]["structuralSignals"] is not None
    assert "selection" in outline


def test_save_unit_selection_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _revision_id, extraction_id = _seed_extraction(paths.sqlite_path)

    saved = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "save_unit_selection",
                "params": {"extractionId": extraction_id, "selectedUnitIds": ["u1"]},
            },
        ]
    )[1]["result"]
    assert saved["selectedUnitIds"] == ["u1"]


def test_get_acquisition_preview_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    preview = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_acquisition_preview",
                "params": {"inputs": ["https://arxiv.org/abs/2401.00001", "@@bad@@"]},
            },
        ]
    )[1]["result"]
    assert preview["summary"]["inputCount"] == 2
    assert preview["summary"]["recognizedCount"] == 1


def test_get_build_plan_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _revision_id, extraction_id = _seed_extraction(paths.sqlite_path)

    plan = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_build_plan",
                "params": {"selections": [{"extractionId": extraction_id, "selectedUnitIds": []}]},
            },
        ]
    )[1]["result"]
    assert plan["routing"] in {"create", "update"}
    assert plan["stages"]
    assert plan["totals"]["calls"] >= 1


def test_start_extraction_repair_requires_consent_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    revision_id, _extraction_id = _seed_extraction(paths.sqlite_path)

    response = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_extraction_repair",
                "params": {"revisionId": revision_id, "pages": ["1"], "consent": {}},
            },
        ]
    )[1]
    assert response["error"]["data"]["code"] == "consent_required"


# --------------------------------------------------------------------------
# ING M4: source-set CRUD + coverage over the sidecar (§4.3/§9.3)
# --------------------------------------------------------------------------


def test_source_set_crud_and_coverage_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _revision_id, extraction_id = _seed_extraction(paths.sqlite_path)

    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "upsert_source_set",
                "params": {
                    "id": "set_sc",
                    "subjectId": "linear-algebra",
                    "title": "Sidecar Set",
                    "members": [
                        {
                            "sourceId": "src_book",
                            "revisionId": _revision_id,
                            "defaultRole": "primary_textbook",
                            "scope": [{"unitId": "u1", "roleOverride": None}],
                            "priority": 1,
                        }
                    ],
                },
            },
            {"jsonrpc": "2.0", "id": 3, "method": "list_source_sets", "params": {}},
            {"jsonrpc": "2.0", "id": 4, "method": "get_source_coverage", "params": {"sourceSetId": "set_sc"}},
        ]
    )
    created = results[1]["result"]["sourceSet"]
    assert created["id"] == "set_sc"
    assert created["members"][0]["defaultRole"] == "primary_textbook"

    listing = results[2]["result"]["sourceSets"]
    assert any(row["id"] == "set_sc" for row in listing)

    coverage = results[3]["result"]["coverage"]
    assert coverage["sourceSetId"] == "set_sc"
    assert coverage["curriculumLinkageSeam"] == "entity_source_links_m5_m6"


def test_start_inventory_over_sidecar(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _revision_id, extraction_id = _seed_extraction(paths.sqlite_path)

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_inventory",
                "params": {
                    "extractionRef": extraction_id,
                    "units": [{"unitId": "u1", "role": "reference", "profile": "semantic"}],
                },
            },
        ]
    )[1]
    # The batch is enqueued (a real codex provider is absent, so the job will fail
    # cleanly when drained — enqueue itself must succeed with a batch id).
    assert "result" in result
    assert result["result"]["id"].startswith("batch_")
