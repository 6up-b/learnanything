"""Reader activity frozen for the delayed-completion definition (data capture; Codex re-review F1).

A section completed the hour before an answer leaves that answer warm, whatever adaptive difficulty is set to. AD's
reading receipts (``ad_reading_opportunities``) are written only under its ``forecast_receipts``, and its spec keeps
them so (G-AD1-11), so this is data capture's own record of the same facts: **the same list of sources**, read by the
collectors AD reads (:func:`learnloop.reading_sources.listed_events`), written to ``reading_exposure_receipts``.

What differs from AD's receipt, because the question differs. AD's is a dose on a learned state; this one is a fact the
outcome reads:

* **no cap**: the newest exposure is what the delay runs from, so a second passage view that day counts;
* **no material view and no withholding**: this is not AD's state, so no AD operation opens and none of its guard runs.
  Reading held-out material is an exposure all the same, and the row holds only its LO and the time;
* **no doses, no dwell, no answer text**: the fact and its source time, no more.

**One read** (landing ruling R1): :func:`read` is how ``router_outcomes_v3``, the time metric and the capture report see
Reader exposures: the stored receipts plus the source activity not yet swept, through the same collectors, the same
mapping and the same source time as the sweep. Correctness rests on this read, which lists every source row, so **the
sweep only freezes**: no answer depends on whether Today has run.

**The sweep and the foreground** (ruling R6). :func:`sweep` runs where Today prepares, so it reads only from the newest
recorded source time less AD's overlap (:data:`learnloop.reading_sources.SWEEP_OVERLAP`) and takes the write lock only when
it has something to write. A row it never reaches (stamped older than its window, or a section no LO named at the time)
stays where the whole read finds it. Today's other reads pass ``since`` (:func:`recent_since`, and for an answer
:func:`read_for_answer`), so nothing on the foreground lists the whole history: the rows that could change that answer are
the recent ones.

**The cost.** The whole read: one indexed lookup per Reader source row, and for each distinct section or span not on record
a document load and an LO scan, about 20 ms. Those mappings, empty results included, are kept for the process against the
vault's content and the source and coverage rows they read (:func:`_revision`), so a repeat costs lookups alone: no model
call, no write, no clock. Measured on copies of the owner's vaults in ``docs/reviews/data-capture-a1-a6-codex-review.md``.

Frozen where Today prepares (:func:`learnloop.daily_plan.measurement.settle`). Under either of data capture's switches, at
every version: a receipt changes nothing served, and only ``router_outcomes_v3`` and the time metric read it. Never
evidence, FSRS, the projection or replay (A12 stands: this writes nothing AD reads).
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, timedelta
import hashlib
import logging
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.data_capture.gates import OUTCOME_VERSION_V3, receipts_on, serving_on
from learnloop.db.stores import data_capture as store
from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS
from learnloop.reading_sources import SWEEP_OVERLAP, listed_events, source_stamp
from learnloop.vault.models import learning_object_facet_union
from learnloop import section_map

logger = logging.getLogger(__name__)

MAPPING_VERSION = "reading_exposure_map_v1"
#: Above any source time: a read has no clock, and a row stamped past the sweep's "now" is still read (AD's stamp form).
NO_UPPER = "9999-12-31T23:59:59.999999Z"


def _section_los(vault: Any, repository: Any, extraction_id: str, section_id: str) -> list[str]:
    """The LOs a section holds: its provenance-linked LOs and its coverage rows. Raises what it can't read."""

    found = list(section_map.learning_objects_for_section(
        vault, repository, extraction_id=extraction_id, section_id=section_id))
    with repository.connection() as connection:
        from learnloop.db.stores import section_coverage as coverage

        if coverage.table_present(connection):
            found.extend(coverage.learning_objects_named(connection, extraction_id, section_id))
    return list(dict.fromkeys(found))


def reading_learning_objects(vault: Any, repository: Any, target: Any) -> list[str]:
    """What a decision's objective freezes (:mod:`learnloop.daily_plan.measurement`) and what an exposure names."""

    if target is None:
        return []
    try:
        return _section_los(vault, repository, str(target.extraction_id), str(target.section_id))
    except Exception:  # noqa: BLE001 - an unreadable section has no objective; the decision stands
        logger.warning("data capture: a reading section's learning objects were not read", exc_info=True)
        return []


def _content_revision(vault: Any) -> str:
    """What the mapping reads of the vault: active LOs' and their facets' provenance, and the notes' canonical sources."""

    digest = hashlib.blake2b(digest_size=16)
    for lo_id, lo in sorted(vault.learning_objects.items()):
        digest.update(repr((lo_id, lo.status, lo.provenance.source_refs,
                            sorted(map(str, learning_object_facet_union(lo))))).encode())
    for facet_id, facet in sorted(getattr(vault, "evidence_facets", {}).items()):
        digest.update(repr((facet_id, facet.provenance.source_refs)).encode())
    for note_id, note in sorted(getattr(vault, "notes", {}).items()):
        digest.update(repr((note_id, getattr(note, "model_extra", None), getattr(note, "related_los", None))).encode())
    return digest.hexdigest()


def _revision(connection: Any, vault: Any) -> tuple[Any, ...]:
    """A mapping stands while these do: the vault's content, the readings and their aliases, the sources' artifacts, the
    coverage rows. A completed reading's document never changes, so its extraction id stands for it."""

    def stamp(table: str) -> tuple[Any, ...]:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
            return ()
        return tuple(connection.execute(f"SELECT COUNT(*), MAX(rowid) FROM {table}").fetchone())

    return (_content_revision(vault), *(stamp(table) for table in (
        "source_extraction_runs", "source_artifacts", "source_span_reanchors", "section_coverage")))


#: Each vault's mappings at its current revision, for the process: empty results included.
_MAPPINGS: OrderedDict[str, tuple[tuple[Any, ...], dict[tuple[str, str], list[str]], dict[tuple[str, str], list[str]]]] = OrderedDict()
_MAPPINGS_KEPT = 8


def _clear_mapping_cache() -> None:
    """A new process's view: what a test uses to say so."""

    _MAPPINGS.clear()


class _Map:
    """A section's and a span's LOs as the objective's freeze reads them (provenance and coverage rows), an item's, a
    note's. Nothing is withheld and no span is a worked example here: only the LO and the time are kept. A failure to read
    maps to nothing for this call and is not kept."""

    def __init__(self, vault: Any, repository: Any, connection: Any) -> None:
        self.vault, self.repository = vault, repository
        key = str(getattr(repository, "sqlite_path", ""))
        revision = _revision(connection, vault)
        entry = _MAPPINGS.get(key)
        if entry is None or entry[0] != revision:
            entry = (revision, {}, {})
            _MAPPINGS[key] = entry
            while len(_MAPPINGS) > _MAPPINGS_KEPT:
                _MAPPINGS.popitem(last=False)
        _MAPPINGS.move_to_end(key)
        self._sections, self._spans = entry[1], entry[2]

    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]:
        key = (extraction_id, section_id)
        if key not in self._sections:
            try:
                self._sections[key] = list(_section_los(self.vault, self.repository, extraction_id, section_id))
            except Exception:  # noqa: BLE001 - never kept: an exposure is not lost to a passing failure
                logger.warning("data capture: a section's learning objects were not read", exc_info=True)
                return []
        return self._sections[key]

    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]:
        key = (extraction_id, span_id)
        if key not in self._spans:
            try:
                self._spans[key] = list(section_map.learning_objects_for_span(
                    self.vault, self.repository, extraction_id=extraction_id, span_id=span_id))
            except Exception:  # noqa: BLE001 - as above
                logger.warning("data capture: a span's learning objects were not read", exc_info=True)
                return []
        return self._spans[key]

    def section_spans(self, _extraction_id: str, _section_id: str) -> list[str]:
        return []

    def worked_example_spans(self, _extraction_id: str) -> set[str]:
        return set()

    def withheld(self, _extraction_id: str, _span_id: str | None) -> bool:
        return False

    def note_withheld(self, _note_id: str) -> bool:
        return False

    def los_for_note(self, note_id: str) -> list[str]:
        note = getattr(self.vault, "notes", {}).get(note_id)
        return [str(lo) for lo in getattr(note, "related_los", None) or []] if note is not None else []

    def lo_for_item(self, practice_item_id: str) -> str | None:
        item = self.vault.practice_items.get(practice_item_id)
        return str(item.learning_object_id) if item is not None else None


class _Rows:
    """What AD's collectors read through its material view, read plainly; ``lookup`` asks this record, not AD's."""

    @staticmethod
    def _has(connection: Any, table: str) -> bool:
        return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone() is not None

    def rows(self, connection: Any, table: str, where: str = "", args: Iterable[Any] = (), *, order: str = "") -> list[dict[str, Any]]:
        if not self._has(connection, table):
            return []
        sql = f"SELECT * FROM {table}" + (f" WHERE {where}" if where else "") + (f" ORDER BY {order}" if order else "")
        return [dict(row) for row in connection.execute(sql, tuple(args))]

    def lookup(self, connection: Any, _table: str, where: str, args: Iterable[Any] = (), *,
               stale_as_missing: bool = False) -> tuple[str, Mapping[str, Any] | None]:
        if not store.reading_exposures_present(connection):
            return "missing", None  # below migration 239 nothing is on record: everything is still activity to read
        return ("ok", {}) if store.reading_exposure_recorded(connection, where, args) else ("missing", None)

    def answered_questions(self, connection: Any, styles: Sequence[str]) -> list[dict[str, Any]]:
        marks = ",".join("?" for _ in styles)
        return self.rows(connection, "reader_authored_questions",
                         f"answered_at IS NOT NULL AND status != 'dismissed' AND question_style IN ({marks})", styles)

    def question(self, connection: Any, question_id: Any) -> dict[str, Any] | None:
        found = self.rows(connection, "reader_authored_questions", "id = ?", (str(question_id),))
        return found[0] if found else None

    def administration_item(self, connection: Any, administration_id: Any) -> str | None:
        if not administration_id:
            return None
        found = self.rows(connection, "activity_administrations", "id = ?", (str(administration_id),))
        if not found or not found[0].get("surface_id"):
            return None
        surface = self.rows(connection, "activity_surfaces", "id = ?", (str(found[0]["surface_id"]),))
        return str(surface[0]["legacy_practice_item_id"]) if surface and surface[0].get("legacy_practice_item_id") else None


def _events(connection: Any, vault: Any, repository: Any, *, lower: str | None = None, upper: str = NO_UPPER) -> list[Any]:
    """The listed activity not yet on record since ``lower`` (all of it with none): what the sweep freezes and what
    :func:`read` adds are this one list."""

    return listed_events(connection, _Map(vault, repository, connection), lower, upper, view=_Rows())


def recent_since(connection: Any) -> str | None:
    """Where the foreground reads from: the newest source time on record less AD's overlap, so a source row stamped a
    little before it is still read. None with nothing on record."""

    newest = store.newest_reading_exposure(connection) if store.reading_exposures_present(connection) else None
    parsed = parse_utc(newest) if newest else None
    return source_stamp((parsed - SWEEP_OVERLAP).isoformat()) if parsed is not None else None


def not_yet_swept(connection: Any, vault: Any, repository: Any, *, since: str | None = None) -> list[tuple[str, str]]:
    """``(LO, source time)`` of the listed activity no sweep has recorded yet. Read-only."""

    return sorted({(str(lo), str(event.written_at)) for event in _events(connection, vault, repository, lower=since)
                   for lo in event.learning_object_ids})


def read(connection: Any, vault: Any, repository: Any, *, since: str | None = None) -> list[tuple[str, str]]:
    """Every Reader exposure, ``(LO, source time)``: the stored receipts plus the source activity not yet swept.

    The one read of them (R1), the same before and after a sweep. Read-only, whichever connection and repository it is
    given, and at any switch: reading an exposure changes nothing served. ``since`` lists only activity after it (the
    foreground's, see the module's note); the stored receipts are always all read."""

    return sorted({*store.reading_receipts(connection), *not_yet_swept(connection, vault, repository, since=since)})


def read_for_answer(connection: Any, vault: Any, repository: Any, *, answered_at: str) -> list[tuple[str, str]]:
    """:func:`read` for judging one answer on the foreground: activity that could have made it warm, or newer than the
    sweep's window. An exposure older than the delay before the answer can't change it."""

    recent = recent_since(connection)
    parsed = parse_utc(answered_at)
    window = (source_stamp((parsed - timedelta(seconds=RETENTION_MIN_DELAY_SECONDS) - SWEEP_OVERLAP).isoformat())
              if parsed is not None else None)
    since = min(recent, window) if recent is not None and window is not None else None
    return read(connection, vault, repository, since=since)


def for_version(connection: Any, vault: Any, repository: Any, version: str, *, recent: bool = False) -> list[tuple[str, str]] | None:
    """:func:`read` for a derivation at ``version`` (``recent``: on the foreground, from :func:`recent_since`); None below
    ``router_outcomes_v3``, which reads no reading receipt."""

    if version != OUTCOME_VERSION_V3:
        return None
    return read(connection, vault, repository, since=recent_since(connection) if recent else None)


def sweep(vault: Any, repository: Any, *, clock: Clock | None = None) -> int:
    """Freeze the listed Reader activity since the window's start (:func:`recent_since`); how many rows it wrote. Idempotent;
    a no-op with both of data capture's switches off or before migration 239. The write lock only with rows to write."""

    if not (receipts_on(vault.config) or serving_on(vault.config)):
        return 0
    swept_at = utc_now_iso(clock)
    upper = (clock or SystemClock()).now().astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    with repository.connection() as connection:
        if not store.reading_exposures_present(connection):
            return 0
        events = _events(connection, vault, repository, lower=recent_since(connection), upper=upper)
    if not events:
        return 0
    written = 0
    with repository.atomic(), repository.connection() as connection:
        for event in events:
            for lo in event.learning_object_ids:
                written += bool(store.insert_reading_exposure(
                    connection, kind=event.kind, subkind=event.subkind, source_table=event.source_table,
                    source_id=event.source_id, source_written_at=event.written_at, learning_object_id=lo,
                    mapping_version=MAPPING_VERSION, swept_at=swept_at))
    return written


def sweep_quietly(vault: Any, repository: Any, *, clock: Clock | None = None) -> int:
    """:func:`sweep`, never raising: the record of an exposure never blocks Today; the next sweep reads it."""

    try:
        return sweep(vault, repository, clock=clock)
    except Exception:  # noqa: BLE001 - its transaction rolled back
        logger.warning("data capture: Reader exposures were not recorded", exc_info=True)
        return 0


__all__ = [
    "MAPPING_VERSION",
    "for_version",
    "not_yet_swept",
    "read",
    "read_for_answer",
    "reading_learning_objects",
    "recent_since",
    "sweep",
    "sweep_quietly",
]
