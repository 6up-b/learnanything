"""E1 grader probes (Slice 1 §13, added 2026-10-11).

* **Valid-alternative false rejection.** The generator writes a CORRECT
  derivation by a different method from the reference. A deterministic check
  of the SUBMITTED derivation (the text the grader sees) admits it only when
  the answer its concluding line ASSERTS (parsed from that line, never found
  as a token in it) is the declared final answer and equals the reference
  (exact normalized match, exact arithmetic, else SymPy equality), and EVERY
  relation in the derivation was checked and holds: an equation the checker
  cannot decide, or any other relation (``<``, ``\\neq``, ...), excludes the
  draft rather than being skipped. Prose steps are not machine-checkable; the
  spec accepts the exact key for them. The blind grader then grades it with
  the reference in context; a score below the maximum is a false rejection.
  Unverified alternatives are excluded from the denominator, never counted.
* **Real-vs-synthetic gap.** The generator writes an answer that is correct
  except for ONE planted error that changes the final answer. Its outcome is
  established independently of the generator's declaration: the answer its
  concluding line asserts must be the declared one and be decidably
  different from the reference (exact arithmetic, polynomial normal form or
  SymPy), so the answer cannot deserve full marks. Only that verified outcome
  is known; the declared criterion is kept as a label, never as ground truth.
  The blind grader's miss rate on these (full marks for a verified-wrong
  answer) is compared with its error rate on the owner's real answers where
  the owner adjudicated the grade.
* **Grade flip under paraphrase.** The generator rewords a real answer without
  changing its content; a pass/fail change between the two blind grades is a
  flip.

The relation checker (:func:`check_relations`) is deliberately narrow. It
tokenizes the whole text, takes every maximal run of math tokens that holds a
relation, and decides an equation chain only when each side parses as plain
arithmetic over numbers and single-letter symbols (``+ - * / ^``, brackets,
unary signs, implicit products such as ``2x``) into an exact polynomial normal
form. ``Let x = 1`` style definitions bind a symbol; constant sides are
compared exactly (to the stated precision for rounded decimals); identities
hold when the normal forms match. A chain next to a prose word that is not a
plain connective (``3 times 2 = 2``), a comma-joined tuple (``x, y = 2, 1``),
LaTeX, functions or a conditional equation is "unchecked".
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.attempts.grading import resolved_rubric
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.required_method import presented_prompt
from learnloop.attempts.answer_check import (  # moved to the attempts layer; re-exported
    RelationCheck,
    answers_differ as _answers_differ,
    answers_equal as _answers_equal,
    asserted_answer as _asserted_answer,
    asserted_conclusion,
    check_relations,
    final_answer_check,
    reference_answers,
    safe_math_text,
)

PROBE_PROMPT_VERSION = "grader-probes-v3"
PROBES = ("valid_alternative", "synthetic_error", "paraphrase")


class ValidAlternativeDraft(WireModel):
    method_note: str = Field(description="One sentence: how this method differs from the reference.")
    derivation_md: str
    final_answer: str = Field(description="The final answer alone, in the reference's notation.")


class SyntheticErrorDraft(WireModel):
    planted_criterion_id: str
    error_description: str
    answer_md: str
    final_answer: str = Field(
        default="",
        description="The (wrong) final answer the planted error leads to, alone, in the reference's notation.",
    )


class ParaphraseDraft(WireModel):
    answer_md: str


def _item_payload(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]:
    rubric = resolved_rubric(vault, item)
    expected = item.expected_answer
    return {
        "practice_item_id": item.id,
        # The question as presented (method-explicit-3 review F4).
        "prompt": presented_prompt(item.prompt, item.required_method),
        "reference_solution": expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True),
        "rubric": [{"id": criterion.id, "points": criterion.points, "description": criterion.description} for criterion in rubric.criteria],
    }


_CHECKABLE_STEPS = (
    "Write every equation in plain ASCII arithmetic (digits, + - * / ^, parentheses and "
    "single-letter variables), one equation chain per sentence, so that a checker can "
    "verify each step."
)


def valid_alternative_prompt(vault: LoadedVault, item: PracticeItem) -> str:
    return render_structured_prompt(
        "learnloop grader probe: valid alternative",
        PROBE_PROMPT_VERSION,
        {
            "task": (
                "Write a COMPLETE and CORRECT solution to this item by a method that "
                "genuinely differs from the reference solution (a different route, "
                "decomposition or representation), written as a strong learner would. "
                f"{_CHECKABLE_STEPS} It must reach the reference's final answer, and "
                "its LAST line must be `Final answer: <answer>` stating only that "
                "answer. Put the same answer alone in `final_answer`, in the "
                "reference's notation."
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
                "The error must change the final answer: the LAST line of `answer_md` "
                "must be `Final answer: <answer>` stating only that (wrong) final "
                "answer, and `final_answer` must hold the same answer alone, in the "
                "reference's notation. Name the criterion in `planted_criterion_id` "
                "(one of the rubric ids) and describe the error. Write it like real "
                "learner work, with no hint that an error was planted."
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
    return execute_structured_operation(client, purpose="diagnosis_valid_alternative", prompt=prompt, result_model=ValidAlternativeDraft, isolated=True)


def request_synthetic_error(client: OperationClient, prompt: str) -> SyntheticErrorDraft:
    return execute_structured_operation(client, purpose="diagnosis_synthetic_error", prompt=prompt, result_model=SyntheticErrorDraft, isolated=True)


def request_paraphrase(client: OperationClient, prompt: str) -> ParaphraseDraft:
    return execute_structured_operation(client, purpose="diagnosis_paraphrase", prompt=prompt, result_model=ParaphraseDraft, isolated=True)


def _expected_text(item: PracticeItem) -> str:
    return item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)


def verify_alternative(item: PracticeItem, draft: ValidAlternativeDraft) -> dict[str, Any]:
    """A deterministic check of the SUBMITTED derivation; never the model's word.

    ``verified`` needs all three: the concluding line asserts the declared
    final answer, that answer equals the reference, and every relation in
    the derivation was checked and holds (none false, none undecided).
    Anything else is excluded from E1's denominator.
    """

    asserted = _asserted_answer(draft.derivation_md, draft.final_answer)
    if asserted is None:
        return {
            "status": "unverified",
            "reason": "concluding_line_does_not_assert_the_final_answer",
            "asserted_answer": asserted_conclusion(draft.derivation_md),
        }
    # A worked-solution reference ("... Therefore P(E)=6/20=3/10.") is never
    # equal to a bare answer as a whole; its numeric conclusion is the check.
    equal, method = None, "symbolic_equality"
    for index, reference in enumerate(reference_answers(_expected_text(item))):
        equal, method = _answers_equal(asserted, reference)
        method = method if index == 0 else f"{method}+reference_conclusion"
        if equal is True:
            break
    if equal is not True:
        return {"status": "unverified", "method": method, "reason": "final_answer_not_shown_equal_to_reference", "asserted_answer": asserted}
    relations = check_relations(draft.derivation_md)
    if relations.false:
        return {"status": "unverified", "method": method, "reason": "false_equation", "false_equations": len(relations.false), "asserted_answer": asserted}
    if relations.unchecked:
        return {"status": "unverified", "method": method, "reason": "unchecked_relation", "unchecked_relations": len(relations.unchecked), "asserted_answer": asserted}
    return {
        "status": "verified",
        "method": f"{method}+asserted_conclusion+every_relation_checked",
        "asserted_answer": asserted,
        "relations_checked": relations.checked,
    }


def verify_synthetic_error(vault: LoadedVault, item: PracticeItem, draft: SyntheticErrorDraft) -> dict[str, Any]:
    """Establish a synthetic answer's outcome independently of its generator.

    ``verified_wrong`` means the answer's concluding line asserts the
    declared final answer and that answer is deterministically NOT the
    reference, so it cannot deserve full marks (``known_full_marks`` False).
    The declared criterion is recorded as a label only; how many points the
    planted error should cost is not known.
    """

    rubric = resolved_rubric(vault, item)
    points = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    maximum = float(rubric.max_points)
    if draft.planted_criterion_id not in points:
        return {"status": "invalid_criterion", "planted_criterion_id": draft.planted_criterion_id}
    declared = {
        "planted_criterion_id": draft.planted_criterion_id,
        "declared_known_score": max(0.0, maximum - points[draft.planted_criterion_id]),
    }
    asserted = _asserted_answer(draft.answer_md, draft.final_answer)
    if asserted is None:
        return {
            "status": "unverified",
            "reason": "concluding_line_does_not_assert_the_declared_answer",
            "asserted_answer": asserted_conclusion(draft.answer_md),
            **declared,
        }
    references = reference_answers(_expected_text(item))
    differ, method = _answers_differ(asserted, references[-1])
    if len(references) > 1:
        method = f"{method}+reference_conclusion"
    if differ is False:
        return {"status": "not_wrong", "method": method, "reason": "final_answer_equals_reference", "asserted_answer": asserted, **declared}
    if differ is None:
        return {"status": "unverified", "method": method, "reason": "final_answer_not_decidable", "asserted_answer": asserted, **declared}
    return {
        "status": "verified_wrong",
        "method": method,
        "known_full_marks": False,
        "max_points": maximum,
        "asserted_answer": asserted,
        **declared,
    }


def is_reference_bearing(item: PracticeItem) -> bool:
    expected = item.expected_answer
    text = expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True)
    return bool(text.strip())


__all__ = [
    "PROBES",
    "PROBE_PROMPT_VERSION",
    "ParaphraseDraft",
    "RelationCheck",
    "SyntheticErrorDraft",
    "ValidAlternativeDraft",
    "asserted_conclusion",
    "check_relations",
    "final_answer_check",
    "is_reference_bearing",
    "paraphrase_prompt",
    "request_paraphrase",
    "request_synthetic_error",
    "request_valid_alternative",
    "safe_math_text",
    "synthetic_error_prompt",
    "valid_alternative_prompt",
    "verify_alternative",
    "verify_synthetic_error",
]
