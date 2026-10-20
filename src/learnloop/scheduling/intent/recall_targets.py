"""Per-intent recall targets at serving time (spec §5.3, Q8).

``due_at`` keeps being written at 0.90 by the attempt path, so replay and the
stored FSRS state are unchanged. The queue reads an **effective due**::

    effective_due = anchor + (due_at - anchor) x ratio(target)
    ratio(target) = (target^(1/-w20) - 1) / (0.9^(1/-w20) - 1)

with ``w20`` the decay weight in use. FSRS intervals are proportional to
stability (``scheduling/fsrs.interval_for_retention``), so the ratio needs no
stability and keeps the surprise factor already folded into ``due_at``.

**The anchor** is the review that produced ``due_at``: the ``created_at`` of
the item's latest attempt that fed FSRS, i.e. one ``classify_attempt_activity``
marks ``eligible_for_fsrs`` from the row's attempt type, ``primed`` and
``hints_used`` (the attempt path's own decision before it writes ``due_at``).
It is never ``last_attempt_at``: a primed retry or a diagnostic administration
between two reviews advances ``last_attempt_at`` but keeps ``due_at``.

Fallbacks (counted by ``learnloop plan report``): no item state or a null
``due_at`` has no effective due (not due-classified, as today); no qualifying
attempt, or an anchor not before ``due_at``, serves ``due_at`` unscaled. At
0.90 the ratio is exactly 1, so uncommitted items are served exactly as today
whatever the anchor (the function returns ``due_at`` itself).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc
from learnloop.diagnosis.causal_activity_policy import classify_attempt_activity

#: The retention ``due_at`` is written at (``attempts.py``: ``interval_for_retention``'s default).
STORED_RETENTION = 0.9

FALLBACK_NO_STATE = "no_state"
FALLBACK_NO_DUE = "no_due_at"
FALLBACK_NO_ANCHOR = "no_qualifying_attempt"
FALLBACK_ANCHOR_NOT_BEFORE_DUE = "anchor_not_before_due"


def ratio(target: float, weights: tuple[float, ...]) -> float:
    """The interval multiplier for ``target`` against the stored 0.90.

    Exactly 1.0 at 0.90 (the same expression divided by itself)."""

    target = float(target)
    if target == STORED_RETENTION:
        return 1.0
    decay = float(weights[20])
    stored = STORED_RETENTION ** (1 / -decay) - 1
    return (target ** (1 / -decay) - 1) / stored


def fsrs_eligible(row: Mapping[str, Any]) -> bool:
    return bool(
        classify_attempt_activity(
            attempt_type=str(row.get("attempt_type") or ""),
            primed=bool(row.get("primed") or 0),
            hints_used=int(row.get("hints_used") or 0),
        ).eligible_for_fsrs
    )


def anchors_from_attempts(rows: Iterable[Mapping[str, Any]]) -> dict[str, tuple[str, str]]:
    """``{item id: (anchor created_at, attempt id)}``: the latest FSRS-eligible
    attempt per item. ``rows`` in any order."""

    anchors: dict[str, tuple[str, str]] = {}
    for row in rows:
        if not fsrs_eligible(row):
            continue
        item_id = str(row["practice_item_id"])
        key = (str(row["created_at"]), str(row["id"]))
        current = anchors.get(item_id)
        if current is None or key > current:
            anchors[item_id] = key
    return anchors


def load_anchors(connection: Any) -> dict[str, tuple[str, str]]:
    from learnloop.db.stores import intent_reads as reads

    return anchors_from_attempts(reads.attempts_for_anchor(connection))


@dataclass(frozen=True)
class EffectiveDue:
    due: datetime | None
    #: None when scaled (or at 0.90); otherwise which fallback applied.
    fallback: str | None = None
    ratio: float = 1.0


def effective_due(
    *,
    due_at: str | None,
    anchor_at: str | None,
    target: float,
    weights: tuple[float, ...],
    has_state: bool = True,
) -> EffectiveDue:
    """§5.3's effective due for one item."""

    if not has_state:
        return EffectiveDue(None, FALLBACK_NO_STATE)
    due = parse_utc(due_at)
    if due is None:
        return EffectiveDue(None, FALLBACK_NO_DUE)
    multiplier = ratio(target, weights)
    if multiplier == 1.0:
        return EffectiveDue(due)
    anchor = parse_utc(anchor_at)
    if anchor is None:
        return EffectiveDue(due, FALLBACK_NO_ANCHOR)
    if anchor >= due:
        return EffectiveDue(due, FALLBACK_ANCHOR_NOT_BEFORE_DUE)
    return EffectiveDue(anchor + (due - anchor) * multiplier, None, multiplier)


__all__ = [
    "EffectiveDue",
    "FALLBACK_ANCHOR_NOT_BEFORE_DUE",
    "FALLBACK_NO_ANCHOR",
    "FALLBACK_NO_DUE",
    "FALLBACK_NO_STATE",
    "STORED_RETENTION",
    "anchors_from_attempts",
    "effective_due",
    "fsrs_eligible",
    "load_anchors",
    "ratio",
]
