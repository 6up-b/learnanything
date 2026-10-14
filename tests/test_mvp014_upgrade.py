"""mvp-0.14 (daily-loop DL1, ``daily_plan_v1``) is the next explicit successor.

mvp-0.9 -> mvp-0.10 (the split) -> mvp-0.11 (placement) -> mvp-0.12
(recurrence groups) -> mvp-0.13 (the stuck prompt) -> mvp-0.14 (the finite
daily plan). DL1 was built as mvp-0.12 over mvp-0.11 and relabelled when it
merged. The upgrade accepts mvp-0.13, or mvp-0.9 to mvp-0.12 through
mvp-0.13's own upgrade (below mvp-0.12, through mvp-0.12's, which checks T1's
same-answer/different-cause guard before any chained step). It changes serving
only: the projection namespace is the same, the plan tables start empty, and
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
from learnloop.daily_plan.engine import plan_active
from learnloop.daily_plan_upgrade import upgrade_to_mvp014
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.placement.state import placement_active
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_202"
CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))


def test_the_plan_successor_keeps_every_predecessor():
    assert DAILY_PLAN_ALGORITHM_VERSION == "mvp-0.14"
    # Router R1's probe ties (mvp-0.15, tests/test_mvp015_upgrade.py),
    # learner-text gaps' sooner check (mvp-0.16, tests/test_mvp016_upgrade.py),
    # the proofs-and-explanations route check (mvp-0.17,
    # tests/test_mvp017_upgrade.py), canonical sources' answer-key gate
    # (mvp-0.18) and source-first needs (mvp-0.19, tests/test_mvp018_upgrade.py),
    # the route rules in the grader (mvp-0.20, tests/test_mvp020_upgrade.py),
    # value-of-information stopping (mvp-0.21, tests/test_mvp021_upgrade.py)
    # and Tier 1's Decider judgments (mvp-0.22, the latest successor,
    # tests/test_mvp022_upgrade.py) followed it and keep the plan.
    # Router R2a's staged frame (mvp-0.23) is now the latest; it keeps the plan.
    assert SUCCESSOR_CHAIN[-10] == DAILY_PLAN_ALGORITHM_VERSION
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.23"
    assert DAILY_PLAN_VERSIONS == frozenset(
        {"mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17", "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21",
         "mvp-0.22", "mvp-0.23"}
    )
    # The chain is linear: mvp-0.14 means the split PLUS placement PLUS
    # recurrence groups PLUS the stuck prompt PLUS the plan.
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS,
    ):
        assert DAILY_PLAN_ALGORITHM_VERSION in versions


def test_the_plan_serves_only_at_the_successor_with_the_switch_on(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False, False),
        "mvp-0.11": (True, True, False),
        "mvp-0.12": (True, True, False),
        "mvp-0.13": (True, True, False),
        "mvp-0.14": (True, True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (split_grading_active(vault), placement_active(vault), plan_active(vault)) == flags, version
    vault = load_vault(paths.root)
    assert recurrence_active(vault) and stuck_prompt_active(vault)
    append_config_toml(paths.root, "[plan]\nenabled = false\n")
    switched_off = load_vault(paths.root)
    assert plan_active(switched_off) is False
    # The kill switch keeps the version and every predecessor's behaviour.
    assert switched_off.config.algorithms.algorithm_version == "mvp-0.14"
    assert split_grading_active(switched_off) and placement_active(switched_off)
    assert recurrence_active(switched_off) and stuck_prompt_active(switched_off)


def _plan_rows(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT COUNT(*) FROM daily_plans").fetchone()[0]


def test_upgrade_from_mvp013_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.13")
    repository = Repository(paths.sqlite_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
    result = upgrade_to_mvp014(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.13", "mvp-0.14")
    upgraded = load_vault(paths.root)
    assert plan_active(upgraded) and placement_active(upgraded) and split_grading_active(upgraded)
    assert recurrence_active(upgraded) and stuck_prompt_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.14"
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert _plan_rows(paths.sqlite_path) == 0
    assert "mvp-0.13" in manifests


def test_an_earlier_vault_goes_through_mvp012s_guard(tmp_path):
    """The chain keeps T1's guard: with ``recurrence.require_guard = true``
    and the guard unrun, from mvp-0.10 the upgrade refuses and the vault stays
    where it was; once the guard passes it
    walks mvp-0.11, mvp-0.12 and mvp-0.13 (each freezing and rebuilding) to
    mvp-0.14."""

    # The guard refuses only when required (owner batch 2: advisory by default).
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp014(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp014(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.14"), result.problems
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.14"
    assert plan_active(upgraded) and stuck_prompt_active(upgraded) and recurrence_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert {"mvp-0.10", "mvp-0.11", "mvp-0.12", "mvp-0.13"} <= manifests
    assert rebuilds[-4:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14"]


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp014(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.13'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.14")
    already = upgrade_to_mvp014(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.14"]


def test_upgrade_command_reaches_mvp014_explicitly(tmp_path):
    # The default target moved on to mvp-0.15 (router R1); mvp-0.14 is still
    # reached explicitly.
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.13")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.14"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.13 -> mvp-0.14" in result.output


def test_new_vaults_serve_the_plan(tmp_path):
    """Owner decision 2026-10-12: new vaults start at LATEST_ALGORITHM_VERSION
    (mvp-0.15 since router R1 merged), which keeps the plan, so a fresh vault
    serves the finite plan (DL1's own text kept new vaults at mvp-0.9; that
    predates the decision)."""

    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION
    assert LATEST_ALGORITHM_VERSION in DAILY_PLAN_VERSIONS
    assert plan_active(fresh)


def test_defaults_fingerprint_is_recorded_for_the_plan_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text("mvp-0.14")))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.14"]
    assert config.plan.enabled is True and config.plan.default_minutes == 25


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild that never touches plan rows."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.13")
    result = upgrade_to_mvp014(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        columns = {row[1] for row in connection.execute("PRAGMA table_info(attention_blocks)")}
        assert {"daily_plan_id", "plan_ordinal", "lane", "chosen_by", "decision_ref", "reading_json"} <= columns
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

    # The first rebuild after an upgrade reaches the fixed point; from the
    # second on, rebuilds are idempotent.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second
    assert _plan_rows(root / "state.sqlite") == 0


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    """Owner batch 2 (2026-10-12): the guard is advisory by default, so the
    chained upgrade from mvp-0.10 reaches mvp-0.14 and passes the guard's status on."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp014(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.14"), result.problems
    assert any("advisory" in note for note in result.notes)
