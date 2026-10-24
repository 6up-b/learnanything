"""Reader workbench RW1b: the intent box and active reading (spec_reader_workbench_v1 §4.2-§4.5).

The intent box's router:

* ``reader.route_intent`` -- start one routing of the box's text on a small
  worker thread (the sidecar is serial, so a Decider call never holds up the
  Reader's other requests) and answer at once with its id;
* ``reader.intent_routing`` -- read it (pending, or the action and why), so
  Enter takes a speculative routing already in flight;
* ``reader.intent_outcome`` -- the routing was used, discarded, or changed by
  the learner (the ``learner_card`` correction); ``reverted`` undoes the
  capture a routed action made when the learner presses "change". A fate
  asked of a routing still in flight is kept and recorded when it lands.

Active reading on a selection:

* ``reader.active_question`` -- ask for (or reuse) the selection's question in
  one style: next step, why step, assumptions, reconstruct; written off the
  request path by the quick-check producer's durable job;
* ``reader.active_question_status`` -- the question once written, and the
  job's state while it is not;
* ``reader.active_question_action`` -- answer (or "show me"), self-check
  (matches · partly · no) or dismiss; a missed answer queues a
  ``reader_formative`` learner text;
* ``reader.reconstruct`` / ``reader.reconstruct_undo`` -- "reconstruct this
  later": the escalated item and its ``test_me_later`` commitment, and undo.

Kill switches (each RPC refuses before reading or writing while its switch is
off): ``reader_intent.enabled`` (the box and its router; with
``reader_inquiry.enabled`` off too), ``reader_intent.speculative_enabled``
(speculative routings are not made), ``reader_active_reading.enabled`` (the
active-reading RPCs), ``reader_formative.enabled`` (no learner text is
queued). Held-out material is never sent to a model, the Decider included.
Desktop only (pinned in tests/test_mobile_allowlist.py; spec D20).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.reader import active_reading as AR
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_guidance as RG
from learnloop.reader import reader_intent as RI
from learnloop.reader import reader_quick_check as RQC
from learnloop.substrate.activities import log_interaction_event
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: The most routings kept in memory for reading back (oldest dropped first).
MAX_KEPT_ROUTINGS = 64
#: The longest one read may wait for a routing to finish (a poll, not a timeout).
MAX_WAIT_MS = 1_000

RW1B_RPCS = (
    "reader.route_intent",
    "reader.intent_routing",
    "reader.intent_outcome",
    "reader.active_question",
    "reader.active_question_status",
    "reader.active_question_action",
    "reader.reconstruct",
    "reader.reconstruct_undo",
)


def intent_enabled(vault: Any) -> bool:
    """The intent box is on: its switch and RW1a's inquiry (its rail and shared parts)."""

    return bool(vault.config.reader_intent.enabled) and RD.inquiry_enabled(vault)


def active_reading_enabled(vault: Any) -> bool:
    return bool(vault.config.reader_active_reading.enabled) and RD.inquiry_enabled(vault)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW1b (absent while off, so
    the wire is unchanged)."""

    fields: dict[str, Any] = {}
    if intent_enabled(vault):
        settings = vault.config.reader_intent
        fields["intent"] = {
            "palette": RI.palette(RI.Availability.from_config(vault.config)),
            # The learner's own notes (a textfile source): the anchor-free actions.
            "notes_palette": RI.palette(RI.Availability.from_config(vault.config, notes=True)),
            "speculative": bool(settings.speculative_enabled),
            "speculate_after_ms": int(settings.speculate_after_ms),
            "timeout_seconds": float(settings.timeout_seconds),
        }
    if active_reading_enabled(vault):
        fields["active_reading"] = {"fold_blocks": RQC.FOLD_BLOCKS}
    return fields


def _require_reader(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    return vault, repository


def _require_intent(ctx: SidecarContext):
    vault, repository = _require_reader(ctx)
    if not RD.inquiry_enabled(vault):
        raise SidecarError("inquiry_disabled", "Reader inquiries are switched off (reader_inquiry.enabled = false).")
    if not vault.config.reader_intent.enabled:
        raise SidecarError("intent_disabled", "The intent box is switched off (reader_intent.enabled = false).")
    return vault, repository


def _require_active(ctx: SidecarContext):
    vault, repository = _require_reader(ctx)
    if not RD.inquiry_enabled(vault):
        raise SidecarError("inquiry_disabled", "Reader inquiries are switched off (reader_inquiry.enabled = false).")
    if not vault.config.reader_active_reading.enabled:
        raise SidecarError(
            "active_reading_disabled", "Active reading is switched off (reader_active_reading.enabled = false)."
        )
    return vault, repository


def _extraction(repository, extraction_id: str) -> str:
    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    return resolved


def _refuse_held_out(vault, repository, extraction_id: str, span_ids: list[str]) -> None:
    protection = RG.reading_protection(vault, repository, extraction_id, span_ids)
    if protection["withheld"] or protection["held_out_span_ids"]:
        raise SidecarError("exam_material", str(protection.get("message") or "This passage is held out."))


def _event(repository, kind: str, payload: dict[str, Any], *, subject_id: str | None) -> None:
    log_interaction_event(
        repository, kind=kind, origin="learner", subject_type="reader_extraction", subject_id=subject_id,
        payload=salience_payload(payload),
    )


# ---------------------------------------------------------------------------
# The router's worker
# ---------------------------------------------------------------------------


@dataclass
class _Running:
    routing_id: str
    extraction_id: str
    speculative: bool
    started: float
    done: threading.Event = field(default_factory=threading.Event)
    routing: RI.Routing | None = None
    error: str | None = None
    #: A fate asked while the routing ran (the text changed, the box closed),
    #: recorded by the worker once the routing lands (Codex review F12).
    lock: threading.Lock = field(default_factory=threading.Lock)
    pending_fate: str | None = None
    #: Set when the worker is finished, its deferred fate included.
    fate_done: threading.Event = field(default_factory=threading.Event)


def _record_fate(repository, running: _Running, fate: str) -> str | None:
    """One fate (``used`` or ``discarded``) and its funnel event."""

    routing = running.routing
    assert routing is not None and routing.judgment_id is not None
    appended = RI.record_fate(repository, routing.judgment_id, fate)
    _event(repository, "reader_action_invoked", {
        "event": "intent_routed", "extraction_id": running.extraction_id, "routing_id": routing.routing_id,
        "action_kind": routing.action, "intention": routing.intention, "status": routing.status,
        "failure_reason": routing.reason, "speculative": routing.speculative,
        "used": fate == "used",
    }, subject_id=running.extraction_id)
    return appended


class IntentRoutings:
    """Routings in flight and just made, kept for reading back (in memory)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _Running] = {}

    def start(self, ctx: SidecarContext, vault: Any, repository: Any, *, text: str, quote: str,
              extraction_id: str, span_ids: list[str], speculative: bool, notes: bool = False) -> _Running:
        routing_id = f"rint_{time.time_ns():x}"
        running = _Running(routing_id, extraction_id, speculative, time.monotonic())
        with self._lock:
            self._kept[routing_id] = running
            while len(self._kept) > MAX_KEPT_ROUTINGS:
                self._kept.pop(next(iter(self._kept)))
        factory = getattr(ctx, "reader_intent_client_factory", None)
        root, config, sqlite_path = vault.root, vault.config, repository.sqlite_path

        def run() -> None:
            from learnloop.db.repositories import Repository

            worker_repo = Repository.attach(sqlite_path)
            try:
                _event(worker_repo, "reader_job_queued", {
                    "extraction_id": extraction_id, "job_id": routing_id, "job_kind": "intent_routing",
                    "speculative": speculative,
                }, subject_id=extraction_id)
                running.routing = RI.route(
                    root, config, worker_repo, text=text, quote=quote, extraction_id=extraction_id,
                    span_ids=span_ids, available=RI.Availability.from_config(config, notes=notes),
                    speculative=speculative,
                    client_factory=factory, routing_id=routing_id,
                )
                routing = running.routing
                _event(worker_repo, "reader_job_completed", {
                    "extraction_id": extraction_id, "job_id": routing_id, "job_kind": "intent_routing",
                    "speculative": speculative,
                    # The funnel's statuses: a routing the Decider made is
                    # completed; any fallback is failed with its reason.
                    "status": "completed" if routing.status == RI.ROUTED else "failed",
                    "failure_reason": routing.reason,
                    "latency_ms": routing.latency_ms, "model_wait_ms": routing.latency_ms, "model": routing.model,
                    "prompt_version": RI.QUESTION_SET_VERSION, "route": RI.ROUTE,
                }, subject_id=extraction_id)
            except Exception as exc:  # noqa: BLE001 - a routing that broke routes to Ask
                running.error = type(exc).__name__
            finally:
                with running.lock:
                    running.done.set()
                    fate = running.pending_fate
                try:
                    if fate and running.routing is not None and running.routing.judgment_id is not None:
                        _record_fate(worker_repo, running, fate)
                except Exception:  # noqa: BLE001 - a fate is a report row, never the Reader's
                    running.error = running.error or "fate_failed"
                finally:
                    running.fate_done.set()

        if getattr(ctx, "reader_intent_inline", False):
            run()
        else:
            threading.Thread(target=run, name=f"reader-intent-{routing_id}", daemon=True).start()
        return running

    def get(self, routing_id: str) -> _Running | None:
        with self._lock:
            return self._kept.get(routing_id)


def _routings(ctx: SidecarContext) -> IntentRoutings:
    routings = getattr(ctx, "reader_intent_routings", None)
    if routings is None:
        routings = IntentRoutings()
        ctx.reader_intent_routings = routings  # type: ignore[attr-defined]
    return routings


def _routing_payload(running: _Running) -> dict[str, Any]:
    if not running.done.is_set():
        return {"routing_id": running.routing_id, "state": "pending", "speculative": running.speculative}
    if running.routing is None:
        # The routing itself broke: Ask, as for any failure (G3).
        fallback = RI.Routing(running.routing_id, RI.DEFAULT_ACTION, RI.FALLBACK, running.speculative,
                              reason="failed")
        return {"state": "done", **fallback.as_dict()}
    return {"state": "done", **running.routing.as_dict()}


class ReaderRouteIntentInput(ParamsModel):
    extraction_id: str
    span_ids: list[str]
    text: str
    quote: str = ""
    speculative: bool = False
    # The learner's own notes: the Decider is offered the anchor-free actions only.
    notes: bool = False


@method("reader.route_intent", ReaderRouteIntentInput)
def reader_route_intent(ctx: SidecarContext, params: ReaderRouteIntentInput) -> dict[str, Any]:
    """Start routing the intent box's text (never on the request path)."""

    vault, repository = _require_intent(ctx)
    extraction_id = _extraction(repository, params.extraction_id)
    spans = [str(span) for span in params.span_ids if span]
    if not spans:
        raise SidecarError("validation_error", "A routing needs the selection's passages.")
    _refuse_held_out(vault, repository, extraction_id, spans)
    text = params.text.strip()
    if not text:
        # An empty Enter asks, with no model call and nothing written.
        return versioned({"state": "done", **RI.Routing("", RI.DEFAULT_ACTION, RI.EMPTY, params.speculative).as_dict()})
    if params.speculative and not RI.speculation_room(vault.config, repository):
        reason = "speculation_off" if not vault.config.reader_intent.speculative_enabled else "speculation_stopped"
        return versioned({"state": "done", **RI.Routing("", RI.DEFAULT_ACTION, RI.NOT_MADE, True,
                                                        reason=reason).as_dict()})
    running = _routings(ctx).start(ctx, vault, repository, text=text, quote=params.quote,
                                   extraction_id=extraction_id, span_ids=spans, speculative=params.speculative,
                                   notes=params.notes)
    return versioned(_routing_payload(running))


class ReaderIntentRoutingInput(ParamsModel):
    routing_id: str
    wait_ms: int = 0


@method("reader.intent_routing", ReaderIntentRoutingInput)
def reader_intent_routing(ctx: SidecarContext, params: ReaderIntentRoutingInput) -> dict[str, Any]:
    """A routing's state; waits up to ``wait_ms`` (at most a second) for it."""

    _require_intent(ctx)
    running = _routings(ctx).get(params.routing_id)
    if running is None:
        raise SidecarError("not_found", "That routing is no longer kept; route again.")
    wait = max(0, min(int(params.wait_ms), MAX_WAIT_MS))
    if wait:
        running.done.wait(wait / 1000)
    return versioned(_routing_payload(running))


class ReaderIntentOutcomeInput(ParamsModel):
    routing_id: str
    outcome: str
    action: str | None = None
    #: ``reverted``: the annotation the routed capture made.
    annotation_id: str | None = None


@method("reader.intent_outcome", ReaderIntentOutcomeInput)
def reader_intent_outcome(ctx: SidecarContext, params: ReaderIntentOutcomeInput) -> dict[str, Any]:
    """``used`` (Enter took it), ``discarded`` (the text changed, the box
    closed), ``corrected`` ("change", with the action picked instead, or none)
    or ``reverted`` ("change" after a routed capture ran: its annotation,
    commitment and synthesis are undone). A fate asked while the routing is
    still in flight is kept and recorded when it lands (``deferred``)."""

    _vault, repository = _require_intent(ctx)
    running = _routings(ctx).get(params.routing_id)
    if running is None:
        raise SidecarError("not_found", "That routing is no longer kept.")
    if params.outcome in RI.FATES:
        with running.lock:
            if not running.done.is_set():
                running.pending_fate = params.outcome
                return versioned({"routing_id": running.routing_id, "recorded": False, "deferred": True})
    if running.routing is None or running.routing.judgment_id is None:
        raise SidecarError("not_found", "That routing is no longer kept.")
    routing = running.routing
    try:
        if params.outcome in RI.FATES:
            appended = _record_fate(repository, running, params.outcome)
        elif params.outcome == "reverted":
            action = RI.ACTIONS_BY_ID.get(routing.action)
            if routing.status != RI.ROUTED or action is None or action.effect.get("kind") not in RI.REVERTIBLE_EFFECTS:
                raise SidecarError("validation_error", "Only a routed capture can be reverted.")
            if not params.annotation_id:
                raise SidecarError("validation_error", "A revert names the capture's annotation.")
            reverted = RI.revert_capture(repository, annotation_id=params.annotation_id)
            return versioned({"routing_id": routing.routing_id, "recorded": True, "reverted": reverted})
        elif params.outcome == "corrected":
            appended = RI.record_correction(repository, routing.judgment_id, params.action)
            chosen = RI.ACTIONS_BY_ID.get(params.action or "")
            _event(repository, "reader_action_invoked", {
                "event": "intent_corrected", "extraction_id": running.extraction_id,
                "routing_id": routing.routing_id, "action_kind": params.action or "cancelled",
                "routed": routing.action, "intention": chosen.intention if chosen else None,
                "speculative": routing.speculative,
            }, subject_id=running.extraction_id)
        else:
            raise SidecarError("validation_error", f"Unknown outcome {params.outcome!r}.")
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"routing_id": routing.routing_id, "recorded": appended is not None})


# ---------------------------------------------------------------------------
# Active reading
# ---------------------------------------------------------------------------


def _question_payload(vault, repository, row: dict[str, Any]) -> dict[str, Any]:
    from learnloop.reader.reader_progression import learning_objects_for_span
    from learnloop_sidecar.handlers.reader import _authored_question_payload

    payload = _authored_question_payload(row)
    payload["answer_basis"] = row.get("answer_basis")
    anchors = payload.get("anchor_span_ids") or []
    learning_object_id = None
    for span_id in anchors:
        linked = learning_objects_for_span(vault, repository, extraction_id=row["extraction_id"], span_id=span_id)
        if linked:
            learning_object_id = linked[0]
            break
    payload["escalation_learning_object_id"] = learning_object_id
    payload["missed"] = RQC.is_missed(row)
    if row.get("question_style") == "reconstruct":
        payload["reconstruct"] = _reconstruct_state(repository, row)
    return payload


def _reconstruct_state(repository, row: dict[str, Any]) -> dict[str, Any] | None:
    from learnloop.curriculum import commitments as C

    commitment_id = AR._commitment_for(repository, str(row["id"]))
    if commitment_id is None:
        return None
    return {"commitment_id": commitment_id, "practice_item_id": row.get("practice_item_id"),
            "disposition": C.resolve_disposition(repository, commitment_id)}


def _job_state(repository, batch_id: str | None) -> dict[str, Any] | None:
    if not batch_id:
        return None
    jobs = repository.ingest_jobs_for_batch(batch_id)
    job = jobs[0] if jobs else None
    if job is None or job.get("job_type") != "reader_quick_check" \
            or (job.get("payload") or {}).get("scope_kind") != "selection":
        return None
    error = job.get("error") or {}
    ended = job.get("status") in ("failed", "cancelled")
    details = (error.get("details") if isinstance(error, dict) else None) or {}
    return {
        "status": job.get("status"),
        "error_code": error.get("code") if isinstance(error, dict) else None,
        "message": (error.get("message") if isinstance(error, dict) else None) if ended else None,
        "refusal": (details.get("refusal") if isinstance(details, dict) else None) if ended else None,
    }


class ReaderActiveQuestionInput(ParamsModel):
    extraction_id: str
    span_ids: list[str]
    style: str


@method("reader.active_question", ReaderActiveQuestionInput)
def reader_active_question(ctx: SidecarContext, params: ReaderActiveQuestionInput) -> dict[str, Any]:
    """The selection's question in one style: reused, or queued for the
    producer (written off the request path). ``folded_span_ids`` names the
    book's next blocks, which the Reader folds at once for the next step."""

    from learnloop_sidecar.handlers.ai_providers import ready_canonical_ingest_provider

    vault, repository = _require_active(ctx)
    if params.style not in RQC.SELECTION_STYLES:
        raise SidecarError("validation_error", f"Unknown question style {params.style!r}.")
    extraction_id = _extraction(repository, params.extraction_id)
    spans = [str(span) for span in params.span_ids if span]
    try:
        view = RQC.selection_view(repository, extraction_id=extraction_id, anchor_span_ids=spans, style=params.style)
    except RQC.ReaderQuickCheckError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    _refuse_held_out(vault, repository, extraction_id, [
        *view["anchor_span_ids"], *(b["span_id"] for b in [*view["before"], *view["following"]])])
    folded = [b["span_id"] for b in view["following"]] if params.style == "next_step" else []
    response: dict[str, Any] = {
        "style": params.style, "anchor_span_ids": view["anchor_span_ids"], "folded_span_ids": folded,
        "status": None, "batch_id": None, "message": None, "question": None,
    }
    _event(repository, "reader_action_invoked", {
        "event": "active_question_requested", "extraction_id": extraction_id, "style": params.style,
        "span_count": len(view["anchor_span_ids"]),
    }, subject_id=extraction_id)
    if params.style == "next_step" and not folded:
        response["status"] = "no_next_step"
        response["message"] = "Nothing follows this line in its section, so there is no next step to try."
        return versioned(response)
    existing = RQC.selection_question(repository, extraction_id=extraction_id,
                                      anchor_span_ids=view["anchor_span_ids"], style=params.style)
    if existing is not None:
        response["status"] = "exists"
        response["question"] = _question_payload(vault, repository, existing)
        return versioned(response)
    from learnloop.ai import plan_fallback

    # Under the passage check's own price, as its job resolves it (fix round
    # L1): no offer or grant the job would refuse.
    with plan_fallback.priced_by(RQC.PASSAGE_CHECK_PRICE_SETTING):
        _provider, runtime, client = ready_canonical_ingest_provider(vault)
    if client is None:
        response["status"] = "provider_unavailable"
        response["message"] = getattr(runtime, "message", None) or "LearnLoop's model is unavailable for this question."
        return versioned(response)
    response["status"] = "queued"
    response["batch_id"] = ctx.ingest_jobs.enqueue_reader_selection_check(
        extraction_id=extraction_id, anchor_span_ids=view["anchor_span_ids"], question_style=params.style,
    )
    return versioned(response)


class ReaderActiveQuestionStatusInput(ParamsModel):
    extraction_id: str
    anchor_span_ids: list[str]
    style: str
    batch_id: str | None = None


@method("reader.active_question_status", ReaderActiveQuestionStatusInput)
def reader_active_question_status(ctx: SidecarContext, params: ReaderActiveQuestionStatusInput) -> dict[str, Any]:
    """The question once written (a cheap local read), and its job's state."""

    vault, repository = _require_active(ctx)
    extraction_id = _extraction(repository, params.extraction_id)
    row = RQC.selection_question(repository, extraction_id=extraction_id,
                                 anchor_span_ids=list(params.anchor_span_ids), style=params.style)
    return versioned({
        "question": _question_payload(vault, repository, row) if row else None,
        "job": _job_state(repository, params.batch_id),
    })


class ReaderActiveQuestionActionInput(ParamsModel):
    question_id: str
    action: str
    response: str | None = None
    self_check: str | None = None


@method("reader.active_question_action", ReaderActiveQuestionActionInput)
def reader_active_question_action(ctx: SidecarContext, params: ReaderActiveQuestionActionInput) -> dict[str, Any]:
    """Answer (an empty answer is "show me"), self-check or dismiss. Formative:
    the row is the record, no attempt is written; a missed answer (partly or
    no on a next step, why step or assumption) queues a ``reader_formative``
    learner text while ``reader_formative.enabled`` is on."""

    vault, repository = _require_active(ctx)
    try:
        # The self-check and its learner-text job are one write (review F7).
        row, formative_job = AR.record_action(
            vault, repository, question_id=params.question_id, action=params.action,
            response_md=params.response, self_check=params.self_check,
        )
    except RQC.ReaderQuickCheckError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    if params.action == "self_checked":
        _event(repository, "reader_action_invoked", {
            "event": "active_question_answered", "extraction_id": row["extraction_id"],
            "style": row.get("question_style"), "self_check": row.get("self_check"),
            "answered": bool(str(row.get("response_md") or "").strip()),
        }, subject_id=row["extraction_id"])
        if formative_job is not None:
            ctx.post_attempt_worker.notify()
    return versioned({"question": _question_payload(vault, repository, row), "formative_job_id": formative_job})


class ReaderReconstructInput(ParamsModel):
    question_id: str
    learning_object_id: str | None = None


@method("reader.reconstruct", ReaderReconstructInput)
def reader_reconstruct(ctx: SidecarContext, params: ReaderReconstructInput) -> dict[str, Any]:
    """"Reconstruct this later": the escalated item and its ``test_me_later`` commitment (idempotent)."""

    vault, repository = _require_active(ctx)
    row = repository.get_reader_authored_question(params.question_id)
    if row is None:
        raise SidecarError("not_found", "Unknown question.")
    learning_object_id = params.learning_object_id or _question_payload(vault, repository, row).get(
        "escalation_learning_object_id")
    if not learning_object_id:
        raise SidecarError(
            "no_learning_object",
            "This passage is not linked to a learning objective yet, so it can't become practice.",
        )
    try:
        result = AR.reconstruct_commit(vault.root, repository, question_id=params.question_id,
                                       learning_object_id=str(learning_object_id))
    except AR.ReconstructUndone as exc:
        raise SidecarError("reconstruct_undone", str(exc)) from exc
    except (AR.ActiveReadingError, RQC.ReaderQuickCheckError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    _event(repository, "reader_action_invoked", {
        "event": "reconstruct_committed", "extraction_id": row["extraction_id"],
        "practice_item_id": result["practice_item_id"], "commitment_id": result["commitment_id"],
    }, subject_id=row["extraction_id"])
    # The escalated card is vault YAML; reload so it schedules.
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    refreshed = repository.get_reader_authored_question(params.question_id) or row
    return versioned({"practice_item_id": result["practice_item_id"], "commitment_id": result["commitment_id"],
                      "due_hint": result["due_hint"], "question": _question_payload(vault, repository, refreshed)})


class ReaderReconstructUndoInput(ParamsModel):
    question_id: str


@method("reader.reconstruct_undo", ReaderReconstructUndoInput)
def reader_reconstruct_undo(ctx: SidecarContext, params: ReaderReconstructUndoInput) -> dict[str, Any]:
    """Undo "reconstruct this later": its commitment and its item are retired."""

    vault, repository = _require_active(ctx)
    try:
        result = AR.reconstruct_undo(vault.root, repository, question_id=params.question_id, vault=vault)
    except AR.ActiveReadingError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    row = repository.get_reader_authored_question(params.question_id)
    if row is not None:
        _event(repository, "reader_action_invoked", {
            "event": "reconstruct_undone", "extraction_id": row["extraction_id"],
            "practice_item_id": result["practice_item_id"], "commitment_id": result["commitment_id"],
        }, subject_id=row["extraction_id"])
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    refreshed = repository.get_reader_authored_question(params.question_id)
    return versioned({"practice_item_id": result["practice_item_id"], "commitment_id": result["commitment_id"],
                      "question": _question_payload(vault, repository, refreshed) if refreshed else None})
