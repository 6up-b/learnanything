"""The two DERIVED span projections (spec §7.6, review F5): each adapter's recipe and quality, the live
write-through equal to a rebuild row for row, idempotent replayers, and the hooks on the real writers."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores import span_projections as store
from learnloop.substrate.passage_spans import (
    project_gap,
    project_question_event,
    rebuild_learner_text_gap_spans,
    rebuild_question_event_spans,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from tests.desk_helpers import BOOK, seed_every_adapter, seed_gap, seed_practice_question, seed_reader_exchange
from tests.helpers import NOW, create_basic_vault

QE_IDS = ("qe_reader", "qe_reader_failed", "qe_practice_placed", "qe_feedback_unplaced", "qe_library")
GAP_IDS = ("g_tutor", "g_formative", "g_workbench", "g_note", "g_stuck", "g_diagnosis", "g_hint", "g_lesson", "g_chat")


def _repository(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return paths, Repository(paths.sqlite_path)


def _seeded(tmp_path):
    paths, repository = _repository(tmp_path)
    with repository.connection() as connection:
        seeded = seed_every_adapter(connection)
    return paths, repository, seeded["vault"]


def _live(repository, vault):
    """The write-through: each source projected as its writer projects it."""

    with repository.connection() as connection:
        for question_event_id in QE_IDS:
            project_question_event(connection, vault, question_event_id)
        for gap_id in GAP_IDS:
            project_gap(connection, vault, gap_id)


def _snapshot(repository):
    with repository.connection() as connection:
        return {table: [tuple(sorted(row.items())) for row in store.rows_for(connection, table)]
                for table in ("question_event_spans", "learner_text_gap_spans")}


def _by(rows, key):
    out: dict[str, set[tuple]] = {}
    for row in rows:
        row = dict(row)
        out.setdefault(row[key], set()).add((row["extraction_id"], row["span_id"], row["role"], row["quality"],
                                             row["learning_object_id"]))
    return out


def test_each_exchange_adapter_places_rows_by_its_recipe(tmp_path):
    _paths, repository, vault = _seeded(tmp_path)
    _live(repository, vault)
    rows = _by(_snapshot(repository)["question_event_spans"], "question_event_id")
    # A Reader exchange: its anchor and selection exactly, the answer's citations; never the passages the
    # tutor was merely given (the manifest's neighbours).
    assert rows["qe_reader"] == {
        (BOOK, "s2", "selection", "exact_selection", None), (BOOK, "s3", "selection", "exact_selection", None),
        (BOOK, "s4", "cited", "citation", None), (BOOK, "s5", "cited", "citation", None)}
    # An exchange whose answer never came keeps its anchor.
    assert rows["qe_reader_failed"] == {(BOOK, "s6", "selection", "exact_selection", None)}
    # A practice question: its item's source passages; with none, only its learning object.
    assert rows["qe_practice_placed"] == {(BOOK, "s7", "context", "source_context", None)}
    assert rows["qe_feedback_unplaced"] == {(None, None, "context", "unanchored", "lo_unplaced")}
    # A library question has no passage recipe.
    assert "qe_library" not in rows


def test_each_gap_adapter_places_rows_by_its_recipe(tmp_path):
    _paths, repository, vault = _seeded(tmp_path)
    _live(repository, vault)
    rows = _by(_snapshot(repository)["learner_text_gap_spans"], "gap_id")
    assert rows["g_tutor"] == {
        (BOOK, "s2", "selection", "exact_selection", None), (BOOK, "s3", "selection", "exact_selection", None),
        (BOOK, "s4", "cited", "citation", None), (BOOK, "s5", "cited", "citation", None)}
    assert rows["g_formative"] == {(BOOK, "s2", "selection", "exact_selection", None)}  # the anchor, not the section
    assert rows["g_workbench"] == {(BOOK, "s3", "context", "source_context", None),
                                   (BOOK, "s4", "context", "source_context", None)}
    assert rows["g_note"] == {(BOOK, "s5", "selection", "exact_selection", None)}
    assert rows["g_stuck"] == {(BOOK, "s7", "context", "source_context", None)}
    assert rows["g_diagnosis"] == {(None, None, "context", "unanchored", "lo_unplaced")}
    assert rows["g_hint"] == {(None, None, "context", "unanchored", "lo_unplaced")}
    assert rows["g_lesson"] == {(None, None, "context", "unanchored", "lo_lesson")}
    # No passage and no learning object: nothing is invented.
    assert "g_chat" not in rows


def test_a_hidden_note_link_places_nothing(tmp_path):
    from tests.desk_helpers import seed_note_link, stub_vault

    _paths, repository = _repository(tmp_path)
    with repository.connection() as connection:
        seed_note_link(connection, note_id="ln_h", note_key="tend:h", extraction_id=BOOK, span_id="s1")
        seed_note_link(connection, note_id="ln_h", note_key="tend:h", extraction_id=BOOK, span_id="s1",
                       status="rejected", created_at="2026-05-19T10:00:00Z")
        seed_gap(connection, gap_id="g_hidden", source_kind="learner_note", source_id="ln_h")
        project_gap(connection, stub_vault(), "g_hidden")
        assert store.rows_for(connection, "learner_text_gap_spans", ["g_hidden"]) == []


def test_the_live_projection_equals_a_rebuild_for_every_adapter(tmp_path):
    _paths, repository, vault = _seeded(tmp_path)
    _live(repository, vault)
    live = _snapshot(repository)
    assert live["question_event_spans"] and live["learner_text_gap_spans"]
    rebuild_question_event_spans(vault, repository)
    rebuild_learner_text_gap_spans(vault, repository)
    assert _snapshot(repository) == live


def test_a_rebuild_from_empty_tables_reproduces_the_live_rows_and_is_idempotent(tmp_path):
    _paths, repository, vault = _seeded(tmp_path)
    _live(repository, vault)
    live = _snapshot(repository)
    repository.clear_derived_projection_tables(["question_event_spans", "learner_text_gap_spans"])
    assert _snapshot(repository) == {"question_event_spans": [], "learner_text_gap_spans": []}
    first = (rebuild_question_event_spans(vault, repository), rebuild_learner_text_gap_spans(vault, repository))
    assert _snapshot(repository) == live
    second = (rebuild_question_event_spans(vault, repository), rebuild_learner_text_gap_spans(vault, repository))
    assert _snapshot(repository) == live
    assert [report["written"] for report in first] == [report["written"] for report in second]
    assert second[0]["cleared_rows_by_table"] == {"question_event_spans": len(live["question_event_spans"])}


def test_projecting_a_source_twice_keeps_one_copy_of_each_row(tmp_path):
    _paths, repository, vault = _seeded(tmp_path)
    _live(repository, vault)
    once = _snapshot(repository)
    _live(repository, vault)
    assert _snapshot(repository) == once


def test_the_umbrella_rebuild_runs_both_replayers(tmp_path):
    paths, repository = _repository(tmp_path)
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        seed_reader_exchange(connection, question_event_id="qe_a", extraction_id=BOOK, anchor="s1", selection=["s2"])
        seed_practice_question(connection, question_event_id="qe_b", practice_item_id="pi_svd_define_001")
        seed_gap(connection, gap_id="g_a", source_kind="tutor_question", source_id="qe_a")
        connection.commit()
    result = rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW))
    by_name = {replayer.name: replayer for replayer in result.replayers}
    assert by_name["question_event_spans"].rows_processed == 3
    assert by_name["learner_text_gap_spans"].rows_processed == 2
    rows = _by(_snapshot(repository)["question_event_spans"], "question_event_id")
    # The basic vault's item has no source passage: the question keeps its learning object.
    assert rows["qe_b"] == {(None, None, "context", "unanchored", "lo_svd_definition")}


def test_a_practice_question_is_projected_as_the_tutor_records_it(tmp_path):
    from learnloop.tutor.ai_contracts import TutorAnswer
    from learnloop.tutor.tutor_qa import ask_question
    from tests.structured_ai import StructuredClientFake

    class Tutor(StructuredClientFake):
        provider_name = "fake_tutor"
        provider_type = "fake"
        model = "fake-model"

        def run_tutor_qa(self, context):
            return TutorAnswer(answer_md="Start from the definition.", question_type="mechanism",
                               facets=list(context.candidate_facets))

    paths, repository = _repository(tmp_path)
    vault = load_vault(paths.root)
    result = ask_question(vault, repository, Tutor(), context="practice", question_md="Why orthogonal?",
                          practice_item_id="pi_svd_define_001", session_id="sess_1", clock=FrozenClock(NOW))
    live = _snapshot(repository)
    assert _by(live["question_event_spans"], "question_event_id")[result["event_id"]] == {
        (None, None, "context", "unanchored", "lo_svd_definition")}
    rebuild_question_event_spans(vault, repository)
    assert _snapshot(repository) == live
