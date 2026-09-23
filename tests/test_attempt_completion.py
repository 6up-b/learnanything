"""Durable attempt completion: saved results, provenance, routing, serialization."""

from __future__ import annotations

import threading
import time

import pytest

from learnloop.ai.runtime import AIRuntimeReport
from learnloop.attempts import attempts, completion_lock, post_attempt
from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptResult,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_self_graded_attempt,
)
from learnloop.attempts.post_attempt import (
    CompletionRouteUnknown,
    committed_submission_result,
    run_post_attempt_pipeline,
)
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import abandon_episode, enter_episode
from learnloop.substrate.data_quality import data_quality_report
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault, set_algorithm_version
from tests.test_diagnostic_augmentation import _proposal, _SequenceDiagnostician

ITEM_ID = "pi_svd_define_001"
READY = AIRuntimeReport(
    status="ready", active_provider="diagnostician", provider_type="openai_chat", model="claude-4",
)


def _vault(tmp_path, algorithm_version: str | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    if algorithm_version is not None:
        set_algorithm_version(paths, algorithm_version)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repository)
    return paths, vault, repository


def _self_graded(vault, repository, *, submission_id: str | None = None, **draft_fields):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="A = U Sigma V transpose",
            submission_id=submission_id,
            **draft_fields,
        ),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=3),
    )


@pytest.mark.parametrize("with_repairs", [True, False])
def test_pipeline_keeps_one_hypothesis_version_with_grader_provenance(tmp_path, with_repairs):
    _paths, vault, repository = _vault(tmp_path, "mvp-0.7")

    def proposal(context):
        graded = _proposal(context.attempt_id)
        return graded if with_repairs else graded.model_copy(update={"repair_suggestions": []})

    client = _SequenceDiagnostician([proposal])
    result = complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="A = U Sigma"),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        runtime=READY, ai_client=client,
    )
    run_post_attempt_pipeline(vault, repository, result=result, ai_client=client)

    with repository.connection() as connection:
        hypotheses = connection.execute(
            "SELECT version, generation_agent_run_id, model FROM causal_hypotheses WHERE attempt_id=?",
            (result.attempt_id,),
        ).fetchall()
    assert hypotheses
    assert {row["version"] for row in hypotheses} == {1}
    assert all(row["generation_agent_run_id"] == result.agent_run_id for row in hypotheses)
    assert all(row["model"] == "claude-4" for row in hypotheses)


def test_committed_model_grade_keeps_its_provenance_through_recovery(tmp_path, monkeypatch):
    _paths, vault, repository = _vault(tmp_path)

    def fail(*args, **kwargs):
        raise ValueError("interrupted augmentation receipt")

    monkeypatch.setattr(attempts, "_record_diagnostic_augmentation", fail)
    with pytest.raises(ValueError, match="augmentation receipt"):
        complete_attempt_with_ai_fallback(
            vault, repository,
            AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="A = U Sigma", submission_id="sub-1"),
            SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
            runtime=READY,
            ai_client=_SequenceDiagnostician([lambda context: _proposal(context.attempt_id)]),
        )

    attempt = repository.practice_attempt_by_submission_id("sub-1")
    with repository.connection() as connection:
        run = connection.execute("SELECT id, status FROM agent_runs WHERE purpose='grading'").fetchone()
        raw_grade_runs = {
            row[0] for row in connection.execute(
                "SELECT agent_run_id FROM raw_grade_events WHERE attempt_id=?", (attempt["id"],)
            )
        }
    # The model grade is authoritative, so its run completed.
    assert run["status"] == "completed"
    assert raw_grade_runs == {run["id"]}

    recovered = committed_submission_result(repository, "sub-1")
    assert (recovered.grading_source, recovered.agent_run_id) == ("ai", run["id"])
    run_post_attempt_pipeline(vault, repository, result=recovered)
    metadata = repository.fetch_attempt_feedback_metadata(attempt["id"])
    assert (metadata["grading_source"], metadata["agent_run_id"]) == ("ai", run["id"])
    assert len(repository.list_attempt_history()) == 1


def test_self_grade_fallback_records_why_and_which_run_failed(tmp_path):
    _paths, vault, repository = _vault(tmp_path)

    def invalid(_context):
        raise ValueError("unparseable grade")

    result = complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="A = U Sigma", submission_id="sub-2"),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        runtime=READY, ai_client=_SequenceDiagnostician([invalid]),
    )
    saved = repository.attempt_completion(result.attempt_id)["result"]
    assert saved["grading_source"] == "self"
    assert saved["fallback_reason"] == "ai_failed:ValueError"
    assert saved["agent_run_id"] == result.agent_run_id is not None
    with repository.connection() as connection:
        status = connection.execute(
            "SELECT status FROM agent_runs WHERE id=?", (result.agent_run_id,)
        ).fetchone()[0]
    assert status == "failed"


def test_resumed_completion_routes_to_the_episode_the_attempt_was_applied_under(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    learning_object_id = vault.learning_object_for_item(vault.practice_items[ITEM_ID]).id
    applied_under = enter_episode(vault, repository, learning_object_id)
    result = _self_graded(vault, repository, submission_id="sub-episode")

    # Completion was interrupted; meanwhile that episode ended and a new one opened.
    abandon_episode(repository, learning_object_id)
    newer = enter_episode(vault, repository, learning_object_id)
    assert newer.id != applied_under.id

    run_post_attempt_pipeline(vault, repository, result=committed_submission_result(repository, "sub-episode"))
    route = repository.attempt_completion(result.attempt_id)["route"]
    assert route["episode_id"] == applied_under.id
    assert route["feedback_deferred"] is False


def test_pending_completion_without_its_episode_is_not_resumed(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    result = _self_graded(vault, repository, submission_id="sub-legacy")
    with repository.connection() as connection:
        connection.execute(
            "UPDATE attempt_completion_work SET route_json=NULL WHERE attempt_id=?", (result.attempt_id,)
        )
        connection.commit()

    with pytest.raises(CompletionRouteUnknown):
        run_post_attempt_pipeline(vault, repository, result=result)
    assert repository.attempt_completion(result.attempt_id)["status"] == "pending"


def test_concurrent_completions_normalize_an_attempt_once(tmp_path, monkeypatch):
    _paths, vault, repository = _vault(tmp_path)
    result = _self_graded(vault, repository, submission_id="sub-race")
    normalized = []

    def slow_normalize(*args, **kwargs):
        normalized.append(kwargs["attempt_id"])
        time.sleep(0.3)
        return []

    monkeypatch.setattr(post_attempt, "normalize_and_resolve_attempt", slow_normalize)
    outcomes = []

    def complete():
        outcomes.append(
            run_post_attempt_pipeline(vault, Repository.attach(repository.sqlite_path), result=result)
        )

    workers = [threading.Thread(target=complete) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert normalized == [result.attempt_id]
    assert sorted(outcome.notes for outcome in outcomes) == [(), ("already_completed",)]


def test_completion_lock_contention_raises_busy(tmp_path, monkeypatch):
    _paths, vault, repository = _vault(tmp_path)
    result = _self_graded(vault, repository, submission_id="sub-busy")
    monkeypatch.setattr(completion_lock, "COMPLETION_LOCK_TIMEOUT_S", 0.1)
    holding = threading.Event()
    release = threading.Event()

    def hold():
        with completion_lock.attempt_completion_lock(repository.sqlite_path):
            holding.set()
            release.wait(5)

    holder = threading.Thread(target=hold)
    holder.start()
    holding.wait(5)
    try:
        with pytest.raises(completion_lock.AttemptCompletionBusy):
            run_post_attempt_pipeline(vault, repository, result=result)
    finally:
        release.set()
        holder.join()
    assert repository.attempt_completion(result.attempt_id)["status"] == "pending"


def test_doors_without_a_completion_phase_are_not_counted_as_interrupted(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    seeded = _self_graded(vault, repository, awaits_completion=False)
    interrupted = _self_graded(vault, repository, submission_id="sub-interrupted")

    seeded_work = repository.attempt_completion(seeded.attempt_id)
    assert seeded_work["status"] == "completed"
    assert seeded_work["route"] is None
    assert seeded_work["result"]["debug"] == {}
    assert repository.attempt_completion(interrupted.attempt_id)["status"] == "pending"

    cohorts = data_quality_report(paths.sqlite_path)["attempt_cohorts"]
    assert sum(cohort.get("completion_pending", 0) for cohort in cohorts) == 1
    assert sum(cohort.get("completion_missing", 0) for cohort in cohorts) == 0


def test_saved_result_loads_across_field_changes(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    result = _self_graded(vault, repository)
    saved = result.as_dict()
    saved["field_from_a_newer_version"] = 1
    del saved["probe_block_end"]

    loaded = AttemptResult.from_dict(saved)
    assert loaded.attempt_id == result.attempt_id
    assert loaded.probe_block_end is None
    assert loaded.debug_payload == result.debug_payload
