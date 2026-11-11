"""What other test files use from ``tests/test_reading_request_sweep.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
import time
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.db.repositories import Repository

from tests.ux_phase1_add_source_helpers import call
from tests.ux_phase1_support import CLOCK, fake_services


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


def _wait_for(predicate, timeout: float = 120.0) -> bool:
    """Polls until ``predicate`` holds (returning at once when it does); the
    bound only matters when the machine is loaded (a parallel full suite)."""

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
