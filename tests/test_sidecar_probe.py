"""Sidecar probe-episode contract (spec_probe_eig_redesign.md §5.8/§12)."""

from __future__ import annotations

import io
import json

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_episodes import enter_episode
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_probe_contract_inactive_without_episode(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_probe_contract",
                "params": {"practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]

    # The sync-opened episode has no admitted instrument, so it parks in
    # pending_items and the item serves as ordinary practice.
    assert result["active"] is False


def test_probe_contract_requires_grading_provider_and_parks_episode(tmp_path):
    # §5.8: under a manual/self-grading provider no qualifying observation may
    # be SERVED — the contract refuses and the episode parks (test 33, serve side).
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    loaded = load_vault(vault_root)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert episode.status == "in_progress"

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_probe_contract",
                "params": {"practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]

    assert result["active"] is False
    assert result["reason"] == "grading_provider_unavailable"
    assert repository.probe_episode(episode.id).status == "pending_items"


def test_stop_probe_diagnosing_converts_episode(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    loaded = load_vault(vault_root)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "stop_probe_diagnosing",
                "params": {"practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]

    assert result["stopped"] is True
    assert result["decision"]["tutorMove"] in ("elicit_reasoning", "localize_error")
    refreshed = repository.probe_episode(episode.id)
    assert refreshed.status == "converted_to_tutoring"
    segments = repository.state_segments_for_learning_object("lo_svd_definition")
    assert segments[-1].reason == "tutoring_transition"
