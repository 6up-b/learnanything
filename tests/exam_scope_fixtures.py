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
* an exam-reserved item, an item made from the held-out unit and one made from a practice-available
  exam unit, all on ``lo_matrices``.

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
SYLLABUS_MARKER = "SYLLABUSMARKER"
SYLLABUS_TEXT = (f"{SYLLABUS_MARKER} Course syllabus: the midterm covers eigenvalues and determinants; "
                 "matrix computations are examined.")

#: Every exam text of the vault: no coverage, path or scope request may contain any of them.
SENTINELS: tuple[str, ...] = (
    EXAM_QUESTION, HELD_OUT_SENTINEL, PAPER_PRACTICE_SENTINEL, PAPER_BLUEPRINT_SENTINEL, PAPER_HELD_SENTINEL,
    PSET_SENTINEL, PSET_HELD_SENTINEL, EXAM_SYLLABUS_SENTINEL,
)
#: The sentinels' first words: no request may carry any of them, even clipped.
SENTINEL_WORDS: tuple[str, ...] = (
    "HELDOUTSENTINEL", "PAPERPRACTICESENTINEL", "PAPERBLUEPRINTSENTINEL", "PAPERHELDSENTINEL", "PSETSENTINEL",
    "PSETHELDSENTINEL", "EXAMSYLLABUSSENTINEL", "Exam question 1",
)
#: Readings no correspondent, path row or slice may name (``ext_lay`` is a book: only its held-out
#: unit is protected, checked by section).
EXAM_EXTRACTIONS: tuple[str, ...] = ("ext_exam", "ext_paper", "ext_pset", "ext_syl_exam")
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
#: The text span of each unit (``seed_source`` numbers a unit's header, then its rows).
SPANS = {"paper_q1": "s2", "paper_q2": "s5", "paper_q3": "s8", "pset_1": "s2", "pset_2": "s5",
         "syl_main": "s2", "syl_exam": "s2", "lay_held": "s9", "exam_q": "s2"}
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
