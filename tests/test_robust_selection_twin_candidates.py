"""The robust selector's winner test against a second item of the same card.

Generated probe instances come in pairs per family card: two items whose
instrument rows, card and pinned channel are the same, so their composition
ensembles are identical member for member. The winner's per-draw advantage over
such a twin is exactly zero, so `evaluate_selection` calls the winner fragile and
abstains with ``couldnt_reliably_distinguish`` even when the instrument
separates the hypotheses well and its robust value is many times its cost. The
probe episode completed on that abstention (refactor bug ledger D-39: every
planted episode of the checkpoint-3 simulation ended this way at its first
check, with its next observation worth 9 to 20 times its minutes). With the
robust gate fixes (mvp-0.59) the selectors rank distinct instruments
(``distinct_instruments``); without them they are mvp-0.58's exactly.
"""

from __future__ import annotations

import pytest

from learnloop.diagnosis import robust_composition as rc

_POSTERIOR = {"h1": 0.4, "h2": 0.35, "h3": 0.25}
# Strongly separating: each hypothesis puts most of its mass on its own class.
_SEPARATING = {
    "h1": {"s": 0.9, "p": 0.05, "o": 0.05},
    "h2": {"s": 0.05, "p": 0.9, "o": 0.05},
    "h3": {"s": 0.05, "p": 0.05, "o": 0.9},
}


def _informative_channel(mass: float = 40.0) -> dict[str, dict[str, float]]:
    classes = ("s", "p", "o")
    return {
        z: {f"{g}|high": (0.85 if g == z else 0.075) * mass for g in classes}
        for z in classes
    }


def _card_ensemble() -> rc.Ensemble:
    # One card: the decision context hash names the card, not the item, so both
    # items of the card get this same ensemble.
    context = rc.decision_context_hash(
        episode_id="episode",
        candidate_card_version="card_perturbation:1",
        resolved_slot_map={label: label for label in _POSTERIOR},
        posterior_at_selection=_POSTERIOR,
        projection_algorithm_version="mvp-0.8",
    )
    return rc.build_ensemble(
        joint_alpha=_informative_channel(),
        instrument_rows=_SEPARATING,
        calibration_model_hash="channel",
        decision_context_hash=context,
    )


def test_the_separating_card_alone_acts():
    """The control: one item of the card is a robust winner and acts."""

    decision = rc.evaluate_selection(candidates=[("item_a", _card_ensemble(), 50.0)], posterior=_POSTERIOR)
    assert decision.should_stop is False
    assert decision.verdict == "act"


def test_a_second_item_of_the_same_card_does_not_make_the_winner_fragile():
    """Adding the card's second item changes nothing a learner could gain: it
    measures the same thing. The decision must stay the lone item's."""

    ensemble = _card_ensemble()
    alone = rc.evaluate_selection(candidates=[("item_a", ensemble, 50.0)], posterior=_POSTERIOR)
    decision = rc.evaluate_selection(
        candidates=[("item_a", ensemble, 50.0), ("item_b", ensemble, 50.0)], posterior=_POSTERIOR,
        distinct_instruments=True,
    )
    assert decision.should_stop is False
    assert decision.abstained is False
    assert decision.verdict == "act"
    assert decision == alone


def test_without_the_fix_the_twin_makes_the_winner_fragile():
    """mvp-0.58's selector, exactly: the twin is the runner-up and the advantage is exactly zero."""

    ensemble = _card_ensemble()
    decision = rc.evaluate_selection(
        candidates=[("item_a", ensemble, 50.0), ("item_b", ensemble, 50.0)], posterior=_POSTERIOR
    )
    assert decision == rc.RobustDecision("item_a", decision.robust_eig_per_second, 0.0, 1.0, False, True,
                                         "couldnt_reliably_distinguish")


def test_a_distinct_rival_is_still_compared():
    """Only identical ensembles collapse: a different card stays the runner-up, so
    its near-tie still makes the winner fragile."""

    ensemble = _card_ensemble()
    other_context = rc.decision_context_hash(
        episode_id="episode", candidate_card_version="card_contrast:1",
        resolved_slot_map={label: label for label in _POSTERIOR}, posterior_at_selection=_POSTERIOR,
        projection_algorithm_version="mvp-0.8",
    )
    rival = rc.build_ensemble(joint_alpha=_informative_channel(), instrument_rows=_SEPARATING,
                              calibration_model_hash="channel", decision_context_hash=other_context)
    candidates = [("item_a", ensemble, 50.0), ("item_b", ensemble, 50.0), ("contrast", rival, 50.0)]
    fixed = rc.evaluate_selection(candidates=candidates, posterior=_POSTERIOR, distinct_instruments=True)
    pair = rc.evaluate_selection(candidates=[candidates[0], candidates[2]], posterior=_POSTERIOR)
    assert fixed == pair
    assert fixed.abstained is True and fixed.lcb_advantage_over_runner_up != 0.0


def _series_candidates():
    ensemble = _card_ensemble()
    series = [rc.expected_information_gain(member, _POSTERIOR) for member in ensemble.members]
    return series, [("item_a", series, 50.0), ("item_b", list(series), 50.0)]


def test_identical_credible_sets_are_one_instrument_to_the_series_selection():
    series, candidates = _series_candidates()
    alone = rc.evaluate_series_selection(candidates=candidates[:1])
    fixed = rc.evaluate_series_selection(candidates=candidates, distinct_instruments=True)
    assert fixed == alone and fixed.verdict == "act"
    ensemble = _card_ensemble()
    sets = rc.evaluate_selection_credible_sets(
        candidates=[("item_a", ensemble, 50.0), ("item_b", ensemble, 50.0)], posterior=_POSTERIOR,
        distinct_instruments=True,
    )
    assert sets == alone


def test_without_the_fix_identical_credible_sets_make_the_winner_fragile():
    series, candidates = _series_candidates()
    decision = rc.evaluate_series_selection(candidates=candidates)
    assert decision.abstained is True and decision.lcb_advantage_over_runner_up <= 0.0
    assert decision.verdict == "couldnt_reliably_distinguish"
