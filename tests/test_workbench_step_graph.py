"""Reader workbench RW2b: the step graph and the error-kind guess (spec_reader_workbench_v1 §5.2 restored rows 18 and 60; G38, G60).

A questionable step marks only the steps that depend on it as not standing,
so ``continue_from`` may be a later independent valid step; without a graph,
the steps before the first questionable one stand. The error-kind guess is
labelled "the model's guess", reaches the diagnoser's trace, and is never
written as a diagnosis or an error event. Fakes only.
"""

from __future__ import annotations

from contextlib import closing
import sqlite3

from learnloop.hints import workbench as W
from tests.workbench_help_fakes import CheckFake, call, check_answer, open_problem, run_job, sidecar
from tests.workbench_help_fakes import step_check as _step


def _steps(*kinds):
    return [W.WorkbenchStep(chain_id=f"c{n}", step_id=f"s{n}", number=n, kind=kind, body_md=f"step {n}")
            for n, kind in enumerate(kinds, start=1)]


def _verdict(n, verdict, *depends):
    return W.StepVerdict(chain_id=f"c{n}", verdict=verdict, method="model", depends_on=tuple(f"c{d}" for d in depends))


def test_a_questionable_step_fells_only_its_dependents():
    steps = _steps("step", "step", "step", "step")
    verdicts = [_verdict(1, "valid"), _verdict(2, "questionable", 1), _verdict(3, "valid", 2), _verdict(4, "valid", 1)]
    standing = W.standing_steps(steps, verdicts)
    assert standing == ["c1", "c4"]
    # continue_from may be a later independent valid step (rule 2).
    assert W.checkpoint_for(steps, standing, None) == "c4"
    # A hint about step 3 continues from what stands before it.
    assert W.checkpoint_for(steps, standing, "c3") == "c1"


def test_without_a_graph_the_steps_before_the_first_questionable_one_stand():
    steps = _steps("step", "step", "step")
    verdicts = [_verdict(1, "valid"), _verdict(2, "questionable"), _verdict(3, "valid")]
    assert W.standing_steps(steps, verdicts) == ["c1"]
    assert W.checkpoint_for(steps, ["c1"], "c2") == "c1"


def test_the_questionable_step_is_never_the_checkpoint_and_stuck_steps_never_stand():
    steps = _steps("step", "stuck", "step")
    verdicts = [_verdict(1, "questionable")]
    standing = W.standing_steps(steps, verdicts)
    assert "c1" not in standing and "c2" not in standing
    assert W.checkpoint_for(steps, standing, "c1") is None


def test_the_service_is_told_the_standing_steps_from_the_last_check(tmp_path):
    def answer(context):
        payload = check_answer(context)
        payload["steps"] = [_step(1, "valid"), _step(2, "questionable", depends_on=[1], quote="F(1/2) + 1"),
                            _step(3, "valid", depends_on=[1])]
        payload["first_questionable_step"] = 2
        return payload

    _paths, ctx, _session = sidecar(tmp_path, check=CheckFake([answer]))
    wb, chains = open_problem(ctx, ("F(x) = x^2 on [0, 1]", "so P(X <= 1/2) = F(1/2) + 1", "F(1) = 1"))
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert hint["status"] == "ready"
    writer = ctx.hint_writer_client
    block = writer.contexts[-1]["workbench"]
    assert [entry["stands"] for entry in block["steps"]] == [True, False, True]
    assert (block["about_step"], block["continue_from_step"]) == (2, 1)
    assert hint["steps"]["aboutStepId"] == chains[1] and hint["steps"]["continueFromStepId"] == chains[0]


def test_the_guess_is_the_models_guess_and_never_a_diagnosis_or_error_event(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)

    def counts():
        with closing(sqlite3.connect(paths.sqlite_path)) as connection:
            return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("attempt_diagnoses", "error_events", "causal_hypotheses", "probe_observations")}

    before = counts()
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    assert view["errorKind"]["label"] == "looks like a concept applied the wrong way (model's guess)"
    assert counts() == before


def test_with_the_error_kind_switch_off_no_guess_is_shown_or_kept(tmp_path):
    paths, ctx, _session = sidecar(tmp_path, "[workbench]\nerror_kind_enabled = false\n")
    wb, _chains = open_problem(ctx)
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    assert view["errorKind"] is None
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT error_kind_guess, alternatives_json FROM help_assists "
                                  "WHERE assist_kind = 'check'").fetchone() == (None, None)
