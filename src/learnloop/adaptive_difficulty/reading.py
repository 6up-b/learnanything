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
* ``lesson`` (teacher TE3a, spec_teacher_v1 §14.2; behind
  ``adaptive_difficulty.lesson_opportunities`` at its successor): a closed
  lesson's node with an LO whose final status is ``landed`` or ``taught``
  (the subkind), from the lesson's receipt (:mod:`.lessons`), dose one on
  each of the LO's facets; once per node and LO.

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

import logging
from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from learnloop.attempts.salience_firewall import LEARNING_OPPORTUNITY_KINDS, LEARNING_OPPORTUNITY_SOURCES
from learnloop.reading_sources import (
    EXPOSURE_CONTEXTS,
    IN_PASSAGE_STYLES,
    SWEEP_OVERLAP,
    TUTOR_ANSWER_MODES,
    UNKNOWN_ANSWER_MODE,
    ReadingMap,
    ListedEvent as _Event,
    listed_events,
    source_stamp as _stamp,
)
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.stores import ad_receipts as store

from learnloop.adaptive_difficulty.switches import receipts_enabled

LOG = logging.getLogger(__name__)

MAPPING_VERSION = "ad_reading_map_v1"
KINDS = LEARNING_OPPORTUNITY_KINDS
PASSAGES_PER_LO_PER_DAY = 1
TUTOR_EXCHANGES_PER_LO_PER_DAY = 3

#: The carve-out's allowlist: (kind, subkind, source table). One list, the
#: firewall's (AD2+AD3 moved it there; G-AD3-13).
SOURCES: tuple[tuple[str, str, str], ...] = LEARNING_OPPORTUNITY_SOURCES


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
        self._irs: dict[str, Any] = {}
        # Router speed stage 2, item 1 (:mod:`.reading_cache`; landing ruling R1): inside one objective job, each
        # section's LOs, each reading's span → section map and its IR are held for the job, a snapshot as of the job's
        # first read; outside a job, main's per-map memo alone. Only with [router_objective] held_reading_map (Codex
        # review F2; off: main's map exactly).
        from learnloop.adaptive_difficulty import reading_cache

        self._held_on = reading_cache.held_on(getattr(vault, "config", None))
        # What the section mapping is handed besides the IR (RO2 landing ruling R6): the operation's
        # projected repository, so the span translator's re-read aliases load each reading's IR through
        # the view too, whichever repository this map was built with.
        from learnloop.adaptive_difficulty.projection import project_repository

        self._projected = project_repository(repository, self.view)

    def _document_ir(self, extraction_id: str) -> Any:
        """The extraction's IR through the reading chokepoint (RO2 landing ruling R6): the material view's
        ``document_ir`` (none for a reading the withheld material touches, or while the view is
        unavailable). The incumbent's mapping loads the IR raw, which AD's guard refuses inside an
        operation, poisoning it and rolling back every AD write of the serve. Cached per map; inside an objective job
        with the held map on, the job's snapshot (landing ruling R1: loaded at the job's first read of the reading)."""

        if extraction_id not in self._irs:
            try:
                raw = getattr(self.repository, "_ad_raw_repository", self.repository)
                job = self._job()
                self._irs[extraction_id] = (self.view.document_ir(raw, extraction_id) if job is None
                                            else job.document_ir(self.view, raw, extraction_id))
            except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
                self._irs[extraction_id] = None
        return self._irs[extraction_id]

    def _job(self) -> Any:
        """The objective job's hold as this map's view reads it (:func:`.reading_cache.job_hold`: the view's epoch
        checked against the job's, a protection change dropping what the job held), or None: switched off (main's
        map exactly), outside a job, or no epoch to key by. Asked at every lookup this map computes."""

        if not self._held_on:
            return None
        from learnloop.adaptive_difficulty import reading_cache

        try:
            return reading_cache.job_hold(self.view, self.repository)
        except Exception:  # noqa: BLE001 - nothing held: the map computes as main does
            return None

    def _held_section(self, job: Any, extraction_id: str, section_id: str) -> tuple[str, ...]:
        """A section's LOs (the caller's withheld rule let it through) from the job's hold, else
        ``learning_objects_for_section_in_ir`` over the job's IR of the reading, held for the job. A failed mapping
        maps to nothing and is not held."""

        from learnloop.section_map import learning_objects_for_section_in_ir

        found = job.get(self.vault, "section", str(extraction_id), str(section_id))
        if found is None:
            ir = self._document_ir(extraction_id)
            if ir is None:
                return ()
            try:
                found = tuple(learning_objects_for_section_in_ir(
                    self.vault, self._projected, ir, extraction_id=extraction_id, section_id=section_id))
            except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
                return ()
            job.put(self.vault, found, "section", str(extraction_id), str(section_id))
        return found

    def _held_span_section(self, job: Any, extraction_id: str, span_id: str) -> str | None:
        """The section of the job's IR of the reading holding a span (``section_map.section_id_in_ir``), from the
        reading's span → section map, held for the job. None for an unreadable reading or a span in no section."""

        from learnloop.section_map import extraction_sections

        sections = job.get(None, "span_sections", str(extraction_id))
        if sections is None:
            ir = self._document_ir(extraction_id)
            if ir is None:
                return None
            try:
                sections = MappingProxyType(
                    {str(span): str(section) for span, section in extraction_sections(ir)[2].items()})
            except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
                return None
            job.put(None, sections, "span_sections", str(extraction_id))
        return sections.get(str(span_id))

    def _landing_section(self, extraction_id: str, section_id: str) -> list[str]:
        """The landing code's own mapping of a section (main ``e9ceaf8d44``), over the IR this map loads once."""

        from learnloop.section_map import learning_objects_for_section_in_ir

        ir = self._document_ir(extraction_id)
        try:
            return [] if ir is None else list(learning_objects_for_section_in_ir(
                self.vault, self._projected, ir, extraction_id=extraction_id, section_id=section_id))
        except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
            return []

    def _landing_span(self, extraction_id: str, span_id: str) -> list[str]:
        """The landing code's own mapping of a span (main ``e9ceaf8d44``), over the IR this map loads once."""

        from learnloop.section_map import learning_objects_for_span_in_ir

        ir = self._document_ir(extraction_id)
        try:
            return [] if ir is None else list(learning_objects_for_span_in_ir(
                self.vault, self._projected, ir, extraction_id=extraction_id, span_id=span_id))
        except Exception:  # noqa: BLE001
            return []

    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]:
        # The sweep's withheld rule first, asked of the view fresh at every call and before any memo is read (landing
        # ruling R1): a reading the withheld material touches maps to nothing. Then this map's memo; then, inside an
        # objective job, the job's hold (a snapshot as of its first read), else the landing code's mapping.
        if self.withheld(extraction_id, None):
            return []
        key = (extraction_id, section_id)
        if key not in self._sections:
            job = self._job()
            self._sections[key] = (self._landing_section(extraction_id, section_id) if job is None
                                   else list(self._held_section(job, extraction_id, section_id)))
        return self._sections[key]

    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]:
        # ``learning_objects_for_span_in_ir``: the span's section in the IR, then that section's mapping; the withheld
        # rule first, fresh at every call before any memo (R1), as for a section.
        if self.withheld(extraction_id, span_id):
            return []
        key = (extraction_id, span_id)
        if key not in self._spans:
            job = self._job()
            if job is None:
                self._spans[key] = self._landing_span(extraction_id, span_id)
            else:
                section = self._held_span_section(job, extraction_id, span_id)
                self._spans[key] = [] if section is None else list(self._held_section(job, extraction_id, section))
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


@entry(read_only=True)
def section_learning_objects(vault: Any, repository: Any, extraction_id: str, section_id: str, *,
                             view: Any = None) -> list[str]:
    """Router objective RO4 (landing, after RO2's ruling R6): a reading section's LOs as AD maps them, for the
    rollouts' reading action, so its doses land on the LOs AD's reading curve (``reading_dose``) counts: through
    the map's ``MaterialView.document_ir`` after the sweep's withheld rule (a reading the withheld material
    touches maps to nothing), inside a read-only AD operation."""

    return list(VaultReadingMap(vault, repository, view).los_for_section(extraction_id, section_id))


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
    if event.kind == "lesson":
        # Teacher TE3a: once per lesson node and LO (the identity is ``<lesson id>/<node id>``).
        return f"lesson:{event.identity}:{lo_id}"
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
        events = listed_events(connection, mapping, lower, upper, view=material)
        from learnloop.adaptive_difficulty.successor import lesson_opportunities_on

        if lesson_opportunities_on(vault.config):
            # Teacher TE3a (spec_teacher_v1 §14.2): every closed lesson's landed or taught node not yet recorded.
            from learnloop.adaptive_difficulty.lessons import lesson_events

            events.extend(lesson_events(connection, mapping, upper, view=material, vault=vault))
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
    "TUTOR_ANSWER_MODES",
    "UNKNOWN_ANSWER_MODE",
    "KINDS",
    "MAPPING_VERSION",
    "ReadingMap",
    "SOURCES",
    "SweepResult",
    "VaultReadingMap",
    "listed_events",
    "section_learning_objects",
    "sweep",
]
