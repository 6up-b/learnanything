"""S2a: intents, typed constraints on both arms, open hypotheses, screens, exposure and paging."""
from __future__ import annotations

from dataclasses import dataclass

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
    assert "unavailable: learner-text gaps not merged" in reasons and "no_hypothesis_set" in reasons


def test_item_tables_are_normalized_and_labelled(textbook):
    paths, repository, _spans, misconception = textbook
    vault = loaded(paths)
    problem, _ = lo_problem(vault, repository, "lo_matrices")
    candidate = item_input(vault, repository, problem, vault.practice_items["pi_determinant_1"], estimator=estimator)
    assert candidate.regime == "item_point" and len(candidate.members) == 3
    check_tables(problem, candidate.members)
    assert candidate.minutes_provenance["prior_source"] == "test"


def test_retention_needs_a_prior_and_a_channel(textbook):
    paths, repository, _spans, _m = textbook
    problem, missing = retention_problem(loaded(paths), repository, "lo_matrices")
    assert problem is None and missing[0]["reason"] == "no_prior"


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
