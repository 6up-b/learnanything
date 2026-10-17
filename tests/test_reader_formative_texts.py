"""RW1b's missed answers as learner text (spec_reader_workbench_v1 §4.2, §3.4 item 13; G36).

A next-step, why-step or assumption answer the learner marks *partly* or *no*
becomes one ``reader_formative`` learner text, read by learner-text gaps'
reader with its own task; a match, a "show me" with no answer, and either
switch off queue nothing. Reading it writes only learner-text gap rows,
their jobs, ledger rows and receipts: no attempt, evidence, mastery,
certification, coldness, FSRS state or probe observation (W1's tiers). The
``ReaderObservationV1`` record RW6a reads gains the gaps named from it.

Every model is a fake.
"""

from __future__ import annotations


import pytest

from learnloop.clock import FrozenClock
from learnloop.diagnosis.text_gaps.contract import READER_FORMATIVE_PROMPT_VERSION
from learnloop.diagnosis.text_gaps.jobs import enqueue_reader_formative, process_next_gap_job
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.diagnosis.text_gaps.sources import learner_text
from learnloop.reader import reader_observations as RO
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingActiveCheck
from learnloop.reader.reader_sessions import ReaderSession
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef
from tests.helpers import NOW, append_config_toml
from tests.recap_fixtures import call, context, table_counts
from tests.test_reader_active_reading import EVIDENCE_TABLES, ActiveClient
from tests.test_reader_guidance import _setup
from tests.text_gap_fakes import GapLLMFake

CLOCK = FrozenClock(NOW)
GAP_TABLES = {"learner_text_gaps", "learner_text_gap_jobs", "judgment_ledger", "model_call_receipts",
              "text_write_provenance", "interaction_events", "judgment_work_claims"}


def _missed(repo, *, check="partly", answer="U and V are just invertible", style="next_step", spans=("s1",)):
    client = ActiveClient() if style == "next_step" else ActiveClient(ReadingActiveCheck(
        question_md="Why does this step hold?", expected_answer_md="Because the factors are orthogonal.",
        span_ids=list(spans)))
    row = RQC.author_selection_question(repo, client, extraction_id="ext1", anchor_span_ids=list(spans),
                                        style=style, clock=CLOCK, owner="job_f")
    RQC.record_selection_action(repo, question_id=row["id"], action="answered", response_md=answer, clock=CLOCK)
    return RQC.record_selection_action(repo, question_id=row["id"], action="self_checked", self_check=check,
                                       clock=CLOCK)


def _jobs(repo):
    with repo.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_kind, source_id, state FROM learner_text_gap_jobs ORDER BY created_at")]


def test_a_missed_answer_is_queued_and_a_match_is_not(tmp_path):
    vault, repo = _setup(tmp_path)
    missed = _missed(repo)
    assert enqueue_reader_formative(vault, repo, question_id=missed["id"], clock=CLOCK)
    assert _jobs(repo) == [("reader_formative", missed["id"], "queued")]
    # Idempotent per question.
    assert enqueue_reader_formative(vault, repo, question_id=missed["id"], clock=CLOCK) is None
    matched = _missed(repo, check="matches", style="why_step")
    assert enqueue_reader_formative(vault, repo, question_id=matched["id"], clock=CLOCK) is None
    assert len(_jobs(repo)) == 1


def test_show_me_with_no_answer_queues_nothing(tmp_path):
    vault, repo = _setup(tmp_path)
    row = RQC.author_selection_question(repo, ActiveClient(), extraction_id="ext1", anchor_span_ids=["s1"],
                                        style="next_step", clock=CLOCK, owner="job_s")
    RQC.record_selection_action(repo, question_id=row["id"], action="answered", clock=CLOCK)
    done = RQC.record_selection_action(repo, question_id=row["id"], action="self_checked", self_check="no",
                                       clock=CLOCK)
    assert enqueue_reader_formative(vault, repo, question_id=done["id"], clock=CLOCK) is None
    assert _jobs(repo) == []


@pytest.mark.parametrize("toml", ["\n[reader_formative]\nenabled = false\n", "\n[learner_text_gaps]\nenabled = false\n"])
def test_either_switch_off_queues_nothing(tmp_path, toml):
    vault, repo = _setup(tmp_path)
    append_config_toml(vault.root, toml)
    missed = _missed(repo)
    assert enqueue_reader_formative(load_vault(vault.root), repo, question_id=missed["id"], clock=CLOCK) is None
    assert _jobs(repo) == []


def test_the_sidecars_self_check_queues_the_text_and_wakes_the_worker(tmp_path, monkeypatch):
    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    woken: list = []
    monkeypatch.setattr(ctx.post_attempt_worker, "notify", lambda: woken.append(True))
    _v, repo = ctx.require_vault()
    row = RQC.author_selection_question(repo, ActiveClient(), extraction_id="ext1", anchor_span_ids=["s1"],
                                        style="next_step", clock=CLOCK, owner="job_x")
    call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "answered",
                                                "response": "U is diagonal"})
    result = call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "self_checked",
                                                         "selfCheck": "no"})
    assert result["formativeJobId"] and woken == [True] and result["question"]["missed"] is True


def _linked_vault(root):
    vault = load_vault(root)
    vault.learning_objects["lo_svd_definition"].provenance.source_refs = [
        SourceRef(ref_type="canonical_source", ref_id="src1", locator="span:ext1/s1", source_id="src1",
                  extraction_id="ext1"),
    ]
    return vault


def test_the_dispatcher_reads_the_answer_with_its_question_passage_and_expected_answer(tmp_path):
    vault, repo = _setup(tmp_path)
    missed = _missed(repo)
    text = learner_text(_linked_vault(vault.root), repo, "reader_formative", missed["id"])
    assert (text.source_kind, text.context_judge, text.text) == ("reader_formative", "gap_reader",
                                                                 "U and V are just invertible")
    assert text.context["expected_answer"] == "The columns of U and V are orthonormal."
    assert text.context["expected_answer_from"] == "the book" and text.context["self_check"] == "partly"
    assert "singular value decomposition" in text.context["passage"].lower()
    assert text.anchor_learning_object_ids == ("lo_svd_definition",)
    assert text.attempt_id is None and text.practice_item_id is None
    # workbench_text is admitted by the schema for RW2b; nothing reads it yet.
    assert learner_text(vault, repo, "workbench_text", "anything") is None


def test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis(tmp_path):
    vault, repo = _setup(tmp_path)
    missed = _missed(repo)
    assert enqueue_reader_formative(vault, repo, question_id=missed["id"], clock=CLOCK)
    llm = GapLLMFake(reading=LearnerGap(kind="wording", prerequisite_name=None, prerequisite_line=None))
    clients = PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, tutor=None,
                              embedder=None)
    before = table_counts(repo)
    outcome = process_next_gap_job(vault.root, repo, owner="t", clients=clients, clock=CLOCK)
    assert outcome.state == "done" and outcome.source_kind == "reader_formative"
    after = table_counts(repo)
    changed = {name for name in after if after[name] != before.get(name)}
    assert changed <= GAP_TABLES, changed
    for table in EVIDENCE_TABLES:
        assert after.get(table, 0) == before.get(table, 0)
    with repo.connection() as connection:
        gap = dict(connection.execute("SELECT * FROM learner_text_gaps").fetchone())
    assert (gap["source_kind"], gap["source_id"], gap["context_judge"], gap["kind"]) == (
        "reader_formative", missed["id"], "gap_reader", "wording")
    # Read with its own task: the reader was told it reads a missed active-reading answer.
    reading_prompts = [payload for purpose, payload in llm.calls if purpose == "learner_gap_reading"]
    assert reading_prompts and "while reading a book" in str(reading_prompts[0])
    with repo.connection() as connection:
        version = connection.execute(
            "SELECT prompt_version FROM judgment_ledger WHERE task = 'learner_gap_reading' OR prompt_version = ?",
            (READER_FORMATIVE_PROMPT_VERSION,)).fetchall()
    assert any(row[0] == READER_FORMATIVE_PROMPT_VERSION for row in version)
    session = ReaderSession("ext1", ("v1",), "2000-01-01T00:00:00Z", "2100-01-01T00:00:00Z")
    (record,) = RO.formative_answer_observations(repo, extraction_id="ext1", session=session)
    assert (record.kind, record.hypotheses, record.authority) == ("next_step_missed", (gap["id"],), "routing_only")


def test_the_widened_kinds_reach_the_salience_firewall_unchanged():
    """Neither new source kind is an evidence input: the firewall's reading
    kinds are untouched, and no evidence writer imports the reader's modules."""

    from learnloop.diagnosis.text_gaps.contract import READABLE_SOURCE_KINDS, SOURCE_KINDS

    assert {"reader_formative", "workbench_text"} <= set(SOURCE_KINDS)
    assert "workbench_text" not in READABLE_SOURCE_KINDS
