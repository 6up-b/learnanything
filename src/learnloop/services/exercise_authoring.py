"""Reader exercise import: selected textbook exercises become real PracticeItems.

The exact-exercise slice of the "become good at tasks like these" journey: the
learner selects one or several consecutive end-of-chapter exercises in the
Reader and asks to practice them. The selection is anchored through the
annotation crosswalk into ordered source-block segments, then ONE codex call
(``run_exercise_authoring``, getattr-discovered) completes each exercise into a
full practice-item contract — expected answer, rubric, facet mapping with
criterion weights, progressive hints, and descriptive depth-rung metadata
(capability + task-feature vector, the same closed vocabularies the rung
backfill uses).

Authority split (the reason this is not a review-gated proposal): the learner
choosing an exercise is the authority for its existence — a learner-authority
write like the quick-check escalation. The exercise SURFACE stays
source-authored: the stored prompt is re-anchored verbatim against the
selection text in code, never taken from the model. Everything the model does
author is admitted or repaired by deterministic validators (facet registry,
rubric arithmetic, capability vocabulary, p1_launch task-feature schema,
coordination⇒whole_task) before the vault write. Depth metadata here DESCRIBES
what the source exercise demands; it never chooses the learner's next practice
rung (``select_rung`` owns that).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span
from learnloop.services.activity_patterns import (
    LEGACY_UNMAPPED,
    ensure_builtin_task_feature_schema,
    ensure_capability_alias_registry,
    map_capability,
    validate_task_features,
)
from learnloop.services.annotations import translate_selection
from learnloop.services.depth_rungs import TASK_FEATURE_SCHEMA_SLUG
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, learning_object_facet_union
from learnloop.vault.writer import upsert_practice_item

# Bounded context: surrounding blocks carry shared preambles ("In the following
# exercises assume...") and in-scope definitions, never the whole chapter.
MAX_CONTEXT_BLOCKS = 24
MAX_CONTEXT_CHARS = 12_000
MAX_CATALOG_OBJECTS = 80
MAX_HINTS = 4

_DEFAULT_RUBRIC = {
    "max_points": 4,
    "criteria": [
        {
            "id": "correctness",
            "points": 4,
            "description": "Answer matches the expected answer in substance.",
        }
    ],
}


class ExerciseAuthoringError(ValueError):
    """Domain error for the reader exercise-import producer."""


def _normalize(text: str) -> str:
    return " ".join((text or "").split())


def _clamp01(value: Any) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def _anchor_statement(selection_text: str, statement: str) -> str | None:
    """Re-anchor the model's echoed statement as a verbatim slice of the
    learner's selection (whitespace-tolerant, same idea as annotation quote
    relocation). Returns the source-owned slice, or None for a paraphrase."""

    tokens = _normalize(statement).split()
    if not tokens:
        return None
    pattern = r"\s+".join(re.escape(token) for token in tokens)
    match = re.search(pattern, selection_text)
    if match is None:
        return None
    return selection_text[match.start() : match.end()]


def _context_blocks(ir: Any, span_ids: list[str]) -> list[dict[str, str]]:
    """The covered blocks plus one neighbor on each side, in document order."""

    blocks = list(getattr(ir, "blocks", []) or [])
    index_by_span = {block.span_id: idx for idx, block in enumerate(blocks)}
    wanted: dict[int, None] = {}
    for span_id in span_ids:
        idx = index_by_span.get(span_id)
        if idx is None:
            continue
        for neighbor in (idx - 1, idx, idx + 1):
            if 0 <= neighbor < len(blocks):
                wanted.setdefault(neighbor, None)
    view: list[dict[str, str]] = []
    total_chars = 0
    for idx in sorted(wanted)[:MAX_CONTEXT_BLOCKS]:
        block = blocks[idx]
        text = _normalize(block.text)
        if not text:
            continue
        total_chars += len(text)
        if total_chars > MAX_CONTEXT_CHARS:
            break
        view.append(
            {"span_id": block.span_id, "kind": str(block.block_type or ""), "text": text}
        )
    return view


def _catalog(vault: LoadedVault, hint: str | None) -> list[dict[str, Any]]:
    """The bounded LO catalog the model maps into: id, title, summary, and the
    canonical facet vocabulary each object exposes."""

    def entry(lo: Any) -> dict[str, Any]:
        facets: list[dict[str, str]] = []
        seen: set[str] = set()
        for facet in learning_object_facet_union(lo):
            canonical = vault.canonical_facet_id(facet)
            if canonical in seen or canonical not in vault.evidence_facets:
                continue
            seen.add(canonical)
            facets.append({"id": canonical, "title": vault.evidence_facets[canonical].title})
        return {
            "id": lo.id,
            "title": lo.title,
            "summary": (lo.summary or "")[:280],
            "facets": facets,
        }

    active = [lo for lo in vault.learning_objects.values() if lo.status == "active"]
    active.sort(key=lambda lo: (lo.id != hint, lo.id))
    return [entry(lo) for lo in active[:MAX_CATALOG_OBJECTS]]


def _validated_rubric(payload: Any) -> dict[str, Any] | None:
    """Admit the model rubric only when the arithmetic holds (points sum to
    max_points ≤ 4, unique non-empty criteria); otherwise the caller falls
    back to the plain correctness rubric."""

    if payload is None or not payload.criteria:
        return None
    max_points = int(payload.max_points)
    if not 1 <= max_points <= 4:
        return None
    criteria: list[dict[str, Any]] = []
    total = 0.0
    for criterion in payload.criteria:
        criterion_id = (criterion.id or "").strip()
        description = (criterion.description or "").strip()
        if not criterion_id or not description:
            return None
        total += float(criterion.points)
        criteria.append(
            {"id": criterion_id, "points": criterion.points, "description": description}
        )
    if len({criterion["id"] for criterion in criteria}) != len(criteria):
        return None
    if abs(total - max_points) > 1e-6:
        return None
    return {"max_points": max_points, "criteria": criteria}


def _normalized_weights(
    raw: Mapping[str, float], facets: list[str], canonical: Any
) -> dict[str, float]:
    """Weights over exactly the admitted facets: model weights canonicalized
    and filtered, missing facets backfilled uniformly, the whole map
    renormalized to 1.0."""

    weights: dict[str, float] = {}
    for key, value in (raw or {}).items():
        facet = canonical(key)
        if facet in facets and float(value) > 0:
            weights[facet] = weights.get(facet, 0.0) + float(value)
    if not weights:
        return {facet: round(1.0 / len(facets), 4) for facet in facets}
    for facet in facets:
        weights.setdefault(facet, min(weights.values()))
    total = sum(weights.values())
    return {facet: round(value / total, 4) for facet, value in weights.items()}


def import_exercises(
    root: Path,
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    raw_selection: Mapping[str, Any],
    render_view_id: str | None = None,
    source_id: str | None = None,
    revision_id: str | None = None,
    learning_object_hint: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author the learner's selected exercise(s) into schedulable PracticeItems.

    Returns ``{items, skipped, warnings, anchor_status}`` where ``items`` are
    written-card summaries and ``skipped`` carries per-exercise reasons
    (paraphrased statement, unknown learning object, duplicate, ...). Raises
    :class:`ExerciseAuthoringError` when nothing can proceed at all.
    """

    from learnloop.codex.client import ExerciseAuthoringContext

    run = getattr(client, "run_exercise_authoring", None)
    if run is None:
        raise ExerciseAuthoringError("provider does not implement run_exercise_authoring")

    translation = translate_selection(
        repository,
        extraction_id=extraction_id,
        raw_selection=raw_selection,
        render_view_id=render_view_id,
    )
    segments = [
        segment
        for segment in translation.get("segments", [])
        if _normalize(str(segment.get("exact_quote") or ""))
    ]
    if not segments:
        raise ExerciseAuthoringError(
            "the selection could not be anchored to any source block; reselect the exercise text"
        )

    # Learner-EDITED node quotes override the extraction slice for the exercise
    # surface: fixing an OCR mishap is a learner-authority write, and the fixed
    # text is what should be practiced. Unedited quotes never override — the
    # extraction slice (with its LaTeX) is richer than rendered glyph text.
    # Anchors and provenance stay extraction-owned either way.
    edited_quotes: dict[str, list[str]] = {}
    for raw_node in raw_selection.get("nodes", []) or []:
        if not isinstance(raw_node, Mapping) or not raw_node.get("edited"):
            continue
        span = str(raw_node.get("span_id") or raw_node.get("spanId") or "")
        quote = str(raw_node.get("quote") or "").strip()
        if span and quote:
            edited_quotes.setdefault(span, []).append(quote)
    parts: list[str] = []
    consumed: dict[str, int] = {}
    for segment in segments:
        span = str(segment.get("span_id") or "")
        queue = edited_quotes.get(span) or []
        index = consumed.get(span, 0)
        if index < len(queue):
            parts.append(queue[index])
            consumed[span] = index + 1
        else:
            parts.append(str(segment["exact_quote"]))
    exercise_text = "\n\n".join(parts)

    # The capture editor combines a multi-block selection into ONE passage; a
    # selection-level edit overrides the whole surface (per-node edits above
    # remain for callers that send them). Anchors stay extraction-owned.
    edited_text = str(
        raw_selection.get("edited_text") or raw_selection.get("editedText") or ""
    ).strip()
    if edited_text:
        exercise_text = edited_text

    span_ids: list[str] = []
    for segment in segments:
        span_id = str(segment.get("span_id") or "")
        if span_id and span_id not in span_ids:
            span_ids.append(span_id)

    vault = load_vault(root)
    ensure_capability_alias_registry(repository)
    schema_version_id = ensure_builtin_task_feature_schema(repository)
    schema_row = repository.task_feature_schema_version(schema_version_id) or {}
    schema_dims = json.loads(schema_row.get("dimensions_json") or "{}")

    ir = repository.load_document_ir(extraction_id)
    context = ExerciseAuthoringContext(
        extraction_id=extraction_id,
        exercise_text=exercise_text,
        segments=[
            {"span_id": str(segment.get("span_id") or ""), "exact_quote": segment["exact_quote"]}
            for segment in segments
        ],
        section_path=list(segments[0].get("section_path") or []),
        context_blocks=_context_blocks(ir, span_ids) if ir is not None else [],
        learning_objects=_catalog(vault, learning_object_hint),
        learning_object_hint=learning_object_hint or "",
        task_feature_schema=schema_dims,
    )
    result = run(context)

    warnings = [str(warning) for warning in result.warnings if str(warning).strip()]
    if not result.items:
        raise ExerciseAuthoringError("the provider returned no authored exercises")

    def canonical(facet: str) -> str:
        return vault.canonical_facet_id(str(facet))

    source_refs = [
        {
            "ref_type": "canonical_source",
            "ref_id": str(source_id or extraction_id),
            "locator": format_block_span(extraction_id, span_id),
            "locator_scheme": BLOCK_SPAN_V1,
        }
        for span_id in span_ids
    ]

    existing_prompts = {
        _normalize(item.prompt): item.id
        for item in vault.practice_items.values()
        if item.status == "active"
    }
    now = utc_now_iso(clock)
    summaries: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for ordinal, entry in enumerate(result.items, start=1):
        label = entry.title.strip() or f"exercise {ordinal}"

        statement = _anchor_statement(exercise_text, entry.statement_md)
        if statement is None:
            if len(result.items) == 1:
                statement = exercise_text
                warnings.append(
                    f"{label}: statement was not verbatim; the full selection is the prompt"
                )
            else:
                skipped.append(
                    {"title": label, "reason": "statement is not a verbatim excerpt of the selection"}
                )
                continue

        duplicate_of = existing_prompts.get(_normalize(statement))
        if duplicate_of is not None:
            skipped.append(
                {
                    "title": label,
                    "reason": "already in your practice",
                    "practice_item_id": duplicate_of,
                    "deduplicated": True,
                }
            )
            continue

        lo_id = entry.learning_object_id if entry.learning_object_id in vault.learning_objects else None
        if lo_id is None and learning_object_hint in vault.learning_objects:
            lo_id = learning_object_hint
            warnings.append(
                f"{label}: unknown learning object {entry.learning_object_id!r}; used the hint"
            )
        if lo_id is None:
            skipped.append(
                {"title": label, "reason": f"unknown learning object {entry.learning_object_id!r}"}
            )
            continue
        lo = vault.learning_objects[lo_id]

        expected = entry.expected_answer_md.strip()
        if not expected:
            skipped.append({"title": label, "reason": "no expected answer authored"})
            continue

        facets: list[str] = []
        for facet in entry.evidence_facets:
            mapped = canonical(facet)
            if mapped in vault.evidence_facets and mapped not in facets:
                facets.append(mapped)
        if not facets:
            for facet in learning_object_facet_union(lo):
                mapped = canonical(facet)
                if mapped in vault.evidence_facets and mapped not in facets:
                    facets.append(mapped)
            if facets:
                warnings.append(f"{label}: facets backfilled from the learning object's blueprint")

        rubric = _validated_rubric(entry.grading_rubric)
        if rubric is None:
            rubric = json.loads(json.dumps(_DEFAULT_RUBRIC))
            warnings.append(f"{label}: rubric failed validation; plain correctness rubric used")

        # Weights arrive as pair lists (strict output schemas cannot express
        # free-form maps); fold them back into the service's mapping shape.
        weight_map = {w.facet_id: w.weight for w in entry.evidence_weights if w.facet_id}
        criterion_map = {
            c.criterion_id: {w.facet_id: w.weight for w in c.weights if w.facet_id}
            for c in entry.criterion_facet_weights
            if c.criterion_id
        }
        weights = _normalized_weights(weight_map, facets, canonical) if facets else {}
        criterion_weights: dict[str, dict[str, float]] = {}
        if facets:
            for criterion in rubric["criteria"]:
                raw = criterion_map.get(criterion["id"]) or {}
                criterion_weights[criterion["id"]] = _normalized_weights(raw, facets, canonical)

        capability: str | None = None
        features: dict[str, Any] | None = None
        raw_capability = (entry.capability or "").strip()
        if raw_capability:
            mapped_capability = map_capability(repository, raw_capability)
            if mapped_capability == LEGACY_UNMAPPED:
                warnings.append(
                    f"{label}: capability {raw_capability!r} is outside the closed vocabulary"
                )
            else:
                capability = mapped_capability
        else:
            warnings.append(f"{label}: no capability classified")
        if capability is not None:
            candidate = (
                entry.task_features.model_dump(exclude_none=True)
                if entry.task_features is not None
                else {}
            )
            if not candidate:
                warnings.append(f"{label}: no task_features returned; depth rung incomplete")
            else:
                ok, errors = validate_task_features(repository, schema_version_id, candidate)
                if not ok:
                    warnings.append(f"{label}: task_features rejected ({'; '.join(errors)})")
                elif capability == "coordination" and candidate.get("span") != "whole_task":
                    warnings.append(
                        f"{label}: coordination requires span=whole_task; depth left unstamped"
                    )
                    capability = None
                else:
                    features = candidate

        hints = [hint.strip() for hint in entry.hints if hint.strip()][:MAX_HINTS]
        difficulty = _clamp01(entry.difficulty)
        item_id = f"pi_exercise_{new_ulid().lower()}"
        payload: dict[str, Any] = {
            "id": item_id,
            "learning_object_id": lo_id,
            "practice_mode": entry.practice_mode.strip() or "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "prompt": statement,
            "expected_answer": expected,
            "grading_rubric": rubric,
            "evidence_facets": facets,
            "evidence_weights": weights,
            "criterion_facet_weights": criterion_weights,
            "hints": hints,
            "provenance": {"origin": "canonical_extract", "source_refs": source_refs},
            "created_at": now,
            "updated_at": now,
        }
        if difficulty is not None:
            payload["difficulty"] = difficulty
            payload["difficulty_source"] = "llm_estimate"
        for field_name in ("retrieval_demand", "transfer_distance", "scaffold_level"):
            value = _clamp01(getattr(entry, field_name))
            if value is not None:
                payload[field_name] = value
        if capability is not None:
            payload["capability"] = capability
        if features is not None:
            payload["task_features"] = features
            payload["task_feature_schema"] = TASK_FEATURE_SCHEMA_SLUG

        upsert_practice_item(root, payload, clock=clock)
        existing_prompts[_normalize(statement)] = item_id
        try:
            repository.append_interaction_event(
                kind="learner_item_authored",
                origin="learner",
                subject_type="practice_item",
                subject_id=item_id,
                payload_json=json.dumps(
                    {
                        "learning_object_id": lo_id,
                        "mechanism": "reader_exercise_import",
                        "extraction_id": extraction_id,
                    },
                    sort_keys=True,
                ),
                clock=clock,
            )
        except Exception:  # noqa: BLE001 - provenance trail is best-effort
            pass

        summaries.append(
            {
                "practice_item_id": item_id,
                "title": entry.title.strip(),
                "prompt": statement,
                "learning_object_id": lo_id,
                "learning_object_title": lo.title,
                "practice_mode": payload["practice_mode"],
                "capability": capability or "",
                "task_features": features or {},
                "evidence_facets": facets,
                "difficulty": difficulty,
                "hint_count": len(hints),
                "classification_reason": entry.classification_reason.strip(),
            }
        )

    if not summaries and skipped:
        reasons = "; ".join(str(row["reason"]) for row in skipped)
        raise ExerciseAuthoringError(f"no exercise could be authored: {reasons}")

    return {
        "extraction_id": extraction_id,
        "items": summaries,
        "skipped": skipped,
        "warnings": warnings,
        "anchor_status": str(translation.get("status") or "exact"),
    }
