"""Shared setup for the router R2b/R2c tests: a routed plan env with fake models."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, ROUTER_MIXTURE_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.policy import policy_for

from tests.daily_plan_fakes import MovableClock, make_env, record_attempt
from tests.helpers import append_config_toml
from tests.daily_plan_build_helpers import _seed_wide, _wide_items, _wide_vault

B = ROUTER_MIXTURE_ALGORITHM_VERSION

#: The objective's rollout horizon in these tests' vaults, in days; the served default is 90. Each rollout simulates
#: every day to the horizon, so it is most of these tests' seconds (about half go at 30 days), and what they assert
#: (one open offer, a switch's twin, a trace's fields) holds the same over a month as over a quarter. A test whose
#: claim needs the served horizon, or that turned out to depend on how long a rollout takes, uses the
#: ``served_horizon`` fixture. Refactor step A6 (docs/reviews/refactor-a6.md) records which and why.
HORIZON_DAYS: float | None = 30.0


@pytest.fixture
def served_horizon(monkeypatch):
    """This test's vaults keep the served 90-day horizon (``mixture_env`` adds no ``horizon_days``)."""

    monkeypatch.setattr(sys.modules[__name__], "HORIZON_DAYS", None)


def _with_horizon(toml: str | None) -> str | None:
    """``toml`` with ``HORIZON_DAYS`` in its ``[router_objective]`` table (added if absent), unless it sets one."""

    if HORIZON_DAYS is None or (toml and "horizon_days" in toml):
        return toml
    line = f"horizon_days = {HORIZON_DAYS!r}\n"
    if toml and re.search(r"(?m)^\[router_objective\]\s*$", toml):
        return re.sub(r"(?m)^\[router_objective\]\s*\n", lambda m: m.group(0) + line, toml, count=1)
    return f"{toml.rstrip()}\n\n[router_objective]\n{line}" if toml else f"[router_objective]\n{line}"


def mixture_env(tmp_path, runtime: Any, *, toml: str | None = None, serve: bool = True,
                version: str = LATEST_ALGORITHM_VERSION, items: Any = None, session_id: str | None = "s1"):
    """A routed plan env on the wide vault, at the head unless ``version`` says otherwise. Its objective rolls out
    ``HORIZON_DAYS`` (see there); a test that appends its own ``[router_objective]`` table later uses
    ``served_horizon``, since the table already exists. A vault at an older ``version`` (``B``, the mixture successor,
    for the tests whose claim is how that tag served) is served as that tag was: every later successor's switch off
    (``successor_switches``, through ``set_algorithm_version``) unless ``toml`` sets it."""

    paths = _wide_vault(tmp_path, version=version)
    toml = _with_horizon(toml)
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
        for key in ("candidates_json", "detail_json", "exclusions_json", "mixture_weights_json", "model_distributions_json",
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


#: The thread RO6's deferred carried valuation runs on after a no-model serve (``objective_job.defer_carry``).
CARRIED_THREAD = "learnloop-objective-carried"


def join_carried_valuations(monkeypatch) -> None:
    """Make the carried valuation land before each serve returns, for tests that compare two twins' numbers across
    serves (review 3, m5). In the no-model branch ``defer_carry`` starts a daemon thread after each serve, and the next
    decision's residual fit reads whatever has landed by then: a race, and in serving RO6's by design (each trace records
    what it read, so replay stays exact). Here each serve waits for the thread it started (``join_carried``) right
    after registering it, so both twins read every earlier carry. Production code is untouched: only the job's
    ``defer_carry`` is wrapped, for the test's duration."""

    from learnloop.daily_plan import objective_job as J

    real = J.defer_carry

    def joined(*args, **kwargs):
        out = real(*args, **kwargs)
        J.join_carried()
        return out

    monkeypatch.setattr(J, "defer_carry", joined)
