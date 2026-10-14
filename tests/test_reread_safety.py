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
                               selected_unit_ids=["u1", "u2", "u3"], exam_use_modes={"u3": "held_out_evaluation"})
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
    # Held-out exam material is never released by a re-read.
    assert selection["exam_use_modes"] == {"h3": "held_out_evaluation"}


def test_held_out_material_stays_withheld_on_the_new_reading(studied):
    from learnloop.content.sources.exam_material import exam_material

    repo = studied["repo"]
    _reread(studied)
    exam = exam_material(studied["vault"], repo)
    assert exam.is_held_out("extB", "b8") and exam.is_held_out("extA", "a7")
    assert not exam.is_held_out("extB", "b1")


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
    assert selection["exam_use_modes"] == {"c3": "held_out_evaluation"}


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
                                         exam_use_modes={"u3": "held_out_evaluation"})
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
    assert selection["exam_use_modes"] == {"h3": "held_out_evaluation"}
    assert [row["section_id"] for row in ctx.repository.reader_section_progress_for(new) if row["completed_at"]] == ["h1"]


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
