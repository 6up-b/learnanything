"""Reader workbench RW2b: "Check my work" (spec_reader_workbench_v1 §5.2, §5.3, §5.8; G9, G12, G38).

The check's verdicts per step, labelled by method: "checked" only when the
sandbox's symbolic check ran and its controls behaved (and without
bubblewrap every marker is the model's reading); never the correction, never
a score; the first questionable step with a reason quoting it; the
error-kind guess labelled as the model's guess. A check is one hint once
shown, on any route (Codex estimated from tokens); the per-problem call cap and the daily money cap
hold; an unchanged re-check counts nothing; a check cancelled before it was
read counts nothing. Fakes only (the symbolic harness runs in the real
sandbox where bubblewrap is installed, else through a fake runner).
"""

from __future__ import annotations

import json

import pytest

from learnloop.workbench import check as check_module
from learnloop.workbench import symbolic
from tests.workbench_help_fakes import (
    STEP_1,
    STEP_2,
    CheckFake,
    call,
    check_answer,
    help_rows,
    open_problem,
    run_job,
    sidecar,
)
from tests.workbench_help_fakes import step_check as _step


def _check(ctx, wb):
    return run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    base.update(values)
    return base


def test_a_check_marks_each_step_by_method_and_names_the_first_questionable_step(tmp_path):
    _paths, ctx, _session = sidecar(tmp_path)
    wb, chains = open_problem(ctx)
    result = _check(ctx, wb)
    assert result["status"] == "ready" and result["shown"] is True
    view = result["check"]
    first, second = view["verdicts"]
    assert (first["chainId"], first["verdict"], first["mark"], first["label"]) == (
        chains[0], "valid", "≈", "model's reading, not checked")
    assert (second["verdict"], second["mark"], second["first"]) == ("questionable", "?", True)
    # The reason quotes the learner's step, and never states the answer.
    assert "F(1/2) + 1" in second["reason"] and "1/4" not in second["reason"]
    assert view["firstQuestionableStepId"] == chains[1]
    assert view["errorKind"]["label"].endswith("(model's guess)")
    assert view["assumptions"] == ["X has density 2x on [0, 1]"]
    # No score anywhere in what the learner sees.
    assert "score" not in json.dumps(view).lower()


def test_a_shown_check_counts_one_hint_and_the_record_line_says_so(tmp_path):
    _paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    result = _check(ctx, wb)
    assert result["record"]["hints"] == 1
    assert "a check" in result["record"]["line"] and "a check" in result["record"]["footer"]
    record = call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]
    assert record["hints"] == 1 and record["help"]["checks"] == 1


def test_the_same_steps_checked_again_count_nothing_more(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    _check(ctx, wb)
    again = _check(ctx, wb)
    assert again["status"] == "unchanged" and again["check"] is not None
    assert len([row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]) == 1
    assert call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]["hints"] == 1


def test_editing_a_checked_step_marks_it_stale_and_a_new_check_runs(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, chains = open_problem(ctx)
    _check(ctx, wb)
    view = call(ctx, "workbench.get", {"sessionId": wb})["session"]
    step = next(entry for entry in view["steps"] if entry["chainId"] == chains[1])
    call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "edit", "op": "edit",
                                      "stepId": step["stepId"], "bodyMd": "so P(X <= 1/2) = F(1/2)"})
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert state["check"]["stale"] is True and state["check"]["changedSteps"] == [2]
    assert [entry["editedSinceCheck"] for entry in state["check"]["verdicts"]] == [False, True]
    assert _check(ctx, wb)["status"] == "ready"
    assert len([row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]) == 2


def test_a_checked_step_says_checked_only_when_the_sandbox_ran_and_its_controls_behaved(tmp_path):
    def answer(context):
        payload = check_answer(context)
        # Each claim is the learner's own (fix round 1, F3): its input in the
        # problem or an earlier step, its result in the step.
        payload["steps"][0]["transformation"] = _transformation(kind="integration", expression="2*x", result="x**2",
                                                                variable="x")
        payload["steps"][1]["transformation"] = _transformation(kind="substitution", expression="x**2",
                                                                result="1/4 + 1", variable="x", value="1/2")
        return payload

    calls = []

    def fake_run(command, **kwargs):
        # Stands for the sandbox: the claims arrive as data; the fixed
        # harness's answer for them (the controls behaved).
        payload = json.loads((__import__("pathlib").Path(command[-1]) / "input.json").read_text())
        calls.append(payload)
        # ``bound``: the harness parsed the learner's own step and the
        # declaration agreed with it (fix round 3); nothing else is trusted.
        results = [{"index": 1, "method": "checked", "holds": True, "reason": "", "bound": True},
                   {"index": 2, "method": "checked", "holds": False, "reason": "", "bound": True}]
        out = ("@@PF-SANDBOX-RESULT@@" + json.dumps({"results": results})).encode()
        return type("Done", (), {"returncode": 0, "stdout": out, "stderr": b""})()

    _paths, ctx, _session = sidecar(tmp_path, symbolic=True, check=CheckFake([answer]))
    ctx.workbench_sandbox_run = fake_run
    import learnloop.content.authoring.pf_sandbox as pf

    original = pf.require_sandbox
    pf.require_sandbox = lambda: "/usr/bin/bwrap"
    try:
        wb, _chains = open_problem(ctx, steps=(STEP_1, "so F(1/2) = 1/4 + 1"))
        view = _check(ctx, wb)["check"]
    finally:
        pf.require_sandbox = original
    first, second = view["verdicts"]
    assert (first["method"], first["mark"], first["label"]) == ("checked", "✓", "checked")
    assert (second["method"], second["mark"], second["verdict"]) == ("checked", "≠", "questionable")
    # Only the declared kinds went to the sandbox, as data, each with the
    # learner's own step to parse and check (fix round 3).
    assert [claim["kind"] for claim in calls[0]["claims"]] == ["integration", "substitution"]
    assert [claim["text"] for claim in calls[0]["claims"]] == [STEP_1, "so F(1/2) = 1/4 + 1"]
    assert calls[0]["claims"][1]["earlier"] == [STEP_1]


def test_a_harness_verdict_without_the_learners_parse_is_never_shown_as_checked(tmp_path):
    def answer(context):
        payload = check_answer(context)
        payload["steps"][0]["transformation"] = _transformation(kind="equivalence", expression="x**2", result="x*x")
        return payload

    def fake_run(command, **kwargs):
        # A verdict the harness did not tie to the learner's parsed step.
        results = [{"index": 1, "method": "checked", "holds": True, "reason": ""}]
        out = ("@@PF-SANDBOX-RESULT@@" + json.dumps({"results": results})).encode()
        return type("Done", (), {"returncode": 0, "stdout": out, "stderr": b""})()

    _paths, ctx, _session = sidecar(tmp_path, symbolic=True, check=CheckFake([answer]))
    ctx.workbench_sandbox_run = fake_run
    import learnloop.content.authoring.pf_sandbox as pf

    original = pf.require_sandbox
    pf.require_sandbox = lambda: "/usr/bin/bwrap"
    try:
        wb, _chains = open_problem(ctx)
        view = _check(ctx, wb)["check"]
    finally:
        pf.require_sandbox = original
    assert view["verdicts"][0]["method"] == "model"


def test_without_bubblewrap_every_verdict_reads_as_the_models_reading(tmp_path, monkeypatch):
    def answer(context):
        payload = check_answer(context)
        payload["steps"][0]["transformation"] = _transformation(kind="equivalence", expression="x**2", result="x*x")
        return payload

    import learnloop.content.authoring.pf_sandbox as pf

    monkeypatch.setattr(pf, "_sandbox_bwrap_path", lambda: None)
    _paths, ctx, _session = sidecar(tmp_path, symbolic=True, check=CheckFake([answer]))
    wb, _chains = open_problem(ctx)
    view = _check(ctx, wb)["check"]
    assert {entry["method"] for entry in view["verdicts"]} == {"model"}
    assert all(entry["label"] == "model's reading, not checked" for entry in view["verdicts"])
    assert view["symbolicAvailable"] is False


def test_an_undeclared_kind_is_never_attempted(tmp_path):
    claims = [symbolic.SymbolicClaim(1, "proof_by_vibes", "x", "x"), symbolic.SymbolicClaim(2, "", "", "")]
    outcomes, problem = symbolic.run_checks(claims, run=lambda *a, **k: pytest.fail("the sandbox ran"))
    assert outcomes == [] and problem is None


def test_with_symbolic_checks_off_the_sandbox_never_runs(tmp_path):
    def answer(context):
        payload = check_answer(context)
        payload["steps"][0]["transformation"] = _transformation(kind="equivalence", expression="x**2", result="x*x")
        return payload

    _paths, ctx, _session = sidecar(tmp_path, "[workbench]\nsymbolic_checks_enabled = false\n",
                                    check=CheckFake([answer]))
    ctx.workbench_sandbox_run = lambda *a, **k: pytest.fail("the sandbox ran")
    wb, _chains = open_problem(ctx)
    assert {entry["method"] for entry in _check(ctx, wb)["check"]["verdicts"]} == {"model"}


def test_a_reason_that_would_give_the_answer_is_replaced(tmp_path):
    def answer(context):
        payload = check_answer(context)
        payload["steps"][1]["reason"] = "the answer is 1/4, not this"
        return payload

    paths, ctx, _session = sidecar(tmp_path, check=CheckFake([answer]))
    wb, _chains = open_problem(ctx)
    second = _check(ctx, wb)["check"]["verdicts"][1]
    assert "1/4" not in second["reason"]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert "reason_gives_answer:2" in json.loads(row["contract_failures_json"])["dropped"]


def test_unknown_steps_later_dependencies_and_foreign_quotes_are_dropped(tmp_path):
    def answer(context):
        payload = check_answer(context)
        payload["steps"].append(_step(7, "valid"))
        payload["steps"][0]["depends_on"] = [2]
        payload["steps"][1]["quote"] = "a line the learner never wrote"
        return payload

    paths, ctx, _session = sidecar(tmp_path, check=CheckFake([answer]))
    wb, _chains = open_problem(ctx)
    view = _check(ctx, wb)["check"]
    assert view["verdicts"][0]["dependsOn"] == []
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    dropped = json.loads(row["contract_failures_json"])["dropped"]
    assert {"unknown_step:7", "depends_on_not_earlier:1->2", "quote_not_in_step:2"} <= set(dropped)


def test_a_check_runs_on_codex_with_its_cost_estimated_from_tokens(tmp_path):
    # Fix round 1, F12: the owner's decision (2026-10-12) lets Codex run every
    # paid role on the subscription; no price is needed and the receipt is
    # estimated_only.
    from tests.hint_fakes import receipts

    paths, ctx, _session = sidecar(tmp_path, check=CheckFake(provider_type="codex_sdk"))
    wb, _chains = open_problem(ctx)
    result = _check(ctx, wb)
    assert result["status"] == "ready" and result["shown"] is True
    assert ctx.workbench_check_client.calls == 1
    [receipt] = receipts(paths.sqlite_path, check_module.OWNER_KIND)
    assert "estimated_only" in json.dumps({key: receipt[key] for key in receipt if receipt[key] is not None})
    assert call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]["hints"] == 1


def test_the_per_problem_call_cap_holds(tmp_path):
    _paths, ctx, _session = sidecar(tmp_path, "[workbench]\nmax_calls_per_session = 1\n")
    wb, chains = open_problem(ctx)
    assert _check(ctx, wb)["status"] == "ready"
    call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "s9", "op": "add", "bodyMd": "P = 1/4",
                                      "afterStepId": chains[-1]})
    capped = _check(ctx, wb)
    assert capped["status"] == "unavailable" and capped["reason"] == "session_capped"
    assert "Hints still work" in capped["message"]


def test_a_metered_check_needs_a_price_and_the_daily_cap_holds(tmp_path):
    _paths, ctx, _session = sidecar(tmp_path, check=CheckFake(provider_type="openrouter"))
    wb, _chains = open_problem(ctx)
    unpriced = _check(ctx, wb)
    assert unpriced["reason"] == "unpriced"
    paths2, ctx2, _session2 = sidecar(tmp_path / "capped", "[workbench]\nprice_per_million = 5.0\nmax_daily_cost_usd = 0\n",
                                      check=CheckFake(provider_type="openrouter"))
    wb2, _chains2 = open_problem(ctx2)
    capped = _check(ctx2, wb2)
    assert capped["reason"] == "capped" and "$0.00" in capped["message"]
    assert ctx2.workbench_check_client.calls == 0


def test_a_cancelled_check_is_never_shown_and_counts_nothing(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    ctx.hints_inline = False
    wb, _chains = open_problem(ctx)
    started = call(ctx, "workbench.check", {"sessionId": wb})
    assert call(ctx, "workbench.cancel_help", {"jobId": started["jobId"]})["cancelled"] is True
    from learnloop.hints import map_builder  # noqa: F401

    job = ctx.workbench_help_jobs.get(started["jobId"])
    assert job.done.wait(30)
    assert call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["state"] == "cancelled"
    assert all(row["shown"] == 0 for row in help_rows(paths, wb))
    assert call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]["hints"] == 0


def test_check_and_help_wait_for_setup_and_refuse_while_switched_off(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.workbench as handler

    monkeypatch.setattr(handler, "_enqueue_import", lambda ctx, vault, repository, request: "batch_1")
    _paths, ctx, _session = sidecar(tmp_path)
    view = call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "stemMd": "Find P.",
                                        "extractionId": "ext", "spanIds": ["s1"],
                                        "importRequest": {"extractionId": "ext", "rawSelection": {"nodes": []}}})["session"]
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError) as unbound:
        call(ctx, "workbench.check", {"sessionId": view["sessionId"]})
    assert unbound.value.code == "not_bound"
    _paths2, ctx2, _session2 = sidecar(tmp_path / "off", "[workbench]\nhelp_enabled = false\n")
    wb, _chains = open_problem(ctx2)
    for name, params in (("workbench.check", {}), ("workbench.suggest_help", {}), ("workbench.request_help", {"takenLevel": 1}),
                         ("workbench.help_state", {}), ("workbench.set_help_style", {"helpStyle": "guide_me"})):
        with pytest.raises(SidecarError) as off:
            call(ctx2, name, {"sessionId": wb, **params})
        assert off.value.code == "help_disabled"


def test_the_prompt_carries_the_steps_and_the_map_never_a_grader(tmp_path):
    fake = CheckFake()
    _paths, ctx, _session = sidecar(tmp_path, check=fake)
    wb, _chains = open_problem(ctx)
    _check(ctx, wb)
    context = fake.contexts[0]
    assert [entry["text"] for entry in context["steps"]] == [STEP_1, STEP_2]
    assert {node["id"] for node in context["approach_map"]["nodes"]} == {"g", "cdf", "goal"}
    assert "declared_kinds" in context and check_module.PROMPT_VERSION in fake.prompts[0]


def test_during_a_diagnostic_block_no_check_or_hint_reaches_a_model(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice

    fake = CheckFake()
    _paths, ctx, _session = sidecar(tmp_path, check=fake)
    wb, _chains = open_problem(ctx)
    monkeypatch.setattr(practice, "_in_diagnostic_block", lambda repository, item: True)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["reason"] == "diagnostic_block"
    assert run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))["reason"] == "diagnostic_block"
    assert run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))["reason"] == \
        "diagnostic_block"
    assert fake.calls == 0 and ctx.hint_writer_client.calls == 0
