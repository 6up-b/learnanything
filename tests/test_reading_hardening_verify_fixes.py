"""Fail-first tests for Codex's verify of reading-hardening
(``~/.cache/codex-agent/jobs/20261013-191205-2qLDSo``, verdict REOPENED;
docs/reviews/reading-hardening.md, "Verify follow-up").

* F1 (remainder): a cancel could still be followed by new work. Every path
  that queues work after reading the book's request (a finished build's
  follow-on, ``after_auto_build``, in the sidecar's worker or a CLI drain;
  the act, ``act_on_reading_request``) read the request, worked out the
  chapters, and queued them, with no check that the request was still the
  one it read. A cancel that committed in between (and settled the request)
  was followed by the very work it answered. Now the queueing and the settle
  are one transaction, and the settle is revision-conditional: a request a
  cancel settled first leaves nothing to queue. A planner whose own batch was
  cancelled while it planned queues no build either.
* N2: one stored retry time that overflowed on conversion to UTC
  (``0001-01-01T00:00:00+01:00``) failed the whole sweep pass, so no request
  after it was ever acted on. Now it reads as due now, and each row's time is
  read on its own.

Every model call is a house fake.
"""

from __future__ import annotations

import threading

import pytest

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline import jobs as jobs_module
from learnloop.content.pipeline.runner import IngestRunner
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.repositories import Repository

from tests.test_reading_request_sweep import (
    _deferred_behind_a_queued_build,
    _later,
    _pending,
    _planner_chapters,
    _planners,
)
from tests.test_ux_phase1_add_source import call
from tests.test_ux_phase1_round2_review import _added_book
from tests.ux_phase1_support import BOOK_MARKDOWN, CLOCK, fake_services, write_book

_SYNTHESIS = ("bootstrap_synthesis", "append_synthesis")


def _in_another_thread(work) -> None:
    """``work`` on its own thread (the sidecar's RPC thread, beside the
    worker), joined: it has committed, or failed, when this returns."""

    failure: list[BaseException] = []

    def run() -> None:
        try:
            work()
        except BaseException as exc:  # noqa: BLE001 - re-raised on the test's thread
            failure.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout=60)
    assert not thread.is_alive(), "the cancel never finished"
    if failure:
        raise failure[0]


def _once(monkeypatch, name: str, before) -> dict[str, int]:
    """Run ``before()`` just before the first call of ``core.<name>`` (a step
    that reads, between the request's read and the queueing)."""

    real = getattr(core, name)
    state = {"fired": 0}

    def hooked(*args, **kwargs):
        if not state["fired"]:
            state["fired"] = 1
            before()
        return real(*args, **kwargs)

    monkeypatch.setattr(core, name, hooked)
    return state


def _cli_cancel(root, batch_id: str) -> None:
    """``learnloop ingest-batches cancel``: another process, which does not
    hold the sidecar's in-process reading lock."""

    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["ingest-batches", "cancel", batch_id, "--vault", str(root)])
    assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# F1: a cancel that settled the request first leaves nothing to queue
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("drained_by", ["the sidecar's worker", "a CLI drain"])
def test_f1_a_cancel_committing_while_a_finished_build_plans_its_follow_on_leaves_nothing_queued(
    tmp_path, monkeypatch, drained_by
):
    """Codex's same-process scenario: Ch. 3's build finishes while u4 waits
    behind it; its completion step reads u4 and works out the follow-on
    chapters without the reading lock. The learner cancels the build right
    then: the cancel commits and settles u4. Before, the completion step
    queued the follow-on anyway (and the same drain ran it). Now the
    follow-on and the settle are one transaction that finds u4 already
    settled, so nothing is queued."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    planners = _planners(ctx)

    def cancel_the_running_build() -> None:
        running = [job for job in ctx.repository.ingest_jobs_by_types(_SYNTHESIS) if job["status"] == "running"]
        assert len(running) == 1
        _in_another_thread(lambda: call(ctx, "cancel_ingest_batch", {"batchId": running[0]["batch_id"]}))
        assert _pending(ctx, source_id) is None  # the cancel answered u4

    hook = _once(monkeypatch, "_wanted_chapters", cancel_the_running_build)
    if drained_by == "a CLI drain":
        cli = IngestRunner(Repository(ctx.repository.sqlite_path), vault_root=root, worker_id="cli-test",
                           clock=CLOCK, services=fake_services())
        cli.drain()
    else:
        ctx.ingest_jobs.drain_foreground()

    assert hook["fired"], "the build's completion step never planned a follow-on"
    assert _planners(ctx) == planners, f"the cancel was followed by new work: {_planner_chapters(ctx)}"
    assert _pending(ctx, source_id) is None
    assert not core._source_work_active(ctx.repository, source_id)


def test_f1_a_cli_cancel_committing_while_the_sidecar_acts_leaves_nothing_queued(tmp_path, monkeypatch):
    """Codex's cross-process scenario: u4 waits behind Ch. 3's queued planner.
    The sidecar's sweep reads u4; before it checks the book's work, the CLI
    cancels the planner (and settles u4) in its own process, which the
    sidecar's lock does not cover. Before, the act then found the work gone
    and queued a planner for Ch. 3–4, the chapters just cancelled. Now its
    queueing and settle are one revision-checked transaction: nothing."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    planners = _planners(ctx)

    hook = _once(monkeypatch, "_source_work_waiting_on", lambda: _cli_cancel(root, planner["batch_id"]))
    sweep = ctx.ingest_jobs.sweep_reading_requests(now=_later())

    assert hook["fired"]
    assert sweep.failed == 0
    assert ctx.repository.get_ingest_job(planner["id"])["status"] == "cancelled"
    assert _planners(ctx) == planners, f"the cancel was followed by new work: {_planner_chapters(ctx)}"
    assert _pending(ctx, source_id) is None


def test_f1_a_request_newer_than_the_one_acted_on_is_left_for_its_own_act(tmp_path, monkeypatch):
    """The other half of the revision check: the learner reads on (a newer
    request) between the act's read and its queueing. The act queues nothing
    for the position it read and settles nothing; the newer request is still
    pending, and the next act plans from it."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    revision = ctx.repository.record_reading_request(source_id, extraction_id, "u3")
    planners = _planners(ctx)

    hook = _once(monkeypatch, "_source_work_waiting_on",
                 lambda: ctx.repository.record_reading_request(source_id, extraction_id, "u4"))
    outcome = core.act_on_reading_request(ctx.ingest_jobs, source_id)

    assert hook["fired"]
    assert (outcome or {}).get("batch_id") is None
    assert _planners(ctx) == planners
    request = ctx.repository.pending_reading_request(source_id)
    assert request is not None and request["revision"] == revision + 1 and request["section_id"] == "u4"

    core.act_on_reading_request(ctx.ingest_jobs, source_id)
    assert _pending(ctx, source_id) is None
    assert _planners(ctx) == planners + 1


def test_f1_a_planner_cancelled_while_it_plans_queues_no_build(tmp_path, monkeypatch):
    """The same race one step earlier: Ch. 3's planner is working out its
    build when the learner cancels it. Before, the planner went on to queue
    its build, which the drain then ran (paid work after the cancel), and only
    the planner itself was marked cancelled. Now queueing checks the job's
    cancel in the same transaction: no build is queued."""

    root, ctx, source_id, extraction_id = _added_book(tmp_path)
    planner = _deferred_behind_a_queued_build(ctx, extraction_id, source_id)
    synthesis_before = len(ctx.repository.ingest_jobs_by_types(_SYNTHESIS))

    hook = _once(monkeypatch, "decide_cost", lambda: _in_another_thread(
        lambda: call(ctx, "cancel_ingest_batch", {"batchId": planner["batch_id"]})))
    ctx.ingest_jobs.drain_foreground()

    assert hook["fired"], "the planner never reached its cost decision"
    assert ctx.repository.get_ingest_job(planner["id"])["status"] == "cancelled"
    assert ctx.repository.get_ingest_batch(core.child_batch_id(planner["id"])) is None, "the cancelled planner queued its build"
    assert len(ctx.repository.ingest_jobs_by_types(_SYNTHESIS)) == synthesis_before
    assert _pending(ctx, source_id) is None


# ---------------------------------------------------------------------------
# N2: one unreadable retry time blocks no other request
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stored", ["0001-01-01T00:00:00+01:00", "not a time"])
def test_n2_a_stored_retry_time_that_cannot_be_read_is_due_now(stored):
    assert jobs_module._reading_due_at(stored) is None


def test_n2_a_retry_time_that_overflows_blocks_no_other_book(tmp_path, monkeypatch):
    """Codex's scenario: the first pending request's stored retry time
    overflows on conversion to UTC, and a second book's request is due after
    it. Before, every pass raised on the first row and acted on neither. Now
    the first reads as due now and both are acted on, in one pass that does
    not fail."""

    root, ctx, first, first_extraction = _added_book(tmp_path)
    second_book = write_book(tmp_path, "second_book.md", BOOK_MARKDOWN.replace("Probability", "Statistics"))
    second = call(ctx, "add_source", {"sources": [str(second_book)]})["items"][0]["sourceId"]
    assert second != first
    second_extraction = resolve_extraction_id(ctx.repository, second)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]

    revision = ctx.repository.record_reading_request(first, first_extraction, "u3")
    assert ctx.repository.fail_reading_request(first, revision, attempts=1, retry_at="0001-01-01T00:00:00+01:00")
    ctx.repository.record_reading_request(second, second_extraction, "u3")
    order = [request["source_id"] for request in ctx.repository.pending_reading_requests()]
    assert order == [first, second]  # the unreadable time comes first

    acted: list[str] = []
    real = core.act_on_reading_request

    def spy(jobs, source_id, **kwargs):
        acted.append(source_id)
        return real(jobs, source_id, **kwargs)

    monkeypatch.setattr(core, "act_on_reading_request", spy)
    sweep = ctx.ingest_jobs.sweep_reading_requests(now=_later())

    assert acted == [first, second]
    assert sweep.failed == 0
    assert _pending(ctx, first) is None and _pending(ctx, second) is None
