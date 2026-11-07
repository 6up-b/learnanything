"""Reader workbench RW1a: inquiry status, reconnect, and reader activity.

Spec: ``docs/specs/spec_reader_workbench_v1.md`` §4.1 and §4.3.

* **An inquiry** is a root Ask exchange and its descendants (the branch links
  ride the ``reader_answer_submitted`` payload). Its **status** is the root's
  existing learner-owned ``question_events.resolution`` -- ``open``,
  ``resolved`` or ``dismissed``, reopen included. No new vocabulary and no
  schema change; "revisit once" and "make it something I can do" are the
  existing ``test_me_later`` and ``help_me_remember`` presets on the root's
  anchor, invoked by the Reader.
* **Reconnect** asks "does this make sense now?" about the root, in the
  learner's own words: *yes* resolves the root as an explicit self-report;
  *still unclear* starts a branch from the root (an ordinary reader.ask); a
  *quick check* asks the quick-check producer for one formative question
  scoped to the root passage.
* **Reader activity** -- visits, selections, actions, detours, reconnect
  lines, model jobs -- is recorded on EXISTING interaction kinds with a
  payload ``event`` field (no new kind, so no table rebuild) and read by
  ``learnloop reader report``.

Everything here is salience-only (W1 tier 1, P3 §8.2): the firewall stamps
every row ``authority_class = 'salience_only'``, no row reaches the evidence
ingestion API, and nothing writes an attempt, observation, mastery or FSRS
row. The status flip writes ``question_events.resolution`` and nothing else.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
from learnloop.router_objective import exposure
from learnloop.substrate.activities import log_interaction_event
from learnloop.tutor import question_queue as QQ

RESOLUTIONS = QQ.RESOLUTIONS
STATUS_TRIGGERS = ("chip", "reconnect", "undo", "key")
RECONNECT_ANSWERS = ("yes", "still_unclear", "quick_check")
RECONNECT_PLACEMENTS = ("inline", "rail")

# Payload ``event`` values on ``reader_action_invoked`` that the Reader UI
# records through ``reader.log_activity`` ...
CLIENT_ACTION_EVENTS: tuple[str, ...] = (
    "action_invoked",     # a learner action, by kind (ask, follow_up, a preset, ...)
    "detour_opened",      # a return-stack entry: a branch, a peek, a citation, another source
    "detour_returned",    # back at the detour's origin (Alt+<-, a crumb, the reconnect line)
    "reconnect_shown",    # the reconnect line appeared (inline or in the rail)
    "proactive_shown",    # another element LearnLoop started (a waiting quick check, ...)
    "back_to_reading",    # the first touch of the source after a usable result
    "cue_shown",          # RW3a: a margin mark in the learner's view (once per visit; spec §11)
    "tutor_offer_shown",  # RW1c: a button under a tutor answer appeared (its kind; spec §15)
    "tutor_offer_pressed",  # RW1c: the learner pressed one (its kind, the tool call it runs, what it found)
    "figure_opened",      # RW5a: an explorable figure expanded (its id; spec §11 events)
    "figure_animated",    # RW5a: "play" (or a step under reduced motion) on a figure's parameter
    # Reader CA5 (ux_reader_compare_ask_v1 §6.5 Records; salience only; CA5a's
    # deferred events): a corresponding section peeked, or opened (go there).
    # CA6 records the same two events from side by side's doors (one
    # definition; the same payload keys as CA5's correspondenceEvents.ts).
    "corresponding_section_peeked",
    "corresponding_section_opened",
    "sketch_paused",      # RW5d P2: the Worker watchdog paused a slow sketch (spec §6.6, §13.4)
    "sketch_error",       # RW5d P2: a sketch call failed at the learner's settings (the kind, never the text)
    # RW5d P2b (spec §13.4; salience only): the fuller version opened from its
    # quick figure's line, and the quick version opened back.
    "fuller_version_opened",
    "quick_version_opened",
    # Reader CA6 (ux_reader_compare_ask_v1 §6.5 Records; salience only): side
    # by side opened and closed (a session: its id and how long it was open,
    # for §14's side-by-side minutes), follow along moving the following pane
    # at a section crossing, and the learner taking that pane back to where it
    # was (§14's undone follow-along moves: the pairing was wrong).
    "side_by_side_opened",
    "side_by_side_closed",
    "follow_along_moved",
    "follow_along_undone",
)
# ... and the ones the sidecar writes itself, for acts with a server effect.
SERVER_ACTION_EVENTS: tuple[str, ...] = (
    "inquiry_status_set",
    "reconnect_answered",
)
# RW1b's server-owned events (the sidecar's ``reader_intent`` handlers): the
# intent box's routing (used or discarded) and its correction, and active
# reading's request, self-check and reconstruct acts. Like every event outside
# ``CLIENT_ACTION_EVENTS``, the UI cannot record them.
RW1B_SERVER_EVENTS: tuple[str, ...] = (
    "intent_routed",
    "intent_corrected",
    "active_question_requested",
    "active_question_answered",
    "reconstruct_committed",
    "reconstruct_undone",
)
# RW4a's server-owned events (the sidecar's ``library_ask`` handlers): a
# library question asked, its organizer notes, a comparison opened and the
# tutor asked about pinned passages (``learnloop.source_retrieval.library_ask.EVENTS``).
RW4A_SERVER_EVENTS: tuple[str, ...] = (
    "library_ask",
    "library_notes",
    "compare_opened",
    "library_tutor_asked",
)
# RW5a's server-owned events (the sidecar's ``figures`` handlers): a figure
# asked for, the region of a figure it was asked for, a "not right?" version
# asked for, a prediction answered and its "what changed?" line written (ids,
# kinds and whether it matched only, never the learner's words).
RW5A_SERVER_EVENTS: tuple[str, ...] = (
    "figure_requested",
    "figure_region_selected",
    "figure_revision_requested",
    "figure_predicted",
    "figure_explained",
)
# Reader RW5d P1's server-owned event (the sidecar's ``figure.request``): a
# "show me" asked with words (how: its origin, whether it had a passage and
# who wrote the goal; never the words themselves).
RW5D_SERVER_EVENTS: tuple[str, ...] = (
    "show_me_requested",
    # RW5d P2b: a rich build cancelled (``figure.rich_cancel``; its tier, never words).
    "rich_build_cancelled",
    # RW5d P3: a figure going out on an attempt host (its id, the host and
    # whether it added a hint-equivalent), and a cold check's take step.
    "attempt_figure_opened",
    "figure_take_step",
)
INQUIRY_EVENTS = CLIENT_ACTION_EVENTS + SERVER_ACTION_EVENTS

# Existing kinds the Reader UI records without an ``event`` field.
CLIENT_ACTIVITY_KINDS: tuple[str, ...] = (
    "reader_view_opened",
    "reader_view_closed",
    "reader_selection",
    "reader_job_queued",
    "reader_job_completed",
)

# The only payload fields kept from the UI: ids, kinds, counts and timings.
# Anything else -- above all the learner's words or a quoted passage -- is
# dropped, so activity rows and the report never carry learner text.
ACTIVITY_FIELDS: frozenset[str] = frozenset({
    "visit_id", "extraction_id", "source_id", "source_kind", "surface", "posture",
    "span_id", "span_count", "action_kind", "detour_id", "detour_kind", "origin_span_id",
    "target_span_id", "depth", "via", "returned_to_origin", "seconds_away", "model_wait_ms",
    "root_exchange_id", "exchange_id", "placement", "element", "job_id", "job_kind",
    "status", "failure_reason", "latency_ms", "model", "prompt_version", "route",
    "active_seconds", "idle_seconds", "seconds_after",
    # RW3a's mark impressions: which cue, its kind and the density in force.
    "cue_id", "cue_kind", "density",
    # RW1b: the intention an action serves, how it was reached (the palette
    # or the intent box) and an active-reading question's style.
    "intention", "entry", "style",
    # RW1c: an offer's kind, the tutor's request it runs (a source_tool_calls
    # id) and what the press found (shown, empty, failed, still looking).
    "offer_kind", "tool_call_id", "offer_result",
    # RW5a: which figure, and the parameter a play or step swept.
    "figure_id", "parameter",
    # Reader CA5: the section a correspondence act starts from and the one it
    # reaches (ids), and whether that one is judged or an unchecked search hit.
    "section_id", "target_source_id", "target_extraction_id", "target_section_id", "by",
    # RW5d P2: a sketch error's kind (work_cap, memory_cap, error, scene, ...).
    "error_kind",
    # Reader CA6: which pane leads (main or side) when follow along moves the
    # other; a side-by-side session's id and how many seconds it was open.
    "leader", "side_by_side_id", "seconds_open",
    # RO0 rows 3 and 4 (spec_router_objective_v1 §4; dropped with [router_objective] receipts off): whether Ask was
    # available for this visit, who sent the learner here, and the plan's block and the session it belongs to.
    "ask_available", "initiator", "block_id", "session_id",
})
#: The RO0 fields above, a switch's to keep.
OBJECTIVE_ACTIVITY_FIELDS: frozenset[str] = frozenset({"ask_available", "initiator", "block_id", "session_id"})
WAIT_ACTIVITY_FIELDS: tuple[str, ...] = ("scrolled", "selected", "typed")
MAX_FIELD_CHARS = 200
MAX_EVENTS_PER_CALL = 200


class InquiryError(ValueError):
    """A refused inquiry or activity request (nothing was written)."""


# ---------------------------------------------------------------------------
# Inquiries
# ---------------------------------------------------------------------------

def resolve_inquiry_root(
    repository: Repository, *, extraction_id: str, exchange_id: str
) -> dict[str, Any]:
    """The root exchange of the inquiry ``exchange_id`` belongs to.

    Walks the durable parent links from this vault's event log (never the
    caller's word); a missing parent ends the walk (legacy exchanges are
    roots), and a cycle is refused."""

    exchanges = {
        e["event_id"]: e for e in RD.ask_history(repository, extraction_id=extraction_id, branches=True)
    }
    current = exchanges.get(exchange_id)
    if current is None:
        raise InquiryError(f"unknown reader exchange {exchange_id!r} on this source")
    seen = {current["event_id"]}
    while current.get("parent_exchange_id") in exchanges:
        parent_id = current["parent_exchange_id"]
        if parent_id in seen:
            raise InquiryError("the inquiry's branch links form a cycle")
        seen.add(parent_id)
        current = exchanges[parent_id]
    if not current.get("question_event_id"):
        raise InquiryError("the inquiry's root has no question to carry its status")
    return current


def set_inquiry_status(
    repository: Repository,
    *,
    extraction_id: str,
    exchange_id: str,
    resolution: str,
    trigger: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Set an inquiry's status on its root question (open | resolved | dismissed).

    ``trigger`` says which act did it (a status chip, the reconnect line's
    *yes*, an undo, a key). Logged as ``inquiry_status_set`` so reopens are
    countable; validated before any write."""

    if resolution not in RESOLUTIONS:
        raise InquiryError(f"unknown inquiry status {resolution!r}")
    if trigger not in STATUS_TRIGGERS:
        raise InquiryError(f"unknown status trigger {trigger!r}")
    root = resolve_inquiry_root(repository, extraction_id=extraction_id, exchange_id=exchange_id)
    question_event_id = str(root["question_event_id"])
    question = repository.question_event(question_event_id)
    if question is None:
        raise InquiryError(f"the inquiry's question {question_event_id!r} is missing")
    previous = str(question.get("resolution") or "open")
    QQ.set_question_resolution(repository, question_event_id=question_event_id, resolution=resolution)
    log_interaction_event(
        repository,
        kind="reader_action_invoked",
        origin="learner",
        subject_type="reader_inquiry",
        subject_id=root["event_id"],
        payload=salience_payload({
            "event": "inquiry_status_set",
            "extraction_id": extraction_id,
            "root_exchange_id": root["event_id"],
            "question_event_id": question_event_id,
            "resolution": resolution,
            "previous_resolution": previous,
            "trigger": trigger,
        }),
        clock=clock,
    )
    return {
        "root_exchange_id": root["event_id"],
        "question_event_id": question_event_id,
        "resolution": resolution,
        "previous_resolution": previous,
    }


def answer_reconnect(
    repository: Repository,
    *,
    extraction_id: str,
    exchange_id: str,
    answer: str,
    via: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's answer to the reconnect line.

    *yes* resolves the root (an explicit self-report, trigger ``reconnect``);
    *still unclear* and *quick check* change no status -- their follow-on (a
    branch question, the passage check) is the caller's next request."""

    if answer not in RECONNECT_ANSWERS:
        raise InquiryError(f"unknown reconnect answer {answer!r}")
    if via not in RECONNECT_PLACEMENTS:
        raise InquiryError(f"unknown reconnect placement {via!r}")
    root = resolve_inquiry_root(repository, extraction_id=extraction_id, exchange_id=exchange_id)
    log_interaction_event(
        repository,
        kind="reader_action_invoked",
        origin="learner",
        subject_type="reader_inquiry",
        subject_id=root["event_id"],
        payload=salience_payload({
            "event": "reconnect_answered",
            "extraction_id": extraction_id,
            "root_exchange_id": root["event_id"],
            "answer": answer,
            "via": via,
        }),
        clock=clock,
    )
    resolution = str(
        (repository.question_event(str(root["question_event_id"])) or {}).get("resolution") or "open"
    )
    if answer == "yes":
        resolution = set_inquiry_status(
            repository, extraction_id=extraction_id, exchange_id=root["event_id"],
            resolution="resolved", trigger="reconnect", clock=clock,
        )["resolution"]
    return {
        "root_exchange_id": root["event_id"],
        "question_event_id": root["question_event_id"],
        "answer": answer,
        "resolution": resolution,
        "anchor_span_ids": list(root.get("selection_span_ids") or []) or [root["span_id"]],
    }


# ---------------------------------------------------------------------------
# Reader activity (the funnel's events)
# ---------------------------------------------------------------------------

_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")


def _snake(key: str) -> str:
    return _CAMEL.sub("_", str(key)).lower()


def _clean_value(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value[:MAX_FIELD_CHARS]
    return None


def _clean_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for raw_key, value in (payload or {}).items():
        key = _snake(raw_key)
        if key == "activity_during_wait" and isinstance(value, Mapping):
            cleaned[key] = {
                field: True
                for field in WAIT_ACTIVITY_FIELDS
                if value.get(field) is True or value.get(_snake(field)) is True
            }
            continue
        if key not in ACTIVITY_FIELDS:
            continue
        clean = _clean_value(value)
        if clean is not None or value is None:
            cleaned[key] = clean
    return cleaned


def _validate(entry: Mapping[str, Any]) -> tuple[str, str | None, dict[str, Any]]:
    kind = str(entry.get("kind") or "")
    event = entry.get("event")
    if kind == "reader_action_invoked":
        if event not in CLIENT_ACTION_EVENTS:
            raise InquiryError(f"unknown or server-owned reader event {event!r}")
    elif kind in CLIENT_ACTIVITY_KINDS:
        if event is not None:
            raise InquiryError(f"{kind} carries no event field")
    else:
        raise InquiryError(f"the Reader does not record {kind!r} as activity")
    payload = entry.get("payload")
    if payload is not None and not isinstance(payload, Mapping):
        raise InquiryError("an activity payload must be an object")
    return kind, (str(event) if event is not None else None), _clean_payload(payload)


def record_activity(
    repository: Repository,
    events: Sequence[Mapping[str, Any]],
    *,
    clock: Clock | None = None,
    config: Any = None,
    device_surface: str | None = None,
) -> list[str]:
    """Record a batch of Reader activity events; all-or-nothing validation.

    ``device_surface`` (mobile v2 §3.4): the device surface the request came from
    (``phone_reader``), set by the server from the request's origin and never from a
    payload (it is not an activity field, so a client's is dropped). The payload's own
    ``surface`` stays the Reader's view (text, pdf, watch). None (the desktop) writes no
    key, so the desktop's rows are as before.

    RO0 (``config``, with ``[router_objective] receipts`` on): a visit says who initiated it and whether Ask was
    available (rows 3 and 4), and an event its client stamped keeps that time as ``occurred_at`` beside the
    server's ``received_at`` (row 5; the client batches, so the gap is real). Off, none of it is written.

    Each entry is ``{kind, event?, payload}``: one of the existing reader kinds
    in ``CLIENT_ACTIVITY_KINDS``, or ``reader_action_invoked`` with an
    ``event`` in ``CLIENT_ACTION_EVENTS``. Payload keys may be camelCase; only
    ``ACTIVITY_FIELDS`` survive (ids, kinds, counts, timings), strings are cut
    to ``MAX_FIELD_CHARS``. Server-owned events (a status flip, a reconnect
    answer) are refused here: they come from their own RPCs."""

    if len(events) > MAX_EVENTS_PER_CALL:
        raise InquiryError(f"at most {MAX_EVENTS_PER_CALL} activity events per call")
    validated = [_validate(entry) for entry in events]
    objective = objective_receipts_on(config)
    ids: list[str] = []
    for entry, (kind, event, payload) in zip(events, validated):
        body = dict(payload)
        if event is not None:
            body["event"] = event
        if device_surface is not None:
            body["device_surface"] = str(device_surface)
        times = _event_times(entry, clock) if objective else {}
        if not objective:
            for name in OBJECTIVE_ACTIVITY_FIELDS:
                body.pop(name, None)
        elif kind == "reader_view_opened":
            # Landing ruling R2: the visit's block and session as of its own time, not its batch's arrival.
            body.update(exposure.visit_fields(config, repository, body,
                                              at=times["occurred_at"] or times["received_at"]))
        ids.append(log_interaction_event(
            repository,
            kind=kind,
            origin="learner",
            subject_type="reader_extraction" if payload.get("extraction_id") else "reader_visit",
            subject_id=payload.get("extraction_id") or payload.get("visit_id"),
            payload=salience_payload(body),
            clock=clock,
            **times,
        ))
    return ids


def _event_times(entry: Mapping[str, Any], clock: Clock | None) -> dict[str, str | None]:
    """RO0 row 5: the client's stamp, if it is a time at all, and when the server had it."""

    stamped = entry.get("occurred_at") or entry.get("occurredAt")
    try:
        when = parse_utc(stamped) if isinstance(stamped, str) else None
    except ValueError:
        when = None
    return {"occurred_at": when.strftime("%Y-%m-%dT%H:%M:%SZ") if when is not None else None,
            "received_at": utc_now_iso(clock)}


__all__ = [
    "CLIENT_ACTION_EVENTS",
    "RW1B_SERVER_EVENTS",
    "RW4A_SERVER_EVENTS",
    "RW5A_SERVER_EVENTS",
    "RW5D_SERVER_EVENTS",
    "CLIENT_ACTIVITY_KINDS",
    "INQUIRY_EVENTS",
    "InquiryError",
    "MAX_FIELD_CHARS",
    "RECONNECT_ANSWERS",
    "SERVER_ACTION_EVENTS",
    "answer_reconnect",
    "record_activity",
    "resolve_inquiry_root",
    "set_inquiry_status",
]
