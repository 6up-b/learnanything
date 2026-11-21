"""The shared "check the contract, ask once more" step for structured answers (no caller adopts it yet).

A parsed answer that fails a declared predicate is discarded and the request is sent once more with the predicate's
fixed requirement; the first request goes out exactly as built. One recovery per logical call, shared with a
provider's schema repair, drawn from the caller's own admission, time and cancellation; nothing is sent past it.
"""

from __future__ import annotations

import json

import pytest

from learnloop.ai.errors import AIInvalidOutput, AIOutputTruncated, AIProviderUnavailable
from learnloop.ai.execution import ModelCheckpoint, content_key, generation_limit, observe_model_calls
from learnloop.ai.structured_contracts import (
    MAX_STRUCTURED_RECOVERIES,
    RECOVERY_NOTE,
    ContractRejected,
    Predicate,
    RecoveryAllowance,
    RecoveryState,
    checked_structured_answer,
    checked_structured_call,
    claim_schema_repair,
    contract_of,
    correction_in_flight,
    correction_prompt,
    first_failure,
    recover_from_receipts,
    recovery_remaining_seconds,
)
from learnloop.ai.transport import execute_structured_operation
from learnloop.diagnosis.ai_contracts import (
    FollowupProbeAuthored,
    FollowupProbeContext,
    FollowupProbeCriterion,
    followup_probe_prompt,
)
from learnloop.followup_run.authoring import (
    AUTHORING_PURPOSE,
    CONTRACT_REASK_REQUIREMENTS,
    request_authored_probe,
)
from tests.structured_ai import RecordingStructuredClientFake
from tests.structured_contracts_helpers import Admit, Recorder, Refused, operation_send, refused, root_receipts

CONTEXT = FollowupProbeContext(
    learning_object_title="Eigenvalues",
    learning_object_concept="eigenvalue",
    learning_object_summary="Scalars a matrix stretches its eigenvectors by.",
    target_facets=["facet_eigen"],
    hypotheses=[{"hypothesis_ref": "H1", "statement": "confuses rows and columns", "cause_scope": "",
                 "target_ref": None}],
    router_decision={"action": "probe"},
)
FIRST = followup_probe_prompt(CONTEXT)
CRITERIA = [FollowupProbeCriterion(id="a", description="one", points=2),
            FollowupProbeCriterion(id="b", description="two", points=2)]
GOOD = FollowupProbeAuthored(prompt_md="Find the eigenvalues of [[2,0],[0,3]].", expected_answer_md="2 and 3",
                             surface_suffix="", criteria=CRITERIA)
# The measured live shape: a wire-valid answer with no question and every list empty.
EMPTY = FollowupProbeAuthored(prompt_md="", expected_answer_md="k" * 636, surface_suffix="s" * 24)
ONE_CRITERION = FollowupProbeAuthored(prompt_md="Q?", expected_answer_md="K", surface_suffix="", criteria=CRITERIA[:1])

NONBLANK = Predicate("empty_question_or_key",
                     lambda a: bool(a.prompt_md.strip() and a.expected_answer_md.strip()),
                     CONTRACT_REASK_REQUIREMENTS["empty_question_or_key"])
CRITERIA_OK = Predicate("criteria_contract_invalid", lambda a: len(a.criteria) >= 2,
                        CONTRACT_REASK_REQUIREMENTS["criteria_contract_invalid"])
CONTRACT = contract_of(NONBLANK, CRITERIA_OK)


class ScriptedAuthor(RecordingStructuredClientFake):
    """Answers each follow-up authoring request with the next scripted answer, or raises it."""

    def __init__(self, *answers):
        super().__init__()
        self.answers = list(answers)
        self.full: list = []

    def complete(self, request):
        self.full.append(request)
        return super().complete(request)

    def run_followup_probe_authoring(self, context):
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer


def _call(client, *, allowance=None, checkpoint=None, contract=CONTRACT, send=None, request_key=None):
    send = send or operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored)
    return checked_structured_answer(
        first_prompt=FIRST, contract=contract, send=send,
        recovery=allowance if allowance is not None else RecoveryAllowance(admit=Admit()),
        checkpoint=checkpoint, failure=refused, request_key=request_key,
    )


# -- the contract -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "requirement"), [
    ("Empty", "Supply a question."), ("empty question", "Supply a question."), ("", "Supply a question."),
    ("empty", ""), ("empty", "   "), ("empty", "Two\nlines."), ("empty", " Padded."),
], ids=["capitalized", "space", "blank_name", "blank", "whitespace", "two_lines", "padded"])
def test_a_predicate_needs_a_snake_case_name_and_one_fixed_requirement_line(name, requirement):
    with pytest.raises(ValueError):
        Predicate(name, lambda _a: True, requirement)


def test_a_contract_holds_distinctly_named_predicates_and_may_be_empty():
    assert contract_of() == ()
    with pytest.raises(ValueError, match="two predicates"):
        contract_of(NONBLANK, Predicate("empty_question_or_key", lambda _a: True, "Again."))
    with pytest.raises(TypeError):
        contract_of(NONBLANK, lambda _a: True)


def test_predicates_run_in_declared_order_and_the_first_failure_wins():
    seen: list[str] = []

    def predicate(name, verdict):
        return Predicate(name, lambda _a: seen.append(name) or verdict, f"Fix {name}.")

    contract = contract_of(predicate("first", True), predicate("second", False), predicate("third", False))
    assert first_failure(contract, GOOD).name == "second"
    assert seen == ["first", "second"]
    assert first_failure(contract_of(predicate("ok", True)), GOOD) is None


def test_a_predicate_must_answer_with_a_bool():
    with pytest.raises(TypeError, match="not bool"):
        first_failure(contract_of(Predicate("items", lambda a: a.criteria, "Supply criteria.")), GOOD)


def test_the_correction_is_the_original_prompt_and_the_exact_suffix():
    assert correction_prompt("PROMPT", Predicate("empty_question_or_key", lambda _a: True, "Supply both.")) == (
        "PROMPT\n\nThe previous answer failed validation: empty_question_or_key. Supply both. "
        "Write the complete answer again, satisfying all the original requirements.")


@pytest.mark.parametrize("reason", sorted(CONTRACT_REASK_REQUIREMENTS))
def test_the_correction_reproduces_the_followup_authors_reask_byte_for_byte(reason):
    client = ScriptedAuthor(GOOD)
    request_authored_probe(client, CONTEXT, rejection_reason=reason)
    [(purpose, sent)] = client.requests
    shared = correction_prompt(FIRST, Predicate(reason, lambda _a: True, CONTRACT_REASK_REQUIREMENTS[reason]))
    assert (purpose, sent) == (AUTHORING_PURPOSE, shared)


# -- the state machine ------------------------------------------------------------------------------------------


def test_a_valid_first_answer_is_one_unchanged_request_and_asks_for_no_recovery():
    client = ScriptedAuthor(GOOD)
    admit, record = Admit(), Recorder()
    result = _call(client, allowance=RecoveryAllowance(admit=admit, record=record))
    assert (result.answer, result.reused, result.sends) == (GOOD, False, 1)
    assert client.requests == [(AUTHORING_PURPOSE, FIRST)]
    assert client.full[0].prompt is FIRST
    assert (admit.asked, record.states, result.state) == (0, [], RecoveryState())


def test_bad_then_good_spends_the_one_recovery_on_a_correction():
    client = ScriptedAuthor(EMPTY, GOOD)
    admit, record = Admit(), Recorder()
    result = _call(client, allowance=RecoveryAllowance(admit=admit, record=record))
    assert (result.answer, result.sends) == (GOOD, 2)
    assert [prompt for _purpose, prompt in client.requests] == [FIRST, correction_prompt(FIRST, NONBLANK)]
    # Owed first (a restart sends the correction), then spent before it is sent.
    assert record.states == [RecoveryState(0, "empty_question_or_key"), RecoveryState(1, "empty_question_or_key")]
    assert admit.asked == 1 and result.state == RecoveryState(1, "empty_question_or_key")
    assert MAX_STRUCTURED_RECOVERIES == 1


def test_bad_then_bad_sends_no_third_request():
    client = ScriptedAuthor(EMPTY, ONE_CRITERION, GOOD)
    admit = Admit(slots=5)
    with pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(admit=admit))
    assert len(client.requests) == 2 and admit.asked == 1
    info = raised.value.info
    assert (info.reason, info.predicate, info.sends) == ("contract_failed", "criteria_contract_invalid", 2)
    assert isinstance(raised.value.__cause__, ContractRejected)


def test_the_correction_names_only_the_first_failing_predicate():
    both_wrong = FollowupProbeAuthored(prompt_md=" ", expected_answer_md="K", surface_suffix="")
    client = ScriptedAuthor(both_wrong, GOOD)
    _call(client)
    correction = client.requests[1][1]
    assert correction.endswith(f"{NONBLANK.requirement} Write the complete answer again, satisfying all the "
                               "original requirements.")
    assert "criteria_contract_invalid" not in correction[len(FIRST):]


def test_no_ambient_authorization_sends_no_recovery():
    """A deadline, time to spare and an output budget are not a spend authorization: only ``admit`` is."""

    client = ScriptedAuthor(EMPTY, GOOD)
    record = Recorder()
    with generation_limit(500), pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(remaining_seconds=lambda: 60.0, record=record))
    assert len(client.requests) == 1
    assert (raised.value.info.reason, raised.value.info.predicate) == ("recovery_refused", "empty_question_or_key")
    assert record.states == [RecoveryState(0, "empty_question_or_key")]


@pytest.mark.parametrize(("allowance", "reason", "admit_asked"), [
    (dict(admit_slots=0), "recovery_refused", 1),
    (dict(remaining=0.0), "deadline", 0),
    (dict(remaining=0.5, min_request_seconds=1.0), "deadline", 0),
    (dict(cancelled=True), "cancelled", 0),
], ids=["budget_exhausted", "deadline_passed", "under_the_request_floor", "cancelled"])
def test_an_exhausted_budget_deadline_or_cancellation_sends_nothing_more(allowance, reason, admit_asked):
    admit = Admit(slots=allowance.get("admit_slots", 1))
    remaining = allowance.get("remaining")
    client = ScriptedAuthor(EMPTY, GOOD)
    with pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(
            admit=admit, remaining_seconds=(lambda: remaining) if remaining is not None else None,
            min_request_seconds=allowance.get("min_request_seconds", 0.0),
            cancelled=(lambda: True) if allowance.get("cancelled") else None,
        ))
    assert len(client.requests) == 1
    assert raised.value.info.reason == reason and raised.value.info.state.recoveries == 0
    # Admission (which may reserve budget) is asked only when time and cancellation allow a request.
    assert admit.asked == admit_asked


def test_the_correction_runs_on_what_remains_of_the_one_deadline():
    # Read for the first request, for the recovery's admission, then for the correction it sends.
    clock = iter([30.0, 20.0, 12.5])
    client = ScriptedAuthor(EMPTY, GOOD)
    _call(client, allowance=RecoveryAllowance(admit=Admit(), remaining_seconds=lambda: next(clock)))
    assert [request.timeout_seconds for request in client.full] == [30.0, 12.5]


def test_a_send_that_skips_the_check_still_cannot_get_a_bad_answer_accepted():
    client = ScriptedAuthor(EMPTY, GOOD)

    def unhooked(attempt, _check):
        return execute_structured_operation(client, purpose=AUTHORING_PURPOSE, prompt=attempt.prompt,
                                            result_model=FollowupProbeAuthored)

    assert _call(client, send=unhooked).answer == GOOD
    assert len(client.requests) == 2


def test_other_failures_of_the_send_are_the_callers_own():
    for error in (AIProviderUnavailable("down"), AIOutputTruncated("cut"), AIInvalidOutput("bad json")):
        client = ScriptedAuthor(error)
        with pytest.raises(type(error)):
            _call(client)
        assert len(client.requests) == 1
    assert not issubclass(ContractRejected, AIProviderUnavailable)


def test_checked_structured_call_returns_the_accepted_answer():
    client = ScriptedAuthor(EMPTY, GOOD)
    send = operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored)
    assert checked_structured_call(first_prompt=FIRST, contract=CONTRACT, send=send,
                                   recovery=RecoveryAllowance(admit=Admit()), checkpoint=None,
                                   failure=refused) == GOOD
    assert [attempt.ordinal for attempt in send.attempts] == [0, 1]
    assert [attempt.correcting for attempt in send.attempts] == [None, "empty_question_or_key"]


# -- resuming -----------------------------------------------------------------------------------------------------


def test_a_restored_owed_correction_is_sent_instead_of_the_first_request():
    client = ScriptedAuthor(GOOD)
    result = _call(client, allowance=RecoveryAllowance(admit=Admit(), state=RecoveryState(0, "empty_question_or_key")))
    assert client.requests == [(AUTHORING_PURPOSE, correction_prompt(FIRST, NONBLANK))]
    assert (result.answer, result.state) == (GOOD, RecoveryState(1, "empty_question_or_key"))


def test_a_resumed_spent_recovery_stays_spent():
    client = ScriptedAuthor(GOOD)
    admit = Admit()
    with pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(admit=admit, state=RecoveryState(1, "empty_question_or_key")))
    assert client.requests == [] and admit.asked == 0
    assert (raised.value.info.reason, raised.value.info.sends) == ("contract_failed", 0)
    # Spent on a schema repair before the restart: the first request is the caller's to resend, the recovery is not.
    client = ScriptedAuthor(EMPTY, GOOD)
    with pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(admit=admit, state=RecoveryState(1)))
    assert len(client.requests) == 1 and admit.asked == 0
    assert raised.value.info.reason == "contract_failed"


def test_a_deferred_correction_is_recorded_and_sent_on_the_next_run():
    record = Recorder()
    client = ScriptedAuthor(EMPTY)
    with pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(admit=Admit(), record=record, defer=True))
    assert len(client.requests) == 1 and raised.value.info.reason == "correction_deferred"
    stored = record.last.as_dict()
    assert stored == {"recoveries": 0, "owed": "empty_question_or_key"}

    client = ScriptedAuthor(GOOD)
    result = _call(client, allowance=RecoveryAllowance(admit=Admit(), state=RecoveryState.from_dict(stored),
                                                        defer=True))
    assert result.answer == GOOD
    assert client.requests == [(AUTHORING_PURPOSE, correction_prompt(FIRST, NONBLANK))]


def test_an_owed_correction_the_contract_no_longer_declares_sends_nothing():
    client = ScriptedAuthor(GOOD)
    with pytest.raises(Refused) as raised:
        _call(client, allowance=RecoveryAllowance(admit=Admit(), state=RecoveryState(0, "retired_predicate")))
    assert client.requests == [] and raised.value.info.reason == "unknown_requirement"


class _Crash(BaseException):
    """The process dies here."""


class _Store:
    def __init__(self, *, crash_on_save: bool = False):
        self.rows: dict = {}
        self.crash_on_save = crash_on_save

    def model_checkpoint(self, cache_key):
        return {"result": self.rows[cache_key]} if cache_key in self.rows else None

    def save_model_checkpoint(self, cache_key, *, purpose, result, usage=None):
        if self.crash_on_save:
            self.crash_on_save = False
            raise _Crash()
        self.rows.setdefault(cache_key, result)

    def discard_model_checkpoint(self, cache_key, *, result=None):
        if result is None or self.rows.get(cache_key) == result:
            self.rows.pop(cache_key, None)


def _checkpoint(store):
    return ModelCheckpoint(store, "key:original", AUTHORING_PURPOSE, FollowupProbeAuthored.model_validate)


def test_a_crash_after_the_rejection_resumes_with_the_correction_not_the_first_request():
    record = Recorder()

    def admit():
        raise _Crash()

    client = ScriptedAuthor(EMPTY)
    with pytest.raises(_Crash):
        _call(client, allowance=RecoveryAllowance(admit=admit, record=record))
    client = ScriptedAuthor(GOOD)
    _call(client, allowance=RecoveryAllowance(admit=Admit(), state=record.last, record=record))
    assert client.requests == [(AUTHORING_PURPOSE, correction_prompt(FIRST, NONBLANK))]


def test_a_crash_after_the_reservation_never_sends_the_recovery_twice():
    record = Recorder()
    client = ScriptedAuthor(EMPTY, _Crash())
    with pytest.raises(_Crash):
        _call(client, allowance=RecoveryAllowance(admit=Admit(), record=record))
    assert record.last == RecoveryState(1, "empty_question_or_key")
    client = ScriptedAuthor(GOOD)
    with pytest.raises(Refused):
        _call(client, allowance=RecoveryAllowance(admit=Admit(), state=record.last))
    assert client.requests == []


def test_a_crash_before_the_checkpoint_save_recovers_the_correction_from_its_receipt_under_the_original_key():
    record, store, events = Recorder(), _Store(crash_on_save=True), []
    client = ScriptedAuthor(EMPTY, GOOD)
    with observe_model_calls(lambda action, event: events.append((action, event))), pytest.raises(_Crash):
        _call(client, allowance=RecoveryAllowance(admit=Admit(), record=record), checkpoint=_checkpoint(store))
    assert store.rows == {}

    # The restart: nothing is sent again; the paid correction is read back from its receipt.
    receipts = [{"status": receipt["status"], "prompt_hash": receipt["prompt_hash"],
                 "output_text": receipt.get("output_text"), "budget_json": receipt["budget_json"]}
                for receipt in reversed(root_receipts(events))]
    found = recover_from_receipts(receipts, first_prompt=FIRST, request_key="key:original", contract=CONTRACT,
                                  read=FollowupProbeAuthored.model_validate_json)
    assert found is not None and found[0] == GOOD
    _checkpoint(store).save(found[0])
    client = ScriptedAuthor()
    result = _call(client, allowance=RecoveryAllowance(admit=Admit(), state=record.last),
                   checkpoint=_checkpoint(store))
    assert (result.answer, result.reused, client.requests) == (GOOD, True, [])


# -- receipts -----------------------------------------------------------------------------------------------------


def test_a_rejected_answer_finishes_its_operation_receipt_as_failed_and_the_correction_names_its_original():
    events: list = []
    client = ScriptedAuthor(EMPTY, GOOD)
    with observe_model_calls(lambda action, event: events.append((action, event))):
        _call(client, request_key="key:original")
    first, correction = root_receipts(events)
    assert (first["status"], first["error_type"]) == ("failed", "ContractRejected")
    assert first["output_text"] == EMPTY.model_dump_json()  # kept for analysis, never reused
    assert first["budget_json"] is None and first["prompt_hash"] == content_key(FIRST)
    assert correction["status"] == "completed"
    assert correction["prompt_hash"] == content_key(correction_prompt(FIRST, NONBLANK))
    assert json.loads(correction["budget_json"]) == {RECOVERY_NOTE: {
        "request_key": "key:original", "failed": "empty_question_or_key", "ordinal": 1}}


def test_without_a_contract_an_operation_and_its_receipt_are_as_before():
    events: list = []
    client = ScriptedAuthor(EMPTY)
    with observe_model_calls(lambda action, event: events.append((action, event))):
        answer = execute_structured_operation(client, purpose=AUTHORING_PURPOSE, prompt=FIRST,
                                              result_model=FollowupProbeAuthored)
    assert answer == EMPTY
    [receipt] = root_receipts(events)
    assert (receipt["status"], receipt["budget_json"], receipt["output_text"]) == (
        "completed", None, EMPTY.model_dump_json())
    # Outside a checked call the provider hooks change nothing.
    assert (claim_schema_repair(), recovery_remaining_seconds(), correction_in_flight()) == (True, None, False)


def _receipt(prompt, answer, *, note=None, status="completed"):
    budget = None if note is None else json.dumps({RECOVERY_NOTE: note})
    return {"status": status, "prompt_hash": content_key(prompt), "output_text": answer.model_dump_json(),
            "budget_json": budget}


def test_receipt_recovery_reruns_the_contract_and_checks_the_correction_linkage():
    corrected = correction_prompt(FIRST, NONBLANK)
    note = {"request_key": "key:original", "failed": "empty_question_or_key", "ordinal": 1}

    def recover(*receipts):
        found = recover_from_receipts(list(receipts), first_prompt=FIRST, request_key="key:original",
                                      contract=CONTRACT, read=FollowupProbeAuthored.model_validate_json)
        return None if found is None else found[0]

    # A completed receipt whose answer parses but fails the contract is never reused.
    assert recover(_receipt(FIRST, EMPTY)) is None
    assert recover(_receipt(FIRST, GOOD, status="failed")) is None
    assert recover(_receipt(corrected, GOOD, note={**note, "request_key": "key:other"})) is None
    assert recover(_receipt(corrected, GOOD, note={**note, "failed": "criteria_contract_invalid"})) is None
    assert recover(_receipt(corrected, GOOD, note={**note, "ordinal": 2})) is None
    assert recover(_receipt(FIRST, GOOD, note=note)) is None  # a note on a prompt that is not the correction
    assert recover(_receipt(corrected, EMPTY, note=note)) is None
    assert recover(_receipt(corrected, GOOD, note=note), _receipt(FIRST, EMPTY)) == GOOD
    assert recover(_receipt(FIRST, GOOD)) == GOOD
    assert recover_from_receipts([_receipt(corrected, GOOD, note=note)], first_prompt=FIRST, request_key=None,
                                 contract=CONTRACT, read=FollowupProbeAuthored.model_validate_json) is None


# -- transports ---------------------------------------------------------------------------------------------------


class _LegacyEndpoint:
    """An endpoint adapter that builds its request from the legacy context, never the prompt."""

    provider_name = "legacy"
    provider_type = "http_adapter"
    model = "legacy-model"

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = 0

    def supports(self, capability):
        return capability == "legacy_followup"

    def complete_legacy(self, request, *, context):
        self.calls += 1
        return self.answers.pop(0)


def test_a_correction_is_refused_over_a_legacy_endpoint_that_cannot_carry_it():
    client = _LegacyEndpoint(EMPTY, GOOD)
    send = operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored,
                          legacy_capability="legacy_followup", legacy_context=CONTEXT)
    with pytest.raises(AIProviderUnavailable, match="legacy"):
        _call(client, send=send)
    assert client.calls == 1
    # A first request over the same endpoint is served as before.
    client = _LegacyEndpoint(GOOD)
    send = operation_send(client, purpose=AUTHORING_PURPOSE, result_model=FollowupProbeAuthored,
                          legacy_capability="legacy_followup", legacy_context=CONTEXT)
    assert _call(client, send=send).answer == GOOD

