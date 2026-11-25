"""What an answer's surprise is scored against, from the difficulty label's retirement on
(``docs/reviews/algorithm-mvp-0.71.md``).

From the selected-forecast tag a bound answer uses the recorded AD slot view's first-serve or repeat receipt.
An unverifiable presentation or missing selected forecast leaves surprise on mastery. An unbound answer uses its
own grade-time receipt where one exists. Earlier label-retirement tags prefer the subject view and then the grade
receipt. The surprise row records the source.

Replay reads receipts and never AD's state, so a rebuild reproduces the live row whatever AD has become; an answer
graded before the tag has no grade-time receipt and falls back to mastery, marked. AD's own module, called by the
grade (``attempts.attempts``): the grade reads AD's recorded forecast, and AD never reads the surprise (its guard
refuses ``attempt_surprise``, an unclassified table, inside its operations). This runs outside AD's operations and
reads only receipts.
"""

from __future__ import annotations

import json
from contextlib import closing
from dataclasses import dataclass, replace
from typing import Any

from learnloop.adaptive_difficulty.grade_forecast import receipt_id, safe_grade_receipt
from learnloop.adaptive_difficulty.grade_forecast import receipt_key as grade_receipt_key
from learnloop.algorithm_versions import SELECTED_FORECAST_VERSIONS, label_retired
from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
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
#: Earlier label-retirement tags always read the subject forecaster.
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
    at = utc_now_iso(clock)
    if _revised_after(repository, at):
        return attempt
    kwargs = {}
    if vault.config.algorithms.algorithm_version in SELECTED_FORECAST_VERSIONS:
        draft = attempt.draft
        if draft.assessment_contract_version_id:
            revision = _contract_revision(repository, draft.assessment_contract_version_id)
            if not revision:
                return attempt
            kwargs["answered_revision"] = revision
        else:
            kwargs["answered_item"] = vault.practice_items.get(draft.practice_item_id)
    draft = attempt.draft
    answered = {"plan_presentation_id": draft.plan_presentation_id, "scheduler_candidate_id": draft.scheduler_candidate_id}
    return replace(attempt, grade_forecast=safe_grade_receipt(
        vault, repository, practice_item_id=draft.practice_item_id, attempt_id=attempt.attempt_id, at=at,
        answered=answered, **kwargs))


def _contract_revision(repository: Any, version_id: str) -> str | None:
    stored = repository.fetch_assessment_contract_version(version_id)
    return ((stored or {}).get("contract") or {}).get("forecast_item_revision")


def _revised_after(repository: Any, at: str) -> bool:
    """Whether a grade was recorded or revised after the answer's cutoff ``at``: AD's evidence then holds a grade the
    learner's answer could not have been forecast with (a retrospective import), so the answer gets no forecast."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'raw_grade_events'").fetchone() is None:
            return False
        latest = connection.execute("SELECT MAX(created_at) FROM raw_grade_events").fetchone()[0]
    return latest is not None and str(latest) > at


def record_grade_forecast(vault: Any, repository: Any, receipt: Any) -> None:
    """Append the live forecast in the grade's transaction, before the grade is computed, so the grade scores against
    the stored row exactly as a replay will (a savepoint: a failed receipt rolls back alone, and the grade then reads
    none and records mastery's prediction as its source). Its id is a function of its attempt, so the grade's other ids
    are unchanged; it carries the vault's tag as every receipt writer does. Only the tag is passed, never the vault:
    the diagnosis receipts' switch (``diagnosis.forecast_receipts``) is not adaptive difficulty's (FR3-10)."""

    if receipt is None:
        return
    attempt_id = str(receipt.columns["source_attempt_id"])
    record_receipts(repository, [receipt], created_at=receipt.inputs_as_of, new_id=lambda: receipt_id(attempt_id),
                    algorithm_version=vault.config.algorithms.algorithm_version)


def _serve_forecasts(connection: Any, presentation: dict[str, Any], selected: bool) -> list[dict[str, Any]]:
    presentation_id = presentation["id"]
    names = SERVE_FORECASTERS
    selected_lo = expected = None
    if selected:
        from learnloop.db.stores.ad_serving import selection_by_key

        block, position = presentation["block_id"], presentation["position"]
        item = presentation["practice_item_id"]
        draw = selection_by_key(connection, f"serve:{block}:{position}")
        if draw is None and not _slot_drawn(connection, block, position):
            # No draw at all (the incumbent's slot: every repeat, a slot AD left alone): the subject view's receipt,
            # as before the tag, read from what was stored.
            return receipts.presentation_forecasts(connection, presentation_id, kind=ITEM_UNASSISTED_SUCCESS,
                                                   forecasters=names)
        if (not draw or draw["kind"] != "serve" or draw["block_id"] != block or draw["slot_position"] != position
                or draw["chosen_item_id"] != item or draw["created_at"] > presentation["served_at"] or draw["empty_support"]):
            return []
        if draw["view"] != "subject":
            selected_lo = draw["learning_object_id"]
            if not selected_lo or draw["view"] != f"lo:{selected_lo}":
                return []
            names = ("ad_threshold@lo", "ad_threshold_repeat@lo")
        if draw["support"]:
            expected = next((entry.get("p_bar") for entry in draw["support"] if isinstance(entry, dict) and entry.get("ref") == item), None)
            if expected is None:
                return []
    rows = receipts.presentation_forecasts(connection, presentation_id, kind=ITEM_UNASSISTED_SUCCESS, forecasters=names)
    # Scored.as_dict freezes the probability to twelve decimal places in the draw's support.
    return [row for row in rows if (selected_lo is None or row["learning_object_id"] == selected_lo)
            and (expected is None or (row["p"] is not None and round(row["p"], 12) == expected))]


def _slot_drawn(connection: Any, block: Any, position: Any) -> bool:
    """Whether AD recorded any serve draw for the slot (one that does not verify still leaves mastery)."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ad_selections'").fetchone() is None:
        return False
    return connection.execute("SELECT 1 FROM ad_selections WHERE kind = 'serve' AND block_id = ? AND slot_position = ? "
                              "LIMIT 1", (block, position)).fetchone() is not None


def _receipt_revision(row: dict[str, Any] | None) -> str | None:
    if not row:
        return None
    try:
        target = json.loads(row["versions_json"]).get("snapshot", {}).get("target", {}).get("target") or {}
        revision = next((m["revision"] for m in target.get("members", ())
                         if m["kind"] == "item" and m["id"] == row["practice_item_id"]), None)
        return revision or json.loads(row.get("inputs_json") or "{}").get("item_revision") or row.get("item_content_hash")
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def _serve_input_revision(connection: Any, presentation_id: str) -> str | None:
    row = connection.execute("SELECT content_hash FROM item_serve_inputs WHERE receipt_key = ?",
                             (f"plan_presentation:{presentation_id}",)).fetchone()
    return row[0] if row else None


def _matches_administration(connection: Any, presentation: dict[str, Any], draft: Any, at: str | None) -> bool:
    """Whether the answer may take this presentation: served in no session, in the answer's own, to an answer that
    names no session, or in a session that had ended by the answer's time ``at`` (starting a session ends every other,
    so no answer of its own can still come); the probe administration it was served for; never an inline check.
    Only a presentation still open in another session is left for that session's answer (H3-R7). Ended sessions stay
    ended, so the decision taken live is the one replay takes from the stored times."""

    served_in = presentation["session_id"]
    return ((served_in is None or draft.session_id is None or served_in == draft.session_id
             or _session_ended(connection, served_in, at))
            and presentation["probe_presentation_id"] == draft.probe_presentation_id
            and not (draft.submission_id or "").startswith("inline:"))


def _session_ended(connection: Any, session_id: str, at: str | None) -> bool:
    row = connection.execute("SELECT ended_at FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return bool(row is not None and row[0] and (at is None or str(row[0]) <= at))


def validate_live_binding(vault: Any, repository: Any, attempt: Any, *, at: str | None = None) -> Any:
    """Drop a refused link and its prepared forecast together so replay also finds the marked fallback.

    A link is refused when the presentation is not bindable or was administered to another session, probe or an inline
    check. An answer to its own presentation keeps the link even when the served revision is not the answered one (an
    edit between the serve and the answer): the presentation records what the learner was shown, and protection, the
    plan and the router read it (H3-R24). Its surprise then reads mastery, live and on replay alike, because no serve
    receipt forecast the revision its grade receipt names (``read_surprise_forecast``). ``at`` is the answer's time."""

    draft = attempt.draft
    if (attempt.replace_existing or not draft.plan_presentation_id
            or vault.config.algorithms.algorithm_version not in SELECTED_FORECAST_VERSIONS):
        return attempt
    with repository.connection() as connection:
        bound, _ = bindable_presentation(connection, draft.plan_presentation_id, practice_item_id=draft.practice_item_id,
                                         attempt_id=attempt.attempt_id)
        presentation = presentation_by_id(connection, bound) if bound else None
        if presentation and _matches_administration(connection, presentation, draft, at):
            return attempt
    return replace(attempt, draft=replace(draft, plan_presentation_id=None), grade_forecast=None)


def read_surprise_forecast(vault: Any, repository: Any, draft: Any, *, attempt_id: str,
                           answered_at: str | None = None) -> SurpriseForecast | None:
    """The forecast this answer's surprise is scored against, or None (mastery's own prediction). Below the label's
    retirement always None: the predecessor's surprise exactly. It reads only stored receipts, live, on a regrade and on
    replay alike.

    From the selected-forecast tag the answered revision is the one the answer's grade receipt names, a row stored
    before the grade (live, in its transaction) and read the same way on replay: an answer without one reads mastery on
    both sides (H3-R28). An inline answer whose contract froze no revision reads mastery: its grade receipt may describe
    a later edit."""

    if not label_retired(vault.config.algorithms.algorithm_version):
        return None
    practice_item_id, plan_presentation_id = draft.practice_item_id, draft.plan_presentation_id
    with repository.connection() as connection:
        selected = vault.config.algorithms.algorithm_version in SELECTED_FORECAST_VERSIONS
        grade = receipts.attempt_forecast(connection, attempt_id, kind=ITEM_UNASSISTED_SUCCESS_AT_GRADE,
                                          receipt_key=grade_receipt_key(attempt_id))
        answered_revision = _receipt_revision(grade)
        if selected and (draft.submission_id or "").startswith("inline:") and not (
                draft.assessment_contract_version_id
                and _contract_revision(repository, draft.assessment_contract_version_id)):
            return None
        bound, _why = bindable_presentation(connection, plan_presentation_id, practice_item_id=practice_item_id,
                                            attempt_id=attempt_id)
        if bound is not None:
            presentation = presentation_by_id(connection, bound)
            served_at = presentation["served_at"]
            if selected:
                stored = connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?",
                                            (attempt_id,)).fetchone()
                if not _matches_administration(connection, presentation, draft, stored[0] if stored else answered_at):
                    return None
            input_revision = _serve_input_revision(connection, bound) if selected else None
            for row in _serve_forecasts(connection, presentation, selected):
                if selected:
                    revision = _receipt_revision(row) or input_revision
                    if (not revision or (input_revision and revision != input_revision)
                            or revision != answered_revision):
                        continue
                if _usable(row, practice_item_id) and valid_for_serve(row, served_at):
                    return SurpriseForecast(float(row["p"]), SERVE_RECEIPT, str(row["receipt_key"]),
                                            str(row["forecaster"]))
            if selected:
                return None
        if selected and (plan_presentation_id or not answered_revision):
            return None
        row = grade
    if _usable(row, practice_item_id):
        return SurpriseForecast(float(row["p"]), GRADE_RECEIPT, str(row["receipt_key"]), str(row["forecaster"]))
    return None


__all__ = ["GRADE_RECEIPT", "MASTERY", "SERVE_FORECASTERS", "SERVE_RECEIPT", "SurpriseForecast",
           "read_surprise_forecast", "record_grade_forecast", "validate_live_binding", "with_grade_forecast"]
