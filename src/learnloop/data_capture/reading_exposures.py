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
mapping and the same source time as the sweep. :func:`sweep` writes what :func:`read` would add and nothing else, so **the
sweep only freezes**: no answer depends on whether Today has run. A row is never mapped again once recorded (what freezing
means), and every source row is listed, not only recent ones, so a row stamped before a sweep and committed after it, or a
section whose LOs appear later, reads the same with or without a sweep between.

Its cost, per call: one indexed lookup per Reader source row, and for each distinct section or span not on record (not yet
swept, or no LO names it yet) a document load and a scan of the active LOs, cached for the call. Rows on record are not
mapped. No model call, no write, no clock. Measured on copies of the owner's vaults (60 to 85 receipts' worth of activity):
300 to 430 ms with nothing swept yet, 2 to 70 ms after a sweep; a vault with n sections no LO names pays about n x 20 ms.

Frozen where Today prepares (:func:`learnloop.daily_plan.measurement.settle`). Under either of data capture's switches, at
every version: a receipt changes nothing served, and only ``router_outcomes_v3`` and the time metric read it. Never
evidence, FSRS, the projection or replay (A12 stands: this writes nothing AD reads).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
import logging
from types import SimpleNamespace
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.data_capture.gates import OUTCOME_VERSION_V3, receipts_on, serving_on
from learnloop.db.stores import data_capture as store
from learnloop.reading_sources import listed_events
from learnloop import section_map

logger = logging.getLogger(__name__)

MAPPING_VERSION = "reading_exposure_map_v1"
#: Above any source time: a read has no clock, and a row stamped past the sweep's "now" is still read (AD's stamp form).
NO_UPPER = "9999-12-31T23:59:59.999999Z"


def reading_learning_objects(vault: Any, repository: Any, target: Any) -> list[str]:
    """The LOs a reading target's section holds (its provenance-linked LOs and coverage rows): what a decision's
    objective freezes (:mod:`learnloop.daily_plan.measurement`) and what an exposure names."""

    if target is None:
        return []
    found: list[str] = []
    try:
        found.extend(section_map.learning_objects_for_section(
            vault, repository, extraction_id=str(target.extraction_id), section_id=str(target.section_id)))
        with repository.connection() as connection:
            from learnloop.db.stores import section_coverage as coverage

            if coverage.table_present(connection):
                found.extend(coverage.learning_objects_named(connection, str(target.extraction_id),
                                                             str(target.section_id)))
    except Exception:  # noqa: BLE001 - an unreadable section has no objective; the decision stands
        logger.warning("data capture: a reading section's learning objects were not read", exc_info=True)
    return list(dict.fromkeys(found))


class _Map:
    """A section's and a span's LOs as the objective's freeze reads them (provenance and coverage rows), an item's, a
    note's. Nothing is withheld and no span is a worked example here: only the LO and the time are kept."""

    def __init__(self, vault: Any, repository: Any) -> None:
        self.vault, self.repository = vault, repository
        self._sections: dict[tuple[str, str], list[str]] = {}
        self._spans: dict[tuple[str, str], list[str]] = {}

    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]:
        key = (extraction_id, section_id)
        if key not in self._sections:
            target = SimpleNamespace(extraction_id=extraction_id, section_id=section_id)
            self._sections[key] = list(reading_learning_objects(self.vault, self.repository, target))
        return self._sections[key]

    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]:
        key = (extraction_id, span_id)
        if key not in self._spans:
            try:
                self._spans[key] = list(section_map.learning_objects_for_span(
                    self.vault, self.repository, extraction_id=extraction_id, span_id=span_id))
            except Exception:  # noqa: BLE001 - an unreadable extraction maps to nothing
                self._spans[key] = []
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


def _stamp(when: datetime) -> str:
    """AD's source-time form (``adaptive_difficulty.reading._stamp``): microseconds and ``Z``, so stamps sort."""

    return when.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _events(connection: Any, vault: Any, repository: Any, *, upper: str = NO_UPPER) -> list[Any]:
    """The listed activity not yet on record, the whole of it (see the module's note): what the sweep freezes and what
    :func:`read` adds are this one list."""

    return listed_events(connection, _Map(vault, repository), None, upper, view=_Rows())


def not_yet_swept(connection: Any, vault: Any, repository: Any) -> list[tuple[str, str]]:
    """``(LO, source time)`` of the listed activity no sweep has recorded yet. Read-only."""

    return sorted({(str(lo), str(event.written_at)) for event in _events(connection, vault, repository)
                   for lo in event.learning_object_ids})


def read(connection: Any, vault: Any, repository: Any) -> list[tuple[str, str]]:
    """Every Reader exposure, ``(LO, source time)``: the stored receipts plus the source activity not yet swept.

    The one read of them (R1), the same before and after a sweep. Read-only, whichever connection and repository it is
    given, and at any switch: reading an exposure changes nothing served."""

    return sorted({*store.reading_receipts(connection), *not_yet_swept(connection, vault, repository)})


def for_version(connection: Any, vault: Any, repository: Any, version: str) -> list[tuple[str, str]] | None:
    """:func:`read` for a derivation at ``version``; None below ``router_outcomes_v3``, which reads no reading receipt."""

    return read(connection, vault, repository) if version == OUTCOME_VERSION_V3 else None


def sweep(vault: Any, repository: Any, *, clock: Clock | None = None) -> int:
    """Freeze the listed Reader activity not yet on record, as :func:`read` already reads it; how many rows it wrote.
    Idempotent; a no-op with both of data capture's switches off or before migration 239."""

    if not (receipts_on(vault.config) or serving_on(vault.config)):
        return 0
    swept_at = utc_now_iso(clock)
    upper = _stamp((clock or SystemClock()).now().astimezone(UTC))
    written = 0
    with repository.atomic(), repository.connection() as connection:
        if not store.reading_exposures_present(connection):
            return 0
        for event in _events(connection, vault, repository, upper=upper):
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


__all__ = ["MAPPING_VERSION", "for_version", "not_yet_swept", "read", "reading_learning_objects", "sweep", "sweep_quietly"]
