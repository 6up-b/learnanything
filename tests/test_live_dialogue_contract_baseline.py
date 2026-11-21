"""Captured on unadopted code first; stopped surfaces retain their baseline behavior."""
import pytest

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable, AITurnTimeout
from learnloop.teacher import service
from learnloop.tutor import ai_contracts as C, teach_back, tutor_qa
from tests.live_dialogue_contract_helpers import chat, teacher
from tests.teach_back_helpers import _setup, TEACH_ITEM_ID


@pytest.mark.parametrize(("answers", "count", "closed", "shown"), [
    ([{"message": "Ready."}], 1, False, "Ready."),
    ([{"message": ""}, {"message": "Ready."}], 2, False, "Ready."),
    ([{"message": ""}] * 2 + [{"message": "Ready."}], 3, False, "Ready."),
    ([{"message": ""}] * 3, 3, True, None),
    ([{"message": " \n\t"}, {"message": "Ready."}], 2, False, "Ready."),
    ([{"message": " \n\t"}] * 2 + [{"message": "Ready."}], 3, False, "Ready."),
    ([{"message": " \n\t"}] * 3, 3, True, None),
    (["not json", {"message": "Ready."}], 2, False, "Ready."),
])
def test_teacher_physical_baseline(tmp_path, monkeypatch, answers, count, closed, shown):
    client, requests = chat(monkeypatch, answers)
    result, repository = teacher(tmp_path, client)
    assert len(requests) == count
    assert result["closed"] is closed
    messages = [entry["text"] for entry in result["feed"] if entry["kind"] == "message"]
    assert messages == ([] if shown is None else [shown])
    if closed:
        assert result["close_reason"] == "teacher_contract_failure"
    # The real service installs one existing gate over every attempt, including repairs.
    assert all(gate is client.gates[0] for gate in client.gates)
    assert client.gates[0].admitted == count
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM lesson_turns WHERE action='spend_reserved'").fetchone()[0] == count


@pytest.mark.parametrize("surface", ["teach_back", "tutor"])
@pytest.mark.parametrize(("answers", "count", "text"), [
    (["Ready."], 1, "Ready."),
    (["", "Ready."], 1, ""),
    (["", ""], 1, ""),
    (["malformed", "Ready."], 2, "Ready."),
    ([" \n\t"], 1, ""),
])
def test_surfaces_without_recovery_admission(tmp_path, monkeypatch, surface, answers, count, text):
    field = "question_md" if surface == "teach_back" else "answer_md"
    client, requests = chat(monkeypatch, [answer if answer == "malformed" else {field: answer} for answer in answers])
    _, vault, repository = _setup(tmp_path)
    if surface == "teach_back":
        state = teach_back.begin_teach_back(vault, repository, vault.practice_items[TEACH_ITEM_ID], opening_md="My explanation.")
        state, result = teach_back.next_question(vault, state, client)
        assert state.asked_count == 1
        assert result[field].strip() == text
        assert state.turns[-1].content_md.strip() == text
    else:
        result = tutor_qa.ask_question(vault, repository, client, context="practice", question_md="Why?",
                                       practice_item_id="pi_svd_define_001")
        assert result[field].strip() == text
        rows = repository.question_events(context="practice", practice_item_id="pi_svd_define_001")
        assert rows[0]["answer_status"] == "answered"
        assert rows[0][field].strip() == text
    assert len(requests) == count
    # Output/learner-question limits did not install a physical recovery authority.
    assert client.gates == [None]


@pytest.mark.parametrize("context_type", [C.TutorQAContext, C.ReaderTutorQAContext, C.ReaderTutorExplorableQAContext,
                                         C.ReaderTutorShowMeQAContext, C.ReaderTutorExplorableShowMeQAContext])
@pytest.mark.parametrize("tools", [False, True])
def test_tutor_schema_variants_and_tool_only_fixture(monkeypatch, context_type, tools):
    payload = {"answer_md": "" if tools else "Ready."}
    if tools:
        payload["tool_requests"] = [{"tool": "find_sources", "query": "matrix geometry", "intent": "explain",
                                     "facet_ids": [], "reason": "Look up an explanation."}]
    client, requests = chat(monkeypatch, [payload])
    answer = tutor_qa.request_tutor_answer(client, context_type(context="reader", question_md="Why?"), tools=tools)
    assert len(requests) == 1
    assert bool(getattr(answer, "tool_requests", [])) is tools
    assert answer.answer_md == ("" if tools else "Ready.")


@pytest.mark.parametrize("surface", ["teach_back", "tutor", "teacher"])
@pytest.mark.parametrize("error", [AITurnTimeout("Timed out."), AIInterrupted("Interrupted.")])
def test_initial_deadline_and_cancellation(tmp_path, monkeypatch, surface, error):
    client, requests = chat(monkeypatch, [{ {"teacher": "message", "teach_back": "question_md", "tutor": "answer_md"}[surface]: "Ready."}])
    # Stop at the public completion boundary after one physical response.
    # This models a terminal deadline/interrupt, not a retryable SDK timeout.
    client.error_after = error
    if surface == "teacher":
        with pytest.raises(service.LessonError):
            teacher(tmp_path, client)
    else:
        _, vault, repository = _setup(tmp_path)
        with pytest.raises(AIProviderUnavailable):
            if surface == "teach_back":
                state = teach_back.begin_teach_back(vault, repository, vault.practice_items[TEACH_ITEM_ID], opening_md="Explain.")
                teach_back.next_question(vault, state, client)
            else:
                tutor_qa.ask_question(vault, repository, client, context="practice", question_md="Why?",
                                      practice_item_id="pi_svd_define_001")
        if surface == "teach_back":
            assert state.asked_count == 0 and len(state.turns) == 1
        else:
            row = repository.question_events(context="practice", practice_item_id="pi_svd_define_001")[0]
            assert row["answer_md"] is None and row["answer_status"] == "failed"
    assert len(requests) == 1


def test_sanitized_empty_teach_back_baseline_stays_stopped(tmp_path, monkeypatch):
    client, requests = chat(monkeypatch, [{"question_md": "\x1b[31m\x1b[0m\x00"}, {"question_md": "Unused?"}])
    _, vault, repository = _setup(tmp_path)
    state = teach_back.begin_teach_back(vault, repository, vault.practice_items[TEACH_ITEM_ID], opening_md="Explain.")
    state, result = teach_back.next_question(vault, state, client)
    assert len(requests) == 1 and client.gates == [None]
    assert result["question_md"] == "" and state.asked_count == 1
