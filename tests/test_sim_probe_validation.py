"""Checkpoint-3 sim validation: planted latent hypothesis types drive the real
episode policy end to end (spec §14 Checkpoint 3.9, regression test 37).

The landing lane runs five seeds per type at the head, in the configuration
where the robust completion gate decides (value of information off), and, with
value of information on, a few seeds where the value stop decides. Per-type
label accuracy needs a sample that can fail: forty seeds per type, in
``tests/test_sim_planted_types_forty_seeds.py`` (arc close)."""

from __future__ import annotations

import copy
import pytest

from learnloop.diagnosis.robust_composition import ABSTENTION_BUDGET_FRACTION
from learnloop.sim.diagnostic_validation import PLANTED_TYPES, ValidationReport, run_probe_validation

from tests.sim_probe_validation_helpers import _vault_with_confusable, run_records

SEEDS = (11, 12, 13, 14, 15)


@pytest.fixture(scope="module")
def validation_runs(tmp_path_factory):
    root = tmp_path_factory.mktemp("planted-validation")
    vault_root = _vault_with_confusable(root)
    return run_probe_validation(vault_root, root / "runs", seeds=SEEDS), root / "runs"


@pytest.fixture(scope="module")
def validation_report(validation_runs):
    return validation_runs[0]


def test_planted_confuses_with_is_diagnosed_within_budget(validation_report):
    """Spec regression test 37: a planted confuses_with student is diagnosed
    within the observation budget with the matching instructional action."""

    report = ValidationReport(results=copy.deepcopy([row for row in validation_report.results if row.planted == "confuses_with" and row.seed in (11, 12, 13)]))
    summary = report.by_planted()["confuses_with"]
    assert summary["completed"] == 3
    assert summary["label_accuracy"] >= 2 / 3
    assert summary["action_accuracy"] >= 2 / 3
    assert summary["mean_observations"] <= 4.0
    for result in report.results:
        if result.label_matched:
            assert result.diagnosed_action == "contrastive_repair"


def test_every_planted_episode_completes_within_its_budget(validation_report):
    # Every requested run opened its episode (a run that opens none is listed, not judged).
    assert validation_report.refusal is None and validation_report.not_run == []
    assert len(validation_report.results) == len(PLANTED_TYPES) * len(SEEDS)
    # Selection, stopping, and accounting: every episode completed within its
    # observation budget through qualifying observations only.
    for result in validation_report.results:
        assert result.completed
        assert result.observations_used <= 4


def test_planted_episodes_abstain_within_the_abstention_budget(validation_report):
    """U-021 (spec_p0_measurement_correctness §4.2): the diagnostician abstains
    in at most ABSTENTION_BUDGET_FRACTION of episodes, and the planted-learner
    suite is where that budget is met. Every planted type here has an
    instrument that separates it, so an abstention is a stop rule's failure,
    not the learner's."""

    results = validation_report.results
    assert results
    abstained = [result for result in results if result.completion_reason == "couldnt_reliably_distinguish"]
    assert len(abstained) / len(results) <= ABSTENTION_BUDGET_FRACTION, [
        (result.planted, result.seed, result.observations_used) for result in abstained
    ]


def test_the_gate_ends_no_episode_whose_next_probe_pays(validation_runs):
    """The robust gate's logged decisions: where it said the next probe pays (``should_stop`` false), the episode
    went on asking; an episode the gate ended (``couldnt_reliably_distinguish``) ended on a fragile stop."""

    report, workdir = validation_runs
    checked = 0
    for result in report.results:
        _detail, gate = run_records(workdir, result.planted, result.seed)
        assert gate, (result.planted, result.seed)
        for decision in gate:
            if not decision["should_stop"]:
                checked += 1
                assert result.observations_used > decision["observations_so_far"], (result.planted, result.seed)
        if result.completion_reason == "couldnt_reliably_distinguish":
            assert gate[-1]["abstained"] and gate[-1]["should_stop"], (result.planted, result.seed)
    assert checked >= len(report.results)


def test_where_value_decides_each_stop_is_the_one_its_numbers_claim(tmp_path):
    """With value of information on (a vault's default) the value stop ends the episode, and per-type label
    accuracy is not what it maximizes (docs/reviews/refactor-k9.0.md §2.1). What it claims at the stop: no next
    probe, alone or in the lookahead's batches, is worth its minutes at the robust value's lower bound, and the
    robust gate's verdict is only the receipt's counterfactual."""

    vault_root = _vault_with_confusable(tmp_path, value_of_information=True)
    report = run_probe_validation(vault_root, tmp_path / "runs", seeds=(11, 12))
    assert len(report.results) == len(PLANTED_TYPES) * 2
    stops = 0
    for result in report.results:
        assert result.completion_reason != "couldnt_reliably_distinguish"
        detail, gate = run_records(tmp_path / "runs", result.planted, result.seed)
        assert gate == []
        if result.completion_reason != "value_of_information_stop":
            continue
        stops += 1
        assert detail["decision"] == "stop" and detail["reason"] == "lcb_evsi_below_minutes_cost"
        best = detail["best"]
        assert best["evsi_robust_minutes"] <= best["cost_minutes"]
        for batch in (detail.get("lookahead") or {}).get("tried", []):
            assert batch["evsi_robust_minutes"] <= batch["cost_minutes"]
        assert detail["former_cap"]["robust_completion_gate"]["switch"] == "voi_stopping.robust_gate_with_value"
    assert stops >= len(PLANTED_TYPES)
