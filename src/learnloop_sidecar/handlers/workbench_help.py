"""Reader workbench RW2b RPCs: "Check my work" and the help ladder (spec_reader_workbench_v1 §5.2-5.6).

The adapter around :mod:`learnloop.workbench.check` (the check) and the
one hint service's workbench surface (:mod:`learnloop.hints.service`,
:mod:`learnloop.hints.workbench`, adaptive hints H3). Desktop only (pinned in
``tests/test_mobile_allowlist.py``); every RPC refuses ``help_disabled``
before reading or writing anything while ``workbench.help_enabled`` (or
``workbench.enabled``) is off, so the RW2a workbench is exactly as before.

**Never on the request path.** A check and a hint take seconds and the
sidecar is serial, so (as H2a's hints and RW4a's library asks)
``workbench.check``, ``workbench.suggest_help`` and ``workbench.request_help``
answer at once with a job and ``workbench.help_job`` reads it.

**Shown when delivered.** The read that returns a ready check or hint
DELIVERS it (:func:`learnloop.hints.workbench.deliver_workbench`, inside H2a's
delivery and fence): its prepared ``help_assists`` row becomes shown, and a
hint's key overlap writes its ``tutor_answer`` reveal with basis
``workbench_hint:<kind>:L<n>`` in the same transaction (the authored kind
exempt, H2b's ruling). A row stamped by its problem's submit is never
delivered after; a row written later and shown while the submit grades is
counted by the attempt's transactional refold (fix round 1, F1); none is
shown once the attempt commits (G-H3). Every read re-checks the switches
(F13).
A delivered hint in the Reader starts the bridge to the book in the background
(``workbench.bridge_enabled``), which never delays the hint.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from typing import Any, Callable, Literal

from pydantic import Field

from learnloop.hints import service as hint_service
from learnloop.hints import workbench as hint_workbench
from learnloop.hints.service import HintRequestError, HintRequestV1, adaptive_enabled
from learnloop.reader import workbench as WB
from learnloop.workbench import check as check_module
from learnloop.workbench import ladder as help_module
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.hints import HintJobs, _as_sidecar_error
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
WORKBENCH_HELP_RPCS: tuple[str, ...] = (
    "workbench.check",
    "workbench.suggest_help",
    "workbench.request_help",
    "workbench.help_job",
    "workbench.cancel_help",
    "workbench.answer_discriminating",
    "workbench.set_help_style",
    "workbench.help_state",
)
CHECK, SUGGEST, HINT, BRIDGE = "check", "suggest", "hint", "bridge"


@dataclass
class _JobMeta:
    kind: str
    session_id: str
    practice_item_id: str


def _jobs(ctx: SidecarContext) -> HintJobs:
    jobs = getattr(ctx, "workbench_help_jobs", None)
    if jobs is None:
        jobs = HintJobs()
        ctx.workbench_help_jobs = jobs  # type: ignore[attr-defined]
    return jobs


def _meta(ctx: SidecarContext) -> dict[str, _JobMeta]:
    meta = getattr(ctx, "workbench_help_meta", None)
    if meta is None:
        meta = {}
        ctx.workbench_help_meta = meta  # type: ignore[attr-defined]
    return meta


def _require(ctx: SidecarContext, session_id: str, *, bound: bool = True, open_: bool = True):
    vault, repository = ctx.require_vault()
    if not help_module.help_enabled(vault):
        raise SidecarError("help_disabled", "Checks and help are switched off (workbench.help_enabled = false).")
    try:
        session = WB.session_row(repository, session_id)
    except WB.WorkbenchError as exc:
        raise SidecarError(exc.code, exc.message) from exc
    if open_ and session["status"] != "open":
        raise SidecarError("not_open", "This problem isn't open; reopen it to keep working.")
    item = None
    if bound:
        item_id = session.get("practice_item_id")
        item = vault.practice_items.get(item_id) if item_id else None
        if item is None:
            raise SidecarError("not_bound", "Check my work and Help are available once setup finishes.")
    return vault, repository, session, item


def _start(ctx: SidecarContext, kind: str, session: dict[str, Any], item: Any,
           work: Callable[[Any, Callable[[], bool]], dict[str, Any]]) -> dict[str, Any]:
    job = _jobs(ctx).start(ctx, item.id, work)
    _meta(ctx)[job.job_id] = _JobMeta(kind, str(session["id"]), item.id)
    return _payload(ctx, job.job_id)


def _diagnostic_block(repository: Any, item: Any) -> bool:
    from learnloop_sidecar.handlers.practice import _in_diagnostic_block

    return _in_diagnostic_block(repository, item)


def _queue_stuck(ctx: SidecarContext, vault: Any, repository: Any, session_id: str) -> None:
    """In-session updates (§5.2): the stuck steps' newest text to learner-text gaps."""

    try:
        if help_module.queue_stuck_texts(vault, repository, session_id):
            ctx.post_attempt_worker.notify()
    except Exception as exc:  # noqa: BLE001 - learner-text gaps never reach the workbench
        log_event("workbench_text_enqueue_failed", session_id=session_id, error=type(exc).__name__)


def _queue_text(ctx: SidecarContext, vault: Any, repository: Any, source_id: str) -> None:
    try:
        from learnloop.diagnosis.text_gaps.jobs import enqueue_workbench_text

        if enqueue_workbench_text(vault, repository, source_id=source_id):
            ctx.post_attempt_worker.notify()
    except Exception as exc:  # noqa: BLE001 - learner-text gaps never reach the workbench
        log_event("workbench_text_enqueue_failed", source_id=source_id, error=type(exc).__name__)


# -- Check my work -------------------------------------------------------------------------


class WorkbenchCheckInput(ParamsModel):
    session_id: str = Field(min_length=1)


@method("workbench.check", WorkbenchCheckInput)
def workbench_check(ctx: SidecarContext, params: WorkbenchCheckInput) -> dict[str, Any]:
    """"Check my work" (``Ctrl+K``, a job): the steps' verdicts, counted as one hint once shown."""

    vault, repository, session, item = _require(ctx, params.session_id)
    if _diagnostic_block(repository, item):
        return _immediate({"status": "refused", "reason": "diagnostic_block",
                           "message": "Checks are off during a diagnostic check."})
    _queue_stuck(ctx, vault, repository, params.session_id)
    steps = help_module.live_workbench_steps(repository, params.session_id)
    client = getattr(ctx, "workbench_check_client", None)
    sandbox_run = getattr(ctx, "workbench_sandbox_run", None)
    submission = WB.submission_id_for(params.session_id)

    def work(worker_repo: Any, cancelled: Callable[[], bool]) -> dict[str, Any]:
        result = check_module.run_check(vault, worker_repo, workbench_session_id=params.session_id,
                                        submission_id=submission, item=item, steps=steps, client=client,
                                        sandbox_run=sandbox_run, cancelled=cancelled)
        return {"status": result.status, "assist_id": result.assist_id, "reason": result.reason,
                "message": result.message}

    return _start(ctx, CHECK, session, item, work)


# -- the ladder ---------------------------------------------------------------------------


class SuggestHelpInput(ParamsModel):
    session_id: str = Field(min_length=1)
    #: The step Help opened below (its chain id), when one has focus.
    focused_step_id: str | None = None


def _hint_clients(ctx: SidecarContext) -> tuple[Any, Any, Any]:
    writer = getattr(ctx, "hint_writer_client", None)
    chooser = getattr(ctx, "hint_chooser_client", None)
    factory = (lambda: chooser) if chooser is not None else None
    return writer, factory, getattr(ctx, "hint_seed", None)


def _context_labels(context: hint_workbench.WorkbenchHintContext) -> dict[str, Any]:
    return {"about_step_id": context.about, "about_step": context.number(context.about),
            "continue_from_step_id": context.continue_from,
            "continue_from_step": context.number(context.continue_from),
            "first_questionable_step": context.number(context.first_questionable)}


@method("workbench.suggest_help", SuggestHelpInput)
def suggest_help(ctx: SidecarContext, params: SuggestHelpInput) -> dict[str, Any]:
    """Help opened (``Ctrl+H``): the five rungs at once, and the suggested
    rung when the chooser returns (a job; the ladder works without it)."""

    vault, repository, session, item = _require(ctx, params.session_id)
    if not adaptive_enabled(vault.config):
        return _immediate({"status": "disabled", "message": "Hints are off (hints.adaptive_enabled = false)."})
    if _diagnostic_block(repository, item):
        return _immediate({"status": "refused", "reason": "diagnostic_block",
                           "message": "Hints are off during a diagnostic check."})
    _queue_stuck(ctx, vault, repository, params.session_id)
    context = help_module.hint_context(vault, repository, session, focused_step=params.focused_step_id)
    level = help_module.fallback_level(repository, params.session_id, context.about)
    _writer, factory, seed = _hint_clients(ctx)

    def work(worker_repo: Any, _cancelled: Callable[[], bool]) -> dict[str, Any]:
        from learnloop.hints.state import assemble_state
        from learnloop.ids import new_ulid

        record = hint_workbench.current_map_for(vault, worker_repo, item.id)
        submission = WB.submission_id_for(params.session_id)
        state = assemble_state(vault, worker_repo, item, session_id=params.session_id, submission_id=submission,
                               work_md=context.work_md(), map_record=record, map_loaded=True)
        hint_workbench.apply_context(state, context)
        suggestion = hint_workbench.suggest(
            vault, worker_repo, state, context, item, fallback_level=level, assist_id="ha_" + new_ulid(),
            client_factory=factory or (lambda: hint_service.default_chooser_client(vault)), seed=seed,
            envelope=hint_service.hints_envelope(vault, worker_repo))
        WB.log_help_offered(worker_repo, params.session_id, about_step_id=context.about,
                            offered_level=suggestion.level, kind=suggestion.kind, chooser=suggestion.chooser,
                            suggestion_id=suggestion.judgment_id)
        return {"status": "ready", "suggestion": suggestion.as_dict(), "steps": _context_labels(context)}

    return _start(ctx, SUGGEST, session, item, work)


class RequestHelpInput(ParamsModel):
    session_id: str = Field(min_length=1)
    request: Literal["more", "feedback", "book_way", "smaller_step"] = "more"
    #: The rung taken (1-5) on "more"; absent on a reply or a pick.
    taken_level: int | None = Field(default=None, ge=1, le=5)
    #: The rung the ladder suggested (logged; §5.5).
    offered_level: int | None = Field(default=None, ge=1, le=5)
    #: The suggestion's ``hint_choice`` judgment (its draw), when it landed.
    suggestion_id: str | None = None
    focused_step_id: str | None = None
    answered_assist_id: str | None = None
    feedback_shortcut: Literal["not_where_stuck", "too_big", "learner_route", "notation"] | None = None
    feedback_text: str | None = Field(default=None, max_length=4000)
    #: "That's not where I'm stuck": the picked step (its chain id).
    feedback_step_id: str | None = None
    seconds_on_item: float | None = Field(default=None, ge=0)


@method("workbench.request_help", RequestHelpInput)
def request_help(ctx: SidecarContext, params: RequestHelpInput) -> dict[str, Any]:
    """Take a rung (choose and take are separate keys on the ladder), reply
    to a hint or pick the book's way or a smaller step (a job)."""

    vault, repository, session, item = _require(ctx, params.session_id)
    if not adaptive_enabled(vault.config):
        return _immediate(hint_service.HintResultV1(
            status=hint_service.DISABLED, reason="adaptive_disabled",
            message="Hints are off (hints.adaptive_enabled = false).").as_dict())
    if _diagnostic_block(repository, item):
        return _immediate(hint_service.HintResultV1(
            status=hint_service.REFUSED, reason="diagnostic_block",
            message="Hints are off during a diagnostic check.").as_dict())
    _queue_stuck(ctx, vault, repository, params.session_id)
    answered_row = None
    if params.answered_assist_id:
        from contextlib import closing

        from learnloop.db.connection import connect
        from learnloop.db.stores.help_assists import assist as assist_row

        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            answered_row = assist_row(connection, params.answered_assist_id)
        if answered_row is None or answered_row.get("workbench_session_id") != params.session_id:
            raise SidecarError("validation_error", "The answered hint is not a hint of this problem.")
    feedback_step = params.feedback_step_id if params.feedback_shortcut == "not_where_stuck" else None
    context = help_module.hint_context(
        vault, repository, session, focused_step=params.focused_step_id, feedback_step=feedback_step,
        answered=answered_row, offered_level=params.offered_level, suggestion_id=params.suggestion_id)
    if params.request == "feedback" and params.feedback_step_id and feedback_step is None:
        # The picked step is recorded on every reply (§5.7), and moves the
        # hint only for "that's not where I'm stuck".
        context = replace(context, feedback_step=params.feedback_step_id)
    request = HintRequestV1(
        practice_item_id=item.id, session_id=params.session_id,
        submission_id=WB.submission_id_for(params.session_id), surface=hint_workbench.SURFACE,
        work_md=context.work_md(), request=params.request, answered_assist_id=params.answered_assist_id,
        feedback_shortcut=params.feedback_shortcut, feedback_text=params.feedback_text,
        taken_level=params.taken_level if params.request == "more" else None,
        seconds_on_item=params.seconds_on_item, workbench=context)
    writer, factory, seed = _hint_clients(ctx)
    labels = _context_labels(context)

    verifier = check_module.hint_claim_verifier(vault, item, sandbox_run=getattr(ctx, "workbench_sandbox_run", None))

    def work(worker_repo: Any, cancelled: Callable[[], bool]) -> dict[str, Any]:
        result = hint_service.request_hint(vault, worker_repo, request, writer_client=writer,
                                           chooser_client_factory=factory, seed=seed, cancelled=cancelled,
                                           claim_verifier=verifier)
        payload = result.as_dict()
        # Reader §5.3 (F14): the hint's claims as checked, each labelled.
        payload["claims"] = help_module.served_claims(worker_repo, result.assist_id)
        payload["steps"] = labels
        payload["step_line"] = hint_workbench.step_labels(context)["line"]
        if result.status == hint_service.UNAVAILABLE and result.reason in help_module.WRITER_DOWN_REASONS:
            # UX §5.6: a capped or unavailable writer says so; rung 3 still
            # serves the item's own hints while they last.
            payload["message"] = help_module.unavailable_message(result.reason, authored_left=bool(item.hints))
        if request.request == "feedback" and (request.feedback_text or "").strip() and result.assist_id:
            _queue_text(ctx, vault, worker_repo, str(result.assist_id))
        return payload

    return _start(ctx, HINT, session, item, work)


# -- reading a job (the read that returns a ready check or hint delivers it) ---------------


class HelpJobInput(ParamsModel):
    job_id: str = Field(min_length=1)


def _immediate(result: dict[str, Any]) -> dict[str, Any]:
    return versioned({"job_id": None, "state": "done", "result": to_camel(result)})


class _RevealNotRecorded(Exception):
    pass


def _deliver(ctx: SidecarContext, meta: _JobMeta, assist_id: str, *, hint: bool) -> str:
    """Show a prepared workbench row; a hint's key overlap goes to the reveal
    ledger in the same transaction (a failed reveal shows nothing)."""

    from learnloop.attempts.reveal_ledger import record_reveal_strict, reveal_episode_id

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(meta.practice_item_id)
    try:
        with repository.atomic():
            outcome, row = hint_workbench.deliver_workbench(repository, assist_id, item=item)
            if hint and outcome == hint_service.SHOWN and row is not None and item is not None \
                    and row.get("hint_kind") and row.get("level") \
                    and not hint_service.reveal_exempt(str(row["hint_kind"])):
                try:
                    amount = hint_service.reveal_amount(item, hint_service.shown_text(item, row))
                    record_reveal_strict(
                        repository, practice_item_id=item.id, learning_object_id=item.learning_object_id,
                        remediation_episode_id=reveal_episode_id(repository, item.id, strict=True),
                        source_kind="tutor_answer", amount=amount,
                        basis=hint_workbench.reveal_basis(str(row["hint_kind"]), int(row["level"])))
                except Exception as exc:  # noqa: BLE001 - any failure: the hint is not shown
                    raise _RevealNotRecorded(type(exc).__name__) from exc
    except _RevealNotRecorded as exc:
        log_event("workbench_hint_reveal_failed", practice_item_id=meta.practice_item_id, error=str(exc))
        return hint_service.REVEAL_NOT_RECORDED
    return outcome


def _check_payload(ctx: SidecarContext, meta: _JobMeta, result: dict[str, Any]) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    steps = help_module.live_workbench_steps(repository, meta.session_id)
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import assist as assist_row

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = assist_row(connection, str(result["assist_id"])) if result.get("assist_id") else None
    view = check_module.check_view(row, steps) if row is not None else None
    return {**result, "check": view}


def _payload(ctx: SidecarContext, job_id: str) -> dict[str, Any]:
    job = _jobs(ctx).get(job_id)
    meta = _meta(ctx).get(job_id)
    _vault, repository = ctx.require_vault()
    if job is None or meta is None or job.sqlite_path != str(repository.sqlite_path):
        raise SidecarError("not_found", "That request is no longer kept; ask again.")
    base = {"job_id": job.job_id, "kind": meta.kind}
    with job.lock:
        if meta.kind == BRIDGE and not job.delivered and not bool(_vault.config.workbench.bridge_enabled):
            # F13: the bridge's switch went off while it searched.
            job.cancelled = True
        if job.cancelled and not job.delivered:
            return versioned({**base, "state": "cancelled", "result": None})
        if not job.done.is_set():
            return versioned({**base, "state": "pending", "result": None})
        if job.error is not None:
            raise job.error
        result = dict(job.result or {})
        deliverable = (meta.kind == CHECK and result.get("status") == "ready") or (
            meta.kind == HINT and result.get("status") == hint_service.READY)
        if deliverable and not job.delivered and job.refused is None:
            outcome = _deliver(ctx, meta, str(result["assist_id"]), hint=meta.kind == HINT)
            if outcome == hint_service.SHOWN:
                job.delivered = True
                if meta.kind == HINT:
                    result["bridge_job_id"] = _start_bridge(ctx, meta, str(result["assist_id"]))
                    job.result = {**(job.result or {}), "bridge_job_id": result["bridge_job_id"]}
            elif outcome == hint_service.REVEAL_NOT_RECORDED:
                result = hint_service.undelivered_result(str(result["assist_id"]), outcome).as_dict()
            else:
                job.refused = outcome
        if job.refused is not None:
            result = hint_service.undelivered_result(str(result.get("assist_id") or ""), job.refused).as_dict()
        result["shown"] = job.delivered if meta.kind in (CHECK, HINT) else None
        if meta.kind == CHECK and (job.delivered or result.get("status") == "unchanged"):
            result = _check_payload(ctx, meta, result)
        if meta.kind == BRIDGE and result.get("status") == "ready" and not job.delivered:
            job.delivered = _show_bridge(repository, str(result["assist_id"]))
            result["shown"] = job.delivered
        if meta.kind == CHECK and job.delivered:
            # The record line and footer name the check (G62).
            result["record"] = _record(ctx, meta.session_id)
        if meta.kind == HINT and job.delivered:
            result["record"] = _record(ctx, meta.session_id)
    return versioned({**base, "state": "done", "result": to_camel(result)})


def _record(ctx: SidecarContext, session_id: str) -> dict[str, Any]:
    from learnloop_sidecar.handlers.workbench import _view

    vault, repository = ctx.require_vault()
    return _view(vault, repository, session_id)["record"]


@method("workbench.help_job", HelpJobInput)
def help_job(ctx: SidecarContext, params: HelpJobInput) -> dict[str, Any]:
    """A check, suggestion, hint or bridge job's state, at once (never a wait).

    The switches are read again here (fix round 1, F13): with
    ``workbench.help_enabled`` off (a reload while a job was pending) the job
    is cancelled before anything is delivered, counted or bridged, and the
    read refuses ``help_disabled``; a bridge waiting while
    ``workbench.bridge_enabled`` went off is cancelled, never shown."""

    vault, _repository = ctx.require_vault()
    if not help_module.help_enabled(vault):
        job = _jobs(ctx).get(params.job_id)
        if job is not None:
            with job.lock:
                if not job.delivered:
                    job.cancelled = True
        raise SidecarError("help_disabled", "Checks and help are switched off (workbench.help_enabled = false).")
    return _payload(ctx, params.job_id)


@method("workbench.cancel_help", HelpJobInput)
def cancel_help(ctx: SidecarContext, params: HelpJobInput) -> dict[str, Any]:
    """Cancel a check or hint before it is shown: never delivered, its row
    stays unshown and counts nothing. A delivered one stays."""

    job = _jobs(ctx).get(params.job_id)
    if job is None:
        raise SidecarError("not_found", "That request is no longer kept.")
    with job.lock:
        if job.delivered:
            return versioned({"job_id": job.job_id, "state": "done", "cancelled": False, "reason": "already_shown"})
        job.cancelled = True
    return versioned({"job_id": job.job_id, "state": "cancelled", "cancelled": True, "reason": None})


# -- the bridge to the book ------------------------------------------------------------------


def _start_bridge(ctx: SidecarContext, meta: _JobMeta, hint_assist_id: str) -> str | None:
    """"Compare with the book" (§5.2 bridging): in the background after a
    hint is shown in the Reader, never delaying it."""

    vault, repository = ctx.require_vault()
    if not bool(vault.config.workbench.bridge_enabled):
        return None
    try:
        session = WB.session_row(repository, meta.session_id)
    except WB.WorkbenchError:
        return None
    item = vault.practice_items.get(meta.practice_item_id)
    if session.get("origin") != "reader" or item is None:
        return None
    if check_module.session_calls(repository, meta.session_id) >= int(vault.config.workbench.max_calls_per_session):
        return None
    provider = getattr(ctx, "workbench_bridge_provider", None)

    def work(worker_repo: Any, _cancelled: Callable[[], bool]) -> dict[str, Any]:
        from learnloop.workbench.bridge import bridge_for_hint

        # F9: the search is one of the problem's calls (reserved before it
        # runs) and its metered calls join the workbench's daily envelope.
        return bridge_for_hint(vault, worker_repo, workbench_session_id=meta.session_id,
                               hint_assist_id=hint_assist_id, item=item, provider=provider,
                               envelope=check_module.daily_envelope(vault, worker_repo),
                               max_calls=int(vault.config.workbench.max_calls_per_session))

    job = _jobs(ctx).start(ctx, item.id, work)
    _meta(ctx)[job.job_id] = _JobMeta(BRIDGE, meta.session_id, item.id)
    return job.job_id


def _show_bridge(repository: Any, assist_id: str) -> bool:
    from learnloop.clock import utc_now_iso
    from learnloop.db.stores.help_assists import mark_bridge_shown

    with repository.atomic():
        return mark_bridge_shown(repository.connection(), assist_id, shown_at=utc_now_iso())


# -- the discriminating answer, the help style, the restored state --------------------------


class WorkbenchDiscriminateInput(ParamsModel):
    session_id: str = Field(min_length=1)
    question_assist_id: str = Field(min_length=1)
    answer_md: str = Field(max_length=2000)


@method("workbench.answer_discriminating", WorkbenchDiscriminateInput)
def answer_discriminating(ctx: SidecarContext, params: WorkbenchDiscriminateInput) -> dict[str, Any]:
    """The learner's answer to a question before a hint (§5.8): an assist row
    on the question's step, never a step and never the submitted answer; it
    moves no posterior and writes no probe observation."""

    vault, repository, session, item = _require(ctx, params.session_id)
    try:
        recorded = hint_service.record_discriminate_answer(
            vault, repository, practice_item_id=item.id, session_id=params.session_id,
            submission_id=WB.submission_id_for(params.session_id), question_assist_id=params.question_assist_id,
            answer_md=params.answer_md, surface=hint_workbench.SURFACE, workbench_session_id=params.session_id)
    except HintRequestError as exc:
        raise SidecarError(exc.code, str(exc), details={"field": exc.field} if exc.field else None) from exc
    if recorded.get("assist_id"):
        _queue_text(ctx, vault, repository, str(recorded["assist_id"]))
    return versioned(to_camel(recorded))


class WorkbenchHelpStyleInput(ParamsModel):
    session_id: str = Field(min_length=1)
    help_style: Literal["let_me_struggle", "balanced", "guide_me"] | None = None


@method("workbench.set_help_style", WorkbenchHelpStyleInput)
def set_help_style(ctx: SidecarContext, params: WorkbenchHelpStyleInput) -> dict[str, Any]:
    """The header's help style for this problem only (D31); null follows the
    stored preference again. It changes only the suggestion."""

    vault, repository, _session, _item = _require(ctx, params.session_id, bound=False)
    try:
        session = WB.set_help_style(repository, params.session_id, params.help_style)
    except WB.WorkbenchError as exc:
        raise SidecarError(exc.code, exc.message) from exc
    return versioned({"help_style": session.get("help_style"), "stored_help_style": vault.config.hints.help_style})


class WorkbenchHelpStateInput(ParamsModel):
    session_id: str = Field(min_length=1)


@method("workbench.help_state", WorkbenchHelpStateInput)
def help_state(ctx: SidecarContext, params: WorkbenchHelpStateInput) -> dict[str, Any]:
    """What a resumed problem restores (§5.1 "the same assistance history"):
    the last shown check and every shown hint under its step."""

    vault, repository, session, _item = _require(ctx, params.session_id, bound=False, open_=False)
    steps = help_module.live_workbench_steps(repository, params.session_id)
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import workbench_rows

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = workbench_rows(connection, params.session_id)
    check = help_module.last_shown_check(rows)
    return versioned(to_camel({
        "check": check_module.check_view(check, steps) if check is not None else None,
        "hints": help_module.hint_views(vault, repository, params.session_id),
        "help_style": session.get("help_style"),
        "stored_help_style": vault.config.hints.help_style,
        "hints_enabled": adaptive_enabled(vault.config),
    }))


__all__ = ["WORKBENCH_HELP_RPCS"]
