"""Reader CA3: compare from anywhere (ux_reader_compare_ask_v1 §4, X1/X2, §12.2; K12).

* One request for every door: the selection verb, the ask box's comparison,
  the tutor's offer and *compare these books* in a library answer all reach
  ``reader.library_compare`` with one payload shape; none needs a pin, and
  pins still work. The policy is the server's, never the request's.
* ``compare_sources`` takes an anchor (compared first as its book's passage,
  after the pins' filters) and named books that only narrow the scope (a book
  outside it is refused; the books not named are listed, never sent).
* ``compare_scope``: one Decider request reads the ask box's (or the refine
  box's) words: a comparison or not, which books are named (one yes/no per
  book, argmax), the topic and an unknown name as spans of the learner's own
  words; failures read nothing; every reading is a ``judgment_ledger`` row and
  the learner's change is a ``learner_card`` row superseding it.
* ``reader_compare.scope_enabled`` off: the RPC takes only today's pinned
  request, the new RPCs refuse, the palette and the prompt contract are
  today's.

Every model is a fake (no network).
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from learnloop.ai.decisions import ChoiceAnswer, ChoiceQuestion, DecisionResult, NoulAnswer, NoulQuestion
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.reader import reader_intent as RI
from learnloop.source_retrieval import compare_scope as CS
from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval.compare import compare_sources
from learnloop.source_retrieval.policy import CallerContext, PolicyRefused
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, finish_job, set_config
from tests.recap_fixtures import call as call_rpc
from tests.router_model_fakes import FakeDecider
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, seed_textbook

QUESTION = "why does the determinant change sign when two rows are swapped"


# -- fakes -----------------------------------------------------------------------------------------


class ScopeDecider(FakeDecider):
    """The Decider at its listed price, answering each question by name:
    ``choices`` maps a question to the option it prefers (a spanned option
    may be named by its text), ``named`` the books' titles it says yes to."""

    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self, *, choices: dict[str, str] | None = None, named: tuple[str, ...] = (),
                 error: Exception | None = None, tie: str | None = None) -> None:
        super().__init__(error=error)
        self.prefer = dict(choices or {})
        self.named = set(named)
        self.tie = tie

    def _decide(self, state, questions, *, purpose, timeout_seconds):
        from learnloop.ai.execution import report_call_usage

        self.calls.append({"state": state, "questions": dict(questions), "purpose": purpose,
                           "timeout_seconds": timeout_seconds})
        if self.error is not None:
            raise self.error
        report_call_usage({"input_tokens": 1200, "output_tokens": 16, "cost": 0.0004})
        answers: dict[str, Any] = {}
        for name, question in questions.items():
            if isinstance(question, ChoiceQuestion):
                options = list(question.options)
                wanted = self.prefer.get(name)
                pick = next((option for option in options if option == wanted
                             or (question.options[option] or "").strip('"') == wanted), None)
                if name == self.tie:
                    probabilities = {option: 1.0 / len(options) for option in options}
                else:
                    pick = pick or options[0]
                    rest = 0.1 / max(1, len(options) - 1)
                    probabilities = {option: (0.9 if option == pick else rest) for option in options}
                    if len(options) == 1:
                        probabilities = {pick: 1.0}
                answers[name] = ChoiceAnswer(choice=pick or options[0], probabilities=probabilities, confidence=0.5)
            elif isinstance(question, NoulQuestion):
                said = any(title in question.instructions for title in self.named)
                answers[name] = NoulAnswer(p_yes=0.8 if said else 0.1)
        return DecisionResult(answers=answers, model=self.model, input_tokens=1200, output_tokens=16, cost=0.0004,
                              response_id="dec_1", provider="Perplexity", raw={"model": self.model})


BOOKS = [CS.Book("b1", "src_axler", "Linear Algebra Done Right", "axler-ladr"),
         CS.Book("b2", "src_strang", "Introduction to Linear Algebra", "strang"),
         CS.Book("b3", "src_lay", "Linear Algebra and Its Applications", "lay")]


def _ledger(repository) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'compare_scope' ORDER BY created_at, rowid")]


def _receipts(repository) -> int:
    with repository.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'compare_scope' AND parent_call_id IS NULL"
        ).fetchone()[0]


# -- compare_sources: the anchor and named books -------------------------------------------------------


@pytest.fixture
def textbook(tmp_path):
    return build_textbook_vault(tmp_path / "vault")


def _third(repository) -> None:
    seed_textbook(repository, source_id="src_third", revision_id="rev_third", extraction_id="ext_third",
                  title="Third Book", units={"c1": ("Determinants", [
                      ("Swapping two rows of a matrix changes the sign of its determinant, by the alternating "
                       "property of determinants.", 1)])})


def test_an_anchor_needs_no_pin_and_leads_as_its_books_passage(textbook):
    paths, repository, spans = textbook
    llm = FakeServiceLLM()
    anchor = f"ext_text:{spans['ch5'][2]}"
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             anchor_span_keys=[anchor], client=llm, verify_client=llm)
    assert result.status == "ok"
    first = result.sources[0]
    assert first["anchor"] is True and (first["extraction_id"], first["span_id"]) == ("ext_text", spans["ch5"][2])
    assert "multiplies its determinant by -1" in first["passage"]
    # The anchor's book is its passage: compared once, and the other book was discovered.
    assert [entry["source_id"] for entry in result.sources].count("src_text") == 1
    assert "src_book" in {entry["source_id"] for entry in result.sources}
    assert result.manifest["anchor_keys"] == [["ext_text", spans["ch5"][2]]]
    assert "source_ids" not in result.manifest and not result.dropped_pins


def test_named_books_only_narrow_and_the_others_are_listed_never_sent(textbook):
    paths, repository, _spans = textbook
    _third(repository)
    llm = FakeServiceLLM()
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             source_ids=["src_text", "src_book"], client=llm, verify_client=llm)
    compared = {entry["source_id"] for entry in result.sources}
    assert compared == {"src_text", "src_book"}
    listed = {entry["source_id"]: entry["label"] for entry in result.also_discussed_in}
    assert listed == {"src_third": "also discussed in (not compared)"}
    assert result.manifest["source_ids"] == ["src_text", "src_book"]
    # The third book's passage reached no model: only the named books were verified and compared.
    assert result.manifest["verification"]["sources_in_scope"] == 2


def test_a_named_book_outside_the_scope_is_refused_before_anything_is_read(textbook):
    paths, repository, _spans = textbook
    llm = FakeServiceLLM()
    with pytest.raises(PolicyRefused) as caught:
        compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                        source_ids=["src_text", "src_elsewhere"], client=llm, verify_client=llm)
    assert caught.value.code == "scope_refused"
    assert llm.calls == []


def test_an_anchor_obeys_the_pins_filters(textbook):
    paths, repository, spans = textbook
    caller = CallerContext(kind="tutor", context="practice", item_id="pi_determinant_2")
    result = compare_sources(loaded(paths), repository, QUESTION, caller=caller,
                             anchor_span_keys=[f"ext_text:{spans['solutions'][1]}"],
                             client=FakeServiceLLM(), verify_client=FakeServiceLLM())
    assert result.policy == "assisted_practice"
    assert [pin["span_id"] for pin in result.dropped_pins] == [spans["solutions"][1]]
    assert "anchor_keys" not in result.manifest
    assert not any(entry.get("anchor") for entry in result.sources)


def test_without_the_ca3_arguments_the_manifest_is_todays(textbook):
    paths, repository, _spans = textbook
    result = compare_sources(loaded(paths), repository, QUESTION, caller=CallerContext(kind="reader"),
                             client=FakeServiceLLM(), verify_client=FakeServiceLLM())
    assert "anchor_keys" not in result.manifest and "source_ids" not in result.manifest
    assert not any("anchor" in entry for entry in result.sources)


# -- the RPC: one request for every door --------------------------------------------------------------


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    import learnloop.instructional.sources as service

    seen: list[dict[str, Any]] = []
    real = service.propose_comparison
    llm = FakeServiceLLM()

    def spy(vault, repository, query, *, caller, **kwargs):
        seen.append({"query": query, "caller": caller, **kwargs})
        return real(vault, repository, query, caller=caller, client=llm, verify_client=llm, **kwargs)

    monkeypatch.setattr(service, "propose_comparison", spy)
    ctx = context(paths.root)
    return paths, ctx, seen


def _row(repository, ask_id):
    return next(row for row in ask_rows(repository) if row["id"] == ask_id)


def test_the_selection_verb_compares_its_anchor_with_no_pin(library):
    _paths, ctx, seen = library
    _vault, repository = ctx.require_vault()
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_text", "anchorSpanIds": ["t3"],
        "openSourceId": "src_text"})
    assert table["status"] == "ok" and table["askId"]
    assert table["rows"][0]["isOpenSource"] is True and table["rows"][0]["key"] == "ext_text:t3"
    assert table["scope"] == {"door": "selection", "question": QUESTION, "sourceIds": [], "anchorKeys": ["ext_text:t3"]}
    assert {book["sourceId"] for book in table["library"]} == {"src_text", "src_book"}  # no exam paper
    (request,) = seen
    assert request["pinned_span_keys"] == [] and request["anchor_span_keys"] == ["ext_text:t3"]
    assert "policy" not in request and request["caller"].kind == "reader"
    row = _row(repository, table["askId"])
    manifest = json.loads(row["manifest_json"])
    assert manifest["comparison_only"] is True and manifest["door"] == "selection"
    assert manifest["policy"] == "reading" and row["query_md"] == QUESTION
    assert json.loads(row["anchor_json"])["span_ids"] == ["t3"]


def test_the_four_doors_send_one_request_shape(library):
    _paths, ctx, seen = library
    _vault, repository = ctx.require_vault()
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"]})
    doors = {
        "selection": {"door": "selection", "question": QUESTION, "extractionId": "ext_text", "anchorSpanIds": ["t3"]},
        "ask_box": {"door": "ask_box", "question": "determinant sign", "extractionId": "ext_text",
                    "sourceIds": ["src_text", "src_book"]},
        "tutor_offer": {"door": "tutor_offer", "question": QUESTION, "extractionId": "ext_text",
                        "anchorSpanIds": ["t3"], "toolCallId": "stc_1"},
        "library_answer": {"door": "library_answer", "askId": asked["askId"], "sourceIds": ["src_text", "src_book"]},
    }
    for door, params in doors.items():
        table = call(ctx, "reader.library_compare", params)
        assert table["scope"]["door"] == door and table["status"] in ("ok", "too_few_sources"), door
        assert set(table) >= {"rows", "alsoDiscussedIn", "scope", "library", "askId"}
    # The same service call, whatever the door: never a client policy, never a pin.
    assert len(seen) == 4
    for request in seen:
        assert "policy" not in request and request["pinned_span_keys"] == []
        assert set(request) - {"query", "caller", "pinned_span_keys", "anchor_span_keys", "source_ids"} == set()
    assert seen[1]["source_ids"] == ["src_text", "src_book"] and seen[1]["query"] == "determinant sign"
    assert seen[3]["query"] == QUESTION  # the library answer's own question
    tutor_row = next(row for row in ask_rows(repository) if json.loads(row["manifest_json"]).get("door") == "tutor_offer")
    assert json.loads(tutor_row["manifest_json"])["tool_call_id"] == "stc_1"


def test_pins_still_work_with_the_switch_on(library):
    _paths, ctx, seen = library
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"]})
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"]})
    assert table["scope"]["door"] == "pins" and seen[-1]["pinned_span_keys"] == ["ext_book:s6", "ext_text:t3"]
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_compare", {"askId": asked["askId"], "door": "pins", "pinnedSpanKeys": ["ext_book:s6"]})


def test_a_library_answer_door_takes_its_answers_question_never_a_new_one(library):
    _paths, ctx, _seen = library
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"]})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"door": "library_answer", "askId": asked["askId"], "question": "other"})
    assert caught.value.code == "validation_error"


def test_a_named_book_outside_the_scope_is_refused_by_the_rpc(library):
    _paths, ctx, seen = library
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"door": "ask_box", "question": QUESTION, "sourceIds": ["src_nowhere"]})
    assert caught.value.code == "scope_refused"


def test_an_exam_anchor_is_refused_before_anything_is_read(library):
    _paths, ctx, seen = library
    _vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        (span_id,) = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' ORDER BY ordinal DESC LIMIT 1"
        ).fetchone()
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"door": "selection", "question": QUESTION, "extractionId": "ext_exam",
                                             "anchorSpanIds": [span_id]})
    assert caught.value.code == "exam_material" and seen == []
    assert ask_rows(repository) == []


def test_switched_off_the_rpc_is_todays_exactly(library):
    paths, _ctx, seen = library
    set_config(paths, "reader_compare", scope_enabled=False)
    ctx = context(paths.root)
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"]})
    # A door's request, an anchor and one pin are refused as today refuses them.
    for params in ({"door": "selection", "question": QUESTION, "extractionId": "ext_text", "anchorSpanIds": ["t3"]},
                   {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6"]},
                   {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"],
                    "sourceIds": ["src_book"]}):
        with pytest.raises(ValidationError):
            call(ctx, "reader.library_compare", params)
    assert seen == []
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"]})
    assert "scope" not in table and "library" not in table
    assert set(seen[0]) == {"query", "caller", "pinned_span_keys"}
    # The contract, the palette and the reading are today's.
    contract = call_rpc(ctx, "reader.prompt_contract", {})
    assert "compareScope" not in contract["libraryAsk"]
    actions = [action["id"] for group in contract["intent"]["palette"] for action in group["actions"]]
    assert "compare_books" not in actions
    with pytest.raises(SidecarError) as caught:
        call_rpc(ctx, "reader.compare_scope", {"text": "how do my books treat this"})
    assert caught.value.code == "reader_compare_scope_disabled"


def test_switched_on_the_contract_and_the_palette_offer_it(library):
    _paths, ctx, _seen = library
    contract = call_rpc(ctx, "reader.prompt_contract", {})
    assert contract["libraryAsk"]["compareScope"] is True
    transfer = next(group for group in contract["intent"]["palette"] if group["group"] == "transfer")
    ids = [action["id"] for action in transfer["actions"]]
    assert ids.index("compare_books") == ids.index("where_else_explained") + 1
    action = transfer["actions"][ids.index("compare_books")]
    assert action["label"] == "how do my other books treat this?" and action["effect"] == {"kind": "compare", "door": "selection"}


def test_the_intent_question_set_moves_only_with_the_verb():
    on = RI.Availability(library=True, compare_scope=True)
    off = RI.Availability(library=True)
    assert RI.question_set_version(off) == RI.QUESTION_SET_VERSION
    assert RI.question_set_version(on) == RI.QUESTION_SET_VERSION + RI.COMPARE_QUESTION_SET_SUFFIX
    assert "compare_books" not in {action.id for action in RI.available_actions(off)}
    assert "compare_books" not in {action.id for action in RI.available_actions(
        RI.Availability(library=True, compare_scope=True, model=False))}  # a held-out passage: nothing to a model
    assert "compare_books" not in {action.id for action in RI.available_actions(
        RI.Availability(library=True, compare_scope=True, notes=True))}


# -- compare_scope: the reading --------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    return loaded(paths), repository


def _read(vault, repository, text, decider, **kwargs):
    return CS.read(vault.root, vault.config, repository, text=text, books=kwargs.pop("books", BOOKS),
                   client_factory=lambda: decider, **kwargs)


def test_a_reading_names_books_a_topic_and_an_unknown_name(repo):
    vault, repository = repo
    decider = ScopeDecider(choices={"intent": "compare", "topic": "eigenvalues", "unmatched": "Hoffman"},
                           named=("Linear Algebra Done Right", "Introduction to Linear Algebra"))
    reading = _read(vault, repository, "how do Axler, Strang and Hoffman treat eigenvalues?", decider)
    assert (reading.status, reading.intent) == ("read", "compare")
    assert reading.source_ids == ["src_axler", "src_strang"]
    assert reading.topic == "eigenvalues" and reading.unmatched == "Hoffman"
    (request,) = decider.calls
    # One request: the intent, one yes/no per book, the unknown name and the topic.
    assert set(request["questions"]) == {"intent", "book:b1", "book:b2", "book:b3", "unmatched", "topic"}
    assert request["timeout_seconds"] == vault.config.reader_compare.scope_timeout_seconds
    assert all(span.strip('"') in request["state"]["learner_text"]
               for span in request["questions"]["topic"].options.values() if span.startswith('"'))
    (row,) = _ledger(repository)
    assert (row["judge"], row["verdict"], row["prompt_version"]) == ("decider", "compare", CS.QUESTION_SET_VERSION)
    assert "Hoffman" not in json.dumps(row) and "eigenvalues" not in json.dumps(row)  # the words only as a hash
    assert json.loads(row["rationale"])["named_source_ids"] == ["src_axler", "src_strang"]
    assert _receipts(repository) == 1


def test_a_library_question_is_not_a_comparison(repo):
    vault, repository = repo
    reading = _read(vault, repository, "what is an eigenvalue", ScopeDecider(choices={"intent": "ask"}))
    assert (reading.status, reading.intent, reading.source_ids) == ("read", "ask", [])
    assert reading.topic == "what is an eigenvalue"  # the first option: all of the words


def test_an_empty_text_makes_no_call(repo):
    vault, repository = repo
    decider = ScopeDecider()
    assert _read(vault, repository, "   ", decider).status == "empty"
    assert decider.calls == [] and _ledger(repository) == []


@pytest.mark.parametrize("error, reason", [
    (AIProviderUnavailable("Decider unavailable"), "unavailable"),
    (TimeoutError("timed out"), "timeout"),
    (SpendLimitExceeded("calls"), "refused"),
    (RuntimeError("boom"), "failed"),
])
def test_a_decider_that_cannot_answer_reads_nothing(repo, error, reason):
    vault, repository = repo
    reading = _read(vault, repository, "how do Axler and Strang treat eigenvalues", ScopeDecider(error=error))
    assert (reading.status, reading.reason, reading.source_ids, reading.topic) == ("fallback", reason, [], None)
    (row,) = _ledger(repository)
    assert row["verdict"] == reason


def test_a_tie_reads_nothing(repo):
    vault, repository = repo
    reading = _read(vault, repository, "Axler Strang", ScopeDecider(tie="intent"))
    assert (reading.status, reading.reason) == ("fallback", "tied")


def test_the_days_cap_holds(repo):
    vault, repository = repo
    vault.config.reader_compare.scope_max_calls_per_day = 1
    decider = ScopeDecider(choices={"intent": "compare"})
    assert _read(vault, repository, "compare Axler and Strang", decider).status == "read"
    capped = _read(vault, repository, "compare Axler and Lay", decider)
    assert (capped.status, capped.reason) == ("fallback", "capped") and len(decider.calls) == 1
    assert CS.calls_today(repository) == 1


def test_the_refine_box_reads_books_or_views(repo):
    vault, repository = repo
    books = _read(vault, repository, "add Lay", ScopeDecider(choices={"intent": "books", "change": "add"},
                                                            named=("Linear Algebra and Its Applications",)),
                  mode="refine", current_source_ids=["src_axler", "src_strang"])
    assert (books.intent, books.change, books.source_ids) == ("books", "add", ["src_lay"])
    views = _read(vault, repository, "a geometric view", ScopeDecider(choices={"intent": "views"}), mode="refine",
                  current_source_ids=["src_axler"])
    assert views.intent == "views" and views.source_ids == []
    request = ScopeDecider(choices={"intent": "views"})
    _read(vault, repository, "just the proofs", request, mode="refine", current_source_ids=["src_axler"])
    assert request.calls[0]["state"]["compared_now"] == ["Linear Algebra Done Right"]
    assert "topic" not in request.calls[0]["questions"] and "change" in request.calls[0]["questions"]


def test_the_learners_change_is_a_learner_card_row(repo):
    vault, repository = repo
    reading = _read(vault, repository, "how do Axler and Strang treat eigenvalues",
                    ScopeDecider(choices={"intent": "compare"}, named=("Linear Algebra Done Right",)))
    first = CS.record_correction(repository, reading.judgment_id, source_ids=["src_axler", "src_lay"])
    second = CS.record_correction(repository, reading.judgment_id, source_ids=None)
    rows = _ledger(repository)
    assert [row["judge"] for row in rows] == ["decider", "learner_card", "learner_card"]
    assert rows[1]["supersedes_id"] == reading.judgment_id and rows[2]["supersedes_id"] == first
    assert (rows[1]["verdict"], rows[2]["verdict"]) == ("books_changed", "reworded") and second == rows[2]["id"]
    assert json.loads(rows[1]["rationale"])["chosen_source_ids"] == ["src_axler", "src_lay"]


def test_word_spans_are_the_learners_words_within_the_apis_bound():
    spans = CS.word_spans("how do Axler and Strang treat eigenvalues?")
    assert "eigenvalues" in spans.values() and "Axler and Strang" in spans.values()
    assert all(not value.endswith("?") for value in spans.values())
    long = CS.word_spans(" ".join(f"w{index}" for index in range(80)))
    assert len(long) + 1 <= 255 and "w79" not in long.values()


def test_the_rpc_reads_off_the_request_path_over_the_books_in_scope(tmp_path):
    paths, _repository, _spans = build_library_vault(tmp_path / "vault")
    ctx = context(paths.root)
    decider = ScopeDecider(choices={"intent": "compare", "topic": "determinant"}, named=("Matrix Theory",))
    ctx.compare_scope_client_factory = lambda: decider
    job = call_rpc(ctx, "reader.compare_scope", {"text": "how does Matrix Theory treat the determinant",
                                                 "extractionId": "ext_text"})
    result = finish_job(ctx, job)
    assert result["intent"] == "compare" and result["sourceIds"] == ["src_text"]
    assert result["books"] == [{"sourceId": "src_text", "title": "Matrix Theory"}]
    assert {book["title"] for book in result["library"]} == {"Matrix Theory", "Linear Algebra Notes"}
    # The exam paper is never offered (nor its title sent).
    assert "Midterm" not in json.dumps(decider.calls[0]["questions"], default=str)
    corrected = call_rpc(ctx, "reader.compare_scope_correction", {"judgmentId": result["judgmentId"],
                                                                  "sourceIds": ["src_text", "src_book"]})
    assert corrected["judgmentId"]


def test_one_book_in_scope_reads_nothing(tmp_path):
    paths, _repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "source_service", enabled=True)
    ctx = context(paths.root)
    decider = ScopeDecider(choices={"intent": "compare"})
    ctx.compare_scope_client_factory = lambda: decider
    vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        connection.execute("UPDATE source_artifacts SET reader_enabled = 0 WHERE id = 'src_book'")
        connection.commit()
    result = finish_job(ctx, call_rpc(ctx, "reader.compare_scope", {"text": "compare my books"}))
    assert (result["status"], result["reason"]) == ("fallback", "too_few_books") and decider.calls == []
