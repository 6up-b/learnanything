"""Router objective RO5, Codex re-review (job 20261105-094834-nrtIdK): each finding reproduced by a test that fails
on the pre-fix source (``059cc15325``). Fakes, in-memory SQLite and synthetic vaults only; no model is asked.

* F2 (reopened): the day's check is administered before any decision of the day, so it never depends on what a
  decision draws (a practice block, a reading, a stop).
* F3 (reopened), F9: the return model's uncertainty is the sessions' own estimating contributions; opposing coins in
  one session, or a couple of busy and free sessions, never give a certain slope.
* F8: a vanishing first stage leaves the prior; a strong instrument far from the prior keeps its resolution.
* F4 (reopened): scoring and serving build one set of sessions (a Reader interval spanning two attempts is one
  session on both clocks); the serving clock is RO4's walk-back exactly.
* F10: a completion rate read at a past date never moves with later assignments or later answers.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
import json
import math
import random
import sqlite3

import pytest

from learnloop.router_objective import assignments as A
from learnloop.router_objective import checks as C
from learnloop.router_objective import price as P
from learnloop.router_objective import scores as S
from learnloop.router_objective import stop_coin as SC

from tests.router_mixture_helpers import run
from tests.router_model_fakes import FakeLLM
from tests.ro4_objective_serving_helpers import policy_answer
from tests.ro5_checks_helpers import _env, _row, _trace, grade_checks


# -- F2 ------------------------------------------------------------------------------------------------------


def _slots(env):
    with env.repository.connection() as connection:
        return [row for row in A.rows(connection, A.CHECK) if row["unit_id"].count(":") == 2]


def _administered(env):
    with env.repository.connection() as connection:
        return C.administered(connection)


def test_f2_the_check_is_administered_before_any_decision_even_when_every_decision_stops(tmp_path, monkeypatch):
    from learnloop.daily_plan import engine

    env = _env(tmp_path)
    real = engine.decide
    seen: list[int] = []

    def stopping(record, context, policy, **kwargs):
        decision = real(record, context, policy, **kwargs)
        seen.append(len(_administered(env)))
        return replace(decision, candidate=None)  # every decision of the day draws stop

    monkeypatch.setattr(engine, "decide", stopping)
    run(env)
    slots, administered = _slots(env), _administered(env)
    assert slots, "the day's check was drawn"
    # Pre-fix: the first decision's stop closed the plan before any practice slot, so nothing was administered.
    assert all(row["id"] in administered for row in slots)
    # Already administered when the day's first decision was made: no decision's draw can change it.
    assert seen and seen[0] == len(slots)


def test_f2_the_same_assignment_administers_the_same_item_whatever_the_policies_answer(tmp_path):
    plain = _env(tmp_path / "a")
    other = _env(tmp_path / "b", llm=FakeLLM(answer=policy_answer))
    run(plain), run(other)

    def items(env):
        units = {row["id"]: row["unit_id"] for row in _slots(env)}
        return sorted((units[key], value["practice_item_id"]) for key, value in _administered(env).items())

    assert items(plain) == items(other) and items(plain)
    for env in (plain, other):
        planned = next(iter(_administered(env).values()))
        assert planned["placed"] == "before_the_boundary_decision"


# -- F3 (reopened) and F9 -------------------------------------------------------------------------------------


P_ARM = 0.05
PRIOR_VARIANCE = 0.25


def _busy_free(arms_by_session):
    """Two sessions, busy (short, long gap) and free, each with the coins named: availability residualization makes
    the coins' residuals differ within a session while the outcomes are the session's."""

    rows = []
    for (session, busy), arms in zip((("s1", True), ("s2", False)), arms_by_session, strict=True):
        z, y, offered = (-0.6, 0.8, 0.5) if busy else (0.4, -0.4, 1.5)
        for k, arm in enumerate(arms):
            weight = 1 / P_ARM if arm == SC.OFFER_STOP else (-1 / P_ARM if arm == SC.PRESENT_NEXT else 0.0)
            rows.append(SC.ReturnRow(f"{session}{k}", session, arm, weight, (0.4 * k, offered), z, y))
    return rows


def test_f9_opposing_coins_in_one_session_never_give_a_certain_slope():
    rows = _busy_free([(SC.OFFER_STOP, SC.PRESENT_NEXT, SC.POLICY)] * 2)
    fitted = SC.fit_return_slope(rows, PRIOR_VARIANCE ** 0.5)
    # Pre-fix: mean -2.0 with variance 0 (the weights' sum cancelled, the residualized moment did not).
    assert fitted.variance >= 0.9 * PRIOR_VARIANCE and abs(fitted.mean) <= 0.05
    assert fitted.source != "posterior_randomized_coin"


def test_f3_a_busy_and_a_free_session_carry_no_return_benefit():
    rows = _busy_free([(SC.OFFER_STOP,), (SC.PRESENT_NEXT,)])
    fitted = SC.fit_return_slope(rows, PRIOR_VARIANCE ** 0.5)
    # Two sessions determine nothing about the slope: the confounded -1.2 never appears, nor certainty.
    assert fitted.variance >= 0.9 * PRIOR_VARIANCE and abs(fitted.mean) <= 0.05


def test_f9_a_few_sessions_never_make_the_slope_certain():
    rng = random.Random(9)
    for _case in range(60):
        rows = []
        for s in range(rng.randint(3, 6)):
            busy = rng.random() < 0.5
            z = (-0.6 if busy else 0.4) + rng.gauss(0, 0.1)
            y = (0.8 if busy else -0.4) + rng.gauss(0, 0.1)
            for k in range(rng.randint(1, 3)):
                arm = rng.choice((SC.OFFER_STOP, SC.PRESENT_NEXT, SC.POLICY))
                weight = 1 / P_ARM if arm == SC.OFFER_STOP else (-1 / P_ARM if arm == SC.PRESENT_NEXT else 0.0)
                rows.append(SC.ReturnRow(f"{s}{k}", f"s{s}", arm, weight, (0.4 * k, 0.5 if busy else 1.5), z, y))
        fitted = SC.fit_return_slope(rows, PRIOR_VARIANCE ** 0.5)
        # The statistic is bounded by the sessions: six can move the prior, never collapse it.
        assert fitted.variance >= 0.02 * PRIOR_VARIANCE, (fitted, len({r.session_id for r in rows}))


# -- F8 ------------------------------------------------------------------------------------------------------


def test_f8_a_vanishing_first_stage_leaves_the_prior_never_an_extreme_certain_slope():
    rng = random.Random(1)
    rows = []
    for i in range(100):
        u = rng.random()
        arm = SC.OFFER_STOP if u < 0.3 else (SC.PRESENT_NEXT if u < 0.6 else SC.POLICY)
        weight = 1 / 0.3 if arm == SC.OFFER_STOP else (-1 / 0.3 if arm == SC.PRESENT_NEXT else 0.0)
        z = 0.1 + (1e-6 if arm == SC.OFFER_STOP else 0.0)  # the offer barely moves the minutes
        rows.append(SC.ReturnRow(f"d{i}", f"s{i}", arm, weight, (1.0, 1.0), z, rng.gauss(0, 1)))
    fitted = SC.fit_return_slope(rows, PRIOR_VARIANCE ** 0.5)
    # Pre-fix: mean -1366.99 with variance 0, as posterior_randomized_coin (it entered serving).
    assert abs(fitted.mean) <= 0.01 and fitted.variance >= 0.95 * PRIOR_VARIANCE


def test_f8_a_strong_instrument_far_from_the_prior_keeps_its_resolution():
    rng = random.Random(4)
    rows = []
    for i in range(20_000):
        u = rng.random()
        arm = SC.OFFER_STOP if u < 0.25 else (SC.PRESENT_NEXT if u < 0.5 else SC.POLICY)
        weight = 4.0 if arm == SC.OFFER_STOP else (-4.0 if arm == SC.PRESENT_NEXT else 0.0)
        z = rng.uniform(-1, 1) - (0.8 if arm == SC.OFFER_STOP else 0.0)
        rows.append(SC.ReturnRow(f"d{i}", f"s{i}", arm, weight, (0.0, 1.0), z, 1.6 * z + rng.gauss(0, 0.05)))
    fitted = SC.fit_return_slope(rows, PRIOR_VARIANCE ** 0.5)  # the truth sits 3.2 prior sds out
    assert fitted.source == "posterior_randomized_coin"
    assert fitted.mean == pytest.approx(1.6, abs=0.03) and 0 < fitted.variance < 1e-3


# -- F4 (reopened) --------------------------------------------------------------------------------------------


def _clock_db(attempts=(), reader=()):
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE practice_attempts (id TEXT, created_at TEXT, latency_seconds REAL, "
                       "attempt_type TEXT, learning_object_id TEXT, correctness REAL)")
    connection.execute("CREATE TABLE interaction_events (kind TEXT, occurred_at TEXT, created_at TEXT, "
                       "payload_json TEXT)")
    for i, (at, seconds) in enumerate(attempts):
        connection.execute("INSERT INTO practice_attempts VALUES (?, ?, ?, 'independent_attempt', 'L', 1.0)",
                           (f"a{i}", at, seconds))
    for at, active, idle in reader:
        connection.execute("INSERT INTO interaction_events VALUES ('reader_view_closed', ?, ?, ?)",
                           (at, at, json.dumps({"active_seconds": active, "idle_seconds": idle})))
    return connection


def test_f4_a_reader_interval_spanning_two_attempts_is_one_session_on_both_clocks():
    # Attempts at 09:55-10:00 and 11:15-11:20 (75 minutes apart); a Reader visit open 09:58-11:30, 20 active minutes.
    connection = _clock_db(attempts=[("2026-01-01T10:00:00Z", 300), ("2026-01-01T11:20:00Z", 300)],
                           reader=[("2026-01-01T11:30:00Z", 1200, 72 * 60)])
    minutes, start, _basis = P.session_active_minutes(connection, now="2026-01-01T11:30:00Z", gap_minutes=60)
    assert minutes == pytest.approx(30.0) and start == "2026-01-01T09:55:00Z"
    row = {**_row(), "created_at": "2026-01-01T09:00:00Z", "kappa0": 1.0, "remembered_minutes": 25.0}
    detail = S.score_decision(connection, row, _trace(), resolved={}, completion_rate=0.5,
                              r_lookup=lambda day: {"L": 0.25}, prices={}, gap_minutes=60)
    # One 30-minute session: 30²/50 = 18 (pre-fix 13: sessions of 5 and 25 minutes).
    assert detail.cost == pytest.approx(18.0)


def _walk_back(spans, *, now, gap_minutes):
    """RO4's serving clock as it was written (the walk back from ``now``), for the byte-identity check."""

    end = datetime.fromisoformat(now.replace("Z", "+00:00"))
    spans = sorted(spans, key=lambda span: span[1], reverse=True)
    gap = timedelta(minutes=float(gap_minutes))
    cursor, seconds, start = end, 0.0, None
    for began, finished, active in spans:
        if cursor - finished >= gap:
            break
        seconds += active
        cursor = min(cursor, began)
        start = began if start is None or began < start else start
    return seconds / 60.0, (start.strftime("%Y-%m-%dT%H:%M:%SZ") if start else None)


def test_f4_the_shared_construction_serves_ro4s_session_minutes_exactly():
    rng = random.Random(12)
    base = datetime(2026, 1, 1, 8, 0, 0)
    for _case in range(150):
        attempts = [((base + timedelta(minutes=rng.uniform(0, 600))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     rng.choice((0, 30, 61.7, 240, 300.25))) for _ in range(rng.randint(0, 12))]
        reader = [((base + timedelta(minutes=rng.uniform(0, 600))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   rng.uniform(1, 2400), rng.choice((0, 0, rng.uniform(0, 7200)))) for _ in range(rng.randint(0, 4))]
        connection = _clock_db(attempts, reader)
        now = (base + timedelta(minutes=rng.uniform(300, 700))).strftime("%Y-%m-%dT%H:%M:%SZ")
        gap = rng.choice((20, 60))
        since = (datetime.fromisoformat(now.replace("Z", "+00:00")) - timedelta(days=P.LOOKBACK_DAYS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        expected = _walk_back(P.activity_spans(connection, since=since, until=now), now=now, gap_minutes=gap)
        minutes, start, _basis = P.session_active_minutes(connection, now=now, gap_minutes=gap)
        assert (minutes, start) == expected  # bit for bit: the same set, the same summation order


# -- F10 -----------------------------------------------------------------------------------------------------


def _shift(day: str, days: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=days)).isoformat()


def test_f10_a_past_completion_rate_never_moves_with_a_later_assignment(tmp_path):
    env = _env(tmp_path)
    run(env)
    grade_checks(env, 1.0)
    day0 = env.today()
    through = _shift(day0, 2)  # day 1 had no session and no draw
    with env.repository.connection() as connection:
        before = C.completion(connection, through=through)
    assert before["completed"] == 1 and before["days_without_session"] == 1
    assert before["rate"] == pytest.approx(0.5)
    later = _shift(day0, 31)
    with env.repository.atomic(), env.repository.connection() as connection:
        A.insert(connection, experiment_id=A.CHECK, unit_id=C.day_unit(later), variant="day", propensity=1.0,
                 seed="s", draw=None, candidate_refs=["L"], detail={"r": {"L": 0.5}}, at=f"{later}T09:00:00Z")
        A.insert(connection, experiment_id=A.CHECK, unit_id=C.slot_unit(later, 0), variant="L", propensity=0.5,
                 seed="s", draw=0.1, candidate_refs=["L"], detail={"slot": 0, "item_id": "x"},
                 at=f"{later}T09:00:00Z")
    with env.repository.connection() as connection:
        after = C.completion(connection, through=through)
    # Pre-fix: 0.6667 (the later day halved the checks per day of the sessionless day's gap).
    assert after["rate"] == pytest.approx(before["rate"]) and after["checks_per_day"] == before["checks_per_day"]


def test_f10_an_answer_after_the_cutoff_is_not_a_completion_as_of_it(tmp_path):
    env = _env(tmp_path)
    run(env)
    grade_checks(env, 1.0)
    day0 = env.today()
    with env.repository.connection() as connection:
        entry = next(e for e in C.resolve(connection, through=_shift(day0, 1)) if e.status == C.COMPLETED)
    answered = f"{_shift(day0, 5)}T12:00:00Z"
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET created_at = ? WHERE id = ?", (answered, entry.attempt_id))
    with env.repository.connection() as connection:
        early = {e.assignment_id: e for e in C.resolve(connection, through=_shift(day0, 2))}[entry.assignment_id]
        rate_early = C.completion(connection, through=_shift(day0, 2))
        late = {e.assignment_id: e for e in C.resolve(connection, through=_shift(day0, 6))}[entry.assignment_id]
    # Pre-fix: completed as of day 2 by an answer given on day 5.
    assert early.status == C.NOT_ANSWERED and early.outcome is None and rate_early["completed"] == 0
    assert late.status == C.COMPLETED and late.outcome == 1.0
    assert not math.isnan(rate_early["rate"])


def test_f2_the_draw_is_over_what_the_days_plan_can_serve_and_a_topic_outside_it_raises_no_need(tmp_path):
    env = _env(tmp_path)
    eligible = {"L1": ["a"], "L2": ["b"], "L3": []}
    record = C.draw_day(env.vault, env.repository, local_date="2026-01-01", now_iso=env.now_iso(),
                        topics={lo: 1 / 90 for lo in eligible},
                        eligible_items=lambda los, _exclude: {lo: eligible[lo] for lo in los},
                        placeable=lambda item_id: item_id == "a")
    # Pre-fix the plan's pool was not consulted: L2's item, outside it, could be drawn and never administered.
    assert record["r"] == {"L1": 1.0, "L2": 0.0, "L3": 0.0} and record["slots"][0]["item_id"] == "a"
    assert record["eligible_outside_plan_pool"] == {"L2": 1}
    assert set(record["generation_needs"]) == {"L3"}  # L2 has an unseen item: nothing to generate
