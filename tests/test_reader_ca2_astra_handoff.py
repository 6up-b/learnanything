"""Reader CA2, the Astra batch review's Medium: the per-attempt metered Ask
budget survives the answer box -> Work in Steps -> Reader handoff.

The practice screen hands its answer box's draft (keyed by its
``submissionId``) to the steps; the Reader resumes that unfinished problem
under the workbench's own key (``workbench:<id>``). Before the fix the
Reader's thread and budget left the answer box's questions out (3/3 -> 0/3,
more paid questions with no new attempt). Now the open records the draft's
key on the problem (``workbench_draft_handed``, salience only) and every
read resolves both identities to one attempt: the same thread, the same
budget, in both directions. Raw question rows are unchanged; the plan route
stays unlimited; a new attempt still starts a fresh allowance. Every model is
a fake.
"""

from __future__ import annotations

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.attempts import salience_firewall as SF
from learnloop.reader import workbench as WB
from learnloop.tutor.tutor_qa import attempt_identities, practice_thread_events, question_usage
from learnloop_sidecar.errors import SidecarError
from tests.test_reader_ca2_codex_review import ITEM, FakeTutor, PlanTutor, _call, sidecar  # noqa: F401 - fixture

LIMIT = 3
BOX = "answer-box-key"


def _ask(ctx, session: str | None = None, **params):
    return _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM,
                                             **({"sessionId": session} if session else {}),
                                             "question": params.pop("question", "Why?"), **params})


def _transcript(ctx, **params):
    return _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": ITEM, **params})


def _used(ctx, *, session: str | None = None, submission_id: str | None = None,
          workbench_session_id: str | None = None) -> tuple[int, int | None]:
    """The metered per-attempt budget as the ask reads it (the test vault's
    transcript route is a subscription one, which shows no bound)."""

    vault, repository = ctx.require_vault()
    return question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id=session,
                          submission_id=submission_id, workbench_session_id=workbench_session_id, metered=True)


def _open_steps(ctx, session: str, **extra) -> str:
    vault, _repository = ctx.require_vault()
    opened = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                           "stemMd": vault.practice_items[ITEM].prompt, "practiceSessionId": session,
                                           **extra})
    return opened["session"]["sessionId"]


def _metered(sidecar):
    paths, ctx, _tutor = sidecar({("tutor_qa", "max_questions_practice"): LIMIT}, tutor=FakeTutor())
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def test_the_budget_spent_in_the_answer_box_stays_spent_in_the_reader(sidecar):
    _paths, ctx, session = _metered(sidecar)
    for index in range(LIMIT):
        _ask(ctx, session, submissionId=BOX, question=f"Why {index}?")
    with pytest.raises(SidecarError) as refused:
        _ask(ctx, session, submissionId=BOX, question="A fourth?")
    assert refused.value.code == "question_limit_reached"
    wb = _open_steps(ctx, session, submissionId=BOX)
    # Resumed in the Reader: no key, no practice session from the client.
    reader = _transcript(ctx, workbenchSessionId=wb)
    assert [event["questionMd"] for event in reader["events"]] == ["Why 0?", "Why 1?", "Why 2?"]
    wb_key = WB.submission_id_for(wb)
    assert _used(ctx, submission_id=wb_key, workbench_session_id=wb) == (LIMIT, LIMIT)   # 3/3, never 0/3
    with pytest.raises(SidecarError) as refused:
        _ask(ctx, workbenchSessionId=wb, question="One more?")
    assert refused.value.code == "question_limit_reached"


def test_the_production_counting_functions_read_one_attempt_across_the_handoff(sidecar):
    """Astra's probe, on the counting functions themselves: 3/3 before and after."""

    _paths, ctx, session = _metered(sidecar)
    vault, repository = ctx.require_vault()
    for index in range(LIMIT):
        _ask(ctx, session, submissionId=BOX, question=f"Why {index}?")
    wb = _open_steps(ctx, session, submissionId=BOX)
    before = question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id=session,
                            submission_id=BOX)
    after = question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id=None,
                           submission_id=WB.submission_id_for(wb), workbench_session_id=wb)
    assert before == after == (LIMIT, LIMIT)
    assert attempt_identities(repository, practice_item_id=ITEM, submission_id=WB.submission_id_for(wb),
                              workbench_session_id=wb) == (frozenset({BOX, WB.submission_id_for(wb)}),
                                                           frozenset({wb}))


def test_the_reader_s_questions_count_back_in_the_answer_box(sidecar):
    """The other direction: steps left for the answer box again."""

    _paths, ctx, session = _metered(sidecar)
    _ask(ctx, session, submissionId=BOX, question="In the box?")
    wb = _open_steps(ctx, session, submissionId=BOX)
    _ask(ctx, workbenchSessionId=wb, question="In the Reader?")
    back = _transcript(ctx, sessionId=session, submissionId=BOX)
    assert [event["questionMd"] for event in back["events"]] == ["In the box?", "In the Reader?"]
    assert _used(ctx, session=session, submission_id=BOX) == (2, LIMIT)


def test_raw_question_rows_keep_the_key_they_were_asked_under(sidecar):
    _paths, ctx, session = _metered(sidecar)
    first = _ask(ctx, session, submissionId=BOX)
    wb = _open_steps(ctx, session, submissionId=BOX)
    second = _ask(ctx, workbenchSessionId=wb)
    _vault, repository = ctx.require_vault()
    assert repository.question_event(first["eventId"])["source_context"]["attempt_key"] == {"submission_id": BOX}
    key = repository.question_event(second["eventId"])["source_context"]["attempt_key"]
    assert key["submission_id"] == WB.submission_id_for(wb) and key["workbench_session_id"] == wb


def test_the_draft_key_is_read_from_the_checkpoint_when_the_screen_names_none(sidecar):
    _paths, ctx, session = _metered(sidecar)
    for index in range(LIMIT):
        _ask(ctx, session, submissionId=BOX, question=f"Why {index}?")
    _call(ctx, "save_practice_draft", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "U Sigma",
                                       "hintsUsed": 0, "submissionId": BOX})
    wb = _open_steps(ctx, session)
    assert len(_transcript(ctx, workbenchSessionId=wb)["events"]) == LIMIT
    assert _used(ctx, submission_id=WB.submission_id_for(wb), workbench_session_id=wb) == (LIMIT, LIMIT)


def test_the_handoff_is_recorded_once_and_salience_only(sidecar):
    _paths, ctx, session = _metered(sidecar)
    wb = _open_steps(ctx, session, submissionId=BOX)
    # A resume on the practice screen names the same draft: nothing new is recorded.
    _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "sessionId": wb,
                                  "practiceSessionId": session, "submissionId": BOX})
    _vault, repository = ctx.require_vault()
    rows = [row for row in repository.reader_interaction_events(kind="reader_action_invoked", subject_id=wb)
            if row["payload"].get("event") == WB.DRAFT_HANDOFF_EVENT]
    assert [row["payload"]["draft_submission_ids"] for row in rows] == [[BOX]]
    assert rows[0]["payload"]["authority_class"] == SF.SALIENCE_ONLY
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(rows[0])
    # The workbench's own key is never recorded as a draft.
    assert WB.record_draft_handoff(repository, wb, [WB.submission_id_for(wb)]) == []


def test_a_reader_open_hands_no_draft(sidecar):
    _paths, ctx, session = _metered(sidecar)
    _ask(ctx, session, submissionId=BOX, question="In the box?")
    vault, repository = ctx.require_vault()
    opened = _call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": ITEM,
                                           "stemMd": vault.practice_items[ITEM].prompt, "submissionId": BOX})
    wb = opened["session"]["sessionId"]
    assert _transcript(ctx, workbenchSessionId=wb)["events"] == []
    assert attempt_identities(repository, practice_item_id=ITEM, submission_id=None,
                              workbench_session_id=wb) == (frozenset(), frozenset({wb}))


def test_another_serving_s_answer_box_is_still_another_attempt(sidecar):
    _paths, ctx, session = _metered(sidecar)
    _ask(ctx, session, submissionId=BOX, question="In the box?")
    _open_steps(ctx, session, submissionId=BOX)
    other = _transcript(ctx, sessionId=session, submissionId="another-serving")
    assert other["events"] == []
    assert _used(ctx, session=session, submission_id="another-serving") == (0, LIMIT)


def test_a_new_attempt_still_gets_a_fresh_allowance(sidecar):
    _paths, ctx, session = _metered(sidecar)
    vault, repository = ctx.require_vault()
    for index in range(LIMIT):
        _ask(ctx, session, submissionId=BOX, question=f"Why {index}?")
    wb = _open_steps(ctx, session, submissionId=BOX)
    # The attempt is submitted (an attempt row after every question): the window starts again.
    from tests.test_reader_ca2_one_ask import _attempt

    _attempt(repository, "att_done", "2999-01-01T00:00:00Z")
    assert practice_thread_events(repository, practice_item_id=ITEM, session_id=None,
                                  submission_id=WB.submission_id_for(wb), workbench_session_id=wb) == []
    assert _used(ctx, session=session, submission_id="next-serve") == (0, LIMIT)
    assert _used(ctx, session=session, submission_id=BOX) == (0, LIMIT)


def test_the_plan_route_stays_unlimited_across_the_handoff(sidecar):
    _paths, ctx, _tutor = sidecar({("tutor_qa", "max_questions_practice"): 1}, tutor=PlanTutor())
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    for index in range(3):
        assert _ask(ctx, session, submissionId=BOX, question=f"Why {index}?")["remaining"] is None
    wb = _open_steps(ctx, session, submissionId=BOX)
    assert _ask(ctx, workbenchSessionId=wb, question="And in the Reader?")["remaining"] is None
