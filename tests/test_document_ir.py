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
