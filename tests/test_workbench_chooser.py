"""Reader workbench RW2b + hints H3: the ladder's suggestion, its draw and its fallback (spec_reader_workbench_v1 §5.5;
G12, G62, G63; adaptive hints G-H7, G-H8).

One Decider request over the five rungs' options (in ``DECIDER_TASKS``,
never a chat fallback), with the workbench's typed state (the check's summary
and map placement, the help style, never a step's text); the suggested rung
is drawn from the Decider's probabilities and its propensity logged. The
suggested rung serves the drawn option with that joint propensity; another
rung draws its kind from the same vector renormalized over that rung, the
conditional probability logged; a rung with one option logs 1; ``argmax``
logs 1; seeds reproduce draws. The time box, an unavailable Decider or
``hints.chooser_enabled = false`` give the Reader's progression: rung 1, then
one rung above the last offered or taken on that step, each rung with its
fixed kind (rung 3 the item's own hints first), propensity 1. Every hint
kind is of its rung; no goal or plan without a map; after a goal, the next
step toward it is offered and "a smaller step toward this goal" serves it;
the book's way and a smaller step log ``learner_pick`` with no propensity.
Fakes only.
"""

from __future__ import annotations

import json

import pytest

from learnloop.hints import chooser as C
from learnloop.hints import kinds as K
from learnloop.hints import workbench as W
from tests.hint_fakes import HINTS, ChooserFake, judgments, prefer
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar


def _setup(tmp_path, config="", *, check=True, **kwargs):
    paths, ctx, session = sidecar(tmp_path, config, **kwargs)
    wb, chains = open_problem(ctx)
    if check:
        run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    return paths, ctx, session, wb, chains


def _suggest(ctx, wb, **params):
    return run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb, **params}))


def _take(ctx, wb, level, suggestion=None, **params):
    extra = {"offeredLevel": suggestion["level"], "suggestionId": suggestion["suggestionId"]} if suggestion else {}
    return run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": level, **extra, **params}))


def _hint_rows(paths, wb):
    return [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]


# -- the suggestion -----------------------------------------------------------------------------------


def test_one_decider_request_over_every_rung_with_the_workbenchs_typed_state(tmp_path):
    chooser = ChooserFake(prefer("next_step@L3", 0.9))
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=chooser)
    suggestion = _suggest(ctx, wb)["suggestion"]
    assert len(chooser.calls) == 1
    question = chooser.calls[0]["questions"][C.KIND_QUESTION]
    levels = {int(option.split("@L")[1]) for option in question.wire()["criteria"]}
    assert levels == {1, 2, 3, 4, 5}
    state = chooser.calls[0]["state"]
    assert state["where"].startswith("the Reader workbench") and state["workbench"]["check"]["questionable"] == 1
    # Never a step's text.
    assert "F(1/2) + 1" not in json.dumps(state) and "x^2" not in json.dumps(state)
    [ledger] = judgments(paths.sqlite_path, C.LEDGER_TASK)
    rationale = json.loads(ledger["rationale"])
    assert ledger["id"] == suggestion["suggestionId"] and rationale["drawn"]["level"] == suggestion["level"]
    assert suggestion["propensity"] == pytest.approx(rationale["propensity"])
    assert suggestion["why"].endswith("LearnLoop's judgment")


def test_the_suggested_rung_serves_the_drawn_option_with_its_joint_propensity(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("error_specific@L3", 0.8)))
    suggestion = _suggest(ctx, wb)["suggestion"]
    hint = _take(ctx, wb, suggestion["level"], suggestion)
    [row] = _hint_rows(paths, wb)
    assert (row["chooser"], row["level_source"], row["offered_level"]) == ("decider", "offered", suggestion["level"])
    assert row["propensity"] == pytest.approx(suggestion["propensity"])
    assert json.loads(row["drawn_option_json"])["kind"] == suggestion["kind"] == hint["kind"] or hint["kind"] == "next_step"


def test_another_rung_draws_its_kind_conditional_on_the_level_from_the_same_vector(tmp_path):
    # No map: no goal to aim for, so the draw multiplies in no horizon.
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("localize@L2", 0.9)),
                                               map_=False, maps_enabled=False)
    suggestion = _suggest(ctx, wb)["suggestion"]
    assert suggestion["level"] == 2
    _take(ctx, wb, 3, suggestion)
    [row] = _hint_rows(paths, wb)
    probabilities = json.loads(row["probabilities_json"])[C.KIND_QUESTION]
    options = json.loads(row["options_json"])["options"]
    drawn = json.loads(row["drawn_option_json"])["option"]
    expected = probabilities[drawn] / sum(probabilities[option] for option in options)
    assert (row["chooser"], row["level_source"]) == ("decider", "learner_pick")
    assert row["propensity"] == pytest.approx(expected)
    # The seed reproduces the draw.
    rng = W._rng(f"{row['seed']}:L3")
    assert C.draw({option: probabilities[option] for option in options}, rng)[0] == drawn


def test_a_rung_with_one_option_logs_propensity_one(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    suggestion = _suggest(ctx, wb)["suggestion"]
    _take(ctx, wb, 5, suggestion)
    [row] = _hint_rows(paths, wb)
    assert (row["hint_kind"], row["propensity"], row["level_source"]) == ("walkthrough", 1.0, "learner_pick")


def test_argmax_logs_one(tmp_path):
    paths, ctx, _session = sidecar(tmp_path, chooser=ChooserFake(prefer("localize@L2", 0.6)))
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace('choice_policy = "sample"', 'choice_policy = "argmax"'))
    ctx.reload(maintenance=False)
    wb, _chains = open_problem(ctx)
    suggestion = _suggest(ctx, wb)["suggestion"]
    assert (suggestion["level"], suggestion["propensity"]) == (2, 1.0)
    _take(ctx, wb, 3, suggestion)
    assert _hint_rows(paths, wb)[0]["propensity"] == 1.0


# -- the fallback (G62, G-H8) ---------------------------------------------------------------------------


@pytest.mark.parametrize("config,chooser", [
    ("chooser_enabled = false\n", None),
    ("chooser_timeout_seconds = 0.01\n", ChooserFake(delay=0.2)),
    ("", ChooserFake(error=RuntimeError("down"))),
])
def test_without_a_judgment_the_ladder_suggests_rung_one_then_one_rung_up_per_press(tmp_path, config, chooser):
    kwargs = {"chooser": chooser} if chooser is not None else {}
    _paths, ctx, _session, wb, _chains = _setup(tmp_path, config, **kwargs)
    if chooser is None:
        ctx.hint_chooser_client = ChooserFake(error=AssertionError("asked while switched off"))
    levels = [_suggest(ctx, wb)["suggestion"] for _ in range(6)]
    assert [entry["level"] for entry in levels] == [1, 2, 3, 4, 5, 5]
    assert all(entry["chooser"] == "fallback" and entry["propensity"] == 1.0 for entry in levels)
    assert levels[0]["why"] == W.FALLBACK_WHY


def test_under_the_fallback_each_rung_has_its_fixed_kind_and_rung_three_serves_the_items_hints_first(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, "chooser_enabled = false\n")
    served = [_take(ctx, wb, level) for level in (1, 2, 3, 3, 3, 4, 5)]
    rows = _hint_rows(paths, wb)
    drawn = [json.loads(row["drawn_option_json"])["kind"] for row in rows]
    # Rung 1 is the discriminating question (rivals are open on the
    # questionable step), rung 3 the item's own hints in order, then the
    # next step; rungs 4 and 5 the continuation and the walkthrough.
    assert drawn == ["discriminating", "localize", "authored", "authored", "next_step", "continuation", "walkthrough"]
    assert [hint["hintMd"] for hint in served[2:4]] == HINTS
    assert all(row["propensity"] == 1.0 for row in rows)
    assert {row["chooser"] for row in rows} <= {"fallback", "learner_pick"}


def test_the_help_style_override_reaches_the_decider_and_changes_only_the_suggestion(tmp_path):
    chooser = ChooserFake(prefer("next_step@L3", 0.9))
    _paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=chooser)
    saved = call(ctx, "workbench.set_help_style", {"sessionId": wb, "helpStyle": "let_me_struggle"})
    assert (saved["helpStyle"], saved["storedHelpStyle"]) == ("let_me_struggle", "balanced")
    _suggest(ctx, wb)
    state = chooser.calls[-1]["state"]
    assert state["help_style"] == "let_me_struggle" and state["workbench"]["help_style_source"] == "this problem"
    # The stored preference is untouched (no config write).
    assert ctx.require_vault()[0].config.hints.help_style == "balanced"


# -- kinds, maps, waypoints and the learner's picks (G63) ---------------------------------------------


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_every_served_hint_is_a_kind_of_its_rung(tmp_path, level):
    _paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake())
    hint = _take(ctx, wb, level)
    assert hint["status"] == "ready" and level in K.KINDS[hint["kind"]].levels and hint["level"] == level


def test_no_goal_or_plan_is_offered_without_a_map(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, map_=False, maps_enabled=False,
                                               chooser=ChooserFake(prefer("waypoint@L3", 0.9)))
    _take(ctx, wb, 3)
    options = json.loads(_hint_rows(paths, wb)[0]["options_json"])
    assert "waypoint@L3" not in options["options"] and options["excluded"]["waypoint@L3"] == "no_map"
    assert "subgoal_plan@L3" not in options["options"]


def test_after_a_goal_the_next_step_toward_it_is_offered_and_a_smaller_step_serves_it(tmp_path):
    chooser = ChooserFake(prefer("waypoint@L3", 0.97), horizon={0: 0.0, 1: 0.0, 2: 0.0, 3: 1.0})
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=chooser)
    goal = _take(ctx, wb, 3)
    assert goal["kind"] == "waypoint" and goal["labels"]["horizon"] == "the goal itself"
    assert "smaller_step" in goal["replies"]
    smaller = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "request": "smaller_step",
                                                                "answeredAssistId": goal["assistId"]}))
    assert smaller["kind"] == "next_step" and smaller["level"] == 3
    rows = _hint_rows(paths, wb)
    assert (rows[-1]["chooser"], rows[-1]["propensity"]) == ("learner_pick", None)
    # Help on the step again: every level-3 option aims at the goal, the next step among them.
    _take(ctx, wb, 3)
    options = json.loads(_hint_rows(paths, wb)[-1]["options_json"])
    assert options["target_node_id"] == rows[0]["target_node_id"] and "next_step@L3" in options["options"]


def test_the_books_way_is_the_learners_pick_with_no_propensity(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    first = _take(ctx, wb, 3)
    book = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "request": "book_way",
                                                             "answeredAssistId": first["assistId"]}))
    assert book["level"] == 3
    row = _hint_rows(paths, wb)[-1]
    assert (row["chooser"], row["propensity"], row["request"]) == ("learner_pick", None, "book_way")


def test_a_reply_keeps_the_level_of_the_hint_it_answers(tmp_path):
    _paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake())
    first = _take(ctx, wb, 2)
    reply = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "request": "feedback",
                                                              "answeredAssistId": first["assistId"],
                                                              "feedbackShortcut": "too_big"}))
    assert reply.get("level") in (2, None)
