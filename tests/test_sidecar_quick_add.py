"""Sidecar contract for Quick add (spec_source_ingestion_v2 §1)."""

from __future__ import annotations

import io
import json

from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault
from tests.sidecar_quick_add_helpers import _MD, _seed_extraction

def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


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


def test_plan_quick_add_enrichment_preset_normalizes_at_rpc_boundary(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    md = tmp_path / "interesting-adjunct.md"
    md.write_text(_MD)
    _seed_extraction(paths.sqlite_path, str(md))

    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "plan_quick_add",
                "params": {
                    "source": str(md),
                    "subjectId": "linear-algebra",
                    "brief": {"authoringPreset": "narrow_adjunct"},
                },
            },
        ]
    )

    plan = results[1]["result"]["plan"]
    assert plan["suggestedRole"] == "reference"
    assert plan["roleAmbiguous"] is False
    assert plan["brief"]["authoringPreset"] == "narrow_adjunct"
    assert plan["brief"]["practiceItems"] == "upfront"
    assert "at most one focused learning object" in plan["brief"]["scope"]


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
