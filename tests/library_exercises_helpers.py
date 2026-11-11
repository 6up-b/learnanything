"""What other test files use from ``tests/test_library_exercises.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from tests.library_ask_fixtures import finish_job
from tests.recap_fixtures import call as call_rpc


QUERY = "solve for the eigenvalue x"
#: RW4b's two RPCs answer with a library job (never on the request path).
JOB_RPCS = frozenset({"reader.exercise_candidates", "reader.find_exercises"})


def call(ctx, name: str, params: dict[str, Any]) -> dict[str, Any]:
    """An RPC as the Reader sees it: RW4b's job RPCs are read until done."""

    result = call_rpc(ctx, name, params)
    if name in JOB_RPCS:
        assert set(result) >= {"jobId", "state"}, result  # never answered on the request path
        return finish_job(ctx, result)
    return result
