"""The escalated repair (Slice 2 §3.7): a DIFFERENT operator and representation.

When a recurrence group reaches K, the card shows a repair that differs from
the ones shown for the group's earlier answers. The diagnosis's own repairs
come first: one whose operator was never shown before is used as is. When
none differs (the diagnoser suggested the same kind of repair again), the
escalation asks the diagnosis route ONCE for a repair of the same cause
through a different operator and representation, given the operators,
practice modes and questions already shown. The answer is used only when its
operator is new; otherwise, or when the request fails, is refused by the
spend caps or is switched off (``recurrence.escalation_repair_enabled``), the
card keeps the honest label: the repair is the same kind as before. Nothing
is requested while the card itself is off (``escalation_card_enabled``):
nobody would see the repair.

The request is admitted on the enclosing command's budget when there is one
(and only while the command's remaining diagnoses still fit), else on a
one-call per-job budget; it is receipted under the attempt.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import Field, model_validator

from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.recurrence.judging import Reserve, admit_beside, estimate_tokens, model_label

LOG = logging.getLogger(__name__)

ESCALATION_REPAIR_PROMPT_VERSION = "escalated-repair-v1"
ESCALATION_REPAIR_PURPOSE = "recurrence_escalation_repair"
#: The spend route the request is admitted on (the diagnosis route's client).
ESCALATION_REPAIR_ROUTE = "escalation_repair"
#: One request per escalation, per job, when no command budget applies.
ESCALATION_REPAIR_CAPS = SpendCaps(
    max_candidates=1,
    max_pairs=0,
    max_retries=2,
    max_calls=1,
    max_total_tokens=60_000,
    max_estimated_usd=0.25,
)
#: Upper bound of one request's prompt, for dry-run estimates.
ESCALATION_REPAIR_PROMPT_TOKENS = 3_000


class EscalatedRepair(WireModel):
    """One repair of the same cause, through a different operator and representation."""

    operator: str = Field(pattern=r"^[a-z][a-z0-9_]*$", description="A snake_case operator NOT used before.")
    representation: str = Field(
        description="The representation it works in (e.g. worked contrast, counterexample, diagram, concrete case)."
    )
    practice_mode: str
    rationale: str = Field(description="Why this approach should reach the cause where the earlier ones did not.")
    eliciting_question: str | None = None
    expected_response_contract: str | None = None
    answer_reveal_budget: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _eliciting_needs_a_question(self) -> "EscalatedRepair":
        if self.operator.startswith("elicit_") and not (self.eliciting_question or "").strip():
            raise ValueError("an elicit_* operator requires an eliciting_question")
        return self


def repair_key(repair: Mapping[str, Any]) -> str | None:
    operator = str(repair.get("operator") or "").strip()
    if operator:
        return operator
    mode = str(repair.get("practice_mode") or "").strip()
    return f"mode:{mode}" if mode else None


def _shown(repair: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: repair.get(key)
        for key in ("operator", "practice_mode", "eliciting_question", "rationale")
        if repair.get(key)
    }


def escalation_repair_prompt(
    *, cause: str, learning_object: str | None, count: int,
    earlier_repairs: Sequence[Mapping[str, Any]], current_repairs: Sequence[Mapping[str, Any]],
) -> str:
    return render_structured_prompt(
        "learnloop escalated repair",
        ESCALATION_REPAIR_PROMPT_VERSION,
        {
            "task": (
                f"This learner has now answered wrongly {count} times with the same underlying cause. "
                "The repairs in `earlier_repairs` were shown for the earlier answers and the diagnosis of "
                "this answer suggested `current_repairs` again: the same kind of help has not stuck. Write "
                "ONE repair that targets the same cause through a DIFFERENT operator (one not listed in either "
                "list) and a DIFFERENT representation (for example a worked contrast between the wrong and the "
                "right reasoning, a counterexample the learner checks, a diagram or concrete case, or explaining "
                "the rule back in their own words). Keep it answerable by the learner unaided and keep the "
                "answer reveal near zero; when the operator begins with elicit_, give one eliciting_question."
            ),
            "context": {
                "cause": cause,
                "learning_object": learning_object,
                "earlier_repairs": [_shown(repair) for repair in earlier_repairs],
                "current_repairs": [_shown(repair) for repair in current_repairs],
            },
        },
    )


def request_different_repair(
    *,
    client: Any,
    cause: str,
    learning_object: str | None,
    count: int,
    earlier_repairs: Sequence[Mapping[str, Any]],
    current_repairs: Sequence[Mapping[str, Any]],
    spend: ReviewSpend,
    reserve: Reserve | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """(the repair, what happened). The repair is None unless its operator is new."""

    used = {key for key in (repair_key(row) for row in [*earlier_repairs, *current_repairs]) if key}
    prompt = escalation_repair_prompt(
        cause=cause, learning_object=learning_object, count=count,
        earlier_repairs=earlier_repairs, current_repairs=current_repairs,
    )
    info: dict[str, Any] = {
        "requested": True,
        "prompt_version": ESCALATION_REPAIR_PROMPT_VERSION,
        "model": model_label(client),
        "operators_already_used": sorted(used),
    }
    # Billed as the client actually built (a plan classified it from config).
    spend.register(ESCALATION_REPAIR_ROUTE, client)
    tokens = estimate_tokens(prompt)
    try:
        admit_beside(spend, ESCALATION_REPAIR_ROUTE, input_tokens=tokens, reserve=reserve)
        with spend.collector.observing():
            with spend.request(ESCALATION_REPAIR_ROUTE, ESCALATION_REPAIR_PURPOSE, input_tokens=tokens):
                result = execute_structured_operation(
                    client, purpose=ESCALATION_REPAIR_PURPOSE, prompt=prompt, result_model=EscalatedRepair,
                    isolated=True,
                )
    except Exception as exc:  # noqa: BLE001 - the card falls back to the honest label
        LOG.warning("escalated-repair request failed (%s)", type(exc).__name__, exc_info=True)
        return None, {**info, "status": "failed", "error": type(exc).__name__}
    repair = EscalatedRepair.model_validate(result).model_dump(mode="json")
    if repair["operator"] in used:
        return None, {**info, "status": "same_operator", "operator": repair["operator"]}
    repair["generated"] = True
    return repair, {**info, "status": "used", "operator": repair["operator"]}


def per_job_spend(cancelled: Callable[[], bool] | None = None, config: Any | None = None) -> ReviewSpend:
    # ``config``: the vault's output-budget policy (None: its code default).
    return ReviewSpend(ESCALATION_REPAIR_CAPS, cancelled=cancelled, config=config)


__all__ = [
    "ESCALATION_REPAIR_CAPS",
    "ESCALATION_REPAIR_PROMPT_TOKENS",
    "ESCALATION_REPAIR_PROMPT_VERSION",
    "ESCALATION_REPAIR_PURPOSE",
    "ESCALATION_REPAIR_ROUTE",
    "EscalatedRepair",
    "escalation_repair_prompt",
    "per_job_spend",
    "repair_key",
    "request_different_repair",
]
