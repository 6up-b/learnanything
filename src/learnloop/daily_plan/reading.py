"""Reading blocks (``spec_daily_loop_v1.md`` §6.10, Q5): as-you-read, no pre-questions in DL1.

A source imported ``as_you_read`` (and uncommitted: DL1 has no intent) puts at
most one reading block a day in the new lane: the reader guide's next
unfinished section, carried as a :class:`ReadingTarget`. "Next" counts from
where the learner left off (the furthest section they read into), and front
and back matter (contents, preface, index) are never the step while a chapter
is left (UX Phase 1 usability round 1, U4), wherever the plan acts: a live
change behind its kill switch, not a successor tag (the owner's ruling at the
UX Phase 1 merge: replay never reads the selection). With
``plan.reading_from_furthest = false`` the selection is DL1's, the first
unfinished section in book order. Its estimate is the section's words left
over ``plan.read_words_per_minute``, where words left =
section words x (1 - spans seen / span count) from ``reader_section_progress``.
Section completion still triggers item generation as today, and those items
enter the new lane on later days. Nothing from an unread section reaches the
maintain lane.
"""

from __future__ import annotations

import json
from typing import Any

from learnloop.content.sources.front_matter import is_front_matter_label
from learnloop.daily_plan.types import ReadingTarget
from learnloop.reader.reader_guidance import extraction_sections


def as_you_read_extraction_ids(repository: Any) -> list[str]:
    """Extractions of sources whose applied synthesis brief is ``as_you_read``.

    Newest first. A manifest whose brief does not name the mode is skipped
    (conservative: only an explicit as-you-read import puts reading in the plan).
    """

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT m.brief_json AS brief, m.extraction_ids_json AS extractions, m.created_at AS created_at "
            "FROM synthesis_manifests m "
            "WHERE EXISTS (SELECT 1 FROM synthesis_runs r WHERE r.manifest_id = m.id AND r.status = 'completed') "
            "ORDER BY m.created_at DESC, m.id DESC"
        ).fetchall()
    ordered: list[str] = []
    for row in rows:
        try:
            brief = json.loads(row["brief"]) if row["brief"] else {}
            extractions = json.loads(row["extractions"]) if row["extractions"] else []
        except (TypeError, ValueError):
            continue
        if not isinstance(brief, dict) or brief.get("practice_items") != "as_you_read":
            continue
        for extraction_id in extractions or []:
            if isinstance(extraction_id, str) and extraction_id not in ordered:
                ordered.append(extraction_id)
    return ordered


def _section_words(ir: Any, span_ids: list[str]) -> int:
    by_span = {block.span_id: block for block in ir.blocks}
    return sum(len(str(by_span[span].text or "").split()) for span in span_ids if span in by_span)


def next_reading_target(
    repository: Any, *, extraction_ids: list[str] | None = None, from_furthest: bool = True,
    exam: Any = None,
) -> ReadingTarget | None:
    """The as-you-read section to continue: the most recently progressed source's
    next unfinished section, else the newest import's first unfinished one.

    ``from_furthest`` (``plan.reading_from_furthest``) is U4's selection; off,
    "next" is DL1's: the first unfinished section in book order, front matter
    included. ``exam`` (the one exam predicate, ``content.sources.
    exam_material``, as ``source_retrieval.corpus.exam_exclusions`` returns
    it: ``extractions`` and ``(extraction, span)`` ``spans``)
    keeps U4's step off exam material: a section with an exam span (a
    ``held_out_evaluation`` unit) is never the step to read, and an exam
    extraction offers none. DL1's selection (the switch off) is unchanged."""

    candidates = extraction_ids if extraction_ids is not None else as_you_read_extraction_ids(repository)
    if not candidates:
        return None
    progress_by_extraction: dict[str, dict[str, dict[str, Any]]] = {}
    latest_touch: dict[str, str] = {}
    for extraction_id in candidates:
        rows = repository.reader_section_progress_for(extraction_id)
        progress_by_extraction[extraction_id] = {str(row["section_id"]): row for row in rows}
        touched = [str(row.get("updated_at") or "") for row in rows]
        if touched:
            latest_touch[extraction_id] = max(touched)
    ordered = sorted(
        candidates,
        key=lambda extraction_id: (
            0 if extraction_id in latest_touch else 1,
            # Most recently read first; untouched ones keep the newest-import order.
            "" if extraction_id not in latest_touch else _desc(latest_touch[extraction_id]),
            candidates.index(extraction_id),
        ),
    )
    for extraction_id in ordered:
        target = _first_unfinished(
            repository, extraction_id, progress_by_extraction.get(extraction_id, {}), from_furthest=from_furthest,
            exam=exam if from_furthest else None,
        )
        if target is not None:
            return target
    return None


def _desc(value: str) -> str:
    # Lexicographic descending key for ISO timestamps.
    return "".join(chr(0x10FFFF - ord(char)) for char in value)


def _first_unfinished(
    repository: Any, extraction_id: str, progress: dict[str, dict[str, Any]], *, from_furthest: bool = True,
    exam: Any = None,
) -> ReadingTarget | None:
    if exam is not None and extraction_id in exam.extractions:
        return None
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return None
    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(run.get("revision_id")) if run.get("revision_id") else None
    source_id = str((revision or {}).get("source_id") or "")
    sections, _block_by_span, _span_to_section = extraction_sections(ir)
    if exam is not None and exam.spans:
        sections = [
            section for section in sections
            if not any((extraction_id, str(span_id)) in exam.spans for span_id in section["span_ids"])
        ]
    ordered = list(sections)
    if from_furthest:
        # Contents, preface, index and the like are never the step to continue
        # with while the book has a chapter left (UX Phase 1 usability round 1,
        # U4); a source that is nothing but such sections still offers them.
        readable = [section for section in sections if not is_front_matter_label(section.get("label"))]
        candidates = readable or sections
        # Continue where the learner left off: from the furthest section they
        # have read into, not a section they skipped on the way (U4).
        touched = [
            index for index, section in enumerate(candidates)
            if _has_progress(progress.get(str(section["id"])))
        ]
        start = max(touched) if touched else 0
        ordered = candidates[start:] + candidates[:start]
    for section in ordered:
        row = progress.get(str(section["id"]))
        if row is not None and row.get("completed_at"):
            continue
        words = _section_words(ir, list(section["span_ids"]))
        if words <= 0:
            continue
        seen = int((row or {}).get("spans_seen") or 0)
        count = int((row or {}).get("span_count") or 0)
        fraction_left = 1.0 - (min(seen, count) / count if count > 0 else 0.0)
        words_left = int(round(words * fraction_left))
        if words_left <= 0:
            continue
        return ReadingTarget(
            source_id=source_id,
            extraction_id=extraction_id,
            section_id=str(section["id"]),
            section_title=str(section.get("label") or "this section"),
            words_left=words_left,
            partial=False,
        )
    return None


def _has_progress(row: dict[str, Any] | None) -> bool:
    return bool(row) and bool(int(row.get("spans_seen") or 0) > 0 or row.get("completed_at") or row.get("revealed_at"))


def section_start_span(repository: Any, extraction_id: str, section_id: str) -> str | None:
    """The section's first readable span: where the reader opens a reading step."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return None
    sections, _blocks, _spans = extraction_sections(ir)
    section = next((row for row in sections if str(row["id"]) == section_id), None)
    return str(section["start_span_id"]) if section is not None else None


__all__ = [
    "as_you_read_extraction_ids",
    "next_reading_target",
    "section_start_span",
]
