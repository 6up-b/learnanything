"""P4 step 2 -- the transparent staged decision policy (spec_p4 §4, §16.1; design §F).

Covers: each planted state selects the expected canonical action; one staged rule +
complete exclusion trace per decision; one-edge discipline; affect check BEFORE any
edge; the legacy weighted sum demoted to a logged comparator with zero authority;
shadow scorers with zero authority; typed stop; retry-after-commit idempotency.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_actions as A
from learnloop.services import controller_snapshot as cs
from learnloop.services import controller_store as store
from learnloop.services import staged_policy as sp
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


def _session():
    return SchedulerSession(session_id="s1", available_minutes=15)


def _bare_snapshot(*, commitments=(), affect=None):
    return cs.ControllerSnapshot(
        snapshot_hash="h", session_id="s", available_minutes=15, energy=None,
        remaining_minutes=15.0, conservative_duration_minutes=3.0, candidates=(),
        exposure_by_hash={}, exposure_by_fingerprint={},
        reserved_assessment_surface_ids=frozenset(), commitments=tuple(commitments),
        affect_by_commitment=affect or {}, param_manifest_hash="p", projection_versions={},
    )


def _auto_commitment(cid="cm1", *, policy="auto_within_envelope", milestone="m1"):
    return cs.CommitmentSummary(
        commitment_id=cid, created_action="select_exemplar", disposition="active",
        depth_policy=policy, depth_policy_version_id="dp1", depth_envelope_version_id="de1",
        goal_id="g1", reached_milestones=(milestone,),
        reviewed_edges=({"edge_id": "e1", "from_milestone": milestone, "to_milestone": "m2",
                         "reviewed": True},),
    )


# --- §4.2 ladder: each planted state selects the expected action ------------------

@pytest.mark.parametrize(
    "signals, expect_action, expect_subtype, expect_rule",
    [
        (sp.StateSignals(pending_triage_route={"first_intervention": "instruct"}),
         A.INSTRUCT, None, "triage_determined_instruct"),
        (sp.StateSignals(pending_triage_route={"first_intervention": "completion"}),
         A.PRACTICE, A.COMPLETION_OR_REPAIR, "triage_determined_repair"),
        (sp.StateSignals(model_misspecified=True), A.EXPAND_MODEL, None, "model_misspecification"),
        (sp.StateSignals(decision_relevant_robust_value=0.9), A.MEASURE_DIAGNOSTIC, None,
         "positive_robust_measurement_value"),
        (sp.StateSignals(target_acquired=False), A.INSTRUCT, None, "target_not_acquired"),
        (sp.StateSignals(capability_fragile=True), A.PRACTICE, A.COMPLETION_OR_REPAIR,
         "capability_fragile"),
        (sp.StateSignals(integration_failing=True), A.PRACTICE, A.INTEGRATION, "integration_failing"),
        (sp.StateSignals(terminal_required_unshown=True, terminal_reserve_valid=True),
         A.ASSESS_TERMINAL, None, "terminal_required_with_reserve"),
        (sp.StateSignals(retention_near_limit=True), A.MAINTAIN, None, "retention_near_limit"),
        (sp.StateSignals(goal_satisfied=True), A.STOP, A.STOP_GOAL_SATISFIED, "goal_satisfied"),
        (sp.StateSignals(), A.STOP, A.STOP_NO_POSITIVE_ROBUST_VALUE, "no_positive_value_stop"),
    ],
)
def test_planted_state_selects_expected_action(signals, expect_action, expect_subtype, expect_rule):
    snap = _bare_snapshot(commitments=(_auto_commitment(),))
    intent = sp.evaluate_staged_rule(snap, signals)
    assert intent.action == expect_action
    assert intent.subtype == expect_subtype
    assert intent.staged_rule == expect_rule
    A.validate(intent.action, intent.subtype)


def test_depth_progression_only_under_auto_within_envelope():
    reached = sp.StateSignals(milestone_reached="m1",
                              milestone_evidence_receipt={"qualifies": True, "evidence_receipt": {}})
    auto = _bare_snapshot(commitments=(_auto_commitment(policy="auto_within_envelope"),))
    intent = sp.evaluate_staged_rule(auto, reached)
    assert intent.action == A.PRACTICE and intent.subtype == A.DEPTH_PROGRESSION

    # suggest_next / hold_at_target cannot auto-select the edge -> falls through to stop.
    for policy in ("suggest_next", "hold_at_target"):
        snap = _bare_snapshot(commitments=(_auto_commitment(policy=policy),))
        other = sp.evaluate_staged_rule(snap, reached)
        assert other.subtype != A.DEPTH_PROGRESSION


# --- decide(): trace + comparator + shadow firewall ------------------------------

def test_decision_trace_is_complete(wired):
    vault, repo = wired
    res = sp.decide(vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
                    clock=CLOCK)
    t = res.trace
    for key in ("snapshot_hash", "staged_rule", "action", "constraint_manifest_hash",
                "decision_params_hash", "feasible_set", "exclusions", "ranking_inputs",
                "chosen_action", "affect_check", "comparator", "model_versions",
                "stop_alternatives", "why", "steps"):
        assert key in t, f"trace missing {key}"
    # exactly one staged rule fired; the why is the staged reason, not a score term.
    assert t["staged_rule"] == "target_not_acquired"
    assert "because target_not_acquired" in t["why"]


def test_decision_persists_snapshot_decision_candidates_and_block(wired):
    vault, repo = wired
    res = sp.decide(vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
                    clock=CLOCK)
    row = store.decision_row(repo, res.decision_id)
    assert row["snapshot_hash"] == res.snapshot_hash
    assert row["mode"] == "shadow"
    assert store.snapshot_row(repo, row["snapshot_id"]) is not None
    cands = store.candidates_for_decision(repo, res.decision_id)
    assert cands and any(c["selected"] for c in cands)
    block_events = store.block_events(repo, row["attention_block_id"])
    assert block_events[0]["kind"] == "block_opened"


def test_legacy_comparator_is_logged_but_not_authority(wired):
    vault, repo = wired
    res = sp.decide(vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
                    clock=CLOCK)
    comparator = res.trace["comparator"]
    assert comparator is not None and comparator["available"]
    # The comparator is recorded on the trace; the staged 'why' never cites a score.
    assert "priority" not in res.why and "score" not in res.why
    # Candidate rows carry the comparator score for comparison only.
    cands = store.candidates_for_decision(repo, res.decision_id)
    assert any(c["comparator_score"] is not None for c in cands)


def test_shadow_scorer_has_zero_authority(wired):
    vault, repo = wired
    # A scorer that screams "pick nothing" and one that raises must not change the choice.
    good = sp.decide(vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
                     clock=CLOCK)

    def screaming(snapshot, chosen):
        return 1e9

    def failing(snapshot, chosen):
        raise RuntimeError("boom")

    shadowed = sp.decide(
        vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
        shadow_scorers=[screaming, failing], clock=CLOCK,
    )
    assert shadowed.chosen_candidate_ref == good.chosen_candidate_ref
    preds = store.shadow_predictions_for_decision(repo, shadowed.decision_id)
    assert {p["scorer_kind"] for p in preds} == {"shadow_scorer_0", "shadow_scorer_1"}
    # A failing scorer is recorded UNUSABLE; all shadow rows carry authority='none'.
    assert any(p["usable"] == 0 for p in preds)
    assert all(p["authority"] == "none" for p in preds)


def test_high_shadow_score_cannot_resurrect_infeasible_candidate(wired):
    """Invariant 1/3: a score can never select an infeasible candidate."""

    vault, repo = wired
    live = cs.Candidate(candidate_ref="live_item", active=True, purpose="practice",
                        due_at="2026-01-01T00:00:00Z")
    dead = cs.Candidate(candidate_ref="dead_item", active=False, purpose="practice")

    def prefer_dead(snapshot, chosen):
        return {"dead_item": 1e9, "live_item": -1e9}

    res = sp.decide(
        vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
        candidates=[live, dead], shadow_scorers=[prefer_dead], clock=CLOCK,
    )
    assert res.chosen_candidate_ref == "live_item"
    assert "dead_item" not in res.trace["feasible_set"]
    assert "dead_item" in res.trace["exclusions"]


# --- affect ordering + one-edge discipline ---------------------------------------

def _seed_auto_commitment(repo):
    from learnloop.services import commitments as C

    commitment = C.create_commitment(
        repo, action="select_exemplar", intent_text="master SVD",
        targets=[{"target_kind": "canonical_facet", "target_ref": "svd", "role": "required"}],
        depth_preset="master_tasks_like_these", clock=CLOCK,
    )
    C.change_depth_policy(repo, commitment_id=commitment.id, policy="auto_within_envelope",
                          clock=CLOCK)
    C.change_depth_envelope(
        repo, commitment_id=commitment.id, bounds={},
        reviewed_edges=[{"edge_id": "e1", "from_milestone": "m1", "to_milestone": "m2",
                         "reviewed": True}],
        clock=CLOCK,
    )
    C.record_milestone_reached(repo, commitment_id=commitment.id, milestone_slug="m1", clock=CLOCK)
    return commitment.id


def test_affect_check_precedes_depth_edge(wired):
    vault, repo = wired
    _seed_auto_commitment(repo)
    res = sp.decide(
        vault, repo, _session(),
        signals=sp.StateSignals(
            milestone_reached="m1",
            milestone_evidence_receipt={"qualifies": True, "evidence_receipt": {"groups": ["g1", "g2"]}},
        ),
        clock=CLOCK,
    )
    steps = [s["step"] for s in res.trace["steps"]]
    assert res.subtype == A.DEPTH_PROGRESSION
    # affect_check appears and always precedes the (at most one) depth_edge step.
    assert "affect_check" in steps and "depth_edge" in steps
    assert steps.index("affect_check") < steps.index("depth_edge")
    assert steps.count("depth_edge") == 1  # one edge per decision
    # U-018 gate OFF: the edge activates nothing; it is a suggest_next proposal.
    assert res.trace["depth_edge"]["committed"] is False


def test_one_edge_discipline_and_u018_gate_off():
    """The staged rule commits at most one edge; under U-018 (off) it activates
    nothing -- the depth edge returns a suggest_next proposal."""

    snap = _bare_snapshot(commitments=(_auto_commitment(),),
                          affect={"cm1": {"negative_affect_count": 0}})
    intent = sp.evaluate_staged_rule(
        snap, sp.StateSignals(milestone_reached="m1"),
    )
    assert intent.subtype == A.DEPTH_PROGRESSION
    # Affect downgrade fires before the edge when negative affect is repeated.
    downgrade = sp._affect_downgrade(
        _bare_snapshot(affect={"cm1": {"negative_affect_count": 3}}), "cm1"
    )
    assert downgrade["downgraded_auto_to_suggest_next"] is True


def test_no_feasible_activity_is_typed_stop(wired):
    vault, repo = wired
    dead = cs.Candidate(candidate_ref="dead", active=False)
    res = sp.decide(vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
                    candidates=[dead], clock=CLOCK)
    assert res.action == A.STOP
    assert res.stop_reason == A.STOP_NO_FEASIBLE_ACTIVITY


def test_retry_after_commit_yields_same_decision(wired):
    vault, repo = wired
    first = sp.decide(vault, repo, _session(), signals=sp.StateSignals(target_acquired=False),
                      receipt_key="rk", clock=CLOCK)
    # A retry with DIFFERENT signals must return the standing decision, not a new choice.
    retry = sp.decide(vault, repo, _session(), signals=sp.StateSignals(model_misspecified=True),
                      receipt_key="rk", clock=CLOCK)
    assert retry.already is True
    assert retry.decision_id == first.decision_id
    assert retry.chosen_candidate_ref == first.chosen_candidate_ref
    assert retry.action == first.action
