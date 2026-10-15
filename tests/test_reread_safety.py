"""Re-read safety (docs/reviews/reread-safety.md).

The GLM-OCR live check on backup copies of the owner's books found that the
card's "Read it again with text recognition" broke a studied book, whatever
the engine: E1, the re-read registered whatever sat at the book's path (a
git-LFS pointer) as a new current revision and the book stopped opening; E2,
with the right bytes, the new reading dropped or misplaced everything the
learner had on the old one. Each test here is the report's proposed test for
one of its "Code changes needed" items 1-5, written to fail before the fix.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pypdf import PdfWriter

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.runner import JobSpec
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import asset_hash, extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.ingest.originals import stored_original_path
from learnloop.vault.models import SourceRef
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import fake_services, fresh_library


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@dataclass
class TickingClock:
    instant: datetime

    def now(self) -> datetime:
        return self.instant

    def advance(self, minutes: int = 1) -> None:
        self.instant = self.instant + timedelta(minutes=minutes)


def _clock() -> TickingClock:
    return TickingClock(datetime(2026, 10, 14, 9, 0, 0, tzinfo=UTC))


# --- two readings of one book ----------------------------------------------------------
#
# The old reading is Marker-shaped (a heading and paragraphs per section); the
# re-read segments differently: other span ids and unit ids, one paragraph
# re-worded at the same place, one passage gone (two new blocks where it was).

_A_TEXT = {
    "a0": ("SectionHeader", 13, ["1 Vectors"], "1 Vectors"),
    "a1": ("Text", 13, ["1 Vectors"], "A vector space is a set with addition and scalar multiplication."),
    "a2": ("Text", 13, ["1 Vectors"], "Every vector space has a zero vector."),
    "a3": ("Text", 14, ["1 Vectors"], "A list of vectors is linearly independent when only the trivial combination is zero."),
    "a4": ("SectionHeader", 15, ["2 Spans"], "2 Spans"),
    "a5": ("Text", 15, ["2 Spans"], "The span of a list is the set of all linear combinations of it."),
    "a6": ("SectionHeader", 16, ["3 Exam review"], "3 Exam review"),
    "a7": ("Text", 16, ["3 Exam review"], "Exam problem: prove that the zero vector is unique."),
}
_B_TEXT = {
    "b0": ("SectionHeader", 13, ["1 Vectors"], "1 Vectors"),
    "b1": ("Text", 13, ["1 Vectors"], "A vector space is a set with addition and scalar multiplication."),
    "b2": ("Text", 13, ["1 Vectors"], "Every vector space has a zero vector 0."),
    "b3": ("Text", 14, ["1 Vectors"], "A list of vectors is linearly independent when only the trivial combination is zero."),
    "b4": ("SectionHeader", 15, ["2 Spans"], "2 Spans"),
    "b5": ("Text", 15, ["2 Spans"], "Spans, in new words, part one."),
    "b6": ("Text", 15, ["2 Spans"], "Spans, in new words, part two."),
    "b7": ("SectionHeader", 16, ["3 Exam review"], "3 Exam review"),
    "b8": ("Text", 16, ["3 Exam review"], "Exam problem: prove that the zero vector is unique."),
}
EXACT, MOVED, GONE = "a1", "a2", "a5"


def _ir(texts, units, *, extractor: str) -> DocumentIR:
    blocks = [
        DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page, section_path=path)
        for index, (span, (kind, page, path, text)) in enumerate(texts.items())
    ]
    return DocumentIR(
        extractor=extractor, extractor_version="1", blocks=blocks,
        units=[DocumentUnit(unit_id=unit_id, label=label, ordinal=index, semantic_hash=semantic,
                            page_start=13, page_end=16, span_ids=spans)
               for index, (unit_id, label, semantic, spans) in enumerate(units)],
        assets=[], health=ExtractionHealth(),
    )


def reading_a() -> DocumentIR:
    return _ir(_A_TEXT, [
        ("u1", "1 Vectors", "sha256:a-u1", ["a0", "a1", "a2", "a3"]),
        ("u2", "2 Spans", "sha256:a-u2", ["a4", "a5"]),
        ("u3", "3 Exam review", "sha256:u3", ["a6", "a7"]),
    ], extractor="marker")


def reading_b() -> DocumentIR:
    return _ir(_B_TEXT, [
        ("h1", "1 Vectors", "sha256:b-h1", ["b0", "b1", "b2", "b3"]),
        ("h2", "2 Spans", "sha256:b-h2", ["b4", "b5", "b6"]),
        ("h3", "3 Exam review", "sha256:u3", ["b7", "b8"]),
    ], extractor="glm_ocr")


def _persist(repo: Repository, ir: DocumentIR, *, revision_id: str, extraction_id: str, clock,
             page_selection=None) -> str:
    request_hash = extraction_request_hash(
        revision_id=revision_id, extractor=ir.extractor, extractor_version=ir.extractor_version,
        page_selection=page_selection, ir_schema_version=IR_SCHEMA_VERSION,
    )
    repo.insert_extraction_run(
        id=extraction_id, revision_id=revision_id, extractor=ir.extractor, extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, page_selection=page_selection,
        status="running", clock=clock,
    )
    repo.persist_document_ir(extraction_id, ir)
    repo.complete_extraction_run(extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir),
                                 clock=clock)
    return extraction_id


def _made_on(extraction_id: str, revision_id: str) -> dict:
    """The selection metadata a writer records with the marks it makes on a
    reading (exam protection by extraction identity): these tests' marks are
    the owner's, exact. A mark without it is a legacy one (ambiguous)."""

    from learnloop.content.sources.exam_material import MARKS_MADE_ON_KEY, marks_made_on

    return {MARKS_MADE_ON_KEY: marks_made_on(extraction_id, revision_id)}


def _confirm_marking(vault, repository, source_id: str, *, clock=None):
    """The card's marking as the owner confirms it: the confirmation shown,
    then the marking bound to the reading and proposal it showed (F13)."""

    from learnloop.content.pipeline import exam_marking

    plan = exam_marking.mark_plan(vault, repository, source_id)
    assert plan is not None, "nothing held back to mark"
    return exam_marking.mark_exam_material(vault, repository, source_id, extraction_id=plan["extraction_id"],
                                           proposal_hash=plan["proposal_hash"], clock=clock)


def _text(repo: Repository, extraction_id: str, span_id: str) -> str:
    return repo.load_document_ir(extraction_id).block_by_span(span_id).text


# --- a seeded library: one book, its reading, the learner's study state ---------------


@pytest.fixture
def studied(tmp_path):
    """A basic vault holding one book read once (``extA``), with progress, a
    selection with a held-out unit, YAML refs, a facet link, source-object
    citations and annotations on it; then a second reading (``extB``)."""

    from learnloop.reader import annotations as ANN
    from learnloop.reader import source_objects as SO
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault
    from tests.test_source_inventory import _register_revision

    clock = _clock()
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    repo.set_source_current_revision("src1", "rev1")
    _persist(repo, reading_a(), revision_id="rev1", extraction_id="extA", clock=clock, page_selection=list(range(13, 39)))
    clock.advance()
    # Progress: section u1 read through, u2 partly.
    repo.upsert_reader_section_progress(extraction_id="extA", section_id="u1", spans_seen=4, span_count=4,
                                        revealed=True, completed=True, clock=clock)
    repo.mark_section_generation(extraction_id="extA", section_id="u1", batch_id="batch_u1")
    repo.upsert_reader_section_progress(extraction_id="extA", section_id="u2", spans_seen=1, span_count=2,
                                        clock=clock)
    repo.upsert_unit_selection(extraction_id="extA", source_id="src1", revision_id="rev1",
                               selected_unit_ids=["u1", "u2", "u3"], exam_use_modes={"u3": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extA", "rev1"))
    repo.insert_entity_source_link(entity_type="facet", entity_id="facet_x", locator=f"span:extA/{EXACT}",
                                   relation="primary", source_id="src1", revision_id="rev1", extraction_id="extA")
    repo.insert_entity_source_link(entity_type="facet", entity_id="facet_y", locator=f"span:extA/{MOVED}",
                                   relation="primary", source_id="src1", revision_id="rev1", extraction_id="extA")
    # Citations made before the book was read again (no block hash, as in the owner's books).
    SO.author_source_object(repo, source_id="src1", revision_id="rev1", object_type="definition",
                            authorial_role="definition",
                            citations=[{"span_id": EXACT}, {"span_id": MOVED}, {"span_id": GONE}], clock=clock)
    annotations = {}
    for span_id, quote in ((EXACT, "vector space"), (MOVED, "zero vector")):
        translation = ANN.translate_selection(repo, extraction_id="extA",
                                              raw_selection={"nodes": [{"span_id": span_id, "quote": quote}]})
        annotations[span_id] = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="extA",
                                                     annotation_type="highlight", translation=translation,
                                                     clock=clock)["annotation_id"]
    clock.advance()
    vault = load_vault(paths.root)
    # An active practice item citing three passages of the old reading.
    item = vault.practice_items["pi_svd_define_001"]

    def refs(*spans):
        return [SourceRef(ref_type="canonical_source", ref_id="src1", locator=f"span:extA/{span}", source_id="src1",
                          extraction_id="extA") for span in spans]

    item.provenance.source_refs = refs(EXACT, MOVED, GONE)
    # Its learning object cites the first passage (the Reader's LO highlight).
    vault.learning_objects[item.learning_object_id].provenance.source_refs = refs(EXACT)
    return {"root": paths.root, "repo": repo, "vault": vault, "clock": clock, "annotations": annotations}


def _reread(studied, *, carry: bool = True) -> str:
    _persist(studied["repo"], reading_b(), revision_id="rev1", extraction_id="extB", clock=studied["clock"],
             page_selection=list(range(13, 39)))
    if carry:
        from learnloop.content.pipeline.reread import carry_over

        carry_over(studied["repo"], "extB", clock=studied["clock"])
    return "extB"


# --- item 3: one alias authority; every reference lands on the same text or is flagged --


def test_every_reference_lands_on_the_same_text_or_is_flagged_never_another_block(studied):
    from learnloop.content.sources import span_aliases
    repo = studied["repo"]
    _reread(studied)
    assert resolve_extraction_id(repo, "src1") == "extB"
    # The aliases are persisted for the re-read (source_span_reanchors).
    rows = {row["from_span_id"]: row for row in repo.span_reanchors_between("extA", "extB")}
    assert rows[EXACT]["to_span_id"] == "b1" and rows[EXACT]["match_kind"] == "exact_hash"
    assert rows[MOVED]["to_span_id"] == "b2" and rows[MOVED]["match_kind"] == "geometry_section"
    assert GONE not in rows

    for span_id in _A_TEXT:
        landed = span_aliases.resolve_span(repo, "extA", span_id, "extB")
        if landed.status == "current":
            assert _text(repo, "extB", landed.span_id) == _text(repo, "extA", span_id)
        elif landed.status == "needs_reanchor":
            assert landed.span_id is not None  # the same place, flagged
        else:
            assert landed.status == "stale" and landed.span_id is None
    assert span_aliases.resolve_span(repo, "extA", MOVED, "extB").status == "needs_reanchor"
    assert span_aliases.resolve_span(repo, "extA", GONE, "extB").status == "stale"


def test_section_progress_and_the_unit_selection_carry_to_the_new_reading(studied):
    repo = studied["repo"]
    _reread(studied)
    progress = {row["section_id"]: row for row in repo.reader_section_progress_for("extB")}
    # u1 -> h1 (its label), read through; its question build is not made twice.
    assert progress["h1"]["completed_at"] == "2026-10-14T09:01:00Z"
    assert progress["h1"]["spans_seen"] == progress["h1"]["span_count"] == 4
    assert progress["h1"]["generation_batch_id"] == "batch_u1"
    assert progress["h2"]["completed_at"] is None and 0 < progress["h2"]["spans_seen"] <= progress["h2"]["span_count"]
    assert sum(1 for row in progress.values() if row["completed_at"]) == 1

    selection = repo.get_unit_selection("extB")
    assert selection["selected_unit_ids"] == ["h1", "h2", "h3"]
    # Exam marks never move to another reading (protection redesign): the
    # re-read is held back whole until the owner marks it.
    assert selection["exam_use_modes"] == {}


def test_held_out_material_stays_withheld_on_the_new_reading(studied):
    from learnloop.content.sources.exam_material import UNMARKED_READING, exam_material

    repo = studied["repo"]
    _reread(studied)
    exam = exam_material(studied["vault"], repo)
    # The reading the mark was made on: exactly as marked.
    assert exam.is_held_out("extA", "a7") and not exam.covers("extA", "a1")
    # The re-read has no mark of its own (protection redesign): held back
    # whole until the owner marks its exam material.
    assert "extB" in exam.held_out.extractions and exam.is_held_out("extB", "b1")
    assert UNMARKED_READING in exam.verdict("extB", "b1").reasons


def test_unit_map_keeps_outline_unit_ids_that_name_the_same_sections():
    from learnloop.content.pipeline.reread import unit_map

    old, new = reading_a(), reading_a().model_copy(deep=True)
    new.units[0].semantic_hash = "sha256:changed"
    assert unit_map(old, new, {})["u1"] == "u1"


def reading_by_page() -> DocumentIR:
    """A coarser re-read (pypdf-like): one block per page, outline units under
    other ids and labels. Nothing matches by id, hash, label or text."""

    pages = {"p13": (13, "1 Vectors A vector space ... zero vector."), "p14": (14, "A list of vectors ..."),
             "p15": (15, "2 Spans The span of a list ..."), "p16": (16, "3 Exam review Exam problem ...")}
    texts = {span: ("Text", page, ["Chapter"], text) for span, (page, text) in pages.items()}
    return _ir(texts, [("c1", "Chapter One", "sha256:c1", ["p13", "p14"]),
                       ("c2", "Chapter Two", "sha256:c2", ["p15"]),
                       ("c3", "Review", "sha256:c3", ["p16"])], extractor="pypdf")


def test_unit_map_falls_back_to_the_pages_a_coarser_reading_puts_them_on():
    """The live re-read of Axler on backup copies: Marker's 60 fine units
    against the PDF outline's 13 left 4 of 11 read sections unmatched."""

    from learnloop.content.pipeline.reread import unit_map

    assert unit_map(reading_a(), reading_by_page(), {}) == {"u1": "c1", "u2": "c2", "u3": "c3"}


def test_progress_on_a_coarser_reading_is_read_through_only_where_every_part_was(studied):
    from learnloop.content.pipeline.reread import carry_over

    repo = studied["repo"]
    _persist(repo, reading_by_page(), revision_id="rev1", extraction_id="extP", clock=studied["clock"])
    carry_over(repo, "extP", clock=studied["clock"])
    progress = {row["section_id"]: row for row in repo.reader_section_progress_for("extP")}
    assert progress["c1"]["completed_at"] is not None and progress["c1"]["spans_seen"] == 2
    # u2 was half read: never shown as read through.
    assert progress["c2"]["completed_at"] is None and progress["c2"]["spans_seen"] < progress["c2"]["span_count"]
    selection = repo.get_unit_selection("extP")
    assert selection["selected_unit_ids"] == ["c1", "c2", "c3"]
    assert selection["exam_use_modes"] == {}  # never carried: the owner marks each reading


def test_the_guide_and_lo_highlights_survive_with_moved_passages_flagged(studied):
    from learnloop.reader.reader_guidance import build_guide_plan
    from learnloop.reader.reader_progression import learning_objects_for_span

    repo, vault = studied["repo"], studied["vault"]
    before = build_guide_plan(vault, repo, extraction_id="extA")
    before_passages = [p for s in before["sections"] for p in s["suggested_passages"]]
    assert {p["span_id"] for p in before_passages} == {EXACT, MOVED, GONE}
    _reread(studied)

    plan = build_guide_plan(vault, repo, extraction_id="extB")
    passages = {p["span_id"]: p for s in plan["sections"] for p in s["suggested_passages"]}
    assert plan["personalized"] is True
    assert passages["b1"]["anchor"] == "current" and passages["b1"]["quote"] == _A_TEXT[EXACT][3]
    # The re-worded passage shows at its place, flagged, with the words that were cited.
    assert passages["b2"]["anchor"] == "needs_reanchor" and passages["b2"]["quote"] == _A_TEXT[MOVED][3]
    # The passage that is gone is not shown as another block, and no old span id leaks.
    assert set(passages) == {"b1", "b2"}
    lo_id = vault.practice_items["pi_svd_define_001"].learning_object_id
    assert lo_id in learning_objects_for_span(vault, repo, extraction_id="extB", span_id="b1")


def test_a_margin_cue_marks_only_a_passage_whose_cited_words_are_there(studied):
    """RW3a's margin cues come from the Guide's misunderstanding passages: a
    passage flagged as reworded (the same place, other words) gets no
    unflagged mark in the margin; the rail shows it flagged."""

    from learnloop.reader import reader_cues as RCU
    from learnloop.reader.reader_guidance import build_guide_plan
    from tests.test_reader_cues import _active_error

    repo, vault = studied["repo"], studied["vault"]
    _active_error(repo)  # a recent misunderstanding on the item's learning object
    _reread(studied)
    plan = build_guide_plan(vault, repo, extraction_id="extB")
    rail = {p["span_id"]: p for s in plan["sections"] for p in s["suggested_passages"]}
    assert rail["b2"]["anchor"] == "needs_reanchor" and rail["b2"]["learner_signal"] == "recent_misunderstanding"
    # The book has a held-out mark on its first reading, so the re-read is
    # held back whole until the owner marks it (protection redesign): no cue.
    candidates, _held = RCU.cue_candidates(vault, repo, extraction_id="extB", plan=plan)
    assert candidates == []
    _confirm_marking(vault, repo, "src1", clock=studied["clock"])
    plan = build_guide_plan(vault, repo, extraction_id="extB")
    candidates, _held = RCU.cue_candidates(vault, repo, extraction_id="extB", plan=plan)
    assert [cue["span_id"] for cue in candidates] == ["b1"]


def test_citations_resolve_against_the_reading_they_were_made_on(studied):
    from learnloop.content.sources import span_aliases
    from learnloop.source_retrieval.find_sources import source_object_lists

    repo = studied["repo"]
    _reread(studied)
    resolver = span_aliases.CitationResolver(repo)
    with repo.connection() as connection:
        citations = {row["span_id"]: dict(row) for row in connection.execute("SELECT * FROM source_object_citations")}
    assert span_aliases.cited_reading(repo, revision_id="rev1", span_id=EXACT,
                                      created_at=citations[EXACT]["created_at"]) == "extA"
    assert resolver.current_key(citations[EXACT]) == ("extB", "b1")
    # Changed or gone: the reading it was made on, never "extB + the old span id".
    assert resolver.current_key(citations[MOVED]) == ("extA", MOVED)
    assert resolver.current_key(citations[GONE]) == ("extA", GONE)
    keys = source_object_lists(repo, "explain", ["extB"])["source_objects"]
    assert keys == [("extB", "b1")]
    assert all(key[1] in _B_TEXT for key in keys)


def test_a_new_citation_records_its_blocks_content_hash(studied):
    from learnloop.content.sources import span_aliases
    from learnloop.reader.reader_requests import _land_proposals

    repo = studied["repo"]
    _reread(studied)
    request = {"source_id": "src1", "revision_id": "rev1", "extraction_id": "extB", "preset": "explain"}
    _land_proposals(repo, request, None, object_type="claim", exact_text="x", content={}, span_ids=["b8"],
                    model_provenance={})
    with repo.connection() as connection:
        row = connection.execute("SELECT * FROM source_object_citations WHERE span_id = 'b8'").fetchone()
    assert row["block_content_hash"] == repo.load_document_ir("extB").block_by_span("b8").content_hash
    assert span_aliases.cited_reading(repo, revision_id="rev1", span_id="b8",
                                      block_content_hash=row["block_content_hash"]) == "extB"


def test_annotations_reanchor_automatically(studied):
    repo = studied["repo"]
    _reread(studied)
    heads = {head["annotation"]["id"]: head for head in repo.annotations_for_source("src1")}
    exact = heads[studied["annotations"][EXACT]]
    assert exact["anchor"]["extraction_id"] == "extB" and exact["anchor"]["status"] == "reanchored"
    assert exact["segments"][0]["span_id"] == "b1"
    moved = heads[studied["annotations"][MOVED]]
    assert moved["anchor"]["extraction_id"] == "extB" and moved["anchor"]["status"] in {"reanchored", "needs_reanchor"}
    if moved["anchor"]["status"] == "reanchored":
        segment = moved["segments"][0]
        assert _text(repo, "extB", segment["span_id"])[segment["codepoint_start"]:segment["codepoint_end"]] == "zero vector"


def test_the_saved_reading_place_translates_through_the_aliases(studied):
    repo = studied["repo"]
    _reread(studied)
    ctx = SidecarContext()
    ctx.load(studied["root"])
    view = call(ctx, "reader.render_view", {"extractionId": "src1"})
    assert view["extractionId"] == "extB" and view["aliasedFrom"] == ["extA"]
    place = call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extA", "spanId": EXACT})
    assert (place["spanId"], place["status"]) == ("b1", "current")
    moved = call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extA", "spanId": MOVED})
    assert (moved["spanId"], moved["status"]) == ("b2", "needs_reanchor")
    gone = call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extA", "spanId": GONE})
    assert (gone["spanId"], gone["status"]) == (None, "stale")
    # A bare span id saved before places recorded their reading: on the reading
    # the current one was read from again.
    legacy = call(ctx, "reader.saved_place", {"sourceId": "src1", "spanId": EXACT})
    assert (legacy["spanId"], legacy["fromExtractionId"]) == ("b1", "extA")
    # Saved on the current reading: as it is.
    same = call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extB", "spanId": "b5"})
    assert (same["spanId"], same["status"]) == ("b5", "current")


def test_source_conflicts_open_the_span_they_cite_never_another_block(studied):
    """The conflict review's "open in source" read ``span:<id>`` on the
    revision's latest reading: after a re-read, another block. Each side now
    opens through the one alias authority."""

    repo, clock = studied["repo"], studied["clock"]
    repo.insert_source_conflict(
        entity_type="facet", entity_id="facet_x", statement="disagree",
        left_source_id="src1", left_revision_id="rev1", left_locator=f"span:extA/{GONE}",
        right_source_id="src1", right_revision_id="rev1", right_locator=f"span:extA/{EXACT}", clock=clock)
    repo.insert_source_conflict(
        entity_type="facet", entity_id="facet_y", statement="disagree too",
        left_source_id="src1", left_revision_id="rev1", left_locator=f"span:{MOVED}",
        right_source_id="src1", right_revision_id="rev1", right_locator="Chapter 1 > Vectors", clock=clock)
    clock.advance()
    _reread(studied)
    ctx = SidecarContext()
    ctx.load(studied["root"])
    sides = {conflict["entityId"]: conflict for conflict in call(ctx, "list_source_conflicts", {})["conflicts"]}
    # Gone from the new reading: the reading it was cited on, whose text it names.
    assert (sides["facet_x"]["leftExtractionId"], sides["facet_x"]["leftSpanId"]) == ("extA", GONE)
    # The same text on the current reading: there.
    assert (sides["facet_x"]["rightExtractionId"], sides["facet_x"]["rightSpanId"]) == ("extB", "b1")
    # A bare span id is read against the reading current when it was cited.
    assert (sides["facet_y"]["leftExtractionId"], sides["facet_y"]["leftSpanId"]) == ("extA", MOVED)
    # Not a span: the revision's reading, nothing to open at.
    assert (sides["facet_y"]["rightExtractionId"], sides["facet_y"]["rightSpanId"]) == ("extB", None)


def test_references_still_resolve_for_a_reread_made_before_the_aliases_were_recorded(studied):
    """A re-read made by an older build (no source_span_reanchors rows): the
    same authority computes the aliases on read, never writing from a read."""

    from learnloop.content.sources import span_aliases
    repo = studied["repo"]
    _reread(studied, carry=False)
    assert repo.span_reanchors_between("extA", "extB") == []
    assert span_aliases.CurrentKeys(repo).key("extA", EXACT) == ("extB", "b1")
    assert span_aliases.CurrentKeys(repo).key("extA", MOVED) == ("extA", MOVED)
    assert repo.span_reanchors_between("extA", "extB") == []


# --- item 4: doctor ---------------------------------------------------------------------


def _codes(root) -> dict[str, list]:
    from learnloop.ops.doctor import run_doctor

    found: dict[str, list] = {}
    for issue in run_doctor(root).issues:
        if issue.code.startswith("source:") and issue.code != "source:retired_keep_local":
            found.setdefault(issue.code, []).append(issue)
    return found


def test_doctor_is_quiet_on_a_book_read_once(studied):
    assert _codes(studied["root"]) == {}


def test_doctor_warns_for_changed_citations_and_links_on_an_old_reading(studied):
    _reread(studied)
    codes = _codes(studied["root"])
    (citations,) = codes["source:citation_text_changed"]
    assert citations.severity == "warning" and citations.details["by_status"] == {"needs_reanchor": 1, "stale": 1}
    (links,) = codes["source:links_on_old_reading"]
    assert links.severity == "warning" and links.details["by_status"] == {"needs_reanchor": 1}


def test_doctor_reports_the_e1_state_with_its_fix(studied):
    from learnloop.ops.doctor import run_doctor

    repo, root = studied["repo"], studied["root"]
    # The state the old re-read left: a new current revision with no reading.
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, supersedes_revision_id, created_at) "
            "VALUES ('rev_pointer', 'src1', 'sha256:pointer', 'rev1', '2026-10-14T10:00:00Z')")
        connection.commit()
    repo.set_source_current_revision("src1", "rev_pointer")
    (issue,) = _codes(root)["source:current_revision_unread"]
    assert issue.severity == "error" and "--fix-state" in issue.message
    assert issue.details["readable_revision_id"] == "rev1"
    run_doctor(root, fix_state=True)
    assert repo.get_source_artifact("src1")["current_revision_id"] == "rev1"
    assert "source:current_revision_unread" not in _codes(root)


# --- items 1, 2 and 5 through the card --------------------------------------------------


def _blank_pdf(path: Path, pages: int) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    # A NUL in the header's binary comment, as a real book's compressed
    # streams carry near its start (same length: offsets stay valid). It makes
    # an extensionless copy of the file unclassifiable, as the owner's books
    # in the originals store are (GLM-OCR live run, 2026-10-14).
    raw = buffer.getvalue().replace(b"%\xe2\xe3\xcf\xd3", b"%\x00\xe3\xcf\xd3", 1)
    path.write_bytes(raw)
    return path


LFS_POINTER = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:b40b1da1c4f0aa1e0bfc2bdc0f2f2a1c84e5b0d8f3a6c9e2b7d4f1a0c3e5b7d9\n"
    b"size 2795246\n"
)


class Readings:
    """A fake extractor: the first reading is Marker-shaped, a re-read with
    text recognition segments differently. Records what each read was given."""

    def __init__(self, *, fail_reread: bool = False) -> None:
        self.seen: list[dict] = []
        self.fail_reread = fail_reread
        # Called while a reading runs: what the Library resolves the book to then.
        self.during = None

    @staticmethod
    def _reread(ctx) -> bool:
        config = ctx.payload.get("pdf_config") or {}
        return bool(config.get("force_ocr")) or config.get("engine") == "glm_ocr"

    def identity(self, fetched, category, ctx):
        reread = self._reread(ctx)
        return {"extractor": "glm_ocr" if reread else "marker", "extractor_version": "1", "model_versions": {},
                "config": dict(ctx.payload.get("pdf_config") or {})}

    def extract(self, fetched, category, ctx):
        reread = self._reread(ctx)
        self.seen.append({"sha": asset_hash(fetched.raw_bytes), "pages": ctx.payload.get("page_selection"),
                          "reread": reread})
        if self.during is not None:
            self.seen[-1]["during"] = self.during()
        if reread and self.fail_reread:
            raise RuntimeError("the reading failed")
        return reading_b() if reread else reading_a()


def _card_ctx(root, readings: Readings, clock):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=clock,
                         services=fake_services(extract=readings.extract, describe_extraction=readings.identity,
                                                background_key_checks=False))
    return ctx


@pytest.fixture
def card_book(tmp_path, monkeypatch):
    """A 40-page book read on pages 14-39 through the import queue."""

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(core, "text_recognition_available", lambda **_: True)
    root = fresh_library(tmp_path)
    clock = _clock()
    readings = Readings()
    ctx = _card_ctx(root, readings, clock)
    book = _blank_pdf(tmp_path / "axler.pdf", 40)
    ctx.ingest_jobs._require_runner().enqueue_batch(
        "import", [JobSpec("import", {"source": str(book), "page_selection": list(range(13, 39))})])
    ctx.ingest_jobs.drain_foreground()
    (artifact,) = ctx.repository.all_source_artifacts()
    clock.advance()
    return {"root": root, "ctx": ctx, "book": book, "source_id": artifact["id"], "readings": readings,
            "clock": clock}


def _revisions(ctx, source_id):
    return ctx.repository.source_revisions_for(source_id)


@pytest.mark.parametrize("damage", ["lfs_pointer", "deleted"])
def test_e1_the_reread_reads_the_stored_original_and_reuses_the_revision(card_book, damage):
    ctx, source_id, book = card_book["ctx"], card_book["source_id"], card_book["book"]
    (revision,) = _revisions(ctx, source_id)
    first = resolve_extraction_id(ctx.repository, source_id)
    if damage == "lfs_pointer":
        book.write_bytes(LFS_POINTER)
    else:
        book.unlink()

    card_book["readings"].during = lambda: resolve_extraction_id(ctx.repository, source_id)
    # No study state yet: the card reads it again without asking.
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    ctx.ingest_jobs.drain_foreground()

    assert ctx.repository.get_ingest_batch(out["batchId"])["status"] == "completed"
    assert card_book["readings"].seen[-1]["during"] == first  # the book resolves throughout
    assert [rev["id"] for rev in _revisions(ctx, source_id)] == [revision["id"]]  # reused, nothing registered
    assert card_book["readings"].seen[-1]["sha"] == revision["asset_hash"]  # the real bytes were read
    assert stored_original_path(card_book["root"], asset_hash(LFS_POINTER)) is None
    current = resolve_extraction_id(ctx.repository, source_id)
    assert current != first and ctx.repository.get_extraction_run(current)["revision_id"] == revision["id"]


def test_e1_the_reread_hands_the_import_the_stored_bytes_never_a_store_path(card_book):
    """GLM-OCR live run (2026-10-14): the originals store's files have no
    extension, so ``resolve_source`` refuses one as a path. A re-read of a
    book whose recorded path is the store file (as the live run pointed the
    copies' books) is handed the stored bytes, checked against the current
    revision's hash, and its path is never classified again."""

    from learnloop.ingest.resolution import UnsupportedSourceError, resolve_source

    ctx, source_id, root = card_book["ctx"], card_book["source_id"], card_book["root"]
    (revision,) = _revisions(ctx, source_id)
    first = resolve_extraction_id(ctx.repository, source_id)
    store = stored_original_path(root, revision["asset_hash"])
    with pytest.raises(UnsupportedSourceError):
        resolve_source(str(store))  # the live finding: a store path is no source
    with ctx.repository.connection() as connection:
        connection.execute("UPDATE source_artifacts SET canonical_uri = ? WHERE id = ?", (str(store), source_id))
        connection.commit()
    card_book["book"].unlink()  # nothing readable anywhere but the store

    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    ctx.ingest_jobs.drain_foreground()

    (job,) = [job for job in ctx.repository.ingest_jobs_for_batch(out["batchId"]) if job["job_type"] == "import"]
    assert job["status"] == "completed", job.get("error")
    assert card_book["readings"].seen[-1]["sha"] == revision["asset_hash"]  # the stored bytes, hash-checked
    assert [rev["id"] for rev in _revisions(ctx, source_id)] == [revision["id"]]  # nothing registered
    assert [artifact["id"] for artifact in ctx.repository.all_source_artifacts()] == [source_id]
    current = resolve_extraction_id(ctx.repository, source_id)
    assert current != first and ctx.repository.get_extraction_run(current)["revision_id"] == revision["id"]


def test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing(card_book):
    ctx, source_id, root = card_book["ctx"], card_book["source_id"], card_book["root"]
    (revision,) = _revisions(ctx, source_id)
    first = resolve_extraction_id(ctx.repository, source_id)
    card_book["book"].write_bytes(LFS_POINTER)
    stored_original_path(root, revision["asset_hash"]).unlink()

    with pytest.raises(SidecarError) as refused:
        call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    assert refused.value.code == "original_changed"
    assert "changed or is missing" in str(refused.value)

    # The import refuses the same way when it is reached another way.
    batch = ctx.ingest_jobs._require_runner().enqueue_batch(
        "import", [JobSpec("import", {"source": str(card_book["book"]), "source_id": source_id})])
    ctx.ingest_jobs.drain_foreground()
    (job,) = ctx.repository.ingest_jobs_for_batch(batch)
    assert job["status"] == "failed" and job["error"]["code"] == "original_changed"
    assert [rev["id"] for rev in _revisions(ctx, source_id)] == [revision["id"]]
    assert stored_original_path(root, asset_hash(LFS_POINTER)) is None
    assert resolve_extraction_id(ctx.repository, source_id) == first
    line = core.source_status_line(ctx.repository, ctx.vault, source_id)
    assert line["text"] == "Couldn't read it again: its original file changed or is missing"


def test_e1_a_failed_import_of_new_bytes_leaves_the_previous_revision_current(card_book, tmp_path):
    ctx, source_id, book = card_book["ctx"], card_book["source_id"], card_book["book"]
    (old,) = _revisions(ctx, source_id)
    first = resolve_extraction_id(ctx.repository, source_id)
    _blank_pdf(book, 41)  # the file at the book's path really changed
    card_book["readings"].fail_reread = True
    runner = ctx.ingest_jobs._require_runner()
    runner.enqueue_batch("import", [JobSpec("import", {"source": str(book), "pdf_config": {"engine": "glm_ocr"}})])
    ctx.ingest_jobs.drain_foreground()
    assert len(_revisions(ctx, source_id)) == 2
    assert ctx.repository.get_source_artifact(source_id)["current_revision_id"] == old["id"]
    assert resolve_extraction_id(ctx.repository, source_id) == first
    assert core.source_status_line(ctx.repository, ctx.vault, source_id) is None or \
        core.source_status_line(ctx.repository, ctx.vault, source_id)["action"] != {"kind": "restore_reading",
                                                                                   "label": "Open the reading you had"}
    # The same import that completes adopts the new revision.
    card_book["readings"].fail_reread = False
    runner.enqueue_batch("import", [JobSpec("import", {"source": str(book), "pdf_config": {"engine": "glm_ocr"}})])
    ctx.ingest_jobs.drain_foreground()
    new = _revisions(ctx, source_id)[-1]
    assert ctx.repository.get_source_artifact(source_id)["current_revision_id"] == new["id"] != old["id"]


def test_a_retried_import_reads_the_revision_it_registered_not_the_current_one(card_book):
    ctx, source_id, book = card_book["ctx"], card_book["source_id"], card_book["book"]
    (old,) = _revisions(ctx, source_id)
    _blank_pdf(book, 41)  # new bytes at the book's path: a new revision, not yet current
    new_hash = asset_hash(book.read_bytes())
    card_book["readings"].fail_reread = True
    batch = ctx.ingest_jobs._require_runner().enqueue_batch(
        "import", [JobSpec("import", {"source": str(book), "pdf_config": {"engine": "glm_ocr"}})])
    ctx.ingest_jobs.drain_foreground()
    assert ctx.repository.get_source_artifact(source_id)["current_revision_id"] == old["id"]
    book.unlink()  # the retry cannot read the path: the store holds the revision it registered
    card_book["readings"].fail_reread = False
    ctx.ingest_jobs.resume_batch(batch)
    ctx.ingest_jobs.drain_foreground()
    (job,) = ctx.repository.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert card_book["readings"].seen[-1]["sha"] == new_hash != old["asset_hash"]
    assert ctx.repository.get_source_artifact(source_id)["current_revision_id"] == job["result"]["revision_id"]


def test_e1_one_tap_repair_for_a_library_already_in_that_state(card_book):
    ctx, source_id = card_book["ctx"], card_book["source_id"]
    (old,) = _revisions(ctx, source_id)
    first = resolve_extraction_id(ctx.repository, source_id)
    with ctx.repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, supersedes_revision_id, created_at) "
            "VALUES ('rev_pointer', ?, ?, ?, '2026-10-14T10:00:00Z')", (source_id, asset_hash(LFS_POINTER), old["id"]))
        connection.commit()
    ctx.repository.set_source_current_revision(source_id, "rev_pointer")
    # The book still opens (its reading is found), and its card offers the repair.
    assert resolve_extraction_id(ctx.repository, source_id) == first
    line = core.source_status_line(ctx.repository, ctx.vault, source_id)
    assert line["action"] == {"kind": "restore_reading", "label": "Open the reading you had"}
    assert line["text"] == "This book's file changed after it was read"
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "restore_reading"})
    assert out["restoredRevisionId"] == old["id"]
    assert ctx.repository.get_source_artifact(source_id)["current_revision_id"] == old["id"]
    after = core.source_status_line(ctx.repository, ctx.vault, source_id)
    assert after is None or after["action"] is None or after["action"]["kind"] != "restore_reading"


def test_the_reread_keeps_the_page_scope_and_carries_the_selection(card_book):
    ctx, source_id = card_book["ctx"], card_book["source_id"]
    first = resolve_extraction_id(ctx.repository, source_id)
    ctx.repository.upsert_unit_selection(extraction_id=first, source_id=source_id,
                                         revision_id=_revisions(ctx, source_id)[0]["id"],
                                         selected_unit_ids=["u1", "u2", "u3"],
                                         exam_use_modes={"u3": "held_out_evaluation"},
                                         exam_paper_metadata=_made_on(first, _revisions(ctx, source_id)[0]["id"]))
    ctx.repository.upsert_reader_section_progress(extraction_id=first, section_id="u1", spans_seen=4, span_count=4,
                                                  completed=True)

    asked = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    # A book with study state asks first, naming the pages and what moves.
    assert asked["needsConfirmation"] is True and "batchId" not in asked
    confirmation = asked["confirmation"]
    assert confirmation["pageSelection"] == list(range(13, 39)) and confirmation["pages"] == 26
    assert confirmation["lines"][0] == "Pages 14–39 (26 pages), as before."
    assert "your progress (1 section)" in confirmation["lines"][2].lower()
    assert ctx.repository.ingest_jobs_for_source(("import",), source_id)[0]["status"] == "completed"

    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    import_job = next(job for job in ctx.repository.ingest_jobs_for_batch(out["batchId"]) if job["job_type"] == "import")
    assert import_job["payload"]["page_selection"] == list(range(13, 39))
    ctx.ingest_jobs.drain_foreground()
    assert card_book["readings"].seen[-1] == {"sha": card_book["readings"].seen[0]["sha"],
                                              "pages": list(range(13, 39)), "reread": True}
    new = resolve_extraction_id(ctx.repository, source_id)
    assert new != first and ctx.repository.get_extraction_run(new)["page_selection"] == list(range(13, 39))
    selection = ctx.repository.get_unit_selection(new)
    assert selection["selected_unit_ids"] == ["h1", "h2", "h3"]
    assert [row["section_id"] for row in ctx.repository.reader_section_progress_for(new) if row["completed_at"]] == ["h1"]

    # Protection redesign: the held-out mark stays on the reading it was made
    # on and never moves; the confirmation said so, and the card now asks the
    # owner to mark the new reading, which is held back whole until then.
    from learnloop.content.pipeline.reread import HELD_BACK_PLAN_LINE
    from learnloop.content.sources.exam_material import exam_material

    assert HELD_BACK_PLAN_LINE in confirmation["lines"]
    assert selection["exam_use_modes"] == {}
    line = core.source_status_line(ctx.repository, ctx.vault, source_id)
    assert line["text"] == "This reading is held back until you mark its exam material" and line["tone"] == "problem"
    assert line["action"] == {"kind": "mark_exam_material", "label": "Mark exam material on this reading"}
    assert new in exam_material(ctx.vault, ctx.repository).held_out.extractions
    asked = call(ctx, "source_action", {"sourceId": source_id, "action": "mark_exam_material"})
    assert asked["needsConfirmation"] is True
    assert asked["confirmation"]["lines"][0] == "Held out as exam material: 3 Exam review."
    assert asked["confirmation"]["confirmLabel"] == "Mark them" and asked["confirmation"]["cancelLabel"] == "Not now"
    assert new in exam_material(ctx.vault, ctx.repository).held_out.extractions  # nothing written yet
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "mark_exam_material", "confirmed": True,
                                      "confirmedExtractionId": asked["confirmation"]["extractionId"],
                                      "confirmedProposalHash": asked["confirmation"]["proposalHash"]})
    assert out["marked"]["heldOutUnitIds"] == ["h3"]
    exam = exam_material(ctx.vault, ctx.repository)
    assert new not in exam.held_out.extractions
    assert exam.is_held_out(new, "b8") and not exam.covers(new, "b1")
    assert exam.is_held_out(first, "a7") and not exam.covers(first, "a1"), "the first reading exactly as marked"
    after = core.source_status_line(ctx.repository, ctx.vault, source_id)
    assert after is None or after["action"] is None or after["action"]["kind"] != "mark_exam_material"


def test_a_book_without_study_state_is_read_again_without_asking(card_book):
    ctx, source_id = card_book["ctx"], card_book["source_id"]
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    assert out.get("needsConfirmation") is None and out["batchId"]


# --- item 2 with GLM-OCR, and item 5: pages and cost where the re-read is asked --------


@pytest.fixture
def no_network(monkeypatch):
    from learnloop.ingest.extractors import glm_ocr as glm

    monkeypatch.setattr(glm, "_open", lambda *a, **kw: pytest.fail("unexpected HTTP request"))
    monkeypatch.setattr(glm, "_PROBES", {})
    return glm


def test_the_z_ai_ok_line_names_pages_and_cost_for_a_404_page_book(tmp_path, monkeypatch, no_network):
    from learnloop.ingest import extractors
    from learnloop.vault.loader import load_vault
    from tests.ux_phase1_support import repository

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.setenv("ZAI_API_KEY", "fake-zai-key-123456")
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    root = fresh_library(tmp_path)
    repo = repository(root)
    from tests.test_glm_ocr import _jobs

    jobs = _jobs(repo, root)
    item = core.add_source(load_vault(root), jobs, str(_blank_pdf(tmp_path / "axler.pdf", 404)))
    jobs._require_runner().drain()
    line = core.source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Reading this document (404 pages, about $0.07) sends the whole file to z.ai (GLM-OCR)"
    assert line["action"] == {"kind": "allow_upload", "label": "OK"}


def test_the_reread_confirmation_shows_pages_and_cost_when_z_ai_reads_it(card_book, monkeypatch, no_network):
    from tests.ux_phase1_support import grant_consent

    ctx, source_id = card_book["ctx"], card_book["source_id"]
    monkeypatch.setenv("ZAI_API_KEY", "fake-zai-key-123456")
    grant_consent(card_book["root"], "whole_files_zai")  # the z.ai OK was given earlier: no OK line will ask
    ctx.reload(maintenance=False)
    asked = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    assert asked["needsConfirmation"] is True
    confirmation = asked["confirmation"]
    assert confirmation["engine"] == "glm_ocr" and confirmation["pages"] == 26
    assert confirmation["estimatedUsd"] == pytest.approx(26 * 6000 * 0.03 / 1_000_000)
    assert confirmation["lines"][1] == "z.ai (GLM-OCR) reads it: less than $0.01."


def test_a_glm_reread_of_a_sliced_book_sends_only_its_pages(card_book, monkeypatch, no_network):
    """Through the real GLM-OCR extractor (a fake transport): the 26 pages
    of the reading it replaces, never the whole 40-page file."""

    import json

    from pypdf import PdfReader
    from tests.test_glm_ocr import hosted
    from tests.ux_phase1_support import grant_consent

    glm = no_network
    sent = []

    def fake(request, timeout):
        body = json.loads(request.data)
        sent.append(body)
        pages = body.get("end_page_id", 1) - body.get("start_page_id", 1) + 1
        return io.BytesIO(json.dumps(hosted(pages)).encode())

    monkeypatch.setattr(glm, "_open", fake)
    ctx, source_id, root = card_book["ctx"], card_book["source_id"], card_book["root"]
    monkeypatch.setenv("ZAI_API_KEY", "fake-zai-key-123456")
    grant_consent(root, "whole_files_zai")
    ctx.reload(maintenance=False)
    # The real extractor this time.
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=card_book["clock"],
                         services=fake_services(background_key_checks=False))
    asked = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    if asked.get("needsConfirmation"):  # z.ai's OK was given: the card names pages and cost first
        call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    assert sent, "GLM-OCR was not asked"
    import base64

    uploaded = sum(len(PdfReader(io.BytesIO(base64.b64decode(body["file"].split(",", 1)[-1]))).pages)
                   for body in sent)
    assert uploaded == 26


# --- Codex review of the stage (2026-10-14): reproductions, written to fail first ------


def _persist_child(repo: Repository, ir: DocumentIR, *, revision_id: str, extraction_id: str, parent: str, clock,
                   page_selection) -> str:
    """A completed one-page repair child of a reading (``handle_extraction_repair``)."""

    request_hash = extraction_request_hash(
        revision_id=revision_id, extractor=ir.extractor, extractor_version=ir.extractor_version,
        page_selection=page_selection, ir_schema_version=IR_SCHEMA_VERSION, config={"repair_of": parent},
    )
    repo.insert_extraction_run(
        id=extraction_id, revision_id=revision_id, extractor=ir.extractor, extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, page_selection=page_selection,
        parent_extraction_id=parent, status="running", clock=clock,
    )
    repo.persist_document_ir(extraction_id, ir)
    repo.complete_extraction_run(extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir),
                                 clock=clock)
    return extraction_id


_EXAM_Q = "Exam question: prove that every eigenvalue of a self-adjoint operator is real."
_THEORY = "Theory: a self-adjoint operator has only real eigenvalues, by the spectral theorem."


def _exam_reading_a() -> DocumentIR:
    return _ir({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], _EXAM_Q),
                "x2": ("SectionHeader", 2, ["Theory"], "Theory"), "x3": ("Text", 2, ["Theory"], _THEORY)},
               [("u1", "Exam", "sha256:exam-a", ["x0", "x1"]), ("u2", "Theory", "sha256:theory-a", ["x2", "x3"])],
               extractor="marker")


def _exam_reading_b() -> DocumentIR:
    """The re-read reuses A's unit ids for the other units: u1 is Theory here."""

    return _ir({"y0": ("SectionHeader", 2, ["Theory"], "Theory"), "y1": ("Text", 2, ["Theory"], _THEORY),
                "y2": ("SectionHeader", 1, ["Exam"], "Exam"), "y3": ("Text", 1, ["Exam"], _EXAM_Q)},
               [("u1", "Theory", "sha256:theory-b", ["y0", "y1"]), ("u2", "Exam", "sha256:exam-b", ["y2", "y3"])],
               extractor="glm_ocr")


@pytest.fixture
def exam_book(tmp_path):
    from tests.helpers import create_basic_vault
    from tests.test_source_inventory import _register_revision

    clock = _clock()
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src_x", revision_id="rev_x")
    repo.set_source_current_revision("src_x", "rev_x")
    _persist(repo, _exam_reading_a(), revision_id="rev_x", extraction_id="extXA", clock=clock)
    clock.advance()
    return {"repo": repo, "clock": clock, "root": paths.root}


def _exam_sets(*, default_role: str = "textbook", scope=(("u1", "exam"),), reading: str | None = "extXA"):
    """The exam book's source set; its scope names the reading it was made on
    (``reading``; None: a legacy scope that names none)."""

    from learnloop.vault.models import SourceSet, SourceSetMember, SourceSetScope, scope_seal

    named = {"scope_extraction_id": reading, "scope_revision_id": "rev_x"} if scope and reading else {}
    member = SourceSetMember(source_id="src_x", revision_id="rev_x", default_role=default_role,
                             scope=[SourceSetScope(unit_id=unit, role_override=role) for unit, role in scope], **named)
    member.scope_seal = scope_seal(member)  # as the vault writer seals it
    return [SourceSet(id="set_x", subject_id="linear_algebra", title="Exam prep", members=[member])]


def test_f1_reused_unit_ids_never_release_a_source_set_exam_scope(exam_book):
    """F1: the scope's ``u1`` named reading A's Exam unit; the re-read B uses
    ``u1`` for Theory. The exam material stays withheld in both readings."""

    from learnloop.content.sources.exam_material import exam_material, role_material

    repo, clock = exam_book["repo"], exam_book["clock"]
    sets = _exam_sets()
    before = exam_material(sets, repo)
    assert before.covers("extXA", "x1") and not before.covers("extXA", "x3")
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    after = exam_material(sets, repo)
    assert after.covers("extXA", "x1"), "the exam question of the reading the scope was made on"
    assert after.covers("extXB", "y3"), "the same exam question on the re-read"
    teaching = role_material(sets, repo, lambda role: role == "exam")
    assert teaching.covers("extXA", "x1") and teaching.covers("extXB", "y3")


def _held_out_inventory(repo, *, extraction_id: str, unit_id: str, span_ids, held_out: bool = True) -> None:
    from learnloop.ids import new_ulid

    repo.insert_unit_inventory(
        id="inv_" + new_ulid(), source_revision_id="rev_x", extraction_id=extraction_id, unit_id=unit_id,
        unit_semantic_hash=f"sha256:{extraction_id}-{unit_id}", inventory_profile="exam",
        inventory_schema_version=1, prompt_version="test", provider="fake", model="fake",
        inventory={"assessment_signals": [{"signal_id": "sig_1", "held_out": held_out,
                                           "span_ids": list(span_ids)}]})


def test_f2_held_out_signals_stay_on_the_passage_they_name_after_a_reread(exam_book):
    """F2: an exam paper's inventory marks A's ``x1`` held out. After the
    re-read that passage is B's ``y3``: the held-out partition keeps (A, x1)
    and protects (B, y3), never "(B, x1)"."""

    from learnloop.content.sources.exam_material import exam_material, held_out_partition

    repo, clock = exam_book["repo"], exam_book["clock"]
    sets = _exam_sets(default_role="exam", scope=())
    _held_out_inventory(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"])
    assert held_out_partition(sets, repo).covers("extXA", "x1")
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    held = held_out_partition(sets, repo)
    assert held.covers("extXA", "x1"), "the passage on the reading the inventory was made on"
    assert held.covers("extXB", "y3"), "the same passage on the re-read"
    assert exam_material(sets, repo).is_held_out("extXB", "y3")


def test_f2_a_held_out_signal_that_matches_nowhere_withholds_the_reading(exam_book):
    from learnloop.content.sources.exam_material import held_out_partition

    repo, clock = exam_book["repo"], exam_book["clock"]
    sets = _exam_sets(default_role="exam", scope=())
    _held_out_inventory(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"])
    # Nothing of A's at the same text or the same place: no alias at all.
    gone = _ir({"z0": ("SectionHeader", 9, ["Appendix"], "Appendix"), "z1": ("Text", 9, ["Appendix"], "Unrelated.")},
               [("u1", "Appendix", "sha256:z", ["z0", "z1"])], extractor="pypdf")
    _persist(repo, gone, revision_id="rev_x", extraction_id="extXZ", clock=clock)
    held = held_out_partition(sets, repo)
    assert held.covers("extXA", "x1") and "extXZ" in held.extractions  # fail closed


def test_f3_reviewing_a_legacy_citation_after_a_reread_keeps_what_it_cites(studied):
    """F3: a status-only review copies a citation with no block hash into a
    new version with a new timestamp; it still names the reading it was made on."""

    from learnloop.reader import source_objects as SO
    from learnloop.source_retrieval.find_sources import source_object_lists

    repo, clock = studied["repo"], studied["clock"]
    _reread(studied)
    clock.advance()
    (head,) = repo.source_objects_for_source("src1")
    SO.review_source_object(repo, source_object_id=head["object"]["id"], status="reviewed", clock=clock)
    assert source_object_lists(repo, "explain", ["extB"])["source_objects"] == [("extB", "b1")]
    (citations,) = _codes(studied["root"])["source:citation_text_changed"]
    # Both versions' citations of the changed and the gone passage, never "current".
    assert citations.details["by_status"] == {"needs_reanchor": 2, "stale": 2}
    # A copy a review made before this fix carries the review's time: it is
    # still read from the first copy's time.
    review_time = clock.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    with repo.connection() as connection:
        connection.execute(
            "UPDATE source_object_citations SET created_at = ? WHERE source_object_version_id IN "
            "(SELECT id FROM source_object_versions WHERE version_ordinal = 2)", (review_time,))
        connection.commit()
    assert source_object_lists(repo, "explain", ["extB"])["source_objects"] == [("extB", "b1")]
    (citations,) = _codes(studied["root"])["source:citation_text_changed"]
    assert citations.details["by_status"] == {"needs_reanchor": 2, "stale": 2}


def test_f3_a_reviewed_copy_keeps_its_citations_origin(studied):
    """The copy itself carries when the citation was made (a stable origin)."""

    from learnloop.reader import source_objects as SO

    repo, clock = studied["repo"], studied["clock"]
    _reread(studied)
    clock.advance()
    (head,) = repo.source_objects_for_source("src1")
    SO.review_source_object(repo, source_object_id=head["object"]["id"], status="reviewed", clock=clock)
    with repo.connection() as connection:
        made = {(row["span_id"], row["created_at"]) for row in connection.execute(
            "SELECT span_id, created_at FROM source_object_citations")}
    assert len(made) == 3  # one origin per citation, across both versions


def test_f4_a_page_repair_never_becomes_the_next_rereads_scope(card_book):
    ctx, source_id, clock = card_book["ctx"], card_book["source_id"], card_book["clock"]
    first = resolve_extraction_id(ctx.repository, source_id)
    revision_id = ctx.repository.get_extraction_run(first)["revision_id"]
    _persist_child(ctx.repository, reading_a(), revision_id=revision_id, extraction_id="ext_repair", parent=first,
                   clock=clock, page_selection=[20])
    clock.advance()
    assert resolve_extraction_id(ctx.repository, source_id) == first  # the Reader opens the top-level reading
    ctx.repository.upsert_reader_section_progress(extraction_id=first, section_id="u1", spans_seen=4, span_count=4,
                                                  completed=True)
    asked = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    confirmation = asked["confirmation"]
    assert confirmation["pageSelection"] == list(range(13, 39))
    assert confirmation["lines"][0] == "Pages 14–39 (26 pages), as before."
    assert "your progress (1 section)" in confirmation["lines"][2].lower()
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    import_job = next(job for job in ctx.repository.ingest_jobs_for_batch(out["batchId"]) if job["job_type"] == "import")
    assert import_job["payload"]["page_selection"] == list(range(13, 39))


def test_f5_a_legacy_saved_place_with_an_unknown_reading_falls_back_to_the_history(studied):
    """F5: a bare span id saved before places recorded their reading, on a
    book read again by an older build (no aliases recorded): its reading is
    unknown, so it is never declared a place on the current reading."""

    _reread(studied, carry=False)
    ctx = SidecarContext()
    ctx.load(studied["root"])
    view = call(ctx, "reader.render_view", {"extractionId": "src1"})
    assert view["extractionId"] == "extB" and view["otherReadings"] == ["extA"]
    legacy = call(ctx, "reader.saved_place", {"sourceId": "src1", "spanId": "b5"})
    assert (legacy["spanId"], legacy["status"]) == (None, "stale")


def test_f5_a_legacy_saved_place_after_a_reread_with_no_alias_falls_back_to_the_history(studied):
    repo = studied["repo"]
    nothing_alike = _ir({"q0": ("Text", 30, ["Other"], "Entirely different words."),
                         "q1": ("Text", 31, ["Other"], "More different words.")},
                        [("w1", "Other", "sha256:w1", ["q0", "q1"])], extractor="pypdf")
    _persist(repo, nothing_alike, revision_id="rev1", extraction_id="extQ", clock=studied["clock"])
    from learnloop.content.pipeline.reread import carry_over

    carry_over(repo, "extQ", clock=studied["clock"])
    assert repo.span_reanchors_between("extA", "extQ") == []
    ctx = SidecarContext()
    ctx.load(studied["root"])
    legacy = call(ctx, "reader.saved_place", {"sourceId": "src1", "spanId": "q1"})
    assert (legacy["spanId"], legacy["status"]) == (None, "stale")


def test_f5_a_legacy_saved_place_on_a_book_read_once_is_on_its_reading(studied):
    ctx = SidecarContext()
    ctx.load(studied["root"])
    view = call(ctx, "reader.render_view", {"extractionId": "src1"})
    assert view["otherReadings"] == []
    legacy = call(ctx, "reader.saved_place", {"sourceId": "src1", "spanId": EXACT})
    assert (legacy["spanId"], legacy["status"]) == (EXACT, "current")


def _annotate(repo, extraction_id: str, span_id: str, quote: str, *, source_id: str, revision_id: str, clock) -> str:
    from learnloop.reader import annotations as ANN

    translation = ANN.translate_selection(repo, extraction_id=extraction_id,
                                          raw_selection={"nodes": [{"span_id": span_id, "quote": quote}]})
    return ANN.append_annotation(repo, source_id=source_id, revision_id=revision_id, extraction_id=extraction_id,
                                 annotation_type="highlight", translation=translation, clock=clock)["annotation_id"]


def test_f6_an_import_that_reuses_an_older_reading_never_moves_annotations_backward(card_book):
    ctx, source_id, clock = card_book["ctx"], card_book["source_id"], card_book["clock"]
    repo = ctx.repository
    first = resolve_extraction_id(repo, source_id)
    revision_id = repo.get_extraction_run(first)["revision_id"]
    _annotate(repo, first, EXACT, "vector space", source_id=source_id, revision_id=revision_id, clock=clock)
    pages = list(range(13, 39))
    # B: the card's re-read; C: another engine's reading of the same pages.
    call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    second = resolve_extraction_id(repo, source_id)
    clock.advance()
    runner = ctx.ingest_jobs._require_runner()
    runner.enqueue_batch("import", [JobSpec("import", {"source": str(card_book["book"]), "source_id": source_id,
                                                       "page_selection": pages,
                                                       "pdf_config": {"engine": "glm_ocr"}})])
    ctx.ingest_jobs.drain_foreground()
    third = resolve_extraction_id(repo, source_id)
    assert len({first, second, third}) == 3
    assert {head["anchor"]["extraction_id"] for head in repo.annotations_for_source(source_id)} == {third}
    clock.advance()
    # The card's re-read again: the extraction cache hands back B.
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    (job,) = [job for job in repo.ingest_jobs_for_batch(out["batchId"]) if job["job_type"] == "import"]
    assert job["result"]["reused_extraction"] is True and job["result"]["extraction_id"] == second
    assert resolve_extraction_id(repo, source_id) == third
    assert {head["anchor"]["extraction_id"] for head in repo.annotations_for_source(source_id)} == {third}


@pytest.mark.parametrize("step", ["aliases", "progress", "selection", "annotations"])
def test_f7_a_carry_over_that_fails_is_finished_later_never_lost(card_book, monkeypatch, step):
    from learnloop.content.pipeline import reread
    from learnloop.content.sources import span_aliases

    ctx, source_id, clock = card_book["ctx"], card_book["source_id"], card_book["clock"]
    repo = ctx.repository
    first = resolve_extraction_id(repo, source_id)
    revision_id = repo.get_extraction_run(first)["revision_id"]
    repo.upsert_unit_selection(extraction_id=first, source_id=source_id, revision_id=revision_id,
                               selected_unit_ids=["u1", "u2", "u3"], exam_use_modes={"u3": "held_out_evaluation"},
                               exam_paper_metadata=_made_on(first, revision_id))
    repo.upsert_reader_section_progress(extraction_id=first, section_id="u1", spans_seen=4, span_count=4,
                                        completed=True)
    _annotate(repo, first, EXACT, "vector space", source_id=source_id, revision_id=revision_id, clock=clock)
    target = {"aliases": (span_aliases, "record_aliases"), "progress": (reread, "carry_progress"),
              "selection": (reread, "carry_selection"), "annotations": (reread, "carry_annotations")}[step]
    original = getattr(*target)

    def busy(*args, **kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(*target, busy)
    call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    new = resolve_extraction_id(repo, source_id)
    assert new != first  # the reading stands
    line = core.source_status_line(repo, ctx.vault, source_id)
    assert line["text"] == "Your progress and notes didn't all move to the new reading"
    assert line["action"] == {"kind": "retry", "label": "Finish moving them"}
    from learnloop.ops.doctor import run_doctor

    assert any(issue.code == "source:reread_carry_incomplete" for issue in run_doctor(card_book["root"]).issues)

    monkeypatch.setattr(*target, original)
    call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    assert [row["section_id"] for row in repo.reader_section_progress_for(new) if row["completed_at"]] == ["h1"]
    assert repo.get_unit_selection(new)["selected_unit_ids"] == ["h1", "h2", "h3"]
    assert repo.get_unit_selection(new)["exam_use_modes"] == {}  # marks never move (protection redesign)
    assert {head["anchor"]["extraction_id"] for head in repo.annotations_for_source(source_id)} == {new}
    assert repo.span_reanchors_between(first, new)
    after = core.source_status_line(repo, ctx.vault, source_id)
    assert after is None or after["text"] != "Your progress and notes didn't all move to the new reading"
    assert not any(issue.code == "source:reread_carry_incomplete" for issue in run_doctor(card_book["root"]).issues)


def test_f9_a_self_hosted_glm_ocr_reread_is_named_and_priced_as_local(card_book, monkeypatch, no_network):
    from tests.ux_phase1_support import set_config

    ctx, source_id, root = card_book["ctx"], card_book["source_id"], card_book["root"]
    monkeypatch.setattr(no_network, "local_available", lambda config=None: True)
    set_config(root, {("ingest", "pdf", "glm_ocr", "backend"): "local",
                      ("ingest", "pdf", "glm_ocr", "local_url"): "http://127.0.0.1:5002/glmocr/parse"})
    ctx.reload(maintenance=False)
    ctx.repository.upsert_reader_section_progress(extraction_id=resolve_extraction_id(ctx.repository, source_id),
                                                  section_id="u1", spans_seen=4, span_count=4, completed=True)
    confirmation = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})["confirmation"]
    assert confirmation["engine"] == "glm_ocr_local" and confirmation["estimatedUsd"] == 0
    assert confirmation["lines"][1] == "GLM-OCR on this computer reads it: free."
    set_config(root, {("ingest", "pdf", "glm_ocr", "local_url"): "http://gpu-box.invalid:5002/glmocr/parse"})
    ctx.reload(maintenance=False)
    confirmation = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})["confirmation"]
    assert confirmation["lines"][1] == "Your GLM-OCR server reads it: free."


def test_f7_doctor_fix_state_finishes_a_carry_over_left_owed(card_book, monkeypatch):
    """The same owed carry-over, finished by ``doctor --fix-state`` (and one an
    interrupted worker left: the job failed after its reading completed)."""

    from learnloop.content.pipeline import reread
    from learnloop.ops.doctor import run_doctor

    ctx, source_id, clock = card_book["ctx"], card_book["source_id"], card_book["clock"]
    repo = ctx.repository
    first = resolve_extraction_id(repo, source_id)
    repo.upsert_reader_section_progress(extraction_id=first, section_id="u1", spans_seen=4, span_count=4,
                                        completed=True)
    original = reread.carry_progress

    def interrupted(*args, **kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(reread, "carry_progress", interrupted)
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    (job,) = [job for job in repo.ingest_jobs_for_batch(out["batchId"]) if job["job_type"] == "import"]
    new = resolve_extraction_id(repo, source_id)
    assert job["payload"]["carry_over_for"] == new and "carry_over_done" not in job["payload"]
    with repo.connection() as connection:  # as an expired lease leaves it
        connection.execute("UPDATE ingest_jobs SET status = 'failed' WHERE id = ?", (job["id"],))
        connection.commit()
    (issue,) = [issue for issue in run_doctor(card_book["root"]).issues
                if issue.code == "source:reread_carry_incomplete"]
    assert issue.severity == "warning" and "--fix-state" in issue.message
    monkeypatch.setattr(reread, "carry_progress", original)
    run_doctor(card_book["root"], fix_state=True)
    assert [row["section_id"] for row in repo.reader_section_progress_for(new) if row["completed_at"]] == ["h1"]
    assert not any(issue.code == "source:reread_carry_incomplete" for issue in run_doctor(card_book["root"]).issues)
    assert reread.carry_owed(repo, source_id) is None


# --- Codex re-review of the stage (2026-10-14): reproductions, written to fail first ---


def _exam_reading_split_units() -> DocumentIR:
    """The re-read reuses ``u1`` for Theory, keeps an "Exam" heading in ``u2``
    and puts the exam question in a unit of its own (Codex re-review F1)."""

    return _ir({"y0": ("SectionHeader", 2, ["Theory"], "Theory"), "y1": ("Text", 2, ["Theory"], _THEORY),
                "y2": ("SectionHeader", 1, ["Exam"], "Exam"),
                "y3": ("SectionHeader", 1, ["Exam", "Questions"], "Questions"),
                "y4": ("Text", 1, ["Exam", "Questions"], _EXAM_Q)},
               [("u1", "Theory", "sha256:theory-b", ["y0", "y1"]), ("u2", "Exam", "sha256:exam-b", ["y2"]),
                ("u3", "Questions", "sha256:questions-b", ["y3", "y4"])],
               extractor="glm_ocr")


def test_rereview_f1_a_reused_unit_id_with_the_question_moved_out_keeps_it_withheld(exam_book):
    """F1 (re-review): A's ``u1`` is Exam. B reuses ``u1`` for Theory, keeps an
    "Exam" heading in ``u2`` and moves the question into a Questions unit. A
    matching label is not the same material: the question stays withheld in B."""

    from learnloop.content.sources.exam_material import exam_material, role_material

    repo, clock = exam_book["repo"], exam_book["clock"]
    sets = _exam_sets()
    _persist(repo, _exam_reading_split_units(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    after = exam_material(sets, repo)
    assert after.covers("extXA", "x1"), "the exam question on the reading the scope was made on"
    assert after.covers("extXB", "y4"), "the same exam question on the re-read, in another unit"
    teaching = role_material(sets, repo, lambda role: role == "exam")
    assert teaching.covers("extXB", "y4")


@pytest.mark.parametrize("carried", [True, False], ids=["carried", "not_carried"])
def test_rereview_f1_a_held_out_mark_follows_its_question_not_its_label(exam_book, carried):
    """The same re-read against a held-out mark (rule 3): A marks ``u1`` (Exam)
    held out; B keeps an "Exam" heading and moves the question into a unit of
    its own. The mark never moves to B, carried over or not (protection
    redesign): B is held back whole until the owner marks it, and the
    owner's marking, pre-filled, holds out the unit the question moved to
    while B's Theory becomes usable."""

    from learnloop.content.pipeline.reread import carry_over
    from learnloop.content.sources.exam_material import exam_material

    repo, clock = exam_book["repo"], exam_book["clock"]
    repo.upsert_unit_selection(extraction_id="extXA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1", "u2"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extXA", "rev_x"))
    _persist(repo, _exam_reading_split_units(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    if carried:
        carry_over(repo, "extXB", clock=clock)
        assert repo.get_unit_selection("extXB")["exam_use_modes"] == {}
    exam = exam_material([], repo)
    assert exam.is_held_out("extXA", "x1") and not exam.covers("extXA", "x3")
    assert "extXB" in exam.held_out.extractions, "the re-read is held back whole until it is marked"
    marked = _confirm_marking([], repo, "src_x", clock=clock)
    assert marked is not None and "u3" in marked["held_out_unit_ids"]
    exam = exam_material([], repo)
    assert exam.is_held_out("extXB", "y4"), "the held-out question, in the unit it moved to"
    assert not exam.covers("extXB", "y1"), "B's Theory is usable once B is marked"


@pytest.fixture
def paper_book(tmp_path):
    """An exam paper registered and not yet read (each test reads it twice)."""

    from tests.helpers import create_basic_vault
    from tests.test_source_inventory import _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src_x", revision_id="rev_x")
    repo.set_source_current_revision("src_x", "rev_x")
    return {"repo": repo, "clock": _clock(), "root": paths.root}


_Q1 = "Question 1: prove that the trace of a matrix is a linear map."
_Q2 = "Question 2: prove that the determinant of a product is the product of the determinants."


def _paper(texts, extractor: str) -> DocumentIR:
    return _ir(texts, [("u1", "Exam", f"sha256:paper-{extractor}", list(texts))], extractor=extractor)


def test_rereview_f2_a_held_out_passage_split_in_two_protects_both_halves(paper_book):
    """F2 (re-review): A's held-out ``x1`` holds two questions; B splits them
    into ``y1`` and ``y2``. The alias names only ``y1`` (the same place, other
    words); both halves stay held out."""

    from learnloop.content.sources import span_aliases
    from learnloop.content.sources.exam_material import held_out_partition

    repo, clock = paper_book["repo"], paper_book["clock"]
    _persist(repo, _paper({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}")},
                          "marker"), revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()
    sets = _exam_sets(default_role="exam", scope=())
    _held_out_inventory(repo, extraction_id="extPA", unit_id="u1", span_ids=["x1"])
    _persist(repo, _paper({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], _Q1),
                           "y2": ("Text", 1, ["Exam"], _Q2)}, "glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)
    landed = span_aliases.resolve_span(repo, "extPA", "x1", "extPB")
    assert (landed.span_id, landed.status) == ("y1", "needs_reanchor")
    held = held_out_partition(sets, repo)
    assert held.covers("extPB", "y1") and held.covers("extPB", "y2")


def test_rereview_f2_a_half_moved_past_another_passage_withholds_the_reading(paper_book):
    """A half that lands beyond the next passage matched word for word can't
    be followed: the whole re-read is held out (fail closed)."""

    from learnloop.content.sources.exam_material import held_out_partition

    repo, clock = paper_book["repo"], paper_book["clock"]
    notes = "Notes: show every step of your working."
    _persist(repo, _paper({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}"),
                           "x2": ("Text", 1, ["Exam"], notes)}, "marker"),
             revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()
    sets = _exam_sets(default_role="exam", scope=())
    _held_out_inventory(repo, extraction_id="extPA", unit_id="u1", span_ids=["x1"])
    _persist(repo, _paper({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], _Q1),
                           "y2": ("Text", 1, ["Exam"], notes), "y3": ("Text", 1, ["Exam"], _Q2)}, "glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)
    held = held_out_partition(sets, repo)
    assert "extPB" in held.extractions


def test_rereview_f10_a_place_is_translated_onto_the_reading_the_reader_has_open(studied):
    """F10 (re-review): the Reader opened B; a third reading C completes before
    it asks where a place from A lands. It names the reading it has open, and
    the place lands there, never on C's span ids applied to B."""

    repo, clock = studied["repo"], studied["clock"]
    _reread(studied)
    clock.advance()
    reading_c = _ir({key.replace("b", "c", 1): value for key, value in _B_TEXT.items()}, [
        ("k1", "1 Vectors", "sha256:c-k1", ["c0", "c1", "c2", "c3"]),
        ("k2", "2 Spans", "sha256:c-k2", ["c4", "c5", "c6"]),
        ("k3", "3 Exam review", "sha256:u3", ["c7", "c8"]),
    ], extractor="pypdf")
    _persist(repo, reading_c, revision_id="rev1", extraction_id="extC", clock=clock, page_selection=list(range(13, 39)))
    assert resolve_extraction_id(repo, "src1") == "extC"
    ctx = SidecarContext()
    ctx.load(studied["root"])
    on_open = call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extA", "spanId": EXACT,
                                               "toExtractionId": "extB"})
    assert (on_open["extractionId"], on_open["spanId"], on_open["status"]) == ("extB", "b1", "current")
    latest = call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extA", "spanId": EXACT})
    assert (latest["extractionId"], latest["spanId"]) == ("extC", "c1")
    with pytest.raises(SidecarError):
        call(ctx, "reader.saved_place", {"sourceId": "src1", "extractionId": "extA", "spanId": EXACT,
                                         "toExtractionId": "ext_of_another_book"})


def test_rereview_f1_a_scope_whose_question_the_reread_reworded_withholds_the_reread(exam_book):
    """A scope interpretation that can't be followed onto a re-read (the
    question re-worded, the units in another order) withholds that whole
    re-read: over-protective, never released."""

    from learnloop.content.sources.exam_material import exam_material

    repo, clock = exam_book["repo"], exam_book["clock"]
    reworded = _exam_reading_split_units()
    reworded.blocks[-1] = reworded.blocks[-1].model_copy(update={
        "text": "Exam question: show that each eigenvalue of a self adjoint operator is real.",
        "content_hash": "sha256:reworded"})
    _persist(repo, reworded, revision_id="rev_x", extraction_id="extXB", clock=clock)
    after = exam_material(_exam_sets(), repo)
    assert "extXB" in after.extractions
    assert after.covers("extXA", "x1") and "extXA" not in after.extractions


@pytest.mark.parametrize("carried", [True, False], ids=["carried", "not_carried"])
def test_rereview_f2_a_held_out_unit_split_across_units_protects_both_halves(paper_book, carried):
    """F2 (re-review), rule 3: A marks its unit held out; B splits the unit's
    two-question passage and puts the second question in a unit of its own.
    The mark never moves (protection redesign): B is held back whole until
    the owner marks it, and the pre-filled marking holds out both halves
    while B's appendix becomes usable."""

    from learnloop.content.pipeline.reread import carry_over
    from learnloop.content.sources.exam_material import exam_material

    repo, clock = paper_book["repo"], paper_book["clock"]
    _persist(repo, _ir({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}"),
                        "x2": ("SectionHeader", 2, ["Appendix"], "Appendix"),
                        "x3": ("Text", 2, ["Appendix"], "Appendix: a table of determinants.")},
                       [("u1", "Exam", "sha256:a-exam", ["x0", "x1"]), ("u2", "Appendix", "sha256:a-app", ["x2", "x3"])],
                       extractor="marker"),
             revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()
    repo.upsert_unit_selection(extraction_id="extPA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extPA", "rev_x"))
    split = _ir({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], _Q1),
                 "y2": ("SectionHeader", 1, ["Exam", "Part two"], "Part two"),
                 "y3": ("Text", 1, ["Exam", "Part two"], _Q2),
                 "y4": ("SectionHeader", 2, ["Appendix"], "Appendix"),
                 "y5": ("Text", 2, ["Appendix"], "Appendix: a table of determinants.")},
                [("u1", "Exam", "sha256:b-exam", ["y0", "y1"]), ("u2", "Part two", "sha256:b-two", ["y2", "y3"]),
                 ("u3", "Appendix", "sha256:b-app", ["y4", "y5"])], extractor="glm_ocr")
    _persist(repo, split, revision_id="rev_x", extraction_id="extPB", clock=clock)
    if carried:
        carry_over(repo, "extPB", clock=clock)
        assert repo.get_unit_selection("extPB")["exam_use_modes"] == {}  # marks never move
    exam = exam_material([], repo)
    assert "extPB" in exam.held_out.extractions, "the re-read is held back whole until it is marked"
    _confirm_marking([], repo, "src_x", clock=clock)
    exam = exam_material([], repo)
    assert exam.is_held_out("extPB", "y1") and exam.is_held_out("extPB", "y3"), "both questions on the re-read"
    assert not exam.is_held_out("extPB", "y5"), "the appendix is usable once B is marked"


def test_rereview_f2_a_long_block_between_the_parts_of_a_split_withholds_the_reading(paper_book):
    """Verification skips only short blocks (a heading, a page number): a long
    block between the two questions means the words don't run on, and the
    whole re-read is held out (fail closed)."""

    from learnloop.content.sources.exam_material import exam_material

    repo, clock = paper_book["repo"], paper_book["clock"]
    _persist(repo, _paper({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}")},
                          "marker"), revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()
    repo.upsert_unit_selection(extraction_id="extPA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extPA", "rev_x"))
    inserted = "A paragraph this reading found between the questions, long enough to be a passage of its own."
    _persist(repo, _paper({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], _Q1),
                           "y2": ("Text", 1, ["Exam"], inserted), "y3": ("Text", 1, ["Exam"], _Q2)}, "glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)
    assert "extPB" in exam_material([], repo).held_out.extractions


def test_rereview_f2_a_held_out_passage_merged_with_its_neighbour_holds_out_the_merged_block(paper_book):
    """A merge: B joins A's held-out question and the unprotected line after
    it into one block. That block holds the question's words: held out, with
    the rest of B, until the owner marks B (protection redesign)."""

    from learnloop.content.sources.exam_material import exam_material

    repo, clock = paper_book["repo"], paper_book["clock"]
    notes = "Notes: show every step of your working."
    _persist(repo, _ir({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], _Q1),
                        "x2": ("SectionHeader", 2, ["Notes"], "Notes"), "x3": ("Text", 2, ["Notes"], notes),
                        "x4": ("Text", 2, ["Notes"], "Good luck.")},
                       [("u1", "Exam", "sha256:a-exam", ["x0", "x1"]),
                        ("u2", "Notes", "sha256:a-notes", ["x2", "x3", "x4"])], extractor="marker"),
             revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()
    repo.upsert_unit_selection(extraction_id="extPA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1", "u2"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extPA", "rev_x"))
    _persist(repo, _ir({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], f"{_Q1} Notes"),
                        "y2": ("Text", 2, ["Notes"], notes), "y3": ("Text", 2, ["Notes"], "Good luck.")},
                       [("u1", "Exam", "sha256:b-exam", ["y0"]), ("u2", "Notes", "sha256:b-notes", ["y1", "y2", "y3"])],
                       extractor="glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)
    exam = exam_material([], repo)
    assert "extPB" in exam.held_out.extractions, "the re-read is held back whole until it is marked"
    assert not exam.is_held_out("extPA", "x4"), "A exactly as marked"


# --- Protection redesign (2026-10-15): the final verify's reproductions, fail first -----
#
# Exam and held-out protection never carries to another reading by content,
# alias or label matching. Each scenario below reproduces one of the final
# Codex verify's findings (F1 reopened, F2 reopened, F11); on the carrier
# design (``9b933cc21``) each left an unprotected copy of protected text.
# Now every reading of a protected book with no protection marked on it is
# withheld whole, so no copy anywhere is left unprotected, and the reading
# the protection was marked on stays protected exactly as marked. Only APIs
# both designs have are used here, so the same tests ran against both.


def _unprotected_copies(repo: Repository, material, *needles: str) -> list[tuple[str, str]]:
    """Every block of every extraction holding any of ``needles`` that ``material`` leaves uncovered."""

    from contextlib import closing

    from learnloop.db.connection import connect

    found: list[tuple[str, str]] = []
    with closing(connect(repo.sqlite_path, read_only=True)) as connection:
        for extraction_id, span_id, text in connection.execute(
                "SELECT extraction_id, span_id, text FROM source_document_blocks ORDER BY extraction_id, ordinal"):
            if any(needle in str(text or "") for needle in needles) and not material.covers(str(extraction_id),
                                                                                             str(span_id)):
                found.append((str(extraction_id), str(span_id)))
    return found


def _second_revision(repo: Repository, *, source_id: str = "src_x", revision_id: str = "rev_x2") -> str:
    with repo.connection() as connection:
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
                           (revision_id, source_id, f"sha256:{revision_id}", "2026-10-14T10:00:00Z"))
        connection.commit()
    return revision_id


def _r2_readings(repo: Repository, clock) -> None:
    """Revision R2 of the exam book: its first reading B1 keeps the question
    under "Exam"; its re-read B2 keeps the "Exam" heading and moves the
    question into a "Questions" unit of its own (final verify, F1)."""

    _second_revision(repo)
    _persist(repo, _ir({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], _EXAM_Q),
                        "y2": ("SectionHeader", 2, ["Theory"], "Theory"), "y3": ("Text", 2, ["Theory"], _THEORY)},
                       [("u1", "Exam", "sha256:b1-exam", ["y0", "y1"]),
                        ("u2", "Theory", "sha256:b1-theory", ["y2", "y3"])], extractor="marker"),
             revision_id="rev_x2", extraction_id="extR2B1", clock=clock)
    clock.advance()
    _persist(repo, _ir({"z0": ("SectionHeader", 1, ["Exam"], "Exam"),
                        "z1": ("SectionHeader", 1, ["Exam", "Questions"], "Questions"),
                        "z2": ("Text", 1, ["Exam", "Questions"], _EXAM_Q),
                        "z3": ("SectionHeader", 2, ["Theory"], "Theory"), "z4": ("Text", 2, ["Theory"], _THEORY)},
                       [("u1", "Exam", "sha256:b2-exam", ["z0"]), ("u2", "Questions", "sha256:b2-q", ["z1", "z2"]),
                        ("u3", "Theory", "sha256:b2-theory", ["z3", "z4"])], extractor="glm_ocr"),
             revision_id="rev_x2", extraction_id="extR2B2", clock=clock)


def test_redesign_f1_a_moved_question_on_a_new_revisions_reread_is_never_unprotected(exam_book):
    """Final verify F1 (source-set scope): the scope pins R1 and names A's
    Exam unit. R2's B1 keeps the question under "Exam"; B2 moves it into a
    Questions unit. The carrier protected B2's heading only. Now no copy of
    the question is unprotected anywhere, and A is protected exactly as
    marked (its Theory stays usable)."""

    from learnloop.content.sources.exam_material import exam_material

    repo, clock = exam_book["repo"], exam_book["clock"]
    _r2_readings(repo, clock)
    material = exam_material(_exam_sets(), repo)
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []
    assert {"extR2B1", "extR2B2"} <= material.held_out.extractions, "R2's readings are withheld whole"
    assert material.covers("extXA", "x1") and not material.covers("extXA", "x3"), "A exactly as marked"


def test_redesign_f1_a_moved_question_under_a_held_out_mark_is_never_unprotected(exam_book):
    """Final verify F1, the held-out variant: A marks its Exam unit held out.
    The carrier held out B2's "Exam" heading only. Now no copy of the question
    is outside the held-out partition, and A's Theory is not held out."""

    from learnloop.content.sources.exam_material import exam_material, held_out_partition

    repo, clock = exam_book["repo"], exam_book["clock"]
    repo.upsert_unit_selection(extraction_id="extXA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1", "u2"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extXA", "rev_x"))
    _r2_readings(repo, clock)
    held = held_out_partition([], repo)
    assert _unprotected_copies(repo, held, _EXAM_Q) == []
    assert _unprotected_copies(repo, exam_material([], repo).held_out, _EXAM_Q) == []
    assert held.covers("extXA", "x1") and not held.covers("extXA", "x3"), "A exactly as marked"


def _paper_a(repo: Repository, clock) -> None:
    """Reading A of the exam paper: unit u1 "Exam" holds both questions in one
    block (x1); u2 is an appendix."""

    _persist(repo, _ir({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}"),
                        "x2": ("SectionHeader", 2, ["Appendix"], "Appendix"),
                        "x3": ("Text", 2, ["Appendix"], "Appendix: a table of determinants.")},
                       [("u1", "Exam", "sha256:a-exam", ["x0", "x1"]),
                        ("u2", "Appendix", "sha256:a-app", ["x2", "x3"])], extractor="marker"),
             revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()


def _paper_b_with_duplicates(repo: Repository, clock) -> None:
    """The re-read B: an exact copy of A's question block (y1) and, as
    duplicated extraction output can produce, split copies of the same two
    questions (y3, y4) after a page heading (final verify, F2)."""

    _persist(repo, _ir({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}"),
                        "y2": ("SectionHeader", 1, ["Exam (continued)"], "Exam (continued)"),
                        "y3": ("Text", 1, ["Exam (continued)"], _Q1), "y4": ("Text", 1, ["Exam (continued)"], _Q2),
                        "y5": ("SectionHeader", 2, ["Appendix"], "Appendix"),
                        "y6": ("Text", 2, ["Appendix"], "Appendix: a table of determinants.")},
                       [("u1", "Exam", "sha256:b-exam", ["y0", "y1"]),
                        ("u2", "Exam (continued)", "sha256:b-cont", ["y2", "y3", "y4"]),
                        ("u3", "Appendix", "sha256:b-app", ["y5", "y6"])], extractor="glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)


@pytest.mark.parametrize("protection", ["held_out_mark", "exam_scope"])
def test_redesign_f2_duplicate_and_fragment_copies_are_never_unprotected(paper_book, protection):
    """Final verify F2: one exact alias (A's x1 to B's y1) counted as complete
    protection, so the split copies y3 and y4 were released, under a held-out
    mark and under a source-set exam scope alike. Now B is withheld whole."""

    from learnloop.content.sources.exam_material import exam_material, held_out_partition

    repo, clock = paper_book["repo"], paper_book["clock"]
    _paper_a(repo, clock)
    sets: list = []
    if protection == "held_out_mark":
        repo.upsert_unit_selection(extraction_id="extPA", source_id="src_x", revision_id="rev_x",
                                   selected_unit_ids=["u1", "u2"], exam_use_modes={"u1": "held_out_evaluation"},
                                   exam_paper_metadata=_made_on("extPA", "rev_x"))
    else:
        sets = _exam_sets(reading="extPA")
    _paper_b_with_duplicates(repo, clock)
    material = exam_material(sets, repo)
    protected = material.held_out if protection == "held_out_mark" else material.material
    assert _unprotected_copies(repo, protected, _Q1, _Q2) == []
    if protection == "held_out_mark":
        assert _unprotected_copies(repo, held_out_partition(sets, repo), _Q1, _Q2) == []
    assert not material.covers("extPA", "x3"), "A's appendix stays usable: A exactly as marked"


_PLUS, _MINUS, _TIMES = "Solve x+1=2.", "Solve x-1=2.", "Solve x*1=2."
_NOTES = "Notes: show every step of your working, and state each rule you use."


def test_redesign_f11_operators_are_never_erased_into_a_release(paper_book):
    """Final verify F11: A holds out "Solve x+1=2. Solve x-1=2."; its "Solve
    x*1=2." is not held out. B re-segments: "Solve x+1=2. Solve x*1=2.", the
    unchanged notes, then "Solve x-1=2.". Both combined passages normalised
    to the same letters and digits, so the carrier verified b1 and released
    b3: the Reader's refusal predicate returned nothing for it and an item
    made from it was not held out. Now B is withheld whole."""

    from types import SimpleNamespace

    from learnloop.content.sources.exam_material import (
        held_out_among,
        held_out_items,
        held_out_material,
        held_out_partition,
    )

    repo, clock = paper_book["repo"], paper_book["clock"]
    _persist(repo, _ir({"a1": ("Text", 1, ["Problems"], f"{_PLUS} {_MINUS}"), "a2": ("Text", 1, ["Notes"], _NOTES),
                        "a3": ("Text", 1, ["More"], _TIMES)},
                       [("u1", "Problems", "sha256:a-p", ["a1"]), ("u2", "Notes", "sha256:a-n", ["a2"]),
                        ("u3", "More", "sha256:a-m", ["a3"])], extractor="marker"),
             revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()
    repo.upsert_unit_selection(extraction_id="extPA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1", "u2", "u3"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extPA", "rev_x"))
    _persist(repo, _ir({"b1": ("Text", 1, ["Problems"], f"{_PLUS} {_TIMES}"), "b2": ("Text", 1, ["Notes"], _NOTES),
                        "b3": ("Text", 1, ["More"], _MINUS)},
                       [("u1", "Problems", "sha256:b-p", ["b1"]), ("u2", "Notes", "sha256:b-n", ["b2"]),
                        ("u3", "More", "sha256:b-m", ["b3"])], extractor="glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)

    held = held_out_partition([], repo)
    assert _unprotected_copies(repo, held, _PLUS, _MINUS) == []
    assert held_out_among(held_out_material([], repo), "extPB", ["b3"]) == ["b3"], "the Reader refuses b3"
    item = SimpleNamespace(id="pi_from_b3", provenance=None,
                           canonical_exercise=SimpleNamespace(extraction_id="extPB", span_ids=["b3"]))
    vault = SimpleNamespace(source_sets=[], practice_items={"pi_from_b3": item})
    assert held_out_items(vault, repo) == frozenset({"pi_from_b3"}), "an item made from b3 is held out"
    assert not held.covers("extPA", "a3"), "A's unprotected question stays usable: A exactly as marked"


# --- Protection redesign: marking a reading, and what is left alone ---------------------


def test_redesign_marking_the_new_reading_makes_it_usable(studied):
    """The held-back re-read becomes usable only once the owner marks it:
    the card says why in plain words and offers the one action, doctor
    names the reading, the marking holds out what the suggestion found (the
    exam review section) and nothing else, and the first reading keeps its
    own mark exactly."""

    from learnloop.content.pipeline import exam_marking
    from learnloop.content.sources.exam_material import (
        HELD_BACK_REFUSAL,
        HELD_OUT_REFUSAL,
        PROTECTION_MARK_KEY,
        exam_material,
        held_out_refusal,
        source_marks,
    )

    repo, vault, root, clock = studied["repo"], studied["vault"], studied["root"], studied["clock"]
    assert source_marks(vault, repo)["src1"].unmarked == ()  # read once: its reading is the marked one
    _reread(studied)
    assert exam_marking.held_back_reading(vault, repo, "src1") == "extB"
    line = core.source_status_line(repo, vault, "src1")
    assert line == {"text": exam_marking.HELD_BACK_LINE, "tone": "problem",
                    "action": {"kind": "mark_exam_material", "label": "Mark exam material on this reading"},
                    "details": exam_marking.HELD_BACK_DETAILS}
    (issue,) = _codes(root)["source:reading_held_back"]
    assert issue.severity == "warning" and issue.details["extraction_id"] == "extB"
    assert "Mark exam material on this reading" in issue.message
    material = exam_material(vault, repo)
    assert held_out_refusal(material.held_out, "extB") == HELD_BACK_REFUSAL
    assert held_out_refusal(material.held_out, "extA") == HELD_OUT_REFUSAL

    plan = exam_marking.mark_plan(vault, repo, "src1")
    assert plan["extraction_id"] == "extB" and plan["held_out_unit_ids"] == ["h3"]
    assert plan["lines"][0] == "Held out as exam material: 3 Exam review."
    assert exam_material(vault, repo).held_out.covers("extB")  # the plan wrote nothing

    marked = _confirm_marking(vault, repo, "src1", clock=clock)
    assert marked == {"extraction_id": "extB", "held_out_unit_ids": ["h3"], "from_extraction_ids": ["extA"]}
    selection = repo.get_unit_selection("extB")
    assert selection["exam_use_modes"] == {"h3": "held_out_evaluation"}
    assert selection["selected_unit_ids"] == ["h1", "h2", "h3"]  # the carried study map is kept
    assert selection["exam_paper_metadata"][PROTECTION_MARK_KEY]["from"] == ["extA"]
    material = exam_material(vault, repo)
    assert "extB" not in material.material.extractions
    assert material.is_held_out("extB", "b7") and material.is_held_out("extB", "b8")
    assert not material.covers("extB", "b1") and not material.covers("extB", "b5")
    assert material.is_held_out("extA", "a7") and not material.covers("extA", "a1"), "A exactly as marked"
    assert exam_marking.held_back_reading(vault, repo, "src1") is None
    assert "source:reading_held_back" not in _codes(root)
    after = core.source_status_line(repo, vault, "src1")
    assert after is None or after["text"] != exam_marking.HELD_BACK_LINE
    assert exam_marking.mark_plan(vault, repo, "src1") is None  # nothing left to mark
    with pytest.raises(exam_marking.StaleMarkConfirmation):
        exam_marking.mark_exam_material(vault, repo, "src1", extraction_id="extB", proposal_hash=plan["proposal_hash"],
                                        clock=clock)


def test_redesign_a_study_map_save_keeps_the_owners_marks(studied):
    """A study-map save that names no exam use modes (the desktop's, the CLI's)
    keeps a reading's marks: it never releases a held-out unit or holds a
    marked reading back again."""

    from learnloop.content.pipeline.exam_marking import held_back_reading
    from learnloop.content.sources.exam_material import exam_material
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    repo, vault, clock = studied["repo"], studied["vault"], studied["clock"]
    save_unit_selection(repo, "extA", ["u1", "u2"])
    assert exam_material(vault, repo).is_held_out("extA", "a7"), "A's mark survives a study-map save"
    _reread(studied)
    _confirm_marking(vault, repo, "src1", clock=clock)
    save_unit_selection(repo, "extB", ["h1"])
    assert held_back_reading(vault, repo, "src1") is None
    assert exam_material(vault, repo).is_held_out("extB", "b8")
    save_unit_selection(repo, "extB", ["h1"], exam_use_modes={})  # an explicit change is the owner's
    assert held_back_reading(vault, repo, "src1") is None  # the owner's mark still marks it
    assert not exam_material(vault, repo).covers("extB", "b8")


def test_redesign_an_unprotected_book_is_unaffected(exam_book):
    """A book with no exam scope, held-out mark or held-out signal is read
    again with nothing withheld, and a protected book beside it changes
    nothing for it."""

    from learnloop.content.pipeline import exam_marking
    from learnloop.content.sources.exam_material import exam_material, held_out_partition, source_marks

    repo, clock = exam_book["repo"], exam_book["clock"]
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    assert source_marks([], repo) == {}
    material = exam_material([], repo)
    assert material.material.empty and held_out_partition([], repo).empty
    assert exam_marking.held_back_reading([], repo, "src_x") is None
    assert exam_marking.mark_plan([], repo, "src_x") is None

    # Another book with a held-out mark and a re-read: only it is held back.
    from tests.test_source_inventory import _register_revision

    _register_revision(repo, source_id="src_p", revision_id="rev_p")
    repo.set_source_current_revision("src_p", "rev_p")
    _persist(repo, _paper({"p0": ("SectionHeader", 1, ["Exam"], "Exam"), "p1": ("Text", 1, ["Exam"], _Q1)}, "marker"),
             revision_id="rev_p", extraction_id="extP1", clock=clock)
    clock.advance()
    repo.upsert_unit_selection(extraction_id="extP1", source_id="src_p", revision_id="rev_p",
                               selected_unit_ids=["u1"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extP1", "rev_p"))
    _persist(repo, _paper({"q0": ("SectionHeader", 1, ["Exam"], "Exam"), "q1": ("Text", 1, ["Exam"], _Q1)}, "glm_ocr"),
             revision_id="rev_p", extraction_id="extP2", clock=clock)
    material = exam_material([], repo)
    assert material.held_out.extractions == {"extP2"} and material.is_held_out("extP1", "p1")
    assert not {"extXA", "extXB"} & material.material.touched
    assert set(source_marks([], repo)) == {"src_p"}


def test_redesign_a_reading_of_a_new_revision_is_held_back_until_marked(exam_book):
    """Revisions: the scope pins R1; R2's readings are held back whole. Once
    R2 is the book's current revision, the card marks its current reading,
    from the scope's reading's exam unit; R2's older reading stays held back
    (doctor counts it)."""

    from learnloop.content.pipeline import exam_marking
    from learnloop.content.sources.exam_material import exam_material

    repo, clock, root = exam_book["repo"], exam_book["clock"], exam_book["root"]
    sets = _exam_sets()
    _r2_readings(repo, clock)
    assert exam_marking.held_back_reading(sets, repo, "src_x") is None  # the Reader opens R1's reading
    repo.set_source_current_revision("src_x", "rev_x2")
    assert exam_marking.held_back_reading(sets, repo, "src_x") == "extR2B2"
    assert exam_marking.held_back_readings(sets, repo) == [
        {"source_id": "src_x", "extraction_id": "extR2B2", "older": ["extR2B1"], "ambiguous": []}]
    marked = _confirm_marking(sets, repo, "src_x", clock=clock)
    assert marked["from_extraction_ids"] == ["extXA"] and "u2" in marked["held_out_unit_ids"]
    material = exam_material(sets, repo)
    assert material.is_held_out("extR2B2", "z2"), "the moved question, held out on the marked reading"
    assert not material.covers("extR2B2", "z4"), "R2's Theory is usable once marked"
    assert "extR2B1" in material.held_out.extractions, "R2's other reading is still held back"
    assert material.covers("extXA", "x1") and not material.covers("extXA", "x3"), "A exactly as marked"
    assert _unprotected_copies(repo, material.material, _EXAM_Q) == []
    del root


def test_redesign_a_signal_a_build_makes_on_a_held_back_reading_never_releases_it(exam_book):
    """An exam paper whose first reading carries the owner's held-out mark:
    an inventory a build makes on the held-back re-read does not mark it
    (only the owner's mark does), so the re-read stays held back whole. A
    paper with signals and no owner's mark is marked where its signals were
    made."""

    from learnloop.content.sources.exam_material import exam_material

    repo, clock = exam_book["repo"], exam_book["clock"]
    sets = _exam_sets(default_role="exam", scope=())
    _held_out_inventory(repo, extraction_id="extXA", unit_id="u1", span_ids=["x1"])
    _persist(repo, _exam_reading_b(), revision_id="rev_x", extraction_id="extXB", clock=clock)
    material = exam_material(sets, repo)
    assert material.is_held_out("extXA", "x1") and not material.is_held_out("extXA", "x3")
    assert "extXB" in material.held_out.extractions
    # The re-read gets an inventory of its own (a build ran on it): with no
    # owner's mark anywhere, its own signals mark it.
    _held_out_inventory(repo, extraction_id="extXB", unit_id="u2", span_ids=["y3"])
    material = exam_material(sets, repo)
    assert "extXB" not in material.held_out.extractions and material.is_held_out("extXB", "y3")
    # With the owner's held-out mark on the first reading, a signal never marks the re-read.
    repo.upsert_unit_selection(extraction_id="extXA", source_id="src_x", revision_id="rev_x",
                               selected_unit_ids=["u1", "u2"], exam_use_modes={"u1": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extXA", "rev_x"))
    material = exam_material(sets, repo)
    assert "extXB" in material.held_out.extractions
    assert material.is_held_out("extXA", "x1") and not material.is_held_out("extXA", "x3")


def test_redesign_a_refresh_keeps_an_exam_scoped_member_on_its_revision(tmp_path):
    """Revision refresh: a member whose scope names exam units by unit id is
    never advanced to the new revision (its unit ids would name other units
    there); the new revision's reading is held back until it is marked."""

    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.content.pipeline.revision_refresh import refresh_revision
    from learnloop.content.sources.exam_material import exam_material
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set
    from tests.test_revision_refresh import _member_revision, _register_new_revision
    from tests.test_source_set_synthesis import _setup

    clock = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
    root, repo = _setup(tmp_path, with_exam=False)
    source_set = next(s for s in load_vault(root).source_sets if s.id == "set_la")
    members = [member.model_dump(mode="json") for member in source_set.members]
    for member in members:
        if member["source_id"] == "src_text":
            member["scope"] = [{"unit_id": "chapter_symmetry", "role_override": "exam"}]
    upsert_source_set(root, {"id": source_set.id, "subject_id": source_set.subject_id, "title": source_set.title,
                             "members": members}, clock=clock)
    _register_new_revision(repo, changed=False)
    result = refresh_revision(root, "set_la", source_id="src_text", old_revision_id="rev_text",
                              new_revision_id="rev_text_v2", new_extraction_id="ext_text_v2",
                              confirm=True, run_append=False, repository=repo, clock=clock)
    assert result.membership_advanced is False and result.kept_pinned == ["src_text"]
    assert result.as_dict()["kept_pinned"] == ["src_text"]
    assert _member_revision(root, "src_text") == "rev_text"
    assert "ext_text_v2" in exam_material(load_vault(root), repo).held_out.extractions
