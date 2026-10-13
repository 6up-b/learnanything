"""S4 (§10.1, G1, G2): the dispatcher derives the policy from the caller."""
from __future__ import annotations

import pytest

from learnloop.db.stores.source_service import tool_call, tool_call_runs
from learnloop.instructional import policy as policy_module
from learnloop.instructional.policy import caller_for, caller_for_question_event
from learnloop.instructional.tools import ToolArgumentsInvalid, request_tool, run_requested_tool, run_tool
from learnloop.source_retrieval.policy import PolicyRefused
from tests.source_service_fakes import (
    FakeServiceLLM, build_textbook_vault, insert_question, learning_state_tables, loaded, table_counts,
)


@pytest.fixture
def textbook(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    return paths, repository, spans


def test_each_caller_gets_its_policy_and_both_rows(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    agent = caller_for(repository, "agent", "cli")
    practice = caller_for_question_event(vault, repository, insert_question(
        repository, context="practice", question="Why does the sign flip?", practice_item_id="pi_determinant_2"))
    library = caller_for_question_event(vault, repository, insert_question(
        repository, context="library", question="Eigenvalues?", note_id=None))
    expected = {"agent": "reading", "practice": "assisted_practice", "library": "reading"}
    tables = learning_state_tables(repository)
    before = table_counts(repository, tables)
    for label, caller in (("agent", agent), ("practice", practice), ("library", library)):
        result = run_tool(vault, repository, "find_sources", {"query": "determinant rows swapped sign"},
                          caller=caller, clients={"source_rerank": FakeServiceLLM()})
        assert result["policy"] == expected[label]
        with repository.connection() as connection:
            request = tool_call(connection, result["tool_call_id"])
            runs = tool_call_runs(connection, result["tool_call_id"])
        assert request["row_kind"] == "request" and request["status"] == "requested"
        assert request["policy"] == expected[label] and request["context"]["kind"] == caller.kind
        assert [run["status"] for run in runs] == ["ran"] and runs[0]["parent_id"] == request["id"]
        if label == "practice":
            assert all(not passage["text"].startswith(("1.", "2.", "3.", "4."))
                       for passage in result["result"]["passages"])
    assert table_counts(repository, tables) == before  # tools never serve (G1)


def test_a_cold_administration_refuses_every_tool(textbook, monkeypatch):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    event_id = insert_question(repository, context="practice", question="Why?", practice_item_id="pi_eigen_1")
    monkeypatch.setattr(policy_module, "cold_administration_open", lambda repo, item_id: item_id == "pi_eigen_1")
    caller = caller_for_question_event(vault, repository, event_id)
    for name, args in (("find_practice", {"query": "eigen"}), ("find_facets", {"query": "eigen"}),
                       ("practice_availability", {})):
        with pytest.raises(PolicyRefused) as refused:
            run_tool(vault, repository, name, args, caller=caller)
        assert refused.value.code == "cold_attempt"
        with repository.connection() as connection:
            assert tool_call(connection, refused.value.tool_call_id)["status"] == "refused"


def test_a_cold_administration_opened_after_the_request_narrows_the_run(textbook, monkeypatch):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    event_id = insert_question(repository, context="practice", question="Why?", practice_item_id="pi_eigen_1")
    caller = caller_for_question_event(vault, repository, event_id)
    request = request_tool(vault, repository, "find_facets", {"query": "eigen"}, caller=caller)
    from learnloop.instructional import tools as tools_module

    monkeypatch.setattr(tools_module, "cold_administration_open", lambda repo, item_id: True)
    with pytest.raises(PolicyRefused):
        run_requested_tool(vault, repository, request["tool_call_id"])
    with repository.connection() as connection:
        assert [run["status"] for run in tool_call_runs(connection, request["tool_call_id"])] == ["failed"]


def test_a_request_cannot_name_an_item_or_widen_its_policy(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    caller = caller_for(repository, "agent", "cli")
    for widened in ({"query": "x", "policy": "post_attempt"}, {"query": "x", "practice_item_id": "pi_eigen_2"}):
        with pytest.raises(ToolArgumentsInvalid):
            run_tool(vault, repository, "find_sources", widened, caller=caller)
    with pytest.raises(PolicyRefused) as refused:
        request_tool(vault, repository, "find_facets", {"query": "x"}, caller=caller_for(repository, "plan"))
    assert refused.value.code == "caller_refused"
