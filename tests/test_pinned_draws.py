"""The suite's default for the router's seeded draws (``tests/pinned_draws.py``; refactor step T3).

A test without ``real_draws`` draws on seeds fixed by its node id and the order of its distinct boundaries, and the
numeric policy runs one batch of draws; with the marker, production's seeds (fresh ids) and refinement come back.
The journey here is the objective path at the head with no model set up (the sidecar's runtime), where the numeric
policy holds the whole mix: the case the D-21 sweep found drawing a stop or an offer at random.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.daily_plan import objective_chooser
from learnloop.router_objective import checks, mix
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests import pinned_draws
from tests.helpers import create_daily_plan_vault

DAY = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
LEARNING_OBJECTS = {f"lo_draw_{index}": [(f"pi_draw_{index}_{n}", 2.0) for n in range(2)] for index in range(3)}
STEPS = 4


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _journey(root: Path, monkeypatch) -> tuple[list[tuple], list[str]]:
    """Up to ``STEPS`` served steps of one plan, each answered "I don't know"; returns each plan-block decision's
    (policy, chosen item, chosen learning object) in order, and their seeds."""

    moment = [DAY]
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: moment[0])
    ctx = SidecarContext()
    try:
        ctx.load(root)
        ctx.grading_provider_override = "manual"
        session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
        for index in range(STEPS):
            step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
            if not step or step["kind"] != "item":
                break
            moment[0] += timedelta(minutes=2)
            _call(ctx, "submit_dont_know", {
                "sessionId": session_id, "practiceItemId": step["practiceItemId"], "latencySeconds": 60,
                "submissionId": f"sub_{index}", "schedulerCandidateId": step.get("schedulerCandidateId"),
            })
    finally:
        ctx.close()
    with sqlite3.connect(root / "state.sqlite") as connection:
        rows = connection.execute(
            "SELECT policy, chosen_practice_item_id, chosen_learning_object_id, seed FROM router_decisions "
            "WHERE decision_kind = 'plan_block' ORDER BY created_at, rowid").fetchall()
    connection.close()
    # (the build's first block, with one option, draws nothing and has no seed)
    return [tuple(row[:3]) for row in rows], [row[3] for row in rows if row[3] is not None]


def _vault(tmp_path: Path, name: str):
    return create_daily_plan_vault(tmp_path / name, learning_objects=LEARNING_OBJECTS)


@pytest.mark.slow  # two journeys on the objective path, about 10 s each
def test_the_same_scenario_built_twice_draws_the_same_choices(tmp_path, request, monkeypatch):
    first, first_seeds = _journey(_vault(tmp_path, "first").root, monkeypatch)
    # What the next run of this test starts from: the same key, the counts at zero.
    pinned_draws.begin(request.node.nodeid)
    second, second_seeds = _journey(_vault(tmp_path, "second").root, monkeypatch)
    assert first and first == second
    assert first_seeds == second_seeds and all(first_seeds)
    assert len(set(first_seeds)) == len(first_seeds)  # each decision still draws on its own seed


@pytest.mark.real_draws
def test_with_the_marker_seeds_are_productions_and_vary(tmp_path, monkeypatch):
    assert not pinned_draws.active()
    _first, first_seeds = _journey(_vault(tmp_path, "first").root, monkeypatch)
    _second, second_seeds = _journey(_vault(tmp_path, "second").root, monkeypatch)
    assert first_seeds and second_seeds and not set(first_seeds) & set(second_seeds)


def test_the_map_keeps_productions_equalities_and_differences(request):
    production = pinned_draws.production("learnloop.router_objective.mix", "seed_for")
    a, again, b = mix.seed_for("key", "d1"), mix.seed_for("key", "d1"), mix.seed_for("key", "d2")
    assert a == again and a != b
    assert len(a) == len(production("key", "d1")) and a != production("key", "d1")
    assert a == pinned_draws.pinned_seed(request.node.nodeid, "objective_mix", 0, len(a))
    # Another family counts on its own: its first seed is its own 0.
    assert checks.day_seed("2026-10-12") == pinned_draws.pinned_seed(request.node.nodeid, "check", 0, len(a))


def test_the_numeric_policy_runs_one_batch(monkeypatch):
    seen = {}

    def production(*_args, **kwargs):
        seen.update(kwargs)

    wrapped = pinned_draws._numeric_wrapper(production)
    wrapped(None, None, keep_going=lambda: True, deadline=5.0)
    assert seen == {"keep_going": None, "deadline": 5.0}
    assert objective_chooser.run_numeric.__wrapped__ is pinned_draws.production(*pinned_draws.NUMERIC_POLICY)
