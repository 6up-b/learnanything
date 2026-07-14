"""ING M7 — sidecar contract wiring for the append / maintenance / exam-readiness /
conflict RPCs. Heavy paths are covered by service tests; here we assert the RPCs
are registered and their envelopes are typed. Codex is unavailable in tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_m7_rpcs_registered(tmp_path: Path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "append_source", "params": {"sourceSetId": "missing_set"}},
            {"jsonrpc": "2.0", "id": 3, "method": "maintenance_feed", "params": {}},
            {"jsonrpc": "2.0", "id": 4, "method": "exam_readiness", "params": {}},
            {"jsonrpc": "2.0", "id": 5, "method": "list_source_conflicts", "params": {}},
        ]
    )
    methods = results[0]["result"]["capabilities"]["methods"]
    for name in ["append_source", "refresh_revision", "maintenance_feed", "exam_readiness",
                 "list_source_conflicts", "resolve_source_conflict", "maintenance_notice_action"]:
        assert name in methods, f"{name} not registered"
    # unknown source set -> typed refusal.
    assert results[1]["error"]["data"]["code"] == "source_set_not_found"
    # maintenance feed + exam readiness + conflicts work without codex.
    assert "notices" in results[2]["result"]
    assert results[3]["result"]["report"]["displayRule"] == "ready_vs_demonstrated"
    assert results[4]["result"]["conflicts"] == []


def test_list_source_conflicts_enriches_extraction_ids(tmp_path: Path):
    """A seeded conflict comes back with each side's extraction id resolved from
    its cited revision, so the client can open both spans via get_span_view."""

    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    from tests.test_source_inventory import _block, _ir, _persist, _register_revision

    clock = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repo = Repository(VaultPaths(vault_root, loaded.config).sqlite_path)
    _register_revision(repo, source_id="src_l", revision_id="rev_l")
    ir = _ir([("u1", "Unit", [_block("s1", "left claim text")], "sha256:l", 1)])
    _persist(repo, ir, revision_id="rev_l", extraction_id="ext_l")
    repo.insert_source_conflict(
        entity_type="facet", entity_id="facet_x", statement="disagree",
        left_source_id="src_l", left_revision_id="rev_l", left_locator="span:s1",
        right_source_id="src_r", right_revision_id="rev_missing", right_locator="span:s9",
        clock=clock,
    )

    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "list_source_conflicts", "params": {}},
        ]
    )
    conflicts = results[1]["result"]["conflicts"]
    assert len(conflicts) == 1
    # left resolves to its completed extraction; right (unknown revision) is null.
    assert conflicts[0]["leftExtractionId"] == "ext_l"
    assert conflicts[0]["rightExtractionId"] is None
