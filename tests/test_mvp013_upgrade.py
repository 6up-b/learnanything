"""mvp-0.13 ("I'm stuck") is an explicit, owner-run successor in the linear chain.

mvp-0.9 -> mvp-0.10 (the split) -> mvp-0.11 (placement) -> mvp-0.12
(recurrence groups) -> mvp-0.13 (the stuck prompt). The stuck prompt was built
as mvp-0.11 over mvp-0.10 and relabelled when it merged. The upgrade accepts
mvp-0.12, or mvp-0.9 to mvp-0.11 through mvp-0.12's own upgrade, which checks
T1's same-answer/different-cause guard before any chained step.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    RECURRENCE_GROUP_VERSIONS,
    STUCK_PROMPT_ALGORITHM_VERSION,
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
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.placement.state import placement_active
from learnloop.stuck_prompt_upgrade import upgrade_to_mvp013
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version
from tests.split_live_helpers import append_config, split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_215"
CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_stuck_version_is_a_successor_and_keeps_every_predecessor():
    assert STUCK_PROMPT_ALGORITHM_VERSION == "mvp-0.13"
    # Daily-loop DL1's finite plan (mvp-0.14), router R1's probe ties
    # (mvp-0.15), learner-text gaps' sooner check (mvp-0.16), the
    # proofs-and-explanations route check (mvp-0.17, tests/test_mvp017_upgrade.py),
    # canonical sources' answer-key gate (mvp-0.18) and source-first needs
    # (mvp-0.19, tests/test_mvp018_upgrade.py), the route rules in the grader
    # (mvp-0.20, tests/test_mvp020_upgrade.py), value-of-information stopping
    # (mvp-0.21, tests/test_mvp021_upgrade.py) and Tier 1's Decider judgments
    # (mvp-0.22, the latest successor, tests/test_mvp022_upgrade.py) followed
    # it and keep the stuck prompt.
    # Router R2a's staged frame (mvp-0.23) is now the latest.
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.29"
    assert SUCCESSOR_CHAIN[-16] == STUCK_PROMPT_ALGORITHM_VERSION
    assert STUCK_PROMPT_VERSIONS == {STUCK_PROMPT_ALGORITHM_VERSION, "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                                     "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29"}
    assert STUCK_PROMPT_ALGORITHM_VERSION in P0_SUCCESSOR_VERSIONS
    assert STUCK_PROMPT_ALGORITHM_VERSION in P0_PROJECTION_VERSIONS
    # The chain is linear: mvp-0.13 means the split PLUS placement PLUS
    # recurrence groups PLUS the stuck prompt.
    assert STUCK_PROMPT_ALGORITHM_VERSION in DIAGNOSIS_SPLIT_VERSIONS
    assert STUCK_PROMPT_ALGORITHM_VERSION in PLACEMENT_VERSIONS
    assert STUCK_PROMPT_ALGORITHM_VERSION in RECURRENCE_GROUP_VERSIONS


def test_only_mvp013_offers_the_stuck_control(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    for version in ("mvp-0.9", "mvp-0.10", "mvp-0.11", "mvp-0.12"):
        set_algorithm_version(paths, version)
        assert stuck_prompt_active(load_vault(paths.root)) is False, version
    set_algorithm_version(paths, "mvp-0.13")
    vault = load_vault(paths.root)
    assert stuck_prompt_active(vault) is True
    assert split_grading_active(vault) and placement_active(vault) and recurrence_active(vault)


def test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.12")
    repository = Repository(paths.sqlite_path)
    with connect(paths.sqlite_path) as connection:
        before = [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")]
    assert stuck_prompt_active(load_vault(paths.root)) is False

    result = upgrade_to_mvp013(paths.root, clock=FrozenClock(NOW))

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.12", "mvp-0.13")
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.13"
    assert stuck_prompt_active(vault) and split_grading_active(vault)
    assert placement_active(vault) and recurrence_active(vault)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.13"
    with connect(paths.sqlite_path) as connection:
        after = [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")]
    assert after == before


def test_upgrade_refuses_older_and_repeated_targets(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    refused = upgrade_to_mvp013(paths.root, clock=FrozenClock(NOW))
    assert refused.upgraded is False and "only 'mvp-0.12'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.13")
    already = upgrade_to_mvp013(paths.root, clock=FrozenClock(NOW))
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.13"]


def test_an_earlier_vault_goes_through_mvp012s_guard(tmp_path):
    """The chain keeps T1's guard: with ``recurrence.require_guard = true``
    and the guard unrun, from mvp-0.10 the upgrade refuses and the vault stays where it was; once the guard passes it
    walks mvp-0.11 and mvp-0.12 (each freezing and rebuilding) to mvp-0.13."""

    # The guard refuses only when required (owner batch 2: advisory by default).
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp013(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert "has not judged" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp013(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.13"), result.problems
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.13"
    assert stuck_prompt_active(upgraded) and recurrence_active(upgraded)
    assert repository.recurrence_state()["active"] is True
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    # Every link ran: each froze its predecessor's manifest and rebuilt.
    assert {"mvp-0.10", "mvp-0.11", "mvp-0.12"} <= manifests
    assert rebuilds[-3:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13"]


def test_upgrade_command_reaches_the_stuck_target_explicitly(tmp_path):
    # The default target moved on (mvp-0.14, then mvp-0.15); mvp-0.13 is
    # still reached explicitly.
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.12")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.13"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.12 -> mvp-0.13" in result.output
    explicit = create_basic_vault(tmp_path / "explicit")
    set_algorithm_version(explicit, "mvp-0.12")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.13"])
    assert result.exit_code == 0, result.output


def test_kill_switch_keeps_the_version_and_every_predecessor(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.13")
    append_config(paths.root, "[stuck_prompt]\nenabled = false")
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.13"
    assert stuck_prompt_active(vault) is False
    assert split_grading_active(vault) and placement_active(vault) and recurrence_active(vault)


def test_defaults_fingerprint_is_recorded_for_the_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text("mvp-0.13")))
    assert config.stuck_prompt.enabled is True
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.13"]


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and a second idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.12")
    result = upgrade_to_mvp013(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)")}
        assert "declared_stuck" in columns
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


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    """Owner batch 2 (2026-10-12): the guard is advisory by default, so the
    chained upgrade from mvp-0.10 goes through and passes the guard's status on."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp013(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.13"), result.problems
    assert any("advisory" in note for note in result.notes)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.13"
