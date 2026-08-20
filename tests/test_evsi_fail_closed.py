"""EVSI-1 hardening: the fail-closed input contracts (decision-value spec inv. 5/6).

Covers: a missing loss cell may never read as 0.0 (0.0 is the reserved
"effective repair" value, so an omission would win argmin ties); a route-less
hypothesis is named, never silently dropped-and-renormalized; a zero-mass prior
is refused, never replaced with an invented uniform; every positive-mass
hypothesis (H_OTHER included) needs both a loss row and a likelihood row;
`rank_feasible` turns those defects into typed exclusions/abstentions, never a
live probe; and the shared candidate order is deterministic and status-first.
"""

from __future__ import annotations

import pytest

from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import evsi as EV
from learnloop.diagnosis.causal_probe_coherence import order_probe_candidates

_ROUTES = [
    {"reason": "memory_lapse", "first_intervention": "reveal_reconstruct"},
    {"reason": "false_belief_or_confusion", "first_intervention": "contrast_counterexample"},
]
_OVERRIDES = {"reveal_reconstruct": 2.0, "contrast_counterexample": 4.0}

_CONDITIONALS = {
    "memory_lapse": {"pass": 0.9, "fail": 0.1},
    "false_belief_or_confusion": {"pass": 0.2, "fail": 0.8},
}
_PRIOR = {"memory_lapse": 0.6, "false_belief_or_confusion": 0.4}


def _table() -> AL.LossTable:
    return AL.build_loss_table(routes=_ROUTES, duration_overrides=_OVERRIDES)


# ---------------------------------------------------------------------------
# action_loss fail-closed
# ---------------------------------------------------------------------------


def test_missing_loss_cell_raises_instead_of_impersonating_the_effective_repair():
    table = _table()
    partial = AL.LossTable(
        hypotheses=table.hypotheses,
        actions=table.actions,
        cells={
            key: cell
            for key, cell in table.cells.items()
            if key != ("memory_lapse", "contrast_counterexample")
        },
        effective_action=table.effective_action,
    )
    with pytest.raises(AL.LossTableIncompleteError) as caught:
        partial.loss("memory_lapse", "contrast_counterexample")
    assert caught.value.reason == "missing_loss_cell"
    # The omission must not leak through the aggregates either.
    with pytest.raises(AL.LossTableIncompleteError):
        partial.expected_loss("contrast_counterexample", _PRIOR)


def test_routeless_hypothesis_fails_closed_instead_of_silently_dropping():
    with pytest.raises(AL.LossTableIncompleteError) as caught:
        AL.build_loss_table(
            routes=_ROUTES,
            hypotheses=["memory_lapse", "ghost_without_route"],
            duration_overrides=_OVERRIDES,
        )
    assert caught.value.reason == "hypotheses_without_routes"
    assert "ghost_without_route" in caught.value.detail


def test_incomplete_grid_fails_registration():
    table = _table()
    partial = AL.LossTable(
        hypotheses=table.hypotheses,
        actions=table.actions,
        cells={
            key: cell
            for key, cell in table.cells.items()
            if key != ("memory_lapse", "reveal_reconstruct")
        },
        effective_action=table.effective_action,
    )
    with pytest.raises(AL.LossTableIncompleteError) as caught:
        AL.assert_derived(partial)
    assert caught.value.reason == "incomplete_grid"
    assert "memory_lapse/reveal_reconstruct" in caught.value.detail


# ---------------------------------------------------------------------------
# evsi fail-closed
# ---------------------------------------------------------------------------


def test_zero_mass_prior_is_refused_not_replaced_with_a_uniform():
    with pytest.raises(EV.EVSIInputError) as caught:
        EV.evsi_for_conditionals(
            _CONDITIONALS,
            {"memory_lapse": 0.0, "false_belief_or_confusion": 0.0},
            _table(),
        )
    assert caught.value.reason == "prior_mass_zero"


def test_positive_mass_hypothesis_missing_from_the_loss_table_aborts_the_value():
    prior = {**_PRIOR, "H_OTHER": 0.1}
    with pytest.raises(EV.EVSIInputError) as caught:
        EV.evsi_for_conditionals(_CONDITIONALS, prior, _table())
    assert caught.value.reason == "incomplete_loss_table"
    assert "H_OTHER" in caught.value.detail


def test_positive_mass_hypothesis_without_a_likelihood_row_aborts_the_value():
    conditionals = {"memory_lapse": {"pass": 0.9, "fail": 0.1}}
    with pytest.raises(EV.EVSIInputError) as caught:
        EV.evsi_for_conditionals(conditionals, _PRIOR, _table())
    assert caught.value.reason == "incomplete_likelihoods"
    assert "false_belief_or_confusion" in caught.value.detail


def test_zero_mass_hypothesis_may_be_absent_without_aborting():
    prior = {**_PRIOR, "H_OTHER": 0.0}
    result = EV.evsi_for_conditionals(_CONDITIONALS, prior, _table())
    assert result.evsi >= 0.0


# ---------------------------------------------------------------------------
# rank_feasible exclusions
# ---------------------------------------------------------------------------


def _candidate(ref: str, **kwargs) -> EV.DiagnosticCandidate:
    defaults = dict(
        members=(_CONDITIONALS,),
        prior=_PRIOR,
        expected_minutes=0.5,
        prior_basis="support_weighted",
    )
    defaults.update(kwargs)
    return EV.DiagnosticCandidate(ref=ref, **defaults)


def test_uniform_fallback_prior_is_excluded_from_live_value_ranking():
    result = EV.rank_feasible(
        [_candidate("q1", prior_basis="uniform_fallback")], _table()
    )
    assert result.verdict == "abstain"
    assert result.reason == "no_evaluable_candidate"
    assert result.should_stop is False
    assert result.excluded[0]["reason"] == "uniform_fallback_prior"


def test_incomplete_candidate_is_excluded_and_the_rest_still_rank():
    broken = _candidate(
        "broken", members=({"memory_lapse": {"pass": 0.9, "fail": 0.1}},)
    )
    good = _candidate("good")
    result = EV.rank_feasible([broken, good], _table())
    assert result.best_ref == "good"
    assert [entry["ref"] for entry in result.excluded] == ["broken"]
    assert result.excluded[0]["reason"] == "incomplete_likelihoods"
    assert "false_belief_or_confusion" in result.excluded[0]["detail"]
    assert result.verdict in {"measure", "stop"}
    # The exclusion is persistable on the receipt.
    assert result.as_dict()["excluded"][0]["reason"] == "incomplete_likelihoods"


def test_all_candidates_excluded_is_an_abstention_never_a_confident_stop():
    """Missing machine data licenses an abstention -- not a live probe, and not a
    confident 'measurement is worthless' stop either (invariant 6)."""

    result = EV.rank_feasible(
        [
            _candidate("a", prior_basis="uniform_fallback"),
            _candidate("b", prior={"memory_lapse": 0.0, "false_belief_or_confusion": 0.0}),
        ],
        _table(),
    )
    assert result.verdict == "abstain"
    assert result.reason == "no_evaluable_candidate"
    assert result.should_stop is False
    assert {entry["reason"] for entry in result.excluded} == {
        "uniform_fallback_prior",
        "prior_mass_zero",
    }


# ---------------------------------------------------------------------------
# The shared deterministic candidate order.
# ---------------------------------------------------------------------------


def test_order_probe_candidates_is_status_first_then_discrimination_then_age():
    def cand(id_: str, status: str, pairs: int, created: str) -> dict:
        return {
            "id": id_,
            "status": status,
            "created_at": created,
            "discrimination": {"separable_pairs": [["h1", "h2"]] * pairs},
        }

    older_registered = cand("c_old", "registered", 3, "2026-01-01T00:00:00Z")
    newer_active = cand("c_new", "active", 0, "2026-06-01T00:00:00Z")
    strong_registered = cand("c_strong", "registered", 2, "2026-05-01T00:00:00Z")
    weak_registered = cand("c_weak", "registered", 2, "2026-04-01T00:00:00Z")

    ordered = order_probe_candidates(
        [older_registered, weak_registered, strong_registered, newer_active]
    )
    # Active first regardless of age or informativeness; then more separable
    # pairs; ties break by created_at then id.
    assert [value["id"] for value in ordered] == [
        "c_new",
        "c_old",
        "c_weak",
        "c_strong",
    ]
