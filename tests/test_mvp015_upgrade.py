"""mvp-0.15 (PLACEHOLDER tag): the valid-alternative gate for proofs, an explicit successor.

mvp-0.9 -> ... -> mvp-0.14 (the finite daily plan) -> mvp-0.15 (the
proofs-and-explanations route check). The upgrade accepts mvp-0.14, or mvp-0.9
to mvp-0.13 through mvp-0.14's own upgrade. It changes what NEW blind grades
persist on proof-like items only: the projection namespace is the same and
nothing is rewritten (playbook items 1, 3, 4 and 8).
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
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    RECURRENCE_GROUP_VERSIONS,
    STUCK_PROMPT_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.proof_check import proof_check_active
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
from learnloop.proof_check_upgrade import upgrade_to_mvp015
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.helpers import create_placement_vault
from tests.split_live_helpers import split_vault

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_185"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_the_route_check_successor_keeps_every_predecessor():
    assert PROOF_ROUTE_CHECK_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.15"
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
    ):
        assert PROOF_ROUTE_CHECK_ALGORITHM_VERSION in versions


def test_the_upgrade_from_the_predecessor_and_through_the_chain(tmp_path):
    paths = create_placement_vault(tmp_path / "v14", version="mvp-0.14")
    result = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.14", "mvp-0.15")
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.15" and proof_check_active(vault)
    already = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.15"]

    chained = create_placement_vault(tmp_path / "v13", version="mvp-0.13")
    result = upgrade_to_mvp015(chained.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.13", "mvp-0.15")

    split, _vault, _repository = split_vault(tmp_path / "v10", version="mvp-0.10", seed=False)
    result = upgrade_to_mvp015(split.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.15"), result.problems


def test_older_versions_are_refused_and_left_alone(tmp_path):
    paths = create_placement_vault(tmp_path / "v8", version="mvp-0.8")
    result = upgrade_to_mvp015(paths.root, clock=CLOCK)
    assert result.upgraded is False and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_upgrade_command_defaults_to_mvp015(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.14")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert "mvp-0.14 -> mvp-0.15" in result.output
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.14")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.15"])
    assert result.exit_code == 0, result.output


def test_defaults_fingerprint_is_recorded_for_the_route_check_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text("mvp-0.15")))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.15"]
    assert config.proof_check.enabled is True and config.ai.routing.proof_check is None


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.14")
    with sqlite3.connect(root / "state.sqlite") as connection:
        clarifications_before = connection.execute("SELECT * FROM grading_clarifications ORDER BY id").fetchall()
    result = upgrade_to_mvp015(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("SELECT * FROM grading_clarifications ORDER BY id").fetchall() == clarifications_before
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
