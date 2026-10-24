"""RW5b Codex review fixes (docs/reviews/reader-rw5b-codex-review.md).

F2: a figure of a block is reused whatever offered it, and across the
panels switch when it can be drawn now. F4: a figure using a panel kind
that is switched off is not revised. F5: with the panels off, a chain shows
its newest version that can still be drawn. Fakes only: no model is called.
"""

from __future__ import annotations

import json
import re

import pytest

from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.source_retrieval import library_ask as LA
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, call, context, rows, set_config
from tests.figure_panels_corpus import gradient_field
from tests.test_figure_offers import ExplorableOrganizer, _ask, _vault


def _panels(paths, on: bool) -> None:
    """Flip ``figures.advanced_panels_enabled`` (set_config appends, and a
    TOML key may be set only once)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "advanced_panels_enabled = " in text:
        config.write_text(re.sub(r"advanced_panels_enabled = (true|false)",
                                 f"advanced_panels_enabled = {'true' if on else 'false'}", text), encoding="utf-8")
    else:
        set_config(paths, "figures", advanced_panels_enabled=on)


def _offered_library(paths, repository) -> str:
    ask_id = _ask(repository)
    LA.organize(load_vault(paths.root), repository, ask_id, client=ExplorableOrganizer())
    return ask_id


# --- F2: one figure per block, whatever offered it -------------------------------------------------

def test_a_block_built_from_a_selection_is_reused_when_a_library_offer_names_it(tmp_path):
    paths, repository = _vault(tmp_path)
    ask_id = _offered_library(paths, repository)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    first = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    assert first["origin"] == "selection" and author.calls == 1
    again = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library", "offerRef": ask_id})
    assert again["reused"] is True and again["figure"]["figureId"] == first["figureId"]
    assert author.calls == 1
    assert len(rows(repository, "interactive_figures")) == 1
    # Under the passage: one figure, not one per origin.
    assert len(call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]) == 1


def test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys():
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="tutor")
    selection = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="selection")
    source = FS.SourceContext(passage=[{"span_id": "p3", "text": "f"}], around=[], figure_span=None)
    assert FS.request_hash(request, source, None) == FS.request_hash(selection, source, None)
    assert FS.REUSE_ORIGIN == "selection"


def test_a_figure_built_before_the_panels_came_on_is_reused_with_them_on(tmp_path):
    paths, repository = _vault(tmp_path, advanced_panels_enabled=False)
    author = AuthorFake()
    first = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    assert rows(repository, "interactive_figures")[0]["prompt_version"] == R.AUTHOR_PROMPT_VERSION
    _panels(paths, True)
    again = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert again["reused"] is True and again["figure"]["figureId"] == first["figureId"]
    assert author.calls == 1


def test_a_figure_that_cant_be_drawn_now_is_not_reused_across_the_switch(tmp_path):
    paths, repository = _vault(tmp_path)
    build(context(paths.root, author=AuthorFake([gradient_field()])), {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    _panels(paths, False)
    author = AuthorFake()
    again = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    assert again["reused"] is False and author.calls == 1
    assert again["figure"]["specJson"] is not None


def test_another_prompts_cant_draw_verdict_is_not_reused(tmp_path):
    paths, repository = _vault(tmp_path, advanced_panels_enabled=False)
    first = build(context(paths.root, author=AuthorFake([("unsupported", "a vector field")])),
                  {"extractionId": EXTRACTION, "spanIds": ["p2"]})["figure"]
    assert first["verification"] == "unsupported"
    _panels(paths, True)
    author = AuthorFake([gradient_field()])
    again = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    assert author.calls == 1 and again["figure"]["verification"] == "illustrative"


# --- F4: no revision of a figure whose panels are switched off --------------------------------------

def test_a_figure_using_a_switched_off_panel_is_not_revised(tmp_path):
    paths, repository = _vault(tmp_path)
    shown = build(context(paths.root, author=AuthorFake([gradient_field()])),
                  {"extractionId": EXTRACTION, "spanIds": ["p2"]})["figure"]
    _panels(paths, False)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": shown["figureId"], "note": "show the minimum"})
    assert caught.value.code == "advanced_disabled"
    assert author.calls == 0
    assert len(rows(repository, "interactive_figures")) == 1


# --- F5: the newest version that can still be drawn -----------------------------------------------

def test_with_the_panels_off_a_chain_shows_its_newest_drawable_version(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake()  # the flagship function plot (RW5a's kinds) first
    ctx = context(paths.root, author=author)
    first = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    author.answers = [gradient_field()]
    revised = build(ctx, {"figureId": first["figureId"], "note": "as a field"}, rpc="reader.figure_revise")["figure"]
    assert json.loads(revised["specJson"])["panels"][0]["kind"] == "vector_field_2d"
    on = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [figure["figureId"] for figure in on] == [revised["figureId"]]
    _panels(paths, False)
    off = call(context(paths.root, author=AuthorFake()), "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [(figure["figureId"], figure["verification"]) for figure in off] == [(first["figureId"], "illustrative")]
    assert off[0]["specJson"] is not None and off[0]["versions"] == 2


# --- F3: the explorable verdict is in judgment_ledger, and the press reads it there -------------------

def _ledger(repository, task):
    return [row for row in rows(repository, "judgment_ledger") if row["task"] == task]


def test_the_organizers_explorable_verdict_is_in_its_ledger_rows(tmp_path):
    paths, repository = _vault(tmp_path)
    _offered_library(paths, repository)
    recorded = {row["right_id"]: json.loads(row["rationale"]) for row in _ledger(repository, "library_contribution")}
    # Every judged candidate's verdict, as the call returned it (code's block rule applies on top).
    assert {key.split(":", 1)[1]: details["explorable"] for key, details in recorded.items()} == {
        "p2": "no", "p3": "yes", "p4": "yes", "p5": "no"}
    assert all("text" in details and "pick_rank" in details for details in recorded.values())


def test_with_offers_off_the_organizers_ledger_rationale_is_rw4as(tmp_path):
    paths, repository = _vault(tmp_path, offers_enabled=False)
    _offered_library(paths, repository)
    assert all(set(json.loads(row["rationale"])) == {"text", "pick_rank"}
               for row in _ledger(repository, "library_contribution"))


def test_a_library_note_edited_to_offer_without_its_ledger_yes_is_refused(tmp_path):
    paths, repository = _vault(tmp_path)
    ask_id = _ask(repository)
    # The organizer judged every passage explorable: no.
    LA.organize(load_vault(paths.root), repository, ask_id, client=ExplorableOrganizer(say_yes=()))
    organizer = LA.ask_row(repository, ask_id)["organizer"]
    assert not any(note.get("explorable") for note in organizer["notes"])
    # The stored output's JSON says otherwise (it is mutable; the ledger is not).
    organizer["notes"] = [{**note, "explorable": True} for note in organizer["notes"]]
    with repository.connection() as connection:
        connection.execute("UPDATE library_asks SET organizer_json = ? WHERE id = ?", (json.dumps(organizer), ask_id))
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library",
                                            "offerRef": ask_id})
    assert caught.value.code == "not_offered" and author.calls == 0


def test_a_tutor_view_naming_a_block_without_its_ledger_verdict_is_refused(tmp_path):
    paths, repository = _vault(tmp_path)
    event_id = repository.insert_question_event({
        "context": "reader", "note_id": f"span:{EXTRACTION}/p2", "question_md": "what is f?", "answer_md": "a",
        "source_context": {"reader_tutor": {"explorable": [{"extraction_id": EXTRACTION, "span_id": "p4"}]}},
        "created_at": "2026-10-23T10:00:00Z"})
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p4"], "origin": "tutor",
                                            "offerRef": event_id})
    assert caught.value.code == "not_offered" and author.calls == 0


def test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event(tmp_path, monkeypatch):
    """F1 + F3 end to end on the server: reader.ask (a fake tutor judging the
    cited equation explorable) writes the verdict to the ledger and carries the
    button; the press names the answer's question event and builds."""

    import learnloop_sidecar.handlers.reader as reader_handler
    from learnloop.figure_admission import TUTOR_EXPLORABLE_TASK
    from learnloop.tutor import ai_contracts as C
    from tests.reader_tutor_fakes import KeepContaining, LookupTutor, Ready

    class ExplorableTutor(LookupTutor):
        def complete(self, request):
            answer = super().complete(request)
            if "explorable" not in type(answer).model_fields:
                return answer
            return answer.model_copy(update={"explorable": [
                C.ExplorableCitation(extraction_id=EXTRACTION, span_id="p3", explorable="yes")]})

    paths, repository = _vault(tmp_path)
    tutor = ExplorableTutor(answer_md="The density of the two-sided exponential.", cite=lambda _c: [(EXTRACTION, "p3")])
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    ctx.reader_tutor_rerank_client = KeepContaining("density")
    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    answer = call(ctx, "reader.ask", {"extractionId": EXTRACTION, "spanId": "p3", "question": "what is this density?",
                                      "selectionSpanIds": ["p3"], "selectionQuote": "f_X(x)"})
    assert tutor.result_models[-1].startswith("ReaderTutorExplorableAnswer")
    buttons = [(b["kind"], b["spanId"]) for b in (answer.get("tutorOffers") or {}).get("buttons") or []]
    assert ("make_explorable", "p3") in buttons
    verdicts = _ledger(repository, TUTOR_EXPLORABLE_TASK)
    assert [(row["left_id"], row["right_id"], row["verdict"]) for row in verdicts] == [
        (answer["eventId"], f"{EXTRACTION}:p3", "yes")]
    # The interaction event is not the judgment (F1): refused before any call.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "tutor",
                                            "offerRef": answer["readerAnswerEventId"]})
    assert caught.value.code == "not_offered" and author.calls == 0
    built = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "tutor", "offerRef": answer["eventId"]})
    assert built["figure"]["origin"] == "tutor" and author.calls == 1
    # The answer's own response carried the judgment; its history never does
    # (the review's §1.5 claim: history is RW1c's, offers on or off).
    assert answer["tutor"]["explorable"] == [{"extractionId": EXTRACTION, "spanId": "p3"}]
    history = call(ctx, "reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]
    assert history and all("explorable" not in (exchange.get("tutor") or {}) for exchange in history)
    assert history[0]["tutor"]["modes"]


# --- F7: the tutor is told which delivered passages are equations or figures -------------------------

def test_the_tutor_context_marks_each_equation_and_figure_block(tmp_path):
    from learnloop.tutor import ai_contracts as C
    from learnloop.tutor import tutor_qa as TQ

    paths, repository = _vault(tmp_path)
    request = type("Req", (), {"intent": "explain", "learner_work": []})()
    spans = [{"extraction_id": EXTRACTION, "span_id": span, "relation": "selected_text", "text": text}
             for span, text in (("p2", "prose"), ("p3", "f"), ("p4", "Figure 5.2: the density"))]
    built = TQ._reader_lookup_context(
        repository, spans, ([], {"books_cover": True}, request), question_md="q", thread=[], answer_mode=None,
        withheld=None, delivery_receipt=None, budget_tokens=50_000, expanded=False, explorable=True)
    assert type(built) is C.ReaderTutorExplorableQAContext
    assert {span["span_id"]: span.get("block") for span in built.source_spans} == {
        "p2": None, "p3": "equation", "p4": "figure"}
    prompt = C.tutor_qa_prompt(built)
    assert '"block": "figure"' in prompt and "carries `block`" in prompt
    # Off (or with nothing to judge) nothing is marked: RW1c's context.
    off = TQ._reader_lookup_context(
        repository, spans, ([], {"books_cover": True}, request), question_md="q", thread=[], answer_mode=None,
        withheld=None, delivery_receipt=None, budget_tokens=50_000, expanded=False, explorable=False)
    assert type(off) is C.ReaderTutorQAContext and all("block" not in span for span in off.source_spans)
