"""UX Phase 1 sidecar contract: one Add, the book opens at once (spec §6.2-§6.3, §10 1.2/1.4/1.6).

``add_source`` registers a local file and stores its original synchronously, so
the Reader can show the original PDF before any extraction; the rest happens in
the durable queue. The library cards carry one learner-facing status line and
``reader.pdf_view`` answers for a book that is still being prepared.
"""

from __future__ import annotations

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.pipeline.add_source import AUTO_STUDY_MAP_JOB
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, write_book, write_pdf


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _held_ctx(root):
    """A sidecar whose queue only records: nothing drains, so the state right
    after Add (registered, not yet extracted) can be observed."""

    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return ctx


def _draining_ctx(root):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    return ctx


def test_add_source_opens_a_pdf_at_once_with_its_original(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    pdf = write_pdf(tmp_path, title="Probability")

    result = call(ctx, "add_source", {"sources": [str(pdf)]})

    item = result["items"][0]
    assert item["status"] == "added"
    assert item["kind"] == "pdf"
    assert item["title"] == "Probability"
    assert item["preparing"] is True
    assert item["sourceId"].startswith("src_") and item["revisionId"].startswith("rev_")
    assert result["opened"] == item
    # The Reader can show the original PDF before any extraction exists.
    view = call(ctx, "reader.pdf_view", {"extractionId": item["sourceId"]})
    assert view["available"] is True
    assert view["preparing"] is True
    assert view["extractionId"] is None
    assert view["sourceId"] == item["sourceId"]
    assert view["blocks"] == []
    assert view["fileName"]
    # The shelf shows the book with one quiet line, never a file:// title.
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["title"] == "Probability"
    # A PDF until its text says book or paper (finishing pass, #6).
    assert card["kindNoun"] == "PDF"
    assert card["statusLine"]["text"] == "Getting this PDF ready"
    assert card["statusLine"]["tone"] == "working"
    # The queue holds exactly one add batch: the import, then the automatic build planner.
    batch = ctx.repository.get_ingest_batch(item["batchId"])
    jobs = ctx.repository.ingest_jobs_for_batch(batch["id"])
    assert batch["workflow_type"] == "add_source"
    assert [job["job_type"] for job in jobs] == ["import", AUTO_STUDY_MAP_JOB]


def test_a_pdf_without_a_title_is_named_from_its_file(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    pdf = write_pdf(tmp_path, "sheldon_axler-linear_algebra_done_right.pdf", title=None)
    item = call(ctx, "add_source", {"sources": [str(pdf)]})["items"][0]
    assert item["title"] == "Sheldon Axler Linear Algebra Done Right"


def test_adding_the_same_book_again_opens_it_without_a_copy(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    pdf = write_pdf(tmp_path)
    first = call(ctx, "add_source", {"sources": [str(pdf)]})["items"][0]
    batches = len(ctx.repository.list_ingest_batches())

    again = call(ctx, "add_source", {"sources": [str(pdf)]})["items"][0]

    assert again["status"] == "existing"
    assert again["sourceId"] == first["sourceId"]
    assert again["message"] == "Already in your library — opened where you left off."
    assert len(ctx.repository.all_source_artifacts()) == 1
    assert len(ctx.repository.list_ingest_batches()) == batches


def test_unrecognised_input_gets_one_plain_line(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    item = call(ctx, "add_source", {"sources": ["just some words"]})["items"][0]
    assert item["status"] == "unsupported"
    assert item["message"] == (
        "LearnLoop can't open this yet — it reads PDFs, images, web pages, arXiv, YouTube, Markdown, text and subtitles."
    )
    assert ctx.repository.list_ingest_batches() == []


def test_several_files_become_several_books_and_the_first_opens(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    first = write_book(tmp_path, "one.md")
    second = write_book(tmp_path, "two.md")
    result = call(ctx, "add_source", {"sources": [str(first), str(second)]})
    assert [item["status"] for item in result["items"]] == ["added", "added"]
    assert result["opened"]["title"] == "One"
    assert len(ctx.repository.all_source_artifacts()) == 2


def test_a_link_is_queued_and_shows_on_the_shelf_while_it_is_fetched(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    item = call(ctx, "add_source", {"sources": ["https://example.org/notes"]})["items"][0]
    assert item["status"] == "queued"
    assert item["kind"] == "web"
    assert item["sourceId"] is None and item["batchId"]
    shelf = call(ctx, "get_source_library", {})
    pending = shelf["pending"]
    assert [entry["batchId"] for entry in pending] == [item["batchId"]]
    assert pending[0]["statusLine"]["text"] == "Getting this article ready"
    # Removing it from the shelf cancels the add; it leaves the shelf.
    call(ctx, "cancel_ingest_batch", {"batchId": item["batchId"]})
    assert call(ctx, "get_source_library", {})["pending"] == []


def test_add_source_with_more_options(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_: True)
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    pdf = write_pdf(tmp_path)
    item = call(
        ctx,
        "add_source",
        {"sources": [str(pdf)], "pages": "1-2", "problemSet": True, "textRecognition": True},
    )["items"][0]
    jobs = ctx.repository.ingest_jobs_for_batch(item["batchId"])
    import_job = next(job for job in jobs if job["job_type"] == "import")
    assert import_job["payload"]["page_selection"] == [0, 1]
    assert import_job["payload"]["reader_enabled"] is False
    # An extractor that recognises text, named explicitly (review F9).
    assert import_job["payload"]["pdf_config"] == {"engine": "marker", "force_ocr": True}
    auto_job = next(job for job in jobs if job["job_type"] == AUTO_STUDY_MAP_JOB)
    assert auto_job["payload"]["problem_set"] is True
    # The per-book "keep on this computer" option is retired (owner, 2026-10-13).
    assert "keep_local" not in import_job["payload"] and "keep_local" not in auto_job["payload"]


def test_add_source_rejects_a_bad_page_range_plainly(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path))], "pages": "9-3"})
    assert caught.value.code == "invalid_page_range"


def test_the_whole_path_runs_with_the_queue_draining(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    item = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["readiness"] == "ready"
    assert card["statusLine"]["text"] == "Questions for Ch. 1–2 come up as you read"
    assert card["subjectId"] == "probability-book"
    assert list(load_vault(root).subjects) == ["probability-book"]
    # Undo from the card, in one tap.
    undone = call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "undo_questions"})
    assert undone["reverted"] > 0
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["statusLine"]["text"] == "Questions for this book were taken back out"


def test_source_action_rejects_unknown_actions(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)
    with pytest.raises(Exception):
        call(ctx, "source_action", {"sourceId": "src_x", "action": "launch_rockets"})


def test_reading_progress_reaches_the_reading_order_build(tmp_path, monkeypatch):
    """reader.mark_section_progress hands the position to the progressive build
    (best effort: a failure there never fails the Reader)."""

    from learnloop.content.pipeline import add_source as core

    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    seen = []
    monkeypatch.setattr(core, "plan_reading_advance",
                        lambda jobs, source_id, extraction_id, section_id: seen.append(section_id))
    from learnloop.content.sources.source_outline import resolve_extraction_id

    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    call(ctx, "reader.mark_section_progress", {"extractionId": extraction_id, "sectionId": "u3", "revealed": True})
    assert seen == ["u3"]

    def broken(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(core, "plan_reading_advance", broken)
    out = call(ctx, "reader.mark_section_progress", {"extractionId": extraction_id, "sectionId": "u4", "revealed": True})
    assert out["progress"]["sectionId"] == "u4"
