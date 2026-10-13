"""S4 (G3): results returned to a model never carry an item's answer."""
from __future__ import annotations

import json

from learnloop.instructional.policy import caller_for, caller_for_question_event
from learnloop.instructional.tools import run_tool
from tests.source_service_fakes import (
    FakeServiceLLM, build_textbook_vault, insert_question, loaded, set_item_answer,
)

ANSWER = "Swapping two rows of a matrix multiplies its determinant by -1, so the determinant changes sign."


def test_no_tool_result_contains_an_expected_answer(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    set_item_answer(paths, "pi_determinant_2", ANSWER)
    vault = loaded(paths)
    llm = FakeServiceLLM()
    practice = caller_for_question_event(vault, repository, insert_question(
        repository, context="practice", question="What happens to the determinant?",
        practice_item_id="pi_determinant_2"))
    agent = caller_for(repository, "agent", "cli")
    clients = {"source_rerank": llm, "practice_rerank": llm, "source_compare": llm}
    outputs = []
    for caller in (practice, agent):
        for name, args in (("find_practice", {"query": "determinant rows swapped sign"}),
                           ("find_sources", {"query": "determinant rows swapped sign"}),
                           ("compare_sources", {"query": "what happens to a determinant when rows are swapped"}),
                           ("find_facets", {"query": "determinant"})):
            outputs.append((caller.kind, name, json.dumps(run_tool(vault, repository, name, args, caller=caller,
                                                                   clients=clients)["result"])))
    for kind, name, text in outputs:
        assert "ANSWER-" not in text, (kind, name)
        assert "grading_rubric" not in text and "expected_answer" not in text
        if kind == "tutor":
            assert "multiplies its determinant by -1" not in text, name


SOLUTION_QUERY = "subtracting 5 gives 3x = 15 so the eigenvalue is x = 5"


def test_an_unbound_agent_never_reads_a_solution_block_or_an_exam(tmp_path):
    """F1 (Codex sources-build review): no item is bound, so the answer filter
    accepts everything; the model-reader role and assessment exclusions still
    apply, by effective role (Marker calls a solution block ``Text``)."""

    from learnloop.source_retrieval.find_sources import find_sources_for_caller

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    llm = FakeServiceLLM()
    agent = caller_for(repository, "agent", "cli")
    clients = {"source_rerank": llm, "practice_rerank": llm, "source_compare": llm}
    solution_keys = {f"ext_text:{span}" for span in spans["solutions"]}
    # The learner-facing contract still returns the solutions (reading is never
    # blocked), each labelled with its effective role.
    hits = find_sources_for_caller(vault, repository, SOLUTION_QUERY, caller=agent, verify=True,
                                   rerank_client=llm)
    roles = {f"{hit['extraction_id']}:{hit['span_id']}": hit["role"] for hit in hits.hits}
    assert any(key in roles and roles[key] == "solution" for key in solution_keys)
    assert all(hit["block_type"] != "solution" for hit in hits.hits)  # the old check could not fire
    for name in ("find_sources", "compare_sources"):
        result = run_tool(vault, repository, name, {"query": SOLUTION_QUERY}, caller=agent, clients=clients)["result"]
        text = json.dumps(result)
        assert "Subtracting 5 gives 3x = 15" not in text, name
        assert "Subtracting 4 gives 2x = 6" not in text, name
        assert "Exam question 1" not in text, name
        assert not solution_keys & set(result.get("passages") and [p["span_key"] for p in result["passages"]] or ())
        assert result["withheld_from_model"].get("solution", 0) >= 1, name
