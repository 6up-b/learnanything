"""Router R1 composed with daily-loop DL1 (owner decisions 2026-10-12).

* **The full list under the plan** (R1 review F3, wired at this merge): while
  the finite plan serves Today, ``get_today_queue`` is the full list one key
  away from it. It serves no head, so its builds are logged as
  ``not_served`` on surface ``full_list`` and every bind from it is a learner
  pick. ``today_head_served`` reads ``plan_active``.
* **Plan block decisions get router decision ids** (owner decision 4): R1
  registers a logger on DL1's ``register_plan_decision_logger`` hook. Each
  block decision and chooser stop ``_boundary`` makes is written as a
  ``router_decisions`` row of kind ``plan_block`` inside the block's
  transaction, and its id becomes the block's ``decision_ref``. A chooser that
  logs its own decision (R2) keeps its id and is not logged twice;
  ``router.log_decisions = false`` writes nothing; a refused row never blocks
  the plan.

No model is called.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import logging
import sqlite3

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.daily_plan import engine
from learnloop.daily_plan.engine import (
    PlanPolicy,
    advance,
    build_plan,
    get_or_create_today,
    legacy_source,
)
from learnloop.daily_plan.types import CONTINUE_CURRENT, STOP_FOR_TODAY, BlockChoice
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.daily_plan_fakes import NOW, MovableClock, make_env, scheduled, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault, create_placement_vault

DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _ctx(root):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx


def _rows(path, kind: str | None = None) -> list[dict]:
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        sql = "SELECT * FROM router_decisions"
        args: tuple = ()
        if kind is not None:
            sql += " WHERE decision_kind = ?"
            args = (kind,)
        rows = [dict(row) for row in connection.execute(sql + " ORDER BY created_at, id", args)]
    for row in rows:
        for column in ("candidates_json", "exclusions_json", "detail_json"):
            row[column] = json.loads(row[column])
    return rows


def _no_goals(paths):
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})


@pytest.fixture
def frozen_now(monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY1)
    return DAY1


# -- the full list under the plan (R1 review F3) ------------------------------------


def test_the_full_list_seam_reads_the_plan(tmp_path):
    from learnloop_sidecar.handlers.queue import today_head_served

    plan = create_daily_plan_vault(tmp_path / "plan", version="mvp-0.15")
    assert today_head_served(load_vault(plan.root)) is False
    append_config_toml(plan.root, "[plan]\nenabled = false\n")
    # The plan's kill switch: Today is the legacy queue again, whose head is served.
    assert today_head_served(load_vault(plan.root)) is True
    legacy = create_placement_vault(tmp_path / "legacy", version="mvp-0.11")
    assert today_head_served(load_vault(legacy.root)) is True


def test_under_the_plan_the_full_list_serves_no_head_and_a_pick_from_it_is_logged(tmp_path, frozen_now):
    paths = create_daily_plan_vault(
        tmp_path / "vault", version="mvp-0.15",
        learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]},
    )
    ctx = _ctx(paths.root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    listing = _call(ctx, "get_today_queue", {"sessionId": session_id})
    [offer] = _rows(paths.sqlite_path, "today_offer")
    assert (offer["surface"], offer["propensity_kind"], offer["chosen_ref"]) == ("full_list", "not_served", None)
    assert offer["detail_json"]["head_served"] is False
    # L3: the learner opens the list's first item from the plan; its answer
    # binds the list's offer, so the pick is logged against the list.
    first = next(item for section in listing["sections"] for item in section["items"])
    step = _call(
        ctx, "plan_learner_pick",
        {"sessionId": session_id, "practiceItemId": first["practiceItemId"],
         "schedulerCandidateId": first["schedulerCandidateId"]},
    )["step"]
    assert step["schedulerCandidateId"] == first["schedulerCandidateId"]
    _call(
        ctx, "submit_dont_know",
        {"sessionId": session_id, "practiceItemId": first["practiceItemId"], "latencySeconds": 60,
         "submissionId": "sub_pick", "schedulerCandidateId": first["schedulerCandidateId"]},
    )
    [pick] = _rows(paths.sqlite_path, "learner_pick")
    assert pick["parent_decision_id"] == offer["id"]
    assert (pick["chosen_ref"], pick["propensity_kind"]) == (first["practiceItemId"], "none")
    assert pick["detail_json"]["offer_served_head"] is False


# -- plan block decisions through DL1's hook (owner decision 4) --------------------


def test_plan_block_decisions_get_router_decision_ids_end_to_end(tmp_path, frozen_now):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths = create_daily_plan_vault(
        tmp_path / "vault", version="mvp-0.15",
        learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]},
    )
    ctx = _ctx(paths.root)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
    step = served["step"]
    assert step["kind"] == "item"

    rows = _rows(paths.sqlite_path, "plan_block")
    assert rows, "every block decision is a plan_block router decision"
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        blocks = {
            row["id"]: dict(row)
            for row in connection.execute(
                "SELECT id, decision_ref, chosen_by, plan_ordinal FROM attention_blocks WHERE daily_plan_id IS NOT NULL"
            )
        }
    by_block = {row["detail_json"]["block_id"]: row for row in rows}
    numbered = [block for block in blocks.values() if block["plan_ordinal"] is not None]
    assert numbered and all(block["id"] in by_block for block in numbered)
    for block in numbered:
        row = by_block[block["id"]]
        # The router decision id is the block's decision_ref (its row and its receipt).
        assert block["decision_ref"] == row["id"]
        assert row["receipt_key"] == f"plan_block:{block['id']}"
        assert (row["surface"], row["mode"], row["policy"]) == ("daily_plan", "daily_plan", "lane_quota_v1")
        assert row["algorithm_version"] == "mvp-0.15"
        # lane_quota_v1 is deterministic.
        assert (row["propensity"], row["propensity_kind"], row["learner_pick"], row["design"]) == (
            1.0, "deterministic", 0, None,
        )
        refs = {candidate["ref"]: candidate for candidate in row["candidates_json"]}
        assert row["chosen_ref"] in refs and refs[row["chosen_ref"]]["propensity"] == 1.0
        assert {CONTINUE_CURRENT, STOP_FOR_TODAY} <= set(refs)
        assert refs[CONTINUE_CURRENT]["feasible"] is False
        assert row["candidate_count"] == len(row["candidates_json"])
        assert sum(candidate["propensity"] or 0.0 for candidate in row["candidates_json"]) == pytest.approx(1.0)
        assert row["chosen_practice_item_id"] and row["chosen_learning_object_id"]
        assert row["snapshot_hash"]
    first_block = next(block for block in numbered if block["plan_ordinal"] == 1)
    first_row = by_block[first_block["id"]]
    assert first_row["chosen_practice_item_id"] == step["practiceItemId"]

    # The served item's answer is the block decision's action.
    _call(
        ctx, "submit_dont_know",
        {"sessionId": session_id, "practiceItemId": step["practiceItemId"], "latencySeconds": 90,
         "submissionId": "sub_1", "schedulerCandidateId": step["schedulerCandidateId"]},
    )
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, Repository(paths.sqlite_path))
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        outcome = dict(
            connection.execute("SELECT * FROM router_outcomes WHERE decision_id = ?", (first_row["id"],)).fetchone()
        )
        attempt_id = connection.execute(
            "SELECT id FROM practice_attempts WHERE practice_item_id = ?", (step["practiceItemId"],)
        ).fetchone()[0]
    assert (outcome["action_status"], outcome["action_attempt_id"]) == ("taken", attempt_id)


def _plan_env(tmp_path, *, policy=None, toml: str | None = None, items=None):
    los = {f"lo_s{i}": [(f"pi_s{i}", 3.0)] for i in range(3)}
    paths = create_daily_plan_vault(tmp_path / "vault", version="mvp-0.15", learning_objects=los, plan_toml=toml)
    _no_goals(paths)
    env = make_env(
        paths.root,
        [scheduled(f"pi_s{i}", f"lo_s{i}", forgetting_risk=0.7) for i in range(3)] if items is None else items,
        clock=MovableClock(NOW), policy=policy or engine.DEFAULT_POLICY,
    )
    for i in range(3):
        seed_due(env.repository, f"pi_s{i}", due=NOW - timedelta(days=2), last=NOW - timedelta(days=9))
    return paths, env


def test_a_chooser_stop_is_a_stop_for_today_plan_block(tmp_path):
    paths, env = _plan_env(tmp_path, items=[])
    record = get_or_create_today(env)
    assert record is not None and not record.blocks
    (stop,) = record.stops()
    [row] = _rows(paths.sqlite_path, "plan_block")
    assert stop.decision_ref == row["id"] and stop.chosen["decision_ref"] == row["id"]
    assert (row["chosen_ref"], row["propensity_kind"], row["propensity"]) == (STOP_FOR_TODAY, "deterministic", 1.0)
    assert row["chosen_practice_item_id"] is None and row["detail_json"]["stop"] is True
    # Logged at the plan's own clock, like the stop receipt.
    assert row["created_at"] == "2026-10-12T09:00:00Z"


def test_a_choosers_own_decision_id_is_kept_and_not_logged_twice(tmp_path):
    class Router:
        name = "fake_router"

        def choose(self, state, feasible):
            return BlockChoice(feasible[0].candidate_id, "mixture", 0.4, "pick", "model_written", "rd_x")

    paths, env = _plan_env(tmp_path, policy=PlanPolicy("fake_source", Router(), legacy_source))
    block = build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip").blocks[0]
    assert block.decision_ref == "rd_x"
    assert _rows(paths.sqlite_path, "plan_block") == []


def test_a_malformed_choosers_fallback_block_gets_r1s_id(tmp_path):
    class Router:
        name = "fake_router"

        def choose(self, state, feasible):
            return BlockChoice(feasible[0].candidate_id, "mixture", 1.5, "pick", "model_written", "rd_x")

    paths, env = _plan_env(tmp_path, policy=PlanPolicy("fake_source", Router(), legacy_source))
    block = build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip").blocks[0]
    [row] = _rows(paths.sqlite_path, "plan_block")
    assert block.decision_ref == row["id"] != "rd_x"
    assert (row["policy"], row["propensity_kind"]) == ("lane_quota_v1", "deterministic")
    # The fallback names the chooser's refused pick (R1's DL1 checklist).
    assert row["fallback"] == block.chosen["fallback_from"]
    assert row["detail_json"]["fallback_reason"] == "propensity_out_of_range"


def test_router_logging_off_writes_no_plan_block_and_leaves_decision_ref_unset(tmp_path):
    paths, env = _plan_env(tmp_path)
    append_config_toml(paths.root, "[router]\nlog_decisions = false\n")
    env = make_env(
        paths.root, [scheduled(f"pi_s{i}", f"lo_s{i}", forgetting_risk=0.7) for i in range(3)],
        clock=MovableClock(NOW),
    )
    record = get_or_create_today(env)
    record, _step = advance(env, serve=False)
    assert record.blocks and all(block.decision_ref is None for block in record.blocks)
    assert _rows(paths.sqlite_path, "plan_block") == []


def test_a_refused_plan_row_never_blocks_the_plan(tmp_path, monkeypatch, caplog):
    from learnloop.db.stores import router as router_store

    paths, env = _plan_env(tmp_path)

    def refuse(connection, row):
        raise sqlite3.IntegrityError("CHECK constraint failed: simulated")

    monkeypatch.setattr(router_store, "insert_router_decision", refuse)
    with caplog.at_level(logging.WARNING):
        record = get_or_create_today(env)
    assert record is not None and record.blocks
    assert all(block.decision_ref is None for block in record.blocks)
    assert _rows(paths.sqlite_path, "plan_block") == []
    assert any("refused" in message for message in caplog.messages)
