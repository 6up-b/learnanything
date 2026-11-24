"""Reader workbench v2 RD10 RPCs: follow-along and suggested video chapters (spec §7.5, §7.9).

* ``reader.follow_along``: what a book window follows at a video's time (no model call, no write;
  ``learnloop.source_retrieval.follow_along``): the video's section with its time bounds, the accepted chapter, and per
  LO the book's correspondent sections from judged coverage.
* ``chapters.list``: a video reading's chapters, suggested and accepted (no model call, no write).
* ``chapters.suggest`` / ``chapters.job`` / ``chapters.cancel``: the chapters judge as a polled job
  (``learnloop.source_retrieval.video_chapters``), on a thread the context owns (``learnloop_sidecar.polled_jobs``),
  off the serial loop. A suggest while that reading's job runs answers with it; a poll reads at once and never waits;
  cancelling refuses the job's next model request before it is sent. Jobs belong to the vault they started in: a poll
  from another vault does not find them, and switching vaults interrupts them.
* ``chapters.decide``: accept a suggested chapter or dismiss it ("not this"), once.

Desktop only (pinned in tests/test_mobile_allowlist.py). Under the Reader's and the curriculum's switches, as
``reader.correspondents`` is. A suggestion is a proposal, never coverage and never evidence.
"""
from __future__ import annotations

import threading
from typing import Any, Literal

from pydantic import Field

from learnloop.curriculum import goal_lens as GL
from learnloop.ids import new_ulid
from learnloop.source_retrieval import follow_along as FA
from learnloop.source_retrieval import section_coverage as SC
from learnloop.source_retrieval import video_chapters as VC
from learnloop_sidecar import polled_jobs as PJ
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.correspondents import _library_cache, _require
from learnloop_sidecar.handlers.goal_lens import protection_now
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
VIDEO_RPCS: tuple[str, ...] = ("reader.follow_along", "chapters.list", "chapters.suggest", "chapters.job",
                               "chapters.cancel", "chapters.decide")
KIND = "chapters.suggest"
NOT_FOUND_MESSAGE = ("This suggestion isn't running any more (LearnLoop restarted or the vault changed since it was "
                     "asked). Ask again: a video already judged is not judged twice.")
_REGISTRY = "video_chapter_jobs"
_JOBS_LOCK = threading.Lock()


class FollowAlongInput(ParamsModel):
    #: The playing video's reading.
    extraction_id: str = Field(min_length=1)
    t: float = Field(ge=0)
    #: The book window's reading.
    book_extraction_id: str = Field(min_length=1)


class ChaptersInput(ParamsModel):
    extraction_id: str = Field(min_length=1)


class ChaptersJobInput(ParamsModel):
    job_id: str = Field(min_length=1, max_length=128)


class ChaptersDecideInput(ParamsModel):
    chapter_id: str = Field(min_length=1, max_length=128)
    decision: Literal["accept", "dismiss"]


def _sections(repository: Any, extraction_id: str) -> list[tuple[str, float, float | None]]:
    return [(section.section_id, section.t0, section.t1) for section in VC.transcript_sections(repository, extraction_id)]


def _protected_chapters(vault: Any, repository: Any, extraction_id: str,
                        chapters: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str | None]:
    """Chapters as a reply may carry them while checks are due (masked at every read, a poll included, so a check
    falling due since the judgment still hides what it covers), and when the next check falls due."""

    protection, next_due = protection_now(vault, repository)
    return GL.protect_chapters(chapters, protection, _sections(repository, extraction_id)), next_due


def _chapters_error(exc: VC.ChaptersError | SC.CoverageError) -> SidecarError:
    return SidecarError(exc.code, getattr(exc, "message", None) or str(exc))


@method("reader.follow_along", FollowAlongInput)
def reader_follow_along(ctx: SidecarContext, params: FollowAlongInput) -> dict[str, Any]:
    """What the book follows at the video's time (no model call, no write)."""

    vault, repository, video = _require(ctx, params.extraction_id)
    _vault, _repository, book = _require(ctx, params.book_extraction_id)
    try:
        reply = FA.follow(vault, repository, video, params.t, book, cache=_library_cache(ctx))
    except SC.CoverageError as exc:
        raise _chapters_error(exc) from exc
    protection, next_due = protection_now(vault, repository)
    return versioned({**GL.protect_follow(reply, protection, _sections(repository, video)), "next_check_due": next_due})


@method("chapters.list", ChaptersInput)
def chapters_list(ctx: SidecarContext, params: ChaptersInput) -> dict[str, Any]:
    """A video reading's chapters, suggested and accepted, by time."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    chapters, next_due = _protected_chapters(vault, repository, resolved, VC.list_chapters(vault, repository, resolved))
    return versioned({"extraction_id": resolved, "chapters": chapters, "next_check_due": next_due})


def _jobs(ctx: SidecarContext) -> PJ.PolledJobs:
    return PJ.registry(ctx, _REGISTRY)


def _error(error: SidecarError | None) -> dict[str, Any] | None:
    if error is None:
        return None
    return {"code": error.code, "message": error.message, "retryable": error.retryable, "details": error.details}


def _payload(job_id: str | None, status: str, *, finished: bool, result: dict[str, Any] | None,
             error: SidecarError | None) -> dict[str, Any]:
    return versioned({"job_id": job_id, "status": status, "done": finished, "result": result, "error": _error(error)})


def _job_payload(ctx: SidecarContext, job: PJ.PolledJob) -> dict[str, Any]:
    from learnloop.ai import plan_fallback

    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
    status = state["status"]
    result = state["result"] if status == PJ.DONE else None
    if result and result.get("chapters") and result.get("extraction_id"):
        vault, repository = ctx.require_vault()
        chapters, _next_due = _protected_chapters(vault, repository, result["extraction_id"], result["chapters"])
        result = {**result, "chapters": chapters}
    return _payload(job.job_id, status, finished=bool(state["finished"]), result=result,
                    error=state["error"] if status == PJ.FAILED else None)


@method("chapters.suggest", ChaptersInput)
def chapters_suggest(ctx: SidecarContext, params: ChaptersInput) -> dict[str, Any]:
    """Judge the video's chapters: ``{job_id, status, done, result, error}`` at once. The result is the suggestion's
    status (``ready``, ``unavailable``, ``capped``, ``failed``, ``stale``, ``no_sections``) with the chapters."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    jobs = _jobs(ctx)
    vault_key = PJ.vault_key(ctx)
    client = getattr(ctx, "video_chapters_client", None)
    live_vault = getattr(ctx, "loaded_vault", None)

    def work(job: PJ.PolledJob) -> dict[str, Any]:
        try:
            result = VC.suggest(vault, repository, resolved, client=client, live_vault=live_vault,
                                wanted=lambda: not job.cancelled and job.live())
        except (VC.ChaptersError, SC.CoverageError) as exc:
            raise _chapters_error(exc) from exc
        return {"status": result.status, "reason": result.reason, "message": result.message, "chapters": result.chapters,
                "extraction_id": resolved}

    with _JOBS_LOCK:
        # Which job is judging which reading now: (vault, reading) -> job id, the finished ones let go.
        judging: dict[tuple[str, str], str] = getattr(ctx, "video_chapters_judging", None) or {}
        judging = {key: job_id for key, job_id in judging.items()
                   if (found := jobs.get(key[0], job_id)) is not None and not found.done.is_set()}
        ctx.video_chapters_judging = judging  # type: ignore[attr-defined]
        running = jobs.get(vault_key, judging.get((vault_key, resolved), ""))
        if running is not None and not running.done.is_set() and not running.cancelled:
            return _job_payload(ctx, running)
        job = jobs.start(ctx, kind=KIND, job_id="vch_" + new_ulid(), work=work, request_key=resolved)
        judging[(vault_key, resolved)] = job.job_id
    return _job_payload(ctx, job)


def _find(ctx: SidecarContext, job_id: str, *, cancel: bool = False) -> dict[str, Any]:
    ctx.require_vault()
    jobs = _jobs(ctx)
    vault_key = PJ.vault_key(ctx)
    job = jobs.cancel(vault_key, job_id) if cancel else jobs.get(vault_key, job_id)
    if job is not None:
        return _job_payload(ctx, job)
    receipt = jobs.receipt(vault_key, job_id)
    if receipt is not None:
        status = PJ.CANCELLED if receipt.status == PJ.CANCELLED else PJ.EXPIRED
        return _payload(receipt.job_id, status, finished=True, result=None, error=None)
    raise SidecarError("job_not_found", NOT_FOUND_MESSAGE, details={"job_id": job_id})


@method("chapters.job", ChaptersJobInput)
def chapters_job(ctx: SidecarContext, params: ChaptersJobInput) -> dict[str, Any]:
    """The suggestion's state, at once (never a wait on the request path)."""

    return _find(ctx, params.job_id)


@method("chapters.cancel", ChaptersJobInput)
def chapters_cancel(ctx: SidecarContext, params: ChaptersJobInput) -> dict[str, Any]:
    """Cancel the suggestion: its next model request is refused; a finished one keeps its outcome."""

    return _find(ctx, params.job_id, cancel=True)


@method("chapters.decide", ChaptersDecideInput)
def chapters_decide(ctx: SidecarContext, params: ChaptersDecideInput) -> dict[str, Any]:
    """Accept a suggested chapter or dismiss it ("not this"), once; the chapter as it now stands."""

    vault, repository = ctx.require_vault()
    try:
        chapter = VC.decide(vault, repository, params.chapter_id, params.decision)
    except VC.ChaptersError as exc:
        raise _chapters_error(exc) from exc
    chapters, _next_due = _protected_chapters(vault, repository, chapter["extraction_id"], [chapter])
    return versioned({"chapter": chapters[0]})


__all__ = ["VIDEO_RPCS"]
