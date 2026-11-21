"""Physical counts and prompt bytes captured before the step 5 adoption."""

from datetime import timedelta
import hashlib
from types import SimpleNamespace

import pytest

from learnloop.ai.structured_contracts import Predicate, RecoveryAllowance, checked_structured_call
from learnloop.clock import FrozenClock
from learnloop.db.stores import followup_serve as store
from learnloop.diagnosis.ai_contracts import FollowupProbeAuthored, followup_probe_prompt
from learnloop.followup_run.authoring import AUTHORING_PURPOSE, CONTRACT_REASK_REQUIREMENTS, request_authored_probe
from learnloop.followup_run.serving import continue_without
from learnloop.followup_serve import workflow as wf
from tests.followup_contract_baseline_helpers import CONTEXT, EMPTY, GOOD, CaptureAuthor, provider_client
from tests.followup_serve_helpers import CLOCK, miss_with_rivals, rival_causes_vault, run_jobs
from tests.structured_contracts_helpers import Admit, Recorder, Refused, operation_send, refused


@pytest.mark.parametrize("provider", ["plan", "openrouter"])
@pytest.mark.parametrize(("answers", "count", "state"), [
    ([GOOD], 1, wf.READY),
    ([EMPTY, GOOD], 2, wf.READY),
    ([EMPTY, EMPTY], 2, wf.FAILED),
    (["not json", GOOD], 2, wf.READY),
    (["not json", EMPTY, GOOD], 3, wf.READY),
    ([EMPTY, "not json", GOOD], 3, wf.READY),
    (["not json", EMPTY, "not json", GOOD], 4, wf.READY),
    (["not json", EMPTY, EMPTY], 3, wf.FAILED),
], ids=["valid", "contract-good", "contract-twice", "schema-good", "schema-contract-good", "contract-schema-good",
        "schema-contract-schema-good", "schema-contract-contract"])
def test_unadopted_physical_request_counts(tmp_path, monkeypatch, answers, count, state, provider):
    vault, repository, _ = rival_causes_vault(tmp_path)
    _, outcome = miss_with_rivals(vault, repository)
    learning_object_id = wf.get(repository, outcome.workflow_id)["learning_object_id"]
    title = vault.learning_objects[learning_object_id].title
    good = GOOD.model_copy(update={"prompt_md": f"On {title}: which factor makes the product valid, and why? (#1)"})
    answers = [good if answer == GOOD else answer for answer in answers]
    client, requests = provider_client(monkeypatch, provider, answers)
    run_jobs(vault, repository, clients=SimpleNamespace(author=client), clock=CLOCK)
    assert len(requests) == count
    row = wf.get(repository, outcome.workflow_id)
    with repository.connection() as connection:
        events = store.workflow_events(connection, outcome.workflow_id)
    assert row["state"] == state, events[-1]["reason"]


@pytest.mark.parametrize("provider", ["plan", "openrouter"])
@pytest.mark.parametrize("stop", ["deadline", "cancelled"])
def test_unadopted_pending_correction_sends_nothing_after_stop(tmp_path, monkeypatch, stop, provider):
    vault, repository, _ = rival_causes_vault(tmp_path)
    result, outcome = miss_with_rivals(vault, repository)
    client, requests = provider_client(monkeypatch, provider, [EMPTY, GOOD])
    clients = SimpleNamespace(author=client)
    first = run_jobs(vault, repository, clients=clients, clock=CLOCK, limit=1)
    assert first[0].state == "retry"
    if stop == "cancelled":
        assert continue_without(repository, result.attempt_id, clock=CLOCK)
    run_jobs(vault, repository, clients=clients, clock=FrozenClock(CLOCK.now() + timedelta(seconds=41)))
    assert len(requests) == 1
    assert wf.get(repository, outcome.workflow_id)["state"] == (wf.SKIPPED if stop == "cancelled" else wf.FAILED)


@pytest.mark.parametrize("provider", ["plan", "openrouter"])
@pytest.mark.parametrize("answers", [
    ["not json", EMPTY, GOOD],
    [EMPTY, "not json", GOOD],
    ["not json", EMPTY, "not json", GOOD],
])
def test_separate_credits_preserve_the_unadopted_success(monkeypatch, provider, answers):
    client, requests = provider_client(monkeypatch, provider, answers)
    contract = (Predicate("empty_question_or_key", lambda answer: bool(
        answer.prompt_md.strip() and answer.expected_answer_md.strip()),
        CONTRACT_REASK_REQUIREMENTS["empty_question_or_key"]),)
    assert checked_structured_call(
        first_prompt=followup_probe_prompt(CONTEXT), contract=contract,
        send=operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored),
        recovery=RecoveryAllowance(admit=Admit(slots=len(answers) - 1)), checkpoint=None, failure=refused,
    ) == GOOD
    assert len(requests) == len(answers)


@pytest.mark.parametrize("provider", ["plan", "openrouter"])
@pytest.mark.parametrize("stop_after", [1, 2, 3])
@pytest.mark.parametrize("stop", ["admission", "deadline", "cancelled"])
def test_every_schema_or_contract_recovery_needs_admission_time_and_no_cancellation(
        monkeypatch, provider, stop_after, stop):
    client, requests = provider_client(monkeypatch, provider, ["not json", EMPTY, "not json", GOOD])
    admit = Admit(slots=stop_after - 1 if stop == "admission" else 3)
    contract = (Predicate("empty_question_or_key", lambda answer: bool(answer.prompt_md.strip()),
                          CONTRACT_REASK_REQUIREMENTS["empty_question_or_key"]),)
    with pytest.raises(Refused) as raised:
        checked_structured_call(
            first_prompt=followup_probe_prompt(CONTEXT), contract=contract,
            send=operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored),
            recovery=RecoveryAllowance(
                admit=admit,
                remaining_seconds=lambda: 0.5 if stop == "deadline" and len(requests) >= stop_after else 40,
                min_request_seconds=1,
                cancelled=lambda: stop == "cancelled" and len(requests) >= stop_after,
            ), checkpoint=None, failure=refused,
        )
    assert len(requests) == stop_after
    assert raised.value.info.reason == ("recovery_refused" if stop == "admission" else stop)
    assert admit.asked == (stop_after if stop == "admission" else stop_after - 1)


@pytest.mark.parametrize("provider", ["plan", "openrouter"])
@pytest.mark.parametrize(("answers", "reason"), [
    (["not json", "still not json", GOOD], "schema_failed"),
    (["not json", EMPTY, "not json", EMPTY, GOOD], "contract_failed"),
    (["not json", EMPTY, "not json", "still not json", GOOD], "schema_failed"),
])
def test_two_attempts_each_allow_only_one_schema_repair(monkeypatch, provider, answers, reason):
    client, requests = provider_client(monkeypatch, provider, answers)
    record = Recorder()
    contract = (Predicate("empty_question_or_key", lambda answer: bool(answer.prompt_md.strip()),
                          CONTRACT_REASK_REQUIREMENTS["empty_question_or_key"]),)
    with pytest.raises(Refused) as raised:
        checked_structured_call(
            first_prompt=followup_probe_prompt(CONTEXT), contract=contract,
            send=operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored),
            recovery=RecoveryAllowance(admit=Admit(slots=10), record=record), checkpoint=None, failure=refused,
        )
    assert len(requests) == len(answers) - 1 <= 4
    assert raised.value.info.reason == reason
    assert record.last.recoveries == (1 if len(requests) == 4 else 0)


def test_capture_unadopted_prompt_digests():
    captured = {}
    for reason in [None, *CONTRACT_REASK_REQUIREMENTS]:
        client = CaptureAuthor()
        request_authored_probe(client, CONTEXT, rejection_reason=reason)
        [(_, prompt)] = client.requests
        captured[reason or "first"] = hashlib.sha256(prompt.encode()).hexdigest()
    assert captured == {
        "first": "7ae031f3850d61b5ea1c195ac6dd7d229852b39f607a0360f5babb046e831ad6",
        "empty_question_or_key": "413c166babd4f2abb1f59953e9f83981e7044e61e4d58ce44e3c6a150aea8514",
        "criteria_contract_invalid": "0fcaf291b044585b6edb6e07cbae4a51ea98461738ba98c6d6cd82c1c3c4472e",
        "prediction_names_unknown_hypothesis": "cc1e6c83b089cea70aa8f46299dc8a242d6458699a7e976f85f7a8c5f5eddb78",
        "prediction_not_over_the_criteria": "ae5b74d224f65a0d78d428b64b10bfa259022e1b8c2b5877395e03940b8f41d0",
        "a_hypothesis_has_no_prediction": "4912e11fa82cd9956912df3a5df62c596165cdd9418aa1c3ac3445c588bef8ca",
        "manipulation_contract_invalid": "e9c8a1de31633b89d93bb27d312fd468b6d6529efe986bed0a1dfcde29f3c843",
    }
