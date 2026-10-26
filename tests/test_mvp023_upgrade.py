"""mvp-0.23 (router R2a, the staged frame on Today) is the next explicit successor.

mvp-0.9 -> ... -> mvp-0.21 (value-of-information stopping) -> mvp-0.22 (Tier
1's Decider judgments) -> mvp-0.23: Today's plan composed by the staged frame
(DL1's lanes and lane_quota_v1 over the set the P4 constraint engine admits)
and golden_path.advance through the P2 bridge (D13), behind
``router.enabled``. Built as a placeholder tag; it kept mvp-0.23 at its
merge, nothing on main having taken it. It changes
what is served from now on, never the meaning of recorded history, so the
upgrade is a tag change plus an idempotent rebuild of the same projection
namespace. It accepts mvp-0.22, or mvp-0.9 to mvp-0.21 through
``decider_upgrade.upgrade_to_mvp022`` (below mvp-0.12 through T1's, whose
same-cause guard is advisory unless ``recurrence.require_guard = true``),
and passes the chained notes through, a refusal's included (playbook items 1,
3, 4 and 8).
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
    ROUTE_RULES_VERSIONS,
    ROUTER_STAGED_FRAME_ALGORITHM_VERSION,
    ROUTER_STAGED_FRAME_VERSIONS,
    SOURCE_FIRST_NEEDS_VERSIONS,
    SOURCE_REFERENCE_GATE_VERSIONS,
    STUCK_PROMPT_VERSIONS,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_VERSIONS,
)
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
from learnloop.daily_plan.engine import DEFAULT_POLICY
from learnloop.daily_plan.policy import bridge_active, policy_for, router_active
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.doctor import run_doctor
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.router_staged_upgrade import upgrade_to_mvp023
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, _set_algorithm_version_at, append_config_toml, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_222"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_the_router_successor_follows_the_decider_and_keeps_every_predecessor():
    assert ROUTER_STAGED_FRAME_ALGORITHM_VERSION == "mvp-0.23"
    assert SUCCESSOR_CHAIN[13:15] == (DECIDER_TIER1_ALGORITHM_VERSION, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    # Router R2b + R2c's model mixture (mvp-0.24) followed it as the latest successor.
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.34"
    assert ROUTER_STAGED_FRAME_VERSIONS == frozenset({"mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33", "mvp-0.34"})
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
        PROBE_TIE_VERSIONS, LEARNER_TEXT_GAP_VERSIONS, SOURCE_REFERENCE_GATE_VERSIONS,
        SOURCE_FIRST_NEEDS_VERSIONS, ROUTE_RULES_VERSIONS, VOI_STOPPING_VERSIONS, DECIDER_TIER1_VERSIONS,
    ):
        assert ROUTER_STAGED_FRAME_ALGORITHM_VERSION in versions
    assert DECIDER_TIER1_ALGORITHM_VERSION not in ROUTER_STAGED_FRAME_VERSIONS


def test_the_router_serves_only_at_the_successor_with_its_switch_on(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.22")
    repository = Repository(paths.sqlite_path)
    for version, served in (("mvp-0.21", False), ("mvp-0.22", False), ("mvp-0.23", True)):
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (router_active(vault), bridge_active(vault)) == (served, served), version
        assert (policy_for(vault, repository) is DEFAULT_POLICY) is (not served), version
    append_config_toml(paths.root, "[router]\nenabled = false\n")
    off = load_vault(paths.root)
    assert off.config.algorithms.algorithm_version == "mvp-0.23"
    assert (router_active(off), bridge_active(off)) == (False, False)
    assert policy_for(off, repository) is DEFAULT_POLICY
    # With the plan off there is no plan to compose; the bridge still acts.
    set_algorithm_version(paths, "mvp-0.23")
    plan_off = create_placement_vault(tmp_path / "plan_off", version="mvp-0.23")
    append_config_toml(plan_off.root, "[plan]\nenabled = false\n")
    vault = load_vault(plan_off.root)
    assert (router_active(vault), bridge_active(vault)) == (False, True)


def test_upgrade_from_mvp022_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.22")
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
        decisions_before = connection.execute("SELECT * FROM router_decisions ORDER BY id").fetchall()

    result = upgrade_to_mvp023(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.22", "mvp-0.23")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.23"
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.23"
    assert router_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        assert connection.execute("SELECT * FROM router_decisions ORDER BY id").fetchall() == decisions_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.22" in manifests


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp023(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp023(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.23"), result.problems
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-13:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                              "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23"]


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp023(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.23"), result.problems
    assert any("advisory" in note for note in result.notes)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.23"


def test_chained_notes_pass_through_an_upgrade_and_a_refusal(tmp_path, monkeypatch):
    from learnloop import router_staged_upgrade

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.21")
    original = router_staged_upgrade.upgrade_to_mvp022

    def noted(root, **kwargs):
        result = original(root, **kwargs)
        result.notes.append("earlier advisory guard")
        return result

    monkeypatch.setattr(router_staged_upgrade, "upgrade_to_mvp022", noted)
    result = upgrade_to_mvp023(paths.root, clock=CLOCK)
    assert result.upgraded and result.notes == ["earlier advisory guard"]

    def refusing(root, **kwargs):
        return UpgradeResult(upgraded=False, from_version="mvp-0.21", to_version="mvp-0.22",
                             problems=["vault is busy"], notes=["earlier advisory guard"])

    later = create_placement_vault(tmp_path / "later", version="mvp-0.21")
    monkeypatch.setattr(router_staged_upgrade, "upgrade_to_mvp022", refusing)
    refused = upgrade_to_mvp023(later.root, clock=CLOCK)
    assert refused.upgraded is False and refused.notes == ["earlier advisory guard"]
    assert refused.problems == ["mvp-0.22 step refused: vault is busy"]
    assert load_vault(later.root).config.algorithms.algorithm_version == "mvp-0.21"


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp023(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.22'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.23")
    already = upgrade_to_mvp023(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.23"]


def test_upgrade_through_the_chain_from_earlier_successors(tmp_path):
    for version in ("mvp-0.16", "mvp-0.20", "mvp-0.21"):
        paths = create_placement_vault(tmp_path / version, version=version)
        result = upgrade_to_mvp023(paths.root, clock=CLOCK)
        assert (result.upgraded, result.from_version, result.to_version) == (True, version, "mvp-0.23"), result.problems


def test_upgrade_command_defaults_to_the_latest(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.22")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"mvp-0.22 -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.34"
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.20")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.23"])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == "mvp-0.23"
    # --to mvp-0.22 still reaches the Decider, not the router.
    earlier = create_placement_vault(tmp_path / "earlier", version="mvp-0.21")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(earlier.root), "--to", "mvp-0.22"])
    assert result.exit_code == 0, result.output
    assert load_vault(earlier.root).config.algorithms.algorithm_version == "mvp-0.22"


def test_new_vaults_start_at_the_router_successor(tmp_path):
    """Owner decision 2026-10-12: new vaults start at LATEST_ALGORITHM_VERSION."""

    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    # mvp-0.24 since router R2b + R2c merged; it keeps the staged frame (the
    # mixture's default mode serves on top of it).
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.34"
    assert fresh.config.router.enabled and fresh.config.router.mode == "mixture"
    assert router_active(fresh)


def test_defaults_fingerprints_are_recorded_for_every_successor():
    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture (a backup-API copy): raw
    history kept, upgrade, FK check, doctor, and an idempotent rebuild."""

    before_hash = hashlib.sha256((HEAD / "state.sqlite").read_bytes()).hexdigest()
    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    _set_algorithm_version_at(root, "mvp-0.22")
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
    result = upgrade_to_mvp023(root, clock=CLOCK)
    assert result.upgraded, result.problems
    after = snapshot(raw_roles)
    for table, rows in raw.items():
        assert all(row in after[table] for row in rows), table
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"plan_presentations", "router_decision_payloads"} <= tables
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error"
        and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan", "router", "learner"))
    ]
    assert errors == []
    vault = load_vault(root)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot((TableRole.DERIVED,))
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot((TableRole.DERIVED,)) == second
    assert upgrade_to_mvp023(root, clock=CLOCK).upgraded is False
    assert hashlib.sha256((HEAD / "state.sqlite").read_bytes()).hexdigest() == before_hash


def test_the_routers_decider_route_is_never_a_tier1_judgment_at_the_successor(tmp_path):
    """Plan §4 (the Decider migration's composition): the router's own Decider
    route never takes Tier 1's generic LLM fallback. R2a calls no model; this
    pins that mvp-0.23 keeps the rule for R2b."""

    from learnloop.decider_judgments import enabled

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.23")
    config = load_vault(paths.root).config
    assert not enabled(config, "router_decider")
    assert not enabled(config, "router_llm")
