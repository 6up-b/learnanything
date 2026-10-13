"""RW1a inquiry status (spec_reader_workbench_v1 §4.1, D4; gate G2).

An inquiry is a root exchange and its descendants. Its status is the root's
existing ``question_events.resolution`` (open | resolved | dismissed), reopen
included; no new status vocabulary and no schema change. Every flip is logged
as a salience-only ``reader_action_invoked`` event (``inquiry_status_set``) so
the report can count reopens, and none writes evidence.
"""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_inquiry as RI
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.reader_fixtures import notes_source, transcript_source
from tests.test_reader_dialogue import _CLOCK, _setup
from tests.test_sidecar_reader import _init, _rpc, _setup as _rpc_setup

# The tables RW1a may write: the event envelope and the questions it already
# writes for every Ask. Nothing else changes when a status flips (G2).
_ALLOWED = {"interaction_events", "question_events", "schema_migrations"}


def table_counts(repo: Repository) -> dict[str, int]:
    with repo.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )]
        return {
            name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            for name in names if name not in _ALLOWED and not name.startswith("source_block_fts")
        }


def _ask(vault, repo, question, parent=None, *, extraction_id="ext1", span_id="s1"):
    return RD.ask(vault, repo, RD.StubReaderClient(), extraction_id=extraction_id, span_id=span_id,
                  question_md=question, parent_exchange_id=parent, clock=_CLOCK)


def _status_events(repo):
    return [e for e in repo.reader_interaction_events(kind="reader_action_invoked")
            if e["payload"].get("event") == "inquiry_status_set"]


def test_status_lives_on_the_root_question_and_reopen_is_accepted(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Why weighted by p?")
    child = _ask(vault, repo, "Conditioning on a coin flip?", root["reader_answer_event_id"])

    # Any exchange in the inquiry names it; the status lands on the root.
    resolved = RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=child["reader_answer_event_id"],
                                     resolution="resolved", trigger="chip", clock=_CLOCK)
    assert resolved["root_exchange_id"] == root["reader_answer_event_id"]
    assert resolved["question_event_id"] == root["event_id"]
    assert (resolved["previous_resolution"], resolved["resolution"]) == ("open", "resolved")
    assert repo.question_event(root["event_id"])["resolution"] == "resolved"
    assert repo.question_event(child["event_id"])["resolution"] == "open"

    reopened = RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                                     resolution="open", trigger="chip", clock=_CLOCK)
    assert (reopened["previous_resolution"], reopened["resolution"]) == ("resolved", "open")
    RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                          resolution="dismissed", trigger="undo", clock=_CLOCK)

    events = _status_events(repo)
    assert [(e["payload"]["resolution"], e["payload"]["previous_resolution"], e["payload"]["trigger"])
            for e in events] == [("resolved", "open", "chip"), ("open", "resolved", "chip"),
                                 ("dismissed", "open", "undo")]
    assert all(e["payload"]["authority_class"] == "salience_only" for e in events)
    history = {e["event_id"]: e for e in RD.ask_history(repo, extraction_id="ext1")}
    assert history[root["reader_answer_event_id"]]["resolution"] == "dismissed"


def test_status_flips_write_no_evidence(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    before = table_counts(repo)
    for resolution in ("resolved", "open", "dismissed", "open"):
        RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                              resolution=resolution, trigger="chip", clock=_CLOCK)
    assert table_counts(repo) == before


@pytest.mark.parametrize("bad", ["unknown_resolution", "unknown_exchange", "wrong_extraction", "bad_trigger"])
def test_invalid_status_requests_are_refused_before_any_write(tmp_path, bad):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    kwargs = {"extraction_id": "ext1", "exchange_id": root["reader_answer_event_id"],
              "resolution": "resolved", "trigger": "chip"}
    if bad == "unknown_resolution":
        kwargs["resolution"] = "revisit_once"
    elif bad == "unknown_exchange":
        kwargs["exchange_id"] = "nope"
    elif bad == "wrong_extraction":
        kwargs["extraction_id"] = "ext2"
    else:
        kwargs["trigger"] = "auto"
    before = repo.reader_interaction_events()
    with pytest.raises(RI.InquiryError):
        RI.set_inquiry_status(repo, clock=_CLOCK, **kwargs)
    assert repo.reader_interaction_events() == before
    assert repo.question_event(root["event_id"])["resolution"] == "open"


def test_status_rpc_and_its_kill_switch(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from learnloop_sidecar.handlers import reader

    root_dir = _rpc_setup(tmp_path)
    client = RD.StubReaderClient()
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), client))
    asked = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask",
                                    "params": {"extractionId": "ext1", "spanId": "s1", "question": "Root"}}])[1]["result"]
    status = {"extractionId": "ext1", "exchangeId": asked["readerAnswerEventId"], "resolution": "resolved",
              "trigger": "chip"}
    result = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.set_inquiry_status",
                                     "params": status}])[1]["result"]
    assert result["resolution"] == "resolved"
    assert result["rootExchangeId"] == asked["readerAnswerEventId"]
    assert result["openCount"] == 0

    append_config_toml(root_dir, """
    [reader_inquiry]
    enabled = false
    """)
    refused = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.set_inquiry_status",
                                      "params": {**status, "resolution": "open"}}])[1]
    assert refused["error"]["data"]["code"] == "inquiry_disabled"


@pytest.mark.parametrize("source", ["transcript", "notes"])
def test_inquiries_work_on_every_source_kind(tmp_path, source):
    vault, repo = _setup(tmp_path)
    fixture = transcript_source(repo) if source == "transcript" else notes_source(repo)
    vault = load_vault(vault.root)
    root = _ask(vault, repo, "What does this assume?", extraction_id=fixture["extraction_id"],
                span_id=fixture["span_id"])
    child = _ask(vault, repo, "And why?", root["reader_answer_event_id"],
                 extraction_id=fixture["extraction_id"], span_id=fixture["span_id"])
    assert child["parent_exchange_id"] == root["reader_answer_event_id"]
    result = RI.set_inquiry_status(repo, extraction_id=fixture["extraction_id"],
                                   exchange_id=child["reader_answer_event_id"], resolution="resolved",
                                   trigger="chip", clock=_CLOCK)
    assert result["root_exchange_id"] == root["reader_answer_event_id"]
