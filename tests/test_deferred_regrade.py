from __future__ import annotations

import sqlite3

from learnloop.clock import FrozenClock
from learnloop.codex.client import GradingContext
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import CriterionEvidence, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.regrade import run_deferred_regrades
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_deferred_regrade_supersedes_self_grade_and_updates_mastery(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )
    before_mastery = repository.mastery_state("lo_svd_definition")

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    all_evidence = repository.fetch_grading_evidence(attempt.attempt_id, include_superseded=True)
    current_evidence = repository.fetch_grading_evidence(attempt.attempt_id)
    regraded_attempt = repository.fetch_practice_attempt(attempt.attempt_id)
    after_mastery = repository.mastery_state("lo_svd_definition")

    assert result.as_dict() == {"attempted": 1, "regraded": 1, "failed": 0, "skipped_reason": None}
    assert len(all_evidence) == 2
    assert all_evidence[0].grader_tier == 1
    assert all_evidence[0].superseded_at is not None
    assert all_evidence[1].grader_tier == 3
    assert current_evidence[0].grader_tier == 3
    assert regraded_attempt["rubric_score"] == 4
    assert after_mastery.evidence_count == before_mastery.evidence_count + 1


def test_deferred_regrade_records_disagreement_event(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=clock,
    )

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    with sqlite3.connect(paths.sqlite_path) as connection:
        event = connection.execute(
            """
            SELECT event_type, entity_type, entity_id, summary
            FROM content_events
            WHERE event_type = 'regrade_disagreement'
            """
        ).fetchone()

    assert event[0] == "regrade_disagreement"
    assert event[1:] == (
        "practice_item",
        "pi_svd_define_001",
        f"Deferred regrade changed rubric_score from 0 to 4; old evidence {repository.fetch_grading_evidence(attempt.attempt_id, include_superseded=True)[0].id}; new evidence {repository.fetch_grading_evidence(attempt.attempt_id)[0].id}.",
    )


def test_deferred_regrade_skips_when_runtime_not_ready(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=CodexRuntimeReport(status="codex_missing", checkout_path="missing", configured_revision="abc"),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    assert result.as_dict() == {"attempted": 0, "regraded": 0, "failed": 0, "skipped_reason": "codex_missing"}


def test_deferred_regrade_failure_leaves_self_grade_current_and_agent_failed(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_InvalidRegradeClient(),
        clock=clock,
    )
    evidence = repository.fetch_grading_evidence(attempt.attempt_id)
    with sqlite3.connect(paths.sqlite_path) as connection:
        agent_status = connection.execute("SELECT status FROM agent_runs WHERE purpose = 'grading_regrade'").fetchone()[0]

    assert result.as_dict() == {"attempted": 1, "regraded": 0, "failed": 1, "skipped_reason": None}
    assert evidence[0].grader_tier == 1
    assert agent_status == "failed"


class _RegradeClient:
    def __init__(self, *, score: int, points: float):
        self.score = score
        self.points = points

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=self.score,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="correctness",
                    points_awarded=self.points,
                    evidence="Codex regrade evidence.",
                )
            ],
            grader_confidence=0.9,
        )


class _InvalidRegradeClient:
    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="missing",
                    points_awarded=4,
                    evidence="Invalid criterion.",
                )
            ],
            grader_confidence=0.9,
        )


def _ready_runtime() -> CodexRuntimeReport:
    return CodexRuntimeReport(
        status="ready",
        checkout_path="codex",
        configured_revision="abc",
        actual_revision="abc",
    )
