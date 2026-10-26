"""Reader CA1: the problem as printed on the desktop (ux_reader_compare_ask_v1 §8, K15).

* ``practice.as_printed``: an item's *as printed* view. The server decides
  what may show: a check on your own now gets the figure-only view or
  nothing, whatever the client asks; the crop is only the problem's own
  blocks (C10). "On your own" is every unassisted administration the server
  knows of (Codex review F1): DL2's due "Check once" (D46), a due cold
  follow-up (``cold_retry``, ``certification_cold_probe``) and an active
  diagnostic presentation of the item, each with or without a commitment. ``render`` adds the crop images; without it
  the view is the header's locator and labels (one cheap read on serve).
* ``practice.report_transcription``: "the transcription doesn't match the
  page", the learner's optional text, as a maintenance notice.

Both are reads or a report: no model call, no evidence, no exposure (the
original page records its own where it opens, ``get_span_view``).
Desktop only (no phone RPC in v1, D20).
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import Field

from learnloop.reader.as_printed import item_as_printed, printed_origin
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

AS_PRINTED_RPCS = ("practice.as_printed", "practice.report_transcription")

#: The learner's note on a transcription report: a storage bound on one
#: free-text field (a guardrail, not a model parameter).
REPORT_NOTE_MAX_CHARS = 4000


class AsPrintedInput(ParamsModel):
    practice_item_id: str
    render: bool = False


class TranscriptionReportInput(ParamsModel):
    practice_item_id: str
    note: str | None = Field(default=None, max_length=REPORT_NOTE_MAX_CHARS)


def _enabled(vault: Any) -> bool:
    return bool(vault.config.practice.as_printed.enabled)


def cold_now(vault: Any, repository: Any, practice_item_id: str) -> bool:
    """The item is administered on your own now (D46: nothing locates it):
    a due cold follow-up on it, an active diagnostic presentation of it, or
    DL2's due "Check once" served cold (F1: the first two need no
    commitment). An error reading any of them hides the print (fails closed)."""

    from learnloop.clock import SystemClock
    from learnloop.intent.checks import cold_followup_duty, served_check

    try:
        now = SystemClock().now()
        if cold_followup_duty(repository, practice_item_id, now=now) is not None:
            return True
        if repository.active_probe_presentation_for_item(practice_item_id) is not None:
            return True
        check = served_check(vault, repository, practice_item_id, now=now)
    except Exception:  # noqa: BLE001 - fail closed: a check that cannot be read is treated as cold
        logging.getLogger(__name__).exception("Could not read whether %s is a check on your own", practice_item_id)
        return True
    return bool(check and check.get("locators_hidden"))


def _source_title(repository: Any, source_id: str | None, extraction_id: str) -> str | None:
    with repository.connection() as connection:
        row = None
        if source_id:
            row = connection.execute("SELECT display_title FROM source_artifacts WHERE id = ?", (source_id,)).fetchone()
        if row is None:
            row = connection.execute(
                "SELECT a.display_title FROM source_extraction_runs r JOIN source_revisions v ON v.id = r.revision_id "
                "JOIN source_artifacts a ON a.id = v.source_id WHERE r.id = ?", (extraction_id,)).fetchone()
    return str(row[0]) if row is not None and row[0] else None


@method("practice.as_printed", AsPrintedInput)
def practice_as_printed(ctx: SidecarContext, params: AsPrintedInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice item {params.practice_item_id} was not found.")
    if not _enabled(vault):
        return versioned(item_as_printed(repository, item, enabled=False, cold=False, render=False))
    cold = cold_now(vault, repository, item.id)
    origin = printed_origin(repository, item)
    photo = None
    if origin is None:
        from learnloop.capture import photo_for_practice_item

        photo = photo_for_practice_item(repository, item.id)
    title = _source_title(repository, origin.source_id, origin.extraction_id) if origin is not None else None
    view = item_as_printed(repository, item, enabled=True, cold=cold, render=params.render,
                           source_title=title, photo=photo, origin=origin)
    return versioned({"practice_item_id": item.id, **view})


@method("practice.report_transcription", TranscriptionReportInput)
def practice_report_transcription(ctx: SidecarContext, params: TranscriptionReportInput) -> dict[str, Any]:
    from learnloop.ops.maintenance_feed import report_transcription_mismatch

    vault, repository = ctx.require_vault()
    if not _enabled(vault):
        raise SidecarError("disabled", "The problem as printed is off (practice.as_printed.enabled).")
    item = vault.practice_items.get(params.practice_item_id)
    origin = printed_origin(repository, item) if item is not None else None
    try:
        notice = report_transcription_mismatch(vault, repository, params.practice_item_id, origin=origin,
                                               note=params.note)
    except LookupError as exc:
        raise SidecarError("not_found", f"Practice item {params.practice_item_id} was not found.") from exc
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    detail = notice.get("detail") or {}
    return versioned({"notice_id": notice.get("id"), "status": notice.get("status"),
                      "reports": detail.get("reports", 1)})
