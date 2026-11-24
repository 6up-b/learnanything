"""``passage.union_range`` (spec §7.6, owner decision 7: "find everything tied to a passage").

One call per visible range, never per span on hover: for each span of the range, everything anchored to
it, translated through the book's span aliases (``content.sources.span_aliases``) from every other
reading of the same book. A span reached through an alias that names the same place but not the same
text is marked ``needs_reanchor``, never shown as if it were the cited text.

Per span: the learner's annotations; pad blocks linked to it; tutor exchanges whose selection or
citations name it; the exchanges where the tutor adjusted the learner's reasoning (an exchange whose
question was read as a misconception); learner-text gaps tied to it, with their anchor quality; passage
links with their relation; the questions the learner carries beside it; figures made for it; "a check is due before this" (the host passage of a due
check, with no item, learning object or purpose); linked notes; reader-authored questions; and its
exposure (how often and when last it was shown) and whether it is exam or held-out material. Per section of the
range: its learning objects and their coverage.

Goal-independent: the goal level is ``goal.lens``'s, a separate read. Read only: it writes nothing.
"""
from __future__ import annotations

import json
from contextlib import closing
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.content.sources.exam_material import exam_withheld
from learnloop.content.sources.span_aliases import STATUS_CURRENT, SpanTranslator, other_readings, reading_source
from learnloop.db.connection import connect
from learnloop.db.stores import pad_reads
from learnloop.db.stores import span_projection_reads as spans_store
from learnloop.intent.inline_checks import due_checks
from learnloop.reader.annotations import annotation_placements
from learnloop.section_map import RangeError, extraction_sections, range_span_ids

EXACT = "exact"


class UnionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _json_list(value: Any) -> list[Any]:
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return []
    return list(parsed) if isinstance(parsed, list) else []


def _rows(connection: Any, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _in(values: Iterable[str]) -> tuple[str, list[str]]:
    wanted = sorted(set(values))
    return ",".join("?" for _ in wanted) or "NULL", wanted


def span_range(ir: Any, *, from_span_id: str | None, to_span_id: str | None, t0: float | None,
           t1: float | None) -> list[str]:
    try:
        return range_span_ids(ir, from_span_id=from_span_id, to_span_id=to_span_id, t0=t0, t1=t1)
    except RangeError as exc:
        raise UnionError(exc.code, str(exc)) from exc


class _Placer:
    """Places a (reading, span) of any reading of the book on this reading's range."""

    def __init__(self, repository: Any, extraction_id: str, wanted: set[str]) -> None:
        self.extraction_id = extraction_id
        self.wanted = wanted
        self.translator = SpanTranslator(repository, extraction_id)

    def place(self, reading: Any, span: Any) -> tuple[str, str] | None:
        if reading is None or span is None:
            return None
        resolution = self.translator.resolve(str(reading), str(span))
        if resolution.span_id is None or resolution.span_id not in self.wanted:
            return None
        return resolution.span_id, (EXACT if resolution.status == STATUS_CURRENT else resolution.status)


def _empty(span_id: str, section_id: str | None) -> dict[str, Any]:
    return {"span_id": span_id, "section_id": section_id, "annotations": [], "pad_blocks": [], "exchanges": [],
            "adjustments": [], "gaps": [], "passage_links": [], "figures": [], "checks_due": [], "notes": [],
            "authored_questions": [], "carried": [], "exposure": {"times_shown": 0, "last_shown_at": None, "withheld": False}}


def union_range(vault: Any, repository: Any, *, extraction_id: str, from_span_id: str | None = None,
                to_span_id: str | None = None, t0: float | None = None, t1: float | None = None,
                notes_by_span: Mapping[str, list[dict[str, Any]]] | None = None, clock: Any = None) -> dict[str, Any]:
    """``notes_by_span``: the notes linked beside each passage of this reading, handed in by the caller
    (the sidecar, which reaches the notes' code; nothing in learnloop below it does)."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise UnionError("extraction_not_found", f"No reading {extraction_id!r}.")
    span_ids = span_range(ir, from_span_id=from_span_id, to_span_id=to_span_id, t0=t0, t1=t1)
    sections, _blocks, span_to_section = extraction_sections(ir)
    out = {span: _empty(span, span_to_section.get(span)) for span in span_ids}
    if not out:
        return {"extraction_id": extraction_id, "spans": [], "sections": []}
    wanted = set(out)
    placer = _Placer(repository, extraction_id, wanted)
    readings = [extraction_id, *other_readings(repository, extraction_id)]
    marks, reading_ids = _in(readings)

    # The learner's annotations, where each lands on this reading.
    source_id = reading_source(repository, extraction_id)
    if source_id is not None:
        heads = repository.annotations_for_source(source_id)
        for head, placement in zip(heads, annotation_placements(repository, heads, extraction_id), strict=True):
            version = (head or {}).get("version") or {}
            entry = {"annotation_id": (head or {}).get("annotation", {}).get("id"),
                     "type": version.get("annotation_type"), "learner_text": version.get("learner_text") or "",
                     "placement": placement["state"],
                     "created_at": version.get("created_at") or (head or {}).get("annotation", {}).get("created_at")}
            spans = [segment["span_id"] for segment in placement["segments"]] or (
                [placement["flag_span_id"]] if placement.get("flag_span_id") else [])
            for span in dict.fromkeys(spans):
                if span in out:
                    out[span]["annotations"].append(entry)

    # Read only by construction: this read's own SQL runs on a read-only connection, so a write through any
    # store fails at the database (the import fence keeps the mutating stores out; this keeps the calls out).
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        # Pad blocks linked to the passage (links that stand, on blocks not removed).
        for anchor in pad_reads.standing_anchors_for_spans(connection, readings):
            placed = placer.place(anchor["extraction_id"], anchor["span_id"])
            head = pad_reads.head(connection, anchor["block_id"]) if placed else None
            lifted_from = None
            # A link left on a lift-out stub (a lift made before links moved with the words) marks the block that
            # carries the words now.
            for _step in range(64):
                if head is None or head["kind"] != "lifted":
                    break
                lifted_from = lifted_from or anchor["block_id"]
                head = pad_reads.head(connection, str((head.get("payload") or {}).get("lifted_block_id") or ""))
            if placed and head is not None and not head["tombstone"]:
                out[placed[0]]["pad_blocks"].append({
                    "block_id": head["block_id"], "pad_id": head["pad_id"], "kind": head["kind"],
                    "provenance": head["provenance"], "event_id": anchor["event_id"],
                    "annotation_id": anchor["annotation_id"], "alias": placed[1], "lifted_from_block_id": lifted_from,
                    "created_at": anchor["created_at"]})

        # Questions the learner carries, beside the passage they were carried from (still carried only: a quiet
        # margin mark, never a nudge; spec §10.12).
        for row in pad_reads.carried_on_readings(connection, readings, ("carried", "not_now")):
            anchor = row["anchor"] or {}
            placed = placer.place(anchor.get("extraction_id"), anchor.get("span_id"))
            if placed:
                out[placed[0]]["carried"].append({
                    "carried_id": row["carried_id"], "text": row["text"], "since": row["since"],
                    "state": row["state"], "alias": placed[1]})

        # Tutor exchanges and the reasoning the tutor adjusted.
        exchange_rows = spans_store.rows_on_readings(connection, "question_event_spans", readings)
        events = {row["id"]: row for row in _rows(
            connection, "SELECT id, context, question_md, created_at FROM question_events WHERE id IN (%s)"
            % _in(row["question_event_id"] for row in exchange_rows)[0],
            _in(row["question_event_id"] for row in exchange_rows)[1])} if exchange_rows else {}
        adjusted = {row["source_id"]: row["id"] for row in _rows(
            connection, "SELECT id, source_id FROM learner_text_gaps WHERE source_kind = 'tutor_question' "
            "AND kind = 'misconception' AND source_id IN (%s)" % _in(events)[0], _in(events)[1])} if events else {}
        for row in exchange_rows:
            placed = placer.place(row["extraction_id"], row["span_id"])
            event = events.get(row["question_event_id"])
            if not placed or event is None:
                continue
            out[placed[0]]["exchanges"].append({
                "question_event_id": row["question_event_id"], "role": row["role"], "quality": row["quality"],
                "alias": placed[1], "context": event["context"], "question_md": event["question_md"],
                "created_at": event["created_at"]})
            if row["question_event_id"] in adjusted:
                entry = {"question_event_id": row["question_event_id"], "gap_id": adjusted[row["question_event_id"]]}
                if entry not in out[placed[0]]["adjustments"]:
                    out[placed[0]]["adjustments"].append(entry)

        # Learner-text gaps, with their anchor quality.
        gap_rows = spans_store.rows_on_readings(connection, "learner_text_gap_spans", readings)
        gaps = {row["id"]: row for row in _rows(
            connection, "SELECT id, source_kind, kind, created_at FROM learner_text_gaps WHERE id IN (%s)"
            % _in(row["gap_id"] for row in gap_rows)[0], _in(row["gap_id"] for row in gap_rows)[1])} if gap_rows else {}
        for row in gap_rows:
            placed = placer.place(row["extraction_id"], row["span_id"])
            gap = gaps.get(row["gap_id"])
            if placed and gap is not None:
                out[placed[0]]["gaps"].append({
                    "gap_id": row["gap_id"], "source_kind": gap["source_kind"], "kind": gap["kind"],
                    "role": row["role"], "quality": row["quality"], "alias": placed[1],
                    "created_at": gap["created_at"]})

        # Passage links, figures and authored questions on any reading of the book.
        for row in _rows(connection, "SELECT id, extraction_id, span_id, target_kind, target_id, relation, quote "
                                     f"FROM passage_links WHERE extraction_id IN ({marks}) ORDER BY created_at, id",
                         reading_ids):
            placed = placer.place(row["extraction_id"], row["span_id"])
            if placed:
                out[placed[0]]["passage_links"].append({
                    "link_id": row["id"], "target_kind": row["target_kind"], "target_id": row["target_id"],
                    "relation": row["relation"], "quote": row["quote"], "alias": placed[1]})
        for row in _rows(connection, "SELECT f.id, f.extraction_id, f.span_ids_json, f.tier, f.verification, "
                                     "f.created_at FROM interactive_figures AS f WHERE f.extraction_id IN "
                                     f"({marks}) AND NOT EXISTS (SELECT 1 FROM interactive_figures AS c WHERE "
                                     "c.supersedes_id = f.id) ORDER BY f.created_at, f.id", reading_ids):
            for span in _json_list(row["span_ids_json"]):
                placed = placer.place(row["extraction_id"], span)
                if placed:
                    out[placed[0]]["figures"].append({"figure_id": row["id"], "tier": row["tier"],
                                                      "verification": row["verification"],
                                                      "created_at": row["created_at"], "alias": placed[1]})
        for row in _rows(connection, "SELECT id, extraction_id, span_ids_json, anchor_span_ids_json, status, "
                                     "question_style, scope_kind, question_md FROM reader_authored_questions WHERE "
                                     f"extraction_id IN ({marks}) AND status != 'dismissed' ORDER BY created_at, id",
                         reading_ids):
            spans = _json_list(row["anchor_span_ids_json"]) or _json_list(row["span_ids_json"])
            for span in dict.fromkeys(spans):
                placed = placer.place(row["extraction_id"], span)
                if placed:
                    out[placed[0]]["authored_questions"].append({
                        "question_id": row["id"], "status": row["status"], "question_style": row["question_style"],
                        "scope_kind": row["scope_kind"], "question_md": row["question_md"], "alias": placed[1]})

        # Exposure: how often the passage was shown, and when last. The Reader's seen-passage rows are not read
        # here: they are generation evidence with one reader of their own.
        for row in _rows(connection, "SELECT extraction_id, span_id, COUNT(*) AS n, MAX(created_at) AS last FROM "
                                     f"source_exposure_events WHERE extraction_id IN ({marks}) GROUP BY extraction_id, "
                                     "span_id", reading_ids):
            placed = placer.place(row["extraction_id"], row["span_id"])
            if placed:
                exposure = out[placed[0]]["exposure"]
                exposure["times_shown"] += int(row["n"])
                exposure["last_shown_at"] = max(filter(None, [exposure["last_shown_at"], row["last"]]), default=None)

        # Each section's learning objects and coverage (the newest row per learning object stands).
        touched = sorted({entry["section_id"] for entry in out.values() if entry["section_id"]})
        coverage: dict[str, dict[str, dict[str, Any]]] = {}
        if touched:
            section_marks, section_list = _in(touched)
            for row in _rows(connection, "SELECT section_id, learning_object_id, treatment, learner_override, created_at "
                                         f"FROM section_coverage WHERE extraction_id = ? AND section_id IN "
                                         f"({section_marks}) ORDER BY created_at, id", [extraction_id, *section_list]):
                coverage.setdefault(row["section_id"], {})[row["learning_object_id"]] = row

    for key in exam_withheld(vault, repository, [(extraction_id, span) for span in out]):
        out[key[1]]["exposure"]["withheld"] = True
    for check in due_checks(vault, repository, extraction_id=extraction_id, clock=clock):
        host = check.get("host") or {}
        if host.get("span_id") in out:
            entry = {"commitment_id": check["commitment_id"]}
            if entry not in out[host["span_id"]]["checks_due"]:
                out[host["span_id"]]["checks_due"].append(entry)
    for span, notes in (notes_by_span or {}).items():
        if span in out:
            out[span]["notes"].extend(notes)

    section_out = []
    for section in sections:
        section_id = str(section["id"])
        if section_id not in {entry["section_id"] for entry in out.values()}:
            continue
        rows = coverage.get(section_id, {})
        section_out.append({
            "section_id": section_id, "title": section["label"],
            "learning_objects": [
                {"learning_object_id": lo_id, "treatment": row["treatment"], "learner_override": row["learner_override"]}
                for lo_id, row in sorted(rows.items())
                if row["learner_override"] != "not_about" and (row["treatment"] != "not_about"
                                                               or row["learner_override"] == "is_about")],
        })
    return {"extraction_id": extraction_id, "spans": [out[span] for span in span_ids], "sections": section_out}


__all__ = ["UnionError", "span_range", "union_range"]
