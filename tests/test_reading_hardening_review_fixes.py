"""Fail-first tests for Codex's review of reading-hardening
(``~/.cache/codex-agent/jobs/20261013-183451-akyp7h``;
docs/reviews/reading-hardening-codex-review.md).

* F1: a cancel and the settling of the book's reading request were two
  commits. When the settle failed (or the process died between them) the
  cancel still went through, the request stayed due, and the sweep re-planned
  the very chapters the learner had just cancelled. Now the cancel and the
  settle commit together or not at all, on every cancel path.
* F2: an act that failed inside the sweep, whose failure could not even be
  recorded, woke the sweep it ran on, so the sweep's own backoff collapsed to
  zero waits. The sweep no longer wakes itself.

Every model call is a house fake.
"""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.db.repositories import Repository

from tests.test_reading_request_sweep import (
    _deferred_behind_a_queued_build,
    _later,
    _pending,
    _planners,
)
from tests.test_ux_phase1_add_source import call
from tests.test_ux_phase1_round2_review import _added_book
from tests.ux_phase1_support import CLOCK, fake_services


class _Crash(BaseException):
    """The process dying mid-operation: nothing after it runs, and only what
    was committed survives."""


def _fail_next(monkeypatch, name: str, error: BaseException) -> dict[str, bool]:
    """Make the next call of ``Repository.<name>`` raise ``error`` once
    ``armed`` is set (the failure Codex injected into the cancel's settle)."""

    real = getattr(Repository, name)
    state = {"armed": False, "fired": False}

    def flaky(self, *args, **kwargs):
        if state["armed"] and not state["fired"]:
            state["fired"] = True
            raise error
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Repository, name, flaky)
    return state


def _status(repo, job_id) -> str:
    return repo.get_ingest_job(job_id)["status"]


def _sweep_once(jobs) -> None:
    """One pass of the reading sweep, as the running sidecar's sweep makes it
    (the request is due: its scripted instant is an hour ahead)."""

    jobs.sweep_reading_requests(now=_later())


# ---------------------------------------------------------------------------
# F1: the cancel and its settle commit together, or neither does
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("failing", ["settle_reading_request", "pending_reading_request"])
def test_f1_a_cancel_whose_settle_fails_cancels_nothing_and_says_so(tmp_path, monkeypatch, failing):
    """Codex's scenario: u4 waits behind Ch. 3's queued planner; the learner
    cancels it, and reading or settling the request fails once. Before, the
    cancel reported success, the request stayed due, and the next sweep
    planned Ch. 3 again (the cancelled planner has no child build, so its
    chapters were still unplanned). Now the cancel fails as a whole: nothing
    was cancelled, the request still waits behind the planner, and the
    learner's next cancel settles both."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    planners = _planners(ctx)
    flaky = _fail_next(monkeypatch, failing, sqlite3.OperationalError("database is locked"))

    flaky["armed"] = True
    with pytest.raises(sqlite3.OperationalError):
        call(ctx, "cancel_ingest_batch", {"batchId": planner["batch_id"]})
    assert flaky["fired"]

    # Neither committed: the planner still runs Ch. 3, and u4 waits behind it.
    assert _status(ctx.repository, planner["id"]) == "queued"
    assert not ctx.repository.get_ingest_job(planner["id"])["cancel_requested"]
    assert _pending(ctx, source_id) == "u4"
    _sweep_once(ctx.ingest_jobs)
    assert _planners(ctx) == planners  # deferred behind the planner, not re-planned

    # The learner's cancel, again: both commit.
    call(ctx, "cancel_ingest_batch", {"batchId": planner["batch_id"]})
    assert _status(ctx.repository, planner["id"]) == "cancelled"
    assert _pending(ctx, source_id) is None
    _sweep_once(ctx.ingest_jobs)
    assert _planners(ctx) == planners  # the cancelled chapters were not planned again


def test_f1_a_crash_between_the_cancel_and_its_settle_leaves_neither_after_a_restart(tmp_path, monkeypatch):
    """The process dies after the cancel's writes and before the settle's.
    Before, the cancel was already durable and the request still due, so the
    next start's sweep planned Ch. 3–4 behind the learner's back. Now only
    what commits together survives: the restarted library still has the
    queued planner and u4 waiting behind it."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    planners = _planners(ctx)
    crash = _fail_next(monkeypatch, "settle_reading_request", _Crash())

    crash["armed"] = True
    with pytest.raises(_Crash):
        ctx.ingest_jobs.cancel_batch(planner["batch_id"])
    ctx.ingest_jobs.shutdown()

    # A new process on the same library: only committed state is left.
    restarted = DurableIngestJobs()
    restarted.bind(Repository(ctx.repository.sqlite_path), root, background=False, clock=CLOCK,
                   services=fake_services())
    restarted._ensure_worker = lambda: None  # type: ignore[method-assign]
    repo = restarted.repository
    cancelled = _status(repo, planner["id"]) == "cancelled"
    still_due = repo.pending_reading_request(source_id) is not None
    assert not (cancelled and still_due), "the cancel survived the crash, its settle did not"
    assert not cancelled and still_due  # the cancel rolled back with its settle

    _sweep_once(restarted)
    assert len(repo.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,))) == planners
    restarted.shutdown()


def test_f1_the_cli_cancel_commits_with_its_settle_too(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    flaky = _fail_next(monkeypatch, "settle_reading_request", sqlite3.OperationalError("disk I/O error"))

    flaky["armed"] = True
    failed = CliRunner().invoke(app, ["ingest-batches", "cancel", planner["batch_id"], "--vault", str(root)])

    assert failed.exit_code != 0
    assert flaky["fired"]
    assert _status(ctx.repository, planner["id"]) == "queued"
    assert _pending(ctx, source_id) == "u4"

    again = CliRunner().invoke(app, ["ingest-batches", "cancel", planner["batch_id"], "--vault", str(root)])
    assert again.exit_code == 0, again.output
    assert _status(ctx.repository, planner["id"]) == "cancelled"
    assert _pending(ctx, source_id) is None


def test_f1_kill_codex_interrupts_nothing_when_its_settle_fails(tmp_path, monkeypatch):
    """``kill-codex`` cancels the running job's batch and stops its call. If
    the settle fails, nothing is cancelled and the call is left running: the
    interrupt happens only after the cancel and the settle committed."""

    from learnloop.ai.transport import INTERRUPT

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    runner = ctx.ingest_jobs._require_runner()
    claimed = ctx.repository.claim_next_ingest_job(
        worker_id=runner.worker_id, now_iso="2026-07-13T12:00:00Z", lease_cutoff_iso="2026-07-13T11:58:00Z",
    )
    assert claimed is not None and claimed["id"] == planner["id"]

    class Client:
        interrupted = False

        def interrupt(self):
            self.interrupted = True

        def supports(self, capability: str) -> bool:
            return capability == INTERRUPT

    client = Client()
    runner._bind_job_interruptible(claimed["id"], claimed["attempt_count"], client)
    flaky = _fail_next(monkeypatch, "settle_reading_request", sqlite3.OperationalError("database is locked"))

    flaky["armed"] = True
    with pytest.raises(sqlite3.OperationalError):
        ctx.ingest_jobs.interrupt_codex(claimed["id"])
    assert not client.interrupted
    assert not ctx.repository.get_ingest_job(planner["id"])["cancel_requested"]
    assert _pending(ctx, source_id) == "u4"

    result = ctx.ingest_jobs.interrupt_codex(claimed["id"])
    assert result["interrupted"] and client.interrupted
    assert ctx.repository.get_ingest_job(planner["id"])["cancel_requested"]
    assert _pending(ctx, source_id) is None
