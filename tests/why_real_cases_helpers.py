"""What other test files use from ``tests/test_why_real_cases.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3


#: What counts as the vault's activity: the newest of these timestamps is when the copy's history ends.
ACTIVITY = (("practice_attempts", "created_at"), ("router_decisions", "created_at"),
            ("model_call_receipts", "started_at"))
#: Per case, the tables it reads and the moment its events were over (a copy must reach past it to hold them):
#: case 1 happened on Nov 7, cases 2-4 on Nov 8.
CASE_NEEDS = {
    1: (("router_decisions", "model_call_receipts"), "2026-11-08T00:00:00Z"),
    2: (("router_decisions", "router_suggestion_responses"), "2026-11-09T00:00:00Z"),
    3: (("interactive_figures", "figure_requests", "model_call_receipts"), "2026-11-09T00:00:00Z"),
    4: (("figure_prefetch_decisions", "figure_requests", "model_call_receipts"), "2026-11-09T00:00:00Z"),
}


def _present(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (table,)).fetchone() is not None


def newest_activity(connection: sqlite3.Connection) -> str | None:
    """The newest attempt, router decision or model call in the copy (normalized to ``...Z``), or None."""

    found = []
    for table, column in ACTIVITY:
        if _present(connection, table):
            row = connection.execute(f"SELECT MAX({column}) FROM {table}").fetchone()
            if row and row[0]:
                found.append(str(row[0]).replace("+00:00", "Z"))
    return max(found) if found else None


def skip_reason(connection: sqlite3.Connection, case: int) -> str | None:
    """Why the copy cannot hold case ``case``'s events (skip), or None when it can (the case must then find them)."""

    tables, events_over = CASE_NEEDS[case]
    missing = [table for table in tables if not _present(connection, table)]
    if missing:
        return f"case {case}: the copy predates the tables it reads ({', '.join(missing)})"
    newest = newest_activity(connection)
    if newest is None or newest < events_over:
        return f"case {case}: the copy's newest activity ({newest}) is before {events_over}; it needs a later backup"
    return None
