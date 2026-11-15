"""The robust completion gate fixes in mvp-0.59 (refactor bug ledger D-39; docs/reviews/refactor-k9.0b.md).

Two faults made every unstable planted episode end ``couldnt_reliably_distinguish`` after two answers: the gate
ended the episode on a fragile *pick* although the robust stop rule said the next probe pays, and the robust
selector took a card's second item (an identical ensemble) as its winner's runner-up, so the winner's advantage
was exactly zero. Both are behind ``probe.episode.robust_gate_fixes`` at mvp-0.59; off, or at mvp-0.58, the gate
and the selector are the predecessor's exactly. Fakes and plain values only; no model call.
"""

from __future__ import annotations

from datetime import timedelta

from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    FIGURE_WAIT_ALGORITHM_VERSION,
    ROBUST_GATE_FIX_VERSIONS,
)
from learnloop.clock import FrozenClock
from learnloop.config.kill_switches import TAGGED_SWITCHES
from learnloop.config.schema import LearnLoopConfig, ProbeEpisodeConfig
from learnloop.diagnosis.probe_episodes import robust_gate_completion
from learnloop.diagnosis.probe_robust import robust_gate_fixes_on
from learnloop.diagnosis.robust_composition import RobustDecision
from learnloop.instructional.valuation import CandidateInput, ValuationProblem, value_problem
from learnloop.ops.upgrades import upgrade
from learnloop.params.parameter_registry import classify_config_path
from learnloop.sim.diagnostic_validation import run_probe_validation
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import vault_repository

from tests.helpers import NOW
from tests.sim_probe_validation_helpers import _vault_with_confusable, run_records

TAG = FACET_BELIEF_FIX_ALGORITHM_VERSION
OLD = FIGURE_WAIT_ALGORITHM_VERSION
SWITCH = "probe.episode.robust_gate_fixes"


def _config(version: str, *, switch: bool = True) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    config.probe.episode.robust_gate_fixes = switch
    return config


def test_the_fixes_ride_on_mvp_0_59_behind_their_own_switch():
    assert TAG == "mvp-0.59" and OLD == "mvp-0.58"
    assert TAG in ROBUST_GATE_FIX_VERSIONS and OLD not in ROBUST_GATE_FIX_VERSIONS
    assert ProbeEpisodeConfig().robust_gate_fixes is True
    assert robust_gate_fixes_on(_config(TAG)) is True
    assert robust_gate_fixes_on(_config(TAG, switch=False)) is False
    assert robust_gate_fixes_on(_config(OLD)) is False
    assert any(row.path == SWITCH and row.tag == TAG and row.default is True for row in TAGGED_SWITCHES)
    rule = classify_config_path(SWITCH)
    assert rule is not None and rule.kind == "structural" and "robust completion gate" in rule.rationale


# -- fix 1: only a fragile stop ends the episode ------------------------------------------------------------------

_FRAGILE_PICK = RobustDecision("perturbation", 0.01, 0.0, 0.75, should_stop=False, abstained=True,
                               verdict="couldnt_reliably_distinguish")
_FRAGILE_STOP = RobustDecision("perturbation", 0.0001, 0.0, 0.75, should_stop=True, abstained=True,
                               verdict="couldnt_reliably_distinguish")
_ACT = RobustDecision("perturbation", 0.01, 0.002, 0.95, should_stop=False, abstained=False, verdict="act")
_STOP = RobustDecision("perturbation", 0.0001, 0.002, 0.95, should_stop=True, abstained=False, verdict="stop")


def test_a_fragile_pick_does_not_end_the_episode_and_a_fragile_stop_does():
    assert robust_gate_completion(_FRAGILE_PICK, stop_only=True) is None
    assert robust_gate_completion(_FRAGILE_STOP, stop_only=True) == "couldnt_reliably_distinguish"
    assert robust_gate_completion(_ACT, stop_only=True) is None
    assert robust_gate_completion(_STOP, stop_only=True) is None


def test_without_the_fix_every_abstention_ends_the_episode():
    assert robust_gate_completion(_FRAGILE_PICK, stop_only=False) == "couldnt_reliably_distinguish"
    assert robust_gate_completion(_FRAGILE_STOP, stop_only=False) == "couldnt_reliably_distinguish"
    assert robust_gate_completion(_ACT, stop_only=False) is None
    assert robust_gate_completion(_STOP, stop_only=False) is None


def _planted_run(tmp_path, *, version, switches_off=(), planted="surface_only", seed=12):
    """One planted episode in the sim's configuration (the gate decides: value of information off)."""

    vault_root = _vault_with_confusable(tmp_path / "source", version=version, switches_off=switches_off)
    report = run_probe_validation(vault_root, tmp_path / "runs", planted_types=(planted,), seeds=(seed,))
    assert len(report.results) == 1
    _detail, gate = run_records(tmp_path / "runs", planted, seed)
    return report.results[0], gate


def test_the_gate_does_not_end_a_planted_episode_whose_next_probe_pays(tmp_path):
    """surface_only, seed 12: after two answers the robust selector's winner (contrast) and runner-up
    (perturbation) are a real near-tie, so the pick is fragile, while the stop rule says the next probe pays.
    mvp-0.58 ended the episode there; the fixed gate keeps asking."""

    result, gate = _planted_run(tmp_path, version=TAG)
    first = gate[0]
    assert first["observations_so_far"] == 2
    assert first["abstained"] is True and first["should_stop"] is False
    assert result.completion_reason != "couldnt_reliably_distinguish"
    assert result.observations_used > 2
    # Every check the gate made before the end said the next probe pays.
    assert all(entry["should_stop"] is False for entry in gate)


def test_at_the_floor_the_gate_still_ends_the_episode_on_a_fragile_pick(tmp_path):
    result, gate = _planted_run(tmp_path, version=OLD)
    assert [(entry["observations_so_far"], entry["abstained"], entry["should_stop"]) for entry in gate] == [
        (2, True, False)
    ]
    assert (result.completion_reason, result.observations_used) == ("couldnt_reliably_distinguish", 2)
    assert (result.diagnosed_label, round(result.diagnosed_probability, 3)) == ("robust_initial_grasp", 0.838)


def test_with_the_switch_off_the_episode_is_the_floors_exactly(tmp_path):
    floor, floor_gate = _planted_run(tmp_path / "floor", version=OLD)
    off, off_gate = _planted_run(tmp_path / "off", version=TAG, switches_off=(SWITCH,))
    assert off.as_dict() == floor.as_dict()

    def decisions(gate):
        # The ensemble's seed names the episode's id, a fresh ULID per run, so the draws (and the agreement
        # fraction) differ between any two runs; what the gate decided does not.
        return [(e["observations_so_far"], e["verdict"], e["abstained"], e["should_stop"]) for e in gate]

    assert decisions(off_gate) == decisions(floor_gate)


# -- fix 2: the robust selection ranks distinct instruments ---------------------------------------------------------

_SLOTS = ("mastered", "misconception:m1", "unfamiliar")


def _twin_inputs():
    table = {slot: ({"hit": 0.95, "miss": 0.05} if slot == "misconception:m1" else {"hit": 0.05, "miss": 0.95})
             for slot in _SLOTS}
    return [CandidateInput(ref=ref, kind="item", members=tuple([table] * 3), outcome_alphabet=("hit", "miss"),
                           regime="item_point", likelihood_basis="estimated_row", expected_minutes=1.0,
                           construction="item_point:3") for ref in ("item_a", "item_b")]


def _twin_problem():
    return ValuationProblem(key="lo:x", space_kind="hypothesis_set", slots=_SLOTS,
                            prior={slot: 1 / 3 for slot in _SLOTS}, prior_basis="hypothesis_set", state_hash="h")


def test_the_valuation_licenses_a_card_whose_second_item_is_beside_it():
    report = value_problem(_twin_problem(), _twin_inputs(), distinct_instruments=True)
    alone = value_problem(_twin_problem(), _twin_inputs()[:1])
    assert report["verdict"] == "act" and report["checks"][0] == alone["checks"][0]
    # The second item is then valued as what it is to the model, a further independent answer given the first's
    # outcome, and is kept only while that clears the stop.
    assert [check["ref"] for check in report["checks"]] == ["item_a", "item_b"]


def test_without_the_fix_the_valuation_abstains_on_the_twin():
    report = value_problem(_twin_problem(), _twin_inputs())
    assert (report["verdict"], report["reason"], report["checks"]) == ("abstain", "couldnt_reliably_distinguish", [])


def test_the_gate_no_longer_reads_a_cards_second_item_as_its_rival(tmp_path):
    """schema_without_transfer, seed 11: after two answers the gate's winner is perturbation and its only fragility
    was the card's second perturbation item (the agreement gate passes); with distinct instruments it acts."""

    result, gate = _planted_run(tmp_path, version=TAG, planted="schema_without_transfer", seed=11)
    first = gate[0]
    assert first["observations_so_far"] == 2
    assert (first["verdict"], first["abstained"]) == ("act", False)
    assert first["lcb_advantage_over_runner_up"] > 0.0


def test_at_the_floor_the_twin_still_makes_the_pick_fragile(tmp_path):
    result, gate = _planted_run(tmp_path, version=OLD, planted="schema_without_transfer", seed=11)
    first = gate[0]
    assert (first["observations_so_far"], first["verdict"], first["lcb_advantage_over_runner_up"]) == (
        2, "couldnt_reliably_distinguish", 0.0
    )
    assert (result.completion_reason, result.observations_used) == ("couldnt_reliably_distinguish", 2)


# -- history: an episode completed before the fix keeps its completion --------------------------------------------

_RECORDED = (
    ("probe_episodes", "SELECT * FROM probe_episodes ORDER BY id"),
    ("probe_observations", "SELECT * FROM probe_observations ORDER BY id"),
    ("probe_presentations", "SELECT * FROM probe_presentations ORDER BY id"),
    ("voi_forecasts", "SELECT * FROM voi_forecasts ORDER BY id"),
)


def _recorded(run_root):
    vault = load_vault(run_root)
    repository = vault_repository(VaultPaths(vault.root, vault.config))
    with repository.connection() as connection:
        return {name: [tuple(row) for row in connection.execute(sql).fetchall()] for name, sql in _RECORDED}


def test_the_upgrade_to_the_fix_does_not_re_decide_a_recorded_episode(tmp_path):
    """surface_only seed 12 abstained after two answers at mvp-0.58 (a fragile pick). The upgrade to mvp-0.59, a
    whole-vault rebuild with the fixes on, replays the learner state but not the episode: its completion, its
    observations and presentations and the gate's logged forecast are the rows the floor wrote."""

    result, _gate = _planted_run(tmp_path, version=OLD)
    assert result.completion_reason == "couldnt_reliably_distinguish"
    run_root = tmp_path / "runs" / "run_surface_only_12"
    before = _recorded(run_root)
    outcome = upgrade(run_root, to=TAG, clock=FrozenClock(NOW + timedelta(days=1)))
    assert outcome.upgraded and not outcome.problems, outcome
    vault = load_vault(run_root)
    assert vault.config.algorithms.algorithm_version == TAG and robust_gate_fixes_on(vault.config)
    assert _recorded(run_root) == before
    repository = vault_repository(VaultPaths(vault.root, vault.config))
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=2)))
    assert _recorded(run_root) == before
