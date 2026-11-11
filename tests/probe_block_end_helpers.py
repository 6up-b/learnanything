"""What other test files use from ``tests/test_probe_block_end.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault


LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
ITEM_2 = "pi_svd_define_002"
CLOCK = FrozenClock(NOW)
MISCONCEPTION_STATEMENT = "The SVD is the same thing as the eigendecomposition."


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    upsert_practice_item(
        vault_root,
        {
            "id": ITEM_2,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {ITEM_2}.",
            "expected_answer": "A factorization into U, Sigma, and V transpose.",
            "surface_family": "fresh_surface",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_ID, ITEM_2))
    return loaded, repository


def _grade(score: int, *, error_attributions=None) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=score,
        criterion_points={"correctness": float(score)},
        evidence_rows=[],
        error_attributions=error_attributions or [],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _submit(loaded, repository, *, item_id, presentation_id, score=4, error_attributions=None):
    return apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation_id,
            ),
            attempt_id=new_ulid(),
            grade=_grade(score, error_attributions=error_attributions),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


def _commit(loaded, repository, episode, *, item_id):
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next(entry for entry in instruments if entry.item.id == item_id)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    return presentation


def _misconception_attribution() -> GradeAttribution:
    return GradeAttribution(
        error_type="conceptual_slip",
        severity=0.9,
        is_misconception=True,
        misconception_statement=MISCONCEPTION_STATEMENT,
    )
