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
   sibling item at the target waypoint through the rung-gated generation path,
   with deterministic stamping: inherited ``evidence_facets`` (goal-scope
   continuity), a shared ``evidence_fingerprint.source_family`` (kinship
   discounting — the variant's evidence is correlated with the source's, never
   double-counted), and authored criterion targets carrying the rung's
   capability. The source item is never mutated.
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
from learnloop.services.mastery import display_mastery
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

    request_id = repository.insert_rung_variant_request(
        {
            "source_practice_item_id": item.id,
            "learning_object_id": item.learning_object_id,
            "direction": direction,
            "source_waypoint_slug": source_slug,
            "target_waypoint_slug": target_rung.waypoint_slug,
            "target_rung_json": json.dumps(target_rung.as_dict(), sort_keys=True),
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

    source_facets = [vault.canonical_facet_id(f) for f in source_item.evidence_facets]

    def _stamp_variant(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            if row.get("item_type") != "practice_item" or row.get("operation") != "create":
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            # (a) Fail-closed facet inheritance: goal scope is facet-based, so
            # the variant must carry the source's facets to keep counting.
            payload_facets = [vault.canonical_facet_id(f) for f in payload.get("evidence_facets") or []]
            if source_facets and (not payload_facets or not set(payload_facets) & set(source_facets)):
                payload["evidence_facets"] = list(source_facets)
                weight = round(1.0 / len(source_facets), 6)
                payload["evidence_weights"] = {facet: weight for facet in source_facets}
            # (b) Shared surface group: kinship discounting treats the variant's
            # evidence as correlated with the source's, never independent.
            fingerprint = payload.get("evidence_fingerprint")
            if not isinstance(fingerprint, dict):
                fingerprint = {}
            fingerprint["source_family"] = surface_group_id(source_item)
            payload["evidence_fingerprint"] = fingerprint
            # (c) Authored criterion targets carrying the rung capability, so
            # future attempts on the variant attribute to that capability slice
            # (compile_criterion_targets prefers authored targets).
            rubric = payload.get("grading_rubric")
            if isinstance(rubric, dict):
                facet_cycle = payload.get("evidence_facets") or source_facets
                for index, criterion in enumerate(rubric.get("criteria") or []):
                    if isinstance(criterion, dict) and not criterion.get("targets"):
                        facet = facet_cycle[index % len(facet_cycle)] if facet_cycle else None
                        if facet:
                            criterion["targets"] = [
                                {"facet": facet, "capability": target_rung.capability, "role": "primary"}
                            ]
            payload["tags"] = sorted(set(payload.get("tags") or []) | {"rung_variant"})

    def _run(extra: str | None) -> tuple[str, "_RungGate"]:
        rung_gate = _RungGate(repository, plan)

        def _composed(rows: list[dict[str, Any]]) -> None:
            rung_gate(rows)
            _stamp_variant(rows)

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
    prompt_excerpt = (source_item.prompt or "")[:600]
    expected = source_item.expected_answer
    expected_excerpt = (expected if isinstance(expected, str) else json.dumps(expected))[:400]
    lines = [
        f"Author exactly ONE new LearnLoop Practice Item: an {request['direction']} sibling variant "
        f"of an existing item, one depth waypoint {'down' if request['direction'] == 'easier' else 'up'} "
        f"({request['source_waypoint_slug']} → {rung.waypoint_slug}).",
        "Create only practice_item proposal items; do not create Learning Objects, concepts, or edges.",
        f"Attach it to learning_object_id '{request['learning_object_id']}'.",
        "SOURCE ITEM (ground the variant in the same knowledge; do NOT duplicate its prompt or surface): "
        + json.dumps(
            {
                "id": source_item.id,
                "practice_mode": source_item.practice_mode,
                "prompt_excerpt": prompt_excerpt,
                "expected_answer_excerpt": expected_excerpt,
                "surface_family": source_item.surface_family,
                "evidence_facets": list(source_item.evidence_facets),
            },
            sort_keys=True,
        ),
        "evidence_facets MUST be exactly the source item's facet ids (same knowledge, different depth); "
        "set evidence_weights accordingly and provide the item's OWN grading_rubric plus "
        "criterion_facet_weights over those facets.",
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
