"""The owner's 2026-10-25 capture (docs/reviews/owner-capture-2026-10-25-fixes.md), sidecar side.

B4: the practice screen's draft is bound to the queue's offer; the learner
goes into "Work in steps" and submits there (the offer is answered by that
attempt); the answer box's draft, its retry key and its hints stayed in the
session checkpoint, so the item opened again restored them, and its submit
failed with "The scheduler offer does not belong to this item/session or
was already consumed." B3: the Ask thread of an item is the current
attempt's, never a previous serving's. B2: the help style changes the next
hint the fallback serves. Fakes only.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, WriterFake, hint_vault
from tests.split_live_helpers import ReadyRuntime
from tests.test_stuck_prompt import StuckFake

STALE = "The scheduler offer does not belong to this item/session or was already consumed."


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


@pytest.fixture
def grader(monkeypatch):
    import learnloop.attempts.attempts as attempts_module
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _sidecar(tmp_path, config: str = ""):
    paths = hint_vault(tmp_path, config=config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _offer(ctx, session):
    snapshot = _call(ctx, "get_today_queue", {"sessionId": session})
    return next(item["schedulerCandidateId"] for section in snapshot["sections"] for item in section["items"]
                if item["practiceItemId"] == ITEM)


def _steps_submit(ctx, session, offer):
    """The practice screen's "Work in steps", one step, Submit (the
    workbench names the screen's serve, as Workbench.tsx does)."""

    view = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                         "stemMd": "Find P.", "schedulerCandidateId": offer,
                                         "planPresentationId": None})["session"]
    _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                       "bodyMd": WORK})
    return _call(ctx, "workbench.submit", {"sessionId": view["sessionId"], "practiceSessionId": session,
                                           "schedulerCandidateId": offer, "planPresentationId": None})["attempt"]


def _draft(ctx, session, key, offer, *, hints=0, answer="F(x) = x^2"):
    _call(ctx, "save_practice_draft", {"sessionId": session, "practiceItemId": ITEM, "answerMd": answer,
                                       "hintsUsed": hints, "submissionId": key, "schedulerCandidateId": offer})


# -- B4 -------------------------------------------------------------------------------------------


def test_b4_a_steps_submit_closes_the_answer_boxs_draft(tmp_path, grader):
    """Root cause: the steps submit answered the item, but the answer box's
    checkpoint (its retry key, hints and offer binding) stayed, so the item
    opened again restored it as if it were the same attempt."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "box-key", offer, hints=1)
    _steps_submit(ctx, session, offer)
    _vault, repository = ctx.require_vault()
    checkpoint = repository.fetch_session_checkpoint(session)
    assert (checkpoint or {}).get("current_practice_item_id") != ITEM


def test_b4_a_submit_under_a_key_whose_offer_another_attempt_answered_still_grades(tmp_path, grader):
    """Fail soft: the retry key's offer was answered by the steps attempt,
    so this submit answers no open offer. It is graded, unattributed (never
    linked to the consumed offer), and the offer keeps its one attempt."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    _draft(ctx, session, "box-key", offer)
    steps = _steps_submit(ctx, session, offer)
    result = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "box-key"})
    assert result["attemptId"] and result["attemptId"] != steps["attemptId"]
    [row] = _rows(paths, "SELECT scheduler_candidate_id FROM practice_attempts WHERE id = ?", (result["attemptId"],))
    assert row["scheduler_candidate_id"] is None
    [candidate] = _rows(paths, "SELECT chosen_attempt_id FROM scheduler_slate_candidates WHERE id = ?", (offer,))
    assert candidate["chosen_attempt_id"] == steps["attemptId"]
    # The retry is the same attempt (the key's receipt answers it).
    again = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                          "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "box-key"})
    assert again["attemptId"] == result["attemptId"]


def test_b4_a_submit_naming_an_answered_offer_still_grades(tmp_path, grader):
    """Fail soft: a new attempt naming an offer an earlier attempt answered
    (a stale offer the screen still held) is graded, unattributed."""

    paths, ctx, session = _sidecar(tmp_path)
    offer = _offer(ctx, session)
    first = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/2",
                                          "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "first", "schedulerCandidateId": offer})
    _draft(ctx, session, "second", offer)
    second = _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1/4",
                                           "hintsUsed": 0, "attemptType": "independent_attempt", "submissionId": "second", "schedulerCandidateId": offer})
    assert second["attemptId"] != first["attemptId"]
    [row] = _rows(paths, "SELECT scheduler_candidate_id FROM practice_attempts WHERE id = ?", (second["attemptId"],))
    assert row["scheduler_candidate_id"] is None
