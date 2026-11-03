"""The M2 usage report (mobile spec §9, §10): read-only, no thresholds.

``suspected_figure`` (§6.4) is a pattern over the prompts of items that reached the phone.
**It is report-only.** §6.4 says pattern lists misfire, so nothing that decides serving reads
it: eligibility reads Markdown structure (``scheduling.device_eligibility``), and a prompt this
pattern catches stays eligible. A hit is a prompt for the owner to look at, in case its figure was
lost on the way into text. Both directions of error are visible and cost nothing here.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
import math
import re
from typing import Any, Mapping

from learnloop.db.repositories import Repository

SUBMIT_ENDPOINTS = ("rpc:submit_attempt", "rpc:submit_dont_know")
GRADE_CONTEST = "grade_contest"
_NOUN = r"(?:figure|fig\.|diagram|picture|image|graph|plot|chart|table|illustration)"
_LOCATOR = r"(?:above|below|shown|pictured|following|attached|see|given in)"
#: A locator and a figure's noun in one sentence: "see the figure", "the graph below".
#: "Graph the function" has no locator, and is not a hit.
_SUSPECTED_FIGURE = re.compile(
    rf"\b{_LOCATOR}\b[^.?!\n]{{0,40}}\b{_NOUN}|\b{_NOUN}[^.?!\n]{{0,40}}\b{_LOCATOR}\b", re.IGNORECASE
)


def suspected_figure(prompt: str) -> str | None:
    """The phrase that reads like a missing figure, or None. Report-only (module docstring)."""

    match = _SUSPECTED_FIGURE.search(prompt or "")
    return match.group(0) if match else None


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)], 3)


def _week(stamp: str) -> str:
    year, week, _day = datetime.fromisoformat(stamp.replace("Z", "+00:00")).isocalendar()
    return f"{year}-W{week:02d}"


def _seconds(start: str, end: str) -> float:
    return (datetime.fromisoformat(end.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()


def _rate(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def mobile_report(repo: Repository, *, prompts: Mapping[str, str] | None = None) -> dict[str, Any]:
    """§9's M2a report, §10's device split and §6.4's suspected figures.

    ``prompts`` is the loaded vault's item prompts; without it the suspected-figure list is
    not computed (``None``), which says so rather than reporting an empty list.
    """

    with repo.connection() as conn:
        attempts = [dict(row) for row in conn.execute(
            "SELECT id, session_id, practice_item_id, entry_surface, created_at FROM practice_attempts"
        )]
        ended = {row["id"] for row in conn.execute("SELECT id FROM sessions WHERE ended_at IS NOT NULL")}
        jobs = [dict(row) for row in conn.execute(
            "SELECT method, state, accepted_at, finished_at FROM mobile_jobs "
            "WHERE method IN ('submit_attempt','submit_dont_know')"
        )]
        logged = Counter(
            int(row["status"])
            for row in conn.execute(
                "SELECT status FROM mobile_request_log WHERE endpoint IN (?,?)", SUBMIT_ENDPOINTS
            )
        )
        contests = [json.loads(row[0] or "{}") for row in conn.execute(
            "SELECT claim_ref FROM hypothesis_events WHERE event_type='presented' AND claim_type=?", (GRADE_CONTEST,)
        )]
        offered = [row[0] for row in conn.execute(
            """SELECT DISTINCT c.practice_item_id FROM scheduler_offer_receipts r
               JOIN scheduler_slate_candidates c ON c.slate_id = r.slate_id AND c.was_returned = 1
               WHERE r.entry_surface = 'phone_queue'"""
        )]

    phone = [row for row in attempts if row["entry_surface"] == "phone_practice"]
    by_week: dict[str, dict[str, set[str]]] = {}
    for row in phone:
        week = by_week.setdefault(_week(row["created_at"]), {"sessions": set(), "attempts": set(), "items": set()})
        week["sessions"].add(str(row["session_id"]))
        week["attempts"].add(str(row["id"]))
        week["items"].add(str(row["practice_item_id"]))
    phone_sessions = {str(row["session_id"]) for row in phone}
    latencies = [
        _seconds(job["accepted_at"], job["finished_at"]) for job in jobs if job["state"] == "completed" and job["finished_at"]
    ]
    answered = sum(count for status, count in logged.items() if status in (200, 202))
    surface_of = {str(row["id"]): str(row["entry_surface"]) for row in attempts}
    contested = {str(ref.get("attemptId")) for ref in contests if ref.get("attemptId")}
    split = Counter(surface_of.values())
    contest_by_surface = Counter(surface_of[attempt] for attempt in contested if attempt in surface_of)
    served = sorted(set(offered) | {str(row["practice_item_id"]) for row in phone})
    figures = None
    if prompts is not None:
        figures = []
        for item_id in served:
            phrase = suspected_figure(prompts.get(item_id, ""))
            if phrase:
                figures.append({"practice_item_id": item_id, "phrase": phrase})
    return {
        "weeks": {
            week: {"sessions": len(values["sessions"]), "attempts": len(values["attempts"]), "items": len(values["items"])}
            for week, values in sorted(by_week.items())
        },
        "phone_sessions": len(phone_sessions),
        "phone_sessions_ended": len(phone_sessions & ended),
        "completion": _rate(len(phone_sessions & ended), len(phone_sessions)),
        "submit_to_feedback_seconds": {"count": len(latencies), "p50": _percentile(latencies, 0.5), "p95": _percentile(latencies, 0.95)},
        "share_of_submits_returning_202": _rate(logged[202], answered),
        "attempts_by_surface": dict(sorted(split.items())),
        "contest_rate_by_surface": {surface: _rate(contest_by_surface[surface], count) for surface, count in sorted(split.items())},
        "suspected_figure": figures,
        "suspected_figure_note": "Report-only: a word pattern. Nothing that decides serving reads it (spec §6.4).",
    }
