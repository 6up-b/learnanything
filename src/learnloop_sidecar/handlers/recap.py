"""Reader workbench RW6a: "Last time here" and Wrap up (spec_reader_workbench_v1 §9.1).

Four desktop RPCs over ``learnloop.reader.recap``:

* ``reader.recap`` -- the returning card for a source (a pure read);
* ``reader.recap_event`` -- the only write: one salience-only
  ``reader_action_invoked`` with payload ``event`` ``recap_shown``,
  ``recap_dismissed`` or ``wrap_up_opened`` (G31);
* ``reader.wrap_up`` -- the session's three lists (a pure read);
* ``reader.wrap_up_offer`` -- whether to offer it where the learner lands
  after leaving a source (a pure read; UX S11).

Kill switches: ``recap.enabled`` (the card and its two events) and
``recap.wrap_up_enabled`` (Wrap up, its offer and ``wrap_up_opened``). Each
RPC refuses before reading or writing anything while its switch is off.
Desktop only (pinned in tests/test_mobile_allowlist.py; spec D20).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import recap as RC
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


def _now() -> datetime:
    return datetime.now(UTC)


def _require(ctx: SidecarContext, *, wrap_up: bool):
    vault, repository = ctx.require_vault()
    if wrap_up and not RC.wrap_up_enabled(vault):
        raise SidecarError("wrap_up_disabled", "Wrap up is switched off (recap.wrap_up_enabled = false).")
    if not wrap_up and not RC.recap_enabled(vault):
        raise SidecarError("recap_disabled", "\"Last time here\" is switched off (recap.enabled = false).")
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    return vault, repository


def _extraction(repository, extraction_id: str) -> str:
    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    return resolved


class ReaderRecapInput(ParamsModel):
    extraction_id: str
    # The Reader's visit (RW1a's envelope): the card is about the session
    # before the one this visit belongs to.
    visit_id: str | None = None


@method("reader.recap", ReaderRecapInput)
def reader_recap(ctx: SidecarContext, params: ReaderRecapInput) -> dict[str, Any]:
    """The "Last time here" card for a source, or ``recap: null`` (first visit,
    within the first session, or dismissed this session). Writes nothing."""

    vault, repository = _require(ctx, wrap_up=False)
    extraction_id = _extraction(repository, params.extraction_id)
    return versioned(RC.build_recap(
        vault, repository, extraction_id=extraction_id, current_visit_id=params.visit_id, now=_now(),
    ))


class ReaderRecapEventInput(ParamsModel):
    extraction_id: str
    event: str
    visit_id: str | None = None


@method("reader.recap_event", ReaderRecapEventInput)
def reader_recap_event(ctx: SidecarContext, params: ReaderRecapEventInput) -> dict[str, Any]:
    """Record that the card was shown or dismissed, or that Wrap up was opened."""

    if params.event not in RC.RECAP_EVENTS:
        raise SidecarError("validation_error", f"unknown recap event {params.event!r}")
    _vault, repository = _require(ctx, wrap_up=params.event in RC.WRAP_UP_EVENTS)
    extraction_id = _extraction(repository, params.extraction_id)
    try:
        event_id = RC.record_recap_event(
            repository, extraction_id=extraction_id, event=params.event, visit_id=params.visit_id,
        )
    except RC.RecapError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"event_id": event_id, "event": params.event})


class ReaderWrapUpInput(ParamsModel):
    extraction_id: str
    # In the Reader: the current visit, so the session runs to now. At the
    # destination: omitted, the source's latest session.
    visit_id: str | None = None


@method("reader.wrap_up", ReaderWrapUpInput)
def reader_wrap_up(ctx: SidecarContext, params: ReaderWrapUpInput) -> dict[str, Any]:
    """The session's resolved, still open and worth reinforcing lists, each
    line with the action the same chip takes elsewhere. Writes nothing."""

    vault, repository = _require(ctx, wrap_up=True)
    extraction_id = _extraction(repository, params.extraction_id)
    return versioned(RC.build_wrap_up(
        vault, repository, extraction_id=extraction_id, current_visit_id=params.visit_id, now=_now(),
    ))


class ReaderWrapUpOfferInput(ParamsModel):
    pass


@method("reader.wrap_up_offer", ReaderWrapUpOfferInput)
def reader_wrap_up_offer(ctx: SidecarContext, params: ReaderWrapUpOfferInput) -> dict[str, Any]:
    """Whether the place the learner lands offers Wrap up: the most recent
    reader session had activity and was not wrapped up. Writes nothing."""

    vault, repository = _require(ctx, wrap_up=True)
    return versioned({"offer": RC.wrap_up_offer(vault, repository, now=_now())})
