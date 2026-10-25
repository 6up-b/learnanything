"""G9 on backup-API copies of the tracked working fixtures.

With ``placement.enabled = false`` an ``mvp-0.11`` vault opens the same initial
episodes and serves the same queue, in the same order, as its predecessors in the
chain, ``mvp-0.10`` and ``mvp-0.9``; so does ``placement.initial_probes = true``.
With placement on, sync opens no opening episode and the episodes these copies
already carry are kept (never rewritten or closed), but the unanswered ones are
ignored (owner decision 2026-10-12): their never-practised LOs start as learning.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.copies import copy_tree_with_databases
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository

from tests.owner_vaults import owner_vault, working_vault_params
from tests.helpers import append_config_toml, set_algorithm_version

# The owner's working vaults: backup-API copies in the owner_vaults lane (S0).
WORKING_FIXTURES = working_vault_params()
MOMENT = FrozenClock(datetime(2026, 10, 12, 9, 30, tzinfo=UTC))


def _copy(tmp_path, fixture, name, *, version, placement_toml=None, sync=True):
    root = tmp_path / name
    copy_tree_with_databases(owner_vault(fixture), root)
    paths = type("Paths", (), {"root": root})()
    set_algorithm_version(paths, version)
    if placement_toml:
        append_config_toml(root, placement_toml)
    vault = load_vault(root)
    repository = open_vault_repository(root, root / vault.config.storage.sqlite_path)
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
    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    baseline = _fingerprint(*_copy(tmp_path, fixture, "baseline", version="mvp-0.9"))
    # The split (mvp-0.10) changes grading, not serving: same queue.
    assert _fingerprint(*_copy(tmp_path, fixture, "split", version="mvp-0.10")) == baseline
    switched_off = _fingerprint(*_copy(
        tmp_path, fixture, "off", version="mvp-0.11", placement_toml="[placement]\nenabled = false\n",
    ))
    assert switched_off == baseline

    # The narrower switch (opening probes back, placement otherwise on) serves
    # the predecessor's opening episodes again, exactly.
    initial_probes = _fingerprint(*_copy(
        tmp_path, fixture, "initial_probes", version="mvp-0.11",
        placement_toml="[placement]\ninitial_probes = true\n",
    ))
    assert initial_probes == baseline


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_placement_ignores_unanswered_opening_episodes_on_fixture_copies(tmp_path, fixture):
    """Owner decision 2026-10-12 (Phase 6 open question 1): the opening
    episodes earlier versions opened, all still unanswered on these copies, are
    kept as they are but ignored while placement serves, so the copies' never-
    practised LOs start as learning (new material) instead of waiting behind
    an opening probe."""

    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    from learnloop.placement.state import ignored_opening_episode_ids

    baseline_vault, baseline_repository = _copy(tmp_path, fixture, "baseline", version="mvp-0.10")
    baseline_queue = build_due_queue(baseline_vault, baseline_repository, clock=MOMENT, persist_explanations=False)
    on_vault, on_repository = _copy(tmp_path, fixture, "on", version="mvp-0.11", sync=False)
    before = {lo: (episode.id, episode.status) for lo, episode in on_repository.open_probe_episodes().items()}
    sync_vault_state(on_vault, on_repository, clock=MOMENT)
    # Nothing is rewritten or closed: the same episodes, in the same state.
    assert {lo: (e.id, e.status) for lo, e in on_repository.open_probe_episodes().items()} == before
    ignored = ignored_opening_episode_ids(on_vault, on_repository)
    assert ignored and ignored == {
        e.id for e in on_repository.open_probe_episodes().values() if e.trigger == "initial"
    }

    queue = build_due_queue(on_vault, on_repository, clock=MOMENT, persist_explanations=False)
    mastery = on_repository.mastery_states()
    never_practised = {
        lo for lo, learning_object in on_vault.learning_objects.items()
        if learning_object.status == "active"
        and (mastery.get(lo) is None or mastery[lo].last_evidence_at is None)
    }
    # Every never-practised LO the predecessor served (behind its opening
    # episode) now starts as learning; nothing else is new material.
    served_before = {s.learning_object_id for s in baseline_queue} & never_practised
    new_material = {s.learning_object_id for s in queue if s.components.get("new_material")}
    assert served_before and new_material == served_before
    assert all(
        "new material: starts as learning, no opening probe" in s.plain_english
        for s in queue if s.components.get("new_material")
    )
    # The serving change is the opening probe's admission only: the same items.
    assert sorted(s.practice_item_id for s in queue) == sorted(s.practice_item_id for s in baseline_queue)
