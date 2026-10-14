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
import threading
import time

import pytest

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.db.repositories import Repository

from tests.test_reading_request_sweep import (
    ScriptedClock,
    _background,
    _deferred_behind_a_queued_build,
    _failing_enqueue,
    _later,
    _pending,
    _planner_chapters,
    _planners,
    _wait_for,
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


# ---------------------------------------------------------------------------
# F2: a failure inside the sweep never wakes that same sweep
# ---------------------------------------------------------------------------


class _RecordingWake:
    """The sweep's wake event, recording every wait without blocking: the
    timeout asked for and whether the event was already set (a wait that
    returns at once, whatever its timeout)."""

    def __init__(self, on_wait) -> None:
        self._set = False
        self.waits: list[tuple[float | None, bool]] = []
        self._on_wait = on_wait

    def wait(self, timeout=None):
        self.waits.append((timeout, self._set))
        self._on_wait(len(self.waits))
        return self._set

    def set(self):
        self._set = True

    def clear(self):
        self._set = False

    def is_set(self):
        return self._set


def test_f2_planning_and_its_record_both_failing_back_off_through_the_sweeps_own_loop(tmp_path, monkeypatch, stopped):
    """Codex's reproduction: planning fails and recording its retry time fails
    too (database writes unavailable). The act's wake set the sweep's own
    event, so every backoff wait (1, 2, 4, 8, 16, 30 s) returned at once and
    the sweep retried the failing act in a tight loop. Run through the real
    sweep loop, pass and act; only the event is replaced, by one that records
    each wait instead of blocking."""

    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_SECONDS", 30.0)
    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_RETRY_SECONDS", 1.0)
    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    jobs.reading_clock = ScriptedClock(_later())
    ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    enqueues = _failing_enqueue(monkeypatch)
    records = {"n": 0}

    def unrecordable(self, *args, **kwargs):
        records["n"] += 1
        raise sqlite3.OperationalError("attempt to write a readonly database")

    monkeypatch.setattr(Repository, "fail_reading_request", unrecordable)

    def stop_after(count):
        if count >= 8:
            jobs._stop.set()

    wake = _RecordingWake(stop_after)
    jobs._reading_sweep_wake = wake  # type: ignore[assignment]
    jobs._background = True
    stopped.append(jobs)
    jobs._reading_sweep_loop()

    # No wait was cut short by the sweep's own wake.
    assert [already for _, already in wake.waits] == [False] * 8
    assert [timeout for timeout, _ in wake.waits] == [30.0, 1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0]
    assert len(enqueues) == 7 and records["n"] == 7  # every pass acted, and could not record it
    assert _pending(ctx, source_id) == "u3"  # never given up


def test_f2_on_the_real_threads_a_failing_unrecordable_act_does_not_spin(tmp_path, monkeypatch, stopped):
    """The same failure on the sidecar's real sweep thread and event. With
    the self-wake, the sweep re-ran the failing act back to back (a pass
    every few milliseconds). Now it waits its backoff (0.1, 0.2, 0.4 s, then
    the 0.5 s pace) between passes. A loaded machine only makes passes rarer."""

    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_SECONDS", 0.5)
    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_RETRY_SECONDS", 0.1)
    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    enqueues = _failing_enqueue(monkeypatch)
    monkeypatch.setattr(Repository, "fail_reading_request",
                        lambda self, *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("disk full")))
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()), hold_builds=True)

    jobs.wake_reading_retries()
    assert _wait_for(lambda: len(enqueues) >= 1)
    first = time.monotonic()
    time.sleep(1.2)
    elapsed = time.monotonic() - first
    passes = len(enqueues)
    jobs.shutdown()

    # 0.1 + 0.2 + 0.4 + 0.5 s: at most five passes fit in 1.2 s (plus slack).
    assert passes <= 8, f"{passes} failing passes in {elapsed:.2f} s: the sweep woke itself"
    assert _pending(ctx, source_id) == "u3"


def test_f2_a_wake_from_outside_the_sweep_still_brings_its_pass_forward(tmp_path, monkeypatch, stopped):
    """Only the sweep's own wake is dropped: a failed act on the Reader's RPC
    (another thread) still wakes the sweep, which then acts at once."""

    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_SECONDS", 30.0)
    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()), hold_builds=True)
    assert _wait_for(lambda: jobs._reading_sweep_thread is not None and jobs._reading_sweep_thread.is_alive())
    acted = threading.Event()
    real = DurableIngestJobs.sweep_reading_requests

    def noted(self, *args, **kwargs):
        sweep = real(self, *args, **kwargs)
        acted.set()
        return sweep

    monkeypatch.setattr(DurableIngestJobs, "sweep_reading_requests", noted)
    ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    jobs.wake_reading_retries()  # from this thread, as the Reader's RPC does

    assert acted.wait(20), "a wake from outside the sweep was dropped"
    assert _wait_for(lambda: _pending(ctx, source_id) is None)
    assert ["u4"] in _planner_chapters(ctx)


@pytest.fixture
def stopped():
    hosts: list[DurableIngestJobs] = []
    yield hosts
    for host in hosts:
        host.shutdown()
