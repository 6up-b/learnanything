"""Selecting and highlighting on the original PDF (reader-pdf-selection).

The Reader's PDF selection model (``apps/learnloop-tauri/src/components/
pdfSelection``) sends each block's part of a selection as an exact slice of
the block's text with code-point offsets. These tests hold the Python side of
that contract:

* every selection the model's tests make (on synthetic pages parsed by the
  real pdf.js, and on the GLM-OCR geometry of the CC BY arXiv answer) anchors
  exactly through ``annotations.translate_selection``, with the same offsets;
* a saved annotation is placed on the reading the Reader has open through the
  one alias authority (``span_aliases``): here, moved after a re-read,
  flagged, or not on this reading, never another block;
* ``reader.pdf_view`` and ``reader.render_view`` say what of the reading the
  held-out partition covers (``exam_material``), so a selection on it offers
  no model action.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import annotations as ANN

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_FIXTURES = ROOT / "apps" / "learnloop-tauri" / "src" / "components" / "pdfSelection" / "fixtures"
ARXIV_BLOCKS = FRONTEND_FIXTURES / "arxiv_2302_11517_glm_blocks.json"
CONTRACT = FRONTEND_FIXTURES / "selection_contract.json"

ARXIV_CREDIT = (
    "Wei Tang, Kangning Cui, Raymond H. Chan, \"Optimized Hard Exudate Detection with Supervised Contrastive "
    "Learning\", arXiv:2302.11517v2 (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/). Block geometry "
    "and text from z.ai's recorded GLM-OCR answer for its pages 1-5 (tests/fixtures/glm_ocr/"
    "arxiv_2302_11517_trimmed.json), read by learnloop.ingest.extractors.glm_ocr.responses_to_ir."
)


def arxiv_ir() -> DocumentIR:
    from learnloop.ingest.extractors import glm_ocr as glm
    from tests.test_glm_ocr import ARXIV_OUTLINE

    answer = json.loads((ROOT / "tests" / "fixtures" / "glm_ocr" / "arxiv_2302_11517_trimmed.json").read_text("utf-8"))
    return glm.responses_to_ir([(answer, [0, 1, 2, 3, 4])], sizes=[(612.0, 792.0)] * 5, outline=ARXIV_OUTLINE,
                               version="t")


def arxiv_pdf_blocks() -> dict:
    """The arXiv answer's blocks as ``reader.pdf_view`` sends them."""

    ir = arxiv_ir()
    blocks = [
        {"spanId": block.span_id, "page": block.page, "bbox": list(block.bbox), "blockType": block.block_type,
         "text": block.text}
        for block in sorted(ir.blocks, key=lambda b: b.ordinal) if block.page is not None and block.bbox
    ]
    return {"credit": ARXIV_CREDIT, "pages": [[612.0, 792.0]] * 5, "blocks": blocks}


def write_arxiv_fixture() -> None:  # pragma: no cover - run by hand when the GLM mapping changes
    ARXIV_BLOCKS.write_text(json.dumps(arxiv_pdf_blocks(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def test_the_frontend_arxiv_fixture_is_the_recorded_answers_geometry():
    """The vitest fixture is what the GLM-OCR mapping reads from the recorded
    answer today (a scan as far as the Reader knows: no text layer)."""

    assert json.loads(ARXIV_BLOCKS.read_text("utf-8")) == arxiv_pdf_blocks()


# --- the selection contract: every node the PDF model sends anchors exactly ----------------


def _contract() -> dict:
    return json.loads(CONTRACT.read_text("utf-8"))


def _synthetic_ir(blocks: list[dict]) -> DocumentIR:
    built = [
        DocumentBlock.build(span_id=block["spanId"], block_type=block["blockType"], text=block["text"], ordinal=index,
                            page=block["page"], bbox=[float(v) for v in block["bbox"]], section_path=["Synthetic"])
        for index, block in enumerate(blocks, start=1)
    ]
    return DocumentIR(extractor="marker", extractor_version="1", blocks=built,
                      units=[DocumentUnit(unit_id="u1", label="Synthetic", ordinal=0, semantic_hash="sha256:u",
                                          span_ids=[b.span_id for b in built])],
                      assets=[], health=ExtractionHealth())


@pytest.fixture
def two_books(tmp_path):
    """A vault with the synthetic book (``ext_syn``) and the arXiv paper's GLM
    reading (``ext_arxiv``), each its own source."""

    from tests.helpers import create_basic_vault
    from tests.test_source_inventory import _persist, _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src_syn", revision_id="rev_syn")
    _persist(repo, _synthetic_ir(_contract()["blocks"]["synthetic"]), revision_id="rev_syn", extraction_id="ext_syn")
    with repo.connection() as connection:
        now = "2026-10-15T09:00:00+00:00"
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES (?,?,?,?,?)", ("src_arxiv", "pdf", "file:///arxiv.pdf", now, now))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
                           ("rev_arxiv", "src_arxiv", "sha256:arxiv", now))
        connection.commit()
    _persist(repo, arxiv_ir(), revision_id="rev_arxiv", extraction_id="ext_arxiv")
    return {"root": paths.root, "repo": repo}


EXTRACTIONS = {"synthetic": "ext_syn", "arxiv": "ext_arxiv"}


@pytest.mark.parametrize("name", [selection["name"] for selection in json.loads(CONTRACT.read_text("utf-8"))["selections"]])
def test_every_pdf_selection_anchors_exactly_with_its_own_offsets(two_books, name):
    selection = next(s for s in _contract()["selections"] if s["name"] == name)
    extraction_id = EXTRACTIONS[selection["extraction"]]
    translation = ANN.translate_selection(two_books["repo"], extraction_id=extraction_id,
                                          raw_selection={"nodes": selection["nodes"]})
    assert translation["status"] == "exact", name
    assert [(s["span_id"], s["codepoint_start"], s["codepoint_end"], s["exact_quote"])
            for s in translation["segments"]] == [
        (n["spanId"], n["start"], n["end"], n["quote"]) for n in selection["nodes"]
    ]


def test_a_node_whose_offsets_drifted_from_its_quote_is_relocated_by_its_quote(two_books):
    """The sidecar stays the authority: offsets that no longer name the quote
    (an extraction text that changed under an open page) are not trusted."""

    translation = ANN.translate_selection(two_books["repo"], extraction_id="ext_syn", raw_selection={
        "nodes": [{"spanId": "s2", "start": 0, "end": 5, "quote": "lazy dog"}]})
    assert translation["status"] == "exact"
    segment = translation["segments"][0]
    assert segment["exact_quote"] == "lazy dog" and segment["codepoint_start"] == 35


def test_a_pdf_highlight_round_trips_through_capture_to_the_place_it_is_drawn(two_books):
    """reader.capture with the model's nodes, then reader.source_annotations
    with the open reading: the placement carries the same span and code
    points the model draws the region boxes from."""

    from tests.test_sidecar_reader_p3 import _rpc

    nodes = next(s for s in _contract()["selections"] if s["name"] == "letters outside the BMP on a scan")["nodes"]
    out = _rpc(two_books["root"], [
        ("reader.capture", {"sourceId": "src_syn", "revisionId": "rev_syn", "extractionId": "ext_syn",
                            "action": "highlight", "clientIdempotencyKey": "k-bmp", "rawSelection": {"nodes": nodes},
                            "learnerText": ""}),
        ("reader.source_annotations", {"sourceId": "src_syn", "extractionId": "ext_syn"}),
        ("reader.source_annotations", {"sourceId": "src_syn"}),
    ])
    assert out[1]["result"]["anchorStatus"] == "exact"
    (row,) = out[2]["result"]["annotations"]
    assert row["placement"] == {
        "state": "here",
        "segments": [{"spanId": n["spanId"], "codepointStart": n["start"], "codepointEnd": n["end"],
                      "exactQuote": n["quote"]} for n in nodes],
        "flagSpanId": None,
    }
    # Without the open reading the wire is as it was.
    assert "placement" not in out[3]["result"]["annotations"][0]


# --- placements through a re-read (the one alias authority) -------------------------------

from tests.test_reread_safety import EXACT, MOVED, _reread, studied  # noqa: E402,F401 - the fixture


def _placements(repo, extraction_id):
    heads = repo.annotations_for_source("src1")
    return {head["annotation"]["id"]: placement
            for head, placement in zip(heads, ANN.annotation_placements(repo, heads, extraction_id))}


def _slice(repo, extraction_id, segment):
    text = repo.load_document_ir(extraction_id).block_by_span(segment["span_id"]).text
    return text[segment["codepoint_start"]:segment["codepoint_end"]]


def test_highlights_are_here_on_the_reading_they_were_made_on(studied):
    repo = studied["repo"]
    placed = _placements(repo, "extA")
    for span_id, quote in ((EXACT, "vector space"), (MOVED, "zero vector")):
        placement = placed[studied["annotations"][span_id]]
        assert placement["state"] == "here"
        (segment,) = placement["segments"]
        assert segment["span_id"] == span_id and _slice(repo, "extA", segment) == quote


def test_a_highlight_carried_by_a_reread_is_drawn_on_its_words_and_labelled_moved(studied):
    repo = studied["repo"]
    _reread(studied)
    placed = _placements(repo, "extB")
    exact = placed[studied["annotations"][EXACT]]
    assert exact["state"] == "moved"
    (segment,) = exact["segments"]
    assert segment["span_id"] == "b1" and _slice(repo, "extB", segment) == "vector space"
    moved_head = next(h for h in repo.annotations_for_source("src1")
                      if h["annotation"]["id"] == studied["annotations"][MOVED])
    moved = placed[studied["annotations"][MOVED]]
    if moved_head["anchor"]["status"] == "reanchored":
        assert moved["state"] == "moved" and _slice(repo, "extB", moved["segments"][0]) == "zero vector"
    else:
        # Not confident: flagged at the passage that took its place, never drawn as text.
        assert moved == {"state": "flagged", "segments": [], "flag_span_id": "b2"}
    # The old reading, opened again, has none of them as its own any more.
    old = _placements(repo, "extA")
    assert {p["state"] for p in old.values()} <= {"moved", "flagged", "elsewhere"}
    for placement in old.values():
        for segment in placement["segments"]:
            assert repo.load_document_ir("extA").block_by_span(segment["span_id"]) is not None


def test_a_highlight_from_before_aliases_resolves_through_them_or_is_flagged(studied):
    """A re-read made by an older build (nothing carried, no aliases
    recorded): the same-text highlight is drawn on the new reading's block,
    the changed one is flagged at its new place, never drawn on another block."""

    repo = studied["repo"]
    _reread(studied, carry=False)
    placed = _placements(repo, "extB")
    exact = placed[studied["annotations"][EXACT]]
    assert exact["state"] == "moved"
    assert exact["segments"][0]["span_id"] == "b1" and _slice(repo, "extB", exact["segments"][0]) == "vector space"
    assert placed[studied["annotations"][MOVED]] == {"state": "flagged", "segments": [], "flag_span_id": "b2"}
    assert repo.span_reanchors_between("extA", "extB") == []  # read-only


def test_a_capture_that_never_anchored_is_not_drawn(studied):
    repo = studied["repo"]
    translation = ANN.translate_selection(repo, extraction_id="extA",
                                          raw_selection={"nodes": [{"span_id": "a3", "quote": "words not in it"}]})
    assert translation["status"] == "needs_reanchor"
    annotation_id = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="extA",
                                          annotation_type="highlight", translation=translation)["annotation_id"]
    assert _placements(repo, "extA")[annotation_id] == {"state": "elsewhere", "segments": [], "flag_span_id": None}


def test_a_segment_naming_a_block_whose_text_changed_is_flagged_not_drawn(studied):
    """A re-anchor that found no block keeps the old reading's span id; the
    same id on the new reading is another passage. The block-hash check keeps
    it off the page."""

    repo = studied["repo"]
    head = repo.annotation_head(studied["annotations"][EXACT])
    segment = dict(head["segments"][0])
    forged = {**head, "anchor": {**head["anchor"], "extraction_id": "extB", "status": "reanchored"},
              "segments": [{**segment, "span_id": "b2"}]}
    _reread(studied, carry=False)
    (placement,) = ANN.annotation_placements(repo, [forged], "extB")
    assert placement["state"] == "elsewhere"


# --- protection: a selection on held-out material offers no model action -----------------


def test_the_reader_is_told_which_passages_are_held_out(studied):
    from learnloop.content.sources.exam_material import HELD_OUT_REFUSAL
    from learnloop_sidecar.context import SidecarContext
    from tests.test_reread_safety import call

    ctx = SidecarContext()
    ctx.load(studied["root"])
    view = call(ctx, "reader.render_view", {"extractionId": "extA"})
    assert view["protection"] == {"withheld": False, "heldOutSpanIds": ["a6", "a7"], "message": HELD_OUT_REFUSAL}
    pdf = call(ctx, "reader.pdf_view", {"extractionId": "extA"})
    assert pdf["protection"] == view["protection"]


def test_a_reading_held_back_by_rule_4_is_withheld_whole(studied):
    from learnloop.content.sources.exam_material import HELD_BACK_REFUSAL
    from learnloop_sidecar.context import SidecarContext
    from tests.test_reread_safety import call

    _reread(studied)
    ctx = SidecarContext()
    ctx.load(studied["root"])
    view = call(ctx, "reader.render_view", {"extractionId": "extB"})
    assert view["protection"] == {"withheld": True, "heldOutSpanIds": [], "message": HELD_BACK_REFUSAL}


def test_a_book_with_no_exam_material_has_no_protection(two_books):
    from tests.test_sidecar_reader_p3 import _rpc

    out = _rpc(two_books["root"], [("reader.render_view", {"extractionId": "ext_syn"}),
                                   ("reader.pdf_view", {"extractionId": "ext_syn"})])
    assert out[1]["result"]["protection"] == {"withheld": False, "heldOutSpanIds": [], "message": None}
    assert out[2]["result"]["protection"] == {"withheld": False, "heldOutSpanIds": [], "message": None}


# --- remove and undo: a delete is a tombstone, and so is its undo -------------------------


def test_a_removed_highlight_comes_back_on_undo_with_its_anchor_and_history(two_books):
    """reader.delete_intent_annotation hides it; reader.restore_annotation
    lists it again, placed exactly where it was. Nothing is hard-deleted."""

    from tests.test_sidecar_reader_p3 import _rpc

    nodes = next(s for s in _contract()["selections"] if s["name"] == "a hyphenated word")["nodes"]
    capture = ("reader.capture", {"sourceId": "src_syn", "revisionId": "rev_syn", "extractionId": "ext_syn",
                                  "action": "highlight", "clientIdempotencyKey": "k-undo",
                                  "rawSelection": {"nodes": nodes}, "learnerText": "remember this"})
    listing = ("reader.source_annotations", {"sourceId": "src_syn", "extractionId": "ext_syn"})
    out = _rpc(two_books["root"], [capture, listing])
    annotation_id = out[1]["result"]["annotationId"]
    (before,) = out[2]["result"]["annotations"]

    out = _rpc(two_books["root"], [
        ("reader.delete_intent_annotation", {"annotationId": annotation_id}),
        listing,
        ("reader.restore_annotation", {"annotationId": annotation_id}),
        listing,
        ("reader.restore_annotation", {"annotationId": annotation_id}),
        ("reader.annotation_history", {"annotationId": annotation_id}),
    ])
    assert out[2]["result"]["annotations"] == []
    assert out[3]["result"]["restored"] is True
    (after,) = out[4]["result"]["annotations"]
    assert after == before
    assert after["placement"]["segments"][0]["exactQuote"] == "long computation of"
    # Undoing what is not deleted changes nothing.
    assert out[5]["result"] == {"version": out[5]["result"]["version"], "annotationId": annotation_id,
                                "restored": False, "eventId": None}
    events = [event["eventType"] for event in out[6]["result"]["history"]["events"]]
    assert events == ["create", "delete_intent", "disposition"]


def test_a_second_delete_after_an_undo_hides_it_again(two_books):
    repo = two_books["repo"]
    translation = ANN.translate_selection(repo, extraction_id="ext_syn", raw_selection={
        "nodes": [{"spanId": "s2", "quote": "lazy dog"}]})
    annotation_id = ANN.append_annotation(repo, source_id="src_syn", revision_id="rev_syn", extraction_id="ext_syn",
                                          annotation_type="highlight", translation=translation)["annotation_id"]
    listed = lambda: [head["annotation"]["id"] for head in repo.annotations_for_source("src_syn")]  # noqa: E731
    assert listed() == [annotation_id]
    ANN.delete_intent_annotation(repo, annotation_id=annotation_id)
    assert listed() == []
    assert ANN.restore_annotation(repo, annotation_id=annotation_id)["restored"] is True
    assert listed() == [annotation_id]
    ANN.delete_intent_annotation(repo, annotation_id=annotation_id)
    assert listed() == []
    with pytest.raises(ANN.AnnotationError):
        ANN.restore_annotation(repo, annotation_id="ann_missing")
