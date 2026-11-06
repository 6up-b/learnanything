"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the offer's value and its sensors. Pure numerics; fakes only.

* the offer's branches against a hand-computed case for a lesson (``Q = p·Q_acc + (1 − p)·Q_dec`` per draw, the
  accepted branch the lesson action at its mass, ``κ0/(2m̄)·p(1−p)d²``); the eve-of-exam regression unchanged with a
  lesson offer beside the blocks; a committed delayed check entering ``E[V(x′)]`` and no commitment changing nothing;
* the acceptance model's posterior predictive moment-matched to a Beta; the lesson's duration from its seed and the
  lessons' own active minutes.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION, LESSON_OPPORTUNITY_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_offer as LO
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import price as P
from learnloop.router_objective import value as V

from tests.test_ro4_value import EXACT, FIXED, _inputs, _logit

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION


# --- the value --------------------------------------------------------------------------------------------


def test_offer_branches_match_a_hand_computed_case_for_a_lesson():
    """A lesson offer: ``Q = p·E[R+V | accepted] + (1−p)·E[R+V | declined]`` per draw, the accepted branch the
    lesson action itself (its learning at the mass on ``γ``), its κ integral ``p·κ0·((m+d)² − m²)/(2m̄)``."""

    p, d, m, mass = 0.3, 10.0, 10.0, 0.5
    gamma = 0.4
    inputs = _inputs(session_minutes=m, horizon_days=1.0,
                     topics=(V.Topic(lo="lo_a", eta_mean=_logit(0.6), eta_var=0.0, undated_density=1 / 90),),
                     learning=V.Learning(gamma=(gamma, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))
    offer = V.Action(ref="offer", kind=V.LESSON, item_los=("lo_a",), minutes=d, mass=mass,
                     accept=(p * 1e6, (1 - p) * 1e6))
    taken = V.Action(ref="taken", kind=V.LESSON, item_los=("lo_a",), minutes=d, mass=mass)
    out = V.evaluate(inputs, [offer, taken], draws=4, seed="lesson-offer").by_ref()
    branches = out["offer"].extra["branches"]
    assert branches["accepted"] == pytest.approx(out["taken"].q)
    p_bar = branches["p_accept"]
    assert p_bar == pytest.approx(p, abs=1e-3)
    assert out["offer"].q == pytest.approx(p_bar * out["taken"].q + (1 - p_bar) * branches["declined"], rel=1e-6)
    k0, mbar = inputs.price.kappa0, inputs.price.remembered
    assert out["offer"].terms["kappa_integral"] == pytest.approx(p_bar * k0 * ((m + d) ** 2 - m ** 2) / (2 * mbar),
                                                                 rel=1e-6)
    terms = out["offer"].extra["branch_terms"]
    assert terms["accepted"]["kappa_integral"] == pytest.approx(k0 * ((m + d) ** 2 - m ** 2) / (2 * mbar))
    # The declined branch at the remembered minutes ends the session: no block of its own to cost.
    assert terms["declined"]["kappa_integral"] == pytest.approx(0.0)
    expected_cost = p * k0 * ((m + d) ** 2 - m ** 2) / (2 * mbar)
    at_mean = k0 * ((m + p * d) ** 2 - m ** 2) / (2 * mbar)
    assert expected_cost - at_mean == pytest.approx(k0 / (2 * mbar) * p * (1 - p) * d ** 2)
    # The lesson's learning: γ at the mass, on the logit, one step (the accepted state's undated uses).
    assert out["taken"].q > out["offer"].extra["branches"]["declined"] - 1.0  # sanity: finite, comparable


def test_the_eve_of_exam_regression_holds_with_a_lesson_offer_beside_the_block():
    gamma = _logit(0.79) - _logit(0.78)
    inputs = _inputs(dated=(V.DatedUse(goal_id="exam", lo="lo_a", at_days=1.0, weight=1.0),),
                     learning=V.Learning(gamma=(gamma, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))
    block = V.Action(ref="cram", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=10.0)
    stop = V.Action(ref="stop_for_today", kind=V.STOP)
    offer = V.Action(ref="lesson_offer:lo_a", kind=V.LESSON, item_los=("lo_a",), minutes=15.0, mass=0.5,
                     accept=(2.0, 3.0), commitments=(("lo_a", 3.0),))
    out = V.evaluate(inputs, [block, offer, stop], draws=4, seed="eve").by_ref()
    assert out["cram"].terms["kappa_integral"] == pytest.approx(0.02)
    assert out["stop_for_today"].q - out["stop_for_today"].terms["terminal"] == pytest.approx(0.780, abs=1e-9)
    assert out["cram"].q - out["cram"].terms["terminal"] == pytest.approx(0.770, abs=1e-9)
    assert out["cram"].q - out["stop_for_today"].q == pytest.approx(-0.010, abs=1e-9)


def test_a_committed_delayed_check_enters_the_value_and_none_changes_nothing():
    topics = (V.Topic(lo="lo_a", eta_mean=_logit(0.5), eta_var=1.0, undated_density=1 / 30),
              V.Topic(lo="lo_b", eta_mean=_logit(0.5), eta_var=1.0, undated_density=1 / 30))
    inputs = _inputs(topics=topics, horizon_days=10.0, session_minutes=0.0, combiner=EXACT,
                     learning=V.Learning(gamma=(0.3, 0.0), gbar=((0.0, 0.0), (0.0, 0.0))))
    plain = V.Action(ref="plain", kind=V.LESSON, item_los=("lo_a",), minutes=15.0, mass=0.5)
    checked = V.Action(ref="checked", kind=V.LESSON, item_los=("lo_a",), minutes=15.0, mass=0.5,
                       commitments=(("lo_a", 3.0),))
    out = V.evaluate(inputs, [plain, checked], draws=8, seed="commit").by_ref()
    assert out["plain"].q_draws != out["checked"].q_draws  # the check's practice and observation moved the path
    # With no commitment the action is valued exactly as before (the stream exists but is never read).
    again = V.evaluate(inputs, [plain], draws=8, seed="commit").by_ref()
    assert again["plain"].q_draws == out["plain"].q_draws


# --- the sensors --------------------------------------------------------------------------------------------


def test_the_acceptance_posterior_is_moment_matched_to_a_beta():
    state = LS.AcceptanceState()
    context = LS.Context(local_hour=10.0, minutes_left=20.0, reentry=False, days_since_last=None)
    candidate = LS.Candidate(ref="lesson:lo", learning_object_ids=("lo",), reason="new_goal", predicted_success=0.3)
    mean, sd = LO.accept_moments(state, context, candidate)
    assert mean == pytest.approx(state.p_accept(context, candidate), abs=1e-9)
    assert 0.0 < sd < math.sqrt(mean * (1 - mean))
    a, b = LO.beta_from_moments(mean, sd)
    assert a / (a + b) == pytest.approx(mean)
    assert math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1))) == pytest.approx(sd)


def _lesson_db(tmp_path):
    import sqlite3

    connection = sqlite3.connect(str(tmp_path / "lessons.sqlite"))
    connection.executescript(
        "CREATE TABLE lessons (id TEXT PRIMARY KEY, opened_at TEXT, closed_at TEXT);"
        "CREATE TABLE lesson_activity_intervals (id TEXT, lesson_id TEXT, screen_session TEXT, seq INTEGER, "
        "started_at TEXT, ended_at TEXT, seconds REAL, foreground INTEGER);"
        "CREATE TABLE practice_attempts (id TEXT, created_at TEXT, latency_seconds REAL);"
        "CREATE TABLE interaction_events (kind TEXT, occurred_at TEXT, created_at TEXT, payload_json TEXT);")
    return connection


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


T0 = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)


def _lesson(connection, lesson_id: str, start: datetime, active_minutes: list[tuple[float, float]], *,
            closed: bool = True) -> None:
    """A lesson with foreground intervals ``(offset, length)`` in minutes from ``start``."""

    end = start + timedelta(minutes=max(o + n for o, n in active_minutes) + 1)
    connection.execute("INSERT INTO lessons VALUES (?, ?, ?)", (lesson_id, _stamp(start),
                                                                _stamp(end) if closed else None))
    for seq, (offset, length) in enumerate(active_minutes, start=1):
        began = start + timedelta(minutes=offset)
        connection.execute("INSERT INTO lesson_activity_intervals VALUES (?, ?, 's', ?, ?, ?, ?, 1)",
                           (f"{lesson_id}:{seq}", lesson_id, seq, _stamp(began),
                            _stamp(began + timedelta(minutes=length)), length * 60.0))


def test_the_lessons_duration_starts_at_the_seed_and_learns_from_active_minutes(tmp_path):
    connection = _lesson_db(tmp_path)
    seeded = LO.duration_model(connection, at=_stamp(T0))
    assert seeded["source"] == "seed" and seeded["median_minutes"] == pytest.approx(15.0)
    assert seeded["log_sd"] == pytest.approx(math.sqrt(LO.DURATION_LOG_SD ** 2 + LO.DURATION_MEDIAN_PRIOR_SD ** 2))
    # Two lessons of 40 active minutes each (overlapping intervals counted once): the median moves toward 40.
    _lesson(connection, "les_a", T0 - timedelta(days=2), [(0, 25), (20, 20)])
    _lesson(connection, "les_b", T0 - timedelta(days=1), [(0, 40)])
    fitted = LO.duration_model(connection, at=_stamp(T0))
    assert LO.lesson_active_minutes(connection, at=_stamp(T0)) == pytest.approx([40.0, 40.0])
    assert fitted["source"] == "fitted, n=2" and 15.0 < fitted["median_minutes"] < 40.0
    precision = 1 / LO.DURATION_MEDIAN_PRIOR_SD ** 2 + 2 / LO.DURATION_LOG_SD ** 2
    mean = (math.log(15.0) / LO.DURATION_MEDIAN_PRIOR_SD ** 2 + 2 * math.log(40.0) / LO.DURATION_LOG_SD ** 2) / precision
    assert fitted["median_minutes"] == pytest.approx(math.exp(mean), rel=1e-6)


