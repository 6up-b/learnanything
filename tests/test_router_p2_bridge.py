"""Router R2a: the P2 bridge wired into ``golden_path.advance`` (D13, plan §5.5).

At the R2a successor with ``router.enabled`` on, ``golden_path.advance`` goes
through ``controller_cutover.advance_live``: the staged policy is consulted for
a staged-owned run and its decision is logged as a ``staged_p2`` router row.
A requested ``to_state`` that is not the canonical successor is the learner's
own choice (owner Q10): it advances the run and is logged as a learner pick. A
staged veto defers the run (no transition) and the RPC says so in one plain
sentence. Switched off, or below the successor, the RPC calls
``golden_path_run.advance`` directly, exactly as before. P2-owned items stay
out of the daily plan (the staged-owned exclusion in ``build_due_queue``).

Fail-first (plan §9 R2a, item 4): ``golden_path.advance`` bypassed the bridge.
"""

from __future__ import annotations

import json

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.curriculum import golden_path_run as GPR
from learnloop.scheduling import controller_cutover as cut
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import _set_algorithm_version_at, append_config_toml
from tests.test_router_staged_p2 import CLOCK, _rows, _run


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _ctx(root):
    ctx = SidecarContext()
    ctx.load(root)
    return ctx


def _staged_rows(repo):
    return [row for row in _rows(repo) if row["decision_kind"] == "staged_p2"]


def _advance(ctx, run_id, to_state, reason, key="k1"):
    return _call(ctx, "golden_path.advance", {
        "runId": run_id, "toState": to_state, "reason": reason, "idempotencyKey": key,
    })


def test_golden_path_advance_consults_the_staged_policy_through_the_bridge(tmp_path):
    repo, receipt, vault = _run(tmp_path)
    canonical = GPR.project_run(repo, receipt.run_id).next_action
    assert canonical.to_state is not None
    # Below the successor the RPC calls the run directly: nothing is logged.
    before = _advance(_ctx(vault.root), receipt.run_id, canonical.to_state, canonical.reason, key="below")
    assert before["state"]["currentState"] == canonical.to_state
    assert _staged_rows(repo) == []

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION

    _set_algorithm_version_at(vault.root, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    canonical = GPR.project_run(repo, receipt.run_id).next_action
    result = _advance(_ctx(vault.root), receipt.run_id, canonical.to_state, canonical.reason, key="at-a")
    [row] = _staged_rows(repo)
    assert row["detail_json"]["run_id"] == receipt.run_id
    assert row["detail_json"]["authority"] == "staged" and row["learner_pick"] == 0
    assert result["bridge"]["authority"] == "staged"
    assert result["state"]["currentState"] == canonical.to_state


def test_a_requested_state_other_than_the_canonical_successor_is_the_learners_choice(tmp_path):
    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION

    repo, receipt, vault = _run(tmp_path)
    _set_algorithm_version_at(vault.root, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    state = GPR.project_run(repo, receipt.run_id)
    canonical = state.next_action
    other = next(
        to for to in GPR.ALLOWED_TRANSITIONS.get(state.current_state, ())
        if to != canonical.to_state and to not in GPR.TERMINAL_STATES
    )
    result = _advance(_ctx(vault.root), receipt.run_id, other, "learner asked", key="pick")
    assert result["state"]["currentState"] == other
    assert result["bridge"]["authority"] == "learner_choice"
    [row] = _staged_rows(repo)
    assert (row["learner_pick"], row["propensity"], row["propensity_kind"]) == (1, None, "none")


def test_a_staged_veto_defers_the_run_and_says_why_in_plain_words(tmp_path, monkeypatch):
    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.router.why import jargon_in

    repo, receipt, vault = _run(tmp_path)
    _set_algorithm_version_at(vault.root, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    monkeypatch.setattr(
        cut, "_constraint_or_evsi_veto", lambda result: "constraint:hard_exposure_collision:exact_surface_collision"
    )
    state = GPR.project_run(repo, receipt.run_id)
    result = _advance(_ctx(vault.root), receipt.run_id, state.next_action.to_state, state.next_action.reason)
    assert result["result"] is None
    assert result["state"]["currentState"] == state.current_state  # no transition
    deferred = result["bridge"]["deferred"]
    assert deferred["vetoReason"] == "constraint:hard_exposure_collision:exact_surface_collision"
    assert deferred["message"] and jargon_in(deferred["message"]) == []
    [row] = _staged_rows(repo)
    assert row["detail_json"]["authority"] == "staged_veto"


def test_switched_off_the_rpc_advances_the_run_directly(tmp_path):
    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION

    repo, receipt, vault = _run(tmp_path)
    _set_algorithm_version_at(vault.root, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    append_config_toml(vault.root, "\n[router]\nenabled = false\n")
    canonical = GPR.project_run(repo, receipt.run_id).next_action
    result = _advance(_ctx(vault.root), receipt.run_id, canonical.to_state, canonical.reason)
    assert result["state"]["currentState"] == canonical.to_state
    assert "bridge" not in result
    assert _staged_rows(repo) == []


def test_the_response_shape_is_unchanged_for_the_desktop(tmp_path):
    """``result`` and ``state`` keep their shape; ``bridge`` is an addition."""

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION

    repo, receipt, vault = _run(tmp_path)
    _set_algorithm_version_at(vault.root, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    canonical = GPR.project_run(repo, receipt.run_id).next_action
    result = _advance(_ctx(vault.root), receipt.run_id, canonical.to_state, canonical.reason)
    assert set(result["result"]) >= {"runId", "eventId", "fromState", "toState", "alreadyExists"}
    assert set(result["state"]) >= {"runId", "currentState", "nextAction", "history"}
    json.dumps(result)


def test_a_retried_constraint_vetoed_advance_stays_deferred(tmp_path):
    """Codex review F1: a retry of a constraint-vetoed advance (the desktop
    reuses the idempotency key while the run head is unchanged) reloads the
    standing staged decision, which carries no in-memory feasibility report.
    The veto must be read back from the persisted trace, so the retry defers
    too and neither call advances the run."""

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.curriculum import commitments as C

    repo, receipt, vault = _run(tmp_path)
    _set_algorithm_version_at(vault.root, ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    # The run owns its exemplar item, and the item is inactive: the staged
    # block's only owned candidate is refused by ``active_status`` (a real
    # constraint, not ownership), so the decision stops no_feasible_activity.
    C.add_target(
        repo, commitment_id=receipt.commitment_id,
        target={"target_kind": "legacy_practice_item", "target_ref": "pi_svd_define_001", "role": "required"},
        clock=CLOCK,
    )
    ctx = _ctx(vault.root)  # loading the vault re-activates its items, so deactivate after
    repo.set_practice_item_active("pi_svd_define_001", active=False, clock=CLOCK)
    state = GPR.project_run(repo, receipt.run_id)
    events_before = len(repo.golden_path_run_events_for(receipt.run_id))

    first = _advance(ctx, receipt.run_id, state.next_action.to_state, state.next_action.reason, key="same")
    assert first["result"] is None
    assert first["bridge"]["deferred"]["vetoReason"] == "constraint:active_status:card_inactive"

    retry = _advance(ctx, receipt.run_id, state.next_action.to_state, state.next_action.reason, key="same")
    assert retry["result"] is None, "a retried veto must not advance the run"
    assert retry["bridge"]["authority"] == "staged_veto"
    assert retry["bridge"]["deferred"]["vetoReason"] == first["bridge"]["deferred"]["vetoReason"]
    assert retry["bridge"]["stagedDecisionId"] == first["bridge"]["stagedDecisionId"]
    assert GPR.project_run(repo, receipt.run_id).current_state == state.current_state
    assert len(repo.golden_path_run_events_for(receipt.run_id)) == events_before
    assert len(repo.golden_path_artifacts_for(receipt.run_id, kind="staged_veto_deferred")) == 1


def test_a_standing_decisions_persisted_trace_names_the_same_veto():
    """F1, unit: a decision reloaded from its row has no feasibility report;
    its trace's exclusions decide the veto, and an ownership-only refusal is
    still not one."""

    from learnloop.scheduling import controller_actions as A
    from learnloop.scheduling import staged_policy as sp

    def standing(exclusions):
        return sp.DecisionResult(
            decision_id="d", already=True, action=A.STOP, subtype=A.STOP_NO_FEASIBLE_ACTIVITY,
            staged_rule="no_feasible_activity", chosen_candidate_ref=None,
            stop_reason=A.STOP_NO_FEASIBLE_ACTIVITY, snapshot_hash="h",
            trace={"exclusions": exclusions},
        )

    owned_only = {"b": [{"constraint_key": sp.OWNERSHIP_REFUSAL_KEY, "reason": "not_owned_by_staged_controller"}]}
    assert cut._constraint_or_evsi_veto(standing(owned_only)) is None
    real = {
        **owned_only,
        "a": [{"constraint_key": "assessment_reservation", "reason": "reserved_assessment_surface"}],
    }
    assert cut._constraint_or_evsi_veto(standing(real)) == "constraint:assessment_reservation:reserved_assessment_surface"
