"""Learner-text gaps composed with what merged before them (mvp-0.16).

* The stuck prompt (mvp-0.13): stuck text is read through main's own
  ``learnloop.attempts.stuck`` module, one attempt by its id
  (``stuck_answer``), never a scan of every stuck answer; an empty
  "I'm stuck" (a deterministic zero, no model call) is no learner text.
* Phase 6 placement reads derived interaction signals: a gap's
  question-time prerequisite target is a signal only at mvp-0.16 (the
  version set), and with the successor's kill switch off serving is
  mvp-0.15's exactly.
* A stuck answer that describes confusion keeps main's ``stuck_confusion``
  row (the item's own LO, no mass) next to its one learner-gap observation
  (another LO).
* Slice 2 T6: the tutor's verified source spans and the tutor's named gap
  are both persisted on the same answer.
* Daily-loop DL1: a check a learner-text gap brought forward, or a created
  prerequisite's one check, is labelled as what it is in the plan.

Every model is a fake.
"""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json

import pytest

from learnloop.attempts import stuck
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job, sweep_backlog
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, process_learner_text
from learnloop.diagnosis.text_gaps.sources import stuck_text_for, tutor_question_text
from learnloop.field.signals import STUCK_CONFUSION_SIGNAL, load_interaction_signals
from learnloop.placement.signals import taught_first_learning_objects
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.text_gap_fakes import GapLLMFake, GapTutor, word_match

EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")
STUCK_TEXT = "I don't get what an eigenvalue is"


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _vault(tmp_path, *, version: str = "mvp-0.16", toml: str = ""):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    if toml:
        append_config_toml(paths.root, toml)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    return paths, repository


def _clients(llm) -> PipelineClients:
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, tutor=None,
                           embedder=None)


def _stuck_answer(paths, repository, text: str, *, minutes: float = 1, complete: bool = True):
    """One real stuck answer through main's door (self-graded: no model)."""

    vault = load_vault(paths.root)
    grade = SelfGradeInput(criterion_points={"correctness": 0.0}, confidence=2)
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_diag_easy", learner_answer_md=text, attempt_type="independent_attempt",
                     declared_stuck=True),
        grade, clock=_at(minutes),
    )
    if complete:
        run_post_attempt_pipeline(vault, repository, result=result, self_grade=grade, clock=_at(minutes))
    return result


def _reading(repository, attempt_id: str, quote: str, *, supersedes: str | None = None,
             at: str = "2026-05-19T12:00:00Z") -> str:
    """The grader's stuck reading as main writes it (task ``stuck_reading``)."""

    with repository.atomic():
        return append_judgment(
            repository.connection(), task=stuck.STUCK_READING_JUDGMENT_TASK, left_kind="attempt",
            left_id=attempt_id, judge="llm", judge_model="fake/grader", prompt_version="blind-v1+stuck-v1",
            input_hash=f"h:{quote}",
            verdict=json.dumps({"attempts_answer": False, "describes_confusion": True, "confusion_quote": quote,
                                "quote_verified": True}),
            supersedes_id=supersedes, created_at=at,
        )


def _jobs(repository):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_kind, source_id FROM learner_text_gap_jobs ORDER BY created_at, id")]


# -- the stuck prompt: main's own per-attempt reader ------------------------------------------


def test_stuck_answer_reads_one_attempt_exactly_as_stuck_answers_does(tmp_path):
    paths, repository = _vault(tmp_path)
    ordinary = complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id="pi_diag_easy", learner_answer_md="lambda = 2",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 2.0}, confidence=2), clock=_at(0),
    )
    first = _stuck_answer(paths, repository, STUCK_TEXT, minutes=1, complete=False)
    empty = _stuck_answer(paths, repository, "   ", minutes=2, complete=False)
    judged = _reading(repository, first.attempt_id, "what an eigenvalue")
    _reading(repository, first.attempt_id, "an eigenvalue", supersedes=judged, at="2026-05-19T12:05:00Z")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        every = {row["attempt_id"]: row for row in stuck.stuck_answers(connection)}
        one = stuck.stuck_answer(connection, first.attempt_id)
        none = stuck.stuck_answer(connection, empty.attempt_id)
        assert stuck.stuck_answer(connection, ordinary.attempt_id) is None
        assert stuck.stuck_answer(connection, "no-such-attempt") is None
    assert set(every) == {first.attempt_id, empty.attempt_id}
    assert one == every[first.attempt_id] and none == every[empty.attempt_id]
    assert one["reading"]["confusion_quote"] == "an eigenvalue" and one["has_text"]
    assert none["has_text"] is False


def test_the_default_adapter_reads_mains_stuck_module_by_id_without_a_scan(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    result = _stuck_answer(paths, repository, STUCK_TEXT, complete=False)
    _reading(repository, result.attempt_id, "what an eigenvalue")
    asked: list[str] = []
    per_attempt = stuck.stuck_answer

    def spy(connection, attempt_id):
        asked.append(attempt_id)
        return per_attempt(connection, attempt_id)

    def no_scan(_connection):
        raise AssertionError("queueing one stuck answer never scans every stuck answer")

    monkeypatch.setattr(stuck, "stuck_answer", spy)
    monkeypatch.setattr(stuck, "stuck_answers", no_scan)
    found = stuck_text_for(repository, result.attempt_id)
    assert asked == [result.attempt_id]
    assert found is not None and (found.text, found.confusion_quote) == (STUCK_TEXT, "what an eigenvalue")
    assert (found.learning_object_id, found.practice_item_id) == ("lo_diag", "pi_diag_easy")


def test_a_stuck_answer_with_text_is_queued_at_recording_and_read(tmp_path):
    paths, repository = _vault(tmp_path)
    result = _stuck_answer(paths, repository, STUCK_TEXT)
    assert _jobs(repository) == [("stuck_answer", result.attempt_id)]
    reader = GapLLMFake(reading=EIGEN_GAP, decide=word_match("eigenvalues"), needed="no")
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=_clients(reader), clock=_at(2))
    assert outcome is not None and outcome.state == "done"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT source_kind, source_id, kind, action, target_id FROM learner_text_gaps").fetchone()
    assert tuple(row) == ("stuck_answer", result.attempt_id, "prerequisite", "matched_prerequisite",
                          "lo_eigen_basics")


def test_an_empty_stuck_answer_is_no_learner_text(tmp_path):
    paths, repository = _vault(tmp_path)
    result = _stuck_answer(paths, repository, "   ")
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    # Main's deterministic zero: scored 0, no model call, no grader reading.
    assert attempt["declared_stuck"] is True and attempt["rubric_score"] == 0
    assert _jobs(repository) == []
    assert stuck_text_for(repository, result.attempt_id) is None
    assert sweep_backlog(load_vault(paths.root), repository, clock=_at(5), dry_run=True)["stuck_answer"] == 0


# -- Phase 6 serving reads the gap's signal only at mvp-0.16 ------------------------------------


def test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch(tmp_path):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    event_id = ask_question(vault, repository, GapTutor(EIGEN_GAP), context="practice",
                            question_md="What is an eigenvalue? I can't diagonalize.",
                            practice_item_id="pi_diag_easy", session_id="sess_1", clock=FrozenClock(NOW))["event_id"]
    llm = GapLLMFake(decide=word_match("eigenvalues"), needed="no")
    row = process_learner_text(paths.root, repository, tutor_question_text(vault, repository, event_id),
                               clients=_clients(llm), clock=FrozenClock(NOW))
    assert (row["action"], row["target_id"]) == ("matched_prerequisite", "lo_eigen_basics")

    def serving(version: str, toml: str = ""):
        set_algorithm_version(paths, version)
        text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
        if toml:
            append_config_toml(paths.root, toml)
        try:
            current = load_vault(paths.root)
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                signals = load_interaction_signals(connection, current, ())
            taught = taught_first_learning_objects(current, repository, ["lo_eigen_basics", "lo_diag"])
            return (
                sorted((s.signal_id, s.lo_id, s.signal_type, s.effective_mass) for s in signals),
                sorted(taught),
            )
        finally:
            (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")

    successor = serving("mvp-0.16")
    predecessor = serving("mvp-0.15")
    grounded = serving("mvp-0.15", "[learner_text_gaps]\nenabled = false\n")
    switched_off = serving("mvp-0.16", "[learner_text_gaps]\nsooner_check_enabled = false\n")
    # The gap's target is the question's prerequisite signal at mvp-0.16 ...
    assert ("question_event:" + event_id + ":lo_eigen_basics", "lo_eigen_basics", "prerequisite", 0.15) in successor[0]
    assert "lo_eigen_basics" in successor[1]
    # ... and nowhere below it, or with the successor's kill switch off: the
    # F11 grounded rule exactly as at mvp-0.15.
    assert predecessor == grounded == switched_off
    assert "lo_eigen_basics" not in predecessor[1]
    assert not [s for s in predecessor[0] if s[1] == "lo_eigen_basics"]


# -- a stuck answer: main's confusion signal and one gap observation ---------------------------


@pytest.mark.parametrize("version", ["mvp-0.15", "mvp-0.16"])
def test_a_stuck_answer_keeps_its_confusion_signal_and_adds_one_gap_observation(tmp_path, version):
    paths, repository = _vault(tmp_path, version=version)
    result = _stuck_answer(paths, repository, STUCK_TEXT)
    _reading(repository, result.attempt_id, "what an eigenvalue")
    reader = GapLLMFake(reading=EIGEN_GAP, decide=word_match("eigenvalues"), needed="no")
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=_clients(reader), clock=_at(2))
    assert outcome is not None and outcome.state == "done"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        signals = load_interaction_signals(connection, load_vault(paths.root), ())
    mine = [s for s in signals if s.attempt_id == result.attempt_id]
    confusion = [s for s in mine if s.signal_type == STUCK_CONFUSION_SIGNAL]
    gaps = [s for s in mine if s.signal_id.startswith("learner_gap:")]
    # Main's stuck_confusion: the item's own LO, no outcome, no mass, at every
    # stuck-prompt version.
    assert [(s.lo_id, s.outcome, s.effective_mass) for s in confusion] == [("lo_diag", None, 0.0)]
    # The gap's observation: another LO, once, and only at mvp-0.16.
    expected = [("lo_eigen_basics", "prerequisite", 0.0, 0.15)] if version == "mvp-0.16" else []
    assert [(s.lo_id, s.signal_type, s.outcome, s.effective_mass) for s in gaps] == expected


# -- Slice 2 T6: verified spans and the named gap on one answer -----------------------------------


def test_t6_verified_spans_and_the_tutors_named_gap_both_hold(tmp_path):
    from tests.source_retrieval_fakes import loaded
    from tests.test_source_retrieval_tutor import CLOCK, QUESTION, CitingTutor, provider, setup

    class NamingTutor(CitingTutor):
        def run_tutor_qa(self, context):
            answer = super().run_tutor_qa(context)
            return answer.model_copy(update={"learner_gap": EIGEN_GAP})

    paths, repository = setup(tmp_path)
    tutor = NamingTutor()
    span_provider, _llm = provider()
    result = ask_question(loaded(paths), repository, tutor, context="practice", question_md=QUESTION,
                          practice_item_id="pi_eigen_1", session_id="s1", source_span_provider=span_provider,
                          clock=CLOCK)
    spans = tutor.contexts[0].source_spans
    assert spans and all(span["extraction_id"] != "ext_exam" for span in spans)
    # T6: only spans that were provided (and verified) are cited and persisted.
    assert {(c["extraction_id"], c["span_id"]) for c in result["citations"]} == {
        (span["extraction_id"], span["span_id"]) for span in spans}
    event = repository.question_event(result["event_id"])
    context = event["source_context"]
    assert context["source_retrieval"]["verification"]["status"] == "verified"
    assert {(c["extraction_id"], c["span_id"]) for c in context["citations"]} == {
        (span["extraction_id"], span["span_id"]) for span in spans}
    # Learner-text gaps: the tutor's named gap on the same answer, read back
    # by the pipeline's tutor-question source.
    assert context["learner_gap"]["prerequisite_name"] == "Eigenvalues"
    assert result["learner_gap"] == context["learner_gap"]
    text = tutor_question_text(loaded(paths), repository, result["event_id"])
    assert text is not None and text.reading is not None
    assert (text.reading.kind, text.reading.prerequisite_name) == ("prerequisite", "Eigenvalues")


# -- Daily-loop DL1: honest labels for gap checks ---------------------------------------------------


@pytest.mark.parametrize(
    ("component", "reason", "headline"),
    [
        ("gap_commitment_check", "the one check on a topic added from your question",
         "maintain: the one check on Eigenvalues, added from your question"),
        ("gap_sooner_check", "a check brought forward: your question pointed at this topic",
         "maintain: the check on Eigenvalues, brought forward by your question"),
        (None, "the first review of a topic assumed known (not tested): this is the check",
         "maintain: the check on Eigenvalues, assumed known (not tested)"),
    ],
)
def test_the_plan_labels_a_gap_check_as_what_it_is(component, reason, headline):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from learnloop.daily_plan.lanes import _lane_reason, classify_item

    components = {"assumed_check": 1.0}
    if component:
        components[component] = 1.0
    scheduled = SimpleNamespace(practice_item_id="pi_eig_easy", learning_object_id="lo_eigen_basics",
                                priority=1.0, components=components, followup_kind=None)
    item = classify_item(scheduled, rank=0, state=None, requested=False, now=datetime(2026, 5, 20, tzinfo=UTC),
                         est_minutes=2.0, check=None, probe_slot_available=True)
    assert (item.lane, item.check_kind, item.reason) == ("maintain", "assumed_check", reason)
    assert _lane_reason("maintain", [item], {"lo_eigen_basics": "Eigenvalues"}) == headline
