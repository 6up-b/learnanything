"""Interaction signals through the production writers and loader (review F4, F5).

The synthetic tests in test_interaction_signals.py inject attempt links and a
facet-to-LO map. Here the question rows come from ``tutor_qa.ask_question``
(as the practice screen and feedback screen call it), the attempts from the
repository, and the rows from the same replay loader the reports use.
"""
from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.tutor.ai_contracts import TutorAnswer
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault
from tests.structured_ai import StructuredClientFake

ITEM = "pi_svd_define_001"
LO = "lo_svd_definition"


class FakeTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, question_type):
        self.question_type = question_type

    def run_tutor_qa(self, context):
        return TutorAnswer(
            answer_md="Think about which factor is orthogonal.",
            question_type=self.question_type,
            facets=list(context.candidate_facets),
        )


def _setup(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _attempt(repository, attempt_id, *, at, session_id="sess_1", hints_used=0, score=4):
    repository.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": ITEM, "learning_object_id": LO,
        "practice_mode": "define", "attempt_type": "independent_attempt",
        "rubric_score": score, "hints_used": hints_used, "session_id": session_id,
        "created_at": at.isoformat(), "learner_answer_md": "A = U S V^T",
    })
    with repository.connection() as connection:
        connection.execute(
            """INSERT INTO grading_evidence
               (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, grading_revision)
               VALUES (?, ?, 'correctness', ?, 1, ?, 1)""",
            (f"evidence-{attempt_id}", attempt_id, score, at.isoformat()),
        )


def _inputs(vault):
    from learnloop.cli.field import _replay_inputs

    return _replay_inputs(vault, legacy_fallback="current_content")


def _ask(vault, repository, question_type, *, at, context="practice", seconds=0.0, **kwargs):
    return ask_question(
        vault, repository, FakeTutor(question_type), context=context,
        question_md="Where do I even start?", practice_item_id=ITEM,
        seconds_into_attempt=seconds, clock=FrozenClock(at), **kwargs,
    )


def test_ask_before_submit_gets_the_early_help_cap(tmp_path):
    """Review F5: the practice screen asks before the attempt exists (no attempt_id)."""
    vault, repository = _setup(tmp_path)
    _ask(vault, repository, "strategy", at=NOW, session_id="sess_1")
    _attempt(repository, "a1", at=NOW + timedelta(minutes=3), hints_used=1)
    inputs = _inputs(vault)
    attempt, = inputs["attempts"]
    assert attempt.help_before_work
    hint = next(s for s in inputs["signals"] if s.signal_id == "hint:a1")
    assert hint.outcome == 0.3  # not the ordinary 0.8 one-hint cap
    assistance = [s for s in inputs["signals"] if s.signal_type == "practice_assistance"]
    assert [(s.attempt_id, s.help_before_work) for s in assistance] == [("a1", True)]


def test_question_links_only_to_the_next_attempt_in_its_window(tmp_path):
    vault, repository = _setup(tmp_path)
    _attempt(repository, "a0", at=NOW - timedelta(minutes=10))
    _ask(vault, repository, "strategy", at=NOW, session_id="sess_1")
    _attempt(repository, "other-session", at=NOW + timedelta(minutes=1), session_id="sess_2")
    _attempt(repository, "a1", at=NOW + timedelta(minutes=3), hints_used=1)
    _attempt(repository, "a2", at=NOW + timedelta(minutes=9), hints_used=1)
    rows = {row.attempt_id: row for row in _inputs(vault)["attempts"]}
    # An attempt on the item in another session closes the window, as in the
    # submit-time hint accounting: the question belonged to that attempt's
    # window but not its session, so it links to no attempt at all.
    assert not rows["a0"].help_before_work
    assert not rows["other-session"].help_before_work
    assert not rows["a1"].help_before_work
    assert not rows["a2"].help_before_work


def test_mid_attempt_question_is_linked_but_not_early_help(tmp_path):
    vault, repository = _setup(tmp_path)
    _ask(vault, repository, "strategy", at=NOW, session_id="sess_1", seconds=40.0)
    _attempt(repository, "a1", at=NOW + timedelta(minutes=3), hints_used=1)
    inputs = _inputs(vault)
    attempt, = inputs["attempts"]
    assert not attempt.help_before_work
    assert next(s for s in inputs["signals"] if s.signal_id == "hint:a1").outcome == 0.8
