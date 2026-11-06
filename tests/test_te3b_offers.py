"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, §24's TE3b row): lesson offers as candidates of the router objective.

Fakes only (the router's models are ``tests.router_model_fakes``; no network). TE1b's candidates are pinned where a
test needs one (``build_candidates``), so the serving path, the logged mix and the responses are what is tested:

* the offer joins the objective's support at a reversible ``plan_block`` boundary (one offer, beside staged's
  top-k, before stop), its sensors on the decision; below the tag, or with ``in_objective`` off, the predecessor's
  decision exactly (byte-identical rows and blocks, the seed pinned);
* G3: ``μ`` recomputes from the logged values with the offer in the support, on every failure path;
* a drawn offer is a plan block of its own (no items), its step the card; the learner's one response is recorded on
  the ``plan_block`` decision and ends the block; moving on without an answer is ``ignored`` at the next boundary;
* the ceiling binds across the day's offers and is logged; no offer beside forced items (a follow-up, a request, a
  randomized check) and so never inside a cold check, a probe or a randomized-check block;
* the LLM policy sees the offer as one more option of its existing request (no new request);
* TE1b's Today-open card is drawn only where the objective does not serve.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION, LESSON_OPPORTUNITY_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.types import LESSON_OFFER_SUBTYPE
from learnloop.db.stores import router_objective as trace_store
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import mix

from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import policy_answer

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION
OFFER = "lesson_offer:lo_diag"


def _candidates() -> list[LS.Candidate]:
    return [
        LS.Candidate(ref=LS.lesson_ref("lo_diag"), learning_object_ids=("lo_diag",), reason="new_goal",
                     predicted_success=0.3, title="Diag"),
        LS.Candidate(ref=LS.lesson_ref("lo_m2"), learning_object_ids=("lo_m2",), reason="cold_failing",
                     predicted_success=0.6, title="M2"),
        LS.Candidate(ref=LS.lesson_ref("lo_p1"), learning_object_ids=("lo_p1",), reason="below_band",
                     predicted_success=0.5, title="P1"),
    ]


@pytest.fixture
def offerable(monkeypatch):
    """TE1b's candidates pinned (one new goal LO first by value, two others)."""

    monkeypatch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: (_candidates(), {}))


@pytest.fixture
def offer_drawn(monkeypatch):
    """The mix's draw serves the offer whenever it is in the support (its logged probability is the exact ``μ`` of
    the offer, so G3 still holds; the uniforms are not reproduced, which no test here reads)."""

    real = mix.draw

    def draw(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        if OFFER in support:
            from dataclasses import replace

            return replace(drawn, chosen=OFFER, propensity=drawn.pi[OFFER])
        return drawn

    monkeypatch.setattr(mix, "draw", draw)


def _objective_rows(env) -> list[dict[str, Any]]:
    return [row for row in rows(env) if row["policy"] == mix.POLICY]


def _first_decision(env) -> tuple[Any, dict[str, Any]]:
    """Advance until the objective has decided a boundary (the day's randomized check block, placed by the rules,
    comes first); answer what is served on the way."""

    from tests.daily_plan_fakes import record_attempt

    for _ in range(8):
        record, step = advance(env, serve=True)
        if _objective_rows(env):
            return record, step
        if step is None or step["kind"] != "item":
            break
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    raise AssertionError("the objective never decided a boundary")


def test_the_offer_joins_the_support_beside_the_blocks_and_before_stop(tmp_path, offerable):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    assert env.policy.lesson_offer is not None
    _first_decision(env)
    row = _objective_rows(env)[0]
    support = row["detail_json"]["mixture"]["support"]
    assert OFFER in support and support[-1] == "stop_for_today" and support.index(OFFER) == len(support) - 2
    assert sum(1 for ref in support if ref.startswith("lesson_offer:")) == 1  # one offer a decision
    offers = row["detail_json"]["lesson_offers"]
    assert offers["status"] == "offered" and offers["candidate_id"] == OFFER
    assert offers["p_accept"]["mean"] > 0 and offers["p_accept"]["sd"] > 0
    assert offers["duration"]["source"] == "seed" and offers["duration"]["median_minutes"] == pytest.approx(15.0)
    # The offer is never staged's pick, and its candidate row is logged with its sensors.
    assert row["detail_json"]["mixture"]["staged_ref"] != OFFER
    entry = next(c for c in row["candidates_json"] if c["ref"] == OFFER)
    assert entry["annotations"]["lesson_offer"]["card"]["candidates"][0]["ref"] == "lesson:lo_diag"
    assert len(entry["annotations"]["lesson_offer"]["card"]["candidates"]) == 3  # the offer and two alternatives


def test_g3_mu_recomputes_with_an_offer_in_the_support_on_every_path(tmp_path, offerable, monkeypatch):
    def check(env):
        _first_decision(env)
        row = _objective_rows(env)[0]
        mixture = row["detail_json"]["mixture"]
        assert OFFER in mixture["support"]
        recomputed = mix.recompute(mixture)
        assert sum(recomputed.values()) == pytest.approx(1.0)
        served = recomputed
        if mixture.get("stop_coin"):
            # RO5's stop coin: the served distribution is the coin's over the mix's (the mix's own μ beside it).
            from learnloop.router_objective import stop_coin as SC

            assert mixture["mix_pi"] == pytest.approx(recomputed)
            served = SC.served_distribution(recomputed, float(mixture["stop_coin"]["rate"]), list(mixture["support"]))
        assert served[row["chosen_ref"]] == pytest.approx(row["propensity"] or 1.0)
        assert recomputed[OFFER] >= float(mixture["epsilon"]) - 1e-12  # the floor reaches the offer
        logged = {c["ref"]: c["propensity"] for c in row["candidates_json"] if c["ref"] in recomputed}
        assert logged[OFFER] == pytest.approx(served[OFFER])
        return mixture

    # Both policies answer (the LLM's request holds the offer as one more option).
    llm = FakeLLM(answer=policy_answer)
    both = check(mixture_env(tmp_path / "both", fake_runtime(llm=llm), version=TAG))
    assert both["failed"] == [] and OFFER in both["llm_distribution"]
    # No model set up: the LLM policy's share is staged's.
    assert check(mixture_env(tmp_path / "none", fake_runtime(), version=TAG))["failed"] == ["llm"]
    # The numeric policy fails too: both shares are staged's.
    from learnloop.daily_plan import objective_inputs

    def broken(*args, **kwargs):
        raise RuntimeError("planted")

    monkeypatch.setattr(objective_inputs, "build", broken)
    assert sorted(check(mixture_env(tmp_path / "broken", fake_runtime(), version=TAG))["failed"]) == ["llm", "numeric"]


def test_the_llm_policy_sees_the_offer_in_its_existing_request(tmp_path, offerable):
    llm = FakeLLM(answer=policy_answer)
    env = mixture_env(tmp_path, fake_runtime(llm=llm), version=TAG)
    _first_decision(env)
    asked = [request for request in llm.requests if request.result_model.__name__ == "RouterLLMChoiceV3"]
    assert len(asked) == 1  # one request for the decision: no new call for the offer
    assert f"[{OFFER}]" in asked[0].prompt and "Offer a lesson on Diagonalization (about 15 min)" in asked[0].prompt
    assert "predicted chance they start it" in asked[0].prompt


def test_a_drawn_offer_is_a_block_answered_on_its_own_decision(tmp_path, offerable, offer_drawn):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    record, step = _first_decision(env)
    assert step["kind"] == "lesson_offer" and step["offer"]["suggestion"]["ref"] == "lesson:lo_diag"
    block = record.current_block()
    assert block.subtype == LESSON_OFFER_SUBTYPE and block.items == [] and block.is_lesson_offer
    decision_id = step["offer"]["decision_id"]
    row = next(r for r in rows(env) if r["id"] == decision_id)
    assert row["chosen_ref"] == OFFER and row["detail_json"]["lesson_offer"]["card"]["candidates"]
    # The trace holds the offer's sensors and its branches' terms.
    with env.repository.connection() as connection:
        trace = trace_store.trace(connection, decision_id)["trace"]
    offer = trace["candidates"][OFFER]["offer"]
    assert offer["sensors"]["p_accept"]["priors_version"] == LS.PRIORS_VERSION
    assert offer["terms"]["q_accepted"] is not None and offer["terms"]["q_declined"] is not None
    assert offer["terms"]["kappa_integral_accepted"] > 0 and offer["sensors"]["duration"]["source"] == "seed"
    assert offer["action"]["commitments"] == [["lo_diag", 3.0]]
    # Start: one response on the plan_block decision, the lesson id reserved, the block ended.
    answer = SG.respond(env.vault, env.repository, decision_id=decision_id, response="accepted",
                        clock=env.clock)
    assert answer["lesson"]["learning_object_ids"] == ["lo_diag"] and answer["lesson"]["lesson_id"]
    with env.repository.connection() as connection:
        response = suggestions.response_for(connection, decision_id)
        assert response["response"] == "accepted"
        assert connection.execute("SELECT COUNT(*) FROM router_suggestion_responses WHERE decision_id = ?",
                                  (decision_id,)).fetchone()[0] == 1
    record, step = advance(env, serve=False)
    ended = next(b for b in record.blocks if b.id == block.id)
    assert ended.finished and ended.outcome == "accepted"
    # A second answer on the same decision is refused (one response a decision).
    with pytest.raises(SG.SuggestionError):
        SG.respond(env.vault, env.repository, decision_id=decision_id, response="declined", clock=env.clock)


def test_moving_on_without_an_answer_is_ignored_at_the_next_boundary(tmp_path, offerable, offer_drawn):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    _record, step = _first_decision(env)
    assert step["kind"] == "lesson_offer"
    decision_id = step["offer"]["decision_id"]
    env.clock.advance(1)
    _record, _next = advance(env, serve=True)  # the card was shown; serving again moves on
    with env.repository.connection() as connection:
        response = suggestions.response_for(connection, decision_id)
    assert response["response"] == "ignored"
    assert json.loads(response["detail_json"])["recorded"] == "moved_on_without_an_answer"


def test_the_ceiling_binds_across_the_days_offers_and_is_logged(tmp_path, offerable):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG,
                      toml="[router.lesson_suggestions]\nceiling_per_day = 0\n")
    _first_decision(env)
    row = _objective_rows(env)[0]
    assert OFFER not in row["detail_json"]["mixture"]["support"]
    offers = row["detail_json"]["lesson_offers"]
    assert offers["status"] == "none:ceiling_bound" and offers["ceiling"]["bound"] is True


def test_no_offer_beside_forced_items():
    offer = LO.build.__wrapped__ if hasattr(LO.build, "__wrapped__") else LO.build
    result = offer(None, None, today="2026-11-06", now_iso="2026-11-06T10:00:00Z", local_hour=10.0,
                   minutes_left=20.0, reentry=False, forced=True)  # type: ignore[arg-type]
    assert result.candidate is None and result.record["status"] == "none:forced_items"


def test_the_randomized_check_block_carries_no_offer(tmp_path, offerable):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    _first_decision(env)
    for row in rows(env):
        detail = row["detail_json"]
        if detail.get("source") == "ro5_randomized_check" or str(row["chosen_ref"]).startswith("forced:"):
            assert "lesson_offers" not in detail and not str(row["chosen_ref"]).startswith("lesson_offer:")


def test_te1bs_daily_card_is_drawn_only_where_the_objective_does_not_serve(tmp_path, offerable):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    assert SG.suggestions_enabled(env.vault) and not SG.suggestions_active(env.vault)
    assert SG.today_suggestion(env.vault, env.repository, clock=env.clock) is None
    with env.repository.connection() as connection:
        assert suggestions.decisions(connection) == []  # no Today-open draw
    off = mixture_env(tmp_path / "off", fake_runtime(), version=TAG,
                      toml="[router_objective]\nenabled = false\n")
    assert SG.suggestions_active(off.vault)  # the objective does not serve: TE1b exactly
