"""What other test files use from ``tests/test_reader_digest_narrative.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.stores import reader_digests as RDG
from learnloop.reader import reader_sessions as RS

from tests.recap_fixtures import EXT, ask
from tests.structured_ai import StructuredClientFake
from tests.reader_followups_helpers import FakeSearch, _candidate, _plan, _seeded


QUESTION = "WHY_THREE_FACTORS_8812"


def payload_of(prompt: str) -> dict[str, Any]:
    return json.loads(prompt[prompt.index("{", prompt.index("prompt_version")):])


class NarrativeFake(StructuredClientFake):
    """``reader_digest``: cites the summary's first citable id unless told otherwise."""

    provider_name = "fake_digest"
    provider_type = "codex_sdk"
    model = "fake-digest-model"

    def __init__(self, *, text: str = "You worked one problem with the book open and asked why there are three "
                                      "factors.", cite: list[str] | None = None, fail: Exception | None = None,
                 provider_type: str = "codex_sdk") -> None:
        self.text = text
        self.cite = cite
        self.fail = fail
        self.provider_type = provider_type
        self.payloads: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        payload = payload_of(request.prompt)
        self.payloads.append(payload)
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        cited = self.cite if self.cite is not None else payload["citable_event_ids"][:1]
        return request.result_model.model_validate({"narrative": self.text, "cited_event_ids": cited})

    @property
    def calls(self) -> int:
        return len(self.payloads)


def _session_with_question(tmp_path, *, config: str | None = None):
    vault, repo, _session = _seeded(tmp_path, config=config)
    ask(vault, repo, QUESTION, 5)
    session = RS.sessions_for_source(repo, EXT)[0]
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    return vault, repo, row


def _row(repo, digest_id: str) -> dict[str, Any]:
    with repo.connection() as connection:
        return RDG.digest(connection, digest_id)
