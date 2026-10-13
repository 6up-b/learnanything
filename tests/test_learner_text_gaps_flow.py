"""Learner-text gaps end to end: the mvp-0.13 sooner check and its kill-switch
parity, the diagnosis and stuck-answer sources, the queue and the sidecar, the
report and the upgrade. Every model is a fake."""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.diagnosis.text_gaps.jobs import enqueue, process_next_gap_job, sweep_backlog
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, process_learner_text
from learnloop.diagnosis.text_gaps.sources import (
    StuckText,
    diagnosis_text,
    stuck_answer_text,
    tutor_question_text,
)
from learnloop.placement.decisions import record_self_report
from learnloop.placement.state import load_placement_state
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake, GapTutor, always, word_match

EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")
DAY = 24 * 60
CHECK = 14 * DAY + 5


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _iso(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _setup(tmp_path, *, version="mvp-0.13", toml="", name="vault"):
    paths = create_placement_vault(tmp_path / name, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    return paths.root, repository


def _clients(llm=None, decider=None, tutor=None) -> PipelineClients:
    llm = llm or GapLLMFake()
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                           drafter=lambda: llm, tutor=(lambda: tutor) if tutor else None, embedder=None)


def _gap(root, repository, *, minutes, item="pi_spec_easy", gap=EIGEN_GAP, llm=None):
    vault = load_vault(root)
    event_id = ask_question(vault, repository, GapTutor(gap), context="practice", question_md="What's an eigenvalue?",
                            practice_item_id=item, session_id="sess_gap", clock=_at(minutes))["event_id"]
    text = tutor_question_text(vault, repository, event_id)
    return process_learner_text(root, repository, text, clients=_clients(llm or GapLLMFake(decide=word_match("eigenvalues"))),
                                clock=_at(minutes))


def _queue(root, repository, minutes):
    return build_due_queue(load_vault(root), repository, clock=_at(minutes), session=SchedulerSession(),
                           persist_explanations=False)


def _answer(root, repository, item_id, points, *, minutes):
    return complete_self_graded_attempt(
        load_vault(root), repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", hints_used=0,
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4), clock=_at(minutes),
    )


def _view(queue):
    return [(entry.practice_item_id, sorted(key for key, value in entry.components.items() if value)) for entry in queue]


# -- the successor: a sooner check ---------------------------------------------------------------


def test_a_gap_brings_an_assumed_los_check_forward_and_the_switch_restores_the_predecessor(tmp_path):
    root, repository = _setup(tmp_path)
    record_self_report(load_vault(root), repository, learning_object_ids=["lo_eigen_basics"], report="know_this",
                       clock=_at(1))
    original = load_placement_state(load_vault(root), repository, now_iso=_iso(2)).open_by_lo["lo_eigen_basics"]
    row = _gap(root, repository, minutes=10)
    assert row["action"] == "matched_prerequisite" and row["target_id"] == "lo_eigen_basics"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        (advance,) = store.check_advances(connection)
    assert (advance["intent"], advance["original_due"], advance["advanced_due"]) == (
        "assumed", original.first_review_due, _iso(10 + DAY).replace(".000000", ""))
    state = load_placement_state(load_vault(root), repository, now_iso=_iso(11))
    assumption = state.open_by_lo["lo_eigen_basics"]
    assert assumption.first_review_due == advance["advanced_due"]
    assert assumption.advanced_from == original.first_review_due
    # Not before the bound (24 h after the gap), then served as the check.
    assert not [s for s in _queue(root, repository, 10 + DAY - 5) if s.learning_object_id == "lo_eigen_basics"]
    due = [s for s in _queue(root, repository, 10 + DAY + 5) if s.learning_object_id == "lo_eigen_basics"]
    assert len(due) == 1 and due[0].components["gap_sooner_check"] == 1.0
    assert "brought forward" in due[0].plain_english[0]
    with_switch = _view(_queue(root, repository, 10 + DAY + 5))
    # Kill switch: exactly the predecessor's serving.
    append_config_toml(root, "[learner_text_gaps]\nsooner_check_enabled = false\n")
    off = _view(_queue(root, repository, 10 + DAY + 5))
    assert not [entry for entry in off if entry[0].startswith("pi_eig_")]
    assert load_placement_state(load_vault(root), repository, now_iso=_iso(11)).open_by_lo[
        "lo_eigen_basics"].first_review_due == original.first_review_due
    set_algorithm_version_on = load_vault(root)
    assert set_algorithm_version_on.config.learner_text_gaps.sooner_check_enabled is False
    with_switch_items = {item for item, _components in with_switch}
    assert {item for item, _ in off} == with_switch_items - {due[0].practice_item_id}


def test_the_switch_off_queue_equals_the_predecessor_version(tmp_path):
    root, repository = _setup(tmp_path, toml="[learner_text_gaps]\nsooner_check_enabled = false\n")
    record_self_report(load_vault(root), repository, learning_object_ids=["lo_eigen_basics"], report="know_this",
                       clock=_at(1))
    _gap(root, repository, minutes=10)
    off = _view(_queue(root, repository, 10 + DAY + 5))
    predecessor = tmp_path / "predecessor"
    root_b, repository_b = _setup(predecessor, version="mvp-0.12")
    record_self_report(load_vault(root_b), repository_b, learning_object_ids=["lo_eigen_basics"], report="know_this",
                       clock=_at(1))
    _gap(root_b, repository_b, minutes=10)
    assert off == _view(_queue(root_b, repository_b, 10 + DAY + 5))
    with closing(connect(repository_b.sqlite_path, read_only=True)) as connection:
        assert store.check_advances(connection) == []  # below mvp-0.13 none is written


def test_a_gap_on_a_maintenance_lo_brings_its_next_review_forward_until_answered(tmp_path):
    root, repository = _setup(tmp_path)
    record_self_report(load_vault(root), repository, learning_object_ids=["lo_eigen_basics"], report="know_this",
                       clock=_at(1))
    (check,) = [s for s in _queue(root, repository, CHECK) if s.learning_object_id == "lo_eigen_basics"]
    _answer(root, repository, check.practice_item_id, 4.0, minutes=CHECK + 1)
    assert load_placement_state(load_vault(root), repository, now_iso=_iso(CHECK + 2)).intent_by_lo[
        "lo_eigen_basics"].intent == "maintenance"
    row = _gap(root, repository, minutes=CHECK + 3)
    assert row["action"] == "matched_prerequisite"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        (advance,) = store.check_advances(connection)
    assert advance["intent"] == "maintenance"
    due_at = CHECK + 3 + DAY + 5
    gap_checks = [s for s in _queue(root, repository, due_at) if s.components.get("gap_sooner_check")]
    assert [s.learning_object_id for s in gap_checks] == ["lo_eigen_basics"]
    _answer(root, repository, gap_checks[0].practice_item_id, 4.0, minutes=due_at + 1)
    state = load_placement_state(load_vault(root), repository, now_iso=_iso(due_at + 2))
    assert state.gap_check_due_by_lo == {}


# -- sources ----------------------------------------------------------------------------------------


def _attempt(repository, attempt_id="att_1", *, item="pi_spec_easy", lo="lo_spectral", answer="lambda is a vector"):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, hints_used, created_at, session_id, subject) "
            "VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, 0, ?, 's', 'linear-algebra')",
            (attempt_id, item, lo, answer, _iso(5)),
        )
        connection.commit()


def _diagnosis(repository, proposal, *, diagnosis_id="diag_1", attempt_id="att_1"):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO attempt_diagnoses(id, attempt_id, diagnosis_prompt_version, provider, model, mode, history_mode, "
            "status, proposal_json, created_at) VALUES (?, ?, 'diag-v1', 'fake', 'fake/diagnoser', 'live', 'full', "
            "'completed', ?, ?)",
            (diagnosis_id, attempt_id, json.dumps(proposal), _iso(6)),
        )
        connection.commit()


def test_a_diagnosis_is_read_from_its_causes_without_a_call(tmp_path):
    root, repository = _setup(tmp_path)
    _attempt(repository)
    _diagnosis(repository, {
        "event_diagnoses": [{"causal_class": "learner_state", "misconception_statement": None}],
        "prerequisite_gap_hypotheses": [{"prerequisite_ref": "lo_eigen_basics", "suggested_discriminator_md": "x"}],
    })
    text = diagnosis_text(load_vault(root), repository, "diag_1")
    assert (text.context_judge, text.reading.kind, text.reading.prerequisite_refs) == (
        "diagnoser", "prerequisite", ("lo_eigen_basics",))
    llm = GapLLMFake()
    row = process_learner_text(root, repository, text, clients=_clients(llm, decider=ChoiceDecider(kind="slip")),
                               clock=_at(7))
    assert (row["action"], row["target_id"], row["match_basis"]) == (
        "matched_prerequisite", "lo_eigen_basics", "diagnoser_ref")
    assert llm.calls == []  # the diagnoser named it; no judge call
    with repository.connection() as connection:
        kinds = connection.execute(
            "SELECT judge, verdict FROM judgment_ledger WHERE task = 'learner_gap_kind' ORDER BY rowid").fetchall()
    assert [tuple(row) for row in kinds] == [("diagnoser", "prerequisite"), ("decider", "slip")]


@pytest.mark.parametrize(("events", "kind"), [
    ([{"causal_class": "transient_execution"}], "slip"),
    ([{"causal_class": "learner_state", "misconception_statement": "Eigenvalues are vectors.",
       "registry_match": {"kind": "new", "statement": "Eigenvalues are vectors."}}], "misconception"),
    ([{"causal_class": "unknown"}], "none"),
])
def test_diagnosis_kinds(tmp_path, events, kind):
    root, repository = _setup(tmp_path)
    _attempt(repository)
    _diagnosis(repository, {"event_diagnoses": events, "prerequisite_gap_hypotheses": []})
    text = diagnosis_text(load_vault(root), repository, "diag_1")
    row = process_learner_text(root, repository, text, clients=_clients(), clock=_at(7))
    assert row["kind"] == kind
    if kind == "misconception":
        # The diagnoser's registry_match path normalizes it: logged, not repeated.
        assert row["action"] == "belief_registry_path"


class _FakeStuck:
    def __init__(self, rows):
        self.rows = rows

    def stuck_texts(self, connection):
        return self.rows


def test_stuck_text_is_read_through_the_source_interface(tmp_path):
    root, repository = _setup(tmp_path)
    source = _FakeStuck([StuckText(attempt_id="att_stuck", practice_item_id="pi_spec_easy",
                                   learning_object_id="lo_spectral", subject_id="linear-algebra",
                                   text="I don't know what an eigenvalue is", created_at=_iso(3))])
    text = stuck_answer_text(load_vault(root), repository, "att_stuck", source)
    assert text.context_judge == "gap_reader" and text.reading is None
    llm = GapLLMFake(decide=word_match("eigenvalues"), reading=EIGEN_GAP)
    row = process_learner_text(root, repository, text, clients=_clients(llm), clock=_at(4))
    assert row["source_kind"] == "stuck_answer" and row["action"] == "matched_prerequisite"
    assert [purpose for purpose, _ in llm.calls][0] == "learner_gap_reading"
    # The default adapter yields nothing until the stuck-prompt stage merges.
    assert sweep_backlog(load_vault(root), repository) == {"stuck_answer": 0, "tutor_question": 0, "diagnosis": 0}
    unread = StuckText(attempt_id="att_stuck_2", practice_item_id="pi_spec_easy", learning_object_id="lo_spectral",
                       subject_id="linear-algebra", text="no idea what spectral means", created_at=_iso(5))
    both = _FakeStuck([*source.rows, unread])
    # The read text is not queued again; the dry run writes nothing.
    assert sweep_backlog(load_vault(root), repository, stuck_source=both, dry_run=True)["stuck_answer"] == 1
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert store.jobs(connection) == []
    assert sweep_backlog(load_vault(root), repository, stuck_source=both)["stuck_answer"] == 1


# -- the queue ------------------------------------------------------------------------------


def test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch(tmp_path):
    root, repository = _setup(tmp_path)
    vault = load_vault(root)
    event_id = ask_question(vault, repository, GapTutor(EIGEN_GAP), context="practice", question_md="eigenvalue?",
                            practice_item_id="pi_spec_easy", session_id="s", clock=_at(1))["event_id"]
    assert enqueue(repository, source_kind="tutor_question", source_id=event_id)
    assert enqueue(repository, source_kind="tutor_question", source_id=event_id) is None
    broken = PipelineClients(judge=lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    failing = GapLLMFake(decide=word_match("eigenvalues"), fail={"learner_gap_same_prerequisite"})
    outcome = process_next_gap_job(root, repository, owner="t", clients=_clients(failing), clock=_at(2))
    # A failed judge call settles nothing (Codex review F1): no row, retried.
    assert outcome.state == "released" and outcome.gap_id is None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert store.gap_for_source(connection, "tutor_question", event_id) is None
    assert process_next_gap_job(root, repository, owner="t", clients=broken, clock=_at(2.5)) is None  # backoff
    outcome = process_next_gap_job(root, repository, owner="t",
                                   clients=_clients(GapLLMFake(decide=word_match("eigenvalues"))), clock=_at(4))
    assert outcome.state == "done" and outcome.action == "matched_prerequisite"
    assert process_next_gap_job(root, repository, owner="t", clients=broken, clock=_at(5)) is None
    append_config_toml(root, "[learner_text_gaps]\nenabled = false\n")
    other = ask_question(load_vault(root), repository, GapTutor(EIGEN_GAP), context="practice", question_md="again?",
                         practice_item_id="pi_spec_easy", session_id="s", clock=_at(6))["event_id"]
    enqueue(repository, source_kind="tutor_question", source_id=other)
    skipped = process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(7))
    assert skipped.state == "skipped"


def test_a_job_that_keeps_failing_is_logged_as_failed_without_a_target(tmp_path, monkeypatch):
    root, repository = _setup(tmp_path)
    event_id = ask_question(load_vault(root), repository, GapTutor(EIGEN_GAP), context="practice", question_md="q",
                            practice_item_id="pi_spec_easy", session_id="s", clock=_at(1))["event_id"]
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    import learnloop.diagnosis.text_gaps.jobs as jobs

    def explode(*_args, **_kwargs):
        raise RuntimeError("pipeline down")

    monkeypatch.setattr(jobs, "process_learner_text", explode)
    states = []
    for attempt in range(jobs.MAX_ATTEMPTS):
        outcome = process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(10 + attempt * 600))
        states.append(outcome.state)
    assert states == ["released", "released", "failed"]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.gap_for_source(connection, "tutor_question", event_id)
    assert (row["action"], row["kind"], row["target_id"]) == ("failed", "unread", None)


# -- the sidecar ----------------------------------------------------------------------------


def test_the_sidecar_queues_the_reading_and_the_overlay_shows_it_with_undo(tmp_path, monkeypatch):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import learner_gaps as rpc
    from learnloop_sidecar.handlers import tutor_qa as tutor_rpc
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

    root, repository = _setup(tmp_path)
    ctx = SidecarContext()
    ctx.post_attempt_worker = PostAttemptWorker(autostart=False)
    ctx.load(root, maintenance=False)

    class _Ready:
        ready = True

    tutor = GapTutor(EIGEN_GAP)
    monkeypatch.setattr(tutor_rpc, "ready_tutor_qa_provider", lambda _vault: ("fake", _Ready(), tutor))
    response = tutor_rpc.ask_tutor_question(ctx, tutor_rpc.AskTutorQuestionInput(
        context="practice", question="What is an eigenvalue?", practice_item_id="pi_diag_easy", session_id="s"))
    assert response["learnerGap"] == {"status": "queued", "kind": "prerequisite"}
    event_id = response["eventId"]
    pending = rpc.get_learner_text_gap(ctx, rpc.GetLearnerTextGapInput(source_id=event_id))
    assert pending["status"] == "pending"
    ctx.post_attempt_worker.gap_clients = lambda _vault: _clients(GapLLMFake(decide=word_match("eigenvalues")))
    (outcome,) = ctx.post_attempt_worker.run_pending("gaps")
    assert outcome.action == "matched_prerequisite"
    done = rpc.get_learner_text_gap(ctx, rpc.GetLearnerTextGapInput(source_id=event_id))
    gap = done["gap"]
    assert done["status"] == "done" and gap["label"].startswith("Noted: this builds on Eigenvalues")
    assert gap["allowedReversals"] == ["undo_edge"] and "link added from your question" in gap["label"]
    assert gap["edgeId"] in {edge.id for edge in ctx.vault.edges}  # the vault was reloaded
    undone = rpc.reverse_learner_text_gap(ctx, rpc.ReverseLearnerTextGapInput(gap_id=gap["gapId"], reversal="undo_edge"))
    assert undone["gap"]["allowedReversals"] == [] and "link undone" in undone["gap"]["label"]
    assert gap["edgeId"] not in {edge.id for edge in ctx.vault.edges}


# -- the report and the upgrade -----------------------------------------------------------------


def test_the_report_counts_per_kind_and_chooser_and_its_dry_run_writes_nothing(tmp_path):
    from learnloop.diagnosis.text_gaps.report import build_report, plan_report, write_report

    root, repository = _setup(tmp_path)
    _gap(root, repository, minutes=1)
    _gap(root, repository, minutes=2, gap=LearnerGap(kind="slip"))
    plan = plan_report(repository)
    assert plan == {"dry_run": True, "learner_texts": 2, "reversals": 0,
                    "by_action": {"matched_prerequisite": 1, "signal_only": 1}, "calls": 0}
    report = build_report(load_vault(root), repository)
    assert report["by_kind_and_chooser"]["prerequisite|tutor"]["matched_prerequisite"] == 1
    assert report["by_kind_and_chooser"]["slip|tutor"]["signal_only"] == 1
    assert report["judges"]["same_prerequisite"]["pairs_judged_by_both"] == 0
    out = tmp_path / "report.md"
    write_report(load_vault(root), repository, out)
    text = out.read_text()
    assert "## Decider or LLM" in text and "## Batch review" in text


def test_upgrade_to_mvp013_from_its_predecessor(tmp_path):
    from learnloop.diagnosis.text_gaps.upgrade import upgrade_to_mvp013

    root, _repository = _setup(tmp_path, version="mvp-0.12")
    result = upgrade_to_mvp013(root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.12", "mvp-0.13")
    assert load_vault(root).config.algorithms.algorithm_version == "mvp-0.13"
    again = upgrade_to_mvp013(root)
    assert not again.upgraded and again.problems == ["vault is already mvp-0.13"]
    old = tmp_path / "old"
    paths = create_placement_vault(old, version="mvp-0.6")
    refused = upgrade_to_mvp013(paths.root)
    assert not refused.upgraded and "cannot upgrade" in refused.problems[0]
    set_algorithm_version  # noqa: B018 - imported for the parity tests' helpers
