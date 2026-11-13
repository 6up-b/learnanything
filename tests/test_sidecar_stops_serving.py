"""A desktop sidecar already bound to a vault stops serving it when the vault becomes unservable: a reload refused
below the oldest supported tag (ADR-019), or an activation journal another process leaves beside its database.
Handlers (``require_vault``), the post-attempt worker (its supplier) and background jobs (the loaded-vault
provider's admission) are refused until a load of the vault succeeds. No model call.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from learnloop.activation_journal import journal_path
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, OLDEST_SUPPORTED, SUCCESSOR_CHAIN
from learnloop.version_floor import BelowOldestSupported
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.server import _handle

from tests.helpers import create_basic_vault

BELOW = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED) - 1]


def _retag(root: Path, tag: str) -> None:
    path = root / "learnloop.toml"
    text, count = re.subn(r'algorithm_version = "[^"]+"', f'algorithm_version = "{tag}"', path.read_text("utf-8"),
                          count=1)
    assert count == 1
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def bound(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(paths.root, maintenance=False)
    assert context.app_snapshot()["vault"]
    yield paths, context
    context.close()


def _rpc(context: SidecarContext, method: str) -> dict:
    return _handle(context, {"jsonrpc": "2.0", "id": 1, "method": method, "params": {}})


def _assert_refused(context: SidecarContext, code: str) -> None:
    generation = context.loaded_vault.generation()
    with pytest.raises(SidecarError) as refused:
        context.app_snapshot()
    assert refused.value.code == code
    assert _rpc(context, "load_vault")["error"]["data"]["code"] == code
    # The worker gets no vault, and a background job's admission of its snapshot fails.
    assert context._worker_target() is None
    assert not context.loaded_vault.admit(generation)


def test_a_reload_refused_below_the_floor_stops_serving_until_a_load_succeeds(bound):
    paths, context = bound
    _retag(paths.root, BELOW)

    response = _rpc(context, "reload_vault")
    assert response["error"]["data"]["code"] == "vault_below_oldest_supported"
    assert OLDEST_SUPPORTED in response["error"]["message"]
    _assert_refused(context, "vault_below_oldest_supported")

    # Still refused while the file stays below the floor.
    with pytest.raises(BelowOldestSupported):
        context.reload(maintenance=False)
    _assert_refused(context, "vault_below_oldest_supported")

    _retag(paths.root, LATEST_ALGORITHM_VERSION)
    assert "result" in _rpc(context, "reload_vault")
    assert context.app_snapshot()["vault"] and context._worker_target() is not None


def test_a_journal_that_appears_while_bound_stops_serving_until_a_load_succeeds(bound):
    paths, context = bound
    journal = journal_path(paths.sqlite_path)
    # Another process's upgrade, published or still running: this context's vault is the predecessor's.
    journal.write_text(json.dumps({"predecessor": OLDEST_SUPPORTED, "target": LATEST_ALGORITHM_VERSION}),
                       encoding="utf-8")
    _assert_refused(context, "vault_upgrade_unfinished")

    # The other process finishes: the journal goes, but the vault this context holds is still the old one.
    journal.unlink()
    _assert_refused(context, "vault_upgrade_unfinished")

    # A watched file change is the moment a load is tried; it succeeds, and the vault is served again.
    result = context.refresh_vault_files(["learnloop.toml"], expected_root=paths.root)
    assert result["mode"] == "full" and result["snapshot"]["vault"]
    assert context.app_snapshot()["vault"] and context._worker_target() is not None
