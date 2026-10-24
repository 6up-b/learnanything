"""Reading and other learning opportunities, frozen in a receipt (spec §5.11, D20, D22; AD1).

At every plan serve, in the serve transaction and before its forecasts, the
sweep records each learning opportunity whose source row was written since
the last sweep (no later than the serve); ``learnloop ad backfill --reading``
sweeps the whole history once. Rows go to ``ad_reading_opportunities``
(RECEIPT, append-only): one per (opportunity, LO), with its kind and subkind,
the source row's id and write time, the facets and doses the mapping resolved
at the sweep, the mapping version and the authority class ``salience_only``.

**Only the listed sources** (:data:`SOURCES`: the reading-signal firewall's
carve-out allowlist, ``attempts.salience_firewall.LEARNING_OPPORTUNITY_SOURCES``,
moved there by the AD2+AD3 stage so the sweep and the carve-out read one list):

* ``reading``: a section completed in the Reader
  (``reader_section_progress.completed_at``, stamped once: ``section_read``),
  and a span view (``source_exposure_events`` in a learner-facing context,
  :data:`EXPOSURE_CONTEXTS`) unless the span is a worked example
  (``passage_viewed``); every LO whose provenance cites the section or span;
  a section once per section and LO, passage views one per LO per day;
* ``reader_tutor_exchange``: an answered tutor question asked while reading
  (``question_events`` with context ``reader`` or ``library``; its subkind is
  the answer mode stored at the ask, ``unknown`` when none was);
  its LO, or its facets where ``facets_json`` names them; three per LO per day.
  Its source time is when the answer completed (``answered_at``, else the
  row's ``created_at`` when it was written answered; Codex review F4);
* ``worked_example``: a worked-example block (found by its role) the learner
  was shown (``shown``: a span view of it) or that sits in a section they
  completed (``in_completed_section``); once per example;
* ``in_passage_question``: an answered ``reader_authored_questions`` row of
  style ``recall``, ``next_step``, ``why_step`` or ``assumptions`` (the
  style), and an owner-placed reading question's ``reader_answer_submitted``
  event (``owner_placed``); once per question. A ``reconstruct`` question,
  a dismissed question and an unanswered prompt write nothing.
* D22's verdict rows: a judged in-passage question also writes one row from
  its FIRST ``judgment_ledger`` self-check verdict (task
  ``reader_quick_check_self_check``): ``self_check:matched`` (matches) or
  ``self_check:missed`` (partly, no), with the question's LOs and doses. A
  later changed verdict writes nothing.

**Never a magnitude.** No dwell, scroll, highlight, skip, visibility segment,
active time or answer text is read: each query selects ids, keys and write
times only, and the receipt has no column that could hold one. No model call.

**Frozen.** A source row written after a serve is not recorded by that
serve's sweep; replay orders opportunities by their source write time, so it
rebuilds the state each serve saw. A later deletion of the source (its
extraction removed with ``delete_source_artifact``) leaves the receipts.
The AD replayer reads them only through the firewall's carve-out
(``salience_firewall.learning_opportunity_events``, A12).
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.logs import warn_failure
from learnloop.adaptive_difficulty.operation import entry

import json
import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Protocol

from learnloop.attempts.salience_firewall import (
    IN_PASSAGE_STYLES,
    LEARNING_OPPORTUNITY_KINDS,
    LEARNING_OPPORTUNITY_SOURCES,
    TUTOR_ANSWER_MODES,
    UNKNOWN_ANSWER_MODE,
)
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.stores import ad_receipts as store

from learnloop.adaptive_difficulty.switches import receipts_enabled

LOG = logging.getLogger(__name__)

MAPPING_VERSION = "ad_reading_map_v1"
KINDS = LEARNING_OPPORTUNITY_KINDS
SELF_CHECK_TASK = "reader_quick_check_self_check"
SELF_CHECK_CLASSES = {"matches": "self_check:matched", "partly": "self_check:missed", "no": "self_check:missed"}
#: The span-view contexts that are the learner reading (the Guide, the Reader,
#: the library, passages the tutor cites, provenance and repair passages). The
#: owner's review tooling (registry_review, conflict_review, gate_diagnostic)
#: is not reading.
EXPOSURE_CONTEXTS = ("reader", "reader_restoration", "library", "tutor_citation", "provenance", "provenance_panel",
                     "remediation", "remediation_delivery", "other")
TUTOR_CONTEXTS = ("reader", "library")
PASSAGES_PER_LO_PER_DAY = 1
TUTOR_EXCHANGES_PER_LO_PER_DAY = 3
#: A serve's sweep re-reads this far behind the newest recorded source time,
#: so a source row stamped a little before an earlier sweep but committed
#: after it (a tutor answer completing, a clock skew) is still recorded once.
SWEEP_OVERLAP = timedelta(hours=1)

#: The carve-out's allowlist: (kind, subkind, source table). One list, the
#: firewall's (AD2+AD3 moved it there; G-AD3-13).
SOURCES: tuple[tuple[str, str, str], ...] = LEARNING_OPPORTUNITY_SOURCES


def _stamp(value: Any) -> str | None:
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


class VaultReadingMap:
    """The default map: ``reader.reader_progression``'s section/span -> LO rule,
    worked examples by role (``source_retrieval.corpus.role_keys``), facets by
    the LO's facet union. Items, facets and held-out material come from the
    operation's material view (A8; Codex verify F19): a withheld item maps to no
    LO and names no facet, and held-out spans are withheld. Cached per sweep."""

    def __init__(self, vault: Any, repository: Any, view: Any = None) -> None:
        from learnloop.adaptive_difficulty.material_view import material_view

        self.vault = vault
        self.repository = repository
        self.view = material_view(vault, repository, view)
        self._sections: dict[tuple[str, str], list[str]] = {}
        self._spans: dict[tuple[str, str], list[str]] = {}
        self._examples: dict[str, set[str]] = {}

    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]:
        from learnloop.reader.reader_progression import learning_objects_for_section

        key = (extraction_id, section_id)
        if key not in self._sections:
            try:
                self._sections[key] = list(learning_objects_for_section(
                    self.vault, self.repository, extraction_id=extraction_id, section_id=section_id))
            except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
                self._sections[key] = []
        return self._sections[key]

    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]:
        from learnloop.reader.reader_progression import learning_objects_for_span

        key = (extraction_id, span_id)
        if key not in self._spans:
            try:
                self._spans[key] = list(learning_objects_for_span(
                    self.vault, self.repository, extraction_id=extraction_id, span_id=span_id))
            except Exception:  # noqa: BLE001
                self._spans[key] = []
        return self._spans[key]

    def section_spans(self, extraction_id: str, section_id: str) -> list[str]:
        return self.view.section_spans(extraction_id, section_id)

    def worked_example_spans(self, extraction_id: str) -> set[str]:
        if extraction_id not in self._examples:
            from learnloop.db.connection import connect

            try:
                with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
                    self._examples[extraction_id] = self.view.worked_example_spans(connection, extraction_id)
            except Exception:  # noqa: BLE001
                warn_failure(LOG, "worked examples of %s unreadable: none", extraction_id)
                self._examples[extraction_id] = set()
        return self._examples[extraction_id]

    def reading_order(self, extraction_id: str) -> dict[str, int]:
        return self.view.reading_order(extraction_id)

    def withheld(self, extraction_id: str, span_id: str | None) -> bool:
        # Held-out material, a reading the withheld material touches (round 8), or everything while
        # the predicate is unavailable (fail closed).
        return self.view.reading_withheld(extraction_id) or self.view.material_withheld(extraction_id, span_id)

    def note_withheld(self, note_id: str) -> bool:
        """Whether a note is withheld (a held-out source's canonical note; fix round 13, F43)."""

        from learnloop.db.connection import connect

        with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
            return self.view.note_withheld(connection, note_id)

    def los_for_note(self, note_id: str) -> list[str]:
        # Read through the material view (F43): a withheld note maps to no LO.
        if self.note_withheld(note_id):
            return []
        note = getattr(self.vault, "notes", {}).get(note_id)
        return [str(lo) for lo in getattr(note, "related_los", None) or []] if note is not None else []

    def lo_for_item(self, practice_item_id: str) -> str | None:
        # A withheld item (an owner-placed or tutor question on it) maps to no LO (Codex verify F19).
        return self.view.lo_for_item(practice_item_id)

    def facets_for_lo(self, learning_object_id: str) -> list[str]:
        lo = getattr(self.vault, "learning_objects", {}).get(learning_object_id)
        if lo is None:
            return []
        # The LO's authored facets, else its visible active items' (Codex verify F19).
        return self.view.lo_facets(lo)


@dataclass(frozen=True)
class _Event:
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


@dataclass
class SweepResult:
    written: int = 0
    considered: int = 0
    by_kind: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"written": self.written, "considered": self.considered, "by_kind": dict(sorted(self.by_kind.items()))}


def _doses(reading_map: ReadingMap, lo_id: str, named: Sequence[str]) -> dict[str, float]:
    own = reading_map.facets_for_lo(lo_id)
    direct = [facet for facet in named if facet in own] if named else []
    if direct:
        return {facet: 1.0 for facet in sorted(set(direct))}
    if not own:
        return {}
    share = round(1.0 / len(own), 12)
    return {facet: share for facet in own}


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
                    view: Any = None) -> list[_Event]:
    events: list[_Event] = []
    # The registry's rule withholds a section with any held-out span in it (the view's rows).
    for row in view.rows(connection, "reader_section_progress", "completed_at IS NOT NULL"):
        extraction_id, section_id, completed_at = row["extraction_id"], row["section_id"], row["completed_at"]
        stamp = _stamp(completed_at)
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
        events.append(_Event("reading", "section_read", "reader_section_progress", section_key, stamp, los,
                             identity=section_key))
        examples = reading_map.worked_example_spans(extraction_id)
        for span in spans:
            if span in examples:
                example = f"{extraction_id}/{span}"
                events.append(_Event("worked_example", "in_completed_section", "reader_section_progress", example,
                                     stamp, tuple(reading_map.los_for_span(extraction_id, span)) or los,
                                     identity=example))
    return events


def _exposure_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                     view: Any = None) -> list[_Event]:
    events: list[_Event] = []
    marks = ",".join("?" for _ in EXPOSURE_CONTEXTS)
    for row in view.rows(connection, "source_exposure_events", f"context IN ({marks})", EXPOSURE_CONTEXTS):
        row_id, extraction_id, span_id, created_at = row["id"], row["extraction_id"], row["span_id"], row["created_at"]
        stamp = _stamp(created_at)
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
            events.append(_Event("worked_example", "shown", "source_exposure_events", str(row_id), stamp, los,
                                 identity=example))
        else:
            events.append(_Event("reading", "passage_viewed", "source_exposure_events", str(row_id), stamp, los))
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
                  view: Any = None) -> list[_Event]:
    from learnloop.ingest.locators import parse_block_span

    events: list[_Event] = []
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
        stamp = _stamp(available_at)
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
        events.append(_Event("reader_tutor_exchange", subkind, "question_events", str(row_id), stamp,
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
                     view: Any = None) -> list[_Event]:
    events: list[_Event] = []
    if view is None:
        return events  # no material view, no question read (fail closed)
    for question in view.answered_questions(connection, IN_PASSAGE_STYLES):
        row_id, extraction_id, section_id = question["id"], question["extraction_id"], question["section_id"]
        style, anchors, answered_at = (question["question_style"], question["anchor_span_ids_json"],
                                       question["answered_at"])
        stamp = _stamp(answered_at)
        if not _in_window(stamp, lower, upper) or _recorded(connection, "in_passage_question", str(style),
                                                            "reader_authored_questions", str(row_id), view=view):
            continue
        los = _question_los(reading_map, str(extraction_id), str(section_id), anchors)
        if not los:
            continue
        events.append(_Event("in_passage_question", str(style), "reader_authored_questions", str(row_id), stamp, los,
                             identity=f"reader_authored_questions:{row_id}"))
    return events


def _owner_placed_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                         view: Any = None) -> list[_Event]:
    events: list[_Event] = []
    for row in view.rows(connection, "interaction_events", "kind = 'reader_answer_submitted'"):
        row_id, administration_id, created_at = row["id"], row.get("administration_id"), row.get("created_at")
        item_id = view.administration_item(connection, administration_id)
        stamp = _stamp(created_at)
        if not _in_window(stamp, lower, upper) or not item_id or _recorded(
                connection, "in_passage_question", "owner_placed", "interaction_events", str(row_id), view=view):
            continue
        lo = reading_map.lo_for_item(str(item_id))
        if not lo:
            continue
        events.append(_Event("in_passage_question", "owner_placed", "interaction_events", str(row_id), stamp, (lo,),
                             identity=f"administration:{administration_id or row_id}"))
    return events


def _verdict_events(connection: Any, reading_map: ReadingMap, lower: str | None, upper: str,
                    view: Any = None) -> list[_Event]:
    events: list[_Event] = []
    if view is None:
        return events  # no material view, no question read (fail closed)
    first: dict[str, tuple[str, str, str]] = {}
    for row in view.rows(connection, "judgment_ledger", "task = ? AND left_kind = 'reader_authored_question'",
                         (SELF_CHECK_TASK,), order="created_at, rowid"):
        row_id, question_id, verdict, created_at = row["id"], row["left_id"], row["verdict"], row["created_at"]
        stamp = _stamp(created_at)
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
        events.append(_Event("in_passage_question", subkind, "judgment_ledger", row_id, stamp, los,
                             identity=f"self_check:{question_id}"))
    return events


_COLLECTORS: tuple[Callable[..., list[_Event]], ...] = (
    _section_events, _exposure_events, _tutor_events, _question_events, _owner_placed_events, _verdict_events,
)


def _capped(kind: str, subkind: str) -> tuple[str, int] | None:
    """A capped kind's occupancy bucket and its cap per LO and day (§5.11), or None."""

    if kind == "reading" and subkind == "passage_viewed":
        return "reading:passage_viewed", PASSAGES_PER_LO_PER_DAY
    if kind == "reader_tutor_exchange":
        return "reader_tutor_exchange", TUTOR_EXCHANGES_PER_LO_PER_DAY
    return None


def occupancy(connection: Any, view: Any) -> dict[tuple[str, str, str], int]:
    """Each capped bucket's occupancy, ``(bucket, LO, day) -> receipts``, counted over the receipts
    AD's material view sees (Codex verify F44, fix round 13): a receipt from withheld material is,
    for AD, a receipt never written, so it occupies no slot of a daily cap."""

    counts: dict[tuple[str, str, str], int] = {}
    for row in view.reading_opportunities(connection):
        capped = _capped(str(row.get("kind")), str(row.get("subkind")))
        if capped is not None:
            key = (capped[0], str(row.get("learning_object_id")), str(row.get("source_written_at") or "")[:10])
            counts[key] = counts.get(key, 0) + 1
    return counts


def _keys(connection: Any, event: _Event, lo_id: str, occupied: dict[tuple[str, str, str], int]) -> str | None:
    """The opportunity's key inside its cap, or None when the cap is full.

    A capped kind's occupancy is the view's (``occupied``, counted by :func:`occupancy` and kept up
    to date as the sweep writes), and its key names the source event (fix round 13, F44): keys
    never collide, so a public event is admitted beside a withheld receipt's existing key."""

    day = event.written_at[:10]
    capped = _capped(event.kind, event.subkind)
    if capped is not None:
        bucket, cap = capped
        if occupied.get((bucket, lo_id, day), 0) >= cap:
            return None
        occupied[(bucket, lo_id, day)] = occupied.get((bucket, lo_id, day), 0) + 1
        return f"{bucket}:{lo_id}:{day}:{event.source_table}:{event.source_id}"
    if event.kind == "reading":
        return f"reading:section_read:{event.identity}:{lo_id}"
    if event.kind == "worked_example":
        return f"worked_example:{event.identity}:{lo_id}"
    if event.subkind.startswith("self_check:"):
        return f"{event.identity}:{lo_id}"
    return f"in_passage_question:{event.identity}:{lo_id}"


def _taken_offers(connection: Any, view: Any) -> dict[str, str]:
    from learnloop.db.stores import ad_serving

    if not ad_serving.has_table(connection, ad_serving.DOSE_OFFERS):
        return {}
    from learnloop.adaptive_difficulty.dose import taken_offers

    return taken_offers(connection, view=view)


def _offer_for(offers: Mapping[str, str], event: "_Event") -> str | None:
    if not offers:
        return None
    if event.source_table == "reader_authored_questions":
        return offers.get(f"question:{event.source_id}")
    if event.kind == "worked_example":
        return offers.get(f"span:{event.identity}")
    return None


@entry(savepoint=True)
def sweep(vault: Any, repository: Any, *, as_of: str, sweep_kind: str = "serve", sweep_ref: str | None = None,
          reading_map: ReadingMap | None = None, clock: Clock | None = None, view: Any = None) -> SweepResult:
    """Record every listed opportunity written no later than ``as_of``.

    Call it inside the deciding transaction (the serve's) or let it open its
    own (the backfill). A serve's sweep reads from :data:`SWEEP_OVERLAP`
    before the newest recorded source time; the backfill reads everything.
    Idempotent: each opportunity is written once, and each cap counts what
    is already recorded. Off with ``forecast_receipts`` (or the master
    switch): nothing is read or written."""

    result = SweepResult()
    if not receipts_enabled(vault.config):
        return result
    upper = _stamp(as_of)
    if upper is None:
        raise ValueError(f"unreadable sweep instant {as_of!r}")
    from learnloop.adaptive_difficulty.material_view import material_view

    material = material_view(vault, repository, view if view is not None else getattr(reading_map, "view", None))
    mapping = reading_map or VaultReadingMap(vault, repository, material)
    if not material.available:
        # The held-out predicate is unavailable: nothing is recorded now (fail closed). The rows
        # stay unrecorded, so the next sweep that can tell reads them (its window starts from the
        # newest recorded source).
        return result
    swept_at = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        if not store.has_table(connection, store.READING):
            return result
        lower = None
        if sweep_kind == "serve":
            # The newest VISIBLE receipt's source time (fix round 12, found by the hardened contract):
            # a receipt from withheld material moves no window, so a later protected receipt never
            # hides an earlier public event from the serve's sweep.
            visible = [row.get("source_written_at") for row in material.reading_opportunities(connection)
                       if row.get("source_written_at")]
            newest = parse_utc(max(visible)) if visible else None
            lower = _stamp((newest - SWEEP_OVERLAP).isoformat()) if newest is not None else None
        events: list[_Event] = []
        for collect in _COLLECTORS:
            events.extend(collect(connection, mapping, lower, upper, view=material))
        events.sort(key=lambda event: (event.written_at, event.source_table, event.source_id, event.subkind))
        result.considered = len(events)
        # AD2+AD3 (§5.12): a taken dose offer's extra carries the offer's id on its receipt.
        offers = _taken_offers(connection, material)
        occupied = occupancy(connection, material)
        for event in events:
            for lo_id in event.learning_object_ids:
                if material.lookup(connection, store.READING, "kind = ? AND subkind = ? AND source_table = ? AND "
                                   "source_id = ? AND learning_object_id = ?",
                                   (event.kind, event.subkind, event.source_table, event.source_id, lo_id),
                                   stale_as_missing=True)[0] != "missing":
                    continue
                key = _keys(connection, event, lo_id, occupied)
                if key is None:
                    continue
                written = store.insert_reading_opportunity(connection, {
                    "protection_epoch": material.epoch,
                    "opportunity_key": key, "kind": event.kind, "subkind": event.subkind,
                    "source_table": event.source_table, "source_id": event.source_id,
                    "source_written_at": event.written_at, "learning_object_id": lo_id,
                    "facet_doses": _doses(mapping, lo_id, event.named_facets),
                    "dose_offer_id": _offer_for(offers, event),
                    "mapping_version": MAPPING_VERSION, "sweep": sweep_kind, "sweep_ref": sweep_ref,
                    "swept_at": swept_at,
                })
                if written is not None:
                    result.written += 1
                    result.by_kind[event.kind] = result.by_kind.get(event.kind, 0) + 1
    return result


__all__ = [
    "EXPOSURE_CONTEXTS",
    "IN_PASSAGE_STYLES",
    "KINDS",
    "MAPPING_VERSION",
    "ReadingMap",
    "SOURCES",
    "SweepResult",
    "VaultReadingMap",
    "sweep",
]
