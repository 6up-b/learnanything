"""The live teacher's one blank-message correction, under its actual lesson gate."""
import itertools
import json
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import observe_model_calls
from learnloop.ai.structured_contracts import correction_prompt, first_failure, recovery_note
from learnloop.teacher import service as S, episodes as E, te2 as T2, visuals as V
from learnloop.teacher.contracts import TeacherTurnV2, capabilities
from learnloop.vault.loader import load_vault
from tests.live_dialogue_contract_helpers import chat, teacher
from tests.structured_contracts_helpers import root_receipts
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients
from tests.teacher_te1_review_fixes_helpers import _metered, _turn


@pytest.mark.parametrize(("visuals", "episodes", "te2"), list(itertools.product([False, True], repeat=3)))
@pytest.mark.parametrize("blank", ["", " \n\t"])
def test_all_eight_turn_variants_check_inside_receipt(tmp_path, monkeypatch, visuals, episodes, te2, blank):
    paths, repository = build_teacher_vault(tmp_path / "vault", config='''
[teacher]
metered_price_per_million = 1.0
max_lesson_cost_usd = 10.0
''')
    vault = load_vault(paths.root)
    opened = S.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                           clients=clients(TeacherFake([{"message": "Welcome."}])))
    state = S.load_state(repository, opened["lesson_id"])
    client, requests = chat(monkeypatch, [{"message": blank}, {"message": "Ready."}])
    events = []
    outcome = S._Outcome()
    first = S._prompt(state, results=[], help_reply=False, visuals=visuals, episodes=episodes, te2=te2)
    with S._lesson_spend(vault, repository, state, clock=None), observe_model_calls(
            lambda action, event: events.append((action, event))):
        answer, _ = S._call_teacher(vault, repository, state, client, results=[], help_reply=False,
                                    outcome=outcome, clock=None,
                                    allowed=capabilities(visuals=visuals, episodes=episodes, probes=te2))
    model = T2.turn_model(E.turn_model(V.turn_model(visuals), episodes), te2)
    assert client.operations[0].result_model is model
    assert type(answer) is TeacherTurnV2
    assert len(requests) == 2 and outcome.usage["calls"] == 2
    assert client.operations[0].prompt == first and client.operations[0].timeout_seconds is None
    assert client.operations[1].prompt == correction_prompt(first, S.TEACHER_MESSAGE_CONTRACT[0])
    assert 0 < client.operations[1].timeout_seconds <= 40
    assert client.gates[0] is client.gates[1] and client.gates[0].admitted == 2
    rejected, accepted = root_receipts(events)
    assert (rejected["status"], rejected["error_type"]) == ("failed", "ContractRejected")
    assert json.loads(rejected["output_text"])["message"] == blank
    assert accepted["status"] == "completed"
    assert recovery_note(accepted["budget_json"])["failed"] == "blank_message"
    assert outcome.shown == [{"kind": "message", "text": "Ready.", "choices": []}]
    state = S.load_state(repository, state.lesson_id)
    turns = [row for row in state.turns if row["actor"] == "teacher" and row["validation"] == "ok"]
    assert [row["payload"]["turn"]["message"] for row in turns] == ["Welcome.", "Ready."]
    assert all("turn" not in row["payload"] for row in state.turns if row["validation"] == "invalid")
    assert first_failure(S.TEACHER_MESSAGE_CONTRACT, model(message=blank)) is not None


@pytest.mark.parametrize(("answers", "count", "closed"), [
    (["not json", {"message": ""}, {"message": "Ready."}], 3, False),
    ([{"message": ""}, "not json", {"message": "Ready."}], 3, False),
    (["not json", {"message": ""}, "not json", {"message": "Ready."}], 4, False),
    (["not json", {"message": ""}, "not json", {"message": ""}, {"message": "Ready."}], 5, False),
    (["not json", {"message": ""}] * 3, 6, True),
    # An ordinary schema failure still gets the old loop's next attempt.
    (["not json", "still bad", {"message": "Ready."}], 3, False),
    (["not json"] * 6, 6, True),
])
def test_schema_repairs_keep_their_own_rule(tmp_path, monkeypatch, answers, count, closed):
    client, requests = chat(monkeypatch, answers)
    result, _ = teacher(tmp_path, client)
    assert len(requests) == count and result["closed"] is closed
    assert client.gates[0].admitted == count


def test_three_blanks_close_and_resume_never_resends(tmp_path, monkeypatch):
    client, requests = chat(monkeypatch, [{"message": " "}, {"message": "\t"}, {"message": ""},
                                          {"message": "Unused."}])
    result, repository = teacher(tmp_path, client)
    assert result["closed"] and result["close_reason"] == "teacher_contract_failure"
    vault = load_vault(tmp_path / "vault")
    S.take_turn(vault, repository, lesson_id=result["lesson_id"], action="resume", payload={}, clients=clients(client))
    assert len(requests) == 3
    state = S.load_state(repository, result["lesson_id"])
    assert not [row for row in state.turns if row["actor"] == "teacher" and row["validation"] == "ok"]
    assert all("turn" not in row["payload"] for row in state.turns if row["validation"] == "invalid")


@pytest.mark.parametrize("first_failures", [
    [{"message": ""}, {"message": ""}],
    [{"message": ""}, {"message": "Ready.", "requests": [{"action": "close"}]}],
    [{"message": "Ready.", "requests": [{"action": "close"}]}, {"message": ""}],
])
def test_two_failed_turns_leave_the_existing_third_slot(tmp_path, monkeypatch, first_failures):
    client, requests = chat(monkeypatch, [*first_failures, {"message": "Recovered."}, {"message": "Unused."}])
    events = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        result, repository = teacher(tmp_path, client)
    assert len(requests) == 3 and client.gates[0].admitted == 3
    assert not result["closed"]
    assert [entry["text"] for entry in result["feed"] if entry["kind"] == "message"] == ["Recovered."]
    state = S.load_state(repository, result["lesson_id"])
    invalid = [row for row in state.turns if row["actor"] == "teacher" and row["validation"] == "invalid"]
    assert len(invalid) == 2 and state.failures == 0
    receipts = root_receipts(events)
    for index, turn in enumerate(first_failures):
        if not turn["message"]:
            assert "turn" not in invalid[index]["payload"]
            assert (receipts[index]["status"], receipts[index]["error_type"]) == ("failed", "ContractRejected")
    if not any(turn["message"] for turn in first_failures):
        assert client.operations[1].prompt == correction_prompt(client.operations[0].prompt,
                                                               S.TEACHER_MESSAGE_CONTRACT[0])
        assert recovery_note(receipts[2]["budget_json"]) is None


def test_real_gate_refuses_correction_without_new_funds(tmp_path):
    paths, repository, client, lesson_id, _ = _metered(tmp_path, [{"message": " "}, {"message": "Unused."}], cap_factor=1.5)
    result = _turn(paths, repository, lesson_id, client)
    assert result["closed"] and result["close_reason"] == "budget"
    assert len(client.prompts) == 2  # opening plus rejected blank; correction never sent


@pytest.mark.parametrize("stop", ["deadline", "cancelled"])
def test_stop_between_blank_and_correction_sends_nothing(tmp_path, monkeypatch, stop):
    client, requests = chat(monkeypatch, [{"message": ""}, {"message": "Unused."}])
    elapsed = [0.0]
    monkeypatch.setattr(S, "time", SimpleNamespace(monotonic=lambda: elapsed[0]))
    if stop == "deadline":
        client.after = lambda: elapsed.__setitem__(0, 41.0)
    else:
        def interrupted():
            if requests:
                raise AIInterrupted("Interrupted.")
        client.before = interrupted  # the provider's existing persistent interruption
    with pytest.raises(S.LessonError) as failure:
        teacher(tmp_path, client)
    assert failure.value.code == "plan_unavailable"
    assert len(requests) == 1


def test_other_contract_and_protection_failures_keep_their_three_turn_policy(tmp_path):
    fake = TeacherFake([{"message": "Ready.", "requests": [{"action": "close"}]}] * 3)
    result, _ = teacher(tmp_path, fake)
    assert result["closed"] and result["close_reason"] == "teacher_contract_failure"
    assert len(fake.prompts) == 3


@pytest.mark.parametrize("blank_at", [0, 1, 2])
def test_blank_recovery_does_not_add_to_other_consecutive_failures(tmp_path, monkeypatch, blank_at):
    bad = {"message": "Ready.", "requests": [{"action": "close"}]}
    answers = [bad, bad, bad]
    answers[blank_at] = {"message": ""}
    client, requests = chat(monkeypatch, [*answers, {"message": "Unused."}])
    result, _ = teacher(tmp_path, client)
    assert result["closed"] and result["close_reason"] == "teacher_contract_failure"
    assert len(requests) == 3


def test_blank_message_cannot_execute_an_otherwise_valid_action(tmp_path, monkeypatch):
    blank = {"message": " ", "requests": [{"action": "close", "close_reason": "goal_reached", "recap": "Done."}]}
    client, requests = chat(monkeypatch, [blank, blank, blank, {"message": "Unused."}])
    result, _ = teacher(tmp_path, client)
    assert len(requests) == 3
    assert result["close_reason"] == "teacher_contract_failure"
    assert not [entry for entry in result["feed"] if entry["kind"] == "message"]
