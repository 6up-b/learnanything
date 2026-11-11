"""What other test files use from ``tests/test_assumed_known.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta
import sqlite3

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault


LOW_Q = "[placement]\nfast_track_q = 0.51\n"
EVIDENCE_TABLES = (
    "practice_attempts",
    "grading_evidence",
    "learning_object_mastery",
    "facet_recall_state",
    "facet_capability_evidence",
    "practice_item_state",
    "coldness_receipts",
    "learner_claims",
    "certification_cold_probe_outcomes",
    "error_events",
)


def _setup(tmp_path, *, version="mvp-0.11", placement_toml=None, name="vault"):
    paths = create_placement_vault(tmp_path / name, version=version, placement_toml=placement_toml)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _at(minutes: float):
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _answer(vault, repository, item_id, points=4.0, *, minutes, hints=0, session_id=None):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            hints_used=hints,
            attempt_type="hinted_attempt" if hints else "independent_attempt",
            session_id=session_id,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
        clock=_at(minutes),
    )


def _queue(vault, repository, minutes, *, persist=True, session_id=None):
    return build_due_queue(
        vault,
        repository,
        clock=_at(minutes),
        session=SchedulerSession(session_id=session_id),
        persist_explanations=persist,
    )


def _snapshot(paths) -> dict[str, list[tuple]]:
    snapshot = {}
    with sqlite3.connect(paths.sqlite_path) as connection:
        for table in EVIDENCE_TABLES:
            if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone() is None:
                continue
            snapshot[table] = sorted(
                tuple(str(value) for value in row) for row in connection.execute(f"SELECT * FROM {table}")
            )
    return snapshot


def _decisions(paths) -> list[dict]:
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM assumption_decisions ORDER BY created_at, id")]
