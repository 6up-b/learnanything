"""What other test files use from ``tests/test_teacher_te1_successor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault


class _Ctx:
    def __init__(self, paths, repository):
        self.paths, self.repository = paths, repository
        self.grading_provider_override = None
        self.reloads = 0

    def require_vault(self):
        return load_vault(self.paths.root), self.repository

    def reload(self, maintenance: bool = True):
        self.reloads += 1
