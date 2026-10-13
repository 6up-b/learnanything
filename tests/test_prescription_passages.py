"""S3 (G11): ranked, verified remediation passages; today's choice when verification can't run; switch parity."""
from __future__ import annotations

import pytest

from learnloop.diagnosis.remediation import prescribe_remediation
from learnloop.ingest.locators import format_block_span
from learnloop.instructional import sources as service_sources
from learnloop.instructional.sources import remediation_passage_provider, tutor_intent_for
from learnloop.source_retrieval.tutor import TutorSpanProvider
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, insert_question, loaded


@pytest.fixture
def case(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    # The facet's first linked span (today's choice) is the chapter's eigenvalue
    # sentence; the passage that actually corrects the confusion is the
    # determinant one.
    for span in (spans["ch5"][1], spans["ch5"][2]):
        repository.insert_entity_source_link(
            entity_type="facet", entity_id="facet_determinant", locator=format_block_span("ext_text", span),
            relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    misconception_id = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        correction_statement="Swapping two rows multiplies the determinant by -1",
        target_facet="facet_determinant", correction_source_span_ids=["src_text"])
    episode = repository.create_remediation_episode(case_kind="misconception", case_ref=misconception_id)
    return paths, repository, spans, episode


def _shown(episode):
    return [(p["role"], p["span_view"]["span_id"], p.get("basis")) for p in episode["passages_shown"]]


def test_switch_off_keeps_todays_prescription_byte_identical(case, monkeypatch):
    paths, repository, spans, episode = case
    vault = loaded(paths)
    vault.config.source_service.remediation_passages = False
    today = prescribe_remediation(vault, repository, episode["id"])
    off = prescribe_remediation(vault, repository, episode["id"], passage_provider=remediation_passage_provider)
    assert off["passages_shown"] == today["passages_shown"]
    assert _shown(today) == [("target", spans["ch5"][1], None)]


def test_ranked_and_verified_passages_replace_the_first_linked_span(case, monkeypatch):
    paths, repository, spans, episode = case
    vault = loaded(paths)
    llm = FakeServiceLLM()
    real = service_sources.remediation_passage_provider

    def provider(vault, repository, **kwargs):
        from learnloop.source_retrieval import find_sources as module

        original = module._verify

        def verify(*args, **inner):
            inner["client"] = llm
            return original(*args, **inner)

        monkeypatch.setattr(module, "_verify", verify)
        return real(vault, repository, **kwargs)

    ranked = prescribe_remediation(vault, repository, episode["id"], passage_provider=provider)
    assert _shown(ranked) == [("target", spans["ch5"][2], "ranked_verified")]


def test_verification_unavailable_falls_back_byte_identically(case):
    paths, repository, _spans, episode = case
    vault = loaded(paths)
    today = prescribe_remediation(vault, repository, episode["id"])
    # No route for source_rerank in the test vault: verification cannot run.
    fallback = prescribe_remediation(vault, repository, episode["id"], passage_provider=remediation_passage_provider)
    assert fallback["passages_shown"] == today["passages_shown"]


def test_tutor_intent_is_remediate_only_with_an_active_misconception(case):
    paths, repository, _spans, _episode = case
    vault = loaded(paths)
    item = vault.practice_items["pi_determinant_1"]
    intent = tutor_intent_for(vault, repository, context="practice", item=item)
    assert intent["intent"] == "remediate" and intent["misconceptions"]
    assert tutor_intent_for(vault, repository, context="library", item=None) is None
    vault.config.source_service.tutor_intents = False
    assert tutor_intent_for(vault, repository, context="practice", item=item) is None


def test_the_tutor_provider_verifies_with_the_remediate_prompt(case):
    paths, repository, _spans, _episode = case
    vault = loaded(paths)
    llm = FakeServiceLLM()
    item = vault.practice_items["pi_determinant_1"]
    provider = TutorSpanProvider(rerank_client=llm, intent_for=tutor_intent_for)
    spans, manifest = provider(vault, repository, context="practice",
                               question_md="why does swapping rows change the determinant sign",
                               learning_object_ids=[item.learning_object_id], item=item)
    assert manifest["intent"] == "remediate" and manifest["basis"] == "retrieved_verified"
    assert "IntentVerification" in {name for _p, name in llm.calls}
    assert "correction_facets" in manifest["search"]["lists"]
    plain = TutorSpanProvider(rerank_client=FakeServiceLLM())
    _spans, plain_manifest = plain(vault, repository, context="practice", question_md="why does swapping rows",
                                   learning_object_ids=[item.learning_object_id], item=item)
    assert "intent" not in plain_manifest
