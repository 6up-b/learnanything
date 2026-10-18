"""Adaptive hints H2a: replies and picks (spec_adaptive_hints_v1 §4.2, §4.5, §5; G-H15).

A "doesn't connect" reply reaches the next request at once, appends a
``learner_card`` verdict ``different`` on ``hint_fit`` (its subject the
answered hint's row) and keeps the answered hint's level; its shortcut and
text ride on the next hint's row (``request = 'feedback'``). Each shortcut's
meaning holds; only ``book_way`` places a hint on the reference route while
the learner's route is valid; ``smaller_step`` serves ``next_step`` toward
the waypoint's target at the same level; after a waypoint, "More"'s level-3
options aim at its target. The learner's picks are ``learner_pick`` with no
propensity. Fakes only.
"""

from __future__ import annotations

import json

import pytest

from learnloop.db.repositories import Repository
from learnloop.hints import service as S
from learnloop.hints.contracts import Target, check_output
from learnloop.hints.state import assemble_state
from learnloop.hints.writer import HintWriterOutputV1, empty_output
from learnloop.vault.loader import load_vault
from tests.approach_map_fakes import edge, good_map, node
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, good_answer, hint_vault, judgments, \
    prefer, store_map

ARGMAX = '[hints]\nchoice_policy = "argmax"\n'


def _two_routes() -> dict:
    """The reference route and a learner (complement) route to the goal."""

    payload = good_map()
    payload["nodes"].append(node("comp", "step", "Use the complement", "P(X > 1/2) = 3/4"))
    payload["edges"] += [edge("g", "comp"), edge("comp", "goal")]
    payload["routes"].append({"id": "r_comp", "name": "Complement route", "path": ["g", "comp", "goal"],
                              "origin": "model", "learner_attempt_ids": []})
    return payload


def _setup(tmp_path, *, config: str = "", map_payload: dict | None = None):
    paths = hint_vault(tmp_path, config=ARGMAX + config)
    store_map(paths, map_payload)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _ask(vault, repository, option: str, answers=(), **overrides):
    writer = WriterFake(list(answers))
    values = {"practice_item_id": ITEM, "session_id": "s1", "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    chooser = ChooserFake(prefer(option, 0.9))
    result = S.request_hint(vault, repository, S.HintRequestV1(**values), writer_client=writer,
                            chooser_client_factory=lambda: chooser, seed="r")
    if result.status == S.READY:
        S.deliver(repository, str(result.assist_id))
    return result, writer, chooser


def _waypoint(context):
    payload = good_answer(context)
    payload["placement"]["reached_node_id"] = "g"
    payload["target_node_id"] = "goal" if context["chosen"].get("horizon") == "the goal itself" else "cdf"
    return payload


def test_a_reply_is_a_hint_fit_verdict_and_rides_on_the_next_hints_row(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "localize@L2")
    second, writer, _c = _ask(vault, repository, "localize@L2", request="feedback",
                              answered_assist_id=first.assist_id, feedback_shortcut="not_where_stuck",
                              feedback_text="I meant the first line", feedback_selection="F(x) = x^2 on [0, 1]",
                              answers=[lambda c: {**good_answer(c), "placement": {
                                  **good_answer(c)["placement"], "first_questionable_quote": "F(x) = x^2 on [0, 1]",
                                  "stands_quote": ""}}])
    [fit] = judgments(paths.sqlite_path, "hint_fit")
    assert (fit["judge"], fit["verdict"], fit["left_kind"], fit["left_id"]) == (
        "learner_card", "different", "help_assist", first.assist_id)
    assert json.loads(fit["rationale"])["shortcut"] == "not_where_stuck"
    # The reply keeps the answered hint's level; its text reaches the writer.
    assert second.level == first.level == 2
    assert writer.contexts[0]["request"]["reply_text"] == "I meant the first line"
    assert writer.contexts[0]["request"]["part_of_work_meant"] == "F(x) = x^2 on [0, 1]"
    rows = assists(paths.sqlite_path)
    assert (rows[1]["request"], rows[1]["feedback_shortcut"], rows[1]["feedback_text"]) == (
        "feedback", "not_where_stuck", "I meant the first line")
    assert rows[0]["request"] == "more" and rows[0]["feedback_text"] is None


def test_not_where_stuck_never_repeats_the_earlier_localization(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "localize@L2")
    second, writer, _c = _ask(vault, repository, "localize@L2", request="feedback",
                              answered_assist_id=first.assist_id, feedback_shortcut="not_where_stuck",
                              answers=[good_answer, lambda c: {**good_answer(c), "strategy": "other", "placement": {
                                  **good_answer(c)["placement"], "first_questionable_quote": "F(x) = x^2 on [0, 1]",
                                  "stands_quote": ""}}])
    assert "rule5_repeated_localization" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert second.status == S.READY


def test_notation_keeps_the_kind_and_quotes_the_learners_symbols(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "next_step@L3")
    second, writer, chooser = _ask(vault, repository, "localize@L2", request="feedback",
                                   answered_assist_id=first.assist_id, feedback_shortcut="notation",
                                   answers=[lambda c: {**good_answer(c), "placement": {
                                       **good_answer(c)["placement"], "quotes": []}},
                                       lambda c: {**good_answer(c), "strategy": "next_step-0"}])
    assert chooser.calls == []  # one option left: the answered kind at its level
    assert (second.kind, second.level) == ("next_step", 3)
    assert "rule5_notation_no_symbols" in writer.contexts[1]["previous_answer_problems"]["failures"]
    # The same kind and strategy are allowed after "the notation" (exempt from rule 5).
    rows = assists(paths.sqlite_path)
    assert rows[1]["strategy"] == rows[0]["strategy"] == "next_step-0" and second.status == S.READY


def test_too_big_after_a_waypoint_gives_a_shorter_step_toward_the_same_target(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "waypoint@L3", answers=[_waypoint])
    assert first.kind == "waypoint"
    target = assists(paths.sqlite_path)[0]["target_node_id"]
    second, writer, chooser = _ask(vault, repository, "waypoint@L3", request="feedback",
                                   answered_assist_id=first.assist_id, feedback_shortcut="too_big",
                                   answers=[lambda c: {**_waypoint(c), "target_node_id": c["chosen"].get(
                                       "target_node_id") or "cdf"}])
    options = json.loads(assists(paths.sqlite_path)[1]["options_json"])
    assert options["target_node_id"] == target and set(options["options"]) <= {"waypoint@L3", "next_step@L3"}
    assert (second.kind, second.level) == ("next_step", 3)
    assert writer.contexts[0]["chosen"]["target_node_id"] == target


def test_learner_route_keeps_the_learners_route_and_never_targets_the_reference(tmp_path):
    paths, vault, repository = _setup(tmp_path, map_payload=_two_routes())
    item = vault.practice_items[ITEM]
    work = "P(X > 1/2) = 3/4 by the complement"
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k9", work_md=work)
    output = HintWriterOutputV1.model_validate(empty_output(
        placement={"route_id": "r_comp", "reached_node_id": "comp", "stands_quote": work, "quotes": [work]},
        route_id="r_ref", target_node_id="goal", hint_md="Now evaluate the CDF at the point.", strategy="s"))
    target = Target("next_step", 3, request="feedback", shortcut="learner_route")
    assert "rule4_left_learner_route" in check_output(output, target=target, state=state, item=item).failures
    kept = output.model_copy(update={"route_id": "r_comp"})
    assert "rule4_left_learner_route" not in check_output(kept, target=target, state=state, item=item).failures
    # Without a reply too: a valid learner route is kept unless the learner asks for the book's way.
    assert "rule4_left_learner_route" in check_output(output, target=Target("next_step", 3), state=state,
                                                      item=item).failures
    assert "rule4_not_reference_route" not in check_output(
        output, target=Target("next_step", 3, reference_route=True, request="book_way"), state=state,
        item=item).failures


def test_book_way_places_the_next_hint_on_the_reference_route_as_the_learners_pick(tmp_path):
    paths, vault, repository = _setup(tmp_path, map_payload=_two_routes())
    first, _w, _c = _ask(vault, repository, "next_step@L3")
    second, writer, chooser = _ask(vault, repository, "next_step@L3", request="book_way",
                                   answered_assist_id=first.assist_id)
    assert chooser.calls == [] and (second.kind, second.level) == ("next_step", 3)
    assert "reference route" in writer.contexts[0]["chosen"]["route"]
    row = assists(paths.sqlite_path)[1]
    assert (row["chooser"], row["propensity"], row["request"]) == ("learner_pick", None, "book_way")


def test_smaller_step_serves_the_next_step_toward_the_waypoints_target(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "waypoint@L3", answers=[_waypoint])
    target = assists(paths.sqlite_path)[0]["target_node_id"]
    second, writer, chooser = _ask(vault, repository, "localize@L2", request="smaller_step",
                                   answered_assist_id=first.assist_id,
                                   answers=[lambda c: {**good_answer(c), "target_node_id": target,
                                                       "placement": {**good_answer(c)["placement"],
                                                                     "reached_node_id": "g"}}])
    assert chooser.calls == [] and (second.kind, second.level) == ("next_step", 3)
    row = assists(paths.sqlite_path)[1]
    assert (row["chooser"], row["propensity"], row["target_node_id"]) == ("learner_pick", None, target)
    assert writer.contexts[0]["chosen"]["target_node_id"] == target


def test_a_smaller_step_answers_only_a_waypoint(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "next_step@L3")
    with pytest.raises(S.HintRequestError):
        _ask(vault, repository, "next_step@L3", request="smaller_step", answered_assist_id=first.assist_id)


def test_after_a_waypoint_more_aims_every_level_3_option_at_its_target(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "waypoint@L3", answers=[_waypoint])
    target = assists(paths.sqlite_path)[0]["target_node_id"]
    _second, writer, _c = _ask(vault, repository, "next_step@L3", answers=[
        lambda c: {**good_answer(c), "target_node_id": "goal" if target != "goal" else "cdf"},
        lambda c: {**good_answer(c), "target_node_id": target, "placement": {
            **good_answer(c)["placement"], "reached_node_id": "g" if target == "cdf" else "cdf"}}])
    options = json.loads(assists(paths.sqlite_path)[1]["options_json"])
    assert options["target_node_id"] == target and "next_step@L3" in options["options"]
    assert "rule6_not_the_waypoint_target" in writer.contexts[1]["previous_answer_problems"]["failures"]


def test_a_reply_or_pick_names_a_shown_hint_of_this_attempt(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    with pytest.raises(S.HintRequestError):
        _ask(vault, repository, "next_step@L3", request="feedback", answered_assist_id="ha_nope")
    first, _w, _c = _ask(vault, repository, "next_step@L3")
    with pytest.raises(S.HintRequestError):  # another submission's hint
        _ask(vault, repository, "next_step@L3", request="feedback", answered_assist_id=first.assist_id,
             submission_id="k2")
    with pytest.raises(S.HintRequestError):  # a shortcut without a reply
        _ask(vault, repository, "next_step@L3", feedback_shortcut="too_big")


def test_worked_help_picks_fix_the_level_and_the_reply_keeps_it(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _w, _c = _ask(vault, repository, "worked_chunk@L4", taken_level=4)
    assert first.level == 4 and first.labels["worked_help"] == "worked help ◌"
    second, _w, _c = _ask(vault, repository, "worked_chunk@L4", request="feedback",
                          answered_assist_id=first.assist_id, feedback_shortcut="too_big")
    assert second.level == 4
    rows = assists(paths.sqlite_path)
    assert [row["level_source"] for row in rows] == ["learner_pick", "learner_pick"]
