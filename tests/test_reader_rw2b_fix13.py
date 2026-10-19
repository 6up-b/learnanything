"""Reader workbench RW2b + hints H3, fix round 13 (``docs/reviews/reader-rw2b-h3-codex-review.md``).

1. RW2b's server assists follow H2b's R1 rule: the counted set is the item's
   WINDOW (shown, unattached, server-counted workbench checks and level 1-3
   hints requested since the item's last attempt, whatever their problem's
   status), attached by the attempt that counts them;
2. in-flight verification reads the live switch right before verifying and
   again before serializing: off at either point, nothing is checked;
3. (the frontend's live gate: ``symbolicOff.test.tsx``).

Fakes only; no model is reached.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

import pytest

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


# -- Item 1: the window, whatever the problem's status ----------------------------------------------


def test_item1_a_check_on_an_abandoned_problem_counts_on_the_answer_box_attempt(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    call(ctx, "workbench.abandon", {"sessionId": wb})
    attempt = _box(ctx, session, "after-abandon")
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1
    # The attempt took the row: it is attached and counted once.
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert row["attempt_id"] == attempt["attemptId"]


def test_item1_reopened_the_answer_box_counts_it_and_the_problems_later_submit_does_not(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    call(ctx, "workbench.abandon", {"sessionId": wb})
    call(ctx, "workbench.reopen", {"sessionId": wb})
    attempt = _box(ctx, session, "after-reopen")
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1
    later = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert _attempt(paths, later["attemptId"])["hints_used"] == 0


# -- Item 2: in-flight verification reads the switch now ---------------------------------------------


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def _switch_off(state):
    toml = state["paths"].root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("symbolic_checks_enabled = true", "symbolic_checks_enabled = false"))
    state["ctx"].reload()


class _Sandbox:
    """Stands for the sandbox: records each run; optionally turns the switch
    off while it runs; answers every claim checked and holding."""

    def __init__(self, state, *, flip=False):
        self.state, self.flip, self.runs = state, flip, 0

    def __call__(self, command, **_kwargs):
        from pathlib import Path

        self.runs += 1
        payload = json.loads((Path(command[-1]) / "input.json").read_text())
        if self.flip:
            _switch_off(self.state)
        results = [{"index": claim["index"], "method": "checked", "holds": True, "reason": "", "bound": True}
                   for claim in payload["claims"]]
        out = ("@@PF-SANDBOX-RESULT@@" + json.dumps({"results": results})).encode()
        return type("Done", (), {"returncode": 0, "stdout": out, "stderr": b""})()


@pytest.fixture
def bwrap(monkeypatch):
    import learnloop.content.authoring.pf_sandbox as pf

    monkeypatch.setattr(pf, "require_sandbox", lambda: "/usr/bin/bwrap")


def _check_answer(state, *, flip):
    def answer(_context):
        if flip:
            _switch_off(state)  # off while the model's call was pending
        return {"steps": [step_check(1, "questionable", reason="the model's reading",
                                     transformation=_transformation(kind="equivalence", expression="x+x",
                                                                    result="2*x")),
                          step_check(2, "unchecked")],
                "first_questionable_step": 1, "error_kind_guess": "invalid_algebra", "error_kind_reason": "",
                "error_readings": [], "assumptions": []}

    return answer


@pytest.mark.parametrize("when", ["during_the_model_call", "during_verification"])
def test_item2_a_check_in_flight_when_the_switch_goes_off_is_never_checked(tmp_path, bwrap, when):
    state = {}
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True,
                                   check=CheckFake([_check_answer(state, flip=when == "during_the_model_call")]))
    state.update(paths=paths, ctx=ctx)
    sandbox = _Sandbox(state, flip=when == "during_verification")
    ctx.workbench_sandbox_run = sandbox
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    assert {entry["method"] for entry in view["verdicts"]} == {"model"}
    assert sandbox.runs == (0 if when == "during_the_model_call" else 1)
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert {entry["method"] for entry in json.loads(row["step_verdicts_json"])} == {"model"}
    assert json.loads(row["placement_json"])["symbolic"] == []
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tasks = [entry[0] for entry in connection.execute("SELECT task FROM judgment_ledger WHERE left_id = ?",
                                                          (row["id"],))]
    assert "workbench_check_symbolic" not in tasks


@pytest.mark.parametrize("when", ["during_the_writer_call", "during_verification"])
def test_item2_a_hint_in_flight_when_the_switch_goes_off_stores_no_checked_claim(tmp_path, bwrap, when):
    state = {}
    claim = {"step": 1, "statement": "x + x = 2x", **_transformation(kind="equivalence", expression="x+x",
                                                                         result="2*x")}

    def writer_answer(context):
        if when == "during_the_writer_call":
            _switch_off(state)
        return {**wb_answer(context), "claims": [claim]}

    writer = WriterFake([writer_answer, wb_answer])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True, writer=writer,
                                   chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    state.update(paths=paths, ctx=ctx)
    sandbox = _Sandbox(state, flip=when == "during_verification")
    ctx.workbench_sandbox_run = sandbox
    wb, _chains = open_problem(ctx, steps=("x + x = 2x", "2x = 2x"))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert [entry["status"] for entry in hint["claims"]] == ["model"]
    assert sandbox.runs == (0 if when == "during_the_writer_call" else 1)
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    stored = json.loads(row["contract_failures_json"])
    assert [entry["status"] for entry in stored["claims"]] == ["model"]
    assert all(entry["status"] == "model" for round_ in stored["rounds"] for entry in round_.get("claims") or [])
