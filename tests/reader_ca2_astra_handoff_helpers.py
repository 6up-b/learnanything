"""What other test files use from ``tests/test_reader_ca2_astra_handoff.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.tutor.tutor_qa import question_usage

from tests.reader_ca2_codex_review_helpers import ITEM, FakeTutor, _call


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

    from learnloop_sidecar.handlers.tutor_qa import attempt_aliases

    vault, repository = ctx.require_vault()
    return question_usage(vault, repository, context="practice", practice_item_id=ITEM, session_id=session,
                          submission_id=submission_id, workbench_session_id=workbench_session_id, metered=True,
                          aliases=attempt_aliases(repository, ITEM, submission_id, workbench_session_id))


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
