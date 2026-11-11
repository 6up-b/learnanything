"""What other test files use from ``tests/test_reader_recap_review_r2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.reader import reader_sessions as RS
from learnloop.reader import recap as RC
from learnloop.reader import workbench as WB
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO
from tests.recap_fixtures import EXT, at, problem, visit
from tests.reader_dialogue_helpers import _setup


def _self_graded(vault, repository, item_id: str, minutes: float, criterion: str, points: float, *,
                 hints: int = 0) -> str:
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.",
                     attempt_type="hinted_attempt" if hints else "independent_attempt", hints_used=hints),
        SelfGradeInput(criterion_points={criterion: points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )
    return str(result.attempt_id)


#: An item on ``compute`` whose one criterion also consumes ``recall`` (supporting).
EMBEDDED_ITEM = "pi_compute_with_recall"
#: An item whose one criterion targets ``recall`` directly (an authored target).
RECALL_ITEM = "pi_recall_targeted"


def _write_item(vault, item_id: str, targets: list[dict]) -> None:
    write_yaml(VaultPaths(vault.root, vault.config).practice_item_path("linear-algebra", item_id), {
        "schema_version": 1, "id": item_id, "learning_object_id": "lo_svd_definition", "subjects": None,
        "practice_mode": "constructed_response",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": f"Prompt for {item_id}.", "expected_answer": "U Sigma V^T.", "difficulty": 0.5, "tags": [],
        "grading_rubric": {"max_points": 4, "fatal_errors": [], "criteria": [{
            "id": "c1", "points": 4, "description": "Answers it.", "targets": targets,
        }]},
        "provenance": {"origin": "human", "source_refs": []}, "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })


def _embedded_world(tmp_path):
    vault, repo = _setup(tmp_path)
    _write_item(vault, EMBEDDED_ITEM, [{"facet": "compute", "capability": "procedure_execution", "role": "primary"},
                                       {"facet": "recall", "capability": "recall", "role": "supporting"}])
    _write_item(vault, RECALL_ITEM, [{"facet": "recall", "capability": "recall", "role": "primary"}])
    return load_vault(vault.root), repo


def _assisted_session(vault, repo):
    """A session whose book-visible, hinted problem on ``recall`` leaves a claim."""

    visit(repo, "v1", 0, 40)
    row = problem(repo, 2, steps=1, book=True)
    attempt = _self_graded(vault, repo, "pi_svd_define_001", 20, "correctness", 4, hints=1)
    WB.mark_submitted(repo, row["id"], attempt_id=attempt, practice_session_id="ps_1", clock=at(20))
    return RS.sessions_for_source(repo, EXT)[0]


def _claimed(vault, repo, session) -> list[str]:
    summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=NOW + timedelta(minutes=300))
    return [claim["facet_id"] for claim in summary["claims_needing_independent_check"]]
