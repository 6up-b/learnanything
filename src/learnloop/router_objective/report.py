"""``learnloop data-capture report``'s RO0 section: coverage per row of spec §4, and bytes measured per day.

Read-only. Size is measured, not assumed: each row's bytes are the lengths actually stored in its columns, and a new
table's pages come from ``dbstat`` where this SQLite has it. A row's coverage counts only what came after its first
receipt, so a vault's earlier history does not read as a gap. No effect is estimated.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import sqlite3
from typing import Any

from learnloop.db.stores import router_objective as store
from learnloop.router_objective import trajectory

_ACTIVE_TABLES: tuple[tuple[str, str, str], ...] = (
    (store.SESSION_RECEIPTS, "created_at", ""),
    (store.DECISION_STATE, "created_at", ""),
    (store.GOAL_EVENTS, "created_at", ""),
    ("question_events", "created_at", "reveal_state_json IS NOT NULL"),
    ("plan_presentations", "served_at", "ask_available IS NOT NULL"),
    ("source_exposure_events", "created_at", "initiator IS NOT NULL"),
    ("interaction_events", "created_at", "received_at IS NOT NULL"),
)


def _value(connection: sqlite3.Connection, sql: str, *parameters: Any) -> Any:
    return connection.execute(sql, parameters).fetchone()[0]


def _coverage(written: int, of: int) -> float | None:
    return round(written / of, 4) if of else None


def _row(written: int, of: int, stored_bytes: int, **more: Any) -> dict[str, Any]:
    return {"written": written, "of": of, "coverage": _coverage(written, of), "stored_bytes": stored_bytes, **more}


def _first(connection: sqlite3.Connection, table: str, clock: str, where: str) -> str | None:
    return _value(connection, f"SELECT MIN({clock}) FROM {table} WHERE {where}")


def _pages(connection: sqlite3.Connection, table: str) -> int | None:
    """The table's pages and its indexes', where this SQLite has ``dbstat``."""

    try:
        return int(_value(connection,
                          "SELECT COALESCE(SUM(pgsize), 0) FROM dbstat WHERE name = ? OR name IN "
                          "(SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = ?)", table, table))
    except sqlite3.Error:
        return None


def _question_rows(connection: sqlite3.Connection) -> dict[str, Any]:
    first = _first(connection, "question_events", "created_at", "reveal_state_json IS NOT NULL")
    # A cold Reader link row is a link to its question, which holds the state.
    since = int(_value(connection, "SELECT COUNT(*) FROM question_events WHERE created_at >= ? AND COALESCE(provider, '') != 'reader'",
                       first)) if first else 0
    written = int(_value(connection, "SELECT COUNT(reveal_state_json) FROM question_events"))
    known_visible = int(_value(connection, "SELECT COUNT(*) FROM question_events WHERE "
                                           "json_extract(reveal_state_json, '$.visible_now') IN ('visible', 'not_visible')"))
    row1 = _row(written, since, int(_value(connection, "SELECT COALESCE(SUM(LENGTH(reveal_state_json)), 0) FROM question_events")),
                visible_now_known=known_visible)
    scope = ("WHERE reveal_state_json IS NOT NULL")
    filled = {name: int(_value(connection, f"SELECT COUNT({name}) FROM question_events {scope}"))
              for name in ("hints_used_before", "scaffold_level", "preceding_tutor_move", "learner_mode")}
    bytes2 = int(_value(connection, "SELECT COALESCE(SUM(COALESCE(LENGTH(scaffold_level), 0) + "
                                    f"COALESCE(LENGTH(preceding_tutor_move), 0) + COALESCE(LENGTH(learner_mode), 0)), 0) "
                                    f"FROM question_events {scope}"))
    row2 = _row(filled["hints_used_before"], since, bytes2, filled=filled)
    opportunity = int(_value(connection, f"SELECT COUNT(question_opportunity) FROM question_events {scope}"))
    opportunity_bytes = int(_value(connection, f"SELECT COALESCE(SUM(LENGTH(question_opportunity)), 0) FROM question_events {scope}"))
    return {"row1": row1, "row2": row2, "opportunity": (opportunity, since, opportunity_bytes)}


def _row3(connection: sqlite3.Connection, opportunity: tuple[int, int, int]) -> dict[str, Any]:
    first = _first(connection, "plan_presentations", "served_at", "ask_available IS NOT NULL")
    written = int(_value(connection, "SELECT COUNT(ask_available) FROM plan_presentations"))
    since = int(_value(connection, "SELECT COUNT(*) FROM plan_presentations WHERE served_at >= ?", first)) if first else 0
    changes = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(LENGTH(detail_json)), 0) FROM attention_block_events WHERE kind = 'ask_availability_changed'"
    ).fetchone()
    visits = connection.execute(
        "SELECT COUNT(*), COUNT(json_extract(payload_json, '$.ask_available')) FROM interaction_events WHERE kind = 'reader_view_opened'"
    ).fetchone()
    return _row(written, since, int(changes[1]) + written + opportunity[2], later_changes=int(changes[0]),
                reader_visits=int(visits[0]), reader_visits_with_it=int(visits[1]),
                questions_with_an_opportunity=opportunity[0], questions=opportunity[1])


def _row4(connection: sqlite3.Connection) -> dict[str, Any]:
    first = _first(connection, "source_exposure_events", "created_at", "initiator IS NOT NULL")
    written = int(_value(connection, "SELECT COUNT(initiator) FROM source_exposure_events"))
    since = int(_value(connection, "SELECT COUNT(*) FROM source_exposure_events WHERE created_at >= ?", first)) if first else 0
    by = dict(Counter({str(row[0]): int(row[1]) for row in connection.execute(
        "SELECT initiator, COUNT(*) FROM source_exposure_events WHERE initiator IS NOT NULL GROUP BY initiator")}))
    stored = int(_value(connection, "SELECT COALESCE(SUM(COALESCE(LENGTH(initiator), 0) + COALESCE(LENGTH(initiator_block_id), 0) + "
                                    "COALESCE(LENGTH(initiator_session_id), 0) + COALESCE(LENGTH(initiator_visit_id), 0)), 0) "
                                    "FROM source_exposure_events"))
    return _row(written, since, stored, by_initiator=by)


def _row5(connection: sqlite3.Connection) -> dict[str, Any]:
    first = _first(connection, "interaction_events", "created_at", "received_at IS NOT NULL")
    written = int(_value(connection, "SELECT COUNT(received_at) FROM interaction_events"))
    stamped = int(_value(connection, "SELECT COUNT(occurred_at) FROM interaction_events WHERE received_at IS NOT NULL"))
    since = int(_value(connection, "SELECT COUNT(*) FROM interaction_events WHERE created_at >= ?", first)) if first else 0
    stored = int(_value(connection, "SELECT COALESCE(SUM(COALESCE(LENGTH(occurred_at), 0) + COALESCE(LENGTH(received_at), 0)), 0) "
                                    "FROM interaction_events WHERE received_at IS NOT NULL"))
    return _row(written, since, stored, with_a_client_time=stamped)


def _sessions(connection: sqlite3.Connection) -> dict[str, Any]:
    first = _first(connection, store.SESSION_RECEIPTS, "created_at", "kind = 'availability'")
    started = int(_value(connection, "SELECT COUNT(*) FROM sessions WHERE started_at >= ?", first)) if first else 0
    ended = int(_value(connection, "SELECT COUNT(*) FROM sessions WHERE started_at >= ? AND ended_at IS NOT NULL", first)) if first else 0
    rows = [dict(row) for row in connection.execute(
        "SELECT kind, minutes_source, end_reason, end_basis, COALESCE(LENGTH(local_time), 0) + COALESCE(LENGTH(time_zone), 0) "
        "+ COALESCE(LENGTH(device), 0) + COALESCE(LENGTH(minutes_source), 0) + COALESCE(LENGTH(end_reason), 0) "
        "+ COALESCE(LENGTH(detail_json), 0) AS size FROM session_receipts")]
    availability = [row for row in rows if row["kind"] == "availability"]
    ends = [row for row in rows if row["kind"] == "end"]
    overrides = [row for row in rows if row["kind"] == "stop_response"]
    return {
        "row7": _row(len(ends), ended, sum(row["size"] for row in [*ends, *overrides]),
                     by_reason=dict(Counter(f"{row['end_reason']}/{row['end_basis']}" for row in ends)),
                     overrides=len(overrides)),
        "row8": _row(len(availability), started, sum(row["size"] for row in availability),
                     missing=sum(1 for row in availability if row["minutes_source"] == "missing")),
    }


def _decision_state(connection: sqlite3.Connection) -> dict[str, Any]:
    first = _first(connection, store.DECISION_STATE, "created_at", "1 = 1")
    decisions = Counter({str(row[0]): int(row[1]) for row in connection.execute(
        "SELECT decision_kind, COUNT(*) FROM router_decisions WHERE created_at >= ? GROUP BY decision_kind", (first or "",))
    }) if first else Counter()
    written = Counter({str(row[0]): int(row[1]) for row in connection.execute(
        "SELECT decision_kind, COUNT(*) FROM decision_state_receipts GROUP BY decision_kind")})
    size = connection.execute(
        "SELECT COALESCE(SUM(stored_bytes), 0), COALESCE(SUM(raw_bytes), 0), COALESCE(AVG(candidate_items), 0), "
        "COALESCE(AVG(candidate_los), 0) FROM decision_state_receipts").fetchone()
    # A learner's pick from an offer reads its parent's, as its prefilter does.
    covered = sum(count for kind, count in decisions.items() if kind != "learner_pick")
    return _row(sum(written.values()), covered, int(size[0]), uncompressed_bytes=int(size[1]),
                candidate_items_mean=round(float(size[2]), 1), candidate_los_mean=round(float(size[3]), 1),
                by_decision_kind={kind: {"receipts": written[kind], "decisions": decisions[kind]}
                                  for kind in sorted(set(decisions) | set(written))})


def _row10(connection: sqlite3.Connection) -> dict[str, Any]:
    arranged = int(_value(connection, "SELECT COUNT(*) FROM decision_objectives WHERE measurement = 'arranged' AND created_at >= "
                                      "COALESCE((SELECT MIN(created_at) FROM decision_objectives WHERE delay_json IS NOT NULL), '9')"))
    delays = int(_value(connection, "SELECT COUNT(delay_json) FROM decision_objectives"))
    typed = int(_value(connection, "SELECT COUNT(non_service_type) FROM decision_measurement_events"))
    first = _first(connection, "decision_measurement_events", "created_at", "non_service_type IS NOT NULL")
    unserved = int(_value(connection, "SELECT COUNT(*) FROM decision_measurement_events WHERE state = 'unavailable' AND created_at >= ?",
                          first)) if first else 0
    untyped = sorted({str(row[0]) for row in connection.execute(
        "SELECT reason FROM decision_measurement_events WHERE state = 'unavailable' AND non_service_type IS NULL AND created_at >= ?",
        (first or "9",))})
    stored = int(_value(connection, "SELECT COALESCE(SUM(LENGTH(delay_json)), 0) FROM decision_objectives")) + int(_value(
        connection, "SELECT COALESCE(SUM(COALESCE(LENGTH(delay_json), 0) + COALESCE(LENGTH(non_service_type), 0)), 0) "
                    "FROM decision_measurement_events"))
    return _row(delays, arranged, stored, unserved=unserved, unserved_typed=typed, untyped_reasons=untyped)


def _row11(connection: sqlite3.Connection, goal_ids: Sequence[str]) -> dict[str, Any]:
    events = Counter({str(row[0]): int(row[1]) for row in connection.execute(
        "SELECT event, COUNT(*) FROM goal_lifecycle_events GROUP BY event")})
    seen = {str(row[0]) for row in connection.execute("SELECT DISTINCT goal_id FROM goal_lifecycle_events")}
    stored = int(_value(connection, "SELECT COALESCE(SUM(LENGTH(event) + LENGTH(reason) + COALESCE(LENGTH(status), 0) + "
                                    "COALESCE(LENGTH(due_at), 0) + COALESCE(LENGTH(previous_due_at), 0)), 0) FROM goal_lifecycle_events"))
    return _row(len(seen & set(goal_ids)), len(goal_ids), stored, by_event=dict(events))


def _row12(connection: sqlite3.Connection) -> dict[str, Any]:
    links = trajectory.rows(connection)
    return {
        "written": len(links), "of": len(links), "coverage": 1.0 if links else None, "stored_bytes": 0, "version": trajectory.VERSION,
        "with_an_action": sum(1 for row in links if row["block_id"] or row["presentations"] or row["scheduler_slate_id"]),
        "with_uptake": sum(1 for row in links if row["attempts_on_presentations"] or row["attempts_on_offer"]),
        "with_a_rejection": sum(1 for row in links if row["items_rejected"]),
        "next_decision_censored": sum(1 for row in links if row["next_decision_censored"]),
        "return_censored": sum(1 for row in links if row["return_censored"]),
    }


def _active_days(connection: sqlite3.Connection) -> list[str]:
    days: set[str] = set()
    for table, clock, where in _ACTIVE_TABLES:
        clause = f"WHERE {where}" if where else ""
        days |= {str(row[0]) for row in connection.execute(
            f"SELECT DISTINCT substr({clock}, 1, 10) FROM {table} {clause}") if row[0]}
    return sorted(days)


def section(connection: sqlite3.Connection, *, goal_ids: Sequence[str]) -> dict[str, Any]:
    """Coverage per row, and what it costs."""

    if not store.table_present(connection, store.DECISION_STATE):
        return {"available": False, "reason": "this database predates migration 243"}
    questions = _question_rows(connection)
    sessions = _sessions(connection)
    state = _decision_state(connection)
    rows = {
        "1_disclosure_state": questions["row1"],
        "2_generating_process": questions["row2"],
        "3_question_opportunity": _row3(connection, questions["opportunity"]),
        "4_exposure_initiator": _row4(connection),
        "5_event_times": _row5(connection),
        "7_session_end": sessions["row7"],
        "8_availability": sessions["row8"],
        "9_13_decision_state": state,
        "10_cold_check_timing": _row10(connection),
        "11_goal_lifecycle": _row11(connection, goal_ids),
        "12_trajectory": _row12(connection),
    }
    days = _active_days(connection)
    total = sum(int(row["stored_bytes"]) for row in rows.values())
    return {
        "available": True,
        "rows": rows,
        "active_days": len(days),
        "stored_bytes": total,
        "bytes_per_active_day": round(total / len(days), 1) if days else None,
        "per_row_bytes_per_active_day": {name: round(int(row["stored_bytes"]) / len(days), 1) if days else None
                                         for name, row in rows.items()},
        "new_table_pages_bytes": {table: _pages(connection, table)
                                  for table in (store.SESSION_RECEIPTS, store.DECISION_STATE, store.GOAL_EVENTS)},
    }


def lines(report: dict[str, Any]) -> list[str]:
    if not report.get("available"):
        return [f"Router objective receipts: unavailable ({report.get('reason')})"]
    out = [f"Router objective receipts: {report['stored_bytes']} bytes over {report['active_days']} active days, "
           f"{report['bytes_per_active_day']} per active day"]
    for name, row in report["rows"].items():
        out.append(f"  row {name}: {row['written']} of {row['of']} (coverage {row['coverage']}), "
                   f"{report['per_row_bytes_per_active_day'][name]} bytes per active day")
    return out


__all__ = ["lines", "section"]
