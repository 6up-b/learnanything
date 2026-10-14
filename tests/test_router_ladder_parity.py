"""Router R2a: the P4 ladder's two copies agree (plan §3.1, R1 Codex review).

``staged_policy.ladder_eligibility`` (what the staged frame annotates Today's
candidates with, and R1 logs) and ``staged_policy.evaluate_staged_rule`` (what
the staged policy acts on) are two copies of the §4.2 ladder. For every
combination of the signals, the rung the first marks ``fired`` is the rule,
action and subtype the second returns, with and without a commitment whose
reviewed edge makes rung 8 reachable.
"""

from __future__ import annotations

import itertools

import pytest

from learnloop.scheduling import controller_snapshot as cs
from learnloop.scheduling import staged_policy as sp


def _snapshot(*, commitment: bool) -> cs.ControllerSnapshot:
    commitments = ()
    if commitment:
        commitments = (
            cs.CommitmentSummary(
                commitment_id="c1", created_action="confirm", disposition="active",
                depth_policy="auto_within_envelope", depth_policy_version_id="dp1", depth_envelope_version_id="de1",
                goal_id="g1", reached_milestones=("m1",),
                reviewed_edges=({"reviewed": True, "from_milestone": "m1", "edge_id": "e1"},),
            ),
        )
    return cs.ControllerSnapshot(
        snapshot_hash="h", session_id=None, available_minutes=None, energy=None, remaining_minutes=None,
        conservative_duration_minutes=3.0, candidates=(), exposure_by_hash={}, exposure_by_fingerprint={},
        reserved_assessment_surface_ids=frozenset(), commitments=commitments, affect_by_commitment={},
        param_manifest_hash="p", projection_versions={},
    )


FLAGS = ("triage", "triage_instruct", "misspecified", "measurement", "acquired", "fragile", "integration",
         "terminal", "milestone", "retention", "goal")


def _signals(values: dict[str, bool]) -> sp.StateSignals:
    route = None
    if values["triage"]:
        route = {"first_intervention": "instruct" if values["triage_instruct"] else "redo"}
    return sp.StateSignals(
        pending_triage_route=route,
        model_misspecified=values["misspecified"],
        decision_relevant_robust_value=1.0 if values["measurement"] else 0.0,
        target_acquired=values["acquired"],
        capability_fragile=values["fragile"],
        integration_failing=values["integration"],
        terminal_required_unshown=values["terminal"],
        terminal_reserve_valid=values["terminal"],
        milestone_reached="m1" if values["milestone"] else None,
        retention_near_limit=values["retention"],
        goal_satisfied=values["goal"],
    )


@pytest.mark.parametrize("commitment", [False, True])
def test_the_fired_rung_is_the_rule_the_staged_policy_applies(commitment):
    snapshot = _snapshot(commitment=commitment)
    checked = 0
    for bits in itertools.product((False, True), repeat=len(FLAGS)):
        values = dict(zip(FLAGS, bits))
        signals = _signals(values)
        intent = sp.evaluate_staged_rule(snapshot, signals)
        rungs = sp.ladder_eligibility(snapshot, signals)
        [fired] = [rung for rung in rungs if rung["fired"]]
        assert (fired["staged_rule"], fired["action"], fired["subtype"]) == (
            intent.staged_rule, intent.action, intent.subtype,
        ), values
        # Every rung before the fired one is ineligible.
        assert not any(rung["eligible"] for rung in rungs[: fired["rung"] - 1]), values
        checked += 1
    assert checked == 2 ** len(FLAGS)


def test_a_short_circuited_block_fires_no_rung():
    rungs = sp.ladder_eligibility(_snapshot(commitment=False), sp.StateSignals(), short_circuited=True)
    assert not any(rung["fired"] for rung in rungs)
    assert {rung["staged_rule"] for rung in rungs if not rung["reversible"]} == set(sp.IRREVERSIBLE_RUNGS)
