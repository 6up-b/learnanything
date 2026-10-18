"""`learnloop hints report`: H2b's rows (spec_adaptive_hints_v1 §6.1, §6.3).

The descriptive rows per kind and level gain what H2's rows can say: the
"doesn't connect" replies by shortcut (``hint_fit`` verdicts), the level of
the help that followed, the outcome placements (``hint_outcome`` verdicts),
the chooser that served each hint, and for waypoints the goals reached
without more help and the smaller steps taken. Unaided next progress is
settled, where the grade cannot settle it, by the next hint's placement
(the work had reached the hint's target before more help) or by the outcome
placement of the final answer (:func:`progress_by_placement`).

Top-level sections: the **expertise-reversal split** (the same columns by the
LO's placement intent and by the predictor's P(success) at request time,
where the row logged them: H2b's rows do, earlier rows say ``not_logged``;
P(success) is split at the median of the logged values, a data-relative cut
reported with its value, never a hand-set threshold), **help abuse and
avoidance** as counts (requests in a row on unchanged work, with the gap
between them; unassisted submissions not fully correct, with their
latency), and **latency and cost per route** (the chooser, the writer,
outcome placement and the maps: p50/p95, re-asks, withholds, fallbacks by
reason, receipts' tokens and metered cost).

Every number carries its sample size; nothing here is a threshold (§6).
Pure read: no model call, and no learner text is read (never
``feedback_text``, ``body_md`` or a receipt's input or output).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from typing import Any

#: The four "doesn't connect" shortcuts, and a reply sent with none.
SHORTCUTS = ("not_where_stuck", "too_big", "learner_route", "notation", "none")
#: The routes whose receipts the report sums (owner kinds).
ROUTE_OWNER_KINDS = ("hint_chooser", "hint_writer", "hint_outcome", "approach_map")
#: Why no hint could be written (the writer-down reasons, H2a's service).
WRITER_DOWN_REASONS = ("codex_refused", "capped", "unpriced", "writer_failed", "unavailable", "models_off",
                       "unrouted")
#: Placement intents (``placement/state.py``), and a row that logged none.
INTENTS = ("assumed", "learning", "maintenance", "unknown", "not_logged")


def loads(value: Any) -> Any:
    try:
        return json.loads(value) if value else None
    except (TypeError, ValueError):
        return None


def answered_id(row: Mapping[str, Any]) -> str | None:
    options = loads(row.get("options_json"))
    return str(options["answered_assist_id"]) if isinstance(options, dict) and options.get("answered_assist_id") \
        else None


def state_at_request(row: Mapping[str, Any]) -> dict[str, Any] | None:
    failures = loads(row.get("contract_failures_json"))
    state = failures.get("state_at_request") if isinstance(failures, dict) else None
    return state if isinstance(state, dict) else None


def table_exists(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def ledger(connection: Any, task: str) -> list[dict[str, Any]]:
    if not table_exists(connection, "judgment_ledger"):
        return []
    return [dict(row) for row in connection.execute(
        "SELECT left_kind, left_id, right_id, verdict, rationale, created_at FROM judgment_ledger WHERE task = ? "
        "ORDER BY created_at, id", (task,)).fetchall()]


def map_paths(connection: Any, map_ids: Iterable[str]) -> dict[str, dict[str, list[str]]]:
    """Each referenced map's routes (id -> node path); structure only."""

    ids = sorted({str(value) for value in map_ids if value})
    if not ids or not table_exists(connection, "approach_maps"):
        return {}
    out: dict[str, dict[str, list[str]]] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for found in connection.execute(
                f"SELECT id, map_json FROM approach_maps WHERE id IN ({', '.join('?' for _ in chunk)})", chunk):
            payload = loads(found["map_json"]) or {}
            out[str(found["id"])] = {str(route.get("id")): [str(node) for node in route.get("path") or ()]
                                     for route in payload.get("routes") or () if isinstance(route, dict)}
    return out


def hint_target(row: Mapping[str, Any], routes: Mapping[str, list[str]]) -> str | None:
    """The hint's target node, or for a kind without one the next node from
    where it was placed (§6.1)."""

    target = row.get("target_node_id")
    if target:
        return str(target)
    path = routes.get(str(row.get("route_id") or ""))
    start = row.get("from_node_id")
    if path and start and start in path and path.index(start) + 1 < len(path):
        return path[path.index(start) + 1]
    return None


def progress_by_next_placement(row: Mapping[str, Any], following: Mapping[str, Any],
                               maps: Mapping[str, Mapping[str, list[str]]]) -> str | None:
    """``reached`` / ``not_reached`` when the next hint's placement (the node
    the work had reached when more help was asked, on the same map and
    route) settles whether this hint's target was reached first; else None."""

    if not row.get("map_id") or row.get("map_id") != following.get("map_id"):
        return None
    routes = maps.get(str(row["map_id"])) or {}
    target = hint_target(row, routes)
    reached = following.get("from_node_id")
    path = routes.get(str(following.get("route_id") or "")) or routes.get(str(row.get("route_id") or ""))
    if not target or not reached or not path or target not in path or reached not in path:
        return None
    return "reached" if path.index(target) <= path.index(reached) else "not_reached"


def _band_p(value: float | None, median: float | None) -> str:
    if value is None or median is None:
        return "not_logged"
    return "at_or_above_median" if value >= median else "below_median"


def expertise_reversal(members: list[dict[str, Any]], *, summarize: Callable[[list[dict[str, Any]]], dict[str, Any]]
                       ) -> dict[str, Any]:
    """The same columns split by placement intent and by P(success) at
    request time (§6.3), per kind and level, where the row logged them."""

    logged = sorted(float(state["p_success"]) for state in (state_at_request(row) for row in members)
                    if state and state.get("p_success") is not None)
    median = logged[(len(logged) - 1) // 2] if logged else None
    by_intent: dict[tuple[str, int | None, str], list[dict[str, Any]]] = defaultdict(list)
    by_p: dict[tuple[str, int | None, str], list[dict[str, Any]]] = defaultdict(list)
    for row in members:
        state = state_at_request(row)
        intent = "not_logged" if state is None else str(state.get("placement_intent") or "unknown")
        key = (str(row.get("hint_kind")), row.get("level"))
        by_intent[(*key, intent)].append(row)
        by_p[(*key, _band_p(state.get("p_success") if state else None, median))].append(row)

    def split(groups: Mapping[tuple[str, int | None, str], list[dict[str, Any]]], name: str) -> list[dict[str, Any]]:
        return [{"hint_kind": kind, "level": level, name: band, **summarize(rows)}
                for (kind, level, band), rows in sorted(groups.items(), key=lambda entry: tuple(
                    "" if part is None else str(part) for part in entry[0]))]

    return {
        "by_placement_intent": split(by_intent, "placement_intent"),
        "by_p_success": split(by_p, "p_success_band"),
        "p_success_median": median,
        "p_success_logged": len(logged),
        "basis": ("rows the hint service wrote from H2b on log the placement intent and P(success) the chooser "
                  "read at request time; P(success) is split at the median of the logged values"),
    }


def help_seeking(connection: Any, all_rows: list[dict[str, Any]], *, since: str | None,
                 percentiles: Callable[[Iterable[float | None]], dict[str, Any]],
                 share: Callable[[int, int], dict[str, Any]], when: Callable[[Any], Any],
                 surface: str | None = None) -> dict[str, Any]:
    """Help abuse and avoidance, as counts with their distributions (§6.3; H4:
    nothing is gated on them). ``all_rows`` is the selection's hint rows;
    avoidance reads the attempts of the selected ``surface`` (review F7)."""

    by_submission: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        if row["assist_kind"] == "hint" and row["submission_id"]:
            by_submission[(row["submission_id"], row["practice_item_id"])].append(row)
    pairs = unchanged = 0
    gaps: list[float] = []
    for rows in by_submission.values():
        ordered = sorted(rows, key=lambda row: (row["requested_at"], row["id"]))
        for earlier, later in zip(ordered, ordered[1:]):
            pairs += 1
            if earlier["work_hash"] and earlier["work_hash"] == later["work_hash"] and (later["request"] or "more") \
                    == "more":
                unchanged += 1
                start, end = when(earlier["shown_at"] or earlier["requested_at"]), when(later["requested_at"])
                if start is not None and end is not None:
                    gaps.append(round(max(0.0, (end - start).total_seconds()), 3))
    return {
        "abuse": {
            "requests_in_a_row_on_unchanged_work": share(unchanged, pairs),
            "seconds_between_them": percentiles(gaps),
            "basis": "two hint requests of one attempt in a row, the second a plain request with the work unchanged",
        },
        "avoidance": _avoidance(connection, all_rows, since=since, surface=surface, percentiles=percentiles),
        "nothing_is_gated_on_these": True,
    }


#: The attempts each assist surface submits (``practice_attempts.entry_surface``),
#: so ``--surface`` selects avoidance's attempts too (H2b review F7). The
#: guided redo and the tutor submit no attempt of their own surface yet (H4).
ATTEMPT_SURFACES: dict[str, tuple[str, ...]] = {
    "practice": ("desktop_practice",),
    "workbench": ("desktop_practice_workbench", "desktop_reader_workbench"),
}


def _avoidance(connection: Any, all_rows: list[dict[str, Any]], *, since: str | None, surface: str | None,
               percentiles: Callable[[Iterable[float | None]], dict[str, Any]]) -> dict[str, Any]:
    basis = "graded submissions not fully correct with no hint, no tutor hint and no worked help"
    entry_surfaces: tuple[str, ...] | None = None
    if surface is not None:
        entry_surfaces = ATTEMPT_SURFACES.get(surface)
        if entry_surfaces is None:
            return {"unassisted_not_fully_correct": None, "of_graded_unassisted_not_fully_correct": None,
                    "latency_seconds": percentiles(()), "surface": surface,
                    "basis": f"no attempt is submitted from the {surface} surface yet: not measured"}
    hinted = {row["attempt_id"] for row in all_rows if row["attempt_id"]}
    query = ("SELECT id, latency_seconds, correctness FROM practice_attempts WHERE COALESCE(hints_used, 0) = 0 "
             "AND COALESCE(primed, 0) = 0 AND correctness IS NOT NULL")
    parameters: list[Any] = []
    if since is not None:
        query += " AND created_at >= ?"
        parameters.append(since)
    if entry_surfaces is not None:
        query += f" AND entry_surface IN ({', '.join('?' for _ in entry_surfaces)})"
        parameters.extend(entry_surfaces)
    wrong = [dict(row) for row in connection.execute(query, parameters).fetchall()
             if float(row["correctness"]) < 1.0 - 1e-9]
    avoided = [row for row in wrong if row["id"] not in hinted]
    return {
        "unassisted_not_fully_correct": len(avoided),
        "of_graded_unassisted_not_fully_correct": len(wrong),
        "latency_seconds": percentiles(row["latency_seconds"] for row in avoided),
        **({"entry_surfaces": list(entry_surfaces)} if entry_surfaces is not None else {}),
        "basis": basis,
    }


def routes(connection: Any, all_rows: list[dict[str, Any]], *, since: str | None,
           percentiles: Callable[[Iterable[float | None]], dict[str, Any]], when: Callable[[Any], Any],
           writer_prompt_version: str, surface: str | None = None) -> dict[str, Any]:
    """Latency and cost per route (§6.3): the chooser, the writer, outcome
    placement and the maps. The chooser's judgments are those of the
    selection's rows (``left_id`` is the assist, review F7); the receipts are
    every surface's, and say so (``receipts_scope``)."""

    hint_rows = [row for row in all_rows if row["assist_kind"] == "hint" and row["chooser"] != "none"]
    written = [row for row in hint_rows if row["prompt_version"] == writer_prompt_version]
    outcomes: Counter = Counter()
    reasons: Counter = Counter()
    reasks = 0
    chooser_reasons: Counter = Counter()
    for row in hint_rows:
        record = loads(row["contract_failures_json"]) or {}
        outcomes[str(record.get("outcome") or "unknown")] += 1
        reason = record.get("reason")
        if reason in WRITER_DOWN_REASONS:
            reasons[str(reason)] += 1
        if len(record.get("rounds") or ()) > 1:
            reasks += 1
        if row["chooser"] == "fallback":
            chooser_reasons[str(record.get("chooser_reason") or "unknown")] += 1
    selected = {str(row["id"]) for row in all_rows}
    choices = [entry for entry in ledger(connection, "hint_choice")
               if (since is None or entry["created_at"] >= since)
               and (surface is None or str(entry["left_id"]) in selected)]
    choice_status: Counter = Counter()
    choice_latency: list[float] = []
    for entry in choices:
        rationale = loads(entry["rationale"]) or {}
        choice_status[str(rationale.get("status") or entry["verdict"])] += 1
        if rationale.get("latency_ms") is not None:
            choice_latency.append(float(rationale["latency_ms"]))
    receipts = _receipts(connection, since=since, percentiles=percentiles, when=when)
    return {
        "hint_chooser": {
            "requests": len(choices), "by_status": dict(sorted(choice_status.items())),
            "latency_ms": percentiles(choice_latency),
            "served_by": dict(sorted(Counter(row["chooser"] for row in hint_rows).items())),
            "fallbacks_by_reason": dict(sorted(chooser_reasons.items())),
            "receipts": receipts.get("hint_chooser"),
        },
        "hint_writer": {
            "requests": len(hint_rows), "written": len(written),
            "latency_ms": percentiles(row["latency_ms"] for row in written),
            "re_asked": reasks, "withheld": outcomes.get("withheld", 0), "downgraded": outcomes.get("downgraded", 0),
            "cancelled": outcomes.get("cancelled", 0), "failed": outcomes.get("failed", 0),
            "outcomes": dict(sorted(outcomes.items())),
            "fallbacks_by_reason": dict(sorted(reasons.items())),
            "receipts": receipts.get("hint_writer"),
        },
        "hint_outcome": {"receipts": receipts.get("hint_outcome")},
        "approach_map": {"receipts": receipts.get("approach_map")},
        "receipts_scope": "all_surfaces",
        "basis": ("the hint rows of the selection (shown or not), the chooser's hint_choice ledger rows and the "
                  "model receipts of each route since the start (receipts are not split by surface); cost is "
                  "the receipts' metered cost, subscription calls are estimated_only"),
    }


def _receipts(connection: Any, *, since: str | None, percentiles: Callable[[Iterable[float | None]], dict[str, Any]],
              when: Callable[[Any], Any]) -> dict[str, dict[str, Any]]:
    if not table_exists(connection, "model_call_receipts"):
        return {}
    query = (f"SELECT owner_kind, status, input_tokens, output_tokens, cost, started_at, finished_at "
             f"FROM model_call_receipts WHERE parent_call_id IS NULL AND owner_kind IN "
             f"({', '.join('?' for _ in ROUTE_OWNER_KINDS)})")
    parameters: list[Any] = list(ROUTE_OWNER_KINDS)
    if since is not None:
        query += " AND started_at >= ?"
        parameters.append(since)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in connection.execute(query, parameters).fetchall():
        grouped[str(row["owner_kind"])].append(dict(row))
    out: dict[str, dict[str, Any]] = {}
    for kind in ROUTE_OWNER_KINDS:
        rows = grouped.get(kind, [])
        seconds = []
        for row in rows:
            start, end = when(row["started_at"]), when(row["finished_at"])
            if start is not None and end is not None:
                seconds.append(round(max(0.0, (end - start).total_seconds()), 3))
        out[kind] = {
            "calls": len(rows), "by_status": dict(sorted(Counter(str(row["status"]) for row in rows).items())),
            "input_tokens": sum(int(row["input_tokens"] or 0) for row in rows),
            "output_tokens": sum(int(row["output_tokens"] or 0) for row in rows),
            "metered_cost_usd": round(sum(float(row["cost"] or 0.0) for row in rows), 6),
            "seconds": percentiles(seconds),
        }
    return out


__all__ = [
    "ATTEMPT_SURFACES", "INTENTS", "ROUTE_OWNER_KINDS", "SHORTCUTS", "answered_id", "expertise_reversal", "help_seeking", "hint_target",
    "ledger", "map_paths", "progress_by_next_placement", "routes", "state_at_request",
]
