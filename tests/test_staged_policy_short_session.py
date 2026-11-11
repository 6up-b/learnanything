"""The staged block planner's short session (spec_p4 §12.2, §16.1 "one three-minute
activity completes a session", §16.9).

A short session is not a separate controller: ``staged_policy.decide`` with a small
``available_minutes`` plans a block that completes within them. These tests drive
``decide`` directly:

- §16.1 -> ``test_three_minute_activity_completes_a_session`` (+ the honest-stop,
  short-pattern-preference and retry variants);
- §16.9 bullet 4 -> ``test_short_session_depth_edge_stops_if_it_cannot_fit``.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.scheduling import controller_actions as A
from learnloop.scheduling import controller_snapshot as cs
from learnloop.scheduling import staged_policy as sp
from learnloop.scheduling.scheduler import SchedulerSession
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

CLOCK = FrozenClock(NOW)


@pytest.fixture
def wired(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    seed_due_item(paths)
    return vault, repo


def _session(minutes: float):
    return SchedulerSession(session_id="s1", available_minutes=minutes)


# --------------------------------------------------------------------------
# §16.1 -- one three-minute activity completes a session
# --------------------------------------------------------------------------


def test_three_minute_activity_completes_a_session(wired):
    """§16.1: a 3-minute session plans a block that COMPLETES within it -- one activity
    is the whole block -- with the budget = the available minutes."""

    vault, repo = wired
    fits = cs.Candidate(candidate_ref="fits", active=True, purpose="practice",
                        practice_mode="setup_only", expected_minutes=3.0)
    res = sp.decide(
        vault, repo, _session(3),
        signals=sp.StateSignals(target_acquired=False), candidates=[fits], clock=CLOCK,
    )
    assert res.action == A.INSTRUCT
    assert res.chosen_candidate_ref == "fits"
    # The block budget is the available minutes (composes, not clamps up to 5).
    assert res.block.budget_minutes == 3.0
    # One completed activity completes the session: a single completing exit rule.
    assert res.block.exit_rules == ("session_complete_on_one_activity",)
    assert res.block.neighborhood.get("short_session") is True


def test_short_session_stops_honestly_when_nothing_fits(wired):
    """§12.2: if no meaningful candidate fits the conservative duration bound, return
    stop:no_feasible_activity -- never fill time with low-value leftovers."""

    vault, repo = wired
    too_long = cs.Candidate(candidate_ref="long", active=True, purpose="practice",
                            expected_minutes=10.0)
    res = sp.decide(
        vault, repo, _session(3),
        signals=sp.StateSignals(target_acquired=False), candidates=[too_long], clock=CLOCK,
    )
    assert res.action == A.STOP and res.chosen_candidate_ref is None
    assert res.stop_reason == A.STOP_NO_FEASIBLE_ACTIVITY


def test_short_session_prefers_admitted_short_p1_patterns(wired):
    """§12.2: a short session PREFERS the admitted short P1 patterns
    (setup_only/example_completion/example_comparison) whose duration fits."""

    vault, repo = wired
    preferred = cs.Candidate(candidate_ref="pref", active=True, purpose="practice",
                             practice_mode="example_completion", expected_minutes=3.0)
    other = cs.Candidate(candidate_ref="other", active=True, purpose="practice",
                         practice_mode="minimal_retrieval", expected_minutes=3.0)
    res = sp.decide(
        vault, repo, _session(3),
        signals=sp.StateSignals(target_acquired=False),
        candidates=[other, preferred], clock=CLOCK,
    )
    assert res.chosen_candidate_ref == "pref"
    assert res.trace["ranking_inputs"]["selector"] == "short_session_preferred_pattern"


def test_short_session_retry_after_commit_is_idempotent(wired):
    """§16.10 operability: a retry after the commit boundary yields ONE decision (the
    short-session path replays the standing decision, not a fresh choice)."""

    vault, repo = wired
    fits = cs.Candidate(candidate_ref="fits", active=True, purpose="practice",
                        expected_minutes=3.0)
    first = sp.decide(
        vault, repo, _session(3), signals=sp.StateSignals(target_acquired=False),
        candidates=[fits], receipt_key="rk_short", clock=CLOCK,
    )
    retry = sp.decide(
        vault, repo, _session(3), signals=sp.StateSignals(model_misspecified=True),
        candidates=[fits], receipt_key="rk_short", clock=CLOCK,
    )
    assert retry.already is True
    assert retry.decision_id == first.decision_id
    assert retry.chosen_candidate_ref == first.chosen_candidate_ref


def _auto_commitment():
    return cs.CommitmentSummary(
        commitment_id="cm1", created_action="select_exemplar", disposition="active",
        depth_policy="auto_within_envelope", depth_policy_version_id="dp1",
        depth_envelope_version_id="de1", goal_id="g1", reached_milestones=("m1",),
        reviewed_edges=({"edge_id": "e1", "from_milestone": "m1", "to_milestone": "m2",
                         "reviewed": True},),
    )


def _planted_snapshot(*, remaining: float, conservative: float):
    return cs.ControllerSnapshot(
        snapshot_hash="h", session_id="s1", available_minutes=remaining, energy=None,
        remaining_minutes=remaining, conservative_duration_minutes=conservative,
        candidates=(), exposure_by_hash={}, exposure_by_fingerprint={},
        reserved_assessment_surface_ids=frozenset(), commitments=(_auto_commitment(),),
        affect_by_commitment={"cm1": {"negative_affect_count": 0}}, param_manifest_hash="p",
        projection_versions={},
    )


def test_short_session_depth_edge_stops_if_it_cannot_fit(wired, monkeypatch):
    """§16.9 bullet 4: a short session may activate a reviewed edge already authorized by
    auto_within_envelope ONLY when the transition fits safely; otherwise it stops."""

    vault, repo = wired
    planted = _planted_snapshot(remaining=2.0, conservative=3.0)  # edge cannot fit 2 min
    monkeypatch.setattr(sp.cs, "build_snapshot", lambda *a, **k: planted)
    res = sp.decide(
        vault, repo, _session(2),
        signals=sp.StateSignals(milestone_reached="m1"), clock=CLOCK,
    )
    assert res.action == A.STOP
    assert res.stop_reason == A.STOP_NO_FEASIBLE_ACTIVITY
    assert res.staged_rule == "short_session_transition_cannot_fit"
