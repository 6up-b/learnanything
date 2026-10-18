"""Adaptive hints H2b, fix round 3: the orchestrator's ruling R1 (docs/reviews/hints-h2b-codex-review.md).

A workbench submit folds the answer box's hints by the rule H2a already uses
for a keyless submit: the practice session's shown, unattached,
server-counted hint rows of the item requested after the item's last attempt
in this practice session, whatever their submission key. It takes that fold
again inside the attempt's own write transaction and attaches exactly those
rows to its attempt. Whichever attempt of the session and item commits first
takes the rows; a later one never counts them again. The record line reads
the same window. This replaces the link and release design, which lost the
hint when problems were reopened and resumed (the verify's F1) and counted it
twice after an interrupted answer-box attach (F10). Fakes only.
"""

from __future__ import annotations

import pytest

from learnloop_sidecar.handlers import practice
from learnloop_sidecar.handlers.workbench import WorkbenchOpenInput
from tests.hint_fakes import ITEM, WORK, ChooserFake, assists, prefer
from tests.test_hint_h2b_review import (  # noqa: F401 - ``grader`` is a fixture
    _attempt,
    _call,
    _hint,
    _sidecar,
    _wb_submit,
    grader,
)

# The practice screen sends no hand-off now: the server's window needs none.
# The tree before ruling R1 (f528311a5) needed the answer box's key and
# session on every open, so on that tree these helpers send what its screen
# sent; that is how each test below reproduces the verify's scenario there.
_BEFORE_R1 = "carried_submission_id" in WorkbenchOpenInput.model_fields


def _open(ctx, session, key, wb=None):
    payload = {"origin": "practice", "entry": "practice_screen"}
    if wb is None:
        payload.update({"practiceItemId": ITEM, "stemMd": "Find P."})
    else:
        payload["sessionId"] = wb
    if _BEFORE_R1:
        payload.update({"carriedSubmissionId": key, "carriedSessionId": session})
    view = _call(ctx, "workbench.open", payload)["session"]
    if wb is None:
        _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s1",
                                           "op": "add", "bodyMd": WORK})
    return view


def _record_hints(ctx, wb):
    return _call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]["hints"]


def _answer_box(ctx, session, key):
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "submissionId": key})


def _two_problems(ctx, session, key="k1"):
    """The verify's F1 sequence up to Submit: open W1, abandon it, open W2,
    leave it, reopen W1, resume W2. Neither problem has submitted."""

    first = _open(ctx, session, key)["sessionId"]
    _call(ctx, "workbench.abandon", {"sessionId": first})
    second = _open(ctx, session, key)["sessionId"]
    assert second != first
    _call(ctx, "workbench.leave", {"sessionId": second})
    _open(ctx, session, key, wb=first)
    _open(ctx, session, key, wb=second)
    return first, second


# -- the verify's F1 sequence --------------------------------------------------------------------


def test_r1_the_verify_sequence_counts_the_hint_once(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    assert _hint(ctx, session, "k1")["shown"] is True
    first, second = _two_problems(ctx, session)
    assert (_record_hints(ctx, first), _record_hints(ctx, second)) == (1, 1)
    attempt = _attempt(paths, _wb_submit(ctx, second, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (1, 0)
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == attempt["id"]


def test_r1_the_verify_sequence_keeps_a_level_five_priming(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    worked = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                                  "answerMd": "", "takenLevel": 5})["result"]
    assert worked["status"] == "ready" and worked["level"] == 5
    _first, second = _two_problems(ctx, session)
    attempt = _attempt(paths, _wb_submit(ctx, second, session)["attemptId"])
    assert attempt["primed"] == 1


@pytest.mark.parametrize("submitter", ["first", "second"])
@pytest.mark.parametrize("order", ["reopen_then_resume", "resume_then_reopen"])
def test_r1_any_order_of_reopen_and_resume_counts_once_from_either_problem(tmp_path, grader, order, submitter):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    first = _open(ctx, session, "k1")["sessionId"]
    _call(ctx, "workbench.abandon", {"sessionId": first})
    second = _open(ctx, session, "k1")["sessionId"]
    _call(ctx, "workbench.leave", {"sessionId": second})
    steps = [first, second] if order == "reopen_then_resume" else [second, first]
    for wb in steps:
        _open(ctx, session, "k1", wb=wb)
    # Both open problems name the hint before Submit (the window they fold).
    assert (_record_hints(ctx, first), _record_hints(ctx, second)) == (1, 1)
    chosen, other = (first, second) if submitter == "first" else (second, first)
    attempt = _attempt(paths, _wb_submit(ctx, chosen, session)["attemptId"])
    assert attempt["hints_used"] == 1
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == attempt["id"]
    # The other problem's window starts at that attempt: nothing again.
    assert _record_hints(ctx, other) == 0
    assert _attempt(paths, _wb_submit(ctx, other, session)["attemptId"])["hints_used"] == 0


def test_r1_back_on_the_answer_box_it_counts_once_and_a_later_workbench_submit_counts_nothing(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    first, second = _two_problems(ctx, session)
    assert (_record_hints(ctx, first), _record_hints(ctx, second)) == (1, 1)
    _call(ctx, "workbench.leave", {"sessionId": second})
    submitted = _answer_box(ctx, session, "k1")
    assert _attempt(paths, submitted["attemptId"])["hints_used"] == 1
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == submitted["attemptId"]
    assert (_record_hints(ctx, first), _record_hints(ctx, second)) == (0, 0)
    _open(ctx, session, "k1", wb=second)
    assert _attempt(paths, _wb_submit(ctx, second, session)["attemptId"])["hints_used"] == 0


# -- F10: an interrupted answer-box attach -------------------------------------------------------


def test_r1_f10_an_interrupted_answer_box_attach_never_lets_a_problem_take_the_hint(tmp_path, grader, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    first = _open(ctx, session, "k1")["sessionId"]
    _call(ctx, "workbench.abandon", {"sessionId": first})
    second = _open(ctx, session, "k1")["sessionId"]
    _call(ctx, "workbench.leave", {"sessionId": second})
    # The answer box's attempt commits; the process ends before H0's keyed
    # attach (the row keeps attempt_id NULL).
    with monkeypatch.context() as interrupted:
        interrupted.setattr(practice, "_attach_hint_reveals", lambda *args, **kwargs: None)
        submitted = _answer_box(ctx, session, "k1")
    assert _attempt(paths, submitted["attemptId"])["hints_used"] == 1
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None
    # The committed attempt started the next window: the problem folds 0 rows.
    _open(ctx, session, "k1", wb=second)
    assert _record_hints(ctx, second) == 0
    attempt = _attempt(paths, _wb_submit(ctx, second, session)["attemptId"])
    assert attempt["hints_used"] == 0
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None
    # The answer box's recovery (a retry of its key) attaches it to its own attempt.
    assert _answer_box(ctx, session, "k1")["attemptId"] == submitted["attemptId"]
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == submitted["attemptId"]


# -- rows outside the window ---------------------------------------------------------------------


def test_r1_a_hint_of_another_practice_session_is_never_folded(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    problem = _open(ctx, session, "k1")["sessionId"]
    _call(ctx, "workbench.leave", {"sessionId": problem})
    _call(ctx, "end_session", {"sessionId": session})
    later = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    _open(ctx, later, "k2", wb=problem)
    assert _record_hints(ctx, problem) == 0
    attempt = _attempt(paths, _wb_submit(ctx, problem, later)["attemptId"])
    assert attempt["hints_used"] == 0
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None


def test_r1_a_hint_requested_before_the_items_last_attempt_in_the_session_is_never_folded(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    problem = _open(ctx, session, "k1")["sessionId"]
    _call(ctx, "workbench.leave", {"sessionId": problem})
    # An attempt of the item under another key commits: its keyed fold does
    # not take k1's row, but the row now lies before the item's last attempt.
    other = _answer_box(ctx, session, "k9")
    assert _attempt(paths, other["attemptId"])["hints_used"] == 0
    _open(ctx, session, "k1", wb=problem)
    assert _record_hints(ctx, problem) == 0
    attempt = _attempt(paths, _wb_submit(ctx, problem, session)["attemptId"])
    assert attempt["hints_used"] == 0
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None
