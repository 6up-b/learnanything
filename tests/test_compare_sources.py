"""S3 (G12): compare_sources: every source considered, quotes verified, no consensus, policy first."""
from __future__ import annotations

import pytest

from learnloop.ingest.locators import format_block_span
from learnloop.source_retrieval.compare import SourceComparison, compare_sources
from learnloop.source_retrieval.policy import CallerContext, PolicyRefused
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call, loaded

QUESTION = "why does the determinant change sign when two rows are swapped"


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _compare(paths, repository, llm, caller=None, **kwargs):
    return compare_sources(loaded(paths), repository, QUESTION, caller=caller or CallerContext(kind="reader"),
                           client=llm, verify_client=llm, **kwargs)


def test_two_sources_are_compared_with_verified_quotes_and_stored(textbook):
    paths, repository, _spans = textbook
    llm = FakeServiceLLM(bad_comparison_quote=True)
    result = _compare(paths, repository, llm, requested_perspectives=["geometric view", "proof"])
    assert result.status == "ok" and result.comparison_id
    titles = {source["source_title"] for source in result.sources}
    assert {"Linear Algebra Notes", "Matrix Theory"} <= titles
    assert all(source["label"] == "source-authored" for source in result.sources)
    assert result.relations and result.relations[0]["relation"] == "different_notation"
    assert any(line["kind"] == "contribution" for line in result.dropped_lines)  # the invented quote
    assert result.missing_perspectives == ["proof"]
    assert "consensus" not in result.as_dict() and "answer" not in result.as_dict()
    assert "consensus" not in SourceComparison.model_json_schema()["properties"]
    # Reopening the same comparison is not paid for twice.
    calls = len(llm.calls)
    again = _compare(paths, repository, llm, requested_perspectives=["geometric view", "proof"])
    assert again.reused and again.comparison_id == result.comparison_id
    assert [name for _p, name in llm.calls[calls:]].count("SourceComparison") == 0


def test_a_cold_caller_is_refused_and_a_wider_policy_too(textbook):
    paths, repository, _spans = textbook
    with pytest.raises(PolicyRefused):
        _compare(paths, repository, FakeServiceLLM(),
                 caller=CallerContext(kind="tutor", context="practice", item_id="pi_determinant_1", cold=True))
    with pytest.raises(PolicyRefused):
        _compare(paths, repository, FakeServiceLLM(),
                 caller=CallerContext(kind="tutor", context="practice", item_id="pi_determinant_1"), policy="reading")


def test_pins_obey_the_policy_in_a_practice_context(textbook):
    paths, repository, spans = textbook
    item_id = "pi_determinant_2"
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id=item_id, locator=format_block_span("ext_text", spans["ch5"][2]),
        relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    caller = CallerContext(kind="tutor", context="practice", item_id=item_id)
    result = _compare(paths, repository, FakeServiceLLM(), caller=caller,
                      pinned_span_ids=[f"ext_text:{spans['solutions'][1]}", f"ext_text:{spans['ch5'][2]}",
                                       "ext_book:s7"])
    reasons = {pin["span_id"]: pin["reason"] for pin in result.dropped_pins}
    assert spans["solutions"][1] in reasons and spans["ch5"][2] in reasons
    assert "not available while you're practising" in reasons[spans["solutions"][1]]
    assert result.policy == "assisted_practice"


def test_a_pinned_solution_in_a_reading_context_is_compared(textbook):
    paths, repository, spans = textbook
    result = _compare(paths, repository, FakeServiceLLM(), pinned_span_ids=[f"ext_text:{spans['solutions'][1]}"])
    assert not result.dropped_pins


def test_every_source_is_considered_and_uncompared_ones_are_listed(textbook):
    paths, repository, _spans = textbook
    vault = loaded(paths)
    vault.config.source_service.compare_max_prompt_tokens = 1000  # room for two passages only
    from tests.source_service_fakes import seed_textbook

    seed_textbook(repository, source_id="src_third", revision_id="rev_third", extraction_id="ext_third",
                  title="Third Book", units={"c1": ("Determinants", [
                      ("Swapping two rows of a matrix changes the sign of its determinant, a rule from the "
                       "alternating property of determinants. " + "The alternating property in detail. " * 60, 1)])})
    result = compare_sources(vault, repository, QUESTION, caller=CallerContext(kind="reader"),
                             client=FakeServiceLLM(), verify_client=FakeServiceLLM())
    compared = {source["source_id"] for source in result.sources}
    listed = {entry["source_id"] for entry in result.also_discussed_in}
    assert len(compared) == 2 and listed and not compared & listed
    assert result.manifest["verification"]["sources_in_scope"] >= 3


def test_the_rpc_and_the_switch(textbook):
    from tests.source_service_fakes import set_config

    paths, _repository, _spans = textbook
    set_config(paths, "source_service", compare=False)
    response = call(paths.root, "compare_sources", {"query": QUESTION, "caller": {"kind": "reader"}})
    assert response["error"]["data"]["code"] == "source_service_disabled"
