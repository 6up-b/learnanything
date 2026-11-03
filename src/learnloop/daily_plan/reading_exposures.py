"""Reader activity frozen for the delayed-completion definition (data capture; Codex re-review F1).

A section completed the hour before an answer leaves that answer warm, whatever adaptive difficulty is set to. AD's
reading receipts (``ad_reading_opportunities``) are written only under its ``forecast_receipts``, and its spec keeps
them so (G-AD1-11), so this is data capture's own record of the same facts: **the same list of sources**, read by AD's
collectors (:func:`learnloop.adaptive_difficulty.reading.listed_events`), written to ``reading_exposure_receipts``.

What differs from AD's receipt, because the question differs. AD's is a dose on a learned state; this one is a fact the
outcome reads:

* **no cap**: the newest exposure is what the delay runs from, so a second passage view that day counts;
* **no material view and no withholding**: this is not AD's state, so no AD operation opens and none of its guard runs.
  Reading held-out material is an exposure all the same, and the row holds only its LO and the time;
* **no doses, no dwell, no answer text**: the fact and its source time, no more.

Written where Today prepares (:func:`learnloop.daily_plan.measurement.settle`, which judges answers against it), so a
section read since then counts once Today next prepares: the source time is kept, and every outcome is derived from the
ledgers at read time, so a late sweep corrects it. Under either of data capture's switches, at every version: a receipt
changes nothing served, and only ``router_outcomes_v3`` and the time metric read it. Never evidence, FSRS, the projection
or replay (A12 stands: this writes nothing AD reads).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
import logging
from types import SimpleNamespace
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.data_capture.gates import receipts_on, serving_on
from learnloop.db.stores import data_capture as store

logger = logging.getLogger(__name__)

MAPPING_VERSION = "reading_exposure_map_v1"


class _Map:
    """A section's and a span's LOs as the objective's freeze reads them (provenance and coverage rows), an item's, a
    note's. Nothing is withheld and no span is a worked example here: only the LO and the time are kept."""

    def __init__(self, vault: Any, repository: Any) -> None:
        self.vault, self.repository = vault, repository
        self._sections: dict[tuple[str, str], list[str]] = {}
        self._spans: dict[tuple[str, str], list[str]] = {}

    def los_for_section(self, extraction_id: str, section_id: str) -> list[str]:
        from learnloop.daily_plan.measurement import reading_learning_objects

        key = (extraction_id, section_id)
        if key not in self._sections:
            target = SimpleNamespace(extraction_id=extraction_id, section_id=section_id)
            self._sections[key] = list(reading_learning_objects(self.vault, self.repository, target))
        return self._sections[key]

    def los_for_span(self, extraction_id: str, span_id: str) -> list[str]:
        from learnloop.reader import reader_progression

        key = (extraction_id, span_id)
        if key not in self._spans:
            try:
                self._spans[key] = list(reader_progression.learning_objects_for_span(
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


def _events(connection: Any, vault: Any, repository: Any, *, upper: str) -> list[Any]:
    from learnloop.adaptive_difficulty.reading import SWEEP_OVERLAP, listed_events

    # AD's own overlap, its reason the same: a source row stamped a little before the newest on record is still read.
    newest = store.newest_reading_exposure(connection)
    parsed = parse_utc(newest) if newest else None
    lower = _stamp(parsed - SWEEP_OVERLAP) if parsed is not None else None
    return listed_events(connection, _Map(vault, repository), lower, upper, view=_Rows())


def sweep(vault: Any, repository: Any, *, clock: Clock | None = None) -> int:
    """Record the listed Reader activity not yet on record; how many rows it wrote. Idempotent; a no-op with both of
    data capture's switches off or before migration 239."""

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


__all__ = ["MAPPING_VERSION", "sweep", "sweep_quietly"]
