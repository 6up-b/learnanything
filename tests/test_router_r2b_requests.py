"""Router R2b: the two models' requests and the strict parsing of their answers.

Fail-first (plan §9 R2b, test 1): a fake LLM that names a block nobody
offered is rejected at parse: its answer is not used, its weight goes to the
staged rule, and the unknown id can never be chosen (G1).
"""

from __future__ import annotations

import pytest

from learnloop.ai.decisions import ChoiceQuestion, NoulQuestion, request_body
from learnloop.router import requests as rq

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, options_in

OPTIONS = (
    rq.BlockOption("repair:lo_r1", "Another go at Spans, where recent answers slipped."),
    rq.BlockOption("maintain:lo_m1", "Bases again, before it slips."),
    rq.BlockOption("stop_for_today", rq.STOP_DESCRIPTION),
)


def _request(*, sensors=()):
    return rq.BoundaryRequest(options=OPTIONS, state=rq.state_text("# Session\n", OPTIONS), sensors=tuple(sensors))


def test_a_fake_llm_naming_an_unknown_block_is_rejected_at_parse():
    answer = {
        "choose_block": [{"id": "repair:lo_r1", "probability": 0.5}, {"id": "ghost:block", "probability": 0.5}],
        "rationale": "Go on.",
        "evidence_ids": [],
    }
    with pytest.raises(rq.RouterResponseInvalid, match="not asked"):
        rq.parse_llm_choice(answer, _request())


def test_through_the_chooser_an_unknown_id_is_a_fallback_and_is_never_chosen(tmp_path):
    def rogue(request):
        refs = options_in(request.prompt)
        answer = FakeLLM.default_answer(request)
        answer["choose_block"] = [{"id": "ghost:block", "probability": 1.0}] + [
            {"id": ref, "probability": 0.0} for ref in refs]
        return answer

    runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=rogue))
    env = mixture_env(tmp_path, runtime)
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions
    for row in decisions:
        assert row["chosen_ref"] != "ghost:block"
        assert row["fallback"] == "llm"
        assert row["detail_json"]["mixture"]["models"]["llm"]["status"] == "invalid"
        assert row["model_distributions_json"]["llm"] is None
        assert row["mixture_weights_json"]["effective"]["llm"] == 0.0


def test_the_llm_distribution_is_renormalized_and_missing_ids_are_zero():
    parsed = rq.parse_llm_choice(
        {"choose_block": [{"id": "repair:lo_r1", "probability": 0.6}, {"id": "maintain:lo_m1", "probability": 0.2}],
         "rationale": " Keep going. ", "evidence_ids": ["att_1", "att_1"]},
        _request(),
    )
    assert parsed.distribution == pytest.approx({"repair:lo_r1": 0.75, "maintain:lo_m1": 0.25, "stop_for_today": 0.0})
    assert parsed.rationale == "Keep going."
    assert parsed.evidence_ids == ("att_1",)


@pytest.mark.parametrize("entries, reason", [
    ([{"id": "repair:lo_r1", "probability": 0.5}, {"id": "repair:lo_r1", "probability": 0.5}], "twice"),
    ([{"id": "repair:lo_r1", "probability": 1.5}], r"outside \[0, 1\]"),
    ([{"id": "repair:lo_r1", "probability": float("nan")}], "finite"),
    ([{"id": "repair:lo_r1", "probability": 0.0}], "no probability"),
    ("repair:lo_r1", "not a list"),
])
def test_malformed_distributions_fail_closed(entries, reason):
    with pytest.raises(rq.RouterResponseInvalid, match=reason):
        rq.parse_llm_choice({"choose_block": entries, "rationale": "", "evidence_ids": []}, _request())


def test_the_decider_gets_typed_questions_and_a_body_with_no_unknown_field():
    sensors = (rq.SensorTopic("lo_r1", "Spans"),)
    request = _request(sensors=sensors)
    questions = request.decider_questions()
    assert isinstance(questions["choose_block"], ChoiceQuestion)
    assert list(questions["choose_block"].options) == ["repair:lo_r1", "maintain:lo_m1", "stop_for_today"]
    assert isinstance(questions["teach_first_lo_r1"], NoulQuestion)
    assert isinstance(questions["will_pass_next_lo_r1"], NoulQuestion)
    assert request.question_set_version == "router_qs_v2"
    assert _request().question_set_version == "router_qs_v1"
    body = request_body("perplexity/pplx-decider-v1.1-27b", request.state, questions)
    assert set(body) == {"model", "state", "questions"}


def test_sensors_name_only_the_asked_topics():
    request = _request(sensors=(rq.SensorTopic("lo_r1", "Spans"),))
    answer = {"choose_block": [{"id": "repair:lo_r1", "probability": 1.0}], "rationale": "", "evidence_ids": [],
              "teach_first": [{"topic_id": "lo_other", "probability": 0.2}], "will_pass_next": []}
    with pytest.raises(rq.RouterResponseInvalid, match="topic"):
        rq.parse_llm_choice(answer, request)
    answer["teach_first"] = [{"topic_id": "lo_r1", "probability": 0.2}]
    answer["will_pass_next"] = [{"topic_id": "lo_r1", "probability": 0.9}]
    parsed = rq.parse_llm_choice(answer, request)
    assert parsed.sensors == {"teach_first": {"lo_r1": 0.2}, "will_pass_next": {"lo_r1": 0.9}}


def test_the_llm_prompt_lists_the_options_and_the_plain_word_rules():
    prompt = _request().llm_prompt()
    assert options_in(prompt) == ["repair:lo_r1", "maintain:lo_m1", "stop_for_today"]
    assert "at most 3 short sentences" in prompt
    assert rq.llm_result_model(rq.LLM_SCHEMA_V1) is rq.RouterLLMAnswerV1
    assert rq.llm_result_model(rq.LLM_SCHEMA_V2) is rq.RouterLLMAnswerV2


def test_every_router_answer_model_has_the_strict_schema_the_transports_send():
    # Found by the live session: a result model that is not a WireModel fails
    # every real structured transport (Codex included) before it is sent.
    from learnloop.ai.strict_schema import strict_output_schema
    from learnloop.daily_plan.router_teach_back import TeachBackSummary

    for version in (rq.LLM_SCHEMA_V1, rq.LLM_SCHEMA_V2, rq.LLM_RESTRAINT_SCHEMA):
        schema = strict_output_schema(rq.llm_result_model(version))
        assert schema["additionalProperties"] is False
    assert strict_output_schema(TeachBackSummary)["additionalProperties"] is False
