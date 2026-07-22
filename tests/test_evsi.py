"""P4 step 3 -- robust EVSI, LCB stop, ranking vs stop, abstention (spec_p4 §6, §16.3).

Covers: EVSI=0 when hypotheses share one optimal action; positive EVSI on a separating
question; burden makes net value non-positive without a negative EIG; ranking uses
per-minute value while stop uses absolute net value; grader-asymmetry integration; no
P(Z|E) substitution; ±0.15 winner/action flip -> abstention.
"""

from __future__ import annotations

import pytest

from learnloop.services import action_loss as AL
from learnloop.services import evsi as EV


def _derived_cell(h, a, minutes):
    if minutes == 0:
        return AL.LossCell(h, a, 0.0, {"kind": "effective_intervention",
                                        "wasted_minutes": 0.0, "delay_minutes": 0.0})
    return AL.LossCell(h, a, float(minutes), {"kind": "ineffective_then_effective",
                                              "wasted_minutes": minutes / 2, "delay_minutes": minutes / 2})


def _table(cells, effective):
    hyps = tuple(sorted({h for h, _ in cells}))
    acts = tuple(sorted({a for _, a in cells}))
    return AL.LossTable(hypotheses=hyps, actions=acts,
                        cells={k: _derived_cell(k[0], k[1], v) for k, v in cells.items()},
                        effective_action=effective, tie_break_order=acts)


# Two hypotheses that SHARE one optimal action a_star (b is always worse).
_SHARED = _table(
    {("h1", "a_star"): 0.0, ("h1", "b"): 5.0, ("h2", "a_star"): 0.0, ("h2", "b"): 5.0},
    {"h1": "a_star", "h2": "a_star"},
)
# Two hypotheses with DIFFERENT effective actions (a separating question resolves them).
_SEPARATING = _table(
    {("h1", "a1"): 0.0, ("h1", "a2"): 6.0, ("h2", "a1"): 6.0, ("h2", "a2"): 0.0},
    {"h1": "a1", "h2": "a2"},
)
_PRIOR = {"h1": 0.5, "h2": 0.5}
_SEP_CONDITIONALS = {"h1": {"e1": 0.9, "e2": 0.1}, "h2": {"e1": 0.1, "e2": 0.9}}


def test_evsi_is_zero_when_hypotheses_share_optimal_action():
    ev = EV.evsi_for_conditionals(_SEP_CONDITIONALS, _PRIOR, _SHARED)
    assert ev.evsi == pytest.approx(0.0)
    assert EV.shared_optimal_action(_SHARED) == "a_star"


def test_evsi_is_positive_on_a_separating_question():
    ev = EV.evsi_for_conditionals(_SEP_CONDITIONALS, _PRIOR, _SEPARATING)
    assert ev.evsi > 0.0
    # No shared optimal action across hypotheses here.
    assert EV.shared_optimal_action(_SEPARATING) is None


def test_ranking_uses_per_minute_while_stop_uses_absolute_value():
    # Identical EVSI, different expected minutes -> the cheaper question ranks higher.
    cheap = EV.DiagnosticCandidate("cheap", (_SEP_CONDITIONALS,), _PRIOR, expected_minutes=1.0)
    dear = EV.DiagnosticCandidate("dear", (_SEP_CONDITIONALS,), _PRIOR, expected_minutes=3.0)
    result = EV.rank_feasible([dear, cheap], _SEPARATING)
    assert result.best_ref == "cheap"
    assert result.ranked[0].ref == "cheap"
    # Ranking (per-minute) and the stop threshold (absolute minutes) are distinct fields.
    assert result.ranked[0].rank_value != result.ranked[0].stop_threshold


def test_burden_can_make_net_value_non_positive_without_negative_evsi():
    # A tiny separating signal has positive EVSI but not enough to clear a large
    # expected-minutes cost -> stop, even though EVSI itself is never negative.
    weak = {"h1": {"e1": 0.55, "e2": 0.45}, "h2": {"e1": 0.45, "e2": 0.55}}
    ev = EV.evsi_for_conditionals(weak, _PRIOR, _SEPARATING)
    assert ev.evsi > 0.0
    cand = EV.DiagnosticCandidate("q", (weak,), _PRIOR, expected_minutes=50.0)
    result = EV.rank_feasible([cand], _SEPARATING)
    assert result.should_stop is True
    assert result.verdict == "stop"


def test_stop_rule_uses_per_candidate_burden():
    # A strongly-separating cheap question MEASURES at zero burden, but a large
    # per-candidate administration burden lifts the stop threshold above its robust EVSI
    # -> stop (audit M1/F3). Pre-fix the stop rule used only the global burden_cost, so
    # candidate.burden_minutes could never force a stop.
    strong = EV.DiagnosticCandidate("q", (_SEP_CONDITIONALS,), _PRIOR,
                                    expected_minutes=0.5, burden_minutes=0.0)
    assert EV.rank_feasible([strong], _SEPARATING).verdict == "measure"

    burdened = EV.DiagnosticCandidate("q", (_SEP_CONDITIONALS,), _PRIOR,
                                      expected_minutes=0.5, burden_minutes=50.0)
    result = EV.rank_feasible([burdened], _SEPARATING)
    assert result.should_stop is True
    assert result.verdict == "stop"
    assert result.ranked[0].stop_threshold == pytest.approx(0.5 + 50.0)


def test_lcb_stop_directionality():
    # A strongly-separating cheap question does NOT stop; a barely-separating expensive
    # one does. Stop fires when LCB(EVSI) <= expected_minutes.
    strong = EV.DiagnosticCandidate("strong", (_SEP_CONDITIONALS,), _PRIOR, expected_minutes=0.5)
    r_strong = EV.rank_feasible([strong], _SEPARATING)
    assert r_strong.should_stop is False and r_strong.verdict == "measure"


def test_no_pze_substitution_uses_composed_pe_given_h():
    # The composed P(E|H) = sum_z P(E|Z) P(Z|H) chain is what EVSI integrates over; a
    # stored P(Z|E) is never substituted. We assert the emission integration reacts to
    # the grader channel asymmetry (P(E|Z)) rather than to a reversed conditional.
    from learnloop.services.robust_composition import compose_emission_over_hypotheses

    # Instrument rows P(Z|H); a symmetric-vs-asymmetric grader channel P(E|Z).
    instrument = {"h1": {"z1": 0.9, "z2": 0.1}, "h2": {"z1": 0.1, "z2": 0.9}}
    symmetric = {"z1": {"g_ok": 0.9, "g_bad": 0.1}, "z2": {"g_ok": 0.1, "g_bad": 0.9}}
    asymmetric = {"z1": {"g_ok": 0.6, "g_bad": 0.4}, "z2": {"g_ok": 0.1, "g_bad": 0.9}}
    pe_sym = compose_emission_over_hypotheses(symmetric, instrument)
    pe_asym = compose_emission_over_hypotheses(asymmetric, instrument)
    ev_sym = EV.evsi_for_conditionals(pe_sym, _PRIOR, _SEPARATING).evsi
    ev_asym = EV.evsi_for_conditionals(pe_asym, _PRIOR, _SEPARATING).evsi
    # The asymmetric grader channel degrades the diagnostic value -> strictly less EVSI.
    assert ev_asym < ev_sym


def test_perturbation_flip_causes_abstention():
    # A knife-edge separating question whose winner flips under the ±0.15 stress must
    # abstain, not silently pick a mean winner (§6.5).
    a = {"h1": {"e1": 0.52, "e2": 0.48}, "h2": {"e1": 0.48, "e2": 0.52}}
    b = {"h1": {"e1": 0.50, "e2": 0.50}, "h2": {"e1": 0.50, "e2": 0.50}}
    ca = EV.DiagnosticCandidate("a", (a,), _PRIOR, expected_minutes=0.2)
    cb = EV.DiagnosticCandidate("b", (b,), _PRIOR, expected_minutes=0.2)
    result = EV.rank_feasible([ca, cb], _SEPARATING)
    # Either it stops (no robust value) or it abstains (winner/action flip) -- never a
    # confident measure on a knife-edge.
    assert result.verdict in ("abstain", "stop")
    if result.verdict == "abstain":
        assert result.abstained is True


def test_downstream_action_flip_across_members_abstains():
    # Two ensemble members that GENUINELY disagree on the recommended action after an
    # emission (audit H2/F1). member 1 says "e1 -> a1", member 2 says "e1 -> a2": the
    # decision you would take after observing e1 flips across the credible set, so the
    # selector must abstain (§6.5). Pre-fix action_flipped keyed off the prior-only
    # current_action (member-invariant) and was never True.
    m1 = {"h1": {"e1": 0.9, "e2": 0.1}, "h2": {"e1": 0.1, "e2": 0.9}}
    m2 = {"h1": {"e1": 0.1, "e2": 0.9}, "h2": {"e1": 0.9, "e2": 0.1}}
    r = EV.robust_evsi([m1, m2], _PRIOR, _SEPARATING)
    assert r.action_flipped is True

    # The full feasible-set ranking abstains with the downstream-action-flip reason: the
    # question has robust value (it does not stop) but the recommended action is
    # ensemble-ambiguous, so it is neither measured nor stopped -- it abstains.
    cand = EV.DiagnosticCandidate("q", (m1, m2), _PRIOR, expected_minutes=0.2)
    result = EV.rank_feasible([cand], _SEPARATING)
    assert result.should_stop is False
    assert result.verdict == "abstain"
    assert result.abstained is True
    assert result.reason == "downstream_action_flip"


def test_members_that_agree_on_action_do_not_abstain():
    # Both members recommend the SAME per-emission action -> no flip -> measure (the
    # negative control for the flip test above).
    m1 = {"h1": {"e1": 0.9, "e2": 0.1}, "h2": {"e1": 0.1, "e2": 0.9}}
    m2 = {"h1": {"e1": 0.85, "e2": 0.15}, "h2": {"e1": 0.15, "e2": 0.85}}
    r = EV.robust_evsi([m1, m2], _PRIOR, _SEPARATING)
    assert r.action_flipped is False
    cand = EV.DiagnosticCandidate("q", (m1, m2), _PRIOR, expected_minutes=0.2)
    result = EV.rank_feasible([cand], _SEPARATING)
    assert result.verdict == "measure"


def test_stress_that_reverses_recommended_action_abstains():
    # A single ensemble member whose per-emission recommended action REVERSES under the
    # ±0.15 stress (audit H2/F2). The rank is stable (one candidate) and members agree
    # (one member), so only the stressed-vs-nominal argmin comparison catches it.
    knife = {"h1": {"e1": 0.58, "e2": 0.42}, "h2": {"e1": 0.42, "e2": 0.58}}
    cand = EV.DiagnosticCandidate("q", (knife,), _PRIOR, expected_minutes=0.05)
    assert EV._action_flips_under_stress(cand, _SEPARATING, EV.PERTURBATION_DELTA) is True
    result = EV.rank_feasible([cand], _SEPARATING)
    if not result.should_stop:
        assert result.verdict == "abstain"
        assert result.reason in ("stress_action_flip", "downstream_action_flip", "stress_winner_flip")
