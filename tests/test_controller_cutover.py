"""P4 §14.2 dual-controller cutover -- the six step-3 coexistence gates + the live
next-action bridge (design §C; spec §14.2).

Covers: the bridge returns the pre-cutover canonical successor when a run is NOT
staged-owned; goes LIVE (decision-equivalent, mode='live') for an owned run; a full live
walk reproduces the canonical stage sequence; a named constraint/EVSI reason is the only
thing that diverges (veto); and the six ordered gates pass as a hard sequential barrier.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_actions as A
from learnloop.services import controller_cutover as cut
from learnloop.services import controller_ownership as own
from learnloop.services import controller_store as store
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import golden_path_run as GPR
from learnloop.services import staged_policy as sp
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import (
    open_administration,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.services.scheduler import SchedulerSession
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault

CLOCK = FrozenClock(NOW)


def _add_probe_item(root, item_id):
    upsert_practice_item(root, {
        "id": item_id, "learning_object_id": "lo_svd_definition", "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "dont_know"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": "Probe prompt.", "expected_answer": "Answer.",
        "grading_rubric": {"max_points": 4,
                           "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                           "fatal_errors": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }, clock=CLOCK)


@pytest.fixture
def run(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_probe_item(root, "pi_probe")
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    item = vault.practice_items["pi_svd_define_001"]
    spec = {
        "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": item.id, "unit_id": "unit-a", "family_key": "method-selection"}],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)
    resolved = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=CLOCK)
    body = {
        "purpose": "method selection",
        "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection"],
        "baseline_milestone": "m0",
        "exemplars": [{"id": item.id, "surface_ref": resolved.surface_id, "weight": 1.0}],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo, goal_id="g1", blueprint_version_id=bv.id, contract_body=body,
        depth_preset="master_tasks_like_these", source_rev="rev-1", unit_id="unit-a",
        assessment_surface_id=resolved.surface_id, clock=CLOCK,
    )
    return repo, receipt, vault


def _session():
    return SchedulerSession(session_id="s1", available_minutes=15)


# --- bridge: legacy when not owned, live when owned ------------------------------

def test_bridge_returns_canonical_when_not_staged_owned(run):
    repo, receipt, vault = run
    state = GPR.project_run(repo, receipt.run_id)
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, clock=CLOCK)
    assert action.authority == "legacy"
    assert action.to_state == state.next_action.to_state  # pre-cutover path unchanged
    assert action.staged_decision_id is None


def test_bridge_goes_live_and_is_decision_equivalent_when_owned(run):
    repo, receipt, vault = run
    own.assign_p2_run(repo, commitment_id=receipt.commitment_id, clock=CLOCK)
    canonical = GPR.project_run(repo, receipt.run_id).next_action
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, receipt_key="rk1", clock=CLOCK)
    assert action.authority == "staged"
    assert action.diverged is False
    assert action.to_state == canonical.to_state  # decision-equivalent
    row = store.decision_row(repo, action.staged_decision_id)
    assert row is not None and row["mode"] == "live"


def test_gate_off_forces_legacy_even_when_owned(run):
    repo, receipt, vault = run
    own.assign_p2_run(repo, commitment_id=receipt.commitment_id, clock=CLOCK)
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=False, clock=CLOCK)
    assert action.authority == "legacy"  # the global switch off == full rollback


def _canonical_walk(start_state: str) -> list[str]:
    """Independently fold the legacy canonical successor map (the pre-cutover path the live
    bridge must reproduce) from a start state to its terminal -- NOT a hardcoded list."""

    seq = [start_state]
    state = start_state
    while state in GPR._CANONICAL_NEXT:
        state = GPR._CANONICAL_NEXT[state][0]
        seq.append(state)
    return seq


def test_full_live_walk_reproduces_canonical_sequence(run):
    # Audit L9: the live walk must reproduce the LEGACY canonical path, derived
    # independently by folding the state machine's canonical successor map -- not compared
    # against a hardcoded literal that could silently drift from the legacy policy.
    repo, receipt, vault = run
    own.assign_p2_run(repo, commitment_id=receipt.commitment_id, clock=CLOCK)
    start = GPR.project_run(repo, receipt.run_id).current_state
    expected = _canonical_walk(start)

    seen = [start]
    for i in range(20):
        state = GPR.project_run(repo, receipt.run_id)
        if state.next_action.terminal or state.next_action.to_state is None:
            break
        result, action = cut.advance_live(
            repo, receipt.run_id, vault=vault, session=_session(),
            idempotency_key=f"s{i}", live=True, clock=CLOCK,
        )
        assert action.diverged is False  # no spurious veto on the happy path
        seen.append(result.to_state)

    assert seen == expected
    # Sanity: the independent legacy walk actually reached the terminal state.
    assert expected[0] == "ready" and expected[-1] == "complete"


def test_advance_live_veto_persists_typed_marker(run, monkeypatch):
    # Audit M4/D5: a staged veto in advance_live must persist a typed run-level MARKER
    # (deferred/waiting + the veto reason) so a caller loop can observe the deferral.
    # Pre-fix the veto returned (None, action) but persisted nothing -- the deferral was
    # invisible. The marker is an inspectable artifact, NOT a run state change.
    import json

    repo, receipt, vault = run
    run_id = receipt.run_id
    before_state = GPR.project_run(repo, run_id).current_state
    before_events = len(repo.golden_path_run_events_for(run_id))

    veto = cut.LiveNextAction(
        to_state=None, reason="staged veto (evsi:stop_waiting_for_delay_or_fresh_surface)",
        terminal=False, authority="staged_veto", diverged=True, staged_decision_id="d1",
        staged_action=A.STOP, veto_reason="evsi:stop_waiting_for_delay_or_fresh_surface",
    )
    monkeypatch.setattr(cut, "staged_next_action", lambda *a, **k: veto)

    result, action = cut.advance_live(
        repo, run_id, vault=vault, session=_session(), idempotency_key="idem-1", clock=CLOCK,
    )
    assert result is None and action is veto

    markers = repo.golden_path_artifacts_for(run_id, kind="staged_veto_deferred")
    assert len(markers) == 1
    payload = json.loads(markers[0]["payload_json"])
    assert payload["status"] == "deferred"
    assert payload["veto_reason"] == "evsi:stop_waiting_for_delay_or_fresh_surface"

    # No run event-stream state change beyond the marker artifact.
    assert GPR.project_run(repo, run_id).current_state == before_state
    assert len(repo.golden_path_run_events_for(run_id)) == before_events

    # Idempotent: a retry with the same key collapses to exactly one marker.
    cut.advance_live(repo, run_id, vault=vault, session=_session(), idempotency_key="idem-1", clock=CLOCK)
    assert len(repo.golden_path_artifacts_for(run_id, kind="staged_veto_deferred")) == 1


# --- veto predicate: only a named constraint/EVSI reason diverges ----------------

def test_ladder_stop_is_not_a_veto():
    result = sp.DecisionResult(
        decision_id="d", already=False, action=A.STOP, subtype=A.STOP_NO_POSITIVE_ROBUST_VALUE,
        staged_rule="no_positive_value_stop", chosen_candidate_ref=None,
        stop_reason=A.STOP_NO_POSITIVE_ROBUST_VALUE, snapshot_hash="h", trace={},
    )
    assert cut._constraint_or_evsi_veto(result) is None


def test_evsi_abstain_is_a_veto():
    result = sp.DecisionResult(
        decision_id="d", already=False, action=A.STOP,
        subtype=A.STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE, staged_rule="evsi_abstained",
        chosen_candidate_ref=None, stop_reason=A.STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE,
        snapshot_hash="h", trace={},
    )
    veto = cut._constraint_or_evsi_veto(result)
    assert veto is not None and veto.startswith("evsi:")


def test_constraint_emptied_feasible_set_is_a_veto():
    import learnloop.services.constraint_engine as ce
    from learnloop.services import controller_snapshot as cs

    cand = cs.Candidate(candidate_ref="c1")
    reason = ce.ExclusionReason("hard_exposure_collision", 1, "exact_surface_collision")
    report = ce.FeasibilityReport(
        feasible=[], excluded=[(cand, ce.Feasibility("c1", (reason,)))],
        per_candidate={"c1": ce.Feasibility("c1", (reason,))}, manifest_hash="m",
    )
    result = sp.DecisionResult(
        decision_id="d", already=False, action=A.STOP, subtype=A.STOP_NO_FEASIBLE_ACTIVITY,
        staged_rule="no_feasible_activity", chosen_candidate_ref=None,
        stop_reason=A.STOP_NO_FEASIBLE_ACTIVITY, snapshot_hash="h", trace={}, feasibility=report,
    )
    veto = cut._constraint_or_evsi_veto(result)
    assert veto is not None and veto.startswith("constraint:hard_exposure_collision")


def test_ownership_only_emptying_is_not_a_veto():
    import learnloop.services.constraint_engine as ce
    from learnloop.services import controller_snapshot as cs

    cand = cs.Candidate(candidate_ref="c1")
    reason = ce.ExclusionReason(sp.OWNERSHIP_REFUSAL_KEY, 1, "not_owned_by_staged_controller")
    report = ce.FeasibilityReport(
        feasible=[], excluded=[(cand, ce.Feasibility("c1", (reason,)))],
        per_candidate={"c1": ce.Feasibility("c1", (reason,))}, manifest_hash="m",
    )
    result = sp.DecisionResult(
        decision_id="d", already=False, action=A.STOP, subtype=A.STOP_NO_FEASIBLE_ACTIVITY,
        staged_rule="no_feasible_activity", chosen_candidate_ref=None,
        stop_reason=A.STOP_NO_FEASIBLE_ACTIVITY, snapshot_hash="h", trace={}, feasibility=report,
    )
    assert cut._constraint_or_evsi_veto(result) is None


# --- the six ordered gates ------------------------------------------------------

def test_all_six_cutover_gates_pass_in_order(run):
    repo, receipt, vault = run

    def exposure_probe():
        resolved = resolve_legacy_item(
            vault, repo, vault.practice_items["pi_probe"], purpose="assessment", clock=CLOCK,
        )
        reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
        return cut.cross_seam_exposure_probe(
            lambda: Repository(repo.sqlite_path),
            open_administration=lambda r: open_administration(
                r, resolved=resolved, reservation=reservation, clock=CLOCK
            ),
        )

    report = cut.run_cutover_gates(
        repo, vault=vault, session=_session(), run_id=receipt.run_id,
        commitment_id=receipt.commitment_id, exposure_probe=exposure_probe, clock=CLOCK,
    )
    assert report.barrier_ok, report.as_dict()
    assert report.all_cleared
    names = [g.name for g in report.gates]
    assert names == [
        "shadow_parity_baseline", "ownership_assignment_for_p2", "staged_live_for_owned",
        "cross_seam_exposure_integrity", "affect_and_one_edge_discipline", "rollback_to_legacy",
    ]
    # After gate f the commitment is back with legacy (rollback restored legacy exactly).
    assert own.resolve_owner(repo, receipt.commitment_id) == own.LEGACY


def test_rollback_switch_returns_owned_to_legacy(run):
    repo, receipt, vault = run
    own.assign_p2_run(repo, commitment_id=receipt.commitment_id, clock=CLOCK)
    assert own.is_staged_owned(repo, receipt.commitment_id)
    receipt_out = cut.rollback(repo, reason="test", clock=CLOCK)
    assert receipt_out["count"] == 1
    assert own.resolve_owner(repo, receipt.commitment_id) == own.LEGACY
    # A subsequent bridge call falls back to legacy authority exactly.
    action = cut.staged_next_action(repo, receipt.run_id, vault=vault, session=_session(),
                                    live=True, clock=CLOCK)
    assert action.authority == "legacy"
