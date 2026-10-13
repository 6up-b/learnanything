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
