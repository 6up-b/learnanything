"""Handwritten work as workbench steps (owner decision 2026-11-23: "feed the transcription into the existing workbench
steps"). The problem pad writes each ink line's text as a step through the workbench's own step writer, under a key
derived from the line, and asks for help as for typed steps (`surface = 'workbench'`). This pins what the client relies
on, server side: the same key answers the step it already made (a reopened problem finds its line's step, never a
second one); the learner's correction is an edit, and help reads the correction, never the reading it replaced; worked
help on that step marks the later attempt as the existing fold marks a typed one. Nothing here is new server code: the
client's ink work goes through these unchanged. Every model is a fake."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from tests.hint_fakes import WriterFake
from tests.hint_h2b_review_helpers import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import call, open_problem, run_job, sidecar, wb_answer

READING = "F(x) = x^2 on [0, 1], so P(X <= 1/2) = F(1/2) + 1"
CORRECTION = "F(x) = x on [0, 1], so P(X <= 1/2) = F(1/2)"


def _ink_step(ctx, wb, line, body, key=None):
    saved = call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": key or f"ink-step:{line}", "op": "add",
                                              "kind": "step", "bodyMd": body})
    return saved["step"]


def test_a_lines_key_answers_its_step_again_and_a_correction_is_what_help_reads(tmp_path, grader):
    writer = WriterFake([wb_answer] * 6)
    _paths, ctx, _session = sidecar(tmp_path, writer=writer)
    wb, _chains = open_problem(ctx, steps=())
    first = _ink_step(ctx, wb, "blk_1", READING)
    again = _ink_step(ctx, wb, "blk_1", READING)
    assert again["chainId"] == first["chainId"]
    steps = call(ctx, "workbench.get", {"sessionId": wb})["session"]["steps"]
    assert [step["chainId"] for step in steps if not step["deleted"]] == [first["chainId"]]
    # The learner's correction under the line: an edit of that step.
    call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "ink-edit:blk_1:v2", "op": "edit",
                                      "stepId": first["stepId"], "bodyMd": CORRECTION})
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3, "focusedStepId": first["chainId"]}))
    assert writer.prompts and CORRECTION in writer.prompts[-1] and READING not in writer.prompts[-1]


def test_worked_help_on_an_ink_step_marks_the_later_attempt_as_on_a_typed_step(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx, steps=())
    step = _ink_step(ctx, wb, "blk_1", READING)
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 4, "focusedStepId": step["chainId"]}))
    assert hint["status"] == "ready" and hint["level"] == 4
    attempt_id = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]["attemptId"]
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        row = dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())
        surfaces = [r[0] for r in connection.execute("SELECT DISTINCT surface FROM help_assists")]
    assert (row["hints_used"], row["primed"]) == (0, 1)
    assert resolve_attempt_activity_policy(attempt_type=row["attempt_type"], primed=True, hints_used=0).eligible_for_certification is False
    assert surfaces == ["workbench"]
