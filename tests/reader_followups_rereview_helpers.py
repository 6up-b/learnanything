"""What other test files use from ``tests/test_reader_followups_rereview.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.reader_followups_helpers import FakeSearch


class _PerCall(FakeSearch):
    """Call ``n`` values ``rounds[n]``; every call but the last stops on its budget.
    Perfect-information tables: a second check with the same information adds none."""

    def __init__(self, rounds):
        super().__init__([])
        self.rounds = rounds

    def __call__(self, query, constraints, *, caller, **kwargs):
        self.candidates = self.rounds[min(len(self.calls), len(self.rounds) - 1)]
        result = dict(super().__call__(query, constraints, caller=caller, **kwargs))
        if len(self.calls) < len(self.rounds):
            result["paging"] = {"outcome": "budget", "cursor": {"judged_items": []}}
        return result
