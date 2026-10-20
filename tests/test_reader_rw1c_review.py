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


# --- Fix round 5 (orchestrator rulings) ----------------------------------------------------------------

OFFERS_ONLY = {"reader_tutor": {"retrieval_enabled": False, "offers_enabled": True}}


def _next_attempt_counts(repository, vault, session_id: str) -> tuple[int, int]:
    """(the next submission's count, the next attempt's post-hoc count) on the item."""

    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt, hint_equivalents_for_submission

    at_submit = hint_equivalents_for_submission(repository, ITEM, session_id)
    return at_submit, hint_equivalents_for_attempt(repository, _later_attempt(repository, vault, "att_next_r5", session_id))


@pytest.mark.parametrize("question_type", ["verification", "other"])
@pytest.mark.parametrize("cold_attempt", ["null", "unfetchable"])
def test_a_cold_bound_ask_is_a_hint_whatever_its_type_and_its_cold_row(tmp_path, monkeypatch, question_type,
                                                                       cold_attempt):
    """R1 (F1, the verify's first case): retrieval on, a cold Ask on the bound
    item with a null or unfetchable ``coldAttemptId`` and a curiosity type. No
    cold practice row can be written, so the bound row carries the hint (L6):
    the next attempt counts it once, and the response says what is stored."""

    tutor = LookupTutor(question_type=question_type)
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    session = repository.create_session()
    answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session), coldActive=True,
                 coldAttemptId=None if cold_attempt == "null" else "att_missing_r5")
    event = repository.question_event(answer["eventId"])
    assert event["practice_item_id"] == ITEM and event["question_type"] == question_type
    assert event["hint_equivalent"] is True
    assert answer["hintEquivalent"] == event["hint_equivalent"]
    with repository.connection() as connection:
        cold_rows = connection.execute("SELECT COUNT(*) FROM question_events WHERE context = 'practice' "
                                       "AND provider = 'reader'").fetchone()[0]
    assert cold_rows == 0  # no cold practice row was written: nothing to deduplicate
    assert _next_attempt_counts(repository, vault, session) == (1, 1)


def test_an_offers_only_bound_question_counts_once(tmp_path, monkeypatch):
    """R1 (F1, the verify's second case): retrieval off and offers on, a
    substantive question in a bound workbench keeps its item, so the next
    attempt counts it once. The unbound control counts nowhere."""

    tutor = LookupTutor()  # mechanism
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor, config=OFFERS_ONLY)
    vault, _repository = ctx.require_vault()
    session = repository.create_session()
    plain = ask(ctx)
    assert repository.question_event(plain["eventId"])["practice_item_id"] is None
    assert plain["hintEquivalent"] is False
    answer = ask(ctx, "how do I start?", workbenchSessionId=_bound_to(repository, ITEM, session))
    event = repository.question_event(answer["eventId"])
    assert event["practice_item_id"] == ITEM and event["session_id"] == session
    assert event["hint_equivalent"] is True and answer["hintEquivalent"] is True
    assert "tutor" not in answer  # retrieval stays off: the base answer contract
    assert _next_attempt_counts(repository, vault, session) == (1, 1)


@pytest.mark.parametrize("retrieval", [True, False])
@pytest.mark.parametrize("cold", [False, True])
@pytest.mark.parametrize("question_type", ["mechanism", "other"])
def test_the_responses_hint_flag_is_the_stored_flag(tmp_path, monkeypatch, retrieval, cold, question_type):
    """R1: one source of truth. Bound, the flag is cold or the ordinary
    classification, retrieval on or off, and the response and the exchange
    read the stored value."""

    tutor = LookupTutor(question_type=question_type)
    _paths, ctx, repository, _spans = reader_ctx(
        tmp_path, monkeypatch, tutor,
        config={"reader_tutor": {"retrieval_enabled": retrieval, "offers_enabled": True}})
    session = repository.create_session()
    answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session), **({"coldActive": True} if cold else {}))
    stored = repository.question_event(answer["eventId"])["hint_equivalent"]
    assert stored is (cold or question_type == "mechanism")
    assert answer["hintEquivalent"] == stored
    with repository.connection() as connection:
        (payload,) = connection.execute("SELECT payload_json FROM interaction_events WHERE id = ?",
                                        (answer["readerAnswerEventId"],)).fetchone()
    import json

    assert json.loads(payload)["hint_equivalent"] == stored


@pytest.mark.parametrize("cold", ["none", "client", "server"])
def test_offers_only_the_bound_items_guards_hold(tmp_path, monkeypatch, cold):
    """R1 (F2): retrieval off and offers on, the verify's probability
    neighbour. Bound, cold or not, the solution stating 2/13 reaches neither
    the tutor's context nor the manifest the exchange records; the unbound
    control shows it."""

    import json

    import learnloop.instructional.policy as policy

    _probability_book(monkeypatch)
    tutor = LookupTutor()
    paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor, config=OFFERS_ONLY)
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    session = _bound_session(repository, ITEM)
    last_exercise = spans["exercises"][-1]
    selection = {"spanId": last_exercise, "selectionSpanIds": [last_exercise],
                 "selectionQuote": "Compute the eigenvalues of the diagonal matrix"}
    ask(ctx, **selection)
    assert any(PROBABILITY_KEY in s["text"] for s in tutor.contexts[-1]["source_spans"]), \
        "the control: unbound, the solution neighbour is delivered"
    extra: dict = {"coldActive": True} if cold == "client" else {}
    if cold == "server":
        monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == ITEM)
    answer = ask(ctx, "how do I start?", workbenchSessionId=session, **selection, **extra)
    given = tutor.contexts[-1]["source_spans"]
    assert not any(PROBABILITY_KEY in s["text"] for s in given)
    assert ("ext_text", last_exercise) in {(s["extraction_id"], s["span_id"]) for s in given}
    assert PROBABILITY_KEY not in json.dumps(answer["manifest"])
    assert "tutor" not in answer  # no excerpt: retrieval is off
    assert answer["manifest"]["delivery"]["itemBoundWithheld"]


ROOT_ANSWER = "Swapping rows flips the sign."
FOLLOW_UP = "so what is the probability?"


@pytest.mark.parametrize("retrieval", [True, False])
@pytest.mark.parametrize("cold", [False, True])
def test_an_earlier_answer_is_rechecked_under_the_binding(tmp_path, monkeypatch, retrieval, cold):
    """R2 (F5): asked unbound, the tutor answered "The required probability
    is 2/13."; bound to the item, a follow-up under that answer must not give
    it to the tutor again. The answer is replaced by the fixed line, the
    thread keeps its shape (both questions, the unrelated root answer), and
    the stored exchange is untouched."""

    import json

    from learnloop.tutor.reader_modes import EARLIER_ANSWER_LEFT_OUT

    tutor = LookupTutor(answer_md=ROOT_ANSWER)
    paths, ctx, repository, _spans = reader_ctx(
        tmp_path, monkeypatch, tutor, config={"reader_tutor": {"retrieval_enabled": retrieval, "offers_enabled": True}})
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    root = ask(ctx)
    tutor.answer_md = PROBABILITY_SOLUTION
    child = ask(ctx, FOLLOW_UP, parentExchangeId=root["readerAnswerEventId"])
    assert child["answerMd"] == PROBABILITY_SOLUTION  # the control: unbound, the tutor said it
    tutor.answer_md = "Start from the sample space."
    session = _bound_session(repository, ITEM)
    follow = ask(ctx, "how do I start?", parentExchangeId=child["readerAnswerEventId"], workbenchSessionId=session,
                 **({"coldActive": True} if cold else {}))
    context = tutor.contexts[-1]
    assert [turn["question_md"] for turn in context["thread"]] == [ROOT_QUESTION, FOLLOW_UP]
    assert [turn["answer_md"] for turn in context["thread"]] == [ROOT_ANSWER, EARLIER_ANSWER_LEFT_OUT]
    assert PROBABILITY_KEY not in json.dumps(context)
    assert PROBABILITY_KEY not in json.dumps(follow["manifest"])
    assert follow["manifest"]["delivery"]["earlierAnswersLeftOut"] == 1
    history = {e["eventId"]: e for e in call(ctx, "reader.ask_history", {"extractionId": "ext_text"})["exchanges"]}
    assert history[child["readerAnswerEventId"]]["answerMd"] == PROBABILITY_SOLUTION
    # Unbound again, the same follow-up reads the earlier answer as it was.
    ask(ctx, "and unbound?", parentExchangeId=child["readerAnswerEventId"])
    assert tutor.contexts[-1]["thread"][-1]["answer_md"] == PROBABILITY_SOLUTION


def test_the_learner_work_keeps_the_learners_own_steps():
    """R2's audit: the bridge's context keeps the learner's own steps; an open
    question's statement (LearnLoop's reading) or a problem line that would
    give the answer away is left out, under a binding only."""

    from learnloop.tutor.reader_modes import BoundAsk, open_question_work, plan_bound_delivery

    leaks = lambda text: "2/13" in text  # noqa: E731 - the injected guard
    binding = BoundAsk(item=SimpleNamespace(id=ITEM, expected_answer=PROBABILITY_KEY), answer_guard=leaks)
    gaps = [{"statement": "The probability is 2/13."}, {"statement": "Which outcomes are equally likely?"}]
    work = [
        *open_question_work(gaps),
        {"kind": "workbench_steps", "author": "the learner", "problem": "Show it is 2/13.",
         "steps": ["count the pairs", "so 2/13?"]},
    ]
    kept = plan_bound_delivery(binding, thread=[], gaps=gaps, learner_work=work).learner_work
    assert [entry.get("statement") for entry in kept if entry["kind"] == "open_question"] == [
        "Which outcomes are equally likely?"]
    steps = next(entry for entry in kept if entry["kind"] == "workbench_steps")
    assert steps["problem"] == "" and steps["steps"] == ["count the pairs", "so 2/13?"]
    assert plan_bound_delivery(None, thread=[], gaps=gaps, learner_work=work).learner_work == work


def _field_rows(vault, attempts: list[tuple[str, str]]):
    from learnloop.field.types import AttemptRow, ItemFeatures

    lo_id = vault.practice_items[ITEM].learning_object_id
    return [AttemptRow(attempt_id, ItemFeatures(ITEM, lo_id, at), 1.0, 1.0) for attempt_id, at in attempts]


@pytest.mark.parametrize("asked,attributed", [("bound_cold", True), ("bound", True), ("unbound", False)])
def test_a_bound_question_precedes_the_next_attempt_in_the_field(tmp_path, monkeypatch, asked, attributed):
    """R3 (F6): a cold bound Ask from a passage without a source-to-LO
    mapping, naming a fetchable prior attempt (the cold row's flag is off:
    the bound row carries the hint). The field still sees the question before
    the next attempt of the item ("questions: with"), through the item window
    the count uses; hints_used and coldness are unchanged. An unbound Reader
    question still attributes nothing."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.field.signals import enrich_attempts, load_interaction_signals
    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    session = repository.create_session()
    _cold_attempt(repository, vault, "att_cold_r5", session)
    if asked == "unbound":
        answer = ask(ctx)
    elif asked == "bound":
        answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session))
    else:
        answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session), coldActive=True,
                     coldAttemptId="att_cold_r5")
        assert _cold_row(repository, answer)["hint_equivalent"] is False
    source = repository.question_event(answer["eventId"])["source_context"]
    assert not source.get("candidate_learning_object_ids"), "the passage has no source-to-LO mapping"
    later = _later_attempt(repository, vault, "att_next_r5", session)
    rows = _field_rows(vault, [("att_cold_r5", "2026-01-01T00:00:00Z"), ("att_next_r5", "2999-01-01T00:00:00Z")])
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        signals = load_interaction_signals(connection, vault, rows)
    enriched = {row.attempt_id: row for row in enrich_attempts(rows, signals)}
    nxt = enriched["att_next_r5"]
    assert nxt.preceded_by_question is attributed
    # Attribution only: the next attempt's coldness and assistance are as they were.
    assert (nxt.features.cold, nxt.retrieval_cold, nxt.help_before_work) == (
        rows[1].features.cold, rows[1].retrieval_cold, rows[1].help_before_work)
    assert enriched["att_cold_r5"].preceded_by_question is False
    assert hint_equivalents_for_attempt(repository, later) == (0 if asked == "unbound" else 1)


def _base_ask_history():
    """fab576ac1's ``ask_history``, read from the base commit (``git archive``)
    and compiled against today's module namespace."""

    import __future__
    import ast
    import io
    import subprocess
    import tarfile

    from learnloop.reader import reader_dialogue as RD

    path = "src/learnloop/reader/reader_dialogue.py"
    try:
        archive = subprocess.run(["git", "archive", "fab576ac1", path], cwd=Path(__file__).resolve().parents[1],
                                 capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("the base commit fab576ac1 is not in this checkout")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        source = tar.extractfile(path).read().decode("utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "ask_history")
    namespace = dict(vars(RD))
    exec(compile(ast.Module(body=[node], type_ignores=[]), f"fab576ac1:{path}", "exec",  # noqa: S102 - the base's own code
                 flags=__future__.annotations.compiler_flag, dont_inherit=True), namespace)
    return namespace["ask_history"]


def test_switching_both_off_restores_the_base_history_projection(tmp_path, monkeypatch):
    """R4 (F7): a saved RW1c answer (an excerpt) projects its ``tutor`` while
    either switch is on; with both off, ``reader.ask_history`` returns exactly
    what the base's projection returns for the same stored event. The durable
    event keeps the view."""

    from learnloop.reader import reader_dialogue as RD
    from tests.library_ask_fixtures import set_config

    base = _base_ask_history()
    tutor = LookupTutor(excerpt=lambda context: next(
        ({"extraction_id": s["extraction_id"], "span_id": s["span_id"], "quote": s["text"]}
         for s in context["source_spans"] if s["span_id"] == "t3"), None))
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    answer = ask(ctx)
    assert answer["tutor"]["excerpt"]
    (on,) = call(ctx, "reader.ask_history", {"extractionId": "ext_text"})["exchanges"]
    assert on["tutor"]["excerpt"]["spanId"] == "t3"
    set_config(paths, "reader_tutor", retrieval_enabled=False, offers_enabled=False)
    ctx = _rebind(paths, ctx)
    off = call(ctx, "reader.ask_history", {"extractionId": "ext_text"})
    assert "tutor" not in off["exchanges"][0]
    monkeypatch.setattr(RD, "ask_history", lambda repository, *, extraction_id, branches=True, **_rest: base(
        repository, extraction_id=extraction_id, branches=branches))
    assert call(ctx, "reader.ask_history", {"extractionId": "ext_text"}) == off
    with repository.connection() as connection:
        (payload,) = connection.execute("SELECT payload_json FROM interaction_events WHERE id = ?",
                                        (answer["readerAnswerEventId"],)).fetchone()
    import json

    assert json.loads(payload)["tutor"]["excerpt"]["span_id"] == "t3"


# --- Fix round 6 (orchestrator rulings) ----------------------------------------------------------------

SPLIT_KEY = "Swapping two rows multiplies the determinant by minus one, so it flips."
SPLIT_FIRST = "Swapping two rows multiplies the determinant."
SPLIT_SECOND = "By minus one, so it flips."
UNRELATED_ANSWER = "Think of the permutations behind each term."


@pytest.mark.parametrize("retrieval", [True, False])
@pytest.mark.parametrize("cold", [False, True])
def test_an_answer_split_across_earlier_turns_is_not_delivered_whole(tmp_path, monkeypatch, retrieval, cold):
    """R1 (F5 reopened): two earlier answers that each say part of the key
    (0.67 and 0.33 alone) say all of it side by side. Bound, the one with the
    higher overlap is left out, so the delivered thread and the manifest no
    longer expose the key; the unrelated root answer and every learner
    question are kept."""

    from learnloop.tutor.reader_modes import EARLIER_ANSWER_LEFT_OUT
    from learnloop.tutor.tutor_qa import span_leaks_expected

    assert not span_leaks_expected(SPLIT_FIRST, SPLIT_KEY) and not span_leaks_expected(SPLIT_SECOND, SPLIT_KEY)
    assert span_leaks_expected(f"{SPLIT_FIRST}\n\n{SPLIT_SECOND}", SPLIT_KEY)
    tutor = LookupTutor(answer_md=UNRELATED_ANSWER)
    paths, ctx, repository, _spans = reader_ctx(
        tmp_path, monkeypatch, tutor, config={"reader_tutor": {"retrieval_enabled": retrieval, "offers_enabled": True}})
    set_item_answer(paths, ITEM, SPLIT_KEY)
    ctx = _rebind(paths, ctx)
    root = ask(ctx)
    tutor.answer_md = SPLIT_FIRST
    first = ask(ctx, "what does a swap do?", parentExchangeId=root["readerAnswerEventId"])
    tutor.answer_md = SPLIT_SECOND
    second = ask(ctx, "by how much?", parentExchangeId=first["readerAnswerEventId"])
    tutor.answer_md = "Start from one row swap."
    session = _bound_session(repository, ITEM)
    follow = ask(ctx, "how do I start?", parentExchangeId=second["readerAnswerEventId"], workbenchSessionId=session,
                 **({"coldActive": True} if cold else {}))
    thread = tutor.contexts[-1]["thread"]
    assert [turn["question_md"] for turn in thread] == [ROOT_QUESTION, "what does a swap do?", "by how much?"]
    assert [turn["answer_md"] for turn in thread] == [UNRELATED_ANSWER, EARLIER_ANSWER_LEFT_OUT, SPLIT_SECOND]
    assert not span_leaks_expected("\n\n".join(turn["answer_md"] for turn in thread), SPLIT_KEY)
    prior = follow["manifest"]["priorExchanges"]
    assert not span_leaks_expected("\n\n".join(turn["answerMd"] for turn in prior), SPLIT_KEY)
    assert follow["manifest"]["delivery"]["earlierAnswersLeftOut"] == 1


def test_a_placeholder_the_key_matches_is_replaced_by_nothing():
    """R1: the replacement is validated too. A degenerate key that the fixed
    line itself states ("while you work this problem") gets the empty answer,
    so nothing delivered matches the guard; the question stays."""

    from learnloop.source_retrieval.reader_tutor import ItemBoundGuard
    from learnloop.tutor.reader_modes import EARLIER_ANSWER_LEFT_OUT, BoundAsk, guard_thread

    guard = ItemBoundGuard(repository=None, item=SimpleNamespace(id=ITEM, expected_answer="while you work this problem"))
    assert guard.text_leaks(EARLIER_ANSWER_LEFT_OUT)
    binding = BoundAsk(item=guard.item, answer_guard=guard.text_leaks, answer_overlap=guard.text_overlap)
    thread = [{"question_md": "how?", "answer_md": "Keep going while you work this problem.", "question_type": "other"},
              {"question_md": "and?", "answer_md": UNRELATED_ANSWER, "question_type": "other"}]
    turns, left_out = guard_thread(thread, binding)
    assert left_out == 1 and [turn["answer_md"] for turn in turns] == ["", UNRELATED_ANSWER]
    assert [turn["question_md"] for turn in turns] == ["how?", "and?"]
    assert not guard.text_leaks("\n\n".join(turn["answer_md"] for turn in turns))


def test_a_mapped_lo_does_not_suppress_the_attribution(tmp_path, monkeypatch):
    """R2 (F6 reopened): the passage maps to the item's LO, the item's subject
    is ``math`` and the question recorded none, so its own row (subject
    ``default``) does not attribute. The zero-mass row always does; it changes
    no other signal, no mass, no coldness, assistance or hint count (compared
    with the derivation without the window link)."""

    from contextlib import closing
    from dataclasses import replace

    import learnloop.field.signals as field_signals
    from learnloop.db.connection import connect
    from learnloop.field.signals import BOUND_QUESTION_SIGNAL, blocks_fast_track, enrich_attempts
    from learnloop.tutor.tutor_qa import hint_equivalents_for_attempt

    tutor = LookupTutor()  # mechanism
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    vault, _repository = ctx.require_vault()
    session = repository.create_session()
    _cold_attempt(repository, vault, "att_cold_r6", session)
    lo_id = vault.practice_items[ITEM].learning_object_id
    import learnloop.reader.reader_progression as progression

    # The passage is mapped to the item's LO (a section-provenance link).
    monkeypatch.setattr(progression, "learning_objects_for_span", lambda *args, **kwargs: [lo_id])
    answer = ask(ctx, workbenchSessionId=_bound_to(repository, ITEM, session))
    assert lo_id in repository.question_event(answer["eventId"])["source_context"]["candidate_learning_object_ids"]
    later = _later_attempt(repository, vault, "att_next_r6", session)
    rows = [replace(row, features=replace(row.features, subject_id="math")) for row in _field_rows(
        vault, [("att_cold_r6", "2026-01-01T00:00:00Z"), ("att_next_r6", "2999-01-01T00:00:00Z")])]

    def derive():
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            signals = field_signals.load_interaction_signals(connection, vault, rows)
        return signals, {row.attempt_id: row for row in enrich_attempts(rows, signals)}

    signals, enriched = derive()
    monkeypatch.setattr(field_signals, "ITEM_WINDOW_QUESTION_CONTEXTS", ())
    unlinked, baseline = derive()
    assert enriched["att_next_r6"].preceded_by_question is True
    assert baseline["att_next_r6"].preceded_by_question is False  # what the suppressed row left
    (bound,) = [s for s in signals if s.signal_type == BOUND_QUESTION_SIGNAL]
    assert (bound.effective_mass, bound.outcome, bound.attempt_id, bound.subject_id) == (0.0, None, None, "math")
    assert not blocks_fast_track(bound)
    assert [s for s in signals if s.signal_type != BOUND_QUESTION_SIGNAL] == list(unlinked)
    for attempt_id in ("att_cold_r6", "att_next_r6"):
        assert replace(enriched[attempt_id], preceded_by_question=False) == replace(
            baseline[attempt_id], preceded_by_question=False)
    assert hint_equivalents_for_attempt(repository, later) == 1


GAP_STATEMENT = "The required probability is 2/13."


def _leaking_gap(repository, vault) -> None:
    """A model-written open question on the passage's (and the item's) LO that states the key."""

    repository.insert_misconception(learning_object_id=vault.practice_items[ITEM].learning_object_id,
                                    statement=GAP_STATEMENT)


def test_a_leaking_gap_statement_never_reaches_the_lookup(tmp_path, monkeypatch):
    """R3 (F8): retrieval and personalization on, a non-cold bound question on
    a passage whose LO has the open question "The required probability is
    2/13." (the key): neither the lookup query nor the verification's prompt
    carries it, nor the bridge's work. The unbound control's query does."""

    import learnloop.instructional.sources as service

    tutor = LookupTutor()
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _leaking_gap(repository, vault)
    queries: list[str] = []
    real = service.propose_sources
    monkeypatch.setattr(service, "propose_sources",
                        lambda vault, repo, query, **kw: queries.append(query) or real(vault, repo, query, **kw))
    passage = {"spanId": "t2", "selectionSpanIds": ["t2"], "selectionQuote": "Eigenvalues are the roots"}
    ask(ctx, "How should I start?", personalized=True, **passage)
    assert GAP_STATEMENT in queries[-1], "the control: unbound, the open question joins the query"
    verifier = ctx.reader_tutor_rerank_client
    seen = len(verifier.prompts)
    ask(ctx, "How should I start?", personalized=True, workbenchSessionId=_bound_session(repository, ITEM), **passage)
    assert PROBABILITY_KEY not in queries[-1] and queries[-1].startswith("How should I start?")
    assert verifier.prompts[seen:], "the verification ran"
    assert not any(PROBABILITY_KEY in prompt for prompt in verifier.prompts[seen:])
    work = tutor.contexts[-1]["reader_tutor"]["learner_work"]
    assert not any(PROBABILITY_KEY in str(entry) for entry in work)


def test_that_didnt_help_bound_withholds_a_leaking_misconception(tmp_path, monkeypatch):
    """R3's audit: "that didn't help" under a binding sends the item's LO's
    misconceptions (statement and correction) to the verification's context;
    one that states the key is withheld there too."""

    tutor = LookupTutor()
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _leaking_gap(repository, vault)
    session = _bound_session(repository, ITEM)
    root = ask(ctx, workbenchSessionId=session)
    verifier = ctx.reader_tutor_rerank_client
    seen = len(verifier.prompts)
    ask(ctx, "That didn't help.", parentExchangeId=root["readerAnswerEventId"], retrievalIntent="remediate",
        workbenchSessionId=session)
    assert verifier.prompts[seen:], "the verification ran"
    assert not any(PROBABILITY_KEY in prompt for prompt in verifier.prompts[seen:])


# --- Fix round 7 (orchestrator ruling) -----------------------------------------------------------------

PASSAGE_T2 = {"spanId": "t2", "selectionSpanIds": ["t2"], "selectionQuote": "Eigenvalues are the roots"}
BEGIN = "how should I begin?"


def _model_written_union(context: dict) -> str:
    """Every model-written text one tutor call carries, as the tutor reads them."""

    texts = [turn["answer_md"] for turn in context["thread"]]
    for entry in (context.get("reader_tutor") or {}).get("learner_work") or []:
        texts.append(str(entry.get("statement") or "") if entry.get("kind") == "open_question"
                     else str(entry.get("problem") or ""))
    return "\n\n".join(text for text in texts if text)


def _misconception(repository, vault, statement: str, correction: str | None = None) -> None:
    repository.insert_misconception(learning_object_id=vault.practice_items[ITEM].learning_object_id,
                                    statement=statement, correction_statement=correction)


@pytest.mark.parametrize("asked", ["bound", "bound_cold", "unbound", "switches_off"])
def test_an_earlier_answer_and_a_gap_are_withheld_as_one(tmp_path, monkeypatch, asked):
    """R1 (F8, the verify's first case): an earlier answer ("Swapping two rows
    multiplies the determinant.", 0.67) and an open gap on the passage's LO
    ("By minus one, so it flips.", 0.33) pass alone but give the key away in
    one tutor call. Bound, cold or not, the plan withholds the higher one, so
    the call's model-written union no longer does, and the manifest records
    exactly the delivered thread. Unbound and with both switches off,
    nothing changes."""

    from learnloop.tutor.reader_modes import EARLIER_ANSWER_LEFT_OUT
    from learnloop.tutor.tutor_qa import span_leaks_expected

    config = {"reader_tutor": {"retrieval_enabled": asked != "switches_off", "offers_enabled": asked != "switches_off"}}
    tutor = LookupTutor(answer_md=SPLIT_FIRST)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor, config=config)
    set_item_answer(paths, ITEM, SPLIT_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _misconception(repository, vault, SPLIT_SECOND)
    root = ask(ctx, BEGIN, personalized=True, **PASSAGE_T2)
    tutor.answer_md = "Start from one row swap."
    extra: dict = {}
    if asked.startswith("bound") or asked == "switches_off":
        extra["workbenchSessionId"] = _bound_session(repository, ITEM)
    if asked == "bound_cold":
        extra["coldActive"] = True
    follow = ask(ctx, "and then?", parentExchangeId=root["readerAnswerEventId"], personalized=True, **extra,
                 **PASSAGE_T2)
    context = tutor.contexts[-1]
    if asked in ("unbound", "switches_off"):
        assert context["thread"][0]["answer_md"] == SPLIT_FIRST  # as before
        if asked == "unbound":
            assert SPLIT_SECOND in _model_written_union(context)
        return
    assert [turn["answer_md"] for turn in context["thread"]] == [EARLIER_ANSWER_LEFT_OUT]
    assert [turn["question_md"] for turn in context["thread"]] == [BEGIN]
    union = _model_written_union(context)
    assert SPLIT_SECOND in union  # the lower one is kept: the plan withholds only what it must
    assert not span_leaks_expected(union, SPLIT_KEY)
    assert follow["manifest"]["priorExchanges"] == [
        {"questionMd": turn["question_md"], "answerMd": turn["answer_md"]} for turn in context["thread"]]
    assert follow["manifest"]["delivery"]["boundWithheld"] == {"answers": 1}


def test_a_gap_and_a_misconceptions_correction_are_withheld_as_one(tmp_path, monkeypatch):
    """R1 (F8, the verify's second case): "that didn't help", bound. One
    misconception states the first half of the key (an open gap and a
    remediation target), another's correction states the second half; the
    verification reads the gaps in its question and the misconceptions in its
    context. Its model-written union no longer gives the key away."""

    from tests.reader_tutor_fakes import prompt_context

    from learnloop.tutor.tutor_qa import span_leaks_expected

    tutor = LookupTutor()
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, SPLIT_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _misconception(repository, vault, SPLIT_FIRST)
    _misconception(repository, vault, "Row swaps are rare.", correction=SPLIT_SECOND)
    session = _bound_session(repository, ITEM)
    root = ask(ctx, BEGIN, personalized=True, workbenchSessionId=session, **PASSAGE_T2)
    verifier = ctx.reader_tutor_rerank_client
    seen = len(verifier.prompts)
    ask(ctx, "That didn't help.", parentExchangeId=root["readerAnswerEventId"], retrievalIntent="remediate",
        personalized=True, workbenchSessionId=session, **PASSAGE_T2)
    contexts = [prompt_context(prompt) for prompt in verifier.prompts[seen:]]
    assert contexts, "the verification ran"
    for context in contexts:
        texts = [context["question"], *(f"{m.get('statement') or ''} {m.get('correction') or ''}"
                                        for m in context.get("misconceptions") or [])]
        assert not span_leaks_expected("\n\n".join(texts), SPLIT_KEY)


def test_a_three_slot_split_is_withheld_as_one(tmp_path, monkeypatch):
    """R1: the key in three thirds, each 0.33 alone, two of them 0.67: an
    earlier answer, an open gap (the bridge's open question) and the problem
    line of the learner's workbench. One tutor call carries all three; the
    plan withholds one (a tie: the most recent, the problem line), and the
    learner's own steps stay."""

    from learnloop.tutor.tutor_qa import span_leaks_expected

    first, second, third = "Swapping two rows", "multiplies the determinant", "by minus one, so it flips"
    tutor = LookupTutor(answer_md=first)
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, SPLIT_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _misconception(repository, vault, second)
    session = _workbench_steps(repository, ITEM, ["swap rows 1 and 2"])
    with repository.connection() as connection:
        connection.execute("UPDATE workbench_sessions SET stem_md = ? WHERE id = ?", (third, session))
        connection.commit()
    root = ask(ctx, BEGIN, personalized=True, **PASSAGE_T2)
    unbound = _model_written_union(tutor.contexts[-1])
    assert second in unbound and third in unbound  # the control: unbound, both are delivered
    tutor.answer_md = "Start from one row swap."
    ask(ctx, "and then?", parentExchangeId=root["readerAnswerEventId"], personalized=True,
        workbenchSessionId=session, **PASSAGE_T2)
    context = tutor.contexts[-1]
    union = _model_written_union(context)
    assert not span_leaks_expected(union, SPLIT_KEY)
    assert context["thread"][0]["answer_md"] == first and second in union and third not in union
    steps = next(e for e in context["reader_tutor"]["learner_work"] if e.get("kind") == "workbench_steps")
    assert steps["steps"] == ["swap rows 1 and 2"] and steps["problem"] == ""


# --- Fix round 8 (orchestrator ruling) -----------------------------------------------------------------

NEAR_KEY_GAP = "The probability is 2/130."


def _long_question(length: int) -> str:
    head = "How should I reason about the determinant when two rows are swapped? "
    return head + "x" * (length - len(head))


def _recording_lookups(monkeypatch) -> list[str]:
    """Every query the Reader's lookup hands the sources (service on or off)."""

    import learnloop.instructional.sources as service
    import learnloop.instructional.tools  # noqa: F401 - bound by name at import: import before patching
    import learnloop.source_retrieval.find_sources as base

    queries: list[str] = []
    real_service, real_base = service.propose_sources, base.find_sources_for_caller
    monkeypatch.setattr(service, "propose_sources",
                        lambda vault, repo, query, **kw: queries.append(query) or real_service(vault, repo, query, **kw))
    monkeypatch.setattr(base, "find_sources_for_caller",
                        lambda vault, repo, query, **kw: queries.append(query) or real_base(vault, repo, query, **kw))
    return queries


@pytest.mark.parametrize("service", [True, False])
@pytest.mark.parametrize("intent", ["explain", "alternative", "remediate"])
def test_a_length_limit_never_cuts_a_statement_into_the_key(tmp_path, monkeypatch, intent, service):
    """R1 (F8, the verify's reproduction): key 2/13, a passing open gap "The
    probability is 2/130." (whole, it scores 0) and a 1,976-character
    learner question: the old 2,000-character cut turned the gap into "... 2/13"
    in the query, its rewrite and the verification's question. Bound, the
    statement is dropped whole, so no delivered query or verification prompt
    holds a text the guard scores as leaking. "Another way" reads its parent's
    question; "that didn't help" adds its own words before the parent's."""

    from tests.reader_tutor_fakes import prompt_context

    from learnloop.tutor.tutor_qa import span_leaks_expected

    assert not span_leaks_expected(NEAR_KEY_GAP, PROBABILITY_KEY)
    tutor = LookupTutor()
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor,
                                                config={"source_service": {"enabled": service}})
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _misconception(repository, vault, NEAR_KEY_GAP)
    queries = _recording_lookups(monkeypatch)
    verifier = ctx.reader_tutor_rerank_client
    session = _bound_session(repository, ITEM)
    follow_up = {"alternative": "Explain it another way", "remediate": "That didn't help."}.get(intent)
    # The parent's length puts the gap across the 2,000-character limit of the query the intent builds.
    question = _long_question(1976 if intent != "remediate" else 1976 - len("That didn't help.") - 1)
    root = ask(ctx, question, personalized=True, workbenchSessionId=session, **PASSAGE_T2)
    if follow_up:
        ask(ctx, follow_up, parentExchangeId=root["readerAnswerEventId"], retrievalIntent=intent,
            personalized=True, workbenchSessionId=session, **PASSAGE_T2)
    assert queries and verifier.prompts, "the lookup and its verification ran"
    assert all(not span_leaks_expected(query, PROBABILITY_KEY) for query in queries)
    for prompt in verifier.prompts:
        context = prompt_context(prompt)
        texts = [context["question"], *(f"{m.get('statement') or ''} {m.get('correction') or ''}"
                                        for m in context.get("misconceptions") or [])]
        assert not any(span_leaks_expected(text, PROBABILITY_KEY) for text in texts)
    assert all(len(query) <= 2000 for query in queries)


def test_a_statement_that_fits_whole_is_still_delivered(tmp_path, monkeypatch):
    """R1: the limit drops only what does not fit whole; a short question
    keeps the gap statement in the bound query."""

    tutor = LookupTutor()
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _misconception(repository, vault, NEAR_KEY_GAP)
    queries = _recording_lookups(monkeypatch)
    ask(ctx, BEGIN, personalized=True, workbenchSessionId=_bound_session(repository, ITEM), **PASSAGE_T2)
    assert queries[-1] == f"{BEGIN} {NEAR_KEY_GAP}"


@pytest.mark.parametrize("bound", [True, False])
def test_the_learners_question_is_truncated_as_before(tmp_path, monkeypatch, bound):
    """R1: the learner's own text is still cut at the limit as before; unbound,
    the whole query is the old one (the old cut, statement included)."""

    from learnloop.source_retrieval.reader_tutor import QUERY_CHARS

    tutor = LookupTutor()
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, ITEM, PROBABILITY_KEY)
    ctx = _rebind(paths, ctx)
    vault, _repository = ctx.require_vault()
    _misconception(repository, vault, NEAR_KEY_GAP)
    queries = _recording_lookups(monkeypatch)
    extra = {"workbenchSessionId": _bound_session(repository, ITEM)} if bound else {}
    long_question = _long_question(2500)
    ask(ctx, long_question, personalized=True, **extra, **PASSAGE_T2)
    assert queries[-1] == long_question[:QUERY_CHARS]
    near = _long_question(1976)
    ask(ctx, near, personalized=True, **extra, **PASSAGE_T2)
    old = f"{near} {NEAR_KEY_GAP}"[:QUERY_CHARS]
    assert queries[-1] == (near if bound else old)
    if not bound:
        assert old.endswith("2/13")  # the unbound query is exactly the base RW1c one
