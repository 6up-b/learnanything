"""What other test files use from ``tests/test_reread_safety_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

import pytest

from learnloop.content.sources import exam_material as EM
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO
from tests.mcp_world import LO, build_world, hold_att_held, no_model_calls
from tests.practice_index_fakes import _item
from tests.source_retrieval_fakes import BOOK
from tests.source_inventory_helpers import _persist


#: A sentence only the re-read of the book has.
REREAD_PASSAGE = "REREAD_ONLY_7719 The determinant of a triangular matrix is the product of its diagonal entries."
#: The question an item made from the re-read was graded against, and the learner's answer.
REREAD_STEM = "REREAD_STEM_6630 why is a triangular determinant the diagonal product?"
REREAD_ANSWER = "REREAD_ANSWER_4418 expand along the first column each time"


def _reread_of_the_book() -> DocumentIR:
    """The book read again (another engine): BOOK's sections under new span
    ids, and one passage the first reading did not have."""

    blocks: list[DocumentBlock] = []
    units: list[DocumentUnit] = []
    ordinal = 0
    for unit_index, (unit_id, (header, rows)) in enumerate(BOOK.items()):
        spans: list[str] = []
        texts = [(header, rows[0][1], "SectionHeader"), *[(text, page, "Text") for text, page in rows]]
        if unit_id == "ch_det":
            texts.append((REREAD_PASSAGE, rows[-1][1], "Text"))
        for text, page, kind in texts:
            span_id = f"r{ordinal}"
            blocks.append(DocumentBlock.build(span_id=span_id, block_type=kind, text=text, ordinal=ordinal, page=page,
                                              section_path=[header]))
            spans.append(span_id)
            ordinal += 1
        units.append(DocumentUnit(unit_id=f"h_{unit_id}", label=header, ordinal=unit_index,
                                  semantic_hash=f"sha256:reread-{unit_id}", page_start=rows[0][1],
                                  page_end=rows[-1][1], span_ids=spans))
    return DocumentIR(extractor="glm_ocr", extractor_version="1", units=units, blocks=blocks, assets=[],
                      health=ExtractionHealth())


@pytest.fixture
def reread_world(tmp_path, monkeypatch):
    """The chat frontend's world, with the book read again (``ext_book_r2``,
    now its current reading) and an item made from the re-read's own passage,
    answered and graded against a pinned contract."""

    no_model_calls(monkeypatch)
    hold_att_held(monkeypatch)
    world = build_world(tmp_path / "w")
    ir = _reread_of_the_book()
    _persist(world.repository, ir, revision_id="rev_book", extraction_id="ext_book_r2")
    span = next(block.span_id for block in ir.blocks if block.text == REREAD_PASSAGE)
    payload = _item("pi_reread", LO, "Why is the determinant of a triangular matrix its diagonal product?",
                    ["facet_determinant"])
    payload["provenance"] = {"origin": "human", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src_book", "extraction_id": "ext_book_r2", "span_ids": [span]}]}
    write_yaml(world.paths.practice_item_path("linear-algebra", "pi_reread"), payload)
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_reread', 'pi_reread', ?, 'short_answer', 'independent_attempt', ?, 1.0, 0, "
            "'2026-09-19T12:00:00Z', 'old', 'human', 'desktop_practice')", (LO, REREAD_ANSWER))
        connection.execute(
            "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES ('acv_reread', 'pi_reread', 'h_reread', ?, 1, ?)",
            (json.dumps({"prompt": REREAD_STEM, "expected_answer": "the diagonal product"}), NOW_ISO))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES ('ge_reread', 'att_reread', 'correct', 1, 1, ?, 'acv_reread')",
            (NOW_ISO,))
        connection.commit()
    return world, span


def _protect_the_first_reading(world) -> None:
    """The owner held a section of the book's FIRST reading out as exam
    material, on that reading (an exact mark): the book is protected, and its
    re-read carries no mark of its own (rule 4)."""

    world.repository.upsert_unit_selection(
        extraction_id="ext_book", source_id="src_book", revision_id="rev_book",
        selected_unit_ids=list(BOOK), exam_use_modes={"ch_orth": EM.HELD_OUT_EVALUATION},
        exam_paper_metadata={EM.MARKS_MADE_ON_KEY: EM.marks_made_on("ext_book", "rev_book")})
