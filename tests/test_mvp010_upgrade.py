"""mvp-0.10 (Slice 1 M2) is an explicit, owner-run successor upgrade (§6.2)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
)
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.ops.vault_upgrade import upgrade_to_mvp010
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version
from tests.split_live_helpers import append_config

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_190"
CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_split_version_is_a_p0_successor():
    assert DIAGNOSIS_SPLIT_ALGORITHM_VERSION == "mvp-0.10"
    assert DIAGNOSIS_SPLIT_ALGORITHM_VERSION in P0_SUCCESSOR_VERSIONS
    assert DIAGNOSIS_SPLIT_ALGORITHM_VERSION in P0_PROJECTION_VERSIONS


def test_upgrade_flips_rebuilds_and_preserves_raw_history(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.9")
    repository = Repository(paths.sqlite_path)
    with connect(paths.sqlite_path) as connection:
        before = [tuple(row) for row in connection.execute("SELECT id, created_at FROM practice_attempts ORDER BY id")]
    assert split_grading_active(load_vault(paths.root)) is False

    result = upgrade_to_mvp010(paths.root, clock=FrozenClock(NOW))

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.9", "mvp-0.10")
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.10"
    assert split_grading_active(vault) is True
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.10"
    with connect(paths.sqlite_path) as connection:
        after = [tuple(row) for row in connection.execute("SELECT id, created_at FROM practice_attempts ORDER BY id")]
    assert after == before


def test_upgrade_is_immediate_successor_only(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    refused = upgrade_to_mvp010(paths.root, clock=FrozenClock(NOW))
    assert refused.upgraded is False and "only 'mvp-0.9'" in refused.problems[0]
    set_algorithm_version(paths, "mvp-0.10")
    already = upgrade_to_mvp010(paths.root, clock=FrozenClock(NOW))
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.10"]


def test_upgrade_command_takes_the_split_target(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.9")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.10"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.9 -> mvp-0.10" in result.output


def test_kill_switch_keeps_the_version_but_grades_joint(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.10")
    append_config(paths.root, "[diagnosis]\nsplit_enabled = false")
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.10"
    assert split_grading_active(vault) is False


def test_defaults_fingerprint_is_recorded_for_the_successor():
    from learnloop.config.template import defaults_fingerprint_for_version

    assert defaults_fingerprint_for_version("mvp-0.10") == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.10"]


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and a second idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.9")
    result = upgrade_to_mvp010(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [issue for issue in run_doctor(root).issues if issue.severity == "error" and issue.code.startswith(("sqlite", "diagnosis", "state"))]
    assert errors == []
    derived = set(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {
                table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                for table in sorted(derived)
            }

    # The first rebuild after any P0-namespace flip settles the calibration
    # priors it seeds (mvp-0.9 behaves identically on this fixture); from the
    # second rebuild on, the projection is a fixed point.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second
