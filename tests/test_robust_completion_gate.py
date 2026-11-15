"""The robust completion gate fixes in mvp-0.59 (refactor bug ledger D-39; docs/reviews/refactor-k9.0b.md).

Two faults made every unstable planted episode end ``couldnt_reliably_distinguish`` after two answers: the gate
ended the episode on a fragile *pick* although the robust stop rule said the next probe pays, and the robust
selector took a card's second item (an identical ensemble) as its winner's runner-up, so the winner's advantage
was exactly zero. Both are behind ``probe.episode.robust_gate_fixes`` at mvp-0.59; off, or at mvp-0.58, the gate
and the selector are the predecessor's exactly. Fakes and plain values only; no model call.
"""

from __future__ import annotations

import json

from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    FIGURE_WAIT_ALGORITHM_VERSION,
    ROBUST_GATE_FIX_VERSIONS,
)
from learnloop.config.kill_switches import TAGGED_SWITCHES
from learnloop.config.schema import LearnLoopConfig, ProbeEpisodeConfig
from learnloop.diagnosis.probe_episodes import robust_gate_completion
from learnloop.diagnosis.probe_robust import robust_gate_fixes_on
from learnloop.diagnosis.robust_composition import RobustDecision
from learnloop.params.parameter_registry import classify_config_path
from learnloop.sim.diagnostic_validation import run_probe_validation
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import vault_repository

from tests.sim_probe_validation_helpers import _vault_with_confusable

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
    run_root = tmp_path / "runs" / f"run_{planted}_{seed}"
    vault = load_vault(run_root)
    repository = vault_repository(VaultPaths(vault.root, vault.config))
    with repository.connection() as connection:
        gate_rows = connection.execute(
            "SELECT forecast_json FROM voi_forecasts WHERE site = 'probe_robust_selection' ORDER BY created_at, id"
        ).fetchall()
    return report.results[0], [json.loads(row[0]) for row in gate_rows]


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
