"""Daily-loop DL1 and replay (L4, L5): the plan is workflow, never evidence.

Rebuild makes zero model calls with plan tables populated, never touches plan
rows, and reproduces the same derived state whether or not a plan ran. In the
durability lane this runs on a fresh vault with production pragmas (WAL).
"""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
import learnloop.clock as clock_module
from tests.daily_plan_fakes import NOW, MovableClock, make_env, record_attempt
from tests.split_live_helpers import enable_embeddings
from tests.test_daily_plan_build import _seed_wide, _wide_items, _wide_vault

PLAN_TABLES = ("daily_plans",)


def _rows(path, tables):
    with sqlite3.connect(path) as connection:
        return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')) for table in tables}


def _plan_rows(path):
    rows = _rows(path, PLAN_TABLES)
    with sqlite3.connect(path) as connection:
        rows["blocks"] = sorted(tuple(r) for r in connection.execute("SELECT * FROM attention_blocks WHERE daily_plan_id IS NOT NULL"))
        rows["events"] = sorted(
            tuple(r)
            for r in connection.execute(
                "SELECT e.* FROM attention_block_events e JOIN attention_blocks b ON b.id = e.block_id WHERE b.daily_plan_id IS NOT NULL"
            )
        )
    return rows


@pytest.mark.durability
def test_rebuild_ignores_the_plan_and_calls_no_model(tmp_path, monkeypatch):
    from learnloop.ai import client
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

    def forbidden(*args, **kwargs):
        raise AssertionError("the plan and replay must not construct a model or embedding client")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    # No provider client of any kind, chat or embedding, is even resolved (G8).
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr("learnloop.diagnosis.split.jobs.default_embedding_client", forbidden)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "__init__", forbidden)
    # Rebuild stamps some derived rows with the wall clock: freeze it so the
    # comparison is about content.
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: NOW)
    paths = _wide_vault(tmp_path)
    # Embeddings on, so an embedding call anywhere in the plan or replay
    # would reach the guards above.
    enable_embeddings(paths.root)
    clock = MovableClock()
    env = make_env(paths.root, _wide_items(), clock=clock)
    _seed_wide(env.repository)
    derived = sorted(tables_for_role(TableRole.DERIVED))
    rebuild_all_derived_state(load_vault(paths.root), env.repository)
    rebuild_all_derived_state(load_vault(paths.root), env.repository)
    before_derived = _rows(paths.sqlite_path, derived)

    build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    for _ in range(3):
        record, step = advance(env, serve=False)
        if step["kind"] != "item":
            break
        advance(env, serve=False, skip_practice_item_id=step["practice_item_id"])
    plan_rows = _plan_rows(paths.sqlite_path)
    assert plan_rows["daily_plans"] and plan_rows["blocks"] and plan_rows["events"]

    for _ in range(2):
        rebuild_all_derived_state(load_vault(paths.root), env.repository)
    # Rebuild never touches the plan, and the plan never reaches derived state.
    assert _plan_rows(paths.sqlite_path) == plan_rows
    assert _rows(paths.sqlite_path, derived) == before_derived


@pytest.mark.durability
def test_a_plan_runs_on_a_fresh_wal_vault(tmp_path):
    paths = _wide_vault(tmp_path)
    clock = MovableClock()
    env = make_env(paths.root, _wide_items(), clock=clock)
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    record, step = advance(env, serve=False)
    clock.advance(2)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now())
    record, _next = advance(env, serve=False)
    assert any(item.done for item in record.items())
    with sqlite3.connect(paths.sqlite_path) as connection:
        # The durability marker builds this vault fresh with production
        # pragmas: the plan ran on a WAL database (review F10).
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
