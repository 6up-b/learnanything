from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeErrorAttribution,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.handlers.serializers import practice_item_detail

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


def test_dont_know_attributes_recall_failure(tmp_path):
    # Spec §"Attempt-type handling": a don't-know is deterministically attributed
    # to recall_failure (score 0, no grading role) and must write an active error
    # event so it feeds surprise and cross-LO propagation downstream.
    repository, result = _attempt(tmp_path, points={"correctness": 4}, confidence=3, attempt_type="dont_know")
    assert result.rubric_score == 0
    assert result.error_event_ids
    events = repository.error_events_for_attempt(result.attempt_id)
    assert [event["error_type"] for event in events] == ["recall_failure"]
    assert all(event["status"] == "active" for event in events)


def test_dont_know_allowed_when_not_in_attempt_types(tmp_path):
    # "dont_know" is a universal escape hatch: it must bypass the per-item
    # attempt_types_allowed list (here only "open_text", as on pi_best_rank1_error)
    # and still grade deterministically to zero — never raising "not allowed".
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_item_path)
    practice_item["attempt_types_allowed"] = ["open_text"]
    write_yaml(practice_item_path, practice_item)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={}, confidence=3),
        clock=FrozenClock(NOW),
    )
    assert result.rubric_score == 0


def test_low_confidence_flags_manual_review(tmp_path):
    _, result = _attempt(tmp_path, points={"correctness": 1}, confidence=1)
    assert result.manual_review_reason == "low_self_confidence"


def test_self_grade_per_criterion_attribution_writes_error_event(tmp_path):
    # A per-criterion attribution mirrors a Codex error_attribution: it writes an
    # active error event (severity + misconception resolved from the taxonomy) and
    # records the criterion in the evidence — but, unlike a fatal error, it does
    # NOT cap the rubric score.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(
            criterion_points={"correctness": 2},
            confidence=4,
            error_attributions=[
                SelfGradeErrorAttribution(error_type="conceptual_slip", criterion_id="correctness")
            ],
        ),
        clock=FrozenClock(NOW),
    )

    assert result.rubric_score == 2  # attribution alone does not cap the score
    assert result.error_event_ids
    events = repository.error_events_for_attempt(result.attempt_id)
    assert [event["error_type"] for event in events] == ["conceptual_slip"]
    assert events[0]["severity"] >= 0.7
    assert events[0]["is_misconception"] is True
    assert "correctness" in (events[0]["repair_plan"] or {}).get("evidence", "")


def test_self_grade_attribution_rejects_unknown_criterion(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    with pytest.raises(AttemptValidationError):
        complete_self_graded_attempt(
            loaded,
            repository,
            AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
            SelfGradeInput(
                criterion_points={"correctness": 1},
                confidence=4,
                error_attributions=[
                    SelfGradeErrorAttribution(error_type="conceptual_slip", criterion_id="does_not_exist")
                ],
            ),
            clock=FrozenClock(NOW),
        )


def test_practice_item_detail_lists_candidate_error_types(tmp_path):
    # The self-grade UI reads selectable error types off the practice-item detail;
    # concept-tied types are flagged relevant so the picker can lead with them.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    detail = practice_item_detail(loaded, repository, "pi_svd_define_001")
    candidates = detail["candidateErrorTypes"]
    slip = next(candidate for candidate in candidates if candidate["id"] == "conceptual_slip")
    assert slip["relevant"] is True
    assert slip["isMisconception"] is True
    assert slip["severityDefault"] == 0.7


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
