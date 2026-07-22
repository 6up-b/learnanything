"""P4 step 3 -- the minutes decision-loss table L(h, a) (spec_p4 §6.2, §16.3; U-023).

Covers: deterministic/inspectable derivation from triage routes + logged attempt
durations; the effective repair wastes zero minutes; every cell carries its
expected-minutes derivation; a free-constant entry fails registration.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import action_loss as AL
from learnloop.services.activities import log_attempt_duration

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)

_ROUTES = [
    {"reason": "memory_lapse", "first_intervention": "reveal_reconstruct"},
    {"reason": "false_belief_or_confusion", "first_intervention": "contrast_counterexample"},
    {"reason": "procedure_execution", "first_intervention": "worked_then_faded"},
]


def test_loss_table_is_derived_from_routes_and_durations():
    overrides = {"reveal_reconstruct": 2.0, "contrast_counterexample": 4.0, "worked_then_faded": 6.0}
    table = AL.build_loss_table(routes=_ROUTES, duration_overrides=overrides)

    # Action space = distinct first_intervention values; hypotheses = the reasons.
    assert set(table.actions) == set(overrides.keys())
    assert set(table.hypotheses) == {r["reason"] for r in _ROUTES}

    # The effective repair for a hypothesis wastes zero minutes.
    assert table.loss("memory_lapse", "reveal_reconstruct") == 0.0
    # A wrong action wastes minutes(a) + delay minutes(effective).
    assert table.loss("memory_lapse", "contrast_counterexample") == pytest.approx(4.0 + 2.0)
    assert table.loss("false_belief_or_confusion", "worked_then_faded") == pytest.approx(6.0 + 4.0)


def test_every_cell_carries_a_minutes_derivation():
    table = AL.build_loss_table(routes=_ROUTES, duration_overrides={
        "reveal_reconstruct": 2.0, "contrast_counterexample": 4.0, "worked_then_faded": 6.0})
    for (h, a), cell in table.cells.items():
        assert "kind" in cell.derivation
        if cell.minutes > 0:
            d = cell.derivation
            assert d["wasted_minutes"] + d["delay_minutes"] == pytest.approx(cell.minutes)
    # assert_derived is a no-op on a properly derived table.
    AL.assert_derived(table)


def test_free_constant_entry_fails_registration():
    """U-023/§16.3: a loss entry without a minutes derivation fails registration."""

    bad = AL.LossTable(
        hypotheses=("h",), actions=("a", "b"),
        cells={
            ("h", "a"): AL.LossCell("h", "a", 0.0, {"kind": "effective_intervention",
                                                     "wasted_minutes": 0.0, "delay_minutes": 0.0}),
            ("h", "b"): AL.raw_cell("h", "b", 7.0),  # a free constant, no derivation
        },
        effective_action={"h": "a"},
    )
    with pytest.raises(AL.LossDerivationError):
        AL.assert_derived(bad)


def test_durations_fall_back_to_logged_pooled_then_heuristic(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    interventions = ["reveal_reconstruct", "contrast_counterexample"]

    # No logged durations -> the heuristic default, flagged as such.
    est = AL.attempt_minutes_by_intervention(interventions, repository=repo)
    assert all(e.source == "heuristic_default" for e in est.values())
    assert est["reveal_reconstruct"].minutes == AL.DEFAULT_INTERVENTION_MINUTES

    # Log two attempt durations (ms) -> the pooled median (minutes) is used.
    log_attempt_duration(repo, administration_id="adm1", attempt_id="a1", duration_ms=120_000, clock=CLOCK)
    log_attempt_duration(repo, administration_id="adm2", attempt_id="a2", duration_ms=240_000, clock=CLOCK)
    est2 = AL.attempt_minutes_by_intervention(interventions, repository=repo)
    assert all(e.source == "pooled_attempt_durations" for e in est2.values())
    # median(120000, 240000) = 180000 ms = 3.0 minutes.
    assert est2["reveal_reconstruct"].minutes == pytest.approx(3.0)
    assert est2["reveal_reconstruct"].sample_count == 2


def test_argmin_action_and_shared_optimal_set():
    table = AL.build_loss_table(routes=_ROUTES, duration_overrides={
        "reveal_reconstruct": 2.0, "contrast_counterexample": 4.0, "worked_then_faded": 6.0})
    # A posterior concentrated on memory_lapse prefers its effective repair.
    posterior = {"memory_lapse": 1.0, "false_belief_or_confusion": 0.0, "procedure_execution": 0.0}
    assert table.argmin_action(posterior) == "reveal_reconstruct"
    assert table.argmin_action_set(posterior) == frozenset({"reveal_reconstruct"})


def test_table_hash_is_order_invariant():
    a = AL.build_loss_table(routes=_ROUTES, duration_overrides={
        "reveal_reconstruct": 2.0, "contrast_counterexample": 4.0, "worked_then_faded": 6.0})
    b = AL.build_loss_table(routes=list(reversed(_ROUTES)), duration_overrides={
        "worked_then_faded": 6.0, "contrast_counterexample": 4.0, "reveal_reconstruct": 2.0})
    assert a.table_hash == b.table_hash
