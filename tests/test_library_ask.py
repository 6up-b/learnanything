"""RW4a: ask your library (spec_reader_workbench_v1 §7.3; G17).

* Sources first: an ask returns verbatim passages grouped by source and role,
  never a tutor essay; nothing but retrieval runs until the learner asks for
  notes, a comparison or the tutor.
* Each organizer line cites exactly its own passage (one listwise call through
  ``judge_listwise``, ledger task ``library_contribution``); a line citing
  another is dropped, never repaired; the same request is answered from the
  ledger with the lines validated the first time.
* The personalized chip: on, the organizer sees the learner's open questions on
  the passages' learning objects and at most one passage names one; off, no
  learner state is sent, the order is retrieval rank and ``personalized=False``
  reaches ``find_sources``.
* "Practice this question" is ``find_practice`` with a Reader caller: it
  proposes and writes no attempt.
* The tutor answers only from the pinned passages (the reader context with a
  pinned-span provider): its context holds them and nothing else, and its
  citations stay inside them.
* Every RW4a event is salience-only, refused as evidence and never recorded by
  the UI; the organizer's daily cap holds.
"""
from __future__ import annotations

import json

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.source_retrieval import library_ask as LA
from learnloop.reader import reader_inquiry as RI
from tests.library_ask_fixtures import (
    OrganizerFake,
    ask_rows,
    build_library_vault,
    call,
    context,
    set_config,
    table_counts,
    tutor_with_citations,
)
from tests.source_service_fakes import LEARNING_STATE_TABLES

QUESTION = "eigenvalues characteristic polynomial determinant"


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    return paths, ctx, spans


def _ask(ctx, **extra):
    params = {"query": QUESTION, "entry": "reader", "extractionId": "ext_text", "spanIds": ["t2"],
              "learningObjectIds": ["lo_matrices"], **extra}
    return call(ctx, "reader.library_ask", params)


def test_an_ask_returns_passages_first_and_no_essay(library):
    _paths, ctx, _spans = library
    _vault, repository = ctx.require_vault()
    before = table_counts(repository, ["model_call_receipts", "question_events", *LEARNING_STATE_TABLES])
    result = _ask(ctx)
    assert result["hits"] and all(hit["label"] == "source-authored" and hit["text"] for hit in result["hits"])
    assert not {"answerMd", "answer", "essay"} & set(result)
    assert result["policy"] == "reading" and result["basis"] == "keyword"
    groups = result["groups"]["sources"]
    assert {source["sourceId"] for source in groups} <= {"src_text", "src_book"}
    for source in groups:
        assert [group["group"] for group in source["groups"]] == [
            name for name in LA.GROUP_ORDER if name in {group["group"] for group in source["groups"]}]
    # Nothing but retrieval ran: no model call, no question, no learning state.
    assert table_counts(repository, ["model_call_receipts", "question_events", *LEARNING_STATE_TABLES]) == before
    row = ask_rows(repository)[0]
    manifest = json.loads(row["manifest_json"])
    assert manifest["policy"] == "reading" and manifest["caller"]["kind"] == "reader"
    assert manifest["caller"]["derived_from"] == "reader caller with no item bound"
    assert json.loads(row["organizer_json"]) == {"status": "not_run"}
    # Each passage shown is an exposure (the sources spec's §5.4 rule 3 reads them).
    exposures = repository.source_exposure_events()
    shown = {(event["extraction_id"], event["span_id"]) for event in exposures if event.get("entity_id") == row["id"]}
    assert shown == {(hit["extractionId"], hit["spanId"]) for hit in result["hits"]}


def test_each_organizer_line_cites_exactly_its_own_passage(library):
    _paths, ctx, _spans = library
    _vault, repository = ctx.require_vault()
    asked = _ask(ctx)
    fake = OrganizerFake(wrong_cite=("p2",), unrelated=("p3",))
    ctx.library_organizer_client = fake
    notes = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert notes["status"] == "judged" and len(fake.prompts) == 1  # one organizer call for the whole answer
    keys = [hit["key"] for hit in asked["hits"]]
    by_key = {note["key"]: note for note in notes["notes"]}
    assert by_key[keys[1]]["line"] is None  # cites another passage: dropped, never repaired
    assert notes["droppedLines"] == [{"key": keys[1], "reason": "its line cites another passage"}]
    assert by_key[keys[0]]["line"] == "adds the passage p1's own point"
    assert by_key[keys[0]]["roles"] == ["definition"]  # roles outside the vocabulary are dropped
    assert by_key[keys[2]]["verdict"] == "unrelated"
    with repository.connection() as connection:
        ledger = connection.execute(
            "SELECT task, judge, left_id FROM judgment_ledger WHERE task = 'library_contribution'").fetchall()
    assert len(ledger) == len(keys) and {tuple(row)[1:] for row in ledger} == {("llm", asked["askId"])}
    # The same ask is not paid for twice.
    again = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert again["reused"] is True and len(fake.prompts) == 1


def test_a_cached_organizer_request_keeps_only_the_lines_validated_the_first_time(library):
    _paths, ctx, _spans = library
    first = _ask(ctx)
    fake = OrganizerFake(wrong_cite=("p2",))
    ctx.library_organizer_client = fake
    call(ctx, "reader.library_ask_notes", {"askId": first["askId"]})
    second = _ask(ctx)  # the same question: the same prompt over the same passages
    notes = call(ctx, "reader.library_ask_notes", {"askId": second["askId"]})
    assert notes["status"] == "cached" and len(fake.prompts) == 1
    keys = [hit["key"] for hit in second["hits"]]
    by_key = {note["key"]: note for note in notes["notes"]}
    assert by_key[keys[1]]["line"] is None
    assert by_key[keys[0]]["line"] == "adds the passage p1's own point"


def test_the_personalized_chip(library):
    _paths, ctx, _spans = library
    _vault, repository = ctx.require_vault()
    misconception_id = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        correction_statement="Swapping two rows multiplies the determinant by -1",
        target_facet="facet_determinant", confused_with_facet=None)
    ctx.library_organizer_client = fake = OrganizerFake(speak=f"misconception:{misconception_id}", reverse=True)
    on = _ask(ctx)
    assert on["personalized"] is True
    notes = call(ctx, "reader.library_ask_notes", {"askId": on["askId"]})
    assert [q["statement"] for q in fake.contexts[0]["open_questions"]] == [
        "Swapping rows leaves the determinant unchanged"]
    speaking = [note for note in notes["notes"] if note["speaksTo"]]
    assert len(speaking) == 1 and speaking[0]["speaksTo"]["statement"].startswith("Swapping rows")
    keys = [hit["key"] for hit in on["hits"]]
    assert notes["order"] == list(reversed(keys))  # the organizer orders a personalized answer

    off = _ask(ctx, personalized=False, query=QUESTION + " please")
    row = [r for r in ask_rows(repository) if r["id"] == off["askId"]][0]
    assert json.loads(row["manifest_json"])["main"]["personalized"] is False  # passed through to find_sources
    plain = call(ctx, "reader.library_ask_notes", {"askId": off["askId"]})
    assert "open_questions" not in fake.contexts[-1]
    assert "Swapping rows" not in fake.prompts[-1]
    assert plain["order"] == [hit["key"] for hit in off["hits"]]  # plain retrieval rank
    assert not any(note["speaksTo"] for note in plain["notes"])


def test_practice_this_question_proposes_through_find_practice_and_serves_nothing(library):
    _paths, ctx, _spans = library
    _vault, repository = ctx.require_vault()
    before = table_counts(repository, LEARNING_STATE_TABLES)
    result = call(ctx, "find_practice", {"query": QUESTION, "learningObjectIds": ["lo_matrices"],
                                         "caller": {"kind": "reader", "ref": "ext_text"}})
    assert result["proposalId"] and result["items"]
    assert table_counts(repository, LEARNING_STATE_TABLES) == before


def test_the_tutor_answers_only_from_the_pinned_passages(library, monkeypatch):
    _paths, ctx, spans = library
    _vault, repository = ctx.require_vault()
    asked = _ask(ctx)
    pinned = ["ext_text:t2", "ext_book:s6"]
    tutor = tutor_with_citations([("ext_text", "t2"), ("ext_text", "t3")])
    import learnloop_sidecar.handlers.ai_providers as providers

    class Ready:
        ready = True

    monkeypatch.setattr(providers, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    answer = call(ctx, "reader.library_ask_tutor", {"askId": asked["askId"], "pinnedSpanKeys": pinned})
    assert answer["label"] == "answers only from these 2 passages"
    assert sorted(answer["groundedKeys"]) == sorted(pinned)
    # The tutor saw the pinned passages and nothing else (no selection neighbours).
    prompt = tutor.prompts[0]
    context_spans = json.loads(prompt[prompt.index("{"):])["context"]["source_spans"]
    assert {(s["extraction_id"], s["span_id"]) for s in context_spans} == {("ext_text", "t2"), ("ext_book", "s6")}
    # Its citations stay inside them: t3 was never provided, so it is dropped.
    assert [(c["extractionId"], c["spanId"]) for c in answer["citations"]] == [("ext_text", "t2")]
    event = repository.question_event(answer["eventId"])
    assert event["context"] == "reader" and event["source_context"]["source_retrieval"]["basis"] == "pinned"
    assert ask_rows(repository)[0]["question_event_id"] == answer["eventId"]


def test_every_rw4a_event_is_salience_only_refused_as_evidence_and_never_client_recorded(library, monkeypatch):
    _paths, ctx, _spans = library
    _vault, repository = ctx.require_vault()
    asked = _ask(ctx)
    ctx.library_organizer_client = OrganizerFake()
    call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    import learnloop_sidecar.handlers.ai_providers as providers

    class Ready:
        ready = True

    monkeypatch.setattr(providers, "ready_tutor_qa_provider",
                        lambda vault: ("fake", Ready(), tutor_with_citations([])))
    call(ctx, "reader.library_ask_tutor", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2"]})
    from learnloop.source_retrieval.compare import Comparison
    import learnloop.instructional.sources as service

    monkeypatch.setattr(service, "propose_comparison",
                        lambda *a, **k: Comparison(status="compared", policy="reading", comparison_id=None))
    call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    seen = set()
    for event in repository.reader_interaction_events(kind="reader_action_invoked"):
        name = event["payload"].get("event")
        if name not in RI.RW4A_SERVER_EVENTS:
            continue
        seen.add(name)
        assert event["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(event)
    assert seen == set(RI.RW4A_SERVER_EVENTS) == set(LA.EVENTS)
    for name in RI.RW4A_SERVER_EVENTS:
        with pytest.raises(RI.InquiryError):
            RI.record_activity(repository, [{"kind": "reader_action_invoked", "event": name, "payload": {}}])


def test_the_organizers_daily_cap_holds(library):
    paths, ctx, _spans = library
    set_config(paths, "library_ask", max_daily_cost_usd=0.0)
    ctx = context(paths.root)
    asked = _ask(ctx)
    ctx.library_organizer_client = fake = OrganizerFake()
    notes = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert notes["status"] == "capped" and "library_ask.max_daily_cost_usd" in notes["reason"]
    assert fake.prompts == [] and notes["notes"] == []


def test_a_failed_organizer_keeps_the_passages(library):
    _paths, ctx, _spans = library
    asked = _ask(ctx)
    ctx.library_organizer_client = OrganizerFake(fail=True)
    notes = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert notes["status"] == "failed" and notes["notes"] == []
    assert asked["hits"]  # the excerpts were already shown, and stay
