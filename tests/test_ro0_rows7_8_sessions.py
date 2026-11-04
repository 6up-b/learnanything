"""RO0 rows 7 and 8 (spec_router_objective_v1 §4): availability before a session, and how it ended."""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.daily_plan.engine import advance, build_plan, keep_going, stop_today
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import sessions as S
from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import append_config_toml, create_basic_vault
from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import fake_runtime

OFF = "[router_objective]\nreceipts = false\n"


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, *, config: str = ""):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    return ctx


def _rows(repository, kind=None):
    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM session_receipts ORDER BY created_at, id")]
    return [row for row in rows if kind is None or row["kind"] == kind]


def test_availability_is_stamped_before_the_first_block(tmp_path):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()
    session = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    [row] = _rows(repository, S.AVAILABILITY)
    assert (row["session_id"], row["minutes_offered"], row["minutes_source"]) == (session, 25.0, "session_start")
    assert row["device"] == "desktop" and row["local_time"] and row["time_zone"] and row["utc_offset_minutes"] is not None
    assert row["external_window_json"] is None, "the m1nty bridge's field, nullable: no integration exists"


def test_missing_is_recorded_as_missing(tmp_path):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()
    _call(ctx, "start_session", {})
    [row] = _rows(repository, S.AVAILABILITY)
    assert row["minutes_offered"] is None and row["minutes_source"] == S.MISSING


def test_todays_plan_is_the_source_when_the_client_says_nothing(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert S.record_availability(env.vault, env.repository, "s1", clock=env.clock)
    assert not S.record_availability(env.vault, env.repository, "s1", clock=env.clock), "once per session"
    [row] = _rows(env.repository, S.AVAILABILITY)
    assert (row["minutes_offered"], row["minutes_source"]) == (25.0, "plan:chip") and row["plan_id"]


def test_a_stop_after_a_finished_plan_accepts_the_offer(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=6.0, remembered=6, minutes_source="chip")
    record = run(env)
    assert record.status == "complete"
    assert S.record_end(env.vault, env.repository, "s1", ended_at="t", clock=env.clock)
    [row] = _rows(env.repository, S.END)
    assert (row["end_reason"], row["end_basis"], row["ended_at"]) == (S.OFFERED_STOP_ACCEPTED, S.EXPLICIT, "t")
    assert row["plan_id"] == record.id and row["block_id"] is not None
    assert row["stop_decision_id"] is not None, "the stop decision in force"


def test_stopping_an_open_plan_is_unprompted(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=True)
    stop_today(env)
    S.record_end(env.vault, env.repository, "s1", clock=env.clock)
    [row] = _rows(env.repository, S.END)
    assert row["end_reason"] == S.UNPROMPTED_STOP and row["end_basis"] == S.EXPLICIT


def test_going_on_past_a_finished_plan_overrides_the_offer_and_is_no_end(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=6.0, remembered=6, minutes_source="chip")
    record = run(env)
    keep_going(env)
    [row] = _rows(env.repository, S.STOP_RESPONSE)
    assert (row["end_reason"], row["end_basis"], row["plan_id"]) == (S.OFFERED_STOP_OVERRIDDEN, S.EXPLICIT, record.id)
    assert row["stop_decision_id"] is not None
    assert _rows(env.repository, S.END) == []


def test_a_clients_word_stands_when_it_is_one_of_ours(tmp_path):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()
    first = _call(ctx, "start_session", {})["sessionId"]
    _call(ctx, "end_session", {"sessionId": first, "endReason": "foreground_lost"})
    second = _call(ctx, "start_session", {})["sessionId"]
    _call(ctx, "end_session", {"sessionId": second, "endReason": "made_up"})
    rows = {row["session_id"]: row for row in _rows(repository, S.END)}
    assert rows[first]["end_reason"] == S.FOREGROUND_LOST
    assert rows[second]["end_reason"] == S.UNPROMPTED_STOP
    # Ending an ended session writes nothing.
    _call(ctx, "end_session", {"sessionId": first})
    assert len(_rows(repository, S.END)) == 2


def test_a_crash_is_inferred_at_recovery_and_marked_inferred(tmp_path):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()
    crashed = _call(ctx, "start_session", {})["sessionId"]
    assert _rows(repository, S.END) == [], "still open: it can be resumed"
    # The process died; the next start ends the stale session at its last activity, and nobody reported it.
    following = _call(ctx, "start_session", {})["sessionId"]
    [row] = _rows(repository, S.END)
    assert (row["session_id"], row["end_reason"], row["end_basis"]) == (crashed, S.APP_CLOSED, S.INFERRED)
    assert row["ended_at"]
    assert '"recovered_by":"start_session"' in row["detail_json"]
    assert {row["session_id"] for row in _rows(repository, S.AVAILABILITY)} == {crashed, following}


def test_a_session_from_before_ro0_is_not_backfilled(tmp_path):
    ctx = _sidecar(tmp_path)
    vault, repository = ctx.require_vault()
    old = repository.create_session()
    repository.end_session(old)
    assert S.sweep_unreported(vault, repository, trigger="test") == 0


def test_off_nothing_is_written(tmp_path):
    ctx = _sidecar(tmp_path, config=OFF)
    _vault, repository = ctx.require_vault()
    first = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _call(ctx, "end_session", {"sessionId": first})
    second = _call(ctx, "start_session", {})["sessionId"]
    assert second and _rows(repository) == []


def test_a_refused_receipt_rolls_back_alone_and_the_session_stands(tmp_path, monkeypatch):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()

    def refused(*_args, **_kwargs):
        raise sqlite3.OperationalError("refused")

    monkeypatch.setattr(store, "insert_session_receipt", refused)
    session = _call(ctx, "start_session", {})["sessionId"]
    assert _call(ctx, "end_session", {"sessionId": session})
    monkeypatch.undo()
    assert _rows(repository) == []


def test_the_store_rolls_back_a_refused_row_alone(tmp_path):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()
    with repository.atomic(), repository.connection() as connection:
        connection.execute("UPDATE sessions SET updated_at = 'marker' WHERE 1 = 0")
        # CHECK fails (an availability row with no source): refused alone, the transaction goes on.
        assert store.insert_session_receipt(connection, {"id": "x", "session_id": "s", "kind": "availability",
                                                         "receipt_version": "v", "created_at": "t", "detail_json": "{}"}) is False
    assert _rows(repository) == []


@pytest.mark.parametrize("table", ["session_receipts"])
def test_a_receipt_is_immutable(tmp_path, table):
    ctx = _sidecar(tmp_path)
    _vault, repository = ctx.require_vault()
    _call(ctx, "start_session", {})
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE {table} SET device = 'x'")
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"DELETE FROM {table}")
        connection.rollback()
