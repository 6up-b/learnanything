"""S4 (§10.1): practice_availability and find_facets make no model call."""
from __future__ import annotations

from dataclasses import dataclass

from learnloop.instructional.policy import caller_for
from learnloop.instructional.tools import run_tool
from tests.source_service_fakes import build_textbook_vault, loaded, table_counts


@dataclass
class _Estimate:
    minutes: float


def test_availability_counts_without_calling_a_model(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    before = table_counts(repository, ["model_call_receipts", "practice_index_proposals", "judgment_ledger"])
    caller = caller_for(repository, "agent", "cli")
    result = run_tool(loaded(paths), repository, "practice_availability",
                      {"facet_ids": ["facet_determinant"], "intents": ["practice", "discriminate"]}, caller=caller,
                      injections={"estimator": lambda item_id, mode, expected: _Estimate(4.0)})["result"]
    practice = result["intents"]["practice"]
    assert practice["admissible_items"] == 3 and practice["expected_minutes"]["median"] == 4.0
    assert practice["kinds"]["source_exercises"] >= 1
    assert "independence" in result["intents"]["discriminate"]["note"]
    facets = run_tool(loaded(paths), repository, "find_facets", {"query": "eigenvalues"}, caller=caller)["result"]
    assert facets["facets"][0]["facet_id"] == "facet_eigen" and "shortlist" in facets["label"]
    assert table_counts(repository, ["model_call_receipts", "practice_index_proposals", "judgment_ledger"]) == before
