"""RW1a reconnect and its passage-scoped quick check (spec §4.1, §4.3; G2, G4).

Reconnect asks "does this make sense now?" about the inquiry's root, in the
learner's own words. *Yes* resolves the root (an explicit self-report); *still
unclear* starts a branch (a reader.ask with the root as parent, covered in the
branch tests); *quick check* asks the quick-check producer for one formative
question scoped to the root passage. Migration 189 gives
``reader_authored_questions`` its scopes; the section lookups filter
``scope_kind = 'section'`` so a reconnect row never shadows its section's
quick check, and section rows stay byte-identical.
"""

from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace

import pytest

from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_inquiry as RI
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingQuickCheck
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.reader_fixtures import notes_source, transcript_source
from tests.structured_ai import StructuredClientFake
from tests.test_reader_dialogue import _CLOCK
from tests.test_reader_guidance import _setup as _guide_setup
from tests.test_reader_inquiry_status import table_counts
from tests.test_sidecar_reader import _init, _rpc, _setup as _rpc_setup

SECTION_PAYLOAD_KEYS = {
    "id", "extraction_id", "section_id", "status", "question_md", "expected_answer_md",
    "span_ids", "practice_item_id", "answered_at",
}


class FakeClient(StructuredClientFake):
    # Billed like Codex on the subscription (no price needed): these tests are
    # about authoring; the passage check's spend admission, isolation and
    # claim are tests/test_reader_passage_check.py's.
    provider_type = "codex_sdk"

    def __init__(self, span_ids=("s1",)) -> None:
        self.calls: list = []
        self.span_ids = list(span_ids)

    def run_reading_quick_check(self, context):
        self.calls.append(context)
        return ReadingQuickCheck(
            question_md="Why is A's eigenbasis orthonormal?",
            expected_answer_md="Because A is symmetric; the spectral theorem gives an orthonormal eigenbasis.",
            span_ids=self.span_ids,
        )


def _setup(tmp_path):
    vault, repository = _guide_setup(tmp_path)
    return vault, repository


def _ask(vault, repo, question, parent=None, *, extraction_id="ext1", span_id="s1", **kwargs):
    return RD.ask(vault, repo, RD.StubReaderClient(), extraction_id=extraction_id, span_id=span_id,
                  question_md=question, parent_exchange_id=parent, clock=_CLOCK, **kwargs)


def _events(repo, event):
    return [e for e in repo.reader_interaction_events(kind="reader_action_invoked")
            if e["payload"].get("event") == event]


# -- migration 189 ------------------------------------------------------------

def test_migration_adds_the_scope_columns_with_section_defaults(tmp_path):
    _vault, repo = _setup(tmp_path)
    with repo.connection() as connection:
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(reader_authored_questions)")}
    for name in ("scope_kind", "question_style", "anchor_span_ids_json", "inquiry_root_event_id", "self_check"):
        assert name in columns
    row = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    assert (row["scope_kind"], row["question_style"]) == ("section", "recall")
    assert row["anchor_span_ids_json"] is None and row["inquiry_root_event_id"] is None
    assert row["self_check"] is None


@pytest.mark.parametrize("column,value", [
    ("scope_kind", "chapter"), ("question_style", "trivia"), ("self_check", "maybe"),
])
def test_scope_columns_carry_their_checks(tmp_path, column, value):
    _vault, repo = _setup(tmp_path)
    row = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    with repo.connection() as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"UPDATE reader_authored_questions SET {column} = ? WHERE id = ?", (value, row["id"]))


def test_every_question_style_is_accepted_now(tmp_path):
    _vault, repo = _setup(tmp_path)
    row = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    with repo.connection() as connection:
        for style in ("recall", "next_step", "why_step", "assumptions", "reconstruct"):
            connection.execute("UPDATE reader_authored_questions SET question_style = ? WHERE id = ?",
                               (style, row["id"]))
        connection.commit()


# -- scopes and reuse keys ------------------------------------------------------

def test_an_inquiry_row_never_shadows_its_sections_quick_check(tmp_path):
    vault, repo = _setup(tmp_path)
    section_row = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    root = _ask(vault, repo, "Why orthonormal?")
    inquiry_row = RQC.author_inquiry_quick_check(
        repo, FakeClient(), extraction_id="ext1", inquiry_root_event_id=root["reader_answer_event_id"],
        anchor_span_ids=["s1"], clock=_CLOCK,
    )
    assert inquiry_row["section_id"] == "u1"  # the anchor's section
    assert inquiry_row["scope_kind"] == "inquiry"
    latest = repo.latest_reader_authored_question(extraction_id="ext1", section_id="u1")
    assert latest["id"] == section_row["id"]
    plan = build_guide_plan(vault, repo, extraction_id="ext1")
    assert plan["sections"][0]["question"]["authored_question_id"] == section_row["id"]


def test_section_quick_checks_are_byte_identical(tmp_path):
    from learnloop_sidecar.handlers.reader import _authored_question_payload

    _vault, repo = _setup(tmp_path)
    row = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    assert set(_authored_question_payload(row)) == SECTION_PAYLOAD_KEYS
    answered = RQC.record_action(repo, question_id=row["id"], action="answered", response_md="Mine.")
    assert answered["self_check"] is None


def test_inquiry_reuse_key_is_root_and_prompt_version(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    other = _ask(vault, repo, "Another root")
    client = FakeClient()
    kwargs = {"extraction_id": "ext1", "anchor_span_ids": ["s1"], "clock": _CLOCK}
    first = RQC.author_inquiry_quick_check(repo, client, inquiry_root_event_id=root["reader_answer_event_id"], **kwargs)
    again = RQC.author_inquiry_quick_check(repo, client, inquiry_root_event_id=root["reader_answer_event_id"], **kwargs)
    assert again["id"] == first["id"] and len(client.calls) == 1
    second = RQC.author_inquiry_quick_check(repo, client, inquiry_root_event_id=other["reader_answer_event_id"], **kwargs)
    assert second["id"] != first["id"] and len(client.calls) == 2
    assert first["prompt_version"] == RQC.INQUIRY_PROMPT_VERSION
    # A dismissed row still suppresses re-authoring for its own key.
    RQC.record_inquiry_action(repo, question_id=first["id"], action="dismissed", clock=_CLOCK)
    suppressed = RQC.author_inquiry_quick_check(repo, client, inquiry_root_event_id=root["reader_answer_event_id"], **kwargs)
    assert suppressed["id"] == first["id"] and suppressed["status"] == "dismissed"
    assert len(client.calls) == 2


def test_the_inquiry_check_is_scoped_to_the_root_passage(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    client = FakeClient(span_ids=["s1", "s99"])
    row = RQC.author_inquiry_quick_check(
        repo, client, extraction_id="ext1", inquiry_root_event_id=root["reader_answer_event_id"],
        anchor_span_ids=["s1"], clock=_CLOCK,
    )
    context = client.calls[0]
    assert context.section["scope"] == "passage"
    provided = [block["span_id"] for block in context.section["blocks"]]
    assert "s1" in provided and len(provided) <= 1 + RQC.PASSAGE_BLOCKS_BEFORE + RQC.PASSAGE_BLOCKS_AFTER
    assert json.loads(row["span_ids_json"]) == ["s1"]  # invented spans dropped
    assert json.loads(row["anchor_span_ids_json"]) == ["s1"]


def test_answering_and_self_checking_an_inquiry_check_is_formative(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    row = RQC.author_inquiry_quick_check(
        repo, FakeClient(), extraction_id="ext1", inquiry_root_event_id=root["reader_answer_event_id"],
        anchor_span_ids=["s1"], clock=_CLOCK,
    )
    before = table_counts(repo)
    answered = RQC.record_inquiry_action(repo, question_id=row["id"], action="answered",
                                         response_md="It's symmetric.", clock=_CLOCK)
    assert answered["status"] == "answered" and answered["response_md"] == "It's symmetric."
    checked = RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked",
                                        self_check="partly", clock=_CLOCK)
    assert checked["self_check"] == "partly"
    after = table_counts(repo)
    # The row is updated in place and the learner's verdict is appended to the
    # judgment ledger (W10); no attempt, observation, mastery or state row.
    assert after.pop("judgment_ledger") == before.pop("judgment_ledger") + 1
    assert after == before
    with pytest.raises(RQC.ReaderQuickCheckError):
        RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="kinda")
    section = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    with pytest.raises(RQC.ReaderQuickCheckError):
        RQC.record_inquiry_action(repo, question_id=section["id"], action="answered", response_md="x")


def _self_check_verdicts(repo, question_id):
    with repo.connection() as connection:
        return [dict(r) for r in connection.execute(
            "SELECT id, verdict, judge, supersedes_id, left_kind, right_kind, right_id, prompt_version "
            "FROM judgment_ledger WHERE task = ? AND left_id = ? ORDER BY created_at, rowid",
            (RQC.SELF_CHECK_TASK, question_id),
        )]


def test_each_self_check_verdict_is_a_learner_card_judgment_and_a_change_supersedes(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    row = RQC.author_inquiry_quick_check(repo, FakeClient(), extraction_id="ext1",
                                         inquiry_root_event_id=root["reader_answer_event_id"],
                                         anchor_span_ids=["s1"], clock=_CLOCK)
    RQC.record_inquiry_action(repo, question_id=row["id"], action="answered", response_md="Symmetric.", clock=_CLOCK)
    RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="partly", clock=_CLOCK)
    RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="partly", clock=_CLOCK)
    (first,) = _self_check_verdicts(repo, row["id"])
    assert (first["verdict"], first["judge"], first["supersedes_id"]) == ("partly", "learner_card", None)
    assert (first["left_kind"], first["right_kind"]) == ("reader_authored_question", "reader_quick_check_response")
    assert first["prompt_version"] == RQC.INQUIRY_PROMPT_VERSION
    # Changing the verdict keeps the earlier one: the new verdict supersedes it.
    RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="no", clock=_CLOCK)
    RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="partly", clock=_CLOCK)
    verdicts = _self_check_verdicts(repo, row["id"])
    assert [v["verdict"] for v in verdicts] == ["partly", "no", "partly"]
    assert verdicts[1]["supersedes_id"] == verdicts[0]["id"] and verdicts[2]["supersedes_id"] == verdicts[1]["id"]
    assert repo.get_reader_authored_question(row["id"])["self_check"] == "partly"
    # The ledger keeps hashes and ids only, never the learner's words.
    with repo.connection() as connection:
        dumped = json.dumps([dict(r) for r in connection.execute("SELECT * FROM judgment_ledger")])
    assert "Symmetric." not in dumped


def test_the_self_check_and_its_ledger_row_commit_together(tmp_path, monkeypatch):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    row = RQC.author_inquiry_quick_check(repo, FakeClient(), extraction_id="ext1",
                                         inquiry_root_event_id=root["reader_answer_event_id"],
                                         anchor_span_ids=["s1"], clock=_CLOCK)
    RQC.record_inquiry_action(repo, question_id=row["id"], action="answered", response_md="Symmetric.", clock=_CLOCK)

    def refuse(*_args, **_kwargs):
        raise sqlite3.OperationalError("the ledger is unavailable")

    monkeypatch.setattr(RQC, "append_judgment", refuse)
    with pytest.raises(sqlite3.OperationalError):
        RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="no", clock=_CLOCK)
    assert repo.get_reader_authored_question(row["id"])["self_check"] is None
    assert _self_check_verdicts(repo, row["id"]) == []


# -- reconnect --------------------------------------------------------------------

def test_reconnect_yes_resolves_the_root_as_a_self_report(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Why weighted by p?")
    child = _ask(vault, repo, "Coin flip?", root["reader_answer_event_id"])
    before = table_counts(repo)
    result = RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=child["reader_answer_event_id"],
                                 answer="yes", via="inline", clock=_CLOCK)
    assert result["resolution"] == "resolved"
    assert repo.question_event(root["event_id"])["resolution"] == "resolved"
    (answered,) = _events(repo, "reconnect_answered")
    assert answered["payload"]["answer"] == "yes" and answered["payload"]["via"] == "inline"
    assert answered["payload"]["root_exchange_id"] == root["reader_answer_event_id"]
    (status,) = _events(repo, "inquiry_status_set")
    assert status["payload"]["trigger"] == "reconnect"
    assert table_counts(repo) == before


def test_reconnect_still_unclear_only_records_the_answer(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    result = RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                                 answer="still_unclear", via="rail", clock=_CLOCK)
    assert result["resolution"] == "open"
    assert _events(repo, "inquiry_status_set") == []
    assert [e["payload"]["answer"] for e in _events(repo, "reconnect_answered")] == ["still_unclear"]


def test_reconnect_refuses_unknown_answers(tmp_path):
    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root")
    with pytest.raises(RI.InquiryError):
        RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                            answer="maybe", via="rail", clock=_CLOCK)
    with pytest.raises(RI.InquiryError):
        RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                            answer="yes", via="popup", clock=_CLOCK)


def test_quick_check_job_authors_the_inquiry_row(tmp_path):
    from learnloop.content.pipeline.jobs import handle_reader_quick_check

    vault, repo = _setup(tmp_path)
    root = _ask(vault, repo, "Root", selection_span_ids=["s1", "s2"], selection_quote_md="A^T = A")
    client = FakeClient()
    ctx = SimpleNamespace(
        payload={"extraction_id": "ext1", "scope_kind": "inquiry",
                 "inquiry_root_event_id": root["reader_answer_event_id"], "anchor_span_ids": ["s1", "s2"]},
        repo=repo, clock=_CLOCK, report=lambda *a, **k: None, vault_root=vault.root,
        job={"id": "ijob_1"}, cancelled=lambda: False,
        services=SimpleNamespace(quick_check_client=lambda ctx: client),
    )
    first = handle_reader_quick_check(ctx)
    again = handle_reader_quick_check(ctx)
    assert first["deduplicated"] is False and again == {"question_id": first["question_id"], "deduplicated": True}
    row = repo.get_reader_authored_question(first["question_id"])
    assert row["scope_kind"] == "inquiry"
    assert json.loads(row["anchor_span_ids_json"]) == ["s1", "s2"]


def test_reconnect_rpcs_round_trip(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import reader

    root_dir = _rpc_setup(tmp_path)
    client = RD.StubReaderClient()
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), client))
    queued: list[dict] = []
    monkeypatch.setattr(reader, "ready_canonical_ingest_provider", lambda vault: ("stub", SimpleNamespace(ready=True), object()), raising=False)

    def enqueue(self, **payload):
        queued.append(payload)
        return "batch_1"

    from learnloop.content.pipeline.jobs import DurableIngestJobs
    monkeypatch.setattr(DurableIngestJobs, "enqueue_reader_inquiry_check", enqueue, raising=False)
    asked = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask",
                                    "params": {"extractionId": "ext1", "spanId": "s1", "question": "Root"}}])[1]["result"]
    exchange = asked["readerAnswerEventId"]
    responses = _rpc([
        _init(root_dir),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.reconnect_answer",
         "params": {"extractionId": "ext1", "exchangeId": exchange, "answer": "quick_check", "via": "rail"}},
        {"jsonrpc": "2.0", "id": 3, "method": "reader.inquiry_question",
         "params": {"extractionId": "ext1", "exchangeId": exchange}},
        {"jsonrpc": "2.0", "id": 4, "method": "reader.reconnect_answer",
         "params": {"extractionId": "ext1", "exchangeId": exchange, "answer": "yes", "via": "inline"}},
    ])
    quick, pending, yes = (r["result"] for r in responses[1:])
    assert quick["status"] == "queued" and quick["question"] is None
    assert queued == [{"extraction_id": "ext1", "inquiry_root_event_id": exchange, "anchor_span_ids": ["s1"]}]
    assert pending == {"version": pending["version"], "question": None}
    assert yes["resolution"] == "resolved"


def test_inquiry_question_action_rpc_records_the_self_check(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import reader

    root_dir = _rpc_setup(tmp_path)
    client = RD.StubReaderClient()
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), client))
    asked = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask",
                                    "params": {"extractionId": "ext1", "spanId": "s1", "question": "Root"}}])[1]["result"]
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths
    loaded = load_vault(root_dir)
    repo = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    row = RQC.author_inquiry_quick_check(repo, FakeClient(), extraction_id="ext1",
                                         inquiry_root_event_id=asked["readerAnswerEventId"],
                                         anchor_span_ids=["s1"], clock=_CLOCK)
    responses = _rpc([
        _init(root_dir),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.inquiry_question",
         "params": {"extractionId": "ext1", "exchangeId": asked["readerAnswerEventId"]}},
        {"jsonrpc": "2.0", "id": 3, "method": "reader.inquiry_question_action",
         "params": {"questionId": row["id"], "action": "answered", "response": "Symmetric."}},
        {"jsonrpc": "2.0", "id": 4, "method": "reader.inquiry_question_action",
         "params": {"questionId": row["id"], "action": "self_checked", "selfCheck": "matches"}},
    ])
    found, answered, checked = (r["result"]["question"] for r in responses[1:])
    assert found["id"] == row["id"] and found["scopeKind"] == "inquiry"
    assert found["status"] == "proposed" and found["selfCheck"] is None
    assert answered["status"] == "answered"
    assert checked["selfCheck"] == "matches"


def test_the_quick_check_read_reports_its_durable_jobs_state(tmp_path, monkeypatch):
    """Codex review F4: the Reader polls the job it queued, so a failed,
    capped or unreachable check says so instead of waiting forever."""
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths
    from learnloop_sidecar.handlers import reader

    root_dir = _rpc_setup(tmp_path)
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), RD.StubReaderClient()))
    asked = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask",
                                    "params": {"extractionId": "ext1", "spanId": "s1", "question": "Root"}}])[1]["result"]
    exchange = asked["readerAnswerEventId"]
    loaded = load_vault(root_dir)
    repo = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    jobs = DurableIngestJobs()
    jobs.bind(repo, loaded.root, background=False)
    jobs._ensure_worker = lambda: None
    batch = jobs.enqueue_reader_inquiry_check(extraction_id="ext1", inquiry_root_event_id=exchange, anchor_span_ids=["s1"])
    other = jobs.enqueue_reader_inquiry_check(extraction_id="ext1", inquiry_root_event_id="another_root", anchor_span_ids=["s1"])

    def read(batch_id):
        return _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.inquiry_question",
                                       "params": {"extractionId": "ext1", "exchangeId": exchange, "batchId": batch_id}}])[1]["result"]

    queued = read(batch)
    assert queued["question"] is None and queued["job"] == {"status": "queued", "errorCode": None, "message": None}
    (job,) = repo.ingest_jobs_for_batch(batch)
    repo.transition_unleased_ingest_job(job["id"], status="failed", phase="failed", message="Today's quick checks (100) are used.",
                                        error={"code": "capped", "message": "Today's quick checks (100) are used."})
    failed = read(batch)["job"]
    assert failed["status"] == "failed" and failed["errorCode"] == "capped"
    # Another inquiry's job is never reported here.
    assert read(other)["job"] is None
    # Without a batch the read is as before.
    plain = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.inquiry_question",
                                    "params": {"extractionId": "ext1", "exchangeId": exchange}}])[1]["result"]
    assert plain["question"] is None and "job" not in plain


def test_a_landed_inquiry_check_names_its_model_and_prompt_version(tmp_path, monkeypatch):
    """Codex review F8: the funnel reads the quick check per route."""
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths
    from learnloop_sidecar.handlers import reader

    root_dir = _rpc_setup(tmp_path)
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), RD.StubReaderClient()))
    asked = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask",
                                    "params": {"extractionId": "ext1", "spanId": "s1", "question": "Root"}}])[1]["result"]
    loaded = load_vault(root_dir)
    repo = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    RQC.author_inquiry_quick_check(repo, FakeClient(), extraction_id="ext1", inquiry_root_event_id=asked["readerAnswerEventId"],
                                   anchor_span_ids=["s1"], clock=_CLOCK)
    found = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.inquiry_question",
                                    "params": {"extractionId": "ext1", "exchangeId": asked["readerAnswerEventId"]}}])[1]["result"]
    assert found["question"]["model"] == "fake-model"
    assert found["question"]["promptVersion"] == RQC.INQUIRY_PROMPT_VERSION


def test_reconnect_rpcs_are_absent_with_the_switch_off(tmp_path):
    root_dir = _rpc_setup(tmp_path)
    append_config_toml(root_dir, """
    [reader_inquiry]
    enabled = false
    """)
    responses = _rpc([
        _init(root_dir),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.reconnect_answer",
         "params": {"extractionId": "ext1", "exchangeId": "x", "answer": "yes", "via": "rail"}},
        {"jsonrpc": "2.0", "id": 3, "method": "reader.inquiry_question",
         "params": {"extractionId": "ext1", "exchangeId": "x"}},
        {"jsonrpc": "2.0", "id": 4, "method": "reader.inquiry_question_action",
         "params": {"questionId": "x", "action": "dismissed"}},
    ])
    assert all(r["error"]["data"]["code"] == "inquiry_disabled" for r in responses[1:])


@pytest.mark.parametrize("source", ["transcript", "notes"])
def test_reconnect_and_its_check_on_every_source_kind(tmp_path, source):
    vault, repo = _setup(tmp_path)
    fixture = transcript_source(repo) if source == "transcript" else notes_source(repo)
    vault = load_vault(vault.root)
    root = _ask(vault, repo, "Why?", extraction_id=fixture["extraction_id"], span_id=fixture["span_id"])
    row = RQC.author_inquiry_quick_check(
        repo, FakeClient(span_ids=[fixture["span_id"]]), extraction_id=fixture["extraction_id"],
        inquiry_root_event_id=root["reader_answer_event_id"], anchor_span_ids=[fixture["span_id"]], clock=_CLOCK,
    )
    assert row["scope_kind"] == "inquiry"
    result = RI.answer_reconnect(repo, extraction_id=fixture["extraction_id"],
                                 exchange_id=root["reader_answer_event_id"], answer="yes", via="inline",
                                 clock=_CLOCK)
    assert result["resolution"] == "resolved"


@pytest.mark.durability
def test_migration_189_and_the_inquiry_check_under_production_sqlite(tmp_path):
    """Durability lane: a fresh vault under WAL + synchronous=FULL applies
    migration 189, and a scoped row lands beside its section's row without
    shadowing it; the reconnect status flip commits."""

    vault, repo = _setup(tmp_path)
    with repo.connection() as connection:
        mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        assert {row[1] for row in connection.execute("PRAGMA table_info(reader_authored_questions)")} >= {
            "scope_kind", "question_style", "anchor_span_ids_json", "inquiry_root_event_id", "self_check",
        }
    assert str(mode).lower() == "wal"
    section = RQC.author_quick_check(repo, FakeClient(), extraction_id="ext1", section_id="u1")
    root = _ask(vault, repo, "Root")
    inquiry = RQC.author_inquiry_quick_check(
        repo, FakeClient(), extraction_id="ext1", inquiry_root_event_id=root["reader_answer_event_id"],
        anchor_span_ids=["s1"], clock=_CLOCK,
    )
    assert repo.latest_reader_authored_question(extraction_id="ext1", section_id="u1")["id"] == section["id"]
    assert inquiry["scope_kind"] == "inquiry"
    RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                        answer="yes", via="rail", clock=_CLOCK)
    assert repo.question_event(root["event_id"])["resolution"] == "resolved"
