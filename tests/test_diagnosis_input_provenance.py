"""Diagnosis input provenance (spec_mcp_frontend_c1 §4.8; owner decision
2026-10-14, "land narrow, then fix source").

Every model-written text the chat frontend withholds carries a write-time
record of what it was written from (``db.stores.write_provenance``), and
``TextGuard`` rule (c) releases it only when the record is complete and every
recorded input passes the shared protection (``learner_protection``).

The first groups replay the C1a narrow stage's last-verify reproductions
(Codex job ``20261014-205718-WNjtvF247``) through the real writers: each text
is still held back when an input it was written from is unsafe, and is
released when every recorded input is safe. On ``499bd3ebd`` nothing records
a write, so every "released" assertion fails there (fail first).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from learnloop.learner_context import (
    HELD_BACK,
    REVISION_UNKNOWN_BEHIND,
    ContextLimits,
    RecordedText,
    learning_context,
)
from learnloop.learner_protection import WITHHELD_EXAM
from learnloop.vault.loader import load_vault
from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at, seed_attempt
from tests.helpers import NOW_ISO
from tests.mcp_world import (
    LEGACY_KEY,
    LO,
    PEER,
    PEER_ANSWER,
    build_world,
    c4_receipt,
    generated_world,
    hold_att_held,
    legacy_answer,
    no_model_calls,
    payload_text,
    pinned_answer,
)
from tests.split_live_helpers import ReadyRuntime, drain_jobs, split_vault, submit

#: The new reasons, spelled out so this module collects on the base commit
#: (fail first: every "released" assertion fails there, on its own).
SOLUTION_OPEN = "withheld: written with the worked solution of a question you can still answer"
QUESTION_UNRECORDED = "withheld: a question it was written from records no question revision"
SVD_ITEM = "pi_svd_compute_001"
SVD_WRONG = "A = U Sigma V wrong"
SVD_RIGHT = "A = U Sigma V^T"


def _wp() -> Any:
    """The write-time records (``db.stores.write_provenance``), imported late."""

    import learnloop.db.stores.write_provenance as module

    return module


def _dp() -> Any:
    """What a diagnosis read (``diagnosis.split.provenance``), imported late."""

    import learnloop.diagnosis.split.provenance as module

    return module


def _context(root: Path, repository: Any, **kwargs: Any) -> dict[str, Any]:
    return learning_context(load_vault(root), repository, limits=ContextLimits(traces=40), **kwargs)


def _trace(context: dict[str, Any], attempt_id: str) -> dict[str, Any]:
    return next(trace for trace in context["recent_answer_traces"] if trace["attempt_id"] == attempt_id)


def _rows(repository: Any, kind: str | None = None) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT kind, record_id, writer, complete, incomplete_reasons_json, inputs_json, derived_from_json "
            "FROM text_write_provenance" + (" WHERE kind = ?" if kind else "") + " ORDER BY created_at, id",
            (kind,) if kind else (),
        ).fetchall()
    return [dict(row) for row in rows]


class ProvenanceFake(ReviewFakeClient):
    """The M1 fake with a chosen summary and, in the snapshot mode, the
    workspace activity the transport reports (``activity(workspace)``)."""

    def __init__(self, *, analysis: str = "The learner keeps the last factor untransposed.",
                 activity: Any = "unset", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.analysis = analysis
        self.activity = activity

    def workspace_activity(self) -> list[str] | None:
        if self.activity == "unset":
            return super().workspace_activity()
        if self.activity is None or not self.workspaces:
            return None
        return list(self.activity(self.workspaces[-1]))

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        return result.model_copy(update={"analysis_md": self.analysis})


# -- the live pipeline: a recorded diagnosis -----------------------------------------------


def test_a_recorded_diagnosis_is_released_once_its_question_cannot_be_answered_cold(tmp_path):
    """The blind grade, the diagnosis and the hypotheses it materializes each
    record what they read. The diagnoser read the item's reference solution
    and rubric, so its summary and causes stay held back while the learner can
    still answer that question cold, and are shown once they have answered it
    correctly (the retrieval policy's rule for unlocking an item's own
    solution)."""

    paths, vault, repository = split_vault(tmp_path, seed=False)
    client = ProvenanceFake()
    wrong = submit(vault, repository, client, answer=SVD_WRONG, when=at(1))
    drain_jobs(vault, repository, client)

    held = _context(paths.root, repository)
    trace = _trace(held, wrong.attempt_id)
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == SOLUTION_OPEN
    (cause,) = [entry for entry in held["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert cause["statement"] is None and cause["statement_note"] == SOLUTION_OPEN

    submit(vault, repository, client, answer=SVD_RIGHT, when=at(2))
    shown = _context(paths.root, repository)
    trace = _trace(shown, wrong.attempt_id)
    assert trace["diagnosis"]["summary"] == "The learner keeps the last factor untransposed."
    assert isinstance(trace["diagnosis"]["summary"], RecordedText)
    (cause,) = [entry for entry in shown["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert cause["statement"] == "The answer goes wrong because the learner misapplies the rule."
    assert trace["diagnosis"]["hypotheses"] == [cause["statement"]]

    kinds = {(row["kind"], row["writer"]): row for row in _rows(repository)}
    assert {("grading", "blind_grader"), ("diagnosis", "diagnoser"), ("hypothesis", "causal_materialization")} <= set(kinds)
    assert all(row["complete"] == 1 for row in kinds.values())
    diagnosis = json.loads(kinds[("diagnosis", "diagnoser")]["inputs_json"])
    assert diagnosis["solution_items"] == [SVD_ITEM] and list(diagnosis["answers"]) == [wrong.attempt_id]


# -- last verify, reproduction 1: a snapshot diagnosis carrying a legacy key -----------------


def _legacy_snapshot_vault(tmp_path):
    """A split vault in the snapshot mode with an unpinned historical answer
    (graded before contracts were pinned) that states a key no contract
    records, on a topic outside the diagnosed attempt's neighbourhood: only
    the whole-vault export shows it."""

    paths, vault, repository = split_vault(tmp_path, seed=False, config='[diagnosis]\nhistory_mode = "snapshot"')
    seed_attempt(vault, repository, attempt_id="att_legacy", item_id="pi_unrelated_001",
                 answer=f"I wrote: {LEGACY_KEY}", when=at(0.5), points={"correctness": 0},
                 error={"error_type": "conceptual_slip", "severity": 0.5, "evidence": "not prime",
                        "resolution_status": "unresolved", "cause_scope": "learner_state",
                        "first_divergence": {"anchor_kind": "span", "criterion_id": "correctness",
                                             "quote": "I wrote"}})
    with repository.connection() as connection:
        connection.execute("UPDATE grading_evidence SET assessment_contract_version_id = NULL "
                           "WHERE attempt_id = 'att_legacy'")
        connection.commit()
    return paths, load_vault(paths.root), repository


def _legacy_file(workspace: Path) -> str:
    (found,) = [path for path in (workspace / "attempts").glob("*.md") if "att_legacy" in path.name]
    return f"attempts/{found.name}"


@pytest.mark.parametrize(("case", "activity", "summary", "note"), [
    ("opened_the_legacy_answer", lambda root: [f"cat {_legacy_file(root)}"],
     f"Like an earlier answer, the learner wrote {LEGACY_KEY}.", REVISION_UNKNOWN_BEHIND),
    ("searched_the_whole_export", lambda root: ["grep -rn determinant ."],
     f"Like an earlier answer, the learner wrote {LEGACY_KEY}.", REVISION_UNKNOWN_BEHIND),
    ("read_outside_the_export", lambda root: ["cat /etc/hostname"],
     f"Like an earlier answer, the learner wrote {LEGACY_KEY}.", HELD_BACK),
    ("reported_nothing", None, f"Like an earlier answer, the learner wrote {LEGACY_KEY}.", HELD_BACK),
    ("read_only_the_index", lambda root: ["cat INDEX.md"], "The learner keeps the last factor untransposed.", None),
])
def test_a_snapshot_diagnosis_records_the_export_entries_it_opened(tmp_path, case, activity, summary, note):
    """Verify F1: a snapshot diagnosis read the whole-vault export without
    recording what it opened. Now the transport's reported reads are mapped
    to the entries they served and recorded with the diagnosis: an opened
    unpinned answer, a search of the whole export (counted as reading every
    entry), a path outside the export or no report at all keeps the summary
    held back; a diagnosis that read only safe entries is shown once the
    question is answered."""

    paths, vault, repository = _legacy_snapshot_vault(tmp_path)
    client = ProvenanceFake(analysis=summary, activity=activity)
    wrong = submit(vault, repository, client, answer=SVD_WRONG, when=at(1))
    drain_jobs(vault, repository, client)
    submit(vault, repository, client, answer=SVD_RIGHT, when=at(2))

    context = _context(paths.root, repository)
    text = payload_text(context)
    trace = _trace(context, wrong.attempt_id)
    assert LEGACY_KEY not in text and "8841" not in text
    if note is None:
        assert trace["diagnosis"]["summary"] == summary
    else:
        assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == note
    (row,) = _rows(repository, "diagnosis")
    reasons = json.loads(row["incomplete_reasons_json"])
    inputs = json.loads(row["inputs_json"])
    if note is None:
        assert row["complete"] == 1 and "att_legacy" not in inputs["answers"]
    # The receipt says what the reported reads served.
    with repository.connection() as connection:
        (retrieval,) = connection.execute("SELECT retrieval_json FROM diagnosis_context_receipts").fetchone()
    served = json.loads(retrieval)["snapshot"]["served"]
    assert served["how"] == {"opened_the_legacy_answer": "entries", "searched_the_whole_export": "whole",
                             "read_outside_the_export": "outside", "reported_nothing": "unreported",
                             "read_only_the_index": "entries"}[case]
    if case == "read_only_the_index":
        assert served["paths"] == ["INDEX.md"]
    if case in ("opened_the_legacy_answer", "searched_the_whole_export"):
        assert row["complete"] == 1 and inputs["answers"]["att_legacy"] == [None]
    if case == "read_outside_the_export":
        assert row["complete"] == 0 and reasons == [_dp().SNAPSHOT_OUTSIDE]
    if case == "reported_nothing":
        assert row["complete"] == 0 and reasons == [_dp().SNAPSHOT_UNREPORTED]


def test_the_export_s_entries_map_to_what_they_serve(tmp_path):
    """The mapping itself: a plain read serves its file, a listing or ``cd``
    names only, a shell wrapper is unwrapped, and anything else (a glob, a
    pipe, an unknown command) counts as the whole export."""

    root = tmp_path / "history"
    entries = _dp().SnapshotEntries(root=root, entries={
        "INDEX.md": _dp().DiagnosisReads(topics=("lo_a",)),
        "attempts/x_att_1.md": _dp().DiagnosisReads(attempts=(_dp().AttemptRead("att_1"),)),
        "attempts/y_att_2.md": _dp().DiagnosisReads(attempts=(_dp().AttemptRead("att_2"),)),
        "registry/m1.md": _dp().DiagnosisReads(records=(("misconception", "m1", "S"),)),
    })

    def answers(reports):
        return sorted(read.attempt_id for read in _dp().snapshot_reads(entries, reports).attempts)

    assert answers(["cat attempts/x_att_1.md"]) == ["att_1"]
    assert answers([str(root / "attempts" / "y_att_2.md")]) == ["att_2"]
    assert answers(["sed -n '1,40p' attempts/x_att_1.md", "head -n 5 INDEX.md"]) == ["att_1"]
    assert answers(["bash -lc 'cat attempts/y_att_2.md'"]) == ["att_2"]
    assert answers(["ls attempts", "cd registry", "pwd"]) == []
    assert answers(["sed -n '$p' INDEX.md", "sed -n 3p attempts/y_att_2.md"]) == ["att_2"]
    from learnloop.ai.providers.codex import UNACCOUNTED_TURN_ITEM

    for whole in (["cat attempts/*.md"], ["grep -r x ."], ["cat INDEX.md | head"], ["python3 -c 'print(1)'"],
                  # A sed script other than a print: ``e`` runs a program, ``w`` writes.
                  ["sed -n '1e grep -r x .' INDEX.md"], ["sed -n 'w copy' attempts/x_att_1.md"],
                  # A tool item the transport could not read.
                  [f"{UNACCOUNTED_TURN_ITEM}: mcpToolCall"]):
        assert answers(whole) == ["att_1", "att_2"], whole
    outside = _dp().snapshot_reads(entries, ["cat ../../state.sqlite"])
    assert outside.unaccounted == (_dp().SNAPSHOT_OUTSIDE,)
    assert _dp().snapshot_reads(entries, None).unaccounted == (_dp().SNAPSHOT_UNREPORTED,)


def test_the_transport_reports_every_tool_item_it_cannot_read():
    """The snapshot record is only as good as the transport's report: a turn
    item that names no command or path and is not text only (a tool this
    extractor cannot read) is reported, never dropped, so the record counts it
    as reading the whole export; a wrapped SDK item is unwrapped."""

    from types import SimpleNamespace

    from learnloop.ai.providers.codex import UNACCOUNTED_TURN_ITEM, _workspace_activity

    result = SimpleNamespace(items=[
        {"type": "agentMessage", "text": "done"},
        SimpleNamespace(type="reasoning", text="thinking"),
        SimpleNamespace(root=SimpleNamespace(type="commandExecution", command=["cat", "INDEX.md"])),
        {"type": "mcpToolCall", "server": "s", "tool": "read"},
        SimpleNamespace(type="web_search", query="x"),
    ])
    assert _workspace_activity(result) == [
        "cat INDEX.md", f"{UNACCOUNTED_TURN_ITEM}: mcpToolCall", f"{UNACCOUNTED_TURN_ITEM}: web_search",
    ]
    assert _workspace_activity(SimpleNamespace(items=None)) is None


# -- the chat world (mcp_world): the other reproductions ------------------------------------


@pytest.fixture
def world(tmp_path, monkeypatch):
    no_model_calls(monkeypatch)
    hold_att_held(monkeypatch)
    return build_world(tmp_path / "w")


def _solve_pi_own(world, attempt_id: str = "att_own_solved", at_iso: str = "2026-09-30T09:00:00Z") -> None:
    """A later correct, pinned answer on ``pi_own``: its attempt window closes."""

    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES (?, 'pi_own', ?, 'short_answer', 'independent_attempt', 'SOLVED_8812 any row works', 1.0, 0, "
            "?, 'old', 'human', 'desktop_practice')", (attempt_id, LO, at_iso))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES (?, ?, 'correct', 1, 1, ?, 'acv_own')",
            (f"ge_{attempt_id}", attempt_id, NOW_ISO))
        connection.commit()


def _diagnose(world, diagnosis_id: str, analysis: str, reads: Any, *, attempt_id: str = "att_own") -> str:
    """A diagnosis written exactly as the job writes it (``jobs._persist``):
    its reads recorded in the transaction that inserts it."""

    from learnloop.diagnosis.split.jobs import record_diagnosis_reads

    proposal = {"analysis_md": analysis}
    with world.repository.atomic():
        record_diagnosis_reads(world.repository, diagnosis_id=diagnosis_id, proposal=proposal, reads=reads)
        world.repository.insert_attempt_diagnosis(
            diagnosis_id=diagnosis_id, attempt_id=attempt_id, diagnosis_prompt_version="test", mode="live",
            history_mode="full", status="completed", proposal=proposal, causal_view=None, validation_report=None,
            receipt=None)
    return diagnosis_id


def _own_reads(*topics: str, shown: tuple[Any, ...] = ()) -> Any:
    return _dp().reads_of_context(
        current_attempt_id="att_own", current_item_id="pi_own", current_learning_object_id=LO,
        learning_object_ids=topics or (LO,), attempts=(), hypotheses=(), registry=(), repairs=(),
    ).join(_dp().DiagnosisReads(attempts=shown))


def _misconception_from(world, misconception_id: str, statement: str, *, attempt_id: str,
                        diagnosis_id: str | None = None) -> None:
    """A belief normalized from the attempt's event (the normalizer's own
    provenance: the attempt's grading and the diagnosis over the event)."""

    from learnloop.diagnosis.misconceptions import _event_statement_provenance

    record = _event_statement_provenance(world.repository, attempt_id, {"diagnosis_id": diagnosis_id})
    world.repository.insert_misconception(id=misconception_id, learning_object_id=LO, statement=statement,
                                          severity=0.8, provenance=record, provenance_writer="normalizer")


def _belief(context: dict[str, Any], misconception_id: str) -> dict[str, Any]:
    return next(entry for entry in context["misconceptions"] if entry["misconception_id"] == misconception_id)


# -- last verify, reproduction 2: a missing C4 receipt ------------------------------------------


@pytest.mark.parametrize("case", ["no_receipt_no_record", "receipt_names_an_unpinned_answer",
                                  "recorded_in_the_grading_transaction"])
def test_a_joint_grading_s_inputs_reach_what_is_written_from_it(world, case):
    """Verify F1, Q14: ``PEER``'s joint grader wrote a cause and the history a
    diagnosis of ``att_own`` read. Before, a missing Phase-C receipt read as
    "shown nothing". Now a grading made since migration 204 records what it
    was shown in its own transaction; an older model grading with no receipt
    cannot be accounted for (held back), and one whose receipt names an
    unpinned answer carries it (held back). Only the recorded, safe grading
    releases the belief and the summary, once the question is answered."""

    legacy_answer(world)
    pinned_answer(world, PEER, PEER_ANSWER, "2026-09-21T09:00:00Z")
    with world.repository.connection() as connection:
        connection.execute("UPDATE grading_evidence SET agent_run_id = 'run_joint_peer' WHERE attempt_id = ?", (PEER,))
        if case == "receipt_names_an_unpinned_answer":
            c4_receipt(connection, PEER, ["att_legacy"])
        connection.commit()
    if case == "recorded_in_the_grading_transaction":
        with world.repository.atomic():
            _wp().record_grading(world.repository.connection(), attempt_id=PEER, writer="joint_grader", shown_history=[])
    _misconception_from(world, "mc_peer", "Thinks the sign of a cofactor never changes", attempt_id=PEER)
    _diagnose(world, "dg_peer", "As in an earlier answer, the learner drops the cofactor sign.",
              _own_reads(shown=(_dp().AttemptRead(PEER, True),)))
    _solve_pi_own(world)

    context = _context(world.root, world.repository)
    belief, trace = _belief(context, "mc_peer"), _trace(context, "att_own")
    assert LEGACY_KEY not in payload_text(context)
    if case == "recorded_in_the_grading_transaction":
        assert belief["statement"] == "Thinks the sign of a cofactor never changes"
        assert trace["diagnosis"]["summary"] == "As in an earlier answer, the learner drops the cofactor sign."
        return
    expected = HELD_BACK if case == "no_receipt_no_record" else REVISION_UNKNOWN_BEHIND
    assert belief["statement"] is None and belief["statement_note"] == expected
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == expected
    with world.repository.connection() as connection:
        record = _wp().grading_record(connection, PEER)
    assert record.complete is (case != "no_receipt_no_record")


# -- last verify, reproduction 3: a generated topic's literal id in a misconception -------------


def _record_drafted(world, lo_id: str, attempt_id: str, item_id: str) -> None:
    """The drafter's record for a prerequisite drafted from a stuck answer,
    written as the gap pipeline writes it (``pipeline._record_written_texts``)."""

    from learnloop.diagnosis.text_gaps.actions import ActionOutcome
    from learnloop.diagnosis.text_gaps.contract import LearnerText
    from learnloop.diagnosis.text_gaps.pipeline import _record_written_texts
    from learnloop.diagnosis.text_gaps.provenance import drafter_record

    vault = load_vault(world.root)
    text = LearnerText(source_kind="stuck_answer", source_id=attempt_id, text="stuck", context_judge="gap_reader",
                       created_at=NOW_ISO, subject_id="linear-algebra", anchor_learning_object_ids=(LO,),
                       practice_item_id=item_id, attempt_id=attempt_id)
    with world.repository.atomic():
        connection = world.repository.connection()
        drafted = drafter_record(connection, vault, text, None, subject_id="linear-algebra")
        outcome = ActionOutcome("created_prerequisite", created_learning_object_id=lo_id,
                                created_provenance=drafted.as_json())
        _record_written_texts(connection, vault, text, outcome, gap_id=f"gap_for_{lo_id}", learner_words="stuck",
                              clock=None)


@pytest.mark.parametrize("which", ["tainted", "safe"])
def test_a_generated_topic_named_in_a_misconception_carries_what_it_was_drafted_from(world, which):
    """Verify F2: a generated topic's literal id was written into a
    misconception. The drafter now records what it drafted from, a diagnosis
    that saw the topic folds that record in, and so does the belief written
    from it: drafted from the unpinned answer it stays held back (and the
    topic stays an alias); drafted from a pinned, safe answer the topic's name
    and the statement are shown."""

    los = generated_world(world)
    lo_id = los[which]
    source = ("att_legacy", "pi_rewritten") if which == "tainted" else ("att_own", "pi_own")
    _record_drafted(world, lo_id, *source)
    diagnosis = _diagnose(world, f"dg_{which}", "The learner mixed up two topics.", _own_reads(LO, lo_id))
    statement = f"Confuses {LO} with {lo_id}"
    _misconception_from(world, "mc_named", statement, attempt_id="att_own", diagnosis_id=diagnosis)

    held = _belief(_context(world.root, world.repository), "mc_named")
    assert held["statement"] is None and held["statement_note"] in (SOLUTION_OPEN, REVISION_UNKNOWN_BEHIND)
    _solve_pi_own(world)
    context = _context(world.root, world.repository)
    belief = _belief(context, "mc_named")
    if which == "tainted":
        assert belief["statement"] is None and belief["statement_note"] == REVISION_UNKNOWN_BEHIND
        assert lo_id not in payload_text(context) and "8841" not in payload_text(context)
        return
    assert belief["statement"] == statement
    gap = next(entry for entry in context["open_learner_text_gaps"] if entry["gap_id"] == "gap_gen_safe")
    assert gap["target_topic"] == "Permutation parity basics" and gap["learning_object_id"] == lo_id


# -- old rows, re-diagnosis --------------------------------------------------------------------


def test_old_rows_stay_held_back_and_a_re_diagnosis_writes_recorded_ones(tmp_path):
    """A diagnosis and its causes written before this stage have no record:
    they stay held back, even once the question is answered. Re-diagnosing
    the attempt writes a new diagnosis and new cause versions with records,
    which are shown; the old rows still are not."""

    from learnloop.diagnosis.split.jobs import enqueue_diagnosis

    paths, vault, repository = split_vault(tmp_path, seed=False)
    client = ProvenanceFake()
    wrong = submit(vault, repository, client, answer=SVD_WRONG, when=at(1))
    submit(vault, repository, client, answer=SVD_RIGHT, when=at(2))
    with repository.connection() as connection:
        connection.execute("DELETE FROM post_attempt_jobs")
        connection.commit()
    old = repository.insert_attempt_diagnosis(
        attempt_id=wrong.attempt_id, diagnosis_prompt_version="test", mode="live", history_mode="full",
        status="completed", proposal={"analysis_md": "An old explanation."}, causal_view=None,
        validation_report=None, receipt=None)
    old_cause = repository.append_causal_hypothesis(
        episode_key="ep_old", attempt_id=wrong.attempt_id, learning_object_id="lo_svd_compute",
        cause_scope="learner_state", statement="An old cause with no record", statement_normalized="old",
        status="candidate")
    assert _wp().stored_record(sqlite3.connect(paths.sqlite_path), "diagnosis", old) is None
    before = _context(paths.root, repository)
    assert _trace(before, wrong.attempt_id)["diagnosis"]["summary_note"] == HELD_BACK
    old_entry = next(entry for entry in before["open_hypotheses"] if entry.get("hypothesis_id") == old_cause["id"])
    assert old_entry["statement"] is None and old_entry["statement_note"] == HELD_BACK

    enqueue_diagnosis(vault, repository, attempt_id=wrong.attempt_id, rediagnose=True)
    drain_jobs(vault, repository, client)
    after = _context(paths.root, repository)
    trace = _trace(after, wrong.attempt_id)
    assert trace["diagnosis"]["summary"] == "The learner keeps the last factor untransposed."
    old_entry = next(entry for entry in after["open_hypotheses"] if entry.get("hypothesis_id") == old_cause["id"])
    assert old_entry["statement"] is None and old_entry["statement_note"] == HELD_BACK
    assert "An old explanation." not in payload_text(after) and "An old cause" not in payload_text(after)


def test_a_text_rewritten_by_a_writer_that_recorded_nothing_is_held_back(world):
    """A record covers the text it was written for (its hash): a statement a
    later writer rewrote without a record is held back; one rewritten with
    its own record is shown again."""

    _diagnose(world, "dg_rewrite", "The learner drops the sign.", _own_reads())
    _misconception_from(world, "mc_rewrite", "Thinks the sign never changes", attempt_id="att_own",
                        diagnosis_id="dg_rewrite")
    _solve_pi_own(world)
    assert _belief(_context(world.root, world.repository), "mc_rewrite")["statement"] == "Thinks the sign never changes"
    with world.repository.connection() as connection:
        connection.execute("UPDATE misconceptions SET statement = 'Rewritten by hand' WHERE id = 'mc_rewrite'")
        connection.commit()
    rewritten = _belief(_context(world.root, world.repository), "mc_rewrite")
    assert rewritten["statement"] is None and rewritten["statement_note"] == HELD_BACK
    with world.repository.connection() as connection:
        record = _wp().closure(connection, [("diagnosis", "dg_rewrite")])
    world.repository.update_misconception("mc_rewrite", statement="Thinks a sign flip is optional",
                                          statement_provenance=record)
    assert _belief(_context(world.root, world.repository), "mc_rewrite")["statement"] == "Thinks a sign flip is optional"


def test_the_kill_switch_puts_back_the_narrow_rule(world):
    """``diagnosis.chat_shows_recorded_text = false``: nothing derived is shown."""

    _diagnose(world, "dg_switch", "The learner drops the sign.", _own_reads())
    _solve_pi_own(world)
    assert _trace(_context(world.root, world.repository), "att_own")["diagnosis"]["summary"] == "The learner drops the sign."
    config = world.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n[diagnosis]\nchat_shows_recorded_text = false\n",
                      encoding="utf-8")
    trace = _trace(_context(world.root, world.repository), "att_own")
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == HELD_BACK


def test_a_correction_written_from_exam_material_is_held_back(world):
    """A correction frozen from facet claims records the source refs those
    facets were authored from; an exam passage keeps it held back."""

    _solve_pi_own(world)
    book = {"ref_type": "canonical_source", "ref_id": "src_book", "extraction_id": "ext_book", "span_ids": ["s1"]}
    exam = {"ref_type": "canonical_source", "ref_id": "src_exam", "extraction_id": "ext_exam", "span_ids": ["s2"]}
    for misconception_id, refs in (("mc_book", [book]), ("mc_exam", [book, exam])):
        world.repository.insert_misconception(
            id=misconception_id, learning_object_id=LO, statement="Thinks rows commute",
            correction_statement="Use this distinction: a row swap negates the value.",
            correction_provenance=_wp().WriteRecord(_wp().Inputs.of(topics=[LO], sources=refs)))
    context = _context(world.root, world.repository)
    assert _belief(context, "mc_book")["correction"] == "Use this distinction: a row swap negates the value."
    exam_belief = _belief(context, "mc_exam")
    assert exam_belief["correction"] is None and exam_belief["correction_note"] == f"withheld: {WITHHELD_EXAM}"


# -- Q9: regrade lineage ------------------------------------------------------------------------


def test_a_regrade_keeps_the_ids_a_belief_lists_resolvable(tmp_path):
    """Q9: a regrade re-mints the attempt's error events. Each new event
    records the ids it replaces, so a belief that lists a replaced event still
    resolves to the current events and to its answer."""

    from learnloop.attempts.regrade import regrade_attempt
    from learnloop.diagnosis.split.history import AttemptRef
    from learnloop.diagnosis.split.live import live_history_store

    paths, vault, repository = split_vault(tmp_path, seed=False)
    client = ProvenanceFake()
    wrong = submit(vault, repository, client, answer=SVD_WRONG, when=at(1))
    old_events = [str(event["id"]) for event in repository.raw_error_events_for_attempt(wrong.attempt_id)]
    assert old_events
    repository.insert_misconception(id="mc_listed", learning_object_id="lo_svd_compute",
                                    statement="Thinks V needs no transpose", severity=0.8,
                                    source_error_event_ids=old_events)
    attempt = repository.fetch_practice_attempt(wrong.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai",
                    clock=None)
    new_events = [str(event["id"]) for event in repository.raw_error_events_for_attempt(wrong.attempt_id)]
    assert new_events and not set(new_events) & set(old_events)
    with repository.connection() as connection:
        resolved = _wp().current_error_event_ids(connection, old_events)
        lineage = connection.execute("SELECT error_event_id, replaces_error_event_id, reason FROM error_event_lineage "
                                     "WHERE attempt_id = ?", (wrong.attempt_id,)).fetchall()
        regraded = [row for row in _rows(repository, _wp().GRADING) if row["writer"] == "regrade"]
    assert all(resolved[old] == tuple(sorted(new_events)) for old in old_events)
    assert {(row[0], row[1]) for row in lineage} == {(new, old) for new in new_events for old in old_events}
    assert len(regraded) == 1 and regraded[0]["record_id"] == wrong.attempt_id
    store = live_history_store(load_vault(paths.root), repository)
    (belief,) = [record for record in store.registry_before(AttemptRef("zz_after", "2099-01-01T00:00:00Z"), None)
                 if record.id == "mc_listed"]
    assert belief.source_attempt_id == wrong.attempt_id


# -- Q10: a question records its contract --------------------------------------------------------


def _question(world, question_id: str, *, context: str, item: str | None, attempt: str | None = None,
              contract: str | None = None, text: str = "is a row swap a sign flip?", gap_id: str | None = None,
              record: bool = True) -> str:
    """A learner question (``insert_question_event``, Q10) and its gap, with
    the gap's words recorded as the gap pipeline records them."""

    from learnloop.diagnosis.text_gaps.actions import ActionOutcome
    from learnloop.diagnosis.text_gaps.pipeline import _record_written_texts
    from learnloop.diagnosis.text_gaps.sources import tutor_question_text
    from tests.mcp_world import gap_row

    world.repository.insert_question_event({
        "id": question_id, "context": context, "practice_item_id": item, "attempt_id": attempt,
        "question_md": text, "answer_md": "an answer", "answer_status": "answered",
        **({"assessment_contract_version_id": contract} if contract else {}),
        "created_at": "2026-09-25T09:00:00Z",
    })
    gap_id = gap_id or f"gap_{question_id}"
    with world.repository.connection() as connection:
        gap_row(connection, gap_id, source_kind="tutor_question", source_id=question_id, attempt_id=attempt,
                item_id=item, text=text, target_kind=None, target_id=None, action="signal_only")
        connection.commit()
    if record:
        vault = load_vault(world.root)
        learner_text = tutor_question_text(vault, world.repository, question_id)
        with world.repository.atomic():
            _record_written_texts(world.repository.connection(), vault, learner_text, ActionOutcome("signal_only"),
                                  gap_id=gap_id, learner_words=text, clock=None)
    return gap_id


def _gap(context: dict[str, Any], gap_id: str) -> dict[str, Any]:
    return next(entry for entry in context["open_learner_text_gaps"] if entry["gap_id"] == gap_id)


def test_a_question_that_records_its_contract_is_shown_when_safe(world):
    """Q10: a question records the item contract it was asked about (the
    caller's, or a graded attempt's pinned one), and the gap's words record
    the question. Asked mid-attempt on an unprotected item it is shown; asked
    on the feedback screen (where the solution may have been shown) it waits
    until the question is answered; on an exam item, or with no contract
    recorded, it is held back."""

    practice = _question(world, "q_practice", context="practice", item="pi_own", contract="acv_own")
    feedback = _question(world, "q_feedback", context="feedback", item="pi_own", attempt="att_own",
                         text="why does the sign flip here?")
    exam = _question(world, "q_exam", context="practice", item="pi_exam", contract="acv_own",
                     text="what are the eigenvalues?")
    unrecorded = _question(world, "q_old", context="practice", item="pi_own", text="an old question, no contract")
    with world.repository.connection() as connection:
        (pinned,) = connection.execute("SELECT assessment_contract_version_id FROM question_events "
                                       "WHERE id = 'q_feedback'").fetchone()
    assert pinned == "acv_own"

    context = _context(world.root, world.repository)
    assert _gap(context, practice)["learner_text"] == "is a row swap a sign flip?"
    assert _gap(context, feedback)["learner_text"] is None
    assert _gap(context, feedback)["learner_text_note"] == SOLUTION_OPEN
    assert _gap(context, exam)["learner_text"] is None
    assert _gap(context, exam)["learner_text_note"] == f"withheld: {WITHHELD_EXAM}"
    assert _gap(context, unrecorded)["learner_text"] is None
    assert _gap(context, unrecorded)["learner_text_note"] == QUESTION_UNRECORDED
    # The gaps written before this stage have no record at all.
    assert _gap(context, "gap_open")["learner_text"] is None and _gap(context, "gap_open")["learner_text_note"] == HELD_BACK

    _solve_pi_own(world)
    assert _gap(_context(world.root, world.repository), feedback)["learner_text"] == "why does the sign flip here?"


def test_the_tutor_records_the_contract_a_mid_attempt_question_is_about(world):
    """Q10 at its writer: mid-attempt the tutor names the item as presented
    (the content-addressed contract snapshot); on no item, nothing."""

    from learnloop.learner.assessment_contracts import snapshot_for_presentation
    from learnloop.tutor.tutor_qa import _question_contract

    vault = load_vault(world.root)
    item = vault.practice_items["pi_own"]
    assert _question_contract(vault, world.repository, item, None) == snapshot_for_presentation(
        world.repository, vault, item)
    assert _question_contract(vault, world.repository, None, None) is None
    assert _question_contract(vault, world.repository, item, "att_own") is None  # the repository pins it


# -- the store ---------------------------------------------------------------------------------


def test_the_records_are_append_only_and_classified(tmp_path):
    from learnloop.db.table_roles import TABLE_ROLES, TableRole

    assert TABLE_ROLES["text_write_provenance"] is TableRole.RAW_LEDGER
    assert TABLE_ROLES["error_event_lineage"] is TableRole.RAW_LEDGER
    paths, _vault, repository = split_vault(tmp_path, seed=False)
    with repository.atomic():
        _wp().record_text_write(repository.connection(), kind="diagnosis", record_id="dg_x", text="t",
                                writer="test", record=_wp().WriteRecord(_wp().Inputs.of(topics=["lo_svd_compute"])))
    with sqlite3.connect(paths.sqlite_path) as connection:
        for statement in ("UPDATE text_write_provenance SET writer = 'x'", "DELETE FROM text_write_provenance"):
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                connection.execute(statement)


def test_the_reasons_spelled_out_here_are_the_protection_s():
    from learnloop.learner_protection import QUESTION_UNRECORDED as QUESTION
    from learnloop.learner_protection import WITHHELD_SOLUTION_OPEN

    assert SOLUTION_OPEN == f"withheld: {WITHHELD_SOLUTION_OPEN}"
    assert QUESTION_UNRECORDED == f"withheld: {QUESTION}"


def test_the_solution_rule_is_the_retrieval_policy_s_window():
    from learnloop.instructional.policy import WINDOW_CLOSING_CORRECTNESS as POLICY
    from learnloop.learner_protection import WINDOW_CLOSING_CORRECTNESS

    assert WINDOW_CLOSING_CORRECTNESS == POLICY
