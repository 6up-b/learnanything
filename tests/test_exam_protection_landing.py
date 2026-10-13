"""Exam protection landing on main: UX Phase 1's exam paths read the one predicate.

UX Phase 1 composed its two exam paths with main's corpus predicates before
exam protection landed: the automatic build's scope
(``corpus.source_exam_exclusions``, which added one book's own
``held_out_evaluation`` units to an ``exam_exclusions`` that read source-set
members only) and U4's reading step (``corpus.exam_exclusions``). Both now
read the one predicate (``content.sources.exam_material``), so there is
exactly one exam and held-out test, and what it adds reaches them: an outline
role pick ``exam`` (the import-batch path's role, before any study map) and a
held-out unit of a book in no source set.
"""

from __future__ import annotations

from contextlib import closing

from learnloop.content.pipeline import add_source as core
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import extraction_units
from learnloop.source_retrieval import corpus
from learnloop.vault.loader import load_vault

from tests.test_ux_phase1_landing import _added_book, _hold_out, _reading_book, _section_spans
from tests.ux_phase1_support import CLOCK, route


def test_the_automatic_build_scope_is_the_one_predicate(tmp_path):
    from learnloop.content.sources.exam_material import exam_material

    root, repo, source_id = _added_book(tmp_path)
    held = _hold_out(repo, source_id, "2 Conditional probability")
    vault = load_vault(root)
    revision_id, extraction_id = core._completed_extraction(repo, source_id)

    scope = corpus.source_exam_exclusions(vault, repo, source_id=source_id, revision_id=revision_id)
    shared = exam_material(vault, repo)
    assert (scope.extractions, scope.spans) == (shared.material.extractions, shared.material.spans)
    assert all(shared.is_held_out(*key) for key in scope.spans)
    withheld = core.exam_material_units(vault, repo, source_id, revision_id, extraction_id)
    assert set(held.unit_ids) <= withheld


def test_a_book_picked_as_an_exam_in_its_outline_builds_nothing(tmp_path):
    """The outline flow's role pick ``exam`` (rule 1 of the predicate, the
    import-batch path's role before the book joins any study map) makes the
    whole book exam material: an automatic build takes nothing from it."""

    root, repo, source_id = _added_book(tmp_path)
    before = core.preview_auto_build(root, repo, source_id, whole_book=True, route=route(), now=CLOCK.now())
    assert before["chapters"]

    extraction_id = resolve_extraction_id(repo, source_id)
    outline = build_source_outline(repo, extraction_id)
    save_unit_selection(repo, extraction_id, [unit.unit_id for unit in outline.units], role_override="exam",
                        clock=CLOCK)
    vault = load_vault(root)
    revision_id, _ = core._completed_extraction(repo, source_id)
    assert core.exam_material_units(vault, repo, source_id, revision_id, extraction_id) is None
    after = core.preview_auto_build(root, repo, source_id, whole_book=True, route=route(), now=CLOCK.now())
    assert after["status"] == "nothing_to_build"


def test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set(tmp_path):
    """A learner's held-out mark on a book no study map holds yet (rule 3:
    every unit selection, in a source set or not) keeps U4's reading step off
    that section, through the real predicate (nothing stubbed)."""

    from learnloop.daily_plan.engine import _exam_material
    from learnloop.daily_plan.reading import next_reading_target

    paths, repo, extraction_id, ids = _reading_book(tmp_path)
    vault = load_vault(paths.root)
    assert not any(member.source_id for source_set in vault.source_sets for member in source_set.members
                   if resolve_extraction_id(repo, member.revision_id) == extraction_id)
    assert next_reading_target(repo, exam=_exam_material(vault, repo)).section_id == ids["1-vectors"]

    spans = set(_section_spans(repo, extraction_id, ids["1-vectors"]))
    with closing(connect(repo.sqlite_path, read_only=True)) as connection:
        units = extraction_units(connection, extraction_id)
    marked = [unit.unit_id for unit in units if spans & set(unit.span_ids)]
    assert marked
    save_unit_selection(repo, extraction_id, [unit.unit_id for unit in units],
                        exam_use_modes={unit_id: "held_out_evaluation" for unit_id in marked}, clock=CLOCK)

    exam = _exam_material(load_vault(paths.root), repo)
    assert exam is not None and spans <= {span for ext, span in exam.spans if ext == extraction_id}
    assert next_reading_target(repo, exam=exam).section_id == ids["2-matrices"]
    # DL1's selection (the switch off) never reads the predicate, as before.
    assert next_reading_target(repo, from_furthest=False, exam=exam).section_id == ids["contents"]
