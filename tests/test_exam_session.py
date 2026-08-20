from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.attempts.attempts import GradeAttribution, ResolvedGrade
from learnloop.goals.exam_pool import reserve_exam_pool, reserved_item_ids
from learnloop.goals.exam_session import (
    ExamSessionError,
    exam_availability,
    finish_exam,
    queue_exam_answer,
    record_exam_answer,
    start_exam,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
GOAL_ID = "goal_linear_algebra_ml"


def _add_item(root, item_id, *, facets, difficulty=0.5):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": difficulty,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def _vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_exam_a", facets=["recall"], difficulty=0.2)
    _add_item(vault_root, "pi_exam_b", facets=["apply"], difficulty=0.6)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


def _grade(rubric_score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points={"correctness": float(rubric_score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _reserved_and_started(tmp_path):
    vault, _paths, repository = _vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    return vault, repository, session


def test_start_freezes_predictions_before_any_evidence(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    assert session["status"] == "in_progress"
    assert len(session["predictions"]) == 2
    predictions = {row["practice_item_id"]: row for row in session["predictions"]}
    # Predictions frozen at start: a value per pooled item, with facet snapshot.
    for row in predictions.values():
        assert 0.0 <= row["predicted_correctness"] <= 1.0
        assert isinstance(row["facet_projection"], dict)

    # No exam_attempt evidence exists yet (freeze happened BEFORE grading).
    frozen = repository.exam_predictions(session["session_id"])
    assert len(frozen) == 2
    assert repository.attempted_practice_item_ids() == set()


def test_start_is_idempotent(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    again = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    assert again["session_id"] == session["session_id"]
    assert again["already_started"] is True
    # No duplicate predictions were frozen.
    assert len(repository.exam_predictions(session["session_id"])) == 2


def test_ungraded_answer_is_durable_and_blocks_finish(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]

    queued = queue_exam_answer(
        vault,
        repository,
        session_id,
        "pi_exam_a",
        answer_md="A response waiting for its grader.",
    )

    assert queued["graded"] is False
    stored = repository.exam_answer(session_id, "pi_exam_a")
    assert stored is not None
    assert stored["answer_md"] == "A response waiting for its grader."
    assert stored["grade"] is None
    with pytest.raises(ExamSessionError, match="grading is still pending"):
        finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))


def test_exam_answer_submission_is_final_but_idempotent(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    queue_exam_answer(
        vault, repository, session_id, "pi_exam_a", answer_md="Final answer."
    )

    repeated = queue_exam_answer(
        vault, repository, session_id, "pi_exam_a", answer_md="Final answer."
    )
    assert repeated["already_submitted"] is True
    with pytest.raises(ExamSessionError, match="cannot be replaced"):
        queue_exam_answer(
            vault, repository, session_id, "pi_exam_a", answer_md="Changed answer."
        )


def test_finish_lands_exam_attempt_evidence_with_full_mass(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    record_exam_answer(vault, repository, session_id, "pi_exam_b", answer_md="B", resolved_grade=_grade(2))

    report = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert report["answered_count"] == 2
    assert report["overall_score"] == pytest.approx((1.0 + 0.5) / 2)

    # Both answers became exam_attempt attempts.
    attempts = {
        attempt["attempt_type"]
        for attempt in repository.list_attempts_by_learning_object(LO_ID)
    }
    assert "exam_attempt" in attempts
    for answer in repository.exam_answers(session_id):
        assert answer["attempt_id"] is not None
        applied = repository.fetch_practice_attempt(answer["attempt_id"])
        assert applied["attempt_type"] == "exam_attempt"

    # Full evidence mass: exam_attempt carries mass 1.0 in the config.
    from learnloop.attempts.evidence import attempt_evidence_mass

    assert attempt_evidence_mass("exam_attempt", vault.config.evidence) == 1.0


def test_finish_is_idempotent_by_session_id(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))

    first = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    attempts_after_first = len(repository.list_attempts_by_learning_object(LO_ID))
    second = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    assert second == first
    # No new attempts applied on the second finish.
    assert len(repository.list_attempts_by_learning_object(LO_ID)) == attempts_after_first


def test_finish_releases_the_exam_pool(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    assert reserved_item_ids(repository)
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    # Pool released: examined items rejoin practice.
    assert reserved_item_ids(repository) == set()


def test_report_has_per_facet_predicted_vs_actual(tmp_path):
    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    record_exam_answer(vault, repository, session_id, "pi_exam_b", answer_md="B", resolved_grade=_grade(0))
    report = finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    facet_ids = {facet["facet_id"] for facet in report["facets"]}
    assert {"recall", "apply"} <= facet_ids
    for facet in report["facets"]:
        assert "projected_recall" in facet
        assert "actual_recall" in facet
    assert report["brier"] is not None


def test_availability_open_ended_goal_never_in_window_but_startable(tmp_path):
    vault, _paths, repository = _vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    availability = exam_availability(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    assert availability["in_window"] is False
    assert availability["days_until_due"] is None
    assert availability["pool_item_count"] == 2
    assert availability["existing_session_id"] is None


def test_availability_in_window_near_due_date(tmp_path):
    from datetime import timedelta

    vault, _paths, repository = _vault(tmp_path)
    vault.goals[0].due_at = (NOW + timedelta(days=3)).isoformat()
    availability = exam_availability(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    assert availability["in_window"] is True
    assert availability["past_due_grace"] is False
    assert availability["days_until_due"] == pytest.approx(3.0, abs=0.01)


def test_exam_answers_certify_facet_evidence_on_canonical_vault(tmp_path):
    """A passed exam must leave real certification credit behind (regression).

    The P0.2 grade interpretation used to be dual-written under a synthetic
    ``exam::<session>::<item>`` attempt id while the answer was applied under a
    fresh ULID. The canonical projection joins interpretations to attempts by
    that id, so it found none, ``build_effective_observation`` fell to its
    missing-interpretation branch (``effective_mass`` 0.0), and a 100% exam
    produced zero facet mass and zero certification credit — every scope facet
    stayed ``unexamined`` no matter how well the learner did.
    """

    from learnloop.db.repositories import Repository
    from learnloop.substrate.state_sync import sync_vault_state
    from tests.helpers import create_basic_vault, set_algorithm_version

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    set_algorithm_version(paths, "mvp-0.8")
    _add_item(vault_root, "pi_exam_a", facets=["recall"], difficulty=0.5)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    reserve_exam_pool(vault, repository, vault.goals[0], item_count=1, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    item_id = session["item_order"][0]
    graded = _grade(4)
    graded.evidence_rows.append(
        {
            "id": "ge_exam_regression",
            "criterion_id": "correctness",
            "points_awarded": 4.0,
            "evidence": "Fully correct.",
            "grader_tier": 3,
            "created_at": NOW_ISO,
        }
    )
    record_exam_answer(
        vault,
        repository,
        session["session_id"],
        item_id,
        answer_md="A full and correct exam answer.",
        resolved_grade=graded,
        clock=FrozenClock(NOW),
    )
    finish_exam(vault, repository, session["session_id"], clock=FrozenClock(NOW))

    attempt_id = repository.exam_answers(session["session_id"])[0]["attempt_id"]
    observation = repository.observation_by_attempt(attempt_id)
    assert observation is not None, "interpretation must key on the applied attempt id"

    cells = repository.facet_capability_evidence_all()
    assert cells, "a graded exam answer must write facet-capability evidence"
    assert any(cell.direct_positive_mass > 0 for cell in cells)
    assert any(cell.certification_credit > 0 for cell in cells)
