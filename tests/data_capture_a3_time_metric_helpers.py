"""What other test files use from ``tests/test_data_capture_a3_time_metric.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from tests.router_outcomes_helpers import A, LO


def _attempt(repository, attempt_id, *, item=A, at, correctness=1.0, latency=120, session="s1", hints=0,
             presentation=None, attempt_type="independent_attempt"):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,"
            " correctness, latency_seconds, manual_review, created_at, session_id, primed, evidence_origin, plan_presentation_id)"
            " VALUES (?,?,?,?,?,?,?,?,0,?,?,0,'human',?)",
            (attempt_id, item, LO, "short_answer", attempt_type, hints, correctness, latency, at, session, presentation),
        )
        connection.commit()


def _reader_visit(repository, visit, *, opened, closed, active):
    with repository.connection() as connection:
        for event_id, kind, at, payload in (
                (f"{visit}o", "reader_view_opened", opened, {"visit_id": visit}),
                (f"{visit}c", "reader_view_closed", closed, {"visit_id": visit, "active_seconds": active})):
            connection.execute(
                "INSERT INTO interaction_events(id, kind, payload_json, origin, created_at, occurred_at, received_at)"
                " VALUES (?,?,?,'learner',?,?,?)", (event_id, kind, json.dumps(payload), at, at, at))
        connection.commit()
