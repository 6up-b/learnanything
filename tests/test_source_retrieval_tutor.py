"""Slice 2 T6: question-dependent, verified tutor spans and labelled LO suggestions."""
from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.suggest import suggest_learning_objects, suggested_learning_objects
from learnloop.source_retrieval.tutor import TutorSpanProvider
from learnloop.tutor.ai_contracts import PromotionAnalysis, TutorAnswer, TutorCitation
from learnloop.tutor.promotions import PromotionError, promote_tutor_question
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES
from tests.helpers import append_config_toml
from tests.source_retrieval_fakes import (
    EXAM_QUESTION,
    FakeSourceLLM,
    HashingEmbedder,
    build_retrieval_vault,
    loaded,
)
from tests.structured_ai import StructuredClientFake

CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))
CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8,
                 max_estimated_usd=10.0)
QUESTION = "Why are the eigenvalues the roots of the characteristic polynomial?"


@pytest.fixture(autouse=True)
def _fresh_dense_cache():
    clear_cache()
    yield
    clear_cache()


class CitingTutor(StructuredClientFake):
    """Cites every span it was given, so the allowlist is what keeps citations honest."""

    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def __init__(self):
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md="Think about det(A - tI).", question_type="mechanism",
            facets=list(context.candidate_facets),
            citations=[TutorCitation(extraction_id=span["extraction_id"], span_id=span["span_id"])
                       for span in context.source_spans]
            + [TutorCitation(extraction_id="ext_exam", span_id="s2")],
        )


def setup(tmp_path, *, embed=True):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_matrices", locator="span:ext_book/s7",
        relation="primary", source_id="src_book", revision_id="rev_book", extraction_id="ext_book")
    if embed:
        for registry, recipes in ((SOURCE_RETRIEVAL_RECIPES, ("source_block",)),
                                  (EMBEDDING_RECIPES, ("facet/definition",))):
            report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=recipes, registry=registry,
                                         client_factory=HashingEmbedder)
            assert report["status"] == "complete", report
    return paths, repository


def provider(llm=None):
    llm = llm or FakeSourceLLM()
    return TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK), llm


def ask(paths, repository, tutor, *, span_provider=None, question=QUESTION, session="s1"):
    return ask_question(loaded(paths), repository, tutor, context="practice", question_md=question,
                        practice_item_id="pi_eigen_1", session_id=session,
                        source_span_provider=span_provider, clock=CLOCK)


def test_tutor_spans_are_retrieved_for_the_question_then_verified(tmp_path):
    paths, repository = setup(tmp_path)
    tutor = CitingTutor()
    span_provider, llm = provider()
    result = ask(paths, repository, tutor, span_provider=span_provider)
    spans = tutor.contexts[0].source_spans
    assert spans and len(spans) <= 4
    assert {span["relation"] for span in spans} == {"retrieved"}
    assert ("ext_book", "s2") in {(span["extraction_id"], span["span_id"]) for span in spans}
    # Assessment material never reaches the verifier, the tutor or a citation.
    rerank_prompts = [context for purpose, context in llm.calls if purpose == "source_rerank"]
    assert rerank_prompts and all(EXAM_QUESTION not in candidate["passage"]
                                  for context in rerank_prompts for candidate in context["candidates"])
    assert all(span["extraction_id"] != "ext_exam" for span in spans)
    assert {(c["extraction_id"], c["span_id"]) for c in result["citations"]} == {
        (span["extraction_id"], span["span_id"]) for span in spans}
    event = repository.question_event(result["event_id"])
    manifest = event["source_context"]["source_retrieval"]
    assert manifest["basis"] == "retrieved_verified" and manifest["spans"] == len(spans)
    assert manifest["verification"]["status"] == "verified"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        verdicts = connection.execute(
            "SELECT judge, verdict, right_kind FROM judgment_ledger WHERE task = 'source_relevance'").fetchall()
    assert len(verdicts) == manifest["candidates"] and {row[0] for row in verdicts} == {"llm"}
    assert {row[2] for row in verdicts} == {"source_span"}


def test_the_question_time_facet_mapping_is_unchanged_by_retrieval(tmp_path):
    paths, repository = setup(tmp_path)
    plain = ask(paths, repository, CitingTutor(), question="Why is this the answer?", session="s1")
    retrieved = ask(paths, repository, CitingTutor(), span_provider=provider()[0],
                    question="Why is this the answer?", session="s2")
    keys = ("facet_learning_object_ids", "learning_object_subject_ids")
    before = repository.question_event(plain["event_id"])["source_context"]
    after = repository.question_event(retrieved["event_id"])["source_context"]
    assert {key: before[key] for key in keys} == {key: after[key] for key in keys}
    assert before["facet_learning_object_ids"]  # the mapping exists, so the check is not vacuous
    assert plain["facets"] == retrieved["facets"]


def test_without_verification_the_tutor_keeps_the_linked_spans_and_says_why(tmp_path):
    paths, repository = setup(tmp_path)
    linked = CitingTutor()
    ask(paths, repository, linked, session="s1")
    metered = CitingTutor()
    span_provider, llm = provider(FakeSourceLLM(provider_type="openrouter"))  # no price -> skipped
    result = ask(paths, repository, metered, span_provider=span_provider, session="s2")
    assert metered.contexts[0].source_spans == linked.contexts[0].source_spans
    assert linked.contexts[0].source_spans[0]["span_id"] == "s7"
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["basis"] == "lo_provenance" and "skipped" in manifest["reason"]
    assert llm.calls == []


def test_a_span_reproducing_the_expected_answer_is_withheld_in_practice(tmp_path):
    paths, repository = setup(tmp_path)
    item = paths.practice_item_path("linear-algebra", "pi_eigen_1")
    text = item.read_text(encoding="utf-8").replace(
        "expected_answer: ANSWER-pi_eigen_1",
        "expected_answer: Eigenvalues are the roots of the characteristic polynomial det(A - tI) of a square matrix.")
    item.write_text(text, encoding="utf-8")
    tutor = CitingTutor()
    span_provider, _llm = provider()
    result = ask(paths, repository, tutor, span_provider=span_provider)
    assert ("ext_book", "s2") not in {(s["extraction_id"], s["span_id"]) for s in tutor.contexts[0].source_spans}
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["withheld_answer_overlap"] >= 1


def test_the_kill_switch_restores_the_linked_spans_and_records_nothing(tmp_path):
    paths, repository = setup(tmp_path, embed=False)
    append_config_toml(paths.root, "[source_retrieval]\nenabled = false\n")
    plain, switched = CitingTutor(), CitingTutor()
    first = ask(paths, repository, plain, session="s1")
    span_provider, llm = provider()
    second = ask(paths, repository, switched, span_provider=span_provider, session="s2")
    assert switched.contexts[0].source_spans == plain.contexts[0].source_spans
    assert llm.calls == []
    for result in (first, second):
        assert "source_retrieval" not in (repository.question_event(result["event_id"])["source_context"] or {})


def test_a_failing_provider_never_costs_the_learner_their_answer(tmp_path):
    paths, repository = setup(tmp_path, embed=False)

    def broken(*_args, **_kwargs):
        raise RuntimeError("retrieval exploded")

    tutor = CitingTutor()
    result = ask(paths, repository, tutor, span_provider=broken)
    assert result["answer_md"] and tutor.contexts[0].source_spans[0]["span_id"] == "s7"
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    timings = manifest.pop("timings_ms")
    assert manifest == {"basis": "lo_provenance", "reason": "retrieval failed (RuntimeError)"}
    assert set(timings) == {"total"} and timings["total"] >= 0


def test_an_unmapped_span_gets_labelled_suggestions_never_candidates(tmp_path):
    paths, repository = setup(tmp_path)
    vault = loaded(paths)
    report = suggest_learning_objects(vault, repository, extraction_id="ext_book", span_id="s12")
    assert report["provenance"] == [] and report["status"] == "suggested"
    assert report["meaning"] == "used"
    assert report["suggestions"][0]["learning_object_id"] == "lo_inner"
    assert {entry["label"] for entry in report["suggestions"]} == {"suggestion"}
    assert suggested_learning_objects(vault, repository, extraction_id="ext_book", span_id="s12") == \
        report["suggestions"]


class ReaderTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def run_tutor_qa(self, context):
        return TutorAnswer(answer_md="Look at the dot product.", question_type="clarification", facets=[])

    def run_promotion_analysis(self, _context):
        return PromotionAnalysis()


def test_a_reader_question_records_the_suggestion_and_promotion_names_it(tmp_path):
    paths, repository = setup(tmp_path)
    vault = loaded(paths)
    result = ask_question(vault, repository, ReaderTutor(), context="reader",
                          question_md="What makes two vectors orthogonal?", extraction_id="ext_book",
                          span_id="s12", learning_object_suggester=suggested_learning_objects, clock=CLOCK)
    event = repository.question_event(result["event_id"])
    context = event["source_context"]
    assert context["candidate_learning_object_ids"] == []
    assert context["suggested_learning_objects"][0]["learning_object_id"] == "lo_inner"
    assert result["suggested_learning_objects"] == context["suggested_learning_objects"]
    with pytest.raises(PromotionError, match="a suggestion and not a provenance link: Inner products"):
        promote_tutor_question(paths.root, ReaderTutor(), event_id=result["event_id"], intent="practice",
                               clock=CLOCK)


def test_suggestions_respect_provenance_and_the_switches(tmp_path):
    paths, repository = setup(tmp_path, embed=False)
    vault = loaded(paths)
    keyword_only = suggest_learning_objects(vault, repository, extraction_id="ext_book", span_id="s12")
    assert keyword_only["meaning"] == "span_not_embedded" and keyword_only["suggestions"]
    append_config_toml(paths.root, "[source_retrieval]\nsuggest_learning_objects = false\n")
    off = suggest_learning_objects(loaded(paths), repository, extraction_id="ext_book", span_id="s12")
    assert off["status"] == "disabled" and off["suggestions"] == []


def test_the_same_question_over_the_same_pool_is_verified_from_the_ledger(tmp_path):
    paths, repository = setup(tmp_path)
    span_provider, llm = provider()
    first = ask(paths, repository, CitingTutor(), span_provider=span_provider, session="s1")
    rerank_calls = sum(1 for purpose, _ in llm.calls if purpose == "source_rerank")
    second = ask(paths, repository, CitingTutor(), span_provider=span_provider, session="s2")
    assert sum(1 for purpose, _ in llm.calls if purpose == "source_rerank") == rerank_calls == 1
    manifests = [repository.question_event(r["event_id"])["source_context"]["source_retrieval"]
                 for r in (first, second)]
    assert [m["verification"]["status"] for m in manifests] == ["verified", "cached"]
    assert manifests[0]["verification"]["verdicts"] == manifests[1]["verification"]["verdicts"]


# --- review F4: the question row lands first, retrieval is time-boxed, no rewrite by default ---


def test_the_question_row_is_written_before_retrieval(tmp_path):
    paths, repository = setup(tmp_path, embed=False)
    seen = []

    def provider(_vault, repo, **_kwargs):
        seen.extend((row["answer_status"], row["question_md"]) for row in repo.question_events(context="practice"))
        return None, {"basis": "lo_provenance", "reason": "probe"}

    result = ask(paths, repository, CitingTutor(), span_provider=provider)
    assert seen == [("pending", QUESTION)]
    event = repository.question_event(result["event_id"])
    assert event["answer_status"] == "answered"
    manifest = event["source_context"]["source_retrieval"]
    assert manifest.pop("timings_ms").keys() == {"total"}  # the provider's wall time, on every path
    assert manifest == {"basis": "lo_provenance", "reason": "probe"}


def test_an_interrupted_retrieval_keeps_the_question(tmp_path):
    paths, repository = setup(tmp_path, embed=False)

    def provider(*_args, **_kwargs):
        raise SystemExit("the app closed during retrieval")

    with pytest.raises(SystemExit):
        ask(paths, repository, CitingTutor(), span_provider=provider)
    rows = repository.question_events(context="practice")
    assert [(row["question_md"], row["answer_status"]) for row in rows] == [(QUESTION, "pending")]


class DeadlineHonouringLLM(FakeSourceLLM):
    """Takes ``latency`` seconds; a request whose timeout is shorter times out."""

    def __init__(self, latency: float, **kwargs):
        super().__init__(**kwargs)
        self.latency = latency
        self.timeouts: list[float | None] = []

    def complete(self, request):
        self.timeouts.append(request.timeout_seconds)
        if request.timeout_seconds is not None and request.timeout_seconds < self.latency:
            from learnloop.ai.errors import AITurnTimeout

            raise AITurnTimeout(f"{request.purpose} timed out")
        return super().complete(request)


def test_a_slow_verification_runs_out_of_time_when_the_time_box_is_restored(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 5\n"
                                   "tutor_deadline_cancels = true\n")
    slow = DeadlineHonouringLLM(latency=30)
    tutor, linked = CitingTutor(), CitingTutor()
    ask(paths, repository, linked, session="s0")
    result = ask(paths, repository, tutor, span_provider=TutorSpanProvider(
        embedder=HashingEmbedder(), rewrite_client=slow, rerank_client=slow, clock=CLOCK))
    assert slow.timeouts and all(timeout is not None and timeout <= 5 for timeout in slow.timeouts)
    assert tutor.contexts[0].source_spans == linked.contexts[0].source_spans
    event = repository.question_event(result["event_id"])
    manifest = event["source_context"]["source_retrieval"]
    assert manifest["basis"] == "lo_provenance" and manifest["reason"] == "verification timed_out"
    assert manifest["time_box_seconds"] == 5 and event["answer_status"] == "answered"


def test_no_paid_step_starts_after_the_time_box(tmp_path):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 0.000001\n"
                                   "tutor_query_rewrite = true\ntutor_deadline_cancels = true\n")
    llm = FakeSourceLLM()
    embedder = HashingEmbedder()
    result = ask(paths, repository, CitingTutor(), span_provider=TutorSpanProvider(
        embedder=embedder, rewrite_client=llm, rerank_client=llm, clock=CLOCK))
    assert llm.calls == [] and embedder.calls == []
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["search"]["rewrite"]["status"] == "timed_out"
    assert manifest["search"]["query_embedding"]["status"] == "timed_out"
    assert manifest["verification"]["status"] == "timed_out" and manifest["basis"] == "lo_provenance"


def test_the_tutor_does_not_rewrite_questions_by_default(tmp_path):
    paths, repository = setup(tmp_path)
    span_provider, llm = provider()
    result = ask(paths, repository, CitingTutor(), span_provider=span_provider)
    assert [purpose for purpose, _ in llm.calls] == ["source_rerank"]
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["search"]["rewrite"] == {"status": "disabled",
                                             "reason": "source_retrieval.tutor_query_rewrite is false"}
    assert manifest["elapsed_ms"] >= 0


def test_the_tutor_records_as_delivered_only_the_spans_it_was_given(tmp_path, monkeypatch):
    """Local contextual retrieval, Codex review F9: the search's candidate pool
    is not a delivery. With a new embedding space on, the delivered rows are
    exactly the verified spans the tutor was given, in that order, and the
    tutor's validated citations join them."""

    import sqlite3

    from learnloop.db.stores.retrieval_spaces import feedback_rows
    from learnloop.source_retrieval import fallback_space
    from tests.local_embeddings_fakes import VOYAGE_PROFILE, FakeVoyageClient

    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, VOYAGE_PROFILE)
    client = FakeVoyageClient()
    monkeypatch.setattr(fallback_space, "fallback_client", lambda _vault: (client, None))
    tutor = CitingTutor()
    span_provider, _llm = provider()
    clear_cache()
    result = ask(paths, repository, tutor, span_provider=span_provider)
    spans = [(span["extraction_id"], span["span_id"]) for span in tutor.contexts[0].source_spans
             if span["relation"] == "retrieved"]
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        rows = feedback_rows(connection)
    query = [row for row in rows if row["event"] == "query"]
    delivered = [(row["extraction_id"], row["span_id"]) for row in rows if row["event"] == "delivered"]
    assert len(query) == 1 and len(query[0]["payload"]["candidates"]) > len(spans)
    assert spans and delivered == spans
    cited = {(row["extraction_id"], row["span_id"]) for row in rows if row["event"] == "cited"}
    assert cited == {(c["extraction_id"], c["span_id"]) for c in result["citations"]} and cited <= set(delivered)
