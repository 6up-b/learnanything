"""P1 step 8 -- the deterministic one-edge depth-transition service
(spec_p1_shared_substrate §5.7, §3.1.1, §10; invariant 12).

P1 exposes the substrate; P2/P4 decide WHEN to call it, and live activation authority
ships only with the auto-depth package (U-018). The service is fully exercised under
acceptance tests, but until U-018 ships a confirmed ``auto_within_envelope`` policy
STORES learner intent and behaves as ``suggest_next`` in the live product. That is the
single structural gate :data:`LIVE_ACTIVATION_ENABLED` (default OFF); the acceptance
harness passes ``live_activation_enabled=True`` to exercise the full transition.

:func:`commit_one_edge` is deterministic and fail-closed. It reuses P0.4's
``goal_contracts.append_authorized_depth_successor`` for the terminal-support side and
P1 commitments for the commitment side (A.3: milestone/transition events append only an
event, no version bump). At most ONE reviewed inside-envelope edge is committed per
decision and it replans; failure is non-destructive (no eligible successor ->
maintain/stop/suggest; it never mutates the predecessor, fabricates a fresh surface, or
walks a second edge).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import card_lineage as CL
from learnloop.services import commitments as C
from learnloop.services import goal_contracts as GC
from learnloop.services.activities import _canonical_hash, _json

# U-018 structural gate. OFF in the live product: a confirmed auto_within_envelope
# policy records intent but activates nothing (behaves as suggest_next). The auto-depth
# package flips this. NOT a tunable knob -- registered structural.
LIVE_ACTIVATION_ENABLED = False


@dataclass(frozen=True)
class TransitionProposal:
    """A non-activating outcome: the transition was refused, deferred to suggest_next,
    or requires authoring. Never mutates anything (§5.7 / §7.5)."""

    kind: str  # suggest_next | authoring_needed | refused
    reason: str
    commitment_id: str
    selected_edge_id: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    @property
    def committed(self) -> bool:
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": "proposal",
            "kind": self.kind,
            "reason": self.reason,
            "commitment_id": self.commitment_id,
            "selected_edge_id": self.selected_edge_id,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True)
class TransitionReceipt:
    """A committed one-edge transition (§5.7 step 7)."""

    commitment_id: str
    selected_edge_id: str
    milestone_slug: str
    goal_contract_version_id: str | None
    forked_lineage_id: str | None
    forked_state_id: str | None
    activated: bool
    events: tuple[str, ...]

    @property
    def committed(self) -> bool:
        return True

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": "receipt",
            "commitment_id": self.commitment_id,
            "selected_edge_id": self.selected_edge_id,
            "milestone_slug": self.milestone_slug,
            "goal_contract_version_id": self.goal_contract_version_id,
            "forked_lineage_id": self.forked_lineage_id,
            "forked_state_id": self.forked_state_id,
            "activated": self.activated,
            "events": list(self.events),
        }


def _resolve_policy(repository: Repository, policy_version_id: str | None) -> str | None:
    if not policy_version_id:
        return None
    row = repository.depth_policy_version(policy_version_id)
    if row is None:
        return None
    return row["policy"]


def _reviewed_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]:
    if not envelope_version_id:
        return []
    row = repository.depth_envelope_version(envelope_version_id)
    if row is None:
        return []
    import json as _json_mod

    return _json_mod.loads(row["reviewed_edges_json"] or "[]")


def commit_one_edge(
    repository: Repository,
    *,
    commitment_id: str,
    milestone: str,
    selected_edge_id: str,
    evidence_receipt: Mapping[str, Any],
    goal_id: str | None = None,
    proposed_contract_body: Mapping[str, Any] | None = None,
    progression_decision: Mapping[str, Any] | None = None,
    fork_edit: Mapping[str, Any] | None = None,
    scheduler_algorithm_version: str = "fsrs6",
    live_activation_enabled: bool | None = None,
    author: str = "controller",
    clock: Clock | None = None,
) -> TransitionReceipt | TransitionProposal:
    """Commit at most one reviewed inside-envelope depth edge (§5.7). Returns a
    :class:`TransitionReceipt` on success or a non-destructive :class:`TransitionProposal`.

    ``fork_edit`` (optional) is ``{"prev_contract":..., "new_contract":...,
    "predecessor_card_version_id":..., "forked_card_version_id":...}``: when the edge
    changes capability/task regime the lineage classifier forks and starts NEW
    scheduling state, borrowing only an explicitly shrunk family-stage difficulty prior
    -- never inheriting stability or certification (§3.7, invariant 12).
    """

    # U-018 belt-and-suspenders (B4): live activation requires BOTH the module gate
    # constant AND (when supplied) the caller argument. The `live_activation_enabled`
    # argument ALONE can never activate while LIVE_ACTIVATION_ENABLED is False -- the
    # acceptance harness must patch the constant explicitly to exercise activation.
    resolved = LIVE_ACTIVATION_ENABLED if live_activation_enabled is None else live_activation_enabled
    live = bool(resolved) and LIVE_ACTIVATION_ENABLED

    head = C.resolve_head(repository, commitment_id)

    # Step 2 (part): policy must be auto_within_envelope. hold_at_target / suggest_next
    # cannot auto-activate (§3.1.1, §9.1).
    policy = _resolve_policy(repository, head.depth_policy_version_id)
    if policy != "auto_within_envelope":
        return TransitionProposal(
            kind="suggest_next" if policy == "suggest_next" else "refused",
            reason=f"policy_not_auto_within_envelope:{policy}",
            commitment_id=commitment_id,
            selected_edge_id=selected_edge_id,
        )

    # Step 1: resolve the single reviewed outgoing edge the caller selected.
    edges = _reviewed_edges(repository, head.depth_envelope_version_id)
    matches = [e for e in edges if e.get("edge_id") == selected_edge_id and e.get("reviewed")]
    if len(matches) == 0:
        return TransitionProposal(
            kind="refused", reason="no_reviewed_edge", commitment_id=commitment_id,
            selected_edge_id=selected_edge_id,
        )
    if len(matches) >= 2:
        return TransitionProposal(
            kind="refused", reason="ambiguous_edge", commitment_id=commitment_id,
            selected_edge_id=selected_edge_id,
        )
    edge = matches[0]

    # Step 2 (part): every successor dimension lies inside the active envelope. An edge
    # explicitly flagged outside-envelope, or a cross-target-family edge, stays a proposal.
    if edge.get("outside_envelope") or edge.get("cross_target_family"):
        return TransitionProposal(
            kind="authoring_needed", reason="edge_outside_envelope",
            commitment_id=commitment_id, selected_edge_id=selected_edge_id,
        )

    # Step 3: predecessor exit gate + fresh-proof.
    receipt = dict(evidence_receipt or {})
    if not receipt.get("qualifies") or not receipt.get("evidence_receipt"):
        return TransitionProposal(
            kind="refused", reason="insufficient_evidence", commitment_id=commitment_id,
            selected_edge_id=selected_edge_id,
        )

    # Step 5 (production gate): while U-018 is deferred, store intent and behave as
    # suggest_next -- activate NOTHING automatically (§3.1.1, §10). All checks above
    # still ran, so the learner sees a validated next edge.
    if not live:
        return TransitionProposal(
            kind="suggest_next", reason="auto_activation_deferred_u018",
            commitment_id=commitment_id, selected_edge_id=selected_edge_id,
            detail={"milestone": milestone, "intent_stored": True},
        )

    # --- Live activation (acceptance harness / U-018) ---

    # Step 4: ask P0.4 to append an authorized_depth_step when terminal support changes.
    goal_contract_version_id: str | None = None
    if goal_id is not None and proposed_contract_body is not None:
        result = GC.append_authorized_depth_successor(
            repository, goal_id=goal_id, proposed_body=proposed_contract_body,
            progression_decision=progression_decision or receipt, author=author, clock=clock,
        )
        if isinstance(result, GC.Draft):
            # Non-destructive: P0.4 refused the terminal-support edge -> proposal.
            return TransitionProposal(
                kind="authoring_needed", reason=f"terminal_support_rejected:{result.rejection_reason}",
                commitment_id=commitment_id, selected_edge_id=selected_edge_id,
                detail={"draft_id": result.id},
            )
        goal_contract_version_id = result.id

    # Step 6: apply the lineage classifier -- every fork starts NEW scheduling state,
    # borrowing only an explicitly shrunk family-stage difficulty prior. The fork
    # rows are written in the SAME transaction as the step-7 events (B4 atomicity);
    # ids are minted here so the transition detail can name them upfront.
    forked_lineage_id: str | None = None
    forked_state_id: str | None = None
    fork_spec: dict[str, Any] | None = None
    if fork_edit is not None:
        classification = CL.classify_edit(
            fork_edit.get("prev_contract", {}), fork_edit.get("new_contract", {})
        )
        # B3: an edit the classifier cannot prove either cosmetic or semantic is parked
        # for authoring -- it must NEVER fall through to a state-preserving commit, and
        # any unexpected verdict fails closed (§3.7, §9.2).
        if classification.verdict == "review_required":
            return TransitionProposal(
                kind="authoring_needed", reason="edit_requires_review",
                commitment_id=commitment_id, selected_edge_id=selected_edge_id,
                detail={"changed_unknown": list(classification.changed_unknown)},
            )
        if classification.verdict not in ("surface_preserving", "fork_required"):
            return TransitionProposal(
                kind="authoring_needed",
                reason=f"unexpected_edit_verdict:{classification.verdict}",
                commitment_id=commitment_id, selected_edge_id=selected_edge_id,
            )
        if classification.verdict == "fork_required":
            forked_lineage_id = new_ulid()
            forked_state_id = new_ulid()
            fork_spec = {
                "lineage_id": forked_lineage_id,
                "state_id": forked_state_id,
                "predecessor_card_version_id": fork_edit["predecessor_card_version_id"],
                "forked_card_version_id": fork_edit["forked_card_version_id"],
                "scheduler_algorithm_version": scheduler_algorithm_version,
                "family_id": fork_edit.get("family_id"),
                "card_id": fork_edit.get("card_id"),
                "model_label": "fsrs",
                "learner_id": "local",
                "informed_difficulty_prior": fork_edit.get("shrunk_family_stage_prior"),
                "classifier_version": CL.LINEAGE_CLASSIFIER_VERSION,
                "rationale": {"reason": "authorized_depth_fork", "edge_id": selected_edge_id},
            }

    # Step 7 (atomic with step 6, idempotent on the decision receipt): append the
    # milestone + transition events (A.3: event only) and the fork rows in ONE
    # transaction. A retry replaying the same receipt is a no-op (no double-commit).
    receipt_key = _canonical_hash({
        "commitment_id": commitment_id,
        "selected_edge_id": selected_edge_id,
        "milestone": milestone,
        "evidence_receipt": receipt.get("evidence_receipt"),
        "decision_id": receipt.get("decision_id"),
    })
    milestone_detail = {"milestone_slug": milestone, "edge_id": selected_edge_id}
    transition_detail = {
        "edge_id": selected_edge_id,
        "milestone": milestone,
        "goal_contract_version_id": goal_contract_version_id,
        "forked_lineage_id": forked_lineage_id,
        "forked_state_id": forked_state_id,
        "receipt_key": receipt_key,
    }
    outcome = repository.record_depth_transition_atomic(
        commitment_id=commitment_id,
        milestone_slug=milestone,
        milestone_detail_json=_json(milestone_detail),
        transition_detail_json=_json(transition_detail),
        receipt_key=receipt_key,
        fork_spec=fork_spec,
        clock=clock,
    )
    if outcome.get("already"):
        # Idempotent replay of a prior committed decision: reflect the stored fork.
        forked_lineage_id = outcome.get("forked_lineage_id")
        forked_state_id = outcome.get("forked_state_id")
    transition_event_id = outcome["transition_event_id"]

    return TransitionReceipt(
        commitment_id=commitment_id,
        selected_edge_id=selected_edge_id,
        milestone_slug=milestone,
        goal_contract_version_id=goal_contract_version_id,
        forked_lineage_id=forked_lineage_id,
        forked_state_id=forked_state_id,
        activated=True,
        events=("depth_milestone_reached", transition_event_id),
    )
