"""ING M6 — create_study_map sidecar contract wiring.

The heavy synthesis path is covered by tests/test_source_set_synthesis.py; here
we assert the RPC is registered and its error envelope is typed. No AI provider
is available in tests, so the happy path degrades to a typed
``provider_unavailable`` rather than fabricating a study map.
"""

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


def test_create_study_map_registered_and_typed_errors(tmp_path: Path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    results = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "create_study_map", "params": {"sourceSetId": "missing_set"}},
        ]
    )
    init = results[0]["result"]
    assert "create_study_map" in init["capabilities"]["methods"]
    # unknown source set -> typed refusal, not a generic failure.
    assert results[1]["error"]["data"]["code"] == "source_set_not_found"
