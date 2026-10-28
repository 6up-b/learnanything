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

import copy
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pydantic import Field

from learnloop.source_retrieval import kept_comparisons as KC
from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval.policy import PolicyRefused
from learnloop_sidecar.background_jobs import background_jobs
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
    fields: dict[str, Any] = {
        "expand_graph": bool(settings.expand_graph),
        "personalized_default": bool(settings.personalized_default),
        "compare": LA.compare_enabled(vault),
    }
    if scope_enabled(vault):
        # Reader CA3: compare from anywhere (absent while off: RW4a's contract).
        fields["compare_scope"] = True
    if KC.by_point_enabled(vault):
        # Reader CA4: the table by point (absent while off: by book, as today).
        fields["compare_by_point"] = True
    return {"library_ask": fields}


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
#: A job's delivery check (Reader RW4b fix round 6, F7): given the finished
#: result, what may go out NOW. Run on every read of the job, never cached.
Deliver = Callable[[dict[str, Any]], dict[str, Any]]


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
    #: Revalidates the kept result at each delivery (exercise jobs: the
    #: statement reader's withholding gate); None for a job that needs none.
    deliver: Deliver | None = None
    #: Plan-first transport T1: the OpenRouter offer the job's requests made
    #: (a ``plan_fallback`` hint), relayed by the read that finds it done.
    fallback_offer: dict[str, Any] | None = None


def _as_sidecar_error(exc: BaseException) -> SidecarError:
    if isinstance(exc, SidecarError):
        return exc
    if isinstance(exc, (LA.LibraryAskError, PolicyRefused)):
        return SidecarError(exc.code, str(exc))
    LOG.warning("library ask job failed: %s", type(exc).__name__, exc_info=exc)
    return SidecarError("internal_error", "LearnLoop couldn't finish that. Your question is kept; try again.",
                        retryable=True)


def fenced(job: _Job, write: Callable[[], Any]) -> bool:
    """Run ``write`` (a job's binding of its result to its ask) unless the job
    is cancelled; False when it was. Under the job's lock, so a cancel (or a
    newer job superseding it) and the write never interleave: once a job is
    cancelled it binds nothing (Reader CA3, Codex final verify F12)."""

    with job.lock:
        if job.cancelled:
            return False
        write()
        return True


class LibraryJobs:
    """Library jobs in flight and just finished, kept for reading back (in memory).

    Reader CA3 (Codex final verify F10): also the passages of each ask's
    latest comparison that was not stored (its comparison step skipped or
    unavailable, or fewer than two books), under their own id, so the tutor
    about it reads every one of them from the server. A stored comparison is
    named by its durable id instead; these are kept as long as the sidecar
    runs (as many asks as jobs are kept), and one no longer kept is said so."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _Job] = {}
        #: ask id -> (passages id, every passage its latest unstored comparison read).
        self._passages: dict[str, tuple[str, list[str]]] = {}

    def remember_passages(self, ask_id: str, keys: list[str]) -> str:
        from learnloop.ids import new_ulid

        passages_id = f"cmpp_{new_ulid()}"
        with self._lock:
            self._passages.pop(ask_id, None)
            self._passages[ask_id] = (passages_id, list(keys))
            while len(self._passages) > MAX_KEPT_JOBS:
                self._passages.pop(next(iter(self._passages)))
        return passages_id

    def forget_passages(self, ask_id: str) -> None:
        """The ask now shows a stored comparison: its unstored one is no longer shown."""

        with self._lock:
            self._passages.pop(ask_id, None)

    def passages(self, ask_id: str) -> tuple[str, list[str]] | None:
        with self._lock:
            found = self._passages.get(ask_id)
        return None if found is None else (found[0], list(found[1]))

    def start(self, ctx: SidecarContext, kind: str, ask_id: str | None, work: Work, *,
              deliver: Deliver | None = None, supersede: bool = False,
              on_job: Callable[[_Job], None] | None = None) -> _Job:
        """``supersede`` (Reader CA3, Codex final verify F12): this job
        replaces the unfinished jobs of its kind for the same ask (a
        refinement of a comparison): they are cancelled, so none of them
        answers or binds after this one started, even when the frontend's own
        cancel comes late. ``on_job`` is given the job before its work runs."""

        from learnloop.ids import new_ulid

        job = _Job(f"ljob_{new_ulid()}", kind, ask_id, time.monotonic(), deliver=deliver)
        with self._lock:
            older = [other for other in self._kept.values() if supersede and ask_id is not None
                     and other.kind == kind and other.ask_id == ask_id and not other.done.is_set()]
            self._kept[job.job_id] = job
            while len(self._kept) > MAX_KEPT_JOBS:
                self._kept.pop(next(iter(self._kept)))
        # Each under its own lock only (a fenced write holds its job's lock
        # and may take this one's), before this job's work starts.
        for other in older:
            with other.lock:
                other.cancelled = True
        if on_job is not None:
            on_job(job)
        _vault, repository = ctx.require_vault()
        sqlite_path = repository.sqlite_path

        # T1 landing (redesign D): the job belongs to the action whose request started it,
        # and carries that action's token when it is granted (taken here, in the request).
        from learnloop.ai import plan_fallback as _plan_fallback

        grant, origin = _plan_fallback.unit_token(_vault.root), _plan_fallback.unit_origin()
        stamp = _plan_fallback.unit_stamp(_vault.root)  # its vault and epoch, now
        _plan_fallback.note_unit("job", job.job_id)

        def run() -> None:
            from learnloop.ai import plan_fallback
            from learnloop.ai.execution import record_model_calls
            from learnloop.db.repositories import Repository

            # Plan-first transport T1: the job's thread has no RPC collector;
            # it keeps its own offers and the read that finds it done relays them.
            with plan_fallback.unit(grant, origin, stamp) as offers:
                try:
                    worker_repo = Repository.attach(sqlite_path)
                    # Receipts are owned as the serial loop owns an RPC's (server._observed_model_calls).
                    with record_model_calls(worker_repo, owner_kind="sidecar_rpc",
                                            owner_id=f"reader.library_{kind}:{job.job_id}"):
                        job.result = work(worker_repo)
                except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                    job.error = _as_sidecar_error(exc)
                finally:
                    job.fallback_offer = offers.hint()
                    job.done.set()

        if getattr(ctx, "library_ask_inline", False):
            run()
        else:
            # Owned by the context: its close cancels the job's further requests
            # and joins it, bounded (test-thread-leak review F1).
            background_jobs(ctx).spawn(run, name=f"library-{kind}-{job.job_id}")
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
    from learnloop.ai import plan_fallback

    plan_fallback.relay_job_offer(job)
    if job.error is not None:
        raise job.error
    result = job.result
    if job.deliver is not None and result is not None:
        # Fix round 6 (F7): what a finished job kept is checked again as it
        # goes out (an exercise held out since the job finished is dropped);
        # the kept result itself is never changed.
        result = job.deliver(copy.deepcopy(result))
    return versioned({**base, "state": "done", "result": result})


def _start(ctx: SidecarContext, kind: str, ask_id: str | None, work: Work, *,
           deliver: Deliver | None = None, supersede: bool = False,
           on_job: Callable[[_Job], None] | None = None) -> dict[str, Any]:
    return _job_payload(_jobs(ctx).start(ctx, kind, ask_id, work, deliver=deliver, supersede=supersede,
                                         on_job=on_job))


def deliver_comparison(ctx: SidecarContext, ask_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """A comparison job's result as it may go out NOW (RW4d fix round 5, F2),
    at every delivery (the first one, and each cached read through
    ``reader.library_job``): a comparison any of whose contributing passages
    is withheld now, or whose provenance cannot be resolved, is refused whole
    (``comparison_withheld``: no table, no keep state, no take). Otherwise its
    keep state is read again (a keep removed or withheld since the job ended
    is not shown)."""

    from learnloop.reader import source_objects as SO

    comparison_id = result.get("comparison_id")
    if not comparison_id:
        return result  # nothing was compared (too few sources): no comparison to withhold
    vault, repository = ctx.require_vault()
    if SO.withheld_comparisons(vault, repository, [(str(comparison_id), ask_id)]):
        raise SidecarError("comparison_withheld",
                           "Part of this comparison is held out for an exam now (or its sources can't be checked), "
                           "so it isn't shown.")
    if "kept" in result:
        result["kept"] = KC.compare_kept_state(vault, repository, ask_id, str(comparison_id))
    return result


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

        result = LA.ask_library(
            vault, worker_repo, params.query, find=find, caller=record, record_shown=shown,
            entry=params.entry, extraction_id=extraction_id, anchor_span_ids=params.span_ids,
            learning_object_ids=params.learning_object_ids, personalized=params.personalized,
            expand=params.expand,
        )
        if KC.keep_enabled(vault):
            # RW4d: "you compared these on …" for passages a kept comparison holds
            # (absent while reader_compare.keep_enabled is off: RW4a's answer).
            result["compared_on"] = KC.compared_on(vault, worker_repo, [hit["key"] for hit in result["hits"]])
        return result

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


#: An anchor's blocks: the selection a comparison may start from. A
#: request-size guardrail. The tutor about a comparison never sends its
#: passages (Codex final verify F10): it names the comparison (stored) or its
#: passages kept on the server (not stored), so no request bound limits it.
ANCHOR_SPANS_MAX = 40


class _PinnedCompareInput(ParamsModel):
    """RW4a/RW4d's request, exactly: what the RPC takes while
    ``reader_compare.scope_enabled`` is off (CA3 off = today)."""

    ask_id: str
    pinned_span_keys: list[str] = Field(min_length=2, max_length=20)
    #: The open source, whose passage leads the table when it is pinned.
    open_source_id: str | None = None
    #: Optional; when given it must name the ask's own binding (never widens it).
    workbench_session_id: str | None = None
    #: RW4d: "a geometric view", "an application" (used only while
    #: reader_compare.keep_enabled is on; otherwise refused when given).
    requested_perspectives: list[str] = Field(default_factory=list, max_length=8)


class LibraryCompareInput(ParamsModel):
    """One comparison request for every door (Reader CA3, K12; §4.1).

    While ``reader_compare.scope_enabled`` is off it is validated as
    :class:`_PinnedCompareInput` (an ask and at least two pins; the CA3 fields
    are refused as unknown), so the RPC is today's exactly. On: a door with no
    library answer names no ``ask_id`` and gives its ``question`` (the
    comparison's own ask row is opened, bound by the server-derived caller); an
    ``anchor_span_ids`` passage in ``extraction_id`` needs no pin; ``source_ids``
    only narrow (refused if they would widen the scope). The policy is never
    the client's: it is derived from where the call comes from."""

    ask_id: str | None = None
    pinned_span_keys: list[str] = Field(default_factory=list, max_length=20)
    #: The open source, whose passage leads the table when it is pinned.
    open_source_id: str | None = None
    #: Optional; when given it must name the ask's own binding (never widens it).
    workbench_session_id: str | None = None
    #: RW4d: "a geometric view", "an application" (used only while
    #: reader_compare.keep_enabled is on; otherwise refused when given).
    requested_perspectives: list[str] = Field(default_factory=list, max_length=8)
    # -- Reader CA3 (reader_compare.scope_enabled) --
    door: Literal["selection", "ask_box", "tutor_offer", "library_answer", "refine", "pins"] | None = None
    #: The comparison's question, for a door with no library answer (no ask_id).
    question: str | None = Field(default=None, max_length=4000)
    #: The anchor's source (the open book) and its passage.
    extraction_id: str | None = None
    anchor_span_ids: list[str] = Field(default_factory=list, max_length=ANCHOR_SPANS_MAX)
    #: The books named or chosen (they only narrow the scope).
    source_ids: list[str] = Field(default_factory=list, max_length=40)
    #: The tutor's offer this comparison answers (recorded on its ask row).
    tool_call_id: str | None = None


_CA3_FIELDS = ("door", "question", "extraction_id", "anchor_span_ids", "source_ids", "tool_call_id")


def scope_enabled(vault: Any) -> bool:
    """Reader CA3 is on: its switch and the comparison it builds on."""

    return LA.compare_enabled(vault) and bool(vault.config.reader_compare.scope_enabled)


@method("reader.library_compare", LibraryCompareInput)
def reader_library_compare(ctx: SidecarContext, params: LibraryCompareInput) -> dict[str, Any]:
    """How the pinned passages' sources treat the question (display only until RW4d)."""

    from learnloop.instructional.interventions import record_shown_spans
    from learnloop.instructional.sources import propose_comparison

    vault, repository = _require(ctx)
    if not LA.compare_enabled(vault):
        raise SidecarError("reader_compare_disabled",
                           "Comparing sources is switched off (reader_compare.enabled or source_service.compare).")
    scoped = scope_enabled(vault)
    if not scoped:
        # CA3 off: today's request exactly (an ask, two pins, no CA3 field).
        _PinnedCompareInput.model_validate(params.model_dump(exclude_defaults=True))
        ask_id = str(params.ask_id)
    else:
        ask_id = _open_for_door(ctx, vault, repository, params)
    row = _ask_row(repository, ask_id)
    caller = follow_up_caller(vault, repository, row, workbench_session_id=params.workbench_session_id)
    keep = KC.keep_enabled(vault)
    perspectives = KC.clean_perspectives(params.requested_perspectives, limit=KC.max_perspectives(vault))
    if perspectives and not keep:
        raise SidecarError("reader_compare_keep_disabled",
                           "Requested perspectives are switched off (reader_compare.keep_enabled is false).")
    scope = _door_scope(repository, row, params) if scoped else None
    by_point = KC.by_point_enabled(vault)
    jobs = _jobs(ctx)
    #: The job this request runs as (given before its work starts).
    running: dict[str, _Job] = {}

    def bind(write: Callable[[], None], passage_keys: Any, comparison_id: str | None) -> dict[str, Any]:
        """CA3 (Codex final verify F10, F12): the result binds its ask only
        while its job is live (not cancelled, not superseded by a newer
        comparison of the ask); a comparison that was not stored keeps its
        passages on the server, named by their own id."""

        bound: dict[str, Any] = {}

        def binding() -> None:
            write()
            if comparison_id is None and passage_keys:
                bound["passages_id"] = jobs.remember_passages(ask_id, list(passage_keys))
            else:
                jobs.forget_passages(ask_id)

        fenced(running["job"], binding)
        return bound

    def work(worker_repo: Any) -> dict[str, Any]:
        def bound_compare(query: str, **kwargs: Any) -> Any:
            return propose_comparison(vault, worker_repo, query, caller=caller, **kwargs)

        def shown(keys: Any, ask_id: str) -> list[str]:
            return record_shown_spans(worker_repo, list(keys), context="library", entity_type="library_ask",
                                      entity_id=ask_id)

        try:
            table = LA.compare(vault, worker_repo, ask_id, pinned_keys=params.pinned_span_keys,
                               compare_sources=bound_compare, record_shown=shown,
                               open_source_id=params.open_source_id, requested_perspectives=perspectives,
                               **({"scope": scope, "bind": bind} if scope is not None else {}),
                               # Reader CA4: v2 by point (off: v1, by book, as today).
                               **({"by_point": True} if by_point else {}))
        except PolicyRefused as exc:
            raise SidecarError(exc.code, "That book isn't one this comparison may read here."
                               if exc.code == "scope_refused" else str(exc)) from exc
        if keep:
            # RW4d: whether this comparison is kept already (absent while off).
            table["kept"] = KC.compare_kept_state(vault, worker_repo, ask_id, table.get("comparison_id"))
        if scope is not None:
            # CA3: the books this comparison could read, for "+ add a book".
            from learnloop_sidecar.handlers.compare_scope import books_payload

            table["library"] = books_payload(vault, worker_repo, caller)
        return table

    # RW4d's whole-comparison withholding at delivery is installed only while
    # keeping is on: off, the compare job is 3988cf778's (fix round 6, F4).
    # CA3 (F12): a newer comparison of the ask supersedes the older ones (off: today's jobs).
    return _start(ctx, "compare", ask_id, work,
                  deliver=(lambda result: deliver_comparison(ctx, ask_id, result)) if keep else None,
                  supersede=scope is not None, on_job=lambda job: running.update(job=job))


def _open_for_door(ctx: SidecarContext, vault: Any, repository: Any, params: LibraryCompareInput) -> str:
    """CA3: the ask this request binds by: the one it names, else (a door with
    no library answer) the comparison's own row, opened under the caller the
    server derives from the open book and workbench session (G19)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id

    if params.ask_id is not None:
        if params.question is not None or params.anchor_span_ids or params.extraction_id or params.tool_call_id:
            raise SidecarError("validation_error",
                               "A comparison of a library answer takes its question and anchor from that answer.")
        return params.ask_id
    if not params.door or params.door == "pins":
        raise SidecarError("validation_error", "A comparison names the door it came through.")
    if params.pinned_span_keys:
        raise SidecarError("validation_error", "Pins belong to a library answer: name its ask.")
    extraction_id = None
    if params.extraction_id:
        extraction_id = resolve_extraction_id(repository, params.extraction_id)
        if extraction_id is None:
            raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    caller = reader_caller(vault, repository, extraction_id=extraction_id,
                           workbench_session_id=params.workbench_session_id)
    record = _caller_record(caller, workbench_session_id=params.workbench_session_id)
    if record.get("policy") == "cold_attempt":
        raise SidecarError("cold_attempt", "Nothing is compared while a check on your own is open.")
    try:
        return LA.open_comparison(vault, repository, question=params.question or "", caller=record,
                                  door=params.door, extraction_id=extraction_id,
                                  anchor_span_ids=params.anchor_span_ids, tool_call_id=params.tool_call_id)
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc


def _door_scope(repository: Any, row: dict[str, Any], params: LibraryCompareInput) -> dict[str, Any]:
    """CA3: the request's scope, from the ask row (its anchor, never one the
    follow-up names) and the books the request names."""

    door = params.door or ("pins" if params.pinned_span_keys else None)
    if door is None:
        raise SidecarError("validation_error", "A comparison names the door it came through.")
    anchor: list[str] = []
    if row.get("extraction_id") and (row.get("manifest") or {}).get("comparison_only"):
        anchor = [f"{row['extraction_id']}:{span}" for span in (row.get("anchor") or {}).get("span_ids") or ()]
    return {"door": door, "anchor_keys": anchor, "source_ids": list(params.source_ids)}


class _PinnedTutorInput(ParamsModel):
    """Today's request, exactly: what the RPC takes while
    ``reader_compare.scope_enabled`` is off (CA3 off = today)."""

    ask_id: str
    pinned_span_keys: list[str] = Field(min_length=1, max_length=20)
    question: str | None = Field(default=None, max_length=4000)


class LibraryAskTutorInput(ParamsModel):
    """The tutor over the pins, or (Reader CA3) over the comparison shown.

    Only while ``reader_compare.scope_enabled`` is on (refused as unknown
    while off), one of: ``comparison_id``, the stored comparison this ask
    shows, whose passages the server reads from the stored comparison (Codex
    re-review F10); ``passages_id``, the comparison this ask shows that was
    not stored, whose passages the server kept when it showed it (Codex final
    verify F10). Either way every passage it compared (an anchor of up to 40
    blocks and one passage per book) is answered from, the tutor's context
    budget saying what it left out, and no passage of it travels in the
    request. ``pinned_span_keys``: the pins (today's bound), added to it."""

    ask_id: str
    pinned_span_keys: list[str] = Field(default_factory=list, max_length=20)
    question: str | None = Field(default=None, max_length=4000)
    comparison_id: str | None = None
    passages_id: str | None = None


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
    if not scope_enabled(vault):
        # CA3 off: today's request exactly (at least one pin, no comparison).
        _PinnedTutorInput.model_validate(params.model_dump(exclude_defaults=True))
    row = _ask_row(repository, params.ask_id)
    pinned_keys = list(params.pinned_span_keys)
    if params.comparison_id is not None and params.passages_id is not None:
        raise SidecarError("validation_error", "Ask about one comparison: its id or its passages, not both.")
    if params.comparison_id is not None:
        try:
            compared = LA.comparison_passage_keys(repository, params.ask_id, params.comparison_id)
        except LA.LibraryAskError as exc:
            raise SidecarError(exc.code, str(exc)) from exc
        pinned_keys = list(dict.fromkeys([*compared, *pinned_keys]))
    elif params.passages_id is not None:
        kept = _jobs(ctx).passages(params.ask_id)
        if kept is None:
            raise SidecarError("not_found", "That comparison is no longer kept; compare again.")
        if kept[0] != params.passages_id:
            raise SidecarError("validation_error", "That comparison isn't the one this question shows.")
        pinned_keys = list(dict.fromkeys([*kept[1], *pinned_keys]))
    if not pinned_keys:
        raise SidecarError("validation_error", "Pin the passages the tutor should answer from.")
    caller = follow_up_caller(vault, repository, row)
    policy, _reason = derive_policy(caller)
    if policy == "cold_attempt":
        raise SidecarError("cold_attempt", "Nothing is retrieved for the tutor while a cold attempt is open.")
    item = vault.practice_items.get(caller.item_id) if caller.item_id else None
    provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError("provider_unavailable",
                           f"{provider_label(provider_name)} is unavailable for the tutor.", retryable=True)
    provider = LA.OnlyPinned(PinnedSpanProvider(pinned_keys), item=item)

    def work(worker_repo: Any) -> dict[str, Any]:
        def answer(*, question_md: str, extraction_id: str, span_id: str) -> dict[str, Any]:
            return RD.ask(vault, worker_repo, client, extraction_id=extraction_id, span_id=span_id,
                          question_md=question_md, source_span_provider=provider)

        try:
            result = LA.ask_tutor(vault, worker_repo, params.ask_id, pinned_keys=pinned_keys,
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
