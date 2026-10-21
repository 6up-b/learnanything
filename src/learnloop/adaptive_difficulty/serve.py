"""AD1's serve hook (spec_adaptive_difficulty_v1 §7.5, §8.1, §5.11).

Called by the daily plan's serve (``daily_plan.engine._serve``) inside the
transaction that INSERTS the ``plan_presentations`` row, right after it, and
only then (Codex review F3): a reopened step's serve keeps its original
``served_at``, so recording it then would freeze today's item and incumbent
under the original presentation's time. A presentation served while AD was
off, or whose first recording failed, keeps no AD record: its inputs are
unavailable, never reconstructed.

1. the reading-opportunity sweep up to the serve (§5.11: "before its
   forecasts");
2. for a never-attempted item, its frozen serve inputs (§7.5);
3. the in-process forecasts (``mastery_ekf``, ``lo_general+composite``) as
   ``item_unassisted_success`` receipts bound to the presentation (§8.1);
4. the outside ``llm_v3`` forecasters' exact request inputs
   (:func:`~learnloop.adaptive_difficulty.outside.freeze_presentation_inputs`).

All four run in one savepoint: a failure rolls back AD's writes alone,
logged, and the serve proceeds (logging never breaks serving). Each write is
idempotent per presentation, so a second call writes nothing new. With
``forecast_receipts`` (or the master switch) off nothing is read or written.
A protected item (held-out material, an exam reservation: A8) gets no serve
inputs and no forecasts. No model call: the outside forecasters run after the
serve, in the background (:mod:`learnloop.adaptive_difficulty.background`).
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import logging
from dataclasses import dataclass, field
from typing import Any

from learnloop.db.stores import ad_receipts as store
from learnloop.scheduling.forecast_receipts import record_receipts

from learnloop.adaptive_difficulty.forecasters import in_process_receipts
from learnloop.adaptive_difficulty.outside import freeze_presentation_inputs
from learnloop.adaptive_difficulty.material_view import current_view, material_view
from learnloop.adaptive_difficulty.reading import sweep
from learnloop.adaptive_difficulty.generation import record_landed_commissions
from learnloop.adaptive_difficulty.serve_inputs import build_row, never_attempted
from learnloop.adaptive_difficulty.serving import frozen_loadings, threshold_receipts
from learnloop.adaptive_difficulty.switches import receipts_enabled

LOG = logging.getLogger(__name__)

PLAN_PRESENTATION = "plan_presentation"


@dataclass
class ServeRecord:
    presentation_id: str
    serve_inputs_id: str | None = None
    receipt_ids: list[str] = field(default_factory=list)
    reading_written: int = 0
    frozen_inputs: str | None = None
    skipped: str | None = None


def _serve_unrecorded(arguments: Any) -> "ServeRecord":
    # The guard refused something in the serve's AD operation: nothing of AD's is kept (the savepoint
    # rolled back what the refusal reached), and the serve proceeds (logging never breaks it).
    return ServeRecord(presentation_id=str(arguments.get("presentation_id")), skipped="failed")


@entry(poisoned=_serve_unrecorded)
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
            # The serve's one material view (A8; fix round 8): every read below goes through it.
            view = material_view(vault, repository)
            record.reading_written = sweep(vault, repository, as_of=served_at, sweep_kind="serve",
                                           sweep_ref=presentation_id, view=view).written
            if view.withheld(practice_item_id):
                record.skipped = "protected"
                return record
            item = view.item(practice_item_id)
            if item is None:
                record.skipped = "unknown_item"
                return record
            if view.covers(item):
                record.skipped = "protected"
                return record
            protected = view.protection
            fresh_item = never_attempted(connection, practice_item_id, served_at, view=view)
            if fresh_item:
                row = build_row(repository, connection, item, presentation_kind=PLAN_PRESENTATION,
                                presentation_id=presentation_id, served_at=served_at, created_at=served_at,
                                view=view)
                # AD2+AD3 (§7.5, §5.10): the revision's loadings in force and the
                # coupling version, from the successor's tag on.
                loadings, coupling_version = frozen_loadings(vault, repository, connection, row["content_hash"],
                                                             served_at, view=view)
                if loadings is not None:
                    row["loadings"], row["coupling_version"] = loadings, coupling_version
                row["protection_epoch"] = view.epoch
                record.serve_inputs_id = store.insert_serve_inputs(connection, row)
            receipts = in_process_receipts(vault, repository, connection, item, presentation_kind=PLAN_PRESENTATION,
                                           presentation_id=presentation_id, served_at=served_at, view=view)
            if fresh_item:
                # AD2+AD3 (§8.2): ad_threshold@subject, @subject_uniform and @lo.
                receipts += threshold_receipts(vault, repository, connection, item,
                                               presentation_kind=PLAN_PRESENTATION, presentation_id=presentation_id,
                                               served_at=served_at, view=view)
                # §7.4: landed commissions' re-forecasts.
                record_landed_commissions(vault, repository, connection, now=served_at, view=view)
            algorithm_version = vault.config.algorithms.algorithm_version
            receipts = [_with_version(receipt, algorithm_version, view.epoch) for receipt in receipts]
            record.receipt_ids = record_receipts(repository, receipts, created_at=served_at)
            # The outside forecasters' exact request inputs, as this serve saw
            # them (Codex review F2): the background job sends these, never
            # a later read of the history or the item.
            record.frozen_inputs = freeze_presentation_inputs(
                vault, connection, item, presentation_id=presentation_id, served_at=served_at, protected=protected,
                view=view)
    except Exception:  # noqa: BLE001 - AD's logging never breaks the serve
        LOG.warning("AD1 serve receipts for presentation %s not recorded", presentation_id, exc_info=True)
        record.skipped = "failed"
    return record


def _recorded(connection: Any, presentation_id: str) -> bool:
    # A record AD may not read counts as written: nothing is recorded over it.
    view = current_view()
    return view.lookup(connection, "forecast_receipts", "plan_presentation_id = ? AND kind = 'item_unassisted_success' "
                       "AND decision_kind = 'serve'", (presentation_id,))[0] != "missing" or view.lookup(
        connection, "item_serve_inputs", "plan_presentation_id = ?", (presentation_id,))[0] != "missing"


def _with_version(receipt: Any, algorithm_version: str, epoch: str | None) -> Any:
    from dataclasses import replace

    # The protection epoch the forecast was computed under (round 2, class 3b): read back only at it.
    return replace(receipt, columns={**dict(receipt.columns), "algorithm_version": algorithm_version},
                   versions={**dict(receipt.versions or {}), "protection_epoch": epoch})


__all__ = ["PLAN_PRESENTATION", "ServeRecord", "record_plan_serve"]
