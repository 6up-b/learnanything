"""RO0 row 12 (spec_router_objective_v1 §4): decision-to-next-state links, a plain read where the ids exist."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.router_objective import trajectory as T
from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import fake_runtime


def _links(env):
    with env.repository.connection() as connection:
        return T.rows(connection)


def test_a_decision_links_to_its_action_uptake_and_the_next_decision(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    run(env, steps=3)
    links = _links(env)
    assert len(links) >= 2
    first, second = links[0], links[1]
    assert first["block_id"] and first["presentations"] >= 1 and first["first_served_at"]
    assert first["attempts_on_presentations"] >= 0 and first["objective_arm"] in (None, "practice", "reading", "stop", "wait", "insert")
    assert first["next_decision_id"] == second["decision_id"] and first["next_decision_censored"] is None
    assert links[-1]["next_decision_id"] is None and links[-1]["next_decision_censored"] == "no_later_decision"


def test_uptake_and_rejection_are_counted(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _record, step = advance(env, serve=True)
    with env.repository.atomic(), env.repository.connection() as connection:
        served = connection.execute("SELECT id FROM plan_presentations WHERE practice_item_id = ?",
                                    (step["practice_item_id"],)).fetchone()[0]
    attempt = record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                             session_id=env.session_id)
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET plan_presentation_id = ? WHERE id = ?", (served, attempt))
    assert _links(env)[0]["attempts_on_presentations"] == 1
    advance(env, serve=False, skip_practice_item_id=step["practice_item_id"])
    assert _links(env)[0]["items_rejected"] == 0, "an answered item is no rejection"


def test_return_time_is_the_next_session_and_censored_until_there_is_one(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), session_id=None)
    env.session_id = env.repository.create_session(clock=env.clock)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    links = _links(env)
    assert links[0]["return_censored"] == "no_later_session" and links[0]["next_session_started_at"] is None
    env.clock.advance(60)
    env.repository.create_session(clock=env.clock)
    links = _links(env)
    assert links[0]["next_session_started_at"] and links[0]["return_censored"] is None


def test_a_view_would_break_the_rebuild_the_ledgers_migrations_use(tmp_path):
    """Why row 12 is a read: SQLite re-resolves views when a table is renamed."""

    with closing(sqlite3.connect(tmp_path / "x.sqlite")) as connection:
        connection.execute("CREATE TABLE router_decisions(id TEXT)")
        connection.execute("CREATE VIEW trajectory AS SELECT id FROM router_decisions")
        connection.execute("CREATE TABLE router_decisions__new(id TEXT)")
        connection.execute("DROP TABLE router_decisions")
        with pytest.raises(sqlite3.OperationalError, match="view trajectory"):
            connection.execute("ALTER TABLE router_decisions__new RENAME TO router_decisions")


def test_the_read_runs_on_the_head_schema(tmp_path):
    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_250" / "state.sqlite"
    with closing(sqlite3.connect(head)) as connection:
        connection.row_factory = sqlite3.Row
        assert isinstance(T.rows(connection), list)
