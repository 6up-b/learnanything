"""Adaptive hints H2b: the report's rows (spec_adaptive_hints_v1 §6.1, §6.3).

On ``help_assists`` rows and attempts seeded through the real sidecar with
fake models: per kind and level, "doesn't connect" by shortcut, the level of
the help that followed, unaided next progress settled by the next hint's
placement and by outcome placement, the outcome placements, the chooser, and
for waypoints the goals reached without more help and the smaller steps
taken; the expertise-reversal split by placement intent and P(success) at
request time; help abuse and avoidance counts; latency and cost per route.
Read-only, no model call, no learner text; every number with its sample
size. Fakes only.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.hints.outcome import place_outcome
from learnloop.hints.report import build_hints_report, item_caps
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, hint_vault, prefer, store_map
from tests.test_hint_outcome import OutcomeFake

PARTIAL = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}
REPLY_TEXT = "the plus one is the part I meant, honestly"
#: The next hint after a reply is placed past the CDF: it had been reached.
AT_CDF = {"route_id": "r_ref", "reached_node_id": "cdf", "quote": "F(x) = x^2 on [0, 1]",
          "work_matches_a_route": True}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _hint(ctx, session, key, option, **params):
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": key,
                                                "answerMd": WORK, **params})["result"]


def _submit(ctx, session, key, grade=PARTIAL, *, answer=WORK):
    attempt = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": answer, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": grade, "submissionId": key})["attemptId"]
    # Attempts are stamped to the second, and a hint requested in the same
    # second as the item's last attempt of the session is refused as already
    # submitted (H2a's keyless fence, round 3 W1): the next one waits a second.
    time.sleep(1.05)
    return attempt


def _seeded(tmp_path, monkeypatch):
    # The fake hints overlap the key a little each; their reveals would sum
    # past auto-prime's 0.35 and prime the attempts (the existing rule), which
    # makes unaided progress "primed". The rows here measure the report, so
    # the sum is lifted for the seeding only.
    import learnloop.attempts.attempts as attempts_module

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n')
    store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    # Attempt 1: a next step aimed at the goal, a "too big a jump" reply with
    # text, a second hint; submitted not fully correct and placed at the CDF.
    first = _hint(ctx, session, "k1", "next_step@L3")
    second = _hint(ctx, session, "k1", "next_step@L3", request="feedback", answeredAssistId=first["assistId"],
                   feedbackShortcut="too_big", feedbackText=REPLY_TEXT)
    attempt_1 = _submit(ctx, session, "k1")
    # Attempt 2: a goal to aim for, then the learner's smaller step; two plain
    # presses on unchanged work (help abuse's count), submitted not fully correct.
    # (Before any work: the goal to aim for is the CDF, two steps from the givens.)
    waypoint = _hint(ctx, session, "k2", "waypoint@L3", answerMd="")
    smaller = _hint(ctx, session, "k2", "next_step@L3", request="smaller_step", answeredAssistId=waypoint["assistId"],
                    answerMd="")
    _hint(ctx, session, "k2", "approach_question@L1", answerMd="")
    attempt_2 = _submit(ctx, session, "k2")
    # Attempt 3: no help at all, not fully correct (help avoidance's count).
    attempt_3 = _submit(ctx, session, "k3")
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    for attempt in (attempt_1, attempt_2):
        assert place_outcome(vault, repository, attempt, client=OutcomeFake([AT_CDF])).status == "placed"
    return paths, {"first": first, "second": second, "waypoint": waypoint, "smaller": smaller,
                   "attempts": (attempt_1, attempt_2, attempt_3)}


def _report(paths, **kwargs):
    vault = load_vault(paths.root)
    return build_hints_report(paths.sqlite_path, item_caps=item_caps(vault.practice_items.values()), **kwargs)


def _kind(report, kind, level):
    [row] = [row for row in report["kinds"] if row["hint_kind"] == kind and row["level"] == level]
    return row


def test_the_rows_per_kind_and_level_read_replies_placements_and_what_followed(tmp_path, monkeypatch):
    paths, seeded = _seeded(tmp_path, monkeypatch)
    assert seeded["first"]["status"] == "ready" and seeded["second"]["status"] == "ready"
    report = _report(paths)
    assert report["report_version"] == "hints-report-v2"
    next_step = _kind(report, "next_step", 3)
    # Replies by shortcut: the first next step was answered "too big a jump".
    assert next_step["doesnt_connect"]["by_shortcut"]["too_big"] == 1
    assert {k: next_step["doesnt_connect"]["replied"][k] for k in ("count", "of")} == {
        "count": 1, "of": next_step["shown"]}
    # The help that followed: a level-3 hint after the first next step, a
    # level-1 question after the smaller step.
    assert next_step["more_help_level"] == {"1": 1, "3": 1}
    # Outcome placement put both final answers at the CDF: the next steps
    # aimed at the goal were not reached, the smaller step's CDF was.
    assert next_step["outcome_placement"] == {"reached": 1, "not_reached": 2, "unknown": 0, "not_placed": 0, "of": 3}
    # Unaided progress, where the grade cannot settle it: the next hint's
    # placement settles the two followed by more help, outcome placement the last.
    progress = next_step["unaided_next_progress"]
    assert progress["not_reached_by"] == {"next_placement": 2, "outcome_placement": 1}
    assert progress["reached_by"] == {"grade": 0, "next_placement": 0, "outcome_placement": 0}
    assert {k: progress["not_reached"][k] for k in ("count", "of")} == {"count": 3, "of": 3}
    assert sum(progress["unknown"].values()) == 0
    question = _kind(report, "approach_question", 1)["unaided_next_progress"]
    assert question["reached_by"]["outcome_placement"] == 1
    assert next_step["chooser"].get("decider", 0) + next_step["chooser"].get("learner_pick", 0) >= 1
    # Every share carries its sample size and interval.
    assert next_step["doesnt_connect"]["replied"]["interval"]["method"] == "wilson"


def test_a_goal_to_aim_for_reports_goals_reached_and_smaller_steps(tmp_path, monkeypatch):
    paths, seeded = _seeded(tmp_path, monkeypatch)
    assert seeded["waypoint"]["kind"] == "waypoint"
    waypoint = _kind(_report(paths), "waypoint", 3)
    assert {k: waypoint["waypoint"]["smaller_steps_taken"][k] for k in ("count", "of")} == {"count": 1, "of": 1}
    # The smaller step followed it, so it was not reached without more help.
    assert waypoint["waypoint"]["goals_reached_without_more_help"]["count"] == 0
    assert "waypoint" not in _kind(_report(paths), "next_step", 3)


def test_the_expertise_reversal_split_reads_the_state_logged_at_request(tmp_path, monkeypatch):
    paths, _seeded_rows = _seeded(tmp_path, monkeypatch)
    split = _report(paths)["expertise_reversal"]
    intents = {(row["hint_kind"], row["placement_intent"]) for row in split["by_placement_intent"]}
    assert ("next_step", "not_logged") not in intents  # H2b's rows log the state
    assert all(row["placement_intent"] in ("assumed", "learning", "maintenance", "unknown")
               for row in split["by_placement_intent"])
    for row in split["by_placement_intent"] + split["by_p_success"]:
        for column in ("unaided_next_progress", "too_big_a_jump", "doesnt_connect"):
            assert row[column]["of"] >= 0 and "interval" in row[column]
        assert set(row["later_independent_success_item"]) >= {"pass", "fail", "ungraded", "pending", "pass_rate"}
    assert split["p_success_logged"] >= 0
    assert "median" in split["basis"]


def test_help_abuse_and_avoidance_are_counts_never_gates(tmp_path, monkeypatch):
    paths, _seeded_rows = _seeded(tmp_path, monkeypatch)
    seeking = _report(paths)["help_seeking"]
    assert seeking["nothing_is_gated_on_these"] is True
    abuse = seeking["abuse"]["requests_in_a_row_on_unchanged_work"]
    # Attempt 2's smaller step and its plain press came on unchanged work; the
    # pick is a reply, so only the plain press counts.
    assert abuse["count"] == 1 and abuse["of"] >= 3
    assert seeking["abuse"]["seconds_between_them"]["n"] == 1
    avoidance = seeking["avoidance"]
    assert avoidance["unassisted_not_fully_correct"] == 1
    assert avoidance["of_graded_unassisted_not_fully_correct"] == 1


def test_latency_and_cost_per_route(tmp_path, monkeypatch):
    paths, _seeded_rows = _seeded(tmp_path, monkeypatch)
    routes = _report(paths)["routes"]
    writer, chooser = routes["hint_writer"], routes["hint_chooser"]
    assert writer["written"] >= 4 and writer["latency_ms"]["n"] == writer["written"]
    assert {"p50", "p95", "p50_interval", "p95_interval"} <= set(writer["latency_ms"])
    assert writer["receipts"]["calls"] >= writer["written"]
    assert chooser["requests"] >= 1 and chooser["latency_ms"]["n"] == chooser["requests"]
    assert chooser["receipts"]["calls"] == chooser["requests"]
    # Two placements of the same answer on the same map: the second reuses
    # the first's checkpointed answer (one paid call).
    assert routes["hint_outcome"]["receipts"]["calls"] == 1
    for route in ("hint_writer", "hint_chooser", "hint_outcome", "approach_map"):
        receipts = routes[route]["receipts"]
        assert {"input_tokens", "output_tokens", "metered_cost_usd", "seconds", "by_status"} <= set(receipts)


def test_the_report_is_read_only_and_carries_no_learner_text(tmp_path, monkeypatch):
    paths, seeded = _seeded(tmp_path, monkeypatch)
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    report = _report(paths)
    text = json.dumps(report)
    assert REPLY_TEXT not in text and WORK not in text
    for hint in ("first", "second", "waypoint"):
        assert seeded[hint]["hintMd"] not in text
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    assert report["not_yet_measured"] == ["off_policy_estimates"]


def test_filters_apply_to_the_new_sections(tmp_path, monkeypatch):
    paths, _seeded_rows = _seeded(tmp_path, monkeypatch)
    future = datetime(2100, 1, 1, tzinfo=UTC).isoformat()
    report = _report(paths, since=future)
    assert report["kinds"] == [] and report["routes"]["hint_writer"]["requests"] == 0
    assert report["help_seeking"]["avoidance"]["unassisted_not_fully_correct"] == 0
    workbench = _report(paths, surface="workbench")
    assert workbench["routes"]["hint_writer"]["requests"] == 0
