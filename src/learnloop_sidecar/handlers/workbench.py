"""Reader workbench RW2a RPCs: the resumable scratchpad (spec_reader_workbench_v1 §5.1).

The adapter around :mod:`learnloop.reader.workbench`. It adds what needs the
sidecar: the exercise import a selected problem waits on (enqueued with the
same code as ``reader.import_exercise``, bound when its job lands), the
practice session a submit runs in, and the submit itself, which goes through
the one submit implementation (``practice.submit_attempt_on``) with the
workbench's entry surface, so it is graded, diagnosed and admitted by the one
eligibility decision exactly like every other answer.

Every RPC refuses ``workbench_disabled`` while ``workbench.enabled`` is off,
before reading or writing anything. Desktop only (spec D20).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from learnloop.attempts.stuck import stuck_attempt_type
from learnloop.reader import workbench as WB
from learnloop.tutor.tutor_qa import hint_equivalents_for_submission
from learnloop_sidecar.context import SidecarContext, session_snapshot
from learnloop_sidecar.dto import ParamsModel, to_camel
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

T = TypeVar("T")

#: Import job statuses that are still running (``reader.exercise_import_status``).
_IMPORT_RUNNING = frozenset({"queued", "running", "blocked", "pending"})


def _require(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not WB.workbench_enabled(vault):
        raise SidecarError("workbench_disabled", "The workbench is switched off (workbench.enabled = false).")
    return vault, repository


def _run(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    try:
        return fn(*args, **kwargs)
    except WB.WorkbenchError as exc:
        raise SidecarError(exc.code, exc.message, details=to_camel(exc.details)) from exc


def _question_hints(vault, repository, session: dict[str, Any]) -> int:
    """The tutor questions the submit's existing fold will add (G62)."""

    item_id = session.get("practice_item_id")
    if not item_id or session.get("status") != "open" or item_id not in vault.practice_items:
        return 0
    practice_session = session.get("practice_session_id")
    if not practice_session:
        recent = repository.most_recent_open_session()
        practice_session = recent["id"] if recent else None
    if not practice_session:
        return 0
    try:
        return int(hint_equivalents_for_submission(repository, item_id, practice_session))
    except Exception:  # noqa: BLE001 - a display line never fails a read
        return 0


def _source_id(repository, extraction_id: str | None) -> str | None:
    if not extraction_id:
        return None
    from learnloop_sidecar.handlers.reader import _source_id_for_extraction

    try:
        return _source_id_for_extraction(repository, extraction_id)
    except Exception:  # noqa: BLE001 - an unknown extraction has no source
        return None


def _ensure_contract(vault, repository, session_id: str) -> None:
    """Snapshot the assessment contract a bound session shows, once (the
    practice screen's serve does the same), so the submit grades the problem
    against what the learner saw even if the item changes before it."""

    row = _run(WB.session_row, repository, session_id)
    item_id = row.get("practice_item_id")
    if not item_id or row.get("assessment_contract_version_id") or row["status"] == "submitted":
        return
    item = vault.practice_items.get(item_id)
    if item is None:
        return
    from learnloop.learner.assessment_contracts import CANONICAL_STATE_VERSIONS, snapshot_for_presentation

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    try:
        version_id = snapshot_for_presentation(repository, vault, item)
    except Exception:  # noqa: BLE001 - without a snapshot the submit takes the current one, as before
        return
    _run(WB.ensure_contract, repository, session_id, version_id)


def _presentation(vault, repository, row: dict[str, Any]) -> dict[str, Any] | None:
    """The bound problem as the learner must see it to answer it: the item's
    presentation blocks (a required method's instruction, a shared stimulus,
    an error hunt's worked solution), with the statement and required method
    the session's contract froze. None before binding: the verbatim stem is
    the provisional display."""

    item_id = row.get("practice_item_id")
    item = vault.practice_items.get(item_id) if item_id else None
    if item is None:
        return None
    from learnloop.vault.required_method import method_instruction
    from learnloop_sidecar.handlers.serializers import item_presentation

    try:
        presentation = item_presentation(item)
    except SidecarError:
        return None
    contract = None
    if row.get("assessment_contract_version_id"):
        stored = repository.fetch_assessment_contract_version(row["assessment_contract_version_id"])
        contract = (stored or {}).get("contract") or None
    if not contract:
        return presentation
    instruction = method_instruction(contract.get("required_method"))
    blocks: list[dict[str, Any]] = []
    for block in presentation["blocks"]:
        if block["kind"] == "required_method_instruction":
            continue
        if block["kind"] == "prompt":
            blocks.append({**block, "markdown": str(contract.get("prompt") or block["markdown"])})
            if instruction is not None:
                blocks.append({"kind": "required_method_instruction", "markdown": instruction, "label": None})
            continue
        blocks.append(block)
    return {**presentation, "blocks": blocks}


def _view(vault, repository, session_id: str, *, parts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    row = _run(WB.session_row, repository, session_id)
    view = _run(
        WB.session_view, repository, session_id,
        question_hints=_question_hints(vault, repository, row),
        server_hints=_carried_server_hints(repository, row),
        extra={"source_id": _source_id(repository, row.get("extraction_id")), "parts": parts,
               "presentation": _presentation(vault, repository, row)},
    )
    return to_camel(view)


def _carried_server_hints(repository, session: dict[str, Any]) -> int:
    """The answer box's shown server hints carried into the problem (H2b
    review F1), every level: what the record line names before Submit."""

    item_id = session.get("practice_item_id")
    if not item_id or session.get("status") != "open":
        return 0
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import carried_fold

    try:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                                  ).fetchone() is None:
                return 0
            return carried_fold(connection, practice_item_id=str(item_id), workbench_session_id=str(session["id"]))[2]
    except Exception:  # noqa: BLE001 - a display line never fails a read
        return 0


def _link_carried_hints(repository, session_id: str, params: "WorkbenchOpenInput") -> None:
    """Link the answer box's shown server hints of the named submission to
    the problem (H2b review F1). Only on the item the problem is bound to;
    the rows are the server's own record of what it showed."""

    if not params.carried_submission_id or not params.carried_session_id:
        return
    row = _run(WB.session_row, repository, session_id)
    item_id = row.get("practice_item_id")
    if not item_id or row.get("status") != "open":
        return
    from learnloop.db.stores.help_assists import link_to_workbench

    with repository.atomic():
        connection = repository.connection()
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                              ).fetchone() is None:
            return
        link_to_workbench(connection, practice_item_id=str(item_id), session_id=params.carried_session_id,
                          submission_id=params.carried_submission_id.strip(), workbench_session_id=session_id)


def _answer(payload: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, **payload}


# -- the exercise import a selected problem waits on (UX S2) ----------------------------------------


def _enqueue_import(ctx: SidecarContext, vault, repository, request: dict[str, Any]) -> str:
    """Queue the exercise import exactly as ``reader.import_exercise`` does."""

    from learnloop.reader import reader_dialogue as RD
    from learnloop_sidecar.handlers.reader import ReaderImportExerciseInput, enqueue_exercise_import

    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader is switched off, so this problem cannot be set up.")
    params = ReaderImportExerciseInput.model_validate(request)
    return enqueue_exercise_import(ctx, vault, repository, params)


def _import_job(ctx: SidecarContext, repository, batch_id: str) -> dict[str, Any] | None:
    """The import batch's job, reloading the vault once when it completed (as
    ``reader.exercise_import_status`` does), so its items schedule."""

    jobs = repository.ingest_jobs_for_batch(batch_id)
    if not jobs:
        return None
    job = jobs[0]
    if job.get("status") == "completed" and ctx.ingest_jobs.needs_reload(job["id"]):
        ctx.reload(maintenance=False)
        ctx.ingest_jobs.mark_reloaded(job["id"])
    return {"status": job.get("status"), "result": job.get("result"), "error": job.get("error"),
            "message": job.get("message")}


def _job_parts(job: dict[str, Any]) -> list[dict[str, Any]]:
    result = to_camel(job.get("result") or {})
    parts = []
    for item in result.get("items") or []:
        item_id = item.get("practiceItemId")
        if item_id:
            parts.append({"practiceItemId": item_id, "title": item.get("title") or "", "prompt": item.get("prompt") or ""})
    return parts


def _job_error(job: dict[str, Any]) -> str:
    error = job.get("error")
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    return str(job.get("message") or "Setting up this exercise did not finish.")


def _start_import(ctx: SidecarContext, vault, repository, request: dict[str, Any]) -> tuple[str | None, str | None]:
    try:
        return _enqueue_import(ctx, vault, repository, request), None
    except SidecarError as exc:
        return None, exc.message


# -- inputs -------------------------------------------------------------------------------------------


class WorkbenchOpenInput(ParamsModel):
    origin: str
    entry: str
    #: Resume this session on the asking surface ("resume your steps", the
    #: ``✎`` mark): reopened when abandoned, moved when on another surface.
    session_id: str | None = None
    #: The answer box's hints the learner saw before working in steps.
    carried_hints: int = 0
    #: A book a problem the learner left for the answer box counted (review F2).
    carried_book: bool = False
    #: Adaptive hints H2b (review F1): the answer box's submission the work
    #: moves from (its key and practice session). The hints the hint service
    #: showed for it go with the work: the server links its own shown rows
    #: (never a count the client sends) and the problem's submit folds them.
    carried_submission_id: str | None = None
    carried_session_id: str | None = None
    #: The serve the problem answers ("check me", the practice screen's
    #: serve), kept on the session so a resume still submits as it (F13).
    #: One pair: naming either replaces both, nulls included; naming neither
    #: keeps the pair the session holds (F15).
    scheduler_candidate_id: str | None = None
    plan_presentation_id: str | None = None
    stem_md: str | None = None
    practice_item_id: str | None = None
    extraction_id: str | None = None
    span_ids: list[str] = []
    parent_session_id: str | None = None
    source_visible: bool | None = None
    client_idempotency_key: str | None = None
    #: A selected problem that is not an item yet: the reader.import_exercise
    #: request the workbench enqueues and binds when it lands.
    import_request: dict[str, Any] | None = None


class WorkbenchSessionInput(ParamsModel):
    session_id: str


class WorkbenchSaveStepInput(ParamsModel):
    session_id: str
    client_idempotency_key: str
    op: str
    step_id: str | None = None
    after_step_id: str | None = None
    kind: str = "step"
    body_md: str | None = None


class WorkbenchSetBookInput(ParamsModel):
    session_id: str
    visible: bool


class WorkbenchBindInput(ParamsModel):
    session_id: str
    practice_item_id: str


class WorkbenchSubmitInput(ParamsModel):
    session_id: str
    #: The app's open practice session, when there is one.
    practice_session_id: str | None = None
    answer_confidence: int | None = None
    latency_seconds: int | None = None
    scheduler_candidate_id: str | None = None
    plan_presentation_id: str | None = None


class WorkbenchAttemptInput(ParamsModel):
    attempt_id: str


class WorkbenchItemInput(ParamsModel):
    practice_item_id: str


class WorkbenchSourceInput(ParamsModel):
    extraction_id: str


# -- RPCs ---------------------------------------------------------------------------------------------


@method("workbench.open", WorkbenchOpenInput)
def workbench_open(ctx: SidecarContext, params: WorkbenchOpenInput) -> dict[str, Any]:
    """Open a problem at once (or resume the open one for the same item or
    selection). On a selection that is not an item yet, the stem is the
    verbatim selection and the import runs in the background."""

    vault, repository = _require(ctx)
    carried = max(0, int(params.carried_hints or 0))
    serve = _named_serve(params)
    if params.session_id:
        row = _run(
            WB.resume_session, repository, params.session_id, origin=params.origin, entry=params.entry,
            extraction_id=params.extraction_id, span_ids=params.span_ids, carried=carried,
            carried_book=params.carried_book, serve=serve,
        )
        _ensure_contract(vault, repository, row["id"])
        _link_carried_hints(repository, row["id"], params)
        return _answer({"session": _view(vault, repository, row["id"]), "resumed": True})
    stem = (params.stem_md or "").strip()
    import_status, batch_id, error = "none", None, None
    if params.practice_item_id:
        item = vault.practice_items.get(params.practice_item_id)
        if item is None:
            raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
        stem = stem or str(getattr(item, "prompt", "") or "")
    else:
        if not params.import_request:
            raise SidecarError("validation_error", "A problem that is not an item yet needs its import request.")
        import_status = "pending"
        resumable = WB.resumable_session(
            repository, extraction_id=params.extraction_id, span_ids=params.span_ids, stem_md=stem,
        )
        if resumable is None and not (
            params.client_idempotency_key
            and _key_exists(repository, params.client_idempotency_key)
        ):
            batch_id, error = _start_import(ctx, vault, repository, dict(params.import_request))
            import_status = "pending" if batch_id else "failed"
    row, resumed = _run(
        WB.open_session, repository,
        origin=params.origin, entry=params.entry, stem_md=stem,
        practice_item_id=params.practice_item_id, extraction_id=params.extraction_id,
        span_ids=params.span_ids, parent_session_id=params.parent_session_id,
        source_visible=params.source_visible, client_idempotency_key=params.client_idempotency_key,
        import_status=import_status, import_batch_id=batch_id,
        import_request=params.import_request, import_error=error, carried=carried,
        carried_book=params.carried_book, serve=serve,
    )
    _ensure_contract(vault, repository, row["id"])
    _link_carried_hints(repository, row["id"], params)
    return _answer({"session": _view(vault, repository, row["id"]), "resumed": resumed})


def _named_serve(params: ParamsModel) -> dict[str, str | None] | None:
    """The serve a request names, as one pair (review F15): ``None`` when it
    names neither identifier (keep the pair the session holds), else both,
    an explicit null included (replace the pair)."""

    if not set(WB.SERVE_COLUMNS) & params.model_fields_set:
        return None
    return {column: getattr(params, column) for column in WB.SERVE_COLUMNS}


def _key_exists(repository, key: str) -> bool:
    from learnloop.db.stores import workbench as store

    with repository.connection() as connection:
        return store.session_by_key(connection, key) is not None


@method("workbench.get", WorkbenchSessionInput)
def workbench_get(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.save_step", WorkbenchSaveStepInput)
def workbench_save_step(ctx: SidecarContext, params: WorkbenchSaveStepInput) -> dict[str, Any]:
    """One change to the work, saved as it is typed (idempotent by key)."""

    vault, repository = _require(ctx)
    step = _run(
        WB.save_step, repository, params.session_id,
        op=params.op, client_idempotency_key=params.client_idempotency_key, step_id=params.step_id,
        after_step_id=params.after_step_id, kind=params.kind, body_md=params.body_md,
    )
    view = _view(vault, repository, params.session_id)
    return _answer({"step": to_camel(step), "savedAt": view["updatedAt"], "record": view["record"]})


@method("workbench.set_book", WorkbenchSetBookInput)
def workbench_set_book(ctx: SidecarContext, params: WorkbenchSetBookInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    _run(WB.set_book, repository, params.session_id, params.visible)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.leave", WorkbenchSessionInput)
def workbench_leave(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    _run(WB.leave, repository, params.session_id)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.abandon", WorkbenchSessionInput)
def workbench_abandon(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    _run(WB.abandon, repository, params.session_id)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.reopen", WorkbenchSessionInput)
def workbench_reopen(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    _run(WB.reopen, repository, params.session_id)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.refresh_import", WorkbenchSessionInput)
def workbench_refresh_import(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    """Bind the problem when its import has landed: one item binds; several
    ask which part (``parts``); none, or a failed job, is ``failed`` with the
    steps kept and "try again"."""

    vault, repository = _require(ctx)
    row = _run(WB.session_row, repository, params.session_id)
    if row["import_status"] != "pending" or not row.get("import_batch_id"):
        return _answer({"session": _view(vault, repository, params.session_id)})
    job = _import_job(ctx, repository, row["import_batch_id"])
    vault, repository = ctx.require_vault()
    if job is None:
        _run(WB.mark_import, repository, params.session_id, status="failed",
             error="Setting up this exercise was lost. Try again.")
        return _answer({"session": _view(vault, repository, params.session_id)})
    status = str(job.get("status") or "")
    if status in _IMPORT_RUNNING or not status:
        return _answer({"session": _view(vault, repository, params.session_id)})
    if status != "completed":
        _run(WB.mark_import, repository, params.session_id, status="failed", error=_job_error(job))
        return _answer({"session": _view(vault, repository, params.session_id)})
    parts = [part for part in _job_parts(job) if part["practiceItemId"] in vault.practice_items]
    if len(parts) == 1:
        _run(WB.bind, repository, params.session_id, parts[0]["practiceItemId"])
        _ensure_contract(vault, repository, params.session_id)
        return _answer({"session": _view(vault, repository, params.session_id)})
    if not parts:
        _run(WB.mark_import, repository, params.session_id, status="failed",
             error="Setup made no practice from this selection. Try again, or select the problem's full text.")
        return _answer({"session": _view(vault, repository, params.session_id)})
    return _answer({"session": _view(vault, repository, params.session_id, parts=parts)})


@method("workbench.bind", WorkbenchBindInput)
def workbench_bind(ctx: SidecarContext, params: WorkbenchBindInput) -> dict[str, Any]:
    """Bind a multi-part import to the part the learner picked (one of its own)."""

    vault, repository = _require(ctx)
    row = _run(WB.session_row, repository, params.session_id)
    job = _import_job(ctx, repository, row["import_batch_id"]) if row.get("import_batch_id") else None
    vault, repository = ctx.require_vault()
    parts = {part["practiceItemId"] for part in _job_parts(job)} if job and job.get("status") == "completed" else set()
    if params.practice_item_id not in parts or params.practice_item_id not in vault.practice_items:
        raise SidecarError("validation_error", "That part is not one this problem's setup made.")
    _run(WB.bind, repository, params.session_id, params.practice_item_id)
    _ensure_contract(vault, repository, params.session_id)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.retry_import", WorkbenchSessionInput)
def workbench_retry_import(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    """"Try again" on a failed setup: the same request, enqueued again."""

    vault, repository = _require(ctx)
    row = _run(WB.session_row, repository, params.session_id)
    if row["import_status"] != "failed":
        return _answer({"session": _view(vault, repository, params.session_id)})
    request = WB.import_request(row)
    if request is None:
        raise SidecarError("validation_error", "This problem has no setup to try again.")
    batch_id, error = _start_import(ctx, vault, repository, request)
    if batch_id:
        _run(WB.mark_import, repository, params.session_id, status="pending", batch_id=batch_id)
    else:
        _run(WB.mark_import, repository, params.session_id, status="failed", error=error)
    return _answer({"session": _view(vault, repository, params.session_id)})


def _kept_offer(repository, candidate_id: str | None, practice_session_id: str, practice_item_id: str) -> str | None:
    """The scheduler offer kept on the session, when it is still an
    unanswered offer of this item in the session the submit runs in; a stale
    one (answered elsewhere, another session after a restart) is dropped, so
    the attribution it carried never fails the submit (review F13)."""

    if not candidate_id:
        return None
    open_offer = repository.scheduler_offer_open(
        scheduler_candidate_id=candidate_id, session_id=practice_session_id, practice_item_id=practice_item_id,
    )
    return candidate_id if open_offer else None


def _practice_session(ctx: SidecarContext, repository, requested: str | None) -> str:
    """The practice session a workbench submit runs in: the app's open one,
    else the most recent open one, else a new one (``start_session``)."""

    if requested:
        session = repository.fetch_session(requested)
        if session is not None and session["ended_at"] is None:
            return requested
    recent = repository.most_recent_open_session()
    if recent is not None:
        return str(recent["id"])
    from learnloop_sidecar.handlers.sessions import SessionStartInput, start_session

    return str(start_session(ctx, SessionStartInput())["sessionId"])


@method("workbench.submit", WorkbenchSubmitInput)
def workbench_submit(ctx: SidecarContext, params: WorkbenchSubmitInput) -> dict[str, Any]:
    """Submit the work through the ordinary attempt path (spec §5.4).

    The answer is the live steps in order; ``hints_used`` is the session's
    hint-equivalents (the book when it counted, the answer box's hints shown
    before steps); the attempt type is the one the answer box would pick; the
    contract is the one the session showed; the serve is the one the request
    names (both identifiers), else the one the session kept (both). A refusal (a cold check answered
    with the book, grading unavailable) keeps the session open with its steps.
    A retry after a lost response is answered from the submission's receipt.
    """

    from learnloop_sidecar.handlers.practice import SubmitAttemptInput, _cached_submission, submit_attempt_on

    vault, repository = _require(ctx)
    row = _run(WB.session_row, repository, params.session_id)
    if row["status"] == "submitted" and row.get("attempt_id") and row.get("practice_item_id"):
        cached = _cached_submission(
            ctx, vault, repository, WB.submission_id_for(row["id"]), row["practice_item_id"]
        )
        if cached is not None:
            practice_session_id = row.get("practice_session_id")
            return _answer({
                "attempt": cached,
                "session": _view(vault, repository, params.session_id),
                "practiceSession": session_snapshot(repository, practice_session_id) if practice_session_id else None,
            })
    plan = _run(WB.submission_plan, repository, params.session_id)
    item = vault.practice_items.get(plan.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Unknown Practice Item {plan.practice_item_id}.")
    practice_session_id = _practice_session(ctx, repository, params.practice_session_id)
    # The serve is one pair (review F15): the one the request names, both
    # identifiers, or else the one the session kept, both identifiers.
    named = _named_serve(params)
    if named is not None:
        scheduler_candidate_id, plan_presentation_id = named["scheduler_candidate_id"], named["plan_presentation_id"]
    else:
        scheduler_candidate_id = _kept_offer(
            repository, plan.scheduler_candidate_id, practice_session_id, plan.practice_item_id,
        )
        plan_presentation_id = plan.plan_presentation_id
    submission = SubmitAttemptInput(
        session_id=practice_session_id,
        practice_item_id=plan.practice_item_id,
        answer_md=plan.composed.answer_md,
        attempt_type=stuck_attempt_type(item.attempt_types_allowed, hints_used=plan.hints_used),
        hints_used=plan.hints_used,
        assessment_contract_version_id=plan.assessment_contract_version_id,
        latency_seconds=params.latency_seconds,
        answer_confidence=params.answer_confidence,
        submission_id=plan.submission_id,
        scheduler_candidate_id=scheduler_candidate_id,
        plan_presentation_id=plan_presentation_id,
        declared_stuck=plan.composed.declared_stuck,
    )
    # H2b review F1: the answer box's shown server hints carried into the
    # problem fold into this attempt and attach to it.
    attempt = submit_attempt_on(ctx, submission, entry_surface=plan.entry_surface,
                                workbench_session_id=plan.session_id)
    vault, repository = ctx.require_vault()
    _run(WB.mark_submitted, repository, params.session_id, attempt_id=str(attempt["attemptId"]),
         practice_session_id=practice_session_id)
    return _answer({
        "attempt": attempt,
        "session": _view(vault, repository, params.session_id),
        "practiceSession": session_snapshot(repository, practice_session_id),
    })


@method("workbench.session_for_attempt", WorkbenchAttemptInput)
def workbench_session_for_attempt(ctx: SidecarContext, params: WorkbenchAttemptInput) -> dict[str, Any]:
    """The submitted problem behind an attempt, for back-from-feedback (UX S6);
    ``null`` for every attempt the workbench did not write."""

    vault, repository = _require(ctx)
    row = WB.session_for_attempt(repository, params.attempt_id)
    return _answer({"session": _view(vault, repository, row["id"]) if row else None})


@method("workbench.for_item", WorkbenchItemInput)
def workbench_for_item(ctx: SidecarContext, params: WorkbenchItemInput) -> dict[str, Any]:
    """The item's open or abandoned problems ("resume your steps" on its card)."""

    vault, repository = _require(ctx)
    rows = WB.sessions_for_item(repository, params.practice_item_id, now=datetime.now(UTC),
                                open_days=WB.open_session_days(vault))
    return _answer({"sessions": to_camel(rows)})


@method("workbench.for_source", WorkbenchSourceInput)
def workbench_for_source(ctx: SidecarContext, params: WorkbenchSourceInput) -> dict[str, Any]:
    """The source's open or abandoned problems: the ``✎`` marks, the rail and
    RW6a's recap (``unfinished`` past ``workbench.open_session_days``)."""

    vault, repository = _require(ctx)
    rows = WB.sessions_for_source(repository, params.extraction_id, now=datetime.now(UTC),
                                  open_days=WB.open_session_days(vault))
    return _answer({"sessions": to_camel(rows), "openSessionDays": WB.open_session_days(vault)})
