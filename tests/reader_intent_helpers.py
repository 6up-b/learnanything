"""What other test files use from ``tests/test_reader_intent.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.reader import reader_intent as RI

from tests.router_model_fakes import FakeDecider as _FakeDecider


class FakeDecider(_FakeDecider):
    """The router's fake Decider at the Decider's listed input price."""

    settings = SimpleNamespace(price_per_million_input=0.02)


ON = RI.Availability(active_reading=True, workbench=True, sources=True)


def _prefer(option: str):
    return lambda refs: {ref: (0.9 if ref == option else 0.1 / max(1, len(refs) - 1)) for ref in refs}
