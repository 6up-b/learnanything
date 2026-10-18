"""Adaptive hints H2a: the writer's contracts and leak control (spec_adaptive_hints_v1 §4.2, §4.6; G-H5, G-H6).

A fake writer that breaks a rule is caught in code, re-asked once with the
failure named, then downgraded to a level-3 ``next_step`` from the last valid
checkpoint; a level-1-3 hint that gives the answer away (short numeric
answers included, and any leak node's state) is re-asked once, then withheld
with the spec's wording. Worked help (levels 4-5) is the learner's to take
and is not withheld. Fakes only; the chooser is argmax over a fake Decider so
each test serves the kind it names.
"""

from __future__ import annotations

import json

import pytest

from learnloop.db.repositories import Repository
from learnloop.hints import service as S
from learnloop.hints.contracts import Target, check_output, leak_flags
from learnloop.hints.kinds import WITHHELD_MESSAGE
from learnloop.hints.state import assemble_state
from learnloop.hints.writer import HintWriterOutputV1, empty_output
from learnloop.vault.loader import load_vault
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, good_answer, hint_vault, prefer, store_map

ARGMAX = '[hints]\nchoice_policy = "argmax"\n'


def _setup(tmp_path, *, config: str = "", with_map: bool = True, **item):
    paths = hint_vault(tmp_path, config=ARGMAX + config, **item)
    if with_map:
        store_map(paths)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _ask(vault, repository, option: str, answers, **overrides):
    writer = WriterFake(list(answers))
    values = {"practice_item_id": ITEM, "session_id": "s1", "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    result = S.request_hint(vault, repository, S.HintRequestV1(**values), writer_client=writer,
                            chooser_client_factory=lambda: ChooserFake(prefer(option, 0.9)), seed="c")
    return result, writer


def _with(**changes):
    """``good_answer`` for the asked kind, with ``changes`` applied."""

    def answer(context):
        payload = good_answer(context)
        for key, value in changes.items():
            if key == "placement":
                payload["placement"] = {**payload["placement"], **value}
            else:
                payload[key] = value(payload) if callable(value) else value
        return payload
    return answer


def _row(paths):
    [row] = assists(paths.sqlite_path)
    return row, json.loads(row["contract_failures_json"])


# -- leak control (G-H5) ---------------------------------------------------------------------


@pytest.mark.parametrize("leaking", [
    "So P(X ≤ 1/2) = 1/4.",                       # the short numeric answer
    "Integrate the density: F(x) = x^2 on [0, 1]. Therefore P(X ≤ 1/2) = 1/4.",  # the whole solution
    "The answer is one quarter, 1/4",
])
def test_a_leaking_hint_is_reasked_once_then_withheld(tmp_path, leaking):
    paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, "next_step@L3", [_with(hint_md=leaking), _with(hint_md=leaking)])
    assert result.status == S.WITHHELD and result.message == WITHHELD_MESSAGE and result.hint_md is None
    assert writer.calls == 2
    assert "leaks" in json.dumps(writer.contexts[1]["previous_answer_problems"])
    row, log = _row(paths)
    assert (row["shown"], row["counted_by"]) == (0, None) and json.loads(row["leak_flags_json"])
    assert log["outcome"] == "withheld"
    # A withheld hint is never deliverable.
    assert S.deliver(repository, str(result.assist_id)) is None


def test_a_leak_fixed_on_the_reask_is_served(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, "next_step@L3", [_with(hint_md="So the answer is 1/4."), good_answer])
    assert result.status == S.READY and writer.calls == 2 and "1/4" not in str(result.hint_md)


def test_no_waypoint_or_label_carries_a_leak_nodes_state(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k1", work_md=WORK)
    assert leak_flags(["Aim for P(X ≤ 1/2) = 1/4."], item=item, current=state.map, level=3)
    labels = [{"node_id": "cdf", "label": "Find the CDF", "current": False},
              {"node_id": "goal", "label": "Show it equals 1/4", "current": True}]
    result, writer = _ask(vault, repository, "subgoal_plan@L3",
                          [_with(plan_labels=labels), _with(plan_labels=labels)])
    assert result.status == S.WITHHELD and writer.calls == 2


def test_worked_help_is_not_withheld_for_showing_the_answer(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, "walkthrough@L5", [], taken_level=5)
    assert result.status == S.READY and "1/4" in str(result.hint_md) and result.evidence["primed"] is True
    assert writer.calls == 1


# -- the shared rules and the kind contracts (G-H6) ------------------------------------------


@pytest.mark.parametrize("option, broken, failure", [
    ("localize@L2", {"placement": {"quotes": []}}, "rule1_no_citation"),
    ("localize@L2", {"placement": {"quotes": ["a line the learner never wrote"]}}, "rule1_quote_not_in_work"),
    ("next_step@L3", {"placement": {"stands_quote": WORK}}, "rule2_past_first_questionable"),
    ("next_step@L3", {"placement": {"stands_quote": "", "first_questionable_quote": ""}}, "rule3_nothing_stands"),
    ("next_step@L3", {"target_node_id": "g"}, "rule6_target_off_route"),
    ("error_specific@L3", {"principle": ""}, "error_specific_no_principle"),
    ("subgoal_plan@L3", {"label_register": ""}, "subgoal_plan_no_register"),
    ("approach_question@L1", {"asks_about": ""}, "approach_question_declares_nothing"),
])
def test_a_broken_rule_is_caught_reasked_once_then_fixed(tmp_path, option, broken, failure):
    paths, vault, repository = _setup(tmp_path)
    result, writer = _ask(vault, repository, option, [_with(**broken), good_answer])
    assert result.status == S.READY and writer.calls == 2
    assert failure in writer.contexts[1]["previous_answer_problems"]["failures"]
    _row_, log = _row(paths)
    assert failure in log["rounds"][0]["failures"] and log["outcome"] == "served"


def test_a_rule_broken_twice_is_downgraded_to_a_level_3_next_step(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    broken = _with(placement={"quotes": []})
    result, writer = _ask(vault, repository, "localize@L2", [broken, broken])
    assert writer.calls == 3 and writer.contexts[2]["chosen"]["kind"] == "next_step"
    assert "downgrade" in writer.contexts[2]["chosen"]
    assert (result.status, result.kind, result.level) == (S.READY, "next_step", 3)
    row, log = _row(paths)
    # The row keeps the drawn option and records the served kind (§4.2, §6.2).
    assert json.loads(row["drawn_option_json"])["option"] == "localize@L2"
    assert (row["hint_kind"], row["level"], log["outcome"]) == ("next_step", 3, "downgraded")


def test_a_downgrade_that_fails_too_serves_nothing_written(tmp_path):
    paths, vault, repository = _setup(tmp_path, hints=[])
    broken = _with(placement={"quotes": ["never written"]})
    result, writer = _ask(vault, repository, "localize@L2", [broken, broken, broken])
    assert writer.calls == 3 and result.status == S.UNAVAILABLE and result.reason == "contract_failed"
    row, _log = _row(paths)
    assert (row["shown"], row["counted_by"]) == (0, None)


def test_a_waypoint_that_misses_the_chosen_horizon_is_caught(tmp_path):
    # Four nodes on the reference route: from "g", "about two steps ahead" is "b".
    from tests.approach_map_fakes import edge, good_map, node

    longer = good_map()
    longer["nodes"] = [node("g", "given", "Read the density", "f(x) = 2x on [0, 1]"),
                       node("a", "step", "Set up the integral", "int_0^x 2t dt", value="x^2"),
                       node("b", "step", "Find the CDF on the support", "$F(x) = x^2$ on [0, 1]", checkpoint=""),
                       node("goal", "goal", "Evaluate the CDF at the point", "P(X ≤ 1/2) = 1/4", conclusion="1/4")]
    longer["edges"] = [edge("g", "a"), edge("a", "b"), edge("b", "goal")]
    longer["routes"][0]["path"] = ["g", "a", "b", "goal"]
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths, longer)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id="s1", submission_id="k1", work_md="")
    output = HintWriterOutputV1.model_validate(empty_output(
        placement={"route_id": "r_ref", "reached_node_id": "g"}, route_id="r_ref", target_node_id="a",
        hint_md="Aim for an integral you can evaluate.", strategy="w"))
    check = check_output(output, target=Target("waypoint", 3, horizon_index=1), state=state, item=item)
    assert "rule6_horizon_mismatch" in check.failures
    right = output.model_copy(update={"target_node_id": "b"})
    assert "rule6_horizon_mismatch" not in check_output(right, target=Target("waypoint", 3, horizon_index=1),
                                                       state=state, item=item).failures


def test_a_continuation_that_reaches_the_goal_is_caught(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    reaching = _with(end_node_id="goal")
    result, writer = _ask(vault, repository, "continuation@L4", [reaching, good_answer], taken_level=4)
    assert writer.calls == 2 and "continuation_reaches_goal" in writer.contexts[1]["previous_answer_problems"][
        "failures"]
    assert result.status == S.READY and result.level == 4


def test_a_worked_chunk_must_leave_a_gap_and_explain_each_piece(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    broken = _with(gap="", pieces=[{"establishes": "x", "how": "", "why": "y"}])
    result, writer = _ask(vault, repository, "worked_chunk@L4", [broken, good_answer], taken_level=4)
    failures = writer.contexts[1]["previous_answer_problems"]["failures"]
    assert {"worked_chunk_leaves_no_gap", "worked_chunk_piece_missing_what_how_why"} <= set(failures)
    assert result.status == S.READY


def test_a_worked_parallel_never_uses_the_items_own_values_and_verifies_a_book_quote(tmp_path):
    from tests.approach_map_fakes import write_item

    paths = hint_vault(tmp_path, config=ARGMAX, family_id="fam")
    write_item(paths, "pi_cdf_2", prompt="Y has density 3y^2 on [0, 1]. Find P(Y ≤ 1/3).", family_id="fam")
    store_map(paths)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    own_values = _with(hint_md="Here, with 2x on [0, 1], F(1/2) is what you need.")
    book = _with(source_origin="book", source_quote="a passage that is not in any seeded example")
    result, writer = _ask(vault, repository, "worked_parallel@L3", [own_values, book, good_answer])
    assert "worked_parallel_uses_item_values" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert writer.calls == 3 and result.kind == "next_step"  # the re-ask's unverified book quote: downgraded


def test_a_repeated_kind_and_strategy_after_a_reply_is_caught(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    first, _ = _ask(vault, repository, "next_step@L3", [_with(strategy="evaluate-cdf")])
    S.deliver(repository, str(first.assist_id))
    same = _with(strategy="evaluate-cdf")
    result, writer = _ask(vault, repository, "next_step@L3", [same, good_answer], request="feedback",
                          answered_assist_id=first.assist_id, feedback_text="this doesn't help me")
    assert "rule5_same_kind_and_strategy" in writer.contexts[1]["previous_answer_problems"]["failures"]
    assert result.status == S.READY


def test_asking_again_on_the_same_work_calls_the_writer_again(tmp_path):
    """Each request is its own paid call: an identical second request after a
    withheld hint is not answered from the first request's checkpoint (the
    request id is part of the prompt)."""

    paths, vault, repository = _setup(tmp_path)
    leaking = _with(hint_md="So P = 1/4.")
    first, writer = _ask(vault, repository, "next_step@L3", [leaking, leaking])
    assert first.status == S.WITHHELD and writer.calls == 2
    second, writer = _ask(vault, repository, "next_step@L3", [])
    assert writer.calls == 1 and second.status == S.READY
    assert writer.contexts[0]["request_id"] == second.assist_id


def test_an_authored_hint_that_gives_the_answer_away_is_withheld_and_not_served_again(tmp_path):
    paths, vault, repository = _setup(tmp_path, config="chooser_enabled = false\n",
                                      hints=["The answer is P = 1/4.", "Evaluate the CDF at the point."])
    first, writer = _ask(vault, repository, "next_step@L3", [])
    assert (first.status, first.message) == (S.WITHHELD, WITHHELD_MESSAGE) and writer.calls == 0
    second, _writer = _ask(vault, repository, "next_step@L3", [])
    assert (second.kind, second.authored_index) == ("authored", 1)
