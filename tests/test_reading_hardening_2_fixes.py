"""Fail-first tests for Codex's review of reading-hardening's verify follow-up
(``~/.cache/codex-agent/jobs/20261013-200341-MF4nxL``;
docs/reviews/reading-hardening-2-codex-review.md).

* F1: the verify follow-up settles a reading request in the transaction that
  queues its build, and starts the worker only after the commit. If starting
  the worker failed, or the process ended first, the build stayed queued and
  nothing durable was left to start it: the request was settled, so neither
  the start's reconciliation nor the sweep acted on anything, and ``bind()``
  only recovers leases. A book's queued preparation that the worker can run
  is now recovered on its own, independently of reading requests: at the
  start, and on every pass of the sweep.

The F2 tests (a video seek's delayed landing) are component tests in
``apps/learnloop-tauri/src/screens/ReaderScreen.checkOffer.test.tsx``.
Every model call is a house fake.
"""

from __future__ import annotations

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import IngestRunner, JobSpec
from learnloop.db.repositories import Repository

from tests.test_reading_request_sweep import (
    ScriptedClock,
    _background,
    _later,
    _pending,
    _planners,
    _report,
    _restart,
    _wait_for,
    fast_sweep,  # noqa: F401 - a fixture
    stopped,  # noqa: F401 - a fixture
)
from tests.test_ux_phase1_round2_review import _added_book
from tests.ux_phase1_support import CLOCK, fake_services


def _newest_planner(ctx) -> dict:
    return ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,))[0]


def _status(ctx, job_id: str) -> str:
    return ctx.repository.get_ingest_job(job_id)["status"]


# ---------------------------------------------------------------------------
# F1: a committed build is run without another learner action
# ---------------------------------------------------------------------------


def test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep(tmp_path, fast_sweep, stopped):
    """Codex's scenario in the running sidecar: the learner reads Ch. 2, so
    the act queues Ch. 3's planner and settles the request in one commit;
    then starting the worker fails. Before, the sweep found no pending request
    and nothing else ran the planner until the learner did something else. Now
    the sweep's own pass finds the queued work and starts the worker."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = _background(ctx, root, stopped, clock=ScriptedClock(_later()))
    planners = _planners(ctx)
    starts: list[int] = []
    real_start = jobs._ensure_worker

    def failing_once() -> None:
        starts.append(1)
        if len(starts) == 1:
            raise RuntimeError("can't start new thread")
        real_start()

    jobs._ensure_worker = failing_once  # type: ignore[method-assign]

    _report(ctx, extraction_id, 1, "u3")  # Ch. 2 read: keep Ch. 3 ahead

    assert starts, "the act never tried to start the worker"
    assert _planners(ctx) == planners + 1
    planner = _newest_planner(ctx)
    assert (planner.get("payload") or {}).get("chapter_ids") == ["u4"]
    assert _pending(ctx, source_id) is None  # settled with the enqueue: nothing left to act on
    assert _wait_for(lambda: _status(ctx, planner["id"]) == "completed", timeout=60), \
        "the build queued before the worker failed to start was stranded"


def test_f1_a_build_queued_just_before_the_process_ended_runs_at_the_next_start(tmp_path, monkeypatch, stopped):
    """The process ends after the commit and before the worker starts. The
    next start's reconciliation finds no pending request (it was settled with
    the enqueue). Before, the planner stayed queued; now the start runs it.
    The sweep's pace is an hour here, so only the start can run it."""

    monkeypatch.setattr(DurableIngestJobs, "READING_SWEEP_SECONDS", 3600.0, raising=False)
    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]  # the process ends first
    planners = _planners(ctx)

    _report(ctx, extraction_id, 1, "u3")
    planner = _newest_planner(ctx)
    assert _planners(ctx) == planners + 1 and planner["status"] == "queued"
    assert _pending(ctx, source_id) is None
    ctx.ingest_jobs.shutdown()

    restarted = _restart(root, stopped, clock=ScriptedClock(_later()))

    assert _wait_for(lambda: _status(restarted, planner["id"]) == "completed", timeout=60), \
        "the build queued before the restart was stranded"


def test_f1_the_start_and_the_sweep_leave_work_that_cannot_run_alone(tmp_path):
    """No worker is started for queued work it could not claim: a job whose
    dependency waits for the learner, or a job in a batch being cancelled.
    The sweep checks every pass, so it must not start an idle worker each
    time for work like this. A book's preparation it can claim is recovered;
    other workflows keep their own resume paths."""

    root, ctx, _source_id, _extraction_id = _added_book(tmp_path)
    repo = ctx.repository
    runner = IngestRunner(Repository(repo.sqlite_path), vault_root=root, worker_id="test", clock=CLOCK,
                          services=fake_services())
    jobs = DurableIngestJobs()
    jobs.bind(Repository(repo.sqlite_path), root, background=True, clock=CLOCK, services=fake_services())
    started: list[int] = []
    jobs._ensure_worker = lambda: started.append(1)  # type: ignore[method-assign]
    try:
        assert jobs.resume_book_preparation() is False  # nothing queued at all
        assert started == []

        waiting = runner.enqueue_batch(core.ADD_SOURCE_WORKFLOW, [
            JobSpec("import", {"source": "a.md"}),
            JobSpec(core.AUTO_STUDY_MAP_JOB, {"source": "a.md"}, depends_on=(0,)),
        ])
        first, _second = repo.ingest_jobs_for_batch(waiting)
        assert repo.transition_unleased_ingest_job(first["id"], status="waiting_for_input")
        cancelling = runner.enqueue_batch(core.AUTO_BUILD_WORKFLOW, [JobSpec(core.AUTO_STUDY_MAP_JOB, {"source_id": "x"})])
        repo.request_ingest_batch_cancel(cancelling)
        elsewhere = runner.enqueue_batch("import", [JobSpec("import", {"source": "b.md"})])

        assert repo.has_runnable_ingest_job() is True  # the plain import, outside a book's preparation
        assert jobs.resume_book_preparation() is False
        assert started == []

        building = runner.enqueue_batch("bootstrap_synthesis", [JobSpec("inventory", {"units": []})],
                                        batch_id=core.child_batch_id("job_planner"))
        assert repo.has_runnable_ingest_job(batch_id_prefixes=(core.AUTO_BUILD_BATCH_PREFIX,)) is True
        assert repo.has_runnable_ingest_job(job_types=("import",), batch_id_prefixes=(core.AUTO_BUILD_BATCH_PREFIX,)) is False
        assert jobs.resume_book_preparation() is True
        assert started == [1]
        assert repo.ingest_jobs_for_batch(building)[0]["status"] == "queued"
        assert repo.ingest_jobs_for_batch(elsewhere)[0]["status"] == "queued"
    finally:
        jobs.shutdown()


def test_f1_a_foreground_host_starts_no_worker_of_its_own(tmp_path):
    """The CLI and the tests drain in the foreground: recovery there is the
    caller's drain, never a background worker."""

    root, ctx, _source_id, _extraction_id = _added_book(tmp_path)
    runner = IngestRunner(Repository(ctx.repository.sqlite_path), vault_root=root, worker_id="test", clock=CLOCK,
                          services=fake_services())
    runner.enqueue_batch(core.AUTO_BUILD_WORKFLOW, [JobSpec(core.AUTO_STUDY_MAP_JOB, {"source_id": "x"})])
    started: list[int] = []
    ctx.ingest_jobs._ensure_worker = lambda: started.append(1)  # type: ignore[method-assign]

    assert ctx.ingest_jobs.resume_book_preparation() is False
    assert started == []


def test_f1_a_failed_check_for_queued_work_is_retried_by_the_sweep(tmp_path, monkeypatch, fast_sweep, stopped):
    """A pass whose check for queued work fails is a failed pass: retried with
    the sweep's backoff, never taken for "nothing queued"."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    _report(ctx, extraction_id, 1, "u3")
    planner = _newest_planner(ctx)
    assert _status(ctx, planner["id"]) == "queued"
    del ctx.ingest_jobs._ensure_worker
    calls = {"n": 0}
    real = Repository.has_runnable_ingest_job

    def flaky(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            import sqlite3

            raise sqlite3.OperationalError("database is locked")
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Repository, "has_runnable_ingest_job", flaky)
    _background(ctx, root, stopped, clock=ScriptedClock(_later()))

    assert _wait_for(lambda: _status(ctx, planner["id"]) == "completed", timeout=60)
    assert calls["n"] >= 2
