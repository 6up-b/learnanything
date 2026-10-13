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


# -- Codex re-review F11: the calibration fields §11.4 says this stage supplies ---------------


def test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement(tmp_path):
    """The outcome join derives the posterior movement on the target
    hypotheses from persisted rows: the problem's prior, the check's member-0
    likelihood row and the observed bucket (no model call)."""

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.db.stores.source_service import outcomes
    from learnloop.substrate.intervention_outcomes import rebuild_intervention_outcomes

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
    picked = section["groups"]["valued"][0]["ref"]
    record_proposal_pick(repository, proposal_id=result["proposal_id"], practice_item_id=picked, vault=vault)
    with repository.connection() as connection:
        [row] = interventions(connection)
    valuation = row["valuation"]
    assert valuation["prior"] and valuation["likelihood"], valuation
    assert set(valuation["likelihood"]) == set(valuation["prior"])
    complete_self_graded_attempt(loaded(paths), repository,
                                 AttemptDraft(practice_item_id=picked, learner_answer_md="it flips sign",
                                              attempt_type="independent_attempt", session_id=None),
                                 SelfGradeInput(criterion_points={"correct": 4}, fatal_errors=[], confidence=3))
    rebuild_intervention_outcomes(loaded(paths), repository)
    with repository.connection() as connection:
        outcome = outcomes(connection)[row["id"]]
    movement = outcome["hypothesis_movement"]
    assert movement["status"] == "computed", movement
    assert movement["observed_bucket"] == outcome["observed_bucket"]
    assert abs(sum(movement["posterior"].values()) - 1.0) < 1e-6
    assert movement["entropy_before_nats"] >= 0 and "information_gained_nats" in movement
    assert movement["basis"] == "bayes_update_member0"


def test_decision_fields_reach_the_record_and_the_outcome_derives_the_action_change(tmp_path):
    """EVSI and the decision's actions are persisted on the record; the
    outcome reads the action after the observation from the persisted table."""

    from learnloop.instructional.interventions import _check_entry
    from learnloop.substrate.intervention_outcomes import outcome_for
    from tests.source_service_fakes import build_service_vault
    from tests.test_intervention_outcomes_replayer import T0, _attempt, _intervention

    from datetime import timedelta

    valuation = {"problems": [{
        "problem": {"key": "causal:hs_1", "prior": {"h1": 0.5, "h2": 0.5}, "state_hash": "s"},
        "mode": "decision", "verdict": "measure", "named_action": "repair_a", "action_kind": "current_action",
        "checks": [{"ref": "pi_eigen_1", "order": 1, "regime": "item_point",
                    "evsi": {"point": 0.4, "lcb": 0.2, "ucb": 0.5, "current_action": "repair_a"},
                    "action_before": "repair_a",
                    "action_by_outcome": {"high|none": "repair_a", "low|none": "repair_b"},
                    "likelihood": {"h1": {"high|none": 0.9, "low|none": 0.1},
                                   "h2": {"high|none": 0.2, "low|none": 0.8}}}],
        "groups": {"valued": [], "bounded": [], "unvalued": []}}]}
    entry = _check_entry(valuation, "pi_eigen_1")
    assert entry["evsi"]["point"] == 0.4 and entry["action_before"] == "repair_a"
    assert entry["action_by_outcome"]["low|none"] == "repair_b" and entry["prior"] == {"h1": 0.5, "h2": 0.5}
    paths, _repository = build_service_vault(tmp_path / "vault")
    row = outcome_for(_intervention(valuation=entry), [_attempt("a", T0 + timedelta(minutes=3), correctness=0.0,
                                                                rubric_score=0)],
                      loaded(paths), as_of=T0 + timedelta(days=1), signals=[])
    assert row["observed_bucket"] == "low|none"
    assert row["action_before"] == "repair_a" and row["action_after"] == "repair_b" and row["action_flipped"] == 1
    assert row["hypothesis_movement"]["posterior"]["h2"] > 0.5


def test_a_studied_worked_example_records_the_seconds_since_exposure(tmp_path):
    """``seconds_since_related_exposure`` read a field the exposure rule never
    emitted; the rule now records when the studied example was shown."""

    from learnloop.instructional.exposure import independent_check_eligibility
    from learnloop.instructional.interventions import record_pick
    from learnloop.db.stores.practice_index import insert_proposal

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_text",
                                             "span_id": spans["worked"][1], "source_id": "src_text"})
    vault = loaded(paths)
    verdict = independent_check_eligibility(vault, repository, {"practice_item_id": "pi_eigen_1"},
                                            intent="discriminate",
                                            judge_client=FakeServiceLLM(equivalence_verdict="related"))
    assert verdict["worked_example"]["seconds_since_exposure"] is not None, verdict["worked_example"]
    with repository.connection() as connection:
        insert_proposal(connection, id="pp_x", created_at="2026-10-12T08:59:00Z", origin="rpc", query_id="q",
                        query_text="eigen", constraints={}, path="direct", path_reason="t", signals={},
                        reranked=True, rerank_status="reranked", rerank_model=None,
                        proposed=[{"practice_item_id": "pi_eigen_1", "rank": 1, "kind": "item"}], exclusions={},
                        manifest={}, algorithm_version="mvp-0.16", caller="plan", caller_ref=None,
                        intent="discriminate")
    record_pick(vault, repository, proposal_id="pp_x", practice_item_id="pi_eigen_1", serve_verdict=verdict)
    with repository.connection() as connection:
        [row] = interventions(connection)
    assert row["seconds_since_related_exposure"] is not None


def test_exposure_age_is_measured_at_delivery_not_at_valuation(tmp_path):
    """Codex third pass F13: an example studied at 10:00, valued at 10:05 and
    delivered at 11:05 left two eligibility records (300 s and 3,900 s), and
    their minimum (300 s) was persisted at delivery, an hour short. The age is
    now measured from the persisted exposure time at the delivery instant."""

    from datetime import datetime, timezone

    from learnloop.clock import FrozenClock
    from learnloop.db.stores.practice_index import insert_proposal
    from learnloop.instructional.exposure import independent_check_eligibility
    from learnloop.instructional.interventions import record_pick

    def at(text):
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_text",
                                             "span_id": spans["worked"][1], "source_id": "src_text",
                                             "created_at": "2026-10-13T10:00:00Z"})
    vault = loaded(paths)
    judge = FakeServiceLLM(equivalence_verdict="related")
    valued = independent_check_eligibility(vault, repository, {"practice_item_id": "pi_eigen_1"},
                                           intent="discriminate", at=at("2026-10-13T10:05:00"), judge_client=judge)
    served = independent_check_eligibility(vault, repository, {"practice_item_id": "pi_eigen_1"},
                                           intent="discriminate", at=at("2026-10-13T11:05:00"), judge_client=judge)
    assert valued["worked_example"]["seconds_since_exposure"] == 300.0
    assert served["worked_example"]["seconds_since_exposure"] == 3900.0
    with repository.connection() as connection:
        insert_proposal(connection, id="pp_age", created_at="2026-10-13T10:05:00Z", origin="rpc", query_id="q",
                        query_text="eigen", constraints={}, path="direct", path_reason="t", signals={},
                        reranked=True, rerank_status="reranked", rerank_model=None,
                        proposed=[{"practice_item_id": "pi_eigen_1", "rank": 1, "kind": "item"}], exclusions={},
                        manifest={}, algorithm_version="mvp-0.16", caller="plan", caller_ref=None,
                        intent="discriminate", valuation={"eligibility": {"pi_eigen_1": valued}})
    record_pick(vault, repository, proposal_id="pp_age", practice_item_id="pi_eigen_1", serve_verdict=served,
                clock=FrozenClock(at("2026-10-13T11:05:00")))
    with repository.connection() as connection:
        [row] = interventions(connection)
    assert row["seconds_since_related_exposure"] == 3900.0
    assert row["created_at"] == "2026-10-13T11:05:00Z"
    # A verdict recorded before the exposure stamps: its check time less the
    # age it measured then, carried to the delivery.
    from learnloop.instructional.interventions import seconds_since_related_exposure
    legacy = {"checked_at": "2026-10-13T10:05:00Z", "worked_example": {"seconds_since_exposure": 300.0},
              "inputs": {"seconds_since_impression": 120.0}}
    assert seconds_since_related_exposure([legacy, None], now="2026-10-13T11:05:00Z") == 3720.0
