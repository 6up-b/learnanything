"""What other test files use from ``tests/test_diagnostic_probe_single_use.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault


CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
DIAG_ITEM = "pi_diag_transposed_factor"


def _add_diagnostic_item(paths, item_id: str = DIAG_ITEM) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Which SVD factor is transposed in the product?",
            "expected_answer": "V",
            "difficulty": 0.5,
            "tags": [],
            "hints": [],
            "hint_policy": {
                "max_useful_hints": 0,
                "fsrs_rating_cap_by_hint": {},
                "mastery_alpha_dampening_by_hint": {},
            },
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "correctness",
                        "points": 4,
                        "description": "Correct selection.",
                    }
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _seed_mastery(repository: Repository) -> None:
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )


def _vault(tmp_path, *, item_ids: tuple[str, ...] = (DIAG_ITEM,)):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    for item_id in item_ids:
        _add_diagnostic_item(paths, item_id)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    _seed_mastery(repository)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository


def _diagnostic_attempt(
    vault,
    repository,
    *,
    attempt_id: str = "att_diag_single_use",
    item_id: str = DIAG_ITEM,
):
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U",
                attempt_type="diagnostic_probe",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points={"correctness": 2},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 2.0,
                        "evidence": "Named a factor but not the transposed one.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=CLOCK,
    )
