"""RW1a reader activity: the funnel's events, behind the salience firewall.

The Reader records visits, selections, actions, detours, reconnect lines and
model jobs on EXISTING interaction kinds with a payload ``event`` field (spec
§4.3: no new kind, no table rebuild). Every row is ``salience_only``: the
evidence ingestion API rejects it, and recording writes nothing but the event
(W1 tier 1, G2). The salience-firewall test gains a case per new ``event``
value (spec §4.3, §11).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.attempts.attempts import apply_attempt
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_inquiry as RI
from tests.helpers import append_config_toml
from tests.test_reader_dialogue import _CLOCK, _setup
from tests.test_reader_inquiry_status import table_counts
from tests.test_sidecar_reader import _init, _rpc, _setup as _rpc_setup


def _client_event(kind: str, event: str | None) -> dict:
    payload = {"visit_id": "v1", "extraction_id": "ext1", "action_kind": "ask", "job_id": "j1",
               "job_kind": "ask", "status": "completed", "latency_ms": 1200, "model_wait_ms": 1100,
               "detour_id": "d1", "detour_kind": "branch", "returned_to_origin": True,
               "element": "reconnect_line", "placement": "inline", "root_exchange_id": "r1"}
    entry = {"kind": kind, "payload": payload}
    if event is not None:
        entry["event"] = event
    return entry


CLIENT_CASES = [(kind, None) for kind in RI.CLIENT_ACTIVITY_KINDS] + [
    ("reader_action_invoked", event) for event in RI.CLIENT_ACTION_EVENTS
]


def test_the_vocabulary_is_the_spec_list_plus_the_funnels_rows():
    # Spec §4.3 / §11 name detour_opened, detour_returned and reconnect_answered
    # for RW1a; the funnel adds the rest. No new interaction kind: every kind
    # used is already in the envelope's CHECK and the firewall vocabulary.
    assert {"detour_opened", "detour_returned", "reconnect_answered"} <= set(RI.INQUIRY_EVENTS)
    for kind in RI.CLIENT_ACTIVITY_KINDS + ("reader_action_invoked",):
        assert kind in SF.READING_EVENT_KINDS


@pytest.mark.parametrize("kind,event", CLIENT_CASES)
def test_every_client_event_is_salience_only_and_never_evidence(tmp_path, kind, event):
    _vault, repo = _setup(tmp_path)
    before = table_counts(repo)
    (event_id,) = RI.record_activity(repo, [_client_event(kind, event)], clock=_CLOCK)
    (row,) = [e for e in repo.reader_interaction_events(kind=kind) if e["id"] == event_id]
    assert row["payload"]["authority_class"] == SF.SALIENCE_ONLY
    if event is not None:
        assert row["payload"]["event"] == event
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(row)
    with pytest.raises(SF.SalienceEvidenceRejected):
        apply_attempt(None, None, SimpleNamespace(**row))  # type: ignore[arg-type]
    assert table_counts(repo) == before


@pytest.mark.parametrize("event", RI.SERVER_ACTION_EVENTS)
def test_every_server_event_is_salience_only_and_never_evidence(tmp_path, event):
    vault, repo = _setup(tmp_path)
    root = RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
                  question_md="Root", clock=_CLOCK)
    before = table_counts(repo)
    if event == "inquiry_status_set":
        RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                              resolution="resolved", trigger="chip", clock=_CLOCK)
    else:
        RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                            answer="still_unclear", via="rail", clock=_CLOCK)
    rows = [e for e in repo.reader_interaction_events(kind="reader_action_invoked")
            if e["payload"].get("event") == event]
    assert rows and all(r["payload"]["authority_class"] == SF.SALIENCE_ONLY for r in rows)
    for row in rows:
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(row)
    assert table_counts(repo) == before


def test_activity_keeps_only_known_fields_and_no_learner_text(tmp_path):
    _vault, repo = _setup(tmp_path)
    (event_id,) = RI.record_activity(repo, [{
        "kind": "reader_action_invoked", "event": "action_invoked",
        "payload": {"visit_id": "v1", "action_kind": "ask", "question": "my private words",
                    "quote": "selected text", "failure_reason": "x" * 500,
                    "activity_during_wait": {"scrolled": True, "typed": "yes", "other": True}},
    }], clock=_CLOCK)
    (row,) = [e for e in repo.reader_interaction_events() if e["id"] == event_id]
    payload = row["payload"]
    assert "question" not in payload and "quote" not in payload
    assert len(payload["failure_reason"]) == RI.MAX_FIELD_CHARS
    assert payload["activity_during_wait"] == {"scrolled": True}


@pytest.mark.parametrize("bad", [
    {"kind": "reader_answer_submitted", "payload": {}},
    {"kind": "reader_action_invoked", "event": "inquiry_status_set", "payload": {}},
    {"kind": "reader_action_invoked", "event": "made_up", "payload": {}},
    {"kind": "reader_action_invoked", "payload": {}},
    {"kind": "reader_selection", "event": "detour_opened", "payload": {}},
])
def test_unknown_or_server_owned_events_are_refused_whole(tmp_path, bad):
    _vault, repo = _setup(tmp_path)
    good = _client_event("reader_selection", None)
    before = repo.reader_interaction_events()
    with pytest.raises(RI.InquiryError):
        RI.record_activity(repo, [good, bad], clock=_CLOCK)
    assert repo.reader_interaction_events() == before


def test_log_activity_rpc_and_its_kill_switch(tmp_path):
    root_dir = _rpc_setup(tmp_path)
    params = {"events": [{"kind": "reader_view_opened", "payload": {"visitId": "v1", "extractionId": "ext1",
                                                                     "sourceKind": "pdf"}},
                         {"kind": "reader_action_invoked", "event": "detour_opened",
                          "payload": {"visitId": "v1", "detourKind": "branch"}}]}
    ok = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.log_activity",
                                 "params": params}])[1]["result"]
    assert ok["recorded"] == 2
    append_config_toml(root_dir, """
    [reader_inquiry]
    enabled = false
    """)
    refused = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.log_activity",
                                      "params": params}])[1]
    assert refused["error"]["data"]["code"] == "inquiry_disabled"
