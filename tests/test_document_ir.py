"""Document IR types, hashing, block roles, and repair composition (ING §2.2/§2.3/§2.6)."""

from __future__ import annotations

from learnloop.ingest.block_roles import classify_block_role
from learnloop.ingest.extractors.marker import chunk_output_to_ir
from learnloop.ingest.hashing import (
    extraction_request_hash,
    extraction_result_hash,
    normalize_semantic_text,
    semantic_hash,
)
from learnloop.ingest.ir import (
    IR_SCHEMA_VERSION,
    DocumentBlock,
    DocumentIR,
    block_content_hash,
    compose_extraction_runs,
)


def _block(span_id, text, *, block_type="Text", page=None, ordinal=1, section_path=None):
    return DocumentBlock.build(
        span_id=span_id,
        block_type=block_type,
        text=text,
        ordinal=ordinal,
        page=page,
        section_path=section_path or [],
    )


def test_ir_declares_schema_version():
    assert IR_SCHEMA_VERSION
    ir = DocumentIR(extractor="pypdf", extractor_version="1")
    assert ir.ir_schema_version == IR_SCHEMA_VERSION


def test_document_ir_round_trip():
    ir = DocumentIR(
        extractor="marker",
        extractor_version="1.9.0",
        blocks=[_block("s1", "hello world", page=0, ordinal=1)],
    )
    restored = DocumentIR.model_validate_json(ir.model_dump_json())
    assert restored == ir
    assert restored.blocks[0].content_hash == block_content_hash("hello world")


class _FakeBlockId:
    """Stands in for marker's BlockId, which is not a str but stringifies."""

    def __str__(self) -> str:
        return "/page/0/Figure/9"

    __hash__ = object.__hash__


def test_marker_image_keys_coerced_to_string_asset_ids():
    # Real-source regression: marker keys block images by BlockId objects;
    # DocumentAsset.id and asset_ids_json need plain strings.
    ir = chunk_output_to_ir(
        blocks=[
            {
                "id": "b1",
                "block_type": "Figure",
                "html": "<p>figure</p>",
                "page": 0,
                "bbox": [0, 0, 1, 1],
                "polygon": None,
                "section_hierarchy": {1: "Figures"},
                "images": {_FakeBlockId(): b"png-bytes"},
            }
        ],
        metadata={},
        extractor_version="test",
    )
    assert ir.assets[0].id == "/page/0/Figure/9"
    assert ir.blocks[0].asset_ids == ["/page/0/Figure/9"]


def _text_of(html, *, block_type="Text"):
    ir = chunk_output_to_ir(
        blocks=[{"id": "b1", "block_type": block_type, "html": html, "page": 0, "bbox": None, "polygon": None, "section_hierarchy": None, "images": None}],
        metadata={},
        extractor_version="test",
    )
    return ir.blocks[0].text


def test_marker_inline_math_becomes_dollar_delimited():
    # Regression: tag stripping used to leave bare LaTeX (`A \cup B`) that no
    # renderer can recognize as math (probability_v2 audit, 2026-07-21).
    text = _text_of("<p>the union <math display='inline'>A \\cup B</math> is the event</p>")
    assert text == "the union $A \\cup B$ is the event"


def test_marker_block_math_becomes_display_delimited():
    text = _text_of('<math display="block">Av = \\lambda v</math>', block_type="Equation")
    assert text == "$$Av = \\lambda v$$"


def test_marker_math_entities_unescaped_inside_delimiters():
    text = _text_of("<p><math display='inline'>a &lt; b &amp; c</math></p>")
    assert text == "$a < b & c$"


def test_marker_bare_and_empty_math_tags():
    # No display attribute → inline; empty math bodies must not emit "$$".
    assert _text_of("<p>x <math>y</math> z</p>") == "x $y$ z"
    assert _text_of("<p>x <math display='inline'> </math> z</p>") == "x z"


def test_marker_block_page_derived_from_block_id():
    # Real-source regression: marker emitted internal page ids (108, 358, ...)
    # in FlatBlockOutput.page on a pypdf-sliced PDF while block ids kept the
    # true 0-based page index; units then swept every block into the last one.
    ir = chunk_output_to_ir(
        blocks=[
            {"id": "/page/0/Text/1", "block_type": "Text", "html": "<p>alpha</p>", "page": 140, "bbox": None, "polygon": None, "section_hierarchy": {1: "A"}, "images": None},
            {"id": "/page/1/Text/1", "block_type": "Text", "html": "<p>beta</p>", "page": 167, "bbox": None, "polygon": None, "section_hierarchy": {1: "B"}, "images": None},
        ],
        metadata={"table_of_contents": [
            {"title": "A", "heading_level": 1, "page_id": 0},
            {"title": "B", "heading_level": 1, "page_id": 1},
        ]},
        extractor_version="test",
    )
    assert [block.page for block in ir.blocks] == [0, 1]
    assert [unit.span_ids for unit in ir.units] == [["s1"], ["s2"]]
    # No id → the page field is still honored.
    fallback = chunk_output_to_ir(
        blocks=[{"id": None, "block_type": "Text", "html": "<p>x</p>", "page": 3, "bbox": None, "polygon": None, "section_hierarchy": None, "images": None}],
        metadata={},
        extractor_version="test",
    )
    assert fallback.blocks[0].page == 3


def _chunk(page, text, ordinal=1):
    return {
        "id": f"/page/{page}/Text/{ordinal}", "block_type": "Text", "html": f"<p>{text}</p>",
        "page": page, "bbox": None, "polygon": None, "section_hierarchy": None, "images": None,
    }


def test_embedded_outline_preferred_over_detected_toc():
    """A PDF's bookmark tree (author-curated) beats marker's layout-detected
    ToC for unit derivation."""

    ir = chunk_output_to_ir(
        blocks=[_chunk(0, "alpha"), _chunk(1, "beta"), _chunk(2, "gamma")],
        metadata={"table_of_contents": [
            {"title": "1A and", "heading_level": 1, "page_id": 0},
            {"title": "Complex Numbers", "heading_level": 1, "page_id": 1},
        ]},
        extractor_version="test",
        embedded_outline=[
            {"title": "Chapter 1 Vector Spaces", "heading_level": 1, "page_id": 0},
            {"title": "1A Complex Numbers", "heading_level": 2, "page_id": 1},
        ],
    )
    assert [unit.label for unit in ir.units] == ["Chapter 1 Vector Spaces", "1A Complex Numbers"]
    assert ir.units[0].locator["scheme"] == "pdf_outline"
    assert ir.units[1].parent_unit_id == ir.units[0].unit_id
    # Chapter spans its own page up to the next entry; the subsection runs to the end.
    assert ir.units[0].span_ids == ["s1"]
    assert ir.units[1].span_ids == ["s2", "s3"]


def test_single_entry_outline_falls_back_to_detected_toc():
    """A lone bookmark ("Cover") is no structure — the detected ToC still wins."""

    ir = chunk_output_to_ir(
        blocks=[_chunk(0, "alpha"), _chunk(1, "beta")],
        metadata={"table_of_contents": [
            {"title": "A", "heading_level": 1, "page_id": 0},
            {"title": "B", "heading_level": 1, "page_id": 1},
        ]},
        extractor_version="test",
        embedded_outline=[{"title": "Cover", "heading_level": 1, "page_id": 0}],
    )
    assert [unit.label for unit in ir.units] == ["A", "B"]
    assert ir.units[0].locator["scheme"] == "toc"


def test_units_from_toc_entries_drops_empty_and_reparents():
    """With a page-sliced import, outline entries outside the window drop and
    their children re-parent to the nearest surviving ancestor."""

    from learnloop.ingest.extractors.base import units_from_toc_entries

    blocks = [_block("s1", "body", page=5, ordinal=1)]
    units = units_from_toc_entries(
        [
            {"title": "Front Matter", "heading_level": 1, "page_id": 0},
            {"title": "Chapter 1", "heading_level": 1, "page_id": 4},
            {"title": "1A", "heading_level": 2, "page_id": 5},
        ],
        blocks,
        locator_scheme="pdf_outline",
        drop_empty=True,
    )
    # Front Matter (pages 0-3) holds no extracted blocks and drops; Chapter 1's
    # own page 4 has no blocks either, but its range ends before 1A so it drops
    # too, re-parenting 1A to the root.
    assert [unit.label for unit in units] == ["1A"]
    assert units[0].parent_unit_id is None
    assert units[0].ordinal == 1
    assert units[0].span_ids == ["s1"]


def test_read_embedded_outline_flattens_nested_bookmarks():
    import io

    import pypdf

    from learnloop.ingest.extractors.pypdf import read_embedded_outline

    writer = pypdf.PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=72, height=72)
    chapter = writer.add_outline_item("Chapter 1 Vector Spaces", 0)
    writer.add_outline_item("1A Complex Numbers", 1, parent=chapter)
    writer.add_outline_item("1B Definition of Vector Space", 2, parent=chapter)
    writer.add_outline_item("Chapter 2 Finite-Dimensional Vector Spaces", 3)
    buffer = io.BytesIO()
    writer.write(buffer)

    entries = read_embedded_outline(buffer.getvalue())
    assert entries == [
        {"title": "Chapter 1 Vector Spaces", "heading_level": 1, "page_id": 0},
        {"title": "1A Complex Numbers", "heading_level": 2, "page_id": 1},
        {"title": "1B Definition of Vector Space", "heading_level": 2, "page_id": 2},
        {"title": "Chapter 2 Finite-Dimensional Vector Spaces", "heading_level": 1, "page_id": 3},
    ]
    # No outline → empty, never an error.
    plain = pypdf.PdfWriter()
    plain.add_blank_page(width=72, height=72)
    plain_buffer = io.BytesIO()
    plain.write(plain_buffer)
    assert read_embedded_outline(plain_buffer.getvalue()) == []
    assert read_embedded_outline(b"%PDF-not really") == []


def test_pypdf_extractor_builds_units_from_embedded_outline(monkeypatch):
    import io

    import pypdf

    from learnloop.ingest.extractors.base import ExtractionContext
    from learnloop.ingest.extractors.pypdf import PyPdfDocumentExtractor

    writer = pypdf.PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=72, height=72)
    chapter = writer.add_outline_item("Chapter 1", 0)
    writer.add_outline_item("1A", 1, parent=chapter)
    buffer = io.BytesIO()
    writer.write(buffer)

    monkeypatch.setattr(
        pypdf.PageObject, "extract_text", lambda self, *args, **kwargs: "page body text"
    )
    ir = PyPdfDocumentExtractor().extract(buffer.getvalue(), ExtractionContext(revision_id="rev"))
    assert [unit.label for unit in ir.units] == ["Chapter 1", "1A"]
    assert ir.units[0].locator["scheme"] == "pdf_outline"
    assert ir.units[1].parent_unit_id == ir.units[0].unit_id
    assert ir.units[0].span_ids == ["s1"]        # page 0 until 1A starts
    assert ir.units[1].span_ids == ["s2", "s3"]  # pages 1-2
    assert ir.extractor_version.endswith("+map2")


def test_semantic_hash_stable_under_cosmetic_html_changes():
    # Same normalized text, cosmetically different markup/whitespace → same hash (§2.2).
    plain = [_block("s1", "An eigenvector of A satisfies", ordinal=1)]
    fussy = [
        DocumentBlock.build(
            span_id="s1",
            block_type="Text",
            text="An   eigenvector   of A   satisfies",
            ordinal=1,
        )
    ]
    assert semantic_hash(plain) == semantic_hash(fussy)


def test_semantic_hash_keeps_equation_content_verbatim():
    # Math is kept verbatim: a LaTeX change *does* change the semantic hash (§2.2).
    one = [_block("s1", "$$Av = \\lambda v$$", block_type="Equation", ordinal=1)]
    two = [_block("s1", "$$A v = \\lambda v$$", block_type="Equation", ordinal=1)]
    assert semantic_hash(one) != semantic_hash(two)


def test_semantic_normalization_drops_repeated_headers_and_page_numbers():
    blocks = []
    for page in range(4):
        blocks.append(_block(f"h{page}", "CHAPTER 4  EIGENVALUES", page=page, ordinal=page * 3 + 1))
        blocks.append(_block(f"b{page}", f"Unique body {page}", page=page, ordinal=page * 3 + 2))
        blocks.append(_block(f"n{page}", str(90 + page), page=page, ordinal=page * 3 + 3))
    text = normalize_semantic_text(blocks)
    assert "CHAPTER 4" not in text  # repeated header dropped
    assert "90" not in text and "93" not in text  # bare page numbers dropped
    assert "Unique body 0" in text and "Unique body 3" in text


def test_block_role_classifier_recognizes_structures():
    assert classify_block_role("Text", ["root", "definition-4-2"], "Definition 4.2. A basis is...") == "definition"
    assert classify_block_role("Text", ["root", "exercises"], "1. Compute the SVD.") == "exercise"
    assert classify_block_role("Text", ["root"], "Worked Example 3. Consider...") == "worked_example"
    assert classify_block_role("Equation", [], "$$x=1$$") == "equation"
    assert classify_block_role("Table", [], "a | b") == "table"
    assert classify_block_role("Text", ["root", "intro"], "This chapter covers...") == "ordinary_prose"


def test_request_hash_computable_before_execution_and_versioned():
    base = dict(
        revision_id="rev_1",
        extractor="marker",
        extractor_version="1.9.0",
        config={"force_ocr": False},
        page_selection=None,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    original = extraction_request_hash(package_version="1.9.0", **base)
    upgraded = extraction_request_hash(package_version="2.0.0", **base)
    assert original != upgraded  # a marker upgrade changes the request hash
    # Deterministic and secret-free.
    assert original == extraction_request_hash(package_version="1.9.0", **base)
    with_secret = dict(base)
    with_secret["config"] = {"force_ocr": False, "openai_api_key": "sk-secret"}
    assert extraction_request_hash(package_version="1.9.0", **with_secret) == original


def test_result_hash_depends_on_request_and_ir():
    ir = DocumentIR(extractor="marker", extractor_version="1", blocks=[_block("s1", "x", ordinal=1)])
    other = DocumentIR(extractor="marker", extractor_version="1", blocks=[_block("s1", "y", ordinal=1)])
    assert extraction_result_hash("req", ir) != extraction_result_hash("req", other)
    assert extraction_result_hash("req", ir) != extraction_result_hash("req2", ir)


def test_repair_composition_replaces_only_repaired_pages():
    metadata = {
        "table_of_contents": [
            {"title": "Intro", "heading_level": 1, "page_id": 0},
            {"title": "Details", "heading_level": 1, "page_id": 1},
        ]
    }
    parent = chunk_output_to_ir(
        blocks=[
            {"id": "a", "block_type": "Text", "html": "<p>clean intro</p>", "page": 0, "bbox": [0, 0, 1, 1], "polygon": None, "section_hierarchy": {1: "Intro"}, "images": None},
            {"id": "b", "block_type": "Text", "html": "<p>garbled deta1ls</p>", "page": 1, "bbox": [0, 0, 1, 1], "polygon": None, "section_hierarchy": {1: "Details"}, "images": None},
        ],
        metadata=metadata,
        extractor_version="1",
    )
    repair = chunk_output_to_ir(
        blocks=[
            {"id": "b2", "block_type": "Text", "html": "<p>repaired details</p>", "page": 1, "bbox": [0, 0, 1, 1], "polygon": None, "section_hierarchy": {1: "Details"}, "images": None},
        ],
        metadata={"table_of_contents": [{"title": "Details", "heading_level": 1, "page_id": 1}]},
        extractor_version="1",
    )
    composed = compose_extraction_runs(parent, repair)
    texts = [block.text for block in composed.blocks]
    assert "clean intro" in texts  # untouched page retained
    assert "repaired details" in texts  # repaired page replaced
    assert "garbled deta1ls" not in texts
    # Composed view is itself a valid single run: sequential span ids.
    assert [block.span_id for block in composed.blocks] == ["s1", "s2"]

    parent_intro_hash = next(u.semantic_hash for u in parent.units if u.label == "Intro")
    composed_intro_hash = next(u.semantic_hash for u in composed.units if u.label == "Intro")
    assert parent_intro_hash == composed_intro_hash  # unaffected unit reusable
