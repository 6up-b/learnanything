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
* **visits**: visits, active minutes, time to the first action;
* **intent box** (RW1b): routings used and discarded (speculative ones apart),
  fallbacks by reason, the learner's corrections counted on used routings
  only, and actions by intention (palette and box alike);
* **active reading** (RW1b): the selection questions by style, answered,
  their self-checks and the missed answers sent to learner-text gaps.

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
        selection_rows = [
            dict(row)
            for row in connection.execute(
                "SELECT question_style, status, self_check, response_md IS NOT NULL AS wrote, created_at "
                "FROM reader_authored_questions WHERE scope_kind = 'selection' ORDER BY created_at, id"
            )
            if in_window(row["created_at"])
        ] if has_scopes else []
        has_gap_jobs = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'learner_text_gap_jobs'"
        ).fetchone() is not None
        formative_texts = [
            row["created_at"] for row in connection.execute(
                "SELECT created_at FROM learner_text_gap_jobs WHERE source_kind = 'reader_formative'"
            ) if in_window(row["created_at"])
        ] if has_gap_jobs else []
        # RW5a: figures (migration 216), counted from their rows: by
        # verification, unsupported requests by kind (RW5b's order and the
        # deferred generated-code figures read it), versions, predictions.
        has_figures = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'interactive_figures'"
        ).fetchone() is not None
        figure_rows = [
            {"verification": row["verification"], "unsupported_kind": row["unsupported_kind"],
             "revision": row["supersedes_id"] is not None, "region": row["region_json"] is not None}
            for row in connection.execute(
                "SELECT verification, unsupported_kind, supersedes_id, region_json, created_at FROM interactive_figures "
                "ORDER BY created_at, id"
            ) if in_window(row["created_at"])
        ] if has_figures else []
        prediction_rows = [
            {"matched": bool(row["matched"]), "explained": row["explanation_text"] is not None}
            for row in connection.execute(
                "SELECT matched, explanation_text, created_at FROM figure_predictions ORDER BY created_at, id"
            ) if in_window(row["created_at"])
        ] if has_figures else []
        # RW4a: library asks (migration 209), counted from their rows; the
        # organizer's lines are counted, never quoted.
        has_asks = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'library_asks'"
        ).fetchone() is not None
        library_asks = [
            {"entry": row["entry"], "personalized": bool(row["personalized"]),
             "organizer": json.loads(row["organizer_json"] or "{}"), "compared": row["comparison_id"] is not None,
             "tutor": row["question_event_id"] is not None}
            for row in connection.execute(
                "SELECT entry, personalized, organizer_json, comparison_id, question_event_id, created_at "
                "FROM library_asks ORDER BY created_at, id"
            ) if in_window(row["created_at"])
        ] if has_asks else []

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

    # -- the intent box and active reading (RW1b) -----------------------------
    routed = actions("intent_routed")
    used = [e for e in routed if e["payload"].get("used") is True]
    # The correction denominator: used routings the Decider chose (a fallback
    # that ran Ask is used, but has no routing to correct). Every executed
    # routing, Enter-only included, reports its use (RW1b review F12).
    used_ids = {str(e["payload"].get("routing_id")) for e in used if e["payload"].get("status") == "routed"}
    corrections = actions("intent_corrected")
    intent_jobs = [c for c in completions if c["payload"].get("job_kind") == "intent_routing"]
    styles = ("next_step", "why_step", "assumptions", "reconstruct")

    # -- the tutor that looks things up (RW1c; spec §15's Tutor and sources row)
    by_answer = {a["id"]: a for a in answers}

    def root_of(exchange_id: str) -> str:
        seen: set[str] = set()
        current = exchange_id
        while parent_of.get(current) in parent_of and current not in seen:
            seen.add(current)
            current = str(parent_of[current])
        return current

    looked = [a for a in windowed if isinstance(a["payload"].get("tutor"), dict)]
    follow_ons: dict[str, list[dict[str, Any]]] = {"alternative": [], "remediate": []}
    for a in looked:
        intent = a["payload"]["tutor"].get("intent")
        if intent in follow_ons:
            follow_ons[intent].append(a)

    def resolved_after(rows: list[dict[str, Any]]) -> dict[str, Any]:
        roots_of = [by_answer.get(root_of(a["id"])) for a in rows]
        done = sum(1 for root in roots_of if root is not None and resolutions.get(
            str(root["payload"].get("question_event_id")), "open") == "resolved")
        return _share(done, len(rows))

    offers_shown = Counter(str(e["payload"].get("offer_kind") or "unknown") for e in actions("tutor_offer_shown"))
    offers_pressed = Counter(str(e["payload"].get("offer_kind") or "unknown") for e in actions("tutor_offer_pressed"))
    press_results = Counter(str(e["payload"].get("offer_result") or "unknown") for e in actions("tutor_offer_pressed"))

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
        "intent": {
            "routings": len(intent_jobs),
            "speculative": sum(1 for c in intent_jobs if c["payload"].get("speculative") is True),
            "used": len(used),
            "used_speculative": sum(1 for e in used if e["payload"].get("speculative") is True),
            "discarded": sum(1 for e in routed if e["payload"].get("used") is False),
            "fallbacks": dict(Counter(
                str(c["payload"].get("failure_reason") or "unknown")
                for c in intent_jobs if c["payload"].get("status") == "failed"
            )),
            # Routing error, counted on used routings only (spec §4.2).
            "corrected": _share(
                sum(1 for e in corrections if str(e["payload"].get("routing_id")) in used_ids), len(used_ids)
            ),
            "actions_by_intention": dict(Counter(
                str(a["payload"].get("intention") or "mark") for a in invoked if a["payload"].get("entry")
            )),
        },
        "active_reading": {
            "questions": {style: sum(1 for r in selection_rows if r["question_style"] == style) for style in styles},
            "answered": sum(1 for r in selection_rows if r["status"] == "answered"),
            "self_check": {
                style: {value: sum(1 for r in selection_rows if r["question_style"] == style
                                   and r["self_check"] == value)
                        for value in ("matches", "partly", "no")}
                for style in styles[:3]
            },
            "formative_texts_queued": len(formative_texts),
        },
        # RW4a (spec §15's Library row): asks by entry, the organizer's notes and
        # the lines it dropped for citing another passage, and what the
        # learner went on to (compare, the tutor). Counts only.
        "library": {
            "asks": len(library_asks),
            "by_entry": dict(Counter(a["entry"] for a in library_asks)),
            "personalized": _share(sum(1 for a in library_asks if a["personalized"]), len(library_asks)),
            "notes": dict(Counter(str(a["organizer"].get("status") or "not_run") for a in library_asks)),
            "lines_dropped": sum(len(a["organizer"].get("dropped_lines") or []) for a in library_asks),
            "compared": _share(sum(1 for a in library_asks if a["compared"]), len(library_asks)),
            "tutor_asked": _share(sum(1 for a in library_asks if a["tutor"]), len(library_asks)),
        },
        # RW1c: answers by mode, abstentions and excerpts dropped by quote
        # verification (a proxy for unsupported content), "another way" and
        # "that didn't help" rates with whether the inquiry was resolved after,
        # and the buttons shown and pressed by kind. Counts only.
        "tutor": {
            "answers": len(looked),
            "by_mode": {mode: sum(1 for a in looked if mode in (a["payload"]["tutor"].get("modes") or []))
                        for mode in ("excerpt", "grounded", "bridge")},
            "abstained": sum(1 for a in looked if a["payload"]["tutor"].get("abstained") is True),
            "excerpts_dropped": sum(1 for a in looked if a["payload"]["tutor"].get("dropped_excerpt")),
            "retrieval": dict(Counter(
                str((a["payload"]["tutor"].get("retrieval") or {}).get("status") or "unknown") for a in looked)),
            "another_way": _share(len(follow_ons["alternative"]), len(looked)),
            "didnt_help": _share(len(follow_ons["remediate"]), len(looked)),
            "resolved_after": {"another_way": resolved_after(follow_ons["alternative"]),
                               "didnt_help": resolved_after(follow_ons["remediate"])},
            "offers": {"shown": dict(offers_shown), "pressed": dict(offers_pressed),
                       "press_results": dict(press_results)},
        },
        # RW5a (spec §8.1): figures built by verification, unsupported requests
        # by kind, "not right?" versions, region requests, and predictions
        # (missed, and with a "what changed?" line). Counts only.
        "figures": {
            "built": dict(Counter(row["verification"] for row in figure_rows)),
            "unsupported_by_kind": dict(Counter(str(row["unsupported_kind"] or "unknown") for row in figure_rows
                                                if row["verification"] == "unsupported")),
            "revisions": sum(1 for row in figure_rows if row["revision"]),
            "regions": sum(1 for row in figure_rows if row["region"]),
            "predictions": len(prediction_rows),
            "predictions_missed": sum(1 for row in prediction_rows if not row["matched"]),
            "what_changed": sum(1 for row in prediction_rows if row["explained"]),
        },
        "routes": [
            {"job_kind": job_kind, "model": model, "prompt_version": version, "n": len(rows),
             "latency_ms": _percentiles(r["payload"].get("latency_ms") for r in rows)}
            for (job_kind, model, version), rows in sorted(routes.items(), key=lambda item: str(item[0]))
        ],
    }


__all__ = ["REPORT_VERSION", "build_reader_report"]
