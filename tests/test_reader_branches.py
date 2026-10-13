"""Branching reuses Reader Ask persistence, grounding, and evidence semantics."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
from learnloop.substrate.activities import log_interaction_event
from learnloop.tutor.ai_contracts import TutorCitation
from learnloop.vault.loader import load_vault
from tests.test_reader_dialogue import _CLOCK, _setup
from tests.test_sidecar_reader import _init, _rpc, _setup as _rpc_setup


def _ask(vault, repo, client, question, parent=None, **kwargs):
    return RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1",
                  question_md=question, parent_exchange_id=parent, clock=_CLOCK, **kwargs)


def test_branches_restore_after_restart_and_inherit_selection_without_siblings(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    root = _ask(vault, repo, client, "Root", selection_span_ids=["s1", "s2"],
                selection_quote_md="A^T = A. The spectral theorem")
    root_id = root["reader_answer_event_id"]
    left = _ask(vault, repo, client, "Left", root_id)
    _ask(vault, repo, client, "Right sibling", root_id)
    assert [t["question_md"] for t in client.contexts[-1].thread] == ["Root"]
    _ask(vault, repo, client, "Separate root")
    assert client.contexts[-1].thread == []

    # New repository + vault instances simulate an application restart.
    repo = Repository(repo.sqlite_path)
    vault = load_vault(vault.root)
    leaf = _ask(vault, repo, client, "Left follow-up", left["reader_answer_event_id"],
                selection_span_ids=["s0"], selection_quote_md="unrelated current selection")
    context = client.contexts[-1]
    assert [t["question_md"] for t in context.thread] == ["Root", "Left"]
    assert leaf["manifest"]["selection"] == root["manifest"]["selection"]
    assert context.source_spans[0]["text"] == "A^T = A. The spectral theorem"
    assert {s["span_id"] for s in context.source_spans if s["relation"] == "in_view"} >= {"s1", "s2"}
    history = RD.ask_history(Repository(repo.sqlite_path), extraction_id="ext1")
    saved = next(e for e in history if e["event_id"] == leaf["reader_answer_event_id"])
    assert saved["parent_exchange_id"] == left["reader_answer_event_id"]
    assert saved["selection_span_ids"] == ["s1", "s2"]
    assert saved["citations"] == leaf["citations"]
    assert saved["span_id"] == "s1" and saved["extraction_id"] == "ext1"
    assert len(history) == 5


def test_legacy_flat_exchange_remains_root_and_can_be_followed(tmp_path):
    vault, repo = _setup(tmp_path)
    legacy = log_interaction_event(repo, kind="reader_answer_submitted", origin="system",
        subject_type="reader_span", subject_id="span:ext1/s1",
        payload={"extraction_id": "ext1", "span_id": "s1", "answer_md": "Old answer",
                 "manifest": {"question_md": "Old question"}}, clock=_CLOCK)
    history = RD.ask_history(repo, extraction_id="ext1")
    assert history[0]["parent_exchange_id"] is None
    assert history[0]["selection_span_ids"] == []
    assert history[0]["selection_quote_md"] is None
    client = RD.StubReaderClient()
    _ask(vault, repo, client, "Clarify", legacy)
    assert client.contexts[-1].thread[0]["question_md"] == "Old question"


@pytest.mark.parametrize("invalid", ["missing", "question_event", "other_span", "other_extraction", "cycle"])
def test_invalid_parents_fail_before_model_call_or_event_write(tmp_path, invalid):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    root = _ask(vault, repo, client, "Root")
    parent = root["reader_answer_event_id"]
    extraction, span = "ext1", "s1"
    if invalid == "missing":
        parent = "does-not-exist"
    elif invalid == "question_event":
        parent = root["event_id"]  # A tutor question ID is not an exchange ID.
    elif invalid == "other_span":
        span = "s0"
    elif invalid == "other_extraction":
        extraction = "ext2"
    else:
        with repo.connection() as connection:
            connection.execute("UPDATE interaction_events SET payload_json = json_set(payload_json, '$.parent_exchange_id', ?) WHERE id = ?", (parent, parent))
            connection.commit()
    before = repo.reader_interaction_events()
    with pytest.raises(RD.ReaderDialogueError):
        RD.ask(vault, repo, client, extraction_id=extraction, span_id=span,
               question_md="Invalid follow-up", parent_exchange_id=parent, clock=_CLOCK)
    assert len(client.contexts) == 1
    assert repo.reader_interaction_events() == before


def test_failed_followup_does_not_become_a_branch_or_pollute_retry(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    root = _ask(vault, repo, client, "Root")

    class Failing(RD.StubReaderClient):
        def complete(self, request):
            raise TimeoutError("offline")

    with pytest.raises(TimeoutError):
        _ask(vault, repo, Failing(), "Interrupted", root["reader_answer_event_id"])
    assert len(RD.ask_history(repo, extraction_id="ext1")) == 1
    _ask(vault, repo, client, "Retry", root["reader_answer_event_id"])
    assert [t["question_md"] for t in client.contexts[-1].thread] == ["Root"]


def test_followup_refuses_an_unresolvable_source_anchor(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    root = _ask(vault, repo, client, "Root")
    with repo.connection() as connection:
        connection.execute("DELETE FROM source_document_blocks WHERE extraction_id = 'ext1' AND span_id = 's1'")
        connection.commit()
    with pytest.raises(RD.ReaderDialogueError, match="source passage is no longer available"):
        _ask(vault, repo, client, "Follow up", root["reader_answer_event_id"])
    assert len(client.contexts) == 1
    assert len(RD.ask_history(repo, extraction_id="ext1")) == 1


def test_branch_keeps_citation_allowlist_and_evidence_isolation(tmp_path):
    vault, repo = _setup(tmp_path)

    class Citing(RD.StubReaderClient):
        def complete(self, request):
            answer = super().complete(request)
            answer.facets = ["facet_svd_definition"]
            answer.citations.append(TutorCitation(extraction_id="invented", span_id="invented"))
            return answer

    client = Citing()
    # Capture every state table used by the existing reader evidence firewall.
    tables = ["facet_recall_state", "practice_item_state", "learner_state_beliefs",
              "activity_observations", "activity_administrations", "practice_attempts"]
    def snapshot():
        with repo.connection() as connection:
            return {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")] for table in tables}
    before = snapshot()
    root = _ask(vault, repo, client, "Root")
    child = _ask(vault, repo, client, "Follow up", root["reader_answer_event_id"])
    assert child["citations"] and all(c["extraction_id"] == "ext1" for c in child["citations"])
    assert snapshot() == before
    for event in repo.question_events(context="reader"):
        assert not event.get("facets")
        assert event["practice_item_id"] is None and event["attempt_id"] is None
    assert all(context.candidate_facets == [] for context in client.contexts)
    assert all(context.expected_answer is None for context in client.contexts)
    for event in repo.reader_interaction_events(kind="reader_answer_submitted"):
        assert event["payload"]["authority_class"] == "salience_only"


def test_deep_branch_bounds_prompt_history_without_losing_saved_links(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    parent = None
    # Seed historical completions without spending the per-day Ask budget.
    for index in range(14):
        parent = log_interaction_event(repo, kind="reader_answer_submitted", origin="system",
            subject_type="reader_span", subject_id="span:ext1/s1",
            payload={"extraction_id": "ext1", "span_id": "s1", "parent_exchange_id": parent,
                     "answer_md": f"Answer {index}", "manifest": {"question_md": f"Question {index}"}}, clock=_CLOCK)
    result = _ask(vault, repo, client, "Leaf", parent)
    assert [t["question_md"] for t in client.contexts[-1].thread] == [f"Question {i}" for i in range(2, 14)]
    assert result["manifest"]["omitted_ancestor_count"] == 2
    assert len(RD.ask_history(repo, extraction_id="ext1")) == 15


def test_branch_rpc_roundtrip_uses_parent_id_and_persists_on_reinitialize(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import reader
    root = _rpc_setup(tmp_path)
    client = RD.StubReaderClient()
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), client))
    def call(params):
        return _rpc([_init(root), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask", "params": params}])[1]
    params = {"extractionId": "ext1", "spanId": "s1", "question": "Root", "selectionSpanIds": ["s0", "s1"], "selectionQuote": "Intro. A^T = A"}
    first = call(params)["result"]
    child = call({**params, "question": "Follow-up", "parentExchangeId": first["readerAnswerEventId"]})["result"]
    assert child["parentExchangeId"] == first["readerAnswerEventId"]
    history = _rpc([_init(root), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask_history", "params": {"extractionId": "ext1"}}])[1]["result"]["exchanges"]
    saved = next(e for e in history if e["eventId"] == child["readerAnswerEventId"])
    assert saved["parentExchangeId"] == first["readerAnswerEventId"]
    assert saved["selectionSpanIds"] == ["s0", "s1"]
    assert saved["selectionQuoteMd"] == "Intro. A^T = A"
    error = call({**params, "parentExchangeId": "absent"})["error"]
    assert error["data"]["code"] == "validation_error"
