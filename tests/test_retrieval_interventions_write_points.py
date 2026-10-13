"""S5 (§11.1): an intervention row only when retrieval is shown or served."""
from __future__ import annotations

import pytest

from learnloop.db.stores.source_service import interventions
from learnloop.instructional.exercises import exercise_candidates
from learnloop.instructional.interventions import (
    record_need_served, record_offer_shown, record_remediation_delivery, record_tutor_citations,
)
from learnloop.instructional.policy import caller_for, caller_for_question_event
from learnloop.instructional.practice import (
    propose_practice, proposed_exercise, record_exercise_pick, record_proposal_delivery, record_proposal_impressions,
    record_proposal_pick,
)
from learnloop.instructional.tools import run_tool
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, insert_question, loaded, set_config


def _rows(repository):
    with repository.connection() as connection:
        return interventions(connection)


@pytest.fixture
def textbook(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    return paths, repository, spans


def test_a_pick_records_the_impressions_shown_before_it(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = propose_practice(vault, repository, "determinant rows swapped sign", {},
                              caller=caller_for(repository, "plan"), rerank_client=llm)
    assert _rows(repository) == []  # retrieval alone writes nothing
    shown = record_proposal_impressions(vault, repository, proposal_id=result["proposal_id"], surface="plan",
                                        keys=[{"practice_item_id": item["practice_item_id"]}
                                              for item in result["items"]])
    assert _rows(repository) == []  # display alone writes nothing either
    picked = result["items"][0]["practice_item_id"]
    record_proposal_pick(repository, proposal_id=result["proposal_id"], practice_item_id=picked, vault=vault,
                         session_id="s1")
    [row] = _rows(repository)
    assert row["kind"] == "practice_pick" and row["proposal_id"] == result["proposal_id"]
    assert row["assets"]["practice_item_ids"] == [picked]
    assert sorted(row["impression_ids"]) == sorted(shown["impression_ids"])
    assert row["session_id"] == "s1" and row["design"] is None and row["propensity"] is None


def test_an_exercise_pick_and_a_need_served_are_source_exercise_rows(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = propose_practice(vault, repository, "solve for the eigenvalue x", {"kinds": "source_exercises"},
                              caller=caller_for(repository, "plan"), rerank_client=llm,
                              exercise_arm=exercise_candidates)
    entry = result["source_exercises"][0]
    proposed = proposed_exercise(repository, result["proposal_id"], entry["extraction_id"], entry["span_ids"])
    record_exercise_pick(repository, proposal_id=result["proposal_id"], entry=proposed)
    assert _rows(repository) == []  # the selection alone: nothing delivered yet
    record_proposal_delivery(vault, repository, {"proposal_id": result["proposal_id"],
                                                 "practice_item_id": "pi_eigen_1"},
                             exercise=proposed, import_id="sei_1")
    record_need_served(vault, repository, {"id": "need_1", "target_facets": ["facet_eigen"],
                                           "learning_object_id": "lo_matrices", "attempt_id": None},
                       practice_item_id="pi_eigen_1")
    rows = _rows(repository)
    assert [row["kind"] for row in rows] == ["source_exercise", "source_exercise"]
    assert rows[0]["assets"]["exercise_key"] == entry["key"] and rows[1]["caller_kind"] == "need"
    assert rows[0]["assets"]["practice_item_ids"] == ["pi_eigen_1"] and rows[0]["assets"]["import_id"] == "sei_1"


def test_passages_and_comparisons_are_recorded_when_shown(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    llm = FakeServiceLLM()
    caller = caller_for_question_event(vault, repository, insert_question(
        repository, context="library", question="determinant rows"))
    passages = run_tool(vault, repository, "find_sources", {"query": "determinant rows swapped sign"},
                        caller=caller, clients={"source_rerank": llm})
    comparison = run_tool(vault, repository, "compare_sources", {"query": "what happens when rows are swapped"},
                          caller=caller, clients={"source_rerank": llm, "source_compare": llm})
    assert _rows(repository) == []
    record_offer_shown(vault, repository, passages["tool_call_id"])
    record_offer_shown(vault, repository, comparison["tool_call_id"])
    rows = _rows(repository)
    assert [row["kind"] for row in rows] == ["source_passage", "comparison"]
    assert rows[0]["tool_call_id"] == passages["tool_call_id"] and rows[0]["assets"]["span_keys"]
    assert rows[0]["assets"]["source_versions"]


def test_tutor_citations_and_remediation_delivery(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    event_id = insert_question(repository, context="library", question="Why?", source_context={
        "citations": [{"extraction_id": "ext_text", "span_id": spans["ch5"][1]}],
        "source_retrieval": {"basis": "retrieved_verified"}})
    linked = insert_question(repository, context="library", question="Why?", source_context={
        "citations": [{"extraction_id": "ext_text", "span_id": spans["ch5"][1]}],
        "source_retrieval": {"basis": "lo_provenance"}})
    assert record_tutor_citations(vault, repository, linked) is None  # not retrieval
    record_tutor_citations(vault, repository, event_id)
    episode = {"id": "ep_1", "case_ref": "mc_1", "passages_shown": [
        {"role": "target", "facet_id": "facet_eigen", "basis": "ranked_verified",
         "span_view": {"extraction_id": "ext_text", "span_id": spans["ch5"][1], "revision_id": "rev_text"}}]}
    record_remediation_delivery(vault, repository, episode)
    rows = _rows(repository)
    assert [row["kind"] for row in rows] == ["source_passage", "remediation_passage"]
    assert rows[0]["question_event_id"] == event_id and rows[1]["remediation_episode_id"] == "ep_1"


def test_a_value_intent_pick_keeps_both_verdicts(textbook):
    from tests.test_discriminating_search import _valuer

    paths, repository, _spans = textbook
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        target_facet="facet_determinant", severity=0.8)
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = propose_practice(vault, repository, "determinant swap rows sign", {
        "intent": "discriminate", "learning_object_ids": ["lo_matrices"],
        "target_hypotheses": [{"kind": "misconception", "id": misconception}]},
        caller=caller_for(repository, "plan"), rerank_client=llm, valuer=_valuer(llm))
    picked = result["items"][0]["practice_item_id"]
    record_proposal_pick(repository, proposal_id=result["proposal_id"], practice_item_id=picked, vault=vault)
    [row] = _rows(repository)
    assert row["intent"] == "discriminate"
    assert row["eligibility"]["serve_time"]["intent"] == "discriminate"
    assert row["eligibility"]["valuation_time"]["exposure_rule_version"] == "reading_exposure_v1"
    assert row["state_ref"]["problems"][0]["key"] == "lo:lo_matrices"


def test_the_switch_off_writes_nothing(textbook):
    paths, repository, _spans = textbook
    set_config(paths, "source_service", interventions=False)
    vault = loaded(paths)
    record_need_served(vault, repository, {"id": "n", "learning_object_id": "lo_matrices"}, practice_item_id="pi_eigen_1")
    assert _rows(repository) == []


@pytest.mark.parametrize("interventions_on", [True, False])
def test_an_opened_offer_records_exposure_that_independence_reads(textbook, interventions_on):
    """F3 (Codex sources-build review): before, opening a passage offer wrote
    only a retrieval intervention, so the exercise it showed stayed "unseen"."""

    from learnloop.instructional.exposure import independent_check_eligibility

    paths, repository, spans = textbook
    if not interventions_on:
        set_config(paths, "source_service", interventions=False)
    vault = loaded(paths)
    llm = FakeServiceLLM()
    caller = caller_for_question_event(vault, repository, insert_question(
        repository, context="library", question="eigenvalue exercise"))
    exercise_span = spans["exercises"][1]  # "1. An eigenvalue t satisfies 3t + 5 = 20 ..."
    candidate = {"key": f"ext_text:{exercise_span}", "extraction_id": "ext_text", "span_ids": [exercise_span]}
    before = independent_check_eligibility(vault, repository, candidate, intent="discriminate")
    assert "source_exposed" not in before["reasons"]
    offer = run_tool(vault, repository, "find_sources",
                     {"query": "an eigenvalue t satisfies 3t + 5 = 20 solve for x"}, caller=caller,
                     clients={"source_rerank": llm})
    shown_key = f"ext_text:{exercise_span}"
    assert shown_key in offer["result_keys"]
    from learnloop.instructional.interventions import offer_shown

    shown = offer_shown(vault, repository, offer["tool_call_id"], span_keys=[shown_key])
    assert len(shown["exposure_event_ids"]) == 1
    events = repository.source_exposure_events(extraction_id="ext_text", span_id=exercise_span)
    assert [event["entity_id"] for event in events] == [offer["tool_call_id"]]
    after = independent_check_eligibility(vault, repository, candidate, intent="discriminate")
    assert "source_exposed" in after["reasons"]
    assert after["inputs"]["exposure_event_ids"] == shown["exposure_event_ids"]
    rows = _rows(repository)
    if interventions_on:
        assert rows[-1]["assets"]["exposure_event_ids"] == shown["exposure_event_ids"]
    else:
        assert rows == []
