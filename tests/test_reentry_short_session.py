"""P4 §15 step 11 -- the §12 re-entry / short-session block-planner adapters
(spec_p4 §12, §16.1 "one three-minute activity completes a session", §16.9).

Covering tests for the two formerly-DEFERRED §16 acceptance rows:

- §16.1 "one three-minute activity completes a session" ->
  ``test_three_minute_activity_completes_a_session`` (+ the honest-stop and
  short-pattern-preference and depth-edge-fit variants);
- §16.9 re-entry / short-session adapter items ->
  ``test_reentry_pins_target_caps_and_reports_without_backlog``,
  ``test_reentry_welcome_back_makes_no_diagnostic_claim``,
  ``test_reentry_classifies_retained_recoverable_needs_attention``,
  ``test_short_session_depth_edge_stops_if_it_cannot_fit``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_actions as A
from learnloop.services import controller_snapshot as cs
from learnloop.services import reentry_adapter as ra
from learnloop.services import short_session as short
from learnloop.services import staged_policy as sp
from learnloop.services.goal_projection import FacetProjection, GoalReport
from learnloop.services.scheduler import SchedulerSession
from learnloop.services.state_sync import sync_vault_state
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
# §16.1 -- one three-minute activity completes a session (SHORT SESSION)
# --------------------------------------------------------------------------


def test_three_minute_activity_completes_a_session(wired):
    """§16.1 (formerly DEFERRED): a 3-minute session plans a block that COMPLETES within
    it -- one activity is the whole block -- with the budget = the available minutes."""

    vault, repo = wired
    fits = cs.Candidate(candidate_ref="fits", active=True, purpose="practice",
                        practice_mode="setup_only", expected_minutes=3.0)
    plan = short.plan_short_session(
        vault, repo, _session(3),
        signals=sp.StateSignals(target_acquired=False), candidates=[fits], clock=CLOCK,
    )
    assert plan.is_short_session is True
    assert plan.completed is True and plan.stopped is False
    assert plan.chosen_candidate_ref == "fits"
    assert plan.decision.action == A.INSTRUCT
    # The block budget is the available minutes (composes, not clamps up to 5).
    assert plan.decision.block.budget_minutes == 3.0
    # One completed activity completes the session: a single completing exit rule.
    assert plan.decision.block.exit_rules == ("session_complete_on_one_activity",)
    assert plan.decision.block.neighborhood.get("short_session") is True


def test_short_session_stops_honestly_when_nothing_fits(wired):
    """§12.2: if no meaningful candidate fits the conservative duration bound, return
    stop:no_feasible_activity -- never fill time with low-value leftovers."""

    vault, repo = wired
    too_long = cs.Candidate(candidate_ref="long", active=True, purpose="practice",
                            expected_minutes=10.0)
    plan = short.plan_short_session(
        vault, repo, _session(3),
        signals=sp.StateSignals(target_acquired=False), candidates=[too_long], clock=CLOCK,
    )
    assert plan.stopped is True and plan.completed is False
    assert plan.stop_reason == A.STOP_NO_FEASIBLE_ACTIVITY


def test_short_session_prefers_admitted_short_p1_patterns(wired):
    """§12.2: a short session PREFERS the admitted short P1 patterns
    (setup_only/example_completion/example_comparison) whose duration fits."""

    vault, repo = wired
    preferred = cs.Candidate(candidate_ref="pref", active=True, purpose="practice",
                             practice_mode="example_completion", expected_minutes=3.0)
    other = cs.Candidate(candidate_ref="other", active=True, purpose="practice",
                         practice_mode="minimal_retrieval", expected_minutes=3.0)
    plan = short.plan_short_session(
        vault, repo, _session(3),
        signals=sp.StateSignals(target_acquired=False),
        candidates=[other, preferred], clock=CLOCK,
    )
    assert plan.chosen_candidate_ref == "pref"
    assert plan.decision.trace["ranking_inputs"]["selector"] == "short_session_preferred_pattern"


def test_short_session_retry_after_commit_is_idempotent(wired):
    """§16.10 operability: a retry after the commit boundary yields ONE decision (the
    short-session path replays the standing decision, not a fresh choice)."""

    vault, repo = wired
    fits = cs.Candidate(candidate_ref="fits", active=True, purpose="practice",
                        expected_minutes=3.0)
    first = short.plan_short_session(
        vault, repo, _session(3), signals=sp.StateSignals(target_acquired=False),
        candidates=[fits], receipt_key="rk_short", clock=CLOCK,
    )
    retry = short.plan_short_session(
        vault, repo, _session(3), signals=sp.StateSignals(model_misspecified=True),
        candidates=[fits], receipt_key="rk_short", clock=CLOCK,
    )
    assert retry.decision.already is True
    assert retry.decision.decision_id == first.decision.decision_id
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


# --------------------------------------------------------------------------
# §16.9 -- re-entry adapter
# --------------------------------------------------------------------------


def test_reentry_welcome_back_makes_no_diagnostic_claim(wired):
    """§16.9 bullet 2: the welcome-back FSRS summary alone makes no diagnostic claim; the
    adapter pins the target distribution and (with nothing to re-check) stops honestly."""

    vault, repo = wired
    plan = ra.plan_reentry(vault, repo, vault.goals[0], _session(15), clock=CLOCK)
    assert plan.welcome_back_is_diagnostic is False
    assert plan.uses_backlog_language is False
    assert plan.pinned_target_hash is not None  # target distribution is pinned
    # Every classified cell carries a neutral status word, never a deficit label; the
    # summary itself makes no diagnostic claim.
    statuses = {c.status for c in plan.retained + plan.recoverable + plan.needs_attention}
    assert statuses <= {"retained", "recoverable", "needs_attention"}
    assert plan.decision is not None  # the re-entry decision runs on the normal trace


def _facet(facet_id, *, lo="lo_svd_definition", ready, decay=True):
    return FacetProjection(
        learning_object_id=lo, facet_id=facet_id, label="uncertain",
        current_recall=ready, projected_recall=ready, on_track=ready >= 0.8,
        predicted_current=ready, predicted_at_horizon=ready, evidence_mass=5.0,
        certified=False, attempts_to_certify=None, demonstrated=False, decay_estimated=decay,
    )


def _plant_projections(monkeypatch, repo, *, ended_dt, now_map, last_map):
    monkeypatch.setattr(repo, "most_recent_ended_at",
                        lambda: ended_dt.strftime("%Y-%m-%dT%H:%M:%SZ"))

    def fake_projections(vault, repository, goal, at, *, clock=None):
        away = abs((at.astimezone(UTC) - ended_dt).total_seconds()) < 3600
        return list((last_map if away else now_map).values())

    monkeypatch.setattr(ra, "facet_projections_at", fake_projections)
    monkeypatch.setattr(ra, "goal_report",
                        lambda *a, **k: GoalReport(goal_id="g", target_recall=0.8, due_at=None,
                                                   horizon=datetime(2026, 1, 1, tzinfo=UTC),
                                                   facets=[], blueprint_readiness_by_lo={}))
    monkeypatch.setattr(ra, "blueprint_weight_by_facet", lambda *a, **k: {})


def test_reentry_classifies_retained_recoverable_needs_attention(wired, monkeypatch):
    """§16.9 bullet 1: reports retained / recoverable / needs_attention (neutral status
    words, with ready intervals as context) -- no deficit labels, no backlog shame."""

    vault, repo = wired
    now = NOW
    ended_dt = now - timedelta(days=20)
    last = {  # at the last session end: all were above target
        "f_keep": _facet("f_keep", ready=0.9),
        "f_reco": _facet("f_reco", ready=0.9),
        "f_need": _facet("f_need", ready=0.9),
        "f_flat": _facet("f_flat", ready=0.9, decay=False),
    }
    now_map = {  # now: keep still solid, reco slipped a little, need slipped a lot
        "f_keep": _facet("f_keep", ready=0.85),
        "f_reco": _facet("f_reco", ready=0.72),   # within 0.15 band -> recoverable
        "f_need": _facet("f_need", ready=0.40),   # far below -> needs_attention
        "f_flat": _facet("f_flat", ready=0.30, decay=False),  # held flat -> trusted
    }
    _plant_projections(monkeypatch, repo, ended_dt=ended_dt, now_map=now_map, last_map=last)

    cells = ra.classify_cells(vault, repo, vault.goals[0], clock=CLOCK)
    by = {c.facet_id: c for c in cells}
    assert "f_flat" not in by  # held flat -> trusted, excluded from confident copy
    assert by["f_keep"].status == "retained" and by["f_keep"].re_checked is False
    assert by["f_reco"].status == "recoverable" and by["f_reco"].re_checked is True
    assert by["f_need"].status == "needs_attention" and by["f_need"].re_checked is True
    # Intervals/context, not deficit labels.
    assert by["f_need"].ready_now == 0.40 and by["f_need"].ready_last == 0.90
    assert {c.status for c in cells} <= {"retained", "recoverable", "needs_attention"}


def test_reentry_pins_target_caps_and_reports_without_backlog(wired, monkeypatch):
    """§16.9 bullet 1 (formerly DEFERRED): re-entry pins the target distribution, caps
    questions, and reports the three buckets -- on the normal decision trace."""

    vault, repo = wired
    now = NOW
    ended_dt = now - timedelta(days=20)
    # Plant more fragile frontier cells than the cap so the cap actually bites.
    last, now_map = {}, {}
    for i in range(ra.REENTRY_QUESTION_CAP + 2):
        fid = f"f{i}"
        last[fid] = _facet(fid, ready=0.9)
        now_map[fid] = _facet(fid, ready=0.3)  # all needs_attention
    _plant_projections(monkeypatch, repo, ended_dt=ended_dt, now_map=now_map, last_map=last)

    plan = ra.plan_reentry(vault, repo, vault.goals[0], _session(15), clock=CLOCK)
    assert plan.pinned_target_hash is not None                 # pins target distribution
    assert len(plan.sampled_cells) == ra.REENTRY_QUESTION_CAP  # caps questions
    assert len(plan.needs_attention) == ra.REENTRY_QUESTION_CAP + 2
    assert plan.uses_backlog_language is False                 # no backlog shame
    assert plan.welcome_back_is_diagnostic is False
    assert plan.decision is not None                           # ran on the normal trace
    # A re-check episode with fragile cells routes a measure_diagnostic block.
    assert plan.decision["action"] in (A.MEASURE_DIAGNOSTIC, A.STOP)
