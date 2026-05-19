from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.codex.client import GradingContext
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import CriterionEvidence, ErrorAttribution, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_attempt_with_codex_fallback, complete_codex_graded_attempt
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_codex_graded_attempt_uses_same_update_path_with_tier_three_evidence(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_codex_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        GradingProposal(
            attempt_id="attempt_codex_1",
            practice_item_id="pi_svd_define_001",
            rubric_score=3,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="correctness",
                    points_awarded=3,
                    evidence="Correct but incomplete.",
                )
            ],
            error_attributions=[
                ErrorAttribution(
                    error_type="conceptual_slip",
                    severity=0.6,
                    evidence="Missing one key distinction.",
                    is_misconception=True,
                )
            ],
            grader_confidence=0.9,
        ),
        agent_run_id="agent_run_grade_1",
        clock=clock,
    )

    attempt = repository.fetch_practice_attempt("attempt_codex_1")
    evidence = repository.fetch_grading_evidence("attempt_codex_1")
    errors = repository.active_errors_by_learning_object("lo_svd_definition")
    surprise = repository.latest_attempt_surprise("attempt_codex_1")

    assert result.attempt_id == "attempt_codex_1"
    assert result.grading_source == "codex"
    assert result.agent_run_id == "agent_run_grade_1"
    assert attempt["rubric_score"] == 3
    assert attempt["confidence"] is None
    assert evidence[0].grader_tier == 3
    assert evidence[0].agent_run_id == "agent_run_grade_1"
    assert errors[0].error_type == "conceptual_slip"
    assert errors[0].severity == 0.6
    assert surprise["observed_joint_bucket"]["error_type"] == "conceptual_slip"
    assert repository.practice_item_state("pi_svd_define_001").last_attempt_at is not None
    assert repository.mastery_state("lo_svd_definition").evidence_count == 1


def test_attempt_orchestration_uses_codex_when_runtime_ready(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    client = _FakeCodexClient()

    result = complete_attempt_with_codex_fallback(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
        ),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        runtime=_ready_runtime(),
        codex_client=client,
        clock=clock,
    )
    agent_run = repository.find_record(result.agent_run_id)[1]

    assert result.grading_source == "codex"
    assert result.fallback_reason is None
    assert result.rubric_score == 4
    assert client.context is not None
    assert client.context.attempt_id == result.attempt_id
    assert agent_run["status"] == "completed"


def test_attempt_orchestration_falls_back_when_runtime_not_ready(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_attempt_with_codex_fallback(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
        ),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=4),
        runtime=CodexRuntimeReport(
            status="codex_missing",
            checkout_path="missing",
            configured_revision="abc",
        ),
        codex_client=_FakeCodexClient(),
        clock=clock,
    )
    evidence = repository.fetch_grading_evidence(result.attempt_id)

    assert result.grading_source == "self"
    assert result.fallback_reason == "codex_missing"
    assert result.agent_run_id is None
    assert evidence[0].grader_tier == 1


def test_attempt_orchestration_falls_back_and_marks_agent_run_failed(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_attempt_with_codex_fallback(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
        ),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=4),
        runtime=_ready_runtime(),
        codex_client=_FakeCodexClient(invalid=True),
        clock=clock,
    )
    agent_run = repository.find_record(result.agent_run_id)[1]
    evidence = repository.fetch_grading_evidence(result.attempt_id)

    assert result.grading_source == "self"
    assert result.fallback_reason.startswith("codex_failed:")
    assert agent_run["status"] == "failed"
    assert evidence[0].grader_tier == 1


class _FakeCodexClient:
    def __init__(self, *, invalid: bool = False):
        self.invalid = invalid
        self.context: GradingContext | None = None

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        self.context = context
        criterion_id = "missing" if self.invalid else "correctness"
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id=criterion_id,
                    points_awarded=4,
                    evidence="Correct answer.",
                )
            ],
            grader_confidence=0.95,
        )


def _ready_runtime() -> CodexRuntimeReport:
    return CodexRuntimeReport(
        status="ready",
        checkout_path="codex",
        configured_revision="abc",
        actual_revision="abc",
    )
