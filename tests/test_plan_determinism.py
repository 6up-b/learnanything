"""Plan determinism (docs/reviews/plan-determinism.md).

Owner rule (2026-10-13): staged plans are deterministic; the router's
exploration comes only from the mixture's logged floor. A plan's pool is the
scheduler's ranked list, and the scheduler's seeded exploration (router R1's
``scheduler_seeded_exploration``: with probability
``scheduler.selection_exploration_rate`` a near-tie moves to the front, hashed
from the session id, the UTC date and the candidate ids) reordered that pool,
so the same vault state planned different blocks for different sessions while
the ``plan_block`` row logged a deterministic choice. That made
``test_reader_rw3a_landing``'s 25-minute case fail about one run in ten (each
run's session id is a fresh ULID).

* Where the router composes Today (``mvp-0.23`` with the router on) the pool
  is the scheduler's greedy order (``daily_plan.engine.plan_scheduler_session``):
  the same vault state plans the same blocks in every session, and the plan's
  builds never draw.
* DL1's own pair (the router switched off, or a vault below ``mvp-0.23``)
  keeps the scheduler's draw exactly (G8). That draw is a logged design: its
  seed material (session, UTC date, candidate ids), rate and window, the
  design probabilities and the realized outcome are on the slate each plan
  build writes, and they reproduce the plan's pick.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

import learnloop.clock as clock_module
import learnloop.scheduling.scheduler as scheduler_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import load_records, plan_scheduler_session
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import append_config_toml, create_daily_plan_vault

A = ROUTER_STAGED_FRAME_ALGORITHM_VERSION
FROZEN = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
#: The placement vault plus two one-minute items on a third LO: their
#: selection rewards make near-ties (``pi_extra_1`` heads the greedy order;
#: ``pi_extra_2`` and ``pi_svd_define_001`` are within the reward window and,
#: drawn, change the first block), so the draw has outcomes that matter.
EXTRA = {"lo_extra": [("pi_extra_1", 1.0), ("pi_extra_2", 1.0)]}
ROUTER_OFF = "[router]\nenabled = false\n"
SESSIONS = tuple(f"s_{index:02d}" for index in range(30))


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)


def _template(tmp_path: Path, name: str, *, toml: str | None = None) -> Path:
    paths = create_daily_plan_vault(tmp_path / name, version=A, learning_objects=EXTRA)
    if toml:
        append_config_toml(paths.root, toml)
    return paths.root


def _copy(template: Path, destination: Path) -> Path:
    copy_tree_with_databases(template, destination)
    return destination


def _open_session(root: Path, session_id: str) -> None:
    """A session with a fixed id (the scheduler's draw hashes it)."""

    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE ended_at IS NULL", ("2026-10-12T08:59:00Z",))
        connection.execute(
            "INSERT INTO sessions(id, started_at, available_minutes) VALUES (?, '2026-10-12T09:00:00Z', 25)",
            (session_id,),
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


def _plan(root: Path, session_id: str) -> tuple:
    _open_session(root, session_id)
    view = _call(_context(root), "get_daily_plan", {"sessionId": session_id})
    return _shape(root, view)


def _slates(root: Path, session_id: str) -> list[dict]:
    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.row_factory = sqlite3.Row
        slates = []
        for slate in connection.execute(
            "SELECT id, created_at, config_snapshot_json FROM scheduler_slates WHERE session_id = ? "
            "ORDER BY created_at, id", (session_id,),
        ):
            candidates = [
                {"practice_item_id": row["practice_item_id"], "rank": row["rank"],
                 "exploration_flag": row["exploration_flag"], **json.loads(row["components_json"])}
                for row in connection.execute(
                    "SELECT practice_item_id, rank, exploration_flag, components_json "
                    "FROM scheduler_slate_candidates WHERE slate_id = ? ORDER BY rank", (slate["id"],),
                )
            ]
            slates.append({"created_at": slate["created_at"],
                           "config": json.loads(slate["config_snapshot_json"]), "candidates": candidates})
    return slates


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


# -- staged plans are deterministic ---------------------------------------------------


def test_the_same_vault_state_plans_the_same_staged_blocks_in_every_session(tmp_path, frozen):
    """Thirty sessions (thirty seeds of the scheduler's draw) on copies of one
    vault state: one staged plan, its decisions logged deterministic. Under
    DL1's pair the same sessions plan several (the draw is live there), so the
    sessions do exercise it."""

    staged = _template(tmp_path, "staged")
    dl1 = _template(tmp_path, "dl1", toml=ROUTER_OFF)
    staged_shapes = {_plan(_copy(staged, tmp_path / f"staged_{sid}"), sid) for sid in SESSIONS}
    dl1_shapes = {_plan(_copy(dl1, tmp_path / f"dl1_{sid}"), sid) for sid in SESSIONS}
    assert len(staged_shapes) == 1
    [(blocks, decisions, _projected)] = staged_shapes
    assert blocks[0] == ("new", "staged", ("pi_extra_1", "pi_extra_2"))
    assert {(row[2], row[3], row[5]) for row in decisions} == {(1.0, "deterministic", "staged_v1")}
    assert len(dl1_shapes) > 1


@pytest.mark.parametrize("outcome", ["pi_extra_2", "pi_svd_define_001"])
def test_a_staged_plan_never_takes_the_schedulers_draw(tmp_path, frozen, monkeypatch, outcome):
    """Every outcome of the draw, forced: the staged plan's builds never draw
    and plan the greedy blocks; their slates log the greedy design (one on the
    head, no realized exploration). DL1's pair takes the same forced outcome
    and plans differently (G8 keeps it)."""

    staged = _template(tmp_path, "staged")
    dl1 = _template(tmp_path, "dl1", toml=ROUTER_OFF)
    greedy = _plan(_copy(staged, tmp_path / "greedy"), "s_greedy")
    dl1_greedy = _plan(_copy(dl1, tmp_path / "dl1_greedy"), "s_greedy")
    drawn = _force(monkeypatch, outcome)
    root = _copy(staged, tmp_path / "forced")
    assert _plan(root, "s_forced") == greedy
    assert drawn == []
    slates = _slates(root, "s_forced")
    assert slates
    for slate in slates:
        head, *rest = slate["candidates"]
        assert head["base_selection_propensity"] == 1.0
        assert all(row["base_selection_propensity"] == 0.0 and not row["exploration_flag"] for row in rest)
    dl1_forced = _plan(_copy(dl1, tmp_path / "dl1_forced"), "s_forced")
    assert drawn and dl1_forced[0] != dl1_greedy[0]
    assert dl1_forced[0][0][2][0] == outcome
    assert dl1_greedy[0] == tuple((lane, "lane_quota", items) for lane, _by, items in greedy[0])


def test_the_plans_scheduler_session_is_greedy_only_where_the_router_composes_today(tmp_path):
    staged = load_vault(_template(tmp_path, "staged"))
    dl1 = load_vault(_template(tmp_path, "dl1", toml=ROUTER_OFF))
    below = load_vault(create_daily_plan_vault(tmp_path / "below", version="mvp-0.22").root)
    assert plan_scheduler_session(staged, "s", 25.4).seeded_exploration is False
    assert plan_scheduler_session(dl1, "s", 25.4).seeded_exploration is True
    assert plan_scheduler_session(below, "s", 25.4).seeded_exploration is True
    assert plan_scheduler_session(staged, "s", 25.4).available_minutes == 25


def test_a_greedy_scheduler_session_never_draws_and_logs_the_greedy_design(tmp_path, frozen, monkeypatch):
    """The scheduler's own switch: with ``seeded_exploration`` off a build
    whose draw would explore (forced) keeps the greedy order, and every place
    that reads the draw's support agrees (the logged design is one on the head)."""

    root = _template(tmp_path, "dl1", toml=ROUTER_OFF)
    vault, repository = load_vault(root), Repository(root / "state.sqlite")
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))

    def build(explore: bool) -> list:
        session = scheduler_module.SchedulerSession(session_id="s_x", available_minutes=25, seeded_exploration=explore)
        return scheduler_module.build_due_queue(vault, repository, session=session, limit=None,
                                                persist_explanations=False)

    explored, greedy = build(True), build(False)
    assert explored[0].components.get("exploration_selected") == 1.0
    promoted = explored[0].practice_item_id
    assert promoted != greedy[0].practice_item_id
    assert [item.practice_item_id for item in explored[1:]] == [
        item.practice_item_id for item in greedy if item.practice_item_id != promoted
    ]
    assert not any(item.components.get("exploration_selected") for item in greedy)
    session = scheduler_module.SchedulerSession(session_id="s_x", seeded_exploration=False)
    assert scheduler_module._exploration_support(greedy, session, vault.config) is None
    propensities = scheduler_module._selection_propensities(greedy, session, vault.config)
    assert propensities[greedy[0].practice_item_id] == 1.0 and sum(propensities.values()) == 1.0


# -- DL1's draw is a logged design, reproduced from its log ---------------------------


def _greedy_queue(root: Path, session_id: str) -> list:
    vault = load_vault(root)
    return scheduler_module.build_due_queue(
        vault, Repository(root / "state.sqlite"),
        session=scheduler_module.SchedulerSession(session_id=session_id, available_minutes=25,
                                                  seeded_exploration=False),
        limit=None, persist_explanations=False,
    )


def _draw(session_id: str, now: datetime, ids: list[str], alternative_ids: list[str]) -> tuple[float, float]:
    return (scheduler_module._stable_fraction("roll", session_id, now, ids),
            scheduler_module._stable_fraction("choice", session_id, now, alternative_ids))


def test_dl1s_draw_is_seeded_from_logged_state_and_its_log_reproduces_the_pick(tmp_path, frozen):
    """The first fixed session whose seeded draw explores (found from the
    vault's greedy order, which a build with the draw off gives). Its plan
    build's slate logs the seed material, the rate and window, each
    candidate's design probability and the realized outcome; recomputing the
    draw from them gives the item the build promoted and the plan's first
    block chose."""

    template = _template(tmp_path, "dl1", toml=ROUTER_OFF)
    design = load_vault(template).config.scheduler
    greedy = _greedy_queue(_copy(template, tmp_path / "greedy"), "s_probe")
    greedy_ids = [item.practice_item_id for item in greedy]
    best_reward = greedy[0].components["selection_reward"]
    alternatives = [item.practice_item_id for item in greedy[1:]
                    if best_reward - item.components["selection_reward"] <= design.selection_exploration_reward_window]
    leading = {"pi_extra_2", "pi_svd_define_001"}  # the outcomes that change the first block

    def drawn(choice: float) -> str:
        return alternatives[min(int(choice * len(alternatives)), len(alternatives) - 1)]

    session_id, promoted = next(
        (sid, drawn(choice))
        for sid in (f"s_{index:03d}" for index in range(400))
        for roll, choice in [_draw(sid, FROZEN, greedy_ids, alternatives)]
        if roll < design.selection_exploration_rate and drawn(choice) in leading
    )
    root = _copy(template, tmp_path / "plan")
    blocks, decisions, _projected = _plan(root, session_id)

    [slate, *_later] = _slates(root, session_id)
    rate = slate["config"]["selection_exploration_rate"]
    window = slate["config"]["selection_exploration_reward_window"]
    now = datetime.fromisoformat(slate["created_at"].replace("Z", "+00:00"))
    logged = {row["practice_item_id"]: row for row in slate["candidates"]}
    # The design, from the log: the greedy head keeps 1 - rate, each near-tie
    # within the window gets rate / n.
    head = next(item for item, row in logged.items() if row["base_selection_propensity"] == pytest.approx(1 - rate))
    logged_alternatives = sorted(item for item, row in logged.items()
                                 if item != head and row["base_selection_propensity"] > 0)
    assert logged_alternatives == sorted(
        item for item, row in logged.items()
        if item != head and logged[head]["selection_reward"] - row["selection_reward"] <= window
    )
    assert all(logged[item]["base_selection_propensity"] == pytest.approx(rate / len(logged_alternatives))
               for item in logged_alternatives)
    # The draw, from the logged seed material (session, UTC date, candidate ids).
    roll, choice = _draw(session_id, now, sorted(logged), logged_alternatives)
    assert roll < rate
    ordered = [item for item in greedy_ids if item in logged_alternatives]  # the greedy order of the near-ties
    reproduced = ordered[min(int(choice * len(ordered)), len(ordered) - 1)]
    [flagged] = [item for item, row in logged.items() if row["exploration_flag"]]
    assert reproduced == flagged == promoted
    # The plan's first block leads with the promoted item, and its decision names it.
    assert blocks[0][2][0] == promoted
    assert decisions[0][1] == promoted
