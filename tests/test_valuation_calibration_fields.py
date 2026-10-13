"""S5 (§11.4): a valued check's intervention keeps what calibration needs."""
from __future__ import annotations

from learnloop.db.stores.source_service import interventions
from learnloop.instructional.policy import caller_for
from learnloop.instructional.practice import propose_practice, record_proposal_pick
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded
from tests.test_discriminating_search import _valuer


def test_a_valued_pick_keeps_predicted_outcomes_regime_and_minutes(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        target_facet="facet_determinant", severity=0.8)
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = propose_practice(vault, repository, "determinant swap rows sign", {
        "intent": "discriminate", "learning_object_ids": ["lo_matrices"],
        "target_hypotheses": [{"kind": "misconception", "id": misconception}]},
        caller=caller_for(repository, "plan"), rerank_client=llm, valuer=_valuer(llm))
    [section] = result["valuation"]["problems"]
    valued = section["groups"]["valued"]
    assert valued, section
    # Three near-identical items: the selector abstains (couldnt_reliably_distinguish),
    # so no check is licensed; a learner-initiated result still lists them in value order.
    assert [item["practice_item_id"] for item in result["items"]][:len(valued)] == [e["ref"] for e in valued]
    lcbs = [entry["value_minutes_lcb"] / entry["expected_minutes"] for entry in valued]
    assert lcbs == sorted(lcbs, reverse=True)
    picked = valued[0]["ref"]
    record_proposal_pick(repository, proposal_id=result["proposal_id"], practice_item_id=picked, vault=vault)
    with repository.connection() as connection:
        [row] = interventions(connection)
    valuation = row["valuation"]
    assert valuation["regime"] == "item_point" and valuation["expected_minutes"] > 0
    assert abs(sum(valuation["predicted_outcomes"].values()) - 1.0) < 1e-6
    assert valuation["robust_eig_nats"] is not None and "not yet calibrated" in valuation["scale"]
