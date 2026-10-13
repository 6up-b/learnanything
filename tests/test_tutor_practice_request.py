"""S0: the tutor's deterministic "Practice this" request, and its server-side caller."""
from __future__ import annotations

import pytest

from learnloop.instructional.offers import practice_request_for_answer
from learnloop.instructional.policy import caller_for_question_event
from learnloop.instructional.practice import constrain_for_caller, propose_practice
from learnloop.practice_index.retrieval import PracticeConstraints
from learnloop.source_retrieval.policy import PolicyRefused, derive_policy
from tests.practice_index_fakes import FakePracticeLLM
from tests.source_service_fakes import build_service_vault, call, insert_question, loaded


def test_the_request_is_deterministic_and_excludes_the_current_item(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    event_id = insert_question(repository, context="practice", question="Why are eigenvalues roots?",
                               practice_item_id="pi_eigen_1", facets=["facet_eigen", "facet_unknown"])
    event = repository.question_event(event_id)
    first = practice_request_for_answer(vault, event)
    assert first == practice_request_for_answer(vault, event)
    assert first["caller"] == {"kind": "tutor", "ref": event_id}
    request = first["request"]
    assert request == {
        "query": "Why are eigenvalues roots?",
        "learning_object_ids": ["lo_matrices"],
        "facet_ids": ["facet_eigen"],
        "exclude_item_ids": ["pi_eigen_1"],
        "intent": "practice",
    }
    assert practice_request_for_answer(vault, event, exercise_arm=True)["request"]["kinds"] == "both"


def test_no_request_for_an_unanswered_question(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    event_id = insert_question(repository, context="practice", question="Why?",
                               practice_item_id="pi_eigen_1", answered=False)
    assert practice_request_for_answer(loaded(paths), repository.question_event(event_id)) is None


def test_the_caller_is_rederived_on_the_server_and_cannot_widen(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    event_id = insert_question(repository, context="feedback", question="What went wrong?",
                               practice_item_id="pi_eigen_2")
    caller = caller_for_question_event(vault, repository, event_id)
    assert caller.item_id == "pi_eigen_2" and caller.learning_object_ids == ("lo_matrices",)
    assert derive_policy(caller)[0] == "assisted_practice"
    # A request that does not exclude the item still never proposes it.
    widened = constrain_for_caller(PracticeConstraints(exclude_item_ids=()), caller)
    assert "pi_eigen_2" in widened.exclude_item_ids
    result = propose_practice(vault, repository, "eigenvalues characteristic polynomial", {},
                              caller=caller, rerank_client=FakePracticeLLM())
    assert "pi_eigen_2" not in {item["practice_item_id"] for item in result["items"]}
    assert result["caller"]["policy"] == "assisted_practice"
    with repository.connection() as connection:
        row = connection.execute("SELECT caller, caller_ref, intent FROM practice_index_proposals").fetchone()
    assert tuple(row) == ("tutor", event_id, "practice")


def test_a_cold_administration_proposes_nothing(tmp_path, monkeypatch):
    from learnloop.instructional import policy as policy_module

    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    event_id = insert_question(repository, context="practice", question="Why?", practice_item_id="pi_eigen_1")
    monkeypatch.setattr(policy_module, "cold_administration_open", lambda repo, item_id: item_id == "pi_eigen_1")
    caller = caller_for_question_event(vault, repository, event_id)
    assert derive_policy(caller)[0] == "cold_attempt"
    with pytest.raises(PolicyRefused):
        propose_practice(vault, repository, "eigenvalues", {}, caller=caller)


def test_ask_tutor_question_returns_the_request(monkeypatch, tmp_path):
    from learnloop_sidecar.handlers import tutor_qa as handler

    paths, repository = build_service_vault(tmp_path / "vault")
    event_id = insert_question(repository, context="practice", question="How do I expand a determinant?",
                               practice_item_id="pi_determinant_1", facets=["facet_determinant"])

    class Runtime:
        ready = True

    def fake_ask(*args, **kwargs):
        return {"event_id": event_id, "answer_md": "ok", "question_type": "mechanism", "facets": [],
                "hint_equivalent": True, "leak_suspected": False, "citations": [], "remaining": 2}

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("codex", Runtime(), object()))
    monkeypatch.setattr(handler, "ask_question", fake_ask)
    response = call(paths.root, "ask_tutor_question", {
        "context": "practice", "question": "How do I expand a determinant?",
        "practiceItemId": "pi_determinant_1", "sessionId": "s1"})
    offer = response["result"]["practiceRequest"]
    assert offer["caller"] == {"kind": "tutor", "ref": event_id}
    assert offer["request"]["excludeItemIds"] == ["pi_determinant_1"]
    # The frontend sends the request back as-is; the server derives the caller.
    found = call(paths.root, "find_practice", {**offer["request"], "caller": offer["caller"]})
    assert "result" in found, found
    assert found["result"]["caller"]["policy"] == "assisted_practice"
    assert "pi_determinant_1" not in {item["practiceItemId"] for item in found["result"]["items"]}


def test_the_offer_switch_removes_the_request(monkeypatch, tmp_path):
    from learnloop_sidecar.handlers import tutor_qa as handler
    from tests.source_service_fakes import set_config

    paths, repository = build_service_vault(tmp_path / "vault")
    set_config(paths, "source_service", tutor_offers=False)
    event_id = insert_question(repository, context="practice", question="Why?", practice_item_id="pi_eigen_1")

    class Runtime:
        ready = True

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("codex", Runtime(), object()))
    monkeypatch.setattr(handler, "ask_question", lambda *a, **k: {
        "event_id": event_id, "answer_md": "ok", "question_type": "mechanism", "facets": [],
        "hint_equivalent": True, "leak_suspected": False, "citations": [], "remaining": 2})
    response = call(paths.root, "ask_tutor_question", {
        "context": "practice", "question": "Why?", "practiceItemId": "pi_eigen_1", "sessionId": "s1"})
    assert response["result"]["practiceRequest"] is None


def test_an_unknown_frontend_caller_kind_is_refused(tmp_path):
    paths, _repository = build_service_vault(tmp_path / "vault")
    response = call(paths.root, "find_practice", {"query": "eigenvalues", "caller": {"kind": "router"}})
    assert response["error"]["data"]["code"] == "validation_error"
    assert "router" in response["error"]["message"]
