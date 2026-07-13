from __future__ import annotations

import shutil
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.services.tutor_qa import TutorQAError, build_tutor_qa_note
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


# --- migration -------------------------------------------------------------


def test_question_promotions_schema_available_on_fresh_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        qp_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(question_promotions)")
        }
        qe_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(question_events)")
        }
        claims_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'learner_claims'"
        ).fetchone()["sql"]
        decision_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'decision_features'"
        ).fetchone()["sql"]

    assert "question_promotions" in tables
    assert {"question_event_id", "intent", "route", "attributed_facets_json"} <= qp_columns
    assert "saved_note_id" in qe_columns
    assert "tutor_gap_declaration" in claims_sql
    assert "question_promotion" in decision_sql
    assert "UNIQUE" in decision_sql


def test_027_rebuild_preserves_existing_rows(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 26:
            shutil.copy2(migration.path, old_migrations / migration.path.name)

    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    with connect(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO learner_claims(
              id, claim_type, scope_type, scope_id, evidence_family,
              claimed_level, prior_pseudo_count, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("claim_legacy", "self_rating", "learning_object", "lo_svd_definition",
             "recall", 0.5, 2.0, "init_wizard", NOW_ISO),
        )
        connection.execute(
            """
            INSERT INTO decision_features(
              id, decision_id, decision_type, ability_vector_json,
              algorithm_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("df_legacy", "ev_legacy", "followup", "{}", "v1", NOW_ISO),
        )
        connection.commit()

    applied = apply_migrations(sqlite_path)
    assert 27 in [migration.version for migration in applied]

    with connect(sqlite_path) as connection:
        claim = connection.execute(
            "SELECT source FROM learner_claims WHERE id = ?", ("claim_legacy",)
        ).fetchone()
        feature = connection.execute(
            "SELECT decision_type FROM decision_features WHERE id = ?", ("df_legacy",)
        ).fetchone()
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert claim["source"] == "init_wizard"
    assert feature["decision_type"] == "followup"
    assert fk_issues == []


def test_learner_claims_accepts_tutor_gap_declaration_source(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    with connect(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO learner_claims(
              id, claim_type, scope_type, scope_id, evidence_family,
              claimed_level, prior_pseudo_count, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("claim_gap", "self_rating", "learning_object", "lo_svd_definition",
             "recall", 0.25, 2.0, "tutor_gap_declaration", NOW_ISO),
        )
        connection.commit()
        row = connection.execute(
            "SELECT source FROM learner_claims WHERE id = ?", ("claim_gap",)
        ).fetchone()
    assert row["source"] == "tutor_gap_declaration"


def test_decision_features_accepts_question_promotion_type(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    feature_id = repository.record_decision_features(
        decision_id="ev_promo",
        decision_type="question_promotion",
        ability_vector={"mastery_mean": 0.4},
        context={"intent": "gap"},
        algorithm_version="v1",
    )
    stored = repository.decision_features(decision_id="ev_promo", decision_type="question_promotion")
    assert stored is not None
    assert stored["id"] == feature_id
    assert stored["context"]["intent"] == "gap"


# --- question_promotions CRUD ---------------------------------------------


def _insert_event(repository: Repository, event_id: str, **overrides) -> str:
    payload = {
        "id": event_id,
        "context": "practice",
        "practice_item_id": "pi_svd_define_001",
        "question_md": "Why does U have orthonormal columns?",
        "answer_md": "Consider the shape of the factors.",
        "answer_status": "answered",
    }
    payload.update(overrides)
    return repository.insert_question_event(payload)


def test_question_promotion_crud_and_idempotent_pk(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    _insert_event(repository, "ev1")

    repository.insert_question_promotion(
        question_event_id="ev1",
        intent="gap",
        route="diagnostic_pending",
        attributed_facets=["recall", "mechanism"],
        question_nature="mechanism",
        attempted_in_thread=True,
    )

    row = repository.question_promotion("ev1")
    assert row is not None
    assert row["intent"] == "gap"
    assert row["route"] == "diagnostic_pending"
    assert row["attributed_facets"] == ["recall", "mechanism"]
    assert row["attempted_in_thread"] is True
    assert row["created_learning_object_id"] is None

    # Re-inserting the same event PK raises (idempotency is the caller's job).
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        repository.insert_question_promotion(
            question_event_id="ev1", intent="practice", route="auto_apply"
        )

    # update fills created ids and transitions the route.
    assert repository.update_question_promotion(
        "ev1",
        route="existing_item",
        created_practice_item_id="pi_new_001",
    )
    updated = repository.question_promotion("ev1")
    assert updated["route"] == "existing_item"
    assert updated["created_practice_item_id"] == "pi_new_001"
    # untouched fields survive the partial update.
    assert updated["attributed_facets"] == ["recall", "mechanism"]
    assert updated["updated_at"] >= row["updated_at"]

    # list + per-event batch fetch.
    assert [r["question_event_id"] for r in repository.question_promotions()] == ["ev1"]
    batch = repository.question_promotions_for_events(["ev1", "missing"])
    assert set(batch) == {"ev1"}
    assert repository.question_promotions_for_events([]) == {}


def test_update_question_promotion_missing_row_returns_false(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    assert repository.update_question_promotion("nope", route="auto_apply") is False


def test_requested_practice_item_ids_orders_oldest_first_and_excludes_attempted(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    for event_id in ("ev_a", "ev_b", "ev_c"):
        _insert_event(repository, event_id)

    # ev_b promoted first (oldest), then ev_a, then ev_c.
    repository.insert_question_promotion(
        question_event_id="ev_b",
        intent="practice",
        route="auto_apply",
        created_practice_item_id="pi_b",
        clock=FrozenClock(NOW),
    )
    repository.insert_question_promotion(
        question_event_id="ev_a",
        intent="practice",
        route="existing_item",
        existing_practice_item_id="pi_a",
        clock=FrozenClock(NOW + timedelta(minutes=1)),
    )
    repository.insert_question_promotion(
        question_event_id="ev_c",
        intent="practice",
        route="auto_apply",
        created_practice_item_id="pi_c",
        clock=FrozenClock(NOW + timedelta(minutes=2)),
    )

    # pi_c already has an attempt -> excluded from the requested floor.
    with connect(repository.sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode,
              attempt_type, hints_used, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("att_c", "pi_c", "lo_svd_definition", "short_answer",
             "independent_attempt", 0, NOW_ISO),
        )
        connection.commit()

    assert repository.requested_practice_item_ids() == ["pi_b", "pi_a"]


def test_pending_gap_need_for_facets(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    repository.upsert_intervention_need(
        {
            "id": "need_gap",
            "attempt_id": None,
            "learning_object_id": "lo_svd_definition",
            "practice_item_id": None,
            "desired_intent": "diagnostic_probe",
            "trigger_reason": "tutor_gap_declaration",
            "target_facets": ["recall", "mechanism"],
            "error_types": [],
            "priority": 0.6,
            "blocked_reason": "tutor_gap_declaration",
            "candidate_requirements": {},
            "updated_at": NOW_ISO,
        }
    )
    # A pending need for a different reason must not match.
    repository.upsert_intervention_need(
        {
            "id": "need_other",
            "attempt_id": None,
            "learning_object_id": "lo_svd_definition",
            "practice_item_id": None,
            "desired_intent": "diagnostic_probe",
            "trigger_reason": "repeat_failure",
            "target_facets": ["transfer"],
            "error_types": [],
            "priority": 0.6,
            "blocked_reason": "repeat_failure",
            "candidate_requirements": {},
            "updated_at": NOW_ISO,
        }
    )

    hit = repository.pending_gap_need_for_facets(["mechanism"])
    assert hit is not None and hit["id"] == "need_gap"
    assert repository.pending_gap_need_for_facets(["transfer"]) is None
    assert repository.pending_gap_need_for_facets([]) is None


# --- saved-note back-link --------------------------------------------------


def test_build_tutor_qa_note_writes_back_link_and_is_idempotent(tmp_path):
    root = tmp_path / "vault"
    create_basic_vault(root)
    repository = Repository(root / "state.sqlite")
    vault = load_vault(root)

    event_id = _insert_event(repository, "ev_note")
    event = repository.question_event(event_id)
    assert event["saved_note_id"] is None

    result = build_tutor_qa_note(vault, repository, event)
    assert result["reused"] is False
    note_id = result["note_id"]
    assert note_id

    # Back-link persisted onto the question_event.
    reread = repository.question_event(event_id)
    assert reread["saved_note_id"] == note_id

    # Second call short-circuits to the existing note (no duplicate).
    vault = load_vault(root)
    again = build_tutor_qa_note(vault, repository, reread)
    assert again["reused"] is True
    assert again["note_id"] == note_id


def test_build_tutor_qa_note_raises_without_subject(tmp_path):
    # Bare vault with no subjects: nowhere to file the note.
    from learnloop.clock import FrozenClock as _FrozenClock
    from learnloop.vault.loader import init_vault

    root = tmp_path / "vault"
    init_vault(root, clock=_FrozenClock(NOW))
    repository = Repository(root / "state.sqlite")
    vault = load_vault(root)
    event_id = repository.insert_question_event(
        {
            "id": "ev_nosubj",
            "context": "library",
            "question_md": "What is a kernel?",
            "answer_md": "Consider null spaces.",
            "answer_status": "answered",
        }
    )
    event = repository.question_event(event_id)
    with pytest.raises(TutorQAError):
        build_tutor_qa_note(vault, repository, event)
