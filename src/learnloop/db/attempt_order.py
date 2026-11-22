"""The order the attempt ledger folds in, and the boundaries of its prefixes.

Live recording applies resolved grades in the order their write transactions commit. An attempt's id is minted
when its grading starts and its ``created_at`` (whole seconds) when its grade is applied, so two grades of one
learning object applied within one second can carry ids in the opposite order from their application. A reader
that orders the ledger by ``(created_at, id)`` then folds those two in another order than live applied them, and
replay rebuilds other state than live left.

Two policies, chosen by the vault's tag (:func:`attempt_order_for`):

* :data:`LEGACY_ORDER`, below ``mvp-0.65``: ``(created_at, id)``, the predecessor's order exactly.
* :data:`APPLICATION_ORDER`, from ``mvp-0.65``: ``(created_at, sequence, id)``, where ``sequence`` is the attempt's
  row in ``attempt_application_order``: reserved by ``apply_attempt`` inside its own write transaction, so it is the
  order the grades were applied in, or ranked by the upgrade in the predecessor's order for attempts applied before
  it (``legacy_order_unknown``: what really happened was never recorded). Occurrence time stays the primary key; the
  sequence only breaks ties inside one ``created_at``. An attempt with no row sorts after every attempt of its second
  that has one, then by id (:data:`UNBOUND_SEQUENCE`), so a ledger without rows orders exactly as the predecessor.

A position is the pair ``(created_at, attempt id)`` replay already passes; its sequence is looked up (in SQL from
the table, in Python from the loaded map), so a bound and the rows it bounds are always keyed alike.

The diagnoser's history (``history_v1``, ``corrected_before``), adaptive difficulty's attempt/claim/opportunity
precedence and the grading epochs keep their own orders; nothing here changes them.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, TypeVar

#: The table that records each attempt's application sequence (migration 261).
APPLICATION_ORDER_TABLE = "attempt_application_order"
#: ``basis`` of a sequence ``apply_attempt`` reserved: the order the attempt was applied in.
BASIS_APPLIED = "applied"
#: ``basis`` of a sequence the upgrade ranked in the predecessor's ``(created_at, id)`` order.
BASIS_LEGACY_ORDER_UNKNOWN = "legacy_order_unknown"

#: Where an attempt with no row sorts among the attempts of its second: after every attempt that has one.
UNBOUND_SEQUENCE = (1 << 63) - 1

#: ``(created_at, attempt id)``: an attempt's place in the ledger, as replay passes it.
Position = tuple[str, str]

_Row = TypeVar("_Row")


@dataclass(frozen=True)
class AttemptOrder:
    """One policy for ordering the attempt ledger, with its SQL and Python forms.

    Every form agrees with every other: a row is before a bound in SQL exactly when it is in Python, and the SQL
    ``ORDER BY`` sorts as :meth:`sorted` does (``tests/test_attempt_order.py``)."""

    policy: str

    @property
    def by_sequence(self) -> bool:
        return self.policy == APPLICATION_POLICY

    # -- the Python form ------------------------------------------------------------------------------------

    def key(self, created_at: Any, attempt_id: Any, sequences: Mapping[str, int]) -> tuple:
        """The sort key of one attempt; ``sequences`` maps attempt ids to their sequence (ignored by the legacy
        policy)."""

        if not self.by_sequence:
            return (created_at, attempt_id)
        return (created_at, sequences.get(str(attempt_id), UNBOUND_SEQUENCE), attempt_id)

    def within(
        self, created_at: Any, attempt_id: Any, bound: Position, sequences: Mapping[str, int], *, inclusive: bool
    ) -> bool:
        """Whether the attempt lies before ``bound`` (or, ``inclusive``, at it). A missing time or id reads as
        ``""``, as the canonical projection's legacy predicate read it."""

        position = self.key(str(created_at or ""), str(attempt_id or ""), sequences)
        limit = self.key(str(bound[0] or ""), str(bound[1] or ""), sequences)
        return position <= limit if inclusive else position < limit

    def sorted(
        self,
        rows: Iterable[_Row],
        sequences: Mapping[str, int],
        *,
        created_at: str = "created_at",
        attempt_id: str = "id",
    ) -> list[_Row]:
        """``rows`` (mappings) oldest first. The legacy policy returns them as given: its readers already ordered
        them by ``(created_at, id)`` in SQL, and re-sorting would only risk comparing a stored ``NULL``."""

        listed = list(rows)
        if not self.by_sequence:
            return listed
        return sorted(listed, key=lambda row: self.key(row[created_at], row[attempt_id], sequences))  # type: ignore[index]

    # -- the SQL form ---------------------------------------------------------------------------------------

    def sequence_sql(self, attempt_id: str = "practice_attempts.id") -> str:
        """The sequence of the attempt whose id column is ``attempt_id`` (qualify it where the query aliases the
        table), :data:`UNBOUND_SEQUENCE` when it has no row. A correlated scalar subquery, so ``SELECT *`` keeps
        exactly the attempt's columns."""

        return (
            f"COALESCE((SELECT application_order.sequence FROM {APPLICATION_ORDER_TABLE} AS application_order "
            f"WHERE application_order.attempt_id = {attempt_id}), {UNBOUND_SEQUENCE})"
        )

    def order_sql(
        self, *, created_at: str = "created_at", attempt_id: str = "practice_attempts.id", descending: bool = False
    ) -> str:
        """The ``ORDER BY`` terms, oldest first (or newest first with ``descending``)."""

        direction = " DESC" if descending else " ASC"
        if not self.by_sequence:
            return f"{created_at}{direction}, {attempt_id}{direction}"
        return f"{created_at}{direction}, {self.sequence_sql(attempt_id)}{direction}, {attempt_id}{direction}"

    def before_sql(
        self, bound: Position, *, created_at: str = "created_at", attempt_id: str = "practice_attempts.id"
    ) -> tuple[str, tuple[Any, ...]]:
        """``(predicate, parameters)``: the attempts strictly before ``bound`` in this order."""

        bound_created, bound_id = bound
        if not self.by_sequence:
            return f"({created_at} < ? OR ({created_at} = ? AND {attempt_id} < ?))", (
                bound_created, bound_created, bound_id)
        row_sequence = self.sequence_sql(attempt_id)
        bound_sequence = (
            f"COALESCE((SELECT bound_order.sequence FROM {APPLICATION_ORDER_TABLE} AS bound_order "
            f"WHERE bound_order.attempt_id = ?), {UNBOUND_SEQUENCE})"
        )
        return (
            f"({created_at} < ? OR ({created_at} = ? AND ({row_sequence} < {bound_sequence} "
            f"OR ({row_sequence} = {bound_sequence} AND {attempt_id} < ?))))",
            (bound_created, bound_created, bound_id, bound_id, bound_id),
        )


LEGACY_POLICY = "created_at_id"
APPLICATION_POLICY = "created_at_application_sequence"

#: Below ``mvp-0.65``: ``(created_at, id)``.
LEGACY_ORDER = AttemptOrder(LEGACY_POLICY)
#: From ``mvp-0.65``: ``(created_at, application sequence, id)``.
APPLICATION_ORDER = AttemptOrder(APPLICATION_POLICY)


# -- the table ----------------------------------------------------------------------------------------------


def application_sequences(connection: Any) -> dict[str, int]:
    """Every attempt's sequence, by attempt id (the Python form's map)."""

    return {
        str(row[0]): int(row[1])
        for row in connection.execute(f"SELECT attempt_id, sequence FROM {APPLICATION_ORDER_TABLE}")
    }


def reserve_application_sequence(
    connection: Any, attempt_id: str, *, algorithm_version: str, recorded_at: str
) -> int:
    """The attempt's sequence: the next one, reserved now, or the one it already has.

    Called inside the attempt's own write transaction (``BEGIN IMMEDIATE``), before anything is computed, so the
    sequence is the order the write lock admitted the applications in; a rollback takes the reservation with it."""

    connection.execute(
        f"INSERT INTO {APPLICATION_ORDER_TABLE}(attempt_id, basis, algorithm_version, recorded_at) "
        "VALUES (?, ?, ?, ?) ON CONFLICT(attempt_id) DO NOTHING",
        (attempt_id, BASIS_APPLIED, algorithm_version, recorded_at),
    )
    return int(
        connection.execute(
            f"SELECT sequence FROM {APPLICATION_ORDER_TABLE} WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()[0]
    )


def rank_legacy_attempts(connection: Any, *, algorithm_version: str, recorded_at: str) -> int:
    """Give every attempt without a sequence one, in the predecessor's ``(created_at, id)`` order, after every
    sequence that exists; how many were ranked. Their basis says the order is not known, only kept."""

    attempt_ids = [
        str(row[0])
        for row in connection.execute(
            f"SELECT id FROM practice_attempts AS attempt WHERE NOT EXISTS (SELECT 1 FROM {APPLICATION_ORDER_TABLE} "
            "AS application_order WHERE application_order.attempt_id = attempt.id) ORDER BY created_at, id"
        )
    ]
    connection.executemany(
        f"INSERT INTO {APPLICATION_ORDER_TABLE}(attempt_id, basis, algorithm_version, recorded_at) VALUES (?, ?, ?, ?)",
        [(attempt_id, BASIS_LEGACY_ORDER_UNKNOWN, algorithm_version, recorded_at) for attempt_id in attempt_ids],
    )
    return len(attempt_ids)


__all__ = [
    "APPLICATION_ORDER",
    "APPLICATION_ORDER_TABLE",
    "APPLICATION_POLICY",
    "AttemptOrder",
    "BASIS_APPLIED",
    "BASIS_LEGACY_ORDER_UNKNOWN",
    "LEGACY_ORDER",
    "LEGACY_POLICY",
    "Position",
    "UNBOUND_SEQUENCE",
    "application_sequences",
    "rank_legacy_attempts",
    "reserve_application_sequence",
]
