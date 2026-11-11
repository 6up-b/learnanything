"""What other test files use from ``tests/test_ad23_fix_r8.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository


def _reserve(monkeypatch, *item_ids: str) -> None:
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: list(item_ids))
