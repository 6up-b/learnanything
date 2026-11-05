"""RO0's gate (spec_router_objective_v1 §4): serving byte-identical with the switch on and off, apart from the new rows and
columns (``tests/test_data_capture_successor.py``'s method), no display order changes, and rebuild leaves the receipts alone."""

from __future__ import annotations

import json

import pytest

from learnloop.algorithm_versions import DATA_CAPTURE_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import append_config_toml, create_basic_vault
from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import fake_runtime, seed_with_first_uniform
from tests.test_data_capture_successor import _blocks, _canonical_rows
from tests.test_router_g4_restraint import PAST_THE_FLOOR

OFF = "[router_objective]\nreceipts = false\n"
NEW_TABLES = ("session_receipts", "decision_state_receipts", "goal_lifecycle_events")
#: Every table a decision's serve writes, read back for the comparison, its new columns and fresh ids aside.
_SERVED_TABLES = ("attention_blocks", "attention_block_events", "plan_presentations", "daily_plans")
_VOLATILE = {"id", "block_id", "daily_plan_id", "parent_plan_id", "router_decision_id", "decision_ref", "controller_decision_id",
             "snapshot_hash", "content_hash", "config_hash", "created_at", "updated_at", "completed_at", "served_at", "session_id",
             "ask_available"}


def _scrub(value):
    if isinstance(value, dict):
        return {key: _scrub(item) for key, item in value.items() if key not in _VOLATILE and "hash" not in key}
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _served(env):
    out = {}
    with env.repository.connection() as connection:
        for table in _SERVED_TABLES:
            rows = [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for row in rows:
                for key, value in list(row.items()):
                    if key.endswith("_json") and isinstance(value, str):
                        row[key] = json.loads(value)
            out[table] = _scrub(rows)
    return out


def _first_difference(left, right, path=""):
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            found = _first_difference(left.get(key), right.get(key), f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path}: length {len(left)} != {len(right)}"
        for index, (one, other) in enumerate(zip(left, right)):
            found = _first_difference(one, other, f"{path}[{index}]")
            if found:
                return found
        return None
    return None if left == right else f"{path}: {left!r} != {right!r}"


def _scrub_step(step):
    return {key: value for key, value in (step or {}).items() if key != "plan_id"}


def _rows(env):
    """The decisions, ``boundary_key`` aside: a digest of the plan's fresh id, as the row's other hashes are."""

    def without(value):
        if isinstance(value, dict):
            return {key: without(item) for key, item in value.items() if key != "boundary_key"}
        return [without(item) for item in value] if isinstance(value, list) else value

    return without(_canonical_rows(env))


def _new_rows(env) -> dict[str, int]:
    with env.repository.connection() as connection:
        return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in NEW_TABLES}


@pytest.mark.parametrize("version", [LATEST_ALGORITHM_VERSION, DATA_CAPTURE_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION])
@pytest.mark.parametrize("budget", [25.0, 6.0], ids=["a_full_plan", "stop_offered"])
def test_the_plan_blocks_rows_and_serves_are_the_same_on_and_off(tmp_path, version, budget):
    # The rule's draw on both sides: a draw is seeded from each run's fresh ids, so only that compares byte for byte.
    def runtime():
        return fake_runtime(seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))

    # Router objective RO4 (mvp-0.47) reads RO0's receipts by its spec (§8.1: p_accept from §4 row 7; the price's
    # day seed and the weight from its own traces), so "nothing serving reads them" holds there with the objective
    # off; with it on, receipts off still serves (tests/test_ro4_successor.py's gates).
    from learnloop.algorithm_versions import ROUTER_OBJECTIVE_VERSIONS

    tagged = version in ROUTER_OBJECTIVE_VERSIONS
    on = mixture_env(tmp_path / "on", runtime(), version=version,
                     toml="[router_objective]\nenabled = false\n" if tagged else None)
    off = mixture_env(tmp_path / "off", runtime(), version=version, toml=OFF + ("enabled = false\n" if tagged else ""))
    steps = {}
    for name, env in (("on", on), ("off", off)):
        build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
        run(env)
        steps[name] = advance(env, serve=False)
    assert _scrub_step(steps["on"][1]) == _scrub_step(steps["off"][1]), "the next step"
    assert _blocks(steps["on"][0]) == _blocks(steps["off"][0]), "no display order changes"
    assert _first_difference(_rows(on), _rows(off)) is None
    assert _served(on) == _served(off)
    assert _new_rows(off) == dict.fromkeys(NEW_TABLES, 0)
    assert _new_rows(on)["decision_state_receipts"] >= 1
    with on.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(ask_available) FROM plan_presentations").fetchone()[0] >= 1
    with off.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(ask_available) FROM plan_presentations").fetchone()[0] == 0


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, config: str = ""):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    return ctx


def _replies(ctx):
    """What the desktop reads across one small session: every reply as the client gets it."""

    started = _call(ctx, "start_session", {"availableMinutes": 25})
    session = started["sessionId"]
    queue = _call(ctx, "get_today_queue", {"sessionId": session})
    ended = _call(ctx, "end_session", {"sessionId": session})
    return {"started": started, "queue": queue, "ended": ended}


def _plain(value):
    text = json.dumps(value, sort_keys=True, default=str)
    import re

    # Fresh ids and times differ by construction.
    text = re.sub(r"[0-9A-HJKMNP-TV-Z]{26}", "ULID", text)
    return re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z?", "TIME", text)


def test_the_desktops_replies_are_byte_identical_on_and_off(tmp_path):
    assert _plain(_replies(_sidecar(tmp_path / "on"))) == _plain(_replies(_sidecar(tmp_path / "off", OFF)))


def test_rebuild_leaves_the_receipts_alone(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    run(env)
    from learnloop.router_objective import sessions as S

    S.record_availability(env.vault, env.repository, "s1", clock=env.clock)
    S.record_end(env.vault, env.repository, "s1", clock=env.clock)

    def snapshot():
        with env.repository.connection() as connection:
            return {
                table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY id")]
                for table in NEW_TABLES
            } | {"asks": [tuple(row) for row in connection.execute(
                "SELECT id, ask_available FROM plan_presentations ORDER BY id")]}

    before = snapshot()
    assert before["decision_state_receipts"] and before["session_receipts"]
    rebuild_all_derived_state(load_vault(env.vault.root), env.repository)
    assert snapshot() == before
