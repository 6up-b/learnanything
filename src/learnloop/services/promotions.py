"""Promote a socratic tutor question into practice / a gap need (spec_tutor_promotion.md §3).

``promote_tutor_question`` is the sidecar-facing entry point. It is idempotent by
the ``question_promotions`` PK: a turn that was already promoted returns its
existing ledger row unchanged. Otherwise it runs the Step-0 PromotionAnalysis,
short-circuits on dedup, materializes the exchange as a grounding note, then
either authors a practice item (practice intent) or files a gap need with a
self-report claim and inline diagnostic generation (gap intent). Every path
records a ``decision_features`` row (``decision_type='question_promotion'``) whose
features are recomputable read-side from a bare ``question_event`` (§0 fitting
contract), and the promotion never touches ``question_events.rating`` (§2 v3).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import CodexUnavailable, PromotionAnalysisContext
from learnloop.codex.prompts import TUTOR_PROMOTION_PROMPT
from learnloop.codex.schemas import PromotionAnalysis
from learnloop.db.repositories import Repository
from learnloop.services.mastery import display_mastery
from learnloop.services.practice_generation import (
    PracticeExpansionError,
    _ability_logit,
    _success_band_difficulty,
    generate_diagnostic_practice_proposal,
)
from learnloop.services.proposals import generate_authoring_proposal
from learnloop.services.tutor_qa import _thread, build_tutor_qa_note
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LearningObject, LoadedVault
from learnloop.vault.models import learning_object_facet_union
from learnloop.vault.paths import VaultPaths

_TUTOR_PROMOTED_TAG = "tutor_promoted"
_TRANSFER_NATURES = frozenset({"transfer", "edge_case", "what_if"})


class PromotionError(ValueError):
    pass


def promote_tutor_question(
    root: Path,
    client: Any,
    *,
    event_id: str,
    intent: str,
    subject_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Promote one answered tutor turn (spec_tutor_promotion.md §3).

    ``intent`` is ``"practice"`` (keep the socratic question as a rep) or
    ``"gap"`` (the learner could not answer it — measure before scheduling; the
    gap route requires an origin LO, so it is restricted to the ``practice`` /
    ``feedback`` contexts). Returns the persisted ``question_promotions`` row
    (see :meth:`Repository.question_promotion`) — ``route`` is one of
    ``auto_apply`` / ``review_required`` / ``diagnostic_pending`` /
    ``existing_item``, and the ``*_id`` columns carry the created/linked entities
    the caller renders into a result chip.
    """

    if intent not in {"practice", "gap"}:
        raise PromotionError(f"Unknown promotion intent {intent!r}")

    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)

    existing = repository.question_promotion(event_id)
    if existing is not None:
        return existing

    event = repository.question_event(event_id)
    if event is None:
        raise PromotionError(f"Question event {event_id} was not found.")
    if event.get("answer_status") != "answered":
        raise PromotionError("Only answered tutor turns can be promoted.")

    context = str(event.get("context"))
    if intent == "gap" and context not in {"practice", "feedback"}:
        raise PromotionError(
            "The gap route requires an origin learning object and is only "
            "available in the practice/feedback contexts."
        )

    origin_item = None
    origin_lo: LearningObject | None = None
    item_id = event.get("practice_item_id")
    if item_id is not None:
        origin_item = vault.practice_items.get(item_id)
        if origin_item is not None:
            origin_lo = vault.learning_objects.get(origin_item.learning_object_id)
    if intent == "gap" and origin_lo is None:
        raise PromotionError("The gap route could not resolve an origin learning object for this turn.")

    thread = _thread(
        repository,
        context=context,
        practice_item_id=event.get("practice_item_id"),
        attempt_id=event.get("attempt_id"),
        note_id=event.get("note_id"),
        session_id=event.get("session_id"),
    )

    analysis = _run_promotion_analysis(
        client,
        vault,
        origin_lo,
        thread,
        intent,
        subject_id=subject_id,
    )
    attributed = [vault.canonical_facet_id(str(facet)) for facet in analysis.attributed_facets]
    attributed = list(dict.fromkeys(attributed))

    # Step 0 dedup short-circuit: an existing item already exercises this probe.
    covered = analysis.covered_by_practice_item_id
    if covered and covered in vault.practice_items:
        return _promote_existing_item(
            root,
            repository,
            vault,
            event=event,
            intent=intent,
            analysis=analysis,
            attributed=attributed,
            origin_lo=origin_lo,
            existing_item_id=covered,
            clock=clock,
        )

    # Step 1 grounding: materialize the turn as a vault note (idempotent).
    note_info = build_tutor_qa_note(vault, repository, event, subject_id=subject_id, clock=clock)
    saved_note_id = note_info["note_id"]
    if not note_info["reused"]:
        vault = load_vault(root)  # make the freshly written note visible

    if intent == "practice":
        return _promote_practice(
            root,
            repository,
            vault,
            client,
            event=event,
            analysis=analysis,
            attributed=attributed,
            origin_lo=origin_lo,
            saved_note_id=saved_note_id,
            clock=clock,
        )
    return _promote_gap(
        root,
        repository,
        vault,
        client,
        event=event,
        analysis=analysis,
        attributed=attributed,
        origin_lo=origin_lo,
        saved_note_id=saved_note_id,
        clock=clock,
    )


def _run_promotion_analysis(
    client: Any,
    vault: LoadedVault,
    origin_lo: LearningObject | None,
    thread: list[dict[str, Any]],
    intent: str,
    *,
    subject_id: str | None = None,
) -> PromotionAnalysis:
    """Step-0 structured extraction; degrades to an empty analysis when unavailable."""

    facet_vocabulary: list[str] = []
    existing_items: list[dict[str, Any]] = []
    concept_neighbors: list[dict[str, Any]] = []
    if origin_lo is not None:
        facet_vocabulary = _origin_facet_vocabulary(vault, origin_lo)
        existing_items = _origin_existing_items(vault, origin_lo)
        concept_neighbors = _concept_neighbors(vault, origin_lo)
    elif subject_id is not None:
        subject_los = [
            lo for lo in vault.learning_objects.values() if subject_id in lo.subjects
        ]
        facet_vocabulary = sorted(
            {
                facet
                for lo in subject_los
                for facet in _origin_facet_vocabulary(vault, lo)
            }
        )
        existing_items = [
            item
            for lo in subject_los
            for item in _origin_existing_items(vault, lo)
        ]

    runner = getattr(client, "run_promotion_analysis", None)
    if not callable(runner):
        return PromotionAnalysis()
    context = PromotionAnalysisContext(
        intent=intent,
        thread=thread,
        learning_object_id=origin_lo.id if origin_lo is not None else None,
        learning_object_title=origin_lo.title if origin_lo is not None else None,
        facet_vocabulary=facet_vocabulary,
        concept_neighbors=concept_neighbors,
        existing_items=existing_items,
    )
    result = runner(context)
    return result if isinstance(result, PromotionAnalysis) else PromotionAnalysis.model_validate(result)


def _promote_existing_item(
    root: Path,
    repository: Repository,
    vault: LoadedVault,
    *,
    event: dict[str, Any],
    intent: str,
    analysis: PromotionAnalysis,
    attributed: list[str],
    origin_lo: LearningObject | None,
    existing_item_id: str,
    clock: Clock | None,
) -> dict[str, Any]:
    """Dedup route: schedule the existing item; gap intent still writes the claim (§3 Step 0)."""

    learner_claim_id: str | None = None
    if intent == "gap" and origin_lo is not None:
        learner_claim_id = _write_gap_claim(repository, vault, origin_lo, attributed, clock=clock)
    _record_promotion_decision_features(
        repository,
        vault,
        event=event,
        origin_lo=origin_lo,
        analysis=analysis,
        attributed=attributed,
        intent=intent,
        outcome="existing_item",
        clock=clock,
    )
    repository.insert_question_promotion(
        question_event_id=str(event["id"]),
        intent=intent,
        route="existing_item",
        attributed_facets=attributed,
        question_nature=analysis.question_nature,
        attempted_in_thread=analysis.attempted_in_thread,
        learner_claim_id=learner_claim_id,
        existing_practice_item_id=existing_item_id,
        clock=clock,
    )
    return repository.question_promotion(str(event["id"]))


def _promote_practice(
    root: Path,
    repository: Repository,
    vault: LoadedVault,
    client: Any,
    *,
    event: dict[str, Any],
    analysis: PromotionAnalysis,
    attributed: list[str],
    origin_lo: LearningObject | None,
    saved_note_id: str,
    clock: Clock | None,
) -> dict[str, Any]:
    """Practice route: author a practice item, enforcing routing in code (§3 Steps 2-3)."""

    source_refs, origin_source_note_ids = _promotion_source_refs(vault, saved_note_id, origin_lo)
    force_review_no_grounding = not origin_source_note_ids
    subjects = _promotion_subjects(vault, origin_lo, saved_note_id)
    instructions = _promotion_instructions(vault, repository, origin_lo, analysis, attributed, event)

    def _enforce_routing(rows: list[dict[str, Any]]) -> None:
        has_lo_create = any(
            row.get("item_type") == "learning_object" and row.get("operation") == "create"
            for row in rows
        )
        force_review = force_review_no_grounding or has_lo_create
        for row in rows:
            payload = row.get("payload")
            if isinstance(payload, dict) and row.get("item_type") in {"practice_item", "learning_object"}:
                tags = list(payload.get("tags") or [])
                if _TUTOR_PROMOTED_TAG not in tags:
                    tags.append(_TUTOR_PROMOTED_TAG)
                payload["tags"] = tags
            if force_review and row.get("_auto_apply"):
                row["_auto_apply"] = False

    patch_id = generate_authoring_proposal(
        root,
        client,
        subjects=subjects,
        source_refs=source_refs,
        instructions=instructions,
        merge_context_source_refs=True,
        row_transform=_enforce_routing,
        clock=clock,
    )

    created_pi, created_lo, auto_applied, has_lo_create = _created_entities(repository, patch_id)
    if has_lo_create:
        outcome = "new_lo_review"
    elif auto_applied:
        outcome = "attached_to_existing_lo_auto"
    else:
        outcome = "attached_to_existing_lo_review"
    route = "auto_apply" if auto_applied else "review_required"

    _record_promotion_decision_features(
        repository,
        vault,
        event=event,
        origin_lo=origin_lo,
        analysis=analysis,
        attributed=attributed,
        intent="practice",
        outcome=outcome,
        clock=clock,
    )
    repository.insert_question_promotion(
        question_event_id=str(event["id"]),
        intent="practice",
        route=route,
        attributed_facets=attributed,
        question_nature=analysis.question_nature,
        attempted_in_thread=analysis.attempted_in_thread,
        proposed_patch_id=patch_id,
        saved_note_id=saved_note_id,
        created_practice_item_id=created_pi if auto_applied else None,
        created_learning_object_id=created_lo if auto_applied else None,
        clock=clock,
    )
    return repository.question_promotion(str(event["id"]))


def _promote_gap(
    root: Path,
    repository: Repository,
    vault: LoadedVault,
    client: Any,
    *,
    event: dict[str, Any],
    analysis: PromotionAnalysis,
    attributed: list[str],
    origin_lo: LearningObject,
    saved_note_id: str,
    clock: Clock | None,
) -> dict[str, Any]:
    """Gap route: self-report claim + intervention need + inline diagnostic gen (§3 Step 2.5)."""

    assert origin_lo is not None  # enforced by the caller (practice/feedback only)
    learner_claim_id = _write_gap_claim(repository, vault, origin_lo, attributed, clock=clock)

    # Need-filing dedup (§4b): link to a pending gap need on the same facets.
    existing_need = repository.pending_gap_need_for_facets(attributed) if attributed else None
    if existing_need is not None:
        need_id = str(existing_need["id"])
    else:
        need_id = _file_gap_need(
            repository,
            origin_lo=origin_lo,
            attributed=attributed,
            analysis=analysis,
            event=event,
            clock=clock,
        )
        # Inline diagnostic generation, tolerating provider unavailability (the
        # need simply waits for the next generation run).
        if callable(getattr(client, "run_authoring_proposal", None)):
            try:
                generate_diagnostic_practice_proposal(root, client, learning_object_id=origin_lo.id)
            except (CodexUnavailable, PracticeExpansionError, TimeoutError):
                pass

    _record_promotion_decision_features(
        repository,
        vault,
        event=event,
        origin_lo=origin_lo,
        analysis=analysis,
        attributed=attributed,
        intent="gap",
        outcome="diagnostic_pending",
        clock=clock,
    )
    repository.insert_question_promotion(
        question_event_id=str(event["id"]),
        intent="gap",
        route="diagnostic_pending",
        attributed_facets=attributed,
        question_nature=analysis.question_nature,
        attempted_in_thread=analysis.attempted_in_thread,
        learner_claim_id=learner_claim_id,
        intervention_need_id=need_id,
        saved_note_id=saved_note_id,
        clock=clock,
    )
    return repository.question_promotion(str(event["id"]))


def _write_gap_claim(
    repository: Repository,
    vault: LoadedVault,
    origin_lo: LearningObject,
    attributed: list[str],
    *,
    clock: Clock | None,
) -> str:
    """G2 self-report: a low ``tutor_gap_declaration`` claim scoped to the LO / facet."""

    config = vault.config.tutor_promotion
    return repository.insert_learner_claim(
        {
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": origin_lo.id,
            "evidence_family": attributed[0] if attributed else None,
            "claimed_level": config.gap_claim_level,
            "prior_pseudo_count": config.gap_claim_pseudo_count,
            "source": "tutor_gap_declaration",
        },
        clock=clock,
    )


def _file_gap_need(
    repository: Repository,
    *,
    origin_lo: LearningObject,
    attributed: list[str],
    analysis: PromotionAnalysis,
    event: dict[str, Any],
    clock: Clock | None,
) -> str:
    """G3 instrument authoring: file a ``tutor_gap_declaration`` intervention need."""

    now = utc_now_iso(clock)
    transfer_biased = analysis.question_nature in _TRANSFER_NATURES
    diagnostic_focus = {
        "tutor_question_context": [
            {"question_md": turn.get("question_md"), "answer_md": turn.get("answer_md")}
            for turn in _thread_from_event(event)
        ],
        "question_nature": analysis.question_nature,
        "attempted_in_thread": analysis.attempted_in_thread,
        "source": "tutor_gap_declaration",
    }
    return repository.upsert_intervention_need(
        {
            "attempt_id": event.get("attempt_id"),
            "learning_object_id": origin_lo.id,
            "practice_item_id": event.get("practice_item_id"),
            "desired_intent": "transfer" if transfer_biased else "diagnose",
            "trigger_reason": "tutor_gap_declaration",
            "target_facets": attributed,
            "error_types": [],
            "priority": 0.6,
            "status": "pending",
            "blocked_reason": "tutor_gap_declaration",
            "candidate_requirements": {"same_learning_object": True},
            "diagnostic_focus": diagnostic_focus,
            "created_at": now,
            "updated_at": now,
        }
    )


def _thread_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    """The promoted turn as a one-item thread for the need's steering context."""

    return [
        {
            "question_md": event.get("question_md"),
            "answer_md": event.get("answer_md"),
            "question_type": event.get("question_type"),
        }
    ]


def _record_promotion_decision_features(
    repository: Repository,
    vault: LoadedVault,
    *,
    event: dict[str, Any],
    origin_lo: LearningObject | None,
    analysis: PromotionAnalysis,
    attributed: list[str],
    intent: str,
    outcome: str,
    clock: Clock | None,
) -> None:
    """Log the promotion training signal (§3 Step 4 / §0 fitting contract).

    Mirrors ``_record_followup_decision_features``: every feature is recomputable
    read-side from a bare ``question_event`` so promotable-but-unpromoted turns
    can serve as the fitting negatives. ``rating`` is copied through as-is and is
    NEVER written back (spec §2 v3)."""

    mastery_mean, mastery_variance = _origin_mastery(repository, origin_lo)
    band = _recommended_difficulty_band(vault, mastery_mean)
    uncertainty_snapshot: dict[str, float] = {}
    if origin_lo is not None:
        for state in repository.facet_uncertainty_states(
            origin_lo.id, statuses=("open", "resolving", "resolved")
        ):
            uncertainty_snapshot[state.facet_id] = float(state.uncertainty)

    repository.record_decision_features(
        decision_id=str(event["id"]),
        decision_type="question_promotion",
        ability_vector={
            "origin_learning_object_id": origin_lo.id if origin_lo is not None else None,
            "origin_mastery_mean": mastery_mean,
            "origin_mastery_variance": mastery_variance,
            "facet_uncertainty_snapshot": uncertainty_snapshot,
        },
        item_demand_vector={
            "attributed_facets": attributed,
            "question_nature": analysis.question_nature,
            "covered_by_practice_item_id": analysis.covered_by_practice_item_id,
            "recommended_difficulty_band": list(band) if band is not None else None,
        },
        context={
            "question_type": event.get("question_type"),
            "hint_equivalent": bool(event.get("hint_equivalent")),
            # Read-only: the 👍/👎 rating is copied as-is, never auto-set (§2 v3).
            "rating": event.get("rating"),
            "seconds_into_attempt": event.get("seconds_into_attempt"),
            "context": event.get("context"),
            "intent": intent,
            "attempted_in_thread": analysis.attempted_in_thread,
            "covered_by": analysis.covered_by_practice_item_id,
            "outcome": outcome,
        },
        algorithm_version=vault.config.algorithms.algorithm_version,
        clock=clock,
    )


def _origin_mastery(
    repository: Repository, origin_lo: LearningObject | None
) -> tuple[float | None, float | None]:
    if origin_lo is None:
        return None, None
    state = repository.mastery_state(origin_lo.id)
    if state is None:
        return None, None
    display = display_mastery(state)
    return display.mastery_mean, display.mastery_variance


def _recommended_difficulty_band(
    vault: LoadedVault, mastery_mean: float | None
) -> tuple[float, float]:
    """Mode-ladder difficulty band (§3 Step 2.6) — reuses the expansion planner math."""

    irt = vault.config.mastery.irt
    return _success_band_difficulty(
        _ability_logit(mastery_mean),
        vault.config.practice_generation.practice_success_band,
        discrimination=irt.discrimination_default,
        difficulty_scale=irt.difficulty_prior_scale,
    )


def _promotion_instructions(
    vault: LoadedVault,
    repository: Repository,
    origin_lo: LearningObject | None,
    analysis: PromotionAnalysis,
    attributed: list[str],
    event: dict[str, Any],
) -> str:
    """TUTOR_PROMOTION_PROMPT + the PROMOTION_CONTEXT payload (thread, origin, band)."""

    mastery_mean, _ = _origin_mastery(repository, origin_lo)
    band = _recommended_difficulty_band(vault, mastery_mean)
    payload = {
        "thread": _thread_from_event(event),
        "origin_practice_item_id": event.get("practice_item_id"),
        "origin_learning_object_id": origin_lo.id if origin_lo is not None else None,
        "origin_learning_object_facets": _origin_facet_vocabulary(vault, origin_lo)
        if origin_lo is not None
        else [],
        "concept_neighbors": _concept_neighbors(vault, origin_lo) if origin_lo is not None else [],
        "attributed_facets": attributed,
        "question_nature": analysis.question_nature,
        "attempted_in_thread": analysis.attempted_in_thread,
        "mastery_mean": mastery_mean,
        "recommended_difficulty_band": list(band),
    }
    return (
        TUTOR_PROMOTION_PROMPT
        + "\n\nPROMOTION_CONTEXT:\n"
        + json.dumps(payload, sort_keys=True, ensure_ascii=False)
    )


def _promotion_source_refs(
    vault: LoadedVault, saved_note_id: str, origin_lo: LearningObject | None
) -> tuple[list[dict[str, Any]], list[str]]:
    """(source_refs, origin_source_note_ids): the grounding note + origin LO source material.

    A note-only grounding is semantically empty (the tutor guardrail forbids the
    answer), so auto-apply requires the origin LO's own source notes (§3 Step 1);
    the returned id list is empty when the LO has none, which forces review."""

    refs: list[dict[str, Any]] = []
    saved_note = vault.notes.get(saved_note_id)
    if saved_note is not None:
        refs.append({"ref_type": "note", "ref_id": saved_note.id, "path": saved_note.path})

    origin_source_note_ids: list[str] = []
    if origin_lo is not None:
        for note in vault.notes.values():
            if note.id == saved_note_id or origin_lo.id not in note.related_los:
                continue
            ref_type = "canonical_source" if note.source_type == "canonical_source" else "note"
            refs.append({"ref_type": ref_type, "ref_id": note.id, "path": note.path})
            origin_source_note_ids.append(note.id)
    return refs, origin_source_note_ids


def _promotion_subjects(
    vault: LoadedVault, origin_lo: LearningObject | None, saved_note_id: str
) -> list[str] | None:
    if origin_lo is not None and origin_lo.subjects:
        return list(origin_lo.subjects)
    note = vault.notes.get(saved_note_id)
    if note is not None and note.subjects:
        return list(note.subjects)
    return None


def _created_entities(
    repository: Repository, patch_id: str
) -> tuple[str | None, str | None, bool, bool]:
    """(created_practice_item_id, created_learning_object_id, auto_applied, has_lo_create)."""

    created_pi: str | None = None
    created_lo: str | None = None
    auto_applied = False
    has_lo_create = False
    for item in repository.proposal_items(patch_id):
        if item.get("operation") != "create":
            continue
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        entity_id = payload.get("id") or item.get("target_entity_id")
        if item.get("item_type") == "practice_item":
            created_pi = created_pi or entity_id
            if item.get("decision") == "accepted":
                auto_applied = True
        elif item.get("item_type") == "learning_object":
            has_lo_create = True
            created_lo = created_lo or entity_id
    return created_pi, created_lo, auto_applied, has_lo_create


def _origin_facet_vocabulary(vault: LoadedVault, origin_lo: LearningObject) -> list[str]:
    facets = {
        vault.canonical_facet_id(facet)
        for facet in learning_object_facet_union(origin_lo)
    }
    for item in vault.practice_items.values():
        if item.learning_object_id == origin_lo.id:
            facets.update(vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets)
    return sorted(facets)


def _origin_existing_items(vault: LoadedVault, origin_lo: LearningObject) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in sorted(vault.practice_items.values(), key=lambda entry: entry.id):
        if item.learning_object_id != origin_lo.id:
            continue
        prompt = " ".join(item.prompt.split())
        items.append(
            {
                "id": item.id,
                "prompt": prompt[:200],
                "surface_family": item.surface_family,
                "evidence_facets": [vault.canonical_facet_id(str(f)) for f in item.evidence_facets],
            }
        )
    return items


def _concept_neighbors(vault: LoadedVault, origin_lo: LearningObject) -> list[dict[str, Any]]:
    concept_id = origin_lo.concept
    if not concept_id:
        return []
    neighbors: dict[str, dict[str, Any]] = {}
    for edge in vault.edges:
        other: str | None = None
        if edge.source == concept_id:
            other = edge.target
        elif edge.target == concept_id:
            other = edge.source
        if other is None or other in neighbors:
            continue
        concept = vault.concepts.get(other)
        neighbors[other] = {
            "id": other,
            "title": concept.title if concept is not None else None,
            "relation": edge.relation_type,
        }
    # Always include the LO's own concept so a NEW-LO batch can reuse it.
    if concept_id not in neighbors:
        concept = vault.concepts.get(concept_id)
        neighbors[concept_id] = {
            "id": concept_id,
            "title": concept.title if concept is not None else None,
            "relation": "self",
        }
    return sorted(neighbors.values(), key=lambda entry: str(entry["id"]))
