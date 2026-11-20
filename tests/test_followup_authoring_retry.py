"""Incomplete model answers get one correction inside the workflow's existing budget."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import json
from types import SimpleNamespace

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.stores import followup_serve as store
from learnloop.diagnosis.ai_contracts import FollowupProbeAuthored, FollowupProbePrediction, followup_probe_prompt
from learnloop.followup_run import jobs
from learnloop.followup_serve import identity, workflow as wf

from tests.followup_journey_helpers import _call, journey  # noqa: F401 - fixture
from tests.figure_build_golden_helpers import freeze_ids, freeze_wall
from tests.followup_serve_helpers import AuthorFake, CLOCK, miss_with_rivals, rival_causes_vault, run_jobs
from tests.structured_ai import StructuredClientFake


class SequenceAuthor(StructuredClientFake, AuthorFake):
    def __init__(self, *answers):
        AuthorFake.__init__(self)
        self.answers = answers
        self.requests = []
        self.profile = SimpleNamespace(timeout_seconds=40)

    def complete(self, request):
        self.requests.append(request)
        return super().complete(request)

    def run_followup_probe_authoring(self, context):
        good = AuthorFake.run_followup_probe_authoring(self, context)
        answer = self.answers[self.calls - 1]
        if isinstance(answer, Exception):
            raise answer
        if answer == "measured":
            return FollowupProbeAuthored(prompt_md="", expected_answer_md="k" * 636, surface_suffix="s" * 24)
        if answer == "same_predictions":
            return good.model_copy(update={"predictions": [
                prediction.model_copy(update={"fails_criteria": ["fact_0"]}) for prediction in good.predictions
            ]})
        return good.model_copy(update=answer or {})


def _run(vault, repository, fake, *, clock=CLOCK, limit=20):
    return run_jobs(vault, repository, clients=SimpleNamespace(author=fake), clock=clock, limit=limit)


def _rows(repository, workflow_id):
    with repository.connection() as connection:
        return (store.workflow_events(connection, workflow_id),
                store.generation_job(connection, f"workflow:{workflow_id}"),
                [dict(row) for row in connection.execute(
                    "SELECT * FROM model_call_receipts WHERE purpose = 'followup_probe_authoring' ORDER BY rowid")])


def _assert_failed(repository, outcome, reason):
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.FAILED and row["practice_item_id"] is None
    assert row["release_reason"] == wf.RELEASE_GENERATION_FAILED
    assert row["feedback_released_at"] is not None
    events, _, _ = _rows(repository, outcome.workflow_id)
    assert events[-1]["reason"] == reason
    with repository.connection() as connection:
        need = store.generation_job(connection, f"factor:{row['factor_id']}")
    assert need["state"] == "queued"
    assert need["not_before"] == (CLOCK.now() + timedelta(hours=1)).isoformat().replace("+00:00", "Z")


def test_measured_empty_answer_then_good_is_served_with_both_receipts_and_reason(journey):
    ctx, vault, repository, result, outcome = journey
    fake = SequenceAuthor("measured", None)
    outcomes = _run(vault, repository, fake)
    assert fake.calls == 2
    assert [job.state for job in outcomes] == ["retry", "done"]
    events, job, receipts = _rows(repository, outcome.workflow_id)
    retry = next(event for event in events if event["reason"] == "authoring_contract_retry")
    assert json.loads(retry["detail_json"])["rejection_reason"] == "empty_question_or_key"
    assert retry["from_state"] == retry["to_state"] == wf.PENDING
    assert job["attempt_count"] == 2
    assert len(receipts) == 2 and {row["owner_id"] for row in receipts} == {job["id"]}
    assert json.loads(receipts[0]["output_text"])["prompt_md"] == ""
    assert receipts[1]["output_text"] != receipts[0]["output_text"]
    assert "empty_question_or_key" in receipts[1]["input_text"]
    assert fake.requests[0].prompt == followup_probe_prompt(fake.contexts[0])
    assert fake.requests[0].timeout_seconds is None
    assert "empty_question_or_key" in fake.requests[1].prompt
    assert "prompt_md" in fake.requests[1].prompt and "expected_answer_md" in fake.requests[1].prompt
    assert fake.requests[0].result_model is fake.requests[1].result_model is FollowupProbeAuthored
    step = _call(ctx, "followup_next", {"attemptId": result.attempt_id})
    assert step["action"] == "open"
    _call(ctx, "open_queue_item", {"practiceItemId": step["practiceItemId"]})
    assert step["practiceItemId"] in identity.closed_probe_ids(repository)


def test_two_incomplete_answers_fail_as_before_without_a_third_request(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor("measured", {"criteria": []})
    _run(vault, repository, fake)
    assert fake.calls == 2
    _assert_failed(repository, outcome, "criteria_contract_invalid")
    assert _run(vault, repository, fake) == []
    assert fake.calls == 2


def test_nondiscriminating_content_still_fails_after_one_request(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor("same_predictions")
    _run(vault, repository, fake)
    assert fake.calls == 1
    _assert_failed(repository, outcome, "predictions_do_not_discriminate")


def test_good_first_answer_keeps_existing_expected_rows(tmp_path, monkeypatch):
    # Freeze incidental IDs/time so an extra write on the successful path changes the captured row bytes.
    freeze_ids(monkeypatch, 45)
    freeze_wall(monkeypatch)
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor(None)
    _run(vault, repository, fake)
    assert fake.calls == 1
    row = wf.get(repository, outcome.workflow_id)
    candidate = repository.causal_probe_candidate(row["probe_candidate_id"])
    assert candidate["status"] == "active" and candidate["reviewer"].startswith("system:followup_machine_admission")
    assert repository.practice_item_state(row["practice_item_id"]).active
    events, job, receipts = _rows(repository, outcome.workflow_id)
    # Keep stable row columns byte-for-byte; generated IDs and timestamps are not a behavior change.
    stable = {"workflow": {key: row[key] for key in ("state", "lane", "release_reason", "settled_reason")},
              "events": [{key: event[key] for key in ("from_state", "to_state", "reason", "detail_json")}
                         for event in events],
              "job": {key: job[key] for key in ("state", "attempt_count", "last_error")}}
    assert json.dumps(stable, sort_keys=True) == json.dumps({
        "events": [
            {"detail_json": '{"origin": "practice"}', "from_state": None, "reason": "opened", "to_state": "pending"},
            {"detail_json": "{}", "from_state": "pending", "reason": "insert_now", "to_state": "ready"},
        ],
        "job": {"attempt_count": 1, "last_error": None, "state": "done"},
        "workflow": {"lane": "probe", "release_reason": None, "settled_reason": None, "state": "ready"},
    }, sort_keys=True)
    with repository.connection() as connection:
        complete_rows = {table: [dict(record) for record in connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
                         for table in ("followup_workflows", "followup_workflow_events", "followup_generation_jobs",
                                       "generated_probe_items", "causal_probe_candidates")}
    assert hashlib.sha256(json.dumps(complete_rows, sort_keys=True).encode()).hexdigest() == "b947645765b753e735a59b8b21fd29cc57acfe5272fddae59c412280335db94e"
    assert len(receipts) == 1
    assert fake.requests[0].prompt == followup_probe_prompt(fake.contexts[0])


@pytest.mark.parametrize(("change", "reason"), [
    ({"expected_answer_md": " \n"}, "empty_question_or_key"),
    ({"criteria": []}, "criteria_contract_invalid"),
    ({"predictions": []}, "a_hypothesis_has_no_prediction"),
    ({"predictions": [FollowupProbePrediction(hypothesis_ref="unknown", fails_criteria=["fact_0"])]},
     "prediction_names_unknown_hypothesis"),
    ({"predictions": [FollowupProbePrediction(hypothesis_ref="H1", fails_criteria=[])]},
     "prediction_not_over_the_criteria"),
    ({"incidental_changes": ["difficulty"]}, "manipulation_contract_invalid"),
])
def test_other_missing_contract_parts_are_reasked(tmp_path, change, reason):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor(change, None)
    _run(vault, repository, fake)
    assert fake.calls == 2 and wf.get(repository, outcome.workflow_id)["state"] == wf.READY
    assert reason in fake.requests[1].prompt


def test_retry_uses_only_the_original_provider_time_left(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor("measured", None)
    first = _run(vault, repository, fake, limit=1)
    assert first[0].state == "retry"
    later = FrozenClock(CLOCK.now() + timedelta(seconds=12))
    _run(vault, repository, fake, clock=later)
    assert fake.calls == 2 and fake.requests[1].timeout_seconds == 28
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.READY


@pytest.mark.parametrize("elapsed", [39.5, 41])
def test_expired_queued_correction_fails_without_a_new_request(tmp_path, elapsed):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor("measured")
    first = _run(vault, repository, fake, limit=1)
    assert first[0].state == "retry"
    later = FrozenClock(CLOCK.now() + timedelta(seconds=elapsed))
    _run(vault, repository, fake, clock=later)
    assert fake.calls == 1 and wf.get(repository, outcome.workflow_id)["state"] == wf.FAILED
    events, job, _ = _rows(repository, outcome.workflow_id)
    assert events[-1]["reason"] == "empty_question_or_key" and job["attempt_count"] == 2


def test_transport_retry_already_spent_the_only_second_attempt(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor(RuntimeError("offline fake failure"), "measured")
    assert _run(vault, repository, fake)[0].state == "retry"
    later = FrozenClock(CLOCK.now() + timedelta(seconds=jobs.RETRY_BACKOFF_SECONDS))
    _run(vault, repository, fake, clock=later)
    assert fake.calls == 2 and wf.get(repository, outcome.workflow_id)["state"] == wf.FAILED


def test_skip_between_requests_cancels_the_queued_correction(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    result, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor("measured")
    assert _run(vault, repository, fake, limit=1)[0].state == "retry"
    from learnloop.followup_run.serving import continue_without

    assert continue_without(repository, result.attempt_id, clock=CLOCK)
    assert _run(vault, repository, fake) == [] and fake.calls == 1
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.SKIPPED


def test_second_request_transport_failure_does_not_get_an_extra_attempt(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    fake = SequenceAuthor("measured", RuntimeError("offline fake failure"))
    outcomes = _run(vault, repository, fake)
    assert fake.calls == 2 and [job.state for job in outcomes] == ["retry", "failed"]
    _assert_failed(repository, outcome, "RuntimeError")


def test_first_answer_that_used_the_whole_budget_keeps_todays_failure(tmp_path):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    clock = SimpleNamespace(now=lambda: CLOCK.now())

    class SlowAuthor(SequenceAuthor):
        def complete(self, request):
            result = super().complete(request)
            clock.now = lambda: CLOCK.now() + timedelta(seconds=41)
            return result

    fake = SlowAuthor("measured")
    outcomes = _run(vault, repository, fake, clock=clock)
    assert fake.calls == 1 and [job.state for job in outcomes] == ["done"]
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.FAILED
