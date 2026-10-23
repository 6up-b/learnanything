"""Reader workbench RW2b: what a workbench attempt records (spec_reader_workbench_v1 §5.4; G5 all rows, G-H2, G-H3, G64).

The workbench sends no client count: the server's fold at ``workbench.submit``
counts the visible book once, one per shown check and per shown level 1-3
hint, ``primed`` for a shown level 4-5 hint, and the answer box's shown hints
by H2b's window; nothing is counted twice and no shown hint is lost. A
cancelled or never-read hint counts nothing; a row delivered after the
submission was admitted is never shown. A key overlap writes a
``tutor_answer`` reveal with basis ``workbench_hint:<kind>:L<n>`` (the item's
own hints exempt). ``resolve_attempt_activity_policy`` gives every assisted
attempt zero certification credit. Abandoned problems write no attempt, a
discriminating answer changes nothing, the answer box's submit records an
open problem's help, and a rebuild reproduces evidence identically. Fakes only.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
import json
import sqlite3

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.hints import service as hint_service
from learnloop.hints import workbench as hint_workbench
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM, WORK, ChooserFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def _attempt(paths, attempt_id):
    [row] = _rows(paths, "SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,))
    return row


def _submit(ctx, wb, session):
    return call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})["attempt"]


def _take(ctx, wb, level, **params):
    return run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": level, **params}))


def _check(ctx, wb):
    return run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))


def _policy(row):
    return resolve_attempt_activity_policy(attempt_type=row["attempt_type"], primed=bool(row["primed"]),
                                           hints_used=int(row["hints_used"]))


# -- the rows of §5.4's table -----------------------------------------------------------------------


def test_no_help_and_no_book_is_the_learners_own_attempt(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 0)
    assert _policy(attempt).eligible_for_certification is True


def test_a_shown_check_is_one_hint_and_the_attempt_certifies_nothing(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert _check(ctx, wb)["shown"] is True
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (1, 0)
    assert _policy(attempt).eligible_for_certification is False


@pytest.mark.parametrize("level", [1, 2, 3])
def test_each_shown_hint_at_levels_one_to_three_adds_one(tmp_path, grader, level):
    paths, ctx, session = sidecar(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx)
    hint = _take(ctx, wb, level)
    assert hint["status"] == "ready" and hint["shown"] is True and hint["level"] == level
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (1, 0)
    assert _policy(attempt).eligible_for_certification is False


@pytest.mark.parametrize("level", [4, 5])
def test_worked_help_primes_and_adds_no_count(tmp_path, grader, level):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    hint = _take(ctx, wb, level)
    assert hint["status"] == "ready" and hint["level"] == level
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 1)
    assert _policy(attempt).eligible_for_certification is False


def test_the_book_a_check_and_three_hints_add_up_with_one_record_line(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, chains = open_problem(ctx, origin="reader", entry="work_through")
    assert call(ctx, "workbench.get", {"sessionId": wb})["session"]["sourceVisible"] is True
    _check(ctx, wb)
    _take(ctx, wb, 1)
    _take(ctx, wb, 3)
    _take(ctx, wb, 4)
    record = call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]
    # book + check + L1 + L3 = 4 hint-equivalents, and worked help.
    assert record["hints"] == 4 and record["help"] == {"checks": 1, "byLevel": [1, 0, 1], "worked": 1, "primed": True}
    assert record["line"].startswith("book open · 4 hints and worked help")
    assert "a check" in record["footer"] and "worked help ◌" in record["footer"]
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (4, 1)
    rows = help_rows(paths, wb)
    assert {row["attempt_id"] for row in rows if row["shown"]} == {attempt["id"]}
    assert {row["practice_session_id"] for row in rows} == {session}


def test_a_key_overlap_writes_the_workbench_reveal_basis_and_the_items_own_hint_none(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    walk = _take(ctx, wb, 5)
    assert walk["kind"] == "walkthrough"
    reveals = _rows(paths, "SELECT source_kind, basis, amount FROM reveal_events")
    assert reveals and reveals[-1]["basis"] == "workbench_hint:walkthrough:L5"
    assert reveals[-1]["source_kind"] == "tutor_answer"


def test_an_authored_hint_served_on_rung_three_writes_no_reveal(tmp_path, grader):
    from tests.hint_fakes import WriterFake

    paths, ctx, session = sidecar(tmp_path, writer=WriterFake(provider_type="codex_sdk"))
    wb, _chains = open_problem(ctx)
    hint = _take(ctx, wb, 3)
    assert hint["status"] == "ready" and hint["kind"] == "authored" and hint["reason"] == "codex_refused"
    assert _rows(paths, "SELECT * FROM reveal_events") == []
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert attempt["hints_used"] == 1


def _written_not_read(ctx, wb):
    """A hint job that finished writing and was never read (the sidecar runs
    it in its own thread, as in the app)."""

    ctx.hints_inline = False
    started = call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    assert started["state"] == "pending"
    assert ctx.workbench_help_jobs.get(started["jobId"]).done.wait(30)
    ctx.hints_inline = True
    return started


def test_a_cancelled_or_unread_hint_counts_nothing(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    started = _written_not_read(ctx, wb)
    # Never read: never shown.
    assert [row["shown"] for row in help_rows(paths, wb)] == [0]
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 0)
    # A read after the submit delivers nothing and shows no text.
    late = call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["result"]
    assert late["shown"] is False and not late.get("hintMd")
    assert [row["shown"] for row in help_rows(paths, wb)] == [0]


def test_a_cancelled_hint_is_never_delivered(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    started = _written_not_read(ctx, wb)
    assert call(ctx, "workbench.cancel_help", {"jobId": started["jobId"]})["cancelled"] is True
    assert call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["state"] == "cancelled"
    assert _attempt(paths, _submit(ctx, wb, session)["attemptId"])["hints_used"] == 0


def test_a_row_is_never_shown_once_its_submission_is_admitted(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    started = _written_not_read(ctx, wb)
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    from learnloop_sidecar.handlers.workbench import _stamp_help_rows

    vault, repository = ctx.require_vault()
    # The submit stamps first, then reads the fold: a delivery in between is refused.
    _stamp_help_rows(repository, wb, 5)
    outcome, shown = hint_workbench.deliver_workbench(repository, row["id"], item=vault.practice_items[ITEM])
    assert (outcome, shown) == (hint_service.SUBMISSION_COMPLETE, None)
    assert call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["result"]["shown"] is False
    assert help_rows(paths, wb)[0]["shown"] == 0


def test_a_hint_delivered_before_the_admission_is_counted(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    started = call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    assert call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["result"]["shown"] is True
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert attempt["hints_used"] == 1


def test_a_workbench_hint_and_an_answer_box_hint_in_the_same_window_count_once_each(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    # The answer box's hint, under its own key (H2a), before the learner moves into steps.
    box = call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                             "answerMd": WORK})["result"]
    assert box["shown"] is True
    wb, _chains = open_problem(ctx)
    _take(ctx, wb, 3)
    record = call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]
    assert record["hints"] == 2
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (2, 0)
    rows = _rows(paths, "SELECT surface, attempt_id, shown FROM help_assists WHERE assist_kind = 'hint'")
    assert sorted((row["surface"], row["attempt_id"] == attempt["id"]) for row in rows) == [
        ("practice", True), ("workbench", True)]
    # A second submit in the window (the answer box again) counts neither again.
    again = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                         "attemptType": "independent_attempt", "hintsUsed": 0, "submissionId": "k2"})
    assert _attempt(paths, again["attemptId"])["hints_used"] == 0


def test_the_answer_box_submit_records_an_open_problems_help(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    _check(ctx, wb)
    _take(ctx, wb, 4)
    # The learner goes back to the answer box and submits there: the open
    # problem's check and worked help are held (RW2a's rule, RW2b's rows).
    attempt = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                           "attemptType": "independent_attempt", "hintsUsed": 0,
                                           "submissionId": "box"})
    row = _attempt(paths, attempt["attemptId"])
    assert row["hints_used"] >= 1 and row["primed"] == 1


def test_a_discriminating_answer_changes_none_of_the_counts(tmp_path, grader):
    from tests.test_workbench_discriminate import _rival_check

    paths, ctx, session = sidecar(tmp_path, check=_rival_check())
    wb, _chains = open_problem(ctx)
    _check(ctx, wb)
    question = _take(ctx, wb, 1)
    assert question["kind"] == "discriminating"
    call(ctx, "workbench.answer_discriminating", {"sessionId": wb, "questionAssistId": question["assistId"],
                                                  "answerMd": "0"})
    attempt = _attempt(paths, _submit(ctx, wb, session)["attemptId"])
    # The check and the question: two; the answer adds nothing.
    assert (attempt["hints_used"], attempt["primed"]) == (2, 0)
    assert "0" not in attempt["learner_answer_md"].split()


def test_an_abandoned_problem_writes_no_attempt_and_a_rebuild_leaves_the_evidence(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    kept, _chains = open_problem(ctx)
    _check(ctx, kept)
    _take(ctx, kept, 3)
    attempt_id = _submit(ctx, kept, session)["attemptId"]
    dropped, _chains2 = open_problem(ctx, ("a different start",))
    before_attempts = len(_rows(paths, "SELECT id FROM practice_attempts"))
    call(ctx, "workbench.abandon", {"sessionId": dropped})
    assert len(_rows(paths, "SELECT id FROM practice_attempts")) == before_attempts

    def snapshot():
        return {table: sorted(json.dumps(row, sort_keys=True, default=str)
                              for row in _rows(paths, f'SELECT * FROM "{table}"'))
                for table in ("practice_attempts", "grading_evidence", "help_assists", "reveal_events")}

    before = snapshot()
    vault = load_vault(paths.root)
    repository = Repository.attach(paths.sqlite_path)
    clock = FrozenClock(datetime(2026, 10, 30, 12, 0, tzinfo=UTC))
    rebuild_all_derived_state(vault, repository, clock=clock)
    assert snapshot() == before
    assert _attempt(paths, attempt_id)["hints_used"] == 2


def test_a_hint_free_workbench_submit_is_what_it_was_before_rw2b(tmp_path, grader):
    shapes = {}
    for label, config in (("help_on", ""), ("help_off", "[workbench]\nhelp_enabled = false\n")):
        paths, ctx, session = sidecar(tmp_path / label, config)
        wb, _chains = open_problem(ctx)
        payload = call(ctx, "workbench.submit", {"sessionId": wb, "practiceSessionId": session})
        attempt = _attempt(paths, payload["attempt"]["attemptId"])
        shapes[label] = {
            "attempt": {key: attempt[key] for key in ("hints_used", "primed", "attempt_type", "entry_surface",
                                                       "learner_answer_md", "declared_stuck", "correctness")},
            "keys": sorted(payload), "attempt_keys": sorted(payload["attempt"]),
            "record": payload["session"]["record"],
            "help_rows": len(help_rows(paths)),
        }
    assert shapes["help_on"] == shapes["help_off"]
