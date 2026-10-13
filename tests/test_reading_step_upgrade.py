"""The reading step's successor (UX Phase 1 round-2 re-review F2).

UX Phase 1's usability round 1 (U4) changed what the plan's reading block
serves: the step continues from the furthest section the learner read into and
is never front or back matter while a chapter is left. That is a change to what
is served, so (spec_daily_loop_v1 L6, §11) it is its own successor on top of
mvp-0.14 (daily_plan_v1), with ``plan.reading_from_furthest`` as its kill
switch. The tag is ``mvp-0.15`` on this branch, a PLACEHOLDER: main's chain
already runs past it, and the merge relabels it to the next free tag, as every
branch-built successor before it.

The upgrade accepts mvp-0.14, or mvp-0.9 to mvp-0.13 through mvp-0.14's own
upgrade. It changes serving only: the projection namespace is the same and
nothing is rewritten.
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
    READING_FROM_FURTHEST_ALGORITHM_VERSION,
    READING_FROM_FURTHEST_VERSIONS,
    RECURRENCE_GROUP_VERSIONS,
    STUCK_PROMPT_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.attempts.stuck import stuck_prompt_active
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import (
    DEFAULTS_SNAPSHOT_BY_ALGORITHM,
    default_config_text,
    defaults_fingerprint_for_version,
    effective_defaults_fingerprint,
)
from learnloop.daily_plan.engine import plan_active, reading_from_furthest_active
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.placement.state import placement_active
from learnloop.reading_step_upgrade import upgrade_to_mvp015
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_186"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_the_reading_step_is_the_latest_successor_and_keeps_every_predecessor():
    assert READING_FROM_FURTHEST_ALGORITHM_VERSION == "mvp-0.15"
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == READING_FROM_FURTHEST_ALGORITHM_VERSION
    assert SUCCESSOR_CHAIN[-2] == DAILY_PLAN_ALGORITHM_VERSION
    assert READING_FROM_FURTHEST_VERSIONS == frozenset({"mvp-0.15"})
    # The chain is linear: mvp-0.15 means the split PLUS placement PLUS
    # recurrence groups PLUS the stuck prompt PLUS the plan PLUS the reading step.
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
    ):
        assert READING_FROM_FURTHEST_ALGORITHM_VERSION in versions


def test_the_reading_step_serves_only_at_its_successor_with_the_switch_on(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False),
        "mvp-0.13": (False, False),
        "mvp-0.14": (True, False),
        "mvp-0.15": (True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (plan_active(vault), reading_from_furthest_active(vault)) == flags, version
    append_config_toml(paths.root, "[plan]\nreading_from_furthest = false\n")
    switched_off = load_vault(paths.root)
    assert reading_from_furthest_active(switched_off) is False
    # The kill switch keeps the version and every predecessor's behaviour.
    assert switched_off.config.algorithms.algorithm_version == "mvp-0.15"
    assert plan_active(switched_off) and split_grading_active(switched_off) and placement_active(switched_off)
    assert recurrence_active(switched_off) and stuck_prompt_active(switched_off)
    # The plan's own switch still turns the whole plan off, reading step included.
    append_config_toml(paths.root, "enabled = false\n")
    assert reading_from_furthest_active(load_vault(paths.root)) is False


def _plan_rows(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT COUNT(*) FROM daily_plans").fetchone()[0]


def test_upgrade_from_mvp014_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.14")
    repository = Repository(paths.sqlite_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
    result = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.14", "mvp-0.15")
    upgraded = load_vault(paths.root)
    assert reading_from_furthest_active(upgraded) and plan_active(upgraded)
    assert placement_active(upgraded) and split_grading_active(upgraded)
    assert recurrence_active(upgraded) and stuck_prompt_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.15"
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert _plan_rows(paths.sqlite_path) == 0
    assert "mvp-0.14" in manifests


def test_an_earlier_vault_goes_through_the_plans_upgrade(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.13")
    result = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.13", "mvp-0.15"), result.problems
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-2:] == ["mvp-0.14", "mvp-0.15"]


def test_a_refusal_down_the_chain_leaves_the_vault_where_it_was(tmp_path):
    # T1's guard, when required, refuses from mvp-0.10 before any step.
    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                             config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.14'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.15")
    already = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.15"]


def test_upgrade_command_defaults_to_mvp015(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.14")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert "mvp-0.14 -> mvp-0.15" in result.output
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.14")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.15"])
    assert result.exit_code == 0, result.output


def test_new_vaults_start_at_the_reading_step_successor(tmp_path):
    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.15"
    assert plan_active(fresh) and reading_from_furthest_active(fresh)


def test_defaults_fingerprint_is_recorded_for_the_reading_step_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text("mvp-0.15")))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.15"]
    assert config.plan.enabled is True and config.plan.reading_from_furthest is True


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild that never touches plan rows."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.14")
    result = upgrade_to_mvp015(root, clock=CLOCK)
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
    assert _plan_rows(root / "state.sqlite") == 0
