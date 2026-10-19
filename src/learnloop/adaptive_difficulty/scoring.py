"""The forecast-score replayer (spec_adaptive_difficulty_v1 §8.3; DERIVED ``item_forecast_scores``).

Each ``item_unassisted_success`` receipt is joined to its bound attempt through
the exact chain ``plan_presentations`` -> ``practice_attempts.plan_presentation_id``
(an item-scoped receipt to its revision's first bound presentation). The outcome
is §5.3's event, read exactly as the update reads it: any help, or a reveal
during the presentation, makes it 0; a presentation exposed before it was
served is not scored; a pending presentation (or a skipped or abandoned one) is
right-censored, never a failure. A receipt whose inputs postdate the serve is
invalid for scoring (§8.1).

Splits: field's first-attempt split (the first attempt on a never-seen LO, the
primary score, D17) and the first surface in a never-seen cell.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from learnloop.db.stores import ad_serving as store
from learnloop.db.stores import forecast_receipts as receipt_store

from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty import replay as RP

SCORE_VERSION = "ad_forecast_scores_v1"
CLIP = (0.005, 0.995)


def log_loss(p: float, y: float) -> float:
    q = min(max(float(p), CLIP[0]), CLIP[1])
    return -(y * math.log(q) + (1.0 - y) * math.log(1.0 - q))


def brier(p: float, y: float) -> float:
    return (float(p) - float(y)) ** 2


def score_rows(connection: Any, vault: Any, repository: Any) -> list[dict[str, Any]]:
    """The scores of every item forecast receipt (pure reads; zero model calls)."""

    from learnloop.scheduling.forecast_receipts import valid_for_serve

    events = RP.load_events(connection, vault, repository)
    by_presentation = {e.plan_presentation_id: e for e in events.attempts if e.plan_presentation_id}
    served = {str(pid): str(at) for pid, at in connection.execute("SELECT id, served_at FROM plan_presentations")}
    first_presentation: dict[str, str] = {}
    if store.has_table(connection, "item_serve_inputs"):
        for content_hash, pid in connection.execute(
                "SELECT content_hash, plan_presentation_id FROM item_serve_inputs WHERE plan_presentation_id IS NOT "
                "NULL ORDER BY served_at, id"):
            first_presentation.setdefault(str(content_hash), str(pid))
    pre_exposed = {str(pid) for (pid,) in connection.execute(
        "SELECT plan_presentation_id FROM item_serve_inputs WHERE pre_exposed = 1 AND plan_presentation_id IS NOT NULL")}\
        if store.has_table(connection, "item_serve_inputs") else set()
    seen_los: set[str] = set()
    seen_cells: set[tuple[str, str]] = set()
    first_lo: dict[str, bool] = {}
    first_cell: dict[str, bool] = {}
    for event in events.attempts:
        if not event.eligible or event.spec is None:
            continue
        first_lo[event.attempt_id] = event.learning_object_id not in seen_los
        cell = event.spec.cell()
        first_cell[event.attempt_id] = cell not in seen_cells
        seen_los.add(event.learning_object_id)
        seen_cells.add(cell)
    rows: list[dict[str, Any]] = []
    for receipt in receipt_store.list_receipts(connection, kind="item_unassisted_success"):
        presentation = receipt.get("plan_presentation_id")
        if receipt.get("scope") == "item":
            presentation = first_presentation.get(str(receipt.get("item_content_hash") or ""))
        row: dict[str, Any] = {"receipt_id": str(receipt["id"]), "forecaster": str(receipt["forecaster"]),
                               "practice_item_id": receipt.get("practice_item_id"),
                               "plan_presentation_id": presentation, "p": receipt.get("p"), "detail": {}}
        if receipt.get("status") not in (None, "ok") or receipt.get("p") is None:
            rows.append({**row, "status": "invalid", "detail": {"why": f"status:{receipt.get('status')}"}})
            continue
        if presentation is None or presentation not in served:
            rows.append({**row, "status": "pending", "detail": {"why": "no_bound_presentation"}})
            continue
        if not valid_for_serve(receipt, served[presentation]):
            rows.append({**row, "status": "invalid", "detail": {"why": "inputs_after_serve"}})
            continue
        if presentation in pre_exposed:
            rows.append({**row, "status": "pre_exposed"})
            continue
        attempt = by_presentation.get(presentation)
        if attempt is None:
            rows.append({**row, "status": "pending", "detail": {"why": "no_attempt"}})
            continue
        if not attempt.eligible:
            rows.append({**row, "attempt_id": attempt.attempt_id, "status": "excluded",
                         "detail": {"why": attempt.reason}})
            continue
        outcome = O.unassisted_success(attempt.category)
        p = float(receipt["p"])
        rows.append({
            **row, "attempt_id": attempt.attempt_id, "outcome": outcome, "status": "scored",
            "log_loss": round(log_loss(p, outcome), 12), "brier": round(brier(p, outcome), 12),
            "first_attempt_lo": first_lo.get(attempt.attempt_id), "first_surface_cell": first_cell.get(attempt.attempt_id),
            "capability": attempt.spec.capability if attempt.spec else None,
            "detail": {"category": attempt.category, "warmth": round(attempt.warmth, 12)},
        })
    return rows


def rebuild(vault: Any, repository: Any) -> dict[str, Any]:
    """Clear and rebuild ``item_forecast_scores`` (zero model calls)."""

    with repository.atomic():
        connection = repository.connection()
        if not store.has_table(connection, store.SCORES):
            return {"written": 0, "skipped": "schema"}
        rows = score_rows(connection, vault, repository)
        store.clear_derived(connection, (store.SCORES,))
        written = store.write_scores(connection, rows)
    return {"written": written}


__all__ = ["CLIP", "SCORE_VERSION", "brier", "log_loss", "rebuild", "score_rows"]
