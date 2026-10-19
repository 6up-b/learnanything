"""RW1c Codex review fixes (docs/reviews/reader-rw1c-codex-review.md), backend.

* **F1.** A Reader question asked inside a workbench session bound to an item
  is help on that item: the question row carries the server-derived item and
  practice session, so the submit's fold counts it, and every displayed
  component (the explanation, the excerpt, the bridge, the cited passages)
  reaches the reveal ledger.
* **F2.** A cold administration refuses every tool, practice request and
  offer, whether the client says so or the server derives it; a bound Reader
  question rebuilt as a tutor caller never reads wider than it was asked.
* **F3.** Item-bound, the guards hold for the complete delivered context (the
  selection's neighbours and the blocks they cite, not only the retrieved
  passages), and the excerpt guard is the span guard (a short key).
* **F7.** "Another way" never shows again a passage the inquiry showed: not as
  an excerpt, not as a citation, and the passages its pressed offers showed
  are excluded from its retrieval too.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.tutor import reader_modes
from tests.reader_tutor_fakes import LookupTutor, ask, call, reader_ctx, spans_given
from tests.source_service_fakes import set_item_answer, table_counts
from tests.test_reader_tutor_retrieval import _bound_session, _workbench_steps

ITEM = "pi_determinant_2"


def _rebind(paths, ctx):
    """A fresh context after the item's YAML changed (the vault reloads)."""

    from tests.library_ask_fixtures import context

    fresh = context(paths.root)
    fresh.reader_tutor_rerank_client = ctx.reader_tutor_rerank_client
    return fresh


# --- F1: a bound Reader question is help on the item ----------------------------------------------


def test_a_bound_reader_question_counts_on_its_items_submission(tmp_path, monkeypatch):
    from learnloop.tutor.tutor_qa import hint_equivalents_for_submission

    tutor = LookupTutor(answer_md="Swapping two rows multiplies the determinant by minus one, so it flips.")
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, "Swapping two rows multiplies the determinant by minus one, so it flips.")
    ctx = _rebind(paths, ctx)
    practice_session = repository.create_session()
    session = _bound_session(repository, ITEM)
    assert hint_equivalents_for_submission(repository, ITEM, practice_session) == 0
    answer = ask(ctx, workbenchSessionId=session)
    event = repository.question_event(answer["eventId"])
    assert event["context"] == "reader"
    assert event["practice_item_id"] == ITEM and event["session_id"] == practice_session
    assert event["hint_equivalent"] is True and event["leak_suspected"] is True
    # The submit's existing fold sees it (the same window as a practice question).
    assert hint_equivalents_for_submission(repository, ITEM, practice_session) == 1
    with repository.connection() as connection:
        reveals = [dict(row) for row in connection.execute(
            "SELECT source_kind, amount, basis FROM reveal_events WHERE question_event_id = ?",
            (answer["eventId"],))]
    tutor_reveal = [row for row in reveals if row["source_kind"] == "tutor_answer"]
    assert tutor_reveal and tutor_reveal[0]["amount"] >= 0.8 and tutor_reveal[0]["basis"] == "tutor_qa:reader"


def test_the_bridge_is_scored_with_the_answer(tmp_path, monkeypatch):
    key = "Swapping two rows multiplies the determinant by minus one, so it flips."
    tutor = LookupTutor(answer_md="Look at what a swap does to each term.", bridge_md=key)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, key)
    ctx = _rebind(paths, ctx)
    repository.create_session()
    session = _workbench_steps(repository, ITEM, ["swap rows 1 and 2", "det stays 5"])
    answer = ask(ctx, spanId="t2", selectionSpanIds=["t2"], selectionQuote="Eigenvalues are the roots",
                 workbenchSessionId=session)
    assert answer["tutor"]["bridgeMd"] == key
    event = repository.question_event(answer["eventId"])
    # The explanation alone does not give the key away; the bridge shown with it does.
    assert event["leak_suspected"] is True and event["leak_overlap"] >= 0.8


def test_an_unbound_reader_question_stays_unbound(tmp_path, monkeypatch):
    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    repository.create_session()
    answer = ask(ctx)
    event = repository.question_event(answer["eventId"])
    assert event["practice_item_id"] is None and event["session_id"] is None and event["hint_equivalent"] is False
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM reveal_events").fetchone()[0] == 0


# --- F2: cold refuses every tool and offer ---------------------------------------------------------


REQUESTS = [
    {"tool": "find_practice", "query": "swap two rows determinant", "intent": "practice",
     "reason": "Practise the sign rule", "facet_ids": [], "learning_object_ids": []},
    {"tool": "find_sources", "query": "determinant changes sign rows swapped", "intent": "explain",
     "reason": "Your other book says it differently", "facet_ids": []},
]


def test_a_cold_ask_offers_nothing(tmp_path, monkeypatch):
    tutor = LookupTutor(tool_requests=REQUESTS)
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    plain = ask(ctx)
    assert plain.get("practiceRequest") or plain.get("toolRequests")  # the control: offers on
    before = table_counts(repository, ["source_tool_calls"])
    answer = ask(ctx, "and during the cold check?", coldActive=True)
    assert "practiceRequest" not in answer and "toolRequests" not in answer and "tutorOffers" not in answer
    assert table_counts(repository, ["source_tool_calls"]) == before


def test_a_server_derived_cold_administration_refuses_every_tool(tmp_path, monkeypatch):
    import learnloop.instructional.policy as policy

    tutor = LookupTutor(tool_requests=REQUESTS)
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    session = _bound_session(repository, ITEM)
    monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == ITEM)
    before = table_counts(repository, ["source_tool_calls"])
    answer = ask(ctx, workbenchSessionId=session)
    assert answer["tutor"]["retrieval"]["status"] == "cold_attempt"
    assert tutor.result_models[-1] == "ReaderTutorAnswer"  # no tool field offered to the model
    assert "practiceRequest" not in answer and "toolRequests" not in answer and "tutorOffers" not in answer
    assert table_counts(repository, ["source_tool_calls"]) == before
    assert all(relation != "retrieved" for _e, _s, relation in spans_given(tutor))


def test_a_bound_reader_question_rebuilds_as_its_items_caller(tmp_path, monkeypatch):
    from learnloop.instructional.policy import caller_for_question_event
    from learnloop.source_retrieval.policy import derive_policy

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    session = _bound_session(repository, ITEM)
    bound = ask(ctx, workbenchSessionId=session)
    vault, _repository = ctx.require_vault()
    caller = caller_for_question_event(vault, repository, bound["eventId"])
    assert caller.item_id == ITEM and derive_policy(caller)[0] == "assisted_practice"
    plain = ask(ctx, "and without the session?")
    assert derive_policy(caller_for_question_event(vault, repository, plain["eventId"]))[0] == "reading"


# --- F3: the complete delivered context is guarded ---------------------------------------------------


def test_item_bound_the_neighbours_and_references_are_guarded_too(tmp_path, monkeypatch):
    tutor = LookupTutor()
    paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, "2 and 3")
    ctx = _rebind(paths, ctx)
    session = _bound_session(repository, ITEM)
    # The selection is the last exercise: its neighbours are the solutions.
    last_exercise = spans["exercises"][-1]
    selection = {"spanId": last_exercise, "selectionSpanIds": [last_exercise],
                 "selectionQuote": "Compute the eigenvalues of the diagonal matrix"}
    control = ask(ctx, **selection)
    solutions = {("ext_text", span) for span in spans["solutions"]}
    unbound = {(e, s) for e, s, _r in spans_given(tutor)}
    assert unbound & solutions, "the control: unbound, a solution neighbour is delivered"
    answer = ask(ctx, "how do I start?", workbenchSessionId=session, **selection)
    given = tutor.contexts[-1]["source_spans"]
    assert not {(s["extraction_id"], s["span_id"]) for s in given} & solutions
    from learnloop.tutor.tutor_qa import span_leaks_expected

    assert not any(span_leaks_expected(s["text"], "2 and 3") for s in given)
    # The learner's own selection (a problem statement) is still theirs to ask about.
    assert ("ext_text", last_exercise) in {(s["extraction_id"], s["span_id"]) for s in given}
    delivery = repository.question_event(answer["eventId"])["source_context"]["delivery"]
    assert delivery["item_bound_withheld"]
    assert control["tutor"]["retrieval"]["policy"] == "reading"


def test_the_excerpt_guard_catches_a_short_key():
    item = SimpleNamespace(expected_answer="2/13")
    spans = [{"extraction_id": "ext", "span_id": "s1", "relation": "retrieved",
              "text": "The required probability is 2/13.", "label": "p"}]
    excerpt = SimpleNamespace(extraction_id="ext", span_id="s1", quote="The required probability is 2/13.")
    kept, why = reader_modes.verify_excerpt(excerpt, spans, item=item)
    assert kept is None and why == "it reproduces the answer to the item being practised"
    control, none = reader_modes.verify_excerpt(excerpt, spans, item=SimpleNamespace(expected_answer="7/9"))
    assert control is not None and none is None


# --- F7: another way never repeats a shown passage ---------------------------------------------------


def test_another_way_drops_a_repeated_excerpt_and_citation():
    spans = [
        {"extraction_id": "ext_text", "span_id": "t3", "relation": "in_view", "text": "Swapping two rows flips it."},
        {"extraction_id": "ext_book", "span_id": "s9", "relation": "retrieved", "source_id": "src_book",
         "text": "A permutation argument shows the sign flips."},
    ]
    answer = SimpleNamespace(excerpt=SimpleNamespace(extraction_id="ext_text", span_id="t3",
                                                     quote="Swapping two rows flips it."), bridge_md=None)
    citations = [{"extraction_id": "ext_text", "span_id": "t3", "label": "a"},
                 {"extraction_id": "ext_book", "span_id": "s9", "label": "b"}]
    request = reader_modes.ReaderTutorRequest(intent="alternative", shown_span_keys=["ext_text:t3"])
    view, shown = reader_modes.finalize(answer, spans, citations, retrieval={"books_cover": True}, request=request)
    assert view["excerpt"] is None and view["dropped_excerpt"] == "this inquiry has already shown that passage"
    assert [(c["extraction_id"], c["span_id"]) for c in shown] == [("ext_book", "s9")]
    assert shown[0]["source_id"] == "src_book" and view["repeated_citations"] == 1
    # An ordinary follow-up may cite the selection again.
    plain, cited = reader_modes.finalize(answer, spans, citations, retrieval={"books_cover": True},
                                         request=reader_modes.ReaderTutorRequest(shown_span_keys=["ext_text:t3"]))
    assert plain["excerpt"] is not None and len(cited) == 2


def test_another_way_excludes_what_the_inquirys_offers_showed(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service
    import learnloop.instructional.tools as tools

    from tests.reader_tutor_fakes import SIGN_PASSAGE, KeepContaining

    tutor = LookupTutor(tool_requests=[{**REQUESTS[1], "query": "cofactor expansion"}])
    # The answer's own lookup keeps the sign passages; the offer's keeps cofactor expansion.
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor, verifier=KeepContaining(SIGN_PASSAGE))
    offer_verifier = KeepContaining("cofactor")
    real_run = tools.run_requested_tool
    monkeypatch.setattr(tools, "run_requested_tool", lambda vault, repo, request_id, **kw: real_run(
        vault, repo, request_id, **{**kw, "clients": {"source_rerank": offer_verifier}}))
    root = ask(ctx)
    (request,) = [r for r in root["toolRequests"] if r["tool"] == "find_sources"]
    ran = call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    keys = [passage["spanKey"] for passage in ran["result"]["passages"]]
    first = {f"{c['extractionId']}:{c['spanId']}" for c in root["citations"]} | set(
        root["tutor"]["retrieval"].get("spanKeys") or [])
    assert keys and not set(keys) & first, "the offer showed a passage the answer did not"
    call(ctx, "record_source_offer_shown", {"toolCallId": request["toolCallId"], "spanKeys": keys})
    calls: list[dict] = []
    real = service.propose_sources
    monkeypatch.setattr(service, "propose_sources",
                        lambda vault, repo, query, **kw: calls.append(kw) or real(vault, repo, query, **kw))
    ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"], retrievalIntent="alternative")
    assert set(calls[-1]["exclude_span_keys"]) >= set(keys)
    retrieved = {f"{e}:{s}" for e, s, relation in spans_given(tutor) if relation == "retrieved"}
    assert not retrieved & set(keys)


@pytest.mark.parametrize("intent", ["alternative"])
def test_another_way_shown_set_reaches_the_request(tmp_path, monkeypatch, intent):
    tutor = LookupTutor()
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    root = ask(ctx)
    other = ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"], retrievalIntent=intent)
    shown = {f"{c['extractionId']}:{c['spanId']}" for c in other["citations"]}
    # Nothing it shows was shown by the answer it is under.
    first = {f"{c['extractionId']}:{c['spanId']}" for c in root["citations"]} | {"ext_text:t3"}
    assert not shown & first
