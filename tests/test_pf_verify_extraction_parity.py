"""S1 (G6): extracting PF-b's verification to ops.pf_verify changes none of PF's decisions."""
from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from learnloop.ai.execution import content_key
from learnloop.content.authoring import pf_contracts as C
from learnloop.content.authoring import pf_sandbox
from learnloop.content.authoring.pf_sandbox import (
    SandboxLimits, SandboxUnavailable, equivalence_confirmations, run_equivalence_checks,
)
from learnloop.ops import pf_verify
from learnloop.ops.pf_calls import CallResult, RoleClient
from tests.pf_fakes import ALWAYS_TRUE_CHECK, PFFake

needs_bwrap = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="bubblewrap is not installed")
BROKEN_CHECK = "def check(reference, answer)\n    return True\n"


class _StubCaller:
    """Records ledger appends in memory; answers calls from a PF fake."""

    def __init__(self) -> None:
        self.ledgered: list[dict[str, Any]] = []

    def call(self, entry: RoleClient, *, prompt: str, prompt_version: str, result_model,
             output_tokens: int | None = None, **_kwargs: Any) -> CallResult:
        # None: the role's policy budget (main's retired per-role caps).
        from learnloop.ai.transport import StructuredRequest

        result = entry.client.complete(StructuredRequest(purpose="pf", prompt=prompt, result_model=result_model))
        return CallResult(result, entry.model or "fake", content_key([prompt, prompt_version]), prompt_version,
                          False, {})

    def ledger(self, **kwargs: Any) -> str:
        self.ledgered.append(kwargs)
        return f"id{len(self.ledgered)}"


def _sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _old_agreement(caller, role, limits, subject_kind, subject_id, input_hash, stem, reference, solves):
    """PF-b's ``_FamilyRun._agreement`` as it was before the extraction (verbatim logic)."""
    entry = role("equivalence")[0]
    call = caller.call(entry, prompt=C.equivalence_prompt(stem=stem, reference=reference,
                                                          answers=[solve["final_answer"] for solve in solves]),
                       prompt_version=C.EQUIVALENCE_PROMPT, result_model=C.EquivalenceResult, output_tokens=2500)
    result = call.result
    usable = len(result.agreements) == len(solves)
    symbolic = result.answer_kind in {"numeric", "symbolic"}
    confirmations = [None] * len(solves)
    normal_form = None
    degenerate = False
    if usable and symbolic and result.sympy_check:
        sandbox = run_equivalence_checks(
            {"check": result.sympy_check},
            [{"program": "check", "reference": reference, "answer": solve["final_answer"]} for solve in solves],
            normal_forms={"reference": reference}, limits=limits,
        )
        if sandbox.ok:
            normal_form = ((sandbox.output or {}).get("normal_forms") or {}).get("reference")
        confirmations, degenerate = equivalence_confirmations(sandbox, len(solves))
    agrees = []
    for index, solve in enumerate(solves):
        llm = bool(usable and result.agreements[index])
        confirmed = (not symbolic) or confirmations[index] is True
        agrees.append(llm and confirmed)
        caller.ledger(
            task="answer_equivalence", left_kind=subject_kind, left_id=subject_id,
            judge="llm", judge_model=call.model, prompt_version=C.EQUIVALENCE_PROMPT,
            input_hash=content_key([input_hash, solve["input_hash"], call.input_hash]),
            verdict=("agree" if llm else "disagree") if usable else "unusable",
            rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                       "answer_kind": result.answer_kind},
        )
        if symbolic:
            caller.ledger(
                task="answer_equivalence", left_kind=subject_kind, left_id=subject_id,
                judge="verifier", prompt_version="pf-equivalence-v1",
                input_hash=content_key([input_hash, solve["input_hash"], call.input_hash, "sympy"]),
                verdict=("degenerate_check" if degenerate else
                         {True: "agree", False: "disagree", None: "error"}[confirmations[index]]),
                rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                           "program_hash": _sha(result.sympy_check or "")},
            )
    return {"agree": sum(agrees), "total": len(solves), "answer_kind": result.answer_kind,
            "usable": usable, "sympy_checked": symbolic, "normal_form": normal_form,
            "degenerate_check": degenerate, "verifier_model": call.model,
            "per_solve": [{"model": solve["model"], "agree": agree} for solve, agree in zip(solves, agrees)]}


def _role(fake):
    entry = RoleClient(role="equivalence", provider="fake", model="fake-model", profile_type=None,
                       subscription=True, client=fake)
    return lambda name: [entry]


def _solves(answers):
    return [{"model": "m", "index": index, "input_hash": f"h{index}", "final_answer": answer,
             "answer_kind": "numeric"} for index, answer in enumerate(answers)]


@pytest.mark.parametrize("check,answers,reference", [
    pytest.param(None, ["5", "5", "4"], "5", id="sympy-confirmed"),
    pytest.param(BROKEN_CHECK, ["5", "5", "5"], "5", id="sympy-run-fails"),
    pytest.param(ALWAYS_TRUE_CHECK, ["5", "6", "5"], "5", id="degenerate"),
    pytest.param(None, ["the focus", "the focus", "a line"], "the focus", id="prose"),
])
@needs_bwrap
def test_combined_agreement_and_ledger_rows_are_pf_s(check, answers, reference):
    fake = PFFake(sympy_check=check)
    limits = SandboxLimits()
    old_caller, new_caller = _StubCaller(), _StubCaller()
    old = _old_agreement(old_caller, _role(fake), limits, "pf_candidate", "pfc_1", "ih", "stem", reference,
                         _solves(answers))
    env = pf_verify.VerifierEnv(caller=new_caller, role=_role(fake), limits=limits)
    new = pf_verify.agreement(env, "pf_candidate", "pfc_1", "ih", "stem", reference, _solves(answers))
    assert {key: new[key] for key in old if key != "per_solve"} == {key: old[key] for key in old if key != "per_solve"}
    assert [{"model": row["model"], "agree": row["agree"]} for row in new["per_solve"]] == old["per_solve"]
    assert new_caller.ledgered == old_caller.ledgered


@needs_bwrap
def test_a_failed_sympy_run_is_disagreement_for_pf_but_reported_apart():
    fake = PFFake(sympy_check=BROKEN_CHECK)
    env = pf_verify.VerifierEnv(caller=_StubCaller(), role=_role(fake), limits=SandboxLimits())
    outcome = pf_verify.agreement(env, "pf_candidate", "pfc_1", "ih", "stem", "5", _solves(["5", "5", "5"]))
    assert outcome["agree"] == 0  # PF's combined value: unconfirmed counts as disagreement
    assert outcome["model_agree"] == 3 and outcome["symbolic_status"] == "sandbox_error"


def test_pf_still_raises_without_a_sandbox_and_the_ladder_reports(monkeypatch):
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    fake = PFFake()
    env = pf_verify.VerifierEnv(caller=_StubCaller(), role=_role(fake), limits=SandboxLimits())
    with pytest.raises(SandboxUnavailable):
        pf_verify.agreement(env, "pf_candidate", "pfc_1", "ih", "stem", "5", _solves(["5", "5"]))
    reported = pf_verify.agreement(env, "pf_candidate", "pfc_1", "ih", "stem", "5", _solves(["5", "5"]),
                                   on_sandbox_unavailable="report")
    assert reported["symbolic_status"] == "sandbox_unavailable" and reported["agree"] == 0


def test_the_pf_run_keeps_its_report_shape():
    from learnloop.ops.pf_generation import PF_AGREEMENT_KEYS

    assert set(PF_AGREEMENT_KEYS) == {"agree", "total", "answer_kind", "usable", "sympy_checked", "normal_form",
                                      "degenerate_check", "verifier_model"}


@pytest.mark.parametrize("symbolic,usable,written,state,degenerate,llm,conf,expected", [
    (False, True, False, "not_run", False, [True], [None], "not_applicable"),
    (True, True, False, "not_run", False, [True], [None], "no_check_written"),
    (True, False, True, "not_run", False, [], [], "no_check_written"),
    (True, True, True, "unavailable", False, [True], [None], "sandbox_unavailable"),
    (True, True, True, "ran", True, [True], [False], "degenerate_check"),
    (True, True, True, "error", False, [True], [None], "sandbox_error"),
    (True, True, True, "ran", False, [True, True], [True, True], "confirmed"),
    (True, True, True, "ran", False, [True, True], [True, False], "rejected"),
])
def test_symbolic_status_table(symbolic, usable, written, state, degenerate, llm, conf, expected):
    assert pf_verify.symbolic_status(symbolic=symbolic, usable=usable, check_written=written, sandbox_state=state,
                                     degenerate=degenerate, llm_agrees=llm, confirmations=conf) == expected
