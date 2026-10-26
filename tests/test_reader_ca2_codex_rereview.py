"""Reader CA2, one Ask: the Codex re-review's findings (docs/reviews/reader-ca2-one-ask-codex-review.md, re-review).

Each scenario runs on real state (the draft checkpoint, a real workbench
opened, submitted and graded through the one submit, real practice sessions
ended and started), never a mocked predicate; every model is a fake.

* F1: an earlier attempt's help opened on the answer box moves onto the
  unfinished workbench when the draft moves into steps, so later drafts of
  other items never lose it, and it counts once.
* F12 (and F2's bypass): a withheld worked answer is stored as its take step;
  no read, note, promotion or queue exposes its text.
* F13: a workbench-bound question counts for the workbench's submit whatever
  practice session it was asked in, as its thread is restored.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import ONE_ASK_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.tutor.tutor_qa import WITHHELD_ANSWER_MD, hint_equivalents_for_submission
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.hint_fakes import ITEM as CDF_ITEM, WORK
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.test_reader_ca2_codex_review import (  # noqa: F401 - the sidecar fixture
    ITEM,
    FakeTutor,
    _call,
    _expected,
    sidecar,
)
from tests.ux_phase1_support import set_config
from tests.workbench_help_fakes import STEP_1, STEP_2, sidecar as help_sidecar

OTHER_ITEM = "pi_svd_define_001"  # another item of the same vault (create_basic_vault's)


def _attempt(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _carried(paths, workbench_id: str) -> int:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return int(connection.execute("SELECT carried_hints FROM workbench_sessions WHERE id = ?",
                                      (workbench_id,)).fetchone()[0])


def _steps_sidecar(tmp_path):
    paths, ctx, session = help_sidecar(tmp_path)
    set_config(paths.root, {("algorithms", "algorithm_version"): ONE_ASK_ALGORITHM_VERSION})
    ctx.load(paths.root)
    return paths, ctx, session


def _draft(ctx, session, item: str, key: str, **extra):
    _call(ctx, "save_practice_draft", {"sessionId": session, "practiceItemId": item, "answerMd": WORK,
                                       "hintsUsed": 0, "submissionId": key, **extra})


def _into_steps(ctx, session, *, carried: int = 0, name_session: bool = True) -> str:
    """The practice screen hands its draft to the steps (``name_session``:
    it names its practice session; else the server takes the most recent
    open one, as for a client before the re-review)."""

    view = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": CDF_ITEM,
                                         "stemMd": "Find P(X <= 1/2).", "carriedHints": carried,
                                         **({"practiceSessionId": session} if name_session else {})})["session"]
    for index, body in enumerate((STEP_1, STEP_2)):
        _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": f"s{index}",
                                           "op": "add", "bodyMd": body})
    return view["sessionId"]


def _reader_problem(ctx) -> str:
    """A problem opened in the Reader on the item, its book hidden (so the
    book's own hint never enters the counts these tests read)."""

    view = _call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": CDF_ITEM,
                                         "stemMd": "Find P(X <= 1/2).", "sourceVisible": False})["session"]
    _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s0",
                                       "op": "add", "bodyMd": STEP_1})
    return view["sessionId"]


# -- F1: the opening moves onto the unfinished workbench ---------------------------------------------


def test_f1_an_opening_carried_into_steps_survives_another_items_draft_and_counts_once(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    wb = _into_steps(ctx, session, name_session=False)
    # The server carried it onto the problem (the client sent no count).
    assert _carried(paths, wb) == 1
    # Item B's draft replaces the session's checkpoint.
    _draft(ctx, session, OTHER_ITEM, "kB")
    attempt = _call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_f1_a_carried_opening_is_not_counted_again_from_the_draft(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    wb = _into_steps(ctx, session)
    # The screen keeps resending the flag with its draft; the carry stays.
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    # A resume carries nothing more.
    _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "sessionId": wb,
                                  "practiceSessionId": session})
    assert _carried(paths, wb) == 1
    checkpoint = _call(ctx, "get_session", {"sessionId": session})["checkpoint"]
    assert checkpoint["earlierOpened"] is True  # the panel still says it is counted
    attempt = _call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_f1_after_steps_the_answer_box_submit_counts_the_carried_opening_once(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    _into_steps(ctx, session)
    # Back on the answer box the screen's count gets the carried hint back
    # (``backToAnswerBox``); the draft no longer adds it.
    attempt = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": CDF_ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 1, "selfGrade": {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3},
        "submissionId": "kA"})
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_f1_a_reader_open_never_takes_the_answer_boxs_opening(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    wb = _reader_problem(ctx)
    assert _carried(paths, wb) == 0
    attempt = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": CDF_ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3},
        "submissionId": "kA"})
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


# -- F12: a withheld answer's text is never stored for a learner-facing path -------------------------


def test_f12_a_withheld_answer_is_never_stored_saved_promoted_or_queued(sidecar):
    _paths, ctx, tutor = sidecar(tutor=FakeTutor(question_type="strategy"))
    vault, repository = ctx.require_vault()
    secret = _expected(vault)
    tutor.answer_md = secret
    answer = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                               "submissionId": "k1", "question": "Just show me the final answer"})
    assert answer["takeOffer"] and answer["answerMd"] == WITHHELD_ANSWER_MD
    event = repository.question_event(answer["eventId"])
    assert event["answer_md"] == WITHHELD_ANSWER_MD
    withheld = event["source_context"]["withheld"]
    assert withheld["reason"] == "worked_help" and withheld["answer_chars"] == len(secret)
    assert secret not in json.dumps(event, default=str, ensure_ascii=False)
    with pytest.raises(SidecarError, match="worked help"):
        _call(ctx, "save_tutor_answer_note", {"eventId": answer["eventId"]})
    with pytest.raises(SidecarError, match="worked help"):
        _call(ctx, "promote_tutor_question", {"eventId": answer["eventId"], "intent": "practice"})
    assert repository.question_event(answer["eventId"])["saved_note_id"] is None
    queue = _call(ctx, "list_question_queue", {"resolution": None})
    assert secret not in json.dumps(queue, ensure_ascii=False)
    transcript = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM,
                                                     "sessionId": "sess_1", "submissionId": "k1"})
    assert secret not in json.dumps(transcript, ensure_ascii=False)


def test_f12_an_ordinary_answer_still_saves_as_a_note(sidecar):
    _paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="mechanism"))
    answer = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                               "submissionId": "k1", "question": "Why orthogonal?"})
    saved = _call(ctx, "save_tutor_answer_note", {"eventId": answer["eventId"]})
    assert saved["noteId"]


# -- F13: a workbench-bound question counts across the practice sessions it was worked in ----------


def test_f13_a_sessionless_reader_question_counts_after_its_session_ends_and_the_problem_resumes(
        tmp_path, grader, monkeypatch):
    import learnloop_sidecar.handlers.tutor_qa as handler

    paths, ctx, first = _steps_sidecar(tmp_path)
    _call(ctx, "end_session", {"sessionId": first})
    wb = _reader_problem(ctx)

    class Ready:
        ready = True

    monkeypatch.setattr(handler, "ready_tutor_qa_provider",
                        lambda vault: ("fake", Ready(), FakeTutor(question_type="mechanism")))
    repository = Repository(paths.sqlite_path)
    assert repository.most_recent_open_session() is None
    asked = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": CDF_ITEM,
                                              "workbenchSessionId": wb, "question": "Why is F(1/2) the value?"})
    session_a = repository.question_event(asked["eventId"])["session_id"]
    assert session_a and asked["hintEquivalent"] is True
    _call(ctx, "end_session", {"sessionId": session_a})
    session_b = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    # The thread is restored in B, and the count agrees with it.
    thread = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": CDF_ITEM,
                                                 "workbenchSessionId": wb, "sessionId": session_b})
    assert [event["id"] for event in thread["events"]] == [asked["eventId"]]
    assert thread["helpRecord"]["counted"] == 1
    assert hint_equivalents_for_submission(repository, CDF_ITEM, session_b) == 1
    attempt = _call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session_b})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_f13_an_unbound_practice_question_keeps_its_own_session_rule(sidecar):
    _paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="mechanism"))
    _vault_, repository = ctx.require_vault()
    _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                      "submissionId": "k1", "question": "Why orthogonal?"})
    assert hint_equivalents_for_submission(repository, ITEM, "sess_1") == 1
    assert hint_equivalents_for_submission(repository, ITEM, "sess_2") == 0


def test_f13_the_field_link_reads_the_same_rule():
    from datetime import UTC, datetime

    from learnloop.hint_window import counts_in_session, following_attempt, workbench_bound

    asked = datetime(2026, 10, 25, 9, tzinfo=UTC)
    attempts = [(datetime(2026, 10, 25, 10, tzinfo=UTC), "att_b", "sess_b")]
    bound = {"attempt_key": {"submission_id": "workbench:wb_1", "workbench_session_id": "wb_1"}}
    assert workbench_bound(bound) and workbench_bound(json.dumps(bound))
    assert not workbench_bound({"attempt_key": {"submission_id": "k1"}}) and not workbench_bound(None)
    assert counts_in_session(context="practice", question_session_id="sess_a", attempt_session_id="sess_b",
                             bound=True)
    assert following_attempt(asked, context="practice", question_session_id="sess_a", attempts=attempts,
                             bound=True) == "att_b"
    assert following_attempt(asked, context="practice", question_session_id="sess_a", attempts=attempts) is None
