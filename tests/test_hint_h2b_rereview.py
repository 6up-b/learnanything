"""Adaptive hints H2b, the Codex re-review's backend findings (docs/reviews/hints-h2b-codex-review.md).

F1 (reopened): a service hint shown before a problem the learner closed goes
with the work into the next problem opened in its place (fix round 3,
ruling R1: every workbench submit folds the keyless window of its practice
session and item, so closing or reopening a problem changes nothing), never
into another practice session. F9: the window's rows are stamped when the
workbench submission reaches the sidecar (first submit kept), with no latency: the
problem's open-to-submit latency starts when the problem opened, after the
hint was shown, so it is not on the row's basis. F8: the vault-open
placement pass pages past candidates it cannot place, so older unplaceable
attempts never starve a placeable one; only placements count against the
pass's bound. Fakes only.
"""

from __future__ import annotations

import time

from learnloop.clock import parse_utc
from learnloop.hints import map_builder, outcome
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM, assists, judgments
from tests.test_hint_h2b_review import (  # noqa: F401 - ``grader`` is a fixture
    _attempt,
    _call,
    _hint,
    _hinted_wrong_attempt,
    _into_steps,
    _report,
    _sidecar,
    _wb_submit,
    grader,
)
from tests.test_hint_outcome import OutcomeFake


# -- F1: close the problem, work in steps again, submit ------------------------------------------


def test_f1_a_hint_carried_into_a_closed_problem_counts_on_the_next_problem(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    assert _hint(ctx, session, "k1")["shown"] is True
    first = _into_steps(ctx, session, "k1")
    assert first["record"]["hints"] == 1
    _call(ctx, "workbench.abandon", {"sessionId": first["sessionId"]})
    # "Work in steps" again: a new problem (the closed one stays closed).
    second = _into_steps(ctx, session, "k1")
    assert second["sessionId"] != first["sessionId"]
    assert second["record"]["hints"] == 1
    attempt = _attempt(paths, _wb_submit(ctx, second["sessionId"], session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (1, 0)
    [row] = assists(paths.sqlite_path)
    # No problem link (ruling R1); the attempt takes it.
    assert (row["workbench_session_id"], row["attempt_id"]) == (None, attempt["id"])


def test_f1_a_level_five_carried_into_a_closed_problem_still_primes(tmp_path, grader):
    from tests.hint_fakes import ChooserFake, prefer

    paths, ctx, session = _sidecar(tmp_path)
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    worked = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                                  "answerMd": "", "takenLevel": 5})["result"]
    assert worked["status"] == "ready" and worked["level"] == 5
    first = _into_steps(ctx, session, "k1")
    _call(ctx, "workbench.abandon", {"sessionId": first["sessionId"]})
    second = _into_steps(ctx, session, "k1")
    attempt = _attempt(paths, _wb_submit(ctx, second["sessionId"], session)["attemptId"])
    assert attempt["primed"] == 1


def test_f1_released_hints_count_once_whichever_attempt_commits_first(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    first = _into_steps(ctx, session, "k1")
    _call(ctx, "workbench.abandon", {"sessionId": first["sessionId"]})
    # Back on the answer box, its key takes the row first.
    submitted = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": "F(x) = x^2", "attemptType": "independent_attempt",
        "hintsUsed": 0, "submissionId": "k1"})
    assert _attempt(paths, submitted["attemptId"])["hints_used"] == 1
    # A later problem on the item in the same session counts nothing again.
    time.sleep(1.05)
    second = _into_steps(ctx, session, "k1")
    assert second["record"]["hints"] == 0
    attempt = _attempt(paths, _wb_submit(ctx, second["sessionId"], session)["attemptId"])
    assert attempt["hints_used"] == 0
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == submitted["attemptId"]


def test_f1_a_reopened_problem_keeps_its_own_carried_hints(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    first = _into_steps(ctx, session, "k1")
    _call(ctx, "workbench.abandon", {"sessionId": first["sessionId"]})
    reopened = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen",
                                             "sessionId": first["sessionId"]})["session"]
    assert reopened["record"]["hints"] == 1
    attempt = _attempt(paths, _wb_submit(ctx, first["sessionId"], session)["attemptId"])
    assert attempt["hints_used"] == 1


def test_f1_released_hints_stay_in_their_practice_session(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    first = _into_steps(ctx, session, "k1")
    _call(ctx, "workbench.abandon", {"sessionId": first["sessionId"]})
    _call(ctx, "end_session", {"sessionId": session})
    later = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    second = _into_steps(ctx, later, "k2")
    assert second["record"]["hints"] == 0
    attempt = _attempt(paths, _wb_submit(ctx, second["sessionId"], later)["attemptId"])
    assert attempt["hints_used"] == 0
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None


# -- F9: the window's rows' submit time --------------------------------------------------------------


def test_f9_window_rows_are_stamped_at_the_workbench_submit(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    view = _into_steps(ctx, session, "k1")
    attempt = _attempt(paths, _call(ctx, "workbench.submit", {
        "sessionId": view["sessionId"], "practiceSessionId": session, "latencySeconds": 40})["attempt"]["attemptId"])
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == attempt["id"]
    # Stamped at admission: after the hint was shown, before the grade.
    assert row["submitted_at"] is not None
    assert parse_utc(row["shown_at"]).replace(microsecond=0) <= parse_utc(row["submitted_at"])
    assert parse_utc(row["submitted_at"]) <= parse_utc(attempt["created_at"]).replace(microsecond=999999)
    # The problem's latency starts when it opened, after the hint was shown:
    # not on this row's basis, so none is written.
    assert row["submit_latency_seconds"] is None
    [kind] = [entry for entry in _report(paths)["kinds"] if entry["hint_kind"] == "next_step"]
    assert kind["timing_unknown"] == 0
    assert kind["seconds_into_attempt_unknown"]["no_submit_latency"] == 1


def test_f9_the_first_submit_time_stays(tmp_path, grader):
    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import stamp_window_submitted

    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    view = _into_steps(ctx, session, "k1")
    with connect(paths.sqlite_path) as connection:
        assert stamp_window_submitted(connection, practice_item_id=ITEM, session_id=session, since=None,
                                      submitted_at="2026-10-18T00:00:00.000Z") == 1
        assert stamp_window_submitted(connection, practice_item_id=ITEM, session_id=session, since=None,
                                      submitted_at="2026-10-18T00:05:00.000Z") == 0
    _wb_submit(ctx, view["sessionId"], session)
    [row] = assists(paths.sqlite_path)
    assert row["submitted_at"] == "2026-10-18T00:00:00.000Z" and row["attempt_id"] is not None


# -- F8: the vault-open placement pass pages past what it cannot place ---------------------------


def test_f8_unplaceable_candidates_never_starve_a_placeable_one(tmp_path, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    blocked = _hinted_wrong_attempt(ctx, session, "k1")
    time.sleep(1.05)
    placeable = _hinted_wrong_attempt(ctx, session, "k2")
    since = "2000-01-01T00:00:00Z"
    assert outcome.unplaced_attempts(paths.sqlite_path, since=since) == [blocked, placeable]
    # The oldest candidate cannot be placed (its item has no map now, say).
    real_due = outcome._due

    def due(vault, repository, attempt_id):
        return (None, "no_map") if attempt_id == blocked else real_due(vault, repository, attempt_id)

    monkeypatch.setattr(outcome, "_due", due)
    monkeypatch.setattr(outcome, "RECONCILE_PAGE", 1)
    vault = load_vault(paths.root)
    registry = map_builder.BackgroundBuilds(drain_seconds=5.0)
    registry.bind(paths.sqlite_path)
    fake = OutcomeFake()
    results: list = []
    for _ in range(2):  # every open: the same oldest candidate first
        thread = outcome.reconcile_outcome_placements(vault, paths.sqlite_path, client=fake, builds=registry,
                                                      limit=1, on_done=results.append)
        assert thread is not None
        thread.join(30)
        if judgments(paths.sqlite_path, "hint_outcome"):
            break
    assert [row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")] == [placeable]
    assert fake.calls == 1
    assert [result.status for result in results][:2] == ["no_map", "placed"]


def test_f8_the_bound_counts_placements_not_candidates(tmp_path, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    first = _hinted_wrong_attempt(ctx, session, "k1")
    time.sleep(1.05)
    second = _hinted_wrong_attempt(ctx, session, "k2")
    vault = load_vault(paths.root)
    registry = map_builder.BackgroundBuilds(drain_seconds=5.0)
    registry.bind(paths.sqlite_path)
    fake = OutcomeFake()
    thread = outcome.reconcile_outcome_placements(vault, paths.sqlite_path, client=fake, builds=registry, limit=1)
    assert thread is not None
    thread.join(30)
    # One placement per pass at limit 1; the next open places the next.
    assert [row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")] == [first]
    thread = outcome.reconcile_outcome_placements(vault, paths.sqlite_path, client=fake, builds=registry, limit=1)
    assert thread is not None
    thread.join(30)
    assert sorted(row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")) == sorted([first, second])
