"""mvp-0.11 (learner field F2) is an explicit successor upgrade in a linear chain.

mvp-0.9 -> mvp-0.10 (Slice 1 M2, the blind-grading/diagnosis split) ->
mvp-0.11 (Slice A Phase 6: the split plus placement) -> mvp-0.12 (Slice 2
T1: plus recurrence groups; tests/test_recurrence_commands.py) -> mvp-0.13
(the stuck prompt; tests/test_mvp013_upgrade.py). The upgrade
accepts mvp-0.10, or mvp-0.9 by running the mvp-0.10 upgrade first.
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
    PLACEMENT_ALGORITHM_VERSION,
    PLACEMENT_VERSIONS,
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
from learnloop.ops.vault_upgrade import upgrade_to_mvp011
from learnloop.placement.state import placement_active
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault, set_algorithm_version

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_222"
CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_placement_successor_keeps_the_split_and_the_p0_projection_namespace():
    assert PLACEMENT_ALGORITHM_VERSION == "mvp-0.11"
    # Router R2a's staged frame (mvp-0.23, after value-of-information
    # stopping's mvp-0.21 and the Decider's mvp-0.22) is the latest
    # successor; it keeps placement.
    assert LATEST_ALGORITHM_VERSION == "mvp-0.33"
    assert PLACEMENT_ALGORITHM_VERSION in P0_SUCCESSOR_VERSIONS
    assert PLACEMENT_ALGORITHM_VERSION in P0_PROJECTION_VERSIONS
    assert PLACEMENT_ALGORITHM_VERSION in CANONICAL_STATE_VERSIONS
    # A linear chain: the split is live at mvp-0.10 and later, placement at
    # mvp-0.11 and later; mvp-0.9 has neither.
    assert DIAGNOSIS_SPLIT_VERSIONS == frozenset(
        {"mvp-0.10", "mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
         "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33"}
    )
    assert PLACEMENT_VERSIONS == frozenset(
        {"mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17", "mvp-0.18",
         "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33"}
    )


def test_split_and_placement_activate_at_the_right_versions(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False), "mvp-0.10": (True, False), "mvp-0.11": (True, True), "mvp-0.12": (True, True),
        "mvp-0.13": (True, True), "mvp-0.14": (True, True), "mvp-0.15": (True, True), "mvp-0.16": (True, True),
        "mvp-0.17": (True, True), "mvp-0.18": (True, True), "mvp-0.19": (True, True), "mvp-0.20": (True, True),
        "mvp-0.21": (True, True),
    }
    for version, (split, placement) in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (split_grading_active(vault), placement_active(vault)) == (split, placement), version


def test_upgrade_from_mvp010_flips_rebuilds_and_preserves_history_and_open_episodes(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.10")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    episodes_before = sorted((lo, e.id, e.trigger) for lo, e in repository.open_probe_episodes().items())
    assert episodes_before  # mvp-0.10 (like mvp-0.9) opened its initial episodes
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()

    result = upgrade_to_mvp011(paths.root, clock=FrozenClock(NOW))

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.11")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.11"
    assert split_grading_active(upgraded) and placement_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.11"
    # Nothing is rewritten; an opening episode already open stays open, so the
    # kill switch can restore it exactly.
    assert sorted((lo, e.id, e.trigger) for lo, e in repository.open_probe_episodes().items()) == episodes_before
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT COUNT(*) FROM assumption_decisions").fetchone() == (0,)
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.10" in manifests


def test_upgrade_from_mvp09_chains_through_the_split(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    repository = Repository(paths.sqlite_path)

    result = upgrade_to_mvp011(paths.root, clock=FrozenClock(NOW))

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.9", "mvp-0.11")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.11"
    assert split_grading_active(upgraded) and placement_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    # Both links ran: each froze its predecessor's manifest and rebuilt.
    assert {"mvp-0.9", "mvp-0.10"} <= manifests
    assert rebuilds[-2:] == ["mvp-0.10", "mvp-0.11"]
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.11"


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp011(paths.root, clock=FrozenClock(NOW))
    assert refused.upgraded is False
    assert "only 'mvp-0.10'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"

    set_algorithm_version(paths, "mvp-0.11")
    already = upgrade_to_mvp011(paths.root, clock=FrozenClock(NOW))
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.11"]


def test_upgrade_command_reaches_mvp011_explicitly_through_the_chain(tmp_path):
    # The default target is now the latest (mvp-0.12, guarded; see
    # tests/test_recurrence_commands.py); mvp-0.11 is still reached explicitly.
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.11"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.9 -> mvp-0.11" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.11"


def test_upgrade_command_still_reaches_mvp010_explicitly(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.10"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.9 -> mvp-0.10" in result.output
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.11"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.10 -> mvp-0.11" in result.output


def test_new_vaults_start_at_the_latest_version(tmp_path):
    """Owner decision 2026-10-12 (Slice 1 M2 open question 1): a new vault
    starts at LATEST_ALGORITHM_VERSION, mvp-0.21 since value-of-information
    stopping merged after the route rules: the split, placement, recurrence
    groups, "I'm stuck", the finite daily plan, probe-tie admission, sooner
    checks, the answer-key certification gate, source-first needs, the route
    rules and value-of-information stopping are all live."""

    from learnloop.attempts.stuck import stuck_prompt_active
    from learnloop.daily_plan.engine import plan_active
    from learnloop.substrate.recurrence_groups import recurrence_active
    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.33"
    assert placement_active(fresh) and split_grading_active(fresh) and recurrence_active(fresh)
    assert stuck_prompt_active(fresh) and plan_active(fresh)
    from learnloop.attempts.grading_support import route_rules_active
    from learnloop.placement.state import gap_sooner_checks_active

    assert gap_sooner_checks_active(fresh) and route_rules_active(fresh)


def test_existing_vaults_keep_their_version_until_the_owner_upgrades(tmp_path):
    """Re-initializing, loading or syncing an existing vault never moves its
    version; only `learnloop upgrade` does."""

    from learnloop.vault.loader import init_vault

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    before = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    init_vault(paths.root, clock=FrozenClock(NOW))
    vault = load_vault(paths.root)
    sync_vault_state(vault, Repository(paths.sqlite_path), clock=FrozenClock(NOW))
    assert (paths.root / "learnloop.toml").read_text(encoding="utf-8") == before
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.9"
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.11"])
    assert result.exit_code == 0, result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.11"
    # The default target is the latest (LATEST_ALGORITHM_VERSION). The chain
    # runs through mvp-0.12, whose same-cause guard is advisory (owner,
    # 2026-10-12; tests/test_recurrence_commands.py): the upgrade reports the
    # guard's status and proceeds.
    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION

    latest = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert latest.exit_code == 0, latest.output
    assert "advisory" in latest.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION


def test_defaults_fingerprint_is_recorded_for_the_placement_successor():
    from learnloop.config.template import defaults_fingerprint_for_version

    assert defaults_fingerprint_for_version("mvp-0.11") == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.11"]


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: the chained upgrade, FK
    check, doctor, and an idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.9")
    result = upgrade_to_mvp011(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error" and issue.code.startswith(("sqlite", "diagnosis", "state", "placement"))
    ]
    assert errors == []
    derived = set(tables_for_role(TableRole.DERIVED))

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
