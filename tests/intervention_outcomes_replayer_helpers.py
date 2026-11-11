"""What other test files use from ``tests/test_intervention_outcomes_replayer.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import datetime, timezone


T0 = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def _intervention(**extra):
    return {"id": "rti_1", "created_at": T0.isoformat(), "session_id": "s1",
            "assets": {"practice_item_ids": ["pi_eigen_1"]}, "targets": {"facets": ["facet_eigen"]}, **extra}


def _attempt(attempt_id, at, **extra):
    return {"id": attempt_id, "practice_item_id": "pi_eigen_1", "created_at": at.isoformat(), "session_id": "s1",
            "correctness": 1.0, "rubric_score": 4, "error_type": None, "attempt_type": "independent_attempt",
            "hints_used": 0, "primed": 0, "latency_seconds": 90.0, "declared_dont_know": 0,
            "facets": {"facet_eigen"}, **extra}
