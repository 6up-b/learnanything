"""Reader workbench v2 inline checks, the reads (spec §3.4, §12.6.1): the due delayed checks with their hosts
(:func:`due_checks`, for the server's own use: the goal lens, the begun card), and the desks' opaque handles
(:func:`due_handles`, ``checks.due_for``'s reply, and :func:`resolve_handle`). Read only; nothing of the item.

A due check is a pending "Check once" (a ``test_me_later`` commitment), exactly as serving reads it
(``scheduling.intent.serving``: due, unanswered and not replaced everywhere), whatever created it. Its
host is the learning object's primary path section: with a goal, the first core section of that goal's
latest path; without one, the passage the learning object is provenance-linked to as its primary
source. A check whose learning object has neither has no host and is still listed.

Here, beside "Check once" serving (``intent.checks``), rather than in ``learnloop.curriculum`` (the spec's
``curriculum/inline_checks.py``): it reads serving's check state (``scheduling.intent``), and ``scheduling``
already imports ``curriculum``, so a module there would close a package cycle (``pyproject.toml``'s acyclic
contract). The administration protocol (``check.begin_inline`` and the rest) is not built yet.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.scheduling.intent.resolution import load_snapshots
from learnloop.scheduling.intent.serving import intent_serving
from learnloop.section_map import extraction_sections


class _Sections:
    """Each reading's sections, loaded once per call."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self._by_reading: dict[str, tuple[dict[str, dict[str, Any]], dict[str, str]]] = {}

    def _load(self, extraction_id: str) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        if extraction_id not in self._by_reading:
            ir = self.repository.load_document_ir(extraction_id)
            if ir is None:
                self._by_reading[extraction_id] = ({}, {})
            else:
                rows, _blocks, span_to_section = extraction_sections(ir)
                self._by_reading[extraction_id] = ({str(row["id"]): row for row in rows}, span_to_section)
        return self._by_reading[extraction_id]

    def section(self, extraction_id: str, section_id: str) -> dict[str, Any] | None:
        return self._load(extraction_id)[0].get(section_id)

    def section_of(self, extraction_id: str, span_id: str) -> str | None:
        found = self._load(extraction_id)[1].get(span_id)
        return str(found) if found is not None else None


def _path_host(connection: Any, goal_id: str, lo_id: str) -> tuple[str, str] | None:
    rows = connection.execute(
        "SELECT extraction_id, section_id, label, ordinal, created_at FROM deliverable_path_sections "
        "WHERE goal_id = ? AND learning_object_id = ? ORDER BY created_at DESC", (goal_id, lo_id)).fetchall()
    if not rows:
        return None
    latest = [row for row in rows if row[4] == rows[0][4] and row[2] not in ("assumed", "already_shown")]
    if not latest:
        return None
    chosen = min(latest, key=lambda row: (row[2] != "core", int(row[3])))
    return str(chosen[0]), str(chosen[1])


def _primary_passage(connection: Any, lo_id: str) -> tuple[str, str] | None:
    row = connection.execute(
        "SELECT locator FROM entity_source_links WHERE entity_type = 'learning_object' AND entity_id = ? "
        "AND relation = 'primary' AND status = 'current' AND locator LIKE 'span:%/%' ORDER BY created_at, id LIMIT 1",
        (lo_id,)).fetchone()
    if row is None:
        return None
    reading, _, span = str(row[0])[len("span:"):].partition("/")
    return (reading, span) if reading and span else None


def _host(connection: Any, sections: _Sections, lo_id: str, goal_id: str | None) -> dict[str, Any] | None:
    if goal_id:
        found = _path_host(connection, goal_id, lo_id)
        if found is not None:
            section = sections.section(*found)
            return {"extraction_id": found[0], "section_id": found[1],
                    "span_id": str(section["start_span_id"]) if section else None}
    passage = _primary_passage(connection, lo_id)
    if passage is None:
        return None
    section_id = sections.section_of(*passage)
    section = sections.section(passage[0], section_id) if section_id else None
    return {"extraction_id": passage[0], "section_id": section_id,
            "span_id": str(section["start_span_id"]) if section else passage[1]}


def _provenance(provenance: Any) -> dict[str, Any]:
    """Who made the check, in one word: its ``via`` (or ``origin``) and nothing else. A commitment's
    provenance can name an item, a question or an annotation, which a due check must not show."""

    if not isinstance(provenance, Mapping):
        return {}
    for key in ("via", "origin", "source"):
        if isinstance(provenance.get(key), str):
            return {key: provenance[key]}
    return {}


def serving_view(vault: Any, repository: Any, *, clock: Clock | None = None) -> Any:
    """The serving view the check reads below share (one build answers both)."""

    now = parse_utc(utc_now_iso(clock)) or datetime.now(UTC)
    return intent_serving(vault, repository, now=now, force=True)


def next_check_due(view: Any) -> str | None:
    """When the next check not due yet falls due (a UTC stamp), or None: a reader of the due checks (the goal band,
    which hides what a due check covers) reads again then."""

    upcoming = [check.date for check in (view.raw_checks.values() if view is not None else ())
                if not check.due and check.answered_by is None and not check.replaced]
    return min(upcoming).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if upcoming else None


def due_checks(vault: Any, repository: Any, *, goal_id: str | None = None,
               learning_object_ids: Iterable[str] | None = None, extraction_id: str | None = None,
               span_id: str | None = None, clock: Clock | None = None, view: Any | None = None) -> list[dict[str, Any]]:
    """Every due check, one row per (check, learning object), oldest due first, filtered. ``view``: a
    ``serving_view`` already built for this read."""

    if view is None:
        view = serving_view(vault, repository, clock=clock)
    if view is None:  # pragma: no cover - force always builds the view
        return []
    pending = view.due_checks()
    if not pending:
        return []
    with repository.connection() as connection:
        snapshots = {snapshot.id: snapshot for snapshot in load_snapshots(connection)}
    items = getattr(vault, "practice_items", {}) or {}
    wanted = set(learning_object_ids) if learning_object_ids is not None else None
    sections = _Sections(repository)
    span_section = sections.section_of(extraction_id, span_id) if extraction_id and span_id else None
    out: list[dict[str, Any]] = []
    with repository.connection() as connection:
        for check in pending:
            snapshot = snapshots.get(check.commitment_id)
            los: set[str] = set(snapshot.learning_object_targets) if snapshot is not None else set()
            for item_id in (snapshot.item_targets if snapshot is not None else ()):
                item = items.get(item_id)
                if item is not None:
                    los.add(str(item.learning_object_id))
            for lo_id in sorted(los):
                if wanted is not None and lo_id not in wanted:
                    continue
                host = _host(connection, sections, lo_id, goal_id)
                if extraction_id and (host is None or host["extraction_id"] != extraction_id):
                    continue
                if span_id and (host is None or span_section is None or host["section_id"] != span_section):
                    continue
                out.append({
                    "commitment_id": check.commitment_id, "lo_id": lo_id,
                    "due": check.date.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "host": host,
                    "provenance": _provenance(check.provenance),
                    # mvp-0.69: an open inline administration holds it (Today shows "being answered in the Reader").
                    "being_answered": check.commitment_id in view.locked,
                })
    return out


def answered_checks(vault: Any, repository: Any, *, since: str, clock: Clock | None = None) -> list[dict[str, Any]]:
    """Every "Check once" answered on the learner's own since ``since`` (a UTC stamp), one row per
    (check, learning object): the goal band fills its ◇ once a check is answered. Answered as serving reads
    it (a settled check, or one an attempt on your own has answered and settling has not recorded yet)."""

    now = parse_utc(utc_now_iso(clock)) or datetime.now(UTC)
    start = parse_utc(since)
    view = intent_serving(vault, repository, now=now, force=True)
    if view is None or start is None:  # pragma: no cover - force always builds the view
        return []
    items = getattr(vault, "practice_items", {}) or {}
    out: list[dict[str, Any]] = []
    for snapshot in sorted(view.resolution.snapshots.values(), key=lambda snap: (str(snap.satisfied_at), snap.id)):
        if snapshot.action != "test_me_later" or snapshot.disposition != "satisfied" or not snapshot.satisfied_at:
            continue
        answered = parse_utc(snapshot.satisfied_at)
        if answered is None or answered < start:
            continue
        los: set[str] = set(snapshot.learning_object_targets)
        for item_id in snapshot.item_targets:
            item = items.get(item_id)
            if item is not None:
                los.add(str(item.learning_object_id))
        for lo_id in sorted(los):
            out.append({"commitment_id": snapshot.id, "lo_id": lo_id,
                        "answered_at": answered.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")})
    return out


# -- the desks' handles (the owner's decision on RD7-56: an unlocated marker) ----------------------------------------
#
# Before "check now" the desks know only that a check is due: ``checks.due_for`` answers an opaque handle per due check
# and nothing else (no LO, host passage, provenance, due date or commitment id), and ``check.begin_inline`` resolves the
# handle here. A handle is a keyed hash of (commitment, how many administrations it has had): the same across reads, spent
# by a begin (the count moves), and meaningless to anyone without the key. The key lives in this process only, so a
# handle dies with the sidecar: the desks read the due checks again after a reconnect, and a dead or guessed handle is
# refused plainly (``check_unknown``), never resolved to a guess.

_HANDLE_KEY = secrets.token_bytes(32)
HANDLE_PREFIX = "chk_"


def handle_of(commitment_id: str, administrations: int) -> str:
    digest = hmac.new(_HANDLE_KEY, f"{commitment_id}\x00{administrations}".encode(), hashlib.sha256).hexdigest()
    return HANDLE_PREFIX + digest[:32]


def due_handles(vault: Any, repository: Any, *, clock: Clock | None = None) -> list[dict[str, Any]]:
    """``checks.due_for``'s rows: one opaque handle per due check, every due check in the vault (a filter by goal,
    reading or passage would itself say where it is), in the handles' own order (the due order could be recalled)."""

    from learnloop.db.stores import check_administrations as store

    view = serving_view(vault, repository, clock=clock)
    pending = view.due_checks() if view is not None else []
    with repository.connection() as connection:
        counts = store.administration_counts(connection)
    rows = [{"handle": handle_of(check.commitment_id, counts.get(check.commitment_id, 0)),
             "being_answered": check.commitment_id in view.locked} for check in pending]
    return sorted(rows, key=lambda row: row["handle"])


def resolve_handle(vault: Any, repository: Any, handle: str, *, clock: Clock | None = None) -> str | None:
    """The due check a handle names now, or None (spent, stale, from another sidecar run, or guessed). A begin's lost
    reply retried with the handle it spent finds the administration it opened (that one is open, the handle one
    administration behind)."""

    from learnloop.db.stores import check_administrations as store

    view = serving_view(vault, repository, clock=clock)
    pending = view.due_checks() if view is not None else []
    with repository.connection() as connection:
        counts = store.administration_counts(connection)
        current = store.open_administration(connection) if store.table_present(connection) else None
    for check in pending:
        count = counts.get(check.commitment_id, 0)
        if hmac.compare_digest(handle_of(check.commitment_id, count), handle):
            return str(check.commitment_id)
        if (current is not None and current["commitment_id"] == check.commitment_id and count
                and hmac.compare_digest(handle_of(check.commitment_id, count - 1), handle)):
            return str(check.commitment_id)
    return None


__all__ = ["answered_checks", "due_checks", "due_handles", "handle_of", "next_check_due", "resolve_handle",
           "serving_view"]
