"""Adaptive hints H2a RPCs: hints written for the learner's work (spec_adaptive_hints_v1 §4.1, §5, §7.1).

Desktop only (pinned in tests/test_mobile_allowlist.py); no frontend calls
them until H2b's panel, so the practice screen is unchanged either way.

**Never on the request path.** The sidecar is serial and a written hint takes
seconds (the chooser's 3 s time box, then the writer), so, as RW4a's library
jobs (Codex review F6 there), ``practice.request_hint`` answers at once with a
job, and the draft flushes and other RPCs are answered meanwhile. An
immediate answer (adaptive hints off, a diagnostic block) is ``done`` at once
with no job thread and no model call.

**Shown when delivered.** ``practice.hint_job`` reads a job at once (never a
wait). The read that returns a ready hint DELIVERS it: its prepared
``help_assists`` row becomes ``shown = 1`` (``learnloop.hints.service.deliver``),
and a key overlap writes the ``reveal_events`` ``tutor_answer`` row with basis
``hint:<kind>:L<level>`` in the same transaction (the reveal ledger's writer
is the attempt package's, so it is written here; a failed reveal write shows
nothing and leaves the job deliverable, review round 2, V4). ``practice.cancel_hint`` before delivery (the screen
took the item's own hint instead) leaves the row ``shown = 0``: it counts
nothing (G-H3). A crash before delivery leaves it unshown too. A read after
the submission committed its attempt (the hint finished before or after the
submit) delivers nothing and answers without the hint's text (review F1):
its count could no longer be taken. A delivered hint schedules H1's lazy
learner-route merge in the background (§4.3.1 row 3, review F9).

**Counted at submit.** ``submit_attempt`` and ``submit_dont_know`` fold the
submission's shown server rows (``learnloop_sidecar.handlers.practice``):
levels 1-3 add to ``hints_used``, levels 4-5 set ``primed``.

``practice.answer_discriminating`` records the learner's answer to a
discriminating question (fire-and-forget safe): an assist row, never part of
the submitted answer; it moves no posterior and writes no probe observation.
"""

from __future__ import annotations

from contextlib import nullcontext

from dataclasses import dataclass, field
import logging
import threading
import time
from typing import Any, Callable, Literal

from pydantic import Field

from learnloop.ai import plan_fallback
from learnloop.hints import service as hint_service
from learnloop.hints.map_builder import schedule_merge_after_hint
from learnloop.hints.service import HintRequestError, HintRequestV1, adaptive_enabled
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
HINT_SERVICE_RPCS: tuple[str, ...] = (
    "practice.request_hint",
    "practice.hint_job",
    "practice.cancel_hint",
    "practice.answer_discriminating",
)
#: The most jobs kept in memory for reading back (oldest dropped first).
MAX_KEPT_JOBS = 32


@dataclass
class _HintJob:
    job_id: str
    practice_item_id: str
    started: float
    #: The vault the job writes to: a read after a vault switch never
    #: delivers it into another vault.
    sqlite_path: str = ""
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    result: dict[str, Any] | None = None
    error: SidecarError | None = None
    cancelled: bool = False
    delivered: bool = False
    #: Plan-first transport T1: the OpenRouter offer the job's requests made
    #: (a ``plan_fallback`` hint), relayed by the read that finds it done.
    fallback_offer: dict[str, Any] | None = None
    #: A ready hint the read could not deliver (H2a review F1): the
    #: delivery outcome, and the job answers without the hint from then on.
    refused: str | None = None


class HintJobs:
    """Hint jobs in flight and just finished (in memory, per sidecar)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _HintJob] = {}

    def start(self, ctx: SidecarContext, practice_item_id: str,
              work: Callable[[Any, Callable[[], bool]], dict[str, Any]]) -> _HintJob:
        from learnloop.ids import new_ulid

        _vault, repository = ctx.require_vault()
        sqlite_path = repository.sqlite_path
        job = _HintJob(f"hjob_{new_ulid()}", practice_item_id, time.monotonic(), sqlite_path=str(sqlite_path))
        with self._lock:
            self._kept[job.job_id] = job
            while len(self._kept) > MAX_KEPT_JOBS:
                self._kept.pop(next(iter(self._kept)))

        # T1 landing review: the learner started this job, so it carries their grant,
        # captured here in their request (a worker thread never inherits one).
        from learnloop.ai import plan_fallback as _plan_fallback

        grant = _plan_fallback.capture_grant(_vault.root)
        # Round 2: a job the learner did not press (opening a book's margin notes or
        # reading path, a suggestion) asks nothing either: a grant could never serve it.
        asked = _plan_fallback.is_pressed()

        def cancelled() -> bool:
            with job.lock:
                return job.cancelled

        def run() -> None:
            from learnloop.ai.execution import record_model_calls
            from learnloop.db.repositories import Repository

            # Plan-first transport T1: the job's thread has no RPC collector;
            # it keeps its own offers and the read that finds it done relays them.
            with plan_fallback.job_grant(grant), \
                (nullcontext() if asked else plan_fallback.quiet()), plan_fallback.collecting() as offers:
                try:
                    worker_repo = Repository.attach(sqlite_path)
                    # Receipts are owned as the serial loop owns an RPC's; the
                    # chooser's and writer's own observers name their owner kinds.
                    with record_model_calls(worker_repo, owner_kind="sidecar_rpc",
                                            owner_id=f"practice.request_hint:{job.job_id}"):
                        job.result = work(worker_repo, cancelled)
                except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                    job.error = _as_sidecar_error(exc)
                finally:
                    job.fallback_offer = offers.hint()
                    job.done.set()

        if getattr(ctx, "hints_inline", False):
            run()
        else:
            threading.Thread(target=run, name=f"hint-{job.job_id}", daemon=True).start()
        return job

    def get(self, job_id: str) -> _HintJob | None:
        with self._lock:
            return self._kept.get(job_id)


def _as_sidecar_error(exc: BaseException) -> SidecarError:
    if isinstance(exc, SidecarError):
        return exc
    if isinstance(exc, HintRequestError):
        return SidecarError(exc.code, str(exc), details={"field": exc.field} if exc.field else None)
    LOG.warning("hint job failed: %s", type(exc).__name__, exc_info=exc)
    return SidecarError("internal_error", "LearnLoop couldn't write a hint just now. Try again.", retryable=True)


def _jobs(ctx: SidecarContext) -> HintJobs:
    jobs = getattr(ctx, "hint_jobs", None)
    if jobs is None:
        jobs = HintJobs()
        ctx.hint_jobs = jobs  # type: ignore[attr-defined]
    return jobs


def _immediate(result: dict[str, Any]) -> dict[str, Any]:
    return versioned({"job_id": None, "state": "done", "result": result})


class RequestHintInput(ParamsModel):
    session_id: str = Field(min_length=1)
    practice_item_id: str = Field(min_length=1)
    #: The screen's stable submission key for the attempt in progress: the
    #: hint's row is counted into that submission's attempt and no other.
    submission_id: str = Field(min_length=1)
    #: The draft (the screen flushes it first); absent: the session checkpoint's.
    answer_md: str | None = Field(default=None, max_length=200_000)
    request: Literal["more", "feedback", "book_way", "smaller_step"] = "more"
    answered_assist_id: str | None = None
    feedback_shortcut: Literal["not_where_stuck", "too_big", "learner_route", "notation"] | None = None
    feedback_text: str | None = Field(default=None, max_length=4000)
    feedback_selection: str | None = Field(default=None, max_length=4000)
    #: The worked-help picks only: 4 or 5 (a Hint press serves levels 1-3, D17).
    taken_level: int | None = Field(default=None, ge=4, le=5)
    seconds_on_item: float | None = Field(default=None, ge=0)


@method("practice.request_hint", RequestHintInput)
def request_hint(ctx: SidecarContext, params: RequestHintInput) -> dict[str, Any]:
    """Ask for a hint written for the learner's work (a job; see the module)."""

    from learnloop_sidecar.handlers.practice import _in_diagnostic_block, _require_open_session

    vault, repository = ctx.require_vault()
    if not adaptive_enabled(vault.config):
        return _immediate(hint_service.HintResultV1(
            status=hint_service.DISABLED, reason="adaptive_disabled",
            message="Adaptive hints are off; the item's own hints are shown as before.").as_dict())
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice item {params.practice_item_id} not found.")
    _require_open_session(repository, params.session_id)
    if _in_diagnostic_block(repository, item):
        # Probe redesign §5.5 (G-H14): no hint during a diagnostic block, and
        # no model is asked.
        return _immediate(hint_service.HintResultV1(
            status=hint_service.REFUSED, reason="diagnostic_block",
            message="Hints are off during a diagnostic check.").as_dict())
    request = HintRequestV1(
        practice_item_id=item.id, session_id=params.session_id, submission_id=params.submission_id.strip(),
        work_md=params.answer_md, request=params.request, answered_assist_id=params.answered_assist_id,
        feedback_shortcut=params.feedback_shortcut, feedback_text=params.feedback_text,
        feedback_selection=params.feedback_selection, taken_level=params.taken_level,
        seconds_on_item=params.seconds_on_item)
    writer_client = getattr(ctx, "hint_writer_client", None)
    chooser_client = getattr(ctx, "hint_chooser_client", None)
    chooser_factory = (lambda: chooser_client) if chooser_client is not None else None
    seed = getattr(ctx, "hint_seed", None)

    def work(worker_repo: Any, cancelled: Callable[[], bool]) -> dict[str, Any]:
        result = hint_service.request_hint(vault, worker_repo, request, writer_client=writer_client,
                                           chooser_client_factory=chooser_factory, seed=seed,
                                           cancelled=cancelled)
        if request.request == "feedback" and (request.feedback_text or "").strip() and result.assist_id:
            # H2b (spec §9): the reply's text is learner text, queued now so a
            # gap it names can join the next hint's rivals.
            _queue_learner_text(ctx, vault, worker_repo, result.assist_id)
        return result.as_dict()

    job = _jobs(ctx).start(ctx, item.id, work)
    return _job_payload(ctx, job)


def _job_payload(ctx: SidecarContext, job: _HintJob) -> dict[str, Any]:
    """The job as the wire reads it; the read that returns a ready hint delivers it."""

    base = {"job_id": job.job_id}
    with job.lock:
        if job.cancelled and not job.delivered:
            return versioned({**base, "state": "cancelled", "result": None})
        if not job.done.is_set():
            return versioned({**base, "state": "pending", "result": None})
        plan_fallback.relay_job_offer(job)
        if job.error is not None:
            raise job.error
        result = dict(job.result or {})
        if result.get("status") == hint_service.READY and not job.delivered and job.refused is None:
            outcome = _deliver(ctx, job.practice_item_id, str(result["assist_id"]))
            if outcome == hint_service.SHOWN:
                job.delivered = True
            elif outcome == hint_service.REVEAL_NOT_RECORDED:
                # Nothing was shown (review round 2, V4); the job stays
                # deliverable, so a later read tries again.
                result = hint_service.undelivered_result(str(result["assist_id"]), outcome).as_dict()
            else:
                job.refused = outcome
        if job.refused is not None:
            # Never the text of a hint the ledger did not record as shown
            # (G-H3): the submission it was written for is already committed.
            result = hint_service.undelivered_result(str(result.get("assist_id") or ""), job.refused).as_dict()
        result["shown"] = job.delivered
    return versioned({**base, "state": "done", "result": result})


class _RevealNotRecorded(Exception):
    """The shown hint's reveal could not be written (rolls the delivery back)."""


def _deliver(ctx: SidecarContext, practice_item_id: str, assist_id: str) -> str:
    """Show the prepared row and write its key overlap to the reveal ledger
    (§5: ``tutor_answer`` with basis ``hint:<kind>:L<level>``) in ONE
    transaction (review round 2, V4): a hint is never shown without its
    reveal. A failed reveal write rolls the shown mark back and answers
    ``REVEAL_NOT_RECORDED`` (nothing shown; a later read retries). Then, once
    shown, schedule the lazy learner-route merge (§4.3.1 row 3, in the
    background). Returns the delivery outcome: only ``SHOWN`` lets the hint's
    text reach the surface."""

    from learnloop.attempts.reveal_ledger import record_reveal_strict, reveal_episode_id

    vault, repository = ctx.require_vault()
    # The item as loaded now: a hint written for an item since removed or
    # changed is refused before it is marked shown (round 3, W5), so its
    # reveal is always written against the item it was written for.
    item = vault.practice_items.get(practice_item_id)
    try:
        with repository.atomic():
            outcome, row = hint_service.deliver_hint(repository, assist_id, item=item)
            # H2b, the authored-reveal ruling: an authored hint the service
            # serves leaves the evidence the client's reveal of the same hint
            # leaves, which writes no reveal row (spec §3.2; §10.1 successor
            # 3 keeps authored reveals out of the ledger in v1). It still
            # counts at level 3 as a server row. Every other kind keeps §5's
            # tutor_answer reveal.
            if outcome == hint_service.SHOWN and row is not None and item is not None \
                    and row.get("hint_kind") and row.get("level") \
                    and not hint_service.reveal_exempt(str(row["hint_kind"])):
                try:
                    amount = hint_service.reveal_amount(item, hint_service.shown_text(item, row))
                    record_reveal_strict(
                        repository, practice_item_id=item.id, learning_object_id=item.learning_object_id,
                        remediation_episode_id=reveal_episode_id(repository, item.id, strict=True),
                        source_kind="tutor_answer", amount=amount,
                        basis=hint_service.reveal_basis(str(row["hint_kind"]), int(row["level"])))
                except Exception as exc:  # noqa: BLE001 - any failure: the hint is not shown
                    raise _RevealNotRecorded(type(exc).__name__) from exc
    except _RevealNotRecorded as exc:
        log_event("hint_reveal_ledger_failed", practice_item_id=practice_item_id, error=str(exc))
        return hint_service.REVEAL_NOT_RECORDED
    if outcome == hint_service.SHOWN and row is not None:
        _schedule_merge(ctx, vault, repository, practice_item_id)
    return outcome


def _schedule_merge(ctx: SidecarContext, vault: Any, repository: Any, practice_item_id: str) -> None:
    """H1's lazy learner-route merge after a hint is shown (H2a review F9):
    background, with H1's locks, claim, lease, envelope and kill switches;
    never delays or fails the delivery."""

    try:
        schedule_merge_after_hint(vault, repository.sqlite_path, practice_item_id,
                                  client=getattr(ctx, "approach_map_client", None),
                                  builds=getattr(ctx, "map_builds", None))
    except Exception as exc:  # noqa: BLE001 - never reaches the delivery
        log_event("approach_map_merge_schedule_failed", practice_item_id=practice_item_id,
                  error=type(exc).__name__)


class HintJobInput(ParamsModel):
    job_id: str = Field(min_length=1)


@method("practice.hint_job", HintJobInput)
def hint_job(ctx: SidecarContext, params: HintJobInput) -> dict[str, Any]:
    """A hint job's state, at once (never a wait on the request path)."""

    return _job_payload(ctx, _require_job(ctx, params.job_id))


def _require_job(ctx: SidecarContext, job_id: str) -> _HintJob:
    _vault, repository = ctx.require_vault()
    job = _jobs(ctx).get(job_id)
    if job is None or job.sqlite_path != str(repository.sqlite_path):
        raise SidecarError("not_found", "That hint request is no longer kept; ask again.")
    return job


@method("practice.cancel_hint", HintJobInput)
def cancel_hint(ctx: SidecarContext, params: HintJobInput) -> dict[str, Any]:
    """Cancel a hint request before it is shown: it is never delivered, and
    its row stays ``shown = 0`` (it counts nothing). A delivered hint stays."""

    job = _require_job(ctx, params.job_id)
    with job.lock:
        if job.delivered:
            return versioned({"job_id": job.job_id, "state": "done", "cancelled": False,
                              "reason": "already_shown"})
        job.cancelled = True
    return versioned({"job_id": job.job_id, "state": "cancelled", "cancelled": True, "reason": None})


class DiscriminateAnswerInput(ParamsModel):
    session_id: str = Field(min_length=1)
    practice_item_id: str = Field(min_length=1)
    submission_id: str = Field(min_length=1)
    #: The discriminating question's row (its result's ``assistId``).
    question_assist_id: str = Field(min_length=1)
    #: The one-line answer, typed in the question's own box.
    answer_md: str = Field(max_length=2000)


@method("practice.answer_discriminating", DiscriminateAnswerInput)
def answer_discriminating(ctx: SidecarContext, params: DiscriminateAnswerInput) -> dict[str, Any]:
    """Record the learner's answer to a discriminating question (fire and
    forget: the screen never waits on it). No model call, no evidence."""

    vault, repository = ctx.require_vault()
    if not adaptive_enabled(vault.config):
        return versioned({"recorded": False, "reason": "adaptive_disabled", "assist_id": None})
    try:
        recorded = hint_service.record_discriminate_answer(
            vault, repository, practice_item_id=params.practice_item_id, session_id=params.session_id,
            submission_id=params.submission_id, question_assist_id=params.question_assist_id,
            answer_md=params.answer_md)
    except HintRequestError as exc:
        raise SidecarError(exc.code, str(exc), details={"field": exc.field} if exc.field else None) from exc
    if recorded.get("assist_id"):
        # H2b (spec §9): a discriminating answer is learner text too.
        _queue_learner_text(ctx, vault, repository, str(recorded["assist_id"]))
    return versioned(recorded)


def _queue_learner_text(ctx: SidecarContext, vault: Any, repository: Any, assist_id: str) -> None:
    """Queue a ``hint_feedback`` learner text (H2b, migration 212) and wake
    the post-attempt worker's ``gaps`` slot. Never fails the hint."""

    try:
        from learnloop.diagnosis.text_gaps.jobs import enqueue_hint_feedback

        if enqueue_hint_feedback(vault, repository, assist_id=assist_id):
            ctx.post_attempt_worker.notify()
    except Exception as exc:  # noqa: BLE001 - learner-text gaps never reach the hint
        log_event("hint_feedback_enqueue_failed", assist_id=assist_id, error=type(exc).__name__)


#: H2b: the hint panel's help-style editor (the "⋯" menu and Settings).
HINT_PANEL_RPCS: tuple[str, ...] = ("practice.set_help_style",)
HELP_STYLES = ("let_me_struggle", "balanced", "guide_me")


class SetHelpStyleInput(ParamsModel):
    help_style: Literal["let_me_struggle", "balanced", "guide_me"]


@method("practice.set_help_style", SetHelpStyleInput)
def set_help_style(ctx: SidecarContext, params: SetHelpStyleInput) -> dict[str, Any]:
    """Write the one stored help-style preference every surface reads
    (``[hints] help_style``, spec D5): from the hint panel's "⋯" menu and from
    Settings. The narrowest write there is: no generic config write exists
    (each Settings section has its own RPC), so this one key goes through the
    comment-preserving settings store and the vault reloads, as
    ``reader.set_cue_preferences`` does. A stated preference the chooser
    weighs, never a block (§4.5). No change, no write."""

    from learnloop.ops.settings_store import SettingsStoreError, apply_config_updates

    vault, _repository = ctx.require_vault()
    if vault.config.hints.help_style != params.help_style:
        try:
            apply_config_updates(vault.root / "learnloop.toml", {("hints", "help_style"): params.help_style})
        except SettingsStoreError as exc:
            raise SidecarError(exc.code, str(exc)) from exc
        ctx.reload(maintenance=False)
        vault, _repository = ctx.require_vault()
    return versioned({"help_style": vault.config.hints.help_style})


__all__ = ["HELP_STYLES", "HINT_PANEL_RPCS", "HINT_SERVICE_RPCS", "HintJobs"]
