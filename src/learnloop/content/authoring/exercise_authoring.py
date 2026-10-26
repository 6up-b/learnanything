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

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Any, Mapping

from learnloop.ai.errors import AIOutputTruncated
from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.content.authoring.ai_contracts import (
    ExerciseAuthoring,
    ExerciseAuthoringContext,
    exercise_authoring_prompt,
)
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.ir import selection_region
from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span
from learnloop.substrate.activity_patterns import (
    LEGACY_UNMAPPED,
    ensure_builtin_task_feature_schema,
    ensure_capability_alias_registry,
    map_capability,
    validate_task_features,
)
from learnloop.reader.annotations import translate_selection
from learnloop.curriculum.depth_rungs import TASK_FEATURE_SCHEMA_SLUG
from learnloop.content.sources.math_text import contains_unicode_math, unicode_math_to_latex
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, learning_object_facet_union
from learnloop.vault.required_method import (
    learning_object_method_targets,
    method_targets,
    normalize_required_method,
)
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


#: Receipts of the one-time statement judgment on a Reader import.
READER_IMPORT_OWNER_KIND = "reader_exercise_import"


def _configured_method_judge(vault: LoadedVault) -> Any:
    """The one-time statement judge from configuration, resolved on first use."""

    from learnloop.content.proposals.method_statement_judge import LazyStatementJudge, resolve_statement_judge

    price = vault.config.source_service.llm_price_per_million
    return LazyStatementJudge(lambda: resolve_statement_judge(vault, price_per_million=price))


class ExerciseAuthoringError(ValueError):
    """Domain error for the reader exercise-import producer."""


def request_exercise_authoring(
    client: StructuredTransport, context: ExerciseAuthoringContext, *,
    admit: Callable[[str, type[ExerciseAuthoring]], AbstractContextManager[Any]] | None = None,
) -> ExerciseAuthoring:
    """Author selected exercises through the shared transport.

    ``admit(prompt, result_model)``, when given, admits the request under the
    caller's spend caps before it is sent (canonical sources' imports), and
    its ``after_truncation()`` (when present) decides the one truncation retry
    at double the budget; None keeps the Reader's import unchanged.
    """

    prompt = exercise_authoring_prompt(context)
    if admit is None:
        return execute_structured_operation(
            client,
            purpose="exercise_authoring",
            prompt=prompt,
            result_model=ExerciseAuthoring,
        )
    while True:
        try:
            with admit(prompt, ExerciseAuthoring):
                return execute_structured_operation(
                    client,
                    purpose="exercise_authoring",
                    prompt=prompt,
                    result_model=ExerciseAuthoring,
                )
        except AIOutputTruncated:
            # Main's shared output-budget policy: a truncated draft is never
            # accepted; the admission logs it and allows one retry at double
            # the budget (admitted and reserved again), else it fails.
            retry = getattr(admit, "after_truncation", None)
            if retry is None or not retry():
                raise


def _normalize(text: str) -> str:
    return " ".join((text or "").split())


def _clamp01(value: Any) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def _anchor_range(selection_text: str, statement: str) -> tuple[int, int] | None:
    """Where the model's echoed statement sits in the learner's selection, as
    a verbatim slice (whitespace-tolerant, same idea as annotation quote
    relocation); None for a paraphrase."""

    tokens = _normalize(statement).split()
    if not tokens:
        return None
    pattern = r"\s+".join(re.escape(token) for token in tokens)
    match = re.search(pattern, selection_text)
    if match is None:
        return None
    return match.start(), match.end()


def _anchor_statement(selection_text: str, statement: str) -> str | None:
    """Re-anchor the model's echoed statement as a verbatim slice of the
    learner's selection. Returns the source-owned slice, or None for a paraphrase."""

    found = _anchor_range(selection_text, statement)
    return None if found is None else selection_text[found[0] : found[1]]


def _owned_spans(part_ranges: Sequence[tuple[str, int, int]] | None,
                 ranges: Sequence[tuple[int, int] | None], index: int) -> set[str]:
    """Reader CA1 (Codex re-review F9, final verify F9): the blocks one item
    of a split selection is printed from, when they are its alone.

    An item's blocks are the parts its statement's slice overlaps. They are
    its own only when no other item of the split overlaps any of them: a
    block holding two exercises belongs to neither, and an item with one
    such block owns none (its crop would show the other exercise, or only
    part of its own). Empty when ownership can't be read: a selection-level
    edit replaced the text, or a sibling's statement could not be anchored
    (it may sit in any block)."""

    if part_ranges is None or any(found is None for found in ranges):
        return set()

    def blocks(found: tuple[int, int]) -> set[str]:
        start, end = found
        return {span for span, part_start, part_end in part_ranges if part_start < end and start < part_end}

    mine = blocks(ranges[index])
    others = set().union(*(blocks(found) for other, found in enumerate(ranges) if other != index))
    return set() if mine & others else mine


def _item_refs(source_refs: Sequence[Mapping[str, Any]], span_ids: Sequence[str], *,
               owned: set[str]) -> list[dict[str, Any]]:
    """One item's copy of the selection's refs. Every block stays a ref (the
    selection is the item's provenance), and each ref says whether that block
    is this item's own (``owned``), so its print never crops another item's
    exercise (Codex re-review F9). Every import records it, split or not: a
    Reader import without it was written before ownership was kept, and its
    crop is not shown as its own (final verify F9)."""

    refs = [json.loads(json.dumps(ref)) for ref in source_refs]
    for ref, span_id in zip(refs, span_ids):
        ref["owned"] = span_id in owned
    return refs


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
        out = {
            "id": lo.id,
            "title": lo.title,
            "summary": (lo.summary or "")[:280],
            "facets": facets,
        }
        # Method-explicit items (owner rule 2026-10-13): absent unless the
        # object's target is a method, so other entries are unchanged.
        targets = learning_object_method_targets(vault, lo.id, [facet["id"] for facet in facets])
        if targets:
            out["required_method_targets"] = targets
        return out

    active = [lo for lo in vault.learning_objects.values() if lo.status == "active"]
    active.sort(key=lambda lo: (lo.id != hint, lo.id))
    return [entry(lo) for lo in active[:MAX_CATALOG_OBJECTS]]


def _validated_rubric(payload: Any) -> dict[str, Any] | None:
    """Admit the model rubric only when the arithmetic holds (points sum to
    a positive integer, unique non-empty criteria); otherwise the caller falls
    back to the plain correctness rubric."""

    if payload is None or not payload.criteria:
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
            {
                "id": criterion_id,
                "points": criterion.points,
                "description": description,
                "tier": criterion.tier,
                "measurement_status": criterion.measurement_status,
            }
        )
    if len({criterion["id"] for criterion in criteria}) != len(criteria):
        return None
    max_points = int(round(total))
    if max_points < 1 or abs(total - max_points) > 1e-6:
        return None
    return {"max_points": max_points, "criteria": criteria}


def _normalized_weights(
    raw: Mapping[str, float], facets: list[str], canonical: Any
) -> dict[str, float]:
    """Normalize only facet links the author actually asserted.

    Missing links are abstentions, not permission to spread weight over the
    available vocabulary. In particular, an empty map remains empty and a
    partial map remains partial after normalization.
    """

    weights: dict[str, float] = {}
    for key, value in (raw or {}).items():
        facet = canonical(key)
        if facet in facets and float(value) > 0:
            weights[facet] = weights.get(facet, 0.0) + float(value)
    if not weights:
        return {}
    total = sum(weights.values())
    return {facet: round(value / total, 4) for facet, value in weights.items()}


def _uniform_criterion_smear(
    criterion_weights: Mapping[str, Mapping[str, float]],
) -> bool:
    """Whether multiple criteria received the same multi-facet distribution."""

    distributions = [
        tuple(sorted((facet, round(float(weight), 6)) for facet, weight in weights.items()))
        for weights in criterion_weights.values()
        if weights
    ]
    return (
        len(distributions) > 1
        and len(distributions[0]) > 1
        and len(set(distributions)) == 1
    )


@dataclass
class AuthoredDraft:
    """One authored exercise, validated and ready to write (nothing written yet)."""

    payload: dict[str, Any]
    summary: dict[str, Any]
    label: str
    statement: str
    #: ``authored`` when the author named facets; ``lo_fallback`` when the
    #: import gave the item its LO's whole facet union (§8.1).
    facet_basis: str
    cited_quote: str = ""


@dataclass
class AuthoredBatch:
    """``author_exercises``' result: drafts plus today's skipped/warnings report."""

    extraction_id: str
    span_ids: list[str]
    exercise_text: str
    drafts: list[AuthoredDraft] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    anchor_status: str = "exact"


def author_exercises(
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
    book_solution: Mapping[str, Any] | None = None,
    admit: Callable[[str, type[ExerciseAuthoring]], AbstractContextManager[Any]] | None = None,
    method_judge: Any = None,
    method_judge_owner: tuple[str, str] | None = None,
) -> AuthoredBatch:
    """Author the selected exercise(s) into validated drafts. Writes nothing.

    The split of ``import_exercises`` (canonical sources S1, §7.2): a check
    can run between authoring and writing. The drafts keep today's rules: the
    verbatim re-anchored stem, the facet registry, rubric arithmetic, the
    capability vocabulary and the task-feature schema. ``book_solution`` (the
    verifier ladder's first rung) is passed to the author so the key can be
    written from the source.

    ``method_judge`` decides, once, whether a statement requires the method
    its author proposed (redesign 2026-10-14): a resolved judge, a
    ``LazyStatementJudge``, or None (the default) to resolve one from
    configuration on first use (``ai.routing.rubric_phrasing_judge``: the
    Decider, else the LLM judge; a metered LLM judge is priced at
    ``source_service.llm_price_per_million``). Its receipts are owned by
    ``method_judge_owner`` (default: the Reader import of ``extraction_id``).
    """

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
    part_spans: list[str] = []
    consumed: dict[str, int] = {}
    transliterated = False
    for segment in segments:
        span = str(segment.get("span_id") or "")
        part_spans.append(span)
        queue = edited_quotes.get(span) or []
        index = consumed.get(span, 0)
        if index < len(queue):
            # Learner-authority text is never rewritten — not even Unicode math.
            parts.append(queue[index])
            consumed[span] = index + 1
        else:
            part = str(segment["exact_quote"])
            # Anchored slices normally carry the extraction's own LaTeX; a
            # pypdf-fallback block's text IS rendered Unicode math, and that
            # must not become a practice surface as ``𝜆``. Deterministic and
            # lossy only where the text already was (flattened scripts stay
            # flattened); surfaced as a warning below.
            if contains_unicode_math(part):
                part, changed = unicode_math_to_latex(part)
                transliterated = transliterated or changed
            parts.append(part)
    exercise_text = "\n\n".join(parts)
    # Each part's place in the joined text, so an item split from the
    # selection knows which blocks are its own (Codex re-review F9).
    part_ranges: list[tuple[str, int, int]] | None = []
    offset = 0
    for span, part in zip(part_spans, parts):
        part_ranges.append((span, offset, offset + len(part)))
        offset += len(part) + 2

    # The capture editor combines a multi-block selection into ONE passage; a
    # selection-level edit overrides the whole surface (per-node edits above
    # remain for callers that send them). Anchors stay extraction-owned.
    edited_text = str(
        raw_selection.get("edited_text") or raw_selection.get("editedText") or ""
    ).strip()
    if edited_text:
        # Learner-authority override — used verbatim, Unicode and all.
        exercise_text = edited_text
        transliterated = False
        part_ranges = None

    span_ids: list[str] = []
    for segment in segments:
        span_id = str(segment.get("span_id") or "")
        if span_id and span_id not in span_ids:
            span_ids.append(span_id)

    vault = load_vault(root)
    judge = method_judge if method_judge is not None else _configured_method_judge(vault)
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
        book_solution=dict(book_solution or {}),
    )
    result = request_exercise_authoring(client, context, admit=admit)

    warnings = [str(warning) for warning in result.warnings if str(warning).strip()]
    if transliterated:
        warnings.insert(0, "converted Unicode math in the exercise text to LaTeX — check sub/superscripts")
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
    # Reader CA1 (ux_reader_compare_ask_v1 §12.4): a region selection (a
    # learner-drawn box inside one block, ``ReaderSelection.region``) is kept
    # on that block's ref, so the problem as printed shows the learner's crop.
    raw_region = raw_selection.get("region")
    for span_id, (page, box) in selection_region(dict(raw_region) if isinstance(raw_region, Mapping) else None,
                                                 span_ids).items():
        for ref in source_refs:
            if ref["locator"] == format_block_span(extraction_id, span_id):
                ref["region"] = {"page": page, "bbox": list(box)}

    existing_prompts = {
        _normalize(item.prompt): item.id
        for item in vault.practice_items.values()
        if item.status == "active"
    }
    now = utc_now_iso(clock)
    batch = AuthoredBatch(extraction_id=extraction_id, span_ids=span_ids, exercise_text=exercise_text,
                          warnings=warnings, anchor_status=str(translation.get("status") or "exact"))
    skipped = batch.skipped

    split = len(result.items) > 1
    # Every item's slice, skipped ones too: a sibling's place decides which
    # blocks are an item's alone (final verify F9).
    anchored = [_anchor_range(exercise_text, entry.statement_md) for entry in result.items]
    for ordinal, entry in enumerate(result.items, start=1):
        label = entry.title.strip() or f"exercise {ordinal}"

        found = anchored[ordinal - 1]
        statement = None if found is None else exercise_text[found[0] : found[1]]
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
        facet_basis = "authored"
        if not facets:
            facet_basis = "lo_fallback"
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
                if not raw:
                    continue
                normalized = _normalized_weights(raw, facets, canonical)
                if normalized:
                    criterion_weights[criterion["id"]] = normalized
        if _uniform_criterion_smear(criterion_weights):
            warnings.append(
                f"{label}: identical multi-facet weights were applied across criteria; "
                "flagged for measurement re-audit"
            )

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
            "trace_contract": (
                entry.trace_contract.model_dump(mode="json", exclude_none=True)
                if entry.trace_contract is not None
                else None
            ),
            "hints": hints,
            "provenance": {"origin": "canonical_extract", "source_refs": _item_refs(
                source_refs, span_ids,
                owned=_owned_spans(part_ranges, anchored, ordinal - 1) if split else set(span_ids))},
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
        if entry.required_method is not None:
            # The book's statement is never rewritten (redesign 2026-10-14): a
            # required method on a target that is not that method is dropped,
            # and whether the statement requires it is decided ONCE, here, by
            # the ledgered judgment (the Decider, else the LLM judge); without
            # one the requirement is dropped. Grading never re-reads the text.
            from learnloop.content.proposals.method_statement_judge import source_judge

            payload["required_method"] = entry.required_method.model_dump(mode="json")
            decide = source_judge(
                judge, repository, subject_id=item_id,
                owner=method_judge_owner or (READER_IMPORT_OWNER_KIND, extraction_id), clock=clock,
                log=lambda reason, label=label: warnings.append(f"{label}: required method not judged: {reason}"),
            )
            for note in normalize_required_method(
                payload,
                method_targets(vault, learning_object_id=lo_id, facet_ids=facets, capability=capability),
                source_statement=True,
                judge_source=decide,
            ):
                if note.startswith("required_method:dropped"):
                    warnings.append(f"{label}: {note}")
        if features is not None:
            payload["task_features"] = features
            payload["task_feature_schema"] = TASK_FEATURE_SCHEMA_SLUG

        existing_prompts[_normalize(statement)] = item_id
        batch.drafts.append(AuthoredDraft(
            payload=payload,
            summary={
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
            },
            label=label,
            statement=statement,
            facet_basis=facet_basis,
            cited_quote=str(getattr(entry, "cited_quote", "") or "").strip(),
        ))
    return batch


def write_draft(root: Path, repository: Repository, draft: AuthoredDraft, *, extraction_id: str,
                clock: Clock | None = None, mechanism: str = "reader_exercise_import",
                extra_payload: Mapping[str, Any] | None = None) -> str:
    """Write one draft as a vault item and mark it with ``learner_item_authored``."""

    payload = {**draft.payload, **dict(extra_payload or {})}
    upsert_practice_item(root, payload, clock=clock)
    try:
        repository.append_interaction_event(
            kind="learner_item_authored",
            origin="learner",
            subject_type="practice_item",
            subject_id=payload["id"],
            payload_json=json.dumps(
                {
                    "learning_object_id": payload["learning_object_id"],
                    "mechanism": mechanism,
                    "extraction_id": extraction_id,
                },
                sort_keys=True,
            ),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - provenance trail is best-effort
        pass
    return str(payload["id"])


def write_exercises(root: Path, repository: Repository, batch: AuthoredBatch, *,
                    clock: Clock | None = None) -> dict[str, Any]:
    """Write every draft of ``batch`` (the Reader import's write step)."""

    summaries: list[dict[str, Any]] = []
    for draft in batch.drafts:
        write_draft(root, repository, draft, extraction_id=batch.extraction_id, clock=clock)
        summaries.append(draft.summary)
    if not summaries and batch.skipped:
        reasons = "; ".join(str(row["reason"]) for row in batch.skipped)
        raise ExerciseAuthoringError(f"no exercise could be authored: {reasons}")
    return {
        "extraction_id": batch.extraction_id,
        "items": summaries,
        "skipped": batch.skipped,
        "warnings": batch.warnings,
        "anchor_status": batch.anchor_status,
    }


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
    method_judge: Any = None,
) -> dict[str, Any]:
    """Author the learner's selected exercise(s) into schedulable PracticeItems.

    Returns ``{items, skipped, warnings, anchor_status}`` where ``items`` are
    written-card summaries and ``skipped`` carries per-exercise reasons
    (paraphrased statement, unknown learning object, duplicate, ...). Raises
    :class:`ExerciseAuthoringError` when nothing can proceed at all.

    The composition of :func:`author_exercises` and :func:`write_exercises`,
    so the item the Reader's path writes is unchanged (parity test G5).
    """

    batch = author_exercises(
        root, repository, client, extraction_id=extraction_id, raw_selection=raw_selection,
        render_view_id=render_view_id, source_id=source_id, revision_id=revision_id,
        learning_object_hint=learning_object_hint, clock=clock, method_judge=method_judge,
    )
    return write_exercises(root, repository, batch, clock=clock)
