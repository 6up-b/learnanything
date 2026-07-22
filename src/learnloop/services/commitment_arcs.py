"""P3 slice 3, step 9 -- commitment arcs (spec_p3_reader_integration §10.1/§10.2,
design B step 9).

An arc is the longitudinal reading -> practice PROGRAM composed with a P1
commitment: a conditional stage machine (comprehend -> complete -> retrieve ->
discriminate -> integrate -> transfer -> revisit), NOT a precomputed set of due
dates (§10.1). Arc state is a projection over:

  * **memory time** -- card/readiness decay and due constraints (surfaced from the
    commitment disposition; arcs do not own scheduling);
  * **arc time** -- the intended stage and evidence-gated progress (folded from the
    append-only ``commitment_arc_events``).

An arc version PINS the commitment's active P1 depth-policy/envelope version and
maps each stage to a reviewed depth-milestone edge. The projector may record an
achieved stage and request EXACTLY ONE P1 automatic transition through the landed
``depth_transition.commit_one_edge``; it CANNOT create an edge, widen an envelope,
or transfer scheduling state across a card fork (§10.1, invariant 1.1.13). It never
hard-gates continued reading.

No new evidence enters here. ``wanted_more_depth``/dwell/highlight/affect prioritize
a displayed edge inside the active envelope but carry no authorization: crossing the
envelope opens an editable successor proposal requiring confirmation (§10.2,
§15.6.1). Reading signals reaching an arc are salience-only (firewall §C).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import depth_transition as DT
from learnloop.services.activities import _canonical_hash, _json

# The default conditional stage ladder (§10.1). An arc may override the ordered set;
# the transitions are conditional (evidence-gated), never precomputed due dates.
DEFAULT_STAGES: tuple[str, ...] = (
    "comprehend", "complete", "retrieve", "discriminate", "integrate", "transfer",
    "revisit",
)

ARC_SCHEMA_VERSION = 1


class ArcError(ValueError):
    """Domain error for the commitment-arc service."""


def _reviewed_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]:
    if not envelope_version_id:
        return []
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        return []
    import json as _json_mod

    return _json_mod.loads(row["reviewed_edges_json"] or "[]")


def _stage_milestone_map(
    stages: Sequence[str], reviewed_edges: Sequence[Mapping[str, Any]]
) -> dict[str, str]:
    """Map each arc stage to the reviewed depth-milestone edge whose
    ``predecessor_milestone`` names that stage, else fall back to positional order.
    Only reviewed edges participate (§10.1)."""

    edges = [e for e in reviewed_edges if e.get("reviewed") and e.get("edge_id")]
    mapping: dict[str, str] = {}
    remaining = list(edges)
    for stage in stages:
        matched = next(
            (e for e in remaining if e.get("predecessor_milestone") == stage), None
        )
        if matched is not None:
            mapping[stage] = matched["edge_id"]
            remaining.remove(matched)
    # Positional fallback for stages that named no predecessor edge.
    for stage in stages:
        if stage in mapping:
            continue
        if remaining:
            mapping[stage] = remaining.pop(0)["edge_id"]
    return mapping


def create_arc(
    repository: Repository,
    *,
    commitment_id: str,
    source_id: str | None = None,
    stages: Sequence[str] | None = None,
    pattern_refs: Sequence[str] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Create an arc bound to a commitment. Version 1 pins the commitment's active
    depth policy/envelope version and maps stages to its reviewed edges (§10.1)."""

    head = C.resolve_head(repository, commitment_id)  # raises if unknown
    ordered = tuple(stages) if stages else DEFAULT_STAGES
    reviewed = _reviewed_edges(repository, head.depth_envelope_version_id)
    stage_map = _stage_milestone_map(ordered, reviewed)

    arc_id = repository.create_commitment_arc(
        commitment_id=commitment_id, source_id=source_id, clock=clock
    )
    body = {
        "schema_version": ARC_SCHEMA_VERSION,
        "stages": list(ordered),
        "pattern_refs": list(pattern_refs or []),
        "depth_policy_version_id": head.depth_policy_version_id,
        "depth_envelope_version_id": head.depth_envelope_version_id,
        "stage_milestone_map": stage_map,
    }
    written = repository.append_commitment_arc_version(
        arc_id=arc_id,
        version={
            "pattern_refs": list(pattern_refs or []),
            "stages": list(ordered),
            "depth_policy_version_id": head.depth_policy_version_id,
            "depth_envelope_version_id": head.depth_envelope_version_id,
            "stage_milestone_map": stage_map,
            "content_hash": _canonical_hash(body),
        },
        clock=clock,
    )
    repository.append_commitment_arc_event(
        arc_id=arc_id, kind="arc_created",
        detail={"commitment_id": commitment_id, "stages": list(ordered)},
        clock=clock,
    )
    return {"arc_id": arc_id, "commitment_id": commitment_id, "version": written, **body}


def _resolve_policy(repository: Repository, policy_version_id: str | None) -> str | None:
    if not policy_version_id:
        return None
    row = repository.depth_policy_version(policy_version_id)
    return row["policy"] if row is not None else None


def project_arc(repository: Repository, *, arc_id: str) -> dict[str, Any]:
    """Rebuildable arc-state head: a projection over memory time + arc time (§10.1).

    Folds the append-only ``commitment_arc_events`` (arc time) and reads the
    commitment disposition (memory time). Pure projection -- no stored head, so it
    rebuilds deterministically after cache corruption (§15.10)."""

    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    version = repository.commitment_arc_head_version(arc_id)
    if version is None:
        raise ArcError(f"arc has no version: {arc_id!r}")
    import json as _json_mod

    stages = _json_mod.loads(version["stages_json"] or "[]")
    stage_map = _json_mod.loads(version["stage_milestone_map_json"] or "{}")
    events = repository.commitment_arc_events(arc_id)

    reached: list[str] = []
    paused = False
    for ev in events:
        detail = _json_mod.loads(ev["detail_json"] or "{}")
        if ev["kind"] in ("stage_reached", "transition_committed"):
            stage = detail.get("stage") or detail.get("milestone")
            if stage and stage not in reached:
                reached.append(stage)
        elif ev["kind"] == "arc_paused":
            paused = True
        elif ev["kind"] == "arc_resumed":
            paused = False

    # arc time: the next unreached stage in the declared order.
    current_stage = next((s for s in stages if s not in reached), None)
    # memory time: the commitment's disposition (arcs never own scheduling).
    disposition = C.resolve_disposition(repository, arc["commitment_id"])
    policy = _resolve_policy(repository, version["depth_policy_version_id"])
    reviewed = _reviewed_edges(repository, version["depth_envelope_version_id"])
    next_edge_id = stage_map.get(current_stage) if current_stage else None
    next_edge = next((e for e in reviewed if e.get("edge_id") == next_edge_id), None)

    return {
        "arc_id": arc_id,
        "commitment_id": arc["commitment_id"],
        "source_id": arc["source_id"],
        "stages": stages,
        "reached_stages": reached,
        "current_stage": current_stage,
        "policy": policy,
        "disposition": disposition,
        "paused": paused,
        "depth_policy_version_id": version["depth_policy_version_id"],
        "depth_envelope_version_id": version["depth_envelope_version_id"],
        "next_reviewed_edge": next_edge,
        "arc_time": {"current_stage": current_stage, "reached": reached},
        "memory_time": {"disposition": disposition},
    }


def preview_for_capture(*, action: str, depth_preset: str | None) -> dict[str, Any]:
    """The provisional arc shown immediately after a commit (§10.2): the declared
    stage ladder + the default policy for the action. No persistence, no promise of
    due dates -- evidence and burden may adapt it (§10.2)."""

    policy = C._ACTION_DEFAULT_POLICY.get(action, "suggest_next")  # noqa: SLF001
    return {
        "stages": list(DEFAULT_STAGES),
        "current_stage": DEFAULT_STAGES[0],
        "policy": policy,
        "depth_preset": depth_preset,
        "caveat": "evidence and burden may adapt this plan",
    }


def advance_arc(
    repository: Repository,
    *,
    arc_id: str,
    stage: str,
    evidence_receipt: Mapping[str, Any],
    selected_edge_id: str | None = None,
    goal_id: str | None = None,
    proposed_contract_body: Mapping[str, Any] | None = None,
    fork_edit: Mapping[str, Any] | None = None,
    live_activation_enabled: bool | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record an achieved stage and request EXACTLY ONE P1 automatic transition
    (§10.1/§10.2). The transition is delegated to ``depth_transition.commit_one_edge``:
    with ``hold_at_target``/``suggest_next`` it activates nothing (returns a
    suggest_next/refused proposal); only ``auto_within_envelope`` (with the U-018 gate
    on) activates one reviewed inside-envelope edge, forking material cards without
    FSRS/certification inheritance. The arc never creates an edge or widens the
    envelope itself. Idempotent on the decision receipt key."""

    view = project_arc(repository, arc_id=arc_id)
    if view["paused"]:
        return {"outcome": "refused", "reason": "arc_paused", "arc_id": arc_id, "committed": False}
    stage_map = {}
    version = repository.commitment_arc_head_version(arc_id)
    if version is not None:
        import json as _json_mod

        stage_map = _json_mod.loads(version["stage_milestone_map_json"] or "{}")
    edge_id = selected_edge_id or stage_map.get(stage)

    # Record the achieved arc stage (append-only, idempotent per stage).
    receipt_key = _canonical_hash({
        "arc_id": arc_id, "stage": stage,
        "evidence_receipt": dict(evidence_receipt).get("evidence_receipt"),
        "decision_id": dict(evidence_receipt).get("decision_id"),
    })
    stage_event = repository.append_commitment_arc_event(
        arc_id=arc_id, kind="stage_reached",
        detail={"stage": stage, "edge_id": edge_id}, receipt_key=receipt_key, clock=clock,
    )
    commitment_id = view["commitment_id"]
    # Also record the P1 commitment milestone (achievement fact, no version bump, A.3).
    C.record_milestone_reached(
        repository, commitment_id=commitment_id, milestone_slug=stage,
        detail={"arc_id": arc_id}, clock=clock,
    )

    if edge_id is None:
        return {
            "outcome": "stage_recorded", "reason": "no_reviewed_edge_for_stage",
            "arc_id": arc_id, "stage": stage, "committed": False,
            "stage_event": stage_event,
        }

    outcome = DT.commit_one_edge(
        repository,
        commitment_id=commitment_id,
        milestone=stage,
        selected_edge_id=edge_id,
        evidence_receipt=evidence_receipt,
        goal_id=goal_id,
        proposed_contract_body=proposed_contract_body,
        fork_edit=fork_edit,
        live_activation_enabled=live_activation_enabled,
        clock=clock,
    )
    committed = bool(getattr(outcome, "committed", False))
    # F5: receipt-key the transition event too, so a replayed decision receipt
    # (same evidence_receipt/decision_id + edge) appends nothing new.
    transition_receipt_key = _canonical_hash({
        "arc_id": arc_id, "stage": stage, "edge_id": edge_id, "kind": "transition",
        "evidence_receipt": dict(evidence_receipt).get("evidence_receipt"),
        "decision_id": dict(evidence_receipt).get("decision_id"),
    })
    repository.append_commitment_arc_event(
        arc_id=arc_id,
        kind="transition_committed" if committed else "transition_requested",
        detail={"stage": stage, "edge_id": edge_id, "outcome": outcome.as_dict()},
        receipt_key=transition_receipt_key,
        clock=clock,
    )
    return {
        "outcome": "transition",
        "arc_id": arc_id,
        "stage": stage,
        "edge_id": edge_id,
        "committed": committed,
        "transition": outcome.as_dict(),
        "stage_event": stage_event,
    }


def pause_arc(
    repository: Repository, *, arc_id: str, reason: str | None = None, clock: Clock | None = None
) -> dict[str, Any]:
    """Pause the arc before the next administration: prevents an uncommitted
    transition and leaves the capture/arc intact (§15.6.1). Also pauses the
    underlying commitment disposition."""

    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    repository.append_commitment_arc_event(
        arc_id=arc_id, kind="arc_paused", detail={"reason": reason}, clock=clock
    )
    C.pause(repository, commitment_id=arc["commitment_id"], clock=clock)
    return {"arc_id": arc_id, "paused": True}


def resume_arc(repository: Repository, *, arc_id: str, clock: Clock | None = None) -> dict[str, Any]:
    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    repository.append_commitment_arc_event(arc_id=arc_id, kind="arc_resumed", clock=clock)
    C.resume(repository, commitment_id=arc["commitment_id"], clock=clock)
    return {"arc_id": arc_id, "paused": False}


def set_depth_policy(
    repository: Repository, *, arc_id: str, policy: str, clock: Clock | None = None
) -> dict[str, Any]:
    """Change the commitment's depth policy and re-pin the arc to the new policy
    version (§10.2). Records ``policy_changed`` + appends a new arc version."""

    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    try:
        new_head = C.change_depth_policy(repository, commitment_id=arc["commitment_id"], policy=policy, clock=clock)
    except C.InvalidTarget as exc:
        raise ArcError(str(exc)) from exc
    _repin(repository, arc_id, new_head, event="policy_changed", detail={"policy": policy}, clock=clock)
    return {"arc_id": arc_id, "policy": policy}


def shrink_envelope(
    repository: Repository,
    *,
    arc_id: str,
    bounds: Mapping[str, Any],
    reviewed_edges: Sequence[Mapping[str, Any]] = (),
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Shrink (reduce) the active envelope before the next administration. Only a
    genuine contraction is allowed: ``change_depth_envelope`` rejects bounds that
    widen authorization on any dimension (``EnvelopeWideningRejected``); widening
    requires a confirmed successor elsewhere. Re-pins the arc (§10.2)."""

    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    new_head = C.change_depth_envelope(
        repository, commitment_id=arc["commitment_id"], bounds=bounds,
        reviewed_edges=reviewed_edges, clock=clock,
    )
    _repin(repository, arc_id, new_head, event="envelope_shrink_requested", detail={"bounds": dict(bounds)}, clock=clock)
    return {"arc_id": arc_id, "shrunk": True}


def _repin(
    repository: Repository, arc_id: str, head: C.CommitmentVersion, *, event: str,
    detail: Mapping[str, Any], clock: Clock | None,
) -> None:
    view = project_arc(repository, arc_id=arc_id)
    reviewed = _reviewed_edges(repository, head.depth_envelope_version_id)
    stage_map = _stage_milestone_map(view["stages"], reviewed)
    body = {
        "schema_version": ARC_SCHEMA_VERSION,
        "stages": view["stages"],
        "pattern_refs": [],
        "depth_policy_version_id": head.depth_policy_version_id,
        "depth_envelope_version_id": head.depth_envelope_version_id,
        "stage_milestone_map": stage_map,
    }
    repository.append_commitment_arc_version(
        arc_id=arc_id,
        version={
            "pattern_refs": [],
            "stages": view["stages"],
            "depth_policy_version_id": head.depth_policy_version_id,
            "depth_envelope_version_id": head.depth_envelope_version_id,
            "stage_milestone_map": stage_map,
            "content_hash": _canonical_hash(body),
        },
        clock=clock,
    )
    repository.append_commitment_arc_event(
        arc_id=arc_id, kind=event if event in _ARC_EVENT_KINDS else "arc_version_appended",
        detail=dict(detail), clock=clock,
    )


_ARC_EVENT_KINDS = frozenset({
    "arc_created", "arc_version_appended", "stage_reached", "transition_requested",
    "transition_committed", "transition_declined", "arc_paused", "arc_resumed",
    "envelope_shrink_requested", "policy_changed", "prime_offered", "prime_answered",
})


def offer_prime(
    repository: Repository, *, arc_id: str, question_ref: str, section: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Offer a learner question from section N as an opt-in prime before section N+1
    (§10.3). Source + annotation remain hidden until response/give-up; the prime is
    salience-only and carries NO cold credit."""

    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    repository.append_commitment_arc_event(
        arc_id=arc_id, kind="prime_offered",
        detail={"question_ref": question_ref, "section": section, "opt_in": True,
                "source_hidden": True}, clock=clock,
    )
    return {"arc_id": arc_id, "question_ref": question_ref, "source_hidden": True,
            "cold_credit": False}


def answer_prime(
    repository: Repository, *, arc_id: str, question_ref: str, gave_up: bool = False,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record a prime answer (§10.3): heavily tempered / no cold credit; it may adjust
    a low-authority prior only, and can never satisfy delayed certification."""

    arc = repository.commitment_arc(arc_id)
    if arc is None:
        raise ArcError(f"unknown arc: {arc_id!r}")
    repository.append_commitment_arc_event(
        arc_id=arc_id, kind="prime_answered",
        detail={"question_ref": question_ref, "gave_up": gave_up, "cold_credit": False,
                "priming": True}, clock=clock,
    )
    return {"arc_id": arc_id, "question_ref": question_ref, "cold_credit": False,
            "satisfies_certification": False}
