"""Reader CA2, the Codex review of the Astra fixes, F4: the handoff that keeps
one metered Ask allowance across answer box -> Work in Steps -> Reader is
committed with the open (or resume) that exposes the problem, never after it.

* A handoff write that fails (SQLite write contention, say) fails the open
  as a whole: no problem is exposed whose Reader budget would read zero;
  the retry opens it with its handoff.
* A resume that cannot record its handoff leaves the problem as it was.
* After a restart the Reader still reads the answer box's questions.
* A handoff that cannot be read when a question is asked refuses the ask
  (no model call); it is never read as an empty allowance.

Every model is a fake.
"""

from __future__ import annotations

import sqlite3

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.stores import workbench as store
from learnloop.reader import workbench as WB
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.test_reader_ca2_astra_handoff import BOX, LIMIT, _ask, _metered, _open_steps, _transcript, _used
from tests.test_reader_ca2_codex_review import ITEM, FakeTutor, _call, sidecar  # noqa: F401 - fixture


def _fail_handoff_writes(monkeypatch) -> None:
    """The handoff's write fails as a locked database would."""

    log = WB._log

    def failing(repository, session, event, clock=None, **extra):
        if event == WB.DRAFT_HANDOFF_EVENT:
            raise sqlite3.OperationalError("database is locked")
        return log(repository, session, event, clock, **extra)

    monkeypatch.setattr(WB, "_log", failing)


def _sessions(repository) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT id, status FROM workbench_sessions WHERE practice_item_id = ?", (ITEM,))]


def _spend(ctx, session: str) -> None:
    for index in range(LIMIT):
        _ask(ctx, session, submissionId=BOX, question=f"Why {index}?")


def test_a_failed_handoff_write_fails_the_open_and_exposes_no_problem(sidecar, monkeypatch):
    _paths, ctx, session = _metered(sidecar)
    _spend(ctx, session)
    _vault, repository = ctx.require_vault()
    with monkeypatch.context() as patched:
        _fail_handoff_writes(patched)
        with pytest.raises(sqlite3.OperationalError):
            _open_steps(ctx, session, submissionId=BOX)
    # Rolled back with it: no problem the Reader could resume with a fresh allowance.
    assert _sessions(repository) == []
    # The retry opens the problem with its handoff: 3/3 in the Reader.
    wb = _open_steps(ctx, session, submissionId=BOX)
    assert _used(ctx, submission_id=WB.submission_id_for(wb), workbench_session_id=wb) == (LIMIT, LIMIT)
    with pytest.raises(SidecarError) as refused:
        _ask(ctx, workbenchSessionId=wb, question="One more?")
    assert refused.value.code == "question_limit_reached"


def test_a_resume_that_cannot_record_its_handoff_leaves_the_problem_as_it_was(sidecar, monkeypatch):
    _paths, ctx, session = _metered(sidecar)
    _vault, repository = ctx.require_vault()
    # A problem opened before the answer box spent its questions, then set aside.
    wb = _open_steps(ctx, session)
    _call(ctx, "workbench.abandon", {"sessionId": wb})
    assert _sessions(repository) == [{"id": wb, "status": "abandoned"}]
    _spend(ctx, session)
    with monkeypatch.context() as patched:
        _fail_handoff_writes(patched)
        with pytest.raises(sqlite3.OperationalError):
            _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "sessionId": wb,
                                          "practiceSessionId": session, "submissionId": BOX})
    # Not reopened without its handoff.
    assert _sessions(repository) == [{"id": wb, "status": "abandoned"}]
    _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "sessionId": wb,
                                  "practiceSessionId": session, "submissionId": BOX})
    assert _used(ctx, submission_id=WB.submission_id_for(wb), workbench_session_id=wb) == (LIMIT, LIMIT)


def test_after_a_restart_the_reader_still_reads_the_answer_box_s_questions(sidecar):
    paths, ctx, session = _metered(sidecar)
    _spend(ctx, session)
    wb = _open_steps(ctx, session, submissionId=BOX)
    restarted = SidecarContext()
    restarted.load(paths.root)
    assert len(_transcript(restarted, workbenchSessionId=wb)["events"]) == LIMIT
    assert _used(restarted, submission_id=WB.submission_id_for(wb), workbench_session_id=wb) == (LIMIT, LIMIT)
    with pytest.raises(SidecarError) as refused:
        _ask(restarted, workbenchSessionId=wb, question="One more?")
    assert refused.value.code == "question_limit_reached"


def test_an_unreadable_handoff_refuses_the_ask_and_makes_no_model_call(sidecar, monkeypatch):
    tutor = FakeTutor()
    _paths, ctx, _tutor = sidecar({("tutor_qa", "max_questions_practice"): LIMIT}, tutor=tutor)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    _spend(ctx, session)
    wb = _open_steps(ctx, session, submissionId=BOX)
    calls = len(tutor.contexts)
    assert calls == LIMIT

    def unreadable(connection, session_ids):
        raise sqlite3.DatabaseError("database disk image is malformed")

    monkeypatch.setattr(store, "handed_submission_ids", unreadable)
    with pytest.raises(sqlite3.DatabaseError):
        _ask(ctx, workbenchSessionId=wb, question="One more?")
    assert len(tutor.contexts) == calls                       # never asked on an empty allowance
