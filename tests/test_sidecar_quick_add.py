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


class _RecordingQuickAddJobs:
    """Records the Quick-add enqueue without running a job."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def enqueue_quick_add_build(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return "batch_quick"

    def get_batch(self, batch_id: str) -> dict:
        return {"id": batch_id, "jobs": []}


def _confirm(tmp_path, **params) -> list[dict]:
    from types import SimpleNamespace

    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.handlers.ingest import ConfirmQuickAddInput, confirm_quick_add_rpc

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    md = tmp_path / "book.md"
    md.write_text(_MD)
    _seed_extraction(paths.sqlite_path, str(md))
    vault, repo = load_vault(vault_root), Repository(paths.sqlite_path)
    jobs = _RecordingQuickAddJobs()
    ctx = SimpleNamespace(require_vault=lambda: (vault, repo), ingest_jobs=jobs, reload=lambda **_: None)
    confirm_quick_add_rpc(ctx, ConfirmQuickAddInput.model_validate(
        {"source": str(md), "subjectId": "linear-algebra", **params}
    ))
    return jobs.calls


def test_confirm_quick_add_forwards_the_exam_goal_flag(tmp_path):
    calls = _confirm(tmp_path, brief={"outcome": "exam_prep", "dueAt": "2026-11-28T04:59:59.000Z"}, createGoal=True)

    assert len(calls) == 1
    assert calls[0]["create_goal"] is True
    assert calls[0]["brief"]["due_at"] == "2026-11-28T04:59:59.000Z"


def test_confirm_quick_add_without_the_flag_asks_for_no_goal(tmp_path):
    (call,) = _confirm(tmp_path)
    assert call["create_goal"] is False
