"""What other test files use from ``tests/test_router_outcomes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision


T0 = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
LO = "lo_svd_definition"
A, B = "pi_svd_define_001", "pi_svd_define_002"


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(**delta) -> str:
    return _iso(T0 + timedelta(**delta))


def _decision(repo, decision_id: str, *, created_at: str, kind: str = "today_offer", session: str = "s1",
              item: str | None = A, candidate: str | None = "c1", parent: str | None = None) -> None:
    pick = kind == "learner_pick"
    row = {
        "id": decision_id, "receipt_key": f"{kind}:{decision_id}", "decision_kind": kind,
        "surface": "desktop_queue", "mode": "legacy_queue", "policy": "learner" if pick else "composed_offer_v2",
        "algorithm_version": "mvp-0.11", "log_version": ROUTER_LOG_VERSION, "session_id": session,
        "parent_decision_id": parent, "snapshot_hash": "h", "candidates_json": "[]", "exclusions_json": "{}",
        "candidate_count": 0, "chosen_ref": item or "stop_for_today", "chosen_practice_item_id": item,
        "chosen_learning_object_id": LO if item else None, "chosen_scheduler_candidate_id": candidate,
        "propensity": None if pick else 1.0, "propensity_kind": "none" if pick else "deterministic",
        "learner_pick": 1 if pick else 0, "detail_json": "{}", "created_at": created_at,
    }
    with repo.atomic(), repo.connection() as connection:
        insert_router_decision(connection, row)


def _attempt(repo, attempt_id: str, *, item: str, created_at: str, correctness: float, session: str = "s1",
             candidate: str | None = None, hints: int = 0, primed: int = 0,
             attempt_type: str = "independent_attempt", origin: str = "human") -> None:
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO practice_attempts(
                 id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,
                 correctness, manual_review, created_at, session_id, scheduler_candidate_id, primed,
                 evidence_origin)
               VALUES (?,?,?,?,?,?,?,0,?,?,?,?,?)""",
            (attempt_id, item, LO, "short_answer", attempt_type, hints, correctness, created_at, session,
             candidate, primed, origin),
        )
        connection.commit()


def _reveal(repo, reveal_id: str, *, item: str, created_at: str) -> None:
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (reveal_id, item, LO, "tutor_answer", 1.0, created_at),
        )
        connection.commit()
