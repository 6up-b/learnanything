"""Reader workbench RW2b + hints H3, fix round 9: symbolic checks are OFF by default.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 9 (orchestrator
decision)": ``workbench.symbolic_checks_enabled`` defaults to false. With the
switch at its default no "checked" or "≠ checked" label is produced on any
path (the check, a hint's claims, the persisted placement and ledger rows,
help_state, the workbench report), and the sandbox is never invoked. Each
test runs with the switch at its default, on a problem and steps that the
checker would otherwise check. Fakes only; no model is reached.
"""

from __future__ import annotations

import json

import pytest

from learnloop.config.schema import WorkbenchConfig
from learnloop.hints.report_workbench import build_workbench_report
from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, help_rows, open_problem, run_job,
                                        sidecar, step_check, wb_answer)

STEPS = ("x + x = 2x", r"\int_0^1 2x dx = 1")


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def _answer(_context):
    return {"steps": [step_check(1, "questionable", reason="the model's reading",
                                 transformation=_transformation(kind="equivalence", expression="x+x",
                                                                result="2*x")),
                      step_check(2, "valid", reason="the model's reading",
                                 transformation=_transformation(kind="integration", expression="2*x", result="1",
                                                                variable="x", lower="0", upper="1"))],
            "first_questionable_step": 1, "error_kind_guess": "invalid_algebra", "error_kind_reason": "",
            "error_readings": [], "assumptions": []}


SANDBOX_CALLS: list[int] = []


def _never_run(*_args, **_kwargs):
    SANDBOX_CALLS.append(1)
    raise AssertionError("the sandbox ran with symbolic checks off")


@pytest.fixture
def checked(tmp_path):
    """A check of two steps the checker would decide, at the default switch."""

    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, check=CheckFake([_answer]))
    ctx.workbench_sandbox_run = _never_run
    wb, _chains = open_problem(ctx, steps=STEPS)
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    return paths, ctx, wb, view


def test_the_default_is_off():
    assert WorkbenchConfig().symbolic_checks_enabled is False


def test_the_check_path_labels_nothing_checked_and_never_runs_the_sandbox(checked):
    _paths, _ctx, _wb, view = checked
    assert [(entry["method"], entry["mark"], entry["label"]) for entry in view["verdicts"]] == [
        ("model", "?", "model's reading, not checked"), ("model", "≈", "model's reading, not checked")]


def test_the_persisted_placement_and_ledger_hold_no_symbolic_verdict(checked):
    import sqlite3
    from contextlib import closing

    paths, _ctx, wb, _view = checked
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    placement = json.loads(row["placement_json"])
    assert placement["symbolic"] == [] and placement["symbolic_problem"] is None
    assert {entry["method"] for entry in json.loads(row["step_verdicts_json"])} == {"model"}
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tasks = [entry[0] for entry in connection.execute(
            "SELECT task FROM judgment_ledger WHERE left_id = ?", (row["id"],)).fetchall()]
        rationales = [json.loads(entry[0]) for entry in connection.execute(
            "SELECT rationale FROM judgment_ledger WHERE left_id = ? AND task = 'workbench_check'",
            (row["id"],)).fetchall()]
    assert "workbench_check_symbolic" not in tasks
    assert rationales and {entry["method"] for entry in rationales} == {"model"}


def test_help_state_shows_no_checked_label(checked):
    _paths, ctx, wb, _view = checked
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert {entry["method"] for entry in state["check"]["verdicts"]} == {"model"}
    assert not {entry["mark"] for entry in state["check"]["verdicts"]} & {"✓", "≠"}


def test_the_workbench_report_counts_no_checked_verdict(checked):
    paths, _ctx, _wb, _view = checked
    block = build_workbench_report(paths.sqlite_path)
    assert block["checks"]["verdict_methods"] == {"model": 2}
    assert block["checks"]["symbolic_outcomes"] == {}


def test_a_hints_claims_are_the_models_reading_and_the_sandbox_never_runs(tmp_path):
    claim = {"step": 2, "statement": r"\int_0^1 2x dx = 1", **_transformation(
        kind="integration", expression="2*x", result="1", variable="x", lower="0", upper="1")}
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}, wb_answer])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, writer=writer,
                                   chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    ctx.workbench_sandbox_run = _never_run
    SANDBOX_CALLS.clear()
    wb, _chains = open_problem(ctx, steps=("x^2 = x^2", "2x = 2x"))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert [(entry["status"], entry["label"]) for entry in hint["claims"]] == [
        ("model", "model's reading, not checked")]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert [entry["status"] for entry in json.loads(row["contract_failures_json"])["claims"]] == ["model"]
    restored = call(ctx, "workbench.help_state", {"sessionId": wb})["hints"][0]
    assert [entry["status"] for entry in restored["claims"]] == ["model"]
    # The verifier swallows a sandbox failure, so ask directly: it never ran.
    assert SANDBOX_CALLS == []
