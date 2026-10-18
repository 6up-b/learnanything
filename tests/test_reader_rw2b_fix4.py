"""Reader workbench RW2b + hints H3, fix round 4: the whole-stage Codex verify's items, under the orchestrator's rulings.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 4 (orchestrator)":

1. a text that would need clipping is never checked (never a truncated prefix);
2. solving is never checked when the written equation restricts the variable
   (a denominator, a log, an even root, a negative power);
3. a hint claim's statement longer than its display bound is never checked;
4. the client's count and the open problem's server assists add up; only the
   carried overlap counts once (the transactional refold too);
5. (Codex for ``workbench_check``: rejected, no code change);
6. an n-th root (n != 2) and a fractional power of a possibly negative base
   are never checked;
7. ``workbench.cancel_help`` refuses ``help_disabled`` like the other seven.

Fakes only; the symbolic tests run the real PF-b sandbox (skipped without
bubblewrap). No model is reached.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3

import pytest

import learnloop_sidecar.handlers.practice as practice_handler
from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.workbench.symbolic import CHECKED, MODEL, SymbolicClaim, run_checks
from learnloop_sidecar.errors import SidecarError
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar, wb_answer

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _outcomes(*claims):
    outcomes, problem = run_checks(list(claims))
    assert problem is None
    return [(o.method, o.holds) for o in outcomes]


# -- Item 1: never check a truncated prefix -------------------------------------------------------


@needs_bwrap
def test_item1_a_long_step_is_checked_whole_or_not_at_all():
    # The verify's reproduction: 1=1, then padding, then +1 (the step says 1 = 2).
    padded = "1=1" + " " * 1997 + "+1"
    assert _outcomes(SymbolicClaim(1, "equivalence", "1", "", text=padded)) == [(CHECKED, False)]
    beyond = "1=1" + " " * 4100 + "+1"
    outcomes, _problem = run_checks([SymbolicClaim(1, "equivalence", "1", "1", text=beyond)])
    assert [(o.method, o.holds, o.bound) for o in outcomes] == [(MODEL, None, False)]
    assert outcomes[0].reason == "too_long:text"


@needs_bwrap
def test_item1_an_overlong_definition_or_problem_is_never_read_in_part():
    long_definition = "f(x) = x^3" + " " * 4100 + "+ x"
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "differentiation", "x**3", "3*x**2", "x", text="f'(x) = 3x^2", earlier=(long_definition,)),
        SymbolicClaim(2, "substitution", "x**2", "4", "x", value="2", text="f(2) = 4",
                      problem="Let $f(x) = x^2$." + " " * 8100 + "$f(x) = x^3$"),
        SymbolicClaim(3, "equivalence", "x", "x", text="x = x", earlier=("1 = 1",) * 201),
    ])
    assert [(o.method, o.reason) for o in outcomes] == [
        (MODEL, "too_long:earlier"), (MODEL, "too_long:problem"), (MODEL, "too_long:earlier")]


# -- Item 2: solving never loses an excluded value ------------------------------------------------


@needs_bwrap
def test_item2_solving_against_a_written_restriction_is_never_checked():
    assert _outcomes(
        # The verify's reproduction: x^2/x = 2x is undefined at 0.
        SymbolicClaim(1, "solving", "x**2/x = 2*x", "0", "x", text="x = 0", earlier=(r"\frac{x^2}{x} = 2x",)),
        SymbolicClaim(2, "solving", "log(x) = 0", "1", "x", text="x = 1", earlier=(r"\ln(x) = 0",)),
        SymbolicClaim(3, "solving", "sqrt(x) = 2", "4", "x", text="x = 4", earlier=(r"\sqrt{x} = 2",)),
        SymbolicClaim(4, "solving", "x**(-1) = 1", "1", "x", text="x = 1", earlier=("x^{-1} = 1",)),
        # A restriction through a defined name counts too.
        SymbolicClaim(5, "solving", "1/x = 1", "1", "x", text="x = 1", earlier=(r"g(x) = \frac{1}{x}", "g(x) = 1")),
    ) == [(MODEL, None)] * 5
    # Without a restriction on the variable, a root is still checked.
    assert _outcomes(SymbolicClaim(1, "solving", "x/2 = 3", "6", "x", text="x = 6",
                                   earlier=(r"\frac{x}{2} = 3",))) == [(CHECKED, True)]


# -- Item 6: no real-root semantics -------------------------------------------------------------


@needs_bwrap
def test_item6_odd_roots_and_fractional_powers_of_a_possibly_negative_base_are_never_checked():
    assert _outcomes(
        # The verify's reproduction: the real cube root of -8 is -2; sympy's principal root is not.
        SymbolicClaim(1, "equivalence", "(-8)**(1/3)", "-2", text=r"\sqrt[3]{-8} = -2"),
        SymbolicClaim(2, "equivalence", "8**(1/3)", "2", text=r"\sqrt[3]{8} = 2"),
        SymbolicClaim(3, "equivalence", "(-8)**(1/3)", "-2", text=r"(-8)^{1/3} = -2"),
        SymbolicClaim(4, "equivalence", "x**(1/2)", "x**(1/2)", text=r"x^{1/2} = x^{1/2}"),
    ) == [(MODEL, None)] * 4
    # A fractional power of a non-negative number, and a square root, still check.
    assert _outcomes(SymbolicClaim(1, "equivalence", "4**(1/2)", "2", text="4^{1/2} = 2"),
                     SymbolicClaim(2, "equivalence", "sqrt(9)", "3", text=r"\sqrt{9} = 3")) == [
        (CHECKED, True), (CHECKED, True)]


# -- Item 3: a clipped statement is never "checked" -----------------------------------------------


def _hint_with(tmp_path, steps, claims):
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": list(claims)}, wb_answer])
    paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=tuple(steps))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    return hint, paths, ctx, wb


@needs_bwrap
def test_item3_a_claim_longer_than_its_display_bound_is_never_checked(tmp_path):
    number = "7" * 238
    claim = {"step": 1, "statement": f"0={number}-{number}", "kind": "equivalence", "expression": "0",
             "result": f"{number}-{number}", "variable": "", "value": "", "lower": "", "upper": "",
             "relation": ""}
    hint, paths, ctx, wb = _hint_with(tmp_path, ["x = x"], [claim])
    [shown] = hint["claims"]
    assert shown["status"] == "model" and shown["label"] == "model's reading, not checked"
    assert shown["statement"].endswith("…") and len(shown["statement"]) == 240
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    stored = json.loads(row["contract_failures_json"])["claims"]
    assert [entry["status"] for entry in stored] == ["model"]
    assert call(ctx, "workbench.help_state", {"sessionId": wb})["hints"][0]["claims"][0]["status"] == "model"


@needs_bwrap
def test_item3_a_checked_claim_is_stored_exactly_as_it_was_verified(tmp_path):
    claim = {"step": 1, "statement": "0  =  7 -  7", "kind": "equivalence", "expression": "0", "result": "7-7",
             "variable": "", "value": "", "lower": "", "upper": "", "relation": ""}
    hint, _paths, _ctx, _wb = _hint_with(tmp_path, ["x = x"], [claim])
    assert [(entry["status"], entry["statement"]) for entry in hint["claims"]] == [("checked", "0 = 7 - 7")]


# -- Item 4: distinct assists add up; only the carried overlap counts once -------------------------


def _box_submit(ctx, session, hints_used, key):
    return call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                        "attemptType": "independent_attempt", "hintsUsed": hints_used,
                                        "submissionId": key})


def test_item4_a_workbench_check_and_an_answer_box_reveal_are_two_assists(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    # Back on the answer box, one authored hint revealed: the client sends 1.
    attempt = _box_submit(ctx, session, 1, "box-two")
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_item4_the_transactional_refold_adds_a_check_shown_during_grading(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    real = practice_handler._server_hint_fold
    done = []

    def fold_then_check(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not done:
            done.append(run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb})))
        return fold

    monkeypatch.setattr(practice_handler, "_server_hint_fold", fold_then_check)
    attempt = _box_submit(ctx, session, 1, "box-late-two")
    assert done and done[0]["shown"] is True
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


@pytest.mark.parametrize("client", [0, 1])
def test_item4_a_carried_count_alone_still_records_one(tmp_path, grader, client):
    paths, ctx, session = sidecar(tmp_path)
    opened = call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                          "stemMd": "Find P(X <= 1/2).", "carriedHints": 1})["session"]
    assert opened["carriedHints"] == 1
    attempt = _box_submit(ctx, session, client, f"box-carried-{client}")
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_item4_a_carried_hint_and_a_check_on_the_workbench_submit_are_two(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    opened = call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                          "stemMd": "Find P(X <= 1/2).", "carriedHints": 1})["session"]
    wb = opened["sessionId"]
    call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "s0", "op": "add",
                                      "bodyMd": "F(x) = x^2 on [0, 1]", "afterStepId": None})
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


# -- Item 7: all eight RPCs go through the switch guard -------------------------------------------

RPCS = [
    ("workbench.check", lambda wb, job: {"sessionId": wb}),
    ("workbench.suggest_help", lambda wb, job: {"sessionId": wb}),
    ("workbench.request_help", lambda wb, job: {"sessionId": wb, "takenLevel": 1}),
    ("workbench.help_job", lambda wb, job: {"jobId": job}),
    ("workbench.cancel_help", lambda wb, job: {"jobId": job}),
    ("workbench.answer_discriminating", lambda wb, job: {"sessionId": wb, "questionAssistId": "ha_x",
                                                         "answerMd": "because"}),
    ("workbench.set_help_style", lambda wb, job: {"sessionId": wb, "helpStyle": "balanced"}),
    ("workbench.help_state", lambda wb, job: {"sessionId": wb}),
]


@pytest.mark.parametrize("name,params", RPCS, ids=[name for name, _params in RPCS])
def test_item7_every_help_rpc_refuses_when_help_is_switched_off(tmp_path, name, params):
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    ctx.hints_inline = False
    started = call(ctx, "workbench.check", {"sessionId": wb})
    assert started["state"] == "pending"
    job = ctx.workbench_help_jobs.get(started["jobId"])
    assert job.done.wait(30)
    ctx.hints_inline = True
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text() + "\n[workbench]\nhelp_enabled = false\n")
    ctx.reload()
    with pytest.raises(SidecarError) as refused:
        call(ctx, name, params(wb, started["jobId"]))
    assert refused.value.code == "help_disabled"
    if name == "workbench.cancel_help":
        # Refused before the job was looked up or changed.
        assert job.cancelled is False
    assert [row["shown"] for row in help_rows(paths, wb)] == [0]
