"""Fail-first tests for the level-triggered reading-request sweep
(docs/reviews/reading-hardening.md, part 1).

Codex's verify of the UX Phase 1 finishing pass
(``~/.cache/codex-agent/jobs/20261013-152028-hedJsZ``, F1 reopened) found five
ways the book's durable "keep one chapter ahead" request could strand, each
because acting on it depended on being woken at the right moment:

* (a) a transient error in the worker's due scan, followed by its idle exit;
* (b) the start's reconciliation deferred behind a build already queued, with
  nothing starting the worker that would run it;
* (c) ``cancel_batch`` neither settling the request nor waking anything;
* (d) blocking work finished by the CLI's ``IngestRunner.drain()``, which never
  runs the reading scan;
* (e) a reconciliation read failure outside the planning handler, logged
  without scheduling another attempt.

The redesign keeps no wake-up on the correctness path: while the sidecar runs,
a periodic sweep acts on every due request whose book's work is done, retries a
failed scan or a failed act with backoff, and never takes a failure for
"nothing due". Each scenario runs through the real worker and sweep threads
(or, for the CLI, a second runner on the same library) with the sweep's clock
scripted. Every model call is a house fake.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import IngestRunner
from learnloop.db.repositories import Repository

from tests.test_ux_phase1_add_source import call
from tests.test_ux_phase1_round2_review import _added_book
from tests.ux_phase1_support import CLOCK, fake_services, route


class ScriptedClock:
    """The sweep's clock: it moves only when the test moves it."""

    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment

    def advance(self, seconds: float) -> None:
        self.moment += timedelta(seconds=seconds)


def _later() -> datetime:
    """An instant after everything the test records with the wall clock."""

    return datetime.now(UTC).replace(microsecond=0) + timedelta(hours=1)


def _planners(ctx) -> int:
    return len(ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,)))


def _planner_chapters(ctx) -> list[list[str]]:
    jobs = ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,))
    return [list((job.get("payload") or {}).get("chapter_ids") or []) for job in jobs]


def _report(ctx, extraction_id, seen, section_id):
    call(ctx, "reader.mark_section_progress",
         {"extractionId": extraction_id, "sectionId": section_id, "spansSeen": seen, "spanCount": 4})


def _pending(ctx, source_id):
    return ctx.repository.source_auto_build_state(source_id)["wanted_section_id"]


def _wait_for(predicate, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


@pytest.fixture
def fast_sweep(monkeypatch):
    """The sweep's pace in real seconds, shortened so a test runs in a moment
    (the production pace is half a minute). Set before any thread starts."""

    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_SECONDS", 0.05, raising=False)
    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_RETRY_SECONDS", 0.02, raising=False)


@pytest.fixture
def stopped():
    """Every ingest host a test starts is shut down at its end."""

    hosts: list[DurableIngestJobs] = []
    yield hosts
    for host in hosts:
        host.shutdown()


def _background(ctx, root, hosts, *, clock=None, services=None, hold_builds=False):
    """The sidecar as it runs for the learner: the ingest worker and the
    reading sweep on their own threads (``hold_builds``: the worker runs
    nothing, so the book's build stays queued)."""

    jobs = ctx.ingest_jobs
    jobs.reading_clock = clock
    if hold_builds:
        jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    jobs.bind(ctx.repository, root, background=True, poll_interval_seconds=0.01, clock=CLOCK,
              services=services or fake_services())
    hosts.append(jobs)
    return jobs


def _deferred_behind_a_queued_build(ctx, extraction_id, source_id):
    """u3 (Ch. 2) queues Ch. 3's build, which is held; u4 (Ch. 3) then waits
    behind it as the book's reading request."""

    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    _report(ctx, extraction_id, 1, "u3")
    planner = next(job for job in ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,))
                   if job["status"] == "queued")
    _report(ctx, extraction_id, 1, "u4")
    assert _pending(ctx, source_id) == "u4"
    return planner


def _restart(root, hosts, *, clock=None, services=None):
    """A new sidecar process on the same library, as the learner starts it:
    background worker and sweep, then the start's maintenance."""

    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    vault = load_vault(root)
    jobs = ctx.ingest_jobs
    jobs.reading_clock = clock
    jobs.bind(Repository(VaultPaths(root, vault.config).sqlite_path), root, background=True,
              poll_interval_seconds=0.01, clock=CLOCK, services=services or fake_services())
    hosts.append(jobs)
    ctx.load(root)  # the start reconciles pending reading requests
    return ctx


# ---------------------------------------------------------------------------
# (a) a transient scan failure is retried, never taken for "nothing due"
# ---------------------------------------------------------------------------


def test_a_a_transient_scan_failure_is_retried_not_taken_for_nothing_due(tmp_path, monkeypatch, fast_sweep, stopped):
    """Codex's reproduction: rounds 1-2 see a retry still to come; by round 3
    it is due, and that round's scan raises one transient database error. The
    request must still be acted on, with nothing else waking anything."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planners = _planners(ctx)
    clock = ScriptedClock(_later())
    deadline = clock.moment + timedelta(seconds=1)
    revision = ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    assert ctx.repository.fail_reading_request(source_id, revision, attempts=1,
                                               retry_at=deadline.isoformat().replace("+00:00", "Z"))

    from learnloop.content.pipeline import jobs as jobs_module

    real_iso = jobs_module._iso
    # The old worker read its clock through ``_iso``; the sweep reads ``reading_clock``.
    monkeypatch.setattr(jobs_module, "_iso", lambda moment: real_iso(clock.now() if moment is None else moment))
    scans = {"n": 0}

    def flaky(real):
        def scan(self, *args, **kwargs):
            scans["n"] += 1
            if scans["n"] == 3:
                raise sqlite3.OperationalError("database is locked")  # one transient failure
            rows = real(self, *args, **kwargs)
            if scans["n"] == 2:
                clock.moment = deadline  # the retry falls due before the next round
            return rows
        return scan

    for name in ("due_reading_requests", "pending_reading_requests"):
        real = getattr(Repository, name, None)
        if real is not None:
            monkeypatch.setattr(Repository, name, flaky(real))

    jobs = _background(ctx, root, stopped, clock=clock)
    jobs.wake_reading_retries()

    assert _wait_for(lambda: _pending(ctx, source_id) is None), "the due request was stranded"
    assert scans["n"] > 3  # the failed scan was followed by another
    assert _planners(ctx) >= planners + 1
    assert ["u4"] in _planner_chapters(ctx)  # Ch. 3, kept ahead of u3 (Ch. 2)


# ---------------------------------------------------------------------------
# (b) the start's reconciliation, deferred behind a queued build
# ---------------------------------------------------------------------------


def test_b_a_start_deferred_behind_a_queued_build_runs_that_build_and_then_acts(tmp_path, fast_sweep, stopped):
    """Codex: ``bind()`` recovers leases without starting the worker, and the
    start's reconciliation, deferred behind Ch. 3's build queued before the
    restart, woke nothing: the build and the request both waited forever."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    ctx.ingest_jobs.shutdown()

    restarted = _restart(root, stopped, clock=ScriptedClock(_later()))

    assert _wait_for(lambda: restarted.repository.get_ingest_job(planner["id"])["status"] == "completed"), \
        "the build queued before the restart never ran"
    assert _wait_for(lambda: _pending(restarted, source_id) is None), "the deferred request was stranded"
    # u4 is Ch. 3: once Ch. 3 is built, Ch. 4 is kept ahead.
    assert _wait_for(lambda: ["u5"] in _planner_chapters(restarted))


# ---------------------------------------------------------------------------
# (c) cancel_batch: the request is settled (the learner's cancel answers it)
# ---------------------------------------------------------------------------


def test_c_cancelling_the_build_a_request_waits_behind_settles_it(tmp_path, fast_sweep, stopped):
    """Codex: a request deferred behind work the learner cancels was neither
    settled nor woken. Decided semantics: the cancel settles the book's
    request (the revision it had), so nothing re-plans the cancelled work
    behind the learner's back; the next section the learner reaches asks again."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()), hold_builds=True)
    planners = _planners(ctx)

    call(ctx, "cancel_ingest_batch", {"batchId": planner["batch_id"]})

    assert _pending(ctx, source_id) is None
    # Several sweeps later the cancelled chapter was not planned again.
    jobs.wake_reading_retries()
    time.sleep(0.3)
    assert _planners(ctx) == planners
    assert ctx.repository.get_ingest_job(planner["id"])["status"] == "cancelled"

    # Reading on asks again, from the new position (u5 is Ch. 4).
    _report(ctx, extraction_id, 1, "u5")
    assert _planners(ctx) == planners + 1
    assert _planner_chapters(ctx).count(["u5"]) == 1


def test_c_a_request_recorded_after_the_cancel_survives_it(tmp_path):
    """Revision-safe (F9): the cancel settles the revision it read; a newer
    request is acted on as usual."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    real_settle = Repository.settle_reading_request

    def newer_first(self, source, revision, **kwargs):
        # The learner reaches u5 between the cancel's read and its settle.
        self.record_reading_request(source, extraction_id, "u5")
        return real_settle(self, source, revision, **kwargs)

    Repository.settle_reading_request = newer_first  # type: ignore[method-assign]
    try:
        ctx.ingest_jobs.cancel_batch(planner["batch_id"])
    finally:
        Repository.settle_reading_request = real_settle  # type: ignore[method-assign]
    assert _pending(ctx, source_id) == "u5"


def test_c_the_cli_cancel_settles_the_request_too(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)

    result = CliRunner().invoke(app, ["ingest-batches", "cancel", planner["batch_id"], "--vault", str(root)])

    assert result.exit_code == 0, result.output
    assert _pending(ctx, source_id) is None


# ---------------------------------------------------------------------------
# (d) blocking work the CLI finishes: the sidecar's sweep acts after it
# ---------------------------------------------------------------------------


def test_d_work_the_cli_finishes_leaves_the_request_due_for_the_sweep(tmp_path, fast_sweep, stopped):
    """Codex: blocking work completed through the CLI's ``IngestRunner.drain()``
    never ran the reading scan. Here Ch. 3's build, queued by the sidecar,
    is drained by a CLI process and fails there (after_auto_build never runs);
    the running sidecar's sweep acts on u4 without being woken."""

    from learnloop.content.pipeline.runner import IngestRunnerError

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    clock = ScriptedClock(_later())
    _background(ctx, root, stopped, clock=clock, hold_builds=True)

    def broken(_context):
        raise IngestRunnerError("the model stopped answering", code="provider_down", retryable=False)

    cli = IngestRunner(Repository(ctx.repository.sqlite_path), vault_root=root, worker_id="cli-test",
                       clock=CLOCK, services=fake_services(on_append=broken))
    cli.recover_stale_leases()
    cli.drain()
    assert not core._source_work_active(ctx.repository, source_id)  # Ch. 3's work is over (it failed)

    # Ch. 3 failed (it waits for the card's Retry): u4 keeps Ch. 4 ahead.
    assert _wait_for(lambda: _pending(ctx, source_id) is None), "the request waited for a wake-up"
    assert ["u5"] in _planner_chapters(ctx)


# ---------------------------------------------------------------------------
# (e) a reconciliation read failure outside the planning handler
# ---------------------------------------------------------------------------


def test_e_a_read_failure_at_the_start_is_retried_by_the_sweep(tmp_path, monkeypatch, fast_sweep, stopped):
    """Codex: reading the pending request failed outside the planning
    handler, so the start only logged it. The request here also had its
    worker retries run out before the restart (no retry time), which nothing
    but a report or another start would rearm."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    revision = ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    assert ctx.repository.fail_reading_request(source_id, revision, attempts=4, retry_at=None)
    ctx.ingest_jobs.shutdown()
    reads = {"n": 0}
    real = Repository.pending_reading_request

    def flaky(self, source):
        reads["n"] += 1
        if reads["n"] == 1:
            raise sqlite3.OperationalError("disk I/O error")
        return real(self, source)

    monkeypatch.setattr(Repository, "pending_reading_request", flaky)

    restarted = _restart(root, stopped, clock=ScriptedClock(_later()))

    assert _wait_for(lambda: _pending(restarted, source_id) is None), "the request was stranded"
    assert reads["n"] >= 2
    assert ["u4"] in _planner_chapters(restarted)


# ---------------------------------------------------------------------------
# Pace: only due requests, with backoff; no hot loop while the learner reads
# ---------------------------------------------------------------------------


def _failing_enqueue(monkeypatch, failures=None) -> list[str]:
    calls: list[str] = []
    real = core.request_auto_build

    def flaky(jobs, source_id, *args, **kwargs):
        calls.append("enqueue")
        if failures is None or len(calls) <= failures:
            raise sqlite3.OperationalError("database is locked")
        return real(jobs, source_id, *args, **kwargs)

    monkeypatch.setattr(core, "request_auto_build", flaky)
    return calls


def test_a_failing_request_backs_off_and_is_never_given_up(tmp_path, monkeypatch):
    """Each failure pushes the next attempt out (2, 10, 30, 120 s, then every
    300 s); a sweep before that time leaves the request alone, and no failure
    ever leaves it without a retry time."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    clock = ScriptedClock(_later())
    jobs.reading_clock = clock
    calls = _failing_enqueue(monkeypatch)
    _report(ctx, extraction_id, 1, "u3")
    assert calls == ["enqueue"]

    waits = []
    for _ in range(7):
        request = ctx.repository.pending_reading_request(source_id)
        assert request["retry_at"] is not None
        due = datetime.fromisoformat(request["retry_at"].replace("Z", "+00:00"))
        waits.append(round((due - clock.moment).total_seconds()))
        before = len(calls)
        clock.moment = due - timedelta(seconds=1)
        jobs.retry_reading_advances()
        assert len(calls) == before  # not due yet: left alone
        clock.moment = due
        jobs.retry_reading_advances()
        assert len(calls) == before + 1
    assert waits == [2, 10, 30, 120, 300, 300, 300]
    assert jobs.reading_advance_pending(extraction_id)  # the Reader still asks again meanwhile


def test_a_request_waiting_on_the_books_work_is_not_replanned_by_the_sweep(tmp_path, monkeypatch, fast_sweep, stopped):
    """While Ch. 3's build is queued, sweep after sweep finds u4 waiting on it
    and plans nothing: no chapters are worked out and nothing is queued."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()), hold_builds=True)
    planners = _planners(ctx)
    outlines = {"n": 0}
    real = core.outline_chapters

    def counting(tree):
        outlines["n"] += 1
        return real(tree)

    monkeypatch.setattr(core, "outline_chapters", counting)
    sweeps = {"n": 0}
    real_sweep = DurableIngestJobs.sweep_reading_requests

    def counted(self, *args, **kwargs):
        sweeps["n"] += 1
        return real_sweep(self, *args, **kwargs)

    monkeypatch.setattr(DurableIngestJobs, "sweep_reading_requests", counted)
    for _ in range(5):
        jobs.wake_reading_retries()
        time.sleep(0.06)

    assert sweeps["n"] >= 3
    assert outlines["n"] == 0
    assert _planners(ctx) == planners
    assert _pending(ctx, source_id) == "u4"


def test_the_sweep_acts_once_the_books_work_ends_on_the_sidecars_own_worker(tmp_path, fast_sweep, stopped):
    """The ordinary path, end to end on the real threads: u4 waits behind
    Ch. 3's build; the worker runs it; the request is acted on (Ch. 4)."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    del ctx.ingest_jobs._ensure_worker  # the held builds are let go
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()))
    jobs.wake_reading_retries()

    assert _wait_for(lambda: _pending(ctx, source_id) is None)
    assert _wait_for(lambda: ["u5"] in _planner_chapters(ctx))


def test_the_sweep_stops_with_the_sidecar_and_a_foreground_host_starts_none(tmp_path, fast_sweep, stopped):
    root, ctx, _source_id, _extraction_id = _added_book(tmp_path)
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()))
    assert _wait_for(lambda: jobs._reading_sweep_thread is not None and jobs._reading_sweep_thread.is_alive())
    thread = jobs._reading_sweep_thread
    jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    thread.join(5)
    assert not thread.is_alive()
    jobs.bind(ctx.repository, root, background=True, clock=CLOCK, services=fake_services())
    assert _wait_for(lambda: jobs._reading_sweep_thread is not None and jobs._reading_sweep_thread.is_alive())
    thread = jobs._reading_sweep_thread
    jobs.shutdown()
    thread.join(5)
    assert not thread.is_alive()


def test_a_scan_that_keeps_failing_backs_off_to_the_sweeps_pace(tmp_path, monkeypatch, stopped):
    """The sweep never gives up on a failing scan, and never spins on one:
    the waits after failures grow 1, 2, 4 ... seconds, capped at its pace."""

    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_SECONDS", 30.0)
    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_RETRY_SECONDS", 1.0)
    root, ctx, _source_id, _extraction_id = _added_book(tmp_path)
    waits: list[float] = []
    done = threading.Event()

    class Wake:
        def wait(self, timeout=None):
            waits.append(timeout)
            if len(waits) >= 8:
                done.set()
                ctx.ingest_jobs._stop.set()
            return False

        def set(self):
            pass

        def clear(self):
            pass

        def is_set(self):
            return False

    def broken(self):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(Repository, "pending_reading_requests", broken)
    jobs = ctx.ingest_jobs
    jobs._reading_sweep_wake = Wake()
    jobs._background = True
    stopped.append(jobs)
    jobs._reading_sweep_loop()

    assert done.is_set()
    # The first wait is the pace (the start reconciles at once); then the backoff.
    assert waits == [30.0, 1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0]


def test_no_stored_retry_time_keeps_a_request_from_ever_being_due(tmp_path):
    """None (retries that ran out before the sweep) and an unreadable value
    both read as due now."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    planners = _planners(ctx)
    revision = ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    with ctx.repository.connection() as connection:
        connection.execute("UPDATE source_auto_build_state SET wanted_retry_at = 'soon' WHERE source_id = ?",
                           (source_id,))
        connection.commit()
    assert ctx.repository.pending_reading_request(source_id)["revision"] == revision

    assert jobs.retry_reading_advances(now=_later()) == 1
    assert _pending(ctx, source_id) is None
    assert _planners(ctx) == planners + 1
