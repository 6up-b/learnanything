"""Adaptive hints H2a: the round-3 verify's reopened items W1-W5 (docs/reviews/hints-h2a-codex-review.md, fix round 3).

Each test reproduces one item on the tree the verify read (``1f23ee970``)
and pins its fix. Fakes only (no model is reached).
"""

from __future__ import annotations

import json
import threading
import time
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.hints import service as S
from learnloop_sidecar.handlers import practice as practice_handlers
from tests.approach_map_fakes import LO
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, add_hypothesis, assists, good_answer, \
    hint_vault, prefer, reveals, store_map
from tests.test_hint_h2a_review_round2 import ARGMAX, SELF_GRADE, _ask, _attempt, _call, _context, _setup

# ---------------------------------------------------------------------------
# W1: a keyless submit closes its session's window for a waiting delivery
# ---------------------------------------------------------------------------


def _keyless_race(tmp_path, option: str = "next_step@L3"):
    """Sidecar B prepares a hint under ``k1``; sidecar A will submit the same
    session and item WITHOUT a submission key."""

    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    a, b = _context(paths), _context(paths)
    session = _call(a, "start_session", {"energy": "medium"})["sessionId"]
    b.hint_writer_client = WriterFake()
    b.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    job = _call(b, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                             "answerMd": WORK})["jobId"]
    assert b.hint_jobs.get(job).done.wait(30)
    return paths, a, b, session, job


def _submit_keyless(ctx, session, hints: int = 0):
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": hints, "selfGrade": SELF_GRADE})


def test_w1_a_delivery_waiting_on_a_keyless_commit_is_refused(tmp_path, monkeypatch):
    paths, a, b, session, job = _keyless_race(tmp_path)
    insert = Repository._insert_practice_attempt
    racer: dict = {}

    def insert_while_racing(self, connection, attempt):
        trying = threading.Event()

        def deliver():
            trying.set()
            racer["result"] = _call(b, "practice.hint_job", {"jobId": job})["result"]

        thread = threading.Thread(target=deliver)
        thread.start()
        assert trying.wait(10)
        time.sleep(0.3)  # B is now waiting on A's write lock
        racer["thread"] = thread
        return insert(self, connection, attempt)

    monkeypatch.setattr(Repository, "_insert_practice_attempt", insert_while_racing)
    result = _submit_keyless(a, session)
    racer["thread"].join(30)
    attempt = _attempt(paths, result["attemptId"])
    assert attempt["submission_id"] is None and (attempt["hints_used"], attempt["primed"]) == (0, 0)
    assert (racer["result"]["status"], racer["result"]["reason"]) == ("unavailable", "submission_complete")
    assert racer["result"]["shown"] is False and racer["result"]["hintMd"] is None
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 0 and reveals(paths.sqlite_path) == []


def test_w1_a_delivery_before_a_keyless_commit_is_counted(tmp_path, monkeypatch):
    paths, a, b, session, job = _keyless_race(tmp_path)
    snapshot = practice_handlers._server_hint_fold
    polled: dict = {}

    def fold_then_deliver(*args, **kwargs):
        fold = snapshot(*args, **kwargs)
        polled["result"] = _call(b, "practice.hint_job", {"jobId": job})["result"]
        return fold

    monkeypatch.setattr(practice_handlers, "_server_hint_fold", fold_then_deliver)
    result = _submit_keyless(a, session)
    assert polled["result"]["shown"] is True
    assert _attempt(paths, result["attemptId"])["hints_used"] == 1


def test_w1_a_hint_free_keyless_submit_records_what_it_did(tmp_path):
    paths = hint_vault(tmp_path, config=ARGMAX)
    ctx = _context(paths)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    first = _attempt(paths, _submit_keyless(ctx, session, hints=1)["attemptId"])
    second = _attempt(paths, _submit_keyless(ctx, session)["attemptId"])
    assert (first["hints_used"], first["primed"], first["attempt_type"], first["submission_id"]) == (
        1, 0, "independent_attempt", None)
    assert (second["hints_used"], second["primed"], second["submission_id"]) == (0, 0, None)
    assert assists(paths.sqlite_path) == []


def _row(connection, assist_id: str, session: str, requested_at: str, *, shown: int = 0, level: int = 3) -> None:
    from learnloop.db.stores.help_assists import insert_assist

    insert_assist(connection, {
        "id": assist_id, "surface": "practice", "assist_kind": "hint", "practice_item_id": ITEM,
        "practice_session_id": session, "submission_id": "k_" + assist_id, "hint_kind": "next_step",
        "level": level, "chooser": "fallback", "shown": shown, "counted_by": "server",
        "requested_at": requested_at})


def _attempt_row(connection, attempt_id: str, session: str, created_at: str, submission_id: str | None) -> None:
    connection.execute(
        "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
        "learner_answer_md, correctness, created_at, session_id, submission_id) "
        "VALUES (?, ?, ?, 'short_answer', 'independent_attempt', '', 0.0, ?, ?, ?)",
        (attempt_id, ITEM, LO, created_at, session, submission_id))


def test_w1_the_fence_and_the_keyless_fold_share_one_window(tmp_path):
    """Rows requested at or before the item's last attempt in the session
    are closed (never shown after it) and outside the next keyless fold;
    rows after it are the next window's. Another session's attempt closes
    nothing here."""

    from learnloop.attempts.hint_fold import read_fold
    from learnloop.db.stores.help_assists import mark_shown

    paths = hint_vault(tmp_path, config=ARGMAX)
    ctx = _context(paths)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    other = _call(_context(paths), "start_session", {"energy": "medium"})["sessionId"]
    with closing(connect(paths.sqlite_path)) as connection:
        _row(connection, "before", session, "2026-10-18T09:00:00Z")
        _row(connection, "tie", session, "2026-10-18T09:05:00Z")
        _row(connection, "after", session, "2026-10-18T09:06:00Z")
        _attempt_row(connection, "att_keyless", session, "2026-10-18T09:05:00Z", None)
        _attempt_row(connection, "att_other_session", other, "2026-10-18T09:30:00Z", None)
        connection.commit()
        assert [mark_shown(connection, row, shown_at="2026-10-18T09:10:00Z")
                for row in ("before", "tie", "after")] == [False, False, True]
        count, primed, since = read_fold(connection, practice_item_id=ITEM, session_id=session, submission_id=None)
        assert (count, primed, since) == (1, False, "2026-10-18T09:05:00Z")


# ---------------------------------------------------------------------------
# W2: an option fallback never raises a fixed level
# ---------------------------------------------------------------------------

def test_w2_the_books_way_after_a_level_2_hint_with_the_draft_cleared_is_not_level_3(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w = _ask(vault, repository, "localize@L2")
    assert (first.status, first.level) == (S.READY, 2)
    second, writer = _ask(vault, repository, "localize@L2", request="book_way", answered_assist_id=first.assist_id,
                          work_md="")
    assert second.status == S.UNAVAILABLE and second.level is None and second.hint_md is None
    assert second.message == S.NO_FITTING_HINT_MESSAGE and writer.calls == 0
    row = assists(paths.sqlite_path)[1]
    assert json.loads(row["options_json"])["options"] == [] and row["counted_by"] is None


# ---------------------------------------------------------------------------
# W3: "already at the givens" passes the whole from-givens contract
# ---------------------------------------------------------------------------

def test_w3_a_walkthrough_at_the_givens_that_claims_work_stands_is_re_asked(tmp_path):
    _paths, vault, repository = _setup(tmp_path)

    def at_givens(stands: str):
        def answer(context):
            out = good_answer(context)
            out["placement"] = {**out["placement"], "reached_node_id": "g", "route_id": "r_ref",
                                "stands_quote": stands, "work_matches_a_route": False,
                                "work_valid_so_far": False}
            return out
        return answer

    result, writer = _ask(vault, repository, "walkthrough@L5", [at_givens(WORK.splitlines()[0]), at_givens("")],
                          taken_level=5)
    assert (result.status, result.kind, result.level, result.reason) == (S.READY, "walkthrough", 5, "unplaced_work")
    assert writer.calls == 2 and writer.contexts[1]["chosen"].get("from_givens")
    assert result.placement["stands_quote"] == ""


# ---------------------------------------------------------------------------
# W4: a kind change keeps the target's placement constraints
# ---------------------------------------------------------------------------

def test_w4_a_second_zero_eig_answer_from_the_givens_keeps_the_from_givens_contract(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    add_hypothesis(paths.sqlite_path, "h1", "Adds one to a CDF value as if it were a density")
    add_hypothesis(paths.sqlite_path, "h2", "Reads the CDF as the density")
    first, _w = _ask(vault, repository, "discriminating@L3")
    assert (first.status, first.kind, first.level) == (S.READY, "discriminating", 3)

    def zero_eig(start: str, target: str, *, quotes: bool):
        def answer(context):
            out = good_answer(context)
            rivals = context.get("rivals") or []
            out["candidates"] = [{"question_md": "What does your formula give at x = 0?",
                                  "predictions": [{"rival_id": rival["id"], "answer": "0"} for rival in rivals]}]
            out["fallback_hint_md"] = "Evaluate your CDF at the point."
            placement = {**out["placement"], "reached_node_id": start, "route_id": "r_ref",
                         "work_matches_a_route": False, "work_valid_so_far": False}
            placement["stands_quote"] = ""  # nothing claimed to stand: only the placement is wrong
            if not quotes:
                placement.update(quotes=[], first_questionable_quote="")
            out["placement"], out["target_node_id"] = placement, target
            return out
        return answer

    result, writer = _ask(vault, repository, "discriminating@L3",
                          [zero_eig("cdf", "goal", quotes=True), zero_eig("cdf", "goal", quotes=True),
                           zero_eig("g", "cdf", quotes=False)],
                          request="book_way", answered_assist_id=first.assist_id)
    log = json.loads(assists(paths.sqlite_path)[-1]["contract_failures_json"])
    assert log["rounds"][0]["switched_to"] == "from_givens"
    assert "from_givens_not_at_givens" in log["rounds"][1]["failures"]
    assert (result.status, result.kind, writer.calls) == (S.READY, "next_step", 3)
    assert result.placement["reached_node_id"] == "g"


# ---------------------------------------------------------------------------
# W5: delivery fails closed when the item is gone or changed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("change", ["removed", "edited"])
def test_w5_a_hint_for_a_removed_or_changed_item_is_never_shown(tmp_path, change):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = _context(paths)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    ctx.hint_writer_client = WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                               "answerMd": WORK, "takenLevel": 5})["jobId"]
    assert ctx.hint_jobs.get(job).done.wait(30)
    vault, _repository = ctx.require_vault()
    if change == "removed":
        vault.practice_items.pop(ITEM)
    else:
        vault.practice_items[ITEM] = vault.practice_items[ITEM].model_copy(
            update={"prompt": vault.practice_items[ITEM].prompt + " (edited)"})
    for _ in range(2):  # refused, and it stays refused (not retried)
        result = _call(ctx, "practice.hint_job", {"jobId": job})["result"]
        assert (result["status"], result["reason"], result["shown"], result["hintMd"]) == (
            "unavailable", "item_changed", False, None)
    [row] = assists(paths.sqlite_path)
    assert (row["shown"], row["shown_at"]) == (0, None) and reveals(paths.sqlite_path) == []
    assert ctx.hint_jobs.get(job).refused == "item_changed"


def test_w5_an_unchanged_item_still_delivers(tmp_path):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    ctx = _context(paths, inline=True)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    ctx.hint_writer_client = WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                               "answerMd": WORK, "takenLevel": 5})
    assert job["result"]["status"] == "ready" and job["result"]["shown"] is True
    assert len(reveals(paths.sqlite_path)) == 1
