"""mvp-0.10 (learner field F2) is an explicit immediate-successor upgrade."""

from __future__ import annotations

import sqlite3

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    P0_PROJECTION_VERSIONS,
    PLACEMENT_ALGORITHM_VERSION,
    PLACEMENT_VERSIONS,
)
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import upgrade_to_mvp010
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault, set_algorithm_version


def test_placement_successor_keeps_the_p0_projection_namespace():
    assert PLACEMENT_ALGORITHM_VERSION == "mvp-0.10"
    assert PLACEMENT_ALGORITHM_VERSION in P0_PROJECTION_VERSIONS
    assert PLACEMENT_ALGORITHM_VERSION in CANONICAL_STATE_VERSIONS
    assert PLACEMENT_VERSIONS == frozenset({"mvp-0.10"})


def test_upgrade_flips_rebuilds_and_preserves_history_and_open_episodes(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    episodes_before = sorted((lo, e.id, e.trigger) for lo, e in repository.open_probe_episodes().items())
    assert episodes_before  # mvp-0.9 opened its initial episodes
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()

    result = upgrade_to_mvp010(paths.root, clock=FrozenClock(NOW))

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.9", "mvp-0.10")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.10"
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.10"
    # Nothing is rewritten; an opening episode already open stays open, so the
    # kill switch can restore it exactly.
    assert sorted((lo, e.id, e.trigger) for lo, e in repository.open_probe_episodes().items()) == episodes_before
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT COUNT(*) FROM assumption_decisions").fetchone() == (0,)


def test_upgrade_is_immediate_successor_only(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp010(paths.root, clock=FrozenClock(NOW))
    assert refused.upgraded is False
    assert "only 'mvp-0.9'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"

    set_algorithm_version(paths, "mvp-0.10")
    already = upgrade_to_mvp010(paths.root, clock=FrozenClock(NOW))
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.10"]


def test_upgrade_command_defaults_to_mvp010(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert "mvp-0.9 -> mvp-0.10" in result.output
