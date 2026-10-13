"""THE held-grade predicate over the ledger (held-grade-evidence).

A proof grade the route check held for review (mvp-0.17, re-review F9:
nothing assessed and nothing validated) is the grader's own, provisional
score. It is no evidence anywhere: no outcome, no FSRS review, no failure, no
success, no label, no observation. Whether an attempt is held is decided once,
by ``outcome_contract.grade_is_held``:

    held = the attempt's LATEST blind grade record holds it
           (``outcome_contract.grade_held_for_review``)
           AND no criterion of its current (non-superseded) grading evidence
               is assessed (a criterion any live row marks unassessed is not,
               exactly as the attempt step reads the criterion vector).

A regrade that validates the route writes a record without the hold; an owner
adjudication writes assessed evidence over it (Ruling A's evidence revision):
either releases it, here and on the next replay.

This module is the ledger's evaluation of that predicate, for every reader of
a persisted attempt; the attempt step evaluates the same predicate in flight
(``attempts._compute_resolved_grade_application``), because the live door
writes the blind record after the step. It is a leaf (it reads the database
through the caller's connection or repository and imports only
``outcome_contract``), so learner, placement and scheduling code read it
without an edge into ``substrate``; ``substrate.canonical_projection``
re-exports it where the merge composed it. The readers are enumerated in
``docs/reviews/held-grade-evidence.md``.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from learnloop.outcome_contract import (
    HELD_ROW_KEY,
    grade_held_for_review,
    grade_is_held,
    unassessed_evidence_row,
)

#: A persisted blind record whose route check held the grade carries this
#: (compact JSON, the ``blind_grade_records`` store): a cheap prefilter only,
#: the decoded record decides.
_HELD_RECORD_MARK = '"held_for_review":true'


def held_for_review_attempts(connection: Any, attempt_ids: Iterable[str] | None = None) -> frozenset[str]:
    """The attempts (of ``attempt_ids``; ``None`` reads every blind-graded
    one) whose grade is held for review NOW, on ``connection``.

    A database without blind records (a pre-170 copy) holds nothing.
    """

    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'blind_grade_records'"
    ).fetchone() is None:
        return frozenset()
    if attempt_ids is None:
        chunks: list[list[str] | None] = [None]
    else:
        ids = sorted({str(value) for value in attempt_ids if value})
        chunks = [ids[start : start + 500] for start in range(0, len(ids), 500)]
    record_held: set[str] = set()
    for chunk in chunks:
        if chunk is not None and not chunk:
            continue
        where = "" if chunk is None else f"b.attempt_id IN ({','.join('?' for _ in chunk)}) AND "
        # The latest record per attempt (its index's order), prefiltered on
        # the hold's mark: a later record without it releases the attempt.
        for attempt_id, record_json in connection.execute(
            "SELECT b.attempt_id, b.record_json FROM blind_grade_records b "
            f"WHERE {where}instr(b.record_json, ?) > 0 "
            "AND NOT EXISTS (SELECT 1 FROM blind_grade_records n WHERE n.attempt_id = b.attempt_id "
            "AND (n.created_at > b.created_at OR (n.created_at = b.created_at AND n.id > b.id)))",
            (*(chunk or ()), _HELD_RECORD_MARK),
        ):
            try:
                record = json.loads(record_json) if isinstance(record_json, str) else (record_json or {})
            except ValueError:
                continue
            if isinstance(record, dict) and grade_held_for_review(record.get("grading_support")):
                record_held.add(str(attempt_id))
    if not record_held:
        return frozenset()
    criteria: dict[str, set[str]] = {}
    unassessed: dict[str, set[str]] = {}
    ids = sorted(record_held)
    for start in range(0, len(ids), 500):
        chunk = ids[start : start + 500]
        for attempt_id, criterion_id, attribution in connection.execute(
            "SELECT attempt_id, criterion_id, attribution_json FROM grading_evidence "
            f"WHERE superseded_at IS NULL AND attempt_id IN ({','.join('?' for _ in chunk)})",
            chunk,
        ):
            criteria.setdefault(str(attempt_id), set()).add(str(criterion_id))
            if unassessed_evidence_row(attribution):
                unassessed.setdefault(str(attempt_id), set()).add(str(criterion_id))
    # The evidence half exactly as the attempt step reads it: replay builds
    # the criterion vector from the same live rows and leaves out every
    # criterion an unassessed row names. A criterion is assessed when a live
    # row grades it and no live row marks it unassessed, so the two
    # evaluations agree whatever tiers stay live beside a hold (review F1).
    return frozenset(
        attempt_id
        for attempt_id in record_held
        if grade_is_held(
            record_held=True,
            anything_assessed=bool(criteria.get(attempt_id, set()) - unassessed.get(attempt_id, set())),
        )
    )


def held_attempt_ids(repository: Any, attempt_ids: Iterable[str] | None = None) -> frozenset[str]:
    """:func:`held_for_review_attempts` through a repository's connection
    (no read at all for an empty id list)."""

    if attempt_ids is not None:
        attempt_ids = [str(value) for value in attempt_ids if value]
        if not attempt_ids:
            return frozenset()
    with repository.connection() as connection:
        return held_for_review_attempts(connection, attempt_ids)


def attempt_grade_held(repository: Any, attempt_id: str | None) -> bool:
    """Is this one persisted attempt's grade held for review now?"""

    return bool(attempt_id) and str(attempt_id) in held_attempt_ids(repository, (str(attempt_id),))


def mark_held_attempts(
    repository: Any, rows: Iterable[Mapping[str, Any]], *, key: str = "id"
) -> list[dict[str, Any]]:
    """``rows`` (copies) with :data:`HELD_ROW_KEY` set on each attempt the
    predicate holds, in one query. Readers that keep held rows for exposure or
    time, and must never read their score, use it."""

    rows = [dict(row) for row in rows]
    held = held_attempt_ids(repository, (row.get(key) for row in rows)) if rows else frozenset()
    for row in rows:
        if row.get(key) in held:
            row[HELD_ROW_KEY] = True
    return rows


__all__ = [
    "HELD_ROW_KEY",
    "attempt_grade_held",
    "held_attempt_ids",
    "held_for_review_attempts",
    "mark_held_attempts",
]
