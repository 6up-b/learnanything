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
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
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
})
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
) -> list[str]:
    """Record a batch of Reader activity events; all-or-nothing validation.

    Each entry is ``{kind, event?, payload}``: one of the existing reader kinds
    in ``CLIENT_ACTIVITY_KINDS``, or ``reader_action_invoked`` with an
    ``event`` in ``CLIENT_ACTION_EVENTS``. Payload keys may be camelCase; only
    ``ACTIVITY_FIELDS`` survive (ids, kinds, counts, timings), strings are cut
    to ``MAX_FIELD_CHARS``. Server-owned events (a status flip, a reconnect
    answer) are refused here: they come from their own RPCs."""

    if len(events) > MAX_EVENTS_PER_CALL:
        raise InquiryError(f"at most {MAX_EVENTS_PER_CALL} activity events per call")
    validated = [_validate(entry) for entry in events]
    ids: list[str] = []
    for kind, event, payload in validated:
        body = dict(payload)
        if event is not None:
            body["event"] = event
        ids.append(log_interaction_event(
            repository,
            kind=kind,
            origin="learner",
            subject_type="reader_extraction" if payload.get("extraction_id") else "reader_visit",
            subject_id=payload.get("extraction_id") or payload.get("visit_id"),
            payload=salience_payload(body),
            clock=clock,
        ))
    return ids


__all__ = [
    "CLIENT_ACTION_EVENTS",
    "RW1B_SERVER_EVENTS",
    "RW4A_SERVER_EVENTS",
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
