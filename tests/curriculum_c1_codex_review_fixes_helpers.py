"""What other test files use from ``tests/test_curriculum_c1_codex_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from tests.rw7b_codex_review_fixes_helpers import _blocks


def _ended(repository, block_id) -> list[dict]:
    _blocks_, events = _blocks(repository)
    return [json.loads(e["detail_json"]) for e in events if e["block_id"] == block_id and e["kind"] == "block_ended"]


NEAR_PRIMARIES = {"Eigenvalues": "Chapter 5 Eigenvalues", "Determinants": "Chapter 3 Determinants"}
