"""Reader workbench RW4a RPCs: ask your library, its notes, compare and the tutor.

Desktop only (pinned in tests/test_mobile_allowlist.py). Each composes the
canonical-sources service under a caller the server derives (never one the
frontend names): the Reader's caller (``reading``), a workbench session's
item (``assisted_practice``), a cold administration (``cold_attempt``,
nothing retrieved). A follow-up (notes, compare, the tutor) is bound by the
ask's own stored caller, rebuilt on the server with today's cold status; a
follow-up never widens it by omitting or naming a session (Codex review F4).
Nothing here writes an attempt, evidence, mastery, certification, FSRS,
scheduler state or a plan. "Practice this question" is the existing
``find_practice`` RPC with a ``reader`` caller (one RPC, DL3's and RW1c's
too). Kill switches: ``library_ask.enabled``, ``library_ask.expand_graph``,
``reader_compare.enabled``; off, every RPC here refuses and the prompt
contract has no ``library_ask`` key.

**Never on the request path** (W12, UX §4.0; Codex review F6). The sidecar is
serial, so each model-backed RPC here (the ask, its notes, compare and the
tutor) starts its work on a small worker thread, as the intent box's router
does, and answers at once with a job: ``reader.library_job`` reads it (at
once: it never waits, since a wait would hold every request queued behind it;
the frontend paces its polls, Codex re-review F11), ``reader.library_job_cancel``
cancels it (the result is fenced:
a cancelled job never answers; a paid call already sent finishes and its
receipt and paid output are kept, as a cancelled Reader Ask's are). Opening
another source, peeking or saving meanwhile is answered at once.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import Field

from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval.policy import PolicyRefused
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
LIBRARY_ASK_RPCS: tuple[str, ...] = (
    "reader.library_ask",
    "reader.library_ask_notes",
    "reader.library_compare",
    "reader.library_ask_tutor",
    "reader.library_job",
    "reader.library_job_cancel",
)
#: The most jobs kept in memory for reading back (oldest dropped first).
MAX_KEPT_JOBS = 64


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW4a (absent while off)."""

    if not LA.library_ask_enabled(vault):
        return {}
    settings = vault.config.library_ask
    return {"library_ask": {
        "expand_graph": bool(settings.expand_graph),
        "personalized_default": bool(settings.personalized_default),
        "compare": LA.compare_enabled(vault),
    }}


def _require(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not LA.library_ask_enabled(vault):
        raise SidecarError("library_ask_disabled",
                           "Ask your library is switched off (library_ask.enabled, source_service.enabled or "
                           "reader_inquiry.enabled is false).")
    return vault, repository


def reader_caller(vault: Any, repository: Any, *, extraction_id: str | None,
                  workbench_session_id: str | None = None) -> Any:
    """The Reader's caller context, built on the server (spec §7.2, G19).

    The Reader context is ``reading``. Asked from inside a workbench session
    whose problem is bound to an item, it is that item's practice context
    (``assisted_practice``); while a cold administration of that item is
    open, ``cold_attempt`` (nothing is retrieved)."""

    from learnloop.instructional.policy import caller_for
    from learnloop.reader import workbench as WB

    item_id = None
    if workbench_session_id:
        try:
            session = WB.session_row(repository, workbench_session_id)
        except Exception as exc:  # noqa: BLE001 - an unknown session is the frontend's mistake
            raise SidecarError("not_found", f"Unknown workbench session {workbench_session_id}.") from exc
        item_id = session.get("practice_item_id") or None
        if item_id is not None and item_id not in vault.practice_items:
            item_id = None
    return caller_for(repository, "reader", extraction_id, item_id=item_id,
                      context="practice" if item_id else None)


def follow_up_caller(vault: Any, repository: Any, row: dict[str, Any], *,
                     workbench_session_id: str | None = None) -> Any:
    """A follow-up's caller: the ask's own stored binding (its item, when it
    was asked inside a bound workbench session), rebuilt on the server so the
    cold status is today's. A follow-up naming a session bound otherwise is
    refused; omitting it never widens the ask's policy (Codex review F4)."""

    from learnloop.instructional.policy import caller_for

    bound = (row.get("manifest") or {}).get("caller")
    if not isinstance(bound, dict):
        raise SidecarError("caller_mismatch", "This library question has no caller on record; ask it again.")
    item_id = bound.get("item_id") or None
    if workbench_session_id is not None:
        named = reader_caller(vault, repository, extraction_id=row.get("extraction_id"),
                              workbench_session_id=workbench_session_id)
        if (named.item_id or None) != item_id:
            raise SidecarError("caller_mismatch",
                               "This follow-up names a different practice item than its library question.")
    if item_id is not None and item_id not in vault.practice_items:
        # Fail closed: the item the ask was bound to is gone, so its exclusions
        # cannot be applied; nothing is read under a wider policy instead.
        raise SidecarError("caller_mismatch",
                           "The practice item this question was asked about is no longer in the vault.")
    return caller_for(repository, "reader", row.get("extraction_id"), item_id=item_id,
                      context="practice" if item_id else None)


def _caller_record(caller: Any, *, workbench_session_id: str | None = None) -> dict[str, Any]:
    from learnloop.source_retrieval.policy import derive_policy

    policy, reason = derive_policy(caller)
    record = {"kind": caller.kind, "ref": caller.ref, "context": caller.context, "item_id": caller.item_id,
              "policy": policy, "derived_from": reason}
    if workbench_session_id:
        record["workbench_session_id"] = workbench_session_id
    return record


def _ask_row(repository: Any, ask_id: str) -> dict[str, Any]:
    try:
        return LA.ask_row(repository, ask_id)
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc


# ---------------------------------------------------------------------------
# The jobs (never on the request path)
# ---------------------------------------------------------------------------

#: One job's work: given the worker's own repository, the result payload (or a SidecarError).
Work = Callable[[Any], dict[str, Any]]


@dataclass
class _Job:
    job_id: str
    kind: str
    ask_id: str | None
    started: float
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    result: dict[str, Any] | None = None
    error: SidecarError | None = None
    cancelled: bool = False


def _as_sidecar_error(exc: BaseException) -> SidecarError:
    if isinstance(exc, SidecarError):
        return exc
    if isinstance(exc, (LA.LibraryAskError, PolicyRefused)):
        return SidecarError(exc.code, str(exc))
    LOG.warning("library ask job failed: %s", type(exc).__name__, exc_info=exc)
    return SidecarError("internal_error", "LearnLoop couldn't finish that. Your question is kept; try again.",
                        retryable=True)


class LibraryJobs:
    """Library jobs in flight and just finished, kept for reading back (in memory)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _Job] = {}

    def start(self, ctx: SidecarContext, kind: str, ask_id: str | None, work: Work) -> _Job:
        from learnloop.ids import new_ulid

        job = _Job(f"ljob_{new_ulid()}", kind, ask_id, time.monotonic())
        with self._lock:
            self._kept[job.job_id] = job
            while len(self._kept) > MAX_KEPT_JOBS:
                self._kept.pop(next(iter(self._kept)))
        _vault, repository = ctx.require_vault()
        sqlite_path = repository.sqlite_path

        def run() -> None:
            from learnloop.ai.execution import record_model_calls
            from learnloop.db.repositories import Repository

            try:
                worker_repo = Repository.attach(sqlite_path)
                # Receipts are owned as the serial loop owns an RPC's (server._observed_model_calls).
                with record_model_calls(worker_repo, owner_kind="sidecar_rpc",
                                        owner_id=f"reader.library_{kind}:{job.job_id}"):
                    job.result = work(worker_repo)
            except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                job.error = _as_sidecar_error(exc)
            finally:
                job.done.set()

        if getattr(ctx, "library_ask_inline", False):
            run()
        else:
            threading.Thread(target=run, name=f"library-{kind}-{job.job_id}", daemon=True).start()
        return job

    def get(self, job_id: str) -> _Job | None:
        with self._lock:
            return self._kept.get(job_id)


def _jobs(ctx: SidecarContext) -> LibraryJobs:
    jobs = getattr(ctx, "library_ask_jobs", None)
    if jobs is None:
        jobs = LibraryJobs()
        ctx.library_ask_jobs = jobs  # type: ignore[attr-defined]
    return jobs


def _job_payload(job: _Job) -> dict[str, Any]:
    """The job as the wire reads it; a failed job raises its error."""

    base = {"job_id": job.job_id, "kind": job.kind, "ask_id": job.ask_id}
    with job.lock:
        cancelled = job.cancelled
    if cancelled:
        return versioned({**base, "state": "cancelled", "result": None})
    if not job.done.is_set():
        return versioned({**base, "state": "pending", "result": None})
    if job.error is not None:
        raise job.error
    return versioned({**base, "state": "done", "result": job.result})


def _start(ctx: SidecarContext, kind: str, ask_id: str | None, work: Work) -> dict[str, Any]:
    return _job_payload(_jobs(ctx).start(ctx, kind, ask_id, work))


class LibraryJobInput(ParamsModel):
    #: No wait: the read answers at once, so a poll never holds the serial loop
    #: (opening a source, peeking or saving behind it); the frontend paces its
    #: polls (Codex re-review F11).
    job_id: str


@method("reader.library_job", LibraryJobInput)
def reader_library_job(ctx: SidecarContext, params: LibraryJobInput) -> dict[str, Any]:
    """A library job's state, at once (never a wait on the request path)."""

    _require(ctx)
    job = _jobs(ctx).get(params.job_id)
    if job is None:
        raise SidecarError("not_found", "That library request is no longer kept; ask again.")
    return _job_payload(job)


class LibraryJobCancelInput(ParamsModel):
    job_id: str


@method("reader.library_job_cancel", LibraryJobCancelInput)
def reader_library_job_cancel(ctx: SidecarContext, params: LibraryJobCancelInput) -> dict[str, Any]:
    """Cancel a library job: it never answers after this (the result is fenced)."""

    _require(ctx)
    job = _jobs(ctx).get(params.job_id)
    if job is None:
        raise SidecarError("not_found", "That library request is no longer kept.")
    with job.lock:
        job.cancelled = True
    return versioned({"job_id": job.job_id, "kind": job.kind, "ask_id": job.ask_id, "state": "cancelled",
                      "result": None})


# ---------------------------------------------------------------------------
# The RPCs
# ---------------------------------------------------------------------------

class LibraryAskInput(ParamsModel):
    query: str = Field(min_length=1, max_length=4000)
    entry: str = "reader"
    extraction_id: str | None = None
    #: The passage the question is about: the selection, or the reading passage.
    span_ids: list[str] = Field(default_factory=list, max_length=40)
    learning_object_ids: list[str] = Field(default_factory=list, max_length=20)
    personalized: bool | None = None
    expand: list[str] | None = None
    workbench_session_id: str | None = None


@method("reader.library_ask", LibraryAskInput)
def reader_library_ask(ctx: SidecarContext, params: LibraryAskInput) -> dict[str, Any]:
    """Passages from the learner's library for a question, sources first (spec §7.3)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.instructional.interventions import record_shown_spans
    from learnloop.instructional.sources import propose_sources

    vault, repository = _require(ctx)
    extraction_id = None
    if params.extraction_id:
        extraction_id = resolve_extraction_id(repository, params.extraction_id)
        if extraction_id is None:
            raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    caller = reader_caller(vault, repository, extraction_id=extraction_id,
                           workbench_session_id=params.workbench_session_id)
    record = _caller_record(caller, workbench_session_id=params.workbench_session_id)

    def work(worker_repo: Any) -> dict[str, Any]:
        def find(query: str, **kwargs: Any) -> Any:
            return propose_sources(vault, worker_repo, query, caller=caller, **kwargs)

        def shown(keys: Any, ask_id: str) -> list[str]:
            return record_shown_spans(worker_repo, list(keys), context="library", entity_type="library_ask",
                                      entity_id=ask_id)

        return LA.ask_library(
            vault, worker_repo, params.query, find=find, caller=record, record_shown=shown,
            entry=params.entry, extraction_id=extraction_id, anchor_span_ids=params.span_ids,
            learning_object_ids=params.learning_object_ids, personalized=params.personalized,
            expand=params.expand,
        )

    return _start(ctx, "ask", None, work)


class LibraryAskIdInput(ParamsModel):
    ask_id: str


@method("reader.library_ask_notes", LibraryAskIdInput)
def reader_library_ask_notes(ctx: SidecarContext, params: LibraryAskIdInput) -> dict[str, Any]:
    """The organizer's line per passage (one listwise call; cached per ask)."""

    vault, repository = _require(ctx)
    _ask_row(repository, params.ask_id)
    client = getattr(ctx, "library_organizer_client", None)

    def work(worker_repo: Any) -> dict[str, Any]:
        return LA.organize(vault, worker_repo, params.ask_id, client=client)

    return _start(ctx, "notes", params.ask_id, work)


class LibraryCompareInput(ParamsModel):
    ask_id: str
    pinned_span_keys: list[str] = Field(min_length=2, max_length=20)
    #: The open source, whose passage leads the table when it is pinned.
    open_source_id: str | None = None
    #: Optional; when given it must name the ask's own binding (never widens it).
    workbench_session_id: str | None = None


@method("reader.library_compare", LibraryCompareInput)
def reader_library_compare(ctx: SidecarContext, params: LibraryCompareInput) -> dict[str, Any]:
    """How the pinned passages' sources treat the question (display only until RW4d)."""

    from learnloop.instructional.interventions import record_shown_spans
    from learnloop.instructional.sources import propose_comparison

    vault, repository = _require(ctx)
    if not LA.compare_enabled(vault):
        raise SidecarError("reader_compare_disabled",
                           "Comparing sources is switched off (reader_compare.enabled or source_service.compare).")
    row = _ask_row(repository, params.ask_id)
    caller = follow_up_caller(vault, repository, row, workbench_session_id=params.workbench_session_id)

    def work(worker_repo: Any) -> dict[str, Any]:
        def bound_compare(query: str, **kwargs: Any) -> Any:
            return propose_comparison(vault, worker_repo, query, caller=caller, **kwargs)

        def shown(keys: Any, ask_id: str) -> list[str]:
            return record_shown_spans(worker_repo, list(keys), context="library", entity_type="library_ask",
                                      entity_id=ask_id)

        return LA.compare(vault, worker_repo, params.ask_id, pinned_keys=params.pinned_span_keys,
                          compare_sources=bound_compare, record_shown=shown, open_source_id=params.open_source_id)

    return _start(ctx, "compare", params.ask_id, work)


class LibraryAskTutorInput(ParamsModel):
    ask_id: str
    pinned_span_keys: list[str] = Field(min_length=1, max_length=20)
    question: str | None = Field(default=None, max_length=4000)


@method("reader.library_ask_tutor", LibraryAskTutorInput)
def reader_library_ask_tutor(ctx: SidecarContext, params: LibraryAskTutorInput) -> dict[str, Any]:
    """The tutor on request, answering only from the pinned passages (§3.4 item 11)."""

    from learnloop.ai.errors import CodexUnavailable
    from learnloop.reader import reader_dialogue as RD
    from learnloop.source_retrieval.policy import derive_policy
    from learnloop.source_retrieval.tutor import PinnedSpanProvider
    from learnloop.tutor.tutor_qa import HeldOutMaterialRefused, QuestionLimitReached, TutorQAError
    from learnloop_sidecar.handlers.ai_providers import provider_label, ready_tutor_qa_provider
    from learnloop_sidecar.handlers.learner_gaps import queue_tutor_question_gap

    vault, repository = _require(ctx)
    row = _ask_row(repository, params.ask_id)
    caller = follow_up_caller(vault, repository, row)
    policy, _reason = derive_policy(caller)
    if policy == "cold_attempt":
        raise SidecarError("cold_attempt", "Nothing is retrieved for the tutor while a cold attempt is open.")
    item = vault.practice_items.get(caller.item_id) if caller.item_id else None
    provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError("provider_unavailable",
                           f"{provider_label(provider_name)} is unavailable for the tutor.", retryable=True)
    provider = LA.OnlyPinned(PinnedSpanProvider(params.pinned_span_keys), item=item)

    def work(worker_repo: Any) -> dict[str, Any]:
        def answer(*, question_md: str, extraction_id: str, span_id: str) -> dict[str, Any]:
            return RD.ask(vault, worker_repo, client, extraction_id=extraction_id, span_id=span_id,
                          question_md=question_md, source_span_provider=provider)

        try:
            result = LA.ask_tutor(vault, worker_repo, params.ask_id, pinned_keys=params.pinned_span_keys,
                                  question_md=params.question, ask=answer)
        except HeldOutMaterialRefused as exc:
            raise SidecarError("exam_material", str(exc)) from exc
        except QuestionLimitReached as exc:
            raise SidecarError("question_limit_reached", str(exc),
                               details={"limit": exc.limit, "used": exc.used, "context": exc.context}) from exc
        except (RD.ReaderDialogueError, TutorQAError) as exc:
            raise SidecarError("validation_error", str(exc)) from exc
        except (CodexUnavailable, TimeoutError) as exc:
            raise SidecarError("provider_unavailable",
                               f"{provider_label(provider_name)} is unavailable for the tutor.",
                               retryable=True) from exc
        # Learner-text gaps: the pinned question is read for a named gap, as
        # any Reader question is (Codex review F3).
        result["learner_gap"] = queue_tutor_question_gap(ctx, vault, worker_repo, result["event_id"], None)
        return result

    return _start(ctx, "tutor", params.ask_id, work)


__all__ = ["LIBRARY_ASK_RPCS", "LibraryJobs", "follow_up_caller", "prompt_contract_fields", "reader_caller"]
