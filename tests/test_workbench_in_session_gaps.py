"""Reader workbench RW2b: in-session updates (spec_reader_workbench_v1 §5.2 "in-session updates", restored row 74).

Every ``workbench_text`` is queued when it is written or sent, not at the
end of the session: a reply and a discriminating answer when their rows are
written, a stuck step's newest text when Help, Check, Leave or Submit sends
it (idempotent per version). A gap named while the learner is still working
joins the open explanations the next hint, the chooser and the
discriminating question read. Fakes only.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import CheckFake, call, check_answer, help_rows, open_problem, run_job, sidecar


def _jobs(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_kind, source_id FROM learner_text_gap_jobs ORDER BY created_at, id")]


def _stuck(ctx, wb, after, body, key="st"):
    return call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": key, "op": "add",
                                             "kind": "stuck", "bodyMd": body, "afterStepId": after})["step"]


def test_a_stuck_step_is_queued_when_help_check_leave_or_submit_sends_it(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    ctx.post_attempt_worker.autostart = False
    wb, chains = open_problem(ctx, ("F(x) = x^2 on [0, 1]",))
    stuck = _stuck(ctx, wb, chains[0], "where does the +1 come from")
    # Typing alone sends nothing.
    assert _jobs(paths) == []
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    assert _jobs(paths) == [("workbench_text", stuck["stepId"])]
    # The same version sent again is not queued twice.
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    assert len(_jobs(paths)) == 1
    edited = call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "st2", "op": "edit",
                                               "stepId": stuck["stepId"], "bodyMd": "still lost on the +1"})["step"]
    call(ctx, "workbench.leave", {"sessionId": wb})
    assert _jobs(paths)[-1] == ("workbench_text", edited["stepId"])
    second = _stuck(ctx, wb, chains[0], "and the bounds", key="st3")
    call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})
    assert ("workbench_text", second["stepId"]) in _jobs(paths)


def test_a_gap_named_mid_problem_joins_the_next_hints_rivals(tmp_path):
    def one_reading(context):
        payload = check_answer(context)
        payload["error_readings"] = payload["error_readings"][:1]
        return payload

    paths, ctx, _session = sidecar(tmp_path, check=CheckFake([one_reading]))
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    # One open explanation: rung 1 is an ordinary question.
    assert run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))["kind"] == \
        "approach_question"
    # Learner-text gaps names a misconception on the item from a reply.
    item = help_rows(paths, wb)[0]["practice_item_id"]
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO learner_text_gaps (id, source_kind, source_id, practice_item_id, learner_text, chooser, "
            "context_judge, kind, named_json, action, algorithm_version, pipeline_version, created_at) "
            "VALUES ('g1', 'workbench_text', 'src1', ?, 'it is +1', 'context_model', 'gap_reader', 'misconception', ?, "
            "'belief_candidate', 'mvp-0.6', 'learner-text-gaps-v1', '2099-01-01T00:00:00Z')",
            (item, json.dumps({"belief_statement": "Adding one keeps a value a probability."})))
        connection.commit()
    question = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 1}))
    assert question["kind"] == "discriminating"
    rivals = ctx.hint_writer_client.contexts[-1]["rivals"]
    assert "Adding one keeps a value a probability." in [rival["statement"] for rival in rivals]
