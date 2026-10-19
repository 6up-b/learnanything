"""Reader workbench RW2b + hints H3: the Codex review's findings, reproduced (fix round 1).

Each test reproduces one finding of ``docs/reviews/reader-rw2b-h3-codex-review.md``
and pins its fix. Fakes only: no model is reached.
"""

from __future__ import annotations

from contextlib import closing
import sqlite3

import learnloop_sidecar.handlers.practice as practice_handler
from tests.hint_fakes import ITEM, WORK, ChooserFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import FUNCTION_FREE_PROMPT, call, help_rows, open_problem, run_job, sidecar


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def _attempt(paths, attempt_id):
    [row] = _rows(paths, "SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,))
    return row


def _take(ctx, wb, level, **params):
    return run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": level, **params}))


def _during_grading(monkeypatch, action):
    """Run ``action`` once, after the submit read its counts and before it
    grades (another sidecar's hint, written and delivered meanwhile)."""

    real = practice_handler._server_hint_fold
    done = []

    def fold_then_act(*args, **kwargs):
        fold = real(*args, **kwargs)
        if not done:
            done.append(action())
        return fold

    monkeypatch.setattr(practice_handler, "_server_hint_fold", fold_then_act)
    return done


# -- F1: help written after the admission and shown during grading is counted -------------------


def test_f1_a_workbench_hint_written_and_shown_during_grading_counts_in_the_workbench_attempt(
        tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx)
    late = _during_grading(monkeypatch, lambda: _take(ctx, wb, 3))
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert late and late[0]["shown"] is True
    row = _attempt(paths, attempt["attemptId"])
    assert row["hints_used"] == 1 and row["attempt_type"] != "independent_attempt"
    assert {r["attempt_id"] for r in help_rows(paths, wb) if r["shown"]} == {row["id"]}


def test_f1_worked_help_shown_during_grading_primes_the_workbench_attempt(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    late = _during_grading(monkeypatch, lambda: _take(ctx, wb, 4))
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert late and late[0]["shown"] is True
    row = _attempt(paths, attempt["attemptId"])
    assert (row["hints_used"], row["primed"]) == (0, 1)


def test_f1_an_open_problems_check_shown_during_an_answer_box_submit_counts_there(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    late = _during_grading(monkeypatch, lambda: run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb})))
    attempt = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                           "attemptType": "independent_attempt", "hintsUsed": 0,
                                           "submissionId": "box-late"})
    assert late and late[0]["shown"] is True
    row = _attempt(paths, attempt["attemptId"])
    assert row["hints_used"] == 1 and row["attempt_type"] != "independent_attempt"


def test_f1_no_help_leaves_the_submit_as_it_was(tmp_path, grader, monkeypatch):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    _during_grading(monkeypatch, lambda: None)
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    row = _attempt(paths, attempt["attemptId"])
    assert (row["hints_used"], row["primed"], row["attempt_type"]) == (0, 0, "independent_attempt")


# -- F15: workbench hints never start outcome placement ---------------------------------------


def test_f15_a_partly_correct_workbench_attempt_with_a_mapped_hint_starts_no_outcome_call(
        tmp_path, grader):
    from learnloop.db.repositories import Repository
    from learnloop.hints import outcome
    from learnloop.vault.loader import load_vault
    from tests.test_hint_outcome import OutcomeFake

    paths, ctx, session = sidecar(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx)
    assert _take(ctx, wb, 3)["shown"] is True
    attempt_id = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]["attemptId"]
    [hint] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert hint["attempt_id"] == attempt_id and hint["map_id"]
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        # Graded partly correct, with a written answer: due, were it a practice hint.
        connection.execute("UPDATE practice_attempts SET correctness = 0.5 WHERE id = ?", (attempt_id,))
        connection.commit()
    fake = OutcomeFake()
    vault = load_vault(paths.root)
    assert outcome.place_outcome(vault, Repository.attach(paths.sqlite_path), attempt_id, client=fake).status \
        == "not_due"
    assert outcome.schedule_outcome_placement(vault, paths.sqlite_path, attempt_id, client=fake) is None
    assert attempt_id not in outcome.unplaced_attempts(paths.sqlite_path, since="2000-01-01T00:00:00Z")
    assert fake.calls == 0


# -- F13: the help switch stops delivery of a pending job ------------------------------------


def _pending(ctx, name, params):
    ctx.hints_inline = False
    started = call(ctx, name, params)
    assert started["state"] == "pending"
    assert ctx.workbench_help_jobs.get(started["jobId"]).done.wait(30)
    ctx.hints_inline = True
    return started


def _switch(paths, ctx, line):
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text() + f"\n[workbench]\n{line}\n")
    ctx.reload()


def test_f13_switching_help_off_while_a_check_is_pending_delivers_and_counts_nothing(tmp_path, grader):
    import pytest

    from learnloop_sidecar.errors import SidecarError

    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    started = _pending(ctx, "workbench.check", {"sessionId": wb})
    _switch(paths, ctx, "help_enabled = false")
    with pytest.raises(SidecarError) as refused:
        call(ctx, "workbench.help_job", {"jobId": started["jobId"]})
    assert refused.value.code == "help_disabled"
    assert [row["shown"] for row in help_rows(paths, wb)] == [0]
    attempt = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 0


def test_f13_a_pending_hint_is_cancelled_by_the_switch_and_stays_cancelled(tmp_path, grader):
    import pytest

    from learnloop_sidecar.errors import SidecarError

    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    started = _pending(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    toml = paths.root / "learnloop.toml"
    before = toml.read_text()
    _switch(paths, ctx, "help_enabled = false")
    with pytest.raises(SidecarError):
        call(ctx, "workbench.help_job", {"jobId": started["jobId"]})
    toml.write_text(before)
    ctx.reload()
    assert call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["state"] == "cancelled"
    assert [row["shown"] for row in help_rows(paths, wb)] == [0]


def test_f13_a_bridge_waiting_when_its_switch_goes_off_is_never_shown(tmp_path, grader):
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    hint = _take(ctx, wb, 3)
    assert hint["shown"] is True and hint.get("bridgeJobId")
    _switch(paths, ctx, "bridge_enabled = false")
    assert call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["state"] == "cancelled"
    assert not [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge" and row["shown"]]


# -- F11: every key RW2b added has a rule in the parameter registry --------------------------

#: The keys RW2b added (``[workbench]`` and the check's route), booleans included.
RW2B_KEYS = (
    "workbench.help_enabled", "workbench.symbolic_checks_enabled", "workbench.discriminate_enabled",
    "workbench.error_kind_enabled", "workbench.bridge_enabled", "workbench.max_calls_per_session",
    "workbench.max_daily_cost_usd", "workbench.price_per_million", "ai.routing.workbench_check",
)


def test_f11_every_key_rw2b_added_is_classified():
    from learnloop.config.schema import WorkbenchConfig
    from learnloop.params import parameter_registry as registry

    # The set is complete: every [workbench] field except RW2a's two.
    added = {f"workbench.{name}" for name in WorkbenchConfig.model_fields} - {
        "workbench.enabled", "workbench.open_session_days"}
    assert added == {key for key in RW2B_KEYS if key.startswith("workbench.")}
    unclassified = [key for key in RW2B_KEYS if registry.classify_config_path(key) is None]
    assert unclassified == []


# -- F4: the check's assumptions are leak-checked like its reasons ----------------------------


def test_f4_an_assumption_that_states_the_answer_is_never_shown(tmp_path):
    import json

    from tests.workbench_help_fakes import CheckFake, check_answer

    def answer(context):
        payload = check_answer(context)
        payload["assumptions"] = ["The final answer is 1/4.", "X has density 2x on [0, 1]"]
        payload["steps"][0]["assumption"] = "P(X <= 1/2) = 1/4"
        return payload

    paths, ctx, _session = sidecar(tmp_path, check=CheckFake([answer]))
    wb, _chains = open_problem(ctx)
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    shown = json.dumps(view)
    assert "1/4" not in shown
    assert view["assumptions"] == ["X has density 2x on [0, 1]"]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert "1/4" not in (row["placement_json"] or "") + (row["step_verdicts_json"] or "")
    dropped = set(json.loads(row["contract_failures_json"])["dropped"])
    assert {"assumptions_gives_answer:0", "assumption_gives_answer:1"} <= dropped


# -- F2: "checked" only for what sympy decides exactly, never a domain-dependent identity -------


def _needs_bwrap():
    import pytest

    from learnloop.content.authoring.pf_sandbox import sandbox_available

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")


def test_f2_false_or_domain_dependent_identities_are_never_checked_as_holding():
    from learnloop.workbench.symbolic import CHECKED, MODEL, SymbolicClaim, run_checks

    _needs_bwrap()
    # Fix round 3: each is the learner's own LaTeX, parsed by code.
    outcomes, problem = run_checks([
        SymbolicClaim(1, "equivalence", "Abs(x)", "x", text="|x| = x"),
        SymbolicClaim(2, "equivalence", "sqrt(x**2)", "x", text=r"\sqrt{x^2} = x"),
        SymbolicClaim(3, "equivalence", "1/10000000000", "0", text=r"\frac{1}{10000000000} = 0"),
        SymbolicClaim(4, "equivalence", "log(x*y)", "log(x) + log(y)", text=r"\log(x \cdot y) = \log(x) + \log(y)"),
    ])
    assert problem is None
    found = [(o.method, o.holds) for o in outcomes]
    # Abs, sqrt and log hold only for positive values the step never states:
    # the model's reading. A tiny constant is not zero: checked, doesn't follow.
    assert found == [(MODEL, None), (MODEL, None), (CHECKED, False), (MODEL, None)]


def test_f2_exact_identities_and_decimals_keep_their_labels():
    from learnloop.workbench.symbolic import CHECKED, CHECKED_NUMERICALLY, SymbolicClaim, run_checks

    _needs_bwrap()
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "equivalence", "sin(x)**2 + cos(x)**2", "1", text=r"(\sin x)^2 + (\cos x)^2 = 1"),
        SymbolicClaim(2, "equivalence", "0.1 + 0.2", "0.3", text="0.1 + 0.2 = 0.3"),
        SymbolicClaim(3, "equivalence", "0.1 + 0.2", "0.31", text="0.1 + 0.2 = 0.31"),
        SymbolicClaim(4, "differentiation", "x**3", "3*x**2 + 1", variable="x",
                      text=r"\frac{d}{dx}\left(x^3\right) = 3x^2 + 1"),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [
        (CHECKED, True), (CHECKED_NUMERICALLY, True), (CHECKED_NUMERICALLY, False), (CHECKED, False)]


# -- F3: a transformation speaks for its step only when it is the learner's ----------------


def _arithmetic_check(transformation):
    from tests.workbench_help_fakes import step_check

    def answer(_context):
        return {"steps": [step_check(1, "questionable", reason="the product is off", quote="6 * 7 = 43",
                                     transformation=transformation)],
                "first_questionable_step": 1, "error_kind_guess": "invalid_algebra",
                "error_kind_reason": "a slip", "error_readings": [], "assumptions": []}

    return answer


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def test_f3_an_unrelated_checked_expression_never_validates_the_learners_step(tmp_path):
    import json

    from tests.workbench_help_fakes import CheckFake

    _needs_bwrap()
    check = CheckFake([_arithmetic_check(_transformation(kind="equivalence", expression="1+1", result="2"))])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, check=check)
    wb, _chains = open_problem(ctx, steps=("6 * 7 = 43",))
    [verdict] = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]["verdicts"]
    assert (verdict["verdict"], verdict["method"], verdict["mark"]) == ("questionable", "model", "?")
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    assert "transformation_not_in_step:1" in json.loads(row["contract_failures_json"])["dropped"]
    [recorded] = json.loads(row["placement_json"])["symbolic"]
    # Fix round 3: a declaration that disagrees with the parse is never checked at all.
    assert recorded["bound"] is False and recorded["holds"] is None


def test_f3_the_learners_own_expression_is_checked_and_decides_the_step(tmp_path):
    from tests.workbench_help_fakes import CheckFake

    _needs_bwrap()
    check = CheckFake([_arithmetic_check(_transformation(kind="equivalence", expression="6*7", result="43"))])
    _paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, check=check)
    wb, _chains = open_problem(ctx, steps=("6 * 7 = 43",))
    [verdict] = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]["verdicts"]
    assert (verdict["verdict"], verdict["method"], verdict["mark"]) == ("questionable", "checked", "≠")


# -- F9: the bridge is held to the workbench's call cap and daily envelope -------------------


class _BridgeProbe:
    """T6's provider stand-in: records each search and the envelopes active
    while it runs; finds nothing unless given spans."""

    def __init__(self, spans=None):
        self.spans = list(spans or [])
        self.envelopes = []

    def __call__(self, vault, repository, **kwargs):
        from learnloop.ai.spend import active_envelopes

        self.envelopes.append([envelope.name for envelope in active_envelopes()])
        return list(self.spans), {"basis": "retrieved_verified" if self.spans else "lo_provenance"}


def _reader_hint(ctx, wb):
    hint = _take(ctx, wb, 3)
    assert hint["shown"] is True
    return hint


def test_f9_a_search_that_finds_nothing_still_counts_against_the_problems_calls(tmp_path, grader):
    paths, ctx, _session = sidecar(tmp_path, "[workbench]\nmax_calls_per_session = 1\n")
    probe = _BridgeProbe()
    ctx.workbench_bridge_provider = probe
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    first = _reader_hint(ctx, wb)
    assert call(ctx, "workbench.help_job", {"jobId": first["bridgeJobId"]})["result"]["status"] == "none"
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    assert row["shown"] == 0 and '"status": "none"' in row["placement_json"]
    # The one call this problem may make is spent: no second search, no check.
    second = _reader_hint(ctx, wb)
    assert second.get("bridgeJobId") is None and len(probe.envelopes) == 1
    capped = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    assert capped["reason"] == "session_capped"


def test_f9_the_search_takes_its_place_before_it_runs_so_a_second_one_is_refused(tmp_path, grader, monkeypatch):
    import learnloop_sidecar.handlers.workbench_help as handler
    from learnloop.workbench.bridge import bridge_for_hint

    _paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    vault, repository = ctx.require_vault()
    monkeypatch.setattr(handler, "_start_bridge", lambda *args, **kwargs: None)
    hint = _reader_hint(ctx, wb)
    probe = _BridgeProbe()
    results = [bridge_for_hint(vault, repository, workbench_session_id=wb, hint_assist_id=hint["assistId"],
                               item=vault.practice_items[ITEM], provider=probe, max_calls=1) for _ in range(2)]
    assert [result.get("reason") for result in results] == [None, "session_capped"]
    assert len(probe.envelopes) == 1


def test_f9_the_search_runs_inside_the_workbench_envelope_and_a_spent_day_refuses_it(tmp_path, grader, monkeypatch):
    import learnloop.workbench.bridge as bridge
    from learnloop.workbench import check as check_module

    paths, ctx, _session = sidecar(tmp_path)
    probe = _BridgeProbe([{"span_id": "s9", "extraction_id": "ext", "label": "Book · §5.3", "text": "step"}])
    ctx.workbench_bridge_provider = probe
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    hint = _reader_hint(ctx, wb)
    assert call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]["status"] == "ready"
    assert check_module.ENVELOPE in probe.envelopes[0]
    # A zero budget with a metered verification route: refused before the search.
    paths2, ctx2, _session2 = sidecar(tmp_path / "zero", "[workbench]\nmax_daily_cost_usd = 0\n")
    probe2 = _BridgeProbe([{"span_id": "s9", "extraction_id": "ext", "label": "x", "text": "y"}])
    ctx2.workbench_bridge_provider = probe2
    monkeypatch.setattr(bridge, "_metered_verification", lambda vault: True)
    wb2, _chains2 = open_problem(ctx2, origin="reader", entry="work_through")
    hint2 = _reader_hint(ctx2, wb2)
    refused = call(ctx2, "workbench.help_job", {"jobId": hint2["bridgeJobId"]})["result"]
    assert refused["status"] == "unavailable" and refused["reason"] == "capped"
    assert probe2.envelopes == []


# -- F10: the check's verdicts reach judgment_ledger -----------------------------------------


def test_f10_a_check_appends_the_models_and_the_verifiers_verdicts_with_the_row(tmp_path):
    import json

    from tests.workbench_help_fakes import STEP_1, CheckFake, check_answer

    _needs_bwrap()

    def answer(context):
        payload = check_answer(context)
        payload["steps"][0]["transformation"] = _transformation(kind="integration", expression="2*x",
                                                                result="x**2", variable="x")
        payload["steps"][1]["reason"] = "the answer is 1/4, not this"
        return payload

    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, check=CheckFake([answer]))
    # Fix round 3: the verifier checks the step as written, so step 1 is in LaTeX.
    assert STEP_1.endswith("on [0, 1]")
    wb, chains = open_problem(ctx, steps=(r"\int 2x  dx = x^2", "so P(X <= 1/2) = F(1/2) + 1"))
    result = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    rows = _rows(paths, "SELECT * FROM judgment_ledger WHERE left_kind = 'help_assist' AND left_id = ? "
                        "ORDER BY task, right_id", (result["assistId"],))
    llm = {row["right_id"]: row for row in rows if row["task"] == "workbench_check"}
    assert set(llm) == set(chains)
    assert {row["judge"] for row in llm.values()} == {"llm"}
    assert llm[chains[0]]["verdict"] == "valid" and llm[chains[1]]["verdict"] == "questionable"
    assert llm[chains[0]]["judge_model"] == "fake-check-model"
    second = json.loads(llm[chains[1]]["rationale"])
    assert second["validation"] == ["reason_gives_answer:2"] and second["error_kind_guess"] == "conceptual"
    [verifier] = [row for row in rows if row["task"] == "workbench_check_symbolic"]
    assert (verifier["judge"], verifier["right_id"], verifier["verdict"]) == ("verifier", chains[0], "holds")
    assert json.loads(verifier["rationale"])["bound"] is True


def test_f10_an_unavailable_check_appends_nothing(tmp_path):
    from tests.workbench_help_fakes import CheckFake

    paths, ctx, _session = sidecar(tmp_path, "[workbench]\nmax_calls_per_session = 1\n",
                                   check=CheckFake(fail=RuntimeError("down")))
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["status"] == "unavailable"
    assert _rows(paths, "SELECT * FROM judgment_ledger WHERE task LIKE 'workbench_check%'") == []


# -- F14: a hint's own claims are verified before it is shown -------------------------------


def _claim(step, statement, **values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {"step": step, "statement": statement, **base, **values}


def _with_claims(*claims):
    from tests.workbench_help_fakes import wb_answer

    def answer(context):
        return {**wb_answer(context), "claims": list(claims)}

    return answer


# Fix round 3: a claim is checked only when its own statement parses (LaTeX,
# one relation) and holds; its declaration must agree with that parse.
TRUE_CLAIM = _claim(1, r"\int 2x  dx = x^2", kind="integration", expression="2*x", result="x**2", variable="x")
FALSE_CLAIM = _claim(2, r"\frac{d}{dx}\left(x^2\right) = 2x + 1", kind="differentiation", expression="x^2",
                     result="2*x + 1", variable="x")
# Fix round 8: no function notation in the steps (it would disable every check).
FALSE_STEPS = ("x^2 = x^2", "2x = 2x")
TRUE_STEPS = FALSE_STEPS


def test_f14_a_hints_checkable_claim_is_verified_and_labelled_checked(tmp_path):
    from tests.hint_fakes import WriterFake

    _needs_bwrap()
    writer = WriterFake([_with_claims(TRUE_CLAIM)])
    _paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT,
                                    writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=TRUE_STEPS)
    hint = _take(ctx, wb, 3)
    assert hint["status"] == "ready" and writer.calls == 1
    assert [(claim["status"], claim["label"]) for claim in hint["claims"]] == [("checked", "checked")]
    # The workbench prompt asks for claims; the practice screen's never does.
    assert "claims_rule" in writer.contexts[0]["workbench"]
    restored = call(ctx, "workbench.help_state", {"sessionId": wb})["hints"][0]
    assert restored["claims"][0]["status"] == "checked"


def test_f14_a_claim_that_does_not_hold_is_reasked_once_naming_it(tmp_path):
    from tests.hint_fakes import WriterFake

    _needs_bwrap()
    writer = WriterFake([_with_claims(FALSE_CLAIM), _with_claims(TRUE_CLAIM)])
    _paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT,
                                    writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=FALSE_STEPS)
    hint = _take(ctx, wb, 3)
    assert hint["status"] == "ready" and writer.calls == 2
    assert "wb_claim_failed:2" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert [claim["status"] for claim in hint["claims"]] == ["checked"]


def test_f14_a_claim_failing_twice_falls_to_the_next_step_without_it(tmp_path):
    from tests.hint_fakes import WriterFake
    from tests.workbench_help_fakes import wb_answer

    _needs_bwrap()
    writer = WriterFake([_with_claims(FALSE_CLAIM), _with_claims(FALSE_CLAIM), wb_answer])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT,
                                   writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=FALSE_STEPS)
    hint = _take(ctx, wb, 3)
    assert writer.calls == 3 and hint["status"] == "ready" and hint["kind"] == "next_step"
    assert hint["claims"] == []
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    import json

    rounds = json.loads(row["contract_failures_json"])["rounds"]
    assert [entry["claims"][0]["status"] for entry in rounds[:2]] == ["failed", "failed"]


def test_f14_an_uncheckable_claim_is_shown_as_the_models_reading(tmp_path):
    from tests.hint_fakes import WriterFake

    writer = WriterFake([_with_claims(_claim(1, "your step 1 stands as written"))])
    _paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx)
    hint = _take(ctx, wb, 3)
    assert [(claim["status"], claim["label"]) for claim in hint["claims"]] == [
        ("model", "model's reading, not checked")]


# == Re-review (Codex, job 20261018-172852-5htI4v) ============================================

# -- F3 (reopened): a transformation binds to the learner's whole assertion --------------------


def _wb_step(number, body):
    from learnloop.hints.workbench import WorkbenchStep

    return WorkbenchStep(chain_id=f"c{number}", step_id=f"s{number}", number=number, kind="step", body_md=body)


def _checks(steps, transformation, *, problem=""):
    """How the last of ``steps`` is checked against ``transformation`` (fix
    round 3: the step's own LaTeX parsed in the real sandbox)."""

    from learnloop.workbench.check import Transformation, _claim as claim_of
    from learnloop.workbench.symbolic import run_checks

    *earlier, step = [_wb_step(index + 1, body) for index, body in enumerate(steps)]
    [outcome], _problem = run_checks([claim_of(1, Transformation(**_transformation(**transformation)), step.body_md,
                                               earlier, problem)])
    return outcome.method, outcome.holds


def test_f3r_a_transformation_of_part_of_the_learners_side_never_validates_the_step(tmp_path):
    from tests.workbench_help_fakes import CheckFake

    _needs_bwrap()

    def answer(_context):
        from tests.workbench_help_fakes import step_check

        return {"steps": [step_check(1, "questionable", reason="one side has an extra term",
                                     transformation=_transformation(kind="equivalence", expression="x+x",
                                                                    result="2*x"))],
                "first_questionable_step": 1, "error_kind_guess": "invalid_algebra",
                "error_kind_reason": "a slip", "error_readings": [], "assumptions": []}

    _paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, check=CheckFake([answer]))
    wb, _chains = open_problem(ctx, steps=("x + x = 2*x + 1",))
    [verdict] = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]["verdicts"]
    assert (verdict["verdict"], verdict["method"], verdict["mark"]) == ("questionable", "model", "?")


def test_f3r_the_whole_written_relation_is_what_is_checked():
    _needs_bwrap()
    equivalence = {"kind": "equivalence", "expression": "x+x", "result": "2*x"}
    assert _checks(["x + x = 2x"], equivalence) == ("checked", True)
    assert _checks(["$x + x = 2x$"], equivalence) == ("checked", True)
    # Words, another side, a chain, a continuation or a bare expression: not checked (fix round 3).
    assert _checks(["Combining like terms: $x + x = 2x$."], equivalence) == ("model", None)
    assert _checks(["x + x = 2*x + 1"], equivalence) == ("model", None)
    assert _checks(["y + x + x = 2x"], equivalence) == ("model", None)
    assert _checks(["x + x = 2x = 5"], equivalence) == ("model", None)
    assert _checks(["x + x", "= 2x"], equivalence) == ("model", None)
    assert _checks(["x + x", "2x"], equivalence) == ("model", None)
    # Declared to match what is written, a wrong constant relation does not hold.
    assert _checks(["x + x - 2x = 1"], {"kind": "equivalence", "expression": "x+x-2*x", "result": "1"}) == (
        "checked", False)


def test_f3r_an_operator_is_checked_on_its_written_operand_and_names_on_their_definitions():
    _needs_bwrap()
    derivative = {"kind": "differentiation", "expression": "x^3", "result": "3x^2", "variable": "x"}
    assert _checks([r"\frac{d}{dx}\left(x^3\right) = 3x^2"], derivative) == ("checked", True)
    assert _checks(["d/dx (x^3) = 3x^2"], derivative) == ("model", None)
    assert _checks([r"\frac{d}{dx}\left(x^3 + x\right) = 3x^2"], derivative) == ("model", None)
    # Fix round 6: a name is never resolved, even one the learner defined.
    assert _checks(["f(x) = x^3", "f'(x) = 3x^2"], derivative) == ("model", None)
    assert _checks(["f(x) = x^3 + x", "f'(x) = 3x^2"], derivative) == ("model", None)
    integral = {"kind": "integration", "expression": "2*x", "result": "x**2", "variable": "x"}
    # The problem's prose is not a definition: F is not defined by it.
    problem = "X has density f(x) = 2x on [0, 1]. Find P(X ≤ 1/2)."
    assert _checks(["F(x) = x^2 on [0, 1]"], integral, problem=problem) == ("model", None)
    assert _checks([r"\int 2x  dx = x^2"], integral) == ("checked", True)
    assert _checks([r"\int 2x + 1  dx = x^2"], integral) == ("model", None)
    normalization = {"kind": "normalization", "expression": "2*x", "result": "", "variable": "x", "lower": "0",
                     "upper": "1"}
    assert _checks([r"\int_0^1 2x  dx = 1"], normalization) == ("checked", True)
    assert _checks([r"\int_0^1 2x  dx = 2"], normalization) == ("model", None)
    solving = {"kind": "solving", "expression": "x^2 - 4 = 0", "result": "2", "variable": "x"}
    assert _checks(["x^2 - 4 = 0", "x = 2"], solving) == ("checked", True)
    assert _checks(["x^2 - 4 = 5", "x = 2"], solving) == ("model", None)
    assert _checks(["x^2 - 4 = 0", "x = 2 or x = -2"], solving) == ("model", None)


def test_f3r_a_hints_claim_about_part_of_a_side_is_the_models_reading():
    from learnloop.hints.workbench import HintClaim
    from learnloop.workbench.check import hint_claim_verifier

    _needs_bwrap()

    class _Config:
        class workbench:  # noqa: N801 - a config stand-in
            symbolic_checks_enabled = True

    class _Vault:
        config = _Config

    class _Context:
        steps = [_wb_step(1, "x + x = 2*x + 1")]

    verify = hint_claim_verifier(_Vault(), type("Item", (), {"prompt": ""})())
    words = HintClaim(step=1, statement="x + x is 2x", **_transformation(kind="equivalence", expression="x+x",
                                                                           result="2*x"))
    part = HintClaim(step=1, statement="x + x = 2*x + 1", **_transformation(kind="equivalence", expression="x+x",
                                                                              result="2*x"))
    assert [(outcome["method"], outcome["holds"]) for outcome in verify([words, part], _Context())] == [
        ("model", None), ("model", None)]


# -- F16: a hint's claims go through the level-aware leak checks --------------------------------


def test_f16_a_claim_that_states_the_answer_withholds_the_hint_and_is_never_stored(tmp_path):
    import json

    from tests.hint_fakes import WriterFake

    leaking = _claim(1, "The final answer is P(X ≤ 1/2) = 1/4.")
    writer = WriterFake([_with_claims(leaking), _with_claims(leaking)])
    paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx)
    hint = _take(ctx, wb, 3)
    assert writer.calls == 2
    assert hint.get("claims", []) == [] and "1/4" not in json.dumps(hint)
    assert "claim" in " ".join(writer.contexts[1]["previous_answer_problems"]["leaks"])
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert row["shown"] == 0
    assert "1/4" not in (row["contract_failures_json"] or "")


def test_f16_a_harmless_claim_is_kept_and_a_leaking_one_re_asks(tmp_path):
    from tests.hint_fakes import WriterFake

    writer = WriterFake([_with_claims(_claim(1, "The final answer is P(X ≤ 1/2) = 1/4.")),
                         _with_claims(_claim(1, "your step 1 stands as written"))])
    _paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx)
    hint = _take(ctx, wb, 3)
    assert hint["status"] == "ready" and writer.calls == 2
    assert [claim["statement"] for claim in hint["claims"]] == ["your step 1 stands as written"]
