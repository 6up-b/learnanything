"""The checkpoint-4 entry gate over a sample that can fail: forty planted episodes per type.

Five runs per type cannot tell a rate (refactor-k9.0.md §3(c): passing 3 of 5 happens with probability 0.68 at a
true rate of 0.6 and 0.50 at 0.5). Forty runs with a threshold of 26 (0.65) tell "at most a coin flip" (0.5) from
"about what the corrected path does" (0.75): a type whose rate is 0.5 passes with probability 4.0%, one at 0.75
fails with probability 5.4%. In the configuration where the robust completion gate decides (value of information
off; where value decides, label accuracy is not what the stop maximizes, see test_sim_probe_validation), on the same
runs as U-021's abstention budget. Each type is its own test so the gate's workers share the runs.

A seed fixes a run (the sim mints each run's ids, the episode id its ensembles seed on among them, from a stream the
seed fixes), so these are fixed numbers, not a sample of them: named (and acted on) correctly in 39, 37, 32, 30 and 33
of 40 (robust_initial_grasp, unfamiliar, surface_only, schema_without_transfer, confuses_with), every episode at its
budget of 4, none abstaining. A change that moves one moved the policy or the planted learner.
"""

from __future__ import annotations

import math

import pytest

from learnloop.diagnosis.robust_composition import ABSTENTION_BUDGET_FRACTION
from learnloop.sim.diagnostic_validation import PLANTED_TYPES, run_probe_validation

from tests.sim_probe_validation_helpers import _vault_with_confusable

SEEDS = tuple(range(11, 51))
THRESHOLD = 26


@pytest.mark.arc_close
@pytest.mark.parametrize("planted", PLANTED_TYPES)
def test_each_planted_type_is_named_in_at_least_26_of_40_episodes_within_the_abstention_budget(tmp_path, planted):
    vault_root = _vault_with_confusable(tmp_path)
    report = run_probe_validation(vault_root, tmp_path / "runs", planted_types=(planted,), seeds=SEEDS)
    assert len(report.results) == len(SEEDS)
    named = sum(result.label_matched for result in report.results)
    acted = sum(result.action_matched for result in report.results)
    misses = sorted((result.seed, result.diagnosed_label) for result in report.results if not result.label_matched)
    assert named >= THRESHOLD and acted >= THRESHOLD, (named, acted, misses)
    for result in report.results:
        assert result.completed and result.observations_used <= 4, result
    # U-021 holds per type here, which is stricter than over all episodes.
    abstained = [result.seed for result in report.results if result.completion_reason == "couldnt_reliably_distinguish"]
    assert len(abstained) <= math.floor(ABSTENTION_BUDGET_FRACTION * len(SEEDS)), abstained
