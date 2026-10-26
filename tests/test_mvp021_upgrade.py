"""mvp-0.21 (value-of-information stopping) is the next explicit successor.

mvp-0.9 -> mvp-0.10 (the split) -> mvp-0.11 (placement) -> mvp-0.12
(recurrence groups) -> mvp-0.13 (the stuck prompt) -> mvp-0.14 (the finite
daily plan) -> mvp-0.15 (probe ties) -> mvp-0.16 (the sooner check) ->
mvp-0.17 (the proofs route check, removed from serving) -> mvp-0.18 (the
answer-key gate) -> mvp-0.19 (source-first needs) -> mvp-0.20 (the route rules
in the grader) -> mvp-0.21 (four count caps lifted onto value of information,
and the probe hypothesis lane reading the diagnoser's verdict). The branch
built it as mvp-0.17 (a placeholder tag) and it was relabelled mvp-0.21 when
it merged after the route rules. The upgrade accepts mvp-0.20, or mvp-0.9 to
mvp-0.19 through mvp-0.20's own upgrade (below mvp-0.12, through T1's, whose
same-cause guard is advisory unless ``recurrence.require_guard = true``). It
changes serving only: the projection namespace is the same, nothing is
migrated by the upgrade and nothing is rewritten (playbook items 1, 3, 4
and 8). Tier 1's Decider judgments followed it as mvp-0.22, the latest
successor (``tests/test_mvp022_upgrade.py``).
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
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.attempts.grading_support import route_rules_active
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
from learnloop.diagnosis import voi_stopping as voi
from learnloop.ops.doctor import run_doctor
from learnloop.placement.state import gap_sooner_checks_active, placement_active
from learnloop.scheduling.scheduler import probe_ties_admitted
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.voi_stopping_upgrade import upgrade_to_mvp021

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.split_live_helpers import split_vault
from tests.test_recurrence_commands import _pass_guard

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_224"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_voi_successor_keeps_every_predecessor():
    assert VOI_STOPPING_ALGORITHM_VERSION == "mvp-0.21"
    # Tier 1's Decider judgments (mvp-0.22, tests/test_mvp022_upgrade.py) and
    # router R2a's staged frame (mvp-0.23, the latest successor,
    # tests/test_mvp023_upgrade.py) followed it.
    assert SUCCESSOR_CHAIN[-12] == VOI_STOPPING_ALGORITHM_VERSION
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.33"
    assert SUCCESSOR_CHAIN[-13] == ROUTE_RULES_ALGORITHM_VERSION
    assert VOI_STOPPING_VERSIONS == frozenset({"mvp-0.21", "mvp-0.22", "mvp-0.23", "mvp-0.24", "mvp-0.25", "mvp-0.26", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33"})
    # The chain is linear: mvp-0.21 means the split PLUS placement PLUS
    # recurrence groups PLUS the stuck prompt PLUS the plan PLUS probe ties
    # PLUS the sooner check PLUS the answer-key gate PLUS source-first needs
    # PLUS the route rules PLUS value-of-information stopping.
    for versions in (
        P0_SUCCESSOR_VERSIONS, P0_PROJECTION_VERSIONS, CANONICAL_STATE_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS,
        PLACEMENT_VERSIONS, RECURRENCE_GROUP_VERSIONS, STUCK_PROMPT_VERSIONS, DAILY_PLAN_VERSIONS,
        PROBE_TIE_VERSIONS, LEARNER_TEXT_GAP_VERSIONS, SOURCE_REFERENCE_GATE_VERSIONS,
        SOURCE_FIRST_NEEDS_VERSIONS, ROUTE_RULES_VERSIONS,
    ):
        assert VOI_STOPPING_ALGORITHM_VERSION in versions


def _flags(vault):
    return (
        split_grading_active(vault), placement_active(vault), plan_active(vault),
        probe_ties_admitted(vault.config), gap_sooner_checks_active(vault), route_rules_active(vault),
        voi.voi_stopping_active(vault.config), voi.probe_lane_reads_diagnosis(vault.config),
    )


def test_each_version_activates_exactly_its_features(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False, False, False, False, False, False, False),
        "mvp-0.10": (True, False, False, False, False, False, False, False),
        "mvp-0.11": (True, True, False, False, False, False, False, False),
        "mvp-0.14": (True, True, True, False, False, False, False, False),
        "mvp-0.15": (True, True, True, True, False, False, False, False),
        "mvp-0.16": (True, True, True, True, True, False, False, False),
        "mvp-0.17": (True, True, True, True, True, False, False, False),
        "mvp-0.18": (True, True, True, True, True, False, False, False),
        "mvp-0.19": (True, True, True, True, True, False, False, False),
        "mvp-0.20": (True, True, True, True, True, True, False, False),
        "mvp-0.21": (True, True, True, True, True, True, True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        assert _flags(load_vault(paths.root)) == flags, version
    vault = load_vault(paths.root)
    assert recurrence_active(vault)
    # Each part's kill switch keeps the version and every predecessor's
    # behaviour, and leaves the other part on.
    append_config_toml(paths.root, "[voi_stopping]\nenabled = false\n")
    part1_off = load_vault(paths.root)
    assert part1_off.config.algorithms.algorithm_version == "mvp-0.21"
    assert _flags(part1_off) == (True, True, True, True, True, True, False, True)
    append_config_toml(paths.root, "probe_lane_reads_diagnosis = false\n".join(["[diagnosis]\n", ""]))
    both_off = load_vault(paths.root)
    assert _flags(both_off) == (True, True, True, True, True, True, False, False)


def test_upgrade_from_mvp020_flips_rebuilds_and_rewrites_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.20")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()
        errors_before = connection.execute("SELECT * FROM error_events ORDER BY id").fetchall()

    result = upgrade_to_mvp021(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.20", "mvp-0.21")
    upgraded = load_vault(paths.root)
    assert upgraded.config.algorithms.algorithm_version == "mvp-0.21"
    assert all(_flags(upgraded))
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == "mvp-0.21"
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
        assert connection.execute("SELECT * FROM error_events ORDER BY id").fetchall() == errors_before
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert "mvp-0.20" in manifests


def test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required(tmp_path):
    """With ``recurrence.require_guard = true`` and the guard unrun, from
    mvp-0.10 the upgrade refuses and the vault stays where it was; once the
    guard passes it walks mvp-0.11 to mvp-0.20 (each freezing and rebuilding)
    to mvp-0.21."""

    paths, vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False,
                                           config="[recurrence]\nrequire_guard = true")
    refused = upgrade_to_mvp021(paths.root, clock=CLOCK)
    assert refused.upgraded is False
    assert refused.problems and all(problem.startswith("mvp-0.12 step refused: ") for problem in refused.problems)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"

    _pass_guard(tmp_path, vault, repository)
    result = upgrade_to_mvp021(paths.root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.10", "mvp-0.21"), result.problems
    upgraded = load_vault(paths.root)
    assert all(_flags(upgraded)) and recurrence_active(upgraded)
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
        rebuilds = [
            row[0]
            for row in connection.execute(
                "SELECT algorithm_version FROM derived_state_rebuilds "
                "WHERE scope = 'p0_projection_activation' ORDER BY created_at, id"
            )
        ]
    assert {"mvp-0.10", "mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16",
            "mvp-0.17", "mvp-0.18", "mvp-0.19", "mvp-0.20"} <= manifests
    assert rebuilds[-11:] == ["mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14", "mvp-0.15", "mvp-0.16", "mvp-0.17",
                              "mvp-0.18", "mvp-0.19", "mvp-0.20", "mvp-0.21"]


def test_by_default_the_chain_passes_the_advisory_guard_notes_on(tmp_path):
    """Owner batch 2 (2026-10-12): the guard is advisory by default, so the
    chained upgrade from mvp-0.10 reaches mvp-0.21 and passes the guard's
    status on as notes (through mvp-0.20's upgrade, which passes on the
    earlier links': chained_notes = list(chained.notes or []))."""

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    result = upgrade_to_mvp021(paths.root, clock=CLOCK)
    assert (result.upgraded, result.to_version) == (True, "mvp-0.21"), result.problems
    assert any("advisory" in note for note in result.notes)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.21"


def test_upgrade_through_the_chain_from_mvp016_to_mvp019(tmp_path):
    for version in ("mvp-0.16", "mvp-0.17", "mvp-0.19"):
        paths = create_placement_vault(tmp_path / version, version=version)
        result = upgrade_to_mvp021(paths.root, clock=CLOCK)
        assert (result.upgraded, result.from_version, result.to_version) == (True, version, "mvp-0.21"), result.problems


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp021(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.20'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, "mvp-0.21")
    already = upgrade_to_mvp021(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == ["vault is already mvp-0.21"]


def test_upgrade_command_defaults_to_the_latest(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.20")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"mvp-0.20 -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.33"
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.20")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", "mvp-0.21"])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == "mvp-0.21"
    # --to mvp-0.20 still reaches the route rules.
    earlier = create_placement_vault(tmp_path / "earlier", version="mvp-0.19")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(earlier.root), "--to", "mvp-0.20"])
    assert result.exit_code == 0, result.output
    assert load_vault(earlier.root).config.algorithms.algorithm_version == "mvp-0.20"


def test_new_vaults_start_at_a_successor_with_voi_stopping(tmp_path):
    """Owner decision 2026-10-12: new vaults start at LATEST_ALGORITHM_VERSION
    (mvp-0.23 since router R2a's staged frame merged), which keeps
    value-of-information stopping."""

    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION == "mvp-0.33"
    assert all(_flags(fresh))


def test_defaults_fingerprint_is_recorded_for_every_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text("mvp-0.21")))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.21"]
    section = config.voi_stopping
    assert section.enabled and section.probe_episodes and section.followups
    assert section.teach_back and section.project_probes
    assert config.diagnosis.probe_lane_reads_diagnosis and config.diagnosis.probe_lane_pending == "hold_out"
    # The former caps stay, as the kill-switch path.
    assert config.probe.episode.session_qualifying_observation_cap == 4
    assert config.scheduler.followup.max_interventions_per_lo_per_session == 1
    assert config.teach_back.session_cap == 1 and config.plan.project_probes_max_per_day == 4
    # Rank 4 (the measured unresolved cost) reaches the value rule's loss table
    # only behind EVSI calibration's own switch, off by default.
    assert config.evsi.measured_loss_enabled is False and config.evsi.forecast_logging is True


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture: upgrade, FK check,
    doctor, and an idempotent rebuild."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, "mvp-0.20")
    result = upgrade_to_mvp021(root, clock=CLOCK)
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

    # The first rebuild after an upgrade reaches the fixed point; from the
    # second on, rebuilds are idempotent.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second


def test_the_successor_rebuild_equals_mvp020s_projection(tmp_path):
    """The projection namespace is unchanged: a rebuild at mvp-0.21 writes the
    same derived state as one at mvp-0.20 (modulo the version stamps)."""

    def derived(version):
        root = tmp_path / version.replace(".", "_")
        copy_tree_with_databases(HEAD, root)
        from tests.helpers import _set_algorithm_version_at

        _set_algorithm_version_at(root, version)
        vault = load_vault(root)
        repository = Repository(root / "state.sqlite")
        rebuild_all_derived_state(vault, repository, clock=CLOCK)
        tables = sorted(set(tables_for_role(TableRole.DERIVED)))
        with connect(repository.sqlite_path, read_only=True) as connection:
            out = {}
            for table in tables:
                rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
                columns = [d[0] for d in connection.execute(f'SELECT * FROM "{table}" LIMIT 0').description]
                keep = [i for i, c in enumerate(columns) if c not in ("algorithm_version", "id", "created_at", "updated_at", "rebuilt_at")]
                out[table] = sorted((tuple(row[i] for i in keep) for row in rows), key=repr)
            return out

    assert derived("mvp-0.21") == derived("mvp-0.20")


def test_migration_200_lets_probe_episodes_record_a_value_stop(tmp_path):
    """Migration 200 (187 on the branch) rebuilds ``probe_episodes`` with the
    new completion reason and the decision column, keeping every index."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    with sqlite3.connect(root / "state.sqlite") as connection:
        schema = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'probe_episodes'").fetchone()[0]
        columns = {row[1] for row in connection.execute("PRAGMA table_info(probe_episodes)")}
        indexes = {row[1] for row in connection.execute("PRAGMA index_list(probe_episodes)")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    assert {200, 201} <= applied
    assert "'value_of_information_stop'" in schema and "'action_equivalent'" in schema
    assert {"completion_posterior_json", "completion_detail_json"} <= columns
    assert {"idx_probe_episodes_lo", "idx_probe_episodes_open", "idx_probe_episodes_target_version"} <= indexes
