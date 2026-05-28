from __future__ import annotations

import shutil

from learnloop.attempt_types import SUPPORTED_ATTEMPT_TYPES
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, applied_versions, discover_migrations
from learnloop.db.repositories import Repository


def test_discover_finds_initial_migration():
    migrations = discover_migrations()
    versions = [migration.version for migration in migrations]
    assert versions == sorted(versions)
    assert 1 in versions


def test_fresh_db_applies_all_migrations(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    applied = apply_migrations(sqlite_path)

    assert [migration.version for migration in applied] == [m.version for m in discover_migrations()]
    assert 1 in applied_versions(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    for required in {
        "practice_attempts",
        "learning_object_mastery",
        "proposed_patches",
        "hypothesis_sets",
        "derived_state_rebuilds",
        "scheduler_slates",
        "scheduler_slate_candidates",
        "learning_outcome_labels",
    }:
        assert required in tables


def test_migrations_are_idempotent(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    second = apply_migrations(sqlite_path)
    assert second == []


def test_existing_db_migrates_cleanly(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    # Re-running against an existing, already-migrated DB is a no-op and keeps the
    # recorded version set stable.
    before = applied_versions(sqlite_path)
    apply_migrations(sqlite_path)
    assert applied_versions(sqlite_path) == before


def test_practice_attempts_allow_open_text_after_fresh_migration(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_open_text", attempt_type="open_text")
        connection.commit()

        row = connection.execute(
            "SELECT attempt_type FROM practice_attempts WHERE id = ?",
            ("attempt_open_text",),
        ).fetchone()

    assert row["attempt_type"] == "open_text"


def test_agent_runs_have_generic_provider_metadata(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(agent_runs)")
        }
        connection.execute(
            """
            INSERT INTO agent_runs(
              id, purpose, provider, provider_type, model, provider_revision,
              started_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "run_deepseek",
                "grading",
                "deepseek_flash",
                "openai_chat",
                "deepseek-v4-flash",
                None,
                "2026-05-19T12:00:00Z",
                "completed",
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM agent_runs WHERE id = ?", ("run_deepseek",)).fetchone()

    assert {"provider_type", "provider_revision"} <= columns
    assert row["provider"] == "deepseek_flash"
    assert row["provider_type"] == "openai_chat"
    assert row["model"] == "deepseek-v4-flash"


def test_attempt_feedback_metadata_allows_ai_source(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_ai", attempt_type="independent_attempt")
        connection.execute(
            """
            INSERT INTO attempt_feedback_metadata(
              attempt_id, grading_source, fatal_errors_json,
              repair_suggestions_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("attempt_ai", "ai", "[]", "[]", "2026-05-19T12:00:00Z", "2026-05-19T12:00:00Z"),
        )
        connection.commit()
        row = connection.execute(
            "SELECT grading_source FROM attempt_feedback_metadata WHERE attempt_id = ?",
            ("attempt_ai",),
        ).fetchone()

    assert row["grading_source"] == "ai"


def test_scheduler_training_log_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        attempt_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(practice_attempts)")
        }
        feedback_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(attempt_feedback_metadata)")
        }

    assert {"session_id", "scheduler_slate_id", "scheduler_candidate_id"} <= attempt_columns
    assert {"shown_count", "first_shown_at", "last_shown_at"} <= feedback_columns


def test_practice_attempts_schema_matches_supported_attempt_types(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        for attempt_type in SUPPORTED_ATTEMPT_TYPES:
            _insert_attempt(connection, attempt_id=f"attempt_{attempt_type}", attempt_type=attempt_type)
        connection.commit()

        count = connection.execute("SELECT COUNT(*) AS count FROM practice_attempts").fetchone()

    assert count["count"] == len(SUPPORTED_ATTEMPT_TYPES)


def test_open_text_migration_preserves_existing_attempts_and_foreign_keys(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 3:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_existing", attempt_type="independent_attempt")
        connection.execute(
            """
            INSERT INTO grading_evidence(
              id, attempt_id, criterion_id, points_awarded, evidence, notes,
              agent_run_id, local_grader_id, grader_tier, created_at,
              superseded_at, superseded_by_evidence_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evidence_existing",
                "attempt_existing",
                "correctness",
                4.0,
                "Complete.",
                None,
                None,
                "self",
                1,
                "2026-05-19T12:00:00Z",
                None,
                None,
            ),
        )
        connection.commit()

    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_open_text", attempt_type="open_text")
        rows = connection.execute("PRAGMA foreign_key_check").fetchall()
        existing = connection.execute(
            "SELECT attempt_type FROM practice_attempts WHERE id = ?",
            ("attempt_existing",),
        ).fetchone()
        evidence = connection.execute(
            "SELECT attempt_id FROM grading_evidence WHERE id = ?",
            ("evidence_existing",),
        ).fetchone()
        connection.commit()

    assert rows == []
    assert existing["attempt_type"] == "independent_attempt"
    assert evidence["attempt_id"] == "attempt_existing"


def test_repository_applies_pending_migrations_on_open(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 3:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)

    Repository(sqlite_path)

    assert 4 in applied_versions(sqlite_path)
    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_open_text", attempt_type="open_text")
        connection.commit()


def _insert_attempt(connection, *, attempt_id: str, attempt_type: str) -> None:
    connection.execute(
        """
        INSERT INTO practice_attempts(
          id, practice_item_id, learning_object_id, subject, concept, practice_mode,
          attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
          rubric_score, correctness, confidence, latency_seconds, hints_used,
          error_type, grader_confidence, manual_review, manual_review_reason,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id,
            "pi_svd",
            "lo_svd",
            "linear-algebra",
            "singular_value_decomposition",
            "constructed_response",
            attempt_type,
            "answer",
            "[]",
            "{}",
            4,
            1.0,
            5,
            10,
            0,
            None,
            0.9,
            0,
            None,
            "2026-05-19T12:00:00Z",
            "2026-05-19T12:00:00Z",
        ),
    )
