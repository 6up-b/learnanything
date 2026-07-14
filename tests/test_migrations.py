from __future__ import annotations

import shutil
import sqlite3

import pytest

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
        "facet_uncertainty",
        "facet_recall_state",
        "facet_capability_evidence",
        "facet_merges",
    }:
        assert required in tables


def test_facet_diagnostic_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        grading_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(grading_evidence)")
        }
        intervention_need_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(intervention_needs)")
        }
        decision_type_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'decision_features'"
        ).fetchone()["sql"]

    assert "learner_confidence" in grading_columns
    assert "diagnostic_focus_json" in intervention_need_columns
    assert "followup" in decision_type_sql


def test_misconception_registry_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        error_event_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(error_events)")
        }
        discrimination_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(item_misconception_discrimination)")
        }

    assert {"misconceptions", "item_misconception_discrimination"} <= tables
    assert {
        "misconception_id",
        "misconception_statement",
        "misconception_consistent_answer",
    } <= error_event_columns
    assert {
        "practice_item_id",
        "misconception_id",
        "sensitivity_alpha",
        "specificity_beta",
        "n_planted_trials",
    } <= discrimination_columns


def test_misconception_migration_applies_on_pre_025_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 24:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    # Seed a pre-025 error event to confirm the ALTER preserves existing rows.
    with connect(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO error_events(
              id, attempt_id, learning_object_id, error_type, severity,
              is_misconception, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("ee_legacy", None, "lo_svd", "conceptual_slip", 0.5, 1, "active", "2026-05-19T12:00:00Z"),
        )
        connection.commit()

    applied = apply_migrations(sqlite_path)
    assert 25 in [migration.version for migration in applied]

    with connect(sqlite_path) as connection:
        row = connection.execute(
            "SELECT error_type, misconception_id FROM error_events WHERE id = ?",
            ("ee_legacy",),
        ).fetchone()
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert row["error_type"] == "conceptual_slip"
    assert row["misconception_id"] is None
    assert fk_issues == []


def test_source_layer_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        run_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(source_extraction_runs)")
        }
        reanchor_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'source_span_reanchors'"
        ).fetchone()["sql"]

    for required in {
        "source_artifacts",
        "source_revisions",
        "source_extraction_runs",
        "source_document_units",
        "source_document_blocks",
        "source_document_assets",
        "source_span_reanchors",
        "source_locator_schemes",
    }:
        assert required in tables
    assert {"extraction_request_hash", "extraction_result_hash"} <= run_columns
    assert "exact_hash" in reanchor_sql and "geometry_section" in reanchor_sql


def test_source_layer_migration_applies_on_pre_032_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 31:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    applied = apply_migrations(sqlite_path)
    assert 32 in [migration.version for migration in applied]

    with connect(sqlite_path) as connection:
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert fk_issues == []
    assert "source_extraction_runs" in tables


def test_durable_ingest_jobs_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        job_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(ingest_jobs)")
        }
        batch_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'ingest_batches'"
        ).fetchone()["sql"]
        job_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'ingest_jobs'"
        ).fetchone()["sql"]

    assert {"ingest_batches", "ingest_jobs", "ingest_job_dependencies"} <= tables
    assert {
        "worker_id",
        "heartbeat_at",
        "phase",
        "current_window",
        "total_windows",
        "usage_json",
        "attempt_count",
        "cancel_requested",
    } <= job_columns
    # Status is a closed CHECK vocabulary; workflow_type/job_type are open strings.
    assert "waiting_for_input" in job_sql and "blocked" in job_sql
    assert "CHECK" not in job_sql.split("job_type")[1].split(",")[0]
    assert "waiting_for_input" in batch_sql


def test_durable_ingest_jobs_migration_applies_on_pre_033_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 32:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    applied = apply_migrations(sqlite_path)
    assert 33 in [migration.version for migration in applied]

    with connect(sqlite_path) as connection:
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert fk_issues == []
    assert {"ingest_batches", "ingest_jobs", "ingest_job_dependencies"} <= tables


def test_source_unit_selections_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(source_unit_selections)")
        }

    assert "source_unit_selections" in tables
    assert {
        "extraction_id",
        "source_id",
        "revision_id",
        "selected_unit_ids_json",
        "boundary_overrides_json",
        "needs_review_json",
    } <= columns


def test_source_unit_selections_migration_applies_on_pre_040_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 39:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    applied = apply_migrations(sqlite_path)
    assert 40 in [migration.version for migration in applied]

    with connect(sqlite_path) as connection:
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert fk_issues == []
    assert "source_unit_selections" in tables


def test_provenance_manifests_apply_intents_schema_is_available(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        link_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(entity_source_links)")
        }

    assert {
        "entity_source_links",
        "notation_mappings",
        "source_conflicts",
        "synthesis_manifests",
        "synthesis_runs",
        "apply_intents",
    } <= tables
    assert {"entity_type", "entity_id", "locator", "relation", "status", "revision_id"} <= link_columns


def test_entity_source_links_relation_and_status_checks(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    with connect(sqlite_path) as connection:
        # Invalid relation is rejected by the CHECK.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO entity_source_links(id, entity_type, entity_id, locator, relation, created_at)"
                " VALUES ('l1', 'facet', 'f1', 'loc', 'not_a_relation', '2026-01-01T00:00:00Z')"
            )
        # Invalid status is rejected by the CHECK.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO entity_source_links(id, entity_type, entity_id, locator, relation, status, created_at)"
                " VALUES ('l2', 'facet', 'f1', 'loc', 'primary', 'bogus', '2026-01-01T00:00:00Z')"
            )


def test_provenance_migration_applies_on_pre_044_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 43:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    applied = apply_migrations(sqlite_path)
    assert 44 in [migration.version for migration in applied]

    with connect(sqlite_path) as connection:
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert fk_issues == []
    assert "apply_intents" in tables


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
