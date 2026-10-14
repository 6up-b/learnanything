"""`learnloop reader report`: the Reader's workflow funnel (RW1a; spec §4.1, §15).

Reports **workflows, with denominators**, not only counts, as the reader
workbench spec and the UX document's §9.2 ask:

* **selection -> action -> usable result -> back to reading**: selections;
  actions by kind; for model-backed actions, queued, completed, failed (with
  reason) and cancelled, latency and model wait (p50/p95); how often the
  learner came back to the source after a usable result;
* **inquiry**: inquiries opened, branch depth and breadth, resolved, dismissed,
  reopened, still open after 7 days, reconnect answers, the passage-scoped
  quick checks and their self-checks;
* **detours**: the return rate (detours opened in the window that end back at
  their origin, each counted once however often it is walked back to) and the
  detour cost (minutes away, model wait separated);
* **proactive load**: LearnLoop-started elements per reading hour (RW3a's
  margin marks included);
* **cues** (RW3a): marks shown, open, check-me and not-relevant rates against
  marks shown, marks per reading hour (the interruption burden) and the
  learner's density and per-book choices;
* **waiting behaviour**: the share of model waits during which the learner
  scrolled, selected or typed;
* **visits**: visits, active minutes, time to the first action.

Reports with noise floors, never thresholds (R6). Read-only: the database is
opened read-only and never migrated; no model is called; no learner text (no
question, answer or quote) is read into the report.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from learnloop.clock import parse_utc
from learnloop.db.connection import connect

REPORT_VERSION = "reader-report-v1"
OPEN_AFTER = timedelta(days=7)

_ACTIVITY_KINDS = (
    "reader_view_opened",
    "reader_view_closed",
    "reader_selection",
    "reader_action_invoked",
    "reader_job_queued",
    "reader_job_completed",
)


def _percentiles(values: Iterable[float]) -> dict[str, Any]:
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return {"n": 0, "p50": None, "p95": None}

    def rank(q: float) -> float:
        return ordered[max(0, math.ceil(q * len(ordered)) - 1)]

    return {"n": len(ordered), "p50": rank(0.50), "p95": rank(0.95)}


def _share(count: int, of: int) -> dict[str, Any]:
    return {"count": count, "of": of, "share": (round(count / of, 4) if of else None)}


def _payload(row: Any) -> dict[str, Any]:
    try:
        payload = json.loads(row["payload_json"] or "{}")
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _when(value: str | None) -> datetime | None:
    try:
        return parse_utc(value) if value else None
    except ValueError:
        return None


def build_reader_report(
    sqlite_path: Path | str,
    *,
    since: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Compute the report from the ledgers (pure read)."""

    now = (now or datetime.now(UTC)).astimezone(UTC)
    since_at = _when(since) if since else None

    def in_window(created_at: str | None) -> bool:
        when = _when(created_at)
        return since_at is None or (when is not None and when >= since_at)

    with closing(connect(Path(sqlite_path), read_only=True)) as connection:
        marks = ", ".join("?" for _ in _ACTIVITY_KINDS)
        activity = [
            {"kind": row["kind"], "created_at": row["created_at"], "payload": _payload(row)}
            for row in connection.execute(
                f"SELECT kind, payload_json, created_at FROM interaction_events WHERE kind IN ({marks}) "
                "ORDER BY created_at, id",
                _ACTIVITY_KINDS,
            )
            if in_window(row["created_at"])
        ]
        answers = [
            {"id": str(row["id"]), "created_at": row["created_at"], "payload": _payload(row)}
            for row in connection.execute(
                "SELECT id, payload_json, created_at FROM interaction_events "
                "WHERE kind = 'reader_answer_submitted' ORDER BY created_at, id"
            )
        ]
        resolutions = {
            str(row["id"]): str(row["resolution"] or "open")
            for row in connection.execute("SELECT id, resolution FROM question_events WHERE context = 'reader'")
        }
        has_scopes = any(
            row[1] == "scope_kind"
            for row in connection.execute("PRAGMA table_info(reader_authored_questions)")
        )
        checks = [
            dict(row)
            for row in connection.execute(
                "SELECT status, self_check, created_at FROM reader_authored_questions "
                "WHERE scope_kind = 'inquiry' ORDER BY created_at, id"
            )
            if in_window(row["created_at"])
        ] if has_scopes else []

    def actions(event: str) -> list[dict[str, Any]]:
        return [
            a for a in activity
            if a["kind"] == "reader_action_invoked" and a["payload"].get("event") == event
        ]

    def of_kind(kind: str) -> list[dict[str, Any]]:
        return [a for a in activity if a["kind"] == kind]

    # -- selection -> action -> usable result -> back to reading ----------------
    invoked = actions("action_invoked")
    queued = of_kind("reader_job_queued")
    completions = of_kind("reader_job_completed")
    model_backed: dict[str, dict[str, Any]] = {}
    kinds = sorted({a["payload"].get("job_kind") or "unknown" for a in queued + completions})
    for job_kind in kinds:
        mine = [c for c in completions if (c["payload"].get("job_kind") or "unknown") == job_kind]
        statuses = Counter(str(c["payload"].get("status") or "unknown") for c in mine)
        done = [c for c in mine if c["payload"].get("status") == "completed"]
        model_backed[job_kind] = {
            "queued": sum(1 for q in queued if (q["payload"].get("job_kind") or "unknown") == job_kind),
            "completed": statuses.get("completed", 0),
            "failed": statuses.get("failed", 0),
            "cancelled": statuses.get("cancelled", 0),
            "failure_reasons": dict(Counter(
                str(c["payload"].get("failure_reason") or "unknown")
                for c in mine if c["payload"].get("status") == "failed"
            )),
            "latency_ms": _percentiles(c["payload"].get("latency_ms") for c in done),
            "model_wait_ms": _percentiles(c["payload"].get("model_wait_ms") for c in done),
        }
    completed_jobs = [c for c in completions if c["payload"].get("status") == "completed"]
    routes: dict[tuple[str, str | None, str | None], list[dict[str, Any]]] = defaultdict(list)
    for c in completed_jobs:
        p = c["payload"]
        routes[(p.get("job_kind") or "unknown", p.get("model"), p.get("prompt_version"))].append(c)

    # -- inquiries --------------------------------------------------------------
    parent_of = {a["id"]: a["payload"].get("parent_exchange_id") for a in answers}

    def depth(exchange_id: str) -> int:
        seen: set[str] = set()
        level, current = 0, parent_of.get(exchange_id)
        while current and current in parent_of and current not in seen:
            seen.add(current)
            level += 1
            current = parent_of.get(current)
        return level

    windowed = [a for a in answers if in_window(a["created_at"])]
    roots = [a for a in windowed if depth(a["id"]) == 0]
    branches = [a for a in windowed if depth(a["id"]) > 0]
    children = Counter(
        parent_of[a["id"]] for a in answers if parent_of.get(a["id"]) in parent_of
    )
    breadths = [count for exchange, count in children.items() if any(w["id"] == exchange for w in windowed)]
    depths = [depth(a["id"]) for a in branches]
    status_events = actions("inquiry_status_set")
    status_counts = Counter(str(e["payload"].get("resolution")) for e in status_events)
    reopened = sum(
        1 for e in status_events
        if e["payload"].get("resolution") == "open"
        and e["payload"].get("previous_resolution") in ("resolved", "dismissed")
    )
    root_resolution = {
        a["id"]: resolutions.get(str(a["payload"].get("question_event_id")), "open") for a in roots
    }
    open_after = sum(
        1 for a in roots
        if root_resolution[a["id"]] == "open"
        and (_when(a["created_at"]) or now) <= now - OPEN_AFTER
    )
    reconnects = Counter(str(e["payload"].get("answer")) for e in actions("reconnect_answered"))

    # -- detours ----------------------------------------------------------------
    # A detour is counted once: its first opening in the window, and its first
    # return to the origin. A return is joined to an opening in the window by
    # its detour_id; one whose opening lies before the window (or is unknown)
    # is not counted, so the return rate is at most 1.
    opened_by_id: dict[str, dict[str, Any]] = {}
    for d in actions("detour_opened"):
        opened_by_id.setdefault(str(d["payload"].get("detour_id") or f"unnamed:{len(opened_by_id)}"), d)
    opened = list(opened_by_id.values())
    returned_by_id: dict[str, dict[str, Any]] = {}
    for r in actions("detour_returned"):
        detour_id = str(r["payload"].get("detour_id") or "")
        if r["payload"].get("returned_to_origin") is True and detour_id in opened_by_id:
            returned_by_id.setdefault(detour_id, r)
    returned = list(returned_by_id.values())
    by_kind: dict[str, dict[str, int]] = {}
    for d in opened:
        kind = str(d["payload"].get("detour_kind") or "unknown")
        by_kind.setdefault(kind, {"opened": 0, "returned": 0})["opened"] += 1
    for r in returned:
        kind = str(r["payload"].get("detour_kind") or "unknown")
        by_kind.setdefault(kind, {"opened": 0, "returned": 0})["returned"] += 1

    # -- proactive load, waiting, visits ---------------------------------------
    cue_shown = actions("cue_shown")
    shown = [("reconnect_line", e) for e in actions("reconnect_shown")] + [
        (str(e["payload"].get("element") or "unknown"), e) for e in actions("proactive_shown")
    ] + [("margin_mark", e) for e in cue_shown]
    closes = of_kind("reader_view_closed")
    active_seconds = sum(float(c["payload"].get("active_seconds") or 0) for c in closes)
    reading_hours = round(active_seconds / 3600, 4)
    waited_with_activity = sum(
        1 for c in completions if any((c["payload"].get("activity_during_wait") or {}).values())
    )
    opens = {
        str(o["payload"].get("visit_id")): _when(o["created_at"])
        for o in of_kind("reader_view_opened") if o["payload"].get("visit_id")
    }
    first_action: dict[str, float] = {}
    for a in invoked:
        visit = str(a["payload"].get("visit_id"))
        started, when = opens.get(visit), _when(a["created_at"])
        if started is not None and when is not None and visit not in first_action:
            first_action[visit] = (when - started).total_seconds()

    return {
        "version": REPORT_VERSION,
        "window": {"since": since_at.isoformat() if since_at else None, "until": now.isoformat()},
        "learner_text": False,
        "selection_to_reading": {
            "selections": len(of_kind("reader_selection")),
            "actions": {
                "total": len(invoked),
                "by_kind": dict(Counter(str(a["payload"].get("action_kind") or "unknown") for a in invoked)),
            },
            "model_backed": model_backed,
            "back_to_reading": _share(len(actions("back_to_reading")), len(completed_jobs)),
        },
        "inquiry": {
            "opened": len(roots),
            "branches": len(branches),
            "depth": {"max": max(depths, default=0),
                      "mean": round(sum(depths) / len(depths), 3) if depths else None},
            "breadth": {"max": max(breadths, default=0),
                        "mean": round(sum(breadths) / len(breadths), 3) if breadths else None},
            "resolved": status_counts.get("resolved", 0),
            "dismissed": status_counts.get("dismissed", 0),
            "reopened": reopened,
            "now": dict(Counter(root_resolution.values())),
            "open_after_7_days": open_after,
            "reconnect_answers": {answer: reconnects.get(answer, 0)
                                  for answer in ("yes", "still_unclear", "quick_check")},
            "quick_checks": {
                "authored": len(checks),
                "answered": sum(1 for c in checks if c["status"] == "answered"),
                "self_check": {value: sum(1 for c in checks if c["self_check"] == value)
                               for value in ("matches", "partly", "no")},
            },
        },
        "detours": {
            "opened": len(opened),
            "returned_to_origin": len(returned),
            "return_rate": _share(len(returned), len(opened)),
            "by_kind": by_kind,
            "cost_minutes": _percentiles(
                round(float(r["payload"].get("seconds_away") or 0) / 60, 3) for r in returned
            ),
            "model_wait_ms": _percentiles(r["payload"].get("model_wait_ms") for r in returned),
        },
        "proactive_load": {
            "shown": len(shown),
            "by_element": dict(Counter(element for element, _ in shown)),
            "reading_hours": reading_hours,
            "per_reading_hour": round(len(shown) / reading_hours, 3) if reading_hours else None,
        },
        "cues": {
            "shown": len(cue_shown),
            "per_reading_hour": round(len(cue_shown) / reading_hours, 3) if reading_hours else None,
            "opened": _share(len(actions("cue_opened")), len(cue_shown)),
            "check_me": _share(len(actions("cue_check_me")), len(cue_shown)),
            "not_relevant": _share(len(actions("cue_not_relevant")), len(cue_shown)),
            "not_relevant_undone": len(actions("cue_not_relevant_undone")),
            "density_changes": dict(Counter(
                f"{e['payload'].get('from')}->{e['payload'].get('to')}" for e in actions("cue_density_changed")
            )),
            "books_switched_off": len(actions("cue_source_off")),
            "books_switched_on": len(actions("cue_source_on")),
        },
        "waiting": _share(waited_with_activity, len(completions)),
        "visits": {
            "visits": len(opens),
            "active_minutes": round(active_seconds / 60, 3),
            "time_to_first_action_seconds": _percentiles(first_action.values()),
        },
        "routes": [
            {"job_kind": job_kind, "model": model, "prompt_version": version, "n": len(rows),
             "latency_ms": _percentiles(r["payload"].get("latency_ms") for r in rows)}
            for (job_kind, model, version), rows in sorted(routes.items(), key=lambda item: str(item[0]))
        ],
    }


__all__ = ["REPORT_VERSION", "build_reader_report"]
