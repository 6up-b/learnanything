"""RW1a's kill switch (``reader_inquiry.enabled``): off is today's flat rail.

Spec §12: with the switch off, every RPC RW1a touches answers byte-identically
on fixture copies. ``reader.ask``, ``reader.ask_history`` and
``reader.prompt_contract`` are checked here against the exact shapes and
values `main` produced at 09c9f8d3 (the flat per-span thread, the
``p2-reader-v1`` manifest, no parent fields anywhere); the new inquiry RPCs are
absent (refused) while it is off.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.test_reader_dialogue import _CLOCK, _setup
from tests.test_sidecar_reader import _init, _rpc, _setup as _rpc_setup

# main@09c9f8d3's reader.ask result keys (handlers/reader.py) and the flat
# ask_history projection (reader_dialogue.ask_history).
MAIN_ASK_RESULT_KEYS = {
    "version", "eventId", "readerAnswerEventId", "answerMd", "answerMode", "citations",
    "manifest", "warmedSurfaceIds", "burnedSurfaceIds", "hintEquivalent", "remaining", "learnerGap",
}
#: Canonical sources (merged after RW1a): the reader answer's deterministic
#: "Practice this" request, behind source_service.tutor_offers (not a
#: reader_inquiry field, so the kill switch leaves it as it is).
SOURCE_SERVICE_ASK_KEYS = {"practiceRequest"}
#: Reader workbench RW1c (merged after RW1a): the answer's modes and the
#: Reader's buttons, behind reader_tutor.retrieval_enabled / offers_enabled
#: (not reader_inquiry fields, so this kill switch leaves them as they are);
#: the manifest then records the retrieval's receipt.
READER_TUTOR_ASK_KEYS = {"tutor", "tutorOffers"}
READER_TUTOR_MANIFEST_KEYS = {"sourceRetrieval", "delivery"}
READER_TUTOR_HISTORY_KEYS = {"tutor"}
MAIN_HISTORY_KEYS = {
    "eventId", "extractionId", "spanId", "questionMd", "answerMd", "answerMode", "citations", "createdAt",
}
MAIN_MANIFEST_KEYS = {
    "version", "span", "selection", "source_spans", "question_md", "answer_mode",
    "goal_invariants", "prior_exchanges", "excluded",
}


def _switch_off(root) -> None:
    append_config_toml(root, """
    [reader_inquiry]
    enabled = false
    """)


def test_service_off_is_the_flat_same_span_thread(tmp_path):
    vault, repo = _setup(tmp_path)
    _switch_off(vault.root)
    vault = load_vault(vault.root)
    assert RD.inquiry_enabled(vault) is False
    client = RD.StubReaderClient()
    first = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1",
                   question_md="First", clock=_CLOCK)
    second = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1",
                    question_md="Second", clock=_CLOCK)
    # Today's thread: every earlier answered exchange on the same span.
    assert client.contexts[0].thread == []
    assert [t["question_md"] for t in client.contexts[1].thread] == ["First"]
    for result in (first, second):
        assert "parent_exchange_id" not in result
        assert set(result["manifest"]) == MAIN_MANIFEST_KEYS
        assert result["manifest"]["version"] == "p2-reader-v1"
    assert second["manifest"]["prior_exchanges"] == [
        {"question_md": "First", "answer_md": "Grounded in the span in view."}
    ]
    for kind in ("learner_question_asked", "reader_answer_submitted"):
        for event in repo.reader_interaction_events(kind=kind):
            assert "parent_exchange_id" not in event["payload"]
    flat = RD.ask_history(repo, extraction_id="ext1", branches=False)
    assert all(set(e) == {"event_id", "extraction_id", "span_id", "question_md", "answer_md",
                          "answer_mode", "citations", "created_at"} for e in flat)


def test_service_off_refuses_a_parent_before_any_write(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    root = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1",
                  question_md="Root", clock=_CLOCK)
    _switch_off(vault.root)
    vault = load_vault(vault.root)
    before = repo.reader_interaction_events()
    try:
        RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1", question_md="Follow",
               parent_exchange_id=root["reader_answer_event_id"], clock=_CLOCK)
    except RD.ReaderDialogueError as exc:
        assert "reader_inquiry" in str(exc)
    else:  # pragma: no cover - the assertion below names the failure
        raise AssertionError("a parent must be refused while reader_inquiry is off")
    assert repo.reader_interaction_events() == before
    assert len(client.contexts) == 1


def _rpc_off(tmp_path):
    root = _rpc_setup(tmp_path)
    _switch_off(root)
    return root


def test_rpcs_off_answer_exactly_as_before(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import reader

    root = _rpc_off(tmp_path)
    client = RD.StubReaderClient()
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), client))
    params = {"extractionId": "ext1", "spanId": "s1", "question": "Root"}
    responses = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.ask", "params": params},
        {"jsonrpc": "2.0", "id": 3, "method": "reader.ask", "params": {**params, "question": "Again"}},
        {"jsonrpc": "2.0", "id": 4, "method": "reader.ask_history", "params": {"extractionId": "ext1"}},
        {"jsonrpc": "2.0", "id": 5, "method": "reader.prompt_contract", "params": {}},
        {"jsonrpc": "2.0", "id": 6, "method": "reader.ask",
         "params": {**params, "parentExchangeId": "anything"}},
    ])
    first, second, history, contract, refused = (r for r in responses[1:])
    for answer in (first["result"], second["result"]):
        assert set(answer) - SOURCE_SERVICE_ASK_KEYS - READER_TUTOR_ASK_KEYS == MAIN_ASK_RESULT_KEYS
        assert answer["manifest"]["version"] == "p2-reader-v1"
        assert set(answer["manifest"]) - READER_TUTOR_MANIFEST_KEYS == {
            "version", "span", "selection", "sourceSpans", "questionMd", "answerMode",
            "goalInvariants", "priorExchanges", "excluded",
        }
    assert [t["question_md"] for t in client.contexts[1].thread] == ["Root"]
    assert all(set(e) - READER_TUTOR_HISTORY_KEYS == MAIN_HISTORY_KEYS for e in history["result"]["exchanges"])
    expected_contract = RD.reader_prompt_contract()
    assert contract["result"]["version"] == expected_contract["version"] == "p2-reader-v1"
    assert "inquiryEnabled" not in contract["result"]
    assert contract["result"]["manifestIncludes"] == expected_contract["manifest_includes"]
    assert refused["error"]["data"]["code"] == "validation_error"


def test_rpcs_on_name_the_switch_and_the_branch_contract(tmp_path):
    root = _rpc_setup(tmp_path)
    contract = _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.prompt_contract", "params": {}},
    ])[1]["result"]
    assert contract["inquiryEnabled"] is True
    assert contract["version"] == "p3-reader-branches-v1"
    assert "the selected branch's reader ancestors only (most recent 12)" in contract["manifestIncludes"]


def test_history_on_carries_status_and_selection_for_each_exchange(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    root = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1", question_md="Root",
                  selection_span_ids=["s1"], selection_quote_md="A^T = A", clock=_CLOCK)
    history = RD.ask_history(Repository(repo.sqlite_path), extraction_id="ext1")
    (saved,) = history
    assert saved["question_event_id"] == root["event_id"]
    assert saved["resolution"] == "open"
    assert saved["parent_exchange_id"] is None
    assert saved["selection_span_ids"] == ["s1"]
    assert saved["selection_quote_md"] == "A^T = A"


def test_rpcs_on_add_only_the_branch_fields(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import reader

    root = _rpc_setup(tmp_path)
    client = RD.StubReaderClient()
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), client))
    params = {"extractionId": "ext1", "spanId": "s1", "question": "Root"}
    answer, history = (r["result"] for r in _rpc([
        _init(root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.ask", "params": params},
        {"jsonrpc": "2.0", "id": 3, "method": "reader.ask_history", "params": {"extractionId": "ext1"}},
    ])[1:])
    assert set(answer) - MAIN_ASK_RESULT_KEYS - SOURCE_SERVICE_ASK_KEYS - READER_TUTOR_ASK_KEYS == {
        "parentExchangeId", "model"}
    assert answer["parentExchangeId"] is None and answer["model"] == "stub-reader-1"
    assert answer["manifest"]["version"] == "p3-reader-branches-v1"
    (saved,) = history["exchanges"]
    assert set(saved) - MAIN_HISTORY_KEYS - READER_TUTOR_HISTORY_KEYS == {
        "parentExchangeId", "selectionSpanIds", "selectionQuoteMd", "selectionSourceQuoteMd",
        "questionEventId", "resolution",
    }
