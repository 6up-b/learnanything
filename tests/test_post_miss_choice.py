"""The post-miss mixed choice (``ObjectiveRestraintGate._mixed``) over a grid of its inputs, pinned case by case.

Every shape of support the choice is called with (the restraint's two arms; the restraint with a lesson, with and
without room to wait; FG1's three arms; FG1 with a lesson, with and without room), every readiness of the two models
and each answer they can give (answered, invalid, of the wrong type, failed, timed out, not asked), the numeric
policy's answer (its first or last arm, an arm outside the support, timed out, failed), the failure rule both ways,
two weights and three seeds (two pinned, one derived from the boundary key and the decision id). The numeric policy,
the weight and the decision id are fixed per case; the rest is the real chooser: the mix, the draw, the trace, the
record and the why. Each case's whole outcome (served arm, propensity, record, why, and the numeric policy's call) is
hashed, and ``tests/goldens/post_miss_choice.json`` holds the hashes the predecessor's code gave.

Regenerate only for a deliberate change to what the choice serves or records:
``POST_MISS_CHOICE_WRITE_GOLDEN=1 pytest tests/test_post_miss_choice.py``, the reason in the commit.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import itertools
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan.objective_job import NumericPolicy
from learnloop.daily_plan.router_chooser import CONTINUE_CURRENT, INSERT_NOW, NO_INTERVENTION, _Card
from learnloop.daily_plan.router_runtime import ANSWERED, DECIDER, FAILED, INVALID, LLM, TIMEOUT, ComponentResult
from learnloop.daily_plan.types import BlockCandidate
from learnloop.router import requests as rq

from tests.helpers import NOW
from tests.probe_router_authority_helpers import TAG

GOLDEN = Path(__file__).parent / "goldens" / "post_miss_choice.json"
WRITE = os.environ.get("POST_MISS_CHOICE_WRITE_GOLDEN") == "1"
LESSON = "lesson_offer:lo_b"
CARD_JSON = {"recent_work": [{"attempt_id": "att_card_1", "topic": "Topic A", "at": "2026-11-01", "result": "missed"}]}
#: Two pinned seeds (their uniforms fall in different components of the draw) and None: the runtime pins none, so the
#: chooser derives the seed from the boundary key and the decision id.
SEEDS = ("grid-seed-a", "grid-seed-b", None)


def _candidate(candidate_id, lane, lo, items, minutes, **kwargs):
    return BlockCandidate(candidate_id=candidate_id, lane=lane, action="practice", subtype=kwargs.pop("subtype", None),
                          learning_object_ids=(lo,), item_ids=items, reading=None, est_minutes=minutes,
                          planner_value=0.5, reason=f"{lane} on {lo}", **kwargs)


INSERT = _candidate(INSERT_NOW, "repair", "lo_a", ("pi_followup",), 2.0,
                    annotations={"reason_code": "repair_followup", "topic": "Topic A"})
CONT = _candidate(CONTINUE_CURRENT, "maintain", "lo_c", ("pi_c1", "pi_c2"), 6.0,
                  annotations={"reason_code": "review", "topic": "Topic C"})
PROBE = _candidate(INSERT_NOW, "repair", "lo_a", ("followup:fw_grid",), 2.5)
REST = _candidate(NO_INTERVENTION, "maintain", "lo_c", ("pi_c1", "pi_c2"), 6.0)
OFFER = _candidate(LESSON, "new", "lo_b", (), 8.0, subtype="lesson_offer",
                   annotations={"reason_code": "lesson_offer", "topic": "Topic B",
                                "lesson_offer": {"learning_object_id": "lo_b", "version": "grid", "reason": "gap"}})


def _shapes() -> dict[str, dict[str, Any]]:
    """Each caller's arguments to ``_mixed``, as the caller builds them (``decide``, ``_decide_with_lesson``,
    ``decide_followup``)."""

    probe = replace(PROBE, annotations={OI.FOLLOWUP_PROBE_NOTE: True})
    return {
        "restraint": dict(candidates=[INSERT, CONT]),
        "restraint_lesson": dict(
            candidates=[INSERT, CONT], valued={INSERT_NOW: INSERT, CONTINUE_CURRENT: CONT, LESSON: OFFER},
            support=[INSERT_NOW, CONTINUE_CURRENT, LESSON],
            sequences={INSERT_NOW: (INSERT, CONT), CONTINUE_CURRENT: (CONT, INSERT),
                       OI.OFFER_DECLINED_STEPS: (CONT, INSERT)},
            llm_schema=rq.LLM_POLICY_SCHEMA),
        "restraint_lesson_no_room": dict(
            candidates=[INSERT, CONT], valued={INSERT_NOW: INSERT, CONTINUE_CURRENT: CONT, LESSON: OFFER},
            support=[INSERT_NOW, LESSON],
            sequences={INSERT_NOW: (INSERT, CONT), CONTINUE_CURRENT: (CONT, INSERT),
                       OI.OFFER_DECLINED_STEPS: (CONT, INSERT)},
            llm_schema=rq.LLM_POLICY_SCHEMA),
        "followup": dict(
            candidates=[INSERT, CONT], valued={INSERT_NOW: PROBE, CONTINUE_CURRENT: CONT, NO_INTERVENTION: REST},
            support=[INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION],
            sequences={INSERT_NOW: (PROBE, CONT), CONTINUE_CURRENT: (CONT, PROBE), NO_INTERVENTION: (REST,)},
            llm_schema=rq.LLM_POLICY_SCHEMA),
        "followup_lesson": dict(
            candidates=[INSERT, CONT],
            valued={INSERT_NOW: probe, LESSON: OFFER, CONTINUE_CURRENT: CONT, NO_INTERVENTION: REST},
            support=[INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION, LESSON],
            sequences={INSERT_NOW: (probe, CONT), CONTINUE_CURRENT: (CONT, probe), NO_INTERVENTION: (REST,),
                       OI.OFFER_DECLINED_STEPS: (CONT, probe)},
            llm_schema=rq.LLM_POLICY_SCHEMA),
        "followup_lesson_no_room": dict(
            candidates=[INSERT, CONT], valued={INSERT_NOW: probe, LESSON: OFFER},
            support=[INSERT_NOW, LESSON],
            sequences={INSERT_NOW: (probe, CONT), OI.OFFER_DECLINED_STEPS: (CONT, probe)},
            llm_schema=rq.LLM_POLICY_SCHEMA),
    }


def _llm_answers(support, choice_schema: bool) -> dict[str, ComponentResult]:
    """The LLM policy's answers a case can hold, by name."""

    def result(status, **kwargs):
        return ComponentResult(name=LLM, status=status, model="fake-router-llm", latency_ms=40, cost_usd=0.002,
                               **kwargs)

    if not choice_schema:
        return {
            "yes_0.3": result(ANSWERED, p_yes=0.3, rationale="Finish this first."),
            "yes_1.0": result(ANSWERED, p_yes=1.0, rationale="Now."),
            "yes_0.0": result(ANSWERED, p_yes=0.0, rationale="Later."),
            "no_p": result(ANSWERED, p_yes=None, rationale=None),
            "failed": result(FAILED, error="boom", rationale="stale words"),
            "timeout": result(TIMEOUT, error="late"),
        }
    weights = [0.6, *([0.4 / (len(support) - 1)] * (len(support) - 1))]
    tilted = dict(zip(reversed(support), weights, strict=True))

    def parsed(distribution, rationale, evidence):
        return rq.ParsedPolicy(distribution=distribution, forecasts={}, reference={}, rationale=rationale,
                               evidence_ids=evidence)

    return {
        "shown": result(ANSWERED, parsed=parsed(tilted, "You missed this recently.", ("att_card_1",))),
        "unknown_evidence": result(ANSWERED, parsed=parsed(tilted, "You missed this recently.", ("att_elsewhere",))),
        "no_rationale": result(ANSWERED, parsed=parsed(tilted, None, ())),
        "missing_arm": result(ANSWERED, parsed=parsed({support[0]: 1.0}, "Only this.", ())),
        "zero_mass": result(ANSWERED, parsed=parsed({**tilted, support[0]: 0.0}, "Not that one.", ())),
        "failed_with_parse": result(FAILED, parsed=parsed(tilted, "Late words.", ("att_card_1",)), error="late"),
        "wrong_type": result(ANSWERED, parsed=rq.ParsedChoice(distribution=tilted, rationale="Choice.")),
        "invalid": result(INVALID, error="unparsable"),
        "timeout": result(TIMEOUT, error="late"),
    }


DECIDERS = {
    "answered": ComponentResult(name=DECIDER, status=ANSWERED, p_yes=0.6, model="fake-decider", latency_ms=20,
                                cost_usd=0.0004),
    "failed": ComponentResult(name=DECIDER, status=FAILED, error="down", model="fake-decider"),
}


def _models(support, choice_schema):
    """(label, ready, results) for every readiness and every answer the ready models can give."""

    llm = _llm_answers(support, choice_schema)
    yield "none", (), {}
    for name, decider in DECIDERS.items():
        yield f"decider:{name}", (DECIDER,), {DECIDER: decider}
    for name, answer in llm.items():
        yield f"llm:{name}", (LLM,), {LLM: answer}
    for (dname, decider), (lname, answer) in itertools.product(DECIDERS.items(), llm.items()):
        yield f"both:{dname}:{lname}", (DECIDER, LLM), {DECIDER: decider, LLM: answer}


def _numerics(support):
    return {
        "first": NumericPolicy(status=ANSWERED, choice=support[0], latency_ms=5),
        "last": NumericPolicy(status=ANSWERED, choice=support[-1], latency_ms=5),
        "outside": NumericPolicy(status=ANSWERED, choice="elsewhere", latency_ms=5),
        "timeout": NumericPolicy(status=TIMEOUT, error="deadline"),
        "failed": NumericPolicy(status=FAILED, error="boom"),
    }


def grid():
    for shape, arguments in _shapes().items():
        support = list(arguments.get("support", (INSERT_NOW, CONTINUE_CURRENT)))
        choice_schema = arguments.get("llm_schema") == rq.LLM_POLICY_SCHEMA
        for (models, ready, results), (numeric_name, numeric), to_other, w, seed in itertools.product(
                list(_models(support, choice_schema)), _numerics(support).items(), (True, False), (0.35, 1.0), SEEDS):
            case = f"{shape}|{models}|numeric:{numeric_name}|other:{int(to_other)}|w:{w}|seed:{seed}"
            yield case, SimpleNamespace(shape=shape, arguments=arguments, ready=ready, results=results,
                                        numeric=numeric, to_other=to_other, w=w, seed=seed)


class _Entry:
    complete = True

    def __init__(self, key, results, card):
        self.key, self._results, self.material = key, results, {"card": card}

    def results(self):
        return dict(self._results)


class _Runtime:
    def __init__(self, entry, seed):
        self._entry = entry
        self.seed = (lambda _key, _decision_id: seed) if seed is not None else None

    def lookup(self, _scope, _key):
        return self._entry

    def clock(self):
        return 1000.0

    def start(self, *_a, **_k):  # pragma: no cover - every case hands the chooser its entry
        raise AssertionError("the grid's entry is always found")


def _card():
    return _Card({"card": "grid"}, "card-hash-grid", "card-v-grid", "The learner missed a question.", CARD_JSON)


def run_case(case: str, spec, monkeypatch) -> dict[str, Any]:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = TAG
    config.router_objective.enabled = True
    config.router_objective.failure_share_to_other_policy = spec.to_other
    vault = SimpleNamespace(config=config, learning_objects={
        lo: SimpleNamespace(title=f"Topic {lo[-1].upper()}") for lo in ("lo_a", "lo_b", "lo_c")})
    calls: list[dict[str, Any]] = []

    def numeric(_vault, _repository, *, state, support, candidates, now_iso, seed, deadline, clock, sequences):
        calls.append({"support": list(support), "candidates": {ref: c.candidate_id + ":" + ",".join(c.item_ids)
                                                                for ref, c in candidates.items()},
                      "sequences": {ref: [c.candidate_id for c in steps] for ref, steps in sequences.items()},
                      "now_iso": now_iso, "seed": seed, "deadline": deadline})
        return spec.numeric

    monkeypatch.setattr(OC, "run_numeric", numeric)
    monkeypatch.setattr(OC, "current_weight", lambda _repository, _config, *, at: (
        spec.w, {"w": spec.w, "source": "grid", "at": at}))
    monkeypatch.setattr(OC, "new_ulid", lambda: "01GR1DDEC1S10N0000000000" + case_digest(case)[:2].upper())
    card = _card()
    entry = _Entry("boundary-key-" + spec.shape, spec.results, card)
    gate = OC.ObjectiveRestraintGate(vault, SimpleNamespace(sqlite_path="/grid/state.sqlite"), _Runtime(entry, spec.seed),
                                     card_builder=lambda _state, _feasible: SimpleNamespace(
                                         payload=lambda: card.payload, card_hash=card.card_hash,
                                         card_version=card.version, text=card.text, json=card.json),
                                     session_id="s_grid", clock=FrozenClock(NOW), may_defer=False)
    readiness = {name: (None if name in spec.ready else "not_set_up") for name in (DECIDER, LLM)}
    outcome = gate._mixed(SimpleNamespace(minutes_left=30.0), list(spec.arguments["candidates"]),
                          key="boundary-key-" + spec.shape, seed="numeric-seed-" + spec.shape, readiness=readiness,
                          ready=spec.ready, topic="Topic A",
                          options=[rq.BlockOption(INSERT_NOW, "Ask now."), rq.BlockOption(CONTINUE_CURRENT, "Wait.")],
                          extra=["A question on Topic A was just missed."],
                          **{name: value for name, value in spec.arguments.items() if name != "candidates"})
    return {"chosen": outcome.chosen_ref, "propensity": outcome.propensity, "record": outcome.record,
            "refused": outcome.refused, "why": outcome.why, "wait_feasible": outcome.wait_feasible,
            "numeric_calls": calls}


def case_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def serialized(outcome: dict[str, Any]) -> str:
    return json.dumps(outcome, sort_keys=True, default=repr, ensure_ascii=False)


def test_the_post_miss_choice_serves_and_records_as_the_golden_says(monkeypatch):
    # The golden lists each shape's digests in the grid's own order, so a difference is named by its case below.
    observed: dict[str, list[str]] = {}
    names: dict[str, list[str]] = {}
    served: dict[str, int] = {}
    for case, spec in grid():
        with monkeypatch.context() as patch:
            outcome = run_case(case, spec, patch)
        observed.setdefault(spec.shape, []).append(case_digest(serialized(outcome))[:12])
        names.setdefault(spec.shape, []).append(case)
        drawn = (outcome["record"].get("mixture") or {}).get("drawn_component")
        key = f"{spec.shape}:{outcome['chosen']}:{drawn}"
        served[key] = served.get(key, 0) + 1
    if WRITE:
        # One line per shape: the digests are a list only this test reads, and the golden stays a few lines long.
        packed = {shape: " ".join(values) for shape, values in observed.items()}
        GOLDEN.write_text(json.dumps({"digests": packed, "served": dict(sorted(served.items()))}, indent=0,
                                     sort_keys=True) + "\n", encoding="utf-8")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    golden["digests"] = {shape: values.split(" ") for shape, values in golden["digests"].items()}
    assert {shape: len(values) for shape, values in observed.items()} == {
        shape: len(values) for shape, values in golden["digests"].items()}
    differ = [names[shape][index] for shape, values in observed.items()
              for index, value in enumerate(values) if value != golden["digests"][shape][index]]
    assert not differ, f"{len(differ)} of {sum(map(len, observed.values()))} cases differ, first: {differ[:5]}"
    assert served == golden["served"]


@pytest.mark.parametrize("case", ["restraint|both:answered:yes_0.3|numeric:first|other:1|w:0.35|seed:None",
                                  "followup_lesson|both:answered:shown|numeric:last|other:1|w:0.35|seed:grid-seed-a"])
def test_a_case_is_the_same_bytes_run_twice(case, monkeypatch):
    spec = dict(grid())[case]
    with monkeypatch.context() as patch:
        first = serialized(run_case(case, spec, patch))
    with monkeypatch.context() as patch:
        second = serialized(run_case(case, spec, patch))
    assert first == second and "0x" not in first


# -- the pure choice with literals --------------------------------------------------------------------------------


def _inputs(**overrides):
    from learnloop.router_objective import choose as C

    values = dict(support=(INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION), staged_ref=INSERT_NOW,
                  wait_ref=CONTINUE_CURRENT, per_option=True, llm_status=ANSWERED,
                  llm_options={INSERT_NOW: 0.2, CONTINUE_CURRENT: 0.3, NO_INTERVENTION: 0.5},
                  llm_option_rationale="Words.", llm_p_yes=None, llm_rationale=None, numeric_status=ANSWERED,
                  numeric_choice=NO_INTERVENTION, w=0.5, to_other_policy=True, epsilon=0.02, seed="literal-seed")
    return C.PostMissInputs(**{**values, **overrides})


def test_the_choice_reads_only_its_inputs_and_draws_only_from_its_seed():
    from learnloop.router_objective import choose as C

    first, again = C.post_miss_choice(_inputs()), C.post_miss_choice(_inputs())
    assert first == again and first.failed == ()
    assert first.effective == {"staged": 0.0, "llm": 0.5, "numeric": 0.5}
    assert first.components["numeric"] == {INSERT_NOW: 0.0, CONTINUE_CURRENT: 0.0, NO_INTERVENTION: 1.0}
    assert first.propensity == first.drawn.pi[first.drawn.chosen] < 1.0
    seeds = {C.post_miss_choice(_inputs(seed=f"s{index}")).drawn.chosen for index in range(40)}
    assert seeds == {INSERT_NOW, CONTINUE_CURRENT, NO_INTERVENTION}


def test_an_answer_the_mix_cannot_use_fails_its_policy_and_moves_its_share():
    from learnloop.router_objective import choose as C

    # An arm with no mass, a parse that is not the policy's, or a status other than answered: the LLM failed, and
    # with the failure rule on, the numeric policy takes the whole mix. Only the policy's own parse, answered, keeps
    # its words on the record.
    for broken, words in ((dict(llm_options={INSERT_NOW: 0.5, CONTINUE_CURRENT: 0.5, NO_INTERVENTION: 0.0}), "Words."),
                          (dict(llm_options=None, llm_option_rationale=None), None),
                          (dict(llm_status=TIMEOUT), None)):
        choice = C.post_miss_choice(_inputs(**broken))
        assert choice.failed == ("llm",) and choice.llm_distribution is None and choice.rationale == words
        assert choice.effective == {"staged": 0.0, "llm": 0.0, "numeric": 1.0}
    # The numeric policy's choice outside the support fails it too; off the rule, the share goes to staged.
    choice = C.post_miss_choice(_inputs(numeric_choice="elsewhere", to_other_policy=False))
    assert choice.failed == ("numeric",) and choice.numeric_choice is None
    assert choice.effective == {"staged": 0.5, "llm": 0.5, "numeric": 0.0}


def test_a_yes_no_answer_is_two_arms_and_keeps_its_words_whatever_it_answered():
    from learnloop.router_objective import choose as C

    two = dict(support=(INSERT_NOW, CONTINUE_CURRENT), per_option=False, llm_options=None,
               llm_option_rationale=None, llm_rationale="Finish this first.", numeric_choice=INSERT_NOW)
    choice = C.post_miss_choice(_inputs(**two, llm_p_yes=0.25))
    assert choice.llm_distribution == {INSERT_NOW: 0.25, CONTINUE_CURRENT: 0.75}
    for certain in (0.0, 1.0, None):
        refused = C.post_miss_choice(_inputs(**two, llm_p_yes=certain))
        assert refused.failed == ("llm",) and refused.rationale == "Finish this first."
    failed = C.post_miss_choice(_inputs(**two, llm_p_yes=0.25, llm_status=FAILED))
    assert failed.failed == ("llm",) and failed.rationale == "Finish this first."
