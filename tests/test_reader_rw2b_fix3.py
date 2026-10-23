"""Reader workbench RW2b + hints H3, fix round 3: "checked" comes only from the learner's own written step.

The orchestrator's ruling on the twice-reopened Codex F3
(``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 3"): the
symbolic check parses the learner's step from its LaTeX with sympy's ``lark``
backend and checks THAT relation; the model's declared transformation only
picks which check to try, and any disagreement between the declaration and
the parse leaves the step "model's reading". A name resolves only to a
definition an earlier step (or the problem's math) writes. A hint's claim is
checked only when its own statement parses and holds.

Each test drives the real sidecar and the real PF-b sandbox (skipped without
bubblewrap). The check model is a fake that marks the step questionable, so
any ``✓`` comes from the code's own check. No model is reached.
"""

from __future__ import annotations

import json

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.workbench_help_fakes import (FUNCTION_FREE_PROMPT, CheckFake, call, help_rows, open_problem,
                                       run_job, sidecar, step_check, wb_answer)

pytestmark = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def _transformation(**values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {**base, **values}


def _last_step_check(transformation, verdict="questionable"):
    """The fake check: every step unchecked but the last, which the model
    marks ``verdict`` and declares ``transformation`` for."""

    def answer(context):
        numbers = [entry["step"] for entry in context["steps"]]
        last = numbers[-1]
        rows = [step_check(number, "unchecked") for number in numbers[:-1]]
        rows.append(step_check(last, verdict, reason="the model's reading", transformation=transformation))
        return {"steps": rows, "first_questionable_step": last if verdict == "questionable" else 0,
                "error_kind_guess": "invalid_algebra" if verdict == "questionable" else "",
                "error_kind_reason": "", "error_readings": [], "assumptions": []}

    return answer


def _check_last(tmp_path, steps, transformation, verdict="questionable"):
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True,
                                   check=CheckFake([_last_step_check(transformation, verdict)]))
    wb, _chains = open_problem(ctx, steps=tuple(steps))
    view = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["check"]
    last = view["verdicts"][-1]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    return (last["verdict"], last["method"], last["mark"]), row


# -- The verify's five reproductions (Codex job 20261018-175123-prT5bb) --------------------------


def test_a_name_resolved_to_another_definition_is_never_checked(tmp_path):
    shown, row = _check_last(tmp_path, ["f(x)=x^3", "g(x)=x^2", "g'(x)=3*x^2"],
                             _transformation(kind="differentiation", expression="x^3", result="3*x^2", variable="x"))
    assert shown == ("questionable", "model", "?")
    recorded = json.loads(row["placement_json"])["symbolic"]
    assert [(entry["step"], entry["bound"], entry["holds"]) for entry in recorded] == [(3, False, None)]


def test_a_derivative_in_y_is_never_checked_as_one_in_x(tmp_path):
    declared = _transformation(kind="differentiation", expression="x^3", result="3*x^2", variable="x")
    assert _check_last(tmp_path / "a", ["d/dy (x^3) = 3*x^2"], declared)[0] == ("questionable", "model", "?")
    assert _check_last(tmp_path / "b", [r"\frac{d}{dy}\left(x^3\right) = 3x^2"], declared)[0] == (
        "questionable", "model", "?")


def test_an_integral_over_0_2_is_never_checked_over_0_1(tmp_path):
    declared = _transformation(kind="normalization", expression="2*x", result="1", variable="x", lower="0",
                               upper="1")
    assert _check_last(tmp_path / "a", [r"\int_0^2 2*x dx = 1"], declared)[0] == ("questionable", "model", "?")
    # Declared as written, the learner's own integral is checked: it is 4, not 1.
    as_written = _transformation(kind="integration", expression="2*x", result="1", variable="x", lower="0",
                                 upper="2")
    assert _check_last(tmp_path / "b", [r"\int_0^2 2*x dx = 1"], as_written, verdict="valid")[0] == (
        "questionable", "checked", "≠")


def test_a_limit_at_2_is_never_checked_at_1(tmp_path):
    declared = _transformation(kind="limit", expression="x^2", result="1", variable="x", value="1")
    # Unbracketed, the parse is ambiguous (the limit of x^2, or a limit squared).
    assert _check_last(tmp_path / "a", [r"\lim_{x \to 2} x^2 = 1"], declared)[0] == ("questionable", "model", "?")
    assert _check_last(tmp_path / "b", [r"\lim_{x \to 2} (x^2) = 1"], declared)[0] == (
        "questionable", "model", "?")
    at_two = _transformation(kind="limit", expression="x^2", result="1", variable="x", value="2")
    assert _check_last(tmp_path / "c", [r"\lim_{x \to 2} (x^2) = 1"], at_two, verdict="valid")[0] == (
        "questionable", "checked", "≠")


def test_grouping_is_kept_so_x_to_the_2_plus_1_is_not_x_squared_plus_1(tmp_path):
    declared = _transformation(kind="equivalence", expression="x^2+1", result="x^2+1")
    assert _check_last(tmp_path / "a", ["x^{2+1} = x^2+1"], declared)[0] == ("questionable", "model", "?")
    cubed = _transformation(kind="equivalence", expression="x**3", result="x**3")
    assert _check_last(tmp_path / "b", ["x^{2+1} = x^3"], cubed)[0] == ("valid", "checked", "✓")


# -- Positive controls: a correct step of each supported kind, from its LaTeX -------------------

POSITIVE = [
    ("equivalence", [r"\frac{2x + 2}{2} = x + 1"],
     dict(kind="equivalence", expression="(2*x + 2)/2", result="x + 1")),
    ("differentiation", [r"\frac{d}{dx}\left(\frac{x^2}{2}\right) = x"],
     dict(kind="differentiation", expression="x**2/2", result="x", variable="x")),
    ("definite integral", [r"\int_0^1 x  dx = \frac{1}{2}"],
     dict(kind="integration", expression="x", result="1/2", variable="x", lower="0", upper="1")),
    ("antiderivative", [r"\int x  dx = \frac{x^2}{2} + C"],
     dict(kind="integration", expression="x", result="x**2/2 + C", variable="x")),
    ("normalization", [r"\int_0^2 \frac{x}{2}  dx = 1"],
     dict(kind="normalization", expression="x/2", result="1", variable="x", lower="0", upper="2")),
    ("limit", [r"\lim_{x \to 1} \left(\frac{x}{2} + 1\right) = \frac{3}{2}"],
     dict(kind="limit", expression="x/2 + 1", result="3/2", variable="x", value="1")),
    ("sum", [r"\sum_{k=1}^{3} \frac{1}{k} = \frac{11}{6}"],
     dict(kind="sum", expression="1/k", result="11/6", variable="k", lower="1", upper="3")),
    # Fix round 6: a solve with no restriction token; substitution is never checked (names).
    ("solve", ["3x - 6 = 12", "x = 6"], dict(kind="solving", expression="3*x - 6 = 12", result="6", variable="x")),
]


@pytest.mark.parametrize("label,steps,declared", POSITIVE, ids=[case[0] for case in POSITIVE])
def test_a_correct_step_of_each_supported_kind_parsed_from_latex_is_checked(tmp_path, label, steps, declared):
    shown, row = _check_last(tmp_path, steps, _transformation(**declared))
    assert shown == ("valid", "checked", "✓"), (label, json.loads(row["placement_json"])["symbolic"])


# -- Names: a definition written earlier resolves; anything else does not -----------------------


def test_a_name_defined_in_an_earlier_step_is_not_resolved_either(tmp_path):
    # Fix round 6 (the orchestrator's ruling): names are never resolved.
    declared = _transformation(kind="differentiation", expression="x**3/3", result="x**2", variable="x")
    assert _check_last(tmp_path / "a", [r"f(x) = \frac{x^3}{3}", "f'(x) = x^2"], declared)[0] == (
        "questionable", "model", "?")
    substitution = _transformation(kind="substitution", expression="x**2/2", result="8", variable="x", value="4")
    assert _check_last(tmp_path / "b", [r"f(x) = \frac{x^2}{2}", r"f\left(4\right) = 8"], substitution)[0] == (
        "questionable", "model", "?")


def test_an_undefined_name_never_resolves(tmp_path):
    declared = _transformation(kind="differentiation", expression="x^3", result="3*x^2", variable="x")
    # g is never defined (f is): the step keeps the model's reading.
    assert _check_last(tmp_path / "a", ["f(x) = x^3", "g'(x) = 3x^2"], declared)[0] == (
        "questionable", "model", "?")
    assert _check_last(tmp_path / "b", ["h'(x) = 3x^2"], declared)[0] == ("questionable", "model", "?")


# -- The hint-claim path: a claim is checked only when its own statement parses and holds --------


def _claim(step, statement, **values):
    return {"step": step, "statement": statement, **_transformation(**values)}


def _hint_with(tmp_path, steps, *answers):
    writer = WriterFake([lambda context, claims=claims: {**wb_answer(context), "claims": list(claims)}
                         for claims in answers] + [wb_answer])
    paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True,
                                   writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=tuple(steps))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    return hint, writer, paths, wb, ctx


def test_a_hints_claim_about_the_wrong_integral_is_never_checked(tmp_path):
    # The verify's hint-path reproduction: the claim declares [0, 1] about a
    # step that integrates over [0, 2]; its statement is in words.
    claim = _claim(1, "your integral of the density is 1", kind="normalization", expression="2*x", result="1",
                   variable="x", lower="0", upper="1")
    hint, writer, paths, wb, ctx = _hint_with(tmp_path, [r"\int_0^2 2*x dx = 1"], [claim])
    assert hint["status"] == "ready" and writer.calls == 1
    assert [(entry["status"], entry["label"]) for entry in hint["claims"]] == [
        ("model", "model's reading, not checked")]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    # The persisted result (what help_state shows again) is the same verdict.
    stored = json.loads(row["contract_failures_json"])
    assert [entry["status"] for entry in stored["claims"]] == ["model"]
    assert [entry["status"] for entry in stored["rounds"][-1]["claims"]] == ["model"]
    restored = call(ctx, "workbench.help_state", {"sessionId": wb})["hints"][0]
    assert [entry["status"] for entry in restored["claims"]] == ["model"]


def test_a_hints_claim_whose_own_statement_is_the_wrong_integral_does_not_hold(tmp_path):
    wrong = _claim(1, r"\int_0^2 2x  dx = 1", kind="integration", expression="2*x", result="1", variable="x",
                   lower="0", upper="2")
    right = _claim(1, r"\int_0^2 2x  dx = 4", kind="integration", expression="2*x", result="4", variable="x",
                   lower="0", upper="2")
    hint, writer, *_rest = _hint_with(tmp_path, [r"\int_0^2 2*x dx = 1"], [wrong], [right])
    assert writer.calls == 2
    assert "wb_claim_failed:1" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert [entry["status"] for entry in hint["claims"]] == ["checked"]


def test_a_hints_claim_never_resolves_a_name(tmp_path):
    # Fix round 6: not even one the learner defined.
    defined = _claim(2, "f'(x) = 3x^2", kind="differentiation", expression="x**3", result="3*x**2", variable="x")
    hint, *_rest = _hint_with(tmp_path / "a", ["f(x) = x^3", "f'(x) = 3x^2"], [defined])
    assert [entry["status"] for entry in hint["claims"]] == ["model"]
    undefined = _claim(2, "g'(x) = 3x^2", kind="differentiation", expression="x**3", result="3*x**2", variable="x")
    hint, *_rest = _hint_with(tmp_path / "b", ["f(x) = x^3", "f'(x) = 3x^2"], [undefined])
    assert [entry["status"] for entry in hint["claims"]] == ["model"]
