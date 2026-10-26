"""Reader workbench RW2a RPCs: the resumable scratchpad (spec_reader_workbench_v1 §5.1).

The adapter around :mod:`learnloop.reader.workbench`. It adds what needs the
sidecar: the exercise import a selected problem waits on (enqueued with the
same code as ``reader.import_exercise``, bound when its job lands), the
practice session a submit runs in, and the submit itself, which goes through
the one submit implementation (``practice.submit_attempt_on``) with the
workbench's entry surface, so it is graded, diagnosed and admitted by the one
eligibility decision exactly like every other answer.

Reader RW4b: a textbook exercise the learner picked from a ``find_practice``
proposal ("use this one", spec §7.4) opens the same way, on its verbatim
statement, with the sources service's own import (S1, the helper
``import_source_exercise`` uses) behind it instead of ``reader.import_exercise``;
it binds only once that import wrote the item, and a refused import binds
nothing. Its view carries ``source_exercise`` (the import and the key's honest
status); every other problem's view is unchanged.

Every RPC refuses ``workbench_disabled`` while ``workbench.enabled`` is off,
before reading or writing anything. Desktop only (spec D20).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import Field

from learnloop.attempts.stuck import stuck_attempt_type
from learnloop.reader import workbench as WB
from learnloop.tutor.tutor_qa import hint_equivalents_for_submission
from learnloop_sidecar.context import SidecarContext, session_snapshot
from learnloop_sidecar.dto import ParamsModel, to_camel
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

T = TypeVar("T")

#: Reader RW4b fix round 4 (R1): the RPC this module adds for a picked
#: exercise's admission (pinned desktop-only in tests/test_mobile_allowlist.py).
EXERCISE_ADMISSION_RPCS: tuple[str, ...] = ("workbench.admit",)

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
    try:
        # No practice session open yet: the submit opens one, so only the
        # questions that count in the item's window whatever the session (a
        # bound Reader question, RW1c fix round 4, F1) will be added.
        return int(hint_equivalents_for_submission(repository, item_id, practice_session,
                                                   item_window_only=not practice_session))
    except Exception:  # noqa: BLE001 - a display line never fails a read
        return 0


def _earlier_hints(vault, repository, session: dict[str, Any]) -> int:
    """Reader CA2 (Codex review F1; orchestrator fix F1/F15): the earlier
    attempt's opened help the submit's server side will add, its own
    component in the record line: carried onto an open problem of the item
    (``earlier_opened_at``), or still on the answer box's draft. One per
    attempt, the same read the submit makes (``practice._earlier_opened_hint``)."""

    item_id = session.get("practice_item_id")
    if not item_id or session.get("status") != "open" or item_id not in vault.practice_items:
        return WB.earlier_hints(session)
    practice_session = session.get("practice_session_id")
    if not practice_session:
        recent = repository.most_recent_open_session()
        practice_session = recent["id"] if recent else None
    from learnloop_sidecar.handlers.practice import _earlier_opened_hint

    try:
        return _earlier_opened_hint(repository, practice_session, str(item_id))
    except Exception:  # noqa: BLE001 - a display line never fails a read
        return WB.earlier_hints(session)


def record_line(vault, repository, session_id: str) -> dict[str, Any]:
    """A problem's record line and save time, with no statement (a step's
    save, the help ladder's record): not a statement-bearing response, so a
    problem whose region was held out since keeps saving its steps."""

    row = _run(WB.session_row, repository, session_id)
    view = _run(WB.session_view, repository, session_id, question_hints=_question_hints(vault, repository, row),
                server_hints=_carried_server_hints(repository, row),
                earlier_hints=_earlier_hints(vault, repository, row))
    return {"updated_at": view.get("updated_at"), "record": to_camel(view.get("record"))}


def _source_id(repository, extraction_id: str | None) -> str | None:
    if not extraction_id:
        return None
    from learnloop_sidecar.handlers.reader import _source_id_for_extraction

    try:
        return _source_id_for_extraction(repository, extraction_id)
    except Exception:  # noqa: BLE001 - an unknown extraction has no source
        return None


def _current_reading(repository, source_id: str) -> str | None:
    """The reading the Reader opens a source on (its latest completed
    extraction, as ``reader.render_view`` resolves a source id)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id

    try:
        return resolve_extraction_id(repository, source_id)
    except Exception:  # noqa: BLE001 - a source with no reading opens on none
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
    # The subject a submit now would record on the attempt (its first, else
    # the field's 'default'), frozen with the contract (RW2d re-review F3).
    subjects = list(vault.subjects_for_item(item) or [])
    _run(WB.ensure_contract, repository, session_id, version_id,
         subject_id=str(subjects[0]) if subjects else "default")


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


def _source_exercise_view(vault, repository, row: dict[str, Any]) -> dict[str, Any] | None:
    """A textbook exercise picked from a proposal (Reader RW4b): its import and
    the answer key's honest status (the sources service's effective status of
    the item as written, so a later check or an edit shows). None for every
    other problem, whose view is unchanged."""

    request = WB.import_request(row)
    if not _is_source_exercise(request):
        return None
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import KEY_STATUS_LABELS, effective_key_status, import_row

    import_id = None
    if row.get("import_batch_id"):
        jobs = repository.ingest_jobs_for_batch(row["import_batch_id"])
        if jobs:
            import_id = (jobs[0].get("payload") or {}).get("import_id")
    found: dict[str, Any] | None = None
    key_status = None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if import_id:
            found = import_row(connection, str(import_id))
        item_id = row.get("practice_item_id")
        item = vault.practice_items.get(item_id) if item_id else None
        if item is not None:
            key_status = effective_key_status(connection, item)
        elif found is not None:
            key_status = found.get("key_status")
    return {
        "proposal_id": request.get("proposal_id"),
        "import_id": import_id,
        "import_status": (found or {}).get("status"),
        "reason": (found or {}).get("reason"),
        "key_status": key_status,
        "key_label": KEY_STATUS_LABELS.get(key_status or "", ""),
    }


def _view(vault, repository, session_id: str, *, parts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """THE one builder of every workbench response that carries a problem's
    statement (Reader RW4b fix round 5, R2): a picked textbook exercise's
    statement is revalidated through the one statement reader here, before
    anything of it is built, and a withheld one refuses
    (``exercise_withheld``) whatever the RPC."""

    row = _run(WB.session_row, repository, session_id)
    _refuse_withheld_exercise(vault, repository, row)
    extra: dict[str, Any] = {"source_id": _source_id(repository, row.get("extraction_id")), "parts": parts,
                             "presentation": _presentation(vault, repository, row)}
    source_exercise = _source_exercise_view(vault, repository, row)
    if source_exercise is not None:
        extra["source_exercise"] = source_exercise
    picked = WB.exercise_pick(row)
    if picked is not None:
        # RW4b: a textbook exercise the learner picked. ``due``: its import
        # bound the problem and the learner pick of that item is still owed,
        # whichever visit or restart sees it first (Codex review F2).
        extra["exercise_pick"] = {
            "proposal_id": picked.get("proposal_id"),
            "exposure": picked.get("exposure"),
            "exposure_checked": picked.get("exposure_checked"),
            "admitted": bool(picked.get("admitted_at")),
            "due": WB.exercise_pick_due(row),
        }
    view = _run(
        WB.session_view, repository, session_id,
        question_hints=_question_hints(vault, repository, row),
        server_hints=_carried_server_hints(repository, row),
        earlier_hints=_earlier_hints(vault, repository, row),
        extra=extra,
    )
    return to_camel(view)


def _carried_server_hints(repository, session: dict[str, Any]) -> int:
    """The answer box's shown server hints the problem's submit will fold
    (H2b fix round 3, ruling R1), every level: what the record line names
    before Submit. The same window the submit folds: the open problem's
    practice session and item, the rows requested since the item's last
    attempt there, whatever their key. A read; never writes."""

    item_id = session.get("practice_item_id")
    if not item_id or session.get("status") != "open":
        return 0
    practice_session = session.get("practice_session_id")
    if not practice_session:
        recent = repository.most_recent_open_session()
        practice_session = recent["id"] if recent else None
    if not practice_session:
        return 0
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import fold_row_count, keyless_window_start

    try:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                                  ).fetchone() is None:
                return 0
            since = keyless_window_start(connection, practice_item_id=str(item_id), session_id=str(practice_session))
            return fold_row_count(connection, practice_item_id=str(item_id), session_id=str(practice_session),
                                  submission_id=None, since=since)
    except Exception:  # noqa: BLE001 - a display line never fails a read
        return 0


def _answer(payload: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, **payload}


# -- the exercise import a selected problem waits on (UX S2) ----------------------------------------


#: The stored import request of a textbook exercise the learner picked from a
#: ``find_practice`` proposal (Reader RW4b, spec §7.4): the sources service's
#: import path (S1), not ``reader.import_exercise``.
SOURCE_EXERCISE_KIND = WB.SOURCE_EXERCISE_KIND


def _is_source_exercise(request: dict[str, Any] | None) -> bool:
    return bool(request) and request.get("kind") == SOURCE_EXERCISE_KIND


def _enqueue_import(ctx: SidecarContext, vault, repository, request: dict[str, Any]) -> str:
    """Queue the exercise import exactly as ``reader.import_exercise`` does, or,
    for a picked textbook exercise proposal, exactly as ``import_source_exercise``
    does (the same helper: the import row, the pick's usage verdict, the job)."""

    region = _picked_region(request)
    if region is not None:
        # The import reads the exercise's statement: only through the one
        # reader, re-checked now (fix round 4, R4).
        from learnloop_sidecar.handlers import library_exercises as LX

        if LX.read_exercise_statement(vault, repository, region[0], region[1]) is None:
            raise SidecarError(EXERCISE_WITHHELD, EXERCISE_WITHHELD_MESSAGE)
    if _is_source_exercise(request):
        from learnloop_sidecar.handlers.source_service import queue_source_exercise_import

        if not vault.config.library_exercises.enabled:
            raise SidecarError("library_exercises_disabled", "Exercises from your sources are switched off.")
        queued = queue_source_exercise_import(
            ctx, vault, repository, proposal_id=str(request.get("proposal_id") or ""),
            extraction_id=str(request.get("extraction_id") or ""),
            span_ids=[str(span) for span in request.get("span_ids") or []])
        return queued["batch_id"]

    from learnloop.reader import reader_dialogue as RD
    from learnloop_sidecar.handlers.reader import ReaderImportExerciseInput, enqueue_exercise_import

    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader is switched off, so this problem cannot be set up.")
    # The picked exercise's record (RW4b) is the workbench's, never the import's.
    params = ReaderImportExerciseInput.model_validate(
        {key: value for key, value in request.items() if key != WB.EXERCISE_PICK_KEY})
    return enqueue_exercise_import(ctx, vault, repository, params)


def _import_job(ctx: SidecarContext, repository, batch_id: str) -> dict[str, Any] | None:
    """The import batch's job, reloading the vault once when it completed (as
    ``reader.exercise_import_status`` does), so its items schedule."""

    jobs = repository.ingest_jobs_for_batch(batch_id)
    if not jobs:
        return None
    from learnloop.ai import plan_fallback

    # Redesign D: the batch's own offer (its action's, never this read's), once.
    plan_fallback.relay_batch_offer(batch_id)
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
    if not parts and result.get("status") == "written" and result.get("practiceItemId"):
        # A textbook exercise's import (S1) writes one item, only once its key
        # was checked within the time box (or labelled "being checked").
        parts.append({"practiceItemId": result["practiceItemId"], "title": result.get("label") or "", "prompt": ""})
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


class WorkbenchSourceExerciseInput(ParamsModel):
    proposal_id: str
    extraction_id: str
    span_ids: list[str] = Field(min_length=1, max_length=40)


class WorkbenchExercisePickInput(ParamsModel):
    """A fallback exercise the learner picked (Reader RW4b): the ``pick`` its
    listing returned, sent back as it came."""

    learning_object_ids: list[str] = Field(default_factory=list, max_length=40)
    shown_event_ids: list[str] = Field(default_factory=list, max_length=80)


class WorkbenchOpenInput(ParamsModel):
    origin: str
    entry: str
    #: Resume this session on the asking surface ("resume your steps", the
    #: ``✎`` mark): reopened when abandoned, moved when on another surface.
    session_id: str | None = None
    #: The answer box's hints the learner saw before working in steps.
    carried_hints: int = 0
    #: The practice screen's open practice session, whose draft the steps
    #: take over (re-review F1: an earlier attempt's help it opened is
    #: carried onto the problem by the server, never by the client's count).
    practice_session_id: str | None = None
    #: A book a problem the learner left for the answer box counted (review F2).
    carried_book: bool = False
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
    #: Reader RW4b: a textbook exercise picked from a find_practice proposal
    #: ("use this one"). The stem is its verbatim statement; the sources
    #: service's import (S1) runs in the background and binds when it wrote the item.
    source_exercise: WorkbenchSourceExerciseInput | None = None
    #: Reader RW4b: the fallback's exercise ("use this one" beside its
    #: ``import_request``), so the server reads its exposure and records the pick.
    exercise_pick: WorkbenchExercisePickInput | None = None


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


class WorkbenchAdmitInput(ParamsModel):
    session_id: str
    #: The app's open practice session, when there is one.
    practice_session_id: str | None = None


class WorkbenchAttemptInput(ParamsModel):
    attempt_id: str


class WorkbenchItemInput(ParamsModel):
    practice_item_id: str


class WorkbenchSourceInput(ParamsModel):
    extraction_id: str


class WorkbenchOpenProblemsInput(ParamsModel):
    """No parameters: every source's open problems."""


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
        # RW4b fix round 4, R3: a resume opens the problem it names, by its id,
        # and only that problem: one asked for with another item, or for
        # another book than the one it is on, is refused; and a picked
        # exercise whose region is exam or held-out material now is not shown
        # again (R4, the one statement reader; its steps are kept).
        named = _run(WB.session_row, repository, params.session_id)
        if params.practice_item_id and named.get("practice_item_id") != params.practice_item_id:
            raise SidecarError("validation_error", "That problem is for another item.",
                               details={"sessionId": params.session_id})
        if (params.origin == "reader" and params.extraction_id and named.get("extraction_id")
                and named["extraction_id"] != params.extraction_id):
            raise SidecarError("validation_error", "That problem is in another book.",
                               details={"sessionId": params.session_id})
        _refuse_withheld_exercise(vault, repository, named)
        draft_session, earlier = _draft_earlier(repository, params, named.get("practice_item_id"))
        row = _run(
            WB.resume_session, repository, params.session_id, origin=params.origin, entry=params.entry,
            extraction_id=params.extraction_id, span_ids=params.span_ids, carried=carried,
            carried_book=params.carried_book, serve=serve, carried_earlier=bool(earlier),
        )
        _carry_earlier(repository, draft_session, earlier, row)
        _ensure_contract(vault, repository, row["id"])
        return _answer({"session": _view(vault, repository, row["id"]), "resumed": True})
    stem = (params.stem_md or "").strip()
    entry = params.entry
    import_status, batch_id, error = "none", None, None
    request = dict(params.import_request) if params.import_request else None
    if params.practice_item_id:
        item = vault.practice_items.get(params.practice_item_id)
        if item is None:
            raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
        stem = stem or str(getattr(item, "prompt", "") or "")
    else:
        if params.import_request and params.source_exercise:
            raise SidecarError("validation_error", "A problem is imported one way: a selection or a proposal's exercise.")
        if params.exercise_pick is not None and not params.import_request:
            raise SidecarError("validation_error", "A fallback exercise opens with its import request.")
        if params.source_exercise or params.exercise_pick is not None:
            if not vault.config.library_exercises.enabled:
                raise SidecarError("library_exercises_disabled", "Exercises from your sources are switched off.")
        if params.source_exercise:
            request = {"kind": SOURCE_EXERCISE_KIND, **params.source_exercise.model_dump()}
        elif params.import_request:
            request = dict(params.import_request)
        else:
            raise SidecarError("validation_error", "A problem that is not an item yet needs its import request.")
        if params.source_exercise or params.exercise_pick is not None:
            stem, entry, request = _picked_exercise(vault, repository, params, request, stem)
        import_status = "pending"
        resumable = WB.resumable_session(
            repository, extraction_id=params.extraction_id, span_ids=params.span_ids, stem_md=stem,
        )
        if resumable is None and not (
            params.client_idempotency_key
            and _key_exists(repository, params.client_idempotency_key)
        ):
            batch_id, error = _start_import(ctx, vault, repository, request)
            import_status = "pending" if batch_id else "failed"
    draft_session, earlier = _draft_earlier(repository, params, params.practice_item_id)
    row, resumed = _run(
        WB.open_session, repository,
        origin=params.origin, entry=entry, stem_md=stem,
        practice_item_id=params.practice_item_id, extraction_id=params.extraction_id,
        span_ids=params.span_ids, parent_session_id=params.parent_session_id,
        source_visible=params.source_visible, client_idempotency_key=params.client_idempotency_key,
        import_status=import_status, import_batch_id=batch_id,
        import_request=request, import_error=error, carried=carried,
        carried_book=params.carried_book, serve=serve, carried_earlier=bool(earlier),
    )
    _carry_earlier(repository, draft_session, earlier, row)
    _ensure_contract(vault, repository, row["id"])
    if resumed:
        _refuse_withheld_exercise(vault, repository, _run(WB.session_row, repository, row["id"]))
    return _answer({"session": _view(vault, repository, row["id"]), "resumed": resumed})


#: The origins whose open hands the practice screen's answer-box draft to the steps.
_DRAFT_HANDOFF_ORIGINS = frozenset({"practice", "plan"})


def _draft_earlier(repository, params: WorkbenchOpenInput, practice_item_id: str | None) -> tuple[str | None, int]:
    """Codex re-review F1: ``(practice session, 1)`` when the practice
    screen's draft of the item, handed to the steps now, opened an earlier
    attempt's help under its current key (``sessions.draft_earlier_opened``),
    else ``(None, 0)``. Carried again onto any problem the draft moves into
    (a problem set aside before keeps its own mark): the problem holds it as
    a set-once component and every count ORs it with the draft's, so it is
    never counted twice. The practice session is the one the screen names
    while open, else the most recent open one. Read from the server's
    checkpoint, never from the client's count."""

    if params.origin not in _DRAFT_HANDOFF_ORIGINS or not practice_item_id:
        return None, 0
    from learnloop_sidecar.handlers.sessions import draft_earlier_opened

    try:
        session_id = params.practice_session_id if _session_open(repository, params.practice_session_id) else None
        if session_id is None:
            recent = repository.most_recent_open_session()
            session_id = str(recent["id"]) if recent else None
        if session_id is None:
            return None, 0
        checkpoint = repository.fetch_session_checkpoint(session_id)
    except Exception:  # noqa: BLE001 - no readable draft carries nothing
        return None, 0
    if not draft_earlier_opened(checkpoint, practice_item_id=str(practice_item_id)):
        return None, 0
    return session_id, 1


def _carry_earlier(repository, draft_session: str | None, earlier: int, row: dict[str, Any]) -> None:
    """Record on the draft that its opening now lives on the problem (its
    own component, ``earlier_opened_at``: never the authored reveals'
    ``carried_hints``, orchestrator fix F15), so the checkpoint never
    counts it again."""

    if not earlier or not draft_session:
        return
    from learnloop_sidecar.handlers.sessions import carry_earlier_opened
    from learnloop_sidecar.logging import log_event

    try:
        carry_earlier_opened(repository, draft_session, practice_item_id=str(row.get("practice_item_id")),
                             workbench_session_id=str(row["id"]))
    except Exception as exc:  # noqa: BLE001 - the problem holds the hint: an unmarked draft
        # reads as the same opening (the submit ORs the two), never lost.
        log_event("workbench_earlier_opened_not_marked", error=type(exc).__name__)


def _picked_exercise(vault, repository, params: WorkbenchOpenInput, request: dict[str, Any],
                     stem: str) -> tuple[str, str, dict[str, Any]]:
    """What a textbook exercise the learner picked opens as (Reader RW4b),
    decided here rather than by the card that offered it: its complete
    statement, read through the one statement reader (fix round 4, R4: an
    exercise held out since its card was shown is refused before anything of
    it is read or returned; Codex review F4: the card's is a preview), how it
    opens from the exposure rule read now (F3: exposed since it was shown, it
    opens as practice beside the book), and the pick's record kept on the
    problem (F2)."""

    from learnloop_sidecar.handlers import library_exercises as LX

    extraction_id, span_ids, pick = _exercise_region(params, request)
    statement = LX.read_exercise_statement(vault, repository, extraction_id, span_ids)
    if statement is None:
        raise SidecarError(EXERCISE_WITHHELD, EXERCISE_WITHHELD_MESSAGE)
    pick.update(extraction_id=extraction_id, span_ids=span_ids, admitted_at=None)
    exposure = LX.pick_exposure(vault, repository, pick)
    pick.update(exposure=exposure, exposure_checked="selection")
    # Only an exercise the proposal proposed (or the fallback's listed region)
    # opens on its own statement; anything else keeps the asked stem and its
    # import refuses it.
    full = statement.text if exposure is not None else None
    return (full or stem), LX.pick_entry(exposure, params.entry), {**request, WB.EXERCISE_PICK_KEY: pick}


#: A picked exercise whose region is exam or held-out material now (or whose
#: check could not be read): nothing of it is shown, opened or imported.
EXERCISE_WITHHELD = "exercise_withheld"
EXERCISE_WITHHELD_MESSAGE = "This exercise is no longer available to practise (it is kept for an exam or a held-out check)."


def _exercise_region(params: WorkbenchOpenInput, request: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    """The picked exercise's extraction, spans and the pick's record to keep."""

    if params.source_exercise is not None:
        extraction_id, span_ids = params.source_exercise.extraction_id, list(params.source_exercise.span_ids)
        return extraction_id, span_ids, {"proposal_id": params.source_exercise.proposal_id}
    selection = ReaderImportSelection.model_validate(request)
    span_ids = _selection_spans(selection.raw_selection)
    if not span_ids:
        raise SidecarError("validation_error", "A fallback exercise opens on its region's blocks.")
    dumped = params.exercise_pick.model_dump() if params.exercise_pick is not None else {}
    return selection.extraction_id, span_ids, {"proposal_id": None, **dumped}


def _selection_spans(raw_selection: dict[str, Any]) -> list[str]:
    spans = [str(node.get("span_id") or node.get("spanId") or "")
             for node in (raw_selection.get("nodes") or []) if isinstance(node, dict)]
    return [span for span in spans if span]


def _picked_region(request: dict[str, Any] | None) -> tuple[str, list[str]] | None:
    """A picked exercise's region from an import request (None for every other problem)."""

    return WB.exercise_request_region(request)


def _refuse_withheld_exercise(vault, repository, row: dict[str, Any]) -> None:
    """A picked exercise's statement is built only while its region may be
    shown (fix rounds 4 and 5): every status, a submitted problem's too."""

    if not WB.statement_cleared(vault, repository, row):
        raise SidecarError(EXERCISE_WITHHELD, EXERCISE_WITHHELD_MESSAGE)


class ReaderImportSelection(ParamsModel):
    """The two fields of a fallback's ``reader.import_exercise`` request the
    workbench reads (the request is otherwise passed on unchanged)."""

    model_config = {**ParamsModel.model_config, "extra": "ignore"}

    extraction_id: str
    raw_selection: dict[str, Any]


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
    line = record_line(vault, repository, params.session_id)
    return _answer({"step": to_camel(step), "savedAt": line["updated_at"], "record": line["record"]})


@method("workbench.set_book", WorkbenchSetBookInput)
def workbench_set_book(ctx: SidecarContext, params: WorkbenchSetBookInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    _run(WB.set_book, repository, params.session_id, params.visible)
    return _answer({"session": _view(vault, repository, params.session_id)})


@method("workbench.leave", WorkbenchSessionInput)
def workbench_leave(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]:
    vault, repository = _require(ctx)
    _run(WB.leave, repository, params.session_id)
    _queue_stuck_texts(ctx, vault, repository, params.session_id)
    return _answer({"session": _view(vault, repository, params.session_id)})


def _queue_stuck_texts(ctx: SidecarContext, vault, repository, session_id: str) -> None:
    """RW2b in-session updates (§5.2): a stuck step's newest text goes to
    learner-text gaps when Leave or Submit sends it. Off with the help."""

    from learnloop.workbench import ladder as workbench_help

    if not workbench_help.help_enabled(vault):
        return
    try:
        if workbench_help.queue_stuck_texts(vault, repository, session_id):
            ctx.post_attempt_worker.notify()
    except Exception:  # noqa: BLE001 - learner-text gaps never reach the workbench
        return


def _schedule_map(ctx: SidecarContext, vault, repository, session_id: str) -> None:
    """RW2b (§5.2): the bound item's approach map is built in the background
    (H1's ``build_on_serve``, its switches, locks and envelope). Off with the help."""

    from learnloop.hints import workbench as hint_workbench
    from learnloop.workbench import ladder as workbench_help

    if not workbench_help.help_enabled(vault):
        return
    row = _run(WB.session_row, repository, session_id)
    if row.get("practice_item_id"):
        hint_workbench.schedule_map(vault, repository.sqlite_path, row["practice_item_id"],
                                    client=getattr(ctx, "approach_map_client", None),
                                    builds=getattr(ctx, "map_builds", None))


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
        _schedule_map(ctx, vault, repository, params.session_id)
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
    _schedule_map(ctx, vault, repository, params.session_id)
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


def _session_open(repository, practice_session_id: str | None) -> bool:
    if not practice_session_id:
        return False
    session = repository.fetch_session(practice_session_id)
    return session is not None and session["ended_at"] is None


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


# -- RW4b fix round 4, R1: the exercise's admission, one server operation ---------------------------------

#: A submit on a picked exercise whose learner pick could not be made and
#: served now: nothing was submitted, the problem stays open, try again.
ADMISSION_PENDING = "admission_pending"


def _admit(ctx: SidecarContext, session_id: str, requested_practice_session: str | None) -> str | None:
    """Admit a picked exercise's item as the learner's pick, for THIS problem
    (Reader RW4b fix round 4, R1). Keyed by the workbench session id, never by
    the item (Codex final verify F10), under the vault mutation lock:

    1. the problem is read by its id and must still owe its pick (bound to
       the item its import wrote, open, not admitted, its region readable);
    2. the practice session is resolved, or started (the submit's own rule);
    3. the plan's learner pick is made with the proposal and import ids,
       under the admission's own idempotency key (``admission_key``, derived
       from the workbench session id). The plan writes the pick's block, its
       serve, its keyed receipt and the proposal's delivery in ONE
       transaction (fix round 6), and the step is then kept on the problem
       (``picked``);
    4. the item is served in that session (the practice screen's serve,
       which records a plan-off proposal's delivery) and kept as ``served``,
       in one transaction (fix round 6);
    5. in one transaction: that serve is stored on THIS problem, with the
       practice session, the exposure read again (the bound item's own
       attempts and family reveals counted, fix round 5, R3), and
       ``admitted_at``.

    Idempotent (fix rounds 5 and 6): a retry after any failure completes
    only what is missing. A pick already kept is never made again; a pick
    whose record was lost is found by its keyed receipt, under any plan, with
    its original presentation; a serve already kept is not repeated. A problem admitted already returns its
    admission (the same practice session). Returns the practice session the
    problem is admitted in, or None when nothing is owed."""

    from learnloop.vault_lock import vault_mutation_lock
    from learnloop_sidecar.handlers import library_exercises as LX
    from learnloop_sidecar.handlers.daily_plan import PlanLearnerPickInput, plan_learner_pick
    from learnloop_sidecar.handlers.practice import ServePracticeItemInput, get_practice_item

    vault, repository = _require(ctx)
    row = _run(WB.session_row, repository, session_id)
    pick = WB.exercise_pick(row)
    if pick is None:
        return None
    if pick.get("admitted_at"):
        return pick.get("practice_session_id") or None
    if not WB.exercise_pick_due(row):
        return None
    with vault_mutation_lock(vault.root, purpose="workbench_admit"):
        vault, repository = _require(ctx)
        row = _run(WB.session_row, repository, session_id)
        pick = WB.exercise_pick(row) or {}
        if pick.get("admitted_at"):
            return pick.get("practice_session_id") or None
        if not WB.exercise_pick_due(row):
            return None
        _refuse_withheld_exercise(vault, repository, row)
        item_id = str(row["practice_item_id"])
        proposal_id = pick.get("proposal_id") or None
        import_id = (_source_exercise_view(vault, repository, row) or {}).get("import_id") if proposal_id else None
        stage = dict(pick.get("admission") or {})
        picked_stage = stage.get("picked") if isinstance(stage.get("picked"), dict) else None
        if picked_stage is None:
            practice_session_id = _practice_session(ctx, repository, requested_practice_session)
            picked = plan_learner_pick(ctx, PlanLearnerPickInput(
                practice_item_id=item_id, session_id=practice_session_id, proposal_id=proposal_id,
                source_exercise_import_id=import_id, idempotency_key=admission_key(session_id)))
            enabled = bool(picked.get("enabled"))
            step = picked.get("step") if isinstance(picked.get("step"), dict) else {}
            item_step = step if step.get("kind") == "item" else {}
            picked_stage = {
                "practice_session_id": practice_session_id,
                "plan_enabled": enabled,
                "serve": {
                    "scheduler_candidate_id": item_step.get("schedulerCandidateId"),
                    "plan_presentation_id": item_step.get("presentationId") if enabled else None,
                },
            }
            vault, repository = ctx.require_vault()
            _run(WB.record_admission_stage, repository, session_id, {"key": admission_key(session_id),
                                                                     "picked": picked_stage})
        practice_session_id = str(picked_stage["practice_session_id"])
        if not stage.get("served"):
            # The plan off: the open list's serve records the proposal's
            # delivery (as the shell's serve did); the plan on: its pick did.
            origin = {} if picked_stage.get("plan_enabled") or not proposal_id else {
                "proposal_id": proposal_id, "source_exercise_import_id": import_id}
            # Fix round 6 (F13): the serve, a plan-off proposal's delivery and
            # the ``served`` record commit in ONE transaction, so a failure
            # between them leaves nothing written and the retry serves once.
            with repository.atomic():
                get_practice_item(ctx, ServePracticeItemInput(practice_item_id=item_id,
                                                              session_id=practice_session_id, **origin))
                _run(WB.record_admission_stage, repository, session_id, {"served": True})
        _run(WB.admit_exercise_pick, repository, session_id, practice_item_id=item_id,
             exposure=LX.pick_exposure(vault, repository, pick, practice_item_id=item_id),
             serve=dict(picked_stage.get("serve") or {}), practice_session_id=practice_session_id)
    admitted = WB.exercise_pick(_run(WB.session_row, repository, session_id)) or {}
    if not admitted.get("admitted_at"):
        raise SidecarError(ADMISSION_PENDING, "This exercise couldn't be added to your practice yet. Try again.",
                           details={"retryable": True})
    return admitted.get("practice_session_id") or practice_session_id


def admission_key(session_id: str) -> str:
    """The learner pick's durable idempotency identity for a picked exercise's
    admission (fix round 5, R1): derived from the workbench session id, kept
    with the pick's plan receipt, so a retried admission finds its pick."""

    return f"workbench_admission:{session_id}"


@method("workbench.admit", WorkbenchAdmitInput)
def workbench_admit(ctx: SidecarContext, params: WorkbenchAdmitInput) -> dict[str, Any]:
    """Make a picked exercise's owed learner pick, for the problem named
    (Reader RW4b fix round 4, R1): see ``_admit``. Answers the problem as it
    now stands and the practice session it was admitted in."""

    _require(ctx)
    practice_session_id = _admit(ctx, params.session_id, params.practice_session_id)
    vault, repository = _require(ctx)
    return _answer({
        "session": _view(vault, repository, params.session_id),
        "practiceSession": session_snapshot(repository, practice_session_id) if practice_session_id else None,
    })


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
    # The gate before anything is admitted, graded or stored (fix round 5, R2).
    _refuse_withheld_exercise(vault, repository, row)
    admitted_in: str | None = None
    if row["status"] == "open" and WB.exercise_pick_due(row):
        # RW4b fix round 4, R2: a picked exercise's owed pick is made, served
        # and recorded on the problem before anything is submitted; when it
        # cannot be, nothing is submitted and the problem stays open to retry
        # (Codex final verify F2: never a submission that leaves it owed).
        try:
            admitted_in = _admit(ctx, params.session_id, params.practice_session_id)
        except SidecarError as exc:
            if exc.code == EXERCISE_WITHHELD:
                raise
            raise SidecarError(ADMISSION_PENDING, "This exercise couldn't be added to your practice yet, so "
                               "nothing was submitted. Try again.", details={"retryable": True}) from exc
        vault, repository = _require(ctx)
        row = _run(WB.session_row, repository, params.session_id)
        if WB.exercise_pick_due(row):
            raise SidecarError(ADMISSION_PENDING, "This exercise couldn't be added to your practice yet, so "
                               "nothing was submitted. Try again.", details={"retryable": True})
    elif row["status"] == "open":
        admitted_in = (WB.exercise_pick(row) or {}).get("practice_session_id") or None
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
    # RW2b (§5.4, G-H3): the submission's admission time on the problem's
    # help rows FIRST (a row stamped then is never delivered after); H0's own
    # stamp in the submit then keeps this one. A row written after the stamp
    # and shown while the submit grades is counted by the attempt's
    # transactional refold of the open problem's help (fix round 1, F1:
    # ``ServerHintFold.held_reader``), and none is shown once the attempt
    # commits under the submission's key (``help_assists.mark_shown``).
    _stamp_help_rows(repository, params.session_id, params.latency_seconds)
    plan = _run(WB.submission_plan, repository, params.session_id)
    item = vault.practice_items.get(plan.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Unknown Practice Item {plan.practice_item_id}.")
    # An admitted exercise answers its admission's serve, made in that
    # practice session (while it is open; else the submit's own rule).
    practice_session_id = _practice_session(ctx, repository, admitted_in if _session_open(repository, admitted_in)
                                            else params.practice_session_id)
    # The serve is one pair (review F15): the one the request names, both
    # identifiers, or else the one the session kept, both identifiers. An
    # admitted exercise's kept serve is its admission's: a named one never
    # replaces it.
    named = None if (WB.exercise_pick(row) or {}).get("admitted_at") else _named_serve(params)
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
        # Fix rounds 4 and 5 (items 4-5): the problem's authored part (the
        # answer box's carried reveals) on its own; its book and its shown
        # checks and hints are the server's, joined once by the held fold.
        hints_used=plan.client_hints,
        authored_hints=plan.carried_hints,
        primed=plan.primed,
        assessment_contract_version_id=plan.assessment_contract_version_id,
        latency_seconds=params.latency_seconds,
        answer_confidence=params.answer_confidence,
        submission_id=plan.submission_id,
        scheduler_candidate_id=scheduler_candidate_id,
        plan_presentation_id=plan_presentation_id,
        declared_stuck=plan.composed.declared_stuck,
    )
    # H2b fix round 3, ruling R1: the attempt folds the answer box's shown
    # server hints by the keyless window (its practice session and item,
    # since the item's last attempt there, whatever their key) and takes
    # exactly those rows in its own transaction.
    attempt = submit_attempt_on(ctx, submission, entry_surface=plan.entry_surface, hint_window_fold=True)
    vault, repository = ctx.require_vault()
    _run(WB.mark_submitted, repository, params.session_id, attempt_id=str(attempt["attemptId"]),
         practice_session_id=practice_session_id)
    _close_answer_box_draft(repository, practice_session_id, plan.practice_item_id)
    _bind_help_rows(repository, params.session_id, plan, attempt_id=str(attempt["attemptId"]),
                    practice_session_id=practice_session_id)
    _queue_stuck_texts(ctx, vault, repository, params.session_id)
    return _answer({
        "attempt": attempt,
        "session": _view(vault, repository, params.session_id),
        "practiceSession": session_snapshot(repository, practice_session_id),
    })


def _close_answer_box_draft(repository, practice_session_id: str, practice_item_id: str) -> None:
    """Owner capture 2026-10-25 (B3, B4): the steps answered the item, so the
    practice screen's draft of it in this session (the answer box the
    learner left for steps: its retry key, its hints, its offer binding) is
    superseded, as an answer-box submit acknowledges its own. Left, it was
    restored when the item opened again: the earlier hints shown as this
    attempt's, and a submit under a key whose offer this attempt answered.
    A draft of another item is left alone. A failure is logged, never raised
    (the attempt is made)."""

    from learnloop_sidecar.logging import log_event

    try:
        repository.clear_practice_checkpoint_for_item(practice_session_id, practice_item_id)
    except Exception as exc:  # noqa: BLE001 - the attempt and its counts are made
        log_event("workbench_answer_box_draft_not_cleared", practice_item_id=practice_item_id,
                  error=type(exc).__name__)


def _stamp_help_rows(repository, session_id: str, latency_seconds: int | None) -> None:
    from learnloop.clock import utc_now_iso
    from learnloop.db.stores.help_assists import stamp_submitted

    row = _run(WB.session_row, repository, session_id)
    if not row.get("practice_item_id") or row["status"] != "open":
        return
    with repository.atomic():
        connection = repository.connection()
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                              ).fetchone() is None:
            return
        stamp_submitted(connection, submission_id=WB.submission_id_for(session_id),
                        practice_item_id=str(row["practice_item_id"]), submitted_at=utc_now_iso(),
                        latency_seconds=float(latency_seconds) if latency_seconds is not None else None)


def _bind_help_rows(repository, session_id: str, plan, *, attempt_id: str, practice_session_id: str) -> None:
    """RW2b: the practice session (set at Submit, the schema's rule) and the
    attempt on the problem's help rows, after the attempt committed. A
    failure is logged, never raised (the attempt and its counts are made)."""

    from learnloop.db.stores.help_assists import bind_workbench_rows
    from learnloop_sidecar.logging import log_event

    try:
        with repository.atomic():
            connection = repository.connection()
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                                  ).fetchone() is None:
                return
            bind_workbench_rows(connection, workbench_session_id=session_id, practice_session_id=practice_session_id,
                                attempt_id=attempt_id, submission_id=plan.submission_id,
                                practice_item_id=plan.practice_item_id)
    except Exception as exc:  # noqa: BLE001 -- telemetry never fails a submit
        log_event("workbench_help_bind_failed", session_id=session_id, error=type(exc).__name__)


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
    return _answer({"sessions": to_camel(_cleared(vault, repository, rows))})


@method("workbench.for_source", WorkbenchSourceInput)
def workbench_for_source(ctx: SidecarContext, params: WorkbenchSourceInput) -> dict[str, Any]:
    """The source's open or abandoned problems: the ``✎`` marks, the rail and
    RW6a's recap (``unfinished`` past ``workbench.open_session_days``)."""

    vault, repository = _require(ctx)
    rows = WB.sessions_for_source(repository, params.extraction_id, now=datetime.now(UTC),
                                  open_days=WB.open_session_days(vault))
    return _answer({"sessions": to_camel(_cleared(vault, repository, rows)),
                    "openSessionDays": WB.open_session_days(vault)})


@method("workbench.open_problems", WorkbenchOpenProblemsInput)
def workbench_open_problems(ctx: SidecarContext, params: WorkbenchOpenProblemsInput) -> dict[str, Any]:
    """UX Phase 3 (spec ux_learnloop_v1 §7.1, §10 3.3): Today's unfinished
    problems ("Exercise 5.9 -- 3 steps written · resume"), newest first, each
    with the source it opens in. A pure read; a problem whose source is gone,
    or whose statement is held out now, is left out.

    Fix round 1 (F3): so is a problem worked on an earlier reading of its
    book (the book was read again since). The Reader opens a book on its
    current reading, where that problem's anchors are another reading's
    spans and the workbench cannot reopen it; the Reader's own marks list the
    open reading's problems only, and Today offers no resume it cannot keep."""

    vault, repository = _require(ctx)
    rows = WB.open_problems(repository, now=datetime.now(UTC), open_days=WB.open_session_days(vault))
    problems = []
    readings: dict[str, str | None] = {}
    for summary in _cleared(vault, repository, rows):
        source_id = _source_id(repository, summary.get("extraction_id"))
        if source_id is None:
            continue
        if source_id not in readings:
            readings[source_id] = _current_reading(repository, source_id)
        if readings[source_id] != summary.get("extraction_id"):
            continue
        problems.append({**summary, "source_id": source_id})
    return _answer({"problems": to_camel(problems)})


def _cleared(vault, repository, summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A list's problems whose statement may be shown (fix round 5, R2): a
    picked exercise whose region is held out now is left out of the list
    (its steps are kept; it cannot be resumed while it is withheld)."""

    return [summary for summary in summaries
            if WB.statement_cleared(vault, repository, _run(WB.session_row, repository, summary["session_id"]))]
