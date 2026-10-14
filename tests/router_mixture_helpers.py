"""Shared setup for the router R2b/R2c tests: a routed plan env with fake models."""

from __future__ import annotations

import json
from typing import Any

from learnloop.algorithm_versions import ROUTER_MIXTURE_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.policy import policy_for

from tests.daily_plan_fakes import MovableClock, make_env, record_attempt
from tests.helpers import append_config_toml
from tests.test_daily_plan_build import _seed_wide, _wide_items, _wide_vault

B = ROUTER_MIXTURE_ALGORITHM_VERSION


def mixture_env(tmp_path, runtime: Any, *, toml: str | None = None, serve: bool = True, version: str = B,
                items: Any = None, session_id: str | None = "s1"):
    paths = _wide_vault(tmp_path, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    env = make_env(paths.root, items if items is not None else _wide_items(), clock=MovableClock(),
                   session_id=session_id)
    _seed_wide(env.repository)
    env.policy = policy_for(env.vault, env.repository, session_id=session_id, clock=env.clock, runtime=runtime,
                            serve=serve)
    return env


def rows(env, kind: str = "plan_block") -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        found = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = ? ORDER BY created_at, id", (kind,)
        )]
    for row in found:
        for key in ("candidates_json", "detail_json", "mixture_weights_json", "model_distributions_json",
                    "sensor_answers_json", "model_ids_json", "similar_decision_ids_json"):
            if row.get(key) is not None:
                row[key] = json.loads(row[key])
    return found


def payloads(env, decision_id: str) -> dict[str, dict[str, Any]]:
    with env.repository.connection() as connection:
        return {
            row["kind"]: dict(row) for row in connection.execute(
                "SELECT * FROM router_decision_payloads WHERE decision_id = ?", (decision_id,)
            )
        }


def run(env, *, steps: int = 30):
    """Serve and answer every item; returns the record and the block sequence."""

    clock = env.clock
    record = None
    for _ in range(steps):
        record, step = advance(env, serve=True)
        if step is None or step["kind"] != "item":
            break
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now(),
                       session_id=env.session_id)
    return record
