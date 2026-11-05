"""RO4 §8.6: the attention price on session minutes, its daily seed, the floor, the guard and the grid posterior."""

from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.config.schema import LearnLoopConfig
from learnloop.router_objective import price as P


def _db(tmp_path):
    connection = sqlite3.connect(tmp_path / "s.sqlite")
    connection.execute("CREATE TABLE practice_attempts (id TEXT, created_at TEXT, latency_seconds REAL)")
    connection.execute("CREATE TABLE interaction_events (kind TEXT, occurred_at TEXT, created_at TEXT, payload_json TEXT)")
    return connection


def test_a_session_ends_after_a_gap_of_session_gap_minutes(tmp_path):
    connection = _db(tmp_path)
    # Yesterday evening (a separate session), then today: 09:00-09:10 and 09:40-09:50 (a 30-minute pause).
    for created, seconds in (("2026-11-04T20:00:00Z", 600), ("2026-11-05T09:10:00Z", 600),
                             ("2026-11-05T09:50:00Z", 600)):
        connection.execute("INSERT INTO practice_attempts VALUES ('a', ?, ?)", (created, seconds))
    connection.execute("INSERT INTO interaction_events VALUES ('reader_view_closed', '2026-11-05T09:30:00Z', "
                       "'2026-11-05T09:30:00Z', ?)", (json.dumps({"active_seconds": 300, "idle_seconds": 0}),))
    minutes, start, basis = P.session_active_minutes(connection, now="2026-11-05T09:55:00Z", gap_minutes=60)
    assert minutes == pytest.approx(25.0) and start == "2026-11-05T09:00:00Z" and basis["gap_minutes"] == 60
    # With a 12-minute gap rule the 09:00 work (15 minutes before the reading began) is another session.
    short, _start, _basis = P.session_active_minutes(connection, now="2026-11-05T09:55:00Z", gap_minutes=12)
    assert short == pytest.approx(15.0)
    # Two hours later: a new session starts at zero.
    later, none, _basis = P.session_active_minutes(connection, now="2026-11-05T12:00:00Z", gap_minutes=60)
    assert later == 0.0 and none is None


def test_the_seed_is_the_days_marginal_gain_floored_at_the_last_positive_value():
    gain = {0.0: 0.0, 20.0: 1.0, 25.0: 1.1, 40.0: 1.3}
    kappa, how = P.seed_from_gain(gain, remembered=20.0, block_minutes=5.0, last_positive=None)
    assert (kappa, how) == (pytest.approx(0.02), P.DAY_SEED)
    flat = {0.0: 0.0, 20.0: 1.0, 25.0: 1.0, 40.0: 1.0}
    assert P.seed_from_gain(flat, remembered=20.0, block_minutes=5.0, last_positive=0.015) == (0.015, P.FLOORED)
    assert P.seed_from_gain(flat, remembered=20.0, block_minutes=5.0, last_positive=None) == (
        pytest.approx(0.05), P.TAIL_AVERAGE)


def test_the_runaway_guard_is_three_remembered_minutes_unless_set():
    config = LearnLoopConfig()
    assert P.guard_minutes(config, 20.0) == 60.0
    config.router_objective.session_guard_minutes = 45.0
    assert P.guard_minutes(config, 20.0) == 45.0


def test_the_grid_posterior_is_its_prior_with_nothing_fed_and_learns_from_choices():
    prior = P.grid_posterior(0.02, [])
    assert prior["status"] == "prior" and prior["serves"] is False and prior["label"] == "preference plus model error"
    stops = [{"gain": 0.01, "block_cost_per_kappa0": 1.0, "continued": False, "scale": 0.005} for _ in range(30)]
    stopped = P.grid_posterior(0.02, stops)
    continues = [{"gain": 0.03, "block_cost_per_kappa0": 1.0, "continued": True, "scale": 0.005} for _ in range(30)]
    went_on = P.grid_posterior(0.02, continues)
    assert stopped["status"] == went_on["status"] == "posterior"
    assert went_on["mean"] < stopped["mean"]
