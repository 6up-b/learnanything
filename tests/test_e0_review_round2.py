"""Regressions for the Codex re-review of the E0 harness (F6, F7 reopened; F19, F20), fakes only.

Every test runs offline: hash-vector embeddings, fake role clients and a
socket guard that refuses any connection. Production retrieval runs on
service copies with ``ai.active_provider = "manual"``, so only the injected
fake clients can answer."""
from __future__ import annotations

from decimal import Decimal
import json
import socket

import pytest

from learnloop.ai.spend import NO_RESERVATION, SpendBudget, SpendCaps, SpendEstimate, spend_envelopes
from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings.answers import TutorAnswer, judge_prompt, tutor_prompt
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, LedgerEnvelope
from learnloop.experiments.contextual_embeddings.callers import FakeRoleCaller
from learnloop.experiments.contextual_embeddings.delivery import Selection, deliver
from learnloop.experiments.contextual_embeddings.paid import snapshot_sqlite
from learnloop.tutor.context_delivery import BlockSource
from tests.e0_fakes import FakeRoleClient, build_e0_vault
from tests.embedding_fakes import BagOfWordsEmbedder

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


PROTECTED_QUOTE = "Solution: apply linearity to 0 = 0 + 0"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _snapshot(tmp_path, **kwargs):
    paths, _repository = build_e0_vault(tmp_path, "e0vault", manual_ai=kwargs.pop("manual_ai", False))
    return C.build_snapshot(C.open_copy(paths.root), **kwargs), paths


# -- F6 (reopened) ----------------------------------------------------------------------------


def _withheld_quote_question(snapshot):
    withheld = next(block.span_id for block in snapshot.blocks["ext_book"]
                    if snapshot.policy.verdict("ext_book", block.span_id))
    permitted = next(unit for unit in snapshot.units if unit.extraction_id == "ext_book")
    return B.BankQuestion("q1", "logged", None, "logged", "explain", "logged_reader", "Why does this follow?",
                          selection=Selection("ext_book", permitted.members[0].span_id, (withheld,),
                                              PROTECTED_QUOTE))


@pytest.mark.parametrize("arm", ["D0", "D1"])
def test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges(tmp_path, arm):
    snapshot, _paths = _snapshot(tmp_path)
    question = B.freeze_context(_withheld_quote_question(snapshot), snapshot)
    assert "Solution" not in question.selected_passage
    # The frozen selection is the one delivery reads: no quote over protected spans.
    assert question.selection.quote is None
    assert all(not snapshot.policy.verdict("ext_book", span_id) for span_id in question.selection.selection_span_ids)
    delivered = deliver(arm, BlockSource(snapshot_sqlite(snapshot)), snapshot, question.selection)
    assert delivered.spans, delivered.receipt
    assert not any("Solution" in str(span.get("text")) for span in delivered.spans)
    assert not any(span.get("relation") == "selected_text" for span in delivered.spans)
    answer = TutorAnswer(answer="because", cited_refs=["r1"], abstained=False)
    assert "Solution" not in tutor_prompt(question, delivered)[0]
    assert "Solution" not in judge_prompt(question, delivered, answer, order_salt=0)


def test_f6_delivery_refuses_a_protected_quote_even_from_an_unfrozen_selection(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    selection = _withheld_quote_question(snapshot).selection
    delivered = deliver("D1", BlockSource(snapshot_sqlite(snapshot)), snapshot, selection)
    assert not any("Solution" in str(span.get("text")) for span in delivered.spans)


def test_f6_a_permitted_quote_is_still_delivered(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    permitted = next(unit for unit in snapshot.units if unit.extraction_id == "ext_book")
    # A quote PROVEN to be permitted canonical text (fix round 4, High 7: an
    # unproven quote is dropped): a part of the selected block itself.
    block = next(item for item in snapshot.blocks["ext_book"] if item.span_id == permitted.members[0].span_id)
    quote = " ".join(block.text.split())[:48]
    question = B.freeze_context(B.BankQuestion(
        "q1", "logged", None, "logged", "explain", "logged_reader", "Why?",
        selection=Selection("ext_book", permitted.members[0].span_id, (), quote)), snapshot)
    assert question.selected_passage == quote and question.selection.quote == quote
    delivered = deliver("D1", BlockSource(snapshot_sqlite(snapshot)), snapshot, question.selection)
    assert any(span.get("relation") == "selected_text" and span["text"] == quote for span in delivered.spans)


# -- F7 (reopened) ----------------------------------------------------------------------------


def _background_pool(snapshot):
    pool = [unit.unit_id for unit in snapshot.units][:3]
    # Both passes agree each candidate is background: the adjudicator inherits that label.
    passes = [{unit: "background" for unit in pool}, {unit: "background" for unit in pool}]
    return pool, B.QuestionLabels("q1", list(pool), passes, [[], [frozenset(pool[:1])]], [False, True])


@pytest.mark.parametrize("explicit", [False, True])
def test_f7_a_set_member_is_checked_against_the_merged_final_labels(tmp_path, explicit):
    snapshot, _paths = _snapshot(tmp_path)
    pool, labels = _background_pool(snapshot)
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "Why does a linear map preserve zero?"), snapshot)

    def respond(role, prompt, _model):
        context = json.loads(prompt[prompt.index("{"):])["context"]
        refs = [candidate["ref"] for candidate in context["candidates"]]
        # Omitted (inherited background) or given explicitly as background: never sufficient.
        given = [{"ref": refs[0], "relevance": "background"}] if explicit else []
        return {"labels": given, "sufficient_sets": [[refs[0]]], "answerable": True, "unresolved": False}

    result = B.adjudicate(question, labels, snapshot, FakeRoleCaller(respond))
    assert result.unresolved and result.final_sets == [] and result.answerable is None
    assert "set_member_not_supporting" in result.problems
    assert B.evidence_sets_from_labels(result, snapshot) == []


def test_f7_an_inherited_supporting_label_still_completes_a_set(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    pool = [unit.unit_id for unit in snapshot.units][:3]
    passes = [{unit: "required" for unit in pool}, {unit: "required" for unit in pool}]
    labels = B.QuestionLabels("q1", list(pool), passes, [[frozenset(pool[:1])], []], [True, False])
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "Why does a linear map preserve zero?"), snapshot)

    def respond(role, prompt, _model):
        context = json.loads(prompt[prompt.index("{"):])["context"]
        refs = [candidate["ref"] for candidate in context["candidates"]]
        return {"labels": [], "sufficient_sets": [[refs[0]]], "answerable": True, "unresolved": False}

    result = B.adjudicate(question, labels, snapshot, FakeRoleCaller(respond))
    assert not result.unresolved and result.problems == [] and len(result.final_sets) == 1


# -- F19 ------------------------------------------------------------------------------------


def _verify_respond(_role, prompt, _model):
    from learnloop.source_retrieval.find_sources import INTENT_VERDICTS

    context = json.loads(prompt[prompt.index("{"):])["context"]
    refs = [candidate["ref"] for candidate in context["candidates"]]
    # An intent's verification (source_intent_fit.v1.<intent>) uses that intent's best verdict.
    version = next(line for line in prompt.splitlines() if line.startswith("prompt_version:"))
    intent = version.rsplit(".", 1)[-1]
    verdict = INTENT_VERDICTS[intent][0] if "source_intent_fit" in version else "answers"
    return {"judgments": [{"ref": ref, "verdict": verdict, "rationale": "On topic."} for ref in refs],
            "picks": refs[:2]}


class MeteredVerifier(FakeRoleClient):
    """A metered OpenRouter verifier: one bounded physical request per call."""

    def supports(self, capability):
        from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION

        return capability in (STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN)


def _verifier(billing):
    if billing == "subscription":
        return FakeRoleClient("codex_low", respond=_verify_respond)
    return MeteredVerifier("e0_openrouter_haiku", respond=_verify_respond)


def _service(tmp_path, paths, name, *, price=None, qwen=False):
    import tomlkit

    from learnloop.experiments.contextual_embeddings.system_arms import (
        enable_embeddings_on_copy,
        make_service_copy,
    )

    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / name)
    if qwen:
        enable_embeddings_on_copy(root)
    if price is not None:
        toml = root / "learnloop.toml"
        document = tomlkit.parse(toml.read_text(encoding="utf-8"))
        document.setdefault("source_retrieval", tomlkit.table())["llm_price_per_million"] = price
        toml.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def _remediate(snapshot):
    return B.freeze_context(B.BankQuestion("q2", "development", None, "writer", "remediate", "intent_remediate",
                                           "I think a vector space has two zero vectors, why not?"), snapshot)


@pytest.mark.parametrize("billing", ["subscription", "metered"])
def test_f19_successful_production_verification_charges_once_per_physical_request(tmp_path, billing):
    from learnloop.experiments.contextual_embeddings.system_arms import open_service, rank_system

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    handle = open_service(_service(tmp_path, paths, "r0", price=None if billing == "subscription" else 2.0))
    question = _remediate(snapshot)
    verifier = _verifier(billing)
    ledger = E0Ledger(tmp_path / "ledger")
    ranked, report = rank_system(handle, snapshot, [question], arm="R0", ledger=ledger,
                                 query_text={"q2": question.retrieval_query}, clients={"rerank_client": verifier})
    assert report["verification"] == {"verified": 1}, report
    assert "q2" in ranked and report["ranked"] == 1 and not report["missing"]
    entries = list(json.loads((tmp_path / "ledger" / "e0_spend_ledger.json").read_text())["entries"].values())
    # Exactly one ledger charge per physical request (one per verified page), in
    # the LLM's own category; nothing billed as an embedding.
    requests = len(verifier.requests)
    assert requests >= 1 and len(entries) == requests
    assert all(entry["category"] == "answers_verification" and entry["billing"] == billing
               and entry["status"] == "settled" for entry in entries)
    summary = ledger.report()
    assert summary["by_category"]["embeddings"]["committed_usd"] == 0.0
    if billing == "subscription":
        assert summary["committed_usd"] == 0.0 and summary["subscription_requests"] == requests
    else:
        assert summary["committed_usd"] > 0 and summary["metered_requests"] == requests


def test_f19_a_qwen_arm_charges_embeddings_and_verification_once_each(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import open_service, rank_system, redact_service_copy

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    root = _service(tmp_path, paths, "qwen", qwen=True)
    handle = open_service(root)
    redact_service_copy(handle, snapshot.policy)
    embedder = BagOfWordsEmbedder(dims=4096)
    from learnloop.experiments.contextual_embeddings.system_arms import backfill_service_copy

    backfill_service_copy(handle, E0Ledger(tmp_path / "backfill-ledger"), client_factory=lambda: embedder)
    embedder.calls.clear()
    question = _remediate(snapshot)
    verifier = _verifier("subscription")
    ledger = E0Ledger(tmp_path / "ledger")
    ranked, report = rank_system(handle, snapshot, [question], arm="R1_pool_verify", ledger=ledger,
                                 query_text={"q2": question.retrieval_query},
                                 clients={"embedder": embedder, "rerank_client": verifier})
    assert "q2" in ranked and report["dense_used"] == 1, report
    entries = list(json.loads((tmp_path / "ledger" / "e0_spend_ledger.json").read_text())["entries"].values())
    categories = sorted(entry["category"] for entry in entries)
    assert len(embedder.calls) >= 1 and len(verifier.requests) == 1
    assert categories == sorted(["embeddings"] * len(embedder.calls) + ["answers_verification"])
    assert all(entry["status"] == "settled" for entry in entries)


def test_f19_the_ledger_envelope_ignores_a_subscription_sentinel(tmp_path):
    ledger = E0Ledger(tmp_path)
    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter", route="qwen")
    budget = SpendBudget(SpendCaps(max_estimated_usd=None))
    with spend_envelopes(envelope):
        with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.0), subscription_route=True):
            pass
    envelope.unreserve(NO_RESERVATION)
    envelope.charge(Decimal(1), NO_RESERVATION)
    envelope.settle(NO_RESERVATION, Decimal(1))
    assert ledger.report()["requests"] == 0


# -- F20 ------------------------------------------------------------------------------------


def _compare_result(status, *, verification="verified", query_embedding="embedded", sources=2):
    from types import SimpleNamespace

    hits = [{"extraction_id": "ext_book", "span_id": f"s{index}"} for index in range(sources)]
    comparison = {"status": status, "manifest": {"verification": {"status": verification,
                                                                  "sources_with_hits": sources},
                                                 "query_embedding": {"status": query_embedding}}}
    return SimpleNamespace(hits=hits, cursor=None, status=status,
                           manifest={"delegated_to": "compare_sources", "comparison": comparison})


@pytest.mark.parametrize("status, verification, missing", [
    ("unavailable: no client", "verified", "compare_unavailable"),
    ("failed: AIProviderUnavailable", "verified", "compare_failed"),
    ("over_budget: e0 cap", "verified", "compare_over_budget"),
    ("ok", "timed_out", "compare_verification_timed_out"),
    ("too_few_sources", "unavailable", "compare_verification_unavailable"),
])
def test_f20_a_failed_delegated_comparison_is_missing_not_ranked(tmp_path, monkeypatch, status, verification,
                                                                  missing):
    from learnloop.experiments.contextual_embeddings import system_arms as S
    from learnloop.source_retrieval import find_sources as F

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    handle = S.open_service(_service(tmp_path, paths, "r0"))
    monkeypatch.setattr(F, "find_sources", lambda *args, **kwargs: _compare_result(status, verification=verification))
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "compare", "intent_compare",
                                               "Compare the two treatments of bases"), snapshot)
    ranked, report = S.rank_system(handle, snapshot, [question], arm="R0", ledger=E0Ledger(tmp_path / "ledger"),
                                   query_text={"q1": question.retrieval_query})
    assert ranked == {} and report["ranked"] == 0
    assert report["missing"] == {missing: 1}


def test_f20_a_completed_comparison_is_ranked_and_a_dense_arm_needs_its_query_embedding(tmp_path, monkeypatch):
    from learnloop.experiments.contextual_embeddings import system_arms as S
    from learnloop.source_retrieval import find_sources as F

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    handle = S.open_service(_service(tmp_path, paths, "r0"))
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "compare", "intent_compare",
                                               "Compare the two treatments of bases"), snapshot)
    ledger = E0Ledger(tmp_path / "ledger")
    monkeypatch.setattr(F, "find_sources", lambda *args, **kwargs: _compare_result("ok"))
    ranked, report = S.rank_system(handle, snapshot, [question], arm="R0", ledger=ledger,
                                   query_text={"q1": question.retrieval_query})
    assert "q1" in ranked and report["ranked"] == 1 and not report["missing"]
    # An honest "too few sources" after a verification that ran is a (short) ranking.
    monkeypatch.setattr(F, "find_sources", lambda *args, **kwargs: _compare_result("too_few_sources", sources=1))
    ranked, report = S.rank_system(handle, snapshot, [question], arm="R0", ledger=ledger,
                                   query_text={"q1": question.retrieval_query})
    assert "q1" in ranked and not report["missing"]
    # A Qwen arm whose comparison searched without its query embedding is no dense result.
    monkeypatch.setattr(F, "find_sources",
                        lambda *args, **kwargs: _compare_result("ok", query_embedding="over_budget"))
    ranked, report = S.rank_system(handle, snapshot, [question], arm="R1_service_rrf", ledger=ledger,
                                   query_text={"q1": question.retrieval_query})
    assert ranked == {} and report["missing"] == {"dense_not_used": 1} and report["dense_used"] == 0
