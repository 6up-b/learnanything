"""Mobile v2 stage V4: the phone Reader's protection (spec_mobile_frontend_v2 §3, §5.1).

The desktop's Reader shows a book's text and refuses every model action on what the
held-out partition covers (``reader_guidance.reading_protection``). The phone is sent
less: no text, crop or page image of anything exam material covers (``exam_material``:
an exam-pool source, a held-out unit, a reading held back until it is marked), and
nothing at all of a reading it covers whole. One predicate decides it for the phone's
RPCs (here, at a phone origin only) and for the host's page and asset endpoints
(``learnloop_mobile.media``), so the text, the images and the phone's caches can't
disagree. A None origin (the desktop) never reaches anything in this module.

Nothing here writes, but an outbox intent's job receipt (:func:`once_per_job`, with the
intent's own rows). The predicate is read at each request, so a mark the owner makes
on the desktop withholds from the phone's next request on.
"""

from __future__ import annotations

from typing import Any, Iterable

# The predicate itself lives beside the media's (``learnloop.reader.phone_media``), so the phone's text, its
# pages, its stored images and its eligibility read one definition (Codex review of V4, F3, F10).
from learnloop.reader.phone_media import PhoneWithheld, phone_withheld

#: The surface a reader call under a phone origin records (spec §3.4).
PHONE_READER_SURFACE = "phone_reader"
#: The refusal code of a phone request for protected material (the adapter's 409).
HELD_OUT_CODE = "held_out_material"


def redact_blocks(blocks: list[dict[str, Any]], withheld: PhoneWithheld) -> list[dict[str, Any]]:
    """The render payload's blocks with every withheld passage's text, assets and math
    removed. The block stays (its id, type and health), so section counts, progress and the
    phone's place line up with the desktop's, and it says ``withheld``."""

    out = []
    for block in blocks:
        if withheld.covers(block.get("span_id")):
            block = {**block, "markdown": "", "sanitized": False, "katex_nodes": [], "assets": [], "withheld": True}
        out.append(block)
    return out


#: The refusal code of a phone's Ask while one of its checks on your own is open (J8).
COLD_CHECK_CODE = "cold_check_open"
COLD_CHECK_MESSAGE = "Ask is off while a check on your own is open. Finish it first, and Ask is back."


def cold_check_open(ctx: Any, vault: Any, repository: Any) -> bool:
    """Mobile v2 J8: an Ask during a cold check is refused, and on the phone the server knows it, never the
    phone's word (§5.2, ``coldActive``). A check is open when a session this device owns has an active probe
    presentation, or its checkpoint's question is administered on your own now (``as_printed.cold_now``: a due
    cold follow-up, an active diagnostic presentation, DL2's served check) or is today's open randomized check
    (RO5). Unreadable state says it is (fail closed)."""

    origin = getattr(ctx, "request_origin", None)
    if origin is None:
        return False
    try:
        with repository.connection() as connection:
            sessions = [str(row[0]) for row in connection.execute(
                "SELECT id FROM sessions WHERE owner_device_id = ? AND ended_at IS NULL", (origin.device_id,)
            ).fetchall()]
        for session_id in sessions:
            if repository.active_probe_presentation_for_session(session_id) is not None:
                return True
            checkpoint = repository.fetch_session_checkpoint(session_id) or {}
            item_id = checkpoint.get("current_practice_item_id")
            if not item_id:
                continue
            from learnloop.daily_plan.engine import PlanEnv, open_randomized_check
            from learnloop_sidecar.handlers.as_printed import cold_now

            if cold_now(vault, repository, str(item_id)):
                return True
            if open_randomized_check(PlanEnv(vault=vault, repository=repository), str(item_id)):
                return True
    except Exception:  # noqa: BLE001 - fail closed: no Ask on a state that can't be read
        import logging

        logging.getLogger(__name__).exception("could not read whether a check is open")
        return True
    return False


def once_per_job(ctx: Any, repository: Any, run: Any) -> Any:
    """Mobile v2 V4 (Codex review F5): an outbox intent's writes, once, whatever restarts.

    Run as one of the host's jobs (the origin names it), ``run()``'s rows and the job's receipt
    (``mobile_jobs.result_json``) commit in one transaction; a job a restart re-runs finds the receipt
    and answers it, writing nothing again. A short request and the desktop (no job) just ``run()``."""

    job_id = getattr(getattr(ctx, "request_origin", None), "job_id", None)
    if job_id is None:
        return run()
    from learnloop.capture.jobs import job_receipt, write_job_receipt

    with repository.atomic():
        connection = repository.connection()
        done = job_receipt(connection, str(job_id))
        if done is not None:
            return done
        result = run()
        write_job_receipt(connection, str(job_id), result)
    return result


def is_phone(ctx: Any) -> bool:
    return getattr(ctx, "request_origin", None) is not None


def destination_material(ctx: Any, vault: Any, repository: Any) -> Any:
    """At a phone origin, the material the phone is never sent, as one ``Material`` for the Reader's
    context assembly (K6-4): the request's selection is refused by :func:`refuse_if_withheld`, and this
    keeps the same predicate's material out of its neighbours, the blocks they cite, retrieved passages
    and earlier answers. None for the desktop. Unreadable: the request is refused (fail closed)."""

    if not is_phone(ctx):
        return None
    from learnloop.content.sources.exam_material import HELD_OUT_REFUSAL, exam_material

    try:
        return exam_material(vault, repository).material
    except Exception:  # noqa: BLE001 - fail closed: an unreadable predicate sends nothing
        import logging

        logging.getLogger(__name__).exception("exam material unreadable for a phone Ask")
        from learnloop_sidecar.errors import SidecarError

        raise SidecarError(HELD_OUT_CODE, HELD_OUT_REFUSAL) from None


#: What the phone is told of an Ask answer that named material held out from it (V4 landing, ruling R1).
ANSWER_WITHHELD_MESSAGE = "This answer drew on material held out from the phone. It's in your history on the desktop."


def sendable_exchanges(vault: Any, repository: Any, extraction_id: str,
                       exchanges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The Reader exchanges (each with its ``event_id``) the phone may be sent now: none of the passages
    its stored event names (``reader_dialogue.ask_provenance``) is withheld from the phone. An exchange the
    stored events don't account for is not sent (fail closed). Read at each request: a fresh answer, the
    Ask history, and a completed job read again (K6-5) all judge by it."""

    from learnloop.reader import reader_dialogue as RD

    provenance = RD.ask_provenance(repository, extraction_id=extraction_id)
    by_reading: dict[str, set[str]] = {extraction_id: set()}
    for places in provenance.values():
        for reading, span in places:
            by_reading.setdefault(reading, set()).add(span)
    withheld = {reading: phone_withheld(vault, repository, reading, sorted(spans))
                for reading, spans in by_reading.items()}
    if withheld[extraction_id].whole:
        return []
    passed = {event_id for event_id, places in provenance.items()
              if not any(withheld[reading].covers(span) for reading, span in places)}
    return [exchange for exchange in exchanges if exchange.get("event_id") in passed]


def refuse_if_withheld(ctx: Any, vault: Any, repository: Any, extraction_id: str | None,
                       span_ids: Iterable[str | None] = ()) -> None:
    """At a phone origin, refuse a request that names protected material (or a reading that
    is protected whole). Nothing for the desktop."""

    if not is_phone(ctx) or not extraction_id:
        return
    withheld = phone_withheld(vault, repository, str(extraction_id), list(span_ids))
    if withheld.any(span_ids) or withheld.whole:
        from learnloop_sidecar.errors import SidecarError

        raise SidecarError(HELD_OUT_CODE, withheld.message or "This passage is held out.")
