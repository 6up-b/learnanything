"""G9 on backup-API copies of the tracked working fixtures.

With ``placement.enabled = false`` an ``mvp-0.11`` vault opens the same initial
episodes and serves the same queue, in the same order, as its predecessors in the
chain, ``mvp-0.10`` and ``mvp-0.9``. With the
switch on, sync opens no opening episode; the episodes these copies already
carry are kept, so their queues are unchanged until new material arrives.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, set_algorithm_version

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
WORKING_FIXTURES = ("linear_algebra", "probability", "arxiv_v2")
MOMENT = FrozenClock(datetime(2026, 10, 12, 9, 30, tzinfo=UTC))


def _copy(tmp_path, fixture, name, *, version, placement_toml=None, sync=True):
    root = tmp_path / name
    copy_tree_with_databases(FIXTURES / fixture, root)
    paths = type("Paths", (), {"root": root})()
    set_algorithm_version(paths, version)
    if placement_toml:
        append_config_toml(root, placement_toml)
    vault = load_vault(root)
    repository = Repository(root / vault.config.storage.sqlite_path)
    if sync:
        sync_vault_state(vault, repository, clock=MOMENT)
    return vault, repository


def _fingerprint(vault, repository):
    episodes = sorted(
        (lo, episode.trigger, episode.status)
        for lo, episode in repository.open_probe_episodes().items()
    )
    queue = build_due_queue(vault, repository, clock=MOMENT, persist_explanations=False)
    return episodes, [
        (s.practice_item_id, round(s.priority, 12), sorted((k, round(v, 9)) for k, v in s.components.items()))
        for s in queue
    ]


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_kill_switch_matches_the_predecessor_on_fixture_copies(tmp_path, fixture):
    if not (FIXTURES / fixture / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    baseline = _fingerprint(*_copy(tmp_path, fixture, "baseline", version="mvp-0.9"))
    # The split (mvp-0.10) changes grading, not serving: same queue.
    assert _fingerprint(*_copy(tmp_path, fixture, "split", version="mvp-0.10")) == baseline
    switched_off = _fingerprint(*_copy(
        tmp_path, fixture, "off", version="mvp-0.11", placement_toml="[placement]\nenabled = false\n",
    ))
    assert switched_off == baseline

    # Switched on, sync opens no opening episode. Every LO in these copies
    # already carries one from earlier versions (all pending_items, none
    # observed), and the successor never rewrites them, so the copies serve the
    # predecessor's queue until new material arrives (documented in the review).
    on_vault, on_repository = _copy(tmp_path, fixture, "on", version="mvp-0.11", sync=False)
    before = {lo: episode.id for lo, episode in on_repository.open_probe_episodes().items()}
    sync_vault_state(on_vault, on_repository, clock=MOMENT)
    assert {lo: episode.id for lo, episode in on_repository.open_probe_episodes().items()} == before
    assert _fingerprint(on_vault, on_repository) == baseline
