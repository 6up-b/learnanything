"""S4 (§10.3): the tutor's typed tool requests: leak check, receipts, eager and lazy runs."""
from __future__ import annotations

from learnloop.db.stores.source_service import tool_call, tool_call_runs, tool_calls
from learnloop.instructional.tools import TOOL_REQUEST_TASK, tutor_request_handler, tutor_tool_requests
from learnloop.tutor.ai_contracts import TUTOR_QA_PROMPT_VERSION, TUTOR_QA_TOOLS_PROMPT_VERSION
from learnloop.tutor.tutor_qa import ask_question
from tests.source_service_fakes import build_service_vault, call, loaded, set_config, tool_tutor

REQUESTS = [
    {"tool": "find_practice", "query": "determinant row swaps", "intent": "practice",
     "facet_ids": ["facet_determinant", "facet_unknown"], "learning_object_ids": [],
     "reason": "Practice the sign rule on a fresh matrix."},
    {"tool": "find_sources", "query": "determinant changes sign", "intent": "explain", "facet_ids": [],
     "reason": "See how your notes explain it."},
    {"tool": "compare_sources", "query": "why does a row swap flip the sign", "facet_ids": [],
     "reason": "How do your books treat this?"},
    {"tool": "find_practice", "query": "ANSWER-pi_determinant_1", "intent": "practice", "facet_ids": [],
     "learning_object_ids": [], "reason": "The answer is ANSWER-pi_determinant_1"},
]


def _ask(paths, repository, client, *, handler=True, question="Why does the sign flip?"):
    return ask_question(loaded(paths), repository, client, context="practice", question_md=question,
                        practice_item_id="pi_determinant_1", session_id="s1",
                        tool_request_handler=tutor_tool_requests if handler else None)


def test_requests_are_validated_recorded_and_offered(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    tutor = tool_tutor(REQUESTS)
    result = _ask(paths, repository, tutor)
    assert tutor.result_models == ["TutorAnswerWithTools"]
    assert f"\n{TUTOR_QA_TOOLS_PROMPT_VERSION}" in tutor.prompts[0] or TUTOR_QA_TOOLS_PROMPT_VERSION in tutor.prompts[0]
    offered = result["tool_requests"]
    assert [entry["tool"] for entry in offered] == ["find_practice", "find_sources", "compare_sources"]
    assert [entry["run"] for entry in offered] == ["eager", "eager", "lazy"]
    assert offered[0]["arguments"]["facet_ids"] == ["facet_determinant"]
    assert offered[0]["dropped"][0]["id"] == "facet_unknown"
    with repository.connection() as connection:
        rows = tool_calls(connection, caller_kind="tutor", caller_ref=result["event_id"])
        ledger = connection.execute("SELECT verdict, rationale, judge_model FROM judgment_ledger WHERE task=?",
                                    (TOOL_REQUEST_TASK,)).fetchall()
    assert [row["status"] for row in rows] == ["requested", "requested", "requested", "refused"]
    leaked = rows[-1]
    assert {entry["why"] for entry in leaked["dropped"]} == {"answer_leak"}
    assert "ANSWER-pi_determinant_1" not in str(leaked["arguments"])
    assert len(ledger) == 4 and ledger[0]["judge_model"] == "fake-tutor-model"
    assert all("ANSWER-pi_determinant_1" not in row["rationale"] for row in ledger)


def test_eager_and_lazy_runs_write_run_rows(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    offered = _ask(paths, repository, tool_tutor(REQUESTS))["tool_requests"]
    for entry in offered:
        response = call(paths.root, "run_source_tool", {"toolCallId": entry["tool_call_id"]})
        assert "result" in response, response
        assert response["result"]["policy"] == "assisted_practice"
        with repository.connection() as connection:
            runs = tool_call_runs(connection, entry["tool_call_id"])
        assert [run["status"] for run in runs] == ["ran"]
    with repository.connection() as connection:
        refused = [row for row in tool_calls(connection) if row["status"] == "refused"][0]
    response = call(paths.root, "run_source_tool", {"toolCallId": refused["id"]})
    assert response["error"]["data"]["code"] == "refused"


def test_the_switch_restores_s0s_tutor_byte_for_byte(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    plain, tools = tool_tutor(REQUESTS), tool_tutor(REQUESTS)
    without = _ask(paths, repository, plain, handler=False)
    assert "tool_requests" not in without and plain.result_models == ["TutorAnswer"]
    assert TUTOR_QA_PROMPT_VERSION in plain.prompts[0] and "tool_requests" not in plain.prompts[0]
    _ask(paths, repository, tools)
    assert "tool_requests" in tools.prompts[0]
    set_config(paths, "source_service", tutor_tools=False)
    assert tutor_request_handler(loaded(paths)) is None


def test_the_sidecar_offers_requests_and_drops_the_s0_request(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import tutor_qa as handler

    paths, repository = build_service_vault(tmp_path / "vault")
    tutor = tool_tutor(REQUESTS[:2])

    class Runtime:
        ready = True

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("fake", Runtime(), tutor))
    response = call(paths.root, "ask_tutor_question", {
        "context": "practice", "question": "Why does the sign flip?", "practiceItemId": "pi_determinant_1",
        "sessionId": "s1"})["result"]
    assert [entry["tool"] for entry in response["toolRequests"]] == ["find_practice", "find_sources"]
    assert response["practiceRequest"] is None
    with repository.connection() as connection:
        assert tool_call(connection, response["toolRequests"][0]["toolCallId"])["caller_kind"] == "tutor"
