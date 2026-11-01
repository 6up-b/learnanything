"""Curriculum C3: exam scoping from a syllabus (spec_deliverable_curriculum_v1 §9, §12 C3; Q2).

* the ``syllabus`` source role: assessment alignment only, never taught from, never a coverage
  candidate, a primary or an alternate, never inventoried for a study map, never protected; its
  passages (or the whole short document) are a scope input;
* practice-available exam and problem-set units contribute their LO ids (never their text) to the
  scope resolver behind ``curriculum.exam_units_in_scope``; held-out units contribute nothing; off,
  C0b's prompt byte for byte;
* G-C1..G-C3 hardened on a fixture holding every kind of exam material (``tests/exam_scope_fixtures``).

Every model is a fake (``StructuredClientFake``); nothing leaves the machine.
"""
from __future__ import annotations

import json

import pytest

from learnloop.content.sources import exam_material as EM
from learnloop.content.sources.role_authority import (
    ASSESSMENT_ONLY_ROLES,
    KNOWN_ROLES,
    can_authorize_semantic,
    default_inventory_profile,
    is_scope_only_role,
    role_authority,
)
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import section_coverage as SC
from learnloop.source_retrieval.corpus import teaching_exclusions
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from tests.deliverable_fixtures import DeliverableFake, prompt_context
from tests.exam_scope_fixtures import (
    EXAM_EXTRACTIONS,
    NEVER_ON_A_PATH,
    PAPER,
    PARTLY_PROTECTED,
    PAST_PAPER_LOS,
    SENTINEL_WORDS,
    SENTINELS,
    SPANS,
    SYLLABUS_MARKER,
    build_exam_scope_vault,
    protect_items,
)
from tests.section_coverage_fixtures import CoverageJudgeFake, table_counts

ALL_LOS = ("lo_det", "lo_eigen", "lo_inner", "lo_matrices", "lo_spectral", "lo_vectors")
OFF = "[curriculum]\nexam_units_in_scope = false"
LA = ("linear-algebra",)


def _deliverable(paths, repository, sentence="Only my midterm: eigenvalues, determinants and matrix computations",
                 **kwargs):
    created = DL.create_deliverable(load_vault(paths.root), repository, sentence, **kwargs)
    return created["goal_id"], load_vault(paths.root)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _names_section(value, extraction_id, section_ids) -> bool:
    """Whether any mapping in ``value`` names one of the reading's sections (by id or ref)."""

    if isinstance(value, dict):
        if value.get("extraction_id") == extraction_id and value.get("section_id") in section_ids:
            return True
        if any(isinstance(v, str) and v in {f"{extraction_id}/{s}" for s in section_ids} for v in value.values()):
            return True
        return any(_names_section(v, extraction_id, section_ids) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_names_section(v, extraction_id, section_ids) for v in value)
    return False


def _clean(text: str) -> None:
    for sentinel in (*SENTINELS, *SENTINEL_WORDS):
        assert sentinel not in text, sentinel


# --- the syllabus role ---------------------------------------------------------------------

def test_the_syllabus_role_scopes_only_assessment_alignment_never_semantic_never_exam():
    authority = role_authority("syllabus")
    assert "syllabus" in KNOWN_ROLES and authority.known
    assert (authority.semantic_contract, authority.assessment_alignment) == (False, True)
    assert not can_authorize_semantic("syllabus") and is_scope_only_role("syllabus")
    assert "syllabus" not in ASSESSMENT_ONLY_ROLES and not EM.is_exam_role("syllabus")  # never protected
    assert default_inventory_profile("syllabus") == "assessment"
    assert not is_scope_only_role("exam") and not is_scope_only_role("notes")


def test_the_role_is_set_through_the_existing_role_surfaces(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    # The outline's role pick (a known role is required there) and the collection membership.
    selection = save_unit_selection(repository, "ext_syl", ["syl_main"], role_override="syllabus")
    assert selection["role_override"] == "syllabus"
    vault = load_vault(paths.root)
    member = next(m for s in vault.source_sets for m in s.members if m.source_id == "src_syl")
    assert member.default_role == "syllabus"


def test_the_fixture_holds_every_kind_of_exam_material(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    exam = EM.exam_material(vault, repository)
    assert exam.covers("ext_exam") and exam.covers("ext_syl_exam") and exam.covers("ext_paper")
    assert exam.is_held_out("ext_paper", SPANS["paper_q3"])
    assert not exam.is_held_out("ext_paper", SPANS["paper_q1"]) and not exam.is_held_out("ext_paper", SPANS["paper_q2"])
    assert exam.is_held_out("ext_pset", SPANS["pset_2"]) and not exam.covers("ext_pset", SPANS["pset_1"])
    assert exam.is_held_out("ext_lay", SPANS["lay_held"])
    assert not exam.covers("ext_syl") and not exam.covers("ext_syl", SPANS["syl_main"])  # a syllabus: not protected
    # Rule 2 inside a book, the outline's exam pick outside every set, rule 4's unmarked alternate reading.
    assert exam.covers("ext_mixed", SPANS["mixed_exam"]) and not exam.covers("ext_mixed", SPANS["mixed_theory"])
    assert exam.covers("ext_outline", SPANS["outline_q1"])
    assert not any(s.id for s in vault.source_sets for m in s.members if m.source_id == "src_outline")
    assert EM.reading_held_back(vault, repository, "ext_lay_alt")


def test_a_syllabus_never_teaches_and_is_never_a_coverage_candidate(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert "ext_syl" in teaching_exclusions(vault, repository).extractions
    library = SC.Library(vault, repository)
    # Left out, or (the unmarked alternate reading, not the one the Reader opens) never read at all.
    assert not {"ext_syl", *EXAM_EXTRACTIONS} & set(library.extractions)
    assert {"ext_syl", *EXAM_EXTRACTIONS} - {"ext_lay_alt"} <= set(library.left_out)
    judge = CoverageJudgeFake()
    for lo_id in ALL_LOS:
        SC.judge(vault, repository, lo_id, client=judge)
    assert judge.calls
    for prompt in judge.prompts:
        assert SYLLABUS_MARKER not in prompt
        _clean(prompt)
    readings = {row[0] for row in _rows(repository, "SELECT DISTINCT extraction_id FROM section_coverage")}
    assert readings and not readings & set(NEVER_ON_A_PATH)


def test_a_syllabus_is_never_inventoried_for_a_study_map(tmp_path):
    from learnloop.content.synthesis.source_set_synthesis import _collect_inputs

    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    for extraction_id, revision_id, unit_id in (("ext_book", "rev_book", "ch_eigen"), ("ext_syl", "rev_syl", "syl_main")):
        repository.insert_unit_inventory(
            id=f"inv_{unit_id}", source_revision_id=revision_id, extraction_id=extraction_id, unit_id=unit_id,
            unit_semantic_hash=f"sha256:{unit_id}", inventory_profile="combined", inventory_schema_version=1,
            prompt_version="test", provider="fake", model="fake",
            inventory={"concept_mentions": [{"name": "eigenvalues"}]})
    vault = load_vault(paths.root)
    source_set = next(s for s in vault.source_sets if s.id == "sset_la")
    inputs = _collect_inputs(repository, vault, source_set)
    units = {(entry["extraction_id"], entry["unit_id"]) for entry in inputs.unit_inventories}
    assert ("ext_book", "ch_eigen") in units
    assert not any(extraction == "ext_syl" for extraction, _unit in units)


# --- a syllabus as a scope input -------------------------------------------------------------

def test_a_syllabus_passage_is_a_scope_input_read_only_by_the_resolver(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "my midterm")
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[SPANS["syl_main"]])
    fake = DeliverableFake()
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert result.status == "ready"
    passage = fake.contexts[0]["inputs"][1]
    assert passage["kind"] == "passage" and SYLLABUS_MARKER in passage["text"]
    needed = {entry["learning_object_id"] for entry in DL.needed_learning_objects(load_vault(paths.root),
                                                                                    repository, goal_id)}
    assert {"lo_eigen", "lo_det", "lo_matrices"} <= needed  # the syllabus's words scoped them
    _clean(fake.prompts[0])


def test_a_whole_short_syllabus_is_one_input_with_its_spans_recorded(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "my midterm")
    row = DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl")
    stored = _rows(repository, "SELECT kind, extraction_id, span_ids_json FROM deliverable_scope_inputs WHERE id = ?",
                   (row["id"],))
    assert stored == [("passage", "ext_syl", json.dumps([SPANS["syl_main"]]))]
    # A book is not a whole-document input: the learner selects a passage of it.
    with pytest.raises(DL.DeliverableError) as caught:
        DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_book")
    assert caught.value.code == "validation_error"


def test_gc2_a_syllabus_with_the_exam_role_is_refused_and_nothing_is_written(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    before = table_counts(repository)
    for span_ids in ([SPANS["syl_exam"]], []):  # a selection, and the whole document
        with pytest.raises(DL.DeliverableError) as caught:
            DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl_exam", span_ids=span_ids)
        assert caught.value.code == "exam_material" and str(caught.value) == DL.EXAM_REFUSAL
    # Every other kind of exam material is refused the same way.
    for extraction_id, span in (("ext_exam", "exam_q"), ("ext_paper", "paper_q1"), ("ext_paper", "paper_q2"),
                                ("ext_paper", "paper_q3"), ("ext_lay", "lay_held"), ("ext_pset", "pset_1"),
                                ("ext_pset", "pset_2"), ("ext_mixed", "mixed_exam"), ("ext_outline", "outline_q1"),
                                ("ext_lay_alt", "alt_eigen")):
        with pytest.raises(DL.DeliverableError) as caught:
            DL.add_input(vault, repository, goal_id, "passage", extraction_id=extraction_id, span_ids=[SPANS[span]])
        assert caught.value.code == "exam_material"
    assert table_counts(repository) == before


def test_gc2_the_same_syllabus_given_the_exam_role_is_refused(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault", syllabus_role="exam")
    goal_id, vault = _deliverable(paths, repository)
    with pytest.raises(DL.DeliverableError) as caught:
        DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[SPANS["syl_main"]])
    assert caught.value.code == "exam_material"


def test_gc2_a_syllabus_made_exam_after_it_was_added_is_never_sent(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "my midterm")
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[SPANS["syl_main"]])
    vault = load_vault(paths.root)
    source_set = next(s for s in vault.source_sets if s.id == "sset_la")
    members = [m.model_dump(mode="json") for m in source_set.members]
    for member in members:
        if member["source_id"] == "src_syl":
            member["default_role"] = "exam"
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": source_set.title,
                                   "members": members})
    fake = DeliverableFake()
    with pytest.raises(DL.DeliverableError) as caught:
        DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert caught.value.code == "exam_material" and fake.calls == 0


def test_a_syllabus_made_exam_during_the_call_keeps_nothing(tmp_path):
    """The request-time guard reads protection again (the syllabus library's roles included)."""

    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "my midterm")
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[SPANS["syl_main"]])
    vault = load_vault(paths.root)
    before = _rows(repository, "SELECT COUNT(*) FROM deliverable_scope_resolutions")
    source_set = next(s for s in vault.source_sets if s.id == "sset_la")
    members = [m.model_dump(mode="json") for m in source_set.members]

    class Turning(DeliverableFake):
        def complete(self, request):
            for member in members:
                if member["source_id"] == "src_syl":
                    member["default_role"] = "exam"
            upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                           "title": source_set.title, "members": members})
            return super().complete(request)

    result = DL.resolve(vault, repository, goal_id, client=Turning())
    assert result.status == "unavailable" and result.reason == "protection_changed"
    assert _rows(repository, "SELECT COUNT(*) FROM deliverable_scope_resolutions") == before


# --- past papers: LO ids only ----------------------------------------------------------------

def test_past_papers_contribute_their_lo_ids_only_and_held_out_units_nothing(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert DL.past_paper_learning_objects(vault, repository, LA) == list(PAST_PAPER_LOS)  # lo_spectral: held out only
    goal_id, vault = _deliverable(paths, repository)
    fake = DeliverableFake()
    result = DL.resolve(vault, repository, goal_id, client=fake)
    assert result.status == "ready"
    context = fake.contexts[0]
    assert context["past_papers_test"] == list(PAST_PAPER_LOS)
    assert DL.SCOPE_PAST_PAPERS_PROMPT_VERSION in fake.prompts[0] and "past_papers_test" in fake.prompts[0]
    _clean(fake.prompts[0])
    assert result.resolution["prompt_version"] == DL.SCOPE_PAST_PAPERS_PROMPT_VERSION
    # A unit held out later stops contributing at once.
    save_unit_selection(repository, "ext_paper", list(PAPER), exam_use_modes={
        "paper_q1": "held_out_evaluation", "paper_q2": "blueprint_only", "paper_q3": "held_out_evaluation"})
    assert "lo_matrices" not in DL.past_paper_learning_objects(load_vault(paths.root), repository, LA)


def test_an_unreadable_predicate_contributes_nothing(tmp_path, monkeypatch):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")

    def broken(*_args, **_kwargs):
        raise RuntimeError("unreadable")

    monkeypatch.setattr(EM, "exam_material", broken)
    assert DL.past_paper_learning_objects(load_vault(paths.root), repository, LA) == []


def test_off_is_c0b_byte_for_byte(tmp_path, monkeypatch):
    paths, repository = build_exam_scope_vault(tmp_path / "vault", config=OFF)
    goal_id, vault = _deliverable(paths, repository)
    goal = DL.goal_of(vault, goal_id)
    with repository.connection() as connection:
        from learnloop.db.stores import deliverables as store

        rows = store.inputs(connection, goal_id)

    def never(*_args, **_kwargs):
        raise AssertionError("the past-papers input is never read with the switch off")

    monkeypatch.setattr(DL, "past_paper_learning_objects", never)
    off = DL.build_scope_prompt(vault, repository, goal, rows)
    assert off.version == DL.SCOPE_PROMPT_VERSION and "past_papers_test" not in prompt_context(off.text)
    # The same prompt C0b renders: on, with nothing to contribute, is the very same text and key.
    on_vault = load_vault(paths.root)
    on_vault.config.curriculum.exam_units_in_scope = True
    monkeypatch.setattr(DL, "past_paper_learning_objects", lambda *_a, **_k: [])
    empty = DL.build_scope_prompt(on_vault, repository, goal, rows)
    assert (off.text, off.state_key, off.version) == (empty.text, empty.state_key, empty.version)
    monkeypatch.undo()
    fake = DeliverableFake()
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert result.resolution["prompt_version"] == DL.SCOPE_PROMPT_VERSION and fake.prompts[0] == off.text
    view = DL.scope_view(load_vault(paths.root), repository, goal_id)
    assert view["topics"] and all("on_past_papers" not in topic for topic in view["topics"])


def test_the_scope_view_says_which_topics_your_past_papers_test(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    DL.resolve(vault, repository, goal_id, client=DeliverableFake())
    view = DL.scope_view(load_vault(paths.root), repository, goal_id)
    marks = {topic["learning_object_id"]: topic["on_past_papers"] for topic in view["topics"]}
    assert marks["lo_matrices"] is True and marks["lo_det"] is True and marks["lo_eigen"] is False
    _clean(json.dumps(view))


def test_the_config_default_is_on():
    from learnloop.config.schema import CurriculumConfig

    assert CurriculumConfig().exam_units_in_scope is True


# --- G-C1 / G-C3 on every kind of exam material ----------------------------------------------

def test_gc1_no_request_correspondent_path_row_or_slice_names_exam_material(tmp_path):
    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    judge = CoverageJudgeFake()
    for lo_id in ALL_LOS:
        SC.judge(vault, repository, lo_id, client=judge)
    goal_id, vault = _deliverable(paths, repository, "eigenvalues, determinants, matrix computations, spectral")
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[SPANS["syl_main"]])
    scope = DeliverableFake()
    assert DL.resolve(load_vault(paths.root), repository, goal_id, client=scope).status == "ready"
    vault = load_vault(paths.root)
    DL.add_input(vault, repository, goal_id, "depth", text="learn_to_use_it")
    vault = load_vault(paths.root)
    path = DeliverableFake()
    DP.judge(vault, repository, goal_id, client=path)
    assert path.calls == 1
    # Every captured request: coverage judge, scope resolver, path judge.
    for prompt in (*judge.prompts, *scope.prompts, *path.prompts):
        _clean(prompt)
    for prompt in (*judge.prompts, *path.prompts):
        assert SYLLABUS_MARKER not in prompt  # a syllabus is read by the resolver only
    # No path row, path view, slice or correspondent names exam material or the syllabus.
    rows = _rows(repository, "SELECT extraction_id, section_id FROM deliverable_path_sections")
    assert rows and not {row[0] for row in rows} & set(NEVER_ON_A_PATH)
    library = SC.Library(vault, repository)
    partly = {extraction_id: library.reading(extraction_id) for extraction_id in PARTLY_PROTECTED}
    for extraction_id, reading in partly.items():
        assert reading is not None and reading.withheld  # the held-out unit's section, the exam unit's
        assert not {(extraction_id, section) for section in reading.withheld} & set(rows)
    outputs = [DP.path_view(vault, repository, goal_id), DP.readiness(vault, repository, goal_id)]
    outputs += [DP.guide_slice(vault, repository, extraction_id) for extraction_id in sorted(library.extractions)]
    for extraction_id in sorted(library.extractions):
        reading = library.reading(extraction_id)
        for section_id in sorted(reading.sections):
            outputs.append(SC.correspondents(vault, repository, extraction_id, section_id))
    for output in outputs:
        text = json.dumps(output, default=str)
        _clean(text)
        assert SYLLABUS_MARKER not in text
        for extraction_id in NEVER_ON_A_PATH:
            assert extraction_id not in text
        for extraction_id, reading in partly.items():
            assert not _names_section(output, extraction_id, reading.withheld)


def test_gc3_readiness_checks_never_pick_exam_reserved_or_held_out_items(tmp_path):
    from datetime import UTC, datetime, timedelta

    paths, repository = build_exam_scope_vault(tmp_path / "vault")
    deadline = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")
    goal_id, vault = _deliverable(paths, repository, "matrix computations", due_at=deadline, exam=True)
    DL.resolve(vault, repository, goal_id, client=DeliverableFake(needs=("lo_matrices",)))
    vault = load_vault(paths.root)
    items = sorted(item.id for item in vault.practice_items.values() if item.learning_object_id == "lo_matrices")
    protected = protect_items(paths, repository, goal_id, items)
    vault = load_vault(paths.root)
    picked = DP.check_item(vault, repository, "lo_matrices")
    assert picked is not None and picked not in protected
    out = DP.ready_checks(vault, repository, goal_id)
    chosen = {entry["learning_object_id"]: entry["item_id"] for entry in out["created"]}
    assert chosen["lo_matrices"] == picked
