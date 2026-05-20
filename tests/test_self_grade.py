from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault


def _attempt(tmp_path, *, points, confidence, attempt_type="independent_attempt", fatal_errors=None):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x", attempt_type=attempt_type),
        SelfGradeInput(criterion_points=points, confidence=confidence, fatal_errors=fatal_errors),
        clock=FrozenClock(NOW),
    )
    return repository, result


def test_self_grade_writes_tier_one_evidence(tmp_path):
    repository, result = _attempt(tmp_path, points={"correctness": 4}, confidence=5)

    assert result.rubric_score == 4
    assert result.grader_confidence == 1.0
    evidence = repository.fetch_grading_evidence(result.attempt_id)
    assert evidence
    assert all(row.grader_tier == 1 for row in evidence)
    assert all(row.local_grader_id == "self" for row in evidence)
    assert all(row.agent_run_id is None for row in evidence)


def test_confidence_maps_to_grader_confidence(tmp_path):
    _, result = _attempt(tmp_path, points={"correctness": 2}, confidence=3)
    assert result.grader_confidence == 0.6


def test_fatal_error_caps_score(tmp_path):
    _, result = _attempt(
        tmp_path, points={"correctness": 4}, confidence=5, fatal_errors=["conceptual_slip"]
    )
    # conceptual_slip caps the grade at 1 in the basic-vault rubric.
    assert result.rubric_score == 1


def test_dont_know_forces_zero(tmp_path):
    _, result = _attempt(tmp_path, points={"correctness": 4}, confidence=3, attempt_type="dont_know")
    assert result.rubric_score == 0


def test_low_confidence_flags_manual_review(tmp_path):
    _, result = _attempt(tmp_path, points={"correctness": 1}, confidence=1)
    assert result.manual_review_reason == "low_self_confidence"


def test_self_grade_uses_default_rubric_when_inline_rubric_is_omitted(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_item_path)
    practice_item.pop("grading_rubric")
    write_yaml(practice_item_path, practice_item)
    write_yaml(
        paths.root / "rubrics" / "short_answer.yaml",
        {
            "schema_version": 1,
            "id": "rubric_short_answer_default",
            "applies_to": {"practice_mode": "short_answer"},
            "rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 3, "description": "States the core idea."},
                    {"id": "clarity", "points": 1, "description": "Is understandable."},
                ],
                "fatal_errors": [],
            },
        },
    )
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 3, "clarity": 1}, confidence=5),
        clock=FrozenClock(NOW),
    )

    assert result.rubric_score == 4
    assert result.correctness == 1.0
