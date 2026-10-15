"""Plan determinism landing onto main (docs/reviews/plan-determinism.md, "Landing onto main").

Main gained router R2b + R2c (``mvp-0.24``: Today's next block drawn from the
logged model mixture) and GLM-OCR after this branch's base. The compositions
checked here, at ``mvp-0.24``:

* **Staged mode** (``router.mode = "staged"``, and the mixture with no model
  set up, where the staged rule decides): the same vault state plans the same
  blocks in every session, Start's sessionless build included, and Begin keeps
  the block Start planned. Every outcome of the scheduler's draw, forced, is
  ignored.
* **The mixture.** The candidates it draws over (the staged rule's pick, the
  top-k support in its order, each candidate's items and planner value) are a
  fixed function of the vault state. Its own draw is untouched: each decision
  is seeded on its boundary key and its id, every logged propensity is
  recomputed exactly from the logged components (G3), the seed reproduces the
  two-stage draw, the epsilon floor holds (and binds where the models put no
  mass), and different seeds still draw different blocks.
* **The kill switch off** (``plan.deterministic_staged_plans = false``): the
  predecessor's scheduler session, so both session-seeded draws reach the
  staged plan (staged mode) and the mixture's candidates (mixture mode) again.
  Given its seed, the mixture's draw is the same with the switch on or off.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import learnloop.scheduling.scheduler as scheduler_module
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, ROUTER_MIXTURE_ALGORITHM_VERSION, ROUTER_MIXTURE_VERSIONS
from learnloop.daily_plan import router_runtime
from learnloop.daily_plan.engine import plan_scheduler_session, staged_plans_deterministic
from learnloop.daily_plan.policy import mixture_active
from learnloop.router import mixture as mx
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_daily_plan_vault
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, first_option, seed_with_first_uniform
from tests.test_plan_determinism import (  # noqa: F401 - ``frozen`` is a fixture
    EXTRA,
    FITS,
    PAIR,
    SWITCH_OFF,
    _copy,
    _first_served,
    _force,
    _pair_draw,
    _plan,
    _plan_at_start,
    frozen,
)

B = ROUTER_MIXTURE_ALGORITHM_VERSION
assert B == "mvp-0.24" and LATEST_ALGORITHM_VERSION in ROUTER_MIXTURE_VERSIONS
STAGED = '[router]\nmode = "staged"\n'
SESSIONS = tuple(f"s_{index:02d}" for index in range(16))


def _vault(tmp_path: Path, name: str, world: str, *, toml: str = "") -> tuple[Path, int]:
    """An ``mvp-0.24`` daily-plan vault: R1's near-ties (``EXTRA``) or a
    contrast pair (both members fit a block, or only one); returns its root
    and the plan's minutes."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    if world == "near_ties":
        paths = create_daily_plan_vault(tmp_path / name, version=B, learning_objects=EXTRA)
        minutes = 25
    else:
        item_minutes, minutes, _block = FITS[world]
        paths = create_daily_plan_vault(
            tmp_path / name, version=B, learning_objects={"lo_pair": [(item, item_minutes) for item in PAIR]}
        )
        for item_id, counterpart in (PAIR, PAIR[::-1]):
            path = paths.practice_item_path("linear-algebra", item_id)
            write_yaml(path, {**read_yaml(path), "contrast_of": counterpart})
    if toml:
        append_config_toml(paths.root, toml)
    return paths.root, minutes


def _decisions(root: Path) -> list[dict]:
    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.row_factory = sqlite3.Row
        found = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id"
        )]
    for row in found:
        for key in ("candidates_json", "detail_json", "mixture_weights_json", "model_distributions_json"):
            if row.get(key) is not None:
                row[key] = json.loads(row[key])
    return found


def _candidates(row: dict) -> tuple:
    """What the mixture draws over, apart from the draw: the staged pick, the
    support in its order and every candidate's lane, items and planner value."""

    detail = row["detail_json"]["mixture"]
    return (
        detail["staged_ref"],
        tuple(detail["support"]),
        tuple((entry["ref"], entry.get("lane"), tuple(entry.get("item_ids") or ()), entry.get("planner_value"))
              for entry in row["candidates_json"]),
    )


def _draw_of(row: dict) -> tuple:
    """The mixture's draw as logged: its seed, uniforms, component, choice and
    each candidate's propensity."""

    detail = row["detail_json"]["mixture"]
    return (row["seed"], detail["u1"], detail["u2"], detail["drawn_component"], row["chosen_ref"],
            row["propensity"], tuple((entry["ref"], entry["propensity"]) for entry in row["candidates_json"]))


def _models(row: dict) -> dict:
    return {name: dist for name, dist in row["model_distributions_json"].items() if dist}


def _exact(row: dict) -> None:
    """G3 on one logged decision: the propensity is recomputed exactly from the
    logged components, the seed reproduces the draw, and every option keeps
    the floor."""

    detail = row["detail_json"]["mixture"]
    assert row["policy"] == mx.POLICY and row["design"] == mx.DESIGN and row["propensity_kind"] == "exact"
    recomputed = mx.recompute({
        "support": detail["support"], "staged_ref": detail["staged_ref"], "chosen": row["chosen_ref"],
        "epsilon": detail["epsilon"], "effective_weights": row["mixture_weights_json"]["effective"],
        "distributions": _models(row),
    })
    assert recomputed == pytest.approx(row["propensity"], abs=1e-12)
    components = mx.component_distributions(detail["support"], detail["staged_ref"], _models(row))
    again = mx.draw(detail["support"], components, row["mixture_weights_json"]["effective"], detail["epsilon"],
                    row["seed"])
    assert (again.chosen, again.component, again.u1, again.u2) == (
        row["chosen_ref"], detail["drawn_component"], detail["u1"], detail["u2"])
    by_ref = {entry["ref"]: entry["propensity"] for entry in row["candidates_json"]}
    assert all(by_ref[ref] >= detail["epsilon"] - 1e-12 for ref in detail["support"])
    assert sum(by_ref[ref] for ref in detail["support"]) == pytest.approx(1.0, abs=1e-12)
    assert all(value == 0.0 for ref, value in by_ref.items() if ref not in detail["support"])


def _runtime(monkeypatch, *, seed=None, **models) -> None:
    monkeypatch.setattr(router_runtime, "_DEFAULT", fake_runtime(seed=seed, **models))


def _uniform_models() -> dict:
    return {"decider": FakeDecider(), "llm": FakeLLM()}


def _llm_on_the_first_option(request) -> dict:
    """The fake LLM's answer with all its block mass on the first option (the
    staged rule's pick leads the options)."""

    answer = dict(FakeLLM.default_answer(request))
    if "choose_block" in answer:
        refs = [entry["id"] for entry in answer["choose_block"]]
        answer["choose_block"] = [{"id": ref, "probability": 1.0 if index == 0 else 0.0}
                                  for index, ref in enumerate(refs)]
    return answer


# -- staged mode at mvp-0.24 ---------------------------------------------------------------


@pytest.mark.parametrize("world", ["near_ties", "both_fit", "one_fits"])
@pytest.mark.parametrize("mode", ["staged", "mixture_not_ready"])
def test_staged_plans_at_mvp024_are_the_same_in_every_session_and_at_start(tmp_path, frozen, monkeypatch, mode,
                                                                           world):
    """``router.mode = "staged"``, or the mixture with no model set up (the
    staged rule decides, ``decided_by = not_ready``): every session, and
    Start's sessionless build, plan one staged plan whose decisions are logged
    deterministic; Begin on Start's plan keeps Start's block. A contrast
    pair's order is the pair's own draw and is recorded with its seed."""

    _runtime(monkeypatch)  # no model set up
    template, minutes = _vault(tmp_path, "template", world, toml=STAGED if mode == "staged" else "")
    vault = load_vault(template)
    assert staged_plans_deterministic(vault) and mixture_active(vault) is (mode != "staged")
    shapes, recorded = set(), {}
    for sid in SESSIONS:
        root = _copy(template, tmp_path / sid)
        shapes.add(_plan(root, sid, minutes))
        recorded.update(_first_served(root))
    start = _copy(template, tmp_path / "start")
    at_start = _plan_at_start(start, minutes)
    shapes.add(at_start)
    assert len(shapes) == 1
    [(blocks, decisions, _projected)] = shapes
    assert {(row[2], row[3], row[5]) for row in decisions} == {(1.0, "deterministic", mx.STAGED_POLICY)}
    assert _plan(start, "s_begin", minutes)[0] == at_start[0]
    if world == "near_ties":
        assert blocks[0] == ("new", "staged", ("pi_extra_1", "pi_extra_2"))
        assert recorded == {}
        return
    first, second, seed = _pair_draw()
    assert blocks == (("new", "staged", FITS[world][2](first, second)),)
    assert recorded == {sid: (first, seed) for sid in SESSIONS}
    assert _first_served(start) == {"s_begin": (first, seed)}


@pytest.mark.parametrize("mode", ["staged", "mixture"])
@pytest.mark.parametrize("outcome", ["pi_extra_2", "pi_svd_define_001"])
def test_no_outcome_of_the_schedulers_draw_reaches_an_mvp024_plan(tmp_path, frozen, monkeypatch, mode, outcome):
    """Every outcome of R1's draw, forced: no plan build at ``mvp-0.24`` draws.
    The staged plan is the greedy one, and the mixture draws over the greedy
    candidates (its own seed pinned, so its draw is the same too)."""

    pinned = seed_with_first_uniform(at_least=0.2)
    _runtime(monkeypatch, seed=pinned, **(_uniform_models() if mode == "mixture" else {}))
    template, _minutes = _vault(tmp_path, "template", "near_ties", toml=STAGED if mode == "staged" else "")
    greedy_root = _copy(template, tmp_path / "greedy")
    greedy = _plan(greedy_root, "s_forced")
    drawn = _force(monkeypatch, outcome)
    forced_root = _copy(template, tmp_path / "forced")
    assert _plan(forced_root, "s_forced") == greedy
    assert drawn == []
    if mode == "mixture":
        [before], [after] = _decisions(greedy_root), _decisions(forced_root)
        assert _candidates(after) == _candidates(before) and _draw_of(after) == _draw_of(before)


# -- the mixture over a deterministic candidate order -------------------------------------


@pytest.mark.parametrize("world", ["near_ties", "both_fit"])
def test_the_mixture_draws_over_the_same_candidates_in_every_session(tmp_path, frozen, monkeypatch, world):
    """The mixture at ``mvp-0.24`` with both models answering (uniform
    distributions) and its own seeds (``seed_for(boundary key, decision id)``):
    every session and Start's build offer it the same staged pick and the same
    top-k support in the same order. Each decision's propensity is exact and
    reproducible from its log (G3), its seed is its own boundary key and id,
    and the floor holds."""

    _runtime(monkeypatch, **_uniform_models())
    template, minutes = _vault(tmp_path, "template", world)
    assert mixture_active(load_vault(template)) and staged_plans_deterministic(load_vault(template))
    offered, seeds = set(), set()
    roots = [(_copy(template, tmp_path / sid), sid) for sid in SESSIONS]
    for root, sid in roots:
        _plan(root, sid, minutes)
    start = _copy(template, tmp_path / "start")
    _plan_at_start(start, minutes)
    for root in [root for root, _sid in roots] + [start]:
        [row] = _decisions(root)
        assert row["mode"] == "mixture" and len(row["detail_json"]["mixture"]["support"]) > 1
        _exact(row)
        assert row["seed"] == mx.seed_for(row["detail_json"]["mixture"]["boundary_key"], row["id"])
        offered.add(_candidates(row))
        seeds.add(row["seed"])
    assert len(offered) == 1
    assert len(seeds) == len(SESSIONS) + 1  # each decision draws on its own seed
    [(staged_ref, support, candidates)] = offered
    assert support[0] == staged_ref
    if world == "both_fit":
        first, second, _seed = _pair_draw()
        assert dict((ref, items) for ref, _lane, items, _value in candidates)[staged_ref] == (first, second)


def test_different_seeds_still_draw_different_blocks_and_the_switch_leaves_the_draw_alone(tmp_path, frozen,
                                                                                         monkeypatch):
    """The mixture's exploration is its own: with one pinned seed per session,
    the sessions draw different blocks over the same candidates. The switch
    changes only the pool: with R1's draw forced to miss (so both pools are the
    greedy order), each session's decision is the same with the switch on or
    off, field for field."""

    on, _minutes = _vault(tmp_path, "on", "near_ties")
    off, _minutes = _vault(tmp_path, "off", "near_ties", toml=SWITCH_OFF)
    assert staged_plans_deterministic(load_vault(on)) and not staged_plans_deterministic(load_vault(off))
    _force(monkeypatch, None)  # the roll misses: no exploration either way
    chosen = set()
    for sid in SESSIONS:
        _runtime(monkeypatch, seed=lambda _key, _decision_id, sid=sid: f"pinned-{sid}", **_uniform_models())
        on_root, off_root = _copy(on, tmp_path / f"on_{sid}"), _copy(off, tmp_path / f"off_{sid}")
        _plan(on_root, sid)
        _plan(off_root, sid)
        [with_switch], [without] = _decisions(on_root), _decisions(off_root)
        _exact(with_switch)
        assert _candidates(with_switch) == _candidates(without)
        assert _draw_of(with_switch) == _draw_of(without)
        chosen.add(with_switch["chosen_ref"])
    assert len(chosen) > 1


def test_the_floor_binds_where_the_models_put_no_mass(tmp_path, frozen, monkeypatch):
    """Both models put all their mass on the staged rule's pick: every other
    option of the support is drawn with exactly epsilon (the floor binds), and
    a seed whose first uniform falls under ``k * epsilon`` takes the uniform
    branch (the floor is live, not only logged)."""

    template, _minutes = _vault(tmp_path, "template", "near_ties")
    epsilon = load_vault(template).config.router.epsilon_min
    _runtime(monkeypatch, decider=FakeDecider(choice=first_option), llm=FakeLLM(answer=_llm_on_the_first_option))
    root = _copy(template, tmp_path / "binds")
    _plan(root, "s_binds")
    [row] = _decisions(root)
    _exact(row)
    detail = row["detail_json"]["mixture"]
    k = len(detail["support"])
    by_ref = {entry["ref"]: entry["propensity"] for entry in row["candidates_json"]}
    assert by_ref[detail["staged_ref"]] == pytest.approx(1.0 - (k - 1) * epsilon, abs=1e-12)
    assert all(by_ref[ref] == pytest.approx(epsilon, abs=1e-12) for ref in detail["support"][1:])

    _runtime(monkeypatch, seed=seed_with_first_uniform(below=k * epsilon), **_uniform_models())
    root = _copy(template, tmp_path / "uniform")
    _plan(root, "s_uniform")
    [row] = _decisions(root)
    _exact(row)
    assert row["detail_json"]["mixture"]["drawn_component"] == mx.UNIFORM


# -- the kill switch at mvp-0.24 ----------------------------------------------------------


def test_the_plans_scheduler_session_at_mvp024(tmp_path):
    """At ``mvp-0.24`` the plan's session is greedy with the pair's own draw in
    both modes; off (or the router off), it is the predecessor's, field for
    field."""

    greedy = scheduler_module.SchedulerSession(
        session_id="s", available_minutes=25, seeded_exploration=False, contrast_order_seed="pair"
    )
    predecessor = scheduler_module.SchedulerSession(session_id="s", available_minutes=25)
    cases = {
        "mixture": ("", greedy),
        "staged": (STAGED, greedy),
        "mixture_off": (SWITCH_OFF, predecessor),
        "staged_off": (STAGED + SWITCH_OFF, predecessor),
        "router_off": ("[router]\nenabled = false\n", predecessor),
    }
    for name, (toml, expected) in cases.items():
        root, _minutes = _vault(tmp_path, name, "near_ties", toml=toml)
        assert plan_scheduler_session(load_vault(root), "s", 25.4) == expected, name


@pytest.mark.parametrize("mode", ["staged", "mixture"])
def test_with_the_switch_off_at_mvp024_the_schedulers_draw_reaches_the_plan_again(tmp_path, frozen, monkeypatch,
                                                                                  mode):
    """Off at ``mvp-0.24``: a forced draw of R1's moves the staged plan's first
    block (staged mode), or the staged pick and the support the mixture draws
    over (mixture mode), as on main before this landing."""

    _runtime(monkeypatch, seed=seed_with_first_uniform(at_least=0.2),
             **(_uniform_models() if mode == "mixture" else {}))
    toml = (STAGED if mode == "staged" else "") + SWITCH_OFF
    off, _minutes = _vault(tmp_path, "off", "near_ties", toml=toml)
    greedy_root = _copy(off, tmp_path / "greedy")
    greedy = _plan(greedy_root, "s_forced")  # no forcing yet: this session's roll misses
    drawn = _force(monkeypatch, "pi_extra_2")
    forced_root = _copy(off, tmp_path / "forced")
    forced = _plan(forced_root, "s_forced")
    assert drawn
    if mode == "staged":
        assert forced[0][0][:2] == ("new", "staged") and forced[0][0][2][0] == "pi_extra_2"
        assert forced[0][0] != greedy[0][0]
        return
    [before], [after] = _decisions(greedy_root), _decisions(forced_root)
    _exact(after)
    assert _candidates(after) != _candidates(before)
    staged_items = dict((ref, items) for ref, _lane, items, _value in _candidates(after)[2])
    assert staged_items[_candidates(after)[0]][0] == "pi_extra_2"


@pytest.mark.parametrize("mode", ["staged", "mixture"])
def test_with_the_switch_off_at_mvp024_a_contrast_pair_follows_the_session_again(tmp_path, frozen, monkeypatch,
                                                                                 mode):
    """Off at ``mvp-0.24``: the pair's order is drawn per session again (both
    orders across the sessions, each session's seed recorded), and Start's
    sessionless build keeps the greedy order, unrecorded."""

    from learnloop.diagnosis import contrast_pairs

    _runtime(monkeypatch, seed=seed_with_first_uniform(at_least=0.2),
             **(_uniform_models() if mode == "mixture" else {}))
    toml = (STAGED if mode == "staged" else "") + SWITCH_OFF
    off, minutes = _vault(tmp_path, "off", "both_fit", toml=toml)
    staged_blocks, recorded = set(), {}
    for sid in SESSIONS:
        root = _copy(off, tmp_path / sid)
        _plan(root, sid, minutes)
        recorded.update(_first_served(root))
        [row] = _decisions(root)
        if mode == "mixture":
            _exact(row)
            staged_ref, _support, candidates = _candidates(row)
            staged_blocks.add(dict((ref, items) for ref, _lane, items, _value in candidates)[staged_ref])
        else:
            staged_blocks.add(tuple(_plan_blocks(root)[0]))
    assert {PAIR, PAIR[::-1]} <= staged_blocks
    key = contrast_pairs.pair_key(*PAIR)
    assert {sid: seed for sid, (_first, seed) in recorded.items()} == {
        sid: contrast_pairs.serving_seed(key, session_id=sid) for sid in SESSIONS
    }
    start = _copy(off, tmp_path / "start")
    _plan_at_start(start, minutes)
    assert _first_served(start) == {}
    [row] = _decisions(start)
    if mode == "mixture":
        staged_ref, _support, candidates = _candidates(row)
        assert dict((ref, items) for ref, _lane, items, _value in candidates)[staged_ref] == tuple(sorted(PAIR))
    else:
        assert tuple(_plan_blocks(start)[0]) == tuple(sorted(PAIR))


def _plan_blocks(root: Path) -> list[list[str]]:
    from learnloop.daily_plan.engine import load_records
    from learnloop.db.repositories import Repository

    return [[item.practice_item_id for item in block.items]
            for record in load_records(Repository(root / "state.sqlite")) for block in record.blocks]
