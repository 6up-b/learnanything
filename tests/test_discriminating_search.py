"""S2a: intents, typed constraints on both arms, open hypotheses, screens, exposure and paging."""
from __future__ import annotations

from dataclasses import dataclass
import json

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.instructional.discriminating import make_valuer
from learnloop.instructional.exercises import exercise_candidates
from learnloop.instructional.exposure import apply_dominance, independent_check_eligibility
from learnloop.instructional.practice import propose_practice
from learnloop.instructional.screen import ExerciseScreen, HypothesisSignature, classify
from learnloop.instructional.valuation import (
    causal_problem, check_tables, item_input, lo_problem, open_hypotheses, retention_problem,
)
from learnloop.instructional.validation import draft_validator
from learnloop.practice_index.retrieval import (
    IntentUnavailable, PracticeConstraints, exercise_filter, find_practice,
)
from learnloop.source_retrieval.policy import CallerContext
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call, loaded, set_config, table_counts


@dataclass
class _Estimate:
    minutes: float

    def as_dict(self):
        return {"minutes": self.minutes, "prior_source": "test"}


def estimator(item_id, mode, expected):
    return _Estimate(12.0 if mode == "proof" else 2.0)


@pytest.fixture
def textbook(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        correction_statement="Swapping two rows multiplies the determinant by -1", target_facet="facet_determinant",
        severity=0.8)
    return paths, repository, spans, misconception


def _valuer(llm):
    return make_valuer(estimator=estimator, screen_client=llm, judge_client=llm)


# -- typed constraints -----------------------------------------------------------------------


def test_reader_aliases_and_value_intent_without_a_valuer(textbook):
    paths, repository, _spans, _m = textbook
    constraints = PracticeConstraints.from_mapping({"unseen_required": True, "exclude_exposed_families": True,
                                                    "allow_generated_variants": False})
    assert constraints.unattempted_only and constraints.exclude_revealed_families and not constraints.allow_generated
    with pytest.raises(IntentUnavailable):
        find_practice(loaded(paths), repository, "determinant", {"intent": "diagnostic_probe"})


def test_item_filters_and_the_required_estimator(textbook):
    paths, repository, _spans, _m = textbook
    vault = loaded(paths)
    complete_self_graded_attempt(vault, repository,
                                 AttemptDraft(practice_item_id="pi_determinant_1", learner_answer_md="x",
                                              attempt_type="independent_attempt"),
                                 SelfGradeInput(criterion_points={"correct": 4}, fatal_errors=[], confidence=3))
    result = find_practice(loaded(paths), repository, "determinant cofactor rows",
                           {"unattempted_only": True, "facet_ids": ["facet_determinant"]})
    assert "pi_determinant_1" not in {item["practice_item_id"] for item in result["items"]}
    assert result["admission"]["excluded"]["attempted"] == 1
    with pytest.raises(IntentUnavailable):
        find_practice(loaded(paths), repository, "determinant", {"max_estimated_minutes": 5})
    timed = find_practice(loaded(paths), repository, "determinant", {"max_estimated_minutes": 5},
                          estimator=estimator)
    assert timed["status"] == "ok"
    every = find_practice(loaded(paths), repository, "determinant eigen",
                          {"facet_ids": ["facet_determinant", "facet_eigen"], "facet_match": "all"})
    assert every["items"] == []


def test_raw_exercise_filters_read_quote_verified_metadata(textbook):
    constraints = PracticeConstraints(facet_ids=("facet_eigen",))
    assert exercise_filter(constraints, None, None) == "failed_unknown"
    assert exercise_filter(constraints, {"facets": ["facet_determinant"]}, None) == "facets"
    assert exercise_filter(constraints, {"facets": ["facet_eigen"]}, None) is None
    every = PracticeConstraints(facet_ids=("facet_eigen", "facet_determinant"), facet_match="all")
    assert exercise_filter(every, {"facets": ["facet_eigen"]}, None) == "facet_match_all"
    timed = PracticeConstraints(max_estimated_minutes=5)
    assert exercise_filter(timed, {"facets": [], "practice_mode": None}, estimator) == "failed_unknown"
    assert exercise_filter(timed, {"practice_mode": "proof"}, estimator) == "too_long"
    with pytest.raises(IntentUnavailable):
        exercise_filter(timed, {"practice_mode": "short_answer"}, None)


def test_post_import_validation_rejects_lo_fallback_and_long_drafts(textbook):
    paths, _repository, _spans, _m = textbook
    vault = loaded(paths)

    @dataclass
    class Draft:
        payload: dict
        facet_basis: str

    validate = draft_validator(vault, PracticeConstraints(facet_ids=("facet_eigen",), max_estimated_minutes=5),
                               intent="discriminate", estimator=estimator)
    ok = validate(Draft({"id": "d", "evidence_facets": ["facet_eigen"], "practice_mode": "short_answer"}, "authored"))
    assert ok["ok"]
    fallback = validate(Draft({"id": "d", "evidence_facets": ["facet_eigen"], "practice_mode": "short_answer"},
                              "lo_fallback"))
    assert not fallback["ok"] and "fallback" in fallback["reason"]
    long = validate(Draft({"id": "d", "evidence_facets": ["facet_eigen"], "practice_mode": "proof"}, "authored"))
    assert not long["ok"] and "minutes" in long["reason"]
    wrong = validate(Draft({"id": "d", "evidence_facets": ["facet_matmul"], "practice_mode": "short_answer"},
                           "authored"))
    assert wrong["correction"].startswith("this exercise turned out to practise facet_matmul")


# -- open hypotheses and tables --------------------------------------------------------------


def test_open_hypotheses_one_problem_per_space_with_typed_misses(textbook):
    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    problems, unavailable = open_hypotheses(
        vault, repository, refs=[{"kind": "misconception", "id": misconception},
                                 {"kind": "named_gap", "id": "gap_1"},
                                 {"kind": "causal_hypothesis", "id": "hs_missing"}])
    assert [problem.key for problem in problems] == ["lo:lo_matrices"]
    assert f"misconception:{misconception}" in problems[0].slots
    assert abs(sum(problems[0].prior.values()) - 1.0) < 1e-9
    reasons = {entry["reason"] for entry in unavailable}
    # Learner-text gaps are merged on main: an unknown gap is looked up, not unavailable.
    assert "unknown_named_gap" in reasons and "no_hypothesis_set" in reasons


def test_item_tables_are_normalized_and_labelled(textbook):
    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    problem, _ = lo_problem(vault, repository, "lo_matrices")
    candidate = item_input(vault, repository, problem, vault.practice_items["pi_determinant_1"], estimator=estimator)
    assert candidate.regime == "item_point" and len(candidate.members) == 3
    check_tables(problem, candidate.members)
    assert candidate.minutes_provenance["prior_source"] == "test"


def test_retention_needs_a_recent_assisted_success(textbook):
    paths, repository, _spans, _m = textbook
    problem, missing = retention_problem(loaded(paths), repository, "lo_matrices")
    assert problem is None and missing[0]["reason"] == "no_recent_assisted_success"


def _attempt(paths, repository, item_id, *, points, hints=0):
    complete_self_graded_attempt(loaded(paths), repository,
                                 AttemptDraft(practice_item_id=item_id, learner_answer_md="x",
                                              attempt_type="independent_attempt", hints_used=hints),
                                 SelfGradeInput(criterion_points={"correct": points}, fatal_errors=[], confidence=3))


def test_retention_is_posed_only_after_an_assisted_only_success_with_the_active_predictor(textbook):
    """F17 (Codex sources-build review): the "holds unaided" question needs a
    recent success that was assisted only, and its prior is the active
    predictor's P(success), not the mastery sigmoid relabelled."""

    from learnloop.placement.predictor import active_predictor

    paths, repository, _spans, _m = textbook
    _attempt(paths, repository, "pi_determinant_1", points=4)  # an unaided success
    problem, missing = retention_problem(loaded(paths), repository, "lo_matrices")
    assert problem is None and missing[0]["reason"] == "no_recent_assisted_success"
    _attempt(paths, repository, "pi_determinant_2", points=4, hints=1)  # now the latest success is assisted
    vault = loaded(paths)
    problem, missing = retention_problem(vault, repository, "lo_matrices")
    assert missing == [] and problem is not None
    expected = active_predictor(vault, repository).predict_item("pi_determinant_2").p_success
    assert abs(problem.prior["holds_unaided"] - expected) < 1e-9
    assert problem.prior_basis == "predictor:mastery_ekf"
    assert problem.context["predictor"]["version"] and problem.context["assisted_success_attempt_id"]
    _attempt(paths, repository, "pi_determinant_3", points=4)  # an unaided success after it
    problem, missing = retention_problem(loaded(paths), repository, "lo_matrices")
    assert problem is None and missing[0]["reason"] == "no_recent_assisted_success"
    # A failed unaided attempt after the assisted success leaves the question open.
    _attempt(paths, repository, "pi_determinant_1", points=4, hints=2)
    _attempt(paths, repository, "pi_determinant_2", points=0)
    assert retention_problem(loaded(paths), repository, "lo_matrices")[0] is not None


def test_causal_space_excludes_h_other_explicitly(textbook):
    paths, repository, _spans, _m = textbook
    from learnloop.diagnosis.probe_hypotheses import H_OTHER

    set_id = repository.insert_hypothesis_set(learning_object_id="lo_matrices", probe_phase_id="p",
                                              hypotheses=[{"label": "h1"}, {"label": "h2"}, {"label": H_OTHER}],
                                              prior={"h1": 0.4, "h2": 0.4, H_OTHER: 0.2},
                                              algorithm_version="mvp-0.6")
    problem, _ = causal_problem(loaded(paths), repository, set_id)
    assert problem.slots == ("h1", "h2") and problem.excluded_mass == {H_OTHER: 0.2}
    candidate = item_input(loaded(paths), repository, problem, loaded(paths).practice_items["pi_eigen_1"])
    assert candidate.regime == "structural" and candidate.missing[0].startswith("incomplete_likelihoods")


# -- screens ----------------------------------------------------------------------------------


def test_screens_are_noiseless_bounds_or_structural():
    refs = {"h1": "a", "h2": "b"}
    complete = ExerciseScreen(exercise_ref="x1", signatures=[
        HypothesisSignature(hypothesis_ref="h1", observable_signature="adds", signature_key="add"),
        HypothesisSignature(hypothesis_ref="h2", observable_signature="multiplies", signature_key="mul")],
        other_cause_signature="anything else", differ_observably=True)
    assert classify(complete, ("a", "b"), refs)["complete"] is True
    same = ExerciseScreen(exercise_ref="x1", signatures=[
        HypothesisSignature(hypothesis_ref="h1", observable_signature="adds", signature_key="add"),
        HypothesisSignature(hypothesis_ref="h2", observable_signature="adds too", signature_key="add")],
        other_cause_signature="", differ_observably=False)
    verdict = classify(same, ("a", "b"), refs)
    assert verdict["complete"] is False
    assert {"identical_signatures", "no_h_other_disposition"} <= set(verdict["reasons"])


# -- the exposure rule ------------------------------------------------------------------------


def _study_worked_example(repository, spans):
    repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_text",
                                             "span_id": spans["worked"][1], "source_id": "src_text"})


def test_equivalent_worked_example_excludes_both_independent_intents(textbook):
    paths, repository, spans, _m = textbook
    _study_worked_example(repository, spans)
    vault = loaded(paths)
    candidate = {"kind": "source_exercise", "extraction_id": "ext_text", "span_ids": [spans["exercises"][1]],
                 "statement": "1. An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x to find the eigenvalue.",
                 "learning_object_ids": ["lo_matrices"], "key": "srcex:1"}
    before = table_counts(repository, ["practice_attempts"])
    equivalent = FakeServiceLLM(equivalence_verdict="equivalent")
    for intent in ("discriminate", "retention"):
        verdict = independent_check_eligibility(vault, repository, candidate, intent=intent, judge_client=equivalent)
        assert not verdict["eligible"] and "equivalent_worked_example" in verdict["reasons"]
    related = FakeServiceLLM(equivalence_verdict="related")
    related.model = "fake-related-model"  # a new judge: the first verdicts are served from the ledger otherwise
    retention = independent_check_eligibility(vault, repository, candidate, intent="retention", judge_client=related)
    assert "related_worked_example" in retention["reasons"]
    discriminate = independent_check_eligibility(vault, repository, candidate, intent="discriminate",
                                                 judge_client=related)
    assert discriminate["eligible"] and discriminate["label"] == "you read a worked example like this one"
    assert independent_check_eligibility(vault, repository, candidate, intent="practice")["eligible"]
    assert table_counts(repository, ["practice_attempts"]) == before  # nothing fabricated


def test_dominance_never_puts_a_labelled_candidate_first_when_values_overlap():
    entries = [{"ref": "labelled", "value_minutes_lcb": 5.0, "value_minutes_ucb": 9.0},
               {"ref": "plain", "value_minutes_lcb": 4.0, "value_minutes_ucb": 8.0}]
    ordered = apply_dominance(entries, {"labelled": {"label": "you read a worked example like this one"}})
    assert [entry["ref"] for entry in ordered] == ["plain", "labelled"]


def test_an_earlier_impression_and_a_source_exposure_exclude(textbook):
    from learnloop.instructional.practice import record_proposal_impressions

    paths, repository, spans, _m = textbook
    vault = loaded(paths)
    result = find_practice(vault, repository, "determinant rows swapped", {}, rerank_client=FakeServiceLLM(),
                           caller={"kind": "tutor", "ref": "q"})
    shown = result["items"][0]["practice_item_id"]
    record_proposal_impressions(vault, repository, proposal_id=result["proposal_id"], surface="tutor_strip",
                                keys=[{"practice_item_id": shown}])
    seen = independent_check_eligibility(vault, repository, {"practice_item_id": shown}, intent="discriminate")
    assert "seen_in_proposal" in seen["reasons"]
    picked = independent_check_eligibility(vault, repository, {"practice_item_id": shown}, intent="discriminate",
                                           picked_proposal_id=result["proposal_id"])
    assert "seen_in_proposal" not in picked["reasons"]
    repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_text",
                                             "span_id": spans["exercises"][1], "source_id": "src_text"})
    exposed = independent_check_eligibility(vault, repository, {"kind": "source_exercise", "extraction_id": "ext_text",
                                                                "span_ids": [spans["exercises"][1]]},
                                            intent="retention")
    assert "source_exposed" in exposed["reasons"]


# -- discriminate end to end -----------------------------------------------------------------


def test_discriminate_values_items_and_bounds_exercises(textbook):
    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = find_practice(vault, repository, "determinant swap rows sign", {
        "intent": "discriminate", "learning_object_ids": ["lo_matrices"],
        "target_hypotheses": [{"kind": "misconception", "id": misconception}]},
        exercise_arm=exercise_candidates, valuer=_valuer(llm), rerank_client=llm, caller={"kind": "tutor", "ref": "q"})
    valuation = result["valuation"]
    section = valuation["problems"][0]
    assert section["problem"]["key"] == "lo:lo_matrices"
    assert section["scale"] == "LearnLoop's estimate; its scale is not yet calibrated"
    assert {entry["regime"] for entry in section["groups"]["valued"]} <= {"item_point"}
    assert result["paging"]["outcome"] in ("exhausted", "unjudged_remain", "perfect_information_bound")
    with repository.connection() as connection:
        row = connection.execute("SELECT intent, valuation_json FROM practice_index_proposals ORDER BY created_at DESC"
                                 ).fetchone()
    assert row["intent"] == "discriminate" and row["valuation_json"]


def test_system_initiated_item_point_checks_abstain(textbook):
    paths, repository, _spans, misconception = textbook
    llm = FakeServiceLLM()
    result = find_practice(loaded(paths), repository, "determinant swap rows sign", {
        "intent": "discriminate", "learning_object_ids": ["lo_matrices"]},
        valuer=_valuer(llm), rerank_client=llm, system_initiated=True)
    verdicts = {section["verdict"] for section in result["valuation"]["problems"]}
    assert verdicts <= {"abstain", "no_discriminating_instrument"}
    assert result["items"] == []  # a point model is not a license for a system-initiated check


def test_the_discriminating_search_switch_refuses_value_intents(textbook):
    paths, repository, _spans, _m = textbook
    set_config(paths, "source_service", discriminating_search=False)
    with pytest.raises(IntentUnavailable):
        propose_practice(loaded(paths), repository, "determinant", {"intent": "discriminate"},
                         caller=CallerContext(kind="plan"))
    response = call(paths.root, "find_practice", {"query": "determinant", "intent": "discriminate",
                                                  "caller": {"kind": "plan"}})
    assert response["error"]["data"]["code"] == "discriminating_search_off"


def test_paging_resumes_with_a_cursor(textbook):
    paths, repository, _spans, _m = textbook
    vault = loaded(paths)
    vault.config.practice_index.candidate_pool = 3
    first = find_practice(vault, repository, "matrix determinant eigen vector", {"limit": 2},
                          rerank_client=FakeServiceLLM())
    assert first["paging"]["outcome"] == "page" and first["paging"]["cursor"]["judged_items"]
    second = find_practice(vault, repository, "matrix determinant eigen vector", {"limit": 2},
                           rerank_client=FakeServiceLLM(), cursor=first["paging"]["cursor"])
    assert not set(first["paging"]["cursor"]["judged_items"]) & {item["practice_item_id"] for item in second["items"]}


def test_presentation_order_applies_dominance_inside_the_valued_group():
    from learnloop.instructional.discriminating import presentation_order

    receipt = {"problems": [{"checks": [{"ref": "c"}], "groups": {
        "valued": [{"ref": "c", "value_minutes_lcb": 9.0, "value_minutes_ucb": 12.0},
                   {"ref": "labelled", "value_minutes_lcb": 5.0, "value_minutes_ucb": 9.0},
                   {"ref": "plain", "value_minutes_lcb": 4.0, "value_minutes_ucb": 8.0}],
        "bounded": [{"ref": "b"}], "unvalued": [{"ref": "u"}]}}]}
    eligibility = {"labelled": {"label": "you read a worked example like this one", "eligible": True}}
    assert presentation_order(receipt, eligibility) == ["c", "plain", "labelled", "b", "u"]


# -- Codex sources-build review F7, F8 ---------------------------------------------------------


def test_final_assembly_never_restores_a_hard_exclusion():
    """F7: the learner-initiated tail appended every relevant candidate in
    relevance order, putting an exposure-rejected one back into the result."""

    from learnloop.practice_index.retrieval import _valued_order

    valuation = {"problems": [], "order": [], "excluded": {"exposed": ["seen_in_proposal"]},
                 "eligibility": {"exposed": {"eligible": False, "reasons": ["seen_in_proposal"]}}}
    assert _valued_order(valuation, ["exposed", "fresh"]) == ["fresh"]
    # Eligibility alone (an older receipt shape) is enforced too.
    assert _valued_order({"problems": [], "eligibility": valuation["eligibility"]}, ["exposed"]) == []


@pytest.mark.parametrize("intent", ["discriminate", "retention"])
def test_an_exposed_item_is_not_proposed_for_a_value_intent(textbook, intent):
    from learnloop.instructional.practice import record_proposal_impressions

    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    llm = FakeServiceLLM()
    earlier = find_practice(vault, repository, "determinant rows swapped", {}, rerank_client=llm,
                            caller={"kind": "tutor", "ref": "q"})
    shown = earlier["items"][0]["practice_item_id"]
    record_proposal_impressions(vault, repository, proposal_id=earlier["proposal_id"], surface="tutor_strip",
                                keys=[{"practice_item_id": shown}])
    result = find_practice(loaded(paths), repository, "determinant rows swapped sign", {
        "intent": intent, "learning_object_ids": ["lo_matrices"],
        "target_hypotheses": [{"kind": "misconception", "id": misconception}] if intent == "discriminate" else []},
        exercise_arm=exercise_candidates, valuer=_valuer(llm), rerank_client=llm,
        caller={"kind": "tutor", "ref": "q2"})
    assert result["valuation"]["eligibility"][shown]["eligible"] is False
    assert shown in result["valuation"]["excluded"]
    assert shown not in {item["practice_item_id"] for item in result["items"]}


@pytest.mark.parametrize("status", ["model_answer", "disputed", "changed_since_check"])
def test_an_unverified_import_is_excluded_from_value_intents_but_not_practice(textbook, status):
    """F8 (G6): only verified keys qualify for the value intents; the item stays
    available for ordinary practice, with its honest label."""

    from learnloop.content.authoring.source_exercise_import import import_source_exercise
    from learnloop.db.stores.source_service import effective_key_status, insert_key_check
    from learnloop.ids import new_ulid
    from learnloop.db.stores.source_service import reference_content_hash

    paths, repository, spans, misconception = textbook
    llm = FakeServiceLLM()
    from tests.source_service_fakes import service_clients, set_item_answer

    outcome = import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                     span_ids=[spans["exercises"][3]], caller="learner",
                                     clients=service_clients(llm))
    item_id = outcome["practice_item_id"]
    item = loaded(paths).practice_items[item_id]
    if status == "changed_since_check":
        set_item_answer(paths, item_id, "an edited key nobody has checked")
        item = loaded(paths).practice_items[item_id]
    with repository.connection() as connection:
        if status != "changed_since_check":
            insert_key_check(connection, id="rkc_" + new_ulid(), practice_item_id=item_id,
                             import_id=outcome["import_id"], content_hash=reference_content_hash(item),
                             key_status=status, rung="test", verification={}, ledger_ids=[], trigger="verify",
                             started_at="2099-01-01T00:00:00Z", created_at="2099-01-01T00:00:00Z")
            connection.commit()
        assert effective_key_status(connection, item) == status
    valuer = _valuer(llm)
    receipt = valuer(loaded(paths), repository, PracticeConstraints(
        intent="discriminate", learning_object_ids=("lo_matrices",),
        target_hypotheses=({"kind": "misconception", "id": misconception},)), items=[item_id], exercises=[])
    assert receipt["eligibility"][item_id]["eligible"] is False
    assert receipt["eligibility"][item_id]["key_status"] == status
    assert "unverified_key" in receipt["excluded"][item_id]
    practice = find_practice(loaded(paths), repository, "eigenvalues diagonal matrix", {}, rerank_client=llm)
    assert practice["admission"]["excluded"].get("unverified_key") is None


def test_an_unjudged_studied_worked_example_excludes_every_independent_intent(textbook):
    """Codex re-review F4: the learner studied a worked example and the
    equivalence judge could not run. Unknown equivalence is a typed exclusion
    from independence until it is resolved, for ``discriminate`` too; ordinary
    practice keeps the candidate, honestly labelled."""

    paths, repository, spans, _m = textbook
    _study_worked_example(repository, spans)
    vault = loaded(paths)
    candidate = {"kind": "source_exercise", "extraction_id": "ext_text", "span_ids": [spans["exercises"][1]],
                 "statement": "1. An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x to find the eigenvalue.",
                 "learning_object_ids": ["lo_matrices"], "key": "srcex:1"}
    down = FakeServiceLLM(fail_purposes={"EquivalenceVerdicts"})
    for intent in ("discriminate", "retention"):
        verdict = independent_check_eligibility(vault, repository, candidate, intent=intent, judge_client=down)
        assert verdict["worked_example"]["verdict"] == "unjudged"
        assert not verdict["eligible"] and "worked_example_unjudged" in verdict["reasons"], verdict
    practice = independent_check_eligibility(vault, repository, candidate, intent="practice", judge_client=down)
    assert practice["eligible"]


def test_a_pick_with_an_unjudged_worked_example_is_served_as_labelled_practice(textbook):
    """The learner-pick recheck uses the same rule: never ``independent_check``."""

    from learnloop.db.stores.practice_index import insert_proposal
    from learnloop.instructional.practice import record_proposal_selection

    paths, repository, spans, _m = textbook
    _study_worked_example(repository, spans)
    with repository.connection() as connection:
        insert_proposal(connection, id="pp_disc", created_at="2026-10-12T08:59:00Z", origin="rpc",
                        query_id="q", query_text="eigenvalues", constraints={}, path="direct",
                        path_reason="test", signals={}, reranked=True, rerank_status="reranked",
                        rerank_model=None,
                        proposed=[{"practice_item_id": "pi_eigen_1", "rank": 1, "relevance": "relevant",
                                   "kind": "item", "rationale": "fits"}],
                        exclusions={}, manifest={}, algorithm_version="mvp-0.14",
                        caller="tutor", caller_ref="qe_1", intent="discriminate")
    selection = record_proposal_selection(repository, proposal_id="pp_disc", practice_item_id="pi_eigen_1",
                                          vault=loaded(paths))
    verdict = selection["independence"]
    assert verdict["worked_example"]["verdict"] == "unjudged", verdict
    assert selection["served_as"] == "practice"
    assert "worked_example_unjudged" in verdict["reasons"]
    assert selection["label"] != "you've seen this question since it was suggested"


class _MeteredLLM(FakeServiceLLM):
    provider_type = "openai"


@pytest.mark.parametrize("refusal", ["over_budget", "failed"])
def test_a_refused_rerank_leaves_its_page_pending_and_a_resume_judges_it(textbook, refusal):
    """Codex re-review F6: a rerank refused before any judgment (its budget, or
    a failed call) marked its whole pool judged, so resuming skipped those
    candidates for good. Only persisted judgments advance the cursor."""

    paths, repository, _spans, _m = textbook
    vault = loaded(paths)
    vault.config.practice_index.candidate_pool = 3
    if refusal == "over_budget":
        vault.config.practice_index.rerank_price_per_million = 1.0
        vault.config.practice_index.rerank_max_cost_usd = 0.0
        refused_client = _MeteredLLM()
    else:
        refused_client = FakeServiceLLM(fail_purposes={"PracticeRerank"})
    query = "matrix determinant eigen vector"
    first = find_practice(vault, repository, query, {"limit": 2}, rerank_client=refused_client)
    assert first["rerank_status"].startswith(refusal), first["rerank_status"]
    paging = first["paging"]
    assert paging["outcome"] in ("budget", "judge_unavailable") and paging["cursor"]
    # Nothing was judged, so nothing is skipped on resume.
    assert paging["cursor"]["judged_items"] == [] and paging["cursor"]["judged_exercises"] == []
    vault.config.practice_index.rerank_max_cost_usd = 1.0
    second = find_practice(vault, repository, query, {"limit": 2}, rerank_client=FakeServiceLLM(),
                           cursor=paging["cursor"])
    assert second["rerank_status"] == "reranked"
    with repository.connection() as connection:
        pools = [json.loads(row[0])["pool"] for row in connection.execute(
            "SELECT exclusions_json FROM practice_index_proposals ORDER BY created_at, id")]
    assert pools[-1] == pools[0] and pools[0] > 0  # the refused page is judged on resume


class _RelevantOnly(FakeServiceLLM):
    """A judge that finds only some candidates relevant, recording each page it reads."""

    def __init__(self, relevant_ids=(), **kwargs):
        super().__init__(**kwargs)
        self.relevant_ids = set(relevant_ids)
        self.pages: list[list[str]] = []
        self.prompts: dict[str, str] = {}

    def complete(self, request):
        from tests.pf_fakes import prompt_context

        if request.result_model.__name__ in ("PracticeRerank", "MixedPracticeRerank"):
            context = prompt_context(request.prompt)
            self.pages.append([c.get("prompt") or c.get("statement") or "" for c in context["candidates"]])
        return super().complete(request)

    def _grade(self, request_text, text):  # type: ignore[override]
        return "relevant" if any(marker in text for marker in self.relevant_ids) else "not_relevant"


def test_a_value_search_pages_on_until_a_stop_inside_one_call(textbook):
    """Codex re-review F5: the first page's candidates are unsuitable and a
    later candidate would pass. The value search keeps paging inside the call
    (no fixed candidate page is a count cap) and values the later candidate."""

    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    vault.config.practice_index.candidate_pool = 1
    constraints = {"intent": "discriminate", "learning_object_ids": ["lo_matrices"], "kinds": "items",
                   "target_hypotheses": [{"kind": "misconception", "id": misconception}]}
    query = "determinant swap rows sign"
    probe = _RelevantOnly()
    probe.model = "fake-probe-judge"
    first_page = find_practice(vault, repository, query, constraints, valuer=_valuer(probe), rerank_client=probe)
    seen_first = probe.pages[0]
    lo_items = [item for item in vault.practice_items.values()
                if item.learning_object_id == "lo_matrices" and item.status != "retired"
                and " ".join(item.prompt.split())[:60] not in " ".join(seen_first)]
    assert lo_items, "the fixture needs an item beyond the first page"
    target = lo_items[-1]
    marker = " ".join(target.prompt.split())[:40]
    judge = _RelevantOnly(relevant_ids=[marker])
    judge.model = "fake-later-judge"
    result = find_practice(vault, repository, query, constraints, valuer=_valuer(judge), rerank_client=judge)
    assert len(judge.pages) >= 2, "the search stopped after one page"
    assert result["paging"]["outcome"] in ("exhausted", "perfect_information_bound"), result["paging"]
    valued = {key for section in result["valuation"]["problems"]
              for group in section["groups"].values() for entry in group for key in [entry.get("ref")]}
    eligibility = result["valuation"].get("eligibility") or {}
    assert target.id in valued or target.id in eligibility, (target.id, valued)
    del first_page


# -- Codex third pass F12: a continuation is the same request, and carried exercises are readmitted ----------


def _stopped_value_search(textbook, constraints):
    """A discriminate search over both arms stopped by its deadline after one
    page: its cursor carries the relevant exercises judged so far."""

    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    vault.config.practice_index.candidate_pool = 2
    llm = FakeServiceLLM()
    request = {"intent": "discriminate", "kinds": "both",
               "target_hypotheses": [{"kind": "misconception", "id": misconception}], **constraints}
    first = find_practice(vault, repository, "eigenvalue solve determinant", request, valuer=_valuer(llm),
                          rerank_client=llm, exercise_arm=exercise_candidates, deadline=0.0)
    cursor = first["paging"]["cursor"]
    carried = [entry["key"] for entry in cursor["relevant"]["exercises"]]
    assert carried, "the fixture needs a carried exercise"
    return vault, repository, llm, request, cursor, carried


def test_a_continuation_with_other_constraints_is_refused(textbook):
    """Before: only the query and intent were compared, so a continuation
    narrowed to a facet restored carried exercises the new filter rejects
    (their provisional facets are unknown, which fails a facet filter)."""

    vault, repository, llm, request, cursor, carried = _stopped_value_search(textbook, {})
    narrower = {**request, "facet_ids": ["facet_eigen"]}
    assert exercise_filter(PracticeConstraints.from_mapping(narrower),
                           cursor["relevant"]["metadata"][carried[0]], estimator) is not None
    with pytest.raises(ValueError, match="same request"):
        find_practice(vault, repository, "eigenvalue solve determinant", narrower, valuer=_valuer(llm),
                      rerank_client=llm, exercise_arm=exercise_candidates, cursor=cursor)


def test_a_carried_exercise_imported_since_is_not_restored(textbook):
    """Same request, but one carried exercise was imported after the first
    page: the arm would no longer admit it, so the continuation drops it."""

    from learnloop.db.stores.source_service import insert_import

    vault, repository, llm, request, cursor, carried = _stopped_value_search(textbook, {})
    record = next(entry for entry in cursor["relevant"]["exercises"] if entry["key"] == carried[0])
    with repository.connection() as connection:
        insert_import(connection, id="sei_since", created_at="2026-10-13T00:00:00Z", caller="learner",
                      extraction_id=record["extraction_id"], span_ids=record["span_ids"], status="written")
    resumed = find_practice(vault, repository, "eigenvalue solve determinant", request, valuer=_valuer(llm),
                            rerank_client=llm, exercise_arm=exercise_candidates, cursor=cursor)
    proposed = {entry["key"] for entry in resumed.get("source_exercises") or ()}
    assert carried[0] not in proposed, proposed
    assert carried[0] not in (resumed["paging"].get("cursor") or {}).get("relevant", {}).get("order", [])
    assert resumed["signals"]["continuation"]["dropped"] == {"already_imported": 1}
