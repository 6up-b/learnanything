"""What other test files use from ``tests/test_ro4_objective_serving.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from typing import Any

from tests.router_mixture_helpers import rows
from tests.router_model_fakes import options_in


def policy_answer(request: Any) -> dict[str, Any]:
    """A valid ``router_llm_choice_v3`` answer: every option positive, the first favoured."""

    fields = request.result_model.model_fields
    if "intervene_now" in fields:
        return {"intervene_now": 0.4, "rationale": "Finish this first.", "evidence_ids": []}
    refs = options_in(request.prompt)
    reference = request.prompt.split("- reference (not an option) [", 1)[1].split("]", 1)[0]
    return {
        "options": [{"id": ref, "probability": (0.6 if index == 0 else 0.4 / max(len(refs) - 1, 1)),
                     "p_cold_1": 0.7, "p_cold_7": 0.65 - 0.01 * index, "p_cold_30": 0.6}
                    for index, ref in enumerate(refs)],
        "reference": {"id": reference, "p_cold_1": 0.7, "p_cold_7": 0.6, "p_cold_30": 0.55},
        "rationale": "This keeps your recent work fresh.", "evidence_ids": [],
    }


def _shape(env) -> list[tuple]:
    out = []
    for row in rows(env):
        detail = row["detail_json"]
        out.append((row["policy"], row["chosen_ref"], row["propensity"], row["propensity_kind"],
                    tuple((c["ref"], c.get("propensity")) for c in row["candidates_json"]),
                    json.dumps(detail.get("mixture"), sort_keys=True, default=str)[:0]))
    return out


def _blocks(record) -> list[tuple]:
    return [(block.lane, tuple(item.practice_item_id for item in block.items)) for block in record.blocks]
