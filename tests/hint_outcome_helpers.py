"""What other test files use from ``tests/test_hint_outcome.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import threading
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION

from tests.structured_ai import StructuredClientFake, _request_context


REACHES_CDF = {"route_id": "r_ref", "reached_node_id": "cdf", "quote": "F(x) = x^2 on [0, 1]",
               "work_matches_a_route": True}


class OutcomeFake(StructuredClientFake):
    provider_name = "fake_outcome"
    provider_type = "codex_sdk"
    model = "fake-outcome-model"

    def __init__(self, answers: list[dict[str, Any]] | None = None, *, provider_type: str = "codex_sdk",
                 gate: threading.Event | None = None) -> None:
        self.answers = list(answers or [])
        self.provider_type = provider_type
        self.gate = gate
        self.contexts: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        self.contexts.append(json.loads(json.dumps(_request_context(request.prompt, request.purpose))))
        if self.gate is not None:
            assert self.gate.wait(30)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 40,
                           "resolved_model": self.model})
        answer = self.answers.pop(0) if self.answers else REACHES_CDF
        return request.result_model.model_validate(answer)

    @property
    def calls(self) -> int:
        return len(self.contexts)
