"""Daily-loop DL1 §6.1 and §6.8: lanes, block packing, finiteness, requests,
displacement and learner picks (gates G2 and G12)."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest

from learnloop.daily_plan import engine
from learnloop.daily_plan.engine import advance, build_plan, decide, learner_pick
from learnloop.daily_plan.lanes import (
    LegacyLanesSource,
    PoolItem,
    ScheduledCheck,
    classify_pool,
    register_scheduled_check_provider,
    unregister_scheduled_check_provider,
)
from learnloop.daily_plan.types import LANES, PlanState
from tests.daily_plan_fakes import NOW, MovableClock, make_env, record_attempt, scheduled, seed_due
from tests.helpers import create_daily_plan_vault

PAST = NOW - timedelta(days=1)
LAST = NOW - timedelta(days=5)
FUTURE = NOW + timedelta(days=5)


def _state(due=None, last=None):
    return SimpleNamespace(
        due_at=None if due is None else due.strftime("%Y-%m-%dT%H:%M:%SZ"),
        last_attempt_at=None if last is None else last.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _lanes(pool):
    return {item.practice_item_id: item.lane for item in pool}


# ── §6.1 lane classification ─────────────────────────────────────────────────


def test_each_item_takes_the_first_lane_that_matches():
    items = [
        scheduled("pi_check", "lo_a", assumed_check=1.0, recent_error=0.4),
        scheduled("pi_follow", "lo_b", followup_kind="cold_retry"),
        scheduled("pi_err", "lo_c", recent_error=0.3),
        scheduled("pi_new_err", "lo_c", recent_error=0.3),
        scheduled("pi_new", "lo_d", new_material=1.0),
        scheduled("pi_due", "lo_e", forgetting_risk=0.5, goal_frontier=0.4),
        scheduled("pi_req_old", "lo_f"),
        scheduled("pi_req_new", "lo_f"),
        scheduled("pi_push", "lo_g", goal_frontier=0.4),
        scheduled("pi_later", "lo_h"),
    ]
    states = {
        "pi_check": None,
        "pi_follow": _state(FUTURE, LAST),
        "pi_err": _state(FUTURE, LAST),
        "pi_new_err": None,
        "pi_new": None,
        "pi_due": _state(PAST, LAST),
        "pi_req_old": _state(FUTURE, LAST),
        "pi_req_new": None,
        "pi_push": _state(FUTURE, LAST),
        "pi_later": _state(FUTURE, LAST),
    }
    pool = classify_pool(
        items,
        item_states=states,
        requested_ids=["pi_req_old", "pi_req_new"],
        now=NOW,
        estimate=lambda _id: 3.5,
        checks={},
        probe_cap_left=4,
    )
    assert _lanes(pool) == {
        # Scheduled checks first: never-attempted, never new, even with an error.
        "pi_check": "maintain",
        "pi_follow": "repair",
        "pi_err": "repair",
        # A never-attempted item on an LO with recent errors is still new
        # material: admission, re-entry and the switch govern it (review F1).
        "pi_new_err": "new",
        "pi_new": "new",
        # Maintain before push: due items on a goal frontier are maintenance.
        "pi_due": "maintain",
        "pi_req_old": "maintain",
        "pi_req_new": "new",
        "pi_push": "push",
        "pi_later": None,
    }
    assert pool[0].check_kind == "assumed_check"


def test_due_project_probes_are_scheduled_checks_under_their_daily_cap():
    """A never-attempted due project probe on an uncommitted, learning-eligible
    LO lands in maintain (not new), under plan.project_probes_max_per_day; the
    fifth stays "later". automation / all_at_once diffs come first."""

    items = [scheduled(f"pi_probe_{i}", "lo_repo") for i in range(5)]
    checks = {f"pi_probe_{i}": ScheduledCheck("project_probe", priority=1 if i == 4 else 0) for i in range(5)}
    pool = classify_pool(
        items, item_states={}, requested_ids=[], now=NOW, estimate=lambda _id: 3.0, checks=checks, probe_cap_left=4,
    )
    lanes = _lanes(pool)
    assert lanes["pi_probe_4"] == "maintain"  # the automation diff comes first
    assert list(lanes.values()).count("maintain") == 4 and list(lanes.values()).count(None) == 1
    assert lanes["pi_probe_3"] is None  # the fifth by rank stays "later"
    assert all(item.check_kind == "project_probe" for item in pool)


def test_project_probes_stay_outside_the_new_item_cap(tmp_path):
    paths = create_daily_plan_vault(
        tmp_path / "vault",
        learning_objects={"lo_repo": [(f"pi_probe_{i}", 1.0) for i in range(5)]},
        plan_toml="[plan]\nmax_new_items_per_day = 1\n",
    )
    probe_ids = {f"pi_probe_{i}" for i in range(5)}

    def provider(_vault, _repository, item_ids):
        return {item_id: ScheduledCheck("project_probe") for item_id in item_ids if item_id in probe_ids}

    register_scheduled_check_provider(provider)
    try:
        items = [scheduled(f"pi_probe_{i}", "lo_repo") for i in range(5)] + [
            scheduled("pi_eig_easy", "lo_eigen_basics", new_material=1.0),
            scheduled("pi_eig_mid", "lo_eigen_basics", new_material=1.0),
        ]
        env = make_env(paths.root, items)
        record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
        admitted = [row["practice_item_id"] for row in record.admission["admitted"]]
        assert admitted == ["pi_eig_easy"]  # the cap of 1 counts new material only
        record, _ = _run_to_end(env)
        planned = {item.practice_item_id: item for item in record.items()}
        assert {i for i in planned if i in probe_ids} == {f"pi_probe_{i}" for i in range(4)}
        assert all(planned[i].lane == "maintain" and planned[i].check_kind == "project_probe" for i in planned if i in probe_ids)
        assert not any(planned[i].new_admitted for i in planned if i in probe_ids)
    finally:
        unregister_scheduled_check_provider(provider)


# ── §6.8 legacy_lanes_v1 packing ─────────────────────────────────────────────


def _pool_item(item_id, lo, lane, minutes, rank):
    return PoolItem(
        practice_item_id=item_id, learning_object_id=lo, rank=rank, priority=0.5, lane=lane,
        reason="", est_minutes=minutes, never_attempted=lane == "new",
    )


def _state_for(minutes_left, lane_left):
    return PlanState(
        plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=minutes_left,
        lane_minutes_left={lane: lane_left.get(lane, 0.0) for lane in LANES},
        days_since_last_activity=0, streak_days=0, current_block_id=None,
    )


def test_a_single_due_item_is_a_complete_block():
    source = LegacyLanesSource(pool=[_pool_item("pi_a", "lo_a", "maintain", 3.5, 0)])
    (candidate,) = source.candidates(_state_for(25.0, {"maintain": 15.0}))
    assert candidate.item_ids == ("pi_a",) and candidate.est_minutes == pytest.approx(3.5)


def test_small_maintain_groups_merge_into_one_block_and_new_stays_on_one_lo():
    pool = [
        _pool_item("pi_a", "lo_a", "maintain", 1.5, 0),
        _pool_item("pi_b", "lo_b", "maintain", 1.5, 1),
        _pool_item("pi_c", "lo_c", "maintain", 1.5, 2),
        _pool_item("pi_n1", "lo_n", "new", 1.5, 3),
        _pool_item("pi_m1", "lo_m", "new", 1.5, 4),
    ]
    source = LegacyLanesSource(pool=pool, admitted_new_ids=frozenset({"pi_n1", "pi_m1"}))
    candidates = source.candidates(_state_for(25.0, {"maintain": 15.0, "new": 10.0}))
    maintain = [c for c in candidates if c.lane == "maintain"]
    assert maintain[0].item_ids == ("pi_a", "pi_b", "pi_c")  # interleaved review, under 5 min each
    assert maintain[0].learning_object_ids == ("lo_a", "lo_b", "lo_c")
    new = [c for c in candidates if c.lane == "new"]
    assert [c.item_ids for c in new] == [("pi_n1",), ("pi_m1",)]  # one LO per new block, short is fine


def test_blocks_never_exceed_15_minutes_or_the_lane_or_the_plan():
    pool = [_pool_item(f"pi_{i}", "lo_a", "maintain", 4.0, i) for i in range(6)]
    source = LegacyLanesSource(pool=pool)
    (first, *_rest) = source.candidates(_state_for(25.0, {"maintain": 15.0}))
    assert first.est_minutes == pytest.approx(12.0)  # three 4-minute items under 15
    (lane_bound, *_rest) = source.candidates(_state_for(25.0, {"maintain": 9.0}))
    assert lane_bound.est_minutes == pytest.approx(8.0)
    (plan_bound, *_rest) = source.candidates(_state_for(4.5, {"maintain": 15.0}))
    assert plan_bound.est_minutes == pytest.approx(4.0)


def test_a_3_5_minute_item_is_served_with_4_minutes_left(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_x": [("pi_x1", 3.0)]})
    env = make_env(paths.root, [scheduled("pi_x1", "lo_x", forgetting_risk=0.6)])
    seed_due(env.repository, "pi_x1", due=PAST, last=LAST)
    record = build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    (block,) = record.blocks
    assert [item.practice_item_id for item in block.items] == ["pi_x1"]
    assert block.est_minutes() == pytest.approx(3.5)
    # STOP was offered (under 5 minutes) but the feasible block was chosen.
    assert block.chosen["stop_offered"] is True and block.chosen["chosen_by"] == "lane_quota"


# ── G2: finite ───────────────────────────────────────────────────────────────


def _run_to_end(env, *, limit=60):
    clock = env.clock
    steps = []
    record = None
    for _ in range(limit):
        record, step = advance(env, serve=True) if env.session_id else advance(env, serve=False)
        _assert_finite(record)
        steps.append(step)
        if step["kind"] != "item":
            break
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now())
        clock.advance(1)
    return record, steps


def _assert_finite(record):
    assert record.minutes_planned() <= record.budget + 1e-6
    allotment, spent = record.ledger()
    for lane in LANES:
        assert spent[lane] <= allotment[lane] + 1e-3, (lane, spent, allotment)


def _wide_vault(tmp_path, **kwargs):
    los = {
        "lo_m1": [("pi_m1a", 1.0), ("pi_m1b", 1.0)],
        "lo_m2": [("pi_m2a", 2.0)],
        "lo_r1": [("pi_r1a", 2.0), ("pi_r1b", 2.0)],
        "lo_p1": [("pi_p1a", 3.0), ("pi_p1b", 3.0)],
    }
    return create_daily_plan_vault(tmp_path / "vault", learning_objects=los, **kwargs)


def _wide_items():
    return [
        scheduled("pi_r1a", "lo_r1", recent_error=0.5),
        scheduled("pi_r1b", "lo_r1", recent_error=0.5),
        scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m1b", "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m2a", "lo_m2", forgetting_risk=0.6),
        scheduled("pi_eig_easy", "lo_eigen_basics", new_material=1.0),
        scheduled("pi_eig_mid", "lo_eigen_basics", new_material=1.0),
        scheduled("pi_diag_easy", "lo_diag", new_material=1.0),
        scheduled("pi_p1a", "lo_p1", goal_frontier=0.4),
        scheduled("pi_p1b", "lo_p1", goal_frontier=0.4),
    ]


def _seed_wide(repository):
    for item in ("pi_r1a", "pi_r1b", "pi_p1a", "pi_p1b"):
        seed_due(repository, item, due=FUTURE, last=LAST)
    for item in ("pi_m1a", "pi_m1b", "pi_m2a"):
        seed_due(repository, item, due=PAST, last=LAST)


@pytest.mark.parametrize("budget", [10, 15, 25, 40])
def test_the_plan_never_exceeds_its_budget_or_a_lanes_allotment(tmp_path, budget):
    paths = _wide_vault(tmp_path)
    env = make_env(paths.root, _wide_items(), clock=MovableClock())
    _seed_wide(env.repository)
    build_plan(env, kind="normal", budget=float(budget), remembered=budget, minutes_source="chip")
    record, steps = _run_to_end(env)
    assert steps[-1]["kind"] == "done"
    assert record.status == "complete"
    assert record.minutes_planned() <= budget + 1e-6
    # Every block decision was logged with its candidate set (G13).
    assert all("candidate_set" in block.chosen for block in record.blocks)


def test_requested_items_go_first_and_are_deducted_before_the_split(tmp_path):
    paths = _wide_vault(tmp_path)
    items = [scheduled("pi_spec_easy", "lo_spectral")] + _wide_items()
    env = make_env(paths.root, items, requested=["pi_spec_easy"])
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    first = record.blocks[0]
    assert first.items[0].practice_item_id == "pi_spec_easy"
    assert first.items[0].origin == "requested"
    split = record.split
    assert split["requested_minutes"] == pytest.approx(3.5)
    assert split["m"] == pytest.approx(25.0 - 3.5)
    assert sum(row["minutes"] for row in split["lanes"].values()) <= 21.5 + 1e-6


def test_mid_plan_followups_displace_the_tail_and_never_grow_the_plan(tmp_path):
    paths = _wide_vault(tmp_path)
    clock = MovableClock()
    live = list(_wide_items())
    env = make_env(paths.root, lambda: live, clock=clock, session_id=None)
    _seed_wide(env.repository)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    record, step = advance(env, serve=False)
    budget_before = record.budget
    # An answer produced a follow-up that was not in the plan at build.
    live.insert(0, scheduled("pi_diag_mid", "lo_diag", followup_kind="negative_surprise_followup"))
    clock.advance(1)
    record, step = advance(env, serve=False)
    followups = [item for item in record.items() if item.origin == "followup"]
    assert [item.practice_item_id for item in followups] == ["pi_diag_mid"]
    assert record.budget == budget_before
    assert record.minutes_planned() <= record.budget + 1e-6
    # It is served next.
    assert step["practice_item_id"] == "pi_diag_mid"


def test_items_that_appear_mid_plan_do_not_join_it(tmp_path):
    """A capture adopted mid-day (a new learner request) joins tomorrow's plan
    or "keep going", never today's (§6.1)."""

    paths = _wide_vault(tmp_path)
    clock = MovableClock()
    live = list(_wide_items())
    env = make_env(paths.root, lambda: live, clock=clock, requested=["pi_spec_hard"])
    _seed_wide(env.repository)
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    live.insert(0, scheduled("pi_spec_hard", "lo_spectral"))
    record, _steps = _run_to_end(env)
    assert "pi_spec_hard" not in {item.practice_item_id for item in record.items()}


# ── G12: learner picks win and displace ──────────────────────────────────────


def test_a_learner_pick_is_logged_without_propensity_and_displaces_the_tail(tmp_path):
    paths = _wide_vault(tmp_path)
    clock = MovableClock()
    env = make_env(paths.root, _wide_items(), clock=clock, session_id=None)
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=8.0, remembered=8, minutes_source="chip")
    planned_before = [item.practice_item_id for item in record.active_items()]
    assert record.minutes_planned() > 4.0
    # pi_p1a (push, 3.5 min) is in the full list but not planned.
    record, step = learner_pick(env, "pi_p1a")
    pick = next(block for block in record.blocks if block.chosen_by == "learner_pick")
    assert pick.chosen["propensity"] is None and pick.chosen["chosen_by"] == "learner_pick"
    assert step["practice_item_id"] == "pi_p1a" and step["origin"] == "learner_pick"
    assert record.minutes_planned() <= record.budget + 1e-6
    displaced = [item.practice_item_id for item in record.items() if item.displaced]
    assert displaced and set(displaced) <= set(planned_before)
    assert pick.items[0].served_at is not None


def test_opening_a_planned_item_from_the_list_serves_it_without_a_new_block(tmp_path):
    paths = _wide_vault(tmp_path)
    env = make_env(paths.root, _wide_items(), session_id=None)
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    target = record.blocks[0].items[-1].practice_item_id
    record, step = learner_pick(env, target)
    assert step["practice_item_id"] == target and step["origin"] != "learner_pick"
    assert not any(block.chosen_by == "learner_pick" for block in record.blocks)


def test_decisions_happen_at_block_boundaries_only(tmp_path):
    paths = _wide_vault(tmp_path)
    env = make_env(paths.root, _wide_items())
    _seed_wide(env.repository)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    first, _ = advance(env, serve=False)
    again, _ = advance(env, serve=False)
    # No answer in between: still the same single chosen block.
    assert len(first.blocks) == len(again.blocks) == 1


def test_engine_rejects_work_while_the_plan_is_off(tmp_path):
    paths = _wide_vault(tmp_path, plan_toml="[plan]\nenabled = false\n")
    env = make_env(paths.root, _wide_items())
    with pytest.raises(engine.PlanInactiveError):
        advance(env, serve=False)


def test_decide_is_pure(tmp_path):
    paths = _wide_vault(tmp_path)
    env = make_env(paths.root, _wide_items())
    _seed_wide(env.repository)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _context, built = engine._live_context(env, record)
    context = engine._context(env, record, built, day=())
    before = env.repository.queue_revision()
    one = decide(record, context, env.policy)
    two = decide(record, context, env.policy)
    assert one.choice == two.choice and one.redistribution == two.redistribution
    assert env.repository.queue_revision() == before
