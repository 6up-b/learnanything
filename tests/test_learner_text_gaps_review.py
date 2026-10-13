"""Learner-text gaps: regression tests for the Codex review findings (F1-F16).

Each test reproduces a failure path the first round's fakes missed. Every
model is a fake; no call leaves the process."""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.text_gaps import actions as gap_actions
from learnloop.diagnosis.text_gaps import pipeline as gap_pipeline
from learnloop.diagnosis.text_gaps.actions import add_prerequisite_edge, reverse_gap
from learnloop.diagnosis.text_gaps.contract import GapReading, LearnerText
from learnloop.diagnosis.text_gaps.jobs import calls_today, enqueue, process_next_gap_job, run_pending
from learnloop.diagnosis.text_gaps.judges import TextBudget
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, ReadingDeferred, process_learner_text
from learnloop.diagnosis.text_gaps.sources import StuckText, tutor_question_text
from learnloop.placement.state import load_placement_state, prerequisite_learning_objects
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import add_note, add_subject, load_vault
from learnloop.vault.writer import delete_concept_edge, upsert_concept_edge, upsert_learning_object, upsert_practice_item

from tests.helpers import NOW, NOW_ISO, append_config_toml, create_placement_vault
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake, GapTutor, always, seed_proposal, word_match

EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")
EIGENVECTOR_GAP = LearnerGap(prerequisite_name="Eigenvectors", prerequisite_line="Vectors a matrix only scales.",
                             kind="prerequisite")
BELIEF = LearnerGap(belief_statement="Every matrix can be diagonalized.", kind="misconception")
DAY = 24 * 60


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _iso(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _vault(tmp_path, *, version: str = "mvp-0.13", toml: str = "", sync: bool = False):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    if toml:
        append_config_toml(paths.root, toml)
    repository = Repository(paths.sqlite_path)
    if sync:
        sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    return paths.root, repository


def _ask(root, repository, tutor, *, item="pi_diag_easy", question="What is an eigenvalue?", minutes=0.0):
    return ask_question(load_vault(root), repository, tutor, context="practice", question_md=question,
                        practice_item_id=item, session_id="sess_1", clock=_at(minutes))["event_id"]


def _clients(llm=None, *, decider=None, tutor=None) -> PipelineClients:
    llm = llm or GapLLMFake()
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                           drafter=lambda: llm, tutor=(lambda: tutor) if tutor else None, embedder=None)


def _run(root, repository, event_id, llm, *, tutor=None, decider=None, minutes=0.0):
    text = tutor_question_text(load_vault(root), repository, event_id)
    return process_learner_text(root, repository, text, clients=_clients(llm, tutor=tutor, decider=decider),
                                clock=_at(minutes))


def _gaps(repository):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.gaps(connection)


def _jobs(repository):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.jobs(connection)


def _ledger(repository, task):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT left_kind, left_id, right_kind, right_id, judge, verdict FROM judgment_ledger WHERE task = ? "
            "ORDER BY rowid", (task,))]


def _created_los(root):
    return sorted(lo for lo in load_vault(root).learning_objects if lo.startswith("lo_ltg_"))


def _source_note(root):
    add_note(root, "linear-algebra", "la_source", "Diagonalization source",
             "A matrix with n independent eigenvectors diagonalizes.", source_type="canonical_source",
             related_los=["lo_diag"], clock=FrozenClock(NOW))


# -- F1: only settled verdicts decide -------------------------------------------------------------


def _fails_on_the_true_match(first: str, second: str) -> str:
    if "eigenvalues" in first and "eigenvalues" in second:
        raise RuntimeError("transient judge failure on the true match")
    return "different"


def test_f1_a_failed_pair_on_the_true_match_never_creates_and_the_retry_matches(tmp_path):
    root, repository = _vault(tmp_path)
    tutor = GapTutor(EIGEN_GAP)
    event_id = _ask(root, repository, tutor, item="pi_spec_easy", question="What's an eigenvalue again?")
    with pytest.raises(ReadingDeferred) as raised:
        _run(root, repository, event_id, GapLLMFake(decide=_fails_on_the_true_match, proposal=seed_proposal()),
             tutor=tutor)
    assert not raised.value.spend and "lo_eigen_basics (failed)" in raised.value.reason
    assert _gaps(repository) == [] and _created_los(root) == []
    row = _run(root, repository, event_id, GapLLMFake(decide=word_match("eigenvalues")), tutor=tutor)
    assert (row["action"], row["target_id"]) == ("matched_prerequisite", "lo_eigen_basics")


def test_f1_a_fenced_pair_is_not_a_verdict():
    from learnloop.matching.judge import JudgedPair
    from learnloop.matching.kinds import Subject

    left = Subject(kind="learner_gap", id="q", text="x", content_hash="h")
    right = Subject(kind="learning_object", id="lo", text="y", content_hash="h")
    fenced = JudgedPair(left, right, "fenced", verdict="different", error="lease_lost")
    assert gap_pipeline._verdicts([fenced]) == {}
    assert gap_pipeline._unsettled([fenced]) == [{"id": "lo", "status": "fenced", "error": "lease_lost"}]


# -- F2: a spend stop never finalizes a text --------------------------------------------------------


def test_f2_a_spend_stop_leaves_both_texts_queued_and_stops_the_run(tmp_path):
    root, repository = _vault(tmp_path)
    for question in ("What's an eigenvalue again?", "Eigenvalues: what are they?"):
        event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy", question=question)
        enqueue(repository, source_kind="tutor_question", source_id=event_id)
    llm = GapLLMFake(decide=word_match("eigenvalues"))
    shared = TextBudget(ReviewSpend(SpendCaps(max_calls=1, max_candidates=1, max_pairs=1, max_retries=0,
                                              max_total_tokens=100_000, max_estimated_usd=1.0)))
    outcomes = run_pending(root, repository, owner="t", clients=_clients(llm), budget_factory=lambda _v: shared,
                           clock=_at(1))
    assert [outcome.state for outcome in outcomes] == ["deferred"]  # the run stops at the first stop
    assert _gaps(repository) == []
    assert [(job["state"], job["attempt_count"]) for job in _jobs(repository)] == [("queued", 0), ("queued", 0)]
    # The next run (a fresh budget) reads both; the paid pair is reused.
    fresh = run_pending(root, repository, owner="t", clients=_clients(llm), clock=_at(2))
    assert [outcome.state for outcome in fresh] == ["done", "done"]
    assert {row["action"] for row in _gaps(repository)} == {"matched_prerequisite"}


def test_f2_a_refused_draft_is_deferred_not_logged_unmatched(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGENVECTOR_GAP))
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    llm = GapLLMFake(decide=always("different"))

    class _MeteredDrafter(GapLLMFake):
        provider_type = "openai_chat"

    # The judge is on the subscription; the metered draft has no dollars left.
    shared = TextBudget(ReviewSpend(SpendCaps(max_calls=50, max_candidates=50, max_pairs=50, max_retries=0,
                                              max_total_tokens=1_000_000, max_estimated_usd=0.0),
                                    price_per_million=1.0))
    clients = PipelineClients(judge=lambda: llm, drafter=lambda: _MeteredDrafter(), embedder=None)
    (outcome,) = run_pending(root, repository, owner="t", clients=clients, budget_factory=lambda _v: shared,
                             clock=_at(1))
    assert outcome.state == "deferred" and "refused" in outcome.error
    assert _gaps(repository) == [] and _created_los(root) == []


# -- F3: crash-safe writes ------------------------------------------------------------------------------


def _fail_once(monkeypatch, module, name):
    original = getattr(module, name)
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError(f"{name} failed once")
        return original(*args, **kwargs)

    monkeypatch.setattr(module, name, flaky)
    return calls


def test_f3_a_creation_retried_after_a_failed_sync_writes_once_and_is_logged(tmp_path, monkeypatch):
    root, repository = _vault(tmp_path)
    tutor = GapTutor(EIGENVECTOR_GAP)
    event_id = _ask(root, repository, tutor)
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    llm = GapLLMFake(decide=always("different"), proposal=seed_proposal())
    _fail_once(monkeypatch, gap_actions, "sync_vault_state")
    first = process_next_gap_job(root, repository, owner="t", clients=_clients(llm, tutor=tutor), clock=_at(1))
    assert first.state == "retry_later" and _gaps(repository) == []
    (written,) = _created_los(root)  # the LO and its edge were written before the sync failed
    progress = _jobs(repository)[0]["payload"]["created"]
    assert progress["learning_object_id"] == written and progress["edge_id"]
    second = process_next_gap_job(root, repository, owner="t", clients=_clients(llm, tutor=tutor), clock=_at(10))
    assert second.state == "done" and second.action == "created_prerequisite"
    (row,) = _gaps(repository)
    assert _created_los(root) == [written] and row["created_learning_object_id"] == written
    assert row["edge_id"] == progress["edge_id"] and row["edge_id"] in {e.id for e in load_vault(root).edges}
    assert [purpose for purpose, _ in llm.calls].count("learner_gap_prerequisite_draft") == 1


def test_f3_a_matched_edge_retried_after_a_failed_sync_is_recorded_and_undoable(tmp_path, monkeypatch):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    llm = GapLLMFake(decide=word_match("eigenvalues"), needed="yes")
    _fail_once(monkeypatch, gap_pipeline, "sync_vault_state")
    assert process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(1)).state == "retry_later"
    recorded = _jobs(repository)[0]["payload"]["edge"]
    assert recorded["edge_id"] in {edge.id for edge in load_vault(root).edges}
    done = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(10))
    assert done.state == "done"
    (row,) = _gaps(repository)
    assert row["edge_id"] == recorded["edge_id"] and row["detail"]["edge"] == "added"
    assert [purpose for purpose, _ in llm.calls].count("learner_gap_prerequisite_needed") == 1
    assert reverse_gap(root, repository, row["id"], "undo_edge")["status"] == "reversed"
    assert recorded["edge_id"] not in {edge.id for edge in load_vault(root).edges}


def test_f3_a_belief_candidate_commits_with_its_ledger_row(tmp_path, monkeypatch):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(BELIEF, question_type="verification"),
                    question="Since every matrix diagonalizes, why check?")
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    _fail_once(monkeypatch, store, "insert_gap")
    assert process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(1)).state == "retry_later"
    assert repository.misconception_candidates_for_learning_object("lo_diag") == []
    assert process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(10)).state == "done"
    (candidate,) = repository.misconception_candidates_for_learning_object("lo_diag")
    assert _gaps(repository)[0]["target_id"] == candidate["id"]


def test_f3_a_sighting_is_counted_once_across_a_retry(tmp_path, monkeypatch):
    root, repository = _vault(tmp_path)
    candidate_id = repository.insert_misconception_candidate(
        learning_object_id="lo_diag", statement="All matrices are diagonalizable.",
        statement_normalized="all matrices are diagonalizable", occurrence_count=1,
    )
    event_id = _ask(root, repository, GapTutor(BELIEF), question="Every matrix diagonalizes, right?")
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    _fail_once(monkeypatch, store, "insert_gap")
    llm = GapLLMFake(decide=always("same"))
    process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(1))
    process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(10))
    assert repository.misconception_candidate_by_id(candidate_id)["occurrence_count"] == 2


def test_f3_a_job_that_gives_up_after_writing_names_the_creation_and_the_owner_can_undo_it(tmp_path, monkeypatch):
    import learnloop.diagnosis.text_gaps.jobs as jobs

    root, repository = _vault(tmp_path)
    tutor = GapTutor(EIGENVECTOR_GAP)
    event_id = _ask(root, repository, tutor)
    enqueue(repository, source_kind="tutor_question", source_id=event_id)

    def seed_down(*_args, **_kwargs):
        raise RuntimeError("seed path down")

    monkeypatch.setattr(gap_pipeline, "_seed", seed_down)
    llm = GapLLMFake(decide=always("different"))
    states = [process_next_gap_job(root, repository, owner="t", clients=_clients(llm, tutor=tutor),
                                   clock=_at(1 + attempt * 600)).state for attempt in range(jobs.MAX_ATTEMPTS)]
    assert states == ["retry_later", "retry_later", "failed"]
    (row,) = _gaps(repository)
    (created,) = _created_los(root)
    assert (row["action"], row["created_learning_object_id"]) == ("failed", created) and row["edge_id"]
    assert gap_actions.creations_today(repository, now_iso=_iso(1)) == 1  # it counts toward the daily cap
    assert reverse_gap(root, repository, row["id"], "undo_creation", actor="owner")["status"] == "reversed"
    assert load_vault(root).learning_objects[created].status == "dormant"


# -- F4: no grounded subject, no vault-wide candidates --------------------------------------------------


def test_f4_without_a_grounded_subject_only_the_anchors_are_judged_and_nothing_is_created(tmp_path):
    root, repository = _vault(tmp_path)
    add_subject(root, "physics", "Physics", clock=FrozenClock(NOW))
    upsert_learning_object(root, {
        "id": "lo_phys_waves", "title": "Waves", "subjects": ["physics"], "concept": "waves",
        "knowledge_type": "definition", "status": "active", "summary": "Waves.",
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })
    text = LearnerText(
        source_kind="tutor_question", source_id="q_two_subjects", text="What's an eigenvalue?", context_judge="tutor",
        created_at=NOW_ISO, subject_id=None, anchor_learning_object_ids=("lo_diag", "lo_phys_waves"),
        reading=GapReading.from_gap(EIGEN_GAP, judge="llm", judge_model="fake/tutor", prompt_version="v"),
    )
    llm = GapLLMFake(decide=always("different"))
    row = process_learner_text(root, repository, text, clients=_clients(llm), clock=FrozenClock(NOW))
    judged = " ".join(str(payload["context"]) for purpose, payload in llm.calls
                      if purpose == "learner_gap_same_prerequisite")
    assert "Eigenvalues" not in judged.replace("'name': 'Eigenvalues'", "")  # lo_eigen_basics never shown
    assert row["detail"]["candidates"]["by_basis"] == {"item": 2}
    assert row["detail"]["candidates"]["grounded_subject"] is None
    assert (row["action"], row["detail"]["reason"]) == ("unmatched_prerequisite", "no_subject")
    assert _created_los(root) == []


# -- F5: several "same" verdicts, or the item's own LO -------------------------------------------------


def test_f5_several_same_verdicts_are_ambiguous_and_target_nothing(tmp_path):
    root, repository = _vault(tmp_path, sync=True)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")
    row = _run(root, repository, event_id, GapLLMFake(decide=always("same")))
    assert (row["action"], row["target_id"], row["detail"]["reason"]) == ("unmatched_prerequisite", None, "ambiguous")
    assert len(row["detail"]["same"]) > 1
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert store.check_advances(connection) == []


def test_f5_a_match_on_the_items_own_lo_is_no_prerequisite_target(tmp_path):
    from learnloop.field.signals import load_interaction_signals

    root, repository = _vault(tmp_path)
    spectral = LearnerGap(prerequisite_name="Spectral theorem", prerequisite_line="Symmetric matrices diagonalize.",
                          kind="prerequisite")
    event_id = _ask(root, repository, GapTutor(spectral), item="pi_spec_easy")
    row = _run(root, repository, event_id, GapLLMFake(decide=word_match("spectral")))
    assert (row["action"], row["target_id"], row["detail"]["reason"]) == (
        "unmatched_prerequisite", None, "own_learning_object")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        signals = load_interaction_signals(connection, load_vault(root), ())
    assert not [s for s in signals if s.lo_id == "lo_spectral" and s.signal_type == "prerequisite"]


# -- F6: a gap target is available from when the gap was read -------------------------------------------


def test_f6_a_question_retargeted_by_a_later_reading_is_observed_at_the_reading(tmp_path):
    from learnloop.field.signals import SIGNAL_VERSION, load_interaction_signals

    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), minutes=0)
    row = _run(root, repository, event_id, GapLLMFake(decide=word_match("eigenvalues"), needed="no"),
               minutes=3 * DAY)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        signals = load_interaction_signals(connection, load_vault(root), ())
    (signal,) = [s for s in signals if s.signal_id.startswith(f"question_event:{event_id}:")]
    assert signal.lo_id == "lo_eigen_basics" and signal.observed_at == row["created_at"] == _iso(3 * DAY)
    assert SIGNAL_VERSION == "interaction-signals-v2"


# -- F8: stuck answers are queued when they are recorded -----------------------------------------------


class _StuckSource:
    """The stuck marker as a fake: ``stuck`` says whether the next answer is one."""

    def __init__(self, *, stuck: bool = False):
        self.stuck = stuck
        self.lookups: list[str] = []

    def stuck_texts(self, connection):
        raise AssertionError("recording an answer never scans every stuck answer")

    def stuck_text(self, connection, attempt_id):
        self.lookups.append(attempt_id)
        if not self.stuck:
            return None
        return StuckText(attempt_id=attempt_id, practice_item_id="pi_diag_easy", learning_object_id="lo_diag",
                         subject_id="linear-algebra", text="I don't get what an eigenvalue is", created_at=NOW_ISO)


def _self_graded(root, repository, *, minutes, points=0.0, item="pi_diag_easy", complete=False):
    """One recorded answer; ``complete`` also runs the doors' post-attempt pipeline."""

    from learnloop.attempts.post_attempt import run_post_attempt_pipeline

    grade = SelfGradeInput(criterion_points={"correctness": points}, confidence=2)
    result = complete_self_graded_attempt(
        load_vault(root), repository,
        AttemptDraft(practice_item_id=item, learner_answer_md="I don't get what an eigenvalue is", hints_used=0,
                     attempt_type="independent_attempt"),
        grade, clock=_at(minutes),
    )
    if complete:
        run_post_attempt_pipeline(load_vault(root), repository, result=result, self_grade=grade, clock=_at(minutes))
    return result


def test_f8_a_stuck_answer_is_queued_at_recording_without_a_diagnosis(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import sources

    root, repository = _vault(tmp_path, sync=True, toml="[diagnosis]\nsplit_enabled = false\n")
    stuck = _StuckSource()
    monkeypatch.setattr(sources, "DEFAULT_STUCK_SOURCE", stuck)
    first = _self_graded(root, repository, minutes=1, complete=True)
    assert _jobs(repository) == [] and stuck.lookups == [first.attempt_id]
    stuck.stuck = True
    second = _self_graded(root, repository, minutes=2, points=4.0, complete=True)  # right, never diagnosed
    assert [(job["source_kind"], job["source_id"]) for job in _jobs(repository)] == [
        ("stuck_answer", second.attempt_id)]


def test_f8_the_adapter_reads_the_marker_before_scanning(tmp_path, monkeypatch):
    import sys
    import types

    from learnloop.diagnosis.text_gaps.sources import StuckAnswersAdapter, stuck_text_for

    root, repository = _vault(tmp_path, sync=True)
    attempt = _self_graded(root, repository, minutes=1)
    with closing(connect(repository.sqlite_path)) as connection, connection:
        connection.execute("ALTER TABLE practice_attempts ADD COLUMN declared_stuck INTEGER NOT NULL DEFAULT 0")
    scans: list[int] = []
    module = types.ModuleType("fake_stuck_module")

    def stuck_answers(connection):
        scans.append(1)
        return [{"attempt_id": attempt.attempt_id, "practice_item_id": "pi_diag_easy", "learning_object_id": "lo_diag",
                 "subject_id": "linear-algebra", "has_text": True, "learner_answer_md": "confused",
                 "created_at": NOW_ISO, "reading": {"confusion_quote": "confused"}}]

    module.stuck_answers = stuck_answers
    monkeypatch.setitem(sys.modules, "fake_stuck_module", module)
    adapter = StuckAnswersAdapter()
    adapter.module = "fake_stuck_module"
    assert stuck_text_for(repository, attempt.attempt_id, adapter) is None and scans == []
    with closing(connect(repository.sqlite_path)) as connection, connection:
        connection.execute("UPDATE practice_attempts SET declared_stuck = 1 WHERE id = ?", (attempt.attempt_id,))
    found = stuck_text_for(repository, attempt.attempt_id, adapter)
    # Read by its id, never by scanning every stuck answer (re-review F4;
    # its reading: test_rr_f4_a_stuck_answer_is_read_by_its_id_with_its_current_reading).
    assert found is not None and found.text == "I don't get what an eigenvalue is" and scans == []


def test_f8_a_diagnosis_no_longer_scans_stuck_answers(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import jobs, sources

    root, repository = _vault(tmp_path)
    monkeypatch.setattr(sources, "DEFAULT_STUCK_SOURCE", _StuckSource(stuck=True))
    queued = jobs.enqueue_after_diagnosis(load_vault(root), repository, attempt_id="att_1",
                                          diagnosis={"id": "diag_1", "mode": "live", "status": "completed"})
    assert len(queued) == 1 and _jobs(repository)[0]["source_kind"] == "diagnosis"


# -- F9: every reversal is a verdict --------------------------------------------------------------------


def test_f9_undoing_an_edge_or_a_creation_is_a_ledger_verdict(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))
    edge_row = _run(root, repository, event_id, GapLLMFake(decide=word_match("eigenvalues"), needed="yes"))
    reverse_gap(root, repository, edge_row["id"], "undo_edge")
    tutor = GapTutor(EIGENVECTOR_GAP)
    created_event = _ask(root, repository, tutor, question="What is an eigenvector?")
    created_row = _run(root, repository, created_event, GapLLMFake(decide=always("different")))
    reverse_gap(root, repository, created_row["id"], "undo_creation", actor="owner")
    needed = [row for row in _ledger(repository, "prerequisite_needed") if row[4] in ("learner_card", "owner")]
    assert needed == [
        ("learning_object", "lo_eigen_basics", "practice_item", "pi_diag_easy", "learner_card", "no"),
        ("learning_object", created_row["created_learning_object_id"], "practice_item", "pi_diag_easy", "owner", "no"),
    ]


def test_f9_an_owner_not_what_i_meant_is_an_owner_verdict(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(BELIEF), question="Every matrix diagonalizes?")
    row = _run(root, repository, event_id, GapLLMFake())
    reverse_gap(root, repository, row["id"], "not_this_belief", actor="owner")
    assert [(r[4], r[5]) for r in _ledger(repository, "same_belief")] == [("owner", "different")]


# -- F10: the edge switch neutralizes added edges; the cycle check is under the lock --------------------


def test_f10_switching_edges_off_removes_their_effect_and_keeps_them_in_the_file(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))
    row = _run(root, repository, event_id, GapLLMFake(decide=word_match("eigenvalues"), needed="yes"))
    assert row["edge_id"] and "lo_eigen_basics" in prerequisite_learning_objects(load_vault(root), "lo_diag")
    append_config_toml(root, "[learner_text_gaps]\nadd_edges_enabled = false\n")
    vault = load_vault(root)
    assert "lo_eigen_basics" not in prerequisite_learning_objects(vault, "lo_diag")
    assert row["edge_id"] not in {edge.id for edge in vault.edges}
    assert row["edge_id"] in {edge.id for edge in gap_actions.edges_on_disk(vault)}


def test_f10_a_creations_edge_follows_the_creation_switch(tmp_path):
    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGENVECTOR_GAP))
    row = _run(root, repository, event_id, GapLLMFake(decide=always("different")))
    assert row["edge_id"] in {edge.id for edge in load_vault(root).edges}
    append_config_toml(root, "[learner_text_gaps]\ncreate_prerequisites_enabled = false\n")
    assert row["edge_id"] not in {edge.id for edge in load_vault(root).edges}


def test_f10_the_cycle_is_rechecked_on_the_file_inside_the_lock(tmp_path):
    root, _repository = _vault(tmp_path)
    stale = load_vault(root)  # loaded when the reading started
    # Meanwhile the graph editor makes eigenvalues build on diagonalization.
    upsert_concept_edge(root, {"id": "edge_editor", "relation_type": "prerequisite", "source": "diagonalization",
                               "target": "eigenvalues", "created_at": NOW_ISO, "updated_at": NOW_ISO})
    text = LearnerText(source_kind="tutor_question", source_id="q", text="?", context_judge="tutor", created_at=NOW_ISO)
    edge_id, status = add_prerequisite_edge(root, stale, prerequisite_lo="lo_eigen_basics", dependent_lo="lo_diag",
                                            text=text, rationale="r")
    assert (edge_id, status) == (None, "refused_cycle")


# -- F11: the report answers "Decider or LLM" on outcomes ----------------------------------------------


def _accept_seed(root, learning_object_id, item_id="pi_ltg_seed_accepted"):
    upsert_practice_item(root, {
        "id": item_id, "learning_object_id": learning_object_id, "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0}, "prompt": "What is an eigenvector of a matrix A?",
        "expected_answer": "A nonzero vector v with Av = lambda v.",
        "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4,
                                                           "description": "Defines it."}], "fatal_errors": []},
        "provenance": {"origin": "human", "source_refs": []}, "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })
    return item_id


def _created_and_checked(tmp_path, points, *, toml=""):
    root, repository = _vault(tmp_path, sync=True, toml="[diagnosis]\nsplit_enabled = false\n" + toml)
    _source_note(root)
    tutor = GapTutor(EIGENVECTOR_GAP)
    event_id = _ask(root, repository, tutor)
    row = _run(root, repository, event_id, GapLLMFake(decide=always("different"), proposal=seed_proposal()),
               tutor=tutor)
    created = row["created_learning_object_id"]
    item_id = _accept_seed(root, created)
    sync_vault_state(load_vault(root), repository, clock=_at(5))
    _self_graded(root, repository, minutes=DAY + 10, points=points, item=item_id)
    return root, repository, row, created


def test_f13_a_created_los_check_passed_goes_to_maintenance(tmp_path):
    root, repository, _row, created = _created_and_checked(tmp_path, 4.0)
    state = load_placement_state(load_vault(root), repository, now_iso=_iso(DAY + 20))
    assert state.intent_by_lo[created].intent == "maintenance"


def test_f13_a_created_los_check_failed_goes_to_learning(tmp_path):
    root, repository, _row, created = _created_and_checked(tmp_path, 0.0)
    state = load_placement_state(load_vault(root), repository, now_iso=_iso(DAY + 20))
    assert state.intent_by_lo[created].intent == "learning"


def test_f11_first_checks_per_chooser_survive_the_creation_switch_and_since_windows_everything(tmp_path):
    from learnloop.diagnosis.text_gaps.report import build_report

    root, repository, _row, _created = _created_and_checked(tmp_path, 4.0)
    append_config_toml(root, "[learner_text_gaps]\ncreate_prerequisites_enabled = false\n")
    report = build_report(load_vault(root), repository)
    created = report["created_prerequisites"]
    assert (created["commitments"], created["passed"]) == (1, 1)
    assert created["by_chooser"]["tutor"]["passed"] == 1
    assert report["judges"]["same_prerequisite"]["pairs_judged_by_both"] == 0
    later = build_report(load_vault(root), repository, since="2999-01-01T00:00:00Z")
    assert later["learner_texts"] == 0 and later["created_prerequisites"]["commitments"] == 0
    assert later["jobs"] == {}


def test_f11_pair_agreement_honours_since(tmp_path):
    from learnloop.diagnosis.text_gaps.report import build_report

    root, repository = _vault(tmp_path)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")
    _run(root, repository, event_id, GapLLMFake(decide=word_match("eigenvalues")),
         decider=ChoiceDecider(kind="prerequisite", pair=word_match("eigenvalues")))
    assert build_report(load_vault(root), repository)["judges"]["same_prerequisite"]["pairs_judged_by_both"] > 0
    later = build_report(load_vault(root), repository, since="2999-01-01T00:00:00Z")
    assert later["judges"]["same_prerequisite"]["pairs_judged_by_both"] == 0


# -- F12: a live daily cap; the seed unit on the costlier route ----------------------------------------


def test_f12_the_live_daily_cap_defers_to_the_next_day_without_using_a_retry(tmp_path):
    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\nmax_calls_per_day = 0\n")
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy")
    enqueue(repository, source_kind="tutor_question", source_id=event_id)
    outcome = process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(1))
    assert (outcome.state, outcome.error) == ("deferred", "daily_cap")
    (job,) = _jobs(repository)
    assert (job["state"], job["attempt_count"], job["not_before"]) == ("queued", 0, "2026-05-20T00:00:00Z")
    assert process_next_gap_job(root, repository, owner="t", clients=_clients(), clock=_at(2)) is None


def test_f12_the_daily_cap_counts_the_pipelines_receipts(tmp_path):
    root, repository = _vault(tmp_path, toml="[learner_text_gaps]\nmax_calls_per_day = 1\n")
    for question in ("What's an eigenvalue again?", "Eigenvalues: what are they?"):
        enqueue(repository, source_kind="tutor_question",
                source_id=_ask(root, repository, GapTutor(EIGEN_GAP), item="pi_spec_easy", question=question))
    llm = GapLLMFake(decide=word_match("eigenvalues"))
    first = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(1))
    assert first.state == "done" and calls_today(repository, clock=_at(1)) >= 1
    second = process_next_gap_job(root, repository, owner="t", clients=_clients(llm), clock=_at(2))
    assert (second.state, second.error) == ("deferred", "daily_cap")


def test_f12_the_seed_unit_is_admitted_on_a_metered_tutor_route(tmp_path):
    root, _repository = _vault(tmp_path, toml="[learner_text_gaps]\nmetered_price_per_million = 1.0\n")
    budget = TextBudget.for_text(load_vault(root))

    class _MeteredTutor:
        provider_name, provider_type, model = "openrouter", "openai_chat", "some/metered-model"

    budget.register_llm(gap_pipeline.TUTOR_ROUTE, _MeteredTutor())
    budget.register_llm(gap_pipeline.DRAFT_ROUTE, GapLLMFake())
    assert gap_pipeline._seed_route(budget) == gap_pipeline.TUTOR_ROUTE
    subscription = TextBudget.for_text(load_vault(root))
    subscription.register_llm(gap_pipeline.TUTOR_ROUTE, GapTutor(None))
    subscription.register_llm(gap_pipeline.DRAFT_ROUTE, GapLLMFake())
    assert gap_pipeline._seed_route(subscription) == gap_pipeline.DRAFT_ROUTE


# -- F13: the whole pipeline's kill switch equals the predecessor --------------------------------------


def test_f13_the_pipeline_switched_off_queues_exactly_as_the_predecessor_version(tmp_path):
    from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue

    def queue_after_a_question(name, version, toml):
        paths = create_placement_vault(tmp_path / name, version=version)
        append_config_toml(paths.root, toml)
        repository = Repository(paths.sqlite_path)
        sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
        event_id = _ask(paths.root, repository, GapTutor(EIGEN_GAP))
        text = tutor_question_text(load_vault(paths.root), repository, event_id)
        assert process_learner_text(paths.root, repository, text, clients=_clients(
            GapLLMFake(decide=word_match("eigenvalues"))), clock=_at(1)) is None
        queue = build_due_queue(load_vault(paths.root), repository, clock=_at(DAY), session=SchedulerSession(),
                                persist_explanations=False)
        return [(entry.practice_item_id, sorted(k for k, v in entry.components.items() if v)) for entry in queue]

    off = queue_after_a_question("off", "mvp-0.13", "[learner_text_gaps]\nenabled = false\n")
    predecessor = queue_after_a_question("predecessor", "mvp-0.12", "[learner_text_gaps]\nenabled = false\n")
    assert off == predecessor and off


# -- F14: one gap observation per answer ---------------------------------------------------------------


def test_f14_a_stuck_answer_and_its_diagnosis_give_one_observation():
    from learnloop.field.signals import derive_interaction_signals

    gaps = [
        {"id": "g_stuck", "source_kind": "stuck_answer", "source_id": "att_1", "attempt_id": "att_1",
         "target_id": "lo_eigen_basics", "target_subject_id": "linear-algebra", "created_at": "2026-05-19T12:01:00Z"},
        {"id": "g_diag", "source_kind": "diagnosis", "source_id": "diag_1", "attempt_id": "att_1",
         "target_id": "lo_eigen_basics", "target_subject_id": "linear-algebra", "created_at": "2026-05-19T12:05:00Z"},
        {"id": "g_other", "source_kind": "diagnosis", "source_id": "diag_2", "attempt_id": "att_2",
         "target_id": "lo_spectral", "target_subject_id": "linear-algebra", "created_at": "2026-05-19T12:06:00Z"},
    ]
    signals = derive_interaction_signals((), (), (), facet_to_lo={}, learner_gaps=gaps)
    assert sorted(signal.signal_id for signal in signals) == ["learner_gap:g_other", "learner_gap:g_stuck"]


# -- F16: polling a reading whose edge is gone does not reload every time ------------------------------


def test_f16_a_removed_edge_reloads_once_and_bumps_nothing(tmp_path, monkeypatch):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import learner_gaps as rpc
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

    root, repository = _vault(tmp_path, sync=True)
    event_id = _ask(root, repository, GapTutor(EIGEN_GAP))
    row = _run(root, repository, event_id, GapLLMFake(decide=word_match("eigenvalues"), needed="yes"))
    delete_concept_edge(root, row["edge_id"])  # removed in the graph editor, not undone
    ctx = SidecarContext()
    ctx.post_attempt_worker = PostAttemptWorker(autostart=False)
    ctx.load(root, maintenance=False)
    reloads: list[int] = []
    original = ctx.reload
    monkeypatch.setattr(ctx, "reload", lambda **kwargs: (reloads.append(1), original(**kwargs))[1])
    revision = repository.queue_revision()["revision"]
    for _poll in range(3):
        assert rpc.get_learner_text_gap(ctx, rpc.GetLearnerTextGapInput(source_id=event_id))["status"] == "done"
    assert len(reloads) == 1
    assert repository.queue_revision()["revision"] == revision
