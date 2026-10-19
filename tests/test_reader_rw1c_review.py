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

from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.tutor import reader_modes
from tests.reader_tutor_fakes import ROOT_QUESTION, LookupTutor, ask, call, reader_ctx, spans_given
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


# --- Re-review (Codex re-review of 015e02706) ---------------------------------------------------------


def _cold_attempt(repository, vault, attempt_id: str, session_id: str | None) -> None:
    item = vault.practice_items[ITEM]
    repository.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": item.id, "learning_object_id": item.learning_object_id,
        "practice_mode": "short_answer", "attempt_type": "independent_attempt", "session_id": session_id,
        "created_at": "2026-01-01T00:00:00Z",
    })


def _cold_row(repository, answer: dict) -> dict:
    """The cold path's practice row for this Ask (not on the wire: read from the store)."""

    with repository.connection() as connection:
        (row,) = connection.execute(
            "SELECT id, hint_equivalent FROM question_events WHERE context = 'practice' AND provider = 'reader' "
            "AND question_md = (SELECT question_md FROM question_events WHERE id = ?)", (answer["eventId"],)).fetchall()
    return {"id": row["id"], "hint_equivalent": bool(row["hint_equivalent"])}


def _reveals(repository, event_id: str) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT source_kind, amount, basis FROM reveal_events WHERE question_event_id = ?", (event_id,))]


def test_a_cold_bound_question_keeps_its_reveals_and_counts_one_hint(tmp_path, monkeypatch):
    """F1 (reopened): the client's cold path records the hint; the bound question
    still carries the item, so what the answer showed reaches the reveal ledger."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_submission

    key = "Swapping two rows multiplies the determinant by minus one, so it flips."
    tutor = LookupTutor(answer_md=key)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, key)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    practice_session = repository.create_session()
    _cold_attempt(repository, vault, "att_cold_rw1c", practice_session)
    session = _bound_session(repository, ITEM)
    answer = ask(ctx, workbenchSessionId=session, coldActive=True, coldAttemptId="att_cold_rw1c")
    event = repository.question_event(answer["eventId"])
    assert event["practice_item_id"] == ITEM
    # The hint is counted once (fix round 4, F1): by the bound question, in the
    # item's window; the cold path's practice row is the link, its flag off.
    assert event["hint_equivalent"] is True
    assert _cold_row(repository, answer)["hint_equivalent"] is False
    assert hint_equivalents_for_submission(repository, ITEM, practice_session) == 1
    tutor_reveal = [row for row in _reveals(repository, answer["eventId"]) if row["source_kind"] == "tutor_answer"]
    assert tutor_reveal and tutor_reveal[0]["amount"] >= 0.8


def test_an_explicitly_cold_question_rebuilds_cold(tmp_path, monkeypatch):
    """F2 (reopened): a cold Ask with no item binding never rebuilds as reading."""

    from learnloop.instructional.policy import caller_for_question_event
    from learnloop.source_retrieval.policy import derive_policy

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    answer = ask(ctx, coldActive=True)
    assert repository.question_event(answer["eventId"])["practice_item_id"] is None
    assert derive_policy(caller_for_question_event(vault, repository, answer["eventId"]))[0] == "cold_attempt"
    found = call(ctx, "find_sources", {"query": "determinant sign swap", "intent": "explain",
                                       "caller": {"kind": "tutor", "ref": answer["eventId"]}})
    assert found["policy"] == "cold_attempt"
    plain = ask(ctx, "and outside the check?")
    assert derive_policy(caller_for_question_event(vault, repository, plain["eventId"]))[0] == "reading"


@pytest.mark.parametrize("retrieval", [False, True])
def test_a_server_derived_cold_refuses_tools_whatever_the_retrieval_switch(tmp_path, monkeypatch, retrieval):
    """F2 (reopened): retrieval off and offers on, the server's own cold status still refuses everything."""

    import learnloop.instructional.policy as policy

    tutor = LookupTutor(tool_requests=REQUESTS)
    _paths, ctx, repository, _spans = reader_ctx(
        tmp_path, monkeypatch, tutor,
        config={"reader_tutor": {"retrieval_enabled": retrieval, "offers_enabled": True}})
    vault, _repository = ctx.require_vault()
    plain = ask(ctx)
    assert plain.get("practiceRequest") or plain.get("toolRequests")  # the control: tools on
    session = _bound_session(repository, ITEM)
    monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == ITEM)
    before = table_counts(repository, ["source_tool_calls"])
    answer = ask(ctx, "during the check?", workbenchSessionId=session)
    assert "practiceRequest" not in answer and "toolRequests" not in answer and "tutorOffers" not in answer
    assert table_counts(repository, ["source_tool_calls"]) == before
    from learnloop.instructional.policy import caller_for_question_event
    from learnloop.source_retrieval.policy import derive_policy

    assert derive_policy(caller_for_question_event(vault, repository, answer["eventId"]))[0] == "cold_attempt"


def test_retrieval_off_a_bound_question_offers_nothing_and_rebuilds_as_its_item(tmp_path, monkeypatch):
    """F2 (reopened): the bound restriction does not depend on the retrieval switch either."""

    from learnloop.instructional.policy import caller_for_question_event
    from learnloop.source_retrieval.policy import derive_policy

    tutor = LookupTutor(tool_requests=REQUESTS)
    _paths, ctx, repository, _spans = reader_ctx(
        tmp_path, monkeypatch, tutor, config={"reader_tutor": {"retrieval_enabled": False, "offers_enabled": True}})
    vault, _repository = ctx.require_vault()
    session = _bound_session(repository, ITEM)
    answer = ask(ctx, workbenchSessionId=session)
    assert "practiceRequest" not in answer and "toolRequests" not in answer
    caller = caller_for_question_event(vault, repository, answer["eventId"])
    assert caller.item_id == ITEM and derive_policy(caller)[0] == "assisted_practice"


EXCERPT_PASSAGE = "Cofactor expansion computes a determinant along any row or column."
PARTIAL_KEY = ("Cofactor expansion along column three; triangular reduction gives pivots whose product "
               "equals twelve exactly.")


def test_a_displayed_excerpt_is_debited_once(tmp_path, monkeypatch):
    """F11: the excerpt is one displayed component; its partial exposure (about
    0.29 of the key) is recorded once, so it does not cross the 0.35 auto-prime
    threshold by being counted twice."""

    from learnloop.attempts.attempts import AUTO_PRIME_REVEAL_THRESHOLD, reveal_total_for_submission
    from learnloop.tutor.tutor_qa import span_answer_overlap

    tutor = LookupTutor(
        answer_md="Think about what each step does.", cite=lambda context: [],
        excerpt=lambda context: next(
            ({"extraction_id": s["extraction_id"], "span_id": s["span_id"], "quote": s["text"]}
             for s in context["source_spans"] if s["text"] == EXCERPT_PASSAGE), None))
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, PARTIAL_KEY)
    ctx = _rebind(paths, ctx)
    repository.create_session()
    exposure = span_answer_overlap(EXCERPT_PASSAGE, PARTIAL_KEY)
    assert exposure < AUTO_PRIME_REVEAL_THRESHOLD <= 2 * exposure  # crosses only when counted twice
    answer = ask(ctx, workbenchSessionId=_bound_session(repository, ITEM))
    assert answer["tutor"]["excerpt"]["quote"] == EXCERPT_PASSAGE and not answer["citations"]
    reveals = _reveals(repository, answer["eventId"])
    assert sum(row["amount"] for row in reveals) == pytest.approx(exposure)
    assert reveal_total_for_submission(repository, ITEM) < AUTO_PRIME_REVEAL_THRESHOLD


# --- Fix round 3 (orchestrator): the replacement row must count where the bound question would --------


def _bound_to(repository, item_id: str, practice_session_id: str) -> str:
    """A workbench session bound to the item and to one practice session (its submit counts there)."""

    session = _bound_session(repository, item_id)
    with repository.connection() as connection:
        connection.execute("UPDATE workbench_sessions SET practice_session_id = ? WHERE id = ?",
                           (practice_session_id, session))
        connection.commit()
    return session


def _later_attempt(repository, vault, attempt_id: str, session_id: str) -> dict:
    """The learner's next attempt on the item in the bound session, after the question."""

    item = vault.practice_items[ITEM]
    repository.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": item.id, "learning_object_id": item.learning_object_id,
        "practice_mode": "short_answer", "attempt_type": "independent_attempt", "session_id": session_id,
        "created_at": "2999-01-01T00:00:00Z",
    })
    return repository.fetch_practice_attempt(attempt_id)


@pytest.mark.parametrize("cold_attempt", ["other_session", "null_session", "no_attempt"])
def test_a_hint_shown_in_the_bound_session_counts_there_once(tmp_path, monkeypatch, cold_attempt):
    """F1 (reopened twice): a cold attempt on the item in another practice session
    A, or in no session, or no cold attempt at all, replaces nothing in the bound
    session B. The bound question keeps its hint, so B's next submission and the
    B attempt both count it once. (``no_attempt`` is a control: no replacement
    row is written, so nothing was ever suppressed.)"""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt, hint_equivalents_for_submission

    key = "Swapping two rows multiplies the determinant by minus one, so it flips."
    tutor = LookupTutor(answer_md=key)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, key)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    session_a = repository.create_session()
    session_b = repository.create_session()
    cold_id = None
    if cold_attempt != "no_attempt":
        cold_id = "att_cold_rw1c_a"
        _cold_attempt(repository, vault, cold_id, session_a if cold_attempt == "other_session" else None)
    answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session_b),
                 coldActive=True, coldAttemptId=cold_id)
    event = repository.question_event(answer["eventId"])
    assert event["practice_item_id"] == ITEM and event["session_id"] == session_b
    assert hint_equivalents_for_submission(repository, ITEM, session_b) == 1
    assert hint_equivalents_for_attempt(repository, _later_attempt(repository, vault, "att_b_rw1c", session_b)) == 1
    assert event["hint_equivalent"] is True
    if cold_attempt == "other_session":
        # Fix round 4 (F1): the cold row in A no longer counts too, so A never sees 2.
        assert _cold_row(repository, answer)["hint_equivalent"] is False


def test_a_same_session_cold_hint_still_counts_once(tmp_path, monkeypatch):
    """The control: the cold row is in the bound session's own window, and only one
    of the two rows counts (1, never 2), at submission and post hoc. Since fix
    round 4 (F1) the bound question carries it, so a session change cannot lose it."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt, hint_equivalents_for_submission

    key = "Swapping two rows multiplies the determinant by minus one, so it flips."
    tutor = LookupTutor(answer_md=key)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, key)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    repository.create_session()
    session_b = repository.create_session()
    _cold_attempt(repository, vault, "att_cold_rw1c_b", session_b)
    answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session_b),
                 coldActive=True, coldAttemptId="att_cold_rw1c_b")
    assert hint_equivalents_for_submission(repository, ITEM, session_b) == 1
    assert hint_equivalents_for_attempt(repository, _later_attempt(repository, vault, "att_b_rw1c", session_b)) == 1
    assert repository.question_event(answer["eventId"])["hint_equivalent"] is True
    assert _cold_row(repository, answer)["hint_equivalent"] is False


# --- Fix round 4 (orchestrator) ------------------------------------------------------------------------


def _end(repository, session_id: str) -> None:
    repository.end_session(session_id)


def test_a_bound_hint_asked_before_any_practice_session_counts_once(tmp_path, monkeypatch):
    """F1 (round 4): no practice session is open when the learner asks; the
    submit then opens one. The bound question counts in the item's window,
    whatever its session (here none), so that submit counts it once, and the
    workbench's own line says so before the submit."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt, hint_equivalents_for_submission
    from learnloop_sidecar.handlers.workbench import _question_hints

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    assert repository.most_recent_open_session() is None
    workbench = _bound_session(repository, ITEM)
    answer = ask(ctx, workbenchSessionId=workbench)
    event = repository.question_event(answer["eventId"])
    assert event["practice_item_id"] == ITEM and event["session_id"] is None and event["hint_equivalent"] is True
    from learnloop.reader import workbench as WB

    assert _question_hints(vault, repository, WB.session_row(repository, workbench)) == 1
    session_c = repository.create_session()
    assert hint_equivalents_for_submission(repository, ITEM, session_c) == 1
    first = _later_attempt(repository, vault, "att_c_rw1c", session_c)
    assert hint_equivalents_for_attempt(repository, first) == 1


def test_a_bound_hint_asked_in_an_ended_session_counts_in_the_next(tmp_path, monkeypatch):
    """F1 (round 4): asked in practice session B, B ends, the learner resumes
    and submits in C: C's submit counts the hint once; the next attempt after
    that counts 0 (the window moved past it)."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt, hint_equivalents_for_submission

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    session_b = repository.create_session()
    answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session_b))
    assert repository.question_event(answer["eventId"])["session_id"] == session_b
    _end(repository, session_b)
    session_c = repository.create_session()
    assert hint_equivalents_for_submission(repository, ITEM, session_c) == 1
    first = _later_attempt(repository, vault, "att_c_rw1c", session_c)
    assert hint_equivalents_for_attempt(repository, first) == 1
    # Counted once: a later attempt of the item, in any session, counts 0.
    assert hint_equivalents_for_submission(repository, ITEM, session_c) == 0
    assert hint_equivalents_for_submission(repository, ITEM, session_b) == 0
    item = vault.practice_items[ITEM]
    repository.insert_practice_attempt({
        "id": "att_c2_rw1c", "practice_item_id": item.id, "learning_object_id": item.learning_object_id,
        "practice_mode": "short_answer", "attempt_type": "independent_attempt", "session_id": session_c,
        "created_at": "2999-01-02T00:00:00Z",
    })
    assert hint_equivalents_for_attempt(repository, repository.fetch_practice_attempt("att_c2_rw1c")) == 0


def test_a_cold_bound_hint_survives_a_session_change_once(tmp_path, monkeypatch):
    """F1 (round 4) with the cold path: asked cold in A (the cold attempt and the
    workbench both in A), A ends, the learner submits in C: counted once in C,
    never twice in A."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_submission

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    session_a = repository.create_session()
    _cold_attempt(repository, vault, "att_cold_rw1c_a", session_a)
    ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session_a), coldActive=True,
        coldAttemptId="att_cold_rw1c_a")
    assert hint_equivalents_for_submission(repository, ITEM, session_a) == 1
    _end(repository, session_a)
    session_c = repository.create_session()
    assert hint_equivalents_for_submission(repository, ITEM, session_c) == 1


def test_an_unbound_reader_question_still_counts_nowhere(tmp_path, monkeypatch):
    """F1 (round 4) control: an unbound Reader question binds no item, so no
    window counts it, as before."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_submission

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    session = repository.create_session()
    answer = ask(ctx)
    assert repository.question_event(answer["eventId"])["practice_item_id"] is None
    assert hint_equivalents_for_submission(repository, ITEM, session) == 0
    assert hint_equivalents_for_submission(repository, ITEM, None) == 0


#: The verify's case (fix round 4, F2): the exercise's own solution states the key.
PROBABILITY_KEY = "2/13"
PROBABILITY_SOLUTION = "The required probability is 2/13."


def _probability_book(monkeypatch) -> None:
    import tests.source_service_fakes as fakes

    book = dict(fakes.TEXTBOOK)
    header, rows = book["solutions"]
    # First, so it is the selected exercise's nearest neighbour.
    book["solutions"] = (header, [(PROBABILITY_SOLUTION, 30), *rows[:2]])
    monkeypatch.setattr(fakes, "TEXTBOOK", book)


@pytest.mark.parametrize("cold", ["client", "server"])
def test_a_cold_bound_question_keeps_the_items_guards(tmp_path, monkeypatch, cold):
    """F2 (round 4): while the bound item is cold, retrieval adds nothing, but
    the selection's neighbours are still delivered; the item's guards hold for
    them, so the solution stating 2/13 reaches neither the tutor nor the excerpt."""

    import learnloop.instructional.policy as policy

    _probability_book(monkeypatch)
    tutor = LookupTutor(excerpt=lambda context: next(
        ({"extraction_id": s["extraction_id"], "span_id": s["span_id"], "quote": s["text"]}
         for s in context["source_spans"] if PROBABILITY_KEY in s["text"]), None))
    paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    session = _bound_session(repository, ITEM)
    last_exercise = spans["exercises"][-1]
    selection = {"spanId": last_exercise, "selectionSpanIds": [last_exercise],
                 "selectionQuote": "Compute the eigenvalues of the diagonal matrix"}
    control = ask(ctx, **selection)
    assert any(PROBABILITY_KEY in s["text"] for s in tutor.contexts[-1]["source_spans"]), \
        "the control: unbound, the solution neighbour is delivered"
    assert control["tutor"]["excerpt"] and PROBABILITY_KEY in control["tutor"]["excerpt"]["quote"]
    extra: dict = {"coldActive": True} if cold == "client" else {}
    if cold == "server":
        monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == ITEM)
    answer = ask(ctx, "how do I start?", workbenchSessionId=session, **selection, **extra)
    given = tutor.contexts[-1]["source_spans"]
    assert not any(PROBABILITY_KEY in s["text"] for s in given)
    assert ("ext_text", last_exercise) in {(s["extraction_id"], s["span_id"]) for s in given}
    assert not (answer.get("tutor") or {}).get("excerpt")
    assert answer["tutor"]["retrieval"]["policy"] == "cold_attempt"
    assert "toolRequests" not in answer and "practiceRequest" not in answer and "tutorOffers" not in answer


def test_another_way_in_the_fallback_repeats_nothing(tmp_path, monkeypatch):
    """F4 (round 4): with the sources service off, "another way" keeps its
    presentation intent, so the passages the inquiry showed are neither quoted
    nor cited again; only the lookup's retrieval intent falls back to explain."""

    tutor = LookupTutor(excerpt=lambda context: next(
        ({"extraction_id": s["extraction_id"], "span_id": s["span_id"], "quote": s["text"]}
         for s in context["source_spans"] if s["span_id"] == "t3"), None))
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor,
                                                  config={"source_service": {"enabled": False}})
    root = ask(ctx)
    assert root["tutor"]["excerpt"]["spanId"] == "t3"  # the control: the selection is quoted
    # Verification unavailable: no abstention, so the shown selection is still the tutor's to quote.
    ctx.reader_tutor_rerank_client = None
    other = ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"],
                retrievalIntent="alternative")
    first = {f"{c['extractionId']}:{c['spanId']}" for c in root["citations"]} | {"ext_text:t3"}
    shown = {f"{c['extractionId']}:{c['spanId']}" for c in other["citations"]}
    assert not shown & first
    assert not other["tutor"].get("excerpt")
    assert other["tutor"]["droppedExcerpt"] == "this inquiry has already shown that passage"
    assert other["tutor"]["intent"] == "alternative" and other["tutor"]["retrieval"]["intent"] == "explain"


DESKTOP_BOUND_ASK = (Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "fixtures"
                     / "readerBoundOffersOnlyAsk.json")


def test_the_desktops_offers_only_bound_ask_refuses_tools_when_cold(tmp_path, monkeypatch):
    """F3 (round 4), the backend half of ``tutorBoundAsk.test.tsx``: the request
    the desktop sends from a bound workbench with only offers on (the shared
    fixture's keys), replayed through the handler while the server derives a
    cold administration of the item: no tool requests, no practice request, no
    offers, no tool call written. The control is the request the desktop sent
    before the fix (no binding): read as plain reading, its tools run."""

    import json

    import learnloop.instructional.policy as policy

    fixture = json.loads(DESKTOP_BOUND_ASK.read_text(encoding="utf-8"))
    tutor = LookupTutor(tool_requests=REQUESTS)
    _paths, ctx, repository, _spans = reader_ctx(
        tmp_path, monkeypatch, tutor, config={"reader_tutor": {"retrieval_enabled": False, "offers_enabled": True}})
    session = _bound_session(repository, ITEM)
    monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == ITEM)
    values = {"answerMode": "answer_directly", "extractionId": "ext_text", "parentExchangeId": None,
              "question": ROOT_QUESTION, "selectionQuote": "the determinant changes sign",
              "selectionSpanIds": ["t3"], "spanId": "t3", "workbenchSessionId": session}
    request = {key: values[key] for key in fixture["requestKeys"]}
    assert request["workbenchSessionId"] == session
    unbound = call(ctx, "reader.ask", {key: value for key, value in request.items() if key != "workbenchSessionId"})
    assert unbound.get("practiceRequest") or unbound.get("toolRequests"), "the control: unbound, tools run"
    before = table_counts(repository, ["source_tool_calls"])
    answer = call(ctx, "reader.ask", {**request, "question": "how do I start?"})
    for key in fixture["absentFromAnswer"]:
        assert key not in answer, key
    assert table_counts(repository, ["source_tool_calls"]) == before
