"""RW1c: offers, not actions, under a Reader tutor answer (spec_reader_workbench_v1 §4.6; G48, G59).

* The answer carries the sources spec's requests (S0's practice request, or
  the tutor's own ``tool_requests``) and the Reader's own button, "Try the
  next step first", on a cited derivation or worked example of the open
  source (only while RW1b's active reading is on; "Make this explorable"
  waits for RW5b, which is not on main).
* **Fetch early, show on press (D44, G59).** The lookups the Reader starts
  when the answer lands (``find_practice``, ``run_source_tool`` for a
  passage request) leave their proposal or run row and nothing else: no
  impression, no exposure, no intervention. The impression
  (``record_proposal_impressions``, surface ``reader``) and the exposure
  (``record_source_offer_shown``) are written on the press. A comparison
  makes no call until pressed. A lookup that found nothing returns nothing
  to show; a failed one leaves a failed run and runs again on the press.
* The tutor never serves, schedules or imports: an answer with every offer
  writes no learning state. A press is a salience-only Reader event.
* ``reader_tutor.offers_enabled`` off: no buttons on the wire; both RW1c
  switches off: no ``readerTutor`` in the prompt contract.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.reader import reader_inquiry as RI
from learnloop.reader.reader_report import build_reader_report
from learnloop_sidecar.errors import SidecarError
from tests.reader_tutor_fakes import LookupTutor, ask, call, reader_ctx
from tests.source_service_fakes import learning_state_tables, table_counts

REQUESTS = [
    {"tool": "find_practice", "query": "swap two rows determinant", "intent": "practice",
     "reason": "Practise the sign rule", "facet_ids": [], "learning_object_ids": []},
    {"tool": "find_sources", "query": "determinant changes sign rows swapped", "intent": "explain",
     "reason": "Your other book says it differently", "facet_ids": []},
    {"tool": "compare_sources", "query": "determinant sign when rows are swapped",
     "reason": "How do your books treat this?", "facet_ids": []},
]
WATCHED = ["practice_index_proposals", "instructional_impressions", "source_exposure_events",
           "retrieval_interventions", "source_comparisons", "source_tool_calls"]


def _worked_example_citation(context):
    return [("ext_text", "t5"), ("ext_text", "t3")]


def _offer_ctx(tmp_path, monkeypatch, *, requests=REQUESTS, config=None, cite=_worked_example_citation):
    import learnloop.instructional.tools as tools

    tutor = LookupTutor(tool_requests=requests, cite=cite)
    paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor, config=config)
    # The tool runs' own model roles, faked (the RPC resolves them from routes).
    verifier = ctx.reader_tutor_rerank_client
    real = tools.run_requested_tool
    monkeypatch.setattr(tools, "run_requested_tool", lambda vault, repo, request_id, **kw: real(
        vault, repo, request_id, **{**kw, "clients": {"source_rerank": verifier, "source_compare": verifier,
                                                      "practice_rerank": verifier}}))
    return tutor, ctx, repository


def _by_tool(answer, tool):
    return [request for request in answer.get("toolRequests") or [] if request["tool"] == tool]


def test_the_answer_carries_the_requests_and_the_readers_own_button(tmp_path, monkeypatch):
    _tutor, ctx, _repository = _offer_ctx(tmp_path, monkeypatch)
    answer = ask(ctx)
    assert {request["tool"] for request in answer["toolRequests"]} == {"find_practice", "find_sources",
                                                                       "compare_sources"}
    assert all(request["toolCallId"] and request["reason"] for request in answer["toolRequests"])
    # The tutor's own find_practice request replaces S0's deterministic one.
    assert "practiceRequest" not in answer
    # "Try the next step first" on the cited worked example (t5) of the open source, not on prose (t3).
    assert answer["tutorOffers"]["buttons"] == [{"kind": "try_next_step", "extractionId": "ext_text", "spanId": "t5",
                                                 "label": "try the next step first", "role": "worked_example"}]


def test_without_tool_requests_the_answer_carries_the_practice_request(tmp_path, monkeypatch):
    _tutor, ctx, _repository = _offer_ctx(tmp_path, monkeypatch, requests=[])
    answer = ask(ctx)
    assert "toolRequests" not in answer
    assert answer["practiceRequest"]["caller"] == {"kind": "tutor", "ref": answer["eventId"]}


def test_eager_lookups_leave_their_rows_and_nothing_shown(tmp_path, monkeypatch):
    _tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch)
    answer = ask(ctx)
    before = table_counts(repository, WATCHED)
    # What the Reader starts when the answer lands: the practice lookup and the passage lookup.
    for request in _by_tool(answer, "find_practice") + _by_tool(answer, "find_sources"):
        call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    after = table_counts(repository, WATCHED)
    assert after["source_tool_calls"] == before["source_tool_calls"] + 2  # one run row each
    assert after["practice_index_proposals"] == before["practice_index_proposals"] + 1
    for table in ("instructional_impressions", "source_exposure_events", "retrieval_interventions",
                  "source_comparisons"):
        assert after[table] == before[table], table


def test_s0s_practice_lookup_is_a_proposal_and_nothing_else(tmp_path, monkeypatch):
    _tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch, requests=[])
    answer = ask(ctx)
    before = table_counts(repository, WATCHED)
    offer = answer["practiceRequest"]
    result = call(ctx, "find_practice", {**offer["request"], "caller": offer["caller"]})
    after = table_counts(repository, WATCHED)
    assert result["proposalId"] and after["practice_index_proposals"] == before["practice_index_proposals"] + 1
    assert after["instructional_impressions"] == before["instructional_impressions"]


def test_impressions_and_exposures_are_written_on_the_press(tmp_path, monkeypatch):
    _tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch)
    answer = ask(ctx)
    (practice,) = _by_tool(answer, "find_practice")
    (passages,) = _by_tool(answer, "find_sources")
    ran = call(ctx, "run_source_tool", {"toolCallId": practice["toolCallId"]})
    shown = call(ctx, "run_source_tool", {"toolCallId": passages["toolCallId"]})
    before = table_counts(repository, WATCHED)
    # The learner presses "Practice this": the proposals rendered are the impression.
    items = ran["result"]["items"]
    assert items, "the fake practice index proposes something"
    recorded = call(ctx, "record_proposal_impressions", {
        "proposalId": ran["result"]["proposalId"], "surface": "reader",
        "keys": [{"kind": "item", "practiceItemId": item["practiceItemId"]} for item in items]})
    assert recorded["recorded"] == len(items)
    # ... and "From your books": the passages it shows are exposures.
    keys = [passage["spanKey"] for passage in shown["result"]["passages"]]
    assert keys
    offer = call(ctx, "record_source_offer_shown", {"toolCallId": passages["toolCallId"], "spanKeys": keys})
    after = table_counts(repository, WATCHED)
    assert after["instructional_impressions"] == before["instructional_impressions"] + len(items)
    assert after["source_exposure_events"] == before["source_exposure_events"] + len(keys)
    assert len(offer["exposureEventIds"]) == len(keys)
    with repository.connection() as connection:
        surfaces = {row[0] for row in connection.execute("SELECT surface FROM instructional_impressions")}
    assert surfaces == {"reader"}


def test_a_comparison_makes_no_call_until_pressed(tmp_path, monkeypatch):
    tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch)
    verifier = ctx.reader_tutor_rerank_client
    answer = ask(ctx)
    for request in _by_tool(answer, "find_practice") + _by_tool(answer, "find_sources"):
        call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 0}
    assert all(name != "SourceComparison" for _purpose, name in verifier.calls)
    (compare,) = _by_tool(answer, "compare_sources")
    assert compare["run"] == "lazy"
    pressed = call(ctx, "run_source_tool", {"toolCallId": compare["toolCallId"]})
    assert pressed["toolCallId"] == compare["toolCallId"]
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 1}
    assert any(name == "SourceComparison" for _purpose, name in verifier.calls)


def test_an_empty_lookup_shows_nothing_and_a_failed_one_runs_again(tmp_path, monkeypatch):
    requests = [{"tool": "find_sources", "query": "zzqx quux wibble", "intent": "explain",
                 "reason": "Nothing will match", "facet_ids": []},
                {"tool": "find_sources", "query": "determinant changes sign rows swapped", "intent": "explain",
                 "reason": "This one fails once", "facet_ids": []}]
    _tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch, requests=requests)
    answer = ask(ctx)
    empty, flaky = answer["toolRequests"]
    found = call(ctx, "run_source_tool", {"toolCallId": empty["toolCallId"]})
    # Nothing fits: the Reader turns the button into its plain line.
    assert found["result"]["passages"] == []
    import learnloop.instructional.tools as tools

    real = tools.execute_tool
    failures = {"left": 1}

    def once(*args, **kwargs):
        if failures["left"]:
            failures["left"] -= 1
            raise TimeoutError("the lookup timed out")
        return real(*args, **kwargs)

    monkeypatch.setattr(tools, "execute_tool", once)
    with pytest.raises(Exception):
        call(ctx, "run_source_tool", {"toolCallId": flaky["toolCallId"]})
    # The button stays; the press runs it again, under the same stored request.
    again = call(ctx, "run_source_tool", {"toolCallId": flaky["toolCallId"]})
    assert again["toolCallId"] == flaky["toolCallId"]
    with repository.connection() as connection:
        statuses = [row[0] for row in connection.execute(
            "SELECT status FROM source_tool_calls WHERE parent_id = ? AND row_kind = 'run' ORDER BY created_at, id",
            (flaky["toolCallId"],))]
    assert statuses == ["failed", "ran"]


def test_the_tutor_never_serves_schedules_or_imports(tmp_path, monkeypatch):
    _tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch)
    tables = learning_state_tables(repository) + ["source_exercise_imports", "reveal_events"]
    before = table_counts(repository, tables)
    answer = ask(ctx)
    for request in _by_tool(answer, "find_practice") + _by_tool(answer, "find_sources"):
        call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    assert table_counts(repository, tables) == before


def test_the_next_step_button_waits_for_active_reading(tmp_path, monkeypatch):
    _tutor, ctx, _repository = _offer_ctx(tmp_path, monkeypatch,
                                          config={"reader_active_reading": {"enabled": False}})
    answer = ask(ctx)
    assert answer["tutorOffers"] == {"buttons": []}
    contract = call(ctx, "reader.prompt_contract", {})
    assert contract["readerTutor"]["tryNextStep"] is False


def test_offers_off_sends_no_buttons_and_both_off_leave_the_contract(tmp_path, monkeypatch):
    _tutor, ctx, _repository = _offer_ctx(tmp_path, monkeypatch, config={"reader_tutor": {"offers_enabled": False}})
    answer = ask(ctx)
    assert "tutorOffers" not in answer and answer["tutor"]["modes"]
    contract = call(ctx, "reader.prompt_contract", {})
    assert contract["readerTutor"]["offers"] is False and contract["readerTutor"]["retrieval"] is True
    _tutor, off, _repository = _offer_ctx(tmp_path / "off", monkeypatch, config={
        "reader_tutor": {"offers_enabled": False, "retrieval_enabled": False}})
    assert "readerTutor" not in call(off, "reader.prompt_contract", {})
    answer = ask(off)
    assert "tutorOffers" not in answer and "tutor" not in answer
    with pytest.raises(SidecarError) as caught:
        ask(off, "Explain it another way", parentExchangeId=answer["readerAnswerEventId"],
            retrievalIntent="alternative")
    assert caught.value.code == "validation_error"


def test_a_press_is_a_salience_only_reader_event_counted_by_the_report(tmp_path, monkeypatch):
    _tutor, ctx, repository = _offer_ctx(tmp_path, monkeypatch)
    answer = ask(ctx)
    (passages,) = _by_tool(answer, "find_sources")
    call(ctx, "reader.log_activity", {"events": [
        {"kind": "reader_action_invoked", "event": "tutor_offer_shown",
         "payload": {"extractionId": "ext_text", "exchangeId": answer["readerAnswerEventId"],
                     "offerKind": kind}} for kind in ("practice", "passages", "compare", "try_next_step")
    ] + [{"kind": "reader_action_invoked", "event": "tutor_offer_pressed",
          "payload": {"extractionId": "ext_text", "exchangeId": answer["readerAnswerEventId"],
                      "offerKind": "passages", "toolCallId": passages["toolCallId"], "offerResult": "shown",
                      "quote": "never kept"}}]})
    (pressed,) = [e for e in repository.reader_interaction_events(kind="reader_action_invoked")
                  if e["payload"].get("event") == "tutor_offer_pressed"]
    assert pressed["payload"]["tool_call_id"] == passages["toolCallId"] and "quote" not in pressed["payload"]
    assert pressed["payload"]["authority_class"] == SF.SALIENCE_ONLY
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(pressed)
    report = build_reader_report(repository.sqlite_path, now=datetime(2030, 1, 1, tzinfo=UTC))["tutor"]
    assert report["answers"] == 1 and report["by_mode"]["grounded"] == 1
    assert report["offers"]["shown"] == {"practice": 1, "passages": 1, "compare": 1, "try_next_step": 1}
    assert report["offers"]["pressed"] == {"passages": 1}
    assert "tutor_offer_pressed" in RI.CLIENT_ACTION_EVENTS


def test_the_report_counts_modes_abstentions_and_follow_ons(tmp_path, monkeypatch):
    from tests.reader_tutor_fakes import RejectAll

    tutor = LookupTutor(excerpt={"extraction_id": "ext_text", "span_id": "t3", "quote": "not in the passage at all"})
    _paths, ctx, repository, _spans = reader_ctx(tmp_path, monkeypatch, tutor)
    root = ask(ctx)
    ask(ctx, "Explain it another way", parentExchangeId=root["readerAnswerEventId"], retrievalIntent="alternative")
    call(ctx, "reader.set_inquiry_status", {"extractionId": "ext_text", "exchangeId": root["readerAnswerEventId"],
                                            "resolution": "resolved"})
    ctx.reader_tutor_rerank_client = RejectAll()
    ask(ctx, "something the books never say?")
    report = build_reader_report(repository.sqlite_path, now=datetime(2030, 1, 1, tzinfo=UTC))["tutor"]
    # "Another way" found nothing the inquiry had not shown, so it abstained too.
    assert report["answers"] == 3 and report["abstained"] == 2 and report["excerpts_dropped"] == 3
    assert report["by_mode"] == {"excerpt": 0, "grounded": 3, "bridge": 0}
    assert report["another_way"] == {"count": 1, "of": 3, "share": 0.3333}
    assert report["didnt_help"] == {"count": 0, "of": 3, "share": 0.0}
    assert report["resolved_after"]["another_way"] == {"count": 1, "of": 1, "share": 1.0}
