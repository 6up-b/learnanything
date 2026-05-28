from __future__ import annotations

from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import FrozenClock
from learnloop.codex.client import GradingContext
from learnloop.codex.schemas import CriterionEvidence, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_attempt_with_ai_fallback
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_attempt_ai_flow_records_provider_model_and_ai_source(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    client = _FakeAIClient()

    result = complete_attempt_with_ai_fallback(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        runtime=AIRuntimeReport(
            status="ready",
            active_provider="deepseek_flash",
            provider_type="openai_chat",
            model="deepseek-v4-flash",
        ),
        ai_client=client,
        clock=clock,
    )
    agent_run = repository.find_record(result.agent_run_id)[1]

    assert result.grading_source == "ai"
    assert result.rubric_score == 4
    assert agent_run["provider"] == "deepseek_flash"
    assert agent_run["provider_type"] == "openai_chat"
    assert agent_run["model"] == "deepseek-v4-flash"


class _FakeAIClient:
    provider_name = "deepseek_flash"
    provider_type = "openai_chat"
    model = "deepseek-v4-flash"

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="correctness",
                    points_awarded=4,
                    evidence="Correct answer.",
                )
            ],
            grader_confidence=0.95,
        )
