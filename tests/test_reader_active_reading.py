"""RW1b's active reading (spec_reader_workbench_v1 §4.2, §4.3; gates G4, G36).

* Next step, why step, assumptions and reconstruct are selection-scoped rows
  of the quick-check producer: formative, keyed, and never an attempt.
* The next step's expected answer is the book's following block, verbatim;
  a why-step or assumption answer is the book's only when its quote is found
  in the passage, else the model's, labelled so (``answer_basis``).
* The selection reuse key holds (the database keeps it unique); a selection
  row never shadows its section's quick check, and section rows are
  byte-identical.
* Answering, "show me" and the three-way self-check write no attempt, no
  evidence and no projection; the self-check is a ``learner_card`` verdict.
* The producer's job path refuses held-out material before any call, and the
  RPCs refuse with ``reader_active_reading.enabled`` off.

Every model is a fake (``StructuredClientFake``).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.clock import FrozenClock
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingActiveCheck, ReadingQuickCheck
from tests.helpers import NOW, append_config_toml
from tests.recap_fixtures import call, context, table_counts
from tests.structured_ai import StructuredClientFake
from tests.test_reader_guidance import _setup

CLOCK = FrozenClock(NOW)
#: Tables a formative act may write; every other table's count stays put (G36).
FORMATIVE_WRITES = {
    "reader_authored_questions", "judgment_ledger", "judgment_work_claims", "model_call_receipts",
    "interaction_events", "learner_text_gap_jobs", "learner_text_gaps",
}
EVIDENCE_TABLES = ("practice_attempts", "grading_evidence", "facet_recall_state", "facet_capability_evidence",
                   "probe_observations", "fsrs_states")


class ActiveClient(StructuredClientFake):
    provider_name = "fake"
    provider_type = "codex_sdk"
    model = "fake-model"

    def __init__(self, result: ReadingActiveCheck | None = None, *, isolates: bool = True) -> None:
        self.result = result or ReadingActiveCheck(question_md="What comes next after this line?",
                                                   next_step_span_ids=["s2"], span_ids=["s2"])
        self.isolates = isolates
        self.requests: list = []

    def supports(self, capability: str) -> bool:
        return self.isolates if capability == ISOLATED_TURN else capability == STRUCTURED_COMPLETION

    def complete(self, request):
        self.requests.append(request)
        return self.result


def _author(repo, client, *, spans=("s1",), style="next_step"):
    return RQC.author_selection_question(repo, client, extraction_id="ext1", anchor_span_ids=list(spans),
                                         style=style, clock=CLOCK, owner="job_a")


def test_the_next_step_is_the_books_following_block_verbatim(tmp_path):
    vault, repo = _setup(tmp_path)
    client = ActiveClient()
    row = _author(repo, client)
    assert (row["scope_kind"], row["question_style"], row["answer_basis"]) == ("selection", "next_step", "source")
    assert row["expected_answer_md"] == "The columns of U and V are orthonormal."
    assert json.loads(row["anchor_span_ids_json"]) == ["s1"] and json.loads(row["span_ids_json"]) == ["s2"]
    (request,) = client.requests
    assert request.isolated is True
    assert "following" in request.prompt and "next_step" in request.prompt
    assert RQC.folded_span_ids(repo, extraction_id="ext1", anchor_span_ids=["s1"]) == ["s2"]


def test_nothing_after_the_line_means_no_next_step_and_no_call(tmp_path):
    vault, repo = _setup(tmp_path)
    client = ActiveClient()
    with pytest.raises(RQC.ReaderQuickCheckError, match="nothing follows"):
        _author(repo, client, spans=("s2",))
    assert client.requests == []


def test_a_why_step_answer_is_the_books_only_when_its_quote_is_found(tmp_path):
    vault, repo = _setup(tmp_path)
    found = ActiveClient(ReadingActiveCheck(
        question_md="Why are the columns orthonormal here?", source_quote="writes A as U Sigma V transpose",
        expected_answer_md="Because of the decomposition.", span_ids=["s1"]))
    row = _author(repo, found, spans=("s2",), style="why_step")
    assert (row["answer_basis"], row["expected_answer_md"]) == ("source", "writes A as U Sigma V transpose")
    assert json.loads(row["span_ids_json"]) == ["s1"]
    invented = ActiveClient(ReadingActiveCheck(
        question_md="What does this assume?", source_quote="A is a square symmetric matrix",
        expected_answer_md="That A is real; any real matrix has an SVD.", span_ids=["s2"]))
    row = _author(repo, invented, spans=("s2",), style="assumptions")
    assert (row["answer_basis"], row["expected_answer_md"]) == ("model", "That A is real; any real matrix has an SVD.")


def test_a_reconstruction_expects_the_selected_derivation(tmp_path):
    vault, repo = _setup(tmp_path)
    client = ActiveClient(ReadingActiveCheck(question_md="Derive the SVD's form without looking at the book.",
                                             span_ids=["s1"]))
    row = _author(repo, client, spans=("s1", "s2"), style="reconstruct")
    assert row["answer_basis"] == "source"
    assert row["expected_answer_md"] == (
        "The singular value decomposition writes A as U Sigma V transpose.\n\nThe columns of U and V are orthonormal.")


def test_the_selection_reuse_key_holds(tmp_path):
    vault, repo = _setup(tmp_path)
    first = _author(repo, ActiveClient())
    again = ActiveClient()
    assert _author(repo, again)["id"] == first["id"] and again.requests == []
    # Another style on the same selection is its own row; a dismissed row still holds its key.
    why = _author(repo, ActiveClient(ReadingActiveCheck(question_md="Why?", expected_answer_md="Because.",
                                                        span_ids=["s1"])), style="why_step")
    assert why["id"] != first["id"]
    RQC.record_selection_action(repo, question_id=why["id"], action="dismissed", clock=CLOCK)
    assert _author(repo, ActiveClient(), style="why_step")["id"] == why["id"]
    # The database refuses a second row for one key.
    fields = {"extraction_id": "ext1", "section_id": first["section_id"], "question_md": "Q", "expected_answer_md": "A",
              "prompt_version": RQC.SELECTION_PROMPT_VERSION, "scope_kind": "selection", "question_style": "next_step",
              "anchor_span_ids": ["s1"], "answer_basis": "source"}
    assert repo.insert_reader_authored_question(fields=fields, clock=CLOCK) == first["id"]


def test_a_selection_row_never_shadows_its_sections_quick_check(tmp_path):
    vault, repo = _setup(tmp_path)
    row = _author(repo, ActiveClient())
    assert repo.latest_reader_authored_question(extraction_id="ext1", section_id=row["section_id"]) is None


def test_section_quick_checks_are_byte_identical(tmp_path):
    from learnloop_sidecar.handlers.reader import _authored_question_payload

    vault, repo = _setup(tmp_path)
    section = RQC.author_quick_check(repo, type("C", (StructuredClientFake,), {
        "provider_name": "fake", "model": "m",
        "complete": lambda self, request: ReadingQuickCheck(question_md="Q?", expected_answer_md="A.", span_ids=["s1"]),
    })(), extraction_id="ext1", section_id=next(iter(_sections(repo))), clock=CLOCK)
    payload = _authored_question_payload(section)
    assert set(payload) == {"id", "extraction_id", "section_id", "status", "question_md", "expected_answer_md",
                            "span_ids", "practice_item_id", "answered_at"}
    assert section["answer_basis"] is None and section["scope_kind"] == "section"


def _sections(repo):
    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir("ext1"))
    return [row["id"] for row in rows]


def test_answering_and_self_checking_write_no_attempt_or_evidence(tmp_path):
    vault, repo = _setup(tmp_path)
    row = _author(repo, ActiveClient())
    before = table_counts(repo)
    RQC.record_selection_action(repo, question_id=row["id"], action="answered", response_md="U is orthogonal",
                                clock=CLOCK)
    done = RQC.record_selection_action(repo, question_id=row["id"], action="self_checked", self_check="partly",
                                       clock=CLOCK)
    assert (done["status"], done["self_check"], done["response_md"]) == ("answered", "partly", "U is orthogonal")
    after = table_counts(repo)
    changed = {name for name in after if after[name] != before.get(name)}
    assert changed <= FORMATIVE_WRITES
    for table in EVIDENCE_TABLES:
        assert after.get(table, 0) == before.get(table, 0)
    with repo.connection() as connection:
        verdicts = connection.execute(
            "SELECT judge, verdict FROM judgment_ledger WHERE task = ? AND left_id = ?",
            (RQC.SELF_CHECK_TASK, row["id"])).fetchall()
    assert [tuple(v) for v in verdicts] == [("learner_card", "partly")]
    assert RQC.is_missed(done)


def test_show_me_reveals_without_an_answer_and_self_check_needs_the_reveal(tmp_path):
    vault, repo = _setup(tmp_path)
    row = _author(repo, ActiveClient())
    with pytest.raises(RQC.ReaderQuickCheckError, match="before comparing"):
        RQC.record_selection_action(repo, question_id=row["id"], action="self_checked", self_check="no", clock=CLOCK)
    shown = RQC.record_selection_action(repo, question_id=row["id"], action="answered", clock=CLOCK)
    assert shown["status"] == "answered" and shown["response_md"] is None and shown["answered_at"]


def test_the_job_refuses_held_out_material_before_any_call(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs as jobs_module
    from learnloop.content.pipeline.jobs import handle_reader_quick_check
    from learnloop.content.pipeline.runner import IngestRunnerError

    vault, repo = _setup(tmp_path)
    client = ActiveClient()
    monkeypatch.setattr(jobs_module, "_refuse_held_out_reader_material",
                        lambda ctx, ext, spans: (_ for _ in ()).throw(IngestRunnerError("held out", code="exam_material")))
    with pytest.raises(IngestRunnerError) as caught:
        handle_reader_quick_check(_job_ctx(repo, vault, client))
    assert caught.value.code == "exam_material" and client.requests == []


def _job_ctx(repo, vault, client, *, style="next_step", spans=("s1",)):
    return SimpleNamespace(
        payload={"extraction_id": "ext1", "scope_kind": "selection", "question_style": style,
                 "anchor_span_ids": list(spans)},
        repo=repo, clock=CLOCK, report=lambda *a, **k: None, vault_root=vault.root,
        job={"id": "sjob_1", "batch_id": "batch_1", "attempt_count": 1},
        cancelled=lambda: False, bind_interruptible=lambda client: None,
        services=SimpleNamespace(quick_check_client=lambda ctx: client),
    )


def test_the_job_writes_the_question_once(tmp_path):
    from learnloop.content.pipeline.jobs import handle_reader_quick_check

    vault, repo = _setup(tmp_path)
    client = ActiveClient()
    first = handle_reader_quick_check(_job_ctx(repo, vault, client))
    again = handle_reader_quick_check(_job_ctx(repo, vault, client))
    assert first["deduplicated"] is False and again == {"question_id": first["question_id"], "deduplicated": True}
    assert len(client.requests) == 1


def test_the_rpcs_queue_reuse_and_answer(tmp_path, monkeypatch):
    vault, repo = _setup(tmp_path)
    ctx = context(vault.root)
    queued: list = []
    monkeypatch.setattr(ctx.ingest_jobs, "enqueue_reader_selection_check",
                        lambda **kwargs: queued.append(kwargs) or "batch_sel")
    monkeypatch.setattr("learnloop_sidecar.handlers.ai_providers.ready_canonical_ingest_provider",
                        lambda vault: ("fake", SimpleNamespace(ready=True), object()))
    asked = call(ctx, "reader.active_question", {"extractionId": "ext1", "spanIds": ["s1"], "style": "next_step"})
    assert (asked["status"], asked["batchId"], asked["foldedSpanIds"]) == ("queued", "batch_sel", ["s2"])
    assert queued == [{"extraction_id": "ext1", "anchor_span_ids": ["s1"], "question_style": "next_step"}]
    _vault, repo = ctx.require_vault()
    row = _author(repo, ActiveClient())
    status = call(ctx, "reader.active_question_status", {"extractionId": "ext1", "anchorSpanIds": ["s1"],
                                                         "style": "next_step"})
    assert status["question"]["id"] == row["id"] and status["question"]["answerBasis"] == "source"
    reused = call(ctx, "reader.active_question", {"extractionId": "ext1", "spanIds": ["s1"], "style": "next_step"})
    assert reused["status"] == "exists" and len(queued) == 1
    answered = call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "answered",
                                                           "response": "U is orthogonal"})
    assert answered["question"]["responseMd"] == "U is orthogonal"
    last = call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "self_checked",
                                                       "selfCheck": "matches"})
    assert last["question"]["selfCheck"] == "matches" and last["formativeJobId"] is None
    nothing = call(ctx, "reader.active_question", {"extractionId": "ext1", "spanIds": ["s2"], "style": "next_step"})
    assert nothing["status"] == "no_next_step" and nothing["foldedSpanIds"] == []


def test_the_rpcs_refuse_while_active_reading_is_off(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, _repo = _setup(tmp_path)
    append_config_toml(vault.root, "\n[reader_active_reading]\nenabled = false\n")
    ctx = context(vault.root)
    before = table_counts(ctx.require_vault()[1])
    for name, params in (
        ("reader.active_question", {"extractionId": "ext1", "spanIds": ["s1"], "style": "next_step"}),
        ("reader.active_question_status", {"extractionId": "ext1", "anchorSpanIds": ["s1"], "style": "next_step"}),
        ("reader.active_question_action", {"questionId": "raq_x", "action": "dismissed"}),
        ("reader.reconstruct", {"questionId": "raq_x"}),
        ("reader.reconstruct_undo", {"questionId": "raq_x"}),
    ):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "active_reading_disabled"
    assert table_counts(ctx.require_vault()[1]) == before


def test_the_active_reading_events_are_salience_only(tmp_path, monkeypatch):
    from learnloop.attempts import salience_firewall as SF

    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    monkeypatch.setattr(ctx.ingest_jobs, "enqueue_reader_selection_check", lambda **kwargs: "batch_sel")
    monkeypatch.setattr("learnloop_sidecar.handlers.ai_providers.ready_canonical_ingest_provider",
                        lambda vault: ("fake", SimpleNamespace(ready=True), object()))
    call(ctx, "reader.active_question", {"extractionId": "ext1", "spanIds": ["s1"], "style": "why_step"})
    _vault, repo = ctx.require_vault()
    with repo.connection() as connection:
        rows = connection.execute("SELECT kind, payload_json FROM interaction_events").fetchall()
    events = [(kind, json.loads(payload)) for kind, payload in rows]
    requested = [payload for kind, payload in events if payload.get("event") == "active_question_requested"]
    assert requested and requested[0]["authority_class"] == "salience_only" and requested[0]["style"] == "why_step"
    for kind, payload in events:
        with pytest.raises(Exception):
            SF.reject_salience({"kind": kind, "payload": payload})
