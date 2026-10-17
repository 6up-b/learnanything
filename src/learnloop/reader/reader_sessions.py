"""Reader workbench RW6a: the reader session (spec_reader_workbench_v1 §9.1).

A **visit** is one opened source on the reader envelope: RW1a's
``reader_view_opened`` / ``reader_view_closed`` pair for one ``visit_id``
(the Reader's funnel, ``screens/reader/useReaderVisit.ts``). It ends at its
close, else at the last event that carries its ``visit_id``, else at its open.

A **reader session** is one visit on a source, or several visits on the same
source less than 30 minutes apart (the gap is the next open minus the previous
end). Sessions are per source: "Last time here" is about this book, and the
wrap-up offer is about the book the learner just left.

Functional core, one read: :func:`visits_from_events` and
:func:`group_sessions` are pure over event rows; :func:`load_visits` reads the
envelope once. Nothing here writes. W1 tier 1: salience only, and never read
by anything that writes evidence (an import-linter contract, G50).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from learnloop.clock import parse_utc

#: Visits less than this apart are one session (spec §9.1; a definition, not a setting).
SESSION_GAP = timedelta(minutes=30)

ENVELOPE_KINDS: tuple[str, ...] = ("reader_view_opened", "reader_view_closed")
#: Kinds whose payload may carry the visit (its last event dates a visit with no close).
VISIT_EVENT_KINDS: tuple[str, ...] = ENVELOPE_KINDS + (
    "reader_selection", "reader_action_invoked", "reader_job_queued", "reader_job_completed",
)


@dataclass(frozen=True)
class Visit:
    visit_id: str
    extraction_id: str
    started_at: str
    ended_at: str


@dataclass(frozen=True)
class ReaderSession:
    """One reader session on one source: its visits and its window."""

    extraction_id: str
    visit_ids: tuple[str, ...]
    started_at: str
    ended_at: str

    @property
    def session_id(self) -> str:
        """The session is named by its first visit (stable as later visits join)."""

        return self.visit_ids[0]

    def contains(self, when: str | None) -> bool:
        moment = _when(when)
        start, end = _when(self.started_at), _when(self.ended_at)
        return moment is not None and start is not None and end is not None and start <= moment <= end

    def as_dict(self) -> dict[str, Any]:
        start, end = _when(self.started_at), _when(self.ended_at)
        minutes = int(round((end - start).total_seconds() / 60)) if start and end else 0
        return {
            "session_id": self.session_id,
            "extraction_id": self.extraction_id,
            "visit_ids": list(self.visit_ids),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "minutes": max(0, minutes),
        }


def _when(value: str | None) -> datetime | None:
    try:
        return parse_utc(value) if value else None
    except ValueError:
        return None


def iso_seconds(moment: datetime) -> str:
    """``moment`` as the ledgers write times (UTC, whole seconds, ``Z``)."""

    return moment.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _payload(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = row.get("payload")
    if isinstance(payload, Mapping):
        return dict(payload)
    raw = row.get("payload_json")
    if raw:
        try:
            decoded = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


# ---------------------------------------------------------------------------
# The pure core
# ---------------------------------------------------------------------------

def visits_from_events(events: Iterable[Mapping[str, Any]]) -> list[Visit]:
    """Visits from envelope rows (``kind``, ``created_at``, ``payload``), oldest first.

    A visit needs its open (which names its source). Its end is the close,
    else the latest event carrying its ``visit_id``, else the open."""

    opened: dict[str, tuple[str, str]] = {}
    closed: dict[str, str] = {}
    last_seen: dict[str, str] = {}
    for row in events:
        payload = _payload(row)
        visit_id = payload.get("visit_id")
        created = str(row.get("created_at") or "")
        if not visit_id or not created:
            continue
        visit_id = str(visit_id)
        kind = row.get("kind")
        if kind == "reader_view_opened" and payload.get("extraction_id"):
            if visit_id not in opened or created < opened[visit_id][1]:
                opened[visit_id] = (str(payload["extraction_id"]), created)
        elif kind == "reader_view_closed":
            closed[visit_id] = max(created, closed.get(visit_id, created))
        if created > last_seen.get(visit_id, ""):
            last_seen[visit_id] = created
    visits = []
    for visit_id, (extraction_id, started) in opened.items():
        ended = closed.get(visit_id) or last_seen.get(visit_id) or started
        visits.append(Visit(visit_id, extraction_id, started, max(started, ended)))
    return sorted(visits, key=lambda v: (v.started_at, v.visit_id))


def group_sessions(visits: Sequence[Visit], *, gap: timedelta = SESSION_GAP) -> list[ReaderSession]:
    """Group visits into sessions per source, oldest first (by start)."""

    by_source: dict[str, list[Visit]] = {}
    for visit in sorted(visits, key=lambda v: (v.started_at, v.visit_id)):
        by_source.setdefault(visit.extraction_id, []).append(visit)
    sessions: list[ReaderSession] = []
    for extraction_id, ordered in by_source.items():
        current: ReaderSession | None = None
        for visit in ordered:
            start, previous_end = _when(visit.started_at), _when(current.ended_at) if current else None
            if current is not None and start is not None and previous_end is not None and start - previous_end < gap:
                current = replace(
                    current, visit_ids=current.visit_ids + (visit.visit_id,),
                    ended_at=max(current.ended_at, visit.ended_at),
                )
                continue
            if current is not None:
                sessions.append(current)
            current = ReaderSession(extraction_id, (visit.visit_id,), visit.started_at, visit.ended_at)
        if current is not None:
            sessions.append(current)
    return sorted(sessions, key=lambda s: (s.started_at, s.extraction_id, s.session_id))


def split_sessions(
    sessions: Sequence[ReaderSession], *, current_visit_id: str | None, now: datetime,
    extraction_id: str | None = None, gap: timedelta = SESSION_GAP,
) -> tuple[ReaderSession | None, ReaderSession]:
    """``(previous, current)`` for one source's sessions, as seen at ``now``.

    The current session is the one holding ``current_visit_id``; a visit not
    on the envelope yet joins the last session when that ended less than
    ``gap`` before ``now``, else starts a new one at ``now``. Either way the
    current session runs to ``now``. ``previous`` is the session before it
    (the card's "last time"), or ``None`` on a first visit."""

    now_iso = iso_seconds(now)
    ordered = sorted(sessions, key=lambda s: (s.started_at, s.session_id))
    index = next(
        (i for i, s in enumerate(ordered) if current_visit_id and current_visit_id in s.visit_ids), None
    )
    if index is None and ordered:
        last_end = _when(ordered[-1].ended_at)
        if last_end is not None and now - last_end < gap:
            index = len(ordered) - 1
            if current_visit_id:
                ordered[index] = replace(ordered[index], visit_ids=ordered[index].visit_ids + (current_visit_id,))
    if index is None:
        current = ReaderSession(
            extraction_id or (ordered[0].extraction_id if ordered else ""), (current_visit_id or "current",),
            now_iso, now_iso,
        )
        return (ordered[-1] if ordered else None), current
    current = replace(ordered[index], ended_at=max(ordered[index].ended_at, now_iso))
    return (ordered[index - 1] if index > 0 else None), current


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------

def envelope_events(repository: Any) -> list[dict[str, Any]]:
    """Every reader-envelope row that can date a visit (one read)."""

    marks = ", ".join("?" for _ in VISIT_EVENT_KINDS)
    with repository.connection() as connection:
        rows = connection.execute(
            f"SELECT kind, payload_json, created_at FROM interaction_events WHERE kind IN ({marks}) "
            "ORDER BY created_at, id",
            VISIT_EVENT_KINDS,
        ).fetchall()
    return [{"kind": row["kind"], "payload_json": row["payload_json"], "created_at": row["created_at"]}
            for row in rows]


def load_visits(repository: Any) -> list[Visit]:
    return visits_from_events(envelope_events(repository))


def all_sessions(repository: Any) -> list[ReaderSession]:
    """Every reader session on every source, oldest first."""

    return group_sessions(load_visits(repository))


def sessions_for_source(repository: Any, extraction_id: str) -> list[ReaderSession]:
    return [s for s in all_sessions(repository) if s.extraction_id == extraction_id]


__all__ = [
    "ENVELOPE_KINDS",
    "ReaderSession",
    "SESSION_GAP",
    "Visit",
    "all_sessions",
    "envelope_events",
    "group_sessions",
    "iso_seconds",
    "load_visits",
    "sessions_for_source",
    "split_sessions",
    "visits_from_events",
]
