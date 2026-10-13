"""The per-book AI opt-out is retired (docs/reviews/reading-hardening.md, part 3).

Owner, 2026-10-13: it is fine to send books to an AI; the per-book "Never send
this book to an AI" (formerly "Keep this book on this computer", spec
ux_learnloop_v1 §6.6) was not asked for. It is gone end to end: Add's option,
book details' two actions, the library card's flag, and every refusal built on
it (question builds, the Reader's Ask, background requests and section checks,
RW1a's passage check, whole-file extraction). The one-time consent sentence and
OK when an AI is connected stay, and so does the separate OK for sending a
whole file.

Migration 198's ``source_artifacts.keep_local`` column stays (no migration);
nothing reads it, and ``learnloop doctor`` names a book that still has it set,
as it does for other retired settings. Every model call is a house fake.
"""

from __future__ import annotations

import pydantic
import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.add_source import latest_auto_outcome, source_status_line
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import CLOCK, Calls, fake_services, fresh_library, grant_consent, write_book


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.delenv("LEARNLOOP_MARKER_PROVIDER", raising=False)


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _ctx(root, *, services=None, hold=False, reader_client=None):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services or fake_services(),
                         reader_synth_client_factory=(lambda: reader_client) if reader_client is not None else None)
    if hold:
        ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return ctx


def _carry_retired_choice(repo, source_id):
    """What a library from before the retirement may hold for a book."""

    with repo.connection() as connection:
        connection.execute("UPDATE source_artifacts SET keep_local = 1 WHERE id = ?", (source_id,))
        connection.commit()


def _card(ctx, source_id):
    return next(card for card in call(ctx, "get_source_library", {})["sources"] if card["sourceId"] == source_id)


# ---------------------------------------------------------------------------
# The control and its RPC fields are gone
# ---------------------------------------------------------------------------


def test_add_no_longer_takes_a_keep_local_option(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _ctx(root, hold=True)

    with pytest.raises(pydantic.ValidationError):
        call(ctx, "add_source", {"sources": [str(write_book(tmp_path))], "keepLocal": True})
    assert "keep_local" not in core.AddSourceOptions.__dataclass_fields__


def test_book_details_no_longer_offer_keeping_a_book_off_the_ai(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]

    for action in ("keep_local", "share_with_ai"):
        with pytest.raises(pydantic.ValidationError):
            call(ctx, "source_action", {"sourceId": source_id, "action": action})
    assert "keepLocal" not in _card(ctx, source_id)
    assert not hasattr(core, "keep_on_this_computer") and not hasattr(core, "share_with_ai")


# ---------------------------------------------------------------------------
# A book that still carries the retired choice is treated like any other
# ---------------------------------------------------------------------------


def test_a_book_carrying_the_retired_choice_gets_its_questions_built(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    calls = Calls()
    ctx = _ctx(root, services=fake_services(calls=calls), hold=True)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    _carry_retired_choice(ctx.repository, source_id)

    ctx.ingest_jobs.drain_foreground()

    assert latest_auto_outcome(ctx.repository, source_id)["outcome"] == "building"
    assert calls.inventory_calls > 0 and calls.synthesis_calls > 0
    line = source_status_line(ctx.repository, load_vault(root), source_id)
    assert "AI" not in line["text"] or "connect" in line["text"].lower()


def test_the_reader_asks_about_a_book_carrying_the_retired_choice(tmp_path, monkeypatch):
    """The Reader's background request and section check are not refused, and
    the drain sends the request (it cancelled it before)."""

    from types import SimpleNamespace

    from learnloop_sidecar.handlers import ai_providers
    from tests.test_reader_requests import _FakePresetClient

    monkeypatch.setattr(ai_providers, "ready_canonical_ingest_provider",
                        lambda vault: ("stub", SimpleNamespace(ready=True), object()))
    root = fresh_library(tmp_path)
    grant_consent(root)
    client = _FakePresetClient()
    ctx = _ctx(root, reader_client=client)
    item = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]
    source_id = item["sourceId"]
    _carry_retired_choice(ctx.repository, source_id)
    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    ir = ctx.repository.load_document_ir(extraction_id)
    span_id = next(block.span_id for block in sorted(ir.blocks, key=lambda b: b.ordinal) if (block.text or "").strip())
    section_id = ir.units[0].unit_id

    queued = call(ctx, "reader.enqueue_request", {
        "sourceId": source_id, "revisionId": item["revisionId"], "extractionId": extraction_id,
        "spanId": span_id, "preset": "worked_example",
    })
    ctx.ingest_jobs.kick_reader_drain()
    assert len(client.calls) == 1
    request_id = queued["request"]["requestId"] if "request" in queued else queued["requestId"]
    assert ctx.repository.get_reader_request(request_id)["status"] == "complete"

    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]  # the check stays queued
    authored = call(ctx, "reader.author_section_question", {"extractionId": extraction_id, "sectionId": section_id})
    assert authored["status"] == "queued"


def test_whole_file_extraction_is_no_longer_narrowed_for_the_retired_choice(tmp_path):
    """A kept-local book used to be read by a local extractor only (never the
    whole-PDF model): the engine the library configured applies to every book."""

    from types import SimpleNamespace

    from learnloop.content.pipeline.jobs import _pdf_payload_config
    from tests.ux_phase1_support import set_config

    root = fresh_library(tmp_path)
    set_config(root, {("ingest", "pdf", "engine"): "native"})
    retired = SimpleNamespace(job={"_keep_local": True}, payload={"keep_local": True}, vault_root=root)
    assert _pdf_payload_config(retired)["engine"] == "native"


# ---------------------------------------------------------------------------
# States the retired choice left behind: one tap moves them on
# ---------------------------------------------------------------------------


def test_a_plan_that_waited_on_the_retired_choice_offers_build_them(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _ctx(root, hold=True)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    runner = ctx.ingest_jobs._require_runner()
    runner.drain(max_jobs=1)  # the import: the book is readable
    planner = next(job for job in core.auto_jobs(ctx.repository, source_id))
    with ctx.repository.connection() as connection:  # what the retired planner recorded
        connection.execute(
            "UPDATE ingest_jobs SET status = 'completed', result_json = ? WHERE id = ?",
            ('{"outcome": "waiting", "reason": "kept_local", "source_id": "%s"}' % source_id, planner["id"]),
        )
        connection.commit()

    line = _card(ctx, source_id)["statusLine"]
    assert line["text"] == "No questions for this book yet"
    assert line["action"] == {"kind": "retry", "label": "Build them as you read"}

    del ctx.ingest_jobs._ensure_worker
    call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    assert latest_auto_outcome(ctx.repository, source_id)["outcome"] == "building"


def test_an_import_the_retired_choice_refused_offers_to_get_it_ready(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs as jobs_module
    from learnloop.content.pipeline.runner import IngestRunnerError

    refused = {"on": True}

    def transcribe(fetched, ctx):
        if refused["on"]:  # what the retired guard raised for a kept-local recording
            raise IngestRunnerError("never sent", code="kept_local", retryable=False)
        raise IngestRunnerError("transcription endpoint not reachable in tests", code="audio_failed")

    monkeypatch.setattr(jobs_module, "_extract_audio", transcribe)
    monkeypatch.setattr(jobs_module, "_guard_file_upload", lambda ctx, flow: None)
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _ctx(root)
    audio = tmp_path / "lecture_one.mp3"
    audio.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00fake audio frames")
    source_id = call(ctx, "add_source", {"sources": [str(audio)]})["items"][0]["sourceId"]

    line = _card(ctx, source_id)["statusLine"]
    assert line["text"] == "This recording isn't ready yet"
    assert line["action"] == {"kind": "retry", "label": "Get it ready"}


# ---------------------------------------------------------------------------
# Doctor names a book that still carries it, as for other retired settings
# ---------------------------------------------------------------------------


def test_doctor_names_books_that_still_carry_the_retired_choice(tmp_path):
    from learnloop.ops.doctor import run_doctor

    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _ctx(root, hold=True)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    assert not [issue for issue in run_doctor(root).issues if issue.code == "source:retired_keep_local"]

    _carry_retired_choice(ctx.repository, source_id)
    notes = [issue for issue in run_doctor(root).issues if issue.code == "source:retired_keep_local"]

    assert len(notes) == 1
    assert notes[0].severity == "warning"
    assert notes[0].details["source_ids"] == [source_id]
    assert "retired" in notes[0].message and "ignored" in notes[0].message
