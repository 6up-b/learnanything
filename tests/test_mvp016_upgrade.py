"""mvp-0.16 (learner-text gaps' sooner check) is the next explicit successor.

mvp-0.9 -> mvp-0.10 (the split) -> mvp-0.11 (placement) -> mvp-0.12
(recurrence groups) -> mvp-0.13 (the stuck prompt) -> mvp-0.14 (the finite
daily plan) -> mvp-0.15 (probe ties) -> mvp-0.16 (a prerequisite gap named in
the learner's own text brings an assumed or maintenance LO's next check
forward). The stage was built as mvp-0.13 over mvp-0.12 and relabelled when it
merged. The upgrade accepts mvp-0.15, or mvp-0.9 to mvp-0.14 through
mvp-0.15's own upgrade (below mvp-0.12, through T1's, whose same-cause guard
is advisory unless ``recurrence.require_guard = true``). It changes serving
only: the projection namespace is the same and nothing is rewritten.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    DAILY_PLAN_VERSIONS,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_VERSIONS,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    PROBE_TIE_VERSIONS,
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
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.learner_text_gap_upgrade import upgrade_to_mvp016
from learnloop.ops.doctor import run_doctor
from learnloop.placement.state import gap_sooner_checks_active, placement_active
from learnloop.scheduling.scheduler import probe_ties_admitted
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_183"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))
LEARNER_GAP_TABLES = {
    "learner_text_gaps",
    "learner_text_gap_reversals",
    "learner_text_gap_jobs",
    "learner_gap_check_advances",
    "learner_gap_commitments",
}


def test_learner_text_gap_successor_keeps_every_predecessor():
    assert LEARNER_TEXT_GAP_ALGORITHM_VERSION == "mvp-0.16"
    # Value-of-information stopping (mvp-0.17, tests/test_mvp017_upgrade.py)
    # followed it and keeps the sooner check.
    assert SUCCESSOR_CHAIN[-2] == LEARNER_TEXT_GAP_ALGORITHM_VERSION
    assert LEARNER_TEXT_GAP_VERSIONS == frozenset({"mvp-0.16", "mvp-0.17"})
    # The chain is linear: mvp-0.16 means the split PLUS placement PLUS
    # recurrence groups PLUS the stuck prompt PLUS the plan PLUS probe ties
    # PLUS the sooner check.
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
        PROBE_TIE_VERSIONS,
    ):
        assert LEARNER_TEXT_GAP_ALGORITHM_VERSION in versions


def test_each_version_activates_exactly_its_features(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False, False, False, False),
        "mvp-0.10": (True, False, False, False, False),
        "mvp-0.11": (True, True, False, False, False),
        "mvp-0.12": (True, True, False, False, False),
        "mvp-0.13": (True, True, False, False, False),
        "mvp-0.14": (True, True, True, False, False),
        "mvp-0.15": (True, True, True, True, False),
        "mvp-0.16": (True, True, True, True, True),
        "mvp-0.17": (True, True, True, True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (
            split_grading_active(vault), placement_active(vault), plan_active(vault),
            probe_ties_admitted(vault.config), gap_sooner_checks_active(vault),
        ) == flags, version
    set_algorithm_version(paths, "mvp-0.16")
    vault = load_vault(paths.root)
    assert recurrence_active(vault) and stuck_prompt_active(vault)
    append_config_toml(paths.root, "[learner_text_gaps]\nsooner_check_enabled = false\n")
    switched_off = load_vault(paths.root)
    # The kill switch keeps the version and every predecessor's behaviour.
    assert gap_sooner_checks_active(switched_off) is False
    assert switched_off.config.algorithms.algorithm_version == "mvp-0.16"
    assert split_grading_active(switched_off) and placement_active(switched_off) and plan_active(switched_off)
    assert probe_ties_admitted(switched_off.config)
    assert recurrence_active(switched_off) and stuck_prompt_active(switched_off)


def test_upgrade_from_mvp015_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.15")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()

    result = upgrade_to_mvp016(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.15", "mvp-0.16")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.16"
    assert gap_sooner_checks_active(upgraded) and probe_ties_admitted(upgraded.config) and plan_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.16"
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        assert connection.execute("SELECT COUNT(*) FROM learner_gap_check_advances").fetchone()[0] == 0
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.15" in manifests


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    """With ``recurrence.require_guard = true`` and the guard unrun, from
    mvp-0.10 the upgrade refuses and the vault stays where it was; once the
    guard passes it walks mvp-0.11 to mvp-0.15 (each freezing and rebuilding)
    to mvp-0.16."""

    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp016(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp016(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.16"), result.problems
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.16"
    assert gap_sooner_checks_active(upgraded) and probe_ties_admitted(upgraded.config) and recurrence_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert {"mvp-0.10", "mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15"} <= manifests
    assert rebuilds[-6:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16"]


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    """Owner batch 2 (2026-10-12): the guard is advisory by default, so the
    chained upgrade from mvp-0.10 reaches mvp-0.16 and passes the guard's
    status on as notes."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp016(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.16"), result.problems
    assert any("advisory" in note for note in result.notes)


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp016(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.15'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.16")
    already = upgrade_to_mvp016(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.16"]


def test_upgrade_command_defaults_to_the_latest(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.15")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"mvp-0.15 -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.15")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.16"])
    assert result.exit_code == 0, result.output


def test_new_vaults_start_at_a_successor_with_the_sooner_check(tmp_path):
    """Owner decision 2026-10-12: new vaults start at LATEST_ALGORITHM_VERSION."""

    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION
    assert LATEST_ALGORITHM_VERSION in LEARNER_TEXT_GAP_VERSIONS
    assert gap_sooner_checks_active(fresh) and probe_ties_admitted(fresh.config) and plan_active(fresh)


def test_defaults_fingerprint_is_recorded_for_the_learner_text_gap_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text("mvp-0.16")))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.16"]
    section = config.learner_text_gaps
    assert section.enabled and section.sooner_check_enabled and section.chooser == "context_model"
    assert section.max_creations_per_day == 3 and section.sooner_check_delay_hours == 24


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.15")
    result = upgrade_to_mvp016(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert LEARNER_GAP_TABLES <= tables
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error"
        and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan", "router", "learner"))
    ]
    assert errors == []
    derived = set(tables_for_role(TableRole.DERIVED))
    assert not (LEARNER_GAP_TABLES & derived)

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
