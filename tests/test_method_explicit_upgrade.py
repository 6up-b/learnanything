"""The method-explicit successor (``mvp-0.25``) is the next explicit successor.

mvp-0.9 -> ... -> mvp-0.20 (the own-route rules in the grader) -> ... ->
mvp-0.24 (router R2b + R2c, the model mixture) -> mvp-0.25 (a criterion tied
to an item's required method is graded on use of that method:
``own-route-v2``). Built as the placeholder ``mvp-0.22-placeholder``, it was
relabelled mvp-0.25 at its merge after VOI v2 (mvp-0.21), the Decider
migration (mvp-0.22) and router R2a / R2b + R2c (mvp-0.23, mvp-0.24). The
upgrade accepts mvp-0.24, or mvp-0.9 to mvp-0.23 through mvp-0.24's own
upgrade (below mvp-0.12, through T1's, whose same-cause guard is advisory
unless ``recurrence.require_guard = true``), and passes the chained notes
through, a refusal's included. It changes what NEW blind grades persist only:
the projection namespace is the same and nothing is rewritten (playbook items
1, 3, 4 and 8).
"""

from __future__ import annotations

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
    LEARNER_TEXT_GAP_VERSIONS,
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    METHOD_EXPLICIT_VERSIONS,
    P0_PROJECTION_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    PLACEMENT_VERSIONS,
    PROBE_TIE_VERSIONS,
    RECURRENCE_GROUP_VERSIONS,
    ROUTE_RULES_VERSIONS,
    ROUTER_MIXTURE_ALGORITHM_VERSION,
    ROUTER_MIXTURE_VERSIONS,
    ROUTER_STAGED_FRAME_VERSIONS,
    SOURCE_FIRST_NEEDS_VERSIONS,
    SOURCE_REFERENCE_GATE_VERSIONS,
    STUCK_PROMPT_VERSIONS,
    SUCCESSOR_CHAIN,
    VOI_STOPPING_VERSIONS,
)
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.attempts.grading_support import method_rules_active, route_rules_active
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
from learnloop.method_explicit_upgrade import upgrade_to_method_explicit
from learnloop.ops.vault_upgrade import UpgradeResult
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

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_226"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))
TARGET = METHOD_EXPLICIT_ALGORITHM_VERSION


def test_the_successor_is_the_latest_and_keeps_every_predecessor():
    assert TARGET == "mvp-0.25"
    # Regrade contracts (mvp-0.26) followed it and keep it.
    assert SUCCESSOR_CHAIN[16] == TARGET and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.38"
    assert SUCCESSOR_CHAIN[15] == ROUTER_MIXTURE_ALGORITHM_VERSION == "mvp-0.24"
    assert METHOD_EXPLICIT_VERSIONS == frozenset({TARGET, "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33", "mvp-0.34", "mvp-0.35", "mvp-0.36", "mvp-0.37", LATEST_ALGORITHM_VERSION})
    # The chain is linear: it means every predecessor's semantics PLUS its own.
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
        PROBE_TIE_VERSIONS, LEARNER_TEXT_GAP_VERSIONS, SOURCE_REFERENCE_GATE_VERSIONS, SOURCE_FIRST_NEEDS_VERSIONS,
        ROUTE_RULES_VERSIONS, VOI_STOPPING_VERSIONS, DECIDER_TIER1_VERSIONS, ROUTER_STAGED_FRAME_VERSIONS,
        ROUTER_MIXTURE_VERSIONS,
    ):
        assert TARGET in versions
    assert ROUTER_MIXTURE_ALGORITHM_VERSION not in METHOD_EXPLICIT_VERSIONS


def test_each_version_activates_exactly_its_features(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False, False),
        "mvp-0.10": (True, False, False),
        "mvp-0.16": (True, False, False),
        "mvp-0.19": (True, False, False),
        "mvp-0.20": (True, True, False),
        "mvp-0.24": (True, True, False),
        TARGET: (True, True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (split_grading_active(vault), route_rules_active(vault), method_rules_active(vault)) == flags, version
    vault = load_vault(paths.root)
    assert placement_active(vault) and plan_active(vault) and probe_ties_admitted(vault.config)
    assert gap_sooner_checks_active(vault) and recurrence_active(vault)
    append_config_toml(paths.root, "[required_method]\nenabled = false\n")
    switched_off = load_vault(paths.root)
    # The kill switch keeps the version and every predecessor's behaviour.
    assert method_rules_active(switched_off) is False and route_rules_active(switched_off) is True
    assert switched_off.config.algorithms.algorithm_version == TARGET
    assert split_grading_active(switched_off) and placement_active(switched_off) and plan_active(switched_off)


def test_upgrade_from_mvp024_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.24")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
    items_before = {path: path.read_bytes() for path in sorted(paths.root.glob("subjects/*/practice-items/*.yaml"))}

    result = upgrade_to_method_explicit(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.24", TARGET)
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == TARGET
    assert method_rules_active(upgraded) and route_rules_active(upgraded) and plan_active(upgraded)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TARGET
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.24" in manifests
    # No item is edited: method-phrased criteria are repaired only by proposals.
    assert {path: path.read_bytes() for path in items_before} == items_before


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    """With ``recurrence.require_guard = true`` and the guard unrun, from
    mvp-0.10 the upgrade refuses and the vault stays where it was; once the
    guard passes it walks mvp-0.11 to mvp-0.24 to the successor."""

    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", TARGET), result.problems
    with sqlite3.connect(paths.sqlite_path) as connection:
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert rebuilds[-15:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                              "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24",
                              TARGET]


def test_by_default_the_chain_reports_the_advisory_guard_and_proceeds(tmp_path):
    """Owner batch 2: the guard is advisory, so the chained upgrade from
    mvp-0.10 reaches the successor and passes the guard's status on as notes
    (chained_notes = list(chained.notes or []))."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, TARGET), result.problems
    assert any("advisory" in note for note in result.notes)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TARGET


def test_chained_notes_pass_through_an_upgrade_and_a_refusal(tmp_path, monkeypatch):
    from learnloop import method_explicit_upgrade

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.23")
    original = method_explicit_upgrade.upgrade_to_mvp024

    def noted(root, **kwargs):
        result = original(root, **kwargs)
        result.notes.append("earlier advisory guard")
        return result

    monkeypatch.setattr(method_explicit_upgrade, "upgrade_to_mvp024", noted)
    result = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert result.upgraded and result.notes == ["earlier advisory guard"]

    def refusing(root, **kwargs):
        return UpgradeResult(upgraded=False, from_version="mvp-0.23", to_version="mvp-0.24",
                             problems=["vault is busy"], notes=["earlier advisory guard"])

    later = create_placement_vault(tmp_path / "later", version="mvp-0.23")
    monkeypatch.setattr(method_explicit_upgrade, "upgrade_to_mvp024", refusing)
    refused = upgrade_to_method_explicit(later.root, clock=CLOCK)
    assert refused.upgraded is False and refused.notes == ["earlier advisory guard"]
    assert refused.problems == ["mvp-0.24 step refused: vault is busy"]
    assert load_vault(later.root).config.algorithms.algorithm_version == "mvp-0.23"


def test_upgrade_through_the_chain_from_earlier_successors(tmp_path):
    for version in ("mvp-0.16", "mvp-0.20", "mvp-0.23"):
        paths = create_placement_vault(tmp_path / version, version=version)
        result = upgrade_to_method_explicit(paths.root, clock=CLOCK)
        assert (result.upgraded, result.from_version, result.to_version) == (True, version, TARGET), result.problems


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.24'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, TARGET)
    already = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == [f"vault is already {TARGET}"]


def test_upgrade_command_defaults_to_the_successor(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.24")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    # The default is the latest successor (regrade contracts, mvp-0.26), through this one.
    assert f"mvp-0.24 -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.38"
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.23")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.25"])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == TARGET
    # mvp-0.24 stays reachable explicitly.
    older = create_placement_vault(tmp_path / "older", version="mvp-0.23")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(older.root), "--to", "mvp-0.24"])
    assert result.exit_code == 0, result.output
    assert load_vault(older.root).config.algorithms.algorithm_version == "mvp-0.24"


def test_new_vaults_start_at_the_successor(tmp_path):
    """Owner decision 2026-10-12: new vaults start at LATEST_ALGORITHM_VERSION."""

    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    # Regrade contracts (mvp-0.26) are the latest and keep the method rules.
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.38"
    assert method_rules_active(fresh) and route_rules_active(fresh)


def test_defaults_fingerprint_is_recorded_for_the_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(TARGET)))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[TARGET]
    # The kill switch defaults on, beside the route rules' own switch; the
    # report's judge route is unset (the code-default decider when ready).
    assert config.required_method.enabled is True and config.proof_check.enabled is True
    assert config.ai.routing.rubric_phrasing_judge is None


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.24")
    result = upgrade_to_method_explicit(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error"
        and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan", "router", "learner",
                                   "required_method"))
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
