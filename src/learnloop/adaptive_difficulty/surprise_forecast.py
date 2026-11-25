"""What an answer's surprise is scored against, from the difficulty label's retirement on
(``docs/reviews/algorithm-mvp-0.71.md``).

Adaptive difficulty's forecast made before the answer, in this order:

1. **the serve-time receipt** of the answer's plan presentation (the subject view's ``ad_threshold@subject``, or
   ``ad_threshold_repeat@subject`` for a repeat), when the answer binds that presentation (the attempt door's own
   rule: the presentation exists, is the item's and no other answer took it), the receipt is ``ok``, has a
   probability and read nothing after the serve;
2. else **the grade-time receipt** (``adaptive_difficulty.grade_forecast``), which the grade records for every
   answer: live, the one computed just before this grade's write; on replay and on a regrade, the one recorded then;
3. else none: surprise reads mastery's own prediction, as it did, and its row says so.

Replay reads receipts and never AD's state, so a rebuild reproduces the live row whatever AD has become; an answer
graded before the tag has no grade-time receipt and falls back to mastery, marked. AD's own module, called by the
grade (``attempts.attempts``): the grade reads AD's recorded forecast, and AD never reads the surprise (its guard
refuses ``attempt_surprise``, an unclassified table, inside its operations). This runs outside AD's operations and
reads only receipts.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from learnloop.adaptive_difficulty.grade_forecast import receipt_id, safe_grade_receipt
from learnloop.adaptive_difficulty.grade_forecast import receipt_key as grade_receipt_key
from learnloop.algorithm_versions import label_retired
from learnloop.clock import utc_now_iso
from learnloop.db.stores import forecast_receipts as receipts
from learnloop.db.stores.plan_presentations import bindable_presentation, presentation_by_id
from learnloop.scheduling.forecast_receipts import (
    ITEM_UNASSISTED_SUCCESS,
    ITEM_UNASSISTED_SUCCESS_AT_GRADE,
    record_receipts,
    valid_for_serve,
)

SERVE_RECEIPT = "serve_receipt"
GRADE_RECEIPT = "grade_receipt"
MASTERY = "mastery"
#: The serve-time forecasters surprise reads: the subject view, the view serving reads.
SERVE_FORECASTERS = ("ad_threshold@subject", "ad_threshold_repeat@subject")


@dataclass(frozen=True)
class SurpriseForecast:
    """AD's ``p̄`` (an unassisted success) for the answer, before it, and where it was read."""

    p: float
    source: str
    receipt_key: str
    forecaster: str


def _usable(row: dict[str, Any] | None, practice_item_id: str) -> bool:
    return (row is not None and row.get("status") == "ok" and row.get("p") is not None
            and str(row.get("practice_item_id") or practice_item_id) == str(practice_item_id))


def with_grade_forecast(vault: Any, repository: Any, attempt: Any, *, clock: Any = None) -> Any:
    """A live answer from the label's retirement on, with adaptive difficulty's forecast of it
    (``ApplyAttemptInput.grade_forecast``), computed read-only before the grade's write transaction, so it sees
    exactly what was committed before the answer, which is not yet written. Replay and a regrade (``replace_existing``)
    compute none: they read the one recorded then. The forecast records the events it read
    (``events_fingerprint``): another writer committing between this read and the grade's write does not change it."""

    if attempt.replace_existing or not label_retired(vault.config.algorithms.algorithm_version):
        return attempt
    return replace(attempt, grade_forecast=safe_grade_receipt(
        vault, repository, practice_item_id=attempt.draft.practice_item_id, attempt_id=attempt.attempt_id,
        at=utc_now_iso(clock)))


def record_grade_forecast(vault: Any, repository: Any, receipt: Any) -> None:
    """Append the live forecast in the grade's transaction, before the grade is computed, so the grade scores against
    the stored row exactly as a replay will (a savepoint: a failed receipt rolls back alone, and the grade then reads
    none and records mastery's prediction as its source). Its id is a function of its attempt, so the grade's other ids
    are unchanged; it carries the vault's tag as every receipt writer does."""

    if receipt is None:
        return
    attempt_id = str(receipt.columns["source_attempt_id"])
    record_receipts(repository, [receipt], vault=vault, created_at=receipt.inputs_as_of,
                    new_id=lambda: receipt_id(attempt_id))


def read_surprise_forecast(vault: Any, repository: Any, draft: Any, *, attempt_id: str) -> SurpriseForecast | None:
    """The forecast this answer's surprise is scored against, or None (mastery's own prediction). Below the label's
    retirement always None: the predecessor's surprise exactly. It reads only stored receipts, live, on a regrade and on
    replay alike."""

    if not label_retired(vault.config.algorithms.algorithm_version):
        return None
    practice_item_id, plan_presentation_id = draft.practice_item_id, draft.plan_presentation_id
    with repository.connection() as connection:
        bound, _why = bindable_presentation(connection, plan_presentation_id, practice_item_id=practice_item_id,
                                            attempt_id=attempt_id)
        if bound is not None:
            served_at = str((presentation_by_id(connection, bound) or {}).get("served_at") or "")
            for row in receipts.presentation_forecasts(connection, bound, kind=ITEM_UNASSISTED_SUCCESS,
                                                       forecasters=SERVE_FORECASTERS):
                if _usable(row, practice_item_id) and valid_for_serve(row, served_at):
                    return SurpriseForecast(float(row["p"]), SERVE_RECEIPT, str(row["receipt_key"]),
                                            str(row["forecaster"]))
        row = receipts.attempt_forecast(connection, attempt_id, kind=ITEM_UNASSISTED_SUCCESS_AT_GRADE,
                                        receipt_key=grade_receipt_key(attempt_id))
    if _usable(row, practice_item_id):
        return SurpriseForecast(float(row["p"]), GRADE_RECEIPT, str(row["receipt_key"]), str(row["forecaster"]))
    return None


__all__ = ["GRADE_RECEIPT", "MASTERY", "SERVE_FORECASTERS", "SERVE_RECEIPT", "SurpriseForecast",
           "read_surprise_forecast", "record_grade_forecast", "with_grade_forecast"]
