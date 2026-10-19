"""Reader workbench RW2b + hints H3, fix round 12 (``docs/reviews/reader-rw2b-h3-codex-review.md``).

1. an empty component snapshot in the refold (the last open problem closed
   during grading) is never read as legacy carried hints;
2. a book the client holds (``bookCounted``) is its own component, ORed into
   the book, in the refold too;
3. an in-flight hint job reads the CURRENT symbolic switch before every
   writer invocation and row serialization;
4. the empty-stuck fallback forwards ``authoredHints`` and ``bookCounted``.

Fakes only; no model is reached.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
import json
import sqlite3
from typing import Any

import pytest

import learnloop_sidecar.handlers.practice as practice_handler
from learnloop.attempts.hint_fold import ServerHintFold, refolded_draft
from learnloop.content.authoring.pf_sandbox import sandbox_available
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, help_rows, open_problem, run_job,
                                        sidecar, step_check, wb_answer)


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _box(ctx, session, key, **values):
    payload = {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
               "submissionId": key, **values}
    return call(ctx, "submit_attempt", payload)


# -- Item 1: an empty snapshot is not legacy carried hints ----------------------------------------


@dataclass(frozen=True)
class _Draft:
    hints_used: int
    primed: bool
    attempt_type: str
    server_hint_fold: Any


def test_item1_the_refold_keeps_one_when_the_last_problem_closed_during_grading():
    # The verify's pure reproduction: one check counted; its problem is gone in the transaction.
    fold = ServerHintFold(practice_item_id=ITEM, session_id="s", submission_id="k", since=None, folded_hints=0,
                          folded_primed=False, base_hints=1, base_primed=False,
                          held_reader=lambda _connection: ((), False), held_client_hints=0, held_hints=1,
                          held_parts=((0, 0, ("ha_check",)),), held_union=("ha_check",), held_known=True)
    assert fold.hints_used() == 1
    draft, _now = refolded_draft(sqlite3.connect(":memory:"), _Draft(1, False, "hinted_attempt", fold))
    assert draft.hints_used == 1


def test_item1_end_to_end_a_problem_submitted_during_grading_is_not_counted_twice(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    real = practice_handler._server_hint_fold
    entered = []

    def during_grading(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not entered:
            entered.append(True)
            call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})
        return fold

    monkeypatch.setattr(practice_handler, "_server_hint_fold", during_grading)
    attempt = _box(ctx, session, "closed-during", hintsUsed=0, authoredHints=0)
    assert entered and _attempt(paths, attempt["attemptId"])["hints_used"] == 1


# -- Item 2: the client-held book is its own component ---------------------------------------------


def _carried_problem_with_a_check(ctx):
    opened = call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                          "stemMd": "Find P(X <= 1/2).", "carriedHints": 1})["session"]
    call(ctx, "workbench.save_step", {"sessionId": opened["sessionId"], "clientIdempotencyKey": "s0", "op": "add",
                                      "bodyMd": "F(x) = x^2 on [0, 1]", "afterStepId": None})
    return opened["sessionId"]


def test_item2_a_book_left_a_carried_hint_and_a_check_are_three(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb = _carried_problem_with_a_check(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    attempt = _box(ctx, session, "book-left-three", hintsUsed=1, authoredHints=0, bookCounted=True)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 3


def test_item2_the_refold_keeps_the_client_held_book(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb = _carried_problem_with_a_check(ctx)
    real = practice_handler._server_hint_fold
    done = []

    def during_grading(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not done:
            done.append(run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb})))
        return fold

    monkeypatch.setattr(practice_handler, "_server_hint_fold", during_grading)
    attempt = _box(ctx, session, "book-left-late", hintsUsed=1, authoredHints=0, bookCounted=True)
    assert done and done[0]["shown"] is True
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 3


# -- Item 3: an in-flight hint reads the switch now -------------------------------------------------


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
def test_item3_a_hint_in_flight_when_the_switch_goes_off_writes_and_stores_the_models_reading(tmp_path):
    state = {}

    def first(context):
        # The switch goes off while the job is in flight (after its context was built).
        toml = state["paths"].root / "learnloop.toml"
        toml.write_text(toml.read_text().replace("symbolic_checks_enabled = true", "symbolic_checks_enabled = false"))
        state["ctx"].reload()
        leaking = {"step": 1, "statement": "The final answer is P(X ≤ 1/2) = 1/4.", **_transformation()}
        return {**wb_answer(context), "claims": [leaking]}  # leaks: the round is asked again

    writer = WriterFake([first, wb_answer, wb_answer])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, writer=writer,
                                   check=CheckFake([_answer]), chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    state.update(paths=paths, ctx=ctx)
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]["verdicts"][0]["method"] == "checked"
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert writer.calls >= 2
    # The first prompt was written while on; every later one reads the switch now.
    assert writer.contexts[0]["workbench"]["steps"][0]["method"] == "checked"
    assert {entry["method"] for entry in writer.contexts[1]["workbench"]["steps"] if entry["method"]} == {"model"}
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert {entry["method"] for entry in json.loads(row["step_verdicts_json"] or "[]")} == {"model"}


# -- Item 4: the empty-stuck fallback forwards every optional count ----------------------------------


def test_item4_a_stale_stuck_screens_empty_answer_keeps_its_authored_hint(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")  # the book counted there
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    attempt = _box(ctx, session, "stale-stuck", answerMd="", declaredStuck=True, hintsUsed=1, authoredHints=1)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 3
