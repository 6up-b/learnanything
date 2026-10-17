"""mvp-0.22 (Tier 1, the Decider migration, owner decision 2026-10-13) is the next explicit successor.

mvp-0.9 -> ... -> mvp-0.19 (source-first needs) -> mvp-0.20 (the route rules
in the grader) -> mvp-0.21 (value-of-information stopping) -> mvp-0.22: the
Decider decides the small judgments ``[decider_routes]`` names, each with its
LLM as fallback and its own kill switch (``learnloop.decider_judgments``). The
branch built it as mvp-0.20 (a placeholder tag, its upgrade in
``sources_upgrade``) and it was relabelled mvp-0.22 when it merged after the
route rules and value-of-information stopping. It changes what is served from
now on, never the meaning of recorded history, so the upgrade is a tag change
plus an idempotent rebuild of the same projection namespace. It accepts
mvp-0.21, or mvp-0.9 to mvp-0.20 through
``voi_stopping_upgrade.upgrade_to_mvp021`` (below mvp-0.12 through T1's, whose
same-cause guard is advisory unless ``recurrence.require_guard = true``), and
passes the chained notes through, a refusal's included (playbook items 1, 3,
4 and 8).
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    DAILY_PLAN_VERSIONS,
    DECIDER_TIER1_ALGORITHM_VERSION,
    DECIDER_TIER1_VERSIONS,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_VERSIONS,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    PROBE_TIE_VERSIONS,
    RECURRENCE_GROUP_VERSIONS,
    ROUTE_RULES_ALGORITHM_VERSION,
    ROUTE_RULES_VERSIONS,
    SOURCE_FIRST_NEEDS_VERSIONS,
    SOURCE_REFERENCE_GATE_VERSIONS,
    STUCK_PROMPT_VERSIONS,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_ALGORITHM_VERSION,
    VOI_STOPPING_VERSIONS,
)
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.decider_judgments import SERVING_TASKS, enabled
from learnloop.decider_upgrade import upgrade_to_mvp022
from learnloop.ops.doctor import run_doctor
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, _set_algorithm_version_at, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_206"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_the_decider_successor_follows_voi_stopping_and_keeps_every_predecessor():
    assert DECIDER_TIER1_ALGORITHM_VERSION == "mvp-0.22"
    assert SUCCESSOR_CHAIN[-8:-5] == (
        ROUTE_RULES_ALGORITHM_VERSION, VOI_STOPPING_ALGORITHM_VERSION, DECIDER_TIER1_ALGORITHM_VERSION,
    )
    # Router R2a's staged frame (mvp-0.23) followed it as the latest successor.
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.27"
    assert DECIDER_TIER1_VERSIONS == frozenset({"mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27"})
    # The chain is linear: mvp-0.22 means everything mvp-0.21 means PLUS the
    # Decider's judgments (main's own mvp-0.20 is the route rules, never the
    # Decider).
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
        PROBE_TIE_VERSIONS, LEARNER_TEXT_GAP_VERSIONS, SOURCE_REFERENCE_GATE_VERSIONS,
        SOURCE_FIRST_NEEDS_VERSIONS, ROUTE_RULES_VERSIONS, VOI_STOPPING_VERSIONS,
    ):
        assert DECIDER_TIER1_ALGORITHM_VERSION in versions
    assert ROUTE_RULES_ALGORITHM_VERSION not in DECIDER_TIER1_VERSIONS
    assert VOI_STOPPING_ALGORITHM_VERSION not in DECIDER_TIER1_VERSIONS


def test_each_version_moves_the_judgments_only_at_the_successor(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.18")
    for version, moved in (("mvp-0.18", False), ("mvp-0.19", False), ("mvp-0.20", False), ("mvp-0.21", False),
                           ("mvp-0.22", True)):
        set_algorithm_version(paths, version)
        config = load_vault(paths.root).config
        assert all(enabled(config, task) is moved for task in SERVING_TASKS), version
        # The span-support check is a content path: its switch acts at every version.
        assert enabled(config, "facet_span_support"), version


def test_upgrade_from_mvp021_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.21")
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
        ledger_before = connection.execute("SELECT * FROM judgment_ledger ORDER BY id").fetchall()

    result = upgrade_to_mvp022(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.21", "mvp-0.22")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.22"
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.22"
    assert all(enabled(upgraded.config, task) for task in SERVING_TASKS)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        assert connection.execute("SELECT * FROM judgment_ledger ORDER BY id").fetchall() == ledger_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    # The predecessor's parameter manifest is frozen before the tag moves.
    assert "mvp-0.21" in manifests


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    """With ``recurrence.require_guard = true`` and the guard unrun, from
    mvp-0.10 the upgrade refuses (the refusal names the mvp-0.12 step) and the
    vault stays where it was; once the guard passes it walks every link."""

    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp022(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp022(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.22"), result.problems
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-12:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                              "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22"]


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    """Owner batch 2 (2026-10-12): the guard is advisory by default; its status
    comes back as notes through every link, mvp-0.22's included."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp022(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.22"), result.problems
    assert any("advisory" in note for note in result.notes)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.22"


def test_chained_notes_pass_through_an_upgrade_and_a_refusal(tmp_path, monkeypatch):
    from learnloop import decider_upgrade

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.20")
    original = decider_upgrade.upgrade_to_mvp021

    def noted(root, **kwargs):
        result = original(root, **kwargs)
        result.notes.append("earlier advisory guard")
        return result

    monkeypatch.setattr(decider_upgrade, "upgrade_to_mvp021", noted)
    result = upgrade_to_mvp022(paths.root, clock=CLOCK)
    assert result.upgraded and result.notes == ["earlier advisory guard"]

    def refusing(root, **kwargs):
        return UpgradeResult(upgraded=False, from_version="mvp-0.20", to_version="mvp-0.21",
                             problems=["vault is busy"], notes=["earlier advisory guard"])

    later = create_placement_vault(tmp_path / "later", version="mvp-0.20")
    monkeypatch.setattr(decider_upgrade, "upgrade_to_mvp021", refusing)
    refused = upgrade_to_mvp022(later.root, clock=CLOCK)
    assert refused.upgraded is False and refused.notes == ["earlier advisory guard"]
    assert refused.problems == ["mvp-0.21 step refused: vault is busy"]
    assert load_vault(later.root).config.algorithms.algorithm_version == "mvp-0.20"


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp022(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.21'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.22")
    already = upgrade_to_mvp022(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.22"]


def test_upgrade_through_the_chain_from_the_route_rules_and_earlier(tmp_path):
    for version in ("mvp-0.16", "mvp-0.19", "mvp-0.20"):
        paths = create_placement_vault(tmp_path / version, version=version)
        result = upgrade_to_mvp022(paths.root, clock=CLOCK)
        assert (result.upgraded, result.from_version, result.to_version) == (True, version, "mvp-0.22"), result.problems


def test_upgrade_command_defaults_to_the_latest(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.21")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"mvp-0.21 -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.27"
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.18")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.22"])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == "mvp-0.22"
    # --to mvp-0.21 still reaches value-of-information stopping, not the Decider.
    earlier = create_placement_vault(tmp_path / "earlier", version="mvp-0.20")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(earlier.root), "--to", "mvp-0.21"])
    assert result.exit_code == 0, result.output
    assert load_vault(earlier.root).config.algorithms.algorithm_version == "mvp-0.21"


def test_new_vaults_start_at_a_successor_with_the_deciders_judgments(tmp_path):
    """Owner decision 2026-10-12: new vaults start at LATEST_ALGORITHM_VERSION
    (mvp-0.23 since router R2a's staged frame merged), which keeps them."""

    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.27"
    assert LATEST_ALGORITHM_VERSION in DECIDER_TIER1_VERSIONS
    assert all(enabled(fresh.config, task) for task in SERVING_TASKS)


def test_defaults_fingerprints_are_recorded_for_every_successor():
    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture (a backup-API copy): raw
    history kept, upgrade, FK check, doctor, and an idempotent rebuild."""

    before_hash = hashlib.sha256((HEAD / "state.sqlite").read_bytes()).hexdigest()
    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    _set_algorithm_version_at(root, "mvp-0.21")
    repository = Repository(root / "state.sqlite")
    raw_roles = (TableRole.RAW_LEDGER, TableRole.RECEIPT)

    def snapshot(roles):
        with connect(repository.sqlite_path, read_only=True) as connection:
            present = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            return {
                table: sorted((tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')), key=repr)
                for role in roles for table in sorted(tables_for_role(role)) if table in present
            }

    raw = snapshot(raw_roles)
    result = upgrade_to_mvp022(root, clock=CLOCK)
    assert result.upgraded, result.problems
    # The version and parameter activation add their own receipts; recorded history is unchanged.
    after = snapshot(raw_roles)
    for table, rows in raw.items():
        assert all(row in after[table] for row in rows), table
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error"
        and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan", "router", "learner"))
    ]
    assert errors == []
    vault = load_vault(root)
    # As the predecessor's fixture test: two rebuilds settle the refreshed
    # parameter manifest before two same-version rebuilds are compared.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot((TableRole.DERIVED,))
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot((TableRole.DERIVED,)) == second
    assert upgrade_to_mvp022(root, clock=CLOCK).upgraded is False
    assert hashlib.sha256((HEAD / "state.sqlite").read_bytes()).hexdigest() == before_hash
