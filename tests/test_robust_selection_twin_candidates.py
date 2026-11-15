"""The robust selector's winner test against a second item of the same card.

Generated probe instances come in pairs per family card: two items whose
instrument rows, card and pinned channel are the same, so their composition
ensembles are identical member for member. The winner's per-draw advantage over
such a twin is exactly zero, so `evaluate_selection` calls the winner fragile and
abstains with ``couldnt_reliably_distinguish`` even when the instrument
separates the hypotheses well and its robust value is many times its cost. The
probe episode completes on that abstention (refactor bug ledger D-39: every
planted episode of the checkpoint-3 simulation ends this way at its first
check, with its next observation worth 9 to 20 times its minutes).
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


@pytest.mark.xfail(strict=True, reason="refactor bug ledger D-39: a tie with a second item of the same card is read "
                                       "as a fragile winner, so the selector abstains")
def test_a_second_item_of_the_same_card_does_not_make_the_winner_fragile():
    """Adding the card's second item changes nothing a learner could gain: it
    measures the same thing. The decision must stay the lone item's."""

    ensemble = _card_ensemble()
    decision = rc.evaluate_selection(
        candidates=[("item_a", ensemble, 50.0), ("item_b", ensemble, 50.0)], posterior=_POSTERIOR
    )
    assert decision.should_stop is False
    assert decision.abstained is False
    assert decision.verdict == "act"
