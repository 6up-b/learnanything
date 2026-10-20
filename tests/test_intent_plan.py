"""Daily-loop DL2 in the finite plan (§5.2, §5.4, §6.1, §6.3, §7).

The real scheduler feeds the real plan engine (``PlanEnv`` with no fake
list). "Check once" items are scheduled checks in the maintain lane (DL1's
``check_once`` kind), never requests-first; several due on one day are bounded
by the plan's minutes, not a count (Reader §9.3 item 6, G27). Learn and
Master feed push; Keep and Light touch admit no new material; re-entry leaves
Light touch out and orders by intent tier.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import INTENT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import PlanEnv, PoolContext, _intents, build_plan
from learnloop.daily_plan.reentry import ReentryGap
from learnloop.daily_plan.types import IntentView
from learnloop.db.repositories import Repository
from learnloop.intent.control import Scope, apply_choice
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from tests.daily_plan_fakes import MovableClock, record_attempt, seed_due
from tests.helpers import create_daily_plan_vault
from tests.intent_fakes import NOW, make_intent_vault
from tests.test_daily_plan_build import _assert_finite, _run_to_end


def _env(iv, at) -> PlanEnv:
    return PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(at))


def _pool(record):
    return {row["practice_item_id"]: row for row in record.split.get("pool") or []}


def test_a_due_check_is_a_maintain_lane_scheduled_check_not_a_request(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    at = NOW + timedelta(days=8)
    record = build_plan(_env(iv, at), kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    row = _pool(record)["pi_b1"]
    assert (row["lane"], row["check_kind"], row["requested"]) == ("maintain", "check_once", False)
    assert record.split["requested"] == []


def test_a_waiting_check_and_a_pause_keep_their_items_out_of_the_plan(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    iv.choose("learning_object", "lo_a", "pause", NOW + timedelta(seconds=1))
    record = build_plan(_env(iv, NOW + timedelta(days=1)), kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    universe = set(record.split["universe"])
    assert not {"pi_b1", "pi_a1", "pi_a2"} & universe
    assert {"pi_c1", "pi_c2"} <= universe


def _many_checks_vault(tmp_path, count: int = 8):
    los = {f"lo_k{index}": [(f"pi_k{index}", 3.5)] for index in range(count)}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=INTENT_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    reviewed = NOW - timedelta(days=3)
    for index in range(count):
        record_attempt(repository, f"pi_k{index}", f"lo_k{index}", reviewed)
        seed_due(repository, f"pi_k{index}", due=NOW + timedelta(days=30), last=reviewed)
        apply_choice(vault, repository, Scope("practice_item", f"pi_k{index}"), "check_once",
                     clock=FrozenClock(NOW + timedelta(seconds=index)))
    return vault, repository


@pytest.mark.parametrize("budget,at_most,at_least", [(10, 2, 2), (40, 8, 5)])
def test_several_checks_due_on_one_day_are_bounded_by_the_minutes_not_a_count(tmp_path, budget, at_most, at_least):
    vault, repository = _many_checks_vault(tmp_path)
    clock = MovableClock(NOW + timedelta(days=8))
    env = PlanEnv(vault=vault, repository=repository, clock=clock)
    build_plan(env, kind="normal", budget=float(budget), remembered=budget, minutes_source="chip")
    record, steps = _run_to_end(env)
    _assert_finite(record)
    served_checks = [s["practice_item_id"] for s in steps if s["kind"] == "item" and s["practice_item_id"].startswith("pi_k")]
    assert at_least <= len(served_checks) <= at_most
    # More than the project-probe count cap: minutes, not a count, bound them.
    assert all(item.check_kind == "check_once" for item in record.items() if item.practice_item_id.startswith("pi_k"))


def _without_goals(iv):
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths = VaultPaths(iv.vault.root, iv.vault.config)
    if paths.goals_path.exists():
        data = read_yaml(paths.goals_path)
        for goal in data.get("goals") or []:
            goal["status"] = "paused"
        write_yaml(paths.goals_path, data)
    iv.reload()


def test_learn_and_master_feed_push_with_items_not_yet_due(tmp_path):
    iv = make_intent_vault(tmp_path / "vault", reviewed_days_ago=1)
    _without_goals(iv)  # no goal frontier: push can only come from intent
    for item_id in ("pi_a1", "pi_a2", "pi_b1"):
        seed_due(iv.repository, item_id, due=NOW + timedelta(days=10), last=NOW - timedelta(days=1))
    iv.choose("learning_object", "lo_a", "learn", NOW)
    record = build_plan(_env(iv, NOW + timedelta(minutes=1)), kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    pool = _pool(record)
    assert pool["pi_a1"]["lane"] == "push" and pool["pi_a2"]["lane"] == "push"
    assert pool["pi_a1"]["reason"] == "you chose Learn or Master here, not due yet"
    assert "pi_b1" not in pool  # uncommitted, not due, no frontier: no lane


def _new_material_vault(tmp_path):
    los = {"lo_n1": [("pi_n1", 2.0)], "lo_n2": [("pi_n2", 2.0)], "lo_n3": [("pi_n3", 2.0)]}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=INTENT_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repository


def test_admission_takes_learn_first_and_keep_adds_no_new_material(tmp_path):
    vault, repository = _new_material_vault(tmp_path)
    apply_choice(vault, repository, Scope("learning_object", "lo_n3"), "learn", clock=FrozenClock(NOW))
    apply_choice(vault, repository, Scope("learning_object", "lo_n2"), "keep", clock=FrozenClock(NOW))
    env = PlanEnv(vault=vault, repository=repository, clock=MovableClock(NOW + timedelta(minutes=1)))
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    admitted = [row["practice_item_id"] for row in record.admission["admitted"]]
    assert "pi_n2" not in admitted
    assert admitted and admitted[0] == "pi_n3"


def test_reentry_leaves_light_touch_out_and_orders_by_intent_tier(tmp_path):
    iv = make_intent_vault(tmp_path / "vault", reviewed_days_ago=12)
    # Far overdue, so a Keep target (0.85) still finds them due.
    seed_due(iv.repository, "pi_b1", due=NOW - timedelta(days=8), last=NOW - timedelta(days=12))
    iv.choose("learning_object", "lo_a", "light_touch", NOW)
    iv.choose("learning_object", "lo_b", "keep", NOW)
    iv.choose("learning_object", "lo_c", "master", NOW)
    env = _env(iv, NOW + timedelta(minutes=1))
    assert env.gap().due
    record = build_plan(env, kind="reentry", budget=15.0, remembered=25, minutes_source="carried")
    ordered = [row["practice_item_id"] for row in record.split["pool"] if row["practice_item_id"].startswith("pi_")
               and row["practice_item_id"][3] in "abc"]
    assert "pi_a1" not in ordered and "pi_a2" not in ordered
    assert ordered.index("pi_c1") < ordered.index("pi_b1")


def test_committed_los_reach_the_chooser_state_with_their_intent():
    context = PoolContext(
        pool=(), lanes_allowed=("maintain",), admitted_new_ids=frozenset(), admitted_new_minutes=0.0,
        reading=None, reading_full_minutes=None, titles={}, gap=ReentryGap(False, 0, 7, None), streak_days=0,
        intent_views={"lo_x": IntentView(choice="keep", disposition="active", recall_target=0.85)},
    )
    assert _intents(context) == {}
    from learnloop.daily_plan.lanes import PoolItem

    item = PoolItem(practice_item_id="pi", learning_object_id="lo_x", rank=0, priority=1.0, lane="maintain",
                    reason="r", est_minutes=1.0, never_attempted=False)
    other = PoolItem(practice_item_id="pj", learning_object_id="lo_y", rank=1, priority=1.0, lane="maintain",
                     reason="r", est_minutes=1.0, never_attempted=False)
    from dataclasses import replace

    views = _intents(replace(context, pool=(item, other), deadlines={"lo_x": "2026-11-01"}))
    assert views["lo_x"] == IntentView(choice="keep", disposition="active", recall_target=0.85, deadline="2026-11-01")
    assert views["lo_y"] == IntentView()


def test_with_no_commitment_the_plan_build_equals_intent_off(tmp_path):
    on = make_intent_vault(tmp_path / "on")
    off = make_intent_vault(tmp_path / "off")
    from tests.helpers import append_config_toml

    append_config_toml(off.root, "[intent]\nenabled = false\n")
    off.reload()
    at = NOW + timedelta(minutes=1)
    plans = []
    for iv in (on, off):
        record = build_plan(_env(iv, at), kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        row = dict(record.row)
        for key in ("id", "created_at", "updated_at", "config_hash"):
            row.pop(key, None)
        blocks = [
            [(item.practice_item_id, item.lane, round(item.est_minutes, 4), item.check_kind) for item in block.items]
            for block in record.blocks
        ]
        plans.append((row["split_json"] if "split_json" in row else record.split, record.admission, blocks))
    assert plans[0] == plans[1]


def test_plan_report_counts_the_recall_target_fallbacks(tmp_path):
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.intent.report import intent_report

    iv = make_intent_vault(tmp_path / "vault")
    # pi_c1: state but its only attempt was primed (no qualifying attempt);
    # pi_c2: a null due_at.
    with iv.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET primed = 1 WHERE practice_item_id = 'pi_c1'")
        connection.commit()
    iv.repository.upsert_practice_item_state("pi_c2", difficulty=5.0, stability=None, due_at=None,
                                             last_attempt_at=None, active=True)
    iv.choose("learning_object", "lo_c", "light_touch", NOW)
    iv.choose("learning_object", "lo_a", "keep", NOW)
    iv.choose("learning_object", "lo_b", "learn", NOW)
    with closing(connect(iv.repository.sqlite_path, read_only=True)) as connection:
        report = intent_report(iv.vault, connection)
    assert report["recall_target_fallbacks"] == {"no_due_at": 1, "no_qualifying_attempt": 1}
    assert report["recall_target_items_scaled"] == 2  # pi_a1, pi_a2 at 0.85; pi_b1 is at 0.90
    assert report["committed_items_by_choice"] == {"keep": 2, "learn": 1, "light_touch": 2}


def test_the_reentry_panel_counts_active_intents_against_their_own_targets(tmp_path):
    from learnloop.daily_plan.reentry import reentry_panel

    iv = make_intent_vault(tmp_path / "vault", reviewed_days_ago=12)
    env = _env(iv, NOW)
    gap = env.gap()
    baseline = reentry_panel(iv.vault, iv.repository, now=NOW, gap=gap)
    iv.choose("learning_object", "lo_a", "light_touch", NOW)
    iv.choose("learning_object", "lo_b", "pause", NOW)
    panel = reentry_panel(iv.vault, iv.repository, now=NOW, gap=gap, intent=iv.serving(NOW))
    counted = baseline.solid_count + baseline.slipped_count
    assert panel.solid_count + panel.slipped_count == counted - 2


def test_an_assumed_lo_with_no_commitment_reads_as_keep_for_its_check(tmp_path):
    """§5.6: an LO assumed known (not tested) with no commitment is Keep for
    its check (maintain lane, target 0.85); an explicit commitment wins."""

    from learnloop.daily_plan.engine import _Pool, _intent_views
    from learnloop.daily_plan.lanes import PoolItem

    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("learning_object", "lo_b", "master", NOW)
    env = _env(iv, NOW + timedelta(minutes=1))

    def check(item_id, lo_id):
        return PoolItem(practice_item_id=item_id, learning_object_id=lo_id, rank=0, priority=1.0, lane="maintain",
                        reason="assumed", est_minutes=2.5, never_attempted=True, check_kind="assumed_check")

    built = _Pool(scheduled=[], pool=[check("pi_a1", "lo_a"), check("pi_b1", "lo_b")], estimator=None, deadlines={},
                  intent=iv.serving(NOW + timedelta(minutes=1)))
    views = _intent_views(env, built, ["lo_a", "lo_b", "lo_c"])
    assert views["lo_a"] == IntentView(choice="keep", disposition="active", recall_target=0.85)
    assert views["lo_b"].choice == "master" and views["lo_b"].recall_target == pytest.approx(0.92)
    assert "lo_c" not in views  # uncommitted, not assumed: DL1's default view
