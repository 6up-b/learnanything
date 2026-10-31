"""Curriculum C0b: the deliverable and its scope in the learner's own words
(spec_deliverable_curriculum_v1 §5, §6.5, §9.1; G-C1 and G-C2 for scoping).

Every model is a fake (``DeliverableFake``); nothing leaves the machine.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.goals import goal_lo as GL
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import section_coverage as SC
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault, cover_all
from tests.section_coverage_fixtures import BOOK_EIGEN, HELD_OUT_SENTINEL, table_counts
from tests.source_retrieval_fakes import EXAM_QUESTION


def _deliverable(paths, repository, sentence="Only my midterm: eigenvalues and determinants", **kwargs):
    created = DL.create_deliverable(load_vault(paths.root), repository, sentence, **kwargs)
    return created["goal_id"], load_vault(paths.root)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def test_the_three_tables_are_append_only(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    with repository.connection() as connection:
        for table in ("deliverable_scope_inputs",):
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                connection.execute(f"UPDATE {table} SET goal_id = 'x'")
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")
        triggers = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
    for table in ("deliverable_scope_inputs", "deliverable_scope_resolutions", "deliverable_path_sections"):
        assert {f"{table}_no_update", f"{table}_no_delete"} <= triggers


def test_a_deliverable_is_a_learner_goal_with_its_sentence_and_first_input(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, due_at="2026-11-12", exam=True)
    goal = next(goal for goal in vault.goals if goal.id == goal_id)
    assert goal.creation_source == "learner" and goal.intent_sentence.startswith("Only my midterm")
    assert goal.due_at == "2026-11-12T23:59:59Z" and goal.exam.enabled and goal.facet_scope.is_empty()
    assert DL.kind_of(goal) == "exam"
    assert _rows(repository, "SELECT kind, text_md FROM deliverable_scope_inputs WHERE goal_id = ?", (goal_id,)) == [
        ("text", "Only my midterm: eigenvalues and determinants")]


def test_resolution_writes_the_scope_through_the_lock_and_a_repeat_pays_nothing(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    fake = DeliverableFake()
    result = DL.resolve(vault, repository, goal_id, client=fake)
    assert result.status == "ready" and fake.calls == 1
    needs = result.resolution["learning_objects"]
    # Validated: the ghost id the fake added is dropped; each LO once with the phrase it answers.
    assert [entry["learning_object_id"] for entry in needs] == ["lo_det", "lo_eigen"]
    assert {entry["phrase"] for entry in needs} == {"determinants", "eigenvalues"}
    vault = load_vault(paths.root)
    goal = next(goal for goal in vault.goals if goal.id == goal_id)
    # The fixture's LOs carry no evidence facet: each is named by its concept (none otherwise).
    assert goal.facet_scope.concepts == ["determinants_c", "singular_value_decomposition"]
    assert result.resolution["facet_scope"] == goal.facet_scope.model_dump()
    ledger = _rows(repository, "SELECT task, judge, verdict FROM judgment_ledger WHERE id = ?",
                   (result.resolution["ledger_id"],))
    assert ledger == [("deliverable_scope", "llm", "resolved")]
    # The resolver read compact LO records, never items.
    context = fake.contexts[0]
    assert {topic["id"] for topic in context["topics"]} >= {"lo_eigen", "lo_det", "lo_matrices"}
    assert "items" not in json.dumps(context["topics"][0])
    again = DL.resolve(vault, repository, goal_id, client=fake)
    assert again.status == "fresh" and fake.calls == 1


def test_a_correction_is_a_new_input_and_reresolves(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    DL.resolve(vault, repository, goal_id, client=DeliverableFake())
    DL.add_input(vault, repository, goal_id, "correction", text="not determinants; we skipped them")
    fake = DeliverableFake(excluded=("Determinants",))
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert result.status == "ready" and [e["learning_object_id"] for e in result.resolution["learning_objects"]] == [
        "lo_eigen"]
    assert [entry["kind"] for entry in fake.contexts[0]["inputs"]] == ["text", "correction"]


def test_unmatched_phrases_never_create_an_lo_without_the_learners_yes(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "eigenvalues and jordan form")
    before = set(load_vault(paths.root).learning_objects)
    result = DL.resolve(vault, repository, goal_id, client=DeliverableFake(unmatched=("jordan form",)))
    assert [entry["phrase"] for entry in result.resolution["unmatched"]] == ["jordan form"]
    assert result.resolution["unmatched"][0]["status"] == "open"
    assert set(load_vault(paths.root).learning_objects) == before  # nothing created
    declined = DL.decide_unmatched(load_vault(paths.root), repository, goal_id, "jordan form", "decline")
    assert declined["created"] is None and declined["resolution"]["unmatched"][0]["status"] == "declined"
    assert set(load_vault(paths.root).learning_objects) == before


def test_add_it_creates_the_lo_through_create_goal_lo_and_joins_the_scope(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "eigenvalues and jordan form")
    DL.resolve(vault, repository, goal_id, client=DeliverableFake(unmatched=("jordan form",)))
    out = DL.decide_unmatched(load_vault(paths.root), repository, goal_id, "jordan form", "create")
    lo_id = out["created"]["learning_object_id"]
    vault = load_vault(paths.root)
    learning_object = vault.learning_objects[lo_id]
    assert learning_object.provenance.origin == "codex_proposal"
    assert learning_object.provenance.mechanism == GL.DELIVERABLE_MECHANISM
    assert learning_object.provenance.goal_id == goal_id and learning_object.subjects == ["linear-algebra"]
    resolution = out["resolution"]
    assert resolution["origin"] == "learner" and resolution["unmatched"][0]["status"] == "created"
    assert lo_id in [entry["learning_object_id"] for entry in resolution["learning_objects"]]
    assert _rows(repository, "SELECT judge, verdict FROM judgment_ledger WHERE id = ?", (resolution["ledger_id"],)) == [
        ("learner_card", "create")]
    # Idempotent per request: a retry names the same LO and writes no second one.
    again = GL.create_goal_lo(paths.root, repository, GL.GoalLoRequest(
        goal_id=goal_id, phrase="jordan form", title="Jordan Form",
        statement="What jordan form means and how to use it.", subject_id="linear-algebra"))
    assert again == {"learning_object_id": lo_id, "concept_id": out["created"]["concept_id"], "created": False}


def test_create_goal_lo_keeps_the_text_gap_cap_plus_one_and_undoes_to_dormant(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[learner_text_gaps]\nmax_creations_per_day = 0")
    request = GL.GoalLoRequest(goal_id="goal_x", phrase="jordan form", title="Jordan form",
                               statement="A matrix's Jordan normal form.", subject_id="linear-algebra")
    first = GL.create_goal_lo(paths.root, repository, request)
    assert first["created"]  # an explicit goal may exceed the cap by one a day
    with pytest.raises(GL.GoalLoError) as caught:
        GL.create_goal_lo(paths.root, repository, GL.GoalLoRequest(
            goal_id="goal_x", phrase="schur form", title="Schur form", statement="Schur decomposition.",
            subject_id="linear-algebra"))
    assert caught.value.code == "capped"
    undone = GL.undo_goal_lo(paths.root, repository, first["learning_object_id"])
    assert undone["status"] == "dormant"
    assert load_vault(paths.root).learning_objects[first["learning_object_id"]].status == "dormant"
    with pytest.raises(GL.GoalLoError):
        GL.undo_goal_lo(paths.root, repository, "lo_eigen")  # only goal LOs


def test_gc2_an_exam_passage_is_refused_as_a_scope_input_and_nothing_is_written(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    before = table_counts(repository)
    for extraction_id, spans in (("ext_exam", ["s2"]), ("ext_lay", ["s9"])):  # the exam; the held-out unit
        with pytest.raises(DL.DeliverableError) as caught:
            DL.add_input(vault, repository, goal_id, "passage", extraction_id=extraction_id, span_ids=spans)
        assert caught.value.code == "exam_material" and str(caught.value) == DL.EXAM_REFUSAL
    assert table_counts(repository) == before


def test_a_book_passage_is_read_through_the_predicate_when_resolved(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "my syllabus")
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_book", span_ids=["s2"])
    fake = DeliverableFake()
    DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    passage = fake.contexts[0]["inputs"][1]
    assert passage["kind"] == "passage" and "characteristic polynomial" in passage["text"]


def test_gc1_no_exam_or_held_out_text_reaches_the_resolver(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "eigenvalues for the midterm")
    cover_all(paths, repository, "lo_eigen")
    fake = DeliverableFake()
    DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    for prompt in fake.prompts:
        assert EXAM_QUESTION not in prompt and "HELDOUTSENTINEL" not in prompt and HELD_OUT_SENTINEL not in prompt


def test_a_model_failure_is_unavailable_and_writes_nothing(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    before = table_counts(repository)
    result = DL.resolve(vault, repository, goal_id, client=DeliverableFake(fail=RuntimeError("boom")))
    assert result.status == "unavailable" and result.reason == "failed"
    after = table_counts(repository)
    assert after.pop("model_call_receipts") >= before.pop("model_call_receipts")  # the failed call's receipt
    assert after == before


def test_without_a_fake_the_models_are_off(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    result = DL.resolve(vault, repository, goal_id)
    assert result.status == "unavailable" and result.reason == "models_off"


def test_the_depth_is_an_input_the_newest_standing(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository)
    assert DL.depth_of(repository, goal_id) is None
    DL.add_input(vault, repository, goal_id, "depth", text="fluency")
    DL.add_input(vault, repository, goal_id, "depth", text="get_the_idea")
    assert DL.depth_of(repository, goal_id) == "get_the_idea"
    with pytest.raises(DL.DeliverableError):
        DL.add_input(vault, repository, goal_id, "depth", text="deep")


def test_only_a_learner_goal_is_a_deliverable(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    other = next((goal for goal in vault.goals if goal.creation_source != "learner"), None)
    with pytest.raises(DL.DeliverableError):
        DL.add_input(vault, repository, other.id if other else "goal_missing", "text", text="x")


def test_also_about_is_resolved_by_the_same_resolver_and_kept_as_a_learner_row(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    fake = DeliverableFake()
    out = DL.also_about(vault, repository, "ext_book", "ch_det", "this is really about determinants", client=fake)
    assert out["status"] == "corrected" and out["learning_object_id"] == "lo_det"
    assert fake.purposes == ["scope"]
    rows = _rows(repository, "SELECT learner_override, learner_text, origin FROM section_coverage "
                             "WHERE section_id = 'ch_det'")
    assert rows == [("is_about", "this is really about determinants", "learner")]
    none = DL.also_about(vault, repository, "ext_book", "ch_det", "xyzzy", client=DeliverableFake(needs=()))
    assert none["status"] == "unmatched"
    with pytest.raises(DL.DeliverableError):
        DL.also_about(vault, repository, "ext_exam", "exam_q", "eigenvalues", client=fake)


def test_scope_view_lists_topics_unmatched_and_the_receipt(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _deliverable(paths, repository, "eigenvalues and jordan form")
    DL.resolve(vault, repository, goal_id, client=DeliverableFake(unmatched=("jordan form",)))
    view = DL.scope_view(load_vault(paths.root), repository, goal_id)
    assert [topic["learning_object_id"] for topic in view["topics"]] == ["lo_eigen"]
    assert view["unmatched"][0]["phrase"] == "jordan form" and view["resolution"]["origin"] == "resolver"
    assert view["kind"] == "quest" and view["depth"] is None
    assert SC.enabled(vault) and BOOK_EIGEN == "ch_eigen"
