"""P2 steps B.9 + B.10 -- post-attempt restoration + boundary diff, and the
milestone + one-edge ``suggest_next`` depth invitation
(spec_p2_narrow_golden_path §8.4, §7.5; §12.5, §12.3.1; migration 087 artifacts).

Restoration is an INSTRUCTIONAL EVENT AFTER MEASUREMENT (§8.4): it restores the
learner's source context, diffs the demonstrated boundary against the diagnostic
baseline, and records the achieved milestone + the single reviewed next edge -- but
it CANNOT modify the assessment observation or continue its measurement segment, so
it appends nothing to the measurement substrate, only inspectable run artifacts.

The headline P2 acceptance -- NO UNPROMPTED DEPTH ACTIVATION -- lives here. On a
passed cold assessment we:

  1. append ``depth_milestone_reached`` (P1 commitment event only, no version bump,
     A.3) via ``commitments.record_milestone_reached``;
  2. evaluate exactly ONE outgoing reviewed edge via the landed P1
     ``depth_transition.commit_one_edge`` -- which, with U-018 double-gated OFF
     (``depth_transition.LIVE_ACTIVATION_ENABLED = False``), returns a
     ``TransitionProposal(kind="suggest_next")`` and ACTIVATES NOTHING.

The invitation is persisted; it activates ONLY on an explicit learner accept, and
even then not while U-018 is off. ``accept_depth_invitation`` records intent as a
non-pinnable draft path (P0 §3.4) and MUST NOT auto-append an authorized successor
while the gate is off; ``decline_depth_invitation`` logs the decision.
"""

from __future__ import annotations

import json as _json_mod
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import depth_transition as DT
from learnloop.services import diagnostic_pack as DP
from learnloop.services import golden_path_run as GPR
from learnloop.services.activities import _json
from learnloop.services.golden_path_assessment import DEMONSTRATED_CLAIM_CERTAINTY

RESTORATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RestorationReceipt:
    run_id: str
    boundary_diff: dict[str, Any]
    source_neighborhoods: dict[str, Any]
    exemplar_comparison: list[dict[str, Any]]
    achieved_milestone: str | None
    active_envelope_version_id: str | None
    next_reviewed_edge: dict[str, Any] | None
    next_action: str
    milestone_recorded: bool = False
    invitation: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Reviewed-edge helpers
# ---------------------------------------------------------------------------

def _reviewed_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]:
    if not envelope_version_id:
        return []
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        return []
    return [e for e in _json_mod.loads(row["reviewed_edges_json"] or "[]") if e.get("reviewed")]


def _invited_edge_for_milestone(
    repository: Repository, run: Mapping[str, Any], milestone: str | None
) -> dict[str, Any] | None:
    """The one reviewed edge to invite at the ACHIEVED milestone (C6): the edge whose
    ``predecessor_milestone`` equals the achieved milestone. An edge that declares no
    predecessor departs from the run's baseline milestone (the launch stub shape), so it
    is the fallback when no edge names this milestone explicitly. One edge per decision
    (§7.5) -- never a chained climb."""

    edges = _reviewed_edges(repository, run["depth_envelope_version_id"])
    if not edges:
        return None
    for edge in edges:
        if edge.get("predecessor_milestone") == milestone:
            return edge
    for edge in edges:
        if not edge.get("predecessor_milestone"):
            return edge
    return None


def _blueprint_spec(repository: Repository, run: Mapping[str, Any]) -> dict[str, Any]:
    version = repository.task_blueprint_version(run["blueprint_version_id"])
    return _json_mod.loads(version["spec_json"]) if version else {}


# ---------------------------------------------------------------------------
# Boundary diff (§8.4) -- baseline boundary_view vs post-assessment, reliability-aware
# ---------------------------------------------------------------------------

def boundary_diff(repository: Repository, *, run_id: str, result: Mapping[str, Any]) -> dict[str, Any]:
    """Diff the demonstrated boundary before/after the cold assessment (§8.4).

    ``before`` is the baseline boundary snapshot frozen at diagnostic-segment close
    (``diagnostic_pack.snapshot_baseline_boundary`` -- the real baseline projection, not
    a hardcoded ``untested``); if no segment ever closed (no instruction ran) it falls
    back to the live baseline projection. ``after`` overlays the cold-assessment outcome
    onto the covered cells, reliability-aware: each moved cell carries the result's claim
    language, interval, and calibration status (P0 DTO rule). One success does not certify
    unsupported cells; one failure does not erase earlier component evidence -- so only the
    covered cells move, and a failure moves them to ``weak``/``developing`` rather than
    clearing anything."""

    snapshot = repository.latest_golden_path_artifact(run_id, kind="baseline_boundary")
    if snapshot is not None:
        before = _json_mod.loads(snapshot["payload_json"])
    else:
        before = DP.boundary_view(repository, run_id=run_id)
    before_by_cell = {(c["facet"], c["capability"]): c["status"] for c in before["cells"]}

    covered = {(c["facet"], c["capability"]) for c in result.get("coverage") or []}
    passed = bool(result.get("passed"))
    point = float(result.get("point") or 0.0)
    claim_language = result.get("claim_language", "provisional")

    if passed:
        after_status = "demonstrated" if point >= DEMONSTRATED_CLAIM_CERTAINTY else "developing"
    else:
        after_status = "weak"

    cells: list[dict[str, Any]] = []
    for (facet, cap), before_status in before_by_cell.items():
        is_covered = (facet, cap) in covered
        status = after_status if is_covered else before_status
        cell = {
            "facet": facet,
            "capability": cap,
            "before": before_status,
            "after": status,
            "changed": is_covered and status != before_status,
        }
        if is_covered:
            # Reliability-aware fields per moved cell (§5.3 / P0 read-DTO rule).
            cell["claim_language"] = claim_language
            cell["interval"] = result.get("interval") or {}
            cell["calibration_status"] = result.get("calibration_status")
        cells.append(cell)

    return {
        "schema_version": RESTORATION_SCHEMA_VERSION,
        "run_id": run_id,
        "cells": cells,
        "passed": passed,
        "target_contract_version_id": result.get("target_contract_version_id"),
    }


# ---------------------------------------------------------------------------
# Milestone + one-edge suggest_next invitation (§7.5) -- NEVER activates
# ---------------------------------------------------------------------------

def record_milestone_and_invite(
    repository: Repository,
    *,
    run_id: str,
    idempotency_key: str,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """On a passed cold assessment, append the milestone fact and evaluate ONE
    reviewed edge as a ``suggest_next`` invitation (§7.5). Returns the invitation
    payload (or None when no reviewed edge exists).

    The INVITATION never activates -- it renders the reviewed edge as ``suggest_next``
    and activation happens ONLY on an explicit :func:`accept_depth_invitation`. So the
    edge is evaluated here with activation force-disabled (``live_activation_enabled=
    False``) EVEN under the acceptance harness's flipped gate: a milestone is never an
    unprompted depth activation (the headline P2 acceptance)."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")

    # C6: record the PROJECTED current milestone (folded from the run event stream), not
    # the run's initial milestone -- a run that reached a later milestone records THAT one.
    milestone = GPR.project_run(repository, run_id).milestone or run["initial_milestone"]
    # Milestone-reached: P1 commitment event only, no version bump (A.3). Idempotent
    # via the commitment event's own natural key is not guaranteed, so we guard on the
    # persisted milestone artifact instead.
    if repository.latest_golden_path_artifact(run_id, kind="milestone") is None:
        C.record_milestone_reached(
            repository, commitment_id=run["commitment_id"], milestone_slug=milestone, clock=clock,
        )
        repository.append_golden_path_artifact(
            run_id=run_id, kind="milestone",
            payload_json=_json({"milestone_slug": milestone, "event_only": True}),
            idempotency_key=idempotency_key + ":milestone", clock=clock,
        )

    # C6: invite the reviewed edge whose predecessor is the ACHIEVED milestone.
    edge = _invited_edge_for_milestone(repository, run, milestone)
    if edge is None:
        return None

    existing = repository.latest_golden_path_artifact(run_id, kind="depth_invitation")
    if existing is not None:
        return _json_mod.loads(existing["payload_json"])

    # Evaluate exactly one reviewed edge through the landed P1 transition service. With
    # the U-018 gate OFF this returns TransitionProposal(kind="suggest_next"): it runs
    # every check but activates nothing (§7.5 / §13). NO successor is appended.
    outcome = DT.commit_one_edge(
        repository,
        commitment_id=run["commitment_id"],
        milestone=milestone,
        selected_edge_id=edge["edge_id"],
        evidence_receipt={"qualifies": True, "evidence_receipt": run_id, "decision_id": idempotency_key},
        live_activation_enabled=False,
    )
    invitation = {
        "milestone_slug": milestone,
        "edge": edge,
        "served_as": "suggest_next",
        "activated": bool(getattr(outcome, "committed", False)),
        "outcome": outcome.as_dict(),
    }
    repository.append_golden_path_artifact(
        run_id=run_id, kind="depth_invitation",
        payload_json=_json(invitation),
        idempotency_key=idempotency_key + ":invitation", clock=clock,
    )
    return invitation


# ---------------------------------------------------------------------------
# Restoration (§8.4)
# ---------------------------------------------------------------------------

def restore(
    repository: Repository,
    *,
    run_id: str,
    idempotency_key: str,
    clock: Clock | None = None,
) -> RestorationReceipt:
    """Restore source context + boundary diff after the grade is committed (§8.4).

    Requires a persisted cold-assessment result (measurement complete). Advances the
    run ``assessing -> restoring`` (idempotent) and records the boundary-diff +
    restoration artifacts and, on a pass, the milestone + one reviewed ``suggest_next``
    edge. Appends NOTHING to the measurement substrate (cannot modify the observation)."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")

    result_row = repository.latest_golden_path_artifact(run_id, kind="assessment_result")
    if result_row is None:
        raise ValueError(f"run {run_id}: cannot restore before the assessment is graded")
    result = _json_mod.loads(result_row["payload_json"])

    # assessing -> restoring (idempotent). Restoration begins only after measurement.
    state = GPR.project_run(repository, run_id)
    if state.current_state == "assessing":
        GPR.advance(
            repository, run_id, to_state="restoring",
            reason="restore source + boundary diff after grade commit",
            idempotency_key=idempotency_key + ":enter", clock=clock,
        )

    diff = boundary_diff(repository, run_id=run_id, result=result)
    if repository.latest_golden_path_artifact(run_id, kind="boundary_diff") is None:
        repository.append_golden_path_artifact(
            run_id=run_id, kind="boundary_diff",
            payload_json=_json(diff),
            idempotency_key=idempotency_key + ":boundary_diff", clock=clock,
        )

    spec = _blueprint_spec(repository, run)
    passed = bool(result.get("passed"))
    # Source neighborhoods tied to missed/strong criteria (§8.4).
    neighborhoods = dict(spec.get("source_neighborhoods") or {})
    source_neighborhoods = {
        "all": neighborhoods,
        "emphasis": "strong_criteria" if passed else "missed_criteria",
    }
    exemplar_comparison = [
        {"exemplar_ref": e.get("exemplar_ref"), "weight": e.get("weight"), "held_out": bool(e.get("held_out"))}
        for e in spec.get("exemplars") or []
    ]

    invitation: dict[str, Any] | None = None
    milestone_recorded = False
    if passed:
        invitation = record_milestone_and_invite(
            repository, run_id=run_id, idempotency_key=idempotency_key, clock=clock,
        )
        milestone_recorded = True

    # C6: the achieved milestone + invited edge follow the PROJECTED current milestone.
    achieved_milestone = GPR.project_run(repository, run_id).milestone or run["initial_milestone"]
    edge = _invited_edge_for_milestone(repository, run, achieved_milestone)
    if passed and invitation is not None:
        next_action = "confirm_reviewed_edge"  # a one-tap suggest_next (never auto-fires)
    elif passed:
        next_action = "maintain"
    else:
        next_action = "repair"

    receipt = RestorationReceipt(
        run_id=run_id,
        boundary_diff=diff,
        source_neighborhoods=source_neighborhoods,
        exemplar_comparison=exemplar_comparison,
        achieved_milestone=achieved_milestone if passed else None,
        active_envelope_version_id=run["depth_envelope_version_id"],
        next_reviewed_edge=edge,
        next_action=next_action,
        milestone_recorded=milestone_recorded,
        invitation=invitation,
    )
    if repository.latest_golden_path_artifact(run_id, kind="restoration") is None:
        repository.append_golden_path_artifact(
            run_id=run_id, kind="restoration",
            payload_json=_json({"schema_version": RESTORATION_SCHEMA_VERSION, **receipt.as_dict()}),
            idempotency_key=idempotency_key + ":restoration", clock=clock,
        )
    return receipt


# ---------------------------------------------------------------------------
# Explicit learner accept / decline of the depth invitation (§7.5)
# ---------------------------------------------------------------------------

def accept_depth_invitation(
    repository: Repository,
    *,
    run_id: str,
    idempotency_key: str,
    live_activation_enabled: bool | None = None,
    fork_edit: Mapping[str, Any] | None = None,
    goal_id: str | None = None,
    proposed_contract_body: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's EXPLICIT acceptance of the reviewed depth edge (§7.5).

    While U-018 is off (default), this records ACCEPT INTENT as a non-pinnable draft
    path (P0 §3.4) and MUST NOT append an authorized successor or activate the edge --
    the run keeps its completed result and its milestone. When the acceptance harness
    flips ``depth_transition.LIVE_ACTIVATION_ENABLED`` on and the policy is
    ``auto_within_envelope``, ``commit_one_edge`` activates EXACTLY ONE edge and the
    run replans into ``deepening``."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")
    invitation_row = repository.latest_golden_path_artifact(run_id, kind="depth_invitation")
    if invitation_row is None:
        raise ValueError(f"run {run_id}: no depth invitation to accept")
    invitation = _json_mod.loads(invitation_row["payload_json"])
    edge = invitation["edge"]

    outcome = DT.commit_one_edge(
        repository,
        commitment_id=run["commitment_id"],
        milestone=invitation["milestone_slug"],
        selected_edge_id=edge["edge_id"],
        evidence_receipt={"qualifies": True, "evidence_receipt": run_id, "decision_id": idempotency_key},
        goal_id=goal_id,
        proposed_contract_body=proposed_contract_body,
        fork_edit=fork_edit,
        live_activation_enabled=live_activation_enabled,
        clock=clock,
    )
    activated = bool(getattr(outcome, "committed", False))

    if activated:
        # Live activation (harness / U-018): commit_one_edge already appended the
        # milestone + depth_transition_committed events atomically (exactly one edge).
        # The run replans into `deepening`.
        state = GPR.project_run(repository, run_id)
        if state.current_state in ("restoring", "maintaining"):
            GPR.advance(
                repository, run_id, to_state="deepening",
                reason="learner confirmed reviewed depth edge; activate one edge + replan",
                idempotency_key=idempotency_key + ":deepen",
                successor_milestone=edge.get("milestone_slug"), clock=clock,
            )

    payload = {
        "edge_id": edge["edge_id"],
        "intent_recorded": True,
        "activated": activated,
        # A non-pinnable draft path while U-018 is off: intent is preserved but NO
        # authorized successor is appended (§3.4 / §7.5). The proposal outcome is the
        # inspectable draft.
        "draft": None if activated else outcome.as_dict(),
        "outcome": outcome.as_dict(),
    }
    repository.append_golden_path_artifact(
        run_id=run_id, kind="depth_accept",
        payload_json=_json(payload),
        idempotency_key=idempotency_key + ":accept", clock=clock,
    )
    return payload


def decline_depth_invitation(
    repository: Repository,
    *,
    run_id: str,
    idempotency_key: str,
    reason: str | None = None,
    to_state: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Log the learner's explicit decline of the depth invitation (§7.5). The reached
    milestone stays reached; the envelope is never widened. Optionally maintains/stops
    the run (``to_state``) -- it never downgrades the completed result."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")
    payload = {"declined": True, "reason": reason or "learner_declined"}
    repository.append_golden_path_artifact(
        run_id=run_id, kind="depth_decline",
        payload_json=_json(payload),
        idempotency_key=idempotency_key + ":decline", clock=clock,
    )
    if to_state is not None:
        state = GPR.project_run(repository, run_id)
        allowed = GPR.ALLOWED_TRANSITIONS.get(state.current_state, frozenset())
        if to_state in allowed:
            GPR.advance(
                repository, run_id, to_state=to_state,
                reason=f"depth invitation declined: {payload['reason']}",
                idempotency_key=idempotency_key + ":decline_state", clock=clock,
            )
    return payload
