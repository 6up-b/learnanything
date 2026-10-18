"""AD1's serve hook (spec_adaptive_difficulty_v1 §7.5, §8.1, §5.11).

Called by the daily plan's serve (``daily_plan.engine._serve``) inside the
transaction that writes the ``plan_presentations`` row, right after it:

1. the reading-opportunity sweep up to the serve (§5.11: "before its
   forecasts");
2. for a never-attempted item, its frozen serve inputs (§7.5);
3. the in-process forecasts (``mastery_ekf``, ``lo_general+composite``) as
   ``item_unassisted_success`` receipts bound to the presentation (§8.1).

All three run in one savepoint: a failure rolls back AD's writes alone,
logged, and the serve proceeds (logging never breaks serving). Each write is
idempotent per presentation, so a reopened step writes nothing new. With
``forecast_receipts`` (or the master switch) off nothing is read or written.
A protected item (held-out material, an exam reservation: A8) gets no serve
inputs and no forecasts. No model call: the outside forecasters run after the
serve, in the background (:mod:`learnloop.adaptive_difficulty.background`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from learnloop.db.stores import ad_receipts as store
from learnloop.scheduling.forecast_receipts import record_receipts

from learnloop.adaptive_difficulty.forecasters import in_process_receipts
from learnloop.adaptive_difficulty.protection import is_protected
from learnloop.adaptive_difficulty.reading import sweep
from learnloop.adaptive_difficulty.serve_inputs import build_row, never_attempted
from learnloop.adaptive_difficulty.switches import receipts_enabled

LOG = logging.getLogger(__name__)

PLAN_PRESENTATION = "plan_presentation"


@dataclass
class ServeRecord:
    presentation_id: str
    serve_inputs_id: str | None = None
    receipt_ids: list[str] = field(default_factory=list)
    reading_written: int = 0
    skipped: str | None = None


def record_plan_serve(vault: Any, repository: Any, *, presentation_id: str, practice_item_id: str,
                      served_at: str) -> ServeRecord | None:
    """Record AD1's serve-time receipts for one plan presentation, in the caller's transaction."""

    if not receipts_enabled(vault.config):
        return None
    record = ServeRecord(presentation_id=presentation_id)
    try:
        with repository.atomic():
            connection = repository.connection()
            if not store.has_table(connection, store.SERVE_INPUTS):
                record.skipped = "schema"
                return record
            if _recorded(connection, presentation_id):
                # A reopened step: its serve was recorded when it was served.
                record.skipped = "recorded"
                return record
            record.reading_written = sweep(vault, repository, as_of=served_at, sweep_kind="serve",
                                           sweep_ref=presentation_id).written
            item = vault.practice_items.get(practice_item_id)
            if item is None:
                record.skipped = "unknown_item"
                return record
            if is_protected(vault, repository, practice_item_id):
                record.skipped = "protected"
                return record
            if never_attempted(connection, practice_item_id, served_at):
                record.serve_inputs_id = store.insert_serve_inputs(connection, build_row(
                    repository, connection, item, presentation_kind=PLAN_PRESENTATION,
                    presentation_id=presentation_id, served_at=served_at, created_at=served_at,
                ))
            receipts = in_process_receipts(vault, repository, connection, item, presentation_kind=PLAN_PRESENTATION,
                                           presentation_id=presentation_id, served_at=served_at)
            algorithm_version = vault.config.algorithms.algorithm_version
            receipts = [_with_version(receipt, algorithm_version) for receipt in receipts]
            record.receipt_ids = record_receipts(repository, receipts, created_at=served_at)
    except Exception:  # noqa: BLE001 - AD's logging never breaks the serve
        LOG.warning("AD1 serve receipts for presentation %s not recorded", presentation_id, exc_info=True)
        record.skipped = "failed"
    return record


def _recorded(connection: Any, presentation_id: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM forecast_receipts WHERE plan_presentation_id = ? AND kind = 'item_unassisted_success' "
        "AND decision_kind = 'serve' LIMIT 1", (presentation_id,),
    ).fetchone() is not None or connection.execute(
        "SELECT 1 FROM item_serve_inputs WHERE plan_presentation_id = ? LIMIT 1", (presentation_id,),
    ).fetchone() is not None


def _with_version(receipt: Any, algorithm_version: str) -> Any:
    from dataclasses import replace

    return replace(receipt, columns={**dict(receipt.columns), "algorithm_version": algorithm_version})


__all__ = ["PLAN_PRESENTATION", "ServeRecord", "record_plan_serve"]
