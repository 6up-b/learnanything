"""Learner-initiated re-runging: easier/harder sibling variants of one item.

From any practice item the learner requests a variant one waypoint down/up the
depth trajectory. Two halves, deliberately split:

1. ``request_rung_variant`` — synchronous, deterministic, fail-closed. Resolves
   the source item's waypoint, steps the trajectory (clamped; deeper than
   ``select_method`` only through a commitment's reviewed depth envelope),
   inserts the durable request row (the per-item lock), and writes the
   EVIDENCE PACKAGE: the request itself is information about the learner —
   a scoped learner claim (cold-state prior) plus a deterministic self-graded
   ``self_report`` attempt on the SOURCE item (0.3 evidence mass; moves LO
   mastery, facet recall, the (facet, capability) ledger, and — owner-approved
   — the source's FSRS state: easier = declared soft failure, harder =
   success). The evidence is NEVER rolled back if generation later fails: the
   request was real evidence regardless of what the authoring model does.

2. ``generate_rung_variant`` — the async job body. Authors ONE grounded
   sibling item at the target waypoint through the rung-gated generation path.
   Measurement targets are independently recompiled; only the shared
   ``evidence_fingerprint.source_family`` is stamped so kinship discounting
   treats sibling evidence as correlated. The source item is never mutated.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.canonical_projection import surface_group_id
from learnloop.services.capability_mapping import default_capability_for
from learnloop.services.depth_rungs import (
    RungTarget,
    adjacent_slug,
    rung_float_proxies,
    select_rung,
    trajectory_slugs,
    waypoint_rung,
)
from learnloop.services.mastery import display_mastery, reanchor_mastery_from_claim
from learnloop.vault.models import LoadedVault, PracticeItem


class RungVariantError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


DIRECTIONS = ("easier", "harder")

CLAIM_SOURCE = "rung_variant_request"

# Items whose stamped capability has no default-trajectory waypoint (e.g.
# coordination/whole_task) sit BEYOND the trajectory: easier steps down to the
# deepest default waypoint; harder requires a reviewed depth envelope.
BEYOND_TRAJECTORY = "beyond_default_trajectory"

_ORDERED_TASK_AXES: dict[str, dict[Any, int]] = {
    "span": {
        "atomic": 0,
        "single_step": 1,
        "multi_step": 2,
        "whole_task": 3,
    },
    "response": {
        "recognize": 0,
        "short_constructed": 1,
        "long_constructed": 2,
        "structured_steps": 3,
        "performance": 4,
    },
    "transfer": {
        "same_context": 0,
        "near": 1,
        "far": 2,
        "novel_combination": 3,
    },
    # More scaffolding makes an otherwise identical item easier.
    "scaffolding": {"worked": 0, "partial": 1, "cue": 2, "none": 3},
}


def audit_variant_direction(
    source_item: PracticeItem,
    payload: dict[str, Any],
    direction: str,
) -> list[str]:
    """Direction-symmetric structural audit for sibling variants."""

    if direction not in DIRECTIONS:
        return []
    violations: list[str] = []
    source_difficulty = source_item.difficulty
    target_difficulty = payload.get("difficulty")
    if source_difficulty is not None and target_difficulty is not None:
        target_value = float(target_difficulty)
        if direction == "harder" and target_value <= float(source_difficulty):
            violations.append(
                f"variant_direction:difficulty:{target_value:g} must exceed {float(source_difficulty):g}"
            )
        if direction == "easier" and target_value >= float(source_difficulty):
            violations.append(
                f"variant_direction:difficulty:{target_value:g} must be below {float(source_difficulty):g}"
            )

    source_features = source_item.task_features or {}
    target_features = payload.get("task_features") or {}
    contract = payload.get("variant_contract")
    contract = contract if isinstance(contract, dict) else {}
    incidental = set(str(value) for value in contract.get("incidental_changes") or [])
    declarations = {
        str(entry.get("axis")): str(entry.get("direction") or "")
        for entry in contract.get("intended_manipulations") or []
        if isinstance(entry, dict) and entry.get("axis")
    }
    declared_axes = set(declarations)
    held_constant = set(str(value) for value in contract.get("held_constant") or [])
    changed_axes: set[str] = set()
    if (
        source_difficulty is not None
        and target_difficulty is not None
        and float(source_difficulty) != float(target_difficulty)
    ):
        changed_axes.add("difficulty")
        actual = (
            "increase"
            if float(target_difficulty) > float(source_difficulty)
            else "decrease"
        )
        declared = declarations.get("difficulty")
        if declared and declared != actual:
            violations.append(
                f"variant_contract:false_direction:difficulty:{declared}!={actual}"
            )
        if "difficulty" in held_constant:
            violations.append("variant_contract:held_constant_changed:difficulty")
        if "difficulty" not in declared_axes and "difficulty" not in incidental:
            violations.append("variant_contract:undeclared_axis_change:difficulty")
    for axis in ("complexity", *_ORDERED_TASK_AXES):
        before = source_features.get(axis)
        after = target_features.get(axis)
        if before is None or after is None or before == after:
            continue
        if axis == "complexity":
            delta = (float(after) > float(before)) - (float(after) < float(before))
        else:
            order = _ORDERED_TASK_AXES[axis]
            if before not in order or after not in order:
                continue
            delta = (order[after] > order[before]) - (order[after] < order[before])
        changed_axes.add(axis)
        actual = "increase" if delta > 0 else "decrease"
        declared = declarations.get(axis)
        if declared and declared != actual:
            violations.append(
                f"variant_contract:false_direction:{axis}:{declared}!={actual}"
            )
        if axis in held_constant:
            violations.append(f"variant_contract:held_constant_changed:{axis}")
        against = (direction == "harder" and delta < 0) or (
            direction == "easier" and delta > 0
        )
        if against:
            if axis in incidental:
                violations.append(
                    f"variant_direction:declared_trade:{axis}:{before!s}->{after!s}"
                )
            else:
                violations.append(
                    f"variant_direction:{axis}:{before!s}->{after!s} moves against {direction}"
                )
        if axis not in declared_axes and axis not in incidental:
            violations.append(f"variant_contract:undeclared_axis_change:{axis}")
    for axis, declared in declarations.items():
        if declared in {"increase", "decrease"} and axis not in changed_axes:
            violations.append(
                f"variant_contract:declared_axis_unchanged:{axis}:{declared}"
            )

    source_trace = source_item.trace_contract
    target_trace = payload.get("trace_contract")
    if source_trace is not None and source_trace.status == "available":
        if not isinstance(target_trace, dict):
            violations.append("variant_contract:missing_trace_comparison")
            return violations
        source_checkpoints = {
            checkpoint
            for recipe in source_trace.recipes
            for checkpoint in recipe.checkpoints
        }
        target_checkpoints = (
            {
                str(checkpoint)
                for recipe in target_trace.get("recipes") or []
                if isinstance(recipe, dict)
                for checkpoint in recipe.get("checkpoints") or []
            }
            if target_trace.get("status", "available") == "available"
            else set()
        )
        dropped = source_checkpoints - target_checkpoints
        added = target_checkpoints - source_checkpoints
        declared_drops = set(str(value) for value in contract.get("drops_checkpoints") or [])
        declared_preserved = set(
            str(value) for value in contract.get("preserves_checkpoints") or []
        )
        declared_deepened = set(
            str(value) for value in contract.get("deepens_checkpoints") or []
        )
        for checkpoint in sorted(dropped - declared_drops):
            violations.append(f"variant_contract:undeclared_checkpoint_drop:{checkpoint}")
        for checkpoint in sorted(added - declared_deepened):
            violations.append(f"variant_contract:undeclared_checkpoint_add:{checkpoint}")
        for checkpoint in sorted(declared_preserved - target_checkpoints):
            violations.append(f"variant_contract:false_checkpoint_preservation:{checkpoint}")
        if direction == "harder":
            for checkpoint in sorted(dropped & declared_drops):
                violations.append(
                    f"variant_direction:declared_trade:dropped_checkpoint:{checkpoint}"
                )
        if direction == "easier":
            for checkpoint in sorted(added & declared_deepened):
                violations.append(
                    f"variant_direction:declared_trade:added_checkpoint:{checkpoint}"
                )
    return violations


def audit_variant_manipulation_contract(
    repository: Repository,
    source_item: PracticeItem,
    candidate_payload: dict[str, Any],
    *,
    adversarial_review: dict[str, Any] | None,
    generation_agent_run_id: str | None = None,
    reviewer_agent_run_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """P2 shared diff audit for harder/easier/rung-shift siblings.

    Direction-specific deterministic checks remain above; undeclared semantic
    differences are reviewed by the same independent mechanism used for causal
    probes, rather than a second variant-only implementation.
    """

    from learnloop.services.causal_probe_coherence import (
        audit_manipulation_contract,
    )

    return audit_manipulation_contract(
        repository,
        source_item=source_item,
        candidate_item=candidate_payload,
        source_kind="rung_variant",
        adversarial_review=adversarial_review,
        generation_agent_run_id=generation_agent_run_id,
        reviewer_agent_run_id=reviewer_agent_run_id,
        clock=clock,
    )


def _variant_kind(source_item: PracticeItem, rung: RungTarget, direction: str) -> str:
    """A rung whose demanded point moves against direction is a trajectory shift."""

    probe_payload = {
        "difficulty": source_item.difficulty,
        "task_features": rung.task_features,
        "variant_contract": {
            "intended_manipulations": [
                {"axis": axis, "direction": "hold"}
                for axis in (source_item.task_features or {})
            ],
            "incidental_changes": [],
        },
    }
    violations = audit_variant_direction(source_item, probe_payload, direction)
    if any("moves against" in violation for violation in violations):
        return "rung_shift"
    return direction


# ---------------------------------------------------------------------------
# Waypoint resolution
# ---------------------------------------------------------------------------


def resolve_item_waypoint(vault: LoadedVault, repository: Repository, item: PracticeItem) -> str:
    """The default-trajectory waypoint this item most plausibly sits at.

    Preference order: (1) the item's own rung metadata (capability +
    task_features, stamped by rung-targeted generation); (2) inference from the
    practice mode's default capability + the legacy float proxies; (3) the
    LO-state-keyed ``select_rung`` waypoint.
    """

    slugs = trajectory_slugs()

    if item.capability and isinstance(item.task_features, dict) and item.task_features:
        trajectory_capabilities = {waypoint_rung(repository, slug).capability for slug in slugs}
        if item.capability not in trajectory_capabilities:
            # e.g. coordination/whole_task — deeper than every default waypoint.
            return BEYOND_TRAJECTORY
        best_slug, best_score = None, -1
        for slug in slugs:
            rung = waypoint_rung(repository, slug)
            if rung.capability != item.capability:
                continue
            score = sum(
                1 for dim, value in rung.task_features.items() if item.task_features.get(dim) == value
            )
            if score > best_score:
                best_slug, best_score = slug, score
        if best_slug is not None:
            return best_slug

    mode_capability = default_capability_for(item.practice_mode)
    candidates = [slug for slug in slugs if waypoint_rung(repository, slug).capability == mode_capability]
    if candidates:
        if len(candidates) == 1:
            return candidates[0]
        # Same capability at multiple waypoints (retrieval): use the float
        # proxies to pick the band the item actually declares.
        best_slug, best_score = candidates[0], -1
        for slug in candidates:
            proxies = rung_float_proxies(waypoint_rung(repository, slug))
            score = 0
            for proxy, (low, high) in proxies.items():
                declared = getattr(item, proxy, None)
                if declared is not None and low <= float(declared) <= high:
                    score += 1
            if score > best_score:
                best_slug, best_score = slug, score
        return best_slug

    mastery = repository.mastery_state(item.learning_object_id)
    mastery_mean = display_mastery(mastery).mastery_mean if mastery is not None else None
    return select_rung(
        vault,
        repository,
        learning_object_id=item.learning_object_id,
        mastery_mean=mastery_mean,
        evidence_count=(mastery.evidence_count if mastery is not None else 0),
    ).waypoint_slug


# ---------------------------------------------------------------------------
# Request (sync: lock + evidence package)
# ---------------------------------------------------------------------------


def request_rung_variant(
    vault: LoadedVault,
    repository: Repository,
    *,
    practice_item_id: str,
    direction: str,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record a re-rung request and write its evidence package. Returns a
    summary dict with the request id and target waypoint; the caller enqueues
    the generation job. Evidence is intentionally not rolled back on any later
    generation failure — the request itself was real evidence."""

    if direction not in DIRECTIONS:
        raise RungVariantError("invalid_direction", f"direction must be one of {DIRECTIONS}")
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        raise RungVariantError("item_not_found", f"Unknown practice item {practice_item_id!r}.")
    if item.status != "active":
        raise RungVariantError("item_not_active", f"Practice item {practice_item_id} is {item.status}.")

    config = vault.config.rung_variants
    # Reconcile stale requests first: a job that crashed / was cancelled before
    # the service updated the row would otherwise wedge the per-item lock and
    # the scheduler's pending-variant hold forever.
    live_pending = []
    for row in repository.pending_rung_variant_requests(practice_item_id):
        if repository.rung_variant_batch_dead(row.get("batch_id")):
            repository.update_rung_variant_request(
                row["id"], status="failed",
                failure_reason="generation job died before completing", clock=clock,
            )
            continue
        live_pending.append(row)
    if len(live_pending) >= config.max_pending_per_item:
        raise RungVariantError(
            "variant_pending",
            "A variant for this item is already being authored — try again once it lands.",
        )

    source_slug = resolve_item_waypoint(vault, repository, item)
    target_rung = _target_rung(vault, repository, item, source_slug, direction)
    variant_kind = _variant_kind(item, target_rung, direction)

    request_id = repository.insert_rung_variant_request(
        {
            "source_practice_item_id": item.id,
            "learning_object_id": item.learning_object_id,
            "direction": direction,
            "source_waypoint_slug": source_slug,
            "target_waypoint_slug": target_rung.waypoint_slug,
            "target_rung_json": json.dumps(target_rung.as_dict(), sort_keys=True),
            "variant_kind": variant_kind,
            "status": "pending",
        },
        clock=clock,
    )

    # Claim FIRST so a cold LO's initial mastery (materialized at attempt time)
    # seeds from it (mastery.initial_mastery_state_for_learning_object).
    claim_level = config.easier_claim_level if direction == "easier" else config.harder_claim_level
    repository.delete_learner_claims(
        source=CLAIM_SOURCE, scope_type="learning_object", scope_id=item.learning_object_id
    )
    claim_id = repository.insert_learner_claim(
        {
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": item.learning_object_id,
            "evidence_family": default_capability_for(item.practice_mode),
            "claimed_level": claim_level,
            "prior_pseudo_count": config.claim_pseudo_count,
            "source": CLAIM_SOURCE,
        },
        clock=clock,
    )
    # Re-anchor immediately: for a warm LO the claim was previously inert
    # (covering_learner_claim only feeds first materialization), which meant a
    # learner asking for harder work changed nothing the scheduler or the
    # generation rung selector could see.
    reanchor_mastery_from_claim(
        vault,
        repository,
        item.learning_object_id,
        claimed_level=claim_level,
        prior_pseudo_count=config.claim_pseudo_count,
        now_iso=utc_now_iso(clock),
    )

    # The belief write: a deterministic self-graded self_report attempt on the
    # SOURCE item (evidence mass 0.3 via EvidenceConfig). Non-blank answer text
    # avoids the blank_answer manual-review flag.
    fraction = config.easier_score_fraction if direction == "easier" else config.harder_score_fraction
    from learnloop.services.grading import resolved_rubric

    rubric = resolved_rubric(vault, item)
    draft = AttemptDraft(
        practice_item_id=item.id,
        learner_answer_md=(
            f"[re-rung request] asked for an {direction} variant "
            f"({source_slug} → {target_rung.waypoint_slug})"
        ),
        attempt_type="self_report",
        session_id=session_id,
    )
    grade = SelfGradeInput(
        criterion_points={
            criterion.id: round(criterion.points * fraction, 4) for criterion in rubric.criteria
        },
        confidence=config.self_grade_confidence,
        notes=f"Learner requested an {direction} variant of this item.",
    )
    attempt = complete_self_graded_attempt(vault, repository, draft, grade, clock=clock)

    try:
        repository.append_interaction_event(
            kind="rung_variant_requested",
            origin="learner",
            subject_type="practice_item",
            subject_id=item.id,
            attempt_id=attempt.attempt_id,
            payload_json=json.dumps(
                {
                    "request_id": request_id,
                    "direction": direction,
                    "source_waypoint": source_slug,
                    "target_waypoint": target_rung.waypoint_slug,
                }
            ),
            occurred_at=utc_now_iso(clock),
            session_id=session_id,
        )
    except Exception:
        pass  # telemetry is best-effort, never blocks the request

    repository.update_rung_variant_request(
        request_id, attempt_id=attempt.attempt_id, learner_claim_id=claim_id, clock=clock
    )
    return {
        "request_id": request_id,
        "direction": direction,
        "variant_kind": variant_kind,
        "source_waypoint": source_slug,
        "target_waypoint": target_rung.waypoint_slug,
        "attempt_id": attempt.attempt_id,
        "learning_object_id": item.learning_object_id,
    }


def _target_rung(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    source_slug: str,
    direction: str,
) -> RungTarget:
    if source_slug == BEYOND_TRAJECTORY:
        # Beyond-trajectory item (e.g. coordination/whole_task): easier steps
        # down onto the trajectory's deepest waypoint; harder needs an envelope
        # (fall through to the commitment path below via target_slug=None).
        if direction == "easier":
            return waypoint_rung(repository, trajectory_slugs()[-1])
        target_slug = None
    else:
        target_slug = adjacent_slug(source_slug, direction)
    if target_slug is not None:
        return waypoint_rung(repository, target_slug)
    if direction == "easier":
        raise RungVariantError(
            "at_easiest_waypoint",
            f"This item already sits at the easiest waypoint ({trajectory_slugs()[0]}).",
        )
    # Harder past select_method: only a commitment's reviewed depth envelope
    # authorizes deeper work (spec v2: depth is a learner-authorized program).
    mastery = repository.mastery_state(item.learning_object_id)
    mastery_mean = display_mastery(mastery).mastery_mean if mastery is not None else None
    for commitment_id in (
        *repository.commitments_targeting(item.learning_object_id),
        *repository.commitments_targeting(item.id),
    ):
        rung = select_rung(
            vault,
            repository,
            learning_object_id=item.learning_object_id,
            mastery_mean=mastery_mean,
            evidence_count=(mastery.evidence_count if mastery is not None else 0),
            commitment_id=commitment_id,
        )
        if rung.source == "milestone_edge":
            return rung
    raise RungVariantError(
        "envelope_required",
        "This is the deepest default waypoint — deeper work needs a reviewed depth envelope "
        "on a commitment covering this material.",
    )


# ---------------------------------------------------------------------------
# Generation (job body)
# ---------------------------------------------------------------------------


def generate_rung_variant(
    root,
    client: Any,
    *,
    request_id: str,
    repository: Repository | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author the requested variant: one grounded sibling item at the target
    waypoint, rung-gated, with deterministic facet/fingerprint/capability
    stamping. Updates the request row to applied / review_required / failed."""

    from learnloop.services.practice_generation import (
        PracticeExpansionError,
        PracticeExpansionPlan,
        _RungGate,
        build_practice_expansion_plan,
    )
    from learnloop.services.proposals import generate_authoring_proposal
    from learnloop.services.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    vault = load_vault(root)
    if repository is None:
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    request = repository.rung_variant_request(request_id)
    if request is None:
        raise RungVariantError("request_not_found", f"Unknown rung variant request {request_id!r}.")
    if request["status"] not in ("pending", "generating"):
        return {"request_id": request_id, "status": request["status"], "deduplicated": True}
    source_item = vault.practice_items.get(request["source_practice_item_id"])
    if source_item is None:
        repository.update_rung_variant_request(
            request_id, status="failed", failure_reason="source item disappeared", clock=clock
        )
        return {"request_id": request_id, "status": "failed"}

    repository.update_rung_variant_request(request_id, status="generating", clock=clock)
    sync_vault_state(vault, repository)

    target_rung = _rebuild_rung(repository, request)
    lo_id = request["learning_object_id"]
    try:
        plan = build_practice_expansion_plan(
            vault,
            repository,
            learning_object_ids=[lo_id],
            require_completed_probe=False,
            target_items_per_lo=1,
            max_new_per_lo=1,
        )
    except PracticeExpansionError as exc:
        repository.update_rung_variant_request(
            request_id, status="failed", failure_reason=str(exc), clock=clock
        )
        return {"request_id": request_id, "status": "failed"}
    targets = [
        dataclasses.replace(target, rung=target_rung, requested_new_items=1)
        for target in plan.targets
        if target.learning_object_id == lo_id
    ]
    if not targets:
        repository.update_rung_variant_request(
            request_id, status="failed", failure_reason="no generation target for the learning object",
            clock=clock,
        )
        return {"request_id": request_id, "status": "failed"}
    plan = PracticeExpansionPlan(targets=targets)

    def _stamp_variant(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            if row.get("item_type") != "practice_item" or row.get("operation") != "create":
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            # Shared surface group: kinship discounting treats the variant's
            # evidence as correlated with the source's, never independent.
            fingerprint = payload.get("evidence_fingerprint")
            if not isinstance(fingerprint, dict):
                fingerprint = {}
            fingerprint["source_family"] = surface_group_id(source_item)
            payload["evidence_fingerprint"] = fingerprint
            payload["tags"] = sorted(set(payload.get("tags") or []) | {"rung_variant"})

    def _run(extra: str | None) -> tuple[str, "_RungGate"]:
        rung_gate = _RungGate(repository, plan)

        def _composed(rows: list[dict[str, Any]]) -> None:
            rung_gate(rows)
            _stamp_variant(rows)
            for row in rows:
                payload = row.get("payload")
                if row.get("item_type") != "practice_item" or not isinstance(payload, dict):
                    continue
                contract = payload.get("variant_contract")
                if not isinstance(contract, dict):
                    rung_gate.violations.append("variant_contract:missing")
                    continue
                expected_kind = str(request.get("variant_kind") or request["direction"])
                if contract.get("variant_kind") != expected_kind:
                    rung_gate.violations.append(
                        f"variant_contract:kind:{contract.get('variant_kind')} != {expected_kind}"
                    )
                if expected_kind in DIRECTIONS:
                    rung_gate.violations.extend(
                        audit_variant_direction(source_item, payload, expected_kind)
                    )

        patch_id = generate_authoring_proposal(
            root,
            client,
            subjects=sorted({s for t in plan.targets for s in t.subjects}) or None,
            instructions=_variant_instructions(plan, source_item, target_rung, request, extra),
            row_transform=_composed,
        )
        return patch_id, rung_gate

    from pydantic import ValidationError

    try:
        try:
            patch_id, rung_gate = _run(None)
        except (ValidationError, ValueError) as exc:
            # Fast/low-effort models occasionally emit schema-invalid proposals
            # (e.g. a forbidden `target` on a create). One corrective retry with
            # the validator's message; a second failure is terminal.
            corrective = (
                "PREVIOUS ATTEMPT REJECTED: the output failed schema validation. "
                f"Fix exactly this and emit a valid proposal: {exc}"
            )
            patch_id, rung_gate = _run(corrective)
        else:
            if rung_gate.violations and vault.config.rung_variants.retry_on_rung_violation:
                corrective = (
                    "PREVIOUS ATTEMPT REJECTED by the deterministic rung gate. Fix these violations exactly: "
                    + "; ".join(rung_gate.violations)
                )
                patch_id, rung_gate = _run(corrective)
    except Exception as exc:
        # The service owns the request row's terminal status: a job that dies
        # must never leave the row wedged in `generating` (which would hold the
        # source item out of the queue and block re-requests).
        repository.update_rung_variant_request(
            request_id, status="failed", failure_reason=str(exc)[:500], clock=clock
        )
        raise

    created = _created_item_row(repository, patch_id)
    if created is None:
        repository.update_rung_variant_request(
            request_id, status="failed", patch_id=patch_id,
            failure_reason="generation produced no practice item", clock=clock,
        )
        return {"request_id": request_id, "status": "failed", "patch_id": patch_id}
    row_id, item_id = created
    if rung_gate.violations:
        repository.update_rung_variant_request(
            request_id, status="review_required", patch_id=patch_id,
            created_practice_item_id=item_id,
            failure_reason="; ".join(rung_gate.violations), clock=clock,
        )
        return {"request_id": request_id, "status": "review_required", "patch_id": patch_id}
    # Learner-authority accept: the learner explicitly asked for this item, and
    # it passed the deterministic rung gate — apply it now rather than parking a
    # requested variant in the review inbox (same authority as item_authoring).
    try:
        from learnloop.services.proposals import accept_items

        accept_items(root, patch_id, [row_id], clock=clock)
    except Exception as exc:
        repository.update_rung_variant_request(
            request_id, status="review_required", patch_id=patch_id,
            created_practice_item_id=item_id,
            failure_reason=f"accept failed: {exc}", clock=clock,
        )
        return {"request_id": request_id, "status": "review_required", "patch_id": patch_id}
    repository.update_rung_variant_request(
        request_id, status="applied", patch_id=patch_id, created_practice_item_id=item_id, clock=clock
    )
    return {"request_id": request_id, "status": "applied", "practice_item_id": item_id, "patch_id": patch_id}


def _rebuild_rung(repository: Repository, request: dict[str, Any]) -> RungTarget:
    try:
        snapshot = json.loads(request["target_rung_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        snapshot = {}
    if snapshot.get("source") == "milestone_edge":
        return RungTarget(
            waypoint_slug=str(snapshot.get("waypoint_slug") or ""),
            capability=str(snapshot.get("capability") or ""),
            task_features=dict(snapshot.get("task_features") or {}),
            task_feature_bounds={
                k: dict(v) for k, v in (snapshot.get("task_feature_bounds") or {}).items()
            },
            task_feature_schema_version_id=str(snapshot.get("task_feature_schema_version_id") or ""),
            source="milestone_edge",
            milestone_slug=snapshot.get("milestone_slug"),
            edge_id=snapshot.get("edge_id"),
            envelope_version_id=snapshot.get("envelope_version_id"),
        )
    return waypoint_rung(repository, str(request["target_waypoint_slug"]))


def _variant_instructions(
    plan: Any,
    source_item: PracticeItem,
    rung: RungTarget,
    request: dict[str, Any],
    extra: str | None,
) -> str:
    variant_kind = str(request.get("variant_kind") or request["direction"])
    lines = [
        f"Author exactly ONE new LearnLoop Practice Item: a {variant_kind} variant "
        f"of an existing item, one depth waypoint {'down' if request['direction'] == 'easier' else 'up'} "
        f"({request['source_waypoint_slug']} → {rung.waypoint_slug}).",
        "Create only practice_item proposal items; do not create Learning Objects, concepts, or edges.",
        f"Attach it to learning_object_id '{request['learning_object_id']}'.",
        "SOURCE ITEM (ground the variant in the same knowledge; do NOT duplicate its prompt or surface): "
        + json.dumps(
            {
                "id": source_item.id,
                "practice_mode": source_item.practice_mode,
                "prompt": source_item.prompt,
                "expected_answer": source_item.expected_answer,
                "surface_family": source_item.surface_family,
                "evidence_facets": list(source_item.evidence_facets),
                "difficulty": source_item.difficulty,
                "capability": source_item.capability,
                "task_features": source_item.task_features,
                "grading_rubric": (
                    source_item.grading_rubric.model_dump(mode="json", exclude_none=True)
                    if source_item.grading_rubric is not None
                    else None
                ),
                "trace_contract": (
                    source_item.trace_contract.model_dump(mode="json", exclude_none=True)
                    if source_item.trace_contract is not None
                    else None
                ),
            },
            sort_keys=True,
        ),
        "Treat the source facets as a prior, not a mandate. Independently compile "
        "the variant's genuine measurement targets; use a strict subset or abstain "
        "with item_local/no_canonical_facet when appropriate. Never inherit a facet "
        "merely to preserve list equality.",
        f"Set variant_contract.variant_kind='{variant_kind}' and declare intended_manipulations "
        "(axis plus direction), incidental_changes, held_constant, and checkpoint "
        "preservation/deepening/drops. Silent demand-axis or checkpoint changes are rejected.",
        "Depth waypoint (a deterministic gate rejects overshoot): set `capability` to "
        f"'{rung.capability}' exactly and every task_features dimension to the target: "
        + json.dumps(rung.task_features, sort_keys=True)
        + ". Keep retrieval_demand/transfer_distance/scaffold_level inside these bands: "
        + json.dumps({k: list(v) for k, v in rung_float_proxies(rung).items()}, sort_keys=True)
        + ".",
        "Calibrate difficulty to the target's recommended_difficulty_band; difficulty varies WITHIN "
        "the waypoint — never change the waypoint to change difficulty. Set difficulty_source='llm_estimate'.",
        f"Targets: {[target.as_dict() for target in plan.targets]}",
    ]
    if extra:
        lines.append(extra)
    return "\n".join(lines)


def _created_item_row(repository: Repository, patch_id: str) -> tuple[str, str] | None:
    """(proposal_row_id, practice_item_id) of the created variant, or None."""

    for row in repository.proposal_items(patch_id):
        if row.get("item_type") != "practice_item" or row.get("operation") != "create":
            continue
        payload = row.get("edited_payload") if row.get("edited_payload") is not None else row.get("payload")
        if isinstance(payload, dict) and payload.get("id"):
            return str(row["id"]), str(payload["id"])
    return None
