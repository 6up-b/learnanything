"""Agent-run token accounting (spec_diagnostic_augmentation_v1.md §2 A7).

Migration 131 + the provider seam in `learnloop.token_usage`: `agent_runs` now
carries est_/actual_ input_/output_tokens so §3 C3's
`tokens_per_resolved_diagnostic_episode` has a numerator. The load-bearing case
is the grading path — that is the run C3 measures — so it is asserted end to end
against a stub client, not just at the repository boundary.
"""

from __future__ import annotations

import types

import pytest

from learnloop.ai.openai_chat import OpenAIChatProviderClient
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import FrozenClock
from learnloop.codex.client import CodexUnavailable, GradingContext
from learnloop.codex.schemas import CriterionEvidence, GradingProposal
from learnloop.config import AIProviderConfig
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services.agent_runs import finish_agent_run
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.token_usage import (
    TokenUsage,
    TokenUsageAccounting,
    consume_client_usage,
    usage_from_chat_response,
    usage_from_codex_turn,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault
from tests.openai_fakes import grading_json, install_fake_openai


# --- schema ----------------------------------------------------------------


def test_agent_run_token_columns_exist_and_default_to_zero(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    repository = Repository(sqlite_path)

    run_id = repository.insert_agent_run({"purpose": "grading", "started_at": NOW_ISO})

    with connect(sqlite_path) as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(agent_runs)")
        }
    assert {
        "est_input_tokens",
        "est_output_tokens",
        "actual_input_tokens",
        "actual_output_tokens",
    } <= columns

    run = repository.agent_run(run_id)
    assert run is not None
    assert run["est_input_tokens"] == 0
    assert run["est_output_tokens"] == 0
    assert run["actual_input_tokens"] == 0
    assert run["actual_output_tokens"] == 0


def test_insert_agent_run_records_estimates(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")

    run_id = repository.insert_agent_run(
        {
            "purpose": "grading",
            "started_at": NOW_ISO,
            "est_input_tokens": 4096,
            "est_output_tokens": 512,
        }
    )

    run = repository.agent_run(run_id)
    assert (run["est_input_tokens"], run["est_output_tokens"]) == (4096, 512)
    # Estimates never imply actuals; those only land at completion.
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (0, 0)


def test_complete_agent_run_records_actual_usage(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    run_id = repository.insert_agent_run({"purpose": "grading", "started_at": NOW_ISO})

    assert repository.complete_agent_run(
        run_id,
        usage=TokenUsage(input_tokens=1200, output_tokens=340, calls=2),
        clock=FrozenClock(NOW),
    )

    run = repository.agent_run(run_id)
    assert run["status"] == "completed"
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (1200, 340)


def test_complete_agent_run_without_usage_preserves_recorded_cost(tmp_path):
    # A second, redundant completion (the synthesis path can complete a run in
    # an inner frame and again in an outer handler) must not zero the cost.
    repository = Repository(tmp_path / "state.sqlite")
    run_id = repository.insert_agent_run({"purpose": "grading", "started_at": NOW_ISO})
    repository.complete_agent_run(run_id, usage=TokenUsage(500, 100, 1))

    repository.complete_agent_run(run_id, status="failed", error_message="late failure")

    run = repository.agent_run(run_id)
    assert run["status"] == "failed"
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (500, 100)


def test_finish_agent_run_without_a_client_leaves_cost_untouched(tmp_path):
    # Candidate revalidation finalizes a run a previous process already paid
    # for: no client, no usage, so nothing may be written over the recorded cost.
    repository = Repository(tmp_path / "state.sqlite")
    run_id = repository.insert_agent_run(
        {"purpose": "source_set_synthesis", "started_at": NOW_ISO}
    )
    repository.complete_agent_run(run_id, usage=TokenUsage(90_000, 12_000, 7))

    assert finish_agent_run(repository, run_id, clock=FrozenClock(NOW))
    assert finish_agent_run(repository, None) is False

    run = repository.agent_run(run_id)
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (90_000, 12_000)


def test_add_agent_run_usage_is_additive(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    run_id = repository.insert_agent_run({"purpose": "authoring", "started_at": NOW_ISO})
    repository.complete_agent_run(run_id, usage=TokenUsage(500, 100, 1))

    assert repository.add_agent_run_usage(run_id, TokenUsage(90, 10, 1))
    # An empty top-up (the common case: no repair pass ran) writes nothing.
    assert repository.add_agent_run_usage(run_id, TokenUsage()) is False

    run = repository.agent_run(run_id)
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (590, 110)


# --- the provider seam -----------------------------------------------------


def _deepseek_profile(**overrides) -> AIProviderConfig:
    settings = {
        "type": "openai_chat",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-v4-flash",
        "response_format": "json_object",
    }
    settings.update(overrides)
    return AIProviderConfig(**settings)


def _grading_context() -> GradingContext:
    return GradingContext(
        attempt_id="attempt_1",
        practice_item_id="pi_1",
        prompt="Define SVD.",
        expected_answer="U Sigma V^T.",
        learner_answer_md="U Sigma V transpose.",
        rubric={"max_points": 4, "criteria": [{"id": "correctness", "points": 4}]},
    )


def test_chat_client_accumulates_usage_across_calls_and_resets_on_consume(monkeypatch):
    # Two billed calls for one logical run: the first response is unparseable,
    # so the client pays for a repair round. Both must be counted.
    install_fake_openai(
        monkeypatch,
        "not json",
        grading_json(),
        usages=[
            {"prompt_tokens": 900, "completion_tokens": 40},
            types.SimpleNamespace(prompt_tokens=310, completion_tokens=120),
        ],
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    client.run_grading_proposal(_grading_context())
    usage = client.consume_usage()

    assert usage == TokenUsage(input_tokens=1210, output_tokens=160, calls=2)
    # Read-and-reset: the next run starts from zero rather than inheriting.
    assert client.consume_usage() == TokenUsage()


def test_chat_client_survives_a_response_with_no_usage(monkeypatch):
    install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    # calls=1 with zero tokens is the distinguishable "provider reported
    # nothing" case, not "no model call happened".
    assert client.consume_usage() == TokenUsage(input_tokens=0, output_tokens=0, calls=1)


def test_chat_client_counts_tokens_of_a_call_whose_body_is_unusable(monkeypatch):
    # An empty content string raises before the response is parsed; the tokens
    # were still billed, and a repair round is not possible.
    install_fake_openai(
        monkeypatch, "   ", usages=[{"prompt_tokens": 700, "completion_tokens": 0}]
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    with pytest.raises(CodexUnavailable):
        client.run_grading_proposal(_grading_context())

    assert client.consume_usage().input_tokens == 700


@pytest.mark.parametrize(
    "response, expected",
    [
        (types.SimpleNamespace(), (0, 0)),
        (types.SimpleNamespace(usage=None), (0, 0)),
        ({"usage": {"prompt_tokens": 10, "completion_tokens": 3}}, (10, 3)),
        # Responses-API / OpenRouter spelling.
        ({"usage": {"input_tokens": 11, "output_tokens": 4}}, (11, 4)),
        ({"usage": {"prompt_tokens": None, "completion_tokens": "nope"}}, (0, 0)),
        ({"usage": {"prompt_tokens": -5, "completion_tokens": 2.9}}, (0, 2)),
    ],
)
def test_usage_from_chat_response_never_raises(response, expected):
    assert usage_from_chat_response(response) == expected


def test_usage_from_codex_turn_prefers_the_thread_total():
    result = types.SimpleNamespace(
        usage=types.SimpleNamespace(
            total=types.SimpleNamespace(input_tokens=5000, output_tokens=800),
            last=types.SimpleNamespace(input_tokens=1000, output_tokens=200),
        )
    )

    assert usage_from_codex_turn(result) == (5000, 800)
    # Older app-servers emit no token-usage notification at all.
    assert usage_from_codex_turn(types.SimpleNamespace(usage=None)) == (0, 0)


def test_consume_client_usage_tolerates_a_client_without_the_method():
    class _Stub:
        def run_grading_proposal(self, context):  # pragma: no cover - never called
            raise NotImplementedError

    assert consume_client_usage(_Stub()) == TokenUsage()
    assert consume_client_usage(None) == TokenUsage()


def test_accounting_state_is_per_instance():
    class _Client(TokenUsageAccounting):
        pass

    first, second = _Client(), _Client()
    first.record_token_usage(10, 2)

    assert first.consume_usage() == TokenUsage(10, 2, 1)
    assert second.consume_usage() == TokenUsage()


# --- the path that makes C3 measurable -------------------------------------


class _MeteredGradingClient(TokenUsageAccounting):
    """A grading client that reports usage the way a real provider does."""

    provider_name = "deepseek_flash"
    provider_type = "openai_chat"
    model = "deepseek-v4-flash"

    def __init__(self, *, fail: bool = False):
        self.fail = fail

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        self.record_token_usage(2400, 310)
        if self.fail:
            raise CodexUnavailable("provider exploded after billing")
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


def _graded_attempt(tmp_path, client):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    result = complete_attempt_with_ai_fallback(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="SVD is U Sigma V^T.",
        ),
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
    return repository, result


def test_grading_path_persists_actual_tokens(tmp_path):
    client = _MeteredGradingClient()

    repository, result = _graded_attempt(tmp_path, client)

    run = repository.agent_run(result.agent_run_id)
    assert run["purpose"] == "grading"
    assert run["status"] == "completed"
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (2400, 310)
    # Drained, so the next graded attempt on this client starts clean.
    assert client.consume_usage() == TokenUsage()


def test_grading_fallback_still_bills_the_failed_run(tmp_path):
    # The tokens C3 must not lose: a model call that was paid for and then fell
    # back to self-grading.
    repository, result = _graded_attempt(tmp_path, _MeteredGradingClient(fail=True))

    assert result.grading_source == "self"
    run = repository.agent_run(result.agent_run_id)
    assert run["status"] == "failed"
    assert (run["actual_input_tokens"], run["actual_output_tokens"]) == (2400, 310)
