"""Personalized, source-grounded guidance for the Reader.

Question *placement* comes only from the reviewed TaskBlueprint ledger.  There is
no hot-path ``ask_now`` planner or density policy: local learner state may explain
why a reviewed check matters and rank restorative passages, but it never invents
an extra boundary question.  ``reader.present_question`` remains the only path
that opens an instructional administration.

This keeps the P3 owner-placement contract intact while still allowing the Guide
to react to an active goal and unresolved misunderstandings.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from typing import Any, Iterable

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault, SourceRef, learning_object_facet_union


_SPAN_LOCATOR_RE = re.compile(r"^span:([^/]+)/(.+)$")
_TIME_LOCATOR_RE = re.compile(r"^t=(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?$")
_FURNITURE_TYPES = {"PageHeader", "PageFooter", "TableOfContents"}
_PATTERN_PHASES = {
    "pretest_prime": "before_section",
    "self_explanation": "after_section",
    "example_comparison": "after_section",
    "setup_only": "after_section",
}
_READING_PHASES = {"before_section", "during_section", "after_section"}


def _extras(value: Any) -> dict[str, Any]:
    extra = getattr(value, "model_extra", None)
    return extra if isinstance(extra, dict) else {}


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def _section_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _normalize_text(value)).strip("-")


def _canonical_note_ids(vault: LoadedVault, artifact: dict[str, Any]) -> set[str]:
    """Resolve legacy note-id provenance to the source-library artifact."""

    artifact_uri = str(artifact.get("canonical_uri") or "")
    note_ids: set[str] = set()
    for note in vault.notes.values():
        canonical = _extras(note).get("canonical_source")
        canonical = canonical if isinstance(canonical, dict) else {}
        note_uri = str(canonical.get("canonical_uri") or canonical.get("original_uri") or "")
        if artifact_uri and note_uri == artifact_uri:
            note_ids.add(note.id)
    return note_ids


def _ref_matches_source(ref: SourceRef, source_id: str, note_ids: set[str]) -> bool:
    extra = _extras(ref)
    return (
        str(extra.get("source_id") or "") == source_id
        or (ref.ref_type == "canonical_source" and ref.ref_id == source_id)
        or ref.ref_id in note_ids
    )


def _span_for_ref(ref: SourceRef, *, source_id: str, extraction_id: str,
                  note_ids: set[str], blocks: list[Any]) -> str | None:
    if not _ref_matches_source(ref, source_id, note_ids):
        return None

    extra = _extras(ref)
    ref_extraction = str(extra.get("extraction_id") or "")
    locator = str(ref.locator or "")
    match = _SPAN_LOCATOR_RE.match(locator)
    if match is not None and (match.group(1) == extraction_id or ref_extraction == extraction_id):
        span_id = match.group(2)
        if any(block.span_id == span_id for block in blocks):
            return span_id

    # Caption IR keeps the cue locator on extractor_block_id. Match a cited
    # video segment to the first overlapping cue so transcript guidance can use
    # the same goal/latent ranking as text and PDF sources.
    time_match = _TIME_LOCATOR_RE.match(locator)
    if time_match is not None:
        ref_start = float(time_match.group(1))
        ref_end = float(time_match.group(2)) if time_match.group(2) is not None else ref_start
        timed: list[tuple[float, str]] = []
        for block in blocks:
            cue_match = _TIME_LOCATOR_RE.match(str(block.extractor_block_id or ""))
            if cue_match is None:
                continue
            cue_start = float(cue_match.group(1))
            cue_end = float(cue_match.group(2)) if cue_match.group(2) is not None else cue_start
            if cue_end >= ref_start and cue_start <= ref_end:
                timed.append((abs(cue_start - ref_start), block.span_id))
        if timed:
            return min(timed)[1]

    # Older canonical refs carry a quote and a heading-path locator rather than
    # an extraction span.  An unambiguous quote is the safest compatibility path.
    quote = _normalize_text(ref.quote)
    if len(quote) >= 8:
        matches = [block.span_id for block in blocks if quote in _normalize_text(block.text)]
        if len(matches) == 1:
            return matches[0]
    return None


def goal_for_item(vault: LoadedVault, learning_object: Any, item: Any) -> Any | None:
    lo_facets = set(learning_object_facet_union(learning_object))
    item_facets = {str(facet) for facet in getattr(item, "evidence_facets", [])}
    candidates = []
    for goal in vault.goals:
        if goal.status != "active":
            continue
        concepts = set(goal.facet_scope.concepts)
        facets = set(goal.facet_scope.facets)
        if learning_object.concept in concepts or bool(facets & (lo_facets | item_facets)):
            candidates.append(goal)
    return max(candidates, key=lambda goal: (goal.priority, goal.id), default=None)


def _learner_signal(repository: Repository, learning_object_id: str,
                    *, goal_match: bool) -> tuple[float, str, str]:
    """Return a local ranking boost and a learner-facing, non-numeric reason."""

    errors = repository.active_errors_by_learning_object(learning_object_id)
    if errors:
        strongest = max(errors, key=lambda error: (error.severity, error.created_at))
        detail = strongest.misconception_statement or strongest.error_type.replace("_", " ")
        return 9.0 + strongest.severity, "recent_misunderstanding", f"Revisit this to resolve: {detail}."

    mastery = repository.mastery_state(learning_object_id)
    if mastery is None or mastery.evidence_count == 0:
        suffix = " for your active goal" if goal_match else " before building on it"
        return 4.0, "new_material", f"This is a useful foundation{suffix}."

    # Ranking only: uncertainty and lower current success probability raise the
    # value of a check.  The numeric posterior never leaves this service.
    uncertainty = min(2.5, max(0.0, mastery.logit_variance))
    needs_support = 1.0 / (1.0 + math.exp(max(-12.0, min(12.0, mastery.logit_mean))))
    boost = uncertainty + 2.0 * needs_support
    if uncertainty >= 0.8:
        return boost, "uncertain", "A quick second pass can firm up an uncertain connection."
    if goal_match:
        return boost, "goal_frontier", "This connection matters to your active goal."
    return boost, "source_relevance", "This passage carries a key idea from the section."


def _refs_for(vault: LoadedVault, item: Any, learning_object: Any) -> Iterable[SourceRef]:
    yield from item.provenance.source_refs
    yield from learning_object.provenance.source_refs
    for facet_id in set(getattr(item, "evidence_facets", [])) | set(learning_object_facet_union(learning_object)):
        facet = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
        if facet is not None:
            yield from facet.provenance.source_refs


def _placement_item_id(placement: dict[str, Any], blueprint_spec: dict[str, Any]) -> str | None:
    """Resolve the explicitly placed surface, with a legacy blueprint fallback.

    Early P2 fixtures recorded only section + pattern.  Their reviewed blueprint
    still pins familiar exemplars, so the first reviewed familiar exemplar is a
    deterministic compatibility surface.  We never search or rank arbitrary
    source questions here.
    """

    for key in (
        "practice_item_id", "practice_item_ref", "question_item_id",
        "surface_ref", "exemplar_ref",
    ):
        value = placement.get(key)
        if value:
            return str(value)
    for exemplar in blueprint_spec.get("exemplars") or []:
        if exemplar.get("held_out") or float(exemplar.get("held_out_weight", 0.0) or 0.0) > 0:
            continue
        value = exemplar.get("exemplar_ref")
        if value:
            return str(value)
    return None


def _placement_phase(placement: dict[str, Any]) -> tuple[str, str | None]:
    pattern = str(placement.get("pattern") or "").strip() or None
    raw_phase = str(placement.get("reading_phase") or placement.get("phase") or "").strip()
    if raw_phase in _READING_PHASES:
        return raw_phase, pattern
    effective_pattern = pattern or (raw_phase if raw_phase in _PATTERN_PHASES else None)
    return _PATTERN_PHASES.get(effective_pattern or "", "after_section"), effective_pattern


def _placement_section(
    placement: dict[str, Any],
    *,
    blueprint_unit_id: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    by_id = {str(section["id"]): section for section in sections}
    by_span = {
        str(section["end_span_id"]): section
        for section in sections
    }
    for key in ("boundary_span_id", "span_id"):
        value = str(placement.get(key) or "")
        if value in by_span:
            return by_span[value]

    target = str(
        placement.get("section_id")
        or placement.get("section")
        or placement.get("unit_id")
        or blueprint_unit_id
        or ""
    )
    if target in by_id:
        return by_id[target]
    target_key = _section_key(target)
    matches = [
        section for section in sections
        if target_key and target_key in {_section_key(str(section["id"])), _section_key(str(section["label"]))}
    ]
    if len(matches) == 1:
        return matches[0]
    # Legacy P2 placement artifacts used a chapter-local section slug.  A
    # one-section extraction is unambiguous even when that slug predates IR ids.
    return sections[0] if len(sections) == 1 else None


def _placement_suppressed(repository: Repository, placement_event_id: str) -> bool:
    """Honor the learner's durable "don't bring this back" control."""

    events = repository.reader_interaction_events(
        kind="reader_question_control",
        subject_id=placement_event_id,
        subject_type="reader_question_placement",
    )
    return any(
        isinstance(event.get("payload"), dict)
        and event["payload"].get("control") == "dont_bring_this_back"
        for event in events
    )


def extraction_sections(ir: Any) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    """Derive the Reader's guide sections from one extraction's IR.

    Returns ``(section_rows, block_by_span, span_to_section)``. Shared by the
    guide plan and the quick-check producer so both agree on what one
    "section" is (readable, non-furniture spans per unit)."""

    blocks = sorted(ir.blocks, key=lambda block: block.ordinal)
    block_by_span = {block.span_id: block for block in blocks}
    span_to_section: dict[str, str] = {}
    section_rows: list[dict[str, Any]] = []

    units = sorted(ir.units, key=lambda unit: unit.ordinal)
    if not units:
        # Valid but unusual IRs may omit units.  Treat the extraction as one
        # section so the Reader still has a coherent progress boundary.
        units = [type("ReaderUnit", (), {
            "unit_id": "whole-source", "label": "This source", "ordinal": 0,
            "span_ids": [block.span_id for block in blocks],
        })()]

    for unit in units:
        readable = [
            span_id for span_id in unit.span_ids
            if span_id in block_by_span and block_by_span[span_id].block_type not in _FURNITURE_TYPES
        ]
        if not readable:
            continue
        for span_id in readable:
            span_to_section[span_id] = unit.unit_id
        section_rows.append({
            "id": unit.unit_id,
            "label": unit.label or "Untitled section",
            "start_span_id": readable[0],
            "end_span_id": readable[-1],
            "span_ids": readable,
        })
    return section_rows, block_by_span, span_to_section


def build_guide_plan(vault: LoadedVault, repository: Repository, *, extraction_id: str) -> dict[str, Any]:
    """Build section checks and suggested passages for one extraction.

    Owner-reviewed placement artifacts become questions first; sections without
    one fall back to the newest AI-authored quick check (``auto_authored``, row
    in ``reader_authored_questions``) — the two sources never blend within a
    section.  Source-grounded Practice Items still rank passages worth
    revisiting, and local learner state supplies a plain-language reason
    without leaking posterior values.
    """

    run = repository.get_extraction_run(extraction_id)
    if run is None:
        raise ValueError(f"unknown extraction: {extraction_id!r}")
    revision = repository.get_source_revision(run["revision_id"])
    source_id = str((revision or {}).get("source_id") or "")
    artifact = repository.get_source_artifact(source_id) or {}
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ValueError(f"extraction has no IR: {extraction_id!r}")

    blocks = sorted(ir.blocks, key=lambda block: block.ordinal)
    note_ids = _canonical_note_ids(vault, artifact)

    passages_by_section: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    question_by_section: dict[str, dict[str, Any]] = {}
    context_candidates: list[dict[str, Any]] = []

    section_rows, block_by_span, span_to_section = extraction_sections(ir)

    for item in vault.practice_items.values():
        if getattr(item, "status", "active") != "active":
            continue
        learning_object = vault.learning_objects.get(item.learning_object_id)
        if learning_object is None or learning_object.status != "active":
            continue

        ref_spans: list[str] = []
        for ref in _refs_for(vault, item, learning_object):
            span_id = _span_for_ref(
                ref, source_id=source_id, extraction_id=extraction_id,
                note_ids=note_ids, blocks=blocks,
            )
            if span_id is not None and span_id not in ref_spans:
                ref_spans.append(span_id)
        if not ref_spans:
            continue

        goal = goal_for_item(vault, learning_object, item)
        latent_boost, signal, passage_reason = _learner_signal(
            repository, learning_object.id, goal_match=goal is not None,
        )
        goal_boost = 4.0 * float(goal.priority) if goal is not None else 0.0
        score = latent_boost + goal_boost
        if item.provenance.source_refs:
            score += 1.0

        golden_run = repository.golden_path_run_for_goal(goal.id) if goal is not None else None
        context_candidates.append({
            "goal_id": goal.id if goal is not None else None,
            "goal_title": goal.title if goal is not None else None,
            "golden_path_run_id": golden_run.get("id") if golden_run else None,
            "target_contract_version_id": golden_run.get("goal_contract_version_id") if golden_run else None,
            "score": score,
        })
        section_ids = {span_to_section[span_id] for span_id in ref_spans if span_id in span_to_section}
        for section_id in section_ids:
            for span_id in ref_spans:
                if span_to_section.get(span_id) != section_id:
                    continue
                block = block_by_span[span_id]
                existing = passages_by_section[section_id].get(span_id)
                passage = {
                    "span_id": span_id,
                    "quote": " ".join(block.text.split())[:260],
                    "reason": passage_reason,
                    "learning_object_id": learning_object.id,
                    "learning_object_title": learning_object.title,
                    "learner_signal": signal,
                    "score": score,
                }
                if existing is None or passage["score"] > existing["score"]:
                    passages_by_section[section_id][span_id] = passage

    # P3 §5.1 / P2 §7.6: read static, reviewed placements.  Active-goal runs are
    # used only to recover a pinned blueprint whose semantic source revision is
    # one of this extraction's stable source identifiers.
    source_revs = {
        str(run.get("revision_id") or ""),
        str((revision or {}).get("id") or ""),
        str((revision or {}).get("asset_hash") or ""),
        source_id,
    }
    unit_ids = {str(section["id"]) for section in section_rows}
    pinned_versions: list[str] = []
    goal_by_blueprint: dict[str, Any] = {}
    for goal in vault.goals:
        if goal.status != "active":
            continue
        golden_run = repository.golden_path_run_for_goal(goal.id)
        if not golden_run:
            continue
        if (
            str(golden_run.get("source_rev") or "") in source_revs
            and str(golden_run.get("unit_id") or "") in unit_ids
        ):
            version_id = str(golden_run.get("blueprint_version_id") or "")
            if version_id:
                pinned_versions.append(version_id)
                goal_by_blueprint[version_id] = goal

    placement_rows = repository.reviewed_reading_question_placements(
        source_revs=sorted(source_revs),
        unit_ids=sorted(unit_ids),
        blueprint_version_ids=pinned_versions,
    )
    for row in placement_rows:
        placement_event_id = str(row.get("placement_event_id") or "")
        if not placement_event_id or _placement_suppressed(repository, placement_event_id):
            continue
        try:
            placement = json.loads(row.get("placement_json") or "{}")
            blueprint_spec = json.loads(row.get("blueprint_spec_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(placement, dict) or not isinstance(blueprint_spec, dict):
            continue
        section = _placement_section(
            placement,
            blueprint_unit_id=str(row.get("unit_id") or ""),
            sections=section_rows,
        )
        if section is None or section["id"] in question_by_section:
            continue
        item_id = _placement_item_id(placement, blueprint_spec)
        item = vault.practice_items.get(item_id or "")
        if item is None or getattr(item, "status", "active") != "active":
            continue
        learning_object = vault.learning_objects.get(item.learning_object_id)
        if learning_object is None or learning_object.status != "active":
            continue

        placed_goal = goal_by_blueprint.get(str(row.get("blueprint_version_id") or ""))
        goal = placed_goal or goal_for_item(vault, learning_object, item)
        latent_boost, signal, learner_reason = _learner_signal(
            repository, learning_object.id, goal_match=goal is not None,
        )
        golden_run = repository.golden_path_run_for_goal(goal.id) if goal is not None else None
        reading_phase, pattern = _placement_phase(placement)
        if signal == "recent_misunderstanding":
            question_reason = learner_reason
            if goal is not None:
                question_reason += f" It also supports “{goal.title}”."
        elif goal is not None:
            question_reason = f"A quick check to connect this section to “{goal.title}”."
        else:
            question_reason = learner_reason
        question_by_section[section["id"]] = {
            "practice_item_id": item.id,
            "learning_object_id": learning_object.id,
            "learning_object_title": learning_object.title,
            "prompt": item.prompt,
            "reason": question_reason,
            "learner_signal": signal,
            "goal_id": goal.id if goal is not None else None,
            "goal_title": goal.title if goal is not None else None,
            "golden_path_run_id": golden_run.get("id") if golden_run else None,
            "target_contract_version_id": golden_run.get("goal_contract_version_id") if golden_run else None,
            "reading_phase": reading_phase,
            "pattern": pattern,
            "placement_event_id": placement_event_id,
            "blueprint_version_id": row.get("blueprint_version_id"),
            "placement": "owner_reviewed",
        }
        context_candidates.append({
            "goal_id": goal.id if goal is not None else None,
            "goal_title": goal.title if goal is not None else None,
            "golden_path_run_id": golden_run.get("id") if golden_run else None,
            "target_contract_version_id": golden_run.get("goal_contract_version_id") if golden_run else None,
            "score": latent_boost + (4.0 * float(goal.priority) if goal is not None else 0.0),
        })

    # Auto-authored fallback (quick-check producer): sections without an
    # owner-reviewed placement show the section's NEWEST authored question, and
    # only while it is still ``proposed`` — an answered/dismissed/escalated
    # newest row consumes the section rather than resurfacing an older one.
    decided_sections: set[str] = set()
    for row in repository.reader_authored_questions_for_extraction(extraction_id):
        section_id = str(row.get("section_id") or "")
        if section_id in question_by_section or section_id in decided_sections:
            continue
        decided_sections.add(section_id)
        if row.get("status") != "proposed":
            continue
        try:
            span_ids = json.loads(row.get("span_ids_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            span_ids = []
        section_passages = passages_by_section.get(section_id, {})
        top_passage = max(
            section_passages.values(), key=lambda passage: passage["score"], default=None
        )
        question_by_section[section_id] = {
            "authored_question_id": row["id"],
            "practice_item_id": None,
            "learning_object_id": None,
            "learning_object_title": None,
            "prompt": row.get("question_md") or "",
            "expected_answer": row.get("expected_answer_md") or "",
            "span_ids": [str(span_id) for span_id in span_ids if isinstance(span_id, str)],
            "reason": "A quick check authored from this section — answer it in your own words, then compare.",
            "learner_signal": "auto_authored",
            "goal_id": None,
            "goal_title": None,
            "golden_path_run_id": None,
            "target_contract_version_id": None,
            "reading_phase": "after_section",
            "pattern": "self_explanation",
            "placement_event_id": None,
            "blueprint_version_id": None,
            "placement": "auto_authored",
            # The learner-confirmed escalation default: the section's strongest
            # source-grounded passage names the Learning Object a minted card
            # would live under.
            "escalation_learning_object_id": (
                top_passage["learning_object_id"] if top_passage is not None else None
            ),
        }

    goal_context = None
    goal_candidates = [candidate for candidate in context_candidates if candidate["goal_id"]]
    if goal_candidates:
        best_goal = max(goal_candidates, key=lambda candidate: (candidate["score"], candidate["goal_id"]))
        goal_context = {
            "goal_id": best_goal["goal_id"],
            "title": best_goal["goal_title"],
            "golden_path_run_id": best_goal["golden_path_run_id"],
            "target_contract_version_id": best_goal["target_contract_version_id"],
        }

    sections: list[dict[str, Any]] = []
    for section in section_rows:
        passages = sorted(
            passages_by_section.get(section["id"], {}).values(),
            key=lambda passage: (-passage["score"], passage["span_id"]),
        )[:3]
        for passage in passages:
            passage.pop("score", None)
        sections.append({
            **section,
            "question": question_by_section.get(section["id"]),
            "suggested_passages": passages,
        })

    return {
        "source_id": source_id,
        "extraction_id": extraction_id,
        "personalized": any(section["question"] or section["suggested_passages"] for section in sections),
        "selection_basis": "reviewed boundary placements + local learner state + active goal + source provenance",
        "goal_context": goal_context,
        "sections": sections,
    }
