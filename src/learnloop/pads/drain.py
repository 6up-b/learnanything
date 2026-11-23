"""The desk drain's read (spec §10.12): closing a desk lists the pads it worked on today, and gives before it asks.

Each row shows what the pad holds (its title, kind, whether it is kept, its first and last lines) and, when the last
line is a question, offers to carry it. The answers are the existing writes: keep and leave are ``pad.apply``'s
``keep``/``unkeep`` (leave keeps the pad in the library, unpinned), carry is ``carried.carry`` with origin ``drain``.
Skipping costs nothing: nothing here writes.
"""
from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Any

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.db.stores import pad_reads as reads


def _lines(heads: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for head in heads:
        if head["tombstone"] or head["kind"] in ("sketch", "cell", "lifted"):
            continue
        lines += [line.strip() for line in str(head["body_md"] or "").splitlines() if line.strip()]
    return lines


def local_day(clock: Any = None) -> str:
    parsed = parse_utc(utc_now_iso(clock))
    assert parsed is not None
    return parsed.astimezone().date().isoformat()


def _day_bounds(day: str) -> tuple[str, str]:
    start = datetime.combine(datetime.fromisoformat(day).date(), time.min).astimezone().astimezone(UTC)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return start.strftime(fmt), (start + timedelta(days=1)).strftime(fmt)


def desk_drain(repository: Any, desk_id: str, *, day: str | None = None, clock: Any = None) -> dict[str, Any]:
    """The pads homed on ``desk_id`` that changed on ``day`` (the learner's local calendar day; today by default)."""

    day = day or local_day(clock)
    since, until = _day_bounds(day)
    rows: list[dict[str, Any]] = []
    with repository.connection() as connection:
        cursor: str | None = None
        while True:
            after = tuple(cursor.split("|", 1)) if cursor else None
            page = reads.list_pads(connection, desk_id=desk_id, kept=None, query=None, after=after, page_size=51)
            for pad in page[:50]:
                if not since <= str(pad["updated_at"]) < until:
                    continue
                lines = _lines(reads.heads(connection, str(pad["pad_id"])))
                last = lines[-1] if lines else ""
                rows.append({"pad_id": pad["pad_id"], "kind": pad["kind"], "title": pad["title"],
                             "kept": bool(pad["kept"]), "version": int(pad["version"]),
                             "first_line": lines[0] if lines else "", "last_line": last,
                             "carry_candidate": last if last.endswith("?") else None,
                             "updated_at": pad["updated_at"]})
            if len(page) <= 50 or str(page[49]["updated_at"]) < since:
                break
            cursor = f"{page[49]['updated_at']}|{page[49]['pad_id']}"
    return {"desk_id": desk_id, "day": day, "pads": rows}


__all__ = ["desk_drain", "local_day"]
