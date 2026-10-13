"""UX Phase 1, usability round 2 (docs/reviews/ux-phase1.md, "Usability round 2 fixes").

Fail-first tests for what the re-test of the round-1 revisions found on the
Phase 1 path (the backend half; the frontend half is in vitest):

* R4 — "Read it again with text recognition" was offered on every readable
  book while text recognition isn't installed, and ended in "Something went
  wrong. Try again."; the backend's own clear sentence never reached the
  screen.
* Minors — the scan details pasted the extractor's raw "install marker-pdf for
  OCR support"; an 11-page paper was a "book" with "Questions … in about 13
  min" for a build that took seconds; the one-time OK named ChatGPT to a Codex
  user; a book added through Ingest got its file name as its title and no line
  at all; with no AI the cards still said questions "come up as you read".
"""

from __future__ import annotations

import pytest

from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarError

from tests.test_ux_phase1_add_source import _draining_ctx, _held_ctx, call
from tests.ux_phase1_support import fresh_library, grant_consent, write_book, write_pdf

# What a learner may never read on these surfaces (spec §9), in the backend's
# own words too.
_JARGON = ("marker", "ocr", "pypdf", "pip install", "extraction", "synthesis", "codex_")


def _plain(text: str | None) -> None:
    lowered = (text or "").lower()
    for term in _JARGON:
        assert term not in lowered, (term, text)


def _card(ctx, source_id):
    return next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == source_id)


def _added_book(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    return root, ctx, source_id


# ---------------------------------------------------------------------------
# R4 — text recognition is offered only where it can run, and says why not
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("installed", [True, False])
def test_r4_a_card_says_whether_text_recognition_can_run_for_it(tmp_path, monkeypatch, installed):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: installed)
    _root, ctx, source_id = _added_book(tmp_path)

    assert _card(ctx, source_id)["textRecognitionAvailable"] is installed


def test_r4_asking_for_text_recognition_that_is_not_installed_says_how_to_get_it(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: False)
    _root, ctx, source_id = _added_book(tmp_path)

    with pytest.raises(SidecarError) as caught:
        call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})

    assert caught.value.code == "text_recognition_unavailable"
    message = str(caught.value)
    assert "isn't installed" in message
    assert "uv sync --extra pdf" in message  # how to get it, plainly
    _plain(message)


# ---------------------------------------------------------------------------
# Scans: the details say how to get text recognition, never the raw message
# ---------------------------------------------------------------------------


def test_scan_details_say_how_to_get_text_recognition_plainly(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: False)
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path, "recitation.pdf"))]})["items"][0]["sourceId"]

    line = _card(ctx, source_id)["statusLine"]

    assert line["text"] == "This PDF is a scan — LearnLoop can show its pages but can't read them yet"
    assert "uv sync --extra pdf" in line["details"]
    assert "restart LearnLoop" in line["details"]
    _plain(line["details"])


def test_adding_with_text_recognition_that_is_not_installed_says_how_to_get_it(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: False)
    root = fresh_library(tmp_path)
    ctx = _held_ctx(root)

    item = call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path))], "textRecognition": True})["items"][0]

    assert "uv sync --extra pdf" in item["message"]
    _plain(item["message"])


# ---------------------------------------------------------------------------
# A paper is a paper, and the build estimate is not invented
# ---------------------------------------------------------------------------


def _pdf_with_units(repo, source_id: str, labels: list[str], *, pages: int = 11) -> None:
    from tests.test_source_inventory import _block, _ir, _persist, _register_revision

    _register_revision(repo, source_id=source_id, revision_id=f"rev_{source_id}")
    per_unit = max(1, pages // max(1, len(labels)))
    units = []
    for index, label in enumerate(labels):
        page = min(pages - 1, index * per_unit)
        units.append((f"u{index + 1}", label, [_block(f"s{index + 1}", f"{label} text about tutoring.", page=page)],
                      f"sha256:{source_id}{index}", page))
    _persist(repo, _ir(units), revision_id=f"rev_{source_id}", extraction_id=f"ext_{source_id}")


def test_a_pdf_with_an_abstract_is_a_paper(tmp_path):
    from learnloop.content.pipeline.add_source import source_kind_noun
    from tests.ux_phase1_support import repository

    root = fresh_library(tmp_path)
    repo = repository(root)
    _pdf_with_units(repo, "src_paper", ["Abstract", "1 Introduction", "2 Related Work", "References"])
    _pdf_with_units(repo, "src_book", ["Contents", "1 Probability and counting", "2 Conditional probability"], pages=113)

    assert source_kind_noun(repo, "src_paper", "pdf") == "paper"
    assert source_kind_noun(repo, "src_book", "pdf") == "book"


def test_a_first_build_promises_no_minutes_it_cannot_know(tmp_path):
    from learnloop.content.pipeline.add_source import source_status_line
    from tests.test_ux_phase1_review_fixes import _add, _drain, _jobs
    from tests.ux_phase1_support import fake_services

    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(), hold=True)
    source_id = _add(root, jobs, write_book(tmp_path))["source_id"]
    _drain(jobs, max_jobs=2)  # the import, then the planner: the build is queued

    line = source_status_line(repo, load_vault(root), source_id)

    assert line["text"] == "Writing questions for Ch. 1–2"
    assert line["tone"] == "working"


def test_a_later_build_is_estimated_from_this_librarys_own_builds(tmp_path):
    from learnloop.content.pipeline.add_source import build_minutes_phrase

    _root, ctx, _source_id = _added_book(tmp_path)  # one build, finished (frozen clock: no time at all)

    assert build_minutes_phrase(ctx.repository, chapter_count=1) == "in under a minute"


def test_no_finished_build_means_no_estimate(tmp_path):
    from learnloop.content.pipeline.add_source import build_minutes_phrase
    from tests.ux_phase1_support import repository

    root = fresh_library(tmp_path)

    assert build_minutes_phrase(repository(root), chapter_count=2) is None


# ---------------------------------------------------------------------------
# The one-time OK names the AI the learner set up
# ---------------------------------------------------------------------------


def test_the_one_time_ok_names_codex_for_a_library_set_up_with_codex():
    from learnloop.content.pipeline.add_source import consent_label, what_leaves

    label = consent_label("codex")

    assert label == "Codex (your ChatGPT account)"
    assert "Codex (your ChatGPT account)" in what_leaves(label)
    assert consent_label("chatgpt") == "ChatGPT"


# ---------------------------------------------------------------------------
# A book added through Ingest: its own title, and one line
# ---------------------------------------------------------------------------


def test_a_pdf_imported_through_ingest_gets_the_title_it_carries(tmp_path):
    root = fresh_library(tmp_path)
    ctx = _draining_ctx(root)
    pdf = write_pdf(tmp_path, "intro-to-probability-ch1-2.pdf", title="Introduction to Probability (Chapters 1-2)")

    call(ctx, "start_import_batch", {"sources": [str(pdf)]})

    titles = [card["title"] for card in call(ctx, "get_source_library", {})["sources"]]
    assert titles == ["Introduction to Probability (Chapters 1-2)"]


def test_a_book_with_no_questions_says_so_with_one_action(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    call(ctx, "start_import_batch", {"sources": [str(write_book(tmp_path))]})
    card = call(ctx, "get_source_library", {})["sources"][0]

    line = card["statusLine"]

    assert line == {
        "text": "No questions for this book yet",
        "tone": "quiet",
        "action": {"kind": "retry", "label": "Build them"},
        "details": None,
    }
    # The action plans the book's first build, as Add would have.
    ctx.ingest_jobs._ensure_worker = lambda: None
    batch_id = call(ctx, "source_action", {"sourceId": card["sourceId"], "action": "retry"})["batchId"]
    assert batch_id


def test_a_book_already_in_a_study_map_never_says_it_has_no_questions(tmp_path):
    from learnloop.vault.writer import upsert_source_set

    root = fresh_library(tmp_path)
    ctx = _draining_ctx(root)
    call(ctx, "start_import_batch", {"sources": [str(write_book(tmp_path))]})
    card = call(ctx, "get_source_library", {})["sources"][0]
    from learnloop.vault.loader import add_subject

    add_subject(root, "probability", "Probability")
    upsert_source_set(root, {
        "id": "set_prob", "subject_id": "probability", "title": "Probability",
        "members": [{"source_id": card["sourceId"], "revision_id": card["currentRevisionId"],
                     "default_role": "primary_textbook", "scope": [], "priority": 1}],
    })
    ctx.reload(maintenance=False)

    assert _card(ctx, card["sourceId"])["statusLine"] is None


# ---------------------------------------------------------------------------
# With no AI, a built book's line says what questions need
# ---------------------------------------------------------------------------


def test_the_as_you_read_line_carries_what_to_say_when_no_ai_is_connected(tmp_path):
    _root, ctx, source_id = _added_book(tmp_path)

    line = _card(ctx, source_id)["statusLine"]

    assert line["text"] == "Questions for Ch. 1–2 come up as you read"
    assert line["withoutAi"] == {
        "text": "Questions for Ch. 1–2 come up as you read once an AI is connected",
        "tone": "quiet",
        "action": {"kind": "connect_ai", "label": "Connect"},
        "details": None,
    }


# ---------------------------------------------------------------------------
# The shelf stays fast for a long book: the card's line reads the chapter
# list, never the whole outline (re-walk: with a 630-page book every library
# read took 6-8 s, polled every 3 s, and the sidecar stalled).
# ---------------------------------------------------------------------------


def test_a_built_books_line_reads_its_text_at_most_once(tmp_path, monkeypatch):
    from learnloop.content.pipeline.add_source import source_status_line

    root, ctx, source_id = _added_book(tmp_path)
    repo = ctx.repository
    loads: list[str] = []
    real = repo.load_document_ir

    def counting(extraction_id, *args, **kwargs):
        loads.append(extraction_id)
        return real(extraction_id, *args, **kwargs)

    monkeypatch.setattr(repo, "load_document_ir", counting)

    line = source_status_line(repo, load_vault(root), source_id)

    assert line["text"] == "Questions for Ch. 1–2 come up as you read"
    assert len(loads) <= 1, loads
