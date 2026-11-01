"""Curriculum C3's synthetic vault with every kind of exam material (spec_deliverable_curriculum_v1
§9, §12 C3; G-C1..G-C3). No network; every model is a fake.

``build_exam_scope_vault`` is C0b's deliverable vault (the book ``ext_book``; the exam-role source
``ext_exam`` whose question is :data:`EXAM_QUESTION`; the second book ``ext_lay`` with the held-out
unit ``lay_held``, :data:`HELD_OUT_SENTINEL`) plus:

* ``ext_paper``: a past paper (role ``exam``) with one unit per use mode: ``paper_q1``
  ``available_for_practice``, ``paper_q2`` ``blueprint_only``, ``paper_q3`` ``held_out_evaluation``;
* ``ext_pset``: a problem set (role ``problem_set``): ``pset_1`` unmarked (practice-available),
  ``pset_2`` ``held_out_evaluation``;
* ``ext_syl``: a course syllabus with the ``syllabus`` role (readable as a scope input only);
* ``ext_syl_exam``: a syllabus given the ``exam`` role (exam material whole);
* ``ext_mixed``: a book (role ``primary_textbook``) whose unit ``mixed_exam`` is overridden to the
  ``exam`` role on the reading it was chosen on (rule 2), beside a teaching unit ``mixed_theory``;
* ``ext_outline``: a past paper outside every source set whose outline role pick is ``exam`` (the
  import-batch path: exam material whole);
* ``ext_lay_alt``: an alternate, unmarked reading of the protected book ``ext_lay`` (rule 4: held
  back whole until protection is marked on it);
* an exam-reserved item, an item made from the held-out unit and one made from a practice-available
  exam unit, all on ``lo_matrices``.

Not built here: held-out *signals* (an inventory's held-out signal ledger); the exam predicate's own
suite covers them (``tests/test_exam_protection.py``), and every reader here reads that one predicate.

Every exam text carries its own sentinel (:data:`SENTINELS`); the syllabus carries
:data:`SYLLABUS_MARKER`, which the scope resolver may read and nothing else ever does.

The LOs' provenance gives the past-papers mapping (§9.2): ``lo_matrices`` cites ``paper_q1``,
``lo_vectors`` cites ``paper_q2``, ``lo_inner`` cites ``pset_1`` and ``lo_det`` cites the exam-role
source (all practice-available); ``lo_spectral`` cites only held-out material (``paper_q3``,
``pset_2``, ``lay_held``) and ``lo_eigen`` only the book.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_concept, upsert_source_set
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.deliverable_fixtures import NOW, build_deliverable_vault
from tests.practice_index_fakes import _learning_object
from tests.section_coverage_fixtures import HELD_OUT_SENTINEL
from tests.source_retrieval_fakes import EXAM_QUESTION, seed_source

PAPER_PRACTICE_SENTINEL = "PAPERPRACTICESENTINEL past paper question one: multiply these two matrices."
PAPER_BLUEPRINT_SENTINEL = "PAPERBLUEPRINTSENTINEL past paper question two: show these vectors are independent."
PAPER_HELD_SENTINEL = "PAPERHELDSENTINEL held-out question three: state and prove the spectral theorem."
PSET_SENTINEL = "PSETSENTINEL problem one: compute the inner product of u and v."
PSET_HELD_SENTINEL = "PSETHELDSENTINEL held-out problem two: diagonalise this symmetric matrix."
EXAM_SYLLABUS_SENTINEL = "EXAMSYLLABUSSENTINEL midterm syllabus kept as exam material: spectral theorem."
MIXED_EXAM_SENTINEL = "MIXEDEXAMSENTINEL exam unit inside a textbook: find the rank of this matrix."
OUTLINE_SENTINEL = "OUTLINESENTINEL past paper picked as exam in the outline: invert this matrix."
ALT_READING_SENTINEL = "ALTREADINGSENTINEL an unmarked second reading of a protected book."
SYLLABUS_MARKER = "SYLLABUSMARKER"
SYLLABUS_TEXT = (f"{SYLLABUS_MARKER} Course syllabus: the midterm covers eigenvalues and determinants; "
                 "matrix computations are examined.")

#: Every exam text of the vault: no coverage, path or scope request may contain any of them.
SENTINELS: tuple[str, ...] = (
    EXAM_QUESTION, HELD_OUT_SENTINEL, PAPER_PRACTICE_SENTINEL, PAPER_BLUEPRINT_SENTINEL, PAPER_HELD_SENTINEL,
    PSET_SENTINEL, PSET_HELD_SENTINEL, EXAM_SYLLABUS_SENTINEL, MIXED_EXAM_SENTINEL, OUTLINE_SENTINEL,
    ALT_READING_SENTINEL,
)
#: The sentinels' first words: no request may carry any of them, even clipped.
SENTINEL_WORDS: tuple[str, ...] = (
    "HELDOUTSENTINEL", "PAPERPRACTICESENTINEL", "PAPERBLUEPRINTSENTINEL", "PAPERHELDSENTINEL", "PSETSENTINEL",
    "PSETHELDSENTINEL", "EXAMSYLLABUSSENTINEL", "Exam question 1", "MIXEDEXAMSENTINEL", "OUTLINESENTINEL",
    "ALTREADINGSENTINEL",
)
#: Readings no correspondent, path row or slice may name (``ext_lay`` is a book: only its held-out
#: unit is protected, checked by section).
EXAM_EXTRACTIONS: tuple[str, ...] = ("ext_exam", "ext_paper", "ext_pset", "ext_syl_exam", "ext_outline",
                                     "ext_lay_alt")
#: Books with one protected unit (checked by section): ``ext_lay``'s held-out unit, ``ext_mixed``'s exam unit.
PARTLY_PROTECTED: dict[str, str] = {"ext_lay": "lay_held", "ext_mixed": "mixed_exam"}
#: The syllabus is never a coverage candidate, a primary or an alternate either.
NEVER_ON_A_PATH: tuple[str, ...] = (*EXAM_EXTRACTIONS, "ext_syl")

PAPER = {
    "paper_q1": ("Question 1", [(PAPER_PRACTICE_SENTINEL, 1)]),
    "paper_q2": ("Question 2", [(PAPER_BLUEPRINT_SENTINEL, 1)]),
    "paper_q3": ("Question 3", [(PAPER_HELD_SENTINEL, 2)]),
}
PSET = {
    "pset_1": ("Problem 1", [(PSET_SENTINEL, 1)]),
    "pset_2": ("Problem 2", [(PSET_HELD_SENTINEL, 1)]),
}
SYLLABUS = {"syl_main": ("Course syllabus", [(SYLLABUS_TEXT, 1)])}
EXAM_SYLLABUS = {"syl_exam": ("Midterm syllabus", [(EXAM_SYLLABUS_SENTINEL, 1)])}
MIXED = {
    "mixed_theory": ("4.1 Rank", [("The rank of a matrix is the dimension of its column space.", 1)]),
    "mixed_exam": ("4.9 Exam practice", [(MIXED_EXAM_SENTINEL, 2)]),
}
OUTLINE = {"outline_q1": ("Question 1", [(OUTLINE_SENTINEL, 1)])}
#: The text span of each unit (``seed_source`` numbers a unit's header, then its rows).
SPANS = {"paper_q1": "s2", "paper_q2": "s5", "paper_q3": "s8", "pset_1": "s2", "pset_2": "s5",
         "syl_main": "s2", "syl_exam": "s2", "lay_held": "s9", "exam_q": "s2", "mixed_theory": "s2",
         "mixed_exam": "s5", "outline_q1": "s2", "alt_eigen": "s2"}
PAST_PAPER_LOS: tuple[str, ...] = ("lo_det", "lo_inner", "lo_matrices", "lo_vectors")


def ref(source_id: str, extraction_id: str, span_id: str) -> dict[str, Any]:
    return {"ref_type": "canonical_source", "ref_id": source_id, "locator": f"span:{extraction_id}/{span_id}",
            "source_id": source_id, "extraction_id": extraction_id}


def set_refs(path: Path, refs: list[dict[str, Any]]) -> None:
    data = read_yaml(path)
    data["provenance"] = {"origin": "human", "source_refs": refs}
    write_yaml(path, data)


def build_exam_scope_vault(root: Path, *, config: str = "", syllabus_role: str = "syllabus"
                           ) -> tuple[VaultPaths, Repository]:
    paths, repository = build_deliverable_vault(root, config=config)
    seed_source(repository, source_id="src_paper", revision_id="rev_paper", extraction_id="ext_paper",
                title="Past midterm 2025", units=PAPER, furniture=False)
    seed_source(repository, source_id="src_pset", revision_id="rev_pset", extraction_id="ext_pset",
                title="Problem set 3", units=PSET, furniture=False)
    seed_source(repository, source_id="src_syl", revision_id="rev_syl", extraction_id="ext_syl",
                title="Course syllabus", units=SYLLABUS, furniture=False)
    seed_source(repository, source_id="src_syl_exam", revision_id="rev_syl_exam", extraction_id="ext_syl_exam",
                title="Midterm syllabus", units=EXAM_SYLLABUS, furniture=False)
    members = [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        {"source_id": "src_lay", "revision_id": "rev_lay", "default_role": "primary_textbook"},
        {"source_id": "src_paper", "revision_id": "rev_paper", "default_role": "exam"},
        {"source_id": "src_pset", "revision_id": "rev_pset", "default_role": "problem_set"},
        {"source_id": "src_syl", "revision_id": "rev_syl", "default_role": syllabus_role},
        {"source_id": "src_syl_exam", "revision_id": "rev_syl_exam", "default_role": "exam"},
    ]
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": members})
    save_unit_selection(repository, "ext_paper", list(PAPER), exam_use_modes={
        "paper_q1": "available_for_practice", "paper_q2": "blueprint_only", "paper_q3": "held_out_evaluation"})
    save_unit_selection(repository, "ext_pset", list(PSET), exam_use_modes={"pset_2": "held_out_evaluation"})
    # Rule 2: an exam unit inside a book, chosen on its reading.
    seed_source(repository, source_id="src_mixed", revision_id="rev_mixed", extraction_id="ext_mixed",
                title="Matrix methods", units=MIXED, furniture=False)
    members.append({"source_id": "src_mixed", "revision_id": "rev_mixed", "default_role": "primary_textbook",
                    "scope": [{"unit_id": "mixed_exam", "role_override": "exam"}],
                    "scope_extraction_id": "ext_mixed", "scope_revision_id": "rev_mixed"})
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": members})
    # The import-batch path: an outline exam pick, in no source set.
    seed_source(repository, source_id="src_outline", revision_id="rev_outline", extraction_id="ext_outline",
                title="Past final 2024", units=OUTLINE, furniture=False)
    save_unit_selection(repository, "ext_outline", list(OUTLINE), role_override="exam")
    # Rule 4: a second, unmarked reading of the protected book ``ext_lay``.
    _second_reading(repository, revision_id="rev_lay", extraction_id="ext_lay_alt")

    upsert_concept(paths.root, "spectral_c", {
        "title": "Spectral theorem", "type": "concept", "aliases": [], "description": "The spectral theorem.",
        "tags": [], "created_at": NOW, "updated_at": NOW})
    spectral = _learning_object("lo_spectral", "Spectral theorem")
    spectral["concept"] = "spectral_c"
    spectral["summary"] = "A real symmetric matrix is orthogonally diagonalisable."
    write_yaml(paths.learning_object_path("linear-algebra", "lo_spectral"), spectral)
    lo = lambda lo_id: paths.learning_object_path("linear-algebra", lo_id)  # noqa: E731
    set_refs(lo("lo_matrices"), [ref("src_paper", "ext_paper", SPANS["paper_q1"])])
    set_refs(lo("lo_vectors"), [ref("src_paper", "ext_paper", SPANS["paper_q2"])])
    set_refs(lo("lo_inner"), [ref("src_pset", "ext_pset", SPANS["pset_1"])])
    set_refs(lo("lo_det"), [ref("src_exam", "ext_exam", SPANS["exam_q"])])
    set_refs(lo("lo_spectral"), [ref("src_paper", "ext_paper", SPANS["paper_q3"]),
                                 ref("src_pset", "ext_pset", SPANS["pset_2"]),
                                 ref("src_lay", "ext_lay", SPANS["lay_held"])])
    return paths, repository


def _second_reading(repository: Repository, *, revision_id: str, extraction_id: str) -> None:
    """Another completed reading of a revision (a re-read), with no protection marked on it."""

    from learnloop.ingest.ir import DocumentIR, DocumentUnit, ExtractionHealth
    from tests.source_retrieval_fakes import _blocks

    units = {"alt_eigen": ("5.1 Eigenvalues again", [(ALT_READING_SENTINEL, 1)])}
    blocks, document_units, start = [], [], 1
    for ordinal, (unit_id, (header, rows)) in enumerate(units.items()):
        unit_blocks, span_ids = _blocks(unit_id, header, rows, start)
        start += len(unit_blocks) + 1
        blocks.extend(unit_blocks)
        document_units.append(DocumentUnit(unit_id=unit_id, label=header, ordinal=ordinal,
                                           semantic_hash=f"sha256:{unit_id}", page_start=rows[0][1],
                                           page_end=rows[-1][1], span_ids=span_ids))
    ir = DocumentIR(extractor="marker", extractor_version="1", units=document_units, blocks=blocks, assets=[],
                    health=ExtractionHealth())
    # Another request (a reading with other settings), an earlier run of the same revision: an
    # alternate reading, not the one the Reader opens.
    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.ingest.ir import IR_SCHEMA_VERSION
    from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash

    earlier = FrozenClock(datetime(2025, 1, 1, tzinfo=UTC))
    config = {"alternate": extraction_id}
    request_hash = extraction_request_hash(revision_id=revision_id, extractor=ir.extractor,
                                           extractor_version=ir.extractor_version, config=config,
                                           ir_schema_version=IR_SCHEMA_VERSION)
    repository.insert_extraction_run(id=extraction_id, revision_id=revision_id, extractor=ir.extractor,
                                     extractor_version=ir.extractor_version, extraction_request_hash=request_hash,
                                     ir_schema_version=IR_SCHEMA_VERSION, config=config, status="running",
                                     clock=earlier)
    repository.persist_document_ir(extraction_id, ir)
    repository.complete_extraction_run(extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir),
                                       clock=earlier)


def protect_items(paths: VaultPaths, repository: Repository, goal_id: str, item_ids: list[str]) -> dict[str, str]:
    """Make the first three items exam material of three kinds: reserved for the goal's exam, made
    from the held-out unit, made from a practice-available exam unit. Returns ``{item: kind}``."""

    reserved, held, practice_unit = item_ids[:3]
    repository.insert_exam_pool_items([{"id": "epi_c3", "goal_id": goal_id, "practice_item_id": reserved,
                                        "reserved_at": "2026-10-30T00:00:00Z"}])
    set_refs(paths.practice_item_path("linear-algebra", held), [ref("src_paper", "ext_paper", SPANS["paper_q3"])])
    set_refs(paths.practice_item_path("linear-algebra", practice_unit),
             [ref("src_paper", "ext_paper", SPANS["paper_q1"])])
    return {reserved: "exam_reserved", held: "held_out", practice_unit: "exam_unit"}
