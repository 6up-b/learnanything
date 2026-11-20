"""UX-11: a web page read into LearnLoop keeps its display equations, its section titles and none of its furniture.

The sample chapter (`samples/understanding-linear-algebra-symmetric-matrices-and-variance.html`) has 34
display-math elements and its reading kept 3, so its exercises said "for each of the following matrices" with no
matrices. A NEW read of a web page now keeps them (extractor ``html`` version 3). A page read before keeps its
stored reading exactly (``tests/fixtures/ux11_extraction_before.json`` was captured from the code before the
change) and gets the new text only when the learner reads it again from its card.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import html as lxml_html

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.runner import FetchedBytes
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.source_unit_inventory import build_inventory_windows, run_unit_inventory
from learnloop.db.connection import connect
from learnloop.ingest.ir import DocumentIR
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop_sidecar.context import SidecarContext
from tests.source_inventory_helpers import FakeInventoryClient
from tests.ux_phase1_add_source_helpers import call
from tests.ux_phase1_support import CLOCK, Calls, fake_services, fresh_library, grant_consent
from tests.web_page_reading_helpers import BEFORE, old_web_reading_services

REPO = Path(__file__).resolve().parents[1]
CHAPTER = "understanding-linear-algebra-symmetric-matrices-and-variance.html"
ARTICLE = "wikipedia-elevator-paradox.html"


def _squeeze(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _page_displays(name: str) -> list[str]:
    tree = lxml_html.fromstring((REPO / "samples" / name).read_bytes())
    return [el.text_content().strip() for el in tree.xpath('//div[contains(concat(" ", @class, " "), " displaymath ")]')]


def _ctx(root, services):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services)
    return ctx


def _add(ctx, tmp_path, name: str, data: bytes) -> tuple[str, str]:
    page = tmp_path / name
    page.write_bytes(data)
    source_id = call(ctx, "add_source", {"sources": [str(page)]})["items"][0]["sourceId"]
    return source_id, resolve_extraction_id(ctx.repository, source_id)


def _stored(ctx, extraction_id):
    with connect(ctx.repository.sqlite_path) as connection:
        run = connection.execute(
            "SELECT extractor, extractor_version FROM source_extraction_runs WHERE id = ?", (extraction_id,)
        ).fetchone()
        rows = connection.execute(
            "SELECT span_id, content_hash, text FROM source_document_blocks WHERE extraction_id = ? ORDER BY ordinal",
            (extraction_id,),
        ).fetchall()
    return tuple(run), [tuple(row) for row in rows]


def _digest(ir: DocumentIR) -> dict:
    lines = [f"{b.span_id}\t{b.content_hash}\t{b.block_type}\t{b.role_hint}\t{'/'.join(b.section_path)}\t{b.page}"
             for b in ir.blocks]
    units = [f"{u.unit_id}\t{u.label}\t{json.dumps(u.locator, sort_keys=True)}\t{u.semantic_hash}\t{','.join(u.span_ids)}"
             for u in ir.units]
    return {
        "blocks": len(ir.blocks),
        "blocks_digest": hashlib.sha256("\n".join(lines).encode()).hexdigest(),
        "units_digest": hashlib.sha256("\n".join(units).encode()).hexdigest(),
    }


@pytest.fixture
def new_read(tmp_path):
    """The production Add path, as a learner adds a web page today."""

    def read(name: str):
        root = fresh_library(tmp_path / f"new-{name.split('.')[0]}")
        grant_consent(root)
        ctx = _ctx(root, fake_services())
        source_id, extraction_id = _add(ctx, tmp_path, name, (REPO / "samples" / name).read_bytes())
        return ctx, source_id, extraction_id

    return read


# --- new reads --------------------------------------------------------------------------------------------------


def test_ux11_the_chapter_keeps_all_34_display_equations_in_page_order(new_read):
    ctx, _source_id, extraction_id = new_read(CHAPTER)
    run, rows = _stored(ctx, extraction_id)
    text = "\n".join(row[2] for row in rows)
    squeezed = _squeeze(text)

    displays = _page_displays(CHAPTER)
    assert len(displays) == 34
    kept, at = [], 0
    for number, display in enumerate(displays, start=1):
        found = squeezed.find(_squeeze(display), at)
        if found >= 0:
            kept.append(number)
            at = found + 1
    assert kept == list(range(1, 35)), f"{len(kept)} of 34 display equations kept in page order: {kept}"
    assert run == ("html", "3")

    # Three of them, each a display of its own: the preview's P and D (a matrix), the spectral form, and the
    # matrix an exercise asks about.
    def block_of(fragment: str) -> str:
        (block,) = [row[2] for row in rows if _squeeze(fragment) in _squeeze(row[2])]
        return block

    matrices = block_of("D = \\begin{bmatrix}\n\\lambda_1 \\amp 0 \\amp \\ldots \\amp 0")
    assert matrices.startswith("\\begin{equation*}") and matrices.rstrip().endswith("\\end{equation*}")
    assert block_of("A = QDQ^{-1} = QDQ^T.").startswith("\\begin{equation*}")
    exercise = block_of("2 \\amp 0 \\amp 4 \\amp 4 \\amp 5 \\amp 3")
    assert exercise.startswith("\\begin{equation*}") and "\\begin{bmatrix}" in exercise

    # The learner's exercise: the matrices follow its sentence, in its own section.
    intro = text.index("For each of the following matrices, determine whether there is a basis")
    assert "\\(\\begin{bmatrix} 3 \\amp -4 \\\\ 4 \\amp 3 \\end{bmatrix} \\text{.}\\)" in text[intro:intro + 400]

    # What the renderers are given is the stored text.
    view = call(ctx, "reader.render_view", {"extractionId": extraction_id})
    assert [block["markdown"] for block in view["blocks"]] == [row[2] for row in rows]


def test_ux11_section_titles_are_the_headings_own_words_and_the_slug_stays_the_id(new_read):
    ctx, _source_id, extraction_id = new_read(ARTICLE)
    ir = ctx.repository.load_document_ir(extraction_id)
    assert [unit.label for unit in ir.units] == [
        "(intro)", "Modeling the elevator problem", "More than one elevator", "The real-world case", "References",
        "External links",
    ]
    assert [unit.locator["path"] for unit in ir.units] == [
        "root/elevator-paradox", "root/elevator-paradox/modeling-the-elevator-problem",
        "root/elevator-paradox/more-than-one-elevator", "root/elevator-paradox/the-real-world-case",
        "root/elevator-paradox/references", "root/elevator-paradox/external-links",
    ]
    assert any(block.section_path == ["elevator-paradox", "modeling-the-elevator-problem"] for block in ir.blocks)

    ctx2, _sid, chapter_extraction = new_read(CHAPTER)
    chapter = ctx2.repository.load_document_ir(chapter_extraction)
    assert [unit.label for unit in chapter.units] == ["Section 7.1 Symmetric matrices and variance"]


def test_ux11_the_articles_sections_carry_no_edit_link_or_maintenance_notice_and_keep_their_text(new_read):
    ctx, _source_id, extraction_id = new_read(ARTICLE)
    _run, rows = _stored(ctx, extraction_id)
    texts = [row[2] for row in rows]
    assert not any("[edit]" in text for text in texts)
    assert not any("This article has multiple issues" in text for text in texts)
    first = {unit.label: unit.span_ids[0] for unit in ctx.repository.load_document_ir(extraction_id).units}
    by_span = {row[0]: row[2] for row in rows}
    assert by_span[first["Modeling the elevator problem"]].startswith("Several attempts (beginning with Gamow")
    assert by_span[first["More than one elevator"]].startswith("If there is more than one elevator")

    # The rule removes the furniture and nothing else: every block the old reading had is still there, less its
    # "[edit]" prefix, except the maintenance notice (and the bar of its table).
    new_text = _squeeze("\n".join(texts))
    old_blocks = [block["text"] for block in BEFORE["html"][ARTICLE]["ir"]["blocks"]]
    furniture = [text for text in old_blocks if text.startswith("This article has multiple issues") or text == "|"]
    assert len(furniture) >= 1
    for text in old_blocks:
        if text in furniture:
            continue
        assert _squeeze(text.removeprefix("[edit]")) in new_text, text[:80]


def test_ux11_hidden_and_collapsed_parts_are_treated_as_the_old_extraction_treated_them():
    from learnloop.content.pipeline.jobs import default_extract

    ctx = SimpleNamespace(payload={}, job={})
    for shape, probe in BEFORE["probe"].items():
        fetched = FetchedBytes(raw_bytes=probe["page"].encode(), content_type="text/html",
                               original_uri="https://example.org/page.html", retrieved_at="2026-11-20T00:00:00Z")
        ir = default_extract(fetched, "web", ctx)
        assert (ir.extractor, ir.extractor_version) == ("html", "3")
        text = "\n".join(block.text for block in ir.blocks)
        assert {mark: mark in text for mark in probe["reaches_text"]} == probe["reaches_text"], shape

    page = (REPO / "samples" / CHAPTER).read_bytes()
    fetched = FetchedBytes(raw_bytes=page, content_type="text/html", original_uri="file:///chapter.html",
                           retrieved_at="2026-11-20T00:00:00Z")
    text = "\n".join(block.text for block in default_extract(fetched, "web", ctx).blocks)
    # The chapter's own hidden parts: its macro definitions, its figures' long descriptions, its search box.
    assert "\\newcommand" not in text
    assert "standard coordinate grid" not in text
    assert "Search Results" not in text


def test_ux11_other_source_kinds_extract_byte_for_byte_as_before(tmp_path):
    root = fresh_library(tmp_path / "kinds")
    ctx = _ctx(root, fake_services())
    inputs = {
        "quiz.pdf": (REPO / "samples" / "mit-18.06-spring-2010-quiz1.pdf").read_bytes(),
        "solutions.pdf": (REPO / "samples" / "mit-18.06-spring-2010-quiz1-solutions.pdf").read_bytes(),
        "notes.md": BEFORE["inputs"]["notes.md"].encode(),
        "notes.txt": BEFORE["inputs"]["notes.txt"].encode(),
    }
    for name, data in inputs.items():
        _source_id, extraction_id = _add(ctx, tmp_path, name, data)
        run = ctx.repository.get_extraction_run(extraction_id)
        expected = BEFORE["other_kinds"][name]
        assert {"extractor": run["extractor"], "extractor_version": run["extractor_version"],
                "model_versions": run.get("model_versions") or {}, "config": run.get("config") or {}} == expected["run"]
        assert _digest(ctx.repository.load_document_ir(extraction_id)) == {
            key: expected[key] for key in ("blocks", "blocks_digest", "units_digest")
        }, name


# --- pages read before ------------------------------------------------------------------------------------------


@pytest.fixture
def read_before(tmp_path):
    """A library holding web pages read by the code before UX-11: the Add path, with the extraction that code
    produced for these bytes (``tests/fixtures/ux11_extraction_before.json``) under its identity. Then the
    current code opens the same library."""

    def read(name: str, *, calls: Calls | None = None):
        root = fresh_library(tmp_path / f"before-{name.split('.')[0]}")
        grant_consent(root)
        before = _ctx(root, old_web_reading_services(name))
        source_id, extraction_id = _add(before, tmp_path, name, (REPO / "samples" / name).read_bytes())
        before.ingest_jobs.drain_foreground()
        ctx = _ctx(root, fake_services(calls=calls))
        return ctx, source_id, extraction_id

    return read


def test_ux11_a_page_read_before_keeps_its_stored_reading_under_the_new_code(read_before, tmp_path):
    ctx, source_id, extraction_id = read_before(CHAPTER)
    fixture = BEFORE["html"][CHAPTER]
    old_ir = DocumentIR.model_validate(fixture["ir"])
    revision_id = ctx.repository.get_extraction_run(extraction_id)["revision_id"]

    # What the new code does with a library: list it, open the page, add the same page again, read its card.
    library = call(ctx, "get_source_library", {})
    assert source_id in json.dumps(library)
    view = call(ctx, "reader.render_view", {"extractionId": extraction_id})
    again = call(ctx, "add_source", {"sources": [str(tmp_path / CHAPTER)]})["items"][0]
    assert again["status"] == "existing" and again["sourceId"] == source_id
    ctx.ingest_jobs.drain_foreground()
    core.source_status_line(ctx.repository, ctx.vault, source_id)

    run, rows = _stored(ctx, extraction_id)
    assert run == ("html", "2")
    assert rows == [(block.span_id, block.content_hash, block.text) for block in old_ir.blocks]
    stored = ctx.repository.load_document_ir(extraction_id)
    assert _digest(stored) == {key: fixture[key] for key in ("blocks", "blocks_digest", "units_digest")}
    # No other reading of the page was made, and the Reader opens the one it had.
    with connect(ctx.repository.sqlite_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM source_extraction_runs WHERE revision_id = ?",
                                   (revision_id,)).fetchone()[0]
    assert count == 1
    assert resolve_extraction_id(ctx.repository, source_id) == extraction_id
    assert [block["markdown"] for block in view["blocks"]] == [block.text for block in old_ir.blocks]
    # What a model is sent for this reading is what it was sent before.
    for unit in stored.units:
        windows = build_inventory_windows(stored, unit.unit_id, input_budget_tokens=20000)
        assert hashlib.sha256(json.dumps(windows, sort_keys=True).encode()).hexdigest() == \
            fixture["inventory_windows"][unit.unit_id]


def test_ux11_the_card_offers_a_page_read_before_its_missing_equations_and_only_that_page(read_before, new_read):
    ctx, source_id, _extraction_id = read_before(CHAPTER)
    line = core.source_status_line(ctx.repository, ctx.vault, source_id)
    assert line["text"] == "This page's text is missing 31 equations"
    assert line["action"] == {"kind": "read_again", "label": "Read it again"}
    assert line["tone"] == "quiet"

    # A page read before with no equation to gain (the article) and a page read now: no offer.
    article_ctx, article_id, _ = read_before(ARTICLE)
    article_line = core.source_status_line(article_ctx.repository, article_ctx.vault, article_id)
    assert article_line is None or (article_line.get("action") or {}).get("kind") != "read_again"
    new_ctx, new_id, _ = new_read(CHAPTER)
    new_line = core.source_status_line(new_ctx.repository, new_ctx.vault, new_id)
    assert new_line is None or (new_line.get("action") or {}).get("kind") != "read_again"


def test_ux11_reading_it_again_gives_the_new_text_and_carries_progress_the_study_map_and_a_highlight(read_before):
    from learnloop.reader import annotations as ANN

    calls = Calls()
    ctx, source_id, old = read_before(CHAPTER, calls=calls)
    repo = ctx.repository
    revision_id = repo.get_extraction_run(old)["revision_id"]
    old_ir = repo.load_document_ir(old)
    (unit,) = old_ir.units
    repo.upsert_reader_section_progress(extraction_id=old, section_id=unit.unit_id, spans_seen=20,
                                        span_count=len(unit.span_ids))
    repo.upsert_unit_selection(extraction_id=old, source_id=source_id, revision_id=revision_id,
                               selected_unit_ids=[unit.unit_id])
    # A highlight on the sentence right before the spectral form, which the old reading kept as a formula.
    quote = "Putting these orthonormal vectors into a matrix"
    (span,) = [block.span_id for block in old_ir.blocks if quote in block.text]
    translation = ANN.translate_selection(repo, extraction_id=old,
                                          raw_selection={"nodes": [{"span_id": span, "quote": quote}]})
    annotation_id = ANN.append_annotation(repo, source_id=source_id, revision_id=revision_id, extraction_id=old,
                                          annotation_type="highlight", translation=translation)["annotation_id"]
    paid_before = (calls.inventory_calls, calls.synthesis_calls)

    asked = call(ctx, "source_action", {"sourceId": source_id, "action": "read_again"})
    assert asked["needsConfirmation"] is True and "batchId" not in asked
    lines = asked["confirmation"]["lines"]
    assert lines[0] == "Read on this computer from the copy saved when you added it: free."
    assert lines[1] == "The new text keeps the 31 equations the old one left out, and each section's own title."
    # The questions the first build wrote cite passages of the old reading: they move too.
    assert lines[2] == ("Your progress (1 section), 1 note, the passages your questions and notes cite and your "
                        "study-map chapters move to the new reading. Anything that can't be matched is marked so you "
                        "can place it again.")
    assert lines[3].startswith("Reading it sends nothing to an AI. Questions already written stay.")
    assert asked["confirmation"]["confirmLabel"] == "Read it again"

    out = call(ctx, "source_action", {"sourceId": source_id, "action": "read_again", "confirmed": True})
    assert out["batchId"]
    ctx.ingest_jobs.drain_foreground()
    new = resolve_extraction_id(repo, source_id)
    assert new != old
    # Reading it again sent nothing to a model and wrote no questions.
    assert (calls.inventory_calls, calls.synthesis_calls) == paid_before
    run, rows = _stored(ctx, new)
    assert run == ("html", "3")
    squeezed = _squeeze("\n".join(row[2] for row in rows))
    assert all(_squeeze(display) in squeezed for display in _page_displays(CHAPTER))
    # The old reading is still there, untouched.
    assert _stored(ctx, old)[1] == [(b.span_id, b.content_hash, b.text) for b in old_ir.blocks]

    (new_unit,) = repo.load_document_ir(new).units
    progress = repo.reader_section_progress_for(new)
    assert [row["section_id"] for row in progress] == [new_unit.unit_id]
    assert 0 < progress[0]["spans_seen"] <= progress[0]["span_count"]
    assert repo.get_unit_selection(new)["selected_unit_ids"] == [new_unit.unit_id]
    head = {head["annotation"]["id"]: head for head in repo.annotations_for_source(source_id)}[annotation_id]
    assert head["anchor"]["extraction_id"] == new and head["anchor"]["status"] == "reanchored"
    segment = head["segments"][0]
    text = dict((row[0], row[2]) for row in rows)[segment["span_id"]]
    assert text[segment["codepoint_start"]:segment["codepoint_end"]] == quote

    # The card no longer offers it.
    line = core.source_status_line(repo, ctx.vault, source_id)
    assert line is None or (line.get("action") or {}).get("kind") != "read_again"

    # What it costs later: the section's text changed, so the next inventory of it is paid again (the old one
    # is not reused), once.
    client = FakeInventoryClient()
    run_unit_inventory(repo, new, new_unit.unit_id, role="textbook", client=client)
    assert len(client.calls) >= 1
    again = FakeInventoryClient()
    run_unit_inventory(repo, new, new_unit.unit_id, role="textbook", client=again)
    assert again.calls == []


def test_ux11_reading_the_article_again_maps_its_sections_and_its_held_out_mark_waits_for_the_owner(read_before):
    from learnloop.content.pipeline import exam_marking
    from learnloop.content.sources.exam_material import MARKS_MADE_ON_KEY, exam_material, marks_made_on

    ctx, source_id, old = read_before(ARTICLE)
    repo = ctx.repository
    revision_id = repo.get_extraction_run(old)["revision_id"]
    labels = {unit.label: unit.unit_id for unit in repo.load_document_ir(old).units}
    modeling, real_world = labels["modeling-the-elevator-problem"], labels["the-real-world-case"]
    repo.upsert_reader_section_progress(extraction_id=old, section_id=modeling, spans_seen=4, span_count=4,
                                        revealed=True, completed=True)
    repo.upsert_unit_selection(extraction_id=old, source_id=source_id, revision_id=revision_id,
                               selected_unit_ids=sorted(labels.values()),
                               exam_use_modes={real_world: "held_out_evaluation"},
                               exam_paper_metadata={MARKS_MADE_ON_KEY: marks_made_on(old, revision_id)})

    # The card's action runs on any page read before, equations or not (the article has none to gain, so its
    # card does not offer it; the action itself is the existing re-read).
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "read_again", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    new = resolve_extraction_id(repo, source_id)
    assert out["batchId"] and new != old
    new_units = {unit.label: unit.unit_id for unit in repo.load_document_ir(new).units}
    progress = {row["section_id"]: row for row in repo.reader_section_progress_for(new)}
    assert progress[new_units["Modeling the elevator problem"]]["completed_at"]
    assert sorted(repo.get_unit_selection(new)["selected_unit_ids"]) == sorted(new_units.values())

    # Protection marks never move to another reading: the new one is held back whole until the owner marks it,
    # and the marking proposes the same section by its new title.
    exam = exam_material(ctx.vault, repo)
    assert new in exam.held_out.extractions
    plan = exam_marking.mark_plan(ctx.vault, repo, source_id)
    assert plan["lines"][0] == "Held out as exam material: The real-world case."
