"""E1 grader probes (Slice 1 §13, added 2026-10-11).

* **Valid-alternative false rejection.** The generator writes a CORRECT
  derivation by a different method from the reference; a deterministic check
  (SymPy equality, else exact normalized match) confirms its final answer. The
  blind grader then grades it with the reference in context; a score below the
  maximum is a false rejection. Unverified alternatives are excluded, never
  counted.
* **Real-vs-synthetic gap.** The generator writes an answer that is correct
  except for ONE planted error confined to one named criterion, so its grade is
  known by construction. The blind grader's error on these is compared with
  its error on the owner's real answers where the owner adjudicated the grade.
* **Grade flip under paraphrase.** The generator rewords a real answer without
  changing its content; a pass/fail change between the two blind grades is a
  flip.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.attempts.grading import resolved_rubric
from learnloop.diagnosis.causal_attribution import SympyVerifierAdapter
from learnloop.vault.models import LoadedVault, PracticeItem

PROBE_PROMPT_VERSION = "grader-probes-v1"
PROBES = ("valid_alternative", "synthetic_error", "paraphrase")
_WS = re.compile(r"\s+")


class ValidAlternativeDraft(WireModel):
    method_note: str = Field(description="One sentence: how this method differs from the reference.")
    derivation_md: str
    final_answer: str = Field(description="The final answer alone, in the reference's notation.")


class SyntheticErrorDraft(WireModel):
    planted_criterion_id: str
    error_description: str
    answer_md: str


class ParaphraseDraft(WireModel):
    answer_md: str


def _item_payload(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]:
    rubric = resolved_rubric(vault, item)
    expected = item.expected_answer
    return {
        "practice_item_id": item.id,
        "prompt": item.prompt,
        "reference_solution": expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True),
        "rubric": [{"id": criterion.id, "points": criterion.points, "description": criterion.description} for criterion in rubric.criteria],
    }


def valid_alternative_prompt(vault: LoadedVault, item: PracticeItem) -> str:
    return render_structured_prompt(
        "learnloop grader probe: valid alternative",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Write a COMPLETE and CORRECT solution to this item by a method that "
                "genuinely differs from the reference solution (a different route, "
                "decomposition or representation), written as a strong learner would. "
                "It must reach the reference's final answer. Put the final answer "
                "alone in `final_answer`, in the reference's notation."
            ),
            "context": _item_payload(vault, item),
        },
    )


def synthetic_error_prompt(vault: LoadedVault, item: PracticeItem) -> str:
    return render_structured_prompt(
        "learnloop grader probe: synthetic planted error",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Write a learner answer that is fully correct EXCEPT for exactly one "
                "error that loses all of ONE rubric criterion's points and nothing else. "
                "Name that criterion in `planted_criterion_id` (one of the rubric ids) "
                "and describe the error. Write it like real learner work, with no hint "
                "that an error was planted."
            ),
            "context": _item_payload(vault, item),
        },
    )


def paraphrase_prompt(vault: LoadedVault, item: PracticeItem, answer: str) -> str:
    return render_structured_prompt(
        "learnloop grader probe: paraphrase",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Reword this learner answer without changing its content: keep every "
                "step, claim, error and the final answer exactly as they are, change "
                "only wording, ordering of sentences where harmless, and formatting. "
                "Do not fix or add anything."
            ),
            "context": {**_item_payload(vault, item), "learner_answer_md": answer},
        },
    )


def request_valid_alternative(client: OperationClient, prompt: str) -> ValidAlternativeDraft:
    return execute_structured_operation(client, purpose="diagnosis_valid_alternative", prompt=prompt, result_model=ValidAlternativeDraft)


def request_synthetic_error(client: OperationClient, prompt: str) -> SyntheticErrorDraft:
    return execute_structured_operation(client, purpose="diagnosis_synthetic_error", prompt=prompt, result_model=SyntheticErrorDraft)


def request_paraphrase(client: OperationClient, prompt: str) -> ParaphraseDraft:
    return execute_structured_operation(client, purpose="diagnosis_paraphrase", prompt=prompt, result_model=ParaphraseDraft)


def _normalized(value: str) -> str:
    return _WS.sub(" ", value.strip().strip("$").strip()).casefold()


def verify_alternative(item: PracticeItem, draft: ValidAlternativeDraft) -> dict[str, Any]:
    """A deterministic check of the alternative's final answer; never the model's word."""

    expected = item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)
    if _normalized(draft.final_answer) == _normalized(expected):
        return {"status": "verified", "method": "exact_match"}
    result = SympyVerifierAdapter().verify(draft.final_answer, expected)
    if result.status == "verified":
        return {"status": "verified", "method": "symbolic_equality"}
    return {"status": "unverified", "method": "symbolic_equality", "verifier_status": result.status}


def synthetic_known_score(vault: LoadedVault, item: PracticeItem, draft: SyntheticErrorDraft) -> tuple[float, float] | None:
    rubric = resolved_rubric(vault, item)
    points = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    if draft.planted_criterion_id not in points:
        return None
    maximum = float(rubric.max_points)
    return max(0.0, maximum - points[draft.planted_criterion_id]), maximum


def is_reference_bearing(item: PracticeItem) -> bool:
    expected = item.expected_answer
    text = expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True)
    return bool(text.strip())


__all__ = [
    "PROBES",
    "PROBE_PROMPT_VERSION",
    "ParaphraseDraft",
    "SyntheticErrorDraft",
    "ValidAlternativeDraft",
    "is_reference_bearing",
    "paraphrase_prompt",
    "request_paraphrase",
    "request_synthetic_error",
    "request_valid_alternative",
    "synthetic_error_prompt",
    "synthetic_known_score",
    "valid_alternative_prompt",
    "verify_alternative",
]
