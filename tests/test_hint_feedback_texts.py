"""Adaptive hints H2b: the ``hint_feedback`` learner-text adapter (spec_adaptive_hints_v1 §9, §5).

Text the learner writes back to a hint on the practice screen is learner
text: a "doesn't connect" reply's text (``help_assists.feedback_text`` on a
``request = 'feedback'`` row, role ``hint_feedback``) and an answer to a
discriminating question (an ``assist_kind = 'discriminate_answer'`` row, role
``discriminate_answer``). Each is queued when its row is written (so a gap
named mid-attempt joins the next hint's rivals), read by learner-text gaps'
reader, and writes only gap rows, their jobs, ledger rows and receipts: no
attempt, evidence, mastery, FSRS state or probe observation. Empty replies,
switches off and the workbench's rows queue nothing. Every model is a fake.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps.contract import NON_SERVING_SOURCE_KINDS, READABLE_SOURCE_KINDS, SOURCE_KINDS
from learnloop.diagnosis.text_gaps.jobs import enqueue_hint_feedback, process_next_gap_job
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.diagnosis.text_gaps.sources import hint_feedback_row, learner_text
from learnloop.hints.discriminating import open_rivals
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, add_hypothesis, hint_vault, prefer, store_map
from tests.text_gap_fakes import GapLLMFake

GAP_TABLES = {"learner_text_gaps", "learner_text_gap_jobs", "judgment_ledger", "model_call_receipts",
              "text_write_provenance", "interaction_events", "judgment_work_claims", "model_work_checkpoints"}
#: A misconception reading may record a belief sighting or candidate (the
#: pipeline's own tables, content only).
BELIEF_TABLES = {"misconception_sightings", "belief_candidates", "misconception_candidates"}
EVIDENCE = ("practice_attempts", "reveal_events", "facet_capability_evidence", "attempt_diagnoses", "help_assists",
            "probe_observations")


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, config: str = ""):
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n' + config)
    store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    ctx.post_attempt_worker.autostart = False
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _hint(ctx, session, option="next_step@L3", **params):
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                                "answerMd": WORK, **params})["result"]


def _jobs(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_kind, source_id, state FROM learner_text_gap_jobs ORDER BY created_at, id")]


def _counts(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in tables}


def test_a_doesnt_connect_reply_with_text_is_queued_when_written_and_wakes_the_worker(tmp_path, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    woken: list[bool] = []
    monkeypatch.setattr(ctx.post_attempt_worker, "notify", lambda: woken.append(True))
    first = _hint(ctx, session)
    reply = _hint(ctx, session, request="feedback", answeredAssistId=first["assistId"],
                  feedbackShortcut="not_where_stuck", feedbackText="I think the +1 is fine, F can be 1.5")
    assert _jobs(paths) == [("hint_feedback", reply["assistId"], "queued")]
    assert woken == [True]
    # An empty reply (allowed) has no text to read: nothing queued.
    _hint(ctx, session, request="feedback", answeredAssistId=first["assistId"])
    assert len(_jobs(paths)) == 1


def test_a_discriminating_answer_is_queued_with_its_role(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    add_hypothesis(paths.sqlite_path, "h1", "The learner thinks a CDF can exceed one.")
    add_hypothesis(paths.sqlite_path, "h2", "The learner adds a constant of integration twice.")
    question = _hint(ctx, session, option="discriminating@L1")
    assert question["kind"] == "discriminating"
    answer = _call(ctx, "practice.answer_discriminating", {
        "sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
        "questionAssistId": question["assistId"], "answerMd": "it gives 1"})
    assert _jobs(paths) == [("hint_feedback", answer["assistId"], "queued")]
    repository = Repository.attach(paths.sqlite_path)
    assert hint_feedback_row(repository, answer["assistId"])["role"] == "discriminate_answer"
    text = learner_text(load_vault(paths.root), repository, "hint_feedback", answer["assistId"])
    assert (text.text, text.context["role"], text.practice_item_id) == ("it gives 1", "discriminate_answer", ITEM)
    assert text.context["question_asked"] == question["hintMd"]


def test_the_reader_sees_the_reply_its_hint_and_question_never_an_answer_key(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    first = _hint(ctx, session)
    reply = _hint(ctx, session, request="feedback", answeredAssistId=first["assistId"], feedbackShortcut="too_big",
                  feedbackText="too far ahead for me")
    vault = load_vault(paths.root)
    text = learner_text(vault, Repository.attach(paths.sqlite_path), "hint_feedback", reply["assistId"])
    assert (text.source_kind, text.context_judge, text.text) == ("hint_feedback", "gap_reader", "too far ahead for me")
    assert text.context["role"] == "hint_feedback" and text.context["shortcut"] == "too_big"
    assert text.context["hint_replied_to"] == first["hintMd"]
    assert text.anchor_learning_object_ids == (vault.practice_items[ITEM].learning_object_id,)
    expected = str(vault.practice_items[ITEM].expected_answer)
    assert expected not in str(text.context)
    # A reply to worked help never shows that help to the reader.
    worked = _hint(ctx, session, option="walkthrough@L5", takenLevel=5)
    on_worked = _hint(ctx, session, request="feedback", answeredAssistId=worked["assistId"], feedbackText="lost")
    text = learner_text(vault, Repository.attach(paths.sqlite_path), "hint_feedback", on_worked["assistId"])
    assert text.context["hint_replied_to"] == "worked help (not shown)"


def test_reading_it_writes_only_gap_rows_and_the_gap_joins_the_next_hints_rivals(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    first = _hint(ctx, session)
    reply = _hint(ctx, session, request="feedback", answeredAssistId=first["assistId"],
                  feedbackText="but F(1/2) + 1 is still a probability")
    belief = "A value of a CDF plus one is still a probability."
    llm = GapLLMFake(reading=LearnerGap(kind="misconception", prerequisite_name=None, prerequisite_line=None,
                                        belief_statement=belief))
    clients = PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, tutor=None,
                              embedder=None)
    repository = Repository.attach(paths.sqlite_path)
    before = _counts(paths)
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    assert outcome.state == "done" and outcome.source_kind == "hint_feedback" and outcome.source_id == reply["assistId"]
    after = _counts(paths)
    changed = {table for table in after if after[table] != before.get(table)}
    assert changed <= GAP_TABLES | BELIEF_TABLES, changed
    for table in EVIDENCE:
        if table in after:
            assert after[table] == before[table], table
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        gap = dict(connection.execute("SELECT * FROM learner_text_gaps").fetchone())
    assert (gap["source_kind"], gap["source_id"], gap["practice_item_id"], gap["kind"]) == (
        "hint_feedback", reply["assistId"], ITEM, "misconception")
    # The gap named mid-attempt is one of the item's open rivals now.
    statements = [rival.statement for rival in open_rivals(repository, load_vault(paths.root).practice_items[ITEM])]
    assert belief in statements


def test_hint_feedback_is_readable_and_non_serving():
    assert "hint_feedback" in SOURCE_KINDS and "hint_feedback" in READABLE_SOURCE_KINDS
    assert "hint_feedback" in NON_SERVING_SOURCE_KINDS


@pytest.mark.parametrize("config", ["[learner_text_gaps]\nenabled = false\n", "adaptive_off"])
def test_either_switch_off_queues_nothing(tmp_path, config):
    paths, ctx, session = _sidecar(tmp_path, config if config != "adaptive_off" else "")
    first = _hint(ctx, session)
    reply = _hint(ctx, session, request="feedback", answeredAssistId=first["assistId"], feedbackText="nope")
    vault = load_vault(paths.root)
    if config == "adaptive_off":
        vault.config.hints.adaptive_enabled = False
        with closing(sqlite3.connect(paths.sqlite_path)) as connection:
            connection.execute("DELETE FROM learner_text_gap_jobs")
            connection.commit()
    assert enqueue_hint_feedback(vault, Repository.attach(paths.sqlite_path), assist_id=reply["assistId"]) is None
    assert _jobs(paths) == []


def test_a_hint_row_without_reply_text_is_no_source(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    first = _hint(ctx, session)
    repository = Repository.attach(paths.sqlite_path)
    assert hint_feedback_row(repository, first["assistId"]) is None
    assert learner_text(load_vault(paths.root), repository, "hint_feedback", first["assistId"]) is None
    assert hint_feedback_row(repository, "ha_missing") is None
