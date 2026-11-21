"""Durable shared-contract recovery through the workflow's own SQLite storage."""

import json
from datetime import timedelta
from types import SimpleNamespace

import pytest

from learnloop.ai.structured_contracts import first_failure
from learnloop.clock import FrozenClock
from learnloop.db.stores import followup_serve as store
from learnloop.diagnosis.ai_contracts import FollowupProbePrediction
from learnloop.followup_run import jobs
from learnloop.followup_run.authoring import AuthoringRejected, authoring_contract, check_structure
from learnloop.followup_serve import workflow as wf
from tests.followup_contract_baseline_helpers import Crash, GOOD, JobAuthor
from tests.followup_serve_helpers import CLOCK, miss_with_rivals, rival_causes_vault, run_jobs


def setup_job(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    author = JobAuthor({"prompt_md": ""}, {})
    return vault, repository, outcome.workflow_id, author, SimpleNamespace(author=author)


def checkpoint_rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM model_work_checkpoints ORDER BY rowid")]


def test_owed_correction_survives_restart_and_saves_only_accepted_answer(tmp_path):
    vault, repository, workflow_id, author, clients = setup_job(tmp_path)
    assert run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)[0].state == "retry"
    retry = wf.noted(repository, workflow_id, reason="authoring_contract_retry")
    assert retry["recovery_state"] == {"recoveries": 0, "owed": "empty_question_or_key"}
    assert checkpoint_rows(repository) == []
    run_jobs(vault, repository, clients=clients, clock=CLOCK)
    assert len(author.requests) == 2 and wf.get(repository, workflow_id)["state"] == wf.READY
    assert author.requests[1].prompt.startswith(author.requests[0].prompt + "\n\nThe previous answer")
    assert repository.model_checkpoint(retry["request_key"])["result"]["prompt_md"]
    assert repository.model_checkpoint(retry["request_key"] + ":recovery")["result"] == {
        "recoveries": 1, "owed": "empty_question_or_key"}
    with repository.connection() as connection:
        events = store.workflow_events(connection, workflow_id)
        receipts = [dict(row) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE purpose='followup_probe_authoring' ORDER BY rowid")]
    assert [event["reason"] for event in events] == ["opened", "authoring_contract_retry", "insert_now"]
    assert receipts[0]["status"] == "failed" and receipts[0]["error_type"] == "ContractRejected"
    assert json.loads(receipts[1]["budget_json"])["structured_recovery"]["request_key"] == retry["request_key"]
    assert run_jobs(vault, repository, clients=clients, clock=CLOCK) == []


@pytest.mark.parametrize(("timeout", "count", "state"), [(40, 1, wf.FAILED), (2000, 2, wf.READY)])
def test_crash_after_rejection_keeps_owed_state_and_the_original_deadline(tmp_path, monkeypatch, timeout, count, state):
    vault, repository, workflow_id, author, clients = setup_job(tmp_path)
    author.profile.timeout_seconds = timeout
    original = wf.note

    def note(*args, **kwargs):
        original(*args, **kwargs)
        if kwargs.get("reason") == "authoring_contract_retry":
            raise Crash()

    monkeypatch.setattr(wf, "note", note)
    with pytest.raises(Crash):
        run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)
    retry = wf.noted(repository, workflow_id, reason="authoring_contract_retry")
    assert retry["recovery_state"]["recoveries"] == 0
    assert checkpoint_rows(repository) == []
    later = FrozenClock(CLOCK.now() + timedelta(seconds=jobs.LEASE_SECONDS + 1))
    run_jobs(vault, repository, clients=clients, clock=later)
    assert len(author.requests) == count
    assert wf.get(repository, workflow_id)["state"] == state


def test_crash_after_claim_never_duplicates_the_correction(tmp_path):
    vault, repository, workflow_id, author, clients = setup_job(tmp_path)
    run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)

    def crash():
        raise Crash()

    author.before_send = crash
    with pytest.raises(Crash):
        run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)
    retry = wf.noted(repository, workflow_id, reason="authoring_contract_retry")
    assert repository.model_checkpoint(retry["request_key"] + ":recovery")["result"]["recoveries"] == 1
    assert repository.model_checkpoint(retry["request_key"]) is None
    author.before_send = lambda: None
    later = FrozenClock(CLOCK.now() + timedelta(seconds=jobs.LEASE_SECONDS + 1))
    run_jobs(vault, repository, clients=clients, clock=later)
    assert len(author.requests) == 1
    with repository.connection() as connection:
        events = store.workflow_events(connection, workflow_id)
    assert events[-1]["reason"] == jobs.ATTEMPTS_EXHAUSTED


def test_exactly_one_second_left_keeps_the_original_inclusive_request_floor(tmp_path):
    vault, repository, workflow_id, author, clients = setup_job(tmp_path)
    run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)
    later = FrozenClock(CLOCK.now() + timedelta(seconds=39))
    run_jobs(vault, repository, clients=clients, clock=later)
    assert len(author.requests) == 2 and author.requests[1].timeout_seconds == 1.0
    assert wf.get(repository, workflow_id)["state"] == wf.READY


@pytest.mark.parametrize("legacy_retry", [False, True])
def test_crash_before_corrected_answer_save_recovers_receipt_under_original_key(tmp_path, monkeypatch, legacy_retry):
    vault, repository, workflow_id, author, clients = setup_job(tmp_path)
    original_note = wf.note

    def note(*args, **kwargs):
        if legacy_retry and kwargs.get("reason") == "authoring_contract_retry":
            kwargs["detail"] = {key: value for key, value in kwargs["detail"].items()
                                if key in {"rejection_reason", "deadline", "rejected_attempt", "retry_attempt"}}
        original_note(*args, **kwargs)

    monkeypatch.setattr(wf, "note", note)
    run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)
    retry = wf.noted(repository, workflow_id, reason="authoring_contract_retry")
    with repository.connection() as connection:
        key = store.generation_job(connection, f"workflow:{workflow_id}")["id"]
    assert ("request_key" not in retry) == legacy_retry
    save = repository.save_model_checkpoint

    def crash(*args, **kwargs):
        raise Crash()

    monkeypatch.setattr(repository, "save_model_checkpoint", crash)
    with pytest.raises(Crash):
        run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)
    assert len(author.requests) == 2
    assert repository.model_checkpoint(key) is None
    monkeypatch.setattr(repository, "save_model_checkpoint", save)
    later = FrozenClock(CLOCK.now() + timedelta(seconds=jobs.LEASE_SECONDS + 1))
    run_jobs(vault, repository, clients=clients, clock=later)
    assert len(author.requests) == 2
    assert wf.get(repository, workflow_id)["state"] == wf.READY
    saved = repository.model_checkpoint(key)["result"]
    assert saved["prompt_md"] and saved["expected_answer_md"]
    assert run_jobs(vault, repository, clients=clients, clock=later) == []


@pytest.mark.parametrize(("changes", "reason", "terminal"), [
    ({"prompt_md": "same", "expected_answer_md": "same", "criteria": []}, "prompt_equals_key", True),
    ({"predictions": [prediction.model_copy(update={"fails_criteria": ["fact_0"]})
                      for prediction in GOOD.predictions], "incidental_changes": ["difficulty"]},
     "predictions_do_not_discriminate", True),
    ({"predictions": [FollowupProbePrediction(hypothesis_ref="H1", fails_criteria=[]),
                      FollowupProbePrediction(hypothesis_ref="unknown", fails_criteria=["fact_0"])]},
     "prediction_not_over_the_criteria", False),
    ({"prompt_md": "", "criteria": []}, "empty_question_or_key", False),
])
def test_named_predicates_preserve_the_interleaved_pipeline(changes, reason, terminal):
    answer = GOOD.model_copy(update=changes)
    refs = {"H1": "first", "H2": "second"}
    with pytest.raises(AuthoringRejected, match=f"^{reason}$"):
        check_structure(answer, refs)
    if terminal:
        with pytest.raises(AuthoringRejected, match=f"^{reason}$"):
            first_failure(authoring_contract(refs), answer)
    else:
        assert first_failure(authoring_contract(refs), answer).name == reason
