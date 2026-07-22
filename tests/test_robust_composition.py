"""P0.3 (spec_p0_measurement_correctness §4.2, §9.2/§9.3): robust composition,
deterministic ensemble, robust ranking/stop/agreement/abstention."""

from __future__ import annotations

import pytest

from learnloop.services import robust_composition as rc


def _alpha(diag: float, mass: float = 40.0) -> dict[str, dict[str, float]]:
    zs = ["s", "p", "o"]
    buckets = {"unknown": 0.05, "low": 0.15, "medium": 0.40, "high": 0.40}
    a: dict[str, dict[str, float]] = {}
    for z in zs:
        row: dict[str, float] = {}
        for g in zs:
            base = diag if g == z else (1 - diag) / 2
            for b, share in buckets.items():
                row[f"{g}|{b}"] = base * share * mass
        a[z] = row
    return a


_POSTERIOR = {"h1": 0.25, "h2": 0.25, "h3": 0.25, "h4": 0.25}
_DISCRIMINATING = {
    "h1": {"s": 0.9, "p": 0.05, "o": 0.05},
    "h2": {"s": 0.05, "p": 0.9, "o": 0.05},
    "h3": {"s": 0.05, "p": 0.05, "o": 0.9},
    "h4": {"s": 0.34, "p": 0.33, "o": 0.33},
}
_FLAT = {
    "h1": {"s": 0.4, "p": 0.3, "o": 0.3},
    "h2": {"s": 0.35, "p": 0.35, "o": 0.3},
    "h3": {"s": 0.33, "p": 0.33, "o": 0.34},
    "h4": {"s": 0.34, "p": 0.33, "o": 0.33},
}


def _ctx(tag: str) -> str:
    return rc.decision_context_hash(
        episode_id="e",
        candidate_card_version=tag,
        resolved_slot_map=None,
        posterior_at_selection=_POSTERIOR,
        projection_algorithm_version="mvp-0.8",
    )


def _ensemble(rows, tag: str, diag: float = 0.85) -> rc.Ensemble:
    return rc.build_ensemble(
        joint_alpha=_alpha(diag),
        instrument_rows=rows,
        calibration_model_hash="mh",
        decision_context_hash=_ctx(tag),
    )


def test_ensemble_is_deterministic_and_byte_stable():
    """Same pinned hashes -> identical ensemble members (§1.4, §9.1 replay)."""

    a = _ensemble(_DISCRIMINATING, "disc")
    b = _ensemble(_DISCRIMINATING, "disc")
    assert a.members == b.members
    assert a.seed == b.seed
    assert len(a.members) == rc.ROBUST_DRAW_COUNT + 1  # posterior mean + draws


def test_composition_marginalizes_true_class():
    """P(E|H) = sum_z P(E|Z) P(Z|H): a hypothesis pinned to one Z inherits that
    class's emission row."""

    emission = {"s": {"g_s": 1.0}, "p": {"g_p": 1.0}, "o": {"g_o": 1.0}}
    rows = {"h1": {"s": 1.0, "p": 0.0, "o": 0.0}}
    composed = rc.compose_emission_over_hypotheses(emission, rows)
    assert composed["h1"]["g_s"] == 1.0
    assert composed["h1"]["g_p"] == 0.0


def test_discriminating_instrument_wins_and_acts():
    """A discriminating instrument clears the 90% agreement gate with a positive
    robust advantage -> the action fires (§4.2 winner robustness + agreement)."""

    disc = _ensemble(_DISCRIMINATING, "disc")
    flat = _ensemble(_FLAT, "flat")
    decision = rc.evaluate_selection(
        candidates=[("disc", disc, 45.0), ("flat", flat, 45.0)], posterior=_POSTERIOR
    )
    assert decision.chosen_slot == "disc"
    assert decision.verdict == "act"
    assert decision.abstained is False
    assert decision.action_agreement_fraction >= rc.ENSEMBLE_ACTION_AGREEMENT_THRESHOLD
    assert decision.lcb_advantage_over_runner_up > 0.0


def test_indistinguishable_candidates_abstain():
    """Statistically tied candidates fail the robust winner test -> the selector
    abstains with 'couldnt_reliably_distinguish' rather than a fragile pick
    (§4.2, §9.3 bullet 1)."""

    tied = [
        ("c1", _ensemble(_FLAT, "c1"), 45.0),
        ("c2", _ensemble(_FLAT, "c2"), 45.0),
        ("c3", _ensemble(_FLAT, "c3"), 45.0),
    ]
    decision = rc.evaluate_selection(candidates=tied, posterior=_POSTERIOR)
    assert decision.abstained is True
    assert decision.verdict == "couldnt_reliably_distinguish"


def test_uninformative_instrument_triggers_stop():
    """When robust EVSI is below the time+burden cost, the stop rule fires (§4.2)."""

    flat = _ensemble(_FLAT, "flat")
    decision = rc.evaluate_selection(
        candidates=[("flat", flat, 45.0)], posterior=_POSTERIOR
    )
    assert decision.should_stop is True


def test_robust_quantile_is_lower_tail():
    assert rc.robust_quantile([0.1, 0.2, 0.3, 0.4, 0.5], 0.10) == 0.1
    assert rc.robust_quantile([], 0.10) == 0.0


def test_robust_quantile_uses_nearest_rank_ceil():
    """L4: nearest-rank (ceil) indexing -- idx = ceil(q*n)-1. For n=15, q=0.10,
    q*n=1.5 -> rank 2 -> the 2nd smallest value, not the 1st (the old floor idx)."""

    values = [v / 15 for v in range(1, 16)]  # 1/15 .. 15/15
    assert rc.robust_quantile(values, 0.10) == pytest.approx(2 / 15)
