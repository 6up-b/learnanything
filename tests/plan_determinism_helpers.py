"""What other test files use from ``tests/test_plan_determinism.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

import learnloop.clock as clock_module
import learnloop.scheduling.scheduler as scheduler_module
from learnloop.daily_plan.engine import load_records
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY


FROZEN = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
#: The placement vault plus two one-minute items on a third LO: their
#: selection rewards make near-ties (``pi_extra_1`` heads the greedy order;
#: ``pi_extra_2`` and ``pi_svd_define_001`` are within the reward window and,
#: drawn, change the first block), so the draw has outcomes that matter.
EXTRA = {"lo_extra": [("pi_extra_1", 1.0), ("pi_extra_2", 1.0)]}
#: The kill switch (Codex review F2): off, the staged plan's pool is
#: mvp-0.23's as it landed (both session-seeded draws).
SWITCH_OFF = "[plan]\ndeterministic_staged_plans = false\n"


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)


def _copy(template: Path, destination: Path) -> Path:
    copy_tree_with_databases(template, destination)
    return destination


def _open_session(root: Path, session_id: str, minutes: int = 25) -> None:
    """A session with a fixed id (the scheduler's draw hashes it). Its minutes
    are the first plan's budget (the last session's minutes)."""

    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE ended_at IS NULL", ("2026-10-12T08:59:00Z",))
        connection.execute(
            "INSERT INTO sessions(id, started_at, available_minutes) VALUES (?, '2026-10-12T09:00:00Z', ?)",
            (session_id, minutes),
        )


def _context(root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx


def _shape(root: Path, view: dict) -> tuple:
    """The plan apart from ids and times: its blocks, their logged decisions
    and the blocks the view projects after them."""

    records = load_records(Repository(root / "state.sqlite"))
    blocks = tuple(
        (block.lane, block.chosen_by, tuple(item.practice_item_id for item in block.items))
        for record in records for block in record.blocks
    )
    with sqlite3.connect(root / "state.sqlite") as connection:
        decisions = tuple(connection.execute(
            "SELECT chosen_ref, chosen_practice_item_id, propensity, propensity_kind, learner_pick, policy "
            "FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id"
        ).fetchall())
    projected = json.dumps(view["plan"]["projected"], sort_keys=True)
    return blocks, decisions, projected


def _plan(root: Path, session_id: str, minutes: int = 25) -> tuple:
    _open_session(root, session_id, minutes)
    view = _call(_context(root), "get_daily_plan", {"sessionId": session_id})
    return _shape(root, view)


def _plan_at_start(root: Path, minutes: int = 25) -> tuple:
    """Start's build (``StartScreen``'s ``useDailyPlan(null)``): the plan is
    built and persisted with no session. The last session (ended) carries the
    minutes Start remembers."""

    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE ended_at IS NULL", ("2026-10-12T08:00:00Z",))
        connection.execute(
            "INSERT INTO sessions(id, started_at, ended_at, available_minutes) "
            "VALUES ('s_earlier', '2026-10-12T07:30:00Z', '2026-10-12T08:00:00Z', ?)",
            (minutes,),
        )
    view = _call(_context(root), "get_daily_plan", {"sessionId": None})
    return _shape(root, view)


def _force(monkeypatch, outcome: str | None) -> list[str]:
    """The scheduler's own draw seam: the roll lands on ``outcome`` (an
    alternative's item id) when it is an alternative, and misses otherwise."""

    drawn: list[str] = []

    def draws(queue, session, now, alternatives):
        ids = [item.practice_item_id for item in alternatives]
        drawn.append(",".join(ids))
        if outcome not in ids:
            return 1.0, 0.0
        return 0.0, (ids.index(outcome) + 0.5) / len(ids)

    monkeypatch.setattr(scheduler_module, "_exploration_draws", draws)
    return drawn


PAIR = ("pi_pair_a", "pi_pair_b")
#: ``(item expected minutes, session minutes, the staged plan's block from
#: the pair's (first, second))``: both members fit one block (1.5 estimated
#: minutes each in 25), or only one fits (a five-minute plan, each member 4.5
#: expected minutes plus the default 0.5 of feedback).
FITS = {
    "both_fit": (1.0, 25, lambda first, second: (first, second)),
    "one_fits": (4.5, 5, lambda first, _second: (first,)),
}


def _first_served(root: Path) -> dict[str, tuple[str, str]]:
    """The pair's recorded member order (A4's serving rows): the member
    served first and the draw's seed, per session."""

    with sqlite3.connect(root / "state.sqlite") as connection:
        rows = connection.execute(
            "SELECT session_id, practice_item_id, randomization_seed FROM contrast_pair_servings "
            "WHERE serve_position = 0 ORDER BY created_at, id"
        ).fetchall()
    return {session_id: (item_id, seed) for session_id, item_id, seed in rows}


def _pair_draw() -> tuple[str, str, str]:
    """The pair's own draw (seeded on the pair alone): ``(first, second, seed)``."""

    from learnloop.diagnosis import contrast_pairs

    seed = contrast_pairs.serving_seed(contrast_pairs.pair_key(*PAIR), session_id=None,
                                       scope=contrast_pairs.SEED_PER_PAIR)
    low, high = sorted(PAIR)
    first, second = (low, high) if contrast_pairs.randomization_draw(seed) < 0.5 else (high, low)
    return first, second, seed
