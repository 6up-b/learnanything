"""mvp-0.18 and mvp-0.19 (canonical sources) are the next explicit successors.

mvp-0.9 -> ... -> mvp-0.17 (the proofs route check) -> mvp-0.18 (certification
follows the answer key, spec_source_practice_and_probes_v1 §7.3a) -> mvp-0.19
(source-first intervention needs, §8.5). The branch built them as mvp-0.15 and
mvp-0.16 (placeholder tags) over mvp-0.14 and they were relabelled at the
merge after probe ties, learner-text gaps and the route check. The upgrades
accept their immediate predecessor, or mvp-0.9 onward through
``proof_check_upgrade.upgrade_to_mvp017`` (below mvp-0.12, through T1's,
whose same-cause guard is advisory unless ``recurrence.require_guard = true``).
Neither rewrites anything: the projection namespace is the same, and attempts
recorded before the tag keep ``reference_status = not_applicable``
(playbook items 1, 3, 4 and 8).

route-check-in-grader (owner decision 2026-10-13) removed mvp-0.17's separate
route check from serving, so mvp-0.17 to mvp-0.19 grade new answers as its kill
switch defined (as mvp-0.16), and the route rules in the grader followed as
mvp-0.20 (``tests/test_mvp020_upgrade.py``), then value-of-information
stopping as mvp-0.21, the latest successor (``tests/test_mvp021_upgrade.py``).
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    DAILY_PLAN_VERSIONS,
    DECIDER_TIER1_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_VERSIONS,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    PROBE_TIE_VERSIONS,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    RECURRENCE_GROUP_VERSIONS,
    ROUTE_RULES_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_VERSIONS,
    SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
    SOURCE_REFERENCE_GATE_VERSIONS,
    STUCK_PROMPT_VERSIONS,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_ALGORITHM_VERSION,
)
from learnloop.attempts.grading_support import route_rules_active
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
from learnloop.daily_plan.engine import plan_active
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.placement.state import gap_sooner_checks_active, placement_active
from learnloop.sources_upgrade import upgrade_to_mvp018, upgrade_to_mvp019
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_218"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_the_sources_successors_follow_the_route_check_and_keep_every_predecessor():
    assert (SOURCE_REFERENCE_GATE_ALGORITHM_VERSION, SOURCE_FIRST_NEEDS_ALGORITHM_VERSION) == ("mvp-0.18", "mvp-0.19")
    # The route rules in the grader (mvp-0.20), value-of-information stopping
    # (mvp-0.21) and Tier 1's Decider judgments (mvp-0.22) followed them.
    # Router R2a's staged frame (mvp-0.23) followed them all.
    assert SUCCESSOR_CHAIN[-13:-7] == (
        PROOF_ROUTE_CHECK_ALGORITHM_VERSION, SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
        SOURCE_FIRST_NEEDS_ALGORITHM_VERSION, ROUTE_RULES_ALGORITHM_VERSION, VOI_STOPPING_ALGORITHM_VERSION,
        DECIDER_TIER1_ALGORITHM_VERSION,
    )
    assert LATEST_ALGORITHM_VERSION == "mvp-0.30"
    assert SOURCE_REFERENCE_GATE_VERSIONS == frozenset(
        {"mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30"}
    )
    assert SOURCE_FIRST_NEEDS_VERSIONS == frozenset({"mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30"})
    # The chain is linear: each means every predecessor's semantics PLUS its own.
    for version in (SOURCE_REFERENCE_GATE_ALGORITHM_VERSION, SOURCE_FIRST_NEEDS_ALGORITHM_VERSION):
        for versions in (
            P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
            PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
            PROBE_TIE_VERSIONS, LEARNER_TEXT_GAP_VERSIONS,
        ):
            assert version in versions


def test_each_version_keeps_its_predecessors_and_grades_as_mvp016(tmp_path):
    # mvp-0.17's separate check is gone (route-check-in-grader): mvp-0.17 to
    # mvp-0.19 grade new answers without it, and the route rules start at
    # mvp-0.20.
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.17")
    for version in ("mvp-0.17", "mvp-0.18", "mvp-0.19"):
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert gap_sooner_checks_active(vault) and plan_active(vault), version
        assert placement_active(vault) and recurrence_active(vault), version
        assert route_rules_active(vault) is False, version


def test_upgrade_from_mvp017_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.17")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()

    result = upgrade_to_mvp018(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.17", "mvp-0.18")
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.18"
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.18"
    result = upgrade_to_mvp019(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.18", "mvp-0.19")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.19"
    assert gap_sooner_checks_active(upgraded) and plan_active(upgraded) and not route_rules_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert {"mvp-0.17", "mvp-0.18"} <= manifests


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    """With ``recurrence.require_guard = true`` and the guard unrun, from
    mvp-0.10 the upgrade refuses (the refusal names the mvp-0.12 step) and the
    vault stays where it was; once the guard passes it walks every link."""

    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp019(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp019(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.19"), result.problems
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-9:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                             "mvp-0.18", "mvp-0.19"]


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    """Owner batch 2 (2026-10-12): the guard is advisory by default; its status
    comes back as notes through every link, mvp-0.18's and mvp-0.19's included."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp019(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.19"), result.problems
    assert any("advisory" in note for note in result.notes)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.19"


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp018(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.17'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.19")
    already = upgrade_to_mvp019(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.19"]


def test_upgrade_command_defaults_to_the_latest(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.17")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert "mvp-0.17 -> mvp-0.30" in result.output
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.17")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.18"])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == "mvp-0.18"


def test_defaults_fingerprints_are_recorded_for_every_successor():
    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.17")
    result = upgrade_to_mvp019(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error"
        and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan", "router", "learner"))
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
