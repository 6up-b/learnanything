"""Reader RW5b: figures offered by the library organizer and the Reader tutor (spec §8.7; G46).

* **At no extra call.** The organizer's one listwise call (RW4a) and the
  tutor's one answer (RW1c) carry ``explorable: yes | no`` on a cited equation
  or figure block: the same number of model requests as without offers, a
  prompt version of their own, and outputs without the field read as no.
* **Code decides the block, the judge only the yes.** "Make this explorable"
  appears only on a block code names an equation or a figure AND the judge
  said yes; nothing else carries it.
* **Pressing builds.** ``reader.figure_request`` with ``origin`` ``library``
  | ``tutor`` and the judgment's ``offerRef`` runs RW5a's pipeline (the same
  author, the same verification) and stores that origin; a block the judgment
  did not offer is refused before any call.
* **Switches.** ``figures.offers_enabled`` off: the organizer's and tutor's
  prompts are their own versions byte for byte, no ``explorable`` reaches the
  output, the contract has no ``offers`` and the press is refused. With no
  equation or figure among the passages the request is unchanged too.
* **Admission (FiguresGate).** An offered build stops, sending nothing more,
  when offers or the advanced panels are switched off mid-build.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.ai.execution import model_call
from learnloop.figure_admission import FiguresChanged, FiguresGate, explorable_yes, offerable
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.ids import new_ulid
from learnloop.source_retrieval import library_ask as LA
from learnloop.tutor import ai_contracts as C
from learnloop.tutor import reader_modes
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    counts,
    rows,
    set_config,
)
from tests.figure_panels_corpus import gradient_field

from tests.pf_fakes import prompt_context

NOW = "2026-10-23T10:00:00Z"
#: ext_prob's §5.4: p2 prose, p3 the density's equation, p4 its figure, p5 the caption.
KEYS = [f"{EXTRACTION}:{span}" for span in ("p2", "p3", "p4", "p5")]


class GatedAuthor(AuthorFake):
    """An author that answers inside ``model_call``, as a real provider does, so
    the build's FiguresGate admits (or refuses) each physical request."""

    def complete(self, request):
        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            return super().complete(request)


class ExplorableOrganizer:
    """The library organizer, deterministic: every passage contributes, its own
    line; ``explorable`` yes on every candidate it was told is a block (or on
    ``say_yes`` refs), unless ``old`` (an output without the field)."""

    provider_name = "fake_organizer"
    provider_type = "codex_sdk"
    model = "fake-organizer-model"

    def __init__(self, *, old: bool = False, say_yes: tuple[str, ...] | None = None) -> None:
        self.old = old
        self.say_yes = say_yes
        self.prompts: list[str] = []
        self.models: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import report_call_usage

        self.prompts.append(request.prompt)
        self.models.append(request.result_model.__name__)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80, "resolved_model": self.model})
        context = prompt_context(request.prompt)
        judgments = []
        for candidate in context["candidates"]:
            ref = candidate["ref"]
            fields: dict[str, Any] = {"ref": ref, "verdict": "contributes", "rationale": f"adds {ref}'s own point",
                                      "cites": [ref], "roles": [], "speaks_to": ""}
            if not self.old and "explorable" in request.result_model.model_fields["judgments"].annotation.__args__[0].model_fields:
                yes = ref in self.say_yes if self.say_yes is not None else "block" in candidate
                fields["explorable"] = "yes" if yes else "no"
            judgments.append(fields)
        return request.result_model.model_validate({"judgments": judgments,
                                                    "picks": [c["ref"] for c in context["candidates"]]})


def _vault(tmp_path, *, roles: bool = False, **figures: Any):
    """The figure vault; RW4e's on-demand roles off unless asked (so the organizer
    request is RW4a's base and its explorable twin)."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    set_config(paths, "roles", on_demand_enabled=roles)
    if figures:
        set_config(paths, "figures", **figures)
    return paths, repository


def _ask(repository, keys=KEYS) -> str:
    ask_id = "la_" + new_ulid()
    with repository.connection() as connection:
        LA.ask_store.insert_ask(connection, {
            "id": ask_id, "entry": "reader", "query_md": "what is the two-sided exponential?", "query_hash": ask_id,
            "extraction_id": EXTRACTION, "anchor": {"span_ids": ["p2"], "learning_object_ids": []},
            "personalized": False, "organizer": {"status": "not_run"}, "prompt_version": LA.PROMPT_VERSION,
            "manifest": {"main": {"returned": [key.split(":", 1) for key in keys]}, "expansions": []},
            "created_at": NOW})
        connection.commit()
    return ask_id


def _organize(paths, repository, fake, keys=KEYS):
    vault = load_vault(paths.root)
    return LA.organize(vault, repository, _ask(repository, keys), client=fake)


# --- the rule -------------------------------------------------------------------------------------

def test_code_decides_the_block_and_only_yes_is_a_yes():
    assert offerable("Equation") and offerable("Figure") and offerable("Picture") and offerable("FigureGroup")
    assert not offerable("Text") and not offerable("ListGroup") and not offerable(None)
    assert explorable_yes("yes") and explorable_yes(" YES ")
    assert not any(explorable_yes(value) for value in ("no", "", None, "maybe", True))


# --- the organizer (RW4a) ---------------------------------------------------------------------------

def test_the_organizer_judges_explorable_in_its_one_call_on_equation_and_figure_blocks(tmp_path):
    paths, repository = _vault(tmp_path)
    fake = ExplorableOrganizer()
    result = _organize(paths, repository, fake)
    assert len(fake.prompts) == 1, "no extra call for the judgment"
    assert fake.models == ["OrganizerExplorableResult"]
    assert LA.PROMPT_VERSION + LA.EXPLORABLE_SUFFIX in fake.prompts[0]
    candidates = prompt_context(fake.prompts[0])["candidates"]
    assert [c.get("block") for c in candidates] == [None, "equation", "figure", None]
    notes = {note["key"]: note for note in result["notes"]}
    assert {key: note["explorable"] for key, note in notes.items()} == {
        KEYS[0]: False, KEYS[1]: True, KEYS[2]: True, KEYS[3]: False}
    assert result["prompt_version"] == LA.PROMPT_VERSION + LA.EXPLORABLE_SUFFIX


def test_a_yes_on_a_prose_passage_is_not_an_offer(tmp_path):
    paths, repository = _vault(tmp_path)
    fake = ExplorableOrganizer(say_yes=("p1", "p4"))  # p1 is the prose paragraph, p4 the caption
    result = _organize(paths, repository, fake)
    assert [note["key"] for note in result["notes"] if note.get("explorable")] == []


def test_an_old_output_without_the_field_reads_as_no(tmp_path):
    paths, repository = _vault(tmp_path)
    result = _organize(paths, repository, ExplorableOrganizer(old=True))
    assert all(note["explorable"] is False for note in result["notes"])
    parsed = LA.OrganizerExplorableNote.model_validate({"ref": "p1", "verdict": "related", "rationale": "x",
                                                        "cites": ["p1"], "roles": [], "speaks_to": ""})
    assert parsed.explorable == "no"
    assert LA.OrganizerExplorableNote.model_validate({"ref": "p1", "verdict": "related", "rationale": "x", "cites": [],
                                                      "roles": [], "speaks_to": "", "explorable": "perhaps"}
                                                     ).explorable == "no"


def test_with_no_equation_or_figure_the_request_is_rw4a_byte_for_byte(tmp_path):
    paths, repository = _vault(tmp_path)
    prose = [KEYS[0], KEYS[3]]
    on = ExplorableOrganizer()
    result = _organize(paths, repository, on, keys=prose)
    paths_off, repository_off = _vault(tmp_path / "off", offers_enabled=False)
    off = ExplorableOrganizer()
    result_off = _organize(paths_off, repository_off, off, keys=prose)
    assert on.models == off.models == ["OrganizerResult"]
    assert on.prompts == off.prompts
    assert all("explorable" not in note for note in result["notes"])
    assert [{k: v for k, v in n.items() if k != "ledger_id"} for n in result["notes"]] == [
        {k: v for k, v in n.items() if k != "ledger_id"} for n in result_off["notes"]]


def test_offers_off_the_organizer_is_its_own_version_and_shows_no_explorable(tmp_path):
    paths, repository = _vault(tmp_path, offers_enabled=False)
    fake = ExplorableOrganizer()
    result = _organize(paths, repository, fake)
    assert fake.models == ["OrganizerResult"]
    assert LA.EXPLORABLE_SUFFIX not in fake.prompts[0] and "explorable" not in fake.prompts[0]
    assert "block" not in json.dumps(prompt_context(fake.prompts[0])["candidates"])
    assert all("explorable" not in note for note in result["notes"])
    assert result["prompt_version"] == LA.PROMPT_VERSION


def test_a_stored_answer_with_offers_is_shown_without_them_once_offers_are_off(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    ask_id = _ask(repository)
    first = LA.organize(vault, repository, ask_id, client=ExplorableOrganizer())
    assert any(note["explorable"] for note in first["notes"])
    set_config(paths, "figures", offers_enabled=False)
    again = LA.organize(load_vault(paths.root), repository, ask_id, client=ExplorableOrganizer())
    assert again["reused"] is True
    assert all("explorable" not in note for note in again["notes"])


def test_the_roles_request_composes_with_explorable(tmp_path):
    paths, repository = _vault(tmp_path, roles=True)
    fake = ExplorableOrganizer()
    result = _organize(paths, repository, fake)
    assert fake.models == ["OrganizerRolesExplorableResult"]
    assert LA.ROLES_PROMPT_VERSION + LA.EXPLORABLE_SUFFIX in fake.prompts[0]
    assert "each with a confidence" in fake.prompts[0]
    assert [note["key"] for note in result["notes"] if note.get("explorable")] == KEYS[1:3]


# --- the tutor (RW1c) ---------------------------------------------------------------------------------

def _context(cls=C.ReaderTutorExplorableQAContext):
    return cls(context="reader", question_md="what is it?", candidate_facets=[], thread=[], source_spans=[],
               answer_mode="answer_directly", reader_tutor={"books_cover": True})


def test_the_tutor_prompt_adds_explorable_only_in_its_own_version():
    plain = C.tutor_qa_prompt(_context(C.ReaderTutorQAContext))
    explorable = C.tutor_qa_prompt(_context())
    assert C.READER_TUTOR_PROMPT_VERSION in plain and "explorable" not in plain
    assert C.READER_TUTOR_EXPLORABLE_PROMPT_VERSION in explorable and "`explorable`" in explorable
    assert C.tutor_qa_prompt(_context(), tools=True).count(C.READER_TUTOR_EXPLORABLE_TOOLS_PROMPT_VERSION) == 1
    # The context itself is the same (no new field): only the task and the version differ.
    assert prompt_context(plain) == prompt_context(explorable)
    from learnloop.tutor import tutor_qa as TQ

    assert TQ._answer_model(_context(), tools=False) is C.ReaderTutorExplorableAnswer
    assert TQ._answer_model(_context(), tools=True) is C.ReaderTutorExplorableAnswerWithTools
    assert TQ._answer_model(_context(C.ReaderTutorQAContext), tools=False) is C.ReaderTutorAnswer


class _Request:
    intent = "explain"
    shown_span_keys = ()
    personalized = False
    learner_work = ()


def _answer(explorable, *, model=C.ReaderTutorExplorableAnswer):
    return model.model_validate({"answer_md": "a", "citations": [], "explorable": explorable})


def test_the_tutor_view_keeps_a_yes_only_on_a_block_it_cites():
    spans = [{"extraction_id": EXTRACTION, "span_id": "p3", "relation": "in_view", "text": "x"}]
    cited = [{"extraction_id": EXTRACTION, "span_id": "p3"}]
    answer = _answer([{"extraction_id": EXTRACTION, "span_id": "p3", "explorable": "yes"},
                      {"extraction_id": EXTRACTION, "span_id": "p4", "explorable": "yes"},  # not cited
                      {"extraction_id": EXTRACTION, "span_id": "p2", "explorable": "no"}])
    view, _shown = reader_modes.finalize(answer, spans, cited, retrieval={"books_cover": True}, request=_Request())
    assert view["explorable"] == [{"extraction_id": EXTRACTION, "span_id": "p3"}]
    abstained, _ = reader_modes.finalize(answer, spans, cited, retrieval={"books_cover": False}, request=_Request())
    assert abstained["explorable"] == []
    # An answer model without the field (offers off): the view is RW1c's, key for key.
    plain = C.ReaderTutorAnswer.model_validate({"answer_md": "a", "citations": []})
    rw1c, _ = reader_modes.finalize(plain, spans, cited, retrieval={"books_cover": True}, request=_Request())
    assert "explorable" not in rw1c
    assert _answer([{"extraction_id": "e", "span_id": "s", "explorable": "certainly"}]).explorable[0].explorable == "no"
    assert C.ReaderTutorExplorableAnswer.model_validate({"answer_md": "a"}).explorable == []


def test_the_tutor_buttons_are_make_explorable_on_this_books_equation_and_figure_blocks(tmp_path):
    from learnloop_sidecar.handlers import reader_tutor as handler

    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    result = {"tutor": {"explorable": [{"extraction_id": EXTRACTION, "span_id": span} for span in ("p2", "p3", "p4")]
                        + [{"extraction_id": "ext_other", "span_id": "x1"}]}}
    buttons = handler.offers(vault, repository, result, extraction_id=EXTRACTION)["buttons"]
    assert [(b["kind"], b["span_id"], b["role"]) for b in buttons] == [
        ("make_explorable", "p3", "equation"), ("make_explorable", "p4", "figure")]
    set_config(paths, "figures", offers_enabled=False)
    off = handler.offers(load_vault(paths.root), repository, result, extraction_id=EXTRACTION)
    assert off == {"buttons": []}


def test_the_tutor_context_asks_for_explorable_only_with_a_block_to_judge(tmp_path):
    from learnloop.tutor import tutor_qa as TQ

    paths, repository = _vault(tmp_path)
    request = type("Req", (), {"intent": "explain", "learner_work": []})()

    def built(spans, explorable=True):
        return TQ._reader_lookup_context(
            repository, spans, ([], {"books_cover": True}, request), question_md="q", thread=[], answer_mode=None,
            withheld=None, delivery_receipt=None, budget_tokens=50_000, expanded=False, explorable=explorable)

    prose = [{"extraction_id": EXTRACTION, "span_id": "p2", "relation": "selected_text", "text": "prose"}]
    equation = [{"extraction_id": EXTRACTION, "span_id": "p3", "relation": "selected_text", "text": "f"}]
    assert type(built(prose)) is C.ReaderTutorQAContext
    assert type(built(equation)) is C.ReaderTutorExplorableQAContext
    assert type(built(equation, explorable=False)) is C.ReaderTutorQAContext
    vault = load_vault(paths.root)
    assert TQ.tutor_explorable_enabled(vault) is bool(vault.config.reader_tutor.offers_enabled)
    set_config(paths, "figures", offers_enabled=False)
    assert TQ.tutor_explorable_enabled(load_vault(paths.root)) is False


# --- the press: RW5a's pipeline with the origin -------------------------------------------------------

def _tutor_event(repository, explorable) -> str:
    """A Reader tutor answer as stored (its question event), its view naming
    ``explorable``, and the tutor's verdicts in the ledger as the answer path
    records them (Codex review F3)."""

    from types import SimpleNamespace

    from learnloop.tutor import tutor_qa as TQ

    event_id = repository.insert_question_event({
        "context": "reader", "note_id": f"span:{EXTRACTION}/p2", "question_md": "what is f?", "answer_md": "a",
        "source_context": {"reader_tutor": {"explorable": explorable}}, "created_at": NOW})
    answer = SimpleNamespace(explorable=[C.ExplorableCitation(extraction_id=entry["extraction_id"],
                                                              span_id=entry["span_id"], explorable="yes")
                                         for entry in explorable])
    TQ._record_explorable_verdicts(repository, event_id, answer, model="fake-tutor-model",
                                   prompt_version=C.READER_TUTOR_EXPLORABLE_PROMPT_VERSION, clock=None)
    return event_id


def test_pressing_a_library_offer_builds_through_rw5a_with_origin_library(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    ask_id = _ask(repository)
    LA.organize(vault, repository, ask_id, client=ExplorableOrganizer())
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    result = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library", "offerRef": ask_id})
    assert result["figure"]["origin"] == "library"
    assert result["figure"]["verification"] == "illustrative"
    assert author.calls == 1
    stored = rows(repository, "interactive_figures")
    assert [(row["origin"], json.loads(row["span_ids_json"])) for row in stored] == [("library", ["p3"])]
    # The same passage pressed again is reused (input hash), with no call.
    again = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library", "offerRef": ask_id})
    assert again["reused"] is True and author.calls == 1


def test_pressing_a_tutor_offer_builds_with_origin_tutor(tmp_path):
    paths, repository = _vault(tmp_path)
    event_id = _tutor_event(repository, [{"extraction_id": EXTRACTION, "span_id": "p4"}])
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    result = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p4"], "origin": "tutor", "offerRef": event_id})
    assert result["figure"]["origin"] == "tutor"
    assert author.calls == 1
    # The author was sent the figure block (retrieval supplies it) and RW5a's context around it.
    sent = author.contexts[0]
    assert [span["span_id"] for span in sent["passage"]] == ["p4"]
    assert sent["request"] == "figure"
    assert {span["span_id"] for span in sent["around"]} >= {"p3", "p5"}


@pytest.mark.parametrize("origin, spans, ref", [
    ("library", ["p2"], "ask"),            # judged no (prose)
    ("library", ["p3", "p4"], "ask"),      # one offer is one block
    ("library", ["p3"], "la_missing"),     # no such question
    ("tutor", ["p3"], "event"),            # the tutor offered p4 only
    ("tutor", ["p4"], None),               # no offer named
])
def test_a_block_the_judgment_did_not_offer_is_refused_before_any_call(tmp_path, origin, spans, ref):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    ask_id = _ask(repository)
    LA.organize(vault, repository, ask_id, client=ExplorableOrganizer())
    event_id = _tutor_event(repository, [{"extraction_id": EXTRACTION, "span_id": "p4"}])
    offer_ref = {"ask": ask_id, "event": event_id}.get(ref, ref)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": spans, "origin": origin,
                                            "offerRef": offer_ref})
    assert caught.value.code == "not_offered"
    assert author.calls == 0
    assert counts(repository, ["interactive_figures"]) == {"interactive_figures": 0}


def test_offers_off_the_contract_has_none_and_the_press_is_refused(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    ask_id = _ask(repository)
    LA.organize(vault, repository, ask_id, client=ExplorableOrganizer())
    ctx = context(paths.root, author=AuthorFake())
    assert call(ctx, "reader.prompt_contract", {})["figures"]["offers"] is True
    set_config(paths, "figures", offers_enabled=False)
    author = AuthorFake()
    ctx = context(paths.root, author=author)
    assert call(ctx, "reader.prompt_contract", {})["figures"] == {"predictions": True, "region": True,
                                                                  "revisions": True}
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"], "origin": "library",
                                            "offerRef": ask_id})
    assert caught.value.code == "offers_disabled"
    # The service refuses it too (not only the RPC).
    with pytest.raises(FS.FigureRefused) as refused:
        FS.check_request(load_vault(paths.root), repository, FS.FigureRequest(
            extraction_id=EXTRACTION, span_ids=["p3"], origin="library"))
    assert refused.value.code == "offers_disabled"
    # A selection is unaffected.
    assert build(ctx)["figure"]["origin"] == "selection"
    assert author.calls == 1


# --- admission: one gate, the offer path included -------------------------------------------------------

def test_an_offered_build_stops_when_offers_are_switched_off_before_its_request(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="library")
    author = GatedAuthor()
    # The switch flips between the build's start and its first physical request.
    original = R.FigureRoute.ask

    def flip_then_ask(self, *args, **kwargs):
        set_config(paths, "figures", offers_enabled=False)
        return original(self, *args, **kwargs)

    import unittest.mock as mock

    with mock.patch.object(R.FigureRoute, "ask", flip_then_ask):
        with pytest.raises(FS.FigureRefused) as caught:
            FS.build_figure(vault, repository, request, author_client=author)
    assert caught.value.code == "figures_changed"
    assert author.calls == 0
    assert counts(repository, ["interactive_figures"]) == {"interactive_figures": 0}


def test_a_selection_build_does_not_stop_for_the_offers_switch(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    author = GatedAuthor()
    original = R.FigureRoute.ask

    def flip_then_ask(self, *args, **kwargs):
        set_config(paths, "figures", offers_enabled=False)
        return original(self, *args, **kwargs)

    import unittest.mock as mock

    with mock.patch.object(R.FigureRoute, "ask", flip_then_ask):
        outcome = FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                                  author_client=author)
    assert outcome.view["origin"] == "selection" and author.calls == 1


def test_a_build_stops_when_the_advanced_panels_are_switched_off_mid_build(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    author = GatedAuthor()
    original = R.FigureRoute.ask

    def flip_then_ask(self, *args, **kwargs):
        set_config(paths, "figures", advanced_panels_enabled=False)
        return original(self, *args, **kwargs)

    import unittest.mock as mock

    with mock.patch.object(R.FigureRoute, "ask", flip_then_ask):
        with pytest.raises(FS.FigureRefused) as caught:
            FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                            author_client=author)
    assert caught.value.code == "figures_changed" and author.calls == 0


def test_the_gate_key_of_an_offered_build_includes_the_offers_switch(tmp_path):
    paths, _repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    offered = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="tutor")
    revision = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], origin="tutor", supersedes_id="fig_x")
    assert FS.key_for(offered) is FS.offer_build_key
    assert FS.key_for(revision) is FS.build_key  # a "not right?" version is a revision
    gate = FiguresGate(vault, FS.key_for(offered), live_vault=lambda: vault)
    gate.check()
    set_config(paths, "figures", offers_enabled=False)
    later = load_vault(paths.root)
    gate = FiguresGate(vault, FS.key_for(offered), live_vault=lambda: later)
    with pytest.raises(FiguresChanged):
        gate.check()


# --- the advanced panels switch on the build path --------------------------------------------------------

def test_the_author_prompt_is_rw5a_byte_for_byte_while_the_panels_are_off():
    assert R.author_prompt({"x": 1}) == R.author_prompt({"x": 1}, advanced=False)
    assert R.AUTHOR_PROMPT_VERSION in R.author_prompt({"x": 1})
    assert R.author_instructions() == R.AUTHOR_INSTRUCTIONS
    on = R.author_prompt({"x": 1}, advanced=True)
    assert R.ADVANCED_PROMPT_VERSION in on and "heatmap_2d" in on and "trajectory_2d" in on
    assert "a vector field," not in R.author_instructions(advanced=True)


def test_with_the_panels_on_the_author_is_told_of_them_and_a_field_is_shown(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([gradient_field()])
    ctx = context(paths.root, author=author)
    result = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    assert result["figure"]["verification"] == "illustrative"
    assert R.ADVANCED_PROMPT_VERSION in author.prompts[0]
    assert json.loads(result["figure"]["specJson"])["panels"][0]["kind"] == "vector_field_2d"
    assert rows(repository, "interactive_figures")[0]["prompt_version"] == R.ADVANCED_PROMPT_VERSION


def test_with_the_panels_off_the_author_may_not_emit_them_and_stored_ones_are_cant_draw(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = context(paths.root, author=AuthorFake([gradient_field()]))
    shown = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p2"]})["figure"]
    assert shown["verification"] == "illustrative"
    set_config(paths, "figures", advanced_panels_enabled=False)
    author = AuthorFake([gradient_field(), gradient_field()])
    ctx = context(paths.root, author=author)
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [(f["verification"], f["specJson"]) for f in listed] == [("unsupported", None)]
    assert "switched off" in listed[0]["unsupportedKind"] and listed[0]["label"].startswith("can't draw this yet")
    # A new build is RW5a's prompt, and a field in the answer is refused (two attempts, then failed).
    failed = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p5"]})["figure"]
    assert failed["verification"] == "failed"
    assert author.calls == 2 and all(R.AUTHOR_PROMPT_VERSION in prompt for prompt in author.prompts)
    assert "switched off" in failed["reason"]
    with pytest.raises(SidecarError):
        call(ctx, "reader.figure_predict", {"figureId": shown["figureId"], "predictionIndex": 0, "answer": "same"})


def test_the_reader_report_counts_offered_figures_only_while_offers_are_on(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    paths, repository = _vault(tmp_path)
    event_id = _tutor_event(repository, [{"extraction_id": EXTRACTION, "span_id": "p4"}])
    ctx = context(paths.root, author=AuthorFake())
    build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p4"], "origin": "tutor", "offerRef": event_id})
    build(ctx)  # a selection
    on = build_reader_report(repository.sqlite_path, figures_enabled=True, figure_offers_enabled=True)
    assert on["figures"]["offered"] == {"library": {}, "tutor": {"illustrative": 1}}
    assert on["figures"]["built"] == {"illustrative": 2}
    off = build_reader_report(repository.sqlite_path, figures_enabled=True)
    assert "offered" not in off["figures"]
