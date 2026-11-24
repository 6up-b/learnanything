"""Size and group append requests using the reconciliation schema and configured ceilings."""

import json
from collections.abc import Callable
from functools import cache
from typing import TypeVar

from learnloop.content.synthesis.ai_contracts import AppendReconciliation, AppendReconciliationContext, append_reconciliation_prompt

T = TypeVar("T")


@cache
def _schema_chars() -> int:
    return len(json.dumps(AppendReconciliation.model_json_schema()))


def append_input_tokens(context: AppendReconciliationContext) -> int:
    return max(1, (len(append_reconciliation_prompt(context)) + _schema_chars()) // 4)


def append_groups(units: list[T], budgets, tokens: Callable[[list[T]], int]) -> list[list[T]]:
    ceiling = budgets.append_input_ceiling
    if len(units) < 2 or tokens(units) <= ceiling:
        return [units]
    room = ceiling - budgets.synthesis_span_request_max_count * budgets.synthesis_span_char_cap // 4
    groups = []
    current = []
    for unit in units:
        if current and tokens([*current, unit]) > room:
            groups.append(current)
            current = []
        current.append(unit)
    groups.append(current)
    return groups
