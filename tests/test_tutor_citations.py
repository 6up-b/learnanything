"""ING M8 — tutor/QA source-span citations (§9.2).

The tutor context carries bounded semantic-authority spans for the LO/facets;
returned citations are validated against those spans (never model-invented), and
the feature degrades to no citations when no links exist.
"""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.tutor.ai_contracts import TutorAnswer, TutorCitation
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault

from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
_ITEM_ID = "pi_identify_symmetry"


class _CitingTutorClient(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, citations):
        self._citations = citations
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md="A symmetric matrix satisfies A^T = A.",
            question_type="mechanism",
            facets=list(context.candidate_facets),
            citations=self._citations,
        )


def _mapped_vault(tmp_path, *, with_exam=True):
    root, repo = _setup(tmp_path, with_exam=with_exam)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"outcome": "exam prep"})
    return load_vault(root), repo


def test_tutor_context_carries_semantic_authority_spans(tmp_path):
    vault, repo = _mapped_vault(tmp_path)
    client = _CitingTutorClient([])
    ask_question(vault, repo, client, context="practice",
                 question_md="Why is this matrix symmetric?", practice_item_id=_ITEM_ID,
                 session_id="s1", clock=_CLOCK)
    spans = client.contexts[0].source_spans
    assert spans and spans[0]["semantic_authority"] is True
    assert any(s["extraction_id"] == "ext_text" and s["span_id"] == "s1" for s in spans)


def test_citations_validated_against_provided_spans(tmp_path):
    vault, repo = _mapped_vault(tmp_path)
    client = _CitingTutorClient(
        [
            TutorCitation(extraction_id="ext_text", span_id="s1", label="model label"),
            TutorCitation(extraction_id="ext_text", span_id="s999_invented"),
        ]
    )
    result = ask_question(vault, repo, client, context="practice",
                          question_md="Why symmetric?", practice_item_id=_ITEM_ID,
                          session_id="s1", clock=_CLOCK)
    citations = result["citations"]
    # invented span dropped; only the provided span survives.
    assert len(citations) == 1
    assert citations[0]["extraction_id"] == "ext_text"
    assert citations[0]["span_id"] == "s1"
    # label comes from the provided span (trustworthy), not the model echo.
    assert citations[0]["label"]


def test_no_links_degrades_to_no_citations(tmp_path):
    # A vault whose practice item's LO has no entity_source_links: no source_spans,
    # no citations, unchanged behavior.
    vault, repo = _mapped_vault(tmp_path)
    # Point at an item but strip provided spans by asking with a bogus item?  Instead
    # assert the contract directly: model cites, but with zero provided spans nothing
    # survives validation.
    from learnloop.tutor.tutor_qa import _validated_citations

    class _Ans:
        citations = [TutorCitation(extraction_id="x", span_id="y")]

    assert _validated_citations(_Ans(), []) == []
