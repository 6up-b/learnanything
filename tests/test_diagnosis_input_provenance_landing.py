"""Diagnosis input provenance landed on main with its release switch OFF
(docs/reviews/diagnosis-input-provenance.md, "Landing onto main").

The owner chose "land narrow, then fix source": the recording infrastructure
lands (every writer of model-written text records what it read, the C4
receipt inside the grading transaction, regrade lineage, question contracts),
but the final verify reopened two High findings in the release path:

* **F2**: the stuck-answer gap reader's ``reading_record`` folds topic
  records without checking the titles it showed;
* **F3**: C4 history dependencies escape grading validation (a legacy joint
  grading's receipt names a history attempt the freeze never checks).

So ``diagnosis.chat_shows_recorded_text`` defaults off: chat's read model is
C1a's narrow rule exactly (every model-written text held back), and the
writers still record. With the switch on, the branch's release behaviour
holds. The reopened reproductions stay withheld with the switch off; with it
on they are released today, which the follow-up ("one context capture
point") fixes, so their switch-on cases are strict xfails.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import anyio
import pytest
from mcp import Client

from learnloop import learner_protection as protection
from learnloop.config.schema import LearnLoopConfig
from learnloop.content.sources import exam_material as EM
from learnloop.learner_context import (
    HELD_BACK,
    ContextLimits,
    RecordedText,
    default_provenance,
    learning_context,
    no_write_provenance,
    recorded_write_provenance,
)
from learnloop.remote.runtime import RemoteRuntime
from learnloop.vault.loader import load_vault
from learnloop_mcp.server import build_server
from tests.diagnosis_split_helpers import at
from tests.helpers import NOW_ISO
from tests.mcp_world import LO, PEER, PEER_ANSWER, c4_receipt, generated_world, payload_text, pinned_answer
from tests.split_live_helpers import drain_jobs, split_vault, submit
from tests.test_diagnosis_input_provenance import (
    SVD_RIGHT,
    SVD_WRONG,
    ProvenanceFake,
    _belief,
    _diagnose,
    _dp,
    _misconception_from,
    _own_reads,
    _record_drafted,
    _rows,
    _solve_pi_own,
    _trace,
    _wp,
    world,  # noqa: F401 -- a fixture
)
from tests.test_reread_safety_landing import _protect_the_first_reading, reread_world  # noqa: F401 -- a fixture

SUMMARY = "The learner drops the sign of a cofactor."
STATEMENT = "Thinks the sign of a cofactor never changes"
MOMENT = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
ALIAS_KEY = b"landing-alias-key"


def _switch_on(root) -> None:
    """The owner turns the release on (``learnloop.toml``)."""

    config = root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n[diagnosis]\nchat_shows_recorded_text = true\n",
                      encoding="utf-8")


def _read(root, repository, **kwargs: Any) -> dict[str, Any]:
    """The read model as the vault's configuration has it (no override)."""

    return learning_context(load_vault(root), repository, limits=ContextLimits(traces=40), now=MOMENT,
                            alias_key=ALIAS_KEY, **kwargs)


def _chat_context(root) -> dict[str, Any]:
    """Chat's ``learning_context`` tool, through the MCP server on a fresh attach."""

    server = build_server(RemoteRuntime.attach(root, load_environment=False))

    async def main():
        async with Client(server) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            result = await client.call_tool("learning_context", {"max_traces": 30})
            return tools["learning_context"].description, result.structured_content

    description, payload = anyio.run(main)
    return {"description": description, "payload": payload}


def _recorded_safe_texts(world) -> None:
    """A diagnosis and a belief written from the learner's own pinned answer,
    each recording what it read; the question is answered since (its attempt
    window closed), so rule (c) can release both."""

    diagnosis = _diagnose(world, "dg_landing", SUMMARY, _own_reads())
    _misconception_from(world, "mc_landing", STATEMENT, attempt_id="att_own", diagnosis_id=diagnosis)
    _solve_pi_own(world)


# -- the default ----------------------------------------------------------------------------


def test_the_release_switch_defaults_off_and_the_default_source_is_the_narrow_rule(world):
    assert LearnLoopConfig().diagnosis.chat_shows_recorded_text is False
    vault = load_vault(world.root)
    assert vault.config.diagnosis.chat_shows_recorded_text is False
    assert default_provenance(vault) is no_write_provenance
    # A configuration that cannot be read never releases.
    assert default_provenance(SimpleNamespace(config=None)) is no_write_provenance
    _switch_on(world.root)
    assert default_provenance(load_vault(world.root)) is recorded_write_provenance


# -- switch off: recorded, safe, still withheld ----------------------------------------------


def test_off_a_fully_recorded_safe_text_is_withheld_in_chat_and_the_writers_still_record(world):
    """Off (the default): a diagnosis summary and a belief whose records are
    complete and whose every input is safe are held back in chat's
    ``learning_context`` exactly as C1a held them back, and the records are
    written all the same. On: the branch's rule (c) releases both."""

    _recorded_safe_texts(world)
    rows = {(row["kind"], row["record_id"]): row for row in _rows(world.repository)}
    assert rows[("diagnosis", "dg_landing")]["complete"] == 1
    assert rows[("misconception", "mc_landing")]["complete"] == 1

    chat = _chat_context(world.root)
    payload = chat["payload"]
    trace = _trace(payload, "att_own")
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == HELD_BACK
    belief = _belief(payload, "mc_landing")
    assert belief["statement"] is None and belief["statement_note"] == HELD_BACK
    assert SUMMARY not in payload_text(payload) and STATEMENT not in payload_text(payload)
    # The tool says what C1a said: model-written wording is held back.
    assert "is held back for now" in chat["description"]

    # Field for field the C1a narrow rule: the same payload as reading with no
    # write-time record at all, although the records exist.
    off = _read(world.root, world.repository)
    narrow = _read(world.root, world.repository, provenance=no_write_provenance)
    assert json.dumps(off, sort_keys=True, default=str) == json.dumps(narrow, sort_keys=True, default=str)

    _switch_on(world.root)
    payload = _chat_context(world.root)["payload"]
    trace = _trace(payload, "att_own")
    assert trace["diagnosis"]["summary"] == SUMMARY
    assert _belief(payload, "mc_landing")["statement"] == STATEMENT
    on = _read(world.root, world.repository)
    assert isinstance(_trace(on, "att_own")["diagnosis"]["summary"], RecordedText)


def test_off_the_live_pipeline_records_and_chat_withholds_until_the_switch_is_on(tmp_path):
    """The real door: the blind grade, the diagnosis and the hypothesis it
    materializes each record what they read (complete) with the switch off;
    the summary and the cause stay held back in chat, after the question is
    answered too. On, they are shown (the branch's behaviour)."""

    paths, vault, repository = split_vault(tmp_path, seed=False)
    assert vault.config.diagnosis.chat_shows_recorded_text is False
    client = ProvenanceFake()
    wrong = submit(vault, repository, client, answer=SVD_WRONG, when=at(1))
    drain_jobs(vault, repository, client)
    submit(vault, repository, client, answer=SVD_RIGHT, when=at(2))

    kinds = {(row["kind"], row["writer"]): row for row in _rows(repository)}
    assert {("grading", "blind_grader"), ("diagnosis", "diagnoser"), ("hypothesis", "causal_materialization")} \
        <= set(kinds)
    assert all(row["complete"] == 1 for row in kinds.values())

    held = _read(paths.root, repository)
    trace = _trace(held, wrong.attempt_id)
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == HELD_BACK
    causes = [entry for entry in held["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert causes and all(entry["statement"] is None and entry["statement_note"] == HELD_BACK for entry in causes)

    _switch_on(paths.root)
    shown = _read(paths.root, repository)
    assert _trace(shown, wrong.attempt_id)["diagnosis"]["summary"] == client.analysis
    (cause,) = [entry for entry in shown["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert cause["statement"] == "The answer goes wrong because the learner misapplies the rule."


# -- the reopened findings: withheld with the switch off ---------------------------------------

#: The final verify's two reopened findings (scratchpad provenance-final-verify.md).
F2_REASON = ("final verify F2 (reopened): the stuck-answer gap reader's reading_record folds a generated "
             "topic's record without checking the title it showed; fixed by the one-capture-point follow-up")
F3_REASON = ("final verify F3 (reopened): a legacy joint grading's C4 history attempt escapes the freeze's "
             "grading validation; fixed by the one-capture-point follow-up")
RENAMED = "Parity, renamed by a writer that recorded nothing"


def _f2_belief_from_a_renamed_topic(world) -> str:
    """F2's reproduction. A generated topic's drafter recorded its safe
    title; a writer that records nothing renames it; a stuck answer on it is
    read with the new title in its context (``sources.stuck_answer_text``),
    and the gap reader's belief statement repeats that title. Returns the
    candidate's id."""

    from learnloop.diagnosis.text_gaps.actions import record_belief
    from learnloop.diagnosis.text_gaps.contract import LearnerText
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    safe = generated_world(world)["safe"]
    _record_drafted(world, safe, "att_own", "pi_own")
    path = world.paths.learning_object_path("linear-algebra", safe)
    lo = read_yaml(path)
    lo["title"] = RENAMED
    write_yaml(path, lo)
    vault = load_vault(world.root)
    text = LearnerText(source_kind="stuck_answer", source_id="att_own", text="stuck", context_judge="gap_reader",
                       created_at=NOW_ISO, subject_id="linear-algebra", anchor_learning_object_ids=(safe,),
                       practice_item_id="pi_own", attempt_id="att_own",
                       context={"surface": "stuck_answer", "learning_objects": [RENAMED]})
    outcome = record_belief(vault, world.repository, text=text, statement=f"Thinks {RENAMED} needs no sign rule",
                            matched=None)
    with world.repository.atomic():
        for write in outcome.writes:
            write()
    return str(outcome.target_id)


def _candidate(context: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    return next(entry for entry in context["misconception_candidates"] if entry["candidate_id"] == candidate_id)


def test_off_f2_a_belief_from_a_renamed_generated_topic_is_withheld(world):
    candidate_id = _f2_belief_from_a_renamed_topic(world)
    _solve_pi_own(world)
    with world.repository.connection() as connection:
        stored = _wp().stored_record(connection, "candidate", candidate_id)
    # The defect the verify reopened: the record claims it is complete.
    assert stored is not None and stored.record.complete
    entry = _candidate(_read(world.root, world.repository), candidate_id)
    assert entry["statement"] is None and entry["statement_note"] == HELD_BACK


@pytest.mark.xfail(strict=True, reason=F2_REASON)
def test_on_f2_a_belief_from_a_renamed_generated_topic_is_withheld(world):
    candidate_id = _f2_belief_from_a_renamed_topic(world)
    _solve_pi_own(world)
    _switch_on(world.root)
    entry = _candidate(_read(world.root, world.repository), candidate_id)
    assert entry["statement"] is None


def _f3_summary_over_a_c4_history_regraded_before_the_freeze(world) -> str:
    """F3's reproduction. ``PEER`` (A) is a legacy joint model grading with
    no record and a C4 receipt naming ``att_b`` (B). The history store's
    grading marks are captured while B pins ``acv_own``; before the freeze
    B's evidence is replaced by evidence pinning ``acv_own_v2`` with its
    grading record. The diagnosis of ``att_own`` shown A is frozen and
    persisted as the job persists it. Returns the diagnosis id."""

    from learnloop.diagnosis.split.jobs import record_diagnosis_reads
    from learnloop.diagnosis.split.provenance import frozen_record

    pinned_answer(world, PEER, PEER_ANSWER, "2026-09-21T09:00:00Z")
    pinned_answer(world, "att_b", "B_WORDS_3307 the cofactor sign alternates", "2026-09-20T09:00:00Z")
    with world.repository.connection() as connection:
        connection.execute("UPDATE grading_evidence SET agent_run_id = 'run_joint_peer' WHERE attempt_id = ?",
                           (PEER,))
        c4_receipt(connection, PEER, ["att_b"])
        connection.commit()
    with world.repository.connection() as connection:
        shown = _wp().grading_marks(connection)
    store = SimpleNamespace(repository=world.repository, grading_marks=lambda: dict(shown))
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES ('acv_own_v2', 'pi_own', 'h_own_v2', ?, 1, ?)",
            (json.dumps({"prompt": "PINNED_PROMPT_V2 explain cofactor expansion", "expected_answer": "V2 KEY"}),
             NOW_ISO))
        connection.execute("UPDATE grading_evidence SET superseded_at = ? WHERE attempt_id = 'att_b'", (NOW_ISO,))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES ('ge_att_b_v2', 'att_b', 'correct', 0, 1, ?, 'acv_own_v2')",
            (NOW_ISO,))
        connection.commit()
    with world.repository.atomic():
        _wp().record_grading(world.repository.connection(), attempt_id="att_b", writer="blind_grader")
    record = frozen_record(store, _own_reads(shown=(_dp().AttemptRead(PEER, True),)))
    proposal = {"analysis_md": SUMMARY}
    with world.repository.atomic():
        record_diagnosis_reads(world.repository, diagnosis_id="dg_f3", proposal=proposal, record=record)
        world.repository.insert_attempt_diagnosis(
            diagnosis_id="dg_f3", attempt_id="att_own", diagnosis_prompt_version="test", mode="live",
            history_mode="full", status="completed", proposal=proposal, causal_view=None, validation_report=None,
            receipt=None)
    return "dg_f3"


def test_off_f3_a_summary_over_a_regraded_c4_history_attempt_is_withheld(world):
    _f3_summary_over_a_c4_history_regraded_before_the_freeze(world)
    _solve_pi_own(world)
    (row,) = [row for row in _rows(world.repository, "diagnosis") if row["record_id"] == "dg_f3"]
    # The defect the verify reopened: complete, with B's new contract.
    assert row["complete"] == 1
    assert json.loads(row["inputs_json"])["answers"]["att_b"] == ["acv_own_v2"]
    trace = _trace(_read(world.root, world.repository), "att_own")
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == HELD_BACK


@pytest.mark.xfail(strict=True, reason=F3_REASON)
def test_on_f3_a_summary_over_a_regraded_c4_history_attempt_is_withheld(world):
    _f3_summary_over_a_c4_history_regraded_before_the_freeze(world)
    _solve_pi_own(world)
    _switch_on(world.root)
    trace = _trace(_read(world.root, world.repository), "att_own")
    assert trace["diagnosis"]["summary"] is None


def test_the_reproductions_hold_no_name_or_key_with_the_switch_off(world):
    """Off, the renamed topic's name, the F3 summary and either statement
    never reach chat's payload."""

    candidate_id = _f2_belief_from_a_renamed_topic(world)
    _f3_summary_over_a_c4_history_regraded_before_the_freeze(world)
    _solve_pi_own(world)
    payload = _chat_context(world.root)["payload"]
    text = payload_text(payload)
    assert RENAMED not in text and SUMMARY not in text
    assert _candidate(payload, candidate_id)["statement"] is None


# -- compositions with main ---------------------------------------------------------------------


def test_rule_4_and_identity_bound_marks_reach_rule_c_through_learner_protection(reread_world):
    """Re-read safety's exam rule 4 and its identity-bound marks flow through
    ``learner_protection`` into rule (c)'s input check. A diagnosis that read
    an answer on an item made from the re-read's own passage, and a
    correction written from that passage, are released (switch on) while the
    book is unprotected; once the owner marks a section of the book's FIRST
    reading (an exact, identity-bound mark), the re-read is held back whole
    (rule 4) and both texts are withheld as exam material. Off, both are held
    back throughout."""

    world, span = reread_world
    _diagnose(world, "dg_reread", "The learner reads the diagonal as the trace.",
              _own_reads(shown=(_dp().AttemptRead("att_reread", False),)))
    passage = {"ref_type": "canonical_source", "ref_id": "src_book", "extraction_id": "ext_book_r2",
               "span_ids": [span]}
    world.repository.insert_misconception(
        id="mc_reread", learning_object_id=LO, statement="Thinks a triangular determinant is its trace",
        correction_statement="Check which entries sit below the main diagonal before expanding.",
        correction_provenance=_wp().WriteRecord(_wp().Inputs.of(topics=[LO], sources=[passage])))
    _solve_pi_own(world)
    with world.repository.connection() as connection:
        record = _wp().stored_record(connection, "diagnosis", "dg_reread").record
    assert record.complete and "pi_reread" in record.inputs.items

    def read() -> tuple[dict[str, Any], dict[str, Any]]:
        context = _read(world.root, world.repository)
        return _trace(context, "att_own")["diagnosis"], _belief(context, "mc_reread")

    summary, belief = read()
    assert summary["summary"] is None and summary["summary_note"] == HELD_BACK
    assert belief["correction"] is None and belief["correction_note"] == HELD_BACK

    _switch_on(world.root)
    summary, belief = read()
    assert summary["summary"] == "The learner reads the diagonal as the trace."
    assert belief["correction"] == "Check which entries sit below the main diagonal before expanding."

    _protect_the_first_reading(world)
    vault = load_vault(world.root)
    assert EM.reading_held_back(vault, world.repository, "ext_book_r2")
    assert protection.withheld_items(vault, world.repository).reason("pi_reread") == protection.WITHHELD_EXAM
    summary, belief = read()
    assert summary["summary"] is None and summary["summary_note"] == f"withheld: {protection.WITHHELD_EXAM}"
    assert belief["correction"] is None and belief["correction_note"] == f"withheld: {protection.WITHHELD_EXAM}"


def test_a_method_explicit_question_records_the_contract_it_was_presented_with(world):
    """Method-explicit items: a question asked mid-attempt records the item's
    contract as presented (Q10, ``snapshot_for_presentation``). That contract
    freezes the required method, and ``answered_prompt`` renders from it the
    question the learner was shown, the method's sentence included. An
    answer graded under it shows that question in chat (rule (a)) whatever
    the switch; the question's words are released only with the switch on."""

    from learnloop.tutor.tutor_qa import _question_contract
    from learnloop.vault.required_method import answered_prompt, method_instruction, presented_prompt
    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from tests.test_diagnosis_input_provenance import _gap, _question

    path = world.paths.practice_item_path("linear-algebra", "pi_own")
    payload = read_yaml(path)
    payload["required_method"] = {"name": "cofactor expansion", "criterion_ids": ["correct"]}
    write_yaml(path, payload)
    vault = load_vault(world.root)
    item = vault.practice_items["pi_own"]
    contract_id = _question_contract(vault, world.repository, item, None)
    assert contract_id
    with world.repository.connection() as connection:
        (frozen,) = connection.execute(
            "SELECT contract_json FROM assessment_contract_versions WHERE id = ?", (contract_id,)).fetchone()
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_method', 'pi_own', ?, 'short_answer', 'independent_attempt', 'METHOD_ANSWER_5150', "
            "0.0, 0, '2026-09-26T09:00:00Z', 'old', 'human', 'desktop_practice')", (LO,))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES ('ge_method', 'att_method', 'correct', 0, 1, ?, ?)",
            (NOW_ISO, contract_id))
        connection.commit()
    contract = json.loads(frozen)
    instruction = method_instruction(item.required_method)
    assert instruction and answered_prompt(item, contract) == presented_prompt(item.prompt, item.required_method)
    assert answered_prompt(item, contract).endswith(instruction)

    gap_id = _question(world, "q_method", context="practice", item="pi_own", contract=contract_id,
                       text="must I expand along the first row?")
    off = _read(world.root, world.repository)
    assert _trace(off, "att_method")["stem"].endswith(instruction)
    assert _gap(off, gap_id)["learner_text"] is None and _gap(off, gap_id)["learner_text_note"] == HELD_BACK
    _switch_on(world.root)
    on = _read(world.root, world.repository)
    assert _trace(on, "att_method")["stem"] == _trace(off, "att_method")["stem"]
    assert _gap(on, gap_id)["learner_text"] == "must I expand along the first row?"


def test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade(tmp_path, monkeypatch):
    """The C4 receipt inside the grading transaction (Q14) composes with the
    coordinated grading paths: a vault an older build wrote (205 not applied)
    is refused by a bare ``Repository(path)``, opened through the coordinator
    (``vault_repository``), and a joint grade on it commits with its receipt
    and its grading record; a receipt that cannot be written rolls the model
    grade back (the door's self-grade commits, with no receipt and no record)."""

    from learnloop.ai.runtime import AIRuntimeReport
    from learnloop.attempts import attempts
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_attempt_with_ai_fallback
    from learnloop.db.connection import connect
    from learnloop.db.migrate import UncoordinatedMigrationError, applied_versions
    from learnloop.db.repositories import Repository
    from learnloop.db.stores.write_provenance import grading_record
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.repository import vault_repository
    from tests.helpers import create_basic_vault
    from tests.test_diagnostic_augmentation import _proposal, _SequenceDiagnostician

    paths = create_basic_vault(tmp_path / "vault")
    with connect(paths.sqlite_path) as connection:
        for trigger in ("text_write_provenance_no_update", "text_write_provenance_no_delete",
                        "error_event_lineage_no_update", "error_event_lineage_no_delete"):
            connection.execute(f"DROP TRIGGER {trigger}")
        connection.execute("DROP TABLE text_write_provenance")
        connection.execute("DROP TABLE error_event_lineage")
        connection.execute("ALTER TABLE question_events DROP COLUMN assessment_contract_version_id")
        connection.execute("DELETE FROM schema_migrations WHERE version = 205")
        connection.commit()
    with pytest.raises(UncoordinatedMigrationError):
        Repository(paths.sqlite_path)
    repository = vault_repository(paths)
    assert 205 in applied_versions(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository)

    def grade(answer: str):
        return complete_attempt_with_ai_fallback(
            vault, repository, AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md=answer),
            SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
            runtime=AIRuntimeReport(status="ready", active_provider="fake", provider_type="openai_chat",
                                    model="fake"),
            ai_client=_SequenceDiagnostician([lambda context: _proposal(context.attempt_id)]),
        )

    graded = grade("A = U Sigma")
    with repository.connection() as connection:
        (receipts,) = connection.execute("SELECT count(*) FROM diagnostic_augmentation_receipts WHERE attempt_id = ?",
                                         (graded.attempt_id,)).fetchone()
        record = grading_record(connection, graded.attempt_id)
        (rows,) = connection.execute("SELECT count(*) FROM text_write_provenance WHERE kind = 'grading' "
                                     "AND record_id = ?", (graded.attempt_id,)).fetchone()
    assert receipts == 1 and rows == 1
    assert record.complete and set(record.inputs.answers) == {graded.attempt_id}

    def fail(*_args: Any, **_kwargs: Any) -> None:
        raise ValueError("interrupted augmentation receipt")

    monkeypatch.setattr(attempts, "_record_diagnostic_augmentation", fail)
    fallback = grade("A = U Sigma V")
    with repository.connection() as connection:
        (model,) = connection.execute(
            "SELECT count(*) FROM grading_evidence WHERE attempt_id = ? AND agent_run_id IS NOT NULL "
            "AND superseded_at IS NULL", (fallback.attempt_id,)).fetchone()
        (receipts,) = connection.execute("SELECT count(*) FROM diagnostic_augmentation_receipts WHERE attempt_id = ?",
                                         (fallback.attempt_id,)).fetchone()
        (rows,) = connection.execute("SELECT count(*) FROM text_write_provenance WHERE kind = 'grading' "
                                     "AND record_id = ?", (fallback.attempt_id,)).fetchone()
    assert (model, receipts, rows) == (0, 0, 0)
