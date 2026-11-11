"""What other test files use from ``tests/test_required_method_reopened.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.required_method_authority_helpers import REQUIRES, StatementDecider


class FailingDecider(StatementDecider):
    def __init__(self, error):
        super().__init__(REQUIRES)
        self.error = error

    def decide(self, state, questions, *, purpose):
        self.calls.append((state, dict(questions)))
        raise self.error


def _mint_status(repository):
    with repository.connection() as connection:
        return [row[0] for row in connection.execute("SELECT status FROM surface_mint_requests")]
