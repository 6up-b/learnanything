"""What other test files use from ``tests/test_reader_passage_check.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import threading

from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.clock import FrozenClock
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingQuickCheck

from tests.helpers import NOW
from tests.structured_ai import StructuredClientFake


_CLOCK = FrozenClock(NOW)


class RecordingClient(StructuredClientFake):
    """A transport that records every request it is sent (no tools, files or network)."""

    provider_name = "fake"
    provider_type = "codex_sdk"  # billed to the subscription unless a test says otherwise
    model = "fake-model"

    def __init__(self, *, provider_type: str | None = None, isolates: bool = True, fail: bool = False,
                 span_ids=("s1",), gate: threading.Event | None = None, entered: threading.Event | None = None,
                 usage: dict | None = None) -> None:
        if provider_type is not None:
            self.provider_type = provider_type
        self.isolates = isolates
        self.fail = fail
        self.span_ids = list(span_ids)
        self.gate = gate
        self.entered = entered
        self.usage = usage
        self.requests: list = []

    def supports(self, capability: str) -> bool:
        if capability == ISOLATED_TURN:
            return self.isolates
        return capability == STRUCTURED_COMPLETION

    def complete(self, request):
        self.requests.append(request)
        if self.entered is not None:
            self.entered.set()
        if self.gate is not None:
            assert self.gate.wait(10)
        if self.usage:
            from learnloop.ai.execution import report_call_usage

            report_call_usage(self.usage)
        if self.fail:
            raise RuntimeError("the provider dropped the connection")
        return ReadingQuickCheck(
            question_md="Why is A's eigenbasis orthonormal?",
            expected_answer_md="Because A is symmetric.",
            span_ids=self.span_ids,
        )


def _spend(**over) -> RQC.PassageCheckSpend:
    values = {"max_checks_per_day": 100, "max_usd_per_check": 0.25, "price_per_million": None, "output_tokens": 4_000}
    values.update(over)
    return RQC.PassageCheckSpend(**values)


def _root(vault, repo, question="Why orthonormal?"):
    return RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
                  question_md=question, clock=_CLOCK)["reader_answer_event_id"]


def _author(repo, client, root, *, spend=None, owner="job_a", clock=_CLOCK):
    return RQC.author_inquiry_quick_check(
        repo, client, extraction_id="ext1", inquiry_root_event_id=root, anchor_span_ids=["s1"],
        clock=clock, spend=spend or _spend(), owner=owner,
    )


def _receipts(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE owner_kind = ? ORDER BY started_at", (RQC.PASSAGE_CHECK_RECEIPT_OWNER,)
        )]


def _inquiry_rows(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM reader_authored_questions WHERE scope_kind = 'inquiry'"
        )]
