"""Reader workbench RW2b + hints H3, fix round 14 (``docs/reviews/reader-rw2b-h3-codex-review.md``).

1. the window includes level 4-5 workbench rows: primed is derived from it
   (whatever the problem's status), the rows are attached, never counted;
2. (rejected as a defect) the guarantee pinned: a check stored "checked"
   while the switch was on is read as the model's by every reader once off;
3. queued diagnoses read the CURRENT switch (the live config file), never a
   vault captured for the drain;
4. workbench delivery is fenced item-wide, like the counting window.

Fakes only; no model is reached.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.live import current_attempt_for
from learnloop.hints.report_workbench import build_workbench_report
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, help_rows, open_problem, run_job,
                                        sidecar, step_check, wb_answer)


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _box(ctx, session, key):
    return call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                        "attemptType": "independent_attempt", "hintsUsed": 0, "authoredHints": 0,
                                        "submissionId": key})


# -- Item 1: worked help primes from the window ---------------------------------------------------


def test_item1_worked_help_on_an_abandoned_problem_primes_the_answer_box_attempt_once(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    worked = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 4}))
    assert worked["shown"] is True and worked["level"] == 4
    call(ctx, "workbench.abandon", {"sessionId": wb})
    first = _attempt(paths, _box(ctx, session, "after-worked")["attemptId"])
    assert (first["hints_used"], first["primed"]) == (0, 1)
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert row["attempt_id"] == first["id"]
    # A later submit does not re-prime from rows an attempt already took.
    import time

    time.sleep(1.05)
    second = _attempt(paths, _box(ctx, session, "later")["attemptId"])
    assert second["primed"] == 0


# -- Items 2 and 3: every reader, the diagnoser's included, reads the switch now ------------------


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def _answer(_context):
    return {"steps": [step_check(1, "questionable", reason="the model's reading",
                                 transformation=_transformation(kind="equivalence", expression="x+x", result="2*x")),
                      step_check(2, "unchecked")],
            "first_questionable_step": 1, "error_kind_guess": "invalid_algebra", "error_kind_reason": "",
            "error_readings": [], "assumptions": []}


@pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")
def test_items_2_3_a_row_stored_checked_reads_as_the_models_everywhere_once_the_switch_is_off(tmp_path, grader):
    writer = WriterFake([wb_answer] * 4)
    paths, ctx, session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, writer=writer,
                                  check=CheckFake([_answer]), chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]["verdicts"][0]["method"] == "checked"
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    # A post-attempt drain captured its vault while the switch was on.
    drain_vault = load_vault(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("symbolic_checks_enabled = true", "symbolic_checks_enabled = false"))
    ctx.reload()
    # The stored row is history: it still says checked.
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert json.loads(row["step_verdicts_json"])[0]["method"] == "checked"
    # The view and help_state.
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert {entry["method"] for entry in state["check"]["verdicts"]} == {"model"}
    # The report.
    assert "checked" not in build_workbench_report(paths.sqlite_path)["checks"]["verdict_methods"]
    # The diagnoser, with the drain's stale vault (item 3): the live config file decides.
    current = current_attempt_for(drain_vault, _attempt(paths, attempt["attemptId"]),
                                  {"rubric_score": 0, "criteria": []}, Repository.attach(paths.sqlite_path))
    [check] = [entry for entry in current.workbench_trace["assists"] if entry["assist"] == "check"]
    assert {verdict["method"] for verdict in check["verdicts"]} == {"model"}


def test_item3_the_trace_is_regated_by_the_accessor():
    from learnloop.symbolic_view import trace_view

    trace = {"note": "n", "assists": [{"assist": "check", "verdicts": [{"step": 1, "method": "checked"}]},
                                      {"assist": "hint", "kind": "next_step"}]}
    off = trace_view(trace, enabled=False)
    assert off["assists"][0]["verdicts"][0]["method"] == "model" and off["assists"][1] == trace["assists"][1]
    assert trace_view(trace, enabled=True) == trace


# -- Item 4: delivery is fenced item-wide --------------------------------------------------------------


def test_item4_a_workbench_check_is_not_delivered_after_another_surfaces_attempt_of_the_item(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    ctx.hints_inline = False
    started = call(ctx, "workbench.check", {"sessionId": wb})
    assert ctx.workbench_help_jobs.get(started["jobId"]).done.wait(30)
    ctx.hints_inline = True
    # Another surface commits an answer-box attempt of the item before delivery.
    _box(ctx, session, "other-surface")
    payload = call(ctx, "workbench.help_job", {"jobId": started["jobId"]})
    assert payload["result"]["shown"] is False
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert row["shown"] == 0
