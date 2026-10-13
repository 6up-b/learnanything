"""Fail-first tests for UX Phase 1's finishing pass (docs/reviews/ux-phase1-finish.md),
the backend half: Codex's final verify of usability round 2
(``~/.cache/codex-agent/jobs/20261013-130030-Ux113F``).

* F8 (reopened) — a failed startup reconciliation stranded reading advancement:
  after a restart cleared the in-memory retry map, a reconciliation enqueue
  failure was only logged, and later progress reports for the same section
  coalesced against the empty map, so the durable pending position was never
  retried.
* F9 — an older background retry erased a newer deferred reading position: the
  worker's retry queued its build, a Reader report deferred a newer section
  while that work ran, and the worker's unconditional clear then deleted it.

The keep-ahead path now has one authoritative state: the book's durable
reading request (position, revision, failed attempts, next retry) in
``source_auto_build_state``. Every model call is a house fake.
"""

from __future__ import annotations

import sqlite3
import threading
import time

from learnloop.content.pipeline import add_source as core
from learnloop.db.repositories import Repository

from tests.test_ux_phase1_add_source import call
from tests.test_ux_phase1_round2_review import _added_book
from tests.ux_phase1_support import CLOCK, fake_services


def _planners(ctx) -> int:
    return len(ctx.repository.ingest_jobs_by_types((core.AUTO_STUDY_MAP_JOB,)))


def _report(ctx, extraction_id, seen, section_id="u3"):
    call(ctx, "reader.mark_section_progress",
         {"extractionId": extraction_id, "sectionId": section_id, "spansSeen": seen, "spanCount": 4})


def _failing_enqueue(monkeypatch, failures: int | None = 1, after=None) -> list[list[str]]:
    """Queueing a keep-ahead build fails ``failures`` times (``None``: always),
    then works. ``after(n)`` runs once the ``n``-th call has queued. Returns the
    chapters each call asked for."""

    calls: list[list[str]] = []
    real = core.request_auto_build

    def flaky(jobs, source_id, *args, **kwargs):
        calls.append(list(kwargs.get("chapter_ids") or []))
        if failures is None or len(calls) <= failures:
            raise sqlite3.OperationalError("database is locked")
        batch_id = real(jobs, source_id, *args, **kwargs)
        if after is not None:
            after(len(calls))
        return batch_id

    monkeypatch.setattr(core, "request_auto_build", flaky)
    return calls


def _immediate_retries(monkeypatch, jobs) -> None:
    monkeypatch.setattr(type(jobs), "READING_RETRY_DELAYS", (0.0, 0.0, 0.0), raising=False)


def _restart(root):
    """A new sidecar process on the same library: nothing in memory survives.
    Its ingest jobs drain in the foreground, as the tests' first process does."""

    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    vault = load_vault(root)
    ctx.ingest_jobs.bind(Repository(VaultPaths(root, vault.config).sqlite_path), root, background=False,
                         clock=CLOCK, services=fake_services())
    ctx.load(root)  # startup maintenance reconciles pending reading positions
    return ctx


def _pending(ctx, source_id):
    state = ctx.repository.source_auto_build_state(source_id)
    return state["wanted_section_id"]


# ---------------------------------------------------------------------------
# F8 (reopened) — a failed startup reconciliation is retried, not stranded
# ---------------------------------------------------------------------------


def test_f8_a_failed_start_reconciliation_is_asked_again_by_the_next_reports(tmp_path, monkeypatch):
    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    calls = _failing_enqueue(monkeypatch, failures=2)
    planners = _planners(ctx)

    _report(ctx, extraction_id, 1)  # the Reader's ask fails: u3 is pending
    assert _pending(ctx, source_id) == "u3"
    ctx.ingest_jobs.shutdown()

    restarted = _restart(root)  # the start's reconciliation fails too
    assert len(calls) == 2
    assert _pending(restarted, source_id) == "u3"
    _immediate_retries(monkeypatch, restarted.ingest_jobs)

    for seen in (2, 3, 4):
        _report(restarted, extraction_id, seen)
    restarted.ingest_jobs.retry_reading_advances()

    # The next report asked again and Ch. 3 is planned; nothing is left waiting.
    assert len(calls) == 3
    assert _planners(restarted) == planners + 1
    assert _pending(restarted, source_id) is None
    assert not restarted.ingest_jobs.reading_advance_pending(extraction_id)


def test_f8_a_failed_start_reconciliation_is_retried_by_the_worker(tmp_path, monkeypatch):
    """No further report comes (the learner closed the book): the restored
    request is retried off the RPC path, by the ingest worker."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    _immediate_retries(monkeypatch, ctx.ingest_jobs)
    calls = _failing_enqueue(monkeypatch, failures=2)
    planners = _planners(ctx)
    _report(ctx, extraction_id, 1)
    ctx.ingest_jobs.shutdown()

    restarted = _restart(root)
    assert len(calls) == 2
    # Still asked for again by the Reader while it is not settled.
    assert restarted.ingest_jobs.reading_advance_pending(extraction_id)

    assert restarted.ingest_jobs.retry_reading_advances() == 1

    assert len(calls) == 3
    assert _planners(restarted) == planners + 1
    assert _pending(restarted, source_id) is None


def test_f8_the_start_acts_at_once_and_rearms_a_backed_off_request(tmp_path, monkeypatch):
    """A request whose failures backed it off before the restart is acted on
    by the start at once, and a failure there starts a fresh backoff.

    (Until reading-hardening part 1 the worker's retries ran out after three;
    now a request is never given up: the sweep backs off to every 300 s, see
    ``tests/test_reading_request_sweep.py``.)"""

    from datetime import UTC, datetime, timedelta

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    calls = _failing_enqueue(monkeypatch, failures=None)
    _report(ctx, extraction_id, 1)
    moment = datetime.now(UTC) + timedelta(hours=1)
    for _ in range(6):
        jobs.retry_reading_advances(now=moment)
        moment += timedelta(seconds=300)  # every retry time comes
    failed = len(calls)
    assert failed == 7
    request = ctx.repository.pending_reading_request(source_id)
    assert request["attempts"] == failed and request["retry_at"] >= jobs_iso(moment)  # minutes away
    jobs.shutdown()

    restarted = _restart(root)  # the retry is still minutes away: the start asks at once
    assert len(calls) == failed + 1
    request = restarted.repository.pending_reading_request(source_id)
    assert request["attempts"] == 1  # a fresh backoff
    assert _pending(restarted, source_id) == "u3"


def test_f8_a_retry_falling_due_after_the_worker_stepped_aside_is_acted_on_by_the_sweep(tmp_path, monkeypatch):
    """Codex's follow-up F1 (finish review) found the worker's idle exit could
    strand a retry that fell due between its scan and its exit check. The
    worker no longer decides that (reading-hardening, part 1): the real worker
    loop steps aside with the retry still to come, and the reading sweep acts
    on it once it is due."""

    from datetime import UTC, datetime, timedelta

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]  # nothing else wakes it
    jobs._poll_interval = 0.01
    planners = _planners(ctx)

    start = datetime.now(UTC).replace(microsecond=0) + timedelta(hours=1)
    deadline = start + timedelta(seconds=1)
    repo = ctx.repository
    revision = repo.record_reading_request(source_id, extraction_id, "u3")
    assert repo.fail_reading_request(source_id, revision, attempts=1, retry_at=jobs_iso(deadline))

    worker = threading.Thread(target=jobs._worker_loop, daemon=True)
    jobs._worker_thread = worker
    worker.start()
    worker.join(30)
    assert not worker.is_alive()
    assert jobs._worker_thread is None  # it stepped aside: its queue is idle
    assert _pending(ctx, source_id) == "u3"  # the worker left the request to the sweep

    assert jobs.retry_reading_advances(now=start) == 0  # not due yet: left alone
    assert _planners(ctx) == planners
    assert jobs.retry_reading_advances(now=deadline) == 1
    # The retry ran: Ch. 3's build was planned and nothing is left due.
    assert _pending(ctx, source_id) is None
    assert _planners(ctx) == planners + 1
    assert repo.due_reading_requests(jobs_iso(deadline + timedelta(days=1))) == []


def jobs_iso(moment):
    from learnloop.content.pipeline import jobs as jobs_module

    return jobs_module._iso(moment)


# ---------------------------------------------------------------------------
# F9 — an older retry never erases a newer position
# ---------------------------------------------------------------------------


def _wait_for(predicate, timeout=10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def test_f9_an_older_retry_never_erases_a_newer_deferred_position(tmp_path, monkeypatch):
    """Codex's interleaving, run on real threads and made deterministic with
    events: the worker's retry for u3 queues Ch. 3's build and pauses before it
    settles; a Reader report reaches u4 (Ch. 3) meanwhile, while Ch. 3's work
    runs; then the retry finishes. u4 must survive and be built after Ch. 3."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    # The builds stay queued (the book's work is running) until drained below.
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    _immediate_retries(monkeypatch, jobs)
    queued, resume = threading.Event(), threading.Event()

    def pause_the_retry(n):
        if n == 2:  # the worker's retry has queued Ch. 3 and has not settled yet
            queued.set()
            assert resume.wait(10)

    calls = _failing_enqueue(monkeypatch, failures=1, after=pause_the_retry)
    planners = _planners(ctx)

    _report(ctx, extraction_id, 1, section_id="u3")  # the Reader's ask fails: u3 waits for a retry
    errors: list[BaseException] = []

    def run(target, *args, **kwargs):
        try:
            target(*args, **kwargs)
        except BaseException as error:  # noqa: BLE001 - surfaced below
            errors.append(error)

    worker = threading.Thread(target=run, args=(jobs.retry_reading_advances,))
    worker.start()
    assert queued.wait(10)
    reader = threading.Thread(target=run, args=(_report, ctx, extraction_id, 1), kwargs={"section_id": "u4"})
    reader.start()
    # The Reader's newer position is durable before the older retry settles.
    assert _wait_for(lambda: _pending(ctx, source_id) == "u4")
    resume.set()
    worker.join(10)
    reader.join(10)
    assert not worker.is_alive() and not reader.is_alive()
    assert errors == []

    assert _planners(ctx) == planners + 1  # Ch. 3, from the retry
    assert _pending(ctx, source_id) == "u4"  # kept for when Ch. 3's work finishes

    # Ch. 3's work finishes: the waiting position is acted on (Ch. 4).
    jobs.drain_foreground()
    jobs.retry_reading_advances()
    assert _pending(ctx, source_id) is None
    assert _planners(ctx) == planners + 2


def test_f9_a_settled_request_clears_only_its_own_revision(tmp_path):
    """The store's compare: settling an older revision leaves a newer one."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    repo = ctx.repository
    older = repo.record_reading_request(source_id, extraction_id, "u3")
    newer = repo.record_reading_request(source_id, extraction_id, "u4")
    assert newer > older

    assert repo.settle_reading_request(source_id, older) is False
    assert _pending(ctx, source_id) == "u4"
    assert repo.fail_reading_request(source_id, older, attempts=1, retry_at=None) is False
    assert repo.pending_reading_request(source_id)["attempts"] == 0

    assert repo.settle_reading_request(source_id, newer) is True
    assert _pending(ctx, source_id) is None


def test_f8_a_saved_report_keeps_its_ask_even_when_acting_cannot_start(tmp_path, monkeypatch):
    """The ask is recorded in the same transaction as the progress it came
    with: when acting on it fails before anything is counted (here, finding
    the book), the request is still there, due, and the worker acts on it."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    planners = _planners(ctx)
    real = core._extraction_source
    broken = {"on": True}

    def flaky(repo, ext):
        if broken["on"]:
            raise sqlite3.OperationalError("database is locked")
        return real(repo, ext)

    monkeypatch.setattr(core, "_extraction_source", flaky)

    out = call(ctx, "reader.mark_section_progress",
               {"extractionId": extraction_id, "sectionId": "u3", "spansSeen": 1, "spanCount": 4})
    assert out["progress"]["spansSeen"] == 1  # the Reader's save went through
    request = ctx.repository.pending_reading_request(source_id)
    assert (request["extraction_id"], request["section_id"]) == (extraction_id, "u3")
    assert _planners(ctx) == planners

    broken["on"] = False
    assert jobs.retry_reading_advances() == 1
    assert _planners(ctx) == planners + 1
    assert _pending(ctx, source_id) is None


def test_f8_a_request_waiting_on_running_work_is_quiet_for_the_reader(tmp_path):
    """A request deferred while the book's work runs is not a failure: reading
    on inside the section stays coalesced (round-2 F1), and the worker acts on
    it once the work ends."""

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    jobs = ctx.ingest_jobs
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    _report(ctx, extraction_id, 1, section_id="u3")  # Ch. 3 queued: the book's work runs
    planners = _planners(ctx)
    _report(ctx, extraction_id, 1, section_id="u4")  # deferred
    assert _pending(ctx, source_id) == "u4"
    assert not jobs.reading_advance_pending(extraction_id)
    revision = ctx.repository.pending_reading_request(source_id)["revision"]

    for seen in (2, 3):
        _report(ctx, extraction_id, seen, section_id="u4")
    assert ctx.repository.pending_reading_request(source_id)["revision"] == revision  # nothing asked again
    assert jobs.retry_reading_advances() == 0  # still waiting on Ch. 3
    assert _planners(ctx) == planners

    jobs.drain_foreground()
    jobs.retry_reading_advances()
    assert _pending(ctx, source_id) is None
    assert _planners(ctx) == planners + 1


def test_f9_undo_invalidates_a_request_being_acted_on(tmp_path):
    """Undo forgets the pending request and advances its revision, so an
    actor still holding the older revision can neither settle nor fail it."""

    from learnloop.content.pipeline.add_source import undo_source_questions

    _root, ctx, source_id, extraction_id = _added_book(tmp_path)
    repo = ctx.repository
    revision = repo.record_reading_request(source_id, extraction_id, "u4")
    undo_source_questions(ctx.ingest_jobs, source_id, clock=CLOCK)
    assert repo.pending_reading_request(source_id) is None
    assert repo.fail_reading_request(source_id, revision, attempts=1, retry_at="2026-10-13T09:00:00Z") is False
    assert repo.source_auto_build_state(source_id)["wanted_retry_at"] is None


# ---------------------------------------------------------------------------
# Persona re-test #6 — the words match what the thing is and what happens
# ---------------------------------------------------------------------------


def test_6_a_pdf_is_a_pdf_until_its_text_says_book_or_paper(tmp_path):
    """The hand-over said "Getting this book ready" for a paper, and a
    two-page handout was a "book"."""

    from learnloop.content.pipeline.add_source import kind_noun, source_kind_noun
    from tests.test_ux_phase1_usability_round2 import _pdf_with_units
    from tests.ux_phase1_support import fresh_library, repository

    root = fresh_library(tmp_path)
    repo = repository(root)
    _pdf_with_units(repo, "src_handout", ["Week 3 handout", "Exercises"], pages=2)
    _pdf_with_units(repo, "src_book", ["Contents", "1 Probability and counting", "2 Conditional probability"], pages=113)
    _pdf_with_units(repo, "src_paper", ["Abstract", "1 Introduction", "References"], pages=11)

    assert kind_noun("pdf") == "PDF"  # before its text is ready: the hand-over, a scan
    assert source_kind_noun(repo, "src_handout", "pdf") == "PDF"
    assert source_kind_noun(repo, "src_book", "pdf") == "book"
    assert source_kind_noun(repo, "src_paper", "pdf") == "paper"
    assert kind_noun("textfile") == "book" and kind_noun("youtube") == "video"


def test_6_a_pdf_being_prepared_is_getting_this_pdf_ready(tmp_path):
    from tests.test_ux_phase1_add_source import _held_ctx
    from tests.ux_phase1_support import fresh_library, write_pdf

    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    item = call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path))]})["items"][0]

    assert item["kindNoun"] == "PDF"
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["kindNoun"] == "PDF"
    assert card["statusLine"]["text"] == "Getting this PDF ready"


def test_6_build_them_says_it_builds_as_you_read(tmp_path):
    """A book with no questions offered "Build them", which built one chapter,
    while details offered "Build questions for the whole book"."""

    from tests.test_ux_phase1_round2_review import _imported_book

    _root, _ctx, card = _imported_book(tmp_path)
    assert card["statusLine"]["text"] == "No questions for this book yet"
    assert card["statusLine"]["action"] == {"kind": "retry", "label": "Build them as you read"}

