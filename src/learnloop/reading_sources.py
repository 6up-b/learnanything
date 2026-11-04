"""The list of Reader sources: every learning opportunity a source row records, and how to read it.

One list, read by adaptive difficulty's sweep (:mod:`learnloop.adaptive_difficulty.reading`) and by data capture's one
read of exposures (:mod:`learnloop.data_capture.reading_exposures`), through whatever map and view each passes. It lived in
the former; the scoreboard and the rebuild must reach it and cannot import AD, so it sits here as a leaf (landing ruling
R7). A row, its time and the LOs its map names: no write, no clock, no model call, no switch.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
import json
from typing import Any, Protocol

from learnloop.clock import parse_utc
from learnloop.db.stores import ad_receipts as store

#: A reader tutor question's answer modes, each a tutor exchange's subkind;
#: ``unknown`` where none was stored (before migration 213, or outside the Reader).
TUTOR_ANSWER_MODES: tuple[str, ...] = ("answer_directly", "help_me_reason", "ask_me_first")
UNKNOWN_ANSWER_MODE = "unknown"
#: The in-passage question styles that are learning opportunities (``reconstruct``
#: questions are escalated to practice items, which AD reads as attempts).
IN_PASSAGE_STYLES: tuple[str, ...] = ("recall", "next_step", "why_step", "assumptions")
#: A serve's sweep re-reads this far behind the newest recorded source time,
#: so a source row stamped a little before an earlier sweep but committed
#: after it (a tutor answer completing, a clock skew) is still recorded once.
SWEEP_OVERLAP = timedelta(hours=1)

SELF_CHECK_TASK = "reader_quick_check_self_check"
SELF_CHECK_CLASSES = {"matches": "self_check:matched", "partly": "self_check:missed", "no": "self_check:missed"}
#: The span-view contexts that are the learner reading (the Guide, the Reader,
#: the library, passages the tutor cites, provenance and repair passages). The
#: owner's review tooling (registry_review, conflict_review, gate_diagnostic)
#: is not reading.
EXPOSURE_CONTEXTS = ("reader", "reader_restoration", "library", "tutor_citation", "provenance", "provenance_panel",
                     "remediation", "remediation_delivery", "other")
TUTOR_CONTEXTS = ("reader", "library")


def source_stamp(value: Any) -> str | None:
    """A source time in one sortable form (microseconds, ``Z``); None when unreadable."""

    if value in (None, ""):
        return None
    try:
        parsed = parse_utc(str(value))
    except ValueError:
        return None
    return parsed.isoformat(timespec="microseconds").replace("+00:00", "Z") if parsed else None


class ReadingMap(Protocol):
    """How a source row maps to LOs and facets (the Reader's own mapping)."""

    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]: ...
    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]: ...
    def section_spans(self, extraction_id: str, section_id: str) -> list[str]: ...
    def worked_example_spans(self, extraction_id: str) -> set[str]: ...
    def withheld(self, extraction_id: str, span_id: str | None) -> bool: ...
    def los_for_note(self, note_id: str) -> list[str]: ...
    def lo_for_item(self, practice_item_id: str) -> str | None: ...
    def facets_for_lo(self, learning_object_id: str) -> list[str]: ...


@dataclass(frozen=True)
class ListedEvent:
    kind: str
    subkind: str
    source_table: str
    source_id: str
    written_at: str
    learning_object_ids: tuple[str, ...]
    #: Facets the source names directly (dose 1 each); otherwise the LO's facets share dose 1.
    named_facets: tuple[str, ...] = ()
    #: What the cap counts: the example or question identity, or a section.
    identity: str = ""


def _in_window(stamp: str | None, lower: str | None, upper: str) -> bool:
    return stamp is not None and stamp <= upper and (lower is None or stamp > lower)


def _recorded(connection: Any, kind: str, subkind: str, table: str, source_id: str, *, view: Any) -> bool:
    """An earlier sweep recorded this source row: it is not mapped again (a serve's sweep re-reads its
    overlap window, never re-resolves it). A receipt AD may not read counts as recorded; one of another
    protection epoch does not: the source is mapped again under the current projection (round 2,
    class 3b)."""

    return view.lookup(connection, store.READING, "kind = ? AND subkind = ? AND source_table = ? AND source_id = ?",
                       (kind, subkind, table, source_id), stale_as_missing=True)[0] != "missing"


def _section_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                    view: Any = None) -> list[ListedEvent]:
    events: list[ListedEvent] = []
    # The registry's rule withholds a section with any held-out span in it (the view's rows).
    for row in view.rows(connection, "reader_section_progress", "completed_at IS NOT NULL"):
        extraction_id, section_id, completed_at = row["extraction_id"], row["section_id"], row["completed_at"]
        stamp = source_stamp(completed_at)
        if not _in_window(stamp, lower, upper):
            continue
        extraction_id, section_id = str(extraction_id), str(section_id)
        if _recorded(connection, "reading", "section_read", "reader_section_progress",
                     f"{extraction_id}/{section_id}", view=view):
            continue
        spans = reading_map.section_spans(extraction_id, section_id)
        if reading_map.withheld(extraction_id, None) or any(reading_map.withheld(extraction_id, span) for span in spans):
            continue
        los = tuple(reading_map.los_for_section(extraction_id, section_id))
        if not los:
            continue
        section_key = f"{extraction_id}/{section_id}"
        events.append(ListedEvent("reading", "section_read", "reader_section_progress", section_key, stamp, los,
                             identity=section_key))
        examples = reading_map.worked_example_spans(extraction_id)
        for span in spans:
            if span in examples:
                example = f"{extraction_id}/{span}"
                events.append(ListedEvent("worked_example", "in_completed_section", "reader_section_progress", example,
                                     stamp, tuple(reading_map.los_for_span(extraction_id, span)) or los,
                                     identity=example))
    return events


def _exposure_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                     view: Any = None) -> list[ListedEvent]:
    events: list[ListedEvent] = []
    marks = ",".join("?" for _ in EXPOSURE_CONTEXTS)
    for row in view.rows(connection, "source_exposure_events", f"context IN ({marks})", EXPOSURE_CONTEXTS):
        row_id, extraction_id, span_id, created_at = row["id"], row["extraction_id"], row["span_id"], row["created_at"]
        stamp = source_stamp(created_at)
        if not _in_window(stamp, lower, upper):
            continue
        extraction_id, span_id = str(extraction_id), str(span_id)
        if (_recorded(connection, "reading", "passage_viewed", "source_exposure_events", str(row_id), view=view)
                or _recorded(connection, "worked_example", "shown", "source_exposure_events", str(row_id),
                             view=view)):
            continue
        if reading_map.withheld(extraction_id, span_id):
            continue
        los = tuple(reading_map.los_for_span(extraction_id, span_id))
        if not los:
            continue
        if span_id in reading_map.worked_example_spans(extraction_id):
            example = f"{extraction_id}/{span_id}"
            events.append(ListedEvent("worked_example", "shown", "source_exposure_events", str(row_id), stamp, los,
                                 identity=example))
        else:
            events.append(ListedEvent("reading", "passage_viewed", "source_exposure_events", str(row_id), stamp, los))
    return events


def _named_facets(raw: Any) -> tuple[str, ...]:
    try:
        value = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        return ()
    if isinstance(value, Mapping):
        value = list(value)
    return tuple(str(facet) for facet in value if isinstance(facet, str)) if isinstance(value, list) else ()


def _note_withheld(connection: Any, reading_map: Any, view: Any, note_id: str) -> bool:
    """A note's protection for the sweep: the map's own rule when it has one, else the view's (every
    note while the view is unavailable)."""

    if hasattr(reading_map, "note_withheld"):
        return bool(reading_map.note_withheld(note_id))
    return bool(view is not None and view.note_withheld(connection, note_id))


def _tutor_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                  view: Any = None) -> list[ListedEvent]:
    from learnloop.ingest.locators import parse_block_span

    events: list[ListedEvent] = []
    # The exchange exists once its answer completed (Codex review F4): a
    # pending question answered later is stamped by ``answered_at`` (set once
    # on completion, migration 213), never by when it was asked; a row
    # written already answered has its completion time in ``created_at``.
    # Every answered row not yet recorded is read, whatever the window's
    # lower bound, so a slow completion is never missed. The registry's rule withholds a question
    # whose complete recorded source context is held out (Codex verify F46), before any mapping.
    for row in view.rows(connection, "question_events", "context IN ('reader', 'library') AND "
                         "answer_status = 'answered'"):
        row_id, note_id, item_id, facets_json = row["id"], row.get("note_id"), row.get("practice_item_id"), \
            row.get("facets_json")
        # The subkind is the answer mode stored at the ask (§5.11; fix round 4, V5), never the context.
        answer_mode = row.get("answer_mode")
        available_at = row.get("answered_at") or row.get("created_at")
        if view.lookup(connection, store.READING, "kind = 'reader_tutor_exchange' AND source_table = "
                       "'question_events' AND source_id = ?", (str(row_id),), stale_as_missing=True)[0] != "missing":
            continue
        stamp = source_stamp(available_at)
        if not _in_window(stamp, None, upper):
            continue
        los: list[str] = []
        parsed = parse_block_span(str(note_id)) if note_id else None
        if parsed is not None:
            if reading_map.withheld(parsed[0], parsed[1]):
                continue
            los = reading_map.los_for_span(parsed[0], parsed[1])
        elif note_id:
            # A question on a withheld note is rejected before any fallback to its item (F43).
            if _note_withheld(connection, reading_map, view, str(note_id)):
                continue
            los = reading_map.los_for_note(str(note_id))
        if not los and item_id:
            lo = reading_map.lo_for_item(str(item_id))
            los = [lo] if lo else []
        if not los:
            continue
        subkind = str(answer_mode) if answer_mode in TUTOR_ANSWER_MODES else UNKNOWN_ANSWER_MODE
        events.append(ListedEvent("reader_tutor_exchange", subkind, "question_events", str(row_id), stamp,
                             tuple(dict.fromkeys(los)), named_facets=_named_facets(facets_json)))
    return events


def _question_los(reading_map: ReadingMap, extraction_id: str, section_id: str, anchors: Any) -> tuple[str, ...]:
    try:
        spans = [str(span) for span in json.loads(anchors)] if anchors else []
    except (TypeError, ValueError):
        spans = []
    if any(reading_map.withheld(extraction_id, span) for span in spans) or reading_map.withheld(extraction_id, None):
        return ()
    los = reading_map.los_for_section(extraction_id, section_id)
    if not los:
        for span in spans:
            los = los + [lo for lo in reading_map.los_for_span(extraction_id, span) if lo not in los]
    return tuple(los)


def _question_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                     view: Any = None) -> list[ListedEvent]:
    events: list[ListedEvent] = []
    if view is None:
        return events  # no material view, no question read (fail closed)
    for question in view.answered_questions(connection, IN_PASSAGE_STYLES):
        row_id, extraction_id, section_id = question["id"], question["extraction_id"], question["section_id"]
        style, anchors, answered_at = (question["question_style"], question["anchor_span_ids_json"],
                                       question["answered_at"])
        stamp = source_stamp(answered_at)
        if not _in_window(stamp, lower, upper) or _recorded(connection, "in_passage_question", str(style),
                                                            "reader_authored_questions", str(row_id), view=view):
            continue
        los = _question_los(reading_map, str(extraction_id), str(section_id), anchors)
        if not los:
            continue
        events.append(ListedEvent("in_passage_question", str(style), "reader_authored_questions", str(row_id), stamp, los,
                             identity=f"reader_authored_questions:{row_id}"))
    return events


def _owner_placed_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                         view: Any = None) -> list[ListedEvent]:
    events: list[ListedEvent] = []
    for row in view.rows(connection, "interaction_events", "kind = 'reader_answer_submitted'"):
        row_id, administration_id, created_at = row["id"], row.get("administration_id"), row.get("created_at")
        item_id = view.administration_item(connection, administration_id)
        stamp = source_stamp(created_at)
        if not _in_window(stamp, lower, upper) or not item_id or _recorded(
                connection, "in_passage_question", "owner_placed", "interaction_events", str(row_id), view=view):
            continue
        lo = reading_map.lo_for_item(str(item_id))
        if not lo:
            continue
        events.append(ListedEvent("in_passage_question", "owner_placed", "interaction_events", str(row_id), stamp, (lo,),
                             identity=f"administration:{administration_id or row_id}"))
    return events


def _verdict_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                    view: Any = None) -> list[ListedEvent]:
    events: list[ListedEvent] = []
    if view is None:
        return events  # no material view, no question read (fail closed)
    first: dict[str, tuple[str, str, str]] = {}
    for row in view.rows(connection, "judgment_ledger", "task = ? AND left_kind = 'reader_authored_question'",
                         (SELF_CHECK_TASK,), order="created_at, rowid"):
        row_id, question_id, verdict, created_at = row["id"], row["left_id"], row["verdict"], row["created_at"]
        stamp = source_stamp(created_at)
        if stamp is None:
            continue
        current = first.get(str(question_id))
        if current is None or stamp < current[2]:
            first[str(question_id)] = (str(row_id), str(verdict), stamp)
    for question_id, (row_id, verdict, stamp) in sorted(first.items()):
        subkind = SELF_CHECK_CLASSES.get(verdict)
        if subkind is None or not _in_window(stamp, lower, upper) or _recorded(
                connection, "in_passage_question", subkind, "judgment_ledger", row_id, view=view):
            continue
        question = view.question(connection, question_id)
        if question is None or str(question["question_style"]) not in IN_PASSAGE_STYLES:
            continue
        los = _question_los(reading_map, str(question["extraction_id"]), str(question["section_id"]),
                            question["anchor_span_ids_json"])
        if not los:
            continue
        events.append(ListedEvent("in_passage_question", subkind, "judgment_ledger", row_id, stamp, los,
                             identity=f"self_check:{question_id}"))
    return events


_COLLECTORS: tuple[Callable[..., list[ListedEvent]], ...] = (
    _section_events, _exposure_events, _tutor_events, _question_events, _owner_placed_events, _verdict_events,
)


def listed_events(connection: Any, reading_map: Any, lower: str | None, upper: str, *, view: Any) -> list[ListedEvent]:
    """Every listed learning opportunity in the window, as ``reading_map`` and ``view`` see them: this list and its
    reading, with no receipt, no cap and no write. Data capture's exposure sweep reads the same list
    (:mod:`learnloop.data_capture.reading_exposures`), since it stands whatever this module's switches say."""

    events: list[ListedEvent] = []
    for collect in _COLLECTORS:
        events.extend(collect(connection, reading_map, lower, upper, view=view))
    return events

__all__ = [
    "EXPOSURE_CONTEXTS",
    "IN_PASSAGE_STYLES",
    "ListedEvent",
    "ReadingMap",
    "SELF_CHECK_CLASSES",
    "SELF_CHECK_TASK",
    "SWEEP_OVERLAP",
    "TUTOR_ANSWER_MODES",
    "TUTOR_CONTEXTS",
    "UNKNOWN_ANSWER_MODE",
    "listed_events",
    "source_stamp",
]
