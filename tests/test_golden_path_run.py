"""P2 step 3 -- golden-path run state machine + resume (spec_p2 §4, §12.6)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import golden_path_run as GPR
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


@pytest.fixture
def run(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    item = next(iter(vault.practice_items.values()))
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
    return repo, receipt


def test_confirmation_seeds_ready_state_and_run_started_event(run):
    repo, receipt = run
    state = GPR.project_run(repo, receipt.run_id)
    assert state.current_state == "ready"
    assert state.event_count == 1
    assert state.history[0]["to_state"] == "ready"
    assert state.next_action.to_state == "measuring"


def test_full_canonical_walk_visits_every_stage_in_order(run):
    repo, receipt = run
    seen = ["ready"]
    for i in range(20):
        state = GPR.project_run(repo, receipt.run_id)
        if state.next_action.terminal or state.next_action.to_state is None:
            break
        res = GPR.advance_canonical(repo, receipt.run_id, idempotency_key=f"s{i}", clock=CLOCK)
        seen.append(res.to_state)
    assert seen == [
        "ready", "measuring", "triaging", "instructing", "practicing",
        "ready_to_assess", "assessing", "restoring", "deepening", "complete",
    ]


def test_every_transition_logs_current_goal_contract_head(run):
    repo, receipt = run
    GPR.advance(repo, receipt.run_id, to_state="measuring", reason="baseline", idempotency_key="k1", clock=CLOCK)
    head = repo.fetch_goal_contract_head("g1")["head_version_id"]
    events = repo.golden_path_run_events_for(receipt.run_id)
    # The run_started event and the measuring transition both pin the head version.
    assert all(e["goal_contract_head_version_id"] == head for e in events)


def test_illegal_transition_refused(run):
    repo, receipt = run
    # ready -> assessing is not a permitted adjacency.
    with pytest.raises(GPR.IllegalTransition):
        GPR.advance(repo, receipt.run_id, to_state="assessing", reason="skip", idempotency_key="bad", clock=CLOCK)


def test_never_reopens_a_closed_diagnostic_segment(run):
    repo, receipt = run
    GPR.advance(repo, receipt.run_id, to_state="measuring", reason="baseline", idempotency_key="k1", clock=CLOCK)
    GPR.advance(repo, receipt.run_id, to_state="instructing", reason="teach", idempotency_key="k2", clock=CLOCK)
    # instructing can never lead back to measuring (invariant 7 / §4.1).
    with pytest.raises(GPR.IllegalTransition):
        GPR.advance(repo, receipt.run_id, to_state="measuring", reason="remeasure", idempotency_key="k3", clock=CLOCK)


def test_idempotent_replay_yields_exactly_one_transition(run):
    repo, receipt = run
    first = GPR.advance(repo, receipt.run_id, to_state="measuring", reason="baseline", idempotency_key="dup", clock=CLOCK)
    again = GPR.advance(repo, receipt.run_id, to_state="measuring", reason="baseline", idempotency_key="dup", clock=CLOCK)
    assert again.already_exists is True and again.event_id == first.event_id
    assert len(repo.golden_path_run_events_for(receipt.run_id)) == 2  # run_started + one measuring


def test_optimistic_head_fence_rejects_stale_expected_head(run):
    repo, receipt = run
    GPR.advance(repo, receipt.run_id, to_state="measuring", reason="baseline", idempotency_key="k1", clock=CLOCK)
    # A caller fenced on the ORIGINAL head (the run_started event) is stale now.
    stale_head = repo.golden_path_run_events_for(receipt.run_id)[0]["id"]
    with pytest.raises(GPR.StaleRunHead):
        GPR.advance(
            repo, receipt.run_id, to_state="triaging", reason="triage",
            idempotency_key="k2", expected_head_event_id=stale_head, clock=CLOCK,
        )


def test_kill_resume_rebuilds_state_and_next_action_from_events(run):
    repo, receipt = run
    for i, target in enumerate(["measuring", "triaging", "instructing"]):
        GPR.advance(repo, receipt.run_id, to_state=target, reason=target, idempotency_key=f"k{i}", clock=CLOCK)

    # Simulate a process kill by corrupting the cached current_state, then rebuild
    # purely from the event log (§12.6 "rebuild from events reproduces state + next
    # feasible action").
    with repo.connection() as c:
        c.execute("UPDATE golden_path_runs SET current_state = 'draft' WHERE id = ?", (receipt.run_id,))
        c.commit()

    fresh_repo = Repository(repo.sqlite_path)
    state = GPR.project_run(fresh_repo, receipt.run_id)
    assert state.current_state == "instructing"
    assert state.next_action.to_state == "practicing"

    # A retried transition after resume does not choose a second item.
    replay = GPR.advance(fresh_repo, receipt.run_id, to_state="instructing", reason="instructing", idempotency_key="k2")
    assert replay.already_exists is True
    assert len(fresh_repo.golden_path_run_events_for(receipt.run_id)) == 4
