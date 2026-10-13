"""Learner-text gaps: regression tests for the Codex re-review findings (F1-F7).

Each test reproduces a failure the first round's fixes left open or
introduced. Every model is a fake; no call leaves the process."""

from __future__ import annotations

from contextlib import closing
import json
from types import SimpleNamespace

import pytest
import yaml

from learnloop.ai.spend import SpendCaps
from learnloop.db.connection import connect
from learnloop.db.stores import learner_gaps as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.text_gaps import actions as gap_actions
from learnloop.diagnosis.text_gaps import pipeline as gap_pipeline
from learnloop.diagnosis.text_gaps.actions import reverse_gap
from learnloop.diagnosis.text_gaps.jobs import calls_today, enqueue, process_next_gap_job, run_pending
from learnloop.diagnosis.text_gaps.judges import TextBudget
from learnloop.field.signals import derive_interaction_signals
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml
from tests.test_learner_text_gaps_review import (
    BELIEF,
    EIGEN_GAP,
    EIGENVECTOR_GAP,
    _ask,
    _at,
    _clients,
    _created_los,
    _fail_once,
    _gaps,
    _jobs,
    _run,
    _self_graded,
    _StuckSource,
    _vault,
)
from tests.text_gap_fakes import GapLLMFake, GapTutor, always, word_match

STUCK = "att_stuck_1"


def _big_caps() -> SpendCaps:
    return SpendCaps(max_calls=200, max_candidates=200, max_pairs=200, max_retries=20,
                     max_total_tokens=5_000_000, max_estimated_usd=1.0)


def _set_payload(repository, payload) -> None:
    with repository.atomic():
        repository.connection().execute("UPDATE learner_text_gap_jobs SET payload_json = ?", (json.dumps(payload),))


def _stuck_creation_written(tmp_path, monkeypatch):
    """A stuck answer read as a missing prerequisite whose creation was
    written before the state sync failed: the job is backing off."""

    root, repository = _vault(tmp_path)
    stuck = _StuckSource(stuck=True)
    enqueue(repository, source_kind="stuck_answer", source_id=STUCK)
    llm = GapLLMFake(decide=always("different"), reading=EIGENVECTOR_GAP)
    _fail_once(monkeypatch, gap_actions, "sync_vault_state")
    first = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(1),
                                 stuck_source=stuck)
    assert first.state == "retry_later" and _gaps(repository) == []
    (written,) = _created_los(root)
    return root, repository, stuck, llm, written


# -- F1: a retry acts on the first reading and finishes what it wrote ---------------------------


@pytest.mark.parametrize("legacy_progress", [False, True])
@pytest.mark.parametrize("second_reading", ["none", "failed"])
def test_rr_f1_a_stuck_retry_finishes_the_recorded_creation_whatever_the_second_reading(
    tmp_path, monkeypatch, second_reading, legacy_progress,
):
    root, repository, stuck, llm, written = _stuck_creation_written(tmp_path, monkeypatch)
    payload = _jobs(repository)[0]["payload"]
    assert payload["decided"]["kind"] == "prerequisite" and payload["reading"]["prerequisite_name"] == "Eigenvectors"
    if legacy_progress:
        # Progress recorded by the first round's code: the creation only.
        _set_payload(repository, {"created": payload["created"]})
    # Read again, the stuck answer would now read as nothing, or fail.
    llm.reading = LearnerGap(kind="none")
    if second_reading == "failed":
        llm.fail = {"learner_gap_reading"}
    second = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(10),
                                  stuck_source=stuck)
    assert (second.state, second.action) == ("done", "created_prerequisite")
    (row,) = _gaps(repository)
    assert _created_los(root) == [written]
    assert (row["kind"], row["created_learning_object_id"]) == ("prerequisite", written)
    assert row["edge_id"] and row["edge_id"] in {edge.id for edge in load_vault(root).edges}
    assert row["detail"]["resumed"] == "creation"
    assert gap_actions.creations_today(repository, now_iso=row["created_at"]) == 1  # the daily cap counts it
    readings = [purpose for purpose, _ in llm.calls].count("learner_gap_reading")
    assert readings == (2 if legacy_progress else 1)  # the recorded reading is never paid for twice
    assert [purpose for purpose, _ in llm.calls].count("learner_gap_prerequisite_draft") == 1


def test_rr_f1_a_recorded_edge_is_finished_after_the_judges_the_chooser_and_the_switch_change(
    tmp_path, monkeypatch,
):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    _fail_once(monkeypatch, gap_pipeline, "sync_vault_state")
    first = process_next_gap_job(root, repository, owner="t",
                                 clients=_clients(GapLLMFake(decide=word_match("eigenvalues"), needed="yes")),
                                 clock=_at(1))
    assert first.state == "retry_later"
    recorded = _jobs(repository)[0]["payload"]["edge"]
    append_config_toml(root, '[learner_text_gaps]\nchooser = "decider"\nadd_edges_enabled = false\n')
    later = GapLLMFake(decide=always("different"), needed="no")
    done = process_next_gap_job(root, repository, owner="t", clients=_clients(later), clock=_at(10))
    assert (done.state, done.action) == ("done", "matched_prerequisite")
    (row,) = _gaps(repository)
    assert (row["target_id"], row["edge_id"], row["chooser"]) == (
        "lo_eigen_basics", recorded["edge_id"], "context_model")
    assert row["detail"]["edge"] == "added" and row["detail"]["resumed"] == "edge"
    assert later.calls == []  # nothing judged, asked or read again
    assert reverse_gap(root, repository, row["id"], "undo_edge")["status"] == "reversed"
    assert recorded["edge_id"] not in {edge.id for edge in gap_actions.edges_on_disk(load_vault(root))}


@pytest.mark.parametrize("why", ["switched_off", "text_gone"])
def test_rr_f1_a_job_stopped_after_a_write_logs_the_write_as_failed_and_undoable(tmp_path, monkeypatch, why):
    root, repository, stuck, llm, written = _stuck_creation_written(tmp_path, monkeypatch)
    if why == "switched_off":
        append_config_toml(root, "[learner_text_gaps]\nenabled = false\n")
    else:
        stuck.stuck = False
    calls = len(llm.calls)
    stopped = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(10),
                                   stuck_source=stuck)
    assert (stopped.state, stopped.action) == ("failed", "failed") and stopped.gap_id
    assert len(llm.calls) == calls  # no paid call finishes it
    (row,) = _gaps(repository)
    assert (row["action"], row["created_learning_object_id"]) == ("failed", written) and row["edge_id"]
    assert [job["state"] for job in _jobs(repository)] == ["failed"]
    assert gap_actions.creations_today(repository, now_iso=row["created_at"]) == 1
    assert reverse_gap(root, repository, row["id"], "undo_creation", actor="owner")["status"] == "reversed"
    assert load_vault(root).learning_objects[written].status == "dormant"


def test_rr_f1_a_job_switched_off_before_any_write_is_still_skipped(tmp_path):
    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\nenabled = false\n")
    enqueue(repository, source_kind="stuck_answer", source_id=STUCK)
    skipped = process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(1),
                                   stuck_source=_StuckSource(stuck=True))
    assert (skipped.state, skipped.gap_id) == ("skipped", None) and _gaps(repository) == []


# -- F2: a gap read later never sets question-time "help before work" -------------------------------


def _signals(question_type, gaps):
    attempt = SimpleNamespace(attempt_id="att_1", lo_id="lo_diag", outcome=0.0, hints_used=0, assisted=False,
                              help_before_work=False, features=SimpleNamespace(subject_id="linear-algebra"))
    event = {"id": "q1", "kind": "tutor_question", "context": "practice", "attempt_id": "att_1",
             "seconds_into_attempt": 0, "question_type": question_type, "created_at": "2026-05-19T12:00:00Z",
             "received_at": "2026-05-19T12:00:00Z", "lo_ids": ["lo_diag"], "payload": {}}
    signals = derive_interaction_signals([event], (), [attempt], facet_to_lo={}, learner_gaps=gaps)
    return signals, [(s.signal_id, s.observed_at, s.help_before_work) for s in signals
                     if s.signal_type == "practice_assistance"]


def test_rr_f2_a_gap_read_later_adds_no_question_time_assistance():
    gap = {"id": "g1", "source_kind": "tutor_question", "source_id": "q1", "attempt_id": None,
           "target_id": "lo_eigen_basics", "target_subject_id": "linear-algebra",
           "created_at": "2026-05-22T12:00:00Z"}
    _, without = _signals(None, [])
    signals, with_gap = _signals(None, [gap])
    assert without == [] and with_gap == []
    # The gap still retargets the question, from when it was read.
    (target,) = [s for s in signals if s.signal_id == "question_event:q1:lo_eigen_basics"]
    assert target.observed_at == "2026-05-22T12:00:00Z"
    # A logged type still gives the question-time row, gap or not.
    _, logged = _signals("prerequisite", [gap])
    assert logged == [("question_event:q1:assistance", "2026-05-19T12:00:00Z", True)]


# -- F3: one text backing off does not stop the drain --------------------------------------------


def _two_texts(root, repository):
    first = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy", question="What's an eigenvalue again?")
    second = _ask(root, repository, GapTutor(BELIEF, question_type="verification"),
                  question="Since every matrix diagonalizes, why check?")
    for event_id in (first, second):
        enqueue(repository, source_kind="tutor_question", source_id=event_id)
    return first, second


@pytest.mark.parametrize("command", [False, True])
def test_rr_f3_a_failed_pair_backs_off_one_text_and_the_run_goes_on(tmp_path, command):
    root, repository = _vault(tmp_path)
    first, second = _two_texts(root, repository)
    llm = GapLLMFake(decide=always("different"), fail={"learner_gap_same_prerequisite"})
    factory = (lambda _vault: TextBudget.for_command(ReviewSpend(_big_caps()))) if command else None
    outcomes = run_pending(root, repository, owner="t", clients=_clients(llm), budget_factory=factory, clock=_at(1))
    assert [(o.source_id, o.state) for o in outcomes] == [(first, "retry_later"), (second, "done")]


def test_rr_f3_the_sidecar_drain_goes_on_past_a_text_backing_off(tmp_path):
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

    root, repository = _vault(tmp_path)
    first, second = _two_texts(root, repository)
    llm = GapLLMFake(decide=always("different"), fail={"learner_gap_same_prerequisite"})
    worker = PostAttemptWorker(autostart=False)
    worker.bind(lambda: (load_vault(root), repository.sqlite_path))
    worker.gap_clients = lambda _vault: _clients(llm)
    outcomes = worker.run_pending("gaps", clock=_at(1))
    assert [(o.source_id, o.state) for o in outcomes] == [(first, "retry_later"), (second, "done")]


# -- F4: queueing a stuck answer reads that one attempt -------------------------------------------


def _stuck_module(monkeypatch, rows, *, per_attempt=None):
    import sys
    import types

    scans: list[int] = []
    module = types.ModuleType("fake_stuck_module_rr")

    def stuck_answers(connection):
        scans.append(1)
        return rows

    module.stuck_answers = stuck_answers
    if per_attempt is not None:
        module.stuck_answer = per_attempt
    monkeypatch.setitem(sys.modules, "fake_stuck_module_rr", module)
    return scans


def _mark_stuck(repository, attempt_id):
    with closing(connect(repository.sqlite_path)) as connection, connection:
        connection.execute("ALTER TABLE practice_attempts ADD COLUMN declared_stuck INTEGER NOT NULL DEFAULT 0")
        connection.execute("UPDATE practice_attempts SET declared_stuck = 1 WHERE id = ?", (attempt_id,))


def _reading_judgment(repository, attempt_id, quote, *, supersedes=None, at="2026-05-19T12:00:00Z"):
    with repository.atomic():
        return append_judgment(
            repository.connection(), task="stuck_reading", left_kind="attempt", left_id=attempt_id, judge="llm",
            judge_model="fake/grader", prompt_version="blind-v1+stuck-v1", input_hash=f"h:{quote}",
            verdict=json.dumps({"describes_confusion": True, "confusion_quote": quote}), supersedes_id=supersedes,
            created_at=at,
        )


def test_rr_f4_a_stuck_answer_is_read_by_its_id_with_its_current_reading(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps.sources import StuckAnswersAdapter, stuck_text_for

    root, repository = _vault(tmp_path, sync=True)
    attempt = _self_graded(root, repository, minutes=1)
    _mark_stuck(repository, attempt.attempt_id)
    scans = _stuck_module(monkeypatch, [])
    adapter = StuckAnswersAdapter()
    adapter.module = "fake_stuck_module_rr"
    first = _reading_judgment(repository, attempt.attempt_id, "what an eigenvalue is")
    _reading_judgment(repository, attempt.attempt_id, "an eigenvalue", supersedes=first, at="2026-05-19T12:05:00Z")
    found = stuck_text_for(repository, attempt.attempt_id, adapter)
    assert found is not None and scans == []  # no scan of every stuck answer
    assert (found.attempt_id, found.learning_object_id, found.practice_item_id) == (
        attempt.attempt_id, "lo_diag", "pi_diag_easy")
    assert found.text == "I don't get what an eigenvalue is" and found.confusion_quote == "an eigenvalue"


def test_rr_f4_the_stuck_modules_own_per_attempt_reader_is_preferred(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps.sources import StuckAnswersAdapter, stuck_text_for

    root, repository = _vault(tmp_path, sync=True)
    attempt = _self_graded(root, repository, minutes=1)
    _mark_stuck(repository, attempt.attempt_id)
    asked: list[str] = []

    def stuck_answer(connection, attempt_id):
        asked.append(attempt_id)
        return {"attempt_id": attempt_id, "practice_item_id": "pi_diag_easy", "learning_object_id": "lo_diag",
                "subject_id": "linear-algebra", "has_text": True, "learner_answer_md": "from the module",
                "created_at": "2026-05-19T12:00:00Z", "reading": {"confusion_quote": "module"}}

    scans = _stuck_module(monkeypatch, [], per_attempt=stuck_answer)
    adapter = StuckAnswersAdapter()
    adapter.module = "fake_stuck_module_rr"
    found = stuck_text_for(repository, attempt.attempt_id, adapter)
    assert found is not None and (found.text, found.confusion_quote) == ("from the module", "module")
    assert asked == [attempt.attempt_id] and scans == []


# -- F5: a command's calls do not use up the live daily cap --------------------------------------


def test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap(tmp_path):
    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\nmax_calls_per_day = 1\n")
    first = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy", question="What's an eigenvalue again?")
    enqueue(repository, source_kind="tutor_question", source_id=first)
    llm = GapLLMFake(decide=word_match("eigenvalues"))
    shared = TextBudget.for_command(ReviewSpend(_big_caps()))
    (command,) = run_pending(root, repository, owner="cli", clients=_clients(llm), budget_factory=lambda _v: shared,
                             clock=_at(1))
    assert command.state == "done"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        owners = dict(connection.execute(
            "SELECT owner_kind, COUNT(*) FROM model_call_receipts WHERE parent_call_id IS NULL GROUP BY owner_kind"
        ).fetchall())
    assert owners.get(store.COMMAND_RECEIPT_OWNER, 0) >= 1 and store.PIPELINE_RECEIPT_OWNER not in owners
    assert calls_today(repository, clock=_at(1)) == 0
    second = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy", question="Eigenvalues: what?")
    enqueue(repository, source_kind="tutor_question", source_id=second)
    live = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(2))
    assert live.state == "done" and calls_today(repository, clock=_at(2)) >= 1


def test_rr_f5_gaps_run_reads_on_a_command_budget(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.diagnosis.text_gaps import jobs

    root, _repository = _vault(tmp_path)
    budgets: list[TextBudget] = []

    def capture(_root, _repository, *, owner, max_jobs, budget_factory):
        budgets.append(budget_factory(load_vault(root)))
        return []

    monkeypatch.setattr(jobs, "run_pending", capture)
    result = CliRunner().invoke(app, ["gaps", "run", "--vault", str(root), "--json"])
    assert result.exit_code == 0, result.output
    assert [budget.owner_kind for budget in budgets] == [store.COMMAND_RECEIPT_OWNER]


# -- F6: a tap counts only on the tapped answer --------------------------------------------------


def test_rr_f6_only_a_tap_on_a_belief_answer_is_counted(tmp_path):
    from learnloop.diagnosis.text_gaps.report import _card_taps

    _root, repository = _vault(tmp_path)

    def tap(left, right, key):
        with repository.atomic():
            append_judgment(repository.connection(), task="same_cause", left_kind="attempt", left_id=left,
                            right_kind="attempt", right_id=right, judge="learner_card", input_hash=key,
                            verdict="different", rationale="diagnosis card: not the same mistake")

    tap("att_later", "att_belief", "k1")  # a later answer's card that cites the belief answer
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert _card_taps(connection, {"att_belief"}, since=None) == 0
    tap("att_belief", "att_earlier", "k2")  # the belief answer's own card
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert _card_taps(connection, {"att_belief"}, since=None) == 1


# -- F7: an edge written before its origin was recorded follows the right switch -------------------


def _strip_edge_origins(root) -> None:
    """The edges as the first round wrote them: no ``provenance.origin``."""

    path = root / "concepts" / "relations.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for edge in data.get("edges") or []:
        provenance = edge.get("provenance")
        if isinstance(provenance, dict):
            provenance.pop("origin", None)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


@pytest.mark.parametrize("switch", ["create_prerequisites_enabled", "add_edges_enabled"])
def test_rr_f7_an_edge_without_a_recorded_origin_follows_its_own_switch(tmp_path, switch):
    root, repository = _vault(tmp_path)
    matched = _run(root, repository, _ask(root, repository, GapTutor(EIGEN_GAP)),
                   GapLLMFake(decide=word_match("eigenvalues"), needed="yes"))
    created = _run(root, repository, _ask(root, repository, GapTutor(EIGENVECTOR_GAP), question="An eigenvector?"),
                   GapLLMFake(decide=always("different")))
    assert matched["edge_id"] and created["edge_id"]
    _strip_edge_origins(root)
    assert {matched["edge_id"], created["edge_id"]} <= {edge.id for edge in load_vault(root).edges}
    append_config_toml(root, f"[learner_text_gaps]\n{switch} = false\n")
    loaded = {edge.id for edge in load_vault(root).edges}
    if switch == "create_prerequisites_enabled":
        assert created["edge_id"] not in loaded and matched["edge_id"] in loaded
    else:
        assert matched["edge_id"] not in loaded and created["edge_id"] in loaded
