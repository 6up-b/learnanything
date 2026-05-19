from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.followups import evaluate_negative_surprise_followup
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _add_followup_item(vault_root) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_svd_define_002",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Follow-up: define SVD again.",
            "expected_answer": "x",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "c"}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )


def _surprising_attempt(vault_root, repository):
    loaded = load_vault(vault_root)
    # Seed a confident prior so a wrong answer produces strong negative surprise.
    repository.upsert_mastery_state(
        MasteryState("lo_svd_definition", 2.0, 1.0, 3, NOW_ISO, "mvp-0.1", NOW_ISO)
    )
    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=4, error_type="conceptual_slip"),
        clock=FrozenClock(NOW),
    )
    return loaded, result


def _evaluate(loaded, repository, result, *, available_minutes=30):
    return evaluate_negative_surprise_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
        available_minutes=available_minutes,
    )


def test_negative_surprise_inserts_followup_when_item_exists(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    assert result.surprise_direction == "negative"

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_svd_define_002"
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["triggered_actions"] == ["negative_surprise_followup:pi_svd_define_002"]
    assert surprise["suppressed_actions"] == []


def test_negative_surprise_suppressed_when_no_suitable_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is False
    assert decision.reason == "negative_surprise_followup:no_suitable_item"
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["suppressed_actions"] == ["negative_surprise_followup:no_suitable_item"]


def test_negative_surprise_suppressed_when_out_of_time(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = _evaluate(loaded, repository, result, available_minutes=0)

    assert decision.triggered is False
    assert decision.reason == "negative_surprise_followup:no_time"
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["suppressed_actions"] == ["negative_surprise_followup:no_time"]


def test_followup_gate_skips_non_negative_surprise(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = evaluate_negative_surprise_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="none",
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        available_minutes=30,
    )

    assert decision.triggered is False
    assert decision.reason == "not_negative"
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["triggered_actions"] == []
    assert surprise["suppressed_actions"] == []
