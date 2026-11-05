"""Router objective RO5 §9 item 2: randomized cold checks, embedded by default, and their scores. Fakes only.

The spec's listed tests: the same seed draws the same; the draw does not change with the action or either policy's
output; ``r_L`` matches the eligible count; no protected or exam-reserved item is ever drawn; ``"off"`` and the
predecessor serve identically (``tests/test_ro5_stop_coin.py`` with every arm off); the replaced item returns to the
pool. Beside them: the frame places the check at the day's first practice slot outside the mix, an ordinary
attempt with no label, help makes it a non-success, a topic with no eligible item raises a generation need, a day
with no session counts toward the completion gap, and a closed window's score forms from a completed check.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION
from learnloop.daily_plan import objective_inputs as OI
from learnloop.router_objective import assignments as A
from learnloop.router_objective import checks as C
from learnloop.router_objective import mix
from learnloop.router_objective import scores as S
from learnloop.router_objective import weight as W
from learnloop.router_objective_switches import CHECKS_EMBEDDED, CHECKS_RATE

from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_ro4_objective_serving import policy_answer

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION
CHECKS_ONLY = "[router_objective]\nstop_coin = 0.0\npick_open_share = 0.0\n"


# -- the draw ----------------------------------------------------------------------------------------------


def test_the_same_date_and_eligible_set_draw_the_same_and_r_is_exact():
    eligible = {"a": ["a1", "a2"], "b": ["b1"], "c": ["c1"], "z": []}
    one = C.draw("2026-11-05", CHECKS_EMBEDDED, 1, eligible, ["a", "b", "c", "z"])
    two = C.draw("2026-11-05", CHECKS_EMBEDDED, 1, eligible, ["a", "b", "c", "z"])
    assert one == two and len(one.slots) == 1
    assert one.r == pytest.approx({"a": 1 / 3, "b": 1 / 3, "c": 1 / 3, "z": 0.0})
    assert one.zero == ("z",) and one.slots[0]["item_id"] in eligible[one.slots[0]["topic"]]
    # Two a day: k/N, without replacement.
    both = C.draw("2026-11-05", CHECKS_EMBEDDED, 2, eligible, ["a", "b", "c", "z"])
    assert len({slot["topic"] for slot in both.slots}) == 2 and both.r["a"] == pytest.approx(2 / 3)
    # A rate: each eligible topic independently at it.
    rated = C.draw("2026-11-05", CHECKS_RATE, 0.5, eligible, ["a", "b", "c", "z"])
    assert rated.r == pytest.approx({"a": 0.5, "b": 0.5, "c": 0.5, "z": 0.0})


def test_the_draw_is_uniform_over_topics_across_dates():
    eligible = {lo: [f"{lo}1"] for lo in "abcd"}
    counts = {lo: 0 for lo in "abcd"}
    n = 4000
    for i in range(n):
        day = C.draw(f"d{i}", CHECKS_EMBEDDED, 1, eligible, list(eligible))
        counts[day.slots[0]["topic"]] += 1
    for lo in counts:
        assert counts[lo] / n == pytest.approx(0.25, abs=0.03)


def _env(tmp_path, *, toml: str = CHECKS_ONLY, llm=None):
    return mixture_env(tmp_path, fake_runtime(llm=llm), version=TAG, toml=toml)


def _check_rows(env) -> list[dict]:
    with env.repository.connection() as connection:
        return A.rows(connection, A.CHECK)


def test_the_draw_does_not_change_with_the_action_or_either_policys_output(tmp_path):
    plain = _env(tmp_path / "a")
    other = _env(tmp_path / "b", llm=FakeLLM(answer=policy_answer))
    run(plain), run(other)

    def drawn(env):
        return [(row["unit_id"], row["variant"], row["propensity"], row["detail"].get("item_id"),
                 row["detail"].get("r")) for row in _check_rows(env)]

    assert drawn(plain) == drawn(other) and drawn(plain)
    with plain.repository.connection() as connection:
        record = C.day_record(connection, plain.today())
    assert record["fixed_before"].startswith("any action draw")
    # r_L matches the eligible count on the day.
    positive = [lo for lo, r in record["r"].items() if r > 0]
    assert all(record["r"][lo] == pytest.approx(1 / len(positive)) for lo in positive)
    assert set(positive) == {lo for lo, n in record["eligible_items"].items() if n > 0}


def test_the_check_takes_the_first_practice_slot_outside_the_mix_with_no_label(tmp_path):
    env = _env(tmp_path)
    record = run(env)
    slot = next(row for row in _check_rows(env) if row["unit_id"].count(":") == 2)
    with env.repository.connection() as connection:
        administered = C.administered(connection)
    assert slot["id"] in administered
    planned = administered[slot["id"]]
    block = next(b for b in record.blocks if b.id == planned["block_id"])
    first = sorted(block.items, key=lambda item: item.position)[0]
    assert first.practice_item_id == planned["practice_item_id"] and first.origin == C.ORIGIN
    # The first non-reading block of the day carries it.
    practice_blocks = [b for b in sorted(record.blocks, key=lambda b: b.ordinal) if not b.is_reading and b.items]
    assert practice_blocks[0].id == block.id
    # Outside the mix: the router decision's items do not name it, and its μ is over blocks only.
    decision = next(row for row in rows(env) if row["id"] == block.decision_ref)
    assert decision.get("chosen_practice_item_id") != planned["practice_item_id"]
    assert mix.recompute(decision["detail_json"]["mixture"])[decision["chosen_ref"]] == pytest.approx(
        decision["propensity"])
    # The learner sees an ordinary question.
    from learnloop.daily_plan.view import _item_row

    assert _item_row(env, first)["origin"] == "chooser"
    # The replaced chooser item is not displaced: it stays in the plan's pool for later blocks.
    replaced = planned.get("replaced")
    if replaced:
        assert replaced in record.split["universe"]
        assert all(item.practice_item_id != replaced or item.block_id != block.id for item in record.items())


def test_completion_is_scored_by_the_label_and_help_makes_it_a_non_success(tmp_path):
    env = _env(tmp_path)
    run(env)
    with env.repository.connection() as connection:
        resolved = [entry for entry in C.resolve(connection, through=env.today()) if entry.status == "completed"]
        assert resolved, "the run answered the check"
        assert resolved[0].outcome in (0.0, 1.0)
        assert C._label({"correctness": 1.0, "hints_used": 0}, assisted=False) == 1.0
        assert C._label({"correctness": 1.0, "hints_used": 1}, assisted=False) == 0.0
        assert C._label({"correctness": 1.0, "hints_used": 0}, assisted=True) == 0.0


def test_no_protected_or_exam_reserved_item_is_ever_eligible(tmp_path, monkeypatch):
    env = _env(tmp_path)
    los = list(OI.population(env.vault, env.repository, env.now_iso()))
    before = OI.check_eligible_items(env.vault, env.repository, los)
    flat = [item for items in before.values() for item in items]
    assert flat
    from learnloop.scheduling import serving_exclusions as SE

    real = SE.routine_serving_exclusions
    reserved = frozenset(flat[:1])

    def with_reserved(vault, repository):
        return SE.ServingExclusions(**{**real(vault, repository).__dict__, "reserved_exam_item_ids": reserved})

    monkeypatch.setattr(SE, "routine_serving_exclusions", with_reserved)
    after = OI.check_eligible_items(env.vault, env.repository, los)
    assert not reserved & {item for items in after.values() for item in items}
    # An attempted, revealed or assisted item is not eligible either.
    record_attempt(env.repository, flat[-1], next(lo for lo, items in before.items() if flat[-1] in items),
                   env.clock.now())
    again = OI.check_eligible_items(env.vault, env.repository, los)
    assert flat[-1] not in {item for items in again.values() for item in items}


def test_a_topic_with_no_eligible_item_has_r_zero_and_raises_a_generation_need(tmp_path):
    env = _env(tmp_path)
    los = list(OI.population(env.vault, env.repository, env.now_iso()))
    eligible = {lo: [] for lo in los}
    eligible[los[0]] = ["x"]
    record = C.draw_day(env.vault, env.repository, local_date="2026-01-01", now_iso=env.now_iso(),
                        topics={lo: 1 / 90 for lo in los}, eligible_items=lambda _los, _ex: eligible)
    assert record["r"][los[0]] == pytest.approx(1.0)
    assert all(record["r"][lo] == 0.0 for lo in los[1:])
    assert set(record["generation_needs"]) == set(los[1:])
    needs = env.repository.pending_intervention_needs(None)
    assert {need["learning_object_id"] for need in needs if need["trigger_reason"] == C.NEED_TRIGGER} == set(los[1:])
    # Once a day: the same record again, and no second set of rows.
    again = C.draw_day(env.vault, env.repository, local_date="2026-01-01", now_iso=env.now_iso(),
                       topics={lo: 1 / 90 for lo in los}, eligible_items=lambda _los, _ex: {})
    assert again == record and len([r for r in _check_rows(env) if r["unit_id"].startswith("check-day:2026-01-01")]) == 2


def test_off_draws_nothing_and_a_day_with_no_session_counts_toward_the_completion_gap(tmp_path):
    off = _env(tmp_path / "off", toml=CHECKS_ONLY + "check_rate = \"off\"\n")
    run(off)
    assert _check_rows(off) == []
    env = _env(tmp_path / "on")
    los = list(OI.population(env.vault, env.repository, env.now_iso()))
    C.draw_day(env.vault, env.repository, local_date="2026-01-01", now_iso=env.now_iso(),
               topics={lo: 1 / 90 for lo in los}, eligible_items=lambda _los, _ex: {lo: ["x"] for lo in los})
    with env.repository.connection() as connection:
        gap = C.completion(connection, through="2026-01-05")
        resolved = C.resolve(connection, through="2026-01-05")
    assert gap["days_without_session"] == 3 and gap["completed"] == 0 and gap["rate"] == 0.0
    assert [entry.status for entry in resolved] == [C.NO_SESSION]
    with env.repository.connection() as connection:
        assert C.r_for(connection, local_date="2026-01-03")[1] == "last_draw_stands"


# -- the score -------------------------------------------------------------------------------------------


def _trace(*, decision_mu=None, llm=None, numeric="a", coin=None):
    return {
        "mixing": {"mu": decision_mu or {"a": 0.5, "b": 0.5}, "chosen": "a"},
        "policies": {"llm": {"distribution": llm or {"a": 0.2, "b": 0.8}}, "numeric": {"choice": numeric}},
        "evaluation": {"window_days": 2, "c0": 0.0, "uses": {"topics": [{"lo": "L", "c": 0.5, "m0": [0.4, 0.4]}],
                                                              "dated": []}},
        **({"stop_coin": coin} if coin else {}),
    }


def _row():
    return {"decision_id": "d1", "created_at": "2026-01-01T10:00:00Z", "window_closes_at": "2026-01-03T10:00:00Z",
            "local_date": "2026-01-01", "llm_status": "answered", "numeric_status": "answered", "kappa0": 0.0,
            "remembered_minutes": 10.0}


class _NoConnection:
    def execute(self, *_args, **_kwargs):
        return []


def test_a_closed_window_scores_from_a_completed_check_with_r_from_the_assignment_and_completion():
    done = C.Resolved(assignment_id="as1", local_date="2026-01-02", topic="L", r=0.25, status="completed",
                      outcome=1.0, attempt_id="att1")
    detail = S.score_decision(_NoConnection(), _row(), _trace(), resolved={("2026-01-02", "L"): done},
                              completion_rate=0.5, r_lookup=lambda day: {"L": 0.25}, prices={}, gap_minutes=60)
    # d(a) = 0.2 - 1 = -0.8; μ(a) = 0.5; one observed use: 0.5 · (1/(0.25·0.5)) · (1 - 0.4).
    expected = (-0.8 / 0.5) * (0.5 * (1 / 0.125) * (1.0 - 0.4))
    assert detail.scored.value == pytest.approx(expected) and detail.assessments == ("att1",)
    assert detail.uses_with_r == 2 and detail.observed == 1


def test_a_coin_forced_decision_a_fallback_and_agreement_carry_no_score():
    kwargs = dict(resolved={}, completion_rate=0.5, r_lookup=lambda day: {"L": 0.25}, prices={}, gap_minutes=60)
    forced = S.score_decision(_NoConnection(), _row(), _trace(coin={"arm": "offer_stop"}), **kwargs)
    assert forced.scored.reason == "stop_coin_forced"
    fell = S.score_decision(_NoConnection(), {**_row(), "llm_status": "timeout"}, _trace(), **kwargs)
    assert fell.scored.reason == W.FALLBACK
    agree = S.score_decision(_NoConnection(), _row(), _trace(llm={"a": 1.0, "b": 0.0}), **kwargs)
    assert agree.scored.reason == W.AGREE
    nothing = S.score_decision(_NoConnection(), _row(), _trace(), resolved={}, completion_rate=0.5,
                               r_lookup=lambda day: {}, prices={}, gap_minutes=60)
    assert nothing.scored.reason == W.NO_RANDOMIZED_USE


def test_the_score_is_unbiased_for_a_planted_delta_on_a_synthetic_log():
    """Monte Carlo: actions drawn from μ, checks assigned at r and completed at the completion rate, outcomes from
    the action's true effect; the mean score recovers Δ = Σ_a d(a)·value(a)."""

    import random

    rng = random.Random(3)
    mu = {"a": 0.3, "b": 0.7}
    llm = {"a": 0.9, "b": 0.1}
    effect = {"a": 0.7, "b": 0.5}
    d = {"a": 0.9 - 1.0, "b": 0.1}
    c = 0.5
    r_assign, completion = 0.25, 0.8
    truth = sum(d[a] * c * 2 * (effect[a] - 0.4) for a in mu)
    total, n = 0.0, 40_000
    for i in range(n):
        action = "a" if rng.random() < mu["a"] else "b"
        resolved = {}
        for day in ("2026-01-02", "2026-01-03"):
            if rng.random() < r_assign and rng.random() < completion:
                outcome = 1.0 if rng.random() < effect[action] else 0.0
                resolved[(day, "L")] = C.Resolved(assignment_id=f"x{i}{day}", local_date=day, topic="L", r=r_assign,
                                                  status="completed", outcome=outcome)
        trace = _trace(decision_mu=mu, llm=llm, numeric="a")
        trace["mixing"]["chosen"] = action
        detail = S.score_decision(_NoConnection(), _row(), trace, resolved=resolved, completion_rate=completion,
                                  r_lookup=lambda day: {"L": r_assign}, prices={}, gap_minutes=60)
        total += detail.scored.value
    assert total / n == pytest.approx(truth, abs=0.04)


def test_w_moves_off_its_prior_on_closed_scores_in_two_bins():
    import random

    rng = random.Random(5)
    seeds = W.Seeds()
    scored = [W.Scored(decision_id=f"d{i}", decided_at=f"2026-0{1 + i // 30}-{1 + i % 28:02d}T10:00:00Z",
                       window_closes_at="2026-01-15T10:00:00Z", value=-0.05 + rng.gauss(0, 0.01)) for i in range(60)]
    posterior = W.posterior(scored, seeds, at="2026-06-01T00:00:00Z")
    assert posterior.source == "posterior" and W.weight(posterior.p, seeds) < seeds.w0
