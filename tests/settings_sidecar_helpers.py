"""What other test files use from ``tests/test_settings_sidecar.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import io
import json

from learnloop_sidecar.server import serve


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _settings_rpc(vault_root, *messages):
    payload = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"vaultPath": str(vault_root)},
        }
    ]
    payload.extend(
        {
            "jsonrpc": "2.0",
            "id": index + 2,
            "method": name,
            "params": params,
        }
        for index, (name, params) in enumerate(messages)
    )
    return _rpc(payload)[1:]
