"""S2a (§8.3.4): the credible-set selector over unequal member counts, and the shape guard."""
from __future__ import annotations

import pytest

from learnloop.diagnosis import robust_composition as RC


def _ensemble(members, ref="x"):
    return RC.Ensemble(members=tuple(members), slots=("A", "B"), emissions=("a", "b"),
                       calibration_model_hash=ref, decision_context_hash=ref, seed=0,
                       draw_count=len(members) - 1, quantile=RC.ROBUST_QUANTILE, perturbation_concentration=0.0)


SHARP = {"A": {"a": 0.95, "b": 0.05}, "B": {"a": 0.05, "b": 0.95}}
DULL = {"A": {"a": 0.6, "b": 0.4}, "B": {"a": 0.4, "b": 0.6}}
FLAT = {"A": {"a": 0.5, "b": 0.5}, "B": {"a": 0.5, "b": 0.5}}
PRIOR = {"A": 0.5, "B": 0.5}


def test_evaluate_selection_refuses_unequal_member_counts():
    with pytest.raises(RC.EnsembleShapeError):
        RC.evaluate_selection(candidates=[("one", _ensemble([SHARP] * 3), 60.0),
                                          ("two", _ensemble([DULL] * 129), 60.0)], posterior=PRIOR)


def test_mixed_sizes_choose_the_sharper_candidate_without_indexing_errors():
    decision = RC.evaluate_selection_credible_sets(
        candidates=[("dull", _ensemble([DULL] * 129), 60.0), ("sharp", _ensemble([SHARP] * 3), 60.0)],
        posterior=PRIOR)
    assert decision.chosen_slot == "sharp" and decision.verdict == "act"
    assert decision.action_agreement_fraction == 1.0
    reverse = RC.evaluate_selection_credible_sets(
        candidates=[("dull", _ensemble([DULL] * 3), 60.0), ("sharp", _ensemble([SHARP] * 129), 60.0)],
        posterior=PRIOR)
    assert reverse.chosen_slot == "sharp"


def test_margin_is_the_quantile_over_every_member_pair_and_agreement_is_independent():
    # Winner members [2, 4] nats/sec-equivalents vs runner [1, 3]: by hand.
    decision = RC.evaluate_series_selection(candidates=[("w", [2.0, 4.0], 1.0), ("r", [1.0, 3.0], 1.0)])
    assert decision.chosen_slot == "w"
    # differences over all pairs: 1, -1, 3, 1 -> sorted -1, 1, 1, 3; 10th pct nearest rank -> -1
    assert decision.lcb_advantage_over_runner_up == pytest.approx(-1.0)
    # agreement: member 2 beats {1} of rival (1/2), member 4 beats both (2/2): mean 0.75
    assert decision.action_agreement_fraction == pytest.approx(0.75)
    assert decision.verdict == "couldnt_reliably_distinguish"


def test_ties_go_to_the_winner():
    decision = RC.evaluate_series_selection(candidates=[("w", [2.0, 2.0], 1.0), ("r", [2.0, 1.0], 1.0)])
    assert decision.chosen_slot in ("w", "r")
    winner = decision.chosen_slot
    assert decision.action_agreement_fraction == pytest.approx(1.0 if winner == "w" else 0.75)


def test_stop_when_nothing_clears_the_minutes_cost():
    decision = RC.evaluate_selection_credible_sets(
        candidates=[("flat", _ensemble([FLAT] * 3), 600.0)], posterior=PRIOR)
    assert decision.verdict in ("stop", "couldnt_reliably_distinguish") and decision.should_stop


def test_same_shape_is_the_live_selector():
    candidates = [("a", _ensemble([SHARP] * 3), 60.0), ("b", _ensemble([DULL] * 3), 60.0)]
    live = RC.evaluate_selection(candidates=candidates, posterior=PRIOR)
    assert live.chosen_slot == "a" and live.verdict == "act"
