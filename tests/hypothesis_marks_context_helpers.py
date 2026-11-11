"""What other test files use from ``tests/test_hypothesis_marks_context.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing

from learnloop.db.connection import connect
from learnloop.ops.capture_report import hypothesis_marks_section
from learnloop.vault.paths import VaultPaths


def _versions(marks):
    return [row["hypothesisVersionId"] for row in marks["hypotheses"]]


def _report(vault):
    path = VaultPaths(vault.root, vault.config).sqlite_path
    from learnloop.db.repositories import Repository

    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        return hypothesis_marks_section(connection, vault, Repository.attach(path, read_only=True), success_correctness=0.7)
