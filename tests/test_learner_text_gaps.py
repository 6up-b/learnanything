"""Learner-text gaps (implementation_handoffs §4): one pipeline from learner text to
named prerequisites and misconceptions. Every model is a fake."""

from __future__ import annotations

from contextlib import closing
import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.diagnosis.text_gaps.actions import UndoError, reverse_gap, would_cycle
from learnloop.diagnosis.text_gaps.contract import PrerequisiteDraft
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, named_gaps_for_card, process_learner_text
from learnloop.diagnosis.text_gaps.sources import tutor_question_text
from learnloop.tutor.ai_contracts import TUTOR_QA_PROMPT_VERSION, LearnerGap
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.lifecycle import LEARNER_TEXT_GAP_DISABLED, practice_item_serving_block
from learnloop.vault.loader import add_note, load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, NOW_ISO, append_config_toml, create_placement_vault
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake, GapTutor, always, seed_proposal, word_match

EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")


def _vault(tmp_path, *, version: str = "mvp-0.13", toml: str = ""):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    if toml:
        append_config_toml(paths.root, toml)
    return paths.root, Repository(paths.sqlite_path)


def _ask(root, repository, tutor, *, item="pi_diag_easy", question="What is an eigenvalue? I can't diagonalize."):
    vault = load_vault(root)
    return ask_question(vault, repository, tutor, context="practice", question_md=question,
                        practice_item_id=item, session_id="sess_1", clock=FrozenClock(NOW))


def _run(root, repository, event_id, *, llm=None, decider=None, tutor=None):
    llm = llm or GapLLMFake()
    clients = PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                              drafter=lambda: llm, tutor=(lambda: tutor) if tutor else None, embedder=None)
    text = tutor_question_text(load_vault(root), repository, event_id)
    return process_learner_text(root, repository, text, clients=clients, clock=FrozenClock(NOW))


def _ledger(repository, task):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT task, left_kind, left_id, right_kind, right_id, judge, judge_model, verdict "
            "FROM judgment_ledger WHERE task = ? ORDER BY rowid", (task,))]


# -- the tutor names the gap ---------------------------------------------------------------


def test_the_tutor_names_the_gap_in_the_answering_call_and_it_is_persisted(tmp_path):
    root, repository = _vault(tmp_path)
    tutor = GapTutor(EIGEN_GAP)
    result = _ask(root, repository, tutor)
    assert result["learner_gap"]["kind"] == "prerequisite"
    assert result["learner_gap"]["prerequisite_name"] == "Eigenvalues"
    event = repository.question_event(result["event_id"])
    assert event["source_context"]["learner_gap"]["prompt_version"] == TUTOR_QA_PROMPT_VERSION
    assert event["source_context"]["learner_gap"]["model"] == "fake/tutor"
    assert TUTOR_QA_PROMPT_VERSION.startswith("mvp-0.9-tutor-qa-learner-gap")


# -- prerequisites ------------------------------------------------------------------------------


def test_a_declared_prerequisite_matches_with_both_judges_logged_and_no_edge(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy",
                    question="What's an eigenvalue again?")["event_id"]
    decider = ChoiceDecider(kind="prerequisite", pair=word_match("eigenvalues"))
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("eigenvalues")), decider=decider)
    assert row["action"] == "matched_prerequisite"
    assert row["target_id"] == "lo_eigen_basics" and row["target_subject_id"] == "linear-algebra"
    assert row["edge_id"] is None and row["detail"]["edge"] == "declared"
    kinds = _ledger(repository, "learner_gap_kind")
    assert {(r["judge"], r["verdict"]) for r in kinds} == {("llm", "prerequisite"), ("decider", "prerequisite")}
    pairs = _ledger(repository, "same_prerequisite")
    assert {r["judge"] for r in pairs} == {"llm", "decider"}
    assert all(r["left_kind"] == "learner_gap" and r["right_kind"] == "learning_object" for r in pairs)


def test_an_undeclared_match_adds_an_edge_after_a_needed_yes_and_one_tap_undo_removes_it(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("eigenvalues"), needed="yes"),
               decider=ChoiceDecider(kind="prerequisite", needed="no"))
    assert row["action"] == "matched_prerequisite" and row["target_id"] == "lo_eigen_basics"
    edge = next(edge for edge in load_vault(root).edges if edge.id == row["edge_id"])
    assert (edge.source, edge.target, edge.relation_type) == ("eigenvalues", "diagonalization", "prerequisite")
    assert (edge.model_extra or {})["provenance"]["mechanism"] == "learner_text_gap_v1"
    assert "Added from your question" in edge.rationale
    needed = _ledger(repository, "prerequisite_needed")
    assert {(r["judge"], r["verdict"]) for r in needed} == {("llm", "yes"), ("decider", "no")}
    assert reverse_gap(root, repository, row["id"], "undo_edge")["status"] == "reversed"
    assert row["edge_id"] not in {edge.id for edge in load_vault(root).edges}
    assert reverse_gap(root, repository, row["id"], "undo_edge")["status"] == "already_reversed"
    with pytest.raises(UndoError):
        reverse_gap(root, repository, row["id"], "undo_creation")


def test_a_needed_no_adds_no_edge(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("eigenvalues"), needed="no"))
    assert row["action"] == "matched_prerequisite" and row["edge_id"] is None
    assert row["detail"]["edge"] == "not_needed"


def test_an_edge_that_would_close_a_cycle_is_refused(tmp_path):
    root, repository = _vault(tmp_path)
    spectral_gap = LearnerGap(prerequisite_name="Spectral theorem", prerequisite_line="Symmetric matrices diagonalize.",
                              kind="prerequisite")
    # Asked on an eigenvalues item: the spectral theorem builds ON eigenvalues.
    event_id = _ask(root, repository, GapTutor(spectral_gap), item="pi_eig_easy")["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("spectral"), needed="yes"))
    assert row["action"] == "matched_prerequisite" and row["target_id"] == "lo_spectral"
    assert row["edge_id"] is None and row["detail"]["edge"] == "refused_cycle"
    vault = load_vault(root)
    assert would_cycle(vault, "spectral_theorem", "eigenvalues")
    assert not would_cycle(vault, "eigenvalues", "diagonalization")


def test_candidates_are_grounded_in_the_asking_subject(tmp_path):
    root, repository = _vault(tmp_path)
    from learnloop.vault.loader import add_subject

    add_subject(root, "physics", "Physics", clock=FrozenClock(NOW))
    upsert_learning_object(root, {
        "id": "lo_phys_eigen", "title": "Eigenvalues of operators", "subjects": ["physics"], "concept": "eigenvalues",
        "knowledge_type": "definition", "status": "active", "summary": "Eigenvalues in quantum mechanics.",
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")["event_id"]
    llm = GapLLMFake(decide=word_match("eigenvalues"))
    row = _run(root, repository, event_id, llm=llm)
    judged = [payload["context"] for purpose, payload in llm.calls if purpose == "learner_gap_same_prerequisite"]
    seen = " ".join(str(context) for context in judged)
    assert "Eigenvalues of operators" not in seen
    assert row["target_id"] == "lo_eigen_basics"
    assert row["detail"]["candidates"]["excluded_cross_subject"] >= 1


# -- a missing prerequisite ----------------------------------------------------------------


def _source_note(root):
    add_note(root, "linear-algebra", "la_source", "Diagonalization source",
             "A matrix with n independent eigenvectors diagonalizes.", source_type="canonical_source",
             related_los=["lo_diag"], clock=FrozenClock(NOW))


EIGENVECTOR_GAP = LearnerGap(prerequisite_name="Eigenvectors", prerequisite_line="Vectors a matrix only scales.",
                             kind="prerequisite")


def _create(root, repository, *, question="What even is an eigenvector?", llm=None):
    tutor = GapTutor(EIGENVECTOR_GAP)
    event_id = _ask(root, repository, tutor, question=question)["event_id"]
    llm = llm or GapLLMFake(decide=always("different"), proposal=seed_proposal())
    return _run(root, repository, event_id, llm=llm, tutor=tutor), llm


def test_a_missing_prerequisite_is_drafted_created_live_seeded_and_committed(tmp_path):
    root, repository = _vault(tmp_path)
    _source_note(root)
    row, llm = _create(root, repository)
    assert row["action"] == "created_prerequisite"
    vault = load_vault(root)
    created = vault.learning_objects[row["created_learning_object_id"]]
    assert created.subjects == ["linear-algebra"] and created.title == "Define an eigenvector"
    assert (created.provenance.model_extra or {})["mechanism"] == "learner_text_gap_v1"
    assert vault.concepts[row["created_concept_id"]].title == "Eigenvectors"
    edge = next(edge for edge in vault.edges if edge.id == row["edge_id"])
    assert (edge.source, edge.target) == (created.concept, "diagonalization")
    assert (edge.model_extra or {})["provenance"]["origin"] == "creation"
    # Codex review F7: the asking LO's source notes cover the material that
    # builds on the prerequisite, not the prerequisite, so they are not its
    # grounding: the promotion path's own rule sends the seed to review.
    assert row["seed_status"] == "review_required" and row["seed_practice_item_id"]
    assert row["seed_practice_item_id"] not in vault.practice_items
    promotion = repository.question_promotion(row["source_id"])
    assert promotion["route"] == "review_required"
    assert [purpose for purpose, _ in llm.calls].count("learner_gap_prerequisite_draft") == 1
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        commitments = store.commitments(connection)
    assert [(c["learning_object_id"], c["practice_item_id"]) for c in commitments] == [
        (created.id, row["seed_practice_item_id"])]
    from learnloop.placement.state import load_placement_state

    state = load_placement_state(vault, repository, now_iso=NOW_ISO)
    assert created.id in state.committed_learning_object_ids
    assert state.open_by_lo[created.id].source == "learner_text_gap"


def test_undo_creation_puts_the_lo_away_and_removes_its_edge_and_commitment(tmp_path):
    root, repository = _vault(tmp_path)
    _source_note(root)
    row, _llm = _create(root, repository)
    result = reverse_gap(root, repository, row["id"], "undo_creation")
    assert result["status"] == "reversed"
    vault = load_vault(root)
    assert vault.learning_objects[row["created_learning_object_id"]].status == "dormant"
    assert row["edge_id"] not in {edge.id for edge in vault.edges}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert store.commitments(connection) == []


def test_a_second_question_matches_the_days_creation_instead_of_creating_again(tmp_path):
    root, repository = _vault(tmp_path)
    _source_note(root)
    first, _llm = _create(root, repository)
    second, _llm = _create(root, repository, question="Eigenvectors: what are they?",
                           llm=GapLLMFake(decide=word_match("eigenvector"), proposal=seed_proposal("pi_other")))
    assert second["action"] == "matched_prerequisite"
    assert second["target_id"] == first["created_learning_object_id"]
    # The first creation's edge already declares it, and it is a same-day
    # creation too: either way it is a candidate, and nothing is created twice.
    assert second["created_learning_object_id"] is None
    assert len([lo for lo in load_vault(root).learning_objects if lo.startswith("lo_ltg_")]) == 1


def test_the_daily_creation_cap_holds(tmp_path):
    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\nmax_creations_per_day = 1\n")
    _source_note(root)
    _create(root, repository)
    other_gap = LearnerGap(prerequisite_name="Determinants", prerequisite_line="A scalar of a square matrix.",
                           kind="prerequisite")
    tutor = GapTutor(other_gap)
    event_id = _ask(root, repository, tutor, question="What's a determinant?")["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=always("different")), tutor=tutor)
    assert row["action"] == "unmatched_prerequisite" and row["detail"]["reason"] == "daily_cap"


def _accept_seed(root, row, item_id="pi_ltg_seed_accepted"):
    """The owner accepted the seed item (written straight to the vault here)."""

    from learnloop.vault.writer import upsert_practice_item

    upsert_practice_item(root, {
        "id": item_id, "learning_object_id": row["created_learning_object_id"], "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0}, "prompt": "What is an eigenvector of a matrix A?",
        "expected_answer": "A nonzero vector v with Av = lambda v.",
        "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4,
                                                           "description": "Defines it."}], "fatal_errors": []},
        "provenance": {"origin": "human", "source_refs": []}, "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })
    return item_id


def test_switching_creation_off_stops_serving_created_los(tmp_path):
    root, repository = _vault(tmp_path)
    _source_note(root)
    row, _llm = _create(root, repository)
    item_id = _accept_seed(root, row)
    assert practice_item_serving_block(load_vault(root), load_vault(root).practice_items[item_id]) is None
    append_config_toml(root, "[learner_text_gaps]\ncreate_prerequisites_enabled = false\n")
    vault = load_vault(root)
    assert practice_item_serving_block(vault, vault.practice_items[item_id]) == LEARNER_TEXT_GAP_DISABLED


def test_an_unsure_verdict_never_creates(tmp_path):
    root, repository = _vault(tmp_path)
    tutor = GapTutor(EIGENVECTOR_GAP)
    event_id = _ask(root, repository, tutor)["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=always("unsure")), tutor=tutor)
    assert row["action"] == "unmatched_prerequisite" and row["detail"]["reason"] == "unsure"
    assert row["created_learning_object_id"] is None


# -- misconceptions --------------------------------------------------------------------------


BELIEF = LearnerGap(belief_statement="Every matrix can be diagonalized.", kind="misconception")


def test_a_tutor_question_that_states_a_belief_reaches_the_holding_pen(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(BELIEF, question_type="verification"),
                    question="Since every matrix diagonalizes, why bother checking?")["event_id"]
    row = _run(root, repository, event_id, decider=ChoiceDecider(kind="misconception"))
    assert row["action"] == "belief_candidate" and row["target_kind"] == "candidate"
    candidates = repository.misconception_candidates_for_learning_object("lo_diag")
    assert [c["statement"] for c in candidates] == ["Every matrix can be diagonalized."]
    # The diagnoser's registry block reads the holding pen: the belief is there.
    from learnloop.diagnosis.split.history import AttemptRef, VaultHistoryStore

    registry = VaultHistoryStore(load_vault(root), repository).registry_before(
        AttemptRef(attempt_id="zz", completed_at="2999-01-01T00:00:00Z"), ["lo_diag"])
    assert [(record.kind, record.statement) for record in registry] == [
        ("candidate", "Every matrix can be diagonalized.")]
    result = reverse_gap(root, repository, row["id"], "not_this_belief")
    assert result["status"] == "reversed"
    assert repository.misconception_candidate_by_id(row["target_id"])["status"] == "withdrawn"
    taps = _ledger(repository, "same_belief")
    assert [(t["judge"], t["verdict"]) for t in taps] == [("learner_card", "different")]


def test_a_belief_matching_a_holding_pen_candidate_is_a_sighting_and_the_decider_never_joins(tmp_path):
    root, repository = _vault(tmp_path)
    candidate_id = repository.insert_misconception_candidate(
        learning_object_id="lo_diag", statement="All matrices are diagonalizable.",
        statement_normalized="all matrices are diagonalizable", occurrence_count=1,
    )
    event_id = _ask(root, repository, GapTutor(BELIEF), question="Every matrix diagonalizes, right?")["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=always("same")),
               decider=ChoiceDecider(kind="misconception", pair=always("different")))
    assert row["action"] == "belief_sighting" and row["target_id"] == candidate_id
    assert repository.misconception_candidate_by_id(candidate_id)["occurrence_count"] == 2
    assert {(r["judge"], r["verdict"]) for r in _ledger(repository, "same_belief")} == {
        ("llm", "same"), ("decider", "different")}


# -- the chooser -------------------------------------------------------------------------------


def test_the_decider_as_chooser_decides_the_kind_and_both_readings_are_logged(tmp_path):
    root, repository = _vault(tmp_path, toml='[learner_text_gaps]\nchooser = "decider"\n')
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    row = _run(root, repository, event_id, decider=ChoiceDecider(kind="none"))
    assert (row["chooser"], row["context_kind"], row["decider_kind"], row["kind"]) == (
        "decider", "prerequisite", "none", "none")
    assert row["action"] == "none"
    assert {(r["judge"], r["verdict"]) for r in _ledger(repository, "learner_gap_kind")} == {
        ("llm", "prerequisite"), ("decider", "none")}


def test_the_decider_as_chooser_is_the_authoritative_prerequisite_judge(tmp_path):
    root, repository = _vault(tmp_path, toml='[learner_text_gaps]\nchooser = "decider"\n')
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=always("different")),
               decider=ChoiceDecider(kind="prerequisite", pair=word_match("eigenvalues")))
    assert row["action"] == "matched_prerequisite" and row["target_id"] == "lo_eigen_basics"
    assert row["detail"]["judges"]["authoritative"] == "decider"


# -- fallback, kinds without action ------------------------------------------------------------------


def test_without_a_reading_nothing_is_targeted_and_the_grounded_rule_stays(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(None, question_type="prerequisite"))["event_id"]
    row = _run(root, repository, event_id, decider=None)
    assert (row["kind"], row["action"], row["target_id"]) == ("unread", "none", None)
    from learnloop.field.signals import learner_gap_targets

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert learner_gap_targets(connection, load_vault(root)) == []


@pytest.mark.parametrize("kind", ["slip", "wording"])
def test_slip_and_wording_are_signals_only_and_listed_for_batch_review(tmp_path, kind):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(LearnerGap(kind=kind)))["event_id"]
    row = _run(root, repository, event_id)
    assert row["action"] == "signal_only" and row["target_id"] is None
    from learnloop.diagnosis.text_gaps.report import batch_review

    assert [entry["gap_id"] for entry in batch_review(repository)] == [row["id"]]
    # Error types are never created automatically.
    assert set(load_vault(root).error_types) == {"conceptual_slip"}


def test_a_matched_target_is_the_questions_weak_signal_with_its_subject(tmp_path):
    root, repository = _vault(tmp_path)
    # On a diagonalization item, which declares no prerequisite: the grounded
    # rule alone maps this prerequisite question to nothing.
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("eigenvalues"), needed="no"))
    from learnloop.field.signals import load_interaction_signals

    def question_signals():
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            signals = load_interaction_signals(connection, load_vault(root), ())
        return [(s.lo_id, s.signal_type, s.subject_id, s.outcome) for s in signals
                if s.signal_id.startswith(f"question_event:{event_id}:")]

    assert question_signals() == [("lo_eigen_basics", "prerequisite", "linear-algebra", 0.0)]
    append_config_toml(root, "[learner_text_gaps]\nenabled = false\n")
    # Switched off: the grounded rule again (no declared prerequisite, no target).
    assert not [signal for signal in question_signals() if signal[0] == "lo_eigen_basics"]


def test_asking_never_lowers_the_record(tmp_path):
    """G13: the pipeline writes no evidence, mastery or certification."""

    root, repository = _vault(tmp_path)
    tables = ("facet_capability_evidence", "learning_object_mastery", "practice_attempts", "grading_evidence")

    def snapshot():
        with repository.connection() as connection:
            return {table: connection.execute(f"SELECT * FROM {table}").fetchall() for table in tables
                    if connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone()}

    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    from learnloop.substrate.state_sync import sync_vault_state

    sync_vault_state(load_vault(root), repository)
    before = snapshot()
    _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("eigenvalues")))
    assert snapshot() == before


def test_named_gaps_reach_the_learner_state_card(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=word_match("eigenvalues")))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        card = named_gaps_for_card(connection, learning_object_ids=["lo_eigen_basics"])
    assert [(event["event_id"], event["kind"], event["target"]["id"]) for event in card] == [
        (row["id"], "prerequisite", "lo_eigen_basics")]


def test_a_text_is_read_once(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")["event_id"]
    llm = GapLLMFake(decide=word_match("eigenvalues"))
    first = _run(root, repository, event_id, llm=llm)
    calls = len(llm.calls)
    assert _run(root, repository, event_id, llm=llm)["id"] == first["id"]
    assert len(llm.calls) == calls


def test_the_draft_contract_is_strict():
    with pytest.raises(Exception):
        PrerequisiteDraft.model_validate({"concept_title": "x"})


# -- the shortlist -----------------------------------------------------------------------------


def test_the_learning_object_recipe_is_canonical_and_active_only(tmp_path):
    from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES

    root, _repository = _vault(tmp_path)
    vault = load_vault(root)
    recipe = EMBEDDING_RECIPES["learning_object/statement"]
    texts = dict(recipe.texts(vault))
    assert texts["lo_eigen_basics"] == "Title: Eigenvalues\nConcept: Eigenvalues\nStatement: About eigenvalues."
    vault.learning_objects["lo_diag"].status = "dormant"
    assert "lo_diag" not in dict(recipe.texts(vault))


class _Embedder:
    model_id = model = "fake/embed"
    dims = 3
    provider_name = "fake_embed"
    provider_type = "openai_embedding"

    def __init__(self, vectors):
        self.vectors = vectors
        self.calls = []

    def embed(self, inputs, task_prefix):
        self.calls.append((list(inputs), task_prefix))
        return [self.vectors(text) for text in inputs]


def test_the_vault_wide_shortlist_ranks_stored_vectors_and_judges_decide(tmp_path):
    import numpy as np

    from learnloop.db.stores.embedding_vectors import put_vector
    from learnloop.diagnosis.text_gaps.kinds import LO_RECIPE

    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\ntop_k = 1\nmetered_price_per_million = 0.01\n")
    toml = root / "learnloop.toml"
    toml.write_text(toml.read_text().replace(
        'enabled = false\nbackfill_enabled = false\nmodel = "qwen/qwen3-embedding-8b"\ndimensions = 4096',
        'enabled = true\nbackfill_enabled = false\nmodel = "fake/embed"\ndimensions = 3'))
    assert load_vault(root).config.embedding.enabled
    vault = load_vault(root)
    directions = {"lo_eigen_basics": [1.0, 0.0, 0.0], "lo_spectral": [0.0, 1.0, 0.0], "lo_svd_definition": [0.0, 0.0, 1.0]}
    with closing(connect(repository.sqlite_path)) as connection, connection:
        for lo_id, direction in directions.items():
            text = dict(LO_RECIPE.texts(vault))[lo_id]
            put_vector(connection, record_kind="learning_object", record_id=lo_id, field="statement",
                       content_hash=LO_RECIPE.content_hash(text), model_id="fake/embed",
                       task_prefix="retrieval-document", vector=np.asarray(direction))
    embedder = _Embedder(lambda _text: [0.9, 0.1, 0.0])
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    llm = GapLLMFake(decide=word_match("eigenvalues"), needed="no")
    clients = PipelineClients(judge=lambda: llm, decider=None, drafter=lambda: llm, embedder=lambda: embedder)
    row = process_learner_text(root, repository, tutor_question_text(load_vault(root), repository, event_id),
                               clients=clients, clock=FrozenClock(NOW))
    assert embedder.calls == [(["Eigenvalues\nScalars a matrix scales its eigenvectors by."], "retrieval-query")]
    summary = row["detail"]["candidates"]
    assert summary["shortlist_basis"] == "knn" and summary["by_basis"].get("shortlist") == 1
    assert row["action"] == "matched_prerequisite" and row["target_id"] == "lo_eigen_basics"
    judged = " ".join(str(payload) for purpose, payload in llm.calls if purpose == "learner_gap_same_prerequisite")
    assert "SVD definition" not in judged  # top-1: the far LO is never shown to the judge


# -- the CLI --------------------------------------------------------------------------------------


def test_the_cli_dry_runs_send_and_write_nothing(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.diagnosis.text_gaps.jobs import enqueue

    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))["event_id"]
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    runner = CliRunner()
    planned = runner.invoke(app, ["gaps", "run", "--vault", str(root), "--dry-run", "--json"])
    assert planned.exit_code == 0, planned.output
    payload = json.loads(planned.output)
    assert payload["dry_run"] is True and payload["plan"]["queued"] == 1
    assert payload["plan"]["routes"]["learner_gap_decider"] == "openrouter_decider"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert [job["state"] for job in store.jobs(connection)] == ["queued"]
        assert store.gaps(connection) == []
    report = runner.invoke(app, ["gaps", "report", "--vault", str(root), "--dry-run", "--json"])
    assert report.exit_code == 0 and json.loads(report.output)["calls"] == 0
    listed = runner.invoke(app, ["gaps", "list", "--vault", str(root), "--json"])
    assert listed.exit_code == 0 and json.loads(listed.output) == {"gaps": []}


def test_declared_prerequisites_and_the_shortlist_share_the_judge_budget(tmp_path):
    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\njudge_max_pairs = 3\n")
    # lo_spectral declares eigenvalues; give it a second declared prerequisite.
    upsert_learning_object(root, {"id": "lo_spectral", "prerequisites": ["eigenvalues", "diagonalization"],
                                  "subjects": ["linear-algebra"]})
    gap = LearnerGap(prerequisite_name="Singular values", prerequisite_line="SVD factorizes a matrix.",
                     kind="prerequisite")
    event_id = _ask(root, repository, GapTutor(gap), item="pi_spec_easy")["event_id"]
    row = _run(root, repository, event_id, llm=GapLLMFake(decide=always("different")))
    summary = row["detail"]["candidates"]
    # The item's LO, then one declared prerequisite and one shortlisted LO.
    assert summary["candidates"] == 3
    assert summary["by_basis"] == {"item": 1, "declared": 1, "shortlist": 1}


def test_a_library_question_is_anchored_by_its_notes_single_learning_object(tmp_path):
    root, repository = _vault(tmp_path)
    add_note(root, "linear-algebra", "diag_notes", "Diagonalization notes", "Notes on diagonalizing.",
             related_los=["lo_diag"], clock=FrozenClock(NOW))
    vault = load_vault(root)
    event_id = ask_question(vault, repository, GapTutor(BELIEF), context="library",
                            question_md="Every matrix diagonalizes, so why the conditions?",
                            note_id="note_diag_notes", clock=FrozenClock(NOW))["event_id"]
    text = tutor_question_text(load_vault(root), repository, event_id)
    assert text.anchor == "lo_diag" and text.subject_id == "linear-algebra"
    row = _run(root, repository, event_id)
    assert row["action"] == "belief_candidate"
    assert repository.misconception_candidate_by_id(row["target_id"])["learning_object_id"] == "lo_diag"
