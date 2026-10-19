"""RW1c: the Reader tutor looks things up (spec_reader_workbench_v1 §4.6; G48, G53).

* **The provider.** Ask in the Reader retrieves from the learner's books with
  its own query (the question, the inquiry's ancestors and, personalized, the
  open gaps on the passage's LOs) through the sources service's
  ``find_sources(verify=True)``; the passages the verification keeps join
  the tutor's context after the selection and its neighbours, which stay
  first; the manifest is stored with the exchange.
* **Policies (G48).** ``reading`` in the Reader, ``assisted_practice`` inside
  a bound workbench session (no exercise, solution or answer-reproducing
  passage), nothing during a cold attempt. When verification cannot run,
  nothing is retrieved (T6's rule 0) and no abstention is claimed.
* **Modes.** A "From your books" excerpt is kept only when its text is in a
  passage the tutor was given (never the learner's selection text, never
  held-out material); otherwise the answer falls back to the explanation.
  The bridge is kept only with the learner's work in context, personalized.
* **Abstention.** Verification kept nothing: the answer opens with the line,
  no excerpt, no citation shown as the books'.
* **Another way / that didn't help.** ``alternative`` excludes every passage
  the inquiry showed and labels how its passages differ; ``remediate`` targets
  the inquiry's named gaps.
* **Held out.** A held-out sentinel never reaches the tutor's prompt, the
  verification's prompt or the displayed excerpt.
* **G53.** With the service absent the base ``find_sources`` serves the
  explain call (another way excludes the shown passages); with it faked, the
  Reader's calls are the documented ones.
* Nothing here writes evidence, mastery, grading inputs or scheduling state.
"""
from __future__ import annotations

import json

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.ids import new_ulid
from learnloop.tutor.reader_modes import ABSTENTION_LINE
from learnloop_sidecar.errors import SidecarError
from tests.reader_tutor_fakes import (
    ROOT_QUESTION, LookupTutor, RejectAll, Verifier, ask, call, reader_ctx, spans_given,
)
from tests.source_service_fakes import learning_state_tables, seed_textbook, set_item_answer, table_counts

NOW = "2026-10-19T10:00:00Z"


def _event(repository, answer):
    return repository.question_event(answer["eventId"])


def _exchange_payload(repository, answer):
    for event in repository.reader_interaction_events(kind="reader_answer_submitted"):
        if event["id"] == answer["readerAnswerEventId"]:
            return event["payload"]
    raise AssertionError("no exchange")


# --- the provider -----------------------------------------------------------------------------


def test_retrieved_passages_join_after_the_selection_and_its_neighbours(tmp_path, monkeypatch):
    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    answer = ask(ctx)
    given = spans_given(tutor)
    relations = [relation for _e, _s, relation in given]
    # The selection and its neighbours first, every retrieved passage after them.
    first_retrieved = relations.index("retrieved")
    assert set(relations[:first_retrieved]) <= {"selected_text", "in_view", "surrounding", "referenced"}
    assert set(relations[first_retrieved:]) == {"retrieved"}
    retrieved = [(e, s) for e, s, relation in given if relation == "retrieved"]
    assert ("ext_book", "s7") in retrieved  # "The determinant changes sign when two rows of a matrix are swapped."
    assert tutor.contexts[-1]["reader_tutor"]["books_cover"] is True
    assert tutor.result_models[-1] == "ReaderTutorAnswerWithTools"
    # The manifest is stored with the exchange, with the spans the tutor was given.
    stored = _event(repository, answer)["source_context"]
    assert stored["source_retrieval"]["basis"] == "reader_lookup"
    assert stored["source_retrieval"]["policy"] == "reading"
    assert stored["source_retrieval"]["find_sources"]["verification"]["status"] == "verified"
    assert [(s["extraction_id"], s["span_id"]) for s in stored["source_spans"]] == [(e, s) for e, s, _r in given]
    payload = _exchange_payload(repository, answer)
    assert payload["manifest"]["source_retrieval"]["span_keys"] == stored["source_retrieval"]["span_keys"]
    assert answer["tutor"]["modes"] == ["grounded"] and answer["tutor"]["abstained"] is False
    assert answer["tutor"]["retrieval"]["policy"] == "reading"


def test_the_tutor_forms_its_own_query_from_the_question_and_the_inquiry(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    calls: list[tuple[str, dict]] = []
    real = service.propose_sources

    def spy(vault, repo, query, **kwargs):
        calls.append((query, dict(kwargs)))
        return real(vault, repo, query, **kwargs)

    monkeypatch.setattr(service, "propose_sources", spy)
    root = ask(ctx)
    ask(ctx, "and what about cofactor expansion?", parentExchangeId=root["readerAnswerEventId"])
    (first_query, first), (second_query, second) = calls
    assert first_query.startswith(ROOT_QUESTION)
    # The follow-up's query carries its ancestor's question too.
    assert second_query.startswith("and what about cofactor expansion?") and ROOT_QUESTION in second_query
    for kwargs in (first, second):
        assert kwargs["verify"] is True and kwargs["intent"] == "explain" and kwargs["scope"] == "library"
        assert kwargs["caller"].kind == "reader" and "policy" not in kwargs


def test_personalized_queries_carry_the_open_gaps_and_the_bridge_sees_the_work(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service

    tutor = LookupTutor(bridge_md='Your step "swap rows 1 and 2" is exactly where the sign flips.')
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    _misconception(repository, "lo_matrices", "Swapping rows leaves the determinant unchanged.")
    _workbench_steps(repository, "pi_determinant_2", ["swap rows 1 and 2", "det stays 5"])
    queries: list[str] = []
    real = service.propose_sources
    monkeypatch.setattr(service, "propose_sources",
                        lambda vault, repo, query, **kw: queries.append(query) or real(vault, repo, query, **kw))
    answer = ask(ctx, spanId="t2", selectionSpanIds=["t2"], selectionQuote="Eigenvalues are the roots")
    assert "Swapping rows leaves the determinant unchanged." in queries[-1]
    work = tutor.contexts[-1]["reader_tutor"]["learner_work"]
    assert {entry["kind"] for entry in work} == {"open_question", "workbench_steps"}
    assert answer["tutor"]["modes"] == ["grounded", "bridge"]
    assert answer["tutor"]["bridgeMd"].startswith("Your step")
    # Personalization off: no gaps in the query, no work in context, no bridge.
    plain = ask(ctx, "why is it a root?", spanId="t2", selectionSpanIds=["t2"], personalized=False)
    assert "Swapping rows leaves" not in queries[-1]
    assert tutor.contexts[-1]["reader_tutor"]["learner_work"] == []
    assert plain["tutor"]["modes"] == ["grounded"] and plain["tutor"]["bridgeMd"] is None
    assert plain["tutor"]["droppedBridge"] == "no work of the learner's was in context"


# --- policies (G48) ----------------------------------------------------------------------------


def _bound_session(repository, item_id: str) -> str:
    session_id = "wbs_" + new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "extraction_id, span_ids_json, source_visible, created_at, updated_at) "
            "VALUES (?, ?, 'Solve it', 'bound', 'reader', 'work_through', 'ext_text', '[\"t3\"]', 1, ?, ?)",
            (session_id, item_id, NOW, NOW))
        connection.commit()
    return session_id


def _workbench_steps(repository, item_id: str, steps: list[str]) -> str:
    session_id = _bound_session(repository, item_id)
    with repository.connection() as connection:
        for index, body in enumerate(steps, start=1):
            connection.execute(
                "INSERT INTO workbench_steps (id, session_id, ordinal, kind, body_md, client_idempotency_key, "
                "created_at) VALUES (?, ?, ?, 'step', ?, ?, ?)",
                ("wst_" + new_ulid(), session_id, float(index), body, f"k{index}", NOW))
        connection.commit()
    return session_id


def _misconception(repository, lo_id: str, statement: str) -> str:
    return repository.insert_misconception(learning_object_id=lo_id, statement=statement)


def test_a_bound_workbench_session_reads_as_its_items_practice(tmp_path, monkeypatch):
    tutor = LookupTutor()
    paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor)
    set_item_answer(paths, "pi_determinant_2", "the determinant changes sign")
    ctx = __import__("tests.library_ask_fixtures", fromlist=["context"]).context(paths.root)
    ctx.reader_tutor_rerank_client = Verifier()
    session = _bound_session(repository, "pi_determinant_2")
    before = table_counts(repository, ["source_tool_calls"])
    answer = ask(ctx, workbenchSessionId=session)
    assert answer["tutor"]["retrieval"]["policy"] == "assisted_practice"
    retrieved = [(e, s) for e, s, relation in spans_given(tutor) if relation == "retrieved"]
    # No exercise, no solution, and nothing that reproduces the item's answer.
    assert not set(retrieved) & {("ext_text", s) for s in spans["exercises"] + spans["solutions"]}
    for span in tutor.contexts[-1]["source_spans"]:
        if span["relation"] == "retrieved":
            assert "changes sign" not in span["text"]
    # Its tools would be rebuilt from the reader question under reading: none are written.
    assert tutor.result_models[-1] == "ReaderTutorAnswer"
    assert "practiceRequest" not in answer and "toolRequests" not in answer
    assert table_counts(repository, ["source_tool_calls"]) == before


def test_a_cold_attempt_retrieves_nothing(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    monkeypatch.setattr(service, "propose_sources", lambda *a, **k: pytest.fail("retrieved during a cold attempt"))
    answer = ask(ctx, coldActive=True)
    assert answer["tutor"]["retrieval"]["status"] == "cold_attempt"
    assert answer["tutor"]["abstained"] is False
    assert all(relation != "retrieved" for _e, _s, relation in spans_given(tutor))


def test_without_a_ready_verification_nothing_is_retrieved_or_claimed(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    ctx.reader_tutor_rerank_client = None
    monkeypatch.setattr(service, "propose_sources", lambda *a, **k: pytest.fail("retrieved without verification"))
    answer = ask(ctx)
    assert answer["tutor"]["retrieval"]["status"].startswith("skipped: verification")
    assert answer["tutor"]["abstained"] is False and answer["tutor"]["abstentionLine"] is None
    assert tutor.contexts[-1]["reader_tutor"]["books_cover"] is None
    assert all(relation != "retrieved" for _e, _s, relation in spans_given(tutor))


# --- modes ---------------------------------------------------------------------------------------


def _quote_of(span_key: tuple[str, str], *, edit: str | None = None):
    def excerpt(context):
        for span in context["source_spans"]:
            if (span["extraction_id"], span["span_id"]) == span_key and span["relation"] != "selected_text":
                text = span["text"] if edit is None else span["text"].replace("sign", edit)
                return {"extraction_id": span_key[0], "span_id": span_key[1], "quote": text}
        return {"extraction_id": span_key[0], "span_id": span_key[1], "quote": "a passage it was never given"}
    return excerpt


def test_a_verbatim_excerpt_is_kept_from_your_books(tmp_path, monkeypatch):
    tutor = LookupTutor(excerpt=_quote_of(("ext_book", "s7")))
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    answer = ask(ctx)
    assert answer["tutor"]["modes"] == ["excerpt", "grounded"]
    excerpt = answer["tutor"]["excerpt"]
    assert (excerpt["extractionId"], excerpt["spanId"]) == ("ext_book", "s7")
    assert "changes sign when two rows" in excerpt["quote"] and excerpt["relation"] == "retrieved"
    # Its text is shown, so its exposure is recorded.
    with repository.connection() as connection:
        rows = connection.execute("SELECT context, extraction_id, span_id, entity_id FROM source_exposure_events "
                                  "WHERE entity_type = 'question_event'").fetchall()
    assert [tuple(row) for row in rows] == [("tutor_citation", "ext_book", "s7", answer["eventId"])]


@pytest.mark.parametrize("excerpt,why", [
    (_quote_of(("ext_book", "s7"), edit="value"), "its text is not in the passage"),
    (lambda context: {"extraction_id": "ext_book", "span_id": "s404", "quote": "Two vectors are orthogonal"},
     "not a passage the tutor was given"),
    (lambda context: {"extraction_id": "ext_text", "span_id": "t3", "quote": "the determinant changes sign"},
     None),
    (lambda context: {"extraction_id": "ext_text", "span_id": "t3", "quote": "sign"}, "too short to be a quote"),
])
def test_an_excerpt_that_is_not_the_books_falls_back_to_the_explanation(tmp_path, monkeypatch, excerpt, why):
    tutor = LookupTutor(excerpt=excerpt)
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    answer = ask(ctx, selectionQuote="the determinant changes sign, in my words")
    if why is None:
        # The in-view block's own words are the book's: kept (the selection text alone is not).
        assert answer["tutor"]["modes"] == ["excerpt", "grounded"]
        assert answer["tutor"]["excerpt"]["relation"] == "in_view"
        return
    assert answer["tutor"]["modes"] == ["grounded"] and answer["tutor"]["excerpt"] is None
    assert answer["tutor"]["droppedExcerpt"] == why
    assert answer["answerMd"] == tutor.answer_md
    assert _event(repository, answer)["source_context"]["reader_tutor"]["dropped_excerpt"] == why


def test_quoting_the_learners_own_selection_is_not_from_the_books(tmp_path, monkeypatch):
    tutor = LookupTutor(excerpt={"extraction_id": "ext_text", "span_id": "t3",
                                 "quote": "my own words about the sign"})
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    answer = ask(ctx, selectionQuote="my own words about the sign")
    assert answer["tutor"]["excerpt"] is None
    assert answer["tutor"]["droppedExcerpt"] == "its text is not in the passage"


# --- abstention ----------------------------------------------------------------------------------


def test_when_verification_keeps_nothing_the_answer_abstains(tmp_path, monkeypatch):
    tutor = LookupTutor(excerpt=_quote_of(("ext_text", "t3")))
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor, verifier=RejectAll())
    answer = ask(ctx)
    tutor_view = answer["tutor"]
    assert tutor_view["abstained"] is True and tutor_view["abstentionLine"] == ABSTENTION_LINE
    assert tutor_view["excerpt"] is None and tutor_view["modes"] == ["grounded"]
    # Nothing in it is labelled as from the books: no citation is shown.
    assert answer["citations"] == [] and tutor_view["withheldCitations"] >= 1
    assert tutor.contexts[-1]["reader_tutor"]["books_cover"] is False
    assert "books_cover is false" in tutor.prompts[-1]
    payload = _exchange_payload(repository, answer)
    assert payload["citations"] == [] and payload["tutor"]["abstained"] is True
    history = call(ctx, "reader.ask_history", {"extractionId": "ext_text"})["exchanges"]
    assert history[0]["tutor"]["abstained"] is True and history[0]["citations"] == []


# --- another way, that didn't help ------------------------------------------------------------


def test_another_way_never_repeats_a_passage_the_inquiry_showed(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service

    tutor = LookupTutor(excerpt=_quote_of(("ext_book", "s7")))
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    calls: list[dict] = []
    real = service.propose_sources
    monkeypatch.setattr(service, "propose_sources",
                        lambda vault, repo, query, **kw: calls.append({"query": query, **kw})
                        or real(vault, repo, query, **kw))
    root = ask(ctx)
    shown = {"ext_text:t3", "ext_book:s7", *answer_keys(root)}
    other = ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"],
                retrievalIntent="alternative")
    call_kwargs = calls[-1]
    assert call_kwargs["intent"] == "alternative" and call_kwargs["query"].startswith(ROOT_QUESTION)
    assert set(call_kwargs["exclude_span_keys"]) >= shown
    second = {f"{e}:{s}" for e, s, relation in spans_given(tutor) if relation == "retrieved"}
    assert not second & shown
    assert other["tutor"]["intent"] == "alternative"
    assert other["tutor"]["retrieval"]["label"] in ("from a different book", "a worked example instead",
                                                     "another passage from your books", None)
    assert tutor.contexts[-1]["reader_tutor"]["intent"] == "alternative"


def answer_keys(answer) -> set[str]:
    return {f"{c['extractionId']}:{c['spanId']}" for c in answer["citations"]} | set(
        answer["tutor"]["retrieval"].get("spanKeys") or [])


def test_that_didnt_help_remediates_the_inquirys_named_gaps(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    calls: list[dict] = []
    real = service.propose_sources
    monkeypatch.setattr(service, "propose_sources",
                        lambda vault, repo, query, **kw: calls.append({"query": query, **kw})
                        or real(vault, repo, query, **kw))
    root = ask(ctx)
    gap_id = _named_gap(repository, root["eventId"])
    unclear = ask(ctx, "I still don't see why the sign flips", parentExchangeId=root["readerAnswerEventId"],
                  retrievalIntent="remediate")
    kwargs = calls[-1]
    assert kwargs["intent"] == "remediate" and kwargs["target_hypotheses"] == [{"kind": "named_gap", "id": gap_id}]
    assert kwargs["query"].startswith("I still don't see why the sign flips")
    # The text starts a branch: a reader question learner-text gaps reads.
    event = _event(repository, unclear)
    assert event["context"] == "reader" and event["question_md"] == "I still don't see why the sign flips"
    assert unclear["parentExchangeId"] == root["readerAnswerEventId"]
    assert unclear["tutor"]["intent"] == "remediate"


def _named_gap(repository, question_event_id: str) -> str:
    gap_id = "ltg_" + new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO learner_text_gaps (id, source_kind, source_id, learner_text, chooser, context_judge, "
            "kind, named_json, action, algorithm_version, pipeline_version, created_at) VALUES "
            "(?, 'tutor_question', ?, 'why?', 'context_model', 'tutor', 'misconception', ?, 'belief_candidate', "
            "'test', 'test', ?)",
            (gap_id, question_event_id, json.dumps({"belief_statement": "a swap keeps the sign"}), NOW))
        connection.commit()
    return gap_id


def test_another_way_with_nothing_new_says_so_honestly(tmp_path, monkeypatch):
    from learnloop.tutor.reader_modes import ALTERNATIVE_ABSTENTION_LINE

    tutor = LookupTutor()
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    root = ask(ctx)
    assert root["tutor"]["abstained"] is False
    # Every passage the verification would keep was shown already.
    other = ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"],
                retrievalIntent="alternative")
    assert other["tutor"]["abstained"] is True
    assert other["tutor"]["abstentionLine"] == ALTERNATIVE_ABSTENTION_LINE


def test_another_way_needs_the_answer_it_is_under(tmp_path, monkeypatch):
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, LookupTutor())
    with pytest.raises(SidecarError) as caught:
        ask(ctx, "Explain it another way", retrievalIntent="alternative")
    assert caught.value.code == "validation_error"


# --- held out --------------------------------------------------------------------------------------

SENTINEL = "QZXSENTINEL"


@pytest.mark.parametrize("held_out", [True, False])
def test_a_held_out_sentinel_never_reaches_the_tutor_the_verifier_or_the_excerpt(tmp_path, monkeypatch, held_out):
    from tests.reader_tutor_fakes import KeepContaining

    tutor = LookupTutor(excerpt={"extraction_id": "ext_held", "span_id": "t2",
                                 "quote": f"{SENTINEL} the determinant changes sign when two rows are swapped"})
    verifier = KeepContaining(SENTINEL.casefold())
    paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor, verifier=verifier)
    held = seed_textbook(repository, source_id="src_held", revision_id="rev_held", extraction_id="ext_held",
                         title="Held-out exam pack", units={"held": ("Held-out problems", [
                             (f"{SENTINEL} the determinant changes sign when two rows are swapped", 2)])})
    if held_out:
        save_unit_selection(repository, "ext_held", list(held), exam_use_modes={"held": "held_out_evaluation"})
    answer = ask(ctx)
    prompts = "\n".join(tutor.prompts + verifier.prompts)
    if not held_out:
        # The control: unmarked, the same passage is retrieved, verified and quoted.
        assert SENTINEL in prompts and answer["tutor"]["excerpt"]["spanId"] == "t2"
        return
    assert SENTINEL not in prompts
    assert SENTINEL not in json.dumps(answer)
    assert answer["tutor"]["excerpt"] is None
    assert answer["tutor"]["droppedExcerpt"] == "not a passage the tutor was given"
    stored = _event(repository, answer)["source_context"]["source_retrieval"]["find_sources"]
    assert stored["exam_withheld"] >= 1


def test_exam_material_never_reaches_the_tutor(tmp_path, monkeypatch):
    from tests.source_retrieval_fakes import EXAM_QUESTION

    tutor = LookupTutor()
    _paths, ctx, _repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    ask(ctx, "how do I compute the eigenvalues of the matrix and justify them?", spanId="t2",
        selectionSpanIds=["t2"], selectionQuote="Eigenvalues are the roots")
    assert all(EXAM_QUESTION not in prompt for prompt in tutor.prompts)
    assert all(e != "ext_exam" for e, _s, _r in spans_given(tutor))


# --- G53: the sources service absent and faked ------------------------------------------------------


def test_with_the_service_absent_the_base_find_sources_serves_explain(tmp_path, monkeypatch):
    import learnloop.source_retrieval.find_sources as base

    tutor = LookupTutor(tool_requests=[{"tool": "find_sources", "query": "rows", "intent": "explain",
                                        "reason": "x", "facet_ids": []}])
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor,
                                                 config={"source_service": {"enabled": False}})
    calls: list[dict] = []
    real = base.find_sources_for_caller
    monkeypatch.setattr(base, "find_sources_for_caller",
                        lambda vault, repo, query, **kw: calls.append(kw) or real(vault, repo, query, **kw))
    root = ask(ctx)
    assert root["tutor"]["retrieval"]["policy"] == "reading" and calls[-1]["intent"] == "explain"
    assert any(relation == "retrieved" for _e, _s, relation in spans_given(tutor))
    # No tool requests; "Practice this" is a plain find_practice on the question.
    assert "toolRequests" not in root
    assert root["practiceRequest"]["request"] == {"query": ROOT_QUESTION}
    other = ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"],
                retrievalIntent="alternative")
    assert calls[-1]["intent"] == "explain" and "ext_text:t3" in calls[-1]["exclude_span_keys"]
    assert other["tutor"]["intent"] == "explain"


def test_with_the_service_faked_the_readers_calls_are_the_documented_ones(tmp_path, monkeypatch):
    import learnloop.instructional.sources as service
    from learnloop.source_retrieval.find_sources import SourceHits

    tutor = LookupTutor()
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    seen: list[dict] = []

    def fake(vault, repo, query, *, caller, intent="explain", **kwargs):
        seen.append({"query": query, "caller": caller, "intent": intent, **kwargs})
        hit = {"extraction_id": "ext_book", "span_id": "s8", "source_id": "src_book", "source_title": "Notes",
               "section": "Determinants", "page": 1, "text": "Cofactor expansion computes a determinant.",
               "role": None}
        return SourceHits(intent=intent, policy="reading", hits=[hit],
                          manifest={"verification": {"status": "verified", "judged": 1, "picked": 1}})

    monkeypatch.setattr(service, "propose_sources", fake)
    answer = ask(ctx)
    (documented,) = seen
    assert documented["intent"] == "explain" and documented["verify"] is True
    assert documented["caller"].kind == "reader" and documented["caller"].item_id is None
    assert ("ext_book", "s8", "retrieved") in spans_given(tutor)
    assert answer["tutor"]["retrieval"]["spanKeys"] == ["ext_book:s8"]


# --- evidence ----------------------------------------------------------------------------------------


def test_the_reader_tutor_writes_no_learning_state(tmp_path, monkeypatch):
    tutor = LookupTutor(excerpt=_quote_of(("ext_book", "s7")),
                        tool_requests=[{"tool": "find_practice", "query": "swap rows", "intent": "practice",
                                        "reason": "Try one", "facet_ids": [], "learning_object_ids": []}])
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    tables = learning_state_tables(repository) + ["reveal_events"]
    before = table_counts(repository, tables)
    root = ask(ctx)
    ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"], retrievalIntent="alternative")
    assert table_counts(repository, tables) == before
