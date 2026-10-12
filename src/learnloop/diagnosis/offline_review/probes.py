"""E1 grader probes (Slice 1 §13, added 2026-10-11).

* **Valid-alternative false rejection.** The generator writes a CORRECT
  derivation by a different method from the reference. A deterministic check
  of the SUBMITTED derivation (the text the grader sees) admits it only when
  its final answer equals the reference (exact normalized match, else SymPy
  equality), its concluding line states that answer, and every numeric
  equation in it holds. The blind grader then grades it with the reference in
  context; a score below the maximum is a false rejection. Unverified
  alternatives are excluded from the denominator, never counted.
* **Real-vs-synthetic gap.** The generator writes an answer that is correct
  except for ONE planted error that changes the final answer. Its outcome is
  established independently of the generator's declaration: the concluding
  line must state a final answer that SymPy (or exact numeric comparison)
  shows differs from the reference, so the answer cannot deserve full marks.
  Only that verified outcome is known; the declared criterion is kept as a
  label, never as ground truth. The blind grader's miss rate on these (full
  marks for a verified-wrong answer) is compared with its error rate on the
  owner's real answers where the owner adjudicated the grade.
* **Grade flip under paraphrase.** The generator rewords a real answer without
  changing its content; a pass/fail change between the two blind grades is a
  flip.
"""

from __future__ import annotations

import ast
import json
import re
from fractions import Fraction
from typing import Any

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.attempts.grading import resolved_rubric
from learnloop.diagnosis.causal_attribution import SympyVerifierAdapter
from learnloop.vault.models import LoadedVault, PracticeItem

PROBE_PROMPT_VERSION = "grader-probes-v2"
PROBES = ("valid_alternative", "synthetic_error", "paraphrase")
_WS = re.compile(r"\s+")
#: Model text reaches SymPy (whose parser evaluates Python) only inside this
#: alphabet: digits, operators, brackets, single-letter symbols and a short
#: list of math function names. Anything else is "unverifiable", never parsed.
_SAFE_MATH = re.compile(r"^[0-9A-Za-z_+\-*/^().,\s]+$")
_SAFE_NAMES = frozenset(
    {"sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "ln", "pi", "oo", "Abs"}
)
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
#: A numeric equation chain: two or more sides of digits and operators.
_NUMERIC_SIDE = r"[0-9][0-9+\-*/^(). ]*"
_EQUATION = re.compile(rf"(?<![\w.^]){_NUMERIC_SIDE}(?:\s*=\s*-?\s*{_NUMERIC_SIDE})+")


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
                "It must reach the reference's final answer, and its LAST line must "
                "state that final answer. Put the final answer alone in "
                "`final_answer`, in the reference's notation."
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
                "The error must change the final answer: end `answer_md` with a line "
                "stating that (wrong) final answer and put it alone in `final_answer`, "
                "in the reference's notation. Name the criterion in "
                "`planted_criterion_id` (one of the rubric ids) and describe the error. "
                "Write it like real learner work, with no hint that an error was planted."
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


def _normalized(value: str) -> str:
    return _WS.sub(" ", value.strip().strip("$").strip()).casefold()


def safe_math_text(text: str) -> bool:
    """Whether ``text`` may be handed to SymPy (its parser evaluates Python)."""

    if not text or not _SAFE_MATH.match(text) or "__" in text:
        return False
    return all(len(name) == 1 or name in _SAFE_NAMES for name in _NAME.findall(text))


def _symbolic_equal(observed: str, expected: str) -> bool | None:
    """True/False when SymPy can decide equality on safe text, else None."""

    left, right = observed.strip().strip("$").strip(), expected.strip().strip("$").strip()
    if not (safe_math_text(left) and safe_math_text(right)):
        return None
    result = SympyVerifierAdapter().verify(left, right)
    if result.status == "verified":
        return True
    if result.status == "contradicted":
        return False
    return None


def _evaluate(side: str) -> Fraction | None:
    """Exact value of a numeric side (digits, + - * / ^, brackets), else None."""

    try:
        tree = ast.parse(side.replace("^", "**").strip(), mode="eval")
    except SyntaxError:
        return None

    def value(node: ast.AST) -> Fraction:
        if isinstance(node, ast.Expression):
            return value(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Fraction(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand = value(node.operand)
            return operand if isinstance(node.op, ast.UAdd) else -operand
        if isinstance(node, ast.BinOp):
            left, right = value(node.left), value(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow) and right.denominator == 1 and abs(right) <= 64:
                return left ** int(right)
        raise ValueError("not a plain numeric expression")

    try:
        return value(tree)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def _decimals(text: str) -> int:
    return max((len(part) for part in re.findall(r"\.(\d+)", text)), default=0)


def false_numeric_equations(text: str) -> list[str]:
    """Numeric equation chains in ``text`` (e.g. ``1+1=99``) that do not hold.

    Only sides made of digits and arithmetic are checked; a side with a
    rounded decimal is compared to its stated precision. Anything symbolic or
    unparseable is skipped, never guessed.
    """

    cleaned = text.replace("$", " ").replace("\\(", " ").replace("\\)", " ")
    false: list[str] = []
    for match in _EQUATION.finditer(cleaned):
        chain = match.group(0)
        sides = [side.strip() for side in chain.split("=")]
        values = [_evaluate(side) for side in sides]
        for (left_text, left), (right_text, right) in zip(zip(sides, values), list(zip(sides, values))[1:]):
            if left is None or right is None:
                continue
            places = max(_decimals(left_text), _decimals(right_text))
            tolerance = Fraction(1, 10 ** places) if places else Fraction(0)
            if abs(left - right) > tolerance:
                false.append(chain.strip())
                break
    return false


def concluding_line_states(text: str, answer: str) -> bool:
    """Whether the last non-empty line of ``text`` states ``answer`` as a token."""

    lines = [line for line in (text or "").splitlines() if line.strip()]
    wanted = _normalized(answer)
    if not lines or not wanted:
        return False
    last = _normalized(lines[-1].replace("$", " "))
    pattern = rf"(?<![0-9a-z.\-]){re.escape(wanted)}(?![0-9a-z^/*]|\.\d)"
    return re.search(pattern, last) is not None


def _matches_reference(answer: str, expected: str) -> tuple[bool | None, str]:
    if _normalized(answer) == _normalized(expected):
        return True, "exact_match"
    return _symbolic_equal(answer, expected), "symbolic_equality"


def _expected_text(item: PracticeItem) -> str:
    return item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)


def verify_alternative(item: PracticeItem, draft: ValidAlternativeDraft) -> dict[str, Any]:
    """A deterministic check of the SUBMITTED derivation; never the model's word.

    ``verified`` needs all three: the final answer equals the reference, the
    derivation's last line states that answer, and no numeric equation in the
    derivation is false. Anything else is excluded from E1's denominator.
    """

    equal, method = _matches_reference(draft.final_answer, _expected_text(item))
    if equal is not True:
        return {"status": "unverified", "method": method, "reason": "final_answer_not_shown_equal_to_reference"}
    if not concluding_line_states(draft.derivation_md, draft.final_answer):
        return {"status": "unverified", "method": method, "reason": "derivation_does_not_conclude_with_the_final_answer"}
    false = false_numeric_equations(draft.derivation_md)
    if false:
        return {"status": "unverified", "method": method, "reason": "false_numeric_equation", "false_equations": len(false)}
    return {"status": "verified", "method": f"{method}+derivation_concludes+numeric_equations_hold"}


def verify_synthetic_error(vault: LoadedVault, item: PracticeItem, draft: SyntheticErrorDraft) -> dict[str, Any]:
    """Establish a synthetic answer's outcome independently of its generator.

    ``verified_wrong`` means the answer's last line states a final answer that
    is deterministically NOT the reference, so it cannot deserve full marks
    (``known_full_marks`` False). The declared criterion is recorded as a label
    only; how many points the planted error should cost is not known.
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
    if not concluding_line_states(draft.answer_md, draft.final_answer):
        return {"status": "unverified", "reason": "answer_does_not_conclude_with_the_final_answer", **declared}
    equal, method = _matches_reference(draft.final_answer, _expected_text(item))
    if equal is True:
        return {"status": "not_wrong", "method": method, "reason": "final_answer_equals_reference", **declared}
    if equal is None:
        return {"status": "unverified", "method": method, "reason": "final_answer_not_decidable", **declared}
    return {"status": "verified_wrong", "method": method, "known_full_marks": False, "max_points": maximum, **declared}


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
    "concluding_line_states",
    "false_numeric_equations",
    "safe_math_text",
    "synthetic_error_prompt",
    "valid_alternative_prompt",
    "verify_alternative",
    "verify_synthetic_error",
]
