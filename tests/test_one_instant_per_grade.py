"""Review round 3, class 2: one instant per grade, and exam answers never dated ahead of now (FR3-7, FR3-8)."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.learner.lesson_weight import mastery_applications
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault


@dataclass
class SteppingClock:
    """A clock that crosses a second on every read: any two reads of one grade fall in different seconds."""

    instant: datetime
    reads: list[datetime] = field(default_factory=list)

    def now(self) -> datetime:
        self.instant += timedelta(seconds=1)
        self.reads.append(self.instant)
        return self.instant


def _facts(repo, attempt_id):
    with closing(connect(repo.sqlite_path, read_only=True)) as connection:
        created = connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone()[0]
        order = connection.execute("SELECT recorded_at FROM attempt_application_order WHERE attempt_id = ?",
                                   (attempt_id,)).fetchone()
        applied = mastery_applications(connection, [attempt_id]).get(attempt_id)
        # The answered learning object's state (an untouched object's row is stamped by whichever process wrote it).
        mastery = [tuple(row) for row in connection.execute(
            "SELECT * FROM learning_object_mastery WHERE learning_object_id = (SELECT learning_object_id FROM "
            "practice_attempts WHERE id = ?)", (attempt_id,))]
    return created, order[0] if order else None, applied, mastery


def test_a_grade_reads_the_clock_once_for_its_instant_and_a_rebuild_reproduces_it(tmp_path):
    """FR3-7 (L42-R17's residue): the clock crosses a second between the grade's reads. The attempt's created_at, its
    application-order key and its mastery observation are one instant, so a rebuild reproduces the live mastery
    (failed before: the observation was dated in the earlier second, the attempt in the later)."""

    paths = create_placement_vault(tmp_path / "vault")
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=FrozenClock(NOW))
    clock = SteppingClock(NOW.astimezone(UTC).replace(microsecond=0))
    result = complete_self_graded_attempt(vault, repo, AttemptDraft("pi_eig_mid", "answer"),
                                          SelfGradeInput({"correctness": 3}, 3), clock=clock)
    assert len({read.second for read in clock.reads}) > 1, "the clock crossed a second during the grade"
    created, order, applied, mastery = _facts(repo, result.attempt_id)
    assert order in (None, created)
    assert applied is None or applied.observed_at == created
    rebuild_all_derived_state(vault, repo)
    assert _facts(repo, result.attempt_id) == (created, order, applied, mastery)


def test_exam_finish_dates_no_answer_ahead_of_now_and_replay_orders_them_as_applied(tmp_path):
    """FR3-8: finishing a two-answer sitting at NOW dates every exam answer at or before NOW (failed before: the second
    was dated NOW + 1 s), so an ordinary answer on the same learning object graded right after the finish, at NOW,
    sorts after them in the replay order (the instant, then the application sequence), as it was applied."""

    from learnloop.db.attempt_order import application_sequences
    from learnloop.goals.exam_session import finish_exam, record_exam_answer

    from tests.exam_session_helpers import _grade, _reserved_and_started
    from tests.helpers import NOW_ISO

    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    record_exam_answer(vault, repository, session_id, "pi_exam_b", answer_md="B", resolved_grade=_grade(1))
    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    exam = [repository.fetch_practice_attempt(answer["attempt_id"]) for answer in repository.exam_answers(session_id)]
    assert len(exam) == 2 and all(attempt["created_at"] <= NOW_ISO for attempt in exam)
    ordinary = complete_self_graded_attempt(vault, repository, AttemptDraft("pi_exam_a", "again"),
                                            SelfGradeInput({"correctness": 0}, 3), clock=FrozenClock(NOW))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        sequences = application_sequences(connection)
    key = lambda attempt: (attempt["created_at"], sequences[attempt["id"]])  # noqa: E731
    assert all(key(repository.fetch_practice_attempt(ordinary.attempt_id)) > key(attempt) for attempt in exam)
    # FR3-23 (owner decision b): a rebuild reproduces the live mastery after the sitting and the ordinary answer. The
    # exam grades give criterion points without evidence rows, which the door records as the grade's rows, and the
    # due item's mastery comes from a recorded seed (failed before: evidence count 3 live, 4 rebuilt; observation
    # weight 0.5 live, 0.0 rebuilt).
    live = _facts(repository, ordinary.attempt_id)
    rebuild_all_derived_state(vault, repository)
    assert _facts(repository, ordinary.attempt_id) == live
