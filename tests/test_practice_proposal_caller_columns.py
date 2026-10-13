"""S0: proposal receipts record who asked; Phase 5b's receipts are unchanged."""
from __future__ import annotations

import json

from learnloop.practice_index.retrieval import PracticeConstraints, find_practice
from tests.practice_index_fakes import FakePracticeLLM
from tests.source_service_fakes import build_service_vault, loaded


def _row(repository, proposal_id):
    with repository.connection() as connection:
        return dict(connection.execute(
            "SELECT * FROM practice_index_proposals WHERE id=?", (proposal_id,)).fetchone())


def test_a_service_caller_is_recorded_with_its_intent(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    result = find_practice(vault, repository, "eigenvalues of a matrix", {}, origin="rpc",
                           rerank_client=FakePracticeLLM(), caller={"kind": "plan", "ref": "plan_1"})
    row = _row(repository, result["proposal_id"])
    assert (row["origin"], row["caller"], row["caller_ref"], row["intent"]) == ("rpc", "plan", "plan_1", "practice")
    proposed = json.loads(row["proposed_json"])
    assert proposed and all(entry["kind"] == "item" and "rationale" in entry for entry in proposed)


def test_without_a_caller_the_receipt_is_phase_5b_s(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault = loaded(paths)
    result = find_practice(vault, repository, "eigenvalues of a matrix", {}, rerank_client=FakePracticeLLM())
    row = _row(repository, result["proposal_id"])
    assert (row["caller"], row["caller_ref"], row["intent"]) == (None, None, None)
    assert set(json.loads(row["proposed_json"])[0]) == {"practice_item_id", "rank", "relevance"}
    # New constraint fields at their defaults leave the stored constraints as before.
    assert set(json.loads(row["constraints_json"])) == {
        "limit", "learning_object_ids", "subjects", "facet_ids", "practice_modes", "exclude_item_ids",
        "min_difficulty", "max_difficulty", "rerank"}


def test_reader_intent_aliases_are_canonicalized():
    assert PracticeConstraints(intent="diagnostic_probe").intent == "discriminate"
    assert PracticeConstraints(intent="retention_check").intent == "retention"
    assert PracticeConstraints.from_mapping({"intent": None}).intent == "practice"
