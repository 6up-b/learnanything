"""Refactor E2: the objective router's choice called with plain values, no vault, database or clock.

``router_objective.choose.choose`` is the boundary's decision: the failed policies and where their share goes (IH5),
the effective weights, the mix's draw, the stop coin on its own uniform after the mix's (RO5), the rule code and
sentence of what is served, the rationale guard and the why; ``decision_record`` is the decision's own record (L6).
Each test builds ``ChoiceInputs`` from literals; a seed that lands a draw where a test needs it is found by trying seeds, never by
patching the draw.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from learnloop.router import mixture as mx
from learnloop.router import why as router_why
from learnloop.router_objective import choose as C
from learnloop.router_objective import mix
from learnloop.router_objective import stop_coin as SC

STOP = "stop_for_today"
SUPPORT = ("repair:a", "maintain:b", STOP)
OPTIONS = {"repair:a": C.OptionFacts("repair_recent_errors", topic="Eigenvalues"),
           "maintain:b": C.OptionFacts("review", topic="Bases")}
LLM_DIST = {"repair:a": 0.6, "maintain:b": 0.3, STOP: 0.1}
RATIONALE = "You slipped on this recently, so another go helps."
AVAILABILITY = {"session_minutes": 12.0, "remembered_minutes": 25.0, "minutes_budget": 25.0, "minutes_left": 13.0,
                "session_id": "s1", "receipt": None}


def inputs(**overrides) -> C.ChoiceInputs:
    values = dict(
        support=SUPPORT, staged_ref="repair:a", options=OPTIONS, llm_status="answered", llm_distribution=LLM_DIST,
        rationale=RATIONALE, cited=("att_1",), card_evidence_ids=frozenset({"att_1", "att_2"}),
        numeric_status="answered", numeric_choice="maintain:b", w=0.5, to_other_policy=True, epsilon=0.02,
        seed="e2-seed", stop_rate=0.0, session_minutes=None, availability=None, staged_why="The plan's own why.",
        no_models=False, boundary_key="bk_e2", algorithm_version="mvp-0.60", llm_schema_version="router_llm_choice_v3",
    )
    values.update(overrides)
    return C.ChoiceInputs(**values)


def record_of(choice: C.Choice, **overrides):
    """The choice's own record, built from the inputs it was chosen on (``overrides`` as given to ``inputs``)."""

    return C.decision_record(choice, inputs(**overrides), question_set_version="qs_v1")


def seed_where(predicate, **overrides) -> tuple[str, C.Choice]:
    for index in range(20_000):
        seed = f"e2-{index}"
        choice = C.choose(inputs(seed=seed, **overrides))
        if predicate(choice):
            return seed, choice
    raise AssertionError("no seed found")


def test_the_statuses_it_compares_are_the_runtimes():
    from learnloop.daily_plan import router_runtime

    assert (C.ANSWERED, C.NOT_READY) == (router_runtime.ANSWERED, router_runtime.NOT_READY)


# -- the rule codes ---------------------------------------------------------------------------------------------


def test_a_served_stop_is_the_stop_offer():
    seed, choice = seed_where(lambda c: c.served == STOP)
    assert (choice.rule_code, choice.rule) == ("stop_offer", router_why.sentence("stop_offer"))
    record = record_of(choice, seed=seed)
    assert record.rule == "stop_offer" and record.chosen_ref == STOP


def test_a_served_block_carries_its_own_reason_code_and_sentence():
    seed, choice = seed_where(lambda c: c.served == "maintain:b" and c.drawn.component == mix.NUMERIC)
    assert (choice.rule_code, choice.rule) == ("review", "Bases again, before it slips.")
    assert record_of(choice, seed=seed).rule == "review"
    assert (choice.why, choice.why_kind) == (f"{router_why.PICKED_BY_ESTIMATE} Bases again, before it slips.",
                                             "computed")


def test_a_block_with_no_code_has_no_rule_and_the_staged_pick_keeps_the_plans_why():
    options = {**OPTIONS, "repair:a": C.OptionFacts("")}
    overrides = dict(options=options, llm_distribution=None, llm_status="timeout", to_other_policy=False)
    seed, choice = seed_where(lambda c: c.served == "repair:a" and c.drawn.component == mix.STAGED, **overrides)
    assert choice.rule_code == "" and record_of(choice, seed=seed, **overrides).rule is None
    assert (choice.why, choice.why_kind) == ("The plan's own why.", "computed")


# -- IH5's failure share ----------------------------------------------------------------------------------------


def test_a_failed_llm_policys_share_goes_to_the_numeric_policy_with_the_switch_on():
    choice = C.choose(inputs(llm_distribution=None, llm_status="timeout"))
    assert choice.failed == (mix.LLM,)
    assert choice.effective == {mix.STAGED: 0.0, mix.LLM: 0.0, mix.NUMERIC: 1.0}
    assert set(choice.components) == {mix.STAGED, mix.NUMERIC}
    assert (choice.fallback, dict(choice.fallback_reasons)) == (mix.LLM, {mix.LLM: "timeout"})


def test_with_the_switch_off_a_failed_policys_share_goes_to_staged():
    choice = C.choose(inputs(llm_distribution=None, llm_status="failed", to_other_policy=False))
    assert choice.effective == {mix.STAGED: 0.5, mix.LLM: 0.0, mix.NUMERIC: 0.5}


def test_a_numeric_choice_outside_the_support_fails_the_numeric_policy():
    choice = C.choose(inputs(numeric_choice="gone:c"))
    assert choice.failed == (mix.NUMERIC,) and choice.numeric_choice is None
    assert choice.effective == {mix.STAGED: 0.0, mix.LLM: 1.0, mix.NUMERIC: 0.0}
    assert dict(choice.fallback_reasons) == {mix.NUMERIC: "answered"}


def test_both_failed_leave_staged_the_whole_mix_and_a_missing_answer_reads_not_ready():
    choice = C.choose(inputs(llm_distribution=None, llm_status="spend", numeric_status=None, numeric_choice=None))
    assert choice.effective == {mix.STAGED: 1.0, mix.LLM: 0.0, mix.NUMERIC: 0.0}
    assert (choice.fallback, dict(choice.fallback_reasons)) == ("both", {mix.LLM: "spend", mix.NUMERIC: "not_ready"})


# -- the propensities -------------------------------------------------------------------------------------------


def test_with_no_coin_the_logged_distribution_is_the_mixs_and_the_propensity_its_draws():
    choice = C.choose(inputs())
    parts = mix.components(list(SUPPORT), "repair:a", llm=LLM_DIST, numeric_ref="maintain:b")
    assert choice.pi == mix.mu(list(SUPPORT), parts, choice.effective, 0.02) == choice.drawn.pi
    assert choice.propensity == choice.drawn.propensity == choice.pi[choice.served]
    assert choice.coin is None and choice.assignments == ()
    record = record_of(choice)
    assert [entry["ref"] for entry in record.alternatives] == [ref for ref in SUPPORT if ref != choice.served]
    assert all(entry["p"] == choice.pi[entry["ref"]] and entry["lost_by"] == "not_drawn"
               for entry in record.alternatives)


def test_a_one_hot_mix_is_served_with_propensity_one():
    choice = C.choose(inputs(llm_distribution=None, llm_status="timeout", numeric_status="failed", epsilon=0.0))
    assert choice.drawn.deterministic and choice.propensity == 1.0 and choice.served == "repair:a"


# -- RO5's coin: the mix's draw, then the coin's own uniform ------------------------------------------------------


COIN = dict(stop_rate=0.45, session_minutes=12.0, availability=AVAILABILITY)


def test_the_coin_draws_after_the_mix_on_its_own_uniform_and_leaves_the_mixs_draw_alone():
    without = C.choose(inputs())
    choice = C.choose(inputs(**COIN))
    assert choice.drawn == without.drawn
    assert (choice.drawn.u1, choice.drawn.u2) == (mx.uniform("e2-seed", "component"), mx.uniform("e2-seed", "candidate"))
    assert choice.coin.u == mx.uniform("e2-seed", "stop_coin")
    assert choice.coin == SC.flip("e2-seed", 0.45, support=list(SUPPORT), mu=choice.drawn.pi,
                                  drawn=choice.drawn.chosen, availability=AVAILABILITY)
    assert choice.pi == SC.served_distribution(choice.drawn.pi, 0.45, list(SUPPORT))
    assert choice.propensity == choice.coin.served_propensity == choice.pi[choice.served]
    [assignment] = choice.assignments
    assert assignment["draw"] == choice.coin.u and assignment["detail"]["availability"] == AVAILABILITY


def test_an_offered_stop_the_coin_chose_shows_no_models_words():
    seed, choice = seed_where(lambda c: c.coin is not None and c.coin.arm == SC.OFFER_STOP
                              and c.drawn.chosen != STOP and c.drawn.component == mix.LLM, **COIN)
    assert choice.served == STOP and not choice.shown and choice.rationale_hidden
    assert (choice.why, choice.why_kind) == (router_why.sentence("stop_offer"), "computed")
    assert record_of(choice, seed=seed, **COIN).facts["propensity"] == choice.coin.served_propensity


def test_the_coin_skips_the_sessions_opening_boundary_and_needs_its_availability():
    assert C.choose(inputs(stop_rate=0.45, session_minutes=0.0)).coin is None
    assert not C.coin_applies(0.45, SUPPORT, None) and not C.coin_applies(0.0, SUPPORT, 5.0)
    assert C.coin_reads_minutes(0.45, SUPPORT) and not C.coin_reads_minutes(0.45, ("repair:a", "maintain:b"))
    with pytest.raises(ValueError, match="availability"):
        C.choose(inputs(stop_rate=0.45, session_minutes=12.0))


# -- the rationale guard ------------------------------------------------------------------------------------------


def _llm_drew(favoured: bool = True):
    return lambda c: c.drawn.component == mix.LLM and (c.drawn.chosen == "repair:a") == favoured


def test_a_rationale_that_passes_is_shown_with_its_evidence():
    _seed, choice = seed_where(_llm_drew())
    assert choice.guard is None and choice.shown and not choice.rationale_hidden
    assert (choice.why, choice.why_kind) == (f"{router_why.MODEL_MARK} {RATIONALE}", "model_written")
    assert choice.evidence_labels == ("att_1",)


@pytest.mark.parametrize(("overrides", "verdict"), [
    ({"rationale": "The probe posterior says this is next."}, "jargon"),
    ({"cited": ("att_9",)}, "unknown_evidence"),
    ({"rationale": "One. Two. Three. Four."}, "too_long"),
    ({"rationale": "This has a 70% chance."}, "probability"),
    ({"rationale": "   "}, "empty"),
    ({"rationale": None}, "absent"),
])
def test_the_guard_refuses_a_rationale_and_the_rules_sentence_is_shown(overrides, verdict):
    _seed, choice = seed_where(_llm_drew(), **overrides)
    assert choice.guard == verdict and not choice.shown and choice.rationale_hidden
    assert choice.why_kind == "model_no_rationale" and choice.evidence_labels == ()
    assert choice.why == f"{router_why.PICKED_BY_MODEL.format(count=3)} {router_why.sentence('repair_recent_errors', topic='Eigenvalues')}"


def test_the_llm_drawing_an_option_it_did_not_favour_hides_its_rationale():
    _seed, choice = seed_where(_llm_drew(favoured=False))
    assert (choice.guard, choice.shown, choice.favoured) == ("another_option", False, "repair:a")


# -- the record and the purity -------------------------------------------------------------------------------------


def test_the_choice_has_its_own_plan_block_record():
    record = record_of(C.choose(inputs(no_models=True)), no_models=True)
    assert (record.kind, record.status, record.decided_by) == ("plan_block", "chosen", C.NO_MODELS)
    assert record.subject_id is None and record.id is None and record.trace_id is None
    assert record.facts["boundary_key"] == "bk_e2" and record.facts["option_count"] == 3
    assert record.versions == {"algorithm_version": "mvp-0.60", "policy": mix.POLICY, "design": mix.DESIGN,
                               "seed": "e2-seed", "why_version": C.WHY_VERSION, "question_set_version": "qs_v1",
                               "llm_schema_version": "router_llm_choice_v3"}
    assert record_of(C.choose(inputs())).decided_by == C.MODE


def test_it_reads_no_database_clock_or_id_stream_and_leaves_its_inputs_alone(monkeypatch):
    import sqlite3

    from learnloop import clock, ids

    def refuse(*_args, **_kwargs):
        raise AssertionError("the choice reached outside its inputs")

    for target, name in ((sqlite3, "connect"), (clock, "utc_now_iso"), (ids, "new_ulid")):
        monkeypatch.setattr(target, name, refuse)
    given = inputs(**COIN)
    snapshot = (dict(given.llm_distribution), dict(given.availability), dict(given.options))
    first, second = C.choose(given), C.choose(replace(given))
    assert first == second
    assert (C.decision_record(first, given, question_set_version="qs_v1")
            == C.decision_record(second, replace(given), question_set_version="qs_v1"))
    assert snapshot == (dict(given.llm_distribution), dict(given.availability), dict(given.options))
