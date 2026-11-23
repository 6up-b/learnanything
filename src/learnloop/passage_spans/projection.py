"""The two DERIVED span projections (spec §7.6, review F5): which passages each tutor exchange
(``question_event_spans``) and each read learner text (``learner_text_gap_spans``) are tied to.

Each source has its own recipe, and none invents locality. A row records its anchor quality:

* ``exact_selection``: the passage the learner selected (a Reader Ask's anchor and selection, an
  authored question's passage, a note's passage link);
* ``citation``: a passage the tutor's answer cited;
* ``source_context``: the passage the learner was working from, without a selection (a practice
  item's source passages, a workbench problem's passages);
* ``unanchored``: no passage; the row keeps the learning object it is about. ``entity_source_links``
  says what content relates to a learning object, not where the learner wrote, so it never places a
  row on a passage.

Rows name the reading they were made on; aliases across re-reads are applied when the union is read
(``learnloop.passage_union.union``), so a re-read never rewrites them.

**One recipe, two writers.** A new exchange or gap is projected at once
(:func:`project_question_event`, :func:`project_gap`), and the replayer
(:func:`rebuild_question_event_spans`, :func:`rebuild_learner_text_gap_spans`, registered in
``substrate.rebuild_orchestrator``) clears a table and projects every source through the same
functions, so a rebuild reproduces the live rows. Zero model calls; nothing here is evidence.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop.db.stores import span_projections as store
from learnloop.passage_spans.exchange_places import CITED, SELECTION, exchange_places

LOG = logging.getLogger(__name__)

EXACT_SELECTION = "exact_selection"
CITATION = "citation"
SOURCE_CONTEXT = "source_context"
UNANCHORED = "unanchored"
CONTEXT = "context"

QUESTION_EVENT_SPANS = "question_event_spans"
LEARNER_TEXT_GAP_SPANS = "learner_text_gap_spans"

#: Gap sources that place a row through their item's passages, else keep its learning object.
_ITEM_PLACED_GAP_KINDS = frozenset({"stuck_answer", "diagnosis", "hint_feedback", "lesson", "external_chat"})


def _json(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _row(extraction_id: str | None, span_id: str | None, role: str, quality: str,
         learning_object_id: str | None = None) -> dict[str, Any]:
    return {"extraction_id": extraction_id, "span_id": span_id, "role": role, "quality": quality,
            "learning_object_id": learning_object_id}


def _dedupe(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = tuple(row.get(column) for column in store.SPAN_COLUMNS)
        if key not in seen:
            seen.add(key)
            out.append(dict(row))
    return out


def _span_key(note_id: Any) -> tuple[str, str] | None:
    text = str(note_id or "")
    if not text.startswith("span:") or "/" not in text:
        return None
    reading, span = text[len("span:"):].split("/", 1)
    return (reading, span) if reading and span else None


def _item_passages(vault: Any, item_id: str | None) -> tuple[list[tuple[str, str]], str | None]:
    """An item's source passages (its canonical exercise and source refs) and its learning object."""

    item = (getattr(vault, "practice_items", None) or {}).get(str(item_id or "")) if item_id else None
    if item is None:
        return [], None
    places: list[tuple[str, str]] = []
    exercise = getattr(item, "canonical_exercise", None)
    if exercise is not None:
        places.extend((str(exercise.extraction_id), str(span)) for span in exercise.span_ids)
    for ref in getattr(getattr(item, "provenance", None), "source_refs", None) or []:
        if ref.extraction_id:
            places.extend((str(ref.extraction_id), str(span)) for span in ref.span_ids)
    return places, str(item.learning_object_id)


def _context_rows(places: list[tuple[str, str]], learning_object_id: str | None) -> list[dict[str, Any]]:
    if places:
        return [_row(reading, span, CONTEXT, SOURCE_CONTEXT) for reading, span in places]
    return [_row(None, None, CONTEXT, UNANCHORED, learning_object_id)] if learning_object_id else []


# -- tutor exchanges --------------------------------------------------------------------------------


def _reader_payloads(connection: Any, question_event_ids: Iterable[str] | None) -> dict[str, list[tuple[str, dict]]]:
    """Each exchange's ``reader_answer_submitted`` events, as (subject, payload), by question event id."""

    sql = "SELECT subject_id, payload_json FROM interaction_events WHERE kind = 'reader_answer_submitted'"
    params: list[Any] = []
    if question_event_ids is not None:
        wanted = sorted(set(question_event_ids))
        if not wanted:
            return {}
        sql += (f" AND json_extract(payload_json, '$.question_event_id') IN ({','.join('?' for _ in wanted)})")
        params.extend(wanted)
    found: dict[str, list[tuple[str, dict]]] = {}
    for subject_id, payload_json in connection.execute(sql + " ORDER BY created_at, id", params):
        payload = _json(payload_json, {})
        event_id = payload.get("question_event_id") if isinstance(payload, dict) else None
        if event_id:
            found.setdefault(str(event_id), []).append((str(subject_id or ""), payload))
    return found


def question_event_rows(vault: Any, event: Mapping[str, Any], payloads: list[tuple[str, dict]]) -> list[dict[str, Any]]:
    """One exchange's rows. A Reader exchange: its anchor (``note_id``), the selection and citations of
    its recorded answer. A practice or feedback question: its item's source passages, else its LO."""

    context = str(event.get("context") or "")
    if context == "reader":
        rows: list[dict[str, Any]] = []
        anchor = _span_key(event.get("note_id"))
        if anchor is not None:
            rows.append(_row(*anchor, SELECTION, EXACT_SELECTION))
        for subject_id, payload in payloads:
            reading = str(payload.get("extraction_id") or (anchor[0] if anchor else ""))
            if not reading:
                continue
            for place_reading, span, role in exchange_places(payload, subject_id=subject_id, extraction_id=reading):
                if role == SELECTION:
                    rows.append(_row(place_reading, span, SELECTION, EXACT_SELECTION))
                elif role == CITED:
                    rows.append(_row(place_reading, span, CITED, CITATION))
        return _dedupe(rows)
    if context in ("practice", "feedback"):
        return _dedupe(_context_rows(*_item_passages(vault, event.get("practice_item_id"))))
    return []


def _question_events(connection: Any, ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    sql = "SELECT id, context, note_id, practice_item_id FROM question_events"
    params: list[Any] = []
    if ids is not None:
        wanted = sorted(set(ids))
        if not wanted:
            return []
        sql += f" WHERE id IN ({','.join('?' for _ in wanted)})"
        params.extend(wanted)
    cursor = connection.execute(sql + " ORDER BY id", params)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def project_question_event(connection: Any, vault: Any, question_event_id: str) -> int:
    """Write (or rewrite) one exchange's rows; returns how many were written."""

    events = _question_events(connection, [question_event_id])
    if not events:
        return 0
    payloads = _reader_payloads(connection, [question_event_id]).get(str(question_event_id), [])
    return store.replace_rows(connection, QUESTION_EVENT_SPANS, str(question_event_id),
                              question_event_rows(vault, events[0], payloads))


def rebuild_question_event_spans(vault: Any, repository: Any) -> dict[str, Any]:
    """The replayer: clear the table, then project every exchange through the live recipe."""

    cleared = repository.clear_derived_projection_tables([QUESTION_EVENT_SPANS])
    written = 0
    with repository.connection() as connection:
        payloads = _reader_payloads(connection, None)
        events = _question_events(connection)
        for event in events:
            written += store.replace_rows(connection, QUESTION_EVENT_SPANS, str(event["id"]),
                                          question_event_rows(vault, event, payloads.get(str(event["id"]), [])))
        connection.commit()
    return {"written": written, "sources": len(events), "cleared_rows_by_table": cleared}


# -- read learner texts ----------------------------------------------------------------------------


def _one(connection: Any, sql: str, params: Iterable[Any]) -> dict[str, Any] | None:
    cursor = connection.execute(sql, tuple(params))
    row = cursor.fetchone()
    return dict(zip([column[0] for column in cursor.description], row, strict=True)) if row is not None else None


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def gap_rows(connection: Any, vault: Any, gap: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One read learner text's rows, by its source kind's recipe (spec §7.6's table)."""

    kind = str(gap.get("source_kind") or "")
    source_id = str(gap.get("source_id") or "")
    lo_id = gap.get("anchor_learning_object_id")
    rows: list[dict[str, Any]] = []
    if kind == "tutor_question":
        events = _question_events(connection, [source_id])
        if events:
            rows = question_event_rows(vault, events[0], _reader_payloads(connection, [source_id]).get(source_id, []))
    elif kind == "reader_formative" and _table(connection, "reader_authored_questions"):
        found = _one(connection, "SELECT extraction_id, span_ids_json, anchor_span_ids_json FROM "
                                 "reader_authored_questions WHERE id = ?", (source_id,))
        if found is not None:
            spans = _json(found.get("anchor_span_ids_json"), []) or _json(found.get("span_ids_json"), [])
            rows = [_row(str(found["extraction_id"]), str(span), SELECTION, EXACT_SELECTION) for span in spans]
    elif kind == "workbench_text":
        session = None
        if _table(connection, "workbench_steps"):
            session = _one(connection, "SELECT s.extraction_id, s.span_ids_json FROM workbench_steps AS w JOIN "
                                       "workbench_sessions AS s ON s.id = w.session_id WHERE w.id = ?", (source_id,))
        if session is None and _table(connection, "help_assists"):
            session = _one(connection, "SELECT s.extraction_id, s.span_ids_json FROM help_assists AS h JOIN "
                                       "workbench_sessions AS s ON s.id = h.workbench_session_id WHERE h.id = ?",
                           (source_id,))
        if session is not None and session.get("extraction_id"):
            rows = [_row(str(session["extraction_id"]), str(span), CONTEXT, SOURCE_CONTEXT)
                    for span in _json(session.get("span_ids_json"), [])]
    elif kind == "learner_note" and _table(connection, "learner_note_links"):
        # The passages the learner linked the note to by hand: per passage, the learner's newest row
        # stands (a later "hide" takes the link back); a model's proposal is not where the learner wrote.
        cursor = connection.execute(
            "SELECT target_key, target_kind, status, extraction_id, span_id FROM learner_note_links WHERE "
            "authorship = 'learner' AND note_key = (SELECT note_key FROM learner_notes WHERE id = ?) "
            "ORDER BY created_at, id", (source_id,))
        standing: dict[str, tuple[Any, ...]] = {}
        for row in cursor.fetchall():
            standing[str(row[0])] = row
        rows = [_row(str(reading), str(span), SELECTION, EXACT_SELECTION)
                for _key, target_kind, status, reading, span in standing.values()
                if target_kind == "passage" and status == "accepted" and span]
    elif kind in _ITEM_PLACED_GAP_KINDS:
        places, item_lo = _item_passages(vault, gap.get("practice_item_id"))
        rows = _context_rows(places, None)
        lo_id = lo_id or item_lo
    if not any(row["span_id"] for row in rows) and lo_id:
        rows.append(_row(None, None, CONTEXT, UNANCHORED, str(lo_id)))
    return _dedupe(rows)


_GAP_COLUMNS = "id, source_kind, source_id, practice_item_id, anchor_learning_object_id"


def project_gap(connection: Any, vault: Any, gap_id: str) -> int:
    """Write (or rewrite) one read learner text's rows; returns how many were written."""

    gap = _one(connection, f"SELECT {_GAP_COLUMNS} FROM learner_text_gaps WHERE id = ?", (gap_id,))
    if gap is None:
        return 0
    return store.replace_rows(connection, LEARNER_TEXT_GAP_SPANS, str(gap_id), gap_rows(connection, vault, gap))


def rebuild_learner_text_gap_spans(vault: Any, repository: Any) -> dict[str, Any]:
    """The replayer: clear the table, then project every gap through the live recipe."""

    cleared = repository.clear_derived_projection_tables([LEARNER_TEXT_GAP_SPANS])
    written = 0
    with repository.connection() as connection:
        cursor = connection.execute(f"SELECT {_GAP_COLUMNS} FROM learner_text_gaps ORDER BY id")
        names = [column[0] for column in cursor.description]
        gaps = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
        for gap in gaps:
            written += store.replace_rows(connection, LEARNER_TEXT_GAP_SPANS, str(gap["id"]),
                                          gap_rows(connection, vault, gap))
        connection.commit()
    return {"written": written, "sources": len(gaps), "cleared_rows_by_table": cleared}


# -- write-through -----------------------------------------------------------------------------------


def write_through_question_events(repository: Any, vault: Any, question_event_ids: Iterable[str]) -> None:
    """Project new or answered exchanges at once. A failure is logged and never fails the learner's
    Ask: the replayer writes the same rows on the next rebuild."""

    ids = [str(value) for value in question_event_ids if value]
    if not ids:
        return
    try:
        with repository.connection() as connection:
            for question_event_id in ids:
                project_question_event(connection, vault, question_event_id)
    except Exception:  # noqa: BLE001 - a display projection never fails the exchange
        LOG.warning("could not project the passages of exchanges %s", ids, exc_info=True)


def write_through_gap(connection: Any, vault: Any, gap_id: str | None) -> None:
    """Project a gap just written, in its writer's transaction (a savepoint of it: ``connection`` is
    the repository's atomic connection), so a failure leaves the gap row and is only logged."""

    if not gap_id:
        return
    try:
        with connection:
            project_gap(connection, vault, gap_id)
    except Exception:  # noqa: BLE001 - a display projection never fails the gap reading
        LOG.warning("could not project the passages of gap %s", gap_id, exc_info=True)


__all__ = [
    "CITATION", "EXACT_SELECTION", "LEARNER_TEXT_GAP_SPANS", "QUESTION_EVENT_SPANS", "SOURCE_CONTEXT", "UNANCHORED",
    "gap_rows", "project_gap", "project_question_event", "question_event_rows", "rebuild_learner_text_gap_spans",
    "rebuild_question_event_spans", "write_through_gap", "write_through_question_events",
]
