"""A second source's import waits its turn behind another book's work, and its card says so.

The queue works one job at a time (``claim_next_ingest_job``), so a cheap import
added while another book's build runs stays ``queued`` until that work is done;
its card said "Getting this PDF ready" for minutes (student-3 #27, #92). The
status line now says which book it waits behind and carries that title as a
fact (``waiting_behind``) for Today. The queue's order and concurrency are
unchanged.
"""

from __future__ import annotations

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.clock import utc_now_iso
from learnloop.content.pipeline import add_source as auto

from tests.ux_phase1_support import CLOCK, fresh_library, write_pdf
from tests.ux_phase1_add_source_helpers import _held_ctx, call


def _start_next_job(ctx):
    """The worker takes the next job in the queue's own order, as it would."""

    now = utc_now_iso(CLOCK)
    return ctx.repository.claim_next_ingest_job(worker_id="w_test", now_iso=now, lease_cutoff_iso="2000-01-01T00:00:00Z")


def _card(ctx, source_id):
    return next(card for card in call(ctx, "get_source_library", {})["sources"] if card["sourceId"] == source_id)


def _two_pdfs(tmp_path):
    (tmp_path / "files").mkdir()
    chapter = write_pdf(tmp_path / "files", "chapter.pdf", title="Symmetric Matrices")
    exam = write_pdf(tmp_path / "files", "exam.pdf", title="Past Exam")
    return chapter, exam


def test_an_import_queued_behind_another_books_running_work_names_that_book(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    chapter, exam = _two_pdfs(tmp_path)
    first = call(ctx, "add_source", {"sources": [str(chapter)]})["items"][0]
    running = _start_next_job(ctx)
    assert running["batch_id"] == first["batchId"]  # the chapter's own work runs

    second = call(ctx, "add_source", {"sources": [str(exam)]})["items"][0]

    line = auto.source_status_line(ctx.repository, ctx.require_vault()[0], second["sourceId"])
    assert line["text"] == "Waiting its turn behind “Symmetric Matrices”"
    assert line["tone"] == "working"
    assert line["waiting_behind"] == "Symmetric Matrices"
    card = _card(ctx, second["sourceId"])
    assert card["statusLine"]["text"] == "Waiting its turn behind “Symmetric Matrices”"
    assert card["statusLine"]["waitingBehind"] == "Symmetric Matrices"
    # The book whose work runs says what it always did.
    assert _card(ctx, first["sourceId"])["statusLine"]["text"] == "Getting this PDF ready"
    assert "waitingBehind" not in _card(ctx, first["sourceId"])["statusLine"]


def test_nothing_else_running_keeps_the_line_as_it_was(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    chapter, exam = _two_pdfs(tmp_path)
    call(ctx, "add_source", {"sources": [str(chapter)]})
    second = call(ctx, "add_source", {"sources": [str(exam)]})["items"][0]

    # Both queued, nothing running: no one to wait behind.
    line = auto.source_status_line(ctx.repository, ctx.require_vault()[0], second["sourceId"])
    assert line == {"text": "Getting this PDF ready", "tone": "working", "action": None, "details": None}


def test_a_link_still_being_fetched_names_the_book_it_waits_behind(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    chapter, _exam = _two_pdfs(tmp_path)
    call(ctx, "add_source", {"sources": [str(chapter)]})
    _start_next_job(ctx)
    link = call(ctx, "add_source", {"sources": ["https://example.org/notes"]})["items"][0]

    pending = next(entry for entry in call(ctx, "get_source_library", {})["pending"] if entry["batchId"] == link["batchId"])
    assert pending["statusLine"]["text"] == "Waiting its turn behind “Symmetric Matrices”"
    assert pending["statusLine"]["waitingBehind"] == "Symmetric Matrices"
