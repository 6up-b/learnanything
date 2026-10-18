"""Adaptive hints H2b, the Codex review's backend findings (docs/reviews/hints-h2b-codex-review.md).

F1: a hint the service showed on the answer box goes with the work into
"Work in steps": the answer box names its submission when the problem opens,
the server links its own shown rows to the problem (never a count the client
sent), and the problem's submit folds them (levels 1-3 count, 4-5 prime) and
attaches them, so going back and submitting on the answer box never counts
them twice. F4: a reply to a hint whose learner-text job never committed is
queued by the backlog sweep and when the sidecar opens the vault. F5: a
hinted attempt whose outcome placement never ran is placed when the vault
opens, through the same claim, checkpoint and fence (a checkpointed answer is
not paid again). F6: a waypoint whose goal the next hint's placement shows
reached counts as reached without more help. F7: ``--surface`` filters the
chooser's statistics and avoidance too. Fakes only.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.hints import map_builder, outcome
from learnloop.hints.outcome import place_outcome
from learnloop.hints.report import build_hints_report, item_caps
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, hint_vault, judgments, prefer, store_map
from tests.split_live_helpers import ReadyRuntime
from tests.test_hint_outcome import OutcomeFake
from tests.test_stuck_prompt import StuckFake

PARTIAL = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def _attempt(paths, attempt_id):
    [row] = _rows(paths, "SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,))
    return row


def _sidecar(tmp_path, config: str = "", *, map_: bool = True):
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n' + config)
    if map_:
        store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


@pytest.fixture
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider (the
    workbench submit has no self-grade)."""

    import learnloop.attempts.attempts as attempts_module
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _hint(ctx, session, key, option="next_step@L3", **params):
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": key,
                                                "answerMd": WORK, **params})["result"]


def _into_steps(ctx, session, key, *, carried: int = 0, hand_off: bool = True):
    payload = {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM, "stemMd": "Find P.",
               "carriedHints": carried}
    if hand_off:
        payload.update({"carriedSubmissionId": key, "carriedSessionId": session})
    view = _call(ctx, "workbench.open", payload)["session"]
    _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                       "bodyMd": WORK})
    return view


def _wb_submit(ctx, wb_session, session):
    return _call(ctx, "workbench.submit", {"sessionId": wb_session, "practiceSessionId": session})["attempt"]


# -- F1: the answer box's service hints go with the work into steps -------------------------------


def test_f1_a_service_hint_shown_on_the_answer_box_counts_on_the_workbench_submit(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    shown = _hint(ctx, session, "k1")
    assert shown["status"] == "ready" and shown["shown"] is True
    view = _into_steps(ctx, session, "k1")
    # The record line names it before Submit; the client's own count stays 0.
    assert view["carriedHints"] == 0
    assert view["record"]["hints"] == 1 and view["record"]["ownAttempt"] is False
    attempt = _attempt(paths, _wb_submit(ctx, view["sessionId"], session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (1, 0)
    assert attempt["entry_surface"] == "desktop_practice_workbench"
    [row] = assists(paths.sqlite_path)
    assert (row["attempt_id"], row["workbench_session_id"], row["submission_id"]) == (
        attempt["id"], view["sessionId"], "k1")


def test_f1_before_the_fix_the_same_flow_recorded_an_unassisted_attempt(tmp_path, grader):
    # The reproduction: without the hand-off the answer box's key is unknown
    # to the problem, and the fold under its own key finds nothing.
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    view = _into_steps(ctx, session, "k1", hand_off=False)
    attempt = _attempt(paths, _wb_submit(ctx, view["sessionId"], session)["attemptId"])
    assert attempt["hints_used"] == 0  # what the review found; the screen now always hands off


def test_f1_a_service_served_authored_hint_and_worked_help_carry_too(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path, "chooser_enabled = false\n")
    # The chooser's fallback serves the item's authored hint (no reveal row).
    authored = _hint(ctx, session, "k1")
    assert (authored["kind"], authored["level"]) == ("authored", 3)
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    worked = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                                  "answerMd": WORK, "takenLevel": 5})["result"]
    assert worked["status"] == "ready" and worked["level"] == 5
    view = _into_steps(ctx, session, "k1")
    attempt = _attempt(paths, _wb_submit(ctx, view["sessionId"], session)["attemptId"])
    # The authored hint counts one; the worked answer primes.
    assert (attempt["hints_used"], attempt["primed"]) == (1, 1)
    assert {row["attempt_id"] for row in assists(paths.sqlite_path) if row["shown"]} == {attempt["id"]}


def test_f1_the_client_count_and_the_server_rows_add_never_double(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    # The item's hint taken through the client path (the authored offer).
    _call(ctx, "practice.record_hint_reveal", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                               "authoredIndex": 0, "answerMd": WORK})
    view = _into_steps(ctx, session, "k1", carried=1)
    assert view["carriedHints"] == 1 and view["record"]["hints"] == 2
    attempt = _attempt(paths, _wb_submit(ctx, view["sessionId"], session)["attemptId"])
    assert attempt["hints_used"] == 2


def test_f1_back_on_the_answer_box_the_hint_counts_once_there(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    view = _into_steps(ctx, session, "k1")
    _call(ctx, "workbench.leave", {"sessionId": view["sessionId"]})
    # The answer box restores the client's own count (0) and submits its key.
    submitted = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": view["carriedHints"], "submissionId": "k1"})
    attempt = _attempt(paths, submitted["attemptId"])
    assert attempt["hints_used"] == 1
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == attempt["id"]


def test_f1_only_the_servers_own_unclosed_rows_are_linked(tmp_path, grader):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    # Another key, another session, an unknown key: nothing is linked.
    for key, practice_session in (("k_other", session), ("k1", "no_such_session")):
        view = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                             "stemMd": "Find P.", "carriedSubmissionId": key,
                                             "carriedSessionId": practice_session})["session"]
        assert view["record"]["hints"] == 0
    assert [row["workbench_session_id"] for row in assists(paths.sqlite_path)] == [None]
    # A row whose count an attempt closed (another submission of the item in
    # the session, after it was requested) is never linked.
    _call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                  "attemptType": "independent_attempt", "hintsUsed": 0, "submissionId": "k9"})
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] is None
    from learnloop.db.stores.help_assists import link_to_workbench

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert link_to_workbench(connection, practice_item_id=ITEM, session_id=session, submission_id="k1",
                                 workbench_session_id=view["sessionId"]) == 0


# -- F4: replies whose learner-text job never committed ----------------------------------------------


def _gap_jobs(paths):
    return _rows(paths, "SELECT source_kind, source_id FROM learner_text_gap_jobs ORDER BY created_at, rowid")


def test_f4_a_reply_whose_job_never_committed_is_queued_by_the_sweep_and_at_open(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import jobs

    paths, ctx, session = _sidecar(tmp_path, "[learner_text_gaps]\nenabled = true\n")
    first = _hint(ctx, session, "k1")
    # The enqueue fails after the reply's row committed (or the process ends).
    monkeypatch.setattr(jobs, "enqueue_hint_feedback", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("x")))
    reply = _hint(ctx, session, "k1", request="feedback", answeredAssistId=first["assistId"],
                  feedbackShortcut="too_big", feedbackText="the plus one is the part I meant")
    assert reply["status"] == "ready"
    assert _gap_jobs(paths) == []
    monkeypatch.undo()
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    assert jobs.sweep_backlog(vault, repository, dry_run=True)["hint_feedback"] == 1
    # Opening the vault reconciles it, once.
    restarted = SidecarContext()
    restarted.load(paths.root)
    assert _gap_jobs(paths) == [{"source_kind": "hint_feedback", "source_id": reply["assistId"]}]
    restarted.load(paths.root)
    assert len(_gap_jobs(paths)) == 1
    assert jobs.sweep_backlog(vault, repository)["hint_feedback"] == 0


def test_f4_nothing_is_reconciled_with_either_switch_off(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import jobs

    paths, ctx, session = _sidecar(tmp_path, "[learner_text_gaps]\nenabled = false\n")
    first = _hint(ctx, session, "k1")
    _hint(ctx, session, "k1", request="feedback", answeredAssistId=first["assistId"], feedbackText="no")
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    assert jobs.reconcile_hint_feedback(vault, repository) == 0
    vault.config.learner_text_gaps.enabled = True
    vault.config.hints.adaptive_enabled = False
    assert jobs.reconcile_hint_feedback(vault, repository) == 0
    assert _gap_jobs(paths) == []


# -- F5: interrupted outcome placement --------------------------------------------------------------


def _hinted_wrong_attempt(ctx, session, key="k1"):
    _hint(ctx, session, key)
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": PARTIAL, "submissionId": key})["attemptId"]


def test_f5_a_placement_never_scheduled_is_resumed_when_the_vault_opens(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    # Tests start no placement without an injected client: the submit's tail
    # stands for a process that ended before scheduling.
    attempt_id = _hinted_wrong_attempt(ctx, session)
    assert judgments(paths.sqlite_path, "hint_outcome") == []
    assert outcome.unplaced_attempts(paths.sqlite_path, since="2000-01-01T00:00:00Z") == [attempt_id]
    fake = OutcomeFake()
    restarted = SidecarContext()
    restarted.load(paths.root, maintenance=False)
    restarted.hint_outcome_client = fake
    restarted.reconcile_hint_work()
    assert map_builder.wait_for_background_builds(30)
    assert [row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")] == [attempt_id]
    assert fake.calls == 1
    # Placed once: a second open finds nothing to do.
    restarted.reconcile_hint_work()
    assert map_builder.wait_for_background_builds(30)
    assert fake.calls == 1 and outcome.unplaced_attempts(paths.sqlite_path, since="2000-01-01T00:00:00Z") == []


def test_f5_a_placement_interrupted_after_its_answer_was_checkpointed_is_not_paid_again(tmp_path, monkeypatch):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_wrong_attempt(ctx, session)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    # The process ends after the paid answer was checkpointed, before the
    # verdicts were written.
    original = outcome._write

    def ended(*_args, **_kwargs):
        raise KeyboardInterrupt("the process ended")

    monkeypatch.setattr(outcome, "_write", ended)
    first = OutcomeFake()
    with pytest.raises(KeyboardInterrupt):
        place_outcome(vault, repository, attempt_id, client=first)
    assert first.calls == 1 and judgments(paths.sqlite_path, "hint_outcome") == []
    monkeypatch.setattr(outcome, "_write", original)
    # The next open places it from the checkpoint: no second paid call.
    again = OutcomeFake()
    registry = map_builder.BackgroundBuilds(drain_seconds=5.0)
    registry.bind(paths.sqlite_path)
    results: list = []
    resumed = outcome.reconcile_outcome_placements(vault, paths.sqlite_path, client=again, builds=registry,
                                                   on_done=results.append)
    assert resumed is not None
    resumed.join(30)
    assert [result.status for result in results] == ["placed"]
    assert again.calls == 0
    assert [row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")] == [attempt_id]


def test_f5_a_retry_answered_from_the_receipt_schedules_the_placement(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_wrong_attempt(ctx, session)
    fake = OutcomeFake()
    ctx.hint_outcome_client = fake
    again = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": PARTIAL, "submissionId": "k1"})
    assert again["attemptId"] == attempt_id
    assert map_builder.wait_for_background_builds(30)
    assert [row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")] == [attempt_id]


def test_f5_reconciliation_keeps_the_switches(tmp_path):
    paths, ctx, session = _sidecar(tmp_path, "outcome_placement_enabled = false\n")
    _hinted_wrong_attempt(ctx, session)
    vault = load_vault(paths.root)
    assert outcome.reconcile_outcome_placements(vault, paths.sqlite_path, client=OutcomeFake()) is None
    vault.config.hints.outcome_placement_enabled = True
    # No injected client in tests: nothing starts (the suite's guard).
    assert outcome.reconcile_outcome_placements(vault, paths.sqlite_path) is None


# -- F6, F7: the report ----------------------------------------------------------------------------


def _report(paths, **kwargs):
    vault = load_vault(paths.root)
    return build_hints_report(paths.sqlite_path, item_caps=item_caps(vault.practice_items.values()), **kwargs)


def test_f6_a_goal_reached_before_the_next_hint_counts_as_reached_without_more_help(tmp_path, monkeypatch):
    import learnloop.attempts.attempts as attempts_module

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    paths, ctx, session = _sidecar(tmp_path)
    # Before any work: the goal to aim for is the CDF. The learner reaches it
    # on their own, then asks for more: the next hint is placed at the CDF.
    waypoint = _hint(ctx, session, "k1", "waypoint@L3", answerMd="")
    assert waypoint["kind"] == "waypoint"
    assert _hint(ctx, session, "k1", "approach_question@L1")["status"] == "ready"
    _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": PARTIAL, "submissionId": "k1"})
    [row] = [row for row in _report(paths)["kinds"] if row["hint_kind"] == "waypoint"]
    assert row["unaided_next_progress"]["reached_by"]["next_placement"] == 1
    goals = row["waypoint"]["goals_reached_without_more_help"]
    assert (goals["count"], goals["of"]) == (1, 1)


def test_f7_surface_filters_the_chooser_statistics_and_avoidance(tmp_path, monkeypatch):
    import learnloop.attempts.attempts as attempts_module

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "k1")
    _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": PARTIAL, "submissionId": "k1"})
    time.sleep(1.05)
    # An unassisted practice-screen answer not fully correct (avoidance's count).
    _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": "P = 1", "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": PARTIAL, "submissionId": "k2"})
    everything = _report(paths)
    assert everything["routes"]["hint_chooser"]["requests"] == 1
    assert everything["help_seeking"]["avoidance"]["unassisted_not_fully_correct"] == 1
    practice = _report(paths, surface="practice")
    assert practice["routes"]["hint_chooser"]["requests"] == 1
    assert practice["help_seeking"]["avoidance"]["unassisted_not_fully_correct"] == 1
    workbench = _report(paths, surface="workbench")
    # Every section of the selection: nothing shown, nothing chosen, no attempt.
    assert workbench["totals"]["shown"] == 0 and workbench["kinds"] == []
    assert workbench["routes"]["hint_writer"]["requests"] == 0
    assert workbench["routes"]["hint_chooser"]["requests"] == 0
    assert workbench["routes"]["hint_chooser"]["served_by"] == {}
    assert workbench["help_seeking"]["abuse"]["requests_in_a_row_on_unchanged_work"]["of"] == 0
    assert workbench["help_seeking"]["avoidance"]["unassisted_not_fully_correct"] == 0
    assert workbench["help_seeking"]["avoidance"]["of_graded_unassisted_not_fully_correct"] == 0
    assert workbench["expertise_reversal"]["by_placement_intent"] == []
    # The receipts are every surface's, and say so.
    assert workbench["routes"]["receipts_scope"] == "all_surfaces"
    assert workbench["routes"]["hint_chooser"]["receipts"]["calls"] == 1
    tutor = _report(paths, surface="tutor")
    assert tutor["help_seeking"]["avoidance"]["unassisted_not_fully_correct"] is None
    assert json.dumps(tutor)  # serializable
