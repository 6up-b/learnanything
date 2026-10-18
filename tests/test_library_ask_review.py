"""RW4a Codex review (stage reader-rw4a): the findings' regressions, fakes only.

* F1: a library question about held-out material (a held-out selection, or a
  reading held back whole) is refused before any retrieval, rewrite,
  embedding, row or model call, from Ctrl+Shift+F's ask and the RPC alike.
* F2: every passage a comparison shows is recorded as exposure, a
  counterpart the ask never showed included, on every display (reused too).
* F3: the pinned tutor's answer is finalized as a Reader answer: a reserved
  surface it reproduces is burned, the exchange is in the Reader's inquiry
  history, and its learner-text gap reading is queued.
* F4: follow-ups keep the ask's caller: compare without a session is still
  the item's practice; a different session is refused; the tutor grounds the
  pins under the item's filters and refuses during a cold administration.
* F5: the organizer's daily cap is a durable, atomic reservation (two
  requests in flight cannot both pass it), and a subscription route is never
  refused by the metered cap.
* F6: the notes, compare, the tutor and the ask itself run off the request
  path: a blocked model never holds up the next Reader RPC; a cancelled job
  never answers.
* F7: the pinned tutor's passages are held to tutor_qa.context_token_budget,
  the receipt records it, and the label counts what was delivered.
* F9: a comparison whose counterparts could not be verified carries the
  unchecked sources and why, so the Reader never calls it "one source".
* F8: a crash between the organizer's ledger commit and its notes leaves
  them recoverable from the paid call's checkpoint, validated again.
"""
from __future__ import annotations

from datetime import UTC, datetime
import json
import threading

import pytest

from learnloop.content.sources.exam_material import Material
from learnloop.source_retrieval import library_ask as LA
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import (
    OrganizerFake,
    ask_rows,
    build_library_vault,
    call,
    call_rpc,
    context,
    finish_job,
    set_config,
    tutor_with_citations,
)

QUESTION = "eigenvalues characteristic polynomial determinant"
NOW = "2026-10-17T10:00:00Z"


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    return paths, repository, spans


def _ask(ctx, **extra):
    params = {"query": QUESTION, "entry": "reader", "extractionId": "ext_text", "spanIds": ["t2"],
              "learningObjectIds": ["lo_matrices"], **extra}
    return call(ctx, "reader.library_ask", params)


def _ready_tutor(monkeypatch, tutor):
    import learnloop_sidecar.handlers.ai_providers as providers

    class Ready:
        ready = True

    monkeypatch.setattr(providers, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))


def _bound_session(repository, item_id: str = "pi_eigen_1", session_id: str = "wbs_1") -> str:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "extraction_id, span_ids_json, source_visible, created_at, updated_at) "
            "VALUES (?, ?, 'Solve it', 'bound', 'reader', 'work_through', 'ext_text', '[\"t6\"]', 1, ?, ?)",
            (session_id, item_id, NOW, NOW))
        connection.commit()
    return session_id


def _exposures(repository, span_key: str) -> int:
    extraction_id, span_id = span_key.split(":", 1)
    with repository.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM source_exposure_events WHERE extraction_id = ? AND span_id = ? "
            "AND entity_type = 'library_ask'", (extraction_id, span_id)).fetchone()[0]


# -- F1: held-out material never reaches retrieval or a model ---------------------------------------


@pytest.mark.parametrize("material", [
    Material(spans=frozenset({("ext_text", "t2")})),
    Material(extractions=frozenset({"ext_text"})),
], ids=["held_out_selection", "reading_held_back"])
def test_a_held_out_selection_is_refused_before_any_retrieval(library, monkeypatch, material):
    paths, repository, _spans = library
    import learnloop.instructional.sources as service

    finds: list[str] = []
    real = service.propose_sources
    monkeypatch.setattr(service, "propose_sources", lambda *a, **k: finds.append(a[2]) or real(*a, **k))
    import learnloop.content.sources.exam_material as exam_material

    monkeypatch.setattr(exam_material, "held_out_material", lambda *_a, **_k: material)
    ctx = context(paths.root)
    # Ctrl+Shift+F prefills the selection's own words and sends its spans.
    with pytest.raises(SidecarError) as caught:
        _ask(ctx, query="the held-out exercise's own words", entry="reader")
    assert caught.value.code == "exam_material"
    assert finds == [] and ask_rows(repository) == []
    # The library search (no reading anchor) still asks.
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "entry": "library_search"})
    assert asked["askId"] and finds == [QUESTION]


# -- F2: every passage a comparison shows is an exposure -----------------------------------------


def test_a_comparison_records_exposure_for_every_passage_it_shows(library, monkeypatch):
    from learnloop.source_retrieval.compare import Comparison
    import learnloop.instructional.sources as service

    paths, repository, _spans = library
    ctx = context(paths.root)
    asked = _ask(ctx)
    shown = {hit["key"] for hit in asked["hits"]}
    # A passage the comparison found that the ask never showed.
    counterpart = next(key for key in (f"ext_book:s{index}" for index in range(1, 20)) if key not in shown)
    counterpart_span = counterpart.split(":", 1)[1]
    sources = [
        {"ref": "s1", "source_id": "src_text", "source_title": "Text", "extraction_id": "ext_text", "span_id": "t2",
         "page": 1, "contributions": [{"contribution": "a definition", "quote": "the characteristic polynomial"}]},
        {"ref": "s2", "source_id": "src_book", "source_title": "Book", "extraction_id": "ext_book",
         "span_id": counterpart_span,
         "page": 2, "contributions": [{"contribution": "an inner product view", "quote": "an inner product"}]},
    ]
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: Comparison(
        status="ok", policy="reading", comparison_id=None, sources=sources, reused=True))
    before = _exposures(repository, counterpart)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"],
                                                 "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert [row["key"] for row in table["rows"]] == ["ext_text:t2", counterpart]
    assert _exposures(repository, counterpart) == before + 1
    assert len(table["exposureEventIds"]) == 2
    # Shown again (a reused comparison): recorded again.
    call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert _exposures(repository, counterpart) == before + 2


# -- F9: a verification failure travels with the table ---------------------------------------------


def test_the_table_carries_unchecked_sources_and_why(library, monkeypatch):
    from learnloop.source_retrieval.compare import Comparison
    import learnloop.instructional.sources as service

    paths, _repository, _spans = library
    ctx = context(paths.root)
    asked = _ask(ctx)
    unverified = [{"source_id": "src_text", "source_title": "Text", "extraction_id": "ext_text", "span_id": "t2",
                   "label": "possible match, not checked"},
                  {"source_id": "src_book", "source_title": "Book", "extraction_id": "ext_book", "span_id": "s2",
                   "label": "possible match, not checked"}]
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: Comparison(
        status="too_few_sources", policy="reading", unverified_sources=unverified,
        manifest={"verification": {"status": "over_budget", "verified_sources": 0, "sources_with_hits": 2},
                  "verification_stopped": "over_budget: source_service.max_daily_cost_usd"}))
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"],
                                                 "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert table["status"] == "too_few_sources" and table["rows"] == []
    assert [entry["sourceTitle"] for entry in table["unverifiedSources"]] == ["Text", "Book"]
    assert table["verification"] == {"status": "over_budget", "verifiedSources": 0,
                                     "stopped": "over_budget: source_service.max_daily_cost_usd"}


# -- F3: the pinned tutor is finalized as a Reader answer ----------------------------------------


def test_the_pinned_tutor_burns_a_reserve_it_reproduces_and_joins_history_and_gaps(library, monkeypatch):
    from learnloop.clock import FrozenClock
    from learnloop.db.stores import learner_gaps as gap_store
    from learnloop.reader import reader_dialogue as RD
    from learnloop.substrate.activities import evaluate_held_out_eligibility, reserve_surface, resolve_legacy_item
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

    paths, repository, _spans = library
    vault = load_vault(paths.root)
    clock = FrozenClock(datetime(2026, 10, 17, 10, tzinfo=UTC))
    resolved = resolve_legacy_item(vault, repository, vault.practice_items["pi_eigen_1"], purpose="assessment",
                                   clock=clock)
    reserve_surface(repository, surface_id=resolved.surface_id, purpose="assessment", clock=clock)
    statement = RD.surface_statement_text(repository.fetch_surface(resolved.surface_id))
    assert statement
    ctx = context(paths.root)
    ctx.post_attempt_worker = PostAttemptWorker(autostart=False)
    asked = _ask(ctx)
    _ready_tutor(monkeypatch, tutor_with_citations([("ext_text", "t2")],
                                                   answer_md=f"Your passages say: {statement}"))
    answer = call(ctx, "reader.library_ask_tutor", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2"]})
    # The reserved surface the answer reproduced is burned, as any Reader answer's is.
    assert resolved.surface_id in answer["burnedSurfaceIds"]
    assert evaluate_held_out_eligibility(repository, surface=repository.fetch_surface(resolved.surface_id),
                                         purpose="assessment").is_unseen is False
    # The exchange is in the Reader's inquiry history (closing the pane keeps it).
    history = RD.ask_history(repository, extraction_id="ext_text")
    assert [exchange["question_event_id"] for exchange in history] == [answer["eventId"]]
    assert history[0]["event_id"] == answer["readerAnswerEventId"]
    # Its learner-text gap reading is queued, as for any Reader question.
    assert answer["learnerGap"]["status"] == "queued"
    with repository.connection() as connection:
        job = gap_store.job_for_source(connection, "tutor_question", answer["eventId"])
    assert job is not None and job["state"] == "queued"


# -- F4: follow-ups keep the ask's caller ---------------------------------------------------------


def test_a_compare_without_its_session_stays_the_items_practice(library, monkeypatch):
    from learnloop.source_retrieval.compare import Comparison
    import learnloop.instructional.sources as service

    paths, repository, _spans = library
    session = _bound_session(repository)
    ctx = context(paths.root)
    asked = _ask(ctx, workbenchSessionId=session)
    assert asked["policy"] == "assisted_practice"
    callers = []
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: callers.append(k["caller"]) or Comparison(
        status="too_few_sources", policy="assisted_practice"))
    call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert callers[0].item_id == "pi_eigen_1" and callers[0].context == "practice"
    # A follow-up naming another binding is refused, never widened.
    other = _bound_session(repository, item_id="pi_eigen_1", session_id="wbs_2")
    plain = _ask(ctx)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"askId": plain["askId"], "workbenchSessionId": other,
                                             "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert caught.value.code == "caller_mismatch" and len(callers) == 1


def test_the_tutor_grounds_a_bound_asks_pins_under_the_items_filters(library, monkeypatch):
    paths, repository, spans = library
    session = _bound_session(repository)
    ctx = context(paths.root)
    asked = _ask(ctx, workbenchSessionId=session)
    solution = f"ext_text:{spans['solutions'][0]}"
    tutor = tutor_with_citations([])
    _ready_tutor(monkeypatch, tutor)
    answer = call(ctx, "reader.library_ask_tutor", {"askId": asked["askId"],
                                                    "pinnedSpanKeys": ["ext_text:t2", solution]})
    assert answer["groundedKeys"] == ["ext_text:t2"]
    assert [f"{pin['extractionId']}:{pin['spanId']}" for pin in answer["droppedPins"]] == [solution]
    prompt = tutor.prompts[0]
    delivered = json.loads(prompt[prompt.index("{"):])["context"]["source_spans"]
    assert {(span["extraction_id"], span["span_id"]) for span in delivered} == {("ext_text", "t2")}


def test_the_tutor_refuses_a_bound_ask_while_its_cold_administration_is_open(library, monkeypatch):
    import learnloop.instructional.policy as policy

    paths, repository, _spans = library
    session = _bound_session(repository)
    ctx = context(paths.root)
    asked = _ask(ctx, workbenchSessionId=session)
    tutor = tutor_with_citations([])
    _ready_tutor(monkeypatch, tutor)
    # The cold administration opened after the ask: the follow-up reads today's status.
    monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == "pi_eigen_1")
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_ask_tutor", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2"]})
    assert caught.value.code == "cold_attempt" and tutor.prompts == []
    with pytest.raises(SidecarError) as compared:
        call(ctx, "reader.library_compare", {"askId": asked["askId"],
                                             "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert compared.value.code == "cold_attempt"


# -- F5: the organizer's cap is atomic; a subscription route is never refused by it ----------------


def test_a_subscription_organizer_is_not_refused_by_the_metered_cap(library):
    paths, _repository, _spans = library
    set_config(paths, "library_ask", max_daily_cost_usd=0.0)
    ctx = context(paths.root)
    asked = _ask(ctx)
    ctx.library_organizer_client = fake = OrganizerFake()  # codex_sdk: the ChatGPT subscription
    notes = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert notes["status"] == "judged" and len(fake.prompts) == 1


def test_two_organizer_requests_in_flight_cannot_both_pass_the_cap(library, monkeypatch):
    paths, repository, _spans = library
    set_config(paths, "source_retrieval", llm_price_per_million=2.0)
    estimates: list[float] = []
    real = LA._OrganizerAdmission.__call__

    def recording(self, estimate):
        estimates.append(float(estimate.estimated_usd))
        return real(self, estimate)

    monkeypatch.setattr(LA._OrganizerAdmission, "__call__", recording)
    # One request's estimate, measured on a probe ask with room to spare.
    probe_ctx = context(paths.root)
    probe = _ask(probe_ctx, query="eigenvalues determinant polynomial probe")
    probe_ctx.library_organizer_client = OrganizerFake(provider_type="openai_chat")
    assert call(probe_ctx, "reader.library_ask_notes", {"askId": probe["askId"]})["status"] == "judged"
    one = estimates[-1]
    spent = LA.organizer_spent_today(LA_vault(paths), repository)
    # Room for one more request, not two.
    set_config(paths, "library_ask", max_daily_cost_usd=round(spent + one * 1.5, 6))
    ctx = context(paths.root)
    first, second = _ask(ctx, query="eigenvalues characteristic first"), _ask(ctx, query="determinant sign second")
    gate = threading.Event()
    slow = OrganizerFake(provider_type="openai_chat", gate=gate)
    ctx.library_organizer_client = slow
    pending = call_rpc(ctx, "reader.library_ask_notes", {"askId": first["askId"]})
    assert slow.started.wait(30)  # the first request is admitted and in flight
    ctx.library_organizer_client = fast = OrganizerFake(provider_type="openai_chat")
    refused = call(ctx, "reader.library_ask_notes", {"askId": second["askId"]})
    assert refused["status"] == "capped" and "library_ask.max_daily_cost_usd" in refused["reason"]
    assert fast.prompts == []
    gate.set()
    assert finish_job(ctx, pending)["status"] == "judged"


def LA_vault(paths):
    from learnloop.vault.loader import load_vault

    return load_vault(paths.root)


# -- F6: off the request path, and cancellable ----------------------------------------------------


def test_a_blocked_organizer_never_holds_up_the_next_reader_rpc(library):
    paths, repository, _spans = library
    ctx = context(paths.root)
    asked = _ask(ctx)
    gate = threading.Event()
    ctx.library_organizer_client = slow = OrganizerFake(gate=gate)
    job = call_rpc(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert job["state"] == "pending" and slow.started.wait(30)
    # The serial loop answers the Reader's next requests while the model works.
    contract = call_rpc(ctx, "reader.prompt_contract", {})
    assert "libraryAsk" in contract
    view = call_rpc(ctx, "get_span_view", {"extractionId": "ext_text", "spanId": "t2", "context": "library"})
    assert view["spanView"]["spanId"] == "t2"
    assert call_rpc(ctx, "reader.library_job", {"jobId": job["jobId"]})["state"] == "pending"
    # Closing the pane cancels it: the job never answers, even once the model is done.
    cancelled = call_rpc(ctx, "reader.library_job_cancel", {"jobId": job["jobId"]})
    assert cancelled["state"] == "cancelled"
    gate.set()
    jobs = ctx.library_ask_jobs
    assert jobs.get(job["jobId"]).done.wait(30)
    assert call_rpc(ctx, "reader.library_job", {"jobId": job["jobId"], "waitMs": 10})["state"] == "cancelled"
    # The paid output is kept: asking again reuses it, with no second call.
    assert json.loads(ask_rows(repository)[0]["organizer_json"])["status"] == "judged"
    again = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    assert again["reused"] is True and len(slow.prompts) == 1


def test_every_model_backed_rpc_answers_with_a_job(library, monkeypatch):
    paths, _repository, _spans = library
    ctx = context(paths.root)
    started = call_rpc(ctx, "reader.library_ask", {"query": QUESTION, "entry": "library_search"})
    assert set(started) >= {"jobId", "state", "kind"} and started["kind"] == "ask"
    asked = finish_job(ctx, started)
    ctx.library_organizer_client = OrganizerFake()
    _ready_tutor(monkeypatch, tutor_with_citations([]))
    for name, params in (("reader.library_ask_notes", {"askId": asked["askId"]}),
                         ("reader.library_ask_tutor", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2"]})):
        job = call_rpc(ctx, name, params)
        assert job["state"] in ("pending", "done") and job["askId"] == asked["askId"]
        finish_job(ctx, job)
    with pytest.raises(SidecarError) as caught:
        call_rpc(ctx, "reader.library_job", {"jobId": "ljob_unknown"})
    assert caught.value.code == "not_found"


# -- F7: the pinned tutor is held to the context budget -------------------------------------------


def test_pinned_passages_are_held_to_the_tutors_context_budget(library):
    from learnloop.reader import reader_dialogue as RD
    from learnloop.vault.loader import load_vault

    paths, repository, _spans = library
    set_config(paths, "tutor_qa", context_token_budget=1000)
    vault = load_vault(paths.root)
    ctx = context(paths.root)
    asked = _ask(ctx)
    long_text = "word " * 10_000  # 50,000 characters

    def provider(_vault, _repository, **_kwargs):
        spans = [{"extraction_id": "ext_text", "span_id": "t2", "text": long_text, "relation": "pinned"},
                 {"extraction_id": "ext_book", "span_id": "s2", "text": "a short second pin", "relation": "pinned"}]
        return spans, {"basis": "pinned", "policy": "reading", "spans": 2,
                       "span_keys": ["ext_text:t2", "ext_book:s2"], "dropped_pins": []}

    tutor = tutor_with_citations([("ext_text", "t2"), ("ext_book", "s2")])

    def answer(*, question_md, extraction_id, span_id):
        return RD.ask(vault, repository, tutor, extraction_id=extraction_id, span_id=span_id,
                      question_md=question_md, source_span_provider=provider)

    result = LA.ask_tutor(vault, repository, asked["askId"], pinned_keys=["ext_text:t2", "ext_book:s2"],
                          question_md=None, ask=answer)
    prompt = tutor.prompts[0]
    delivered = json.loads(prompt[prompt.index("{"):])["context"]["source_spans"]
    assert len(delivered) == 1 and len(delivered[0]["text"]) <= 1000 * 4
    assert delivered[0]["trimmed"]["total_chars"] == len(long_text)
    event = repository.question_event(result["event_id"])
    delivery = event["source_context"]["delivery"]
    assert delivery["budget_tokens"] == 1000 and delivery["trimmed"][0]["span_id"] == "t2"
    assert [entry["span_id"] for entry in delivery["dropped"]] == ["s2"]
    # The label and the citation allowlist are the delivered passages.
    assert result["grounded_keys"] == ["ext_text:t2"] and result["trimmed_keys"] == ["ext_text:t2"]
    assert result["label"] == "answers only from this passage"
    assert [c["span_id"] for c in result["citations"]] == ["t2"]
    assert any(pin["span_id"] == "s2" for pin in result["dropped_pins"])


# -- F8: a crash between the ledger and the notes is recoverable ----------------------------------


def test_a_crash_after_the_ledger_commit_keeps_the_notes_recoverable(library, monkeypatch):
    paths, repository, _spans = library
    vault = LA_vault(paths)
    ctx = context(paths.root)
    asked = _ask(ctx)
    fake = OrganizerFake(wrong_cite=("p2",))
    real_update = LA._update

    def crash(repo, ask_id, **columns):
        if "organizer_json" in columns:
            raise RuntimeError("the process died here")
        return real_update(repo, ask_id, **columns)

    monkeypatch.setattr(LA, "_update", crash)
    with pytest.raises(RuntimeError):
        LA.organize(vault, repository, asked["askId"], client=fake)
    monkeypatch.setattr(LA, "_update", real_update)
    assert json.loads(ask_rows(repository)[0]["organizer_json"])["status"] == "not_run"
    notes = LA.organize(vault, repository, asked["askId"], client=fake)
    assert notes["status"] == "cached" and len(fake.prompts) == 1  # nothing paid again
    by_key = {note["key"]: note for note in notes["notes"]}
    assert by_key[asked["hits"][0]["key"]]["line"] == "adds the passage p1's own point"
    # Validated again: the line citing another passage is still dropped.
    assert by_key[asked["hits"][1]["key"]]["line"] is None
    assert notes["unchecked_lines"] == 0 and not any(note.get("unchecked") for note in notes["notes"])


def test_with_no_paid_answer_left_a_cached_line_stays_out_and_is_retried(library, monkeypatch):
    paths, repository, _spans = library
    vault = LA_vault(paths)
    ctx = context(paths.root)
    asked = _ask(ctx)
    fake = OrganizerFake()
    real_update = LA._update
    monkeypatch.setattr(LA, "_update", lambda repo, ask_id, **columns: (_ for _ in ()).throw(RuntimeError("died"))
                        if "organizer_json" in columns else real_update(repo, ask_id, **columns))
    with pytest.raises(RuntimeError):
        LA.organize(vault, repository, asked["askId"], client=fake)
    monkeypatch.setattr(LA, "_update", real_update)
    monkeypatch.setattr(LA, "_recovered_answer", lambda *_a, **_k: None)
    notes = LA.organize(vault, repository, asked["askId"], client=fake)
    assert notes["status"] == "cached" and all(note["line"] is None for note in notes["notes"])
    assert notes["unchecked_lines"] == len(notes["notes"])
    # Not reused as final: a later request tries to recover again.
    monkeypatch.undo()
    again = LA.organize(vault, repository, asked["askId"], client=fake)
    assert again["reused"] is False and again["unchecked_lines"] == 0
