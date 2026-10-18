"""`learnloop hints report`: which hints are used and what follows (spec_adaptive_hints_v1 §6).

H0's rows are the **descriptive** ones (§6.3), with authored hints as the
baseline kind (§10 H0, "Data it starts"): per surface, kind and level, how many
were shown, on how many items, sessions and attempts, which hint in the item's
list, when (reveal to submit, and how far into the attempt), and what followed
(§6.1, as far as H0's rows can say it): more help in the same attempt, the
attempt's recorded outcome, and later independent success on the item and on
its learning object, with how many are still pending (never imputed).

Every number is a report with its sample size, never a threshold (§6). Pure
read: the database is opened read-only and never migrated, no model is
called, and no learner text is read (the rows carry a hash and a length of the
draft, never the draft). Unaided next progress, "doesn't connect" and the
off-policy estimates need H1-H5's rows and are not computed here.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from learnloop.clock import parse_utc
from learnloop.db.connection import connect

REPORT_VERSION = "hints-report-v1"
#: How many items the per-item list shows (a display cap).
TOP_ITEMS = 20


def _percentiles(values: Iterable[float | None]) -> dict[str, Any]:
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return {"n": 0, "p50": None, "p95": None}

    def rank(q: float) -> float:
        return ordered[max(0, math.ceil(q * len(ordered)) - 1)]

    return {"n": len(ordered), "p50": rank(0.50), "p95": rank(0.95)}


def _share(count: int, of: int) -> dict[str, Any]:
    return {"count": count, "of": of, "share": (round(count / of, 4) if of else None)}


def _when(value: str | None) -> datetime | None:
    try:
        return parse_utc(value) if value else None
    except ValueError:
        return None


def _outcome(correctness: float | None) -> str:
    if correctness is None:
        return "ungraded"
    if correctness >= 1.0 - 1e-9:
        return "correct"
    if correctness <= 1e-9:
        return "incorrect"
    return "partial"


def _table_exists(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def build_hints_report(
    sqlite_path: Path | str,
    *,
    since: str | None = None,
    surface: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Compute the descriptive rows from ``help_assists`` and the attempts (pure read)."""

    now = (now or datetime.now(UTC)).astimezone(UTC)
    since_at = _when(since) if since else None
    if since is not None and since_at is None:
        raise ValueError(f"--since {since!r} is not an ISO time")
    with closing(connect(Path(sqlite_path), read_only=True)) as connection:
        if not _table_exists(connection, "help_assists"):
            raise ValueError("this vault's database has no help_assists table (migration 210)")
        clauses = ["shown = 1"]
        parameters: list[Any] = []
        if surface is not None:
            clauses.append("surface = ?")
            parameters.append(surface)
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT id, surface, assist_kind, hint_kind, level, practice_item_id, practice_session_id, "
                "attempt_id, authored_index, work_chars, requested_at, shown_at FROM help_assists "
                f"WHERE {' AND '.join(clauses)} ORDER BY requested_at, id",
                parameters,
            ).fetchall()
        ]
        rows = [
            row for row in rows
            if since_at is None or ((_when(row["shown_at"] or row["requested_at"]) or now) >= since_at)
        ]
        attempt_ids = sorted({row["attempt_id"] for row in rows if row["attempt_id"]})
        attempts: dict[str, dict[str, Any]] = {}
        for start in range(0, len(attempt_ids), 500):
            chunk = attempt_ids[start:start + 500]
            for row in connection.execute(
                "SELECT id, practice_item_id, learning_object_id, attempt_type, correctness, latency_seconds, "
                f"hints_used, primed, created_at FROM practice_attempts WHERE id IN ({', '.join('?' for _ in chunk)})",
                chunk,
            ).fetchall():
                attempts[row["id"]] = dict(row)
        # Later independent attempts (hints_used = 0, not primed) on each
        # touched item and learning object, in time order.
        items = sorted({a["practice_item_id"] for a in attempts.values()})
        los = sorted({a["learning_object_id"] for a in attempts.values() if a["learning_object_id"]})
        independent_by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
        independent_by_lo: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if items or los:
            for row in connection.execute(
                "SELECT id, practice_item_id, learning_object_id, correctness, created_at FROM practice_attempts "
                "WHERE COALESCE(hints_used, 0) = 0 AND COALESCE(primed, 0) = 0 ORDER BY created_at, id"
            ).fetchall():
                if row["practice_item_id"] in items:
                    independent_by_item[row["practice_item_id"]].append(dict(row))
                if row["learning_object_id"] in los:
                    independent_by_lo[row["learning_object_id"]].append(dict(row))

    def later(attempt: dict[str, Any], pool: list[dict[str, Any]]) -> str:
        for candidate in pool:
            if candidate["id"] != attempt["id"] and (candidate["created_at"], candidate["id"]) > (
                attempt["created_at"], attempt["id"]
            ):
                return "pass" if _outcome(candidate["correctness"]) == "correct" else "fail"
        return "pending"

    groups: dict[tuple[str, str, str | None, int | None], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["surface"], row["assist_kind"], row["hint_kind"], row["level"])].append(row)
    by_attempt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["attempt_id"]:
            by_attempt[row["attempt_id"]].append(row)

    kinds: list[dict[str, Any]] = []
    for (row_surface, assist_kind, hint_kind, level), members in sorted(
        groups.items(), key=lambda entry: tuple("" if part is None else str(part) for part in entry[0])
    ):
        attached = [row for row in members if row["attempt_id"] in attempts]
        per_item = Counter(row["practice_item_id"] for row in members)
        per_session = Counter(row["practice_session_id"] for row in members if row["practice_session_id"])
        to_submit: list[float] = []
        into_attempt: list[float] = []
        more_help = 0
        for row in attached:
            attempt = attempts[row["attempt_id"]]
            shown = _when(row["shown_at"] or row["requested_at"])
            submitted = _when(attempt["created_at"])
            if shown is not None and submitted is not None:
                gap = max(0.0, (submitted - shown).total_seconds())
                to_submit.append(round(gap, 3))
                if attempt["latency_seconds"] is not None:
                    into_attempt.append(round(max(0.0, float(attempt["latency_seconds"]) - gap), 3))
            if any(
                (other["requested_at"], other["id"]) > (row["requested_at"], row["id"])
                for other in by_attempt[row["attempt_id"]]
            ):
                more_help += 1
        counted_attempts = {row["attempt_id"] for row in attached}
        outcomes = Counter(_outcome(attempts[a]["correctness"]) for a in counted_attempts)
        later_item = Counter(
            later(attempts[a], independent_by_item.get(attempts[a]["practice_item_id"], [])) for a in counted_attempts
        )
        later_lo = Counter(
            later(attempts[a], independent_by_lo.get(attempts[a]["learning_object_id"] or "", []))
            for a in counted_attempts
        )
        kinds.append({
            "surface": row_surface,
            "assist_kind": assist_kind,
            "hint_kind": hint_kind,
            "level": level,
            "baseline": hint_kind == "authored",
            "shown": len(members),
            "items": len(per_item),
            "sessions": len(per_session),
            "attempts": len(counted_attempts),
            "unattached": len(members) - len(attached),
            "per_item": _percentiles(per_item.values()),
            "per_session": _percentiles(per_session.values()),
            "by_authored_index": {
                str(index): count
                for index, count in sorted(Counter(
                    row["authored_index"] for row in members if row["authored_index"] is not None
                ).items())
            },
            "work_empty_at_request": _share(sum(1 for row in members if not row["work_chars"]), len(members)),
            "seconds_reveal_to_submit": _percentiles(to_submit),
            "seconds_into_attempt": _percentiles(into_attempt),
            "more_help_in_attempt": _share(more_help, len(attached)),
            "attempt_outcome": {key: outcomes.get(key, 0) for key in ("correct", "partial", "incorrect", "ungraded")},
            "attempt_types": dict(sorted(Counter(attempts[a]["attempt_type"] for a in counted_attempts).items())),
            "later_independent_success": {
                "item": {key: later_item.get(key, 0) for key in ("pass", "fail", "pending")},
                "learning_object": {key: later_lo.get(key, 0) for key in ("pass", "fail", "pending")},
            },
        })

    per_item_all = Counter(row["practice_item_id"] for row in rows)
    top_items = [
        {
            "practice_item_id": item_id,
            "shown": count,
            "sessions": len({row["practice_session_id"] for row in rows if row["practice_item_id"] == item_id}),
            "attempts": len({row["attempt_id"] for row in rows if row["practice_item_id"] == item_id and row["attempt_id"]}),
        }
        for item_id, count in sorted(per_item_all.items(), key=lambda entry: (-entry[1], entry[0] or ""))[:TOP_ITEMS]
    ]
    return {
        "report_version": REPORT_VERSION,
        "generated_at": now.isoformat(),
        "since": since_at.isoformat() if since_at else None,
        "surface": surface,
        "totals": {
            "shown": len(rows),
            "items": len(per_item_all),
            "sessions": len({row["practice_session_id"] for row in rows if row["practice_session_id"]}),
            "attempts": len(by_attempt),
            "unattached": sum(1 for row in rows if not row["attempt_id"]),
            "per_attempt": _percentiles(Counter(row["attempt_id"] for row in rows if row["attempt_id"]).values()),
        },
        "kinds": kinds,
        "top_items": top_items,
        "not_yet_measured": [
            "unaided_next_progress", "doesnt_connect", "off_policy_estimates", "expertise_reversal_split",
        ],
    }


__all__ = ["REPORT_VERSION", "build_hints_report"]
