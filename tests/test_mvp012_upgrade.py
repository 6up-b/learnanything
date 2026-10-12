"""mvp-0.12 (router R1's probe-tie admission) is an explicit successor upgrade.

The linear chain is mvp-0.9 -> mvp-0.10 (the blind-grading/diagnosis split) ->
mvp-0.11 (placement) -> mvp-0.12 (probe near-ties join the Today queue's
seeded epsilon tie-break, with a logged propensity). The upgrade accepts
mvp-0.11, or mvp-0.9 / mvp-0.10 by running the mvp-0.11 upgrade first.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    PROBE_TIE_ALGORITHM_VERSION,
    PROBE_TIE_VERSIONS,
)
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, effective_defaults_fingerprint
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.ops.vault_upgrade import upgrade_to_mvp012
from learnloop.placement.state import placement_active
from learnloop.scheduling.scheduler import probe_ties_admitted
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault, set_algorithm_version

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_176"
CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_probe_tie_successor_keeps_the_chain_and_the_p0_projection_namespace():
    assert PROBE_TIE_ALGORITHM_VERSION == "mvp-0.12" == LATEST_ALGORITHM_VERSION
    assert PROBE_TIE_ALGORITHM_VERSION in P0_SUCCESSOR_VERSIONS
    assert PROBE_TIE_ALGORITHM_VERSION in P0_PROJECTION_VERSIONS
    assert PROBE_TIE_ALGORITHM_VERSION in CANONICAL_STATE_VERSIONS
    # Linear: mvp-0.12 keeps the split and placement, and only it admits ties.
    assert PROBE_TIE_ALGORITHM_VERSION in DIAGNOSIS_SPLIT_VERSIONS
    assert PROBE_TIE_ALGORITHM_VERSION in PLACEMENT_VERSIONS
    assert PROBE_TIE_VERSIONS == frozenset({"mvp-0.12"})


def test_each_version_activates_exactly_its_features(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False, False),
        "mvp-0.10": (True, False, False),
        "mvp-0.11": (True, True, False),
        "mvp-0.12": (True, True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (split_grading_active(vault), placement_active(vault), probe_ties_admitted(vault.config)) == flags


def test_upgrade_from_mvp011_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.11")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()

    result = upgrade_to_mvp012(paths.root, clock=FrozenClock(NOW))

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.11", "mvp-0.12")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.12"
    assert probe_ties_admitted(upgraded.config) and placement_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.12"
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.11" in manifests


def test_upgrade_from_mvp09_chains_through_the_split_and_placement(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    result = upgrade_to_mvp012(paths.root, clock=FrozenClock(NOW))
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.9", "mvp-0.12")
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert {"mvp-0.9", "mvp-0.10", "mvp-0.11"} <= manifests
    assert rebuilds[-3:] == ["mvp-0.10", "mvp-0.11", "mvp-0.12"]


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp012(paths.root, clock=FrozenClock(NOW))
    assert refused.upgraded is False
    assert "only 'mvp-0.11'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"

    set_algorithm_version(paths, "mvp-0.12")
    already = upgrade_to_mvp012(paths.root, clock=FrozenClock(NOW))
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.12"]


def test_upgrade_command_defaults_to_mvp012(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.11")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert "mvp-0.11 -> mvp-0.12" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.12"


def test_defaults_fingerprint_is_recorded_for_the_probe_tie_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig
    from learnloop.config.template import DEFAULT_CONFIG_TEXT

    text = DEFAULT_CONFIG_TEXT.replace('algorithm_version = "mvp-0.9"', 'algorithm_version = "mvp-0.12"')
    config = LearnLoopConfig.model_validate(tomllib.loads(text))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.12"]
    assert config.router.log_decisions is True and config.router.probe_tie_admission is True


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: the chained upgrade, FK
    check, doctor, and an idempotent rebuild (router_outcomes included)."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.9")
    result = upgrade_to_mvp012(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error" and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "router"))
    ]
    assert errors == []
    derived = set(tables_for_role(TableRole.DERIVED))
    assert "router_outcomes" in derived

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {
                table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                for table in sorted(derived)
            }

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second
