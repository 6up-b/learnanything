"""P2 step 2 -- the ONE atomic exemplar confirmation
(spec_p2_narrow_golden_path §3.1, §1.2 invariant 2, §12.1, §12.6; migration 082).

This is the single most important P2 seam. A confirmation composes four LANDED
services -- P0.4 goal-contract v1, the P1 commitment + depth policy/envelope, and the
P0/P1 assessment reservation -- plus the run row, into ONE all-or-nothing boundary:

    activate reviewed blueprint
      -> append goal-contract v1 + head
      -> create commitment (+v1 version/targets/created event)
      -> reserve the fresh held-out assessment surface
      -> mint the golden-path run + run_started event

If ANY internal write fails, the whole transaction rolls back and NOTHING becomes
active (§3.1). The service prepares every content-addressed value up front (reusing the
landed services' pure helpers so the shapes stay byte-identical) and hands the prepared
payloads to ``Repository.confirm_golden_path_atomic``, which drives the single
``BEGIN IMMEDIATE`` transaction. There is no new measurement code here.

Depth policy/envelope version objects are content-addressed and immutable; they are
ensured up front (idempotent) exactly as ``commitments.create_commitment`` does -- an
orphaned shared version object left by a rolled-back confirmation is inert and reused on
retry, so ensuring them outside the run transaction does not make anything "active".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import goal_contracts as GC
from learnloop.services.activities import _canonical_hash, _json


class NotConfirmable(Exception):
    """The proposed contract body is not a confirmable v1 (missing exemplar, reviewed
    blueprint scope, or baseline milestone) -- spec_p2 §3.1 / §1.1 entry gate."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class ConfirmationMismatch(Exception):
    """A re-confirm of an already-confirmed goal differs only in a run-shaping param
    (e.g. ``depth_preset``/``action``) -- the contract identity matches an existing run
    but the run shape does not (C4). Rather than SILENTLY returning the old run (whose
    preset the caller did not ask for), this is raised explicitly so the caller either
    reuses the exact original parameters or starts a distinct run deliberately."""

    def __init__(self, goal_id: str, *, existing_run_id: str, detail: str):
        self.goal_id = goal_id
        self.existing_run_id = existing_run_id
        self.detail = detail
        super().__init__(
            f"goal {goal_id}: re-confirm differs from run {existing_run_id} in a "
            f"run-shaping param ({detail}); it would not return the requested run"
        )


@dataclass(frozen=True)
class RunReceipt:
    """The result of one atomic confirmation (§3.1)."""

    run_id: str
    goal_id: str
    commitment_id: str
    commitment_version_id: str
    goal_contract_version_id: str
    blueprint_version_id: str
    reservation_id: str | None
    reserved_surface_id: str | None
    mode: str
    current_state: str
    minted: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _confirmation_receipt_key(
    *,
    goal_id: str,
    blueprint_version_id: str,
    contract_content_hash: str,
    reserved_surface_id: str | None,
    depth_preset: str,
    action: str,
    source_rev: str,
    unit_id: str,
) -> str:
    """Content identity of the whole confirmation. Makes the boundary idempotent: a
    byte-identical re-confirm returns the existing run, never a second one (§12.6).

    Includes every run-SHAPING param (C4): ``depth_preset``, ``action``, ``source_rev``,
    and ``unit_id`` alongside the contract identity, so a re-confirm differing only in
    (say) the depth preset does NOT collide with the original key and silently return a
    run built with a different preset."""

    return _canonical_hash(
        {
            "goal_id": goal_id,
            "blueprint_version_id": blueprint_version_id,
            "contract_content_hash": contract_content_hash,
            "reserved_surface_id": reserved_surface_id,
            "depth_preset": depth_preset,
            "action": action,
            "source_rev": source_rev,
            "unit_id": unit_id,
        }
    )


def _assert_reviewed_edges_match_blueprint(
    repository: Repository, blueprint_version_id: str, reviewed_edges: Sequence[Mapping[str, Any]]
) -> None:
    """C5: every reviewed edge the contract pins must be a REVIEWED depth_milestone the
    blueprint version declares (matched by ``edge_id`` and reviewed there). Refuse
    otherwise -- a confirmation cannot smuggle an unreviewed/foreign depth edge into the
    immutable envelope."""

    import json as _json_mod

    version = repository.task_blueprint_version(blueprint_version_id)
    if version is None:
        raise NotConfirmable(f"unknown_blueprint_version:{blueprint_version_id}")
    spec = _json_mod.loads(version["spec_json"])
    blueprint_reviewed = {
        str(edge.get("edge_id"))
        for edge in (spec.get("depth_milestones") or [])
        if edge.get("reviewed") and edge.get("edge_id")
    }
    for edge in reviewed_edges:
        if not edge.get("reviewed"):
            continue
        edge_id = str(edge.get("edge_id"))
        if edge_id not in blueprint_reviewed:
            raise NotConfirmable(f"reviewed_edge_not_in_blueprint:{edge_id}")


def _commitment_targets(contract_body: Mapping[str, Any]) -> list[C.CommitmentTarget]:
    targets: list[Mapping[str, Any]] = []
    for exemplar in contract_body.get("exemplars") or []:
        ref = exemplar.get("id") or exemplar.get("exemplar_ref")
        if ref:
            targets.append({"target_kind": "p0_target_exemplar", "target_ref": str(ref), "role": "required"})
    if not targets:
        for concept in (contract_body.get("facet_scope") or {}).get("concepts") or []:
            targets.append({"target_kind": "canonical_facet", "target_ref": str(concept), "role": "required"})
    if not targets:
        raise NotConfirmable("no_commitment_target")
    return C._coerce_targets(targets)


def confirm_exemplar_and_start(
    repository: Repository,
    *,
    goal_id: str,
    blueprint_version_id: str,
    contract_body: Mapping[str, Any],
    depth_preset: str,
    source_rev: str,
    unit_id: str,
    action: str = "select_exemplar",
    assessment_surface_id: str | None = None,
    assessment_support_hash: str | None = None,
    assessment_eligibility: Mapping[str, Any] | None = None,
    intent_text: str | None = None,
    interpretation_text: str | None = None,
    orchestration_policy: Mapping[str, Any] | None = None,
    decision_param_manifest: Mapping[str, Any] | None = None,
    visible_caps: Mapping[str, Any] | None = None,
    author: str = "learner",
    learner_id: str = "local",
    fault_hook: Callable[[str], None] | None = None,
    clock: Clock | None = None,
) -> RunReceipt:
    """Atomically confirm an exemplar interpretation and start a golden-path run.

    Mode (§1.1, A.3.4): ``certifying`` when a fresh assessment surface is supplied and
    reservable; otherwise ``practice_only`` (no terminal claim). The chosen depth
    policy comes from the preset/action defaults and is *served* as ``suggest_next``
    regardless of the stored policy (U-018 deferred, §13).
    """

    if depth_preset not in C.DEPTH_PRESETS:
        raise NotConfirmable(f"unknown_depth_preset:{depth_preset}")
    if action not in C.COMMIT_ACTIONS:
        raise NotConfirmable(f"passive_action_cannot_commit:{action}")

    # --- goal-contract v1 payload (reuse P0.4 pure helpers; same guards as
    # goal_contracts.confirm_goal_contract so v1 shape is identical). ---
    body = GC.canonicalize_body(contract_body)
    exemplars = body.get("exemplars") or []
    scope = body.get("facet_scope") or {}
    has_blueprint = bool(scope.get("concepts") or scope.get("facets") or body.get("required_capabilities"))
    has_baseline = bool(body.get("baseline_milestone"))
    if len(exemplars) < 1:
        raise NotConfirmable("no_exemplar")
    if not (has_blueprint and has_baseline):
        raise NotConfirmable("no_reviewed_blueprint")

    goal_contract = {
        "contract_json": _json(body),
        "content_hash": GC.content_hash(body),
        "support_hash": GC.support_hash(body),
        "contract_schema_version": int(body.get("schema_version", GC.CONTRACT_SCHEMA_VERSION)),
        "head_envelope_version": GC._envelope_version(body),
        "author": author,
    }

    # --- depth policy/envelope (content-addressed, idempotent -- same as
    # commitments.create_commitment). ---
    policy_body = C._default_depth_body(action, depth_preset)
    policy_id = repository.ensure_depth_policy_version(
        policy=policy_body["policy"],
        body_json=_json(policy_body),
        content_hash=_canonical_hash(policy_body),
        clock=clock,
    )
    envelope_body = C._default_envelope_body(depth_preset)
    # B.2 (§3.1): pin the blueprint's REVIEWED depth edges (and any authored bounds)
    # from the reviewed contract into the immutable envelope so the P1 one-edge
    # transition service (depth_transition.commit_one_edge) can later render exactly
    # one reviewed inside-envelope edge as a suggest_next invitation (§7.5). Absent a
    # reviewed depth_envelope the DAG stays empty (the preset default).
    proposed_envelope = body.get("depth_envelope")
    if isinstance(proposed_envelope, Mapping):
        reviewed_edges = proposed_envelope.get("reviewed_edges")
        if reviewed_edges:
            # C5: cross-validate the contract's reviewed edges against the blueprint's
            # reviewed depth_milestones -- every pinned reviewed edge must be a reviewed
            # edge the activated blueprint version actually declares (same edge_id, and
            # reviewed there). A contract that pins an edge the blueprint does not review
            # is refused, so the run can never later render an unreviewed depth edge.
            _assert_reviewed_edges_match_blueprint(repository, blueprint_version_id, reviewed_edges)
            envelope_body["reviewed_edges"] = list(reviewed_edges)
        bounds = proposed_envelope.get("bounds")
        if bounds:
            envelope_body["bounds"] = dict(bounds)
    envelope_id = repository.ensure_depth_envelope_version(
        envelope_version=f"env-{C.DEPTH_ENVELOPE_SCHEMA_VERSION}",
        bounds_json=_json(envelope_body["bounds"]),
        reviewed_edges_json=_json(envelope_body["reviewed_edges"]),
        content_hash=_canonical_hash(envelope_body),
        clock=clock,
    )

    # --- commitment v1 version_fields (mirror commitments.create_commitment). ---
    coerced = _commitment_targets(body)
    ts_hash = C.target_set_hash(coerced)
    version_fields: dict[str, Any] = {
        "intent_text": intent_text or body.get("purpose") or f"tasks like this ({unit_id})",
        "interpretation_text": interpretation_text,
        "goal_id": goal_id,
        "depth_preset": depth_preset,
        "depth_policy_version_id": policy_id,
        "depth_envelope_version_id": envelope_id,
        "attention_bounds_json": None,
        "due_hint": None,
        "hiatus_hint": None,
        "reason": None,
        "provenance_json": _json({"golden_path": True, "blueprint_version_id": blueprint_version_id}),
        "target_set_hash": ts_hash,
    }
    version_fields["version_hash"] = C._version_hash(
        version_fields, coerced, predecessor_version_id=None, version=1
    )

    receipt_key = _confirmation_receipt_key(
        goal_id=goal_id,
        blueprint_version_id=blueprint_version_id,
        contract_content_hash=goal_contract["content_hash"],
        reserved_surface_id=assessment_surface_id,
        depth_preset=depth_preset,
        action=action,
        source_rev=source_rev,
        unit_id=unit_id,
    )

    # C4: a re-confirm whose contract identity matches an existing run for this goal but
    # whose receipt key differs (it differs ONLY in a run-shaping param, e.g. the depth
    # preset) must NOT silently return the old run -- raise an explicit mismatch. A
    # byte-identical re-confirm (same receipt key) still returns the existing run below.
    existing_for_goal = repository.golden_path_run_for_goal(goal_id)
    if existing_for_goal is not None and existing_for_goal["receipt_key"] != receipt_key:
        existing_gcv = repository.fetch_goal_contract_version(existing_for_goal["goal_contract_version_id"])
        if existing_gcv is not None and existing_gcv["content_hash"] == goal_contract["content_hash"]:
            raise ConfirmationMismatch(
                goal_id,
                existing_run_id=existing_for_goal["id"],
                detail="depth_preset or other run-shaping param differs from the confirmed run",
            )

    reservation_payload: dict[str, Any] | None = None
    mode = "practice_only"
    if assessment_surface_id is not None:
        mode = "certifying"
        reservation_payload = {
            "surface_id": assessment_surface_id,
            "purpose": "assessment",
            "target_support_hash": assessment_support_hash or goal_contract["support_hash"],
            "eligibility_json": _json(dict(assessment_eligibility) if assessment_eligibility else {}),
        }

    result = repository.confirm_golden_path_atomic(
        receipt_key=receipt_key,
        blueprint_version_id=blueprint_version_id,
        goal_id=goal_id,
        goal_contract=goal_contract,
        commitment={
            "learner_id": learner_id,
            "created_action": action,
            "idempotency_key": receipt_key,
            "version_fields": version_fields,
            "targets": [C._target_row(t) for t in coerced],
            "author": author,
        },
        run={
            "learner_id": learner_id,
            "source_rev": source_rev,
            "unit_id": unit_id,
            "initial_milestone": str(body.get("baseline_milestone")),
            "mode": mode,
            "orchestration_policy_json": _json(dict(orchestration_policy)) if orchestration_policy else None,
            "decision_param_manifest_json": _json(dict(decision_param_manifest)) if decision_param_manifest else None,
            "visible_caps_json": _json(dict(visible_caps)) if visible_caps else None,
        },
        reservation=reservation_payload,
        fault_hook=fault_hook,
        clock=clock,
    )

    run_row = result["run"]
    if result["already_exists"]:
        return _receipt_from_existing(repository, run_row, minted=False)
    return RunReceipt(
        run_id=run_row["id"],
        goal_id=goal_id,
        commitment_id=result["commitment_id"],
        commitment_version_id=result["commitment_version_id"],
        goal_contract_version_id=result["goal_contract_version_id"],
        blueprint_version_id=blueprint_version_id,
        reservation_id=result["reservation_id"],
        reserved_surface_id=run_row["reserved_surface_id"],
        mode=run_row["mode"],
        current_state=run_row["current_state"],
        minted=True,
    )


def _receipt_from_existing(repository: Repository, run_row: Mapping[str, Any], *, minted: bool) -> RunReceipt:
    return RunReceipt(
        run_id=run_row["id"],
        goal_id=run_row["goal_id"],
        commitment_id=run_row["commitment_id"],
        commitment_version_id=run_row["commitment_version_id"],
        goal_contract_version_id=run_row["goal_contract_version_id"],
        blueprint_version_id=run_row["blueprint_version_id"],
        reservation_id=run_row["reserved_reservation_id"],
        reserved_surface_id=run_row["reserved_surface_id"],
        mode=run_row["mode"],
        current_state=run_row["current_state"],
        minted=minted,
    )
