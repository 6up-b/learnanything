"""Adaptive hints H2a, G-H4: the grader stays blind (spec_adaptive_hints_v1 standing constraint H2).

A hinted attempt (adaptive hints shown at several levels, a stored approach
map, a discriminating question and its answer) is graded from a context
built from the item and the submitted answer only: the rendered
blind-grading prompt contains no hint text, kind, strategy, map label or
state, placement, rival, propensity or learner state, and the context has no
field that could hold them. Fakes only.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from contextlib import closing

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.attempts.blind_grading import BlindGradingContext, blind_grading_context, blind_grading_prompt
from learnloop.hints.kinds import KIND_NAMES
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.approach_map_fakes import good_map, node
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, add_hypothesis, assists, good_answer, hint_vault, \
    prefer, store_map

MARKERS = ("ZEBRAHINT", "ZEBRASTRATEGY", "ZEBRALABEL", "ZEBRASTATE", "ZEBRARIVAL", "ZEBRAQUESTION", "ZEBRAANSWER")


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_the_blind_prompt_of_a_hinted_attempt_carries_no_hint_map_placement_or_state(tmp_path):
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n')
    marked = good_map()
    marked["nodes"][1] = node("cdf", "step", "ZEBRALABEL the CDF", "$F(x) = x^2$ on [0, 1] ZEBRASTATE")
    store_map(paths, marked)
    add_hypothesis(paths.sqlite_path, "h1", "ZEBRARIVAL adds one to a CDF value")
    add_hypothesis(paths.sqlite_path, "h2", "Reads the CDF as the density")
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]

    def ask(option, answer, **params):
        ctx.hint_writer_client = WriterFake([answer])
        ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
        return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM,
                                                    "submissionId": "k1", "answerMd": WORK, **params})["result"]

    ask("next_step@L3", lambda c: {**good_answer(c), "hint_md": "ZEBRAHINT evaluate your CDF",
                                   "strategy": "ZEBRASTRATEGY"})

    def question(c):
        payload = good_answer(c)
        payload["candidates"][0]["question_md"] = "ZEBRAQUESTION what does it give at x = 0?"
        return payload

    asked = ask("discriminating@L1", question)
    _call(ctx, "practice.answer_discriminating", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                                  "questionAssistId": asked["assistId"], "answerMd": "ZEBRAANSWER"})
    ask("worked_chunk@L4", good_answer, takenLevel=4)
    result = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3},
        "submissionId": "k1"})
    rows = assists(paths.sqlite_path)
    assert len(rows) == 4 and {row["attempt_id"] for row in rows} == {result["attemptId"]}
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        answer, hints_used, primed = connection.execute(
            "SELECT learner_answer_md, hints_used, primed FROM practice_attempts WHERE id = ?",
            (result["attemptId"],)).fetchone()
    assert hints_used == 2 and primed == 1  # the attempt is hinted and primed ...
    vault = load_vault(paths.root)
    prompt = blind_grading_prompt(blind_grading_context(vault, vault.practice_items[ITEM],
                                                        attempt_id=result["attemptId"], learner_answer_md=answer))
    # ... and its grader sees none of it.
    for marker in MARKERS:
        assert marker not in prompt, marker
    for word in ("subgoal_plan", "next_step", "worked_chunk", "hints_used", "placement", "propensity",
                 "help_style", "p_success", "placement_intent", "approach_map", "waypoint"):
        assert word not in prompt, word
    # The strongest form: the prompt equals the one the same answer gets on a
    # vault where no hint was ever served (the grader's own instructions
    # happen to use plain words such as "localize").
    clean = hint_vault(tmp_path, name="clean")
    clean_vault = load_vault(clean.root)
    baseline = blind_grading_prompt(blind_grading_context(clean_vault, clean_vault.practice_items[ITEM],
                                                          attempt_id=result["attemptId"], learner_answer_md=answer))
    assert prompt == baseline
    assert set(KIND_NAMES)
    for column in ("body_md", "placement_json", "rivals_json", "map_id"):
        for row in rows:
            if row[column]:
                assert str(row[column]) not in prompt


def test_the_blind_context_has_no_field_for_hints_or_learner_state():
    fields = {field.name for field in dataclasses.fields(BlindGradingContext)}
    for word in ("hint", "map", "placement", "rival", "assist", "propensity", "help", "state", "mastery"):
        assert not any(word in name for name in fields), (word, fields)
