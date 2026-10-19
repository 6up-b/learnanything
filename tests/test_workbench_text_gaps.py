"""Reader workbench RW2b: the ``workbench_text`` learner-text adapter (spec_reader_workbench_v1 §5.6; G36, G62).

Text the learner writes while working in steps is learner text: a stuck
step (its newest version), a "this doesn't connect" reply with text, and an
answer to a discriminating question; the adapter reads each with its item,
step, anchors and role (``stuck`` | ``hint_feedback`` | ``discriminate_answer``),
never the answer key or worked help. Reading one writes only gap rows, their
jobs, ledger rows and receipts (W1 tier 2): no attempt, evidence, mastery,
FSRS state or probe observation. The kind is readable and non-serving; the
practice screen's ``hint_feedback`` adapter never reads a workbench row; each
box's *where this goes* names where its text goes. Every model is a fake.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import re
import sqlite3

from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps.contract import NON_SERVING_SOURCE_KINDS, READABLE_SOURCE_KINDS
from learnloop.diagnosis.text_gaps.jobs import enqueue_workbench_text, process_next_gap_job
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.diagnosis.text_gaps.sources import hint_feedback_row, learner_text, workbench_text_row
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM
from tests.text_gap_fakes import GapLLMFake
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar

GAP_TABLES = {"learner_text_gaps", "learner_text_gap_jobs", "judgment_ledger", "model_call_receipts",
              "text_write_provenance", "interaction_events", "judgment_work_claims", "model_work_checkpoints"}
BELIEF_TABLES = {"misconception_sightings", "belief_candidates", "misconception_candidates"}
EVIDENCE = ("practice_attempts", "reveal_events", "facet_capability_evidence", "attempt_diagnoses", "help_assists",
            "probe_observations", "grading_evidence", "facet_recall_state")


def _jobs(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_kind, source_id FROM learner_text_gap_jobs ORDER BY created_at, id")]


def _counts(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in tables}


def _stuck_problem(ctx):
    wb, chains = open_problem(ctx, ("F(x) = x^2 on [0, 1]",))
    saved = call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "st", "op": "add",
                                              "kind": "stuck", "bodyMd": "I don't see why F(1/2) is the answer",
                                              "afterStepId": chains[0]})
    return wb, saved["step"]


def test_a_stuck_step_is_read_with_its_role_item_and_anchor(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    ctx.post_attempt_worker.autostart = False
    wb, step = _stuck_problem(ctx)
    repository = Repository.attach(paths.sqlite_path)
    row = workbench_text_row(repository, step["stepId"])
    assert row["role"] == "stuck" and row["workbench_session_id"] == wb
    vault = load_vault(paths.root)
    text = learner_text(vault, repository, "workbench_text", step["stepId"])
    assert (text.source_kind, text.text, text.context["role"], text.practice_item_id) == (
        "workbench_text", "I don't see why F(1/2) is the answer", "stuck", ITEM)
    assert text.anchor_learning_object_ids == (vault.practice_items[ITEM].learning_object_id,)
    assert str(vault.practice_items[ITEM].expected_answer) not in str(text.context)


def test_a_reply_and_a_discriminating_answer_are_workbench_text_never_hint_feedback(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    ctx.post_attempt_worker.autostart = False
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    answer = call(ctx, "workbench.answer_discriminating", {"sessionId": wb, "questionAssistId": question["assistId"],
                                                           "answerMd": "0"})
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    reply = run_job(ctx, call(ctx, "workbench.request_help", {
        "sessionId": wb, "request": "feedback", "answeredAssistId": hint["assistId"], "feedbackShortcut": "too_big",
        "feedbackText": "too far for me"}))
    repository = Repository.attach(paths.sqlite_path)
    vault = load_vault(paths.root)
    assert workbench_text_row(repository, answer["assistId"])["role"] == "discriminate_answer"
    assert workbench_text_row(repository, reply["assistId"])["role"] == "hint_feedback"
    text = learner_text(vault, repository, "workbench_text", reply["assistId"])
    assert text.context["hint_replied_to"] == hint["hintMd"] and text.context["shortcut"] == "too_big"
    # The practice screen's adapter never takes a workbench row.
    assert hint_feedback_row(repository, reply["assistId"]) is None
    queued = {source_id for kind, source_id in _jobs(paths) if kind == "workbench_text"}
    assert {answer["assistId"], reply["assistId"]} <= queued


def test_reading_it_writes_only_gap_rows(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    ctx.post_attempt_worker.autostart = False
    _wb, step = _stuck_problem(ctx)
    repository = Repository.attach(paths.sqlite_path)
    vault = load_vault(paths.root)
    assert enqueue_workbench_text(vault, repository, source_id=step["stepId"])
    belief = "The answer is always the CDF at the point, whatever is asked."
    llm = GapLLMFake(reading=LearnerGap(kind="misconception", prerequisite_name=None, prerequisite_line=None,
                                        belief_statement=belief))
    clients = PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, tutor=None,
                              embedder=None)
    before = _counts(paths)
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    assert outcome.state == "done" and outcome.source_kind == "workbench_text"
    after = _counts(paths)
    changed = {table for table in after if after[table] != before.get(table)}
    assert changed <= GAP_TABLES | BELIEF_TABLES, changed
    for table in EVIDENCE:
        if table in after:
            assert after[table] == before[table], table


def test_the_kind_is_readable_and_non_serving_and_the_switches_hold(tmp_path):
    assert "workbench_text" in READABLE_SOURCE_KINDS and "workbench_text" in NON_SERVING_SOURCE_KINDS
    for config in ("[learner_text_gaps]\nenabled = false\n", "[workbench]\nhelp_enabled = false\n"):
        paths, ctx, _session = sidecar(tmp_path / str(abs(hash(config))), config)
        _wb, step = _stuck_problem(ctx)
        assert enqueue_workbench_text(load_vault(paths.root), Repository.attach(paths.sqlite_path),
                                      source_id=step["stepId"]) is None


def test_an_empty_stuck_step_or_an_ordinary_step_is_no_source(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, chains = open_problem(ctx, ("F(x) = x^2",))
    empty = call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "e", "op": "add",
                                              "kind": "stuck", "bodyMd": "  ", "afterStepId": chains[0]})["step"]
    repository = Repository.attach(paths.sqlite_path)
    assert workbench_text_row(repository, empty["stepId"]) is None
    view = call(ctx, "workbench.get", {"sessionId": wb})["session"]
    assert workbench_text_row(repository, view["steps"][0]["stepId"]) is None


def test_each_boxs_where_this_goes_matches_where_its_text_goes():
    """G62's table-driven check over the boxes and the source kinds."""

    model = Path(__file__).resolve().parents[1] / "apps/learnloop-tauri/src/screens/workbench/helpModel.ts"
    source = model.read_text(encoding="utf-8")
    table = re.search(r"export const WHERE_THIS_GOES = \{(.*?)\} as const;", source, re.S).group(1)
    boxes = dict(re.findall(r"(\w+): \{\s*line: \"([^\"]+)\",\s*routedTo: \"(\w+)\"", table) and
                 [(box, (line, routed)) for box, line, routed in
                  re.findall(r"(\w+): \{\s*line: \"([^\"]+)\",\s*routedTo: \"(\w+)\"", table)])
    assert set(boxes) == {"stuck", "doesntConnect", "discriminating"}
    for _box, (line, routed) in boxes.items():
        # Each of these boxes goes to learner-text gaps as workbench_text,
        # and its line says a model may read it to name a gap, never to grade.
        assert routed == "workbench_text" and routed in READABLE_SOURCE_KINDS
        assert "name a gap" in line and line.endswith("never to grade you.")
