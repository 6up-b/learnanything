"""Fail-first tests for the Codex re-review of UX Phase 1 usability round 2
(docs/reviews/ux-phase1-round2-codex-review.md, "Re-review"), the backend half:

* F8 — the round-2 F1 fix coalesced "keep one chapter ahead" on saved reading
  progress: the first report of a section saved ``spans_seen`` before asking,
  so when that ask failed (a busy database, a config mid-edit) every later
  report in the section skipped it as already reached, and nothing retried it.
"""

from __future__ import annotations

import sqlite3
import time

from learnloop.content.pipeline import add_source as core

from tests.test_ux_phase1_add_source import call
from tests.test_ux_phase1_round2_review import _added_book
from tests.ux_phase1_support import CLOCK, fake_services


# ---------------------------------------------------------------------------
# F8 — a failed keep-ahead is kept and retried, not coalesced away
# ---------------------------------------------------------------------------


def _planners(ctx) -> int:
    return len(ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,)))


def _report(ctx, extraction_id, seen, section_id="u3"):
    call(ctx, "reader.mark_section_progress",
         {"extractionId": extraction_id, "sectionId": section_id, "spansSeen": seen, "spanCount": 4})


def _failing(monkeypatch, failures=1) -> list[str]:
    """``advance_reading_build`` raises a transient error ``failures`` times
    (``None``: always), then runs for real. Returns the sections asked for."""

    calls: list[str] = []
    real = core.advance_reading_build

    def flaky(jobs, extraction_id, section_id):
        calls.append(section_id)
        if failures is None or len(calls) <= failures:
            raise sqlite3.OperationalError("database is locked")
        return real(jobs, extraction_id, section_id)

    monkeypatch.setattr(core, "advance_reading_build", flaky)
    return calls


def test_f8_a_keep_ahead_that_failed_is_asked_again_by_the_next_report(tmp_path, monkeypatch):
    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    calls = _failing(monkeypatch)
    planners = _planners(ctx)

    for seen in (1, 2, 3):
        _report(ctx, extraction_id, seen)

    # The first ask failed; the second report asks again and Ch. 3 is
    # planned; the third, after that success, is coalesced.
    assert calls == ["u3", "u3"]
    assert _planners(ctx) == planners + 1


def test_f8_a_keep_ahead_that_failed_is_kept_for_the_next_start(tmp_path, monkeypatch):
    from learnloop.content.pipeline.add_source import reconcile_reading_builds

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    _failing(monkeypatch)
    planners = _planners(ctx)

    _report(ctx, extraction_id, 1)

    # Durably: the book's pending reading position, which the next start
    # (and a finished build, and reconnecting an AI) acts on.
    state = ctx.repository.source_auto_build_state(source_id)
    assert (state["wanted_extraction_id"], state["wanted_section_id"]) == (extraction_id, "u3")
    assert reconcile_reading_builds(ctx.ingest_jobs) == [source_id]
    assert _planners(ctx) == planners + 1
    assert ctx.repository.source_auto_build_state(source_id)["wanted_section_id"] is None


def test_f8_a_keep_ahead_that_failed_is_retried_off_the_rpc_path(tmp_path, monkeypatch):
    """No further report comes (the learner stopped reading): the ingest
    worker retries the ask, not the Reader's progress RPC."""

    root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    jobs.bind(ctx.repository, root, background=True, poll_interval_seconds=0.05, clock=CLOCK, services=fake_services())
    # The worker only retries here: the planning job it queues is not run.
    monkeypatch.setattr(jobs._runner, "drain", lambda **kwargs: 0)
    monkeypatch.setattr(type(jobs), "READING_RETRY_DELAYS", (0.0, 0.0, 0.0), raising=False)
    calls = _failing(monkeypatch)
    planners = _planners(ctx)
    try:
        _report(ctx, extraction_id, 1)
        deadline = time.monotonic() + 5
        while _planners(ctx) == planners and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        jobs.shutdown()

    assert calls == ["u3", "u3"]
    assert _planners(ctx) == planners + 1


def test_f8_the_worker_retries_a_bounded_number_of_times_then_the_next_report_asks_again(tmp_path, monkeypatch):
    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    calls = _failing(monkeypatch, failures=None)

    _report(ctx, extraction_id, 1)
    for _ in range(10):
        jobs.retry_reading_advances(now=float("inf"))

    retries = len(jobs.READING_RETRY_DELAYS)
    assert calls == ["u3"] * (1 + retries)
    # Still not settled: the Reader's next report asks again (and re-arms the
    # worker's retries), rather than treating the section as handled.
    _report(ctx, extraction_id, 2)
    assert calls == ["u3"] * (2 + retries)
    jobs.retry_reading_advances(now=float("inf"))
    assert calls == ["u3"] * (3 + retries)


def test_f8_the_newest_position_wins_a_pending_retry(tmp_path, monkeypatch):
    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    calls = _failing(monkeypatch, failures=2)
    planners = _planners(ctx)

    _report(ctx, extraction_id, 1, section_id="u2")  # fails: a retry waits for u2
    _report(ctx, extraction_id, 1, section_id="u3")  # a first reach, fails too: the retry is for u3 now
    jobs.retry_reading_advances(now=float("inf"))

    assert calls == ["u2", "u3", "u3"]
    assert _planners(ctx) == planners + 1  # u3 is Ch. 2: Ch. 3 is planned
    assert not jobs.reading_advance_pending(extraction_id)
