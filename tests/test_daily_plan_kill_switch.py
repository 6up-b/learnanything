"""Daily-loop DL1 gate G1: the plan kill switch, on fixture copies.

With ``plan.enabled = false`` (or below ``mvp-0.14``) ``get_today_queue``, Start
and Today behave exactly as the predecessor (``mvp-0.13``), including the
re-entry cap,
whatever the router does. Every row of §6.8's ``plan.enabled`` x
``router.enabled`` table has a parity test. ``router.enabled`` does not exist
on this base (router R0/R2 are unmerged), so the router rows plug a fake
router chooser into the §6.8 seam (``PlanPolicy``) exactly as R2 will.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401
from learnloop.daily_plan.engine import (
    DEFAULT_POLICY,
    PlanInactiveError,
    PlanPolicy,
    advance,
    build_plan,
    get_or_create_today,
    learner_pick,
)
from learnloop.daily_plan.types import BlockChoice, STOP_FOR_TODAY
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.owner_vaults import owner_vault, working_vault_params
from tests.daily_plan_fakes import MovableClock, make_env, record_attempt, scheduled, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault, set_algorithm_version
from tests.test_daily_plan_build import _assert_finite, _seed_wide, _wide_items, _wide_vault

# The owner's working vaults: backup-API copies in the owner_vaults lane (S0).
WORKING_FIXTURES = working_vault_params()
FROZEN = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)
_VOLATILE = {"schedulerSlateId", "schedulerCandidateId", "generatedAt"}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _served(value):
    if isinstance(value, dict):
        return {key: _served(item) for key, item in value.items() if key not in _VOLATILE}
    if isinstance(value, list):
        return [_served(item) for item in value]
    return value


def _copy(tmp_path, fixture, name, *, version, toml=None):
    root = tmp_path / name
    copy_tree_with_databases(owner_vault(fixture), root)
    set_algorithm_version(type("Paths", (), {"root": root})(), version)
    if toml:
        append_config_toml(root, toml)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx, root


def _today_reads(ctx):
    return {
        "queue": _served(_call(ctx, "get_today_queue", {})),
        "queue_25": _served(_call(ctx, "get_today_queue", {"availableMinutes": 25})),
        "start": _served(_call(ctx, "get_start_summary", {})),
    }


def _plan_rows(root):
    """Every plan row and planned block, whole: equal before and after means nothing was written."""

    repository = Repository(root / "state.sqlite") if (root / "state.sqlite").exists() else None
    with repository.connection() as connection:
        plans = [tuple(row) for row in connection.execute("SELECT * FROM daily_plans ORDER BY id")]
        blocks = [tuple(row) for row in connection.execute(
            "SELECT * FROM attention_blocks WHERE daily_plan_id IS NOT NULL ORDER BY id")]
    return plans, blocks


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_plan_off_is_dl0_on_fixture_copies(tmp_path, monkeypatch, fixture):
    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    dl0, _ = _copy(tmp_path, fixture, "dl0", version="mvp-0.13")
    off, off_root = _copy(tmp_path, fixture, "off", version="mvp-0.14", toml="[plan]\nenabled = false\n")
    baseline = _today_reads(dl0)
    assert baseline["queue"]["totalItems"] > 0
    assert _today_reads(off) == baseline
    # The plan RPCs answer "off" and write nothing (an owner copy keeps the plans the
    # owner already made: none is added and none changes).
    plans_before = _plan_rows(off_root)
    for name, params in (
        ("get_daily_plan", {}),
        ("next_plan_item", {}),
        ("set_plan_minutes", {"minutes": 40}),
        ("plan_keep_going", {}),
        ("plan_more_new", {}),
        ("plan_learner_pick", {"practiceItemId": "pi_missing"}),
        ("plan_reading_ended", {"outcome": "left_reader"}),
    ):
        assert _call(off, name, params)["enabled"] is False, name
    assert _call(off, "get_today_headline", {})["enabled"] is False
    assert _plan_rows(off_root) == plans_before
    # Still DL0 after those calls.
    assert _today_reads(off) == baseline


def test_the_plan_needs_the_successor_version(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    paths = create_daily_plan_vault(tmp_path / "vault", version="mvp-0.13")
    ctx = SidecarContext()
    ctx.load(paths.root)
    off = _call(ctx, "get_daily_plan", {})
    assert off["enabled"] is False and off["reason"] == "algorithm_version"


# ── §6.8's plan.enabled x router.enabled table ──────────────────────────────


@dataclass
class FakeRouterChooser:
    """Picks the last feasible candidate, and every third time names a bad id."""

    name: str = "fake_router"
    calls: int = 0

    def choose(self, state, feasible):
        self.calls += 1
        if self.calls % 3 == 0:
            return BlockChoice(candidate_id="hallucinated", chosen_by="mixture", propensity=0.2, why="", why_kind="model_no_rationale")
        if not feasible:
            return BlockChoice(candidate_id=STOP_FOR_TODAY, chosen_by="mixture", propensity=1.0, why="done", why_kind="model_written")
        return BlockChoice(candidate_id=feasible[-1].candidate_id, chosen_by="mixture", propensity=1.0 / len(feasible), why="router", why_kind="model_written", decision_ref=f"rd_{self.calls}")


def _router_policy():
    return PlanPolicy(source_name="staged_frame_fake", chooser=FakeRouterChooser(), make_source=DEFAULT_POLICY.make_source)


@pytest.mark.parametrize("router_on", [False, True])
def test_plan_off_rows_serve_the_open_queue_whatever_the_router(tmp_path, monkeypatch, router_on):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    paths = _wide_vault(tmp_path, plan_toml="[plan]\nenabled = false\n")
    env = make_env(paths.root, _wide_items(), policy=_router_policy() if router_on else DEFAULT_POLICY)
    with pytest.raises(PlanInactiveError):
        get_or_create_today(env)
    ctx = SidecarContext()
    ctx.load(paths.root)
    assert _call(ctx, "get_daily_plan", {})["enabled"] is False
    assert "reentryRefresherCap" in _call(ctx, "get_today_queue", {})


def test_plan_on_router_off_is_dl1s_deterministic_pair(tmp_path):
    paths = _wide_vault(tmp_path)
    env = make_env(paths.root, _wide_items())
    _seed_wide(env.repository)
    record = get_or_create_today(env)
    assert (record.row["source"], record.row["chooser"]) == ("legacy_lanes_v1", "lane_quota_v1")
    assert all(block.chosen["chosen_by"] == "lane_quota" and block.chosen["propensity"] == 1.0 for block in record.blocks)


def test_plan_on_router_on_keeps_the_containers_invariants(tmp_path):
    """G2, G12 and G13 hold with a model chooser in the seam."""

    paths = _wide_vault(tmp_path)
    clock = MovableClock()
    env = make_env(paths.root, _wide_items(), clock=clock, policy=_router_policy())
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert record.row["chooser"] == "fake_router"
    picked = False
    for _ in range(40):
        record, step = advance(env, serve=False)
        _assert_finite(record)  # G2: never past the budget or a lane's allotment
        if step["kind"] != "item":
            break
        if not picked:
            # G12: a learner pick wins, with no propensity, inside the budget.
            record, pick = learner_pick(env, "pi_p1b")
            picked = True
            _assert_finite(record)
            clock.advance(2)
            record_attempt(env.repository, "pi_p1b", "lo_p1", clock.now())
            continue
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now())
    blocks = record.blocks
    assert any(block.chosen_by == "learner_pick" and block.chosen["propensity"] is None for block in blocks)
    routed = [block for block in blocks if block.chosen_by != "learner_pick"]
    # G13: every decision logged with its candidate set; bad names fell back.
    assert all(block.chosen["candidate_set"] is not None for block in routed)
    assert any(block.chosen["fallback"] for block in routed) or len(routed) < 3
    assert all(
        block.chosen["chosen_by"] == ("lane_quota" if block.chosen["fallback"] else "mixture") for block in routed
    )


def test_new_admission_switch_admits_no_system_chosen_new_material(tmp_path):
    paths = _wide_vault(tmp_path, plan_toml="[plan]\nnew_admission_enabled = false\n")
    items = [scheduled("pi_spec_easy", "lo_spectral")] + _wide_items()
    env = make_env(paths.root, items, requested=["pi_spec_easy"])
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    assert record.admission["admitted"] == []
    assert record.admission["stopped_by"] == "admission_disabled"
    # Learner requests are still served (L3).
    assert record.blocks[0].items[0].practice_item_id == "pi_spec_easy"


def test_headline_switch_hides_only_the_headline(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    paths = create_daily_plan_vault(tmp_path / "vault", plan_toml="[plan]\nheadline = false\n")
    ctx = SidecarContext()
    ctx.load(paths.root)
    assert _call(ctx, "get_today_headline", {})["enabled"] is False
    plan = _call(ctx, "get_daily_plan", {})
    assert plan["enabled"] is True and plan["headlineEnabled"] is False
