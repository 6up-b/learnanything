"""list_vault_epigraphs sidecar contract: newest first, subject filter, limit clamp."""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _seed(vault_root: Path) -> None:
    repo = Repository(vault_root / "state.sqlite")
    for tick, subject in enumerate(("linear-algebra", "other")):
        clock = FrozenClock(datetime(2026, 9, 3, 12, tick, 0, tzinfo=UTC))
        repo.insert_vault_epigraphs(
            subject_id=subject, source_set_id="set_1", synthesis_run_id=f"run_{subject}", mode="append",
            epigraphs=[{"kind": "quote", "text": f"{subject} {i}"} for i in range(6)]
            + [{"kind": "haiku", "text": "one\ntwo\nthree"}],
            prompt_version="mvp-0.1-vault-epigraphs", provider="fake", model="fake-model", clock=clock,
        )


def test_list_vault_epigraphs_registered_newest_first_and_camel_cased(tmp_path: Path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    _seed(vault_root)

    results = _rpc([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
        {"jsonrpc": "2.0", "id": 2, "method": "list_vault_epigraphs", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "list_vault_epigraphs", "params": {"subjectId": "other", "limit": 2}},
        {"jsonrpc": "2.0", "id": 4, "method": "list_vault_epigraphs", "params": {"limit": 0}},
    ])

    assert "list_vault_epigraphs" in results[0]["result"]["capabilities"]["methods"]
    default = results[1]["result"]
    assert default["version"] == 1
    assert len(default["epigraphs"]) == 12  # 14 seeded, default limit 12
    first = default["epigraphs"][0]
    assert first["subjectId"] == "other"  # the later batch comes first
    assert first["kind"] == "haiku"
    assert first["lines"] == ["one", "two", "three"]
    assert first["synthesisRunId"] == "run_other"
    assert first["promptVersion"] == "mvp-0.1-vault-epigraphs"
    assert first["createdAt"].startswith("2026-09-03T12:01:00")

    filtered = results[2]["result"]["epigraphs"]
    assert len(filtered) == 2
    assert {row["subjectId"] for row in filtered} == {"other"}

    assert len(results[3]["result"]["epigraphs"]) == 1  # limit clamps to >= 1


def test_list_vault_epigraphs_requires_a_loaded_vault():
    results = _rpc([{"jsonrpc": "2.0", "id": 1, "method": "list_vault_epigraphs", "params": {}}])
    assert results[0]["error"]["data"]["code"] == "vault_not_loaded"
