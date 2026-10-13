"""S3 (G2, G11, G21): find_sources with intents, policies, correction refs and the Reader's contract."""
from __future__ import annotations

import pytest

from learnloop.ingest.locators import format_block_span
from learnloop.instructional.policy import caller_for
from learnloop.instructional.sources import propose_sources
from learnloop.source_retrieval.find_sources import find_sources, find_sources_for_caller
from learnloop.source_retrieval.policy import CallerContext, PolicyRefused
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call, loaded, set_config


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _llm():
    return FakeServiceLLM()


def test_explain_returns_verbatim_labelled_hits_with_identity(textbook):
    paths, repository, _spans = textbook
    hits = find_sources(loaded(paths), repository, "eigenvalues characteristic polynomial", policy="reading")
    assert hits.status == "ok" and hits.hits
    hit = hits.hits[0]
    assert hit["label"] == "source-authored" and hit["authorship"] == "source"
    assert hit["revision_id"] and hit["source_id"] and hit["verdict"] is None
    assert hits.manifest["verification"]["status"] == "not_requested"
    assert {"query_hash", "policy", "extractions", "returned"} <= set(hits.manifest)


def test_explain_verifies_when_asked_and_other_intents_always_do(textbook):
    paths, repository, _spans = textbook
    llm = _llm()
    hits = find_sources(loaded(paths), repository, "eigenvalues characteristic polynomial", policy="reading",
                        verify=True, rerank_client=llm)
    assert hits.manifest["verification"]["status"] == "verified"
    assert all(hit["verdict"] in ("answers", "related") for hit in hits.hits)
    worked = find_sources(loaded(paths), repository, "solve for the eigenvalue", policy="reading",
                          intent="worked_example", learner_work_md="I subtracted 2 first", rerank_client=llm)
    assert worked.manifest["roles"] == ["worked_example"]
    assert worked.hits and all(hit["span_id"] == "t5" for hit in worked.hits)
    assert worked.hits[0]["verdict"] in ("follows_learner_route", "worked_example")


def test_cold_attempt_returns_nothing_and_authoring_is_not_a_policy(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    assert find_sources(vault, repository, "eigenvalues", policy="cold_attempt").hits == []
    with pytest.raises(PolicyRefused):
        find_sources(vault, repository, "eigenvalues", policy="authoring")


def test_assisted_practice_drops_exercises_solutions_and_item_answers(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]
    hits = find_sources(vault, repository, "eigenvalue solve subtract solution exercise", policy="assisted_practice",
                        item=item, scope="teaching")
    keys = {(hit["extraction_id"], hit["span_id"]) for hit in hits.hits}
    assert not keys & {("ext_text", span) for span in spans["exercises"] + spans["solutions"]}
    assert all(hit["extraction_id"] != "ext_exam" for hit in hits.hits)


def test_a_policy_argument_cannot_widen_the_callers(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    caller = CallerContext(kind="tutor", ref="q", context="practice", item_id="pi_eigen_1")
    with pytest.raises(PolicyRefused):
        find_sources_for_caller(vault, repository, "eigenvalues", caller=caller, policy="reading")
    hits = find_sources_for_caller(vault, repository, "eigenvalues", caller=caller, scope="teaching")
    assert hits.policy == "assisted_practice"
    cold = CallerContext(kind="tutor", ref="q", context="practice", item_id="pi_eigen_1", cold=True)
    assert find_sources_for_caller(vault, repository, "eigenvalues", caller=cold).hits == []


def test_post_attempt_opens_the_solution_only_after_the_window_closes_and_records_a_reveal(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id=item.id, locator=format_block_span("ext_text", spans["solutions"][1]),
        relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    open_window = CallerContext(kind="reader", item_id=item.id, post_attempt_requested=True, window_open=True)
    assert find_sources_for_caller(vault, repository, "subtracting gives eigenvalue", caller=open_window,
                                   scope="teaching").policy == "assisted_practice"
    closed = CallerContext(kind="reader", item_id=item.id, post_attempt_requested=True, window_open=False)
    hits = find_sources_for_caller(vault, repository, "subtracting gives eigenvalue", caller=closed)
    assert hits.policy == "post_attempt"
    assert ("ext_text", spans["solutions"][1]) in {(hit["extraction_id"], hit["span_id"]) for hit in hits.hits}
    with repository.connection() as connection:
        reveal = connection.execute("SELECT source_kind, practice_item_id FROM reveal_events").fetchone()
    assert tuple(reveal) == ("source_review", item.id)


def test_remediate_reads_correction_refs_and_reports_missing_sources(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    repository.insert_entity_source_link(
        entity_type="facet", entity_id="facet_determinant", locator=format_block_span("ext_text", spans["ch5"][2]),
        relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    misconception_id = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        correction_statement="Swapping two rows multiplies the determinant by -1",
        target_facet="facet_determinant", confused_with_facet=None,
        correction_source_span_ids=["src_text", "src_gone"])
    hits = propose_sources(vault, repository, "", caller=CallerContext(kind="reader"), intent="remediate",
                           target_hypotheses=[{"kind": "misconception", "id": misconception_id}],
                           rerank_client=_llm())
    lists = hits.manifest["search"]["lists"]
    assert "correction_facets" in lists and "correction_sources" in lists
    report = hits.manifest["personalized_for"]["misconceptions"][0]
    assert report["missing_sources"] == ["src_gone"]
    assert hits.hits and hits.hits[0]["verdict"] in ("addresses_confusion", "contrasts")
    assert hits.manifest["label"] == "chosen for your open question"
    plain = propose_sources(vault, repository, "", caller=CallerContext(kind="reader"), intent="remediate",
                            target_hypotheses=[{"kind": "misconception", "id": misconception_id}],
                            personalized=False, rerank_client=_llm())
    assert "correction_facets" not in plain.manifest["search"]["lists"]


def test_alternative_excludes_what_was_shown_and_prefers_other_sources(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    shown = [f"ext_book:{span}" for span in ("s2", "s3")]
    hits = find_sources(vault, repository, "eigenvalues characteristic polynomial", policy="reading",
                        intent="alternative", exclude_span_ids=shown, rerank_client=_llm())
    keys = {(hit["extraction_id"], hit["span_id"]) for hit in hits.hits}
    assert not keys & {("ext_book", "s2"), ("ext_book", "s3")}
    assert all(hit["verdict"] == "different_treatment" for hit in hits.hits)
    assert hits.manifest["personalized_for"]["shown_sources"] == ["src_book"]


def test_expansions_are_labelled_ranked_lists(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    with pytest.raises(ValueError):
        find_sources(vault, repository, "x y", policy="reading", expand=["siblings"])
    hits = find_sources(vault, repository, "eigenvalues", policy="reading", expand=["prerequisites", "applications"],
                        learning_object_ids=["lo_matrices"])
    assert hits.manifest["expand"] == ["prerequisites", "applications"]


def test_the_rpc_derives_the_caller_and_refuses_a_wider_policy(textbook):
    paths, repository, _spans = textbook
    response = call(paths.root, "find_sources", {"query": "eigenvalues", "caller": {"kind": "reader"}})
    assert response["result"]["policy"] == "reading" and response["result"]["hits"]
    refused = call(paths.root, "find_sources", {
        "query": "eigenvalues", "policy": "reading",
        "caller": {"kind": "reader", "practiceItemId": "pi_eigen_1"}})
    assert refused["error"]["data"]["code"] == "policy_refused"
    set_config(paths, "source_service", enabled=False)
    off = call(paths.root, "find_sources", {"query": "eigenvalues", "caller": {"kind": "reader"}})
    assert off["error"]["data"]["code"] == "source_service_disabled"


def test_reader_consumer_contract_calls(textbook):
    """G21: each call exactly as the Reader spec writes it returns the documented fields."""
    paths, repository, spans = textbook
    vault = loaded(paths)
    reading = CallerContext(kind="reader")
    rw4a = find_sources_for_caller(vault, repository, "eigenvalues", caller=reading, verify=True,
                                   expand=["prerequisites", "applications"], rerank_client=_llm())
    assert {"hits", "manifest", "policy", "intent"} <= set(rw4a.as_dict())
    rw1c = find_sources_for_caller(vault, repository, "eigenvalues", caller=reading, intent="alternative",
                                   exclude_span_ids=["ext_book:s2"], rerank_client=_llm())
    assert ("ext_book", "s2") not in {(hit["extraction_id"], hit["span_id"]) for hit in rw1c.hits}
    roles = find_sources_for_caller(vault, repository, "solve eigenvalue", caller=reading, roles=["exercise"])
    assert {hit["span_id"] for hit in roles.hits} <= set(spans["exercises"])
    rw2c = find_sources_for_caller(vault, repository, "solve for the eigenvalue",
                                   caller=CallerContext(kind="reader", context="practice", item_id="pi_eigen_1"),
                                   intent="worked_example", rerank_client=_llm())
    assert rw2c.policy == "assisted_practice"
    keys = find_sources_for_caller(vault, repository, "eigenvalues", caller=reading,
                                   exclude_span_keys=[["ext_book", "s2"]])
    assert ("ext_book", "s2") not in {(hit["extraction_id"], hit["span_id"]) for hit in keys.hits}


# -- Codex sources-build review F14: the rest of the Reader's contract -----------------------------


def _propose_role(repository, span_id, role, *, confidence=None):
    from learnloop.reader.source_objects import author_source_object

    author_source_object(repository, source_id="src_text", revision_id="rev_text", object_type="motif_or_passage",
                         authorial_role=role, content={"confidence": confidence} if confidence else {},
                         citations=[{"revision_id": "rev_text", "span_id": span_id}])


def test_roles_match_an_rw4e_proposal(textbook):
    """A Reader RW4e role proposal (``authorial_role``) satisfies the positive
    filter; ingest's hints have no counterexample or intuition role."""

    paths, repository, spans = textbook
    vault = loaded(paths)
    reading = CallerContext(kind="reader")
    before = find_sources_for_caller(vault, repository, "determinant rows swapped", caller=reading,
                                     roles=["counterexample"])
    assert before.hits == []
    _propose_role(repository, spans["ch5"][2], "counterexample")
    hits = find_sources_for_caller(vault, repository, "determinant rows swapped", caller=reading,
                                   roles=["counterexample"])
    assert [(hit["extraction_id"], hit["span_id"]) for hit in hits.hits] == [("ext_text", spans["ch5"][2])]
    assert hits.manifest["search"]["role_basis"] == {"hints": 0, "proposals": 1, "low_confidence": 0}


def test_a_low_confidence_proposal_counts_only_when_nothing_better_exists(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    reading = CallerContext(kind="reader")
    _propose_role(repository, spans["ch5"][1], "intuition", confidence="low")
    alone = find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=reading,
                                    roles=["intuition"])
    assert {hit["span_id"] for hit in alone.hits} == {spans["ch5"][1]}
    assert alone.manifest["search"]["role_basis"]["low_confidence"] == 1
    _propose_role(repository, spans["ch5"][2], "intuition")
    better = find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial determinant",
                                     caller=reading, roles=["intuition"])
    assert {hit["span_id"] for hit in better.hits} == {spans["ch5"][2]}


def test_a_proposal_never_admits_a_block_into_an_item_bound_scope(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    _propose_role(repository, spans["solutions"][1], "intuition")  # a solution block
    practice = CallerContext(kind="tutor", context="practice", item_id="pi_eigen_1")
    hits = find_sources_for_caller(vault, repository, "subtracting gives eigenvalue", caller=practice,
                                   scope="teaching", roles=["intuition"])
    assert spans["solutions"][1] not in {hit["span_id"] for hit in hits.hits}


def test_facet_ids_target_retrieval_and_verification(textbook):
    paths, repository, spans = textbook
    vault = loaded(paths)
    repository.insert_entity_source_link(
        entity_type="facet", entity_id="facet_determinant", locator=format_block_span("ext_text", spans["ch5"][2]),
        relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    llm = _llm()
    hits = find_sources_for_caller(vault, repository, "what changes the sign", caller=CallerContext(kind="reader"),
                                   facet_ids=["facet_determinant"], verify=True, rerank_client=llm)
    assert "facets" in hits.manifest["search"]["lists"]
    assert hits.manifest["facets_targeted"][0]["facet_id"] == "facet_determinant"
    assert ("ext_text", spans["ch5"][2]) in {(hit["extraction_id"], hit["span_id"]) for hit in hits.hits}
    plain = find_sources_for_caller(vault, repository, "what changes the sign", caller=CallerContext(kind="reader"),
                                    verify=True, rerank_client=llm)
    assert "facets" not in plain.manifest["search"]["lists"] and plain.manifest["facets_targeted"] == []


def test_find_sources_compare_delegates_to_compare_sources(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    llm = _llm()
    hits = find_sources_for_caller(vault, repository, "what happens when rows are swapped",
                                   caller=CallerContext(kind="reader"), intent="compare", rerank_client=llm,
                                   compare_client=llm)
    assert hits.intent == "compare" and hits.manifest["delegated_to"] == "compare_sources"
    comparison = hits.manifest["comparison"]
    assert comparison["comparison_id"] and "consensus" not in comparison
    assert [hit["source_id"] for hit in hits.hits] == [source["source_id"] for source in comparison["sources"]]
    assert all(hit["label"] == "source-authored" for hit in hits.hits)
    # The policy is the caller's: a cold caller is refused, never widened.
    cold = find_sources_for_caller(vault, repository, "rows", caller=CallerContext(
        kind="tutor", context="practice", item_id="pi_eigen_1", cold=True), intent="compare")
    assert cold.hits == [] and cold.status.startswith("empty")
