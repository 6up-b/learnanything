"""Field §3.1 interaction signals as F2 placement routes them (live with mvp-0.10).

Confusion questions while reading, help before starting and suspected leaks
keep an LO out of fast-track and teach it first; "I know this" still works;
curiosity carries no negative signal; asking never changes the record (G13).
"""

from __future__ import annotations

from datetime import timedelta
import sqlite3

from learnloop.field.signals import blocks_fast_track
from learnloop.field.types import SignalRow
from learnloop.placement.decisions import reconcile_fast_track, record_self_report
from learnloop.tutor.ai_contracts import TutorAnswer
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.models import Note

from tests.helpers import NOW
from tests.structured_ai import StructuredClientFake
from tests.test_assumed_known import LOW_Q, _answer, _at, _decisions, _queue, _setup, _snapshot


class FakeTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, question_type):
        self.question_type = question_type

    def run_tutor_qa(self, context):
        return TutorAnswer(
            answer_md="Look at what the matrix does to its eigenvectors.",
            question_type=self.question_type,
            facets=list(context.candidate_facets),
        )


def _read_question(vault, repository, lo_id, question_type, *, minutes):
    vault.notes[f"note_{lo_id}"] = Note(id=f"note_{lo_id}", title=lo_id, related_los=[lo_id])
    return ask_question(
        vault, repository, FakeTutor(question_type), context="library",
        question_md="I don't follow this step.", note_id=f"note_{lo_id}", clock=_at(minutes),
    )


def _two_clean_answers(vault, repository, *, start=10):
    _answer(vault, repository, "pi_diag_hard", minutes=start)
    _answer(vault, repository, "pi_diag_mid", minutes=start + 1)


def test_reader_confusion_blocks_fast_track_and_teaches_the_lo_first(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _read_question(vault, repository, "lo_eigen_basics", "clarification", minutes=1)

    queue = _queue(vault, repository, 2, persist=False)
    layer0 = [s for s in queue if s.components.get("new_material") and s.components["placement_layer"] == 0.0]
    # Taught first within its prerequisite layer.
    assert [s.learning_object_id for s in layer0][:3] == ["lo_eigen_basics"] * 3
    assert layer0[0].plain_english[0].startswith("taught first")
    assert all(s.components["taught_first"] == 0.0 for s in layer0 if s.learning_object_id == "lo_diag")

    _answer(vault, repository, "pi_eig_hard", minutes=10)
    _answer(vault, repository, "pi_eig_mid", minutes=11)
    assert reconcile_fast_track(vault, repository, clock=_at(12)) == []

    # "I know this" still assumes known, confusion or not.
    result = record_self_report(
        vault, repository, learning_object_ids=["lo_eigen_basics"], report="know_this", clock=_at(13),
    )
    assert result["results"][0]["status"] == "assumed"


def test_curiosity_carries_no_negative_signal(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _read_question(vault, repository, "lo_diag", "other", minutes=1)
    queue = _queue(vault, repository, 2, persist=False)
    assert not any(s.components.get("taught_first") for s in queue)
    _two_clean_answers(vault, repository)
    assert [d["learning_object_id"] for d in reconcile_fast_track(vault, repository, clock=_at(20))] == ["lo_diag"]


def test_help_before_starting_blocks_fast_track(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id = repository.create_session(available_minutes=25, clock=_at(0))
    ask_question(
        vault, repository, FakeTutor("strategy"), context="practice",
        question_md="Where do I even start?", practice_item_id="pi_diag_hard",
        session_id=session_id, seconds_into_attempt=2.4,
        question_context={"attempt_progress": "no_draft"}, clock=_at(1),
    )
    _answer(vault, repository, "pi_diag_hard", minutes=3, session_id=session_id)
    _answer(vault, repository, "pi_diag_mid", minutes=4, session_id=session_id)
    assert reconcile_fast_track(vault, repository, clock=_at(5)) == []


def test_suspected_leak_makes_the_answer_non_cold_for_fast_track(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _two_clean_answers(vault, repository)
    with sqlite3.connect(paths.sqlite_path) as connection:
        (first_attempt,) = connection.execute(
            "SELECT id FROM practice_attempts WHERE practice_item_id = 'pi_diag_hard'"
        ).fetchone()
    repository.insert_question_event(
        {
            "context": "practice", "practice_item_id": "pi_diag_hard", "attempt_id": first_attempt,
            "question_md": "Is it the third one?", "question_type": "verification",
            "leak_suspected": True, "created_at": (NOW + timedelta(minutes=9)).isoformat().replace("+00:00", "Z"),
        }
    )
    assert reconcile_fast_track(vault, repository, clock=_at(20)) == []
    assert blocks_fast_track(SignalRow("s", "lo", "2026-01-01T00:00:00Z", "other", leak_suspected=True))


def test_asking_never_changes_the_record_only_routing(tmp_path):
    """G13: with and without the question, evidence, mastery and certification
    are byte-identical; only placement routing differs."""

    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    _two_clean_answers(vault, repository)
    before = _snapshot(paths)
    _read_question(vault, repository, "lo_diag", "mechanism", minutes=15)
    reconcile_fast_track(vault, repository, clock=_at(16))
    _queue(vault, repository, 17)
    assert _snapshot(paths) == before
    assert _decisions(paths) == []

    control_paths, control_vault, control_repository = _setup(tmp_path, placement_toml=LOW_Q, name="control")
    _two_clean_answers(control_vault, control_repository)
    assert [d["source"] for d in reconcile_fast_track(control_vault, control_repository, clock=_at(16))] == [
        "fast_track"
    ]
