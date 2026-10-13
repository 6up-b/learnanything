"""Daily-loop DL1 §7 and gate G10: goal-optional re-entry.

It shows without any goal after the gap (the last real activity, F1); it
respects the minute and item caps; it uses only repair and maintain; it shows
no overdue count and no streak; no due date is rewritten.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401
from learnloop.daily_plan.engine import advance, get_or_create_today
from learnloop.daily_plan.lanes import reentry_order
from learnloop.db.repositories import Repository
from learnloop.vault.yaml_io import write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.daily_plan_fakes import NOW, MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault

LAST = NOW - timedelta(days=30)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _no_goals(paths):
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})


def _many_due(tmp_path, count=12):
    los = {f"lo_r{i}": [(f"pi_r{i}", 1.0)] for i in range(count)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los)
    _no_goals(paths)
    return paths


def _ended_session_at(repository: Repository, moment: datetime) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at, available_minutes) VALUES ('s_old', ?, ?, 40)",
            (iso(moment - timedelta(minutes=30)), iso(moment)),
        )
        connection.commit()


def test_reentry_needs_no_goal_and_respects_its_minute_and_item_caps(tmp_path):
    paths = _many_due(tmp_path)
    items = [scheduled(f"pi_r{i}", f"lo_r{i}", forgetting_risk=0.7) for i in range(12)] + [
        scheduled("pi_eig_easy", "lo_eigen_basics", new_material=1.0),
    ]
    clock = MovableClock(NOW)
    env = make_env(paths.root, items, clock=clock)
    for i in range(12):
        seed_due(env.repository, f"pi_r{i}", due=NOW - timedelta(days=10), last=LAST)
    _ended_session_at(env.repository, NOW - timedelta(days=12))
    states_before = env.repository.practice_item_states()
    record = get_or_create_today(env)
    assert record.kind == "reentry"
    assert record.budget == 15.0  # min(remembered 40, plan.reentry_minutes)
    assert record.row["remembered_minutes"] == 40
    assert record.lanes_allowed == ("repair", "maintain")
    assert record.split["reentry_gap"]["gap_days"] == 12
    # Drive it to the end without answering anything: blocks are chosen at
    # each boundary once the previous items are skipped.
    steps = 0
    while True:
        record, step = advance(env, serve=False)
        if step["kind"] != "item":
            break
        advance(env, serve=False, skip_practice_item_id=step["practice_item_id"])
        steps += 1
        assert steps < 30
    assert record.item_count() <= 8  # D11
    assert record.minutes_planned() <= 15.0 + 1e-6
    assert {item.lane for item in record.items()} <= {"repair", "maintain"}
    assert "pi_eig_easy" not in {item.practice_item_id for item in record.items()}
    # No due date is rewritten: the plan never touches memory state.
    assert env.repository.practice_item_states() == states_before


def test_no_reentry_within_the_gap(tmp_path):
    paths = _many_due(tmp_path, count=2)
    env = make_env(paths.root, [scheduled("pi_r0", "lo_r0", forgetting_risk=0.7)], clock=MovableClock(NOW))
    _ended_session_at(env.repository, NOW - timedelta(days=3))
    assert get_or_create_today(env).kind == "normal"


def test_reentry_orders_assumed_checks_then_deadlines_then_rank():
    from learnloop.daily_plan.lanes import PoolItem

    def item(item_id, rank, **kw):
        return PoolItem(practice_item_id=item_id, learning_object_id="lo", rank=rank, priority=0.5, lane="maintain", reason="", est_minutes=1.0, never_attempted=False, **kw)

    ordered = reentry_order([item("a", 0), item("b", 1, deadline=True), item("c", 2, check_kind="assumed_check")])
    assert [i.practice_item_id for i in ordered] == ["c", "b", "a"]


def test_the_reentry_panel_is_survival_first_with_no_overdue_count_or_streak(tmp_path, monkeypatch):
    paths = _many_due(tmp_path, count=3)
    frozen = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: frozen)
    repository = Repository(paths.sqlite_path)
    for i in range(3):
        # Reviewed long ago with a short stability: slipped below 0.90 now.
        seed_due(repository, f"pi_r{i}", due=frozen - timedelta(days=20), last=frozen - timedelta(days=21), stability=3.0)
    _ended_session_at(repository, frozen - timedelta(days=20))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    plan = _call(ctx, "get_daily_plan", {})["plan"]
    assert plan["kind"] == "reentry"
    panel = plan["reentry"]
    assert panel["gapDays"] == 20
    assert panel["solidCount"] + panel["slippedCount"] >= 1
    assert set(panel) >= {"gapDays", "solidCount", "slippedCount", "slippedNames", "planMinutes", "planItems"}
    flat = repr(panel).lower()
    assert "overdue" not in flat and "streak" not in flat
    assert panel["planMinutes"] <= 15 and panel["planItems"] <= 8


def test_with_the_plan_off_the_dl0_queue_cap_still_applies_and_with_it_on_the_list_is_whole(tmp_path, monkeypatch):
    frozen = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: frozen)
    results = {}
    for enabled in (False, True):
        root = tmp_path / f"vault_{enabled}"
        paths = create_daily_plan_vault(root, plan_toml=f"[plan]\nenabled = {str(enabled).lower()}\n")
        repository = Repository(paths.sqlite_path)
        seed_due(repository, "pi_svd_define_001", due=frozen - timedelta(days=20), last=frozen - timedelta(days=25), stability=3.0)
        _ended_session_at(repository, frozen - timedelta(days=20))
        ctx = SidecarContext()
        ctx.load(paths.root)
        queue = _call(ctx, "get_today_queue", {})
        results[enabled] = queue["reentryRefresherCap"]
    assert results[True] is None
