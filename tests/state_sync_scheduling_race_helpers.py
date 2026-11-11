"""What other test files use from ``tests/test_state_sync_scheduling_race.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from learnloop.attempts.attempts import AttemptDraft
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository

from tests.helpers import NOW


SUBJECT = "linear-algebra"
ATTEMPT_CLOCK = FrozenClock(NOW + timedelta(hours=1))
PROBE = "pi_diag_transposed_factor"
PROBE_LO = "lo_svd_definition"


def _add_diagnostic_probe(paths, prompt: str = "Which SVD factor is transposed in the product?") -> None:
    from learnloop.vault.yaml_io import write_yaml

    from tests.helpers import NOW_ISO

    write_yaml(
        paths.practice_item_path(SUBJECT, PROBE),
        {
            "schema_version": 1,
            "id": PROBE,
            "learning_object_id": PROBE_LO,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": prompt,
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
                    {"id": "correctness", "points": 4, "description": "Correct selection."}
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _commit_probe_attempt(vault, sqlite_path: Path) -> None:
    """A real diagnostic administration through its own Repository: it retires the probe."""

    from learnloop.attempts.attempts import ApplyAttemptInput, ResolvedGrade, apply_attempt

    from tests.helpers import NOW_ISO

    apply_attempt(
        vault,
        Repository(sqlite_path),
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=PROBE,
                learner_answer_md="U",
                attempt_type="diagnostic_probe",
            ),
            attempt_id="att_probe_after_decision_read",
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points={"correctness": 2},
                evidence_rows=[
                    {
                        "id": "ge_att_probe_after_decision_read",
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
        clock=ATTEMPT_CLOCK,
    )
