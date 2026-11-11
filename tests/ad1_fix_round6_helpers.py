"""What other test files use from ``tests/test_ad1_fix_round6.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


class _Moving:
    """A live-vault provider whose generation moves when told to."""

    def __init__(self, vault):
        self.vault, self.current, self.always = vault, 0, False

    def __call__(self):
        return self.vault

    def generation(self):
        if self.always:
            self.current += 1
        return self.current
