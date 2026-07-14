"""Track 0: session attempt attribution joins by session_id, not time window.

Two overlapping sessions must attribute attempts through the persisted
``practice_attempts.session_id``; the time-window fallback exists only for
legacy rows whose ``session_id`` is NULL.
"""

from __future__ import annotations

from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault

LO_ID = "lo_svd_definition"


def _insert_session(repository, session_id, started_at, ended_at):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO sessions(id, started_at, ended_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, started_at, ended_at, started_at),
        )
        connection.commit()


def _insert_attempt(repository, attempt_id, *, created_at, session_id, item_id="pi_svd_define_001"):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode,
              attempt_type, rubric_score, correctness, created_at, session_id
            )
            VALUES (?, ?, ?, 'short_answer', 'independent_attempt', 4, 1.0, ?, ?)
            """,
            (attempt_id, item_id, LO_ID, created_at, session_id),
        )
        connection.commit()


def test_overlapping_sessions_attribute_attempts_by_session_id(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    # Session B is entirely inside session A's time window.
    _insert_session(repository, "sess_a", "2026-05-19T10:00:00Z", "2026-05-19T12:00:00Z")
    _insert_session(repository, "sess_b", "2026-05-19T10:30:00Z", "2026-05-19T11:30:00Z")

    _insert_attempt(repository, "att_a1", created_at="2026-05-19T10:15:00Z", session_id="sess_a")
    _insert_attempt(repository, "att_a2", created_at="2026-05-19T11:00:00Z", session_id="sess_a")
    # Recorded inside A's window but belongs to B: the old time-window join
    # would have double-counted this into session A.
    _insert_attempt(repository, "att_b1", created_at="2026-05-19T10:45:00Z", session_id="sess_b")

    counts_a = repository.session_attempt_counts("sess_a")
    counts_b = repository.session_attempt_counts("sess_b")
    assert counts_a == {"attempts_recorded": 2, "items_reviewed": 1}
    assert counts_b == {"attempts_recorded": 1, "items_reviewed": 1}


def test_time_window_fallback_applies_only_to_legacy_null_session_rows(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    _insert_session(repository, "sess_a", "2026-05-19T10:00:00Z", "2026-05-19T12:00:00Z")
    _insert_session(repository, "sess_b", "2026-05-19T10:30:00Z", "2026-05-19T11:30:00Z")

    # A legacy row (session_id NULL) inside both windows is recovered by the
    # time fallback for each session — the best available attribution.
    _insert_attempt(repository, "att_legacy", created_at="2026-05-19T10:50:00Z", session_id=None)
    # A session-stamped row inside both windows counts only for its own session.
    _insert_attempt(repository, "att_b1", created_at="2026-05-19T10:55:00Z", session_id="sess_b")
    # A legacy row outside session B's window counts only for session A.
    _insert_attempt(repository, "att_legacy_late", created_at="2026-05-19T11:45:00Z", session_id=None)

    assert repository.session_attempt_counts("sess_a")["attempts_recorded"] == 2
    assert repository.session_attempt_counts("sess_b")["attempts_recorded"] == 2


def test_unknown_session_returns_none(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    assert repository.session_attempt_counts("missing") is None
