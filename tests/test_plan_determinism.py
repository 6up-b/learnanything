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

The Codex review (docs/reviews/plan-determinism-codex-review.md):

* F1: a contrast pair's member order (Meas §3.A4) was a second
  session-seeded draw in the pool, so a staged plan still chose a different
  member, or ordered a block differently, by session. A staged plan now draws
  it per pair (seeded on the pair alone, still recorded for A4's check), and
  every other queue build keeps the per-session draw. The re-review's F1:
  Start's build has no session, and it skipped the pair's draw; it now takes
  it (and writes no serving row), so Start plans what every session plans.
* F2: the rule is a live change behind ``plan.deterministic_staged_plans``
  (the owner's standing ruling for serving changes replay never reads), not a
  successor tag. Off, the staged plan's pool is built under the predecessor's
  scheduler session, both draws per session again; replay never reads it.
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
#: The kill switch (Codex review F2): off, the staged plan's pool is
#: mvp-0.23's as it landed (both session-seeded draws).
SWITCH_OFF = "[plan]\ndeterministic_staged_plans = false\n"
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
    # Start builds the plan with no session (re-review F1): the same plan.
    staged_shapes.add(_plan_at_start(_copy(staged, tmp_path / "staged_start")))
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
    switched_off = load_vault(_template(tmp_path, "off", toml=SWITCH_OFF))
    assert plan_scheduler_session(staged, "s", 25.4) == scheduler_module.SchedulerSession(
        session_id="s", available_minutes=25, seeded_exploration=False, contrast_order_seed="pair"
    )
    # Everywhere else the predecessor's session, field for field.
    predecessor = scheduler_module.SchedulerSession(session_id="s", available_minutes=25)
    for vault in (dl1, below, switched_off):
        assert plan_scheduler_session(vault, "s", 25.4) == predecessor


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


# -- contrast pairs: a staged plan's member order is the pair's own (Codex review F1) --

PAIR = ("pi_pair_a", "pi_pair_b")
#: ``(item expected minutes, session minutes, the staged plan's block from
#: the pair's (first, second))``: both members fit one block (1.5 estimated
#: minutes each in 25), or only one fits (a five-minute plan, each member 4.5
#: expected minutes plus the default 0.5 of feedback).
FITS = {
    "both_fit": (1.0, 25, lambda first, second: (first, second)),
    "one_fits": (4.5, 5, lambda first, _second: (first,)),
}


def _pair_template(tmp_path: Path, name: str, item_minutes: float, *, toml: str | None = None) -> Path:
    """The placement vault plus one LO whose two items are a contrast pair
    (Meas §3.A4: each names the other in ``contrast_of``)."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths = create_daily_plan_vault(
        tmp_path / name, version=A, learning_objects={"lo_pair": [(item, item_minutes) for item in PAIR]}
    )
    for item_id, counterpart in (PAIR, PAIR[::-1]):
        path = paths.practice_item_path("linear-algebra", item_id)
        write_yaml(path, {**read_yaml(path), "contrast_of": counterpart})
    if toml:
        append_config_toml(paths.root, toml)
    return paths.root


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


@pytest.mark.parametrize("fit", sorted(FITS))
def test_a_contrast_pair_plans_the_same_staged_block_in_every_session(tmp_path, frozen, fit):
    """Codex review F1. A contrast pair's member order (Meas §3.A4) was drawn
    per session, seeded on the session and the pair, and the plan packs its
    pool in that order. So when both members fit a block, the block's order
    and its logged choice varied by session; when only one fits, the plan
    chose either member. Every one was logged deterministic (propensity one).

    In a staged plan the order is the pair's own draw, seeded on the pair
    alone: thirty sessions on copies of one vault state plan one block with one
    logged choice, and each session's serving row records that order and its
    seed for A4's order-effect check. DL1's pair keeps the per-session draws
    (G8): the same thirty sessions plan both orders there (and, where R1's
    draw promotes a near-tie, other blocks).

    Re-review F1: Start builds and persists the plan with no session
    (``useDailyPlan(null)``), and the scheduler left a sessionless queue in
    its greedy order, so Start planned ``[pi_pair_a, pi_pair_b]`` (or chose
    ``pi_pair_a`` alone) where every named session planned the pair's own
    draw. The pair's draw needs no session, so Start plans the same block; it
    writes no serving row (there is no session to key one on), and the session
    Begin opens records the order Start planned."""

    item_minutes, minutes, block = FITS[fit]
    staged = _pair_template(tmp_path, "staged", item_minutes)
    dl1 = _pair_template(tmp_path, "dl1", item_minutes, toml=ROUTER_OFF)
    staged_shapes, recorded = set(), {}
    for sid in SESSIONS:
        root = _copy(staged, tmp_path / f"staged_{sid}")
        staged_shapes.add(_plan(root, sid, minutes))
        recorded.update(_first_served(root))
    start = _copy(staged, tmp_path / "staged_start")
    at_start = _plan_at_start(start, minutes)
    staged_shapes.add(at_start)
    assert _first_served(start) == {}
    assert len(staged_shapes) == 1
    [(blocks, decisions, _projected)] = staged_shapes
    first, second, seed = _pair_draw()
    assert blocks == (("new", "staged", block(first, second)),)
    assert [(row[1], row[2], row[3], row[5]) for row in decisions] == [(first, 1.0, "deterministic", "staged_v1")]
    assert recorded == {sid: (first, seed) for sid in SESSIONS}
    # Begin on Start's plan: the session keeps the block Start planned, and
    # its serving row records that order and the pair's seed.
    assert _plan(start, "s_begin", minutes)[0] == at_start[0]
    assert _first_served(start) == {"s_begin": (first, seed)}

    dl1_blocks = {_plan(_copy(dl1, tmp_path / f"dl1_{sid}"), sid, minutes)[0] for sid in SESSIONS}
    assert {(("new", "lane_quota", block(*PAIR)),), (("new", "lane_quota", block(*PAIR[::-1])),)} <= dl1_blocks


def test_the_per_session_draw_keeps_its_own_path(tmp_path, frozen):
    """A4's per-session draw is unchanged everywhere but the staged plan's
    pool: a queue build under the scheduler's default session (Today's full
    list, ``skip_practice_item``, the CLI and TUI queues, DL1's plan) on the
    same staged vault orders the pair by session and records that session's
    seed."""

    from learnloop.diagnosis import contrast_pairs

    root = _pair_template(tmp_path, "staged", 1.0)
    vault, repository = load_vault(root), Repository(root / "state.sqlite")
    firsts = set()
    for sid in SESSIONS:
        queue = scheduler_module.build_due_queue(
            vault, repository, session=scheduler_module.SchedulerSession(session_id=sid, available_minutes=25),
            limit=None, persist_explanations=False,
        )
        firsts.add(next(item.practice_item_id for item in queue if item.practice_item_id in PAIR))
    assert firsts == set(PAIR)
    key = contrast_pairs.pair_key(*PAIR)
    assert {sid: seed for sid, (_first, seed) in _first_served(root).items()} == {
        sid: contrast_pairs.serving_seed(key, session_id=sid) for sid in SESSIONS
    }


# -- the kill switch, not a successor (Codex review F2) -------------------------------


def test_the_switch_acts_only_where_the_router_composes_today(tmp_path):
    """``plan.deterministic_staged_plans`` (default on) acts where the router
    composes Today. A vault whose config predates the key (every existing
    ``mvp-0.23`` vault) reads it on; off keeps the version and the staged
    frame, and so does the router's own switch, which returns DL1's pair."""

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.daily_plan.engine import staged_plans_deterministic
    from learnloop.daily_plan.policy import router_active

    from tests.helpers import set_algorithm_version

    paths = create_daily_plan_vault(tmp_path / "vault", version="mvp-0.14")
    assert "deterministic_staged_plans" not in (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    for version, flag in {"mvp-0.14": False, "mvp-0.22": False, A: True, LATEST_ALGORITHM_VERSION: True}.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert vault.config.plan.deterministic_staged_plans is True
        assert staged_plans_deterministic(vault) is flag, version
    off = load_vault(_template(tmp_path, "off", toml=SWITCH_OFF))
    assert staged_plans_deterministic(off) is False
    assert off.config.algorithms.algorithm_version == A and router_active(off)
    assert staged_plans_deterministic(load_vault(_template(tmp_path, "router_off", toml=ROUTER_OFF))) is False
    assert staged_plans_deterministic(load_vault(_template(tmp_path, "plan_off", toml="[plan]\nenabled = false\n"))) is False


def test_with_the_switch_off_the_schedulers_draw_reaches_the_staged_plan_again(tmp_path, frozen, monkeypatch):
    """Rollback parity, R1's draw: off, the staged plan's pool is built under
    the predecessor's session (the call ``6dabbc33c`` made, compared field for
    field above), so a forced draw moves the staged plan's first block as it
    did before the fix, and the build draws."""

    staged = _template(tmp_path, "staged")
    off = _template(tmp_path, "off", toml=SWITCH_OFF)
    greedy = _plan(_copy(staged, tmp_path / "greedy"), "s_forced")
    assert _plan(_copy(off, tmp_path / "off_greedy"), "s_forced")[0] == greedy[0]  # the roll missed: same plan
    drawn = _force(monkeypatch, "pi_extra_2")
    assert _plan(_copy(staged, tmp_path / "on_forced"), "s_forced")[0] == greedy[0]
    assert drawn == []
    blocks, _decisions, _projected = _plan(_copy(off, tmp_path / "off_forced"), "s_forced")
    assert drawn
    assert blocks[0][:2] == ("new", "staged") and blocks[0][2][0] == "pi_extra_2"
    assert blocks[0] != greedy[0][0]


def test_with_the_switch_off_a_contrast_pair_follows_the_session_again(tmp_path, frozen):
    """Rollback parity, A4's draw: off, the staged plan orders the pair by
    session (both orders across thirty sessions) and records each session's
    seed, as before the fix. Start's sessionless build leaves the pair in the
    greedy order, unrecorded, as before the re-review's fix."""

    from learnloop.diagnosis import contrast_pairs

    item_minutes, minutes, block = FITS["both_fit"]
    off = _pair_template(tmp_path, "off", item_minutes, toml=SWITCH_OFF)
    shapes, recorded = set(), {}
    for sid in SESSIONS:
        root = _copy(off, tmp_path / f"off_{sid}")
        shapes.add(_plan(root, sid, minutes)[0])
        recorded.update(_first_served(root))
    assert {(("new", "staged", block(*PAIR)),), (("new", "staged", block(*PAIR[::-1])),)} <= shapes
    key = contrast_pairs.pair_key(*PAIR)
    assert {sid: seed for sid, (_first, seed) in recorded.items()} == {
        sid: contrast_pairs.serving_seed(key, session_id=sid) for sid in SESSIONS
    }
    start = _copy(off, tmp_path / "off_start")
    assert _plan_at_start(start, minutes)[0] == (("new", "staged", block(*sorted(PAIR))),)
    assert _first_served(start) == {}


def test_every_defaults_snapshot_records_the_switch_on():
    """Each recorded snapshot moves only because the effective config gains
    the key (default on); none records it off."""

    import tomllib

    from learnloop.algorithm_versions import SUCCESSOR_CHAIN
    from learnloop.config.schema import LearnLoopConfig
    from learnloop.config.template import (
        DEFAULTS_SNAPSHOT_BY_ALGORITHM,
        default_config_text,
        defaults_fingerprint_for_version,
    )

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
        config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(version)))
        assert config.plan.deterministic_staged_plans is True, version


def test_replay_never_reads_the_switch(tmp_path):
    """On the migration-head fixture at the latest tag: a rebuild with the
    switch on and one with it off leave every DERIVED table the same, and
    neither writes a plan row (a plan is a workflow row replay never reads)."""

    from datetime import UTC as _UTC

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.clock import FrozenClock
    from learnloop.daily_plan.engine import staged_plans_deterministic
    from learnloop.db.connection import connect
    from learnloop.db.table_roles import TableRole, tables_for_role
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    from tests.helpers import _set_algorithm_version_at

    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_217"
    clock = FrozenClock(datetime(2026, 10, 14, 12, 0, tzinfo=_UTC))
    root = tmp_path / "head"
    copy_tree_with_databases(head, root)
    _set_algorithm_version_at(root, LATEST_ALGORITHM_VERSION)
    repository = Repository(root / "state.sqlite")
    derived = sorted(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                    for table in derived}

    assert staged_plans_deterministic(load_vault(root))
    rebuild_all_derived_state(load_vault(root), repository, clock=clock)
    rebuild_all_derived_state(load_vault(root), repository, clock=clock)
    switched_on = snapshot()
    append_config_toml(root, SWITCH_OFF)
    assert not staged_plans_deterministic(load_vault(root))
    rebuild_all_derived_state(load_vault(root), repository, clock=clock)
    assert snapshot() == switched_on
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("SELECT COUNT(*) FROM daily_plans").fetchone()[0] == 0
