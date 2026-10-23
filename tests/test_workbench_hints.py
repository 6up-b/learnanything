"""Reader workbench RW2b + hints H3: the reconciliation contract in the workbench (spec_reader_workbench_v1 §5.2;
G7, G8, G33, G60; adaptive hints G-H5, G-H6, G-H15).

A fake writer that cites no learner step, quotes across steps, continues
from the questionable step or a step depending on it, is shown under a step
it does not quote, repeats its kind and strategy after a "doesn't connect"
reply (other than "the notation"), or with a map starts elsewhere than the
node its checkpoint reached, is caught, re-asked once, then downgraded (a
taken rung 1 or 2 is never raised). A hint at levels 1-3 that would give the
answer away is never shown. The four shortcuts have their effects; every
reply keeps the level and appends a ``hint_fit`` verdict. A hint sits under
its about-step, builds on ``continue_from``, and its label names both.
Bridging never returns the item's exercise or solution, never delays the
hint, and lands under it. Fakes only.
"""

from __future__ import annotations

import json

from tests.hint_fakes import ChooserFake, WriterFake, judgments, prefer
from tests.workbench_help_fakes import STEP_1, STEP_2, call, help_rows, open_problem, run_job, sidecar, wb_answer


def _setup(tmp_path, answers=None, config="", **kwargs):
    writer = WriterFake(list(answers or []) + [wb_answer] * 12)
    paths, ctx, session = sidecar(tmp_path, config, writer=writer, **kwargs)
    wb, chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    return paths, ctx, session, wb, chains


def _take(ctx, wb, level, **params):
    return run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": level, **params}))


def _failures(paths, wb):
    rows = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    return [round_["failures"] for round_ in json.loads(rows[-1]["contract_failures_json"])["rounds"]]


def _with(**placement):
    def answer(context):
        payload = wb_answer(context)
        payload["placement"] = {**payload["placement"], **placement}
        return payload
    return answer


# -- G7: the contract, re-asked once, then downgraded ---------------------------------------------


def test_a_hint_citing_no_step_is_re_asked_then_downgraded(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, [_with(quotes=[]), _with(quotes=[])])
    hint = _take(ctx, wb, 3)
    failures = _failures(paths, wb)
    assert "wb_rule1_no_step_cited" in failures[0] and "wb_rule1_no_step_cited" in failures[1]
    assert hint["status"] == "ready" and hint["kind"] == "next_step" and hint["level"] == 3


def test_a_quote_spanning_two_steps_is_not_the_learners(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, [_with(quotes=[f"{STEP_1} {STEP_2}"])])
    _take(ctx, wb, 3)
    assert "wb_rule1_quote_not_in_one_step" in _failures(paths, wb)[0]


def test_continuing_from_the_questionable_step_is_caught(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, [_with(stands_quote=STEP_2, first_questionable_quote="")])
    _take(ctx, wb, 3)
    assert "wb_rule2_checkpoint_not_standing" in _failures(paths, wb)[0]


def test_a_hint_that_does_not_quote_its_about_step_is_caught(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, [_with(quotes=[STEP_1], first_questionable_quote="")])
    _take(ctx, wb, 3)
    assert "wb_rule3_about_step_not_quoted" in _failures(paths, wb)[0]


def test_with_a_map_a_hint_must_start_from_the_node_its_checkpoint_reached(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, [_with(reached_node_id="g")],
                                               chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    _take(ctx, wb, 3)
    assert "wb_rule7_not_from_continue_from" in _failures(paths, wb)[0]


def test_a_failing_taken_rung_two_is_never_raised_to_a_level_three_hint(tmp_path):
    bad = _with(quotes=[])
    paths, ctx, _session, wb, _chains = _setup(tmp_path, [bad, bad, bad])
    hint = _take(ctx, wb, 2)
    assert hint["status"] == "unavailable" and hint["reason"] == "contract_failed"
    assert all(row["shown"] == 0 for row in help_rows(paths, wb) if row["assist_kind"] == "hint")


# -- G8: leak control --------------------------------------------------------------------------------


def test_a_level_three_hint_that_gives_the_answer_away_is_never_shown(tmp_path):
    def leaking(context):
        payload = wb_answer(context)
        payload["hint_md"] = "So P(X <= 1/2) = 1/4."
        return payload

    paths, ctx, _session, wb, _chains = _setup(tmp_path, [leaking, leaking])
    hint = _take(ctx, wb, 3)
    assert hint["status"] == "withheld" and "1/4" not in json.dumps(hint)
    assert all(row["shown"] == 0 for row in help_rows(paths, wb) if row["assist_kind"] == "hint")


# -- G60: where a hint sits and what it builds on --------------------------------------------------


def test_a_hint_sits_under_its_about_step_builds_on_what_stands_and_says_both(tmp_path):
    paths, ctx, _session, wb, chains = _setup(tmp_path)
    hint = _take(ctx, wb, 3)
    assert hint["steps"]["aboutStepId"] == chains[1] and hint["steps"]["continueFromStepId"] == chains[0]
    assert hint["stepLine"] == "on your step 2 · continues from step 1"
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert (row["about_step_id"], row["continue_from_step_id"], row["first_questionable_step_id"]) == (
        chains[1], chains[0], chains[1])
    snapshot = json.loads(row["step_snapshot_json"])
    assert [entry["chain_id"] for entry in snapshot] == chains and all(entry["hash"] for entry in snapshot)
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert [view["aboutStepId"] for view in state["hints"]] == [chains[1]]


# -- G33: "doesn't connect" ---------------------------------------------------------------------------


def _reply(ctx, wb, hint, shortcut=None, text="", step=None):
    return run_job(ctx, call(ctx, "workbench.request_help", {
        "sessionId": wb, "request": "feedback", "answeredAssistId": hint["assistId"],
        **({"feedbackShortcut": shortcut} if shortcut else {}), **({"feedbackText": text} if text else {}),
        **({"feedbackStepId": step} if step else {})}))


def test_not_where_im_stuck_moves_the_hint_to_the_picked_step_and_keeps_its_level(tmp_path):
    paths, ctx, _session, wb, chains = _setup(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    first = _take(ctx, wb, 3)
    moved = _reply(ctx, wb, first, "not_where_stuck", step=chains[0])
    assert moved["status"] == "ready" and moved["level"] == 3
    assert moved["steps"]["aboutStepId"] == chains[0]
    rows = [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"]
    assert (rows[-1]["about_step_id"], rows[-1]["feedback_step_id"], rows[-1]["feedback_shortcut"]) == (
        chains[0], chains[0], "not_where_stuck")
    # One learner_card verdict "different" on hint_fit, its subject the answered hint.
    [fit] = judgments(paths.sqlite_path, "hint_fit")
    assert (fit["judge"], fit["verdict"], fit["left_id"]) == ("learner_card", "different", first["assistId"])


def test_a_reply_changes_kind_or_strategy_except_after_the_notation(tmp_path):
    def same_strategy(context):
        payload = wb_answer(context)
        payload["strategy"] = "fixed"
        return payload

    paths, ctx, _session, wb, _chains = _setup(tmp_path, [same_strategy, same_strategy, same_strategy],
                                               chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    first = _take(ctx, wb, 3)
    _reply(ctx, wb, first, "learner_route")
    assert any("rule5_same_kind_and_strategy" in failures for failures in _failures(paths, wb))


def test_the_notation_keeps_the_kind_and_quotes_the_learners_symbols(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    first = _take(ctx, wb, 3)
    again = _reply(ctx, wb, first, "notation", text="I write F for the CDF")
    assert again["status"] == "ready" and again["kind"] == first["kind"] and again["level"] == 3
    context = ctx.hint_writer_client.contexts[-1]
    assert context["request"]["reply_shortcut"] == "notation" and context["request"]["reply_text"] == "I write F for the CDF"


def test_a_different_approach_stays_on_the_learners_route(tmp_path):
    def other_route(context):
        payload = wb_answer(context)
        payload["placement"] = {**payload["placement"], "route_id": "r_ref", "work_valid_so_far": True}
        payload["route_id"] = "r_other"
        return payload

    paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    first = _take(ctx, wb, 3)
    ctx.hint_writer_client.answers[:0] = [other_route, other_route]
    _reply(ctx, wb, first, "learner_route")
    failures = _failures(paths, wb)
    assert any("rule4_left_learner_route" in round_ or "rule6_unknown_route" in round_ for round_ in failures)


def test_a_reply_text_reaches_the_next_hint_at_once(tmp_path):
    _paths, ctx, _session, wb, _chains = _setup(tmp_path, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    first = _take(ctx, wb, 3)
    _reply(ctx, wb, first, "too_big", text="I don't see where the +1 comes from")
    assert ctx.hint_writer_client.contexts[-1]["request"]["reply_text"] == "I don't see where the +1 comes from"


def test_no_hint_is_shown_unless_the_learner_asked_or_replied(tmp_path):
    paths, ctx, _session, wb, _chains = _setup(tmp_path)
    # A check and a suggestion write no hint.
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    assert [row for row in help_rows(paths, wb) if row["assist_kind"] == "hint"] == []


# -- bridging ---------------------------------------------------------------------------------------


class BridgeFake:
    def __init__(self, spans):
        self.spans = spans
        self.calls = []

    def __call__(self, vault, repository, *, context, question_md, learning_object_ids, item):
        self.calls.append({"context": context, "question": question_md, "item": item.id})
        return self.spans, {"basis": "retrieved_verified"}


def test_a_hint_in_the_reader_gets_a_bridge_to_the_book_after_it_is_shown(tmp_path):
    paths, ctx, _session = sidecar(tmp_path, writer=WriterFake([wb_answer] * 6))
    fake = BridgeFake([{"span_id": "s9", "extraction_id": "ext", "label": "Book · §5.3", "text": "boundary step"}])
    ctx.workbench_bridge_provider = fake
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    # The hint landed first; the bridge is its own job.
    assert hint["status"] == "ready" and hint["bridgeJobId"]
    bridge = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]
    assert bridge["status"] == "ready" and bridge["shown"] is True and bridge["line"].startswith("§ compare with the book")
    # Through T6's item-bound practice context, never counted.
    assert fake.calls[0]["context"] == "practice"
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    assert (row["counted_by"], row["shown"]) == (None, 1)
    assert call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]["hints"] == 2  # book + hint
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert state["hints"][0]["bridge"]["spanId"] == "s9"


def test_no_bridge_off_the_reader_or_with_the_switch_off(tmp_path):
    _paths, ctx, _session = sidecar(tmp_path, writer=WriterFake([wb_answer] * 6))
    ctx.workbench_bridge_provider = BridgeFake([{"span_id": "s9", "extraction_id": "ext", "label": "x", "text": "y"}])
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))["bridgeJobId"] is None
    _paths2, ctx2, _session2 = sidecar(tmp_path / "off", "[workbench]\nbridge_enabled = false\n",
                                       writer=WriterFake([wb_answer] * 6))
    ctx2.workbench_bridge_provider = BridgeFake([{"span_id": "s9", "extraction_id": "ext", "label": "x", "text": "y"}])
    wb2, _chains2 = open_problem(ctx2, origin="reader", entry="work_through")
    assert run_job(ctx2, call(ctx2, "workbench.request_help", {"sessionId": wb2, "takenLevel": 3}))["bridgeJobId"] is None
