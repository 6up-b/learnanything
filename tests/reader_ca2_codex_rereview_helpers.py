"""What other test files use from ``tests/test_reader_ca2_codex_rereview.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from learnloop.algorithm_versions import ONE_ASK_ALGORITHM_VERSION

from tests.hint_fakes import WORK
from tests.reader_ca2_codex_review_helpers import _call
from tests.ux_phase1_support import set_config
from tests.workbench_help_fakes import sidecar as help_sidecar


def _attempt(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _steps_sidecar(tmp_path):
    paths, ctx, session = help_sidecar(tmp_path)
    set_config(paths.root, {("algorithms", "algorithm_version"): ONE_ASK_ALGORITHM_VERSION})
    ctx.load(paths.root)
    return paths, ctx, session


def _draft(ctx, session, item: str, key: str, **extra):
    _call(ctx, "save_practice_draft", {"sessionId": session, "practiceItemId": item, "answerMd": WORK,
                                       "hintsUsed": 0, "submissionId": key, **extra})
