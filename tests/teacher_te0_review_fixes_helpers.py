"""What other test files use from ``tests/test_teacher_te0_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


HELD_SUPPORT = {
    "proof_route_check": {"status": "checked", "held_for_review": True, "version": "proof-route-check-v3"},
    "valid_alternative_gate_applied": True,
    "assessed_shortfall": False,
}
