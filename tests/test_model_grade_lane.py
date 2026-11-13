"""The model-grade observation lane on every vault version that opens.

An AI or Codex grade feeds the mastery update the grade channel's
interpretation variance as extra measurement noise; a self or deterministic
grade does not. It holds on the version ``learnloop init`` writes.
"""

from __future__ import annotations

from learnloop.algorithm_versions import P0_PROJECTION_VERSIONS
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CONTROL_LO_ID = "lo_svd_uniqueness"
CONTROL_ITEM_ID = "pi_svd_unique_001"


def _init_version_vault(tmp_path, name: str):
    # The basic vault is at the tag a new vault is given.
    paths = create_basic_vault(tmp_path / name / "vault")
    assert ALGORITHM_VERSION in P0_PROJECTION_VERSIONS
    return paths


def _apply_grade(vault, repository, practice_item_id: str, grading_source: str):
    """Apply one 3-of-4 grade on ``practice_item_id`` under ``grading_source``."""

    attempt_id = new_ulid()
    grade = ResolvedGrade(
        rubric_score=3,
        criterion_points={"correctness": 3.0},
        evidence_rows=[
            {
                "id": new_ulid(),
                "criterion_id": "correctness",
                "points_awarded": 3.0,
                "evidence": "Names the factors but not their shapes.",
                "notes": None,
                "agent_run_id": None,
                "local_grader_id": None,
                "grader_tier": 3,
                "learner_confidence": None,
                "created_at": NOW_ISO,
            }
        ],
        error_attributions=[],
        grader_confidence=0.9,
        confidence=None,
        manual_review_reason=None,
    )
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=practice_item_id,
                learner_answer_md="U, Sigma and V transpose.",
            ),
            attempt_id=attempt_id,
            grade=grade,
            grading_source=grading_source,
        ),
        clock=FrozenClock(NOW),
    )


def test_ai_graded_practice_takes_the_soft_score_lane_on_the_init_version(tmp_path):
    lanes = {}
    for grading_source in ("self", "ai"):
        paths = _init_version_vault(tmp_path, grading_source)
        repository = Repository(paths.sqlite_path)
        _apply_grade(load_vault(paths.root), repository, ITEM_ID, grading_source)
        lanes[grading_source] = repository.mastery_state(LO_ID)

    # Same grade: the model lane widens the measurement noise by the grade
    # channel's interpretation variance, so it removes less variance and moves
    # the mean less than the self lane.
    assert lanes["ai"].logit_variance > lanes["self"].logit_variance
    assert 0 < abs(lanes["ai"].logit_mean) < abs(lanes["self"].logit_mean)


def _add_control_learning_object(paths) -> None:
    write_yaml(
        paths.learning_object_path("linear-algebra", CONTROL_LO_ID),
        {
            "schema_version": 1,
            "id": CONTROL_LO_ID,
            "title": "SVD uniqueness",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "Which parts of an SVD are unique.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    upsert_practice_item(
        paths.root,
        {
            "id": CONTROL_ITEM_ID,
            "learning_object_id": CONTROL_LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["uniqueness"],
            "evidence_weights": {"uniqueness": 1.0},
            "prompt": "Which parts of an SVD are unique?",
            "expected_answer": "The singular values.",
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


def test_replay_reenters_each_attempts_stored_lane(tmp_path):
    """Replay reads each attempt's stored grading source, so a model grade and
    a self grade side by side rebuild to what their live writes left."""

    paths = _init_version_vault(tmp_path, "rebuild")
    _add_control_learning_object(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _apply_grade(vault, repository, ITEM_ID, "ai")
    _apply_grade(vault, repository, CONTROL_ITEM_ID, "self")
    assert shadow_rebuild(vault).learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
