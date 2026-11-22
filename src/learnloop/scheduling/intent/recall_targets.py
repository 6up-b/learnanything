"""Per-intent recall targets at serving time (spec §5.3, Q8).

``due_at`` keeps being written at 0.90 by the attempt path, so replay and the
stored FSRS state are unchanged. The queue reads an **effective due**::

    effective_due = anchor + (due_at - anchor) x ratio(target)
    ratio(target) = (target^(1/-w20) - 1) / (0.9^(1/-w20) - 1)

with ``w20`` the decay weight in use. FSRS intervals are proportional to
stability (``scheduling/fsrs.interval_for_retention``), so the ratio needs no
stability. It scales whatever interval ``due_at`` stores: below mvp-0.46 (or
with ``scheduler.surprise.remove_interval_factor`` off) that interval carries
the surprise factor, and from mvp-0.46 it is ``interval_for_retention(S)``
alone (router objective RO1, spec_router_objective_v1 §5.1).

**The anchor** is the review that produced ``due_at``: the ``created_at`` of
the item's latest attempt that fed FSRS, i.e. one ``classify_attempt_activity``
marks ``eligible_for_fsrs`` from the row's attempt type, ``primed`` and
``hints_used`` (the attempt path's own decision before it writes ``due_at``).
It is never ``last_attempt_at``: a primed retry or a diagnostic administration
between two reviews advances ``last_attempt_at`` but keeps ``due_at``. Nor is
it an attempt whose grade is held for review now (``held_grades``: the
attempt path leaves FSRS state exactly as it was for a held grade, until a
regrade or an adjudication assesses it; Codex review F4).

Fallbacks (counted by ``learnloop plan report``): no item state or a null
``due_at`` has no effective due (not due-classified, as today); no qualifying
attempt, or an anchor not before ``due_at``, serves ``due_at`` unscaled. At
0.90 the ratio is exactly 1, so uncommitted items are served exactly as today
whatever the anchor (the function returns ``due_at`` itself).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc
from learnloop.diagnosis.causal_activity_policy import classify_attempt_activity
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.scheduling.intent.resolution import Resolution, load_snapshots

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


def anchors_from_attempts(
    rows: Iterable[Mapping[str, Any]], *, held: frozenset[str] = frozenset()
) -> dict[str, tuple[str, str]]:
    """``{item id: (anchor created_at, attempt id)}``: the latest attempt per
    item that wrote FSRS state (eligible, and not ``held`` for review).
    ``rows`` in any order."""

    anchors: dict[str, tuple[str, str]] = {}
    for row in rows:
        if not fsrs_eligible(row) or str(row["id"]) in held:
            continue
        item_id = str(row["practice_item_id"])
        key = (str(row["created_at"]), str(row["id"]))
        current = anchors.get(item_id)
        if current is None or key > current:
            anchors[item_id] = key
    return anchors


def load_anchors(connection: Any) -> dict[str, tuple[str, str]]:
    from learnloop.db.stores import intent_reads as reads
    from learnloop.held_grades import held_for_review_attempts

    rows = reads.attempts_for_anchor(connection)
    eligible = [str(row["id"]) for row in rows if fsrs_eligible(row)]
    held = held_for_review_attempts(connection, eligible) if eligible else frozenset()
    return anchors_from_attempts(rows, held=frozenset(held))


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


def item_effective_due(
    *,
    target: float,
    due_at: str | None,
    anchor_at: Callable[[], str | None],
    weights: tuple[float, ...],
    has_state: bool,
) -> EffectiveDue:
    """One item's effective due as the plan and the queue read it: the stored ``due_at`` at the 0.90 target (no
    anchor read), else :func:`effective_due`. ``anchor_at`` is called only when the scaling needs it."""

    if target == 0.90:
        parsed = parse_utc(due_at)
        return EffectiveDue(parsed, None if parsed is not None else (FALLBACK_NO_STATE if not has_state else FALLBACK_NO_DUE))
    return effective_due(
        due_at=due_at,
        anchor_at=anchor_at() if due_at is not None else None,
        target=target,
        weights=weights,
        has_state=has_state,
    )


def ordinary_due_reader(vault: Any, repository: Any) -> Callable[[str, Any], datetime | None]:
    """``read(item_id, state)``: one item's effective due as ``IntentServing.effective`` reads it, or None when it
    has no review date, for a reader outside the queue build.

    Building an ``IntentServing`` view imports the build (its checks reach the scheduler), which a diagnosis-side
    caller may not do. This resolves the same inputs (the covering commitments' recall target, the fitted FSRS
    weights, the anchor review) and computes through :func:`item_effective_due`. It leaves out only the build's fold
    of answered "Check once" commitments to ``satisfied``, which moves a commitment's disposition, never the recall
    target an item resolves to."""

    with repository.connection() as connection:
        snapshots = load_snapshots(connection)
    resolution = Resolution(
        [snapshot for snapshot in snapshots if not snapshot.retired and snapshot.covers_items],
        dict(vault.config.intent.recall_targets),
    )
    weights = tuple(resolve_fsrs_weights(repository))
    anchors: dict[str, tuple[str, str]] | None = None

    def anchor(item_id: str) -> str | None:
        nonlocal anchors
        if anchors is None:
            with repository.connection() as connection:
                anchors = load_anchors(connection)
        found = anchors.get(item_id)
        return found[0] if found is not None else None

    def read(item_id: str, state: Any) -> datetime | None:
        item = vault.practice_items.get(item_id)
        learning_object_id = getattr(item, "learning_object_id", None) if item is not None else None
        target = resolution.for_item(item_id, str(learning_object_id) if learning_object_id else None).recall_target
        return item_effective_due(
            target=target,
            due_at=getattr(state, "due_at", None) if state is not None else None,
            anchor_at=lambda: anchor(item_id),
            weights=weights,
            has_state=state is not None,
        ).due

    return read


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
    "item_effective_due",
    "load_anchors",
    "ordinary_due_reader",
    "ratio",
]
