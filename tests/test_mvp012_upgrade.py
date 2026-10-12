"""mvp-0.12 (daily-loop DL1, ``daily_plan_v1``) is the next explicit successor.

mvp-0.9 -> mvp-0.10 (the split) -> mvp-0.11 (placement) -> mvp-0.12 (the finite
daily plan). The upgrade accepts mvp-0.11, or mvp-0.10 / mvp-0.9 by running the
earlier links first. It changes serving only: the projection namespace is the
same, the plan tables start empty, and nothing is rewritten.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    DAILY_PLAN_ALGORITHM_VERSION,
    DAILY_PLAN_VERSIONS,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
)
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, effective_defaults_fingerprint
from learnloop.daily_plan.engine import plan_active
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.ops.vault_upgrade import upgrade_to_mvp012
from learnloop.placement.state import placement_active
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_174"
CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))


def test_the_plan_successor_keeps_the_split_placement_and_the_p0_namespace():
    assert DAILY_PLAN_ALGORITHM_VERSION == "mvp-0.12"
    assert LATEST_ALGORITHM_VERSION == "mvp-0.12"
    assert DAILY_PLAN_VERSIONS == frozenset({"mvp-0.12"})
    for versions in (P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS, PLACEMENT_VERSIONS):
        assert DAILY_PLAN_ALGORITHM_VERSION in versions


def test_the_plan_serves_only_at_the_successor_with_the_switch_on(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {"mvp-0.9": (False, False, False), "mvp-0.11": (True, True, False), "mvp-0.12": (True, True, True)}
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (split_grading_active(vault), placement_active(vault), plan_active(vault)) == flags, version
    append_config_toml(paths.root, "[plan]\nenabled = false\n")
    assert plan_active(load_vault(paths.root)) is False


def _plan_rows(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT COUNT(*) FROM daily_plans").fetchone()[0]


def test_upgrade_from_mvp011_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.11")
    repository = Repository(paths.sqlite_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
    result = upgrade_to_mvp012(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.11", "mvp-0.12")
    upgraded = load_vault(paths.root)
    assert plan_active(upgraded) and placement_active(upgraded) and split_grading_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.12"
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert _plan_rows(paths.sqlite_path) == 0
    assert "mvp-0.11" in manifests


def test_upgrade_chains_from_mvp09(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    result = upgrade_to_mvp012(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.9", "mvp-0.12")
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-3:] == ["mvp-0.10", "mvp-0.11", "mvp-0.12"]


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp012(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.11'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.12")
    already = upgrade_to_mvp012(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.12"]


def test_upgrade_command_defaults_to_mvp012(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.11")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert "mvp-0.11 -> mvp-0.12" in result.output


def test_new_vaults_stay_at_mvp09_without_the_plan(tmp_path):
    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == "mvp-0.9"
    assert not plan_active(fresh)


def test_defaults_fingerprint_is_recorded_for_the_plan_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig
    from learnloop.config.template import DEFAULT_CONFIG_TEXT

    text = DEFAULT_CONFIG_TEXT.replace('algorithm_version = "mvp-0.9"', 'algorithm_version = "mvp-0.12"')
    config = LearnLoopConfig.model_validate(tomllib.loads(text))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.12"]
    assert config.plan.enabled is True and config.plan.default_minutes == 25


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: the chained upgrade, FK
    check, doctor, and an idempotent rebuild that never touches plan rows."""

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
        if issue.severity == "error" and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan"))
    ]
    assert errors == []
    derived = set(tables_for_role(TableRole.DERIVED))
    assert "daily_plans" not in derived

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {
                table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                for table in sorted(derived)
            }

    # The first rebuild after an upgrade reaches the fixed point (as for
    # mvp-0.11); from the second on, rebuilds are idempotent.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second
