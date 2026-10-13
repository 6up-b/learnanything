"""Reference-key verification, extracted from PF-b (spec_source_practice_and_probes_v1 §7.3).

PF-b's run class used to own three verification steps as private methods: the
solver panel's independent solves, the equivalence judge's agreement with the
key confirmed by an LLM-written sympy check in the bubblewrap sandbox, and the
reference verifier's check that a quote-verified span supports the key. The
canonical-sources track checks imported textbook exercises' answer keys with
the same steps, so they live here, public, and the run class calls them.

**PF's decisions are preserved.** :func:`agreement` returns the combined
per-solve value PF decides on (``agree``: the LLM agreed AND, for a numeric
or symbolic answer, the sympy check confirmed it), with the same ledger rows in
the same order. It also reports what that combined value hides, which the
source-import ladder needs to label a key honestly:

* ``model_agree``: how many solves the LLM equivalence judge found to agree,
  whatever the symbolic check said;
* ``symbolic_status``: ``not_applicable`` (a prose answer), ``confirmed``,
  ``rejected`` (the check ran and the solves the judge accepted were not
  confirmed), ``degenerate_check``, ``no_check_written``, ``sandbox_error``
  (it failed or timed out) or ``sandbox_unavailable``;
* ``per_solve``: the LLM verdict, the symbolic verdict and the combined value.

``on_sandbox_unavailable="raise"`` (PF's) keeps today's behaviour: a missing
sandbox raises :class:`SandboxUnavailable` (and PF refuses up front anyway).
``"report"`` (the source-import ladder's) returns ``sandbox_unavailable``.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import hashlib
import json
import subprocess
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.content.authoring import pf_contracts as C
from learnloop.content.authoring.pf_sandbox import (
    SandboxLimits,
    SandboxUnavailable,
    equivalence_confirmations,
    run_equivalence_checks,
    sandbox_available,
)
from learnloop.ops.pf_calls import CallResult, PFCaller, RoleClient

#: Output-token bounds of the three verification roles (PF's own values).
PANEL_OUTPUT_TOKENS = 1500
EQUIVALENCE_OUTPUT_TOKENS = 2500
SPAN_SUPPORT_OUTPUT_TOKENS = 1200
SYMBOLIC_KINDS = frozenset({"numeric", "symbolic"})
SYMBOLIC_STATUSES = ("not_applicable", "confirmed", "rejected", "degenerate_check", "no_check_written",
                     "sandbox_error", "sandbox_unavailable")


def _sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


OnCall = Callable[[CallResult], None]


@dataclass
class VerifierEnv:
    """What the verification steps need: receipts and ledger, role clients, limits.

    ``role`` resolves a PF role (``panel``, ``equivalence``, ``span_support``)
    to its pinned clients; ``run`` is the sandbox's subprocess runner (tests
    inject one).
    """

    caller: PFCaller
    role: Callable[[str], list[RoleClient]]
    limits: SandboxLimits
    run: Callable[..., Any] = subprocess.run

    def call(self, entry: RoleClient, *, on_call: OnCall | None = None, **kwargs: Any) -> CallResult:
        call = self.caller.call(entry, **kwargs)
        if on_call is not None:
            on_call(call)
        return call


def panel_solves(env: VerifierEnv, stem: str, *, solves_per_model: int,
                 on_call: OnCall | None = None) -> list[dict[str, Any]]:
    """Each panel model solves ``stem`` ``solves_per_model`` times, never seeing a key."""

    solves = []
    for entry in env.role("panel"):
        for index in range(solves_per_model):
            call = env.call(
                entry, on_call=on_call, prompt=C.panel_solve_prompt(stem=stem, solve_index=index),
                prompt_version=C.PANEL_SOLVE_PROMPT, result_model=C.PanelSolve,
                output_tokens=PANEL_OUTPUT_TOKENS,
            )
            solves.append({"model": call.model, "index": index, "input_hash": call.input_hash,
                           "final_answer": call.result.final_answer,
                           "answer_kind": call.result.answer_kind})
    return solves


def equivalence(env: VerifierEnv, stem: str, reference: str, solves: Sequence[dict[str, Any]], *,
                on_call: OnCall | None = None) -> tuple[CallResult, Any]:
    entry = env.role("equivalence")[0]
    call = env.call(
        entry, on_call=on_call,
        prompt=C.equivalence_prompt(stem=stem, reference=reference,
                                    answers=[solve["final_answer"] for solve in solves]),
        prompt_version=C.EQUIVALENCE_PROMPT, result_model=C.EquivalenceResult,
        output_tokens=EQUIVALENCE_OUTPUT_TOKENS,
    )
    return call, call.result


def agreement(env: VerifierEnv, subject_kind: str, subject_id: str, input_hash: str, stem: str,
              reference: str, solves: Sequence[dict[str, Any]], *, on_call: OnCall | None = None,
              on_sandbox_unavailable: str = "raise") -> dict[str, Any]:
    """LLM agreement per solve, confirmed by the sandboxed sympy check where numeric/symbolic.

    The combined ``agree`` and every ledger row are exactly PF-b's; the
    separate model and symbolic results ride along (module docstring).
    """

    if on_sandbox_unavailable not in ("raise", "report"):
        raise ValueError("on_sandbox_unavailable must be 'raise' or 'report'")
    call, result = equivalence(env, stem, reference, solves, on_call=on_call)
    usable = len(result.agreements) == len(solves)
    symbolic = result.answer_kind in SYMBOLIC_KINDS
    confirmations: list[bool | None] = [None] * len(solves)
    normal_form = None
    degenerate = False
    sandbox_state = "not_run"
    if usable and symbolic and result.sympy_check:
        if on_sandbox_unavailable == "report" and not sandbox_available():
            sandbox_state = "unavailable"
        else:
            try:
                sandbox = run_equivalence_checks(
                    {"check": result.sympy_check},
                    [{"program": "check", "reference": reference, "answer": solve["final_answer"]}
                     for solve in solves],
                    normal_forms={"reference": reference}, limits=env.limits, run=env.run,
                )
            except SandboxUnavailable:
                if on_sandbox_unavailable == "raise":
                    raise
                sandbox_state = "unavailable"
            else:
                sandbox_state = "ran" if sandbox.ok else "error"
                if sandbox.ok:
                    normal_form = ((sandbox.output or {}).get("normal_forms") or {}).get("reference")
                # A degenerate check (it accepts a wrong answer) confirms nothing.
                confirmations, degenerate = equivalence_confirmations(sandbox, len(solves))
    agrees: list[bool] = []
    llm_agrees: list[bool] = []
    for index, solve in enumerate(solves):
        llm = bool(usable and result.agreements[index])
        confirmed = (not symbolic) or confirmations[index] is True
        agrees.append(llm and confirmed)
        llm_agrees.append(llm)
        env.caller.ledger(
            task="answer_equivalence", left_kind=subject_kind, left_id=subject_id,
            judge="llm", judge_model=call.model, prompt_version=C.EQUIVALENCE_PROMPT,
            input_hash=content_key([input_hash, solve["input_hash"], call.input_hash]),
            verdict=("agree" if llm else "disagree") if usable else "unusable",
            rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                       "answer_kind": result.answer_kind},
        )
        if symbolic:
            env.caller.ledger(
                task="answer_equivalence", left_kind=subject_kind, left_id=subject_id,
                judge="verifier", prompt_version="pf-equivalence-v1",
                input_hash=content_key([input_hash, solve["input_hash"], call.input_hash, "sympy"]),
                verdict=("degenerate_check" if degenerate else
                         {True: "agree", False: "disagree", None: "error"}[confirmations[index]]),
                rationale={"solve_model": solve["model"], "solve_index": solve["index"],
                           "program_hash": _sha(result.sympy_check or "")},
            )
    status = symbolic_status(symbolic=symbolic, usable=usable, check_written=bool(result.sympy_check),
                             sandbox_state=sandbox_state, degenerate=degenerate,
                             llm_agrees=llm_agrees, confirmations=confirmations)
    return {"agree": sum(agrees), "total": len(solves), "answer_kind": result.answer_kind,
            "usable": usable, "sympy_checked": symbolic, "normal_form": normal_form,
            "degenerate_check": degenerate,
            "verifier_model": call.model,
            "model_agree": sum(llm_agrees),
            "symbolic_status": status,
            "per_solve": [
                {"model": solve["model"], "agree": agree, "model_agree": llm, "symbolic": confirmation}
                for solve, agree, llm, confirmation in zip(solves, agrees, llm_agrees, confirmations)]}


def symbolic_status(*, symbolic: bool, usable: bool, check_written: bool, sandbox_state: str,
                    degenerate: bool, llm_agrees: Sequence[bool],
                    confirmations: Sequence[bool | None]) -> str:
    """What the symbolic check said, apart from the model's agreement."""

    if not symbolic:
        return "not_applicable"
    if not usable or not check_written:
        return "no_check_written"
    if sandbox_state == "unavailable":
        return "sandbox_unavailable"
    if degenerate:
        return "degenerate_check"
    if sandbox_state != "ran" or any(
            agreed and confirmation is None for agreed, confirmation in zip(llm_agrees, confirmations)):
        return "sandbox_error"
    agreed = [confirmation for agreed, confirmation in zip(llm_agrees, confirmations) if agreed]
    if agreed and all(confirmation is True for confirmation in agreed):
        return "confirmed"
    if any(confirmation is False for confirmation in agreed):
        return "rejected"
    # The judge accepted no solve, so there was nothing for the check to confirm.
    return "rejected" if any(confirmation is True for confirmation in confirmations) else "confirmed"


def span_support(env: VerifierEnv, *, subject_kind: str, subject_id: str, question: str,
                 cited_quote: str, reference_answer: str, explanation: str, item_kind: str,
                 on_call: OnCall | None = None) -> dict[str, Any]:
    """The reference verifier's independent check that a cited span supports the key."""

    entry = env.role("span_support")[0]
    call = env.call(
        entry, on_call=on_call, prompt=C.span_support_prompt(
            question=question, cited_span=cited_quote, reference_answer=reference_answer,
            explanation=explanation, item_kind=item_kind),
        prompt_version=C.SPAN_SUPPORT_PROMPT, result_model=C.SpanSupportVerdict,
        output_tokens=SPAN_SUPPORT_OUTPUT_TOKENS,
    )
    result = call.result
    executable = item_kind == "what_if" and result.executable_consequence
    supported = result.answer_supported and result.rationale_supported and not executable
    env.caller.ledger(
        task="reference_verified", left_kind=subject_kind, left_id=subject_id,
        judge="llm", judge_model=call.model, prompt_version=C.SPAN_SUPPORT_PROMPT,
        input_hash=call.input_hash, verdict="pass" if supported else "fail",
        rationale={"check": "span_supports_answer", "answer_supported": result.answer_supported,
                   "rationale_supported": result.rationale_supported,
                   "executable_consequence": result.executable_consequence,
                   "item_kind": item_kind},
    )
    return {"supported": supported, "answer_supported": result.answer_supported,
            "rationale_supported": result.rationale_supported,
            # An executable what-if needs the execution check, which is not
            # built: its reference stays unverified (§5.3).
            "execution_check_required": executable, "model": call.model,
            "span_answer": result.span_answer}


def verify_reference(env: VerifierEnv, *, stem: str, reference: str, subject_kind: str,
                     subject_id: str, input_hash: str, solves_per_model: int,
                     on_sandbox_unavailable: str = "raise",
                     on_call: OnCall | None = None) -> dict[str, Any]:
    """The panel-plus-sympy check of one key: solves, then agreement.

    Returns :func:`agreement`'s report plus the solves. The caller decides on
    it (PF on ``agree``; the source-import ladder on ``model_agree`` and
    ``symbolic_status``).
    """

    solves = panel_solves(env, stem, solves_per_model=solves_per_model, on_call=on_call)
    outcome = agreement(env, subject_kind, subject_id, input_hash, stem, reference, solves,
                        on_call=on_call, on_sandbox_unavailable=on_sandbox_unavailable)
    outcome["solves"] = [{"model": solve["model"], "index": solve["index"],
                          "final_answer": solve["final_answer"], "answer_kind": solve["answer_kind"]}
                         for solve in solves]
    return outcome


__all__ = [
    "SYMBOLIC_STATUSES",
    "VerifierEnv",
    "agreement",
    "equivalence",
    "panel_solves",
    "span_support",
    "symbolic_status",
    "verify_reference",
]
