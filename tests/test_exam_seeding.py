from __future__ import annotations

from tests.structured_ai import StructuredClientFake

import shutil

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.goals.exam_seeding import (
    EXAM_ATTEMPT_TYPE,
    ExamSeedingError,
    exam_ingest_instructions,
    find_exam_items,
    parse_exam_outcomes,
    seed_exam_attempts,
)
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.content.pipeline.source_ingestion import ingest_canonical_source
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, create_basic_vault

EXAM_DATE = "2026-05-01"
LIVE_NOW = NOW  # 2026-05-19, after the exam date


def _exam_vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    clock = FrozenClock(NOW)
    for question, rubric in (
        ("1", {"max_points": 4, "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}], "fatal_errors": []}),
        (
            "2",
            {
                "max_points": 4,
                "criteria": [
                    {"id": "setup", "points": 3, "description": "Sets up the factorization."},
                    {"id": "interpretation", "points": 1, "description": "Interprets the factors."},
                ],
                "fatal_errors": [],
            },
        ),
        ("3", {"max_points": 4, "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}], "fatal_errors": []}),
    ):
        upsert_practice_item(
            vault_root,
            {
                "id": f"pi_exam_q{question}",
                "learning_object_id": "lo_svd_definition",
                "subjects": None,
                "practice_mode": "constructed_response",
                "attempt_types_allowed": ["independent_attempt", "dont_know"],
                "evidence_facets": ["recall"],
                "evidence_weights": {"recall": 1.0},
                "prompt": f"Exam question {question} about SVD.",
                "expected_answer": "Model solution.",
                "tags": ["exam_question", f"exam_q:{question}"],
                "grading_rubric": rubric,
                "created_at": "2026-05-19T12:00:00Z",
                "updated_at": "2026-05-19T12:00:00Z",
            },
            clock=clock,
        )
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, loaded, repository


def _outcomes(**overrides):
    payload = {
        "exam_date": EXAM_DATE,
        "outcomes": {
            "1": {"score": 1.0},
            "2": {"score": 0.5, "answer_md": "Half-right setup.", "confidence": 2},
            "3": {"score": 0.0},
        },
    }
    payload.update(overrides)
    return parse_exam_outcomes(payload)


def test_seed_creates_backdated_discounted_attempts(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)

    result = seed_exam_attempts(loaded, repository, outcomes=_outcomes())

    assert result.seeded_count == 3
    assert result.skipped_existing_count == 0
    assert result.no_outcome_count == 0
    assert result.rebuild is not None
    attempts = repository.list_attempts_by_learning_object("lo_svd_definition")
    assert len(attempts) == 3
    by_item = {attempt["practice_item_id"]: attempt for attempt in attempts}
    for attempt in attempts:
        assert attempt["attempt_type"] == EXAM_ATTEMPT_TYPE
        assert attempt["created_at"].startswith(EXAM_DATE)
        # Reliability discount comes from config, not the 1-5 confidence mapping.
        assert attempt["grader_confidence"] == pytest.approx(loaded.config.exam_seeding.grader_confidence)
    # Per-question second offsets keep created_at ordering stable (q1 < q2 < q3).
    assert [attempt["practice_item_id"] for attempt in attempts] == [
        "pi_exam_q1",
        "pi_exam_q2",
        "pi_exam_q3",
    ]
    # Outcome confidence is used when provided; config default (3) otherwise.
    assert by_item["pi_exam_q2"]["confidence"] == 2
    assert by_item["pi_exam_q1"]["confidence"] == loaded.config.exam_seeding.default_learner_confidence
    assert by_item["pi_exam_q2"]["learner_answer_md"] == "Half-right setup."
    assert by_item["pi_exam_q3"]["learner_answer_md"] == "[imported exam outcome: score 0.00]"
    assert by_item["pi_exam_q1"]["correctness"] == pytest.approx(1.0)
    assert by_item["pi_exam_q2"]["correctness"] == pytest.approx(0.5)
    assert by_item["pi_exam_q3"]["correctness"] == pytest.approx(0.0)
    # Proportional criterion split: score * criterion.points per criterion.
    evidence = {
        row.criterion_id: row.points_awarded
        for row in repository.fetch_grading_evidence(by_item["pi_exam_q2"]["id"])
    }
    assert evidence == {"setup": pytest.approx(1.5), "interpretation": pytest.approx(0.5)}
    # Beliefs seeded through the normal pipeline: mastery + facet evidence exist.
    mastery = repository.mastery_state("lo_svd_definition")
    assert mastery is not None
    assert mastery.evidence_count == 3
    assert mastery.last_evidence_at.startswith(EXAM_DATE)
    facet_states = repository.facet_recall_states("lo_svd_definition")
    assert any(state.facet_id == "recall" for state in facet_states)
    for question in ("1", "2", "3"):
        state = repository.practice_item_state(f"pi_exam_q{question}")
        assert state is not None
        assert state.last_attempt_at.startswith(EXAM_DATE)


def test_seed_rerun_is_idempotent(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)
    first = seed_exam_attempts(loaded, repository, outcomes=_outcomes())
    assert first.seeded_count == 3

    second = seed_exam_attempts(loaded, repository, outcomes=_outcomes())

    assert second.seeded_count == 0
    assert second.skipped_existing_count == 3
    assert {entry.status for entry in second.entries} == {"skipped_existing"}
    assert len(repository.list_attempts_by_learning_object("lo_svd_definition")) == 3


def test_unmatched_outcome_key_errors(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)
    outcomes = parse_exam_outcomes({"exam_date": EXAM_DATE, "outcomes": {"1": 1.0, "9": 0.5, "10": 0.5}})

    with pytest.raises(ExamSeedingError, match="no matching exam item.*9, 10"):
        seed_exam_attempts(loaded, repository, outcomes=outcomes)
    assert repository.list_attempts_by_learning_object("lo_svd_definition") == []


def test_exam_item_without_outcome_warns_and_skips(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)
    outcomes = parse_exam_outcomes({"exam_date": EXAM_DATE, "outcomes": {"1": 1.0, "3": 0.0}})

    result = seed_exam_attempts(loaded, repository, outcomes=outcomes)

    assert result.seeded_count == 2
    assert result.no_outcome_count == 1
    warning = next(entry for entry in result.entries if entry.status == "no_outcome")
    assert warning.practice_item_id == "pi_exam_q2"
    attempts = repository.list_attempts_by_learning_object("lo_svd_definition")
    assert {attempt["practice_item_id"] for attempt in attempts} == {"pi_exam_q1", "pi_exam_q3"}


def test_dry_run_writes_nothing(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)

    result = seed_exam_attempts(loaded, repository, outcomes=_outcomes(), dry_run=True)

    assert result.dry_run is True
    assert result.seeded_count == 3
    assert {entry.status for entry in result.entries} == {"would_seed"}
    assert result.rebuild is None
    assert repository.list_attempts_by_learning_object("lo_svd_definition") == []
    assert repository.mastery_state("lo_svd_definition") is None


def test_rebuild_after_seeding_is_stable(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)
    seed_exam_attempts(loaded, repository, outcomes=_outcomes())

    def snapshot():
        mastery = repository.mastery_state("lo_svd_definition")
        item_states = {
            question: repository.practice_item_state(f"pi_exam_q{question}")
            for question in ("1", "2", "3")
        }
        facets = {
            (state.facet_id, state.practice_item_id): (state.recall_mean, state.independent_evidence_mass)
            for state in repository.facet_recall_states("lo_svd_definition")
        }
        return mastery, item_states, facets

    before = snapshot()
    rebuild_derived_state(loaded, repository, learning_object_ids=["lo_svd_definition"])
    after = snapshot()

    assert after[0].logit_mean == pytest.approx(before[0].logit_mean)
    assert after[0].logit_variance == pytest.approx(before[0].logit_variance)
    assert after[0].evidence_count == before[0].evidence_count
    for question in ("1", "2", "3"):
        assert after[1][question].due_at == before[1][question].due_at
        assert after[1][question].stability == pytest.approx(before[1][question].stability)
        assert after[1][question].difficulty == pytest.approx(before[1][question].difficulty)
    assert set(after[2]) == set(before[2])
    for key, (mean, mass) in before[2].items():
        assert after[2][key][0] == pytest.approx(mean)
        assert after[2][key][1] == pytest.approx(mass)


def test_seeded_exam_interleaves_before_later_live_attempt(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)
    # Live attempt first (recorded at NOW = 2026-05-19), then seed an exam
    # dated 2026-05-01: after the rebuild, replay must order the exam evidence
    # *before* the live attempt.
    live = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_exam_q1", learner_answer_md="live answer"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=FrozenClock(LIVE_NOW),
    )

    result = seed_exam_attempts(loaded, repository, outcomes=_outcomes())

    assert result.seeded_count == 3
    attempts = repository.list_attempts_by_learning_object("lo_svd_definition")
    assert [attempt["attempt_type"] for attempt in attempts] == [
        EXAM_ATTEMPT_TYPE,
        EXAM_ATTEMPT_TYPE,
        EXAM_ATTEMPT_TYPE,
        "independent_attempt",
    ]
    assert attempts[-1]["id"] == live.attempt_id
    # Replay finished on the live attempt, so derived mastery reflects the
    # correct time order (last evidence at the live attempt's timestamp).
    mastery = repository.mastery_state("lo_svd_definition")
    assert mastery.evidence_count == 4
    assert mastery.last_evidence_at == "2026-05-19T12:00:00Z"
    # The live item's FSRS state was replayed with the exam attempt as its
    # first review (elapsed days computed in order, not from insertion order).
    item_state = repository.practice_item_state("pi_exam_q1")
    assert item_state.last_attempt_at == "2026-05-19T12:00:00Z"


def test_exam_date_required_when_absent_everywhere():
    with pytest.raises(ExamSeedingError, match="exam date is required"):
        parse_exam_outcomes({"outcomes": {"1": 1.0}})


def test_parse_accepts_flat_mapping_and_date_override():
    parsed = parse_exam_outcomes({"1": 0.25, "2": {"score": 1.0}}, exam_date_override=EXAM_DATE)
    assert parsed.exam_date.isoformat() == EXAM_DATE
    assert parsed.outcomes["1"].score == pytest.approx(0.25)
    assert parsed.outcomes["2"].score == pytest.approx(1.0)


def test_subject_scoping_excludes_other_subjects(tmp_path):
    _vault_root, loaded, repository = _exam_vault(tmp_path)
    assert find_exam_items(loaded, subject="linear-algebra")
    assert find_exam_items(loaded, subject="another-subject") == {}


def test_migration_018_allows_exam_evidence_on_existing_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 17:
            shutil.copy2(migration.path, old_migrations / migration.path.name)
    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_live", attempt_type="independent_attempt", session_id="sess1")
        connection.commit()

    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_exam", attempt_type=EXAM_ATTEMPT_TYPE)
        connection.commit()
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        existing = connection.execute(
            "SELECT attempt_type, session_id FROM practice_attempts WHERE id = ?",
            ("attempt_live",),
        ).fetchone()
        indexes = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'practice_attempts'"
            )
        }
    assert existing["attempt_type"] == "independent_attempt"
    assert existing["session_id"] == "sess1"
    assert {"idx_attempts_lo_time", "idx_attempts_item_time"} <= indexes


def test_ingest_exam_instructions_reach_context_and_tags_apply(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    html = tmp_path / "exam.html"
    text = " ".join(
        [
            "Question 1: define the singular value decomposition of a matrix.",
            "Question 2: explain what the singular values represent geometrically.",
            "The exam covers factorization structure and interpretation of factors.",
        ]
        * 5
    )
    html.write_text(
        f"<html><head><title>LA practice exam</title></head>"
        f"<body><h1>Practice exam</h1><p>{text}</p></body></html>",
        encoding="utf-8",
    )
    client = _FakeExamCanonicalClient()

    result = ingest_canonical_source(
        vault_root,
        str(html),
        client,
        subject_id="linear-algebra",
        instructions=exam_ingest_instructions("Focus on chapter 2."),
        purpose="exam_ingest",
        clock=FrozenClock(NOW),
    )

    context = client.calls[0]
    assert "one practice_item per exam question" in context.instructions
    assert "exam_q:<n>" in context.instructions
    assert "Focus on chapter 2." in context.instructions
    repository = Repository(vault_root / "state.sqlite")
    batch = repository.proposal_batch_for_agent_run(result.agent_run_id)
    assert batch["purpose"] == "exam_ingest"
    assert result.auto_applied_count == 2
    loaded = load_vault(vault_root)
    item = loaded.practice_items["pi_exam_ingested_q1_001"]
    assert "exam_q:1" in item.tags
    assert "exam_question" in item.tags
    assert find_exam_items(loaded)["1"].id == "pi_exam_ingested_q1_001"


class _FakeExamCanonicalClient(StructuredClientFake):
    provider_name = "codex"
    provider_type = "codex_sdk"
    model = None

    def __init__(self):
        self.calls: list[CanonicalIngestContext] = []

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        self.calls.append(context)
        source_ref_id = context.canonical_source["id"]
        locator = context.chunks[0].locator
        return AuthoringProposal.model_validate(
            {
                "summary": "Exam ingest proposal.",
                "source_refs": [
                    {
                        "ref_type": "canonical_source",
                        "ref_id": source_ref_id,
                        "path": context.canonical_source["path"],
                        "locator": locator,
                    }
                ],
                "items": [
                    {
                        "client_item_id": "lo_exam_ingested_svd",
                        "item_type": "learning_object",
                        "operation": "create",
                        "proposed_entity_id": "lo_exam_ingested_svd",
                        "source_ref_ids": [source_ref_id],
                        "rationale": "Exam question targets the SVD definition.",
                        "review_route": "auto_apply",
                        "payload": {
                            "title": "Exam-ingested SVD definition",
                            "subjects": [context.target_subject],
                            "concept_id": "singular_value_decomposition",
                            "knowledge_type": "definition",
                            "summary": "SVD factors a matrix into orthogonal factors and singular values.",
                        },
                    },
                    {
                        "client_item_id": "pi_exam_ingested_q1",
                        "item_type": "practice_item",
                        "operation": "create",
                        "proposed_entity_id": "pi_exam_ingested_q1_001",
                        "source_ref_ids": [source_ref_id],
                        "rationale": "Exam question 1 as a practice item.",
                        "review_route": "auto_apply",
                        "payload": {
                            "learning_object_id": "lo_exam_ingested_svd",
                            "subjects": None,
                            "practice_mode": "constructed_response",
                            "attempt_types_allowed": ["independent_attempt", "dont_know"],
                            "prompt": "Define the singular value decomposition.",
                            "expected_answer": "A = U Sigma V^T with orthogonal U, V.",
                            "evidence_facets": ["recall"],
                            "evidence_weights": {"recall": 1.0},
                            "tags": ["exam_question", "exam_q:1"],
                            "grading_rubric": {
                                "max_points": 4,
                                "criteria": [
                                    {"id": "correctness", "points": 4, "description": "States the factorization."}
                                ],
                                "fatal_errors": [],
                            },
                        },
                    },
                ],
            }
        )

    def run_authoring_proposal(self, context):  # pragma: no cover - unused
        raise NotImplementedError

    def run_grading_proposal(self, context):  # pragma: no cover - unused
        raise NotImplementedError


def _insert_attempt(connection, *, attempt_id: str, attempt_type: str, session_id: str | None = None) -> None:
    connection.execute(
        """
        INSERT INTO practice_attempts(
          id, practice_item_id, learning_object_id, subject, concept, practice_mode,
          attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
          rubric_score, correctness, confidence, latency_seconds, hints_used,
          error_type, grader_confidence, manual_review, manual_review_reason,
          created_at, updated_at, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            session_id,
        ),
    )
