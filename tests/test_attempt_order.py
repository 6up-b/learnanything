"""The attempt ledger's order and its prefix boundaries (``learnloop.db.attempt_order``).

The SQL and Python forms of each policy agree on every pair of attempts, the legacy policy is the predecessor's
``(created_at, id)`` exactly, and the application policy breaks only ties inside one ``created_at``.
"""

from __future__ import annotations

import itertools
import sqlite3
from contextlib import closing

import pytest

from learnloop.db.attempt_order import (
    APPLICATION_ORDER,
    BASIS_APPLIED,
    BASIS_LEGACY_ORDER_UNKNOWN,
    LEGACY_ORDER,
    UNBOUND_SEQUENCE,
    application_sequences,
    rank_legacy_attempts,
    reserve_application_sequence,
)

T0 = "2026-10-12T09:00:00Z"
T1 = "2026-10-12T09:00:01Z"

#: (id, created_at, sequence or None). Ids sort A < B < C < D < E; the sequences say B, then A, were applied in T0,
#: then D in T1 before C (C unbound: no row), and E unbound in T1.
ROWS = (
    ("A", T0, 2),
    ("B", T0, 1),
    ("C", T1, None),
    ("D", T1, 3),
    ("E", T1, None),
)


def _database():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE practice_attempts (id TEXT PRIMARY KEY, created_at TEXT NOT NULL)")
    connection.execute(
        "CREATE TABLE attempt_application_order (sequence INTEGER PRIMARY KEY, attempt_id TEXT NOT NULL UNIQUE, "
        "basis TEXT NOT NULL, algorithm_version TEXT NOT NULL, recorded_at TEXT NOT NULL)"
    )
    for attempt_id, created_at, sequence in ROWS:
        connection.execute("INSERT INTO practice_attempts VALUES (?, ?)", (attempt_id, created_at))
        if sequence is not None:
            connection.execute(
                "INSERT INTO attempt_application_order VALUES (?, ?, 'applied', 'mvp-0.65', ?)",
                (sequence, attempt_id, T0),
            )
    return connection


def _sql_order(connection, order, *, descending=False):
    terms = order.order_sql(attempt_id="practice_attempts.id", descending=descending)
    return [row[0] for row in connection.execute(f"SELECT id FROM practice_attempts ORDER BY {terms}")]


def _sql_before(connection, order, bound):
    predicate, args = order.before_sql(bound, attempt_id="practice_attempts.id")
    return {row[0] for row in connection.execute(f"SELECT id FROM practice_attempts WHERE {predicate}", args)}


def test_the_legacy_order_is_created_at_then_id_whatever_the_sequences_say():
    with closing(_database()) as connection:
        assert _sql_order(connection, LEGACY_ORDER) == ["A", "B", "C", "D", "E"]
        assert _sql_order(connection, LEGACY_ORDER, descending=True) == ["E", "D", "C", "B", "A"]
        sequences = application_sequences(connection)
    rows = [{"id": i, "created_at": c} for i, c, _ in ROWS]
    assert LEGACY_ORDER.sorted(rows, sequences) == rows  # as its SQL reader gave them


def test_the_application_order_breaks_ties_by_sequence_and_unbound_rows_last_by_id():
    with closing(_database()) as connection:
        assert _sql_order(connection, APPLICATION_ORDER) == ["B", "A", "D", "C", "E"]
        assert _sql_order(connection, APPLICATION_ORDER, descending=True) == ["E", "C", "D", "A", "B"]
        sequences = application_sequences(connection)
    rows = [{"id": i, "created_at": c} for i, c, _ in reversed(ROWS)]
    assert [row["id"] for row in APPLICATION_ORDER.sorted(rows, sequences)] == ["B", "A", "D", "C", "E"]


def test_occurrence_time_stays_first():
    # A sequence never moves an attempt across seconds: D was applied after A and B but sorts after them by time
    # alone, and an earlier second always sorts first however late it was applied.
    with closing(_database()) as connection:
        connection.execute("INSERT INTO practice_attempts VALUES ('Z', '2026-10-12T08:59:59Z')")
        connection.execute("INSERT INTO attempt_application_order VALUES (99, 'Z', 'applied', 'mvp-0.65', ?)", (T1,))
        assert _sql_order(connection, APPLICATION_ORDER)[0] == "Z"


@pytest.mark.parametrize("order", [LEGACY_ORDER, APPLICATION_ORDER], ids=["legacy", "application"])
def test_the_sql_and_python_boundaries_agree_on_every_pair(order):
    with closing(_database()) as connection:
        sequences = application_sequences(connection)
        for (bound_id, bound_created, _), (row_id, row_created, _) in itertools.product(ROWS, ROWS):
            in_sql = row_id in _sql_before(connection, order, (bound_created, bound_id))
            in_python = order.within(row_created, row_id, (bound_created, bound_id), sequences, inclusive=False)
            assert in_sql == in_python, (order.policy, bound_id, row_id)
            through = order.within(row_created, row_id, (bound_created, bound_id), sequences, inclusive=True)
            assert through == (in_python or row_id == bound_id)
        # And the boundary is the order's own prefix.
        listed = _sql_order(connection, order)
        for index, bound_id in enumerate(listed):
            created = dict((i, c) for i, c, _ in ROWS)[bound_id]
            assert _sql_before(connection, order, (created, bound_id)) == set(listed[:index])


def test_the_legacy_boundary_is_the_predecessor_expression_on_every_pair():
    with closing(_database()) as connection:
        for (bound_id, bound_created, _) in ROWS:
            base = {row[0] for row in connection.execute(
                "SELECT id FROM practice_attempts WHERE (created_at < ? OR (created_at = ? AND id < ?))",
                (bound_created, bound_created, bound_id))}
            assert _sql_before(connection, LEGACY_ORDER, (bound_created, bound_id)) == base
    # The Python form is the canonical projection's old predicate: (str(created_at or ""), str(id or "")).
    assert LEGACY_ORDER.within(None, None, ("", "A"), {}, inclusive=False)
    assert LEGACY_ORDER.within(T0, "A", (T0, "A"), {"A": 9}, inclusive=True)
    assert not LEGACY_ORDER.within(T0, "B", (T0, "A"), {"B": 1, "A": 2}, inclusive=False)


def test_a_bound_without_a_row_is_keyed_as_its_rows_are():
    # An unbound bound (C) sorts after every bound row of its second: D is before it, E (also unbound) after.
    with closing(_database()) as connection:
        assert _sql_before(connection, APPLICATION_ORDER, (T1, "C")) == {"A", "B", "D"}
        assert _sql_before(connection, APPLICATION_ORDER, (T1, "E")) == {"A", "B", "C", "D"}
    assert APPLICATION_ORDER.key(T1, "C", {}) == (T1, UNBOUND_SEQUENCE, "C")


def test_a_reservation_is_the_next_sequence_and_a_second_one_returns_it():
    with closing(_database()) as connection:
        connection.execute("INSERT INTO practice_attempts VALUES ('F', ?)", (T1,))
        first = reserve_application_sequence(connection, "F", algorithm_version="mvp-0.65", recorded_at=T1)
        again = reserve_application_sequence(connection, "F", algorithm_version="mvp-0.66", recorded_at=T0)
        assert first == again == 4
        assert connection.execute(
            "SELECT basis, algorithm_version, recorded_at FROM attempt_application_order WHERE attempt_id = 'F'"
        ).fetchone() == (BASIS_APPLIED, "mvp-0.65", T1)


def test_ranking_legacy_attempts_fills_only_the_unbound_in_the_predecessor_order_after_every_sequence():
    with closing(_database()) as connection:
        assert rank_legacy_attempts(connection, algorithm_version="mvp-0.65", recorded_at=T1) == 2
        assert connection.execute(
            "SELECT attempt_id, sequence, basis FROM attempt_application_order WHERE sequence > 3 ORDER BY sequence"
        ).fetchall() == [("C", 4, BASIS_LEGACY_ORDER_UNKNOWN), ("E", 5, BASIS_LEGACY_ORDER_UNKNOWN)]
        assert rank_legacy_attempts(connection, algorithm_version="mvp-0.65", recorded_at=T1) == 0


def test_on_a_ledger_with_no_rows_the_application_order_is_the_legacy_order():
    with closing(_database()) as connection:
        connection.execute("DELETE FROM attempt_application_order")
        assert _sql_order(connection, APPLICATION_ORDER) == _sql_order(connection, LEGACY_ORDER)
        for (bound_id, bound_created, _) in ROWS:
            assert _sql_before(connection, APPLICATION_ORDER, (bound_created, bound_id)) == _sql_before(
                connection, LEGACY_ORDER, (bound_created, bound_id))
