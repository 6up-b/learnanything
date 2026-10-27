"""mvp-0.24 (router R2b + R2c, the model mixture on Today) is the next explicit successor.

mvp-0.9 -> ... -> mvp-0.22 (Tier 1's Decider judgments) -> mvp-0.23 (router
R2a, the staged frame) -> mvp-0.24: Today's next block drawn from the logged
model mixture (behind ``router.mode = "mixture"``, its default) and mid-block
follow-ups decided by the restraint (behind ``router.restraint``). Built as
a placeholder tag; it kept mvp-0.24 at its merge, nothing on main having
taken it. It changes what is served from now on, never the meaning of
recorded history, so the upgrade is a tag change plus an idempotent rebuild
of the same projection namespace. It accepts mvp-0.23,
or mvp-0.9 to mvp-0.22 through ``router_staged_upgrade.upgrade_to_mvp023``
(below mvp-0.12 through T1's advisory guard), and passes the chained notes
through, a refusal's included (playbook items 1, 3, 4 and 8).
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
    DECIDER_TIER1_VERSIONS,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    ROUTER_MIXTURE_ALGORITHM_VERSION,
    ROUTER_MIXTURE_VERSIONS,
    ROUTER_STAGED_FRAME_ALGORITHM_VERSION,
    ROUTER_STAGED_FRAME_VERSIONS,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_VERSIONS,
)
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
from learnloop.daily_plan.engine import DEFAULT_POLICY
from learnloop.daily_plan.policy import mixture_active, policy_for, router_active
from learnloop.daily_plan.router_chooser import RouterChooser
from learnloop.daily_plan.staged_frame import StagedChooser
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.ops.vault_upgrade import UpgradeResult
from learnloop.router_mixture_upgrade import upgrade_to_mvp024
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, _set_algorithm_version_at, append_config_toml, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_225"
CLOCK = FrozenClock(datetime(2026, 10, 14, 12, 0, tzinfo=UTC))


def test_the_mixture_successor_follows_the_staged_frame_and_keeps_every_predecessor():
    assert ROUTER_MIXTURE_ALGORITHM_VERSION == "mvp-0.24"
    assert SUCCESSOR_CHAIN[14:16] == (ROUTER_STAGED_FRAME_ALGORITHM_VERSION, ROUTER_MIXTURE_ALGORITHM_VERSION)
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.37"
    assert ROUTER_MIXTURE_VERSIONS == frozenset({"mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33", "mvp-0.34", "mvp-0.35", "mvp-0.36", "mvp-0.37"})
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, DAILY_PLAN_VERSIONS, VOI_STOPPING_VERSIONS, DECIDER_TIER1_VERSIONS,
        ROUTER_STAGED_FRAME_VERSIONS,
    ):
        assert ROUTER_MIXTURE_ALGORITHM_VERSION in versions
    assert ROUTER_STAGED_FRAME_ALGORITHM_VERSION not in ROUTER_MIXTURE_VERSIONS


def test_the_mixture_serves_only_at_the_successor_in_mixture_mode(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.23")
    repository = Repository(paths.sqlite_path)
    for version, served in (("mvp-0.22", False), ("mvp-0.23", False), ("mvp-0.24", True)):
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        # mode = "mixture" is the default at every version; it is dormant below mvp-0.24.
        assert vault.config.router.mode == "mixture"
        assert mixture_active(vault) is served, version
        chooser = policy_for(vault, repository).chooser
        if version == "mvp-0.22":
            assert policy_for(vault, repository) is DEFAULT_POLICY
        else:
            assert isinstance(chooser, RouterChooser if served else StagedChooser), version
    # router.mode = "staged" is R2a's pair exactly; router.enabled = false is DL1's.
    append_config_toml(paths.root, '[router]\nmode = "staged"\n')
    staged = load_vault(paths.root)
    assert staged.config.algorithms.algorithm_version == "mvp-0.24"
    assert router_active(staged) and not mixture_active(staged)
    assert isinstance(policy_for(staged, repository).chooser, StagedChooser)
    assert policy_for(staged, repository).restraint is None
    off = create_placement_vault(tmp_path / "off", version="mvp-0.24")
    append_config_toml(off.root, "[router]\nenabled = false\n")
    assert policy_for(load_vault(off.root), Repository(off.sqlite_path)) is DEFAULT_POLICY


def test_the_restraint_has_its_own_switch(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.24")
    repository = Repository(paths.sqlite_path)
    assert policy_for(load_vault(paths.root), repository).restraint is not None
    append_config_toml(paths.root, "[router]\nrestraint = false\n")
    assert policy_for(load_vault(paths.root), repository).restraint is None


def test_upgrade_from_mvp023_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.23")
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        decisions_before = connection.execute("SELECT * FROM router_decisions ORDER BY id").fetchall()
    result = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.23", "mvp-0.24")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.24"
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.24"
    assert mixture_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM router_decisions ORDER BY id").fetchall() == decisions_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.23" in manifests


def test_upgrade_through_the_chain_from_earlier_successors(tmp_path):
    for version in ("mvp-0.16", "mvp-0.21", "mvp-0.22"):
        paths = create_placement_vault(tmp_path / version, version=version)
        result = upgrade_to_mvp024(paths.root, clock=CLOCK)
        assert (result.upgraded, result.from_version, result.to_version) == (True, version, "mvp-0.24"), result.problems


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.24"), result.problems
    assert any("advisory" in note for note in result.notes)


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    """With ``recurrence.require_guard = true`` and the guard unrun, from
    mvp-0.10 the chain refuses at T1's mvp-0.12 step: the refusal names that
    step unprefixed through both later links and the vault keeps its version;
    with the guard passed, the whole chain runs to mvp-0.24."""

    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.24"), result.problems
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-14:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                              "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24"]


def test_chained_notes_pass_through_an_upgrade_and_a_refusal(tmp_path, monkeypatch):
    from learnloop import router_mixture_upgrade

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.22")
    original = router_mixture_upgrade.upgrade_to_mvp023

    def noted(root, **kwargs):
        result = original(root, **kwargs)
        result.notes.append("earlier advisory guard")
        return result

    monkeypatch.setattr(router_mixture_upgrade, "upgrade_to_mvp023", noted)
    result = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert result.upgraded and result.notes == ["earlier advisory guard"]

    def refusing(root, **kwargs):
        return UpgradeResult(upgraded=False, from_version="mvp-0.22", to_version="mvp-0.23",
                             problems=["vault is busy"], notes=["earlier advisory guard"])

    later = create_placement_vault(tmp_path / "later", version="mvp-0.22")
    monkeypatch.setattr(router_mixture_upgrade, "upgrade_to_mvp023", refusing)
    refused = upgrade_to_mvp024(later.root, clock=CLOCK)
    assert refused.upgraded is False and refused.notes == ["earlier advisory guard"]
    assert refused.problems == ["mvp-0.23 step refused: vault is busy"]
    assert load_vault(later.root).config.algorithms.algorithm_version == "mvp-0.22"


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.23'" in refused.problems[0]
    set_algorithm_version(paths, "mvp-0.24")
    already = upgrade_to_mvp024(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.24"]


def test_upgrade_command_defaults_to_the_latest(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.23")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    # The default is the latest successor (regrade contracts, mvp-0.26).
    assert f"mvp-0.23 -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.37"
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.21")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.24"])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == "mvp-0.24"
    # --to mvp-0.23 still reaches the staged frame alone.
    earlier = create_placement_vault(tmp_path / "earlier", version="mvp-0.22")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(earlier.root), "--to", "mvp-0.23"])
    assert result.exit_code == 0, result.output
    assert load_vault(earlier.root).config.algorithms.algorithm_version == "mvp-0.23"


def test_new_vaults_start_at_the_mixture_successor(tmp_path):
    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.37"
    router = fresh.config.router
    assert router.enabled and router.mode == "mixture" and router.restraint
    assert (router.k, router.epsilon_min, router.timeout_seconds, router.prefetch_timeout_seconds) == (6, 0.02, 8.0, 45.0)
    assert router.weights.model_dump() == {"staged": 1 / 3, "decider": 1 / 3, "llm": 1 / 3}
    assert router.max_daily_cost_usd == 5.0
    assert mixture_active(fresh)


def test_defaults_fingerprints_are_recorded_for_every_successor():
    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version


def test_the_floor_must_leave_room_for_the_draw(tmp_path):
    import pytest
    from pydantic import ValidationError

    from learnloop.config.schema import RouterConfig

    with pytest.raises(ValidationError, match="epsilon_min"):
        RouterConfig(k=6, epsilon_min=0.2)
    with pytest.raises(ValidationError):
        RouterConfig(weights={"staged": 0, "decider": 0, "llm": 0})


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture (a backup-API copy)."""

    before_hash = hashlib.sha256((HEAD / "state.sqlite").read_bytes()).hexdigest()
    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    _set_algorithm_version_at(root, "mvp-0.23")
    repository = Repository(root / "state.sqlite")
    result = upgrade_to_mvp024(root, clock=CLOCK)
    assert result.upgraded, result.problems
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    vault = load_vault(root)

    def derived():
        with sqlite3.connect(root / "state.sqlite") as connection:
            present = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            return {
                table: sorted((tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')), key=repr)
                for table in sorted(tables_for_role(TableRole.DERIVED)) if table in present
            }

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = derived()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert derived() == second
    assert upgrade_to_mvp024(root, clock=CLOCK).upgraded is False
    assert hashlib.sha256((HEAD / "state.sqlite").read_bytes()).hexdigest() == before_hash
