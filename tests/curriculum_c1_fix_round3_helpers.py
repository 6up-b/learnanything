"""What other test files use from ``tests/test_curriculum_c1_fix_round3.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3

from learnloop.daily_plan import engine as E
from learnloop.vault.loader import load_vault


def _env(c1):
    return E.PlanEnv(load_vault(c1.paths.root), c1.repository)


def _raw(c1, sql, params=()):
    """A write from another connection (as a background job or another process makes it)."""

    connection = sqlite3.connect(c1.paths.sqlite_path)
    try:
        connection.execute(sql, params)
        connection.commit()
    finally:
        connection.close()
