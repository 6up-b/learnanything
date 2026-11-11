"""What other test files use from ``tests/test_reader_ca2_fix_orchestrator.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from tests.hint_fakes import ITEM as CDF_ITEM
from tests.reader_ca2_codex_review_helpers import _call
from tests.workbench_help_fakes import STEP_1


def _row(paths, workbench_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM workbench_sessions WHERE id = ?", (workbench_id,)).fetchone())


def _open(ctx, session: str, *, carried: int = 0, resume: str | None = None) -> dict:
    params = {"origin": "practice", "entry": "practice_screen", "carriedHints": carried, "practiceSessionId": session}
    if resume:
        params["sessionId"] = resume
    else:
        params.update({"practiceItemId": CDF_ITEM, "stemMd": "Find P(X <= 1/2)."})
    return _call(ctx, "workbench.open", params)["session"]


def _step(ctx, workbench_id: str, key: str = "s0") -> None:
    _call(ctx, "workbench.save_step", {"sessionId": workbench_id, "clientIdempotencyKey": key, "op": "add",
                                       "bodyMd": STEP_1})


#: The table 223 alters: the earlier migrations' "nothing else changed" diffs on the way to head read it.
CA2_ALTERED_TABLES = frozenset({"workbench_sessions"})
