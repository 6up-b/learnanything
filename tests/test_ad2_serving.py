"""Adaptive difficulty AD2: the serving (spec_adaptive_difficulty_v1 §14 AD2, "The serving"; G-AD2-19..31).

Each failed before AD2 for the reason the spec names: no slot draw (the plan
served its planned item), no ``ad_selections``, no deferral (a displaced item
returned to the pool), the generation prompt carried the band instruction. All
through the real plan engine on synthetic plan vaults; fakes only, no model call.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import timedelta
from typing import Any

import pytest

from learnloop.adaptive_difficulty import selection as S
from learnloop.daily_plan import ad_slot
from learnloop.daily_plan.engine import advance, build_plan, day_records, keep_going, load_records
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import (
    LO,
    ad23_vault,
    answer,
    block_events,
    env_for,
    reveal,
    rows,
    selections,
    set_item,
)
from tests.daily_plan_fakes import iso

HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
ROUTER_OFF = "[router]\nenabled = false\n"
ROUTER_STAGED = "[router]\nmode = \"staged\"\n"


def _plan(tmp_path, items, *, config: str = ROUTER_OFF, features: dict | None = None, budget: float = 3.0,
          minutes: dict[str, float] | None = None, ad: str = ""):
    paths = ad23_vault(tmp_path, items=items, features=features, config=config, ad=ad)
    for item_id, value in (minutes or {}).items():
        set_item(paths, item_id, expected_minutes=value)
    env, clock = env_for(paths, items=items)
    record = build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
    return paths, env, clock, record


def _serve_rows(paths) -> list[dict[str, Any]]:
    return selections(paths, kind="serve")


# -- G-AD2-19 -----------------------------------------------------------------------------------


def test_propensity_recomputes_from_logged_row(tmp_path):
    """A draw's propensities recompute exactly from its logged row (scores, constants, seed)."""

    paths, env, _clock, _record = _plan(tmp_path, ("pi_h", "pi_e1", "pi_e2"), features={"pi_h": HARD})
    _record, step = advance(env, serve=True)
    (row,) = _serve_rows(paths)
    redone = S.recompute(row)
    assert {k: round(v, 12) for k, v in redone.propensities.items()} == {
        entry["ref"]: entry["propensity"] for entry in row["support"]}
    assert redone.chosen == row["chosen_item_id"] == step["practice_item_id"]
    assert row["propensity"] == pytest.approx(redone.propensity, abs=1e-12)
    assert sum(entry["propensity"] for entry in row["support"]) == pytest.approx(1.0, abs=1e-9)


def test_seed_reproduces_draw():
    """The seed is ``sha256(design:key)`` and reproduces the draw; another key may differ."""

    scored = [S.Scored(f"i{k}", 0.40 + 0.01 * k, 0.70, 0.1) for k in range(6)]
    first = S.draw(scored, key="block:3")
    assert first.seed == S.seed_for(S.SELECT_VERSION, "block:3")
    assert S.draw(scored, key="block:3") == first
    draws = {S.draw(scored, key=f"block:{k}").chosen for k in range(40)}
    assert len(draws) > 1  # the near-tie set and the overlap share randomize


# -- G-AD2-20 -----------------------------------------------------------------------------------


def _generation_prompt(paths) -> tuple[Any, str]:
    from learnloop.content.authoring.practice_generation import (
        _practice_expansion_instructions,
        build_practice_expansion_plan,
    )

    vault = load_vault(paths.root)
    plan = build_practice_expansion_plan(vault, Repository(paths.sqlite_path), learning_object_ids=[LO],
                                         require_completed_probe=False)
    return plan, _practice_expansion_instructions(plan, extra_instructions=None)


def test_generation_prompt_has_no_band_language_under_successor(tmp_path):
    """Under the successor with ``generation_contract`` on, the prompt asks for an item AT the
    commissioned point and drops every band instruction and the target's band field (§7.1).
    Fails before AD2: the prompt told the model to calibrate to the 70-85% band."""

    from learnloop.adaptive_difficulty.generation import CONTRACT_TEXT

    paths = ad23_vault(tmp_path / "on", items=("pi_g1",))
    plan, text = _generation_prompt(paths)
    (target,) = plan.targets
    assert target.ad_commission_id is not None
    assert "recommended_difficulty_band" not in json.dumps(target.as_dict())
    assert "recommended_difficulty_band" not in text and "Calibrate" not in text
    assert "difficulty band" not in text and "70-85%" not in text
    assert CONTRACT_TEXT in text and "NEVER change the waypoint" in text
    # The commissioned point bounds every dimension (max = the point): the gate rejects overshoot.
    assert target.rung.source == "ad_commission"
    assert all(bound["max"] == target.rung.task_features[dim] for dim, bound in target.rung.task_feature_bounds.items())
    (commission,) = selections(paths, kind="commission")
    assert commission["id"] == target.ad_commission_id and commission["chosen_point"]
    # Below the tag, or with the switch off, today's prompt exactly.
    for name, version, ad in (("below", "mvp-0.27", ""), ("off", "mvp-0.28", "generation_contract = false\n")):
        other = ad23_vault(tmp_path / name, items=("pi_g1",), version=version, ad=ad)
        plan_b, text_b = _generation_prompt(other)
        assert plan_b.targets[0].ad_commission_id is None
        assert "recommended_difficulty_band" in json.dumps(plan_b.targets[0].as_dict())
        assert "Calibrate each item's difficulty to its target's recommended_difficulty_band" in text_b
        assert CONTRACT_TEXT not in text_b
        assert not selections(other)


# -- G-AD2-21 -----------------------------------------------------------------------------------


def _served_sequence(tmp_path, name: str, *, version: str, ad: str) -> list[Any]:
    items = ("pi_h", "pi_e1", "pi_e2", "pi_e3")
    paths = ad23_vault(tmp_path / name, items=items, features={"pi_h": HARD}, version=version,
                       config=ROUTER_OFF, ad=ad)
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    sequence = []
    for _ in range(6):
        record, step = advance(env, serve=True)
        sequence.append({key: step.get(key) for key in ("kind", "practice_item_id", "learning_object_id", "position")})
        if step["kind"] != "item":
            break
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    records = [{"blocks": [[(i.practice_item_id, i.est_minutes, i.position, i.displaced_reason) for i in b.items]
                           for b in r.blocks], "status": r.status} for r in day_records(env)]
    return [sequence, records, selections(paths)]


def test_selection_switch_off_restores_lane_order(tmp_path):
    """With ``selection = false`` the plan, its order and every served item are the predecessor's
    (``mvp-0.27``) exactly, and no draw is written; with it on, AD substitutes the hard slot."""

    before = _served_sequence(tmp_path, "pred", version="mvp-0.27", ad="")
    off = _served_sequence(tmp_path, "off", version="mvp-0.28", ad="selection = false\n")
    on = _served_sequence(tmp_path, "on", version="mvp-0.28", ad="")
    assert off[:2] == before[:2] and not off[2] and not before[2]
    assert on[2] and on[0][0]["practice_item_id"] != before[0][0]["practice_item_id"]


# -- G-AD2-22 -----------------------------------------------------------------------------------


def test_exam_reserved_and_retired_items_never_selected(tmp_path, monkeypatch):
    """An exam-reserved and a retired candidate are never in the support (check 0)."""

    paths, env, _clock, _record = _plan(tmp_path, ("pi_h", "pi_e1", "pi_e2", "pi_e3"), features={"pi_h": HARD})
    set_item(paths, "pi_e3", status="retired")
    env.vault = load_vault(paths.root)
    real = ad_slot._exclusions

    def reserved(env_: Any) -> Any:
        from dataclasses import replace

        found = real(env_)
        return replace(found, reserved_exam_item_ids=found.reserved_exam_item_ids | {"pi_e1"})

    monkeypatch.setattr(ad_slot, "_exclusions", reserved)
    _record, step = advance(env, serve=True)
    (row,) = _serve_rows(paths)
    refs = {entry["ref"] for entry in row["support"]}
    failed = {entry["ref"]: entry["failed"] for entry in row["excluded"]}
    assert "pi_e1" not in refs and "exam_reserved" in failed["pi_e1"]
    assert "pi_e3" not in refs and "pi_e3" not in {c for c in failed if "retired" not in failed[c]}
    assert step["practice_item_id"] not in ("pi_e1", "pi_e3")


def test_coordination_requires_envelope(tmp_path):
    """A coordination item is never in the support without a reviewed envelope, nor is an item
    authored above the default trajectory's depth envelope."""

    paths, env, _clock, _record = _plan(tmp_path, ("pi_h", "pi_c", "pi_x"), features={"pi_h": HARD})
    set_item(paths, "pi_c", capability="coordination")
    set_item(paths, "pi_x", task_features={**HARD, "complexity": 4})
    env.vault = load_vault(paths.root)
    _record, step = advance(env, serve=True)
    (row,) = _serve_rows(paths)
    failed = {entry["ref"]: entry["failed"] for entry in row["excluded"]}
    assert "envelope" in failed["pi_x"]
    assert "pi_c" not in {entry["ref"] for entry in row["support"]}
    assert step["practice_item_id"] == "pi_h"


# -- G-AD2-23 -----------------------------------------------------------------------------------


def test_calibrate_mode_prefers_overlap_band():
    """With ``max P_band < calibrate_below`` (0.25, amendment A17) the draw calibrates: the most
    informative item of the overlap set (near-ties within 5% relative), mixed with the overlap
    share (§6.2)."""

    scored = [S.Scored("a", 0.20, 0.60, 0.15), S.Scored("b", 0.24, 0.95, 0.40), S.Scored("c", 0.10, 0.70, 0.30),
              S.Scored("d", 0.10, 0.80, 0.296)]
    mode, pi, tied, overlap, q = S.propensities(scored)
    assert mode == S.MODE_CALIBRATE
    assert overlap == ("a", "c", "d") and tied == ("c", "d") and q == 0.10
    assert pi["b"] == 0.0  # outside the overlap band, however informative
    assert pi["c"] == pytest.approx(0.45 + 0.10 / 3) and pi["a"] == pytest.approx(0.10 / 3)
    assert sum(pi.values()) == pytest.approx(1.0)


def test_calibrate_with_empty_overlap_picks_nearest_to_band():
    """With the overlap set empty, the item whose ``p̄`` is nearest ``[0.55, 0.90]``, ties by id."""

    scored = [S.Scored("z", 0.01, 0.30, 0.2), S.Scored("y", 0.02, 0.50, 0.1), S.Scored("x", 0.02, 0.50, 0.3),
              S.Scored("w", 0.01, 0.97, 0.5)]
    mode, pi, tied, overlap, q = S.propensities(scored)
    assert mode == S.MODE_CALIBRATE and overlap == () and q == 0.0
    assert tied == ("x",) and pi["x"] == 1.0  # y ties x at 0.05 from the band; ties by id


# -- G-AD2-24 / G-AD2-29 --------------------------------------------------------------------------


def test_joint_propensity_logged_with_router_block(tmp_path):
    """The draw logs ``π_router`` beside ``π_AD`` and the pair's ``π_router · π_AD`` (§10.1)."""

    paths, env, _clock, record = _plan(tmp_path, ("pi_h", "pi_e1", "pi_e2"), features={"pi_h": HARD},
                                       config=ROUTER_STAGED)
    block = record.blocks[0]
    _record, _step = advance(env, serve=True)
    (row,) = _serve_rows(paths)
    expected = ad_slot.router_propensity(record, block)
    assert row["router_propensity"] == pytest.approx(expected)
    assert row["pair_propensity"] == pytest.approx(expected * row["propensity"])
    assert row["block_id"] == block.id and row["slot_position"] == block.items[0].position


def _first_block(tmp_path, name: str, ad: str) -> tuple[Any, Any]:
    paths, env, _clock, record = _plan(tmp_path / name, ("pi_h", "pi_e1", "pi_e2"), features={"pi_h": HARD},
                                       config=ROUTER_STAGED, ad=ad)
    decisions = rows(paths.sqlite_path, "SELECT candidates_json, chosen_ref, chosen_practice_item_id, propensity, "
                                        "propensity_kind FROM router_decisions WHERE decision_kind = 'plan_block' "
                                        "ORDER BY created_at")
    _record, step = advance(env, serve=True)
    return (paths, env, step), decisions


def test_draw_after_block_choice_with_pair_propensity(tmp_path):
    """AD draws only at a ``new_admitted`` slot of the block the router chose, inside the serve;
    the router's candidates and propensity are byte-identical with AD on vs off; the
    substitution folds into the plan record."""

    (paths_on, env_on, step_on), decisions_on = _first_block(tmp_path, "on", "")
    (paths_off, _env_off, step_off), decisions_off = _first_block(tmp_path, "off", "selection = false\n")
    assert decisions_on == decisions_off and decisions_on
    assert step_off["practice_item_id"] == "pi_h" and step_on["practice_item_id"] != "pi_h"
    (event,) = block_events(paths_on, "item_substituted")
    assert event["detail"]["slot_item_id"] == "pi_h" and event["detail"]["practice_item_id"] == step_on["practice_item_id"]
    (record,) = day_records(env_on)
    slot = record.blocks[0].items[0]
    assert slot.practice_item_id == step_on["practice_item_id"] and slot.substituted_from == "pi_h"
    assert slot.ad_selection_id == _serve_rows(paths_on)[0]["id"]
    # The substitution event precedes the item's serve in the block's ledger.
    ordered = rows(paths_on.sqlite_path, "SELECT kind FROM attention_block_events WHERE block_id = ? "
                                         "ORDER BY event_ordinal", (record.blocks[0].id,))
    kinds = [r["kind"] for r in ordered]
    assert kinds.index("item_substituted") < kinds.index("item_served")


# -- G-AD2-25 -----------------------------------------------------------------------------------


def _land(paths, item_id: str, features: dict, at: str, *, capability: str, **extra: Any) -> None:
    """A generated item landing for the commission's cell (a copy of the LO's item at ``features``)."""

    import yaml

    from tests.ad_fakes import stamp_task_features
    from tests.helpers import write_yaml

    payload = yaml.safe_load(paths.practice_item_path("linear-algebra", "pi_g1").read_text(encoding="utf-8"))
    payload.update({"id": item_id, "created_at": at, "updated_at": at, "prompt": f"Question {item_id}."})
    write_yaml(paths.practice_item_path("linear-algebra", item_id), payload)
    stamp_task_features(paths, item_id, features, difficulty_source="llm_estimate", **extra)
    set_item(paths, item_id, capability=capability)


def test_commission_result_appended_never_mutates_selection(tmp_path):
    """A landed commissioned item gets an ``ad_commission_results`` receipt, ``in_band`` when its
    re-forecast ``p̄`` lies in ``[0.55, 0.90]`` and ``realized_out_of_band`` otherwise; the
    selection row is never mutated, and an out-of-band item, though in the pool, is not served
    on account of the commission (§7.4)."""

    from datetime import datetime

    from learnloop.adaptive_difficulty.generation import record_landed_commissions, rung_features

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    before = dict(commission)
    point = {**rung_features(commission["chosen_point"]), "tools": ["closed_book"]}
    landed_at = (datetime.fromisoformat(commission["created_at"].replace("Z", "+00:00")) + timedelta(hours=1))
    at = landed_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    # The generator's own estimate says very hard (z_llm = 2.5): the re-forecast reads it.
    _land(paths, "pi_land", point, at, capability=commission["cell_capability"], difficulty=1.0)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    later = (landed_at + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with repository.atomic():
        written = record_landed_commissions(vault, repository, repository.connection(), now=later)
    assert len(written) == 1
    (result,) = ad_serving.commission_results(repository.connection())
    assert result["selection_id"] == commission["id"] and result["practice_item_id"] == "pi_land"
    assert result["status"] == ("in_band" if 0.55 <= result["p_bar"] <= 0.90 else "realized_out_of_band")
    assert result["features"]["complexity"] == point.get("complexity", result["features"]["complexity"])
    assert selections(paths, kind="commission")[0] == before
    assert ad_serving.open_commissions(repository.connection()) == []
    with closing(connect(paths.sqlite_path)) as connection:
        for sql in ("UPDATE ad_selections SET mode = 'band'", "DELETE FROM ad_commission_results"):
            with pytest.raises(Exception, match="append-only"):
                connection.execute(sql)
    with repository.atomic():
        assert record_landed_commissions(vault, repository, repository.connection(), now=later) == []
    # The commission names no item to serve: no serve draw references it.
    assert commission["chosen_item_id"] is None
    assert all(row["chosen_item_id"] != "pi_land" or row["kind"] == "serve" for row in selections(paths))


# -- G-AD2-26 -----------------------------------------------------------------------------------


def test_serve_propensity_is_over_existing_items(tmp_path):
    """A serve draw's support is items that exist (its propensity enters off-policy evaluation);
    a commission draw's is feature points, logged apart and never multiplied into a serve."""

    paths, env, _clock, _record = _plan(tmp_path, ("pi_h", "pi_e1", "pi_e2"), features={"pi_h": HARD})
    advance(env, serve=True)
    vault = load_vault(paths.root)
    for row in _serve_rows(paths):
        assert all(entry["ref"] in vault.practice_items for entry in row["support"])
        assert row["chosen_item_id"] in vault.practice_items
    for row in selections(paths, kind="commission"):
        assert all(entry["ref"].startswith("point:") for entry in row["support"])
        assert row["chosen_item_id"] is None and row["pair_propensity"] is None


def test_empty_overlap_sets_q_zero():
    scored = [S.Scored("a", 0.50, 0.95), S.Scored("b", 0.45, 0.96)]
    mode, pi, tied, overlap, q = S.propensities(scored)
    assert mode == S.MODE_BAND and overlap == () and q == 0.0
    assert pi == {"a": 0.5, "b": 0.5}


def test_empty_support_makes_no_draw_and_displaces(tmp_path):
    """No candidate passes: no draw; the row records ``empty_support`` and each failed check, and
    the slot is displaced with ``ad_ineligible``."""

    paths, env, clock, _record = _plan(tmp_path, ("pi_a",))
    reveal(paths, "pi_a", amount=0.1, at=iso(clock.now() - timedelta(hours=2)))
    _record, step = advance(env, serve=True)
    (row,) = _serve_rows(paths)
    assert row["empty_support"] == 1 and row["mode"] == "empty_support" and row["chosen_item_id"] is None
    assert row["excluded"] == [{"ref": "pi_a", "failed": ["recent_reveal"]}]
    (event,) = block_events(paths, "item_displaced")
    assert event["detail"]["reason"] == "ad_ineligible" and event["detail"]["failed"] == ["recent_reveal"]
    assert step["kind"] == "done"


def test_empty_pool_commissions_at_generation(tmp_path):
    """A cell with no servable item (so no slot) gets a commission where generation picks a
    waypoint (``generation_contract``)."""

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    set_item(paths, "pi_g1", status="retired")
    plan, _text = _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    assert plan.targets and plan.targets[0].ad_commission_id == commission["id"]
    assert commission["cell_capability"] == plan.targets[0].rung.capability and commission["chosen_point"]


# -- G-AD2-27 / G-AD2-28 --------------------------------------------------------------------------


def test_item_over_block_budget_not_in_support(tmp_path):
    """An otherwise eligible item whose estimate exceeds the slot item's plus the slack is not in
    ``S``; after any substitution the block stays within 15 minutes and the plan within its
    budget. Fails before AD2: no slot substitution existed."""

    paths, env, _clock, record = _plan(tmp_path, ("pi_h", "pi_long", "pi_e1"), features={"pi_h": HARD},
                                       minutes={"pi_long": 6.0})
    advance(env, serve=True)
    (row,) = _serve_rows(paths)
    failed = {entry["ref"]: entry["failed"] for entry in row["excluded"]}
    assert "over_block_budget" in failed["pi_long"]
    (after,) = day_records(env)
    assert after.minutes_planned() <= 3.0 + 1e-9
    assert all(block.est_minutes() <= 15.0 + 1e-9 for block in after.blocks)


def test_support_respects_constraints_reversibility_and_admission(tmp_path, monkeypatch):
    """An item the constraint engine refuses, one holding an open cold check or a reserved
    surface, one planned in another of today's plans, and a costlier item for a floor-admitted
    slot are never in ``S``."""

    from learnloop.daily_plan import staged_frame

    items = ("pi_h", "pi_refused", "pi_cold", "pi_reserved", "pi_planned", "pi_cost", "pi_ok")
    paths, env, _clock, record = _plan(tmp_path, items, features={"pi_h": HARD}, config=ROUTER_STAGED,
                                       minutes={"pi_cost": 2.4})
    real_material = staged_frame.StagedFrame.material

    def material(self: Any, candidates: Any) -> Any:
        from dataclasses import replace

        found = real_material(self, candidates)
        return replace(found, refusals={**dict(found.refusals), "pi_refused": ({"constraint": "fake_refusal"},)},
                       cold_items=frozenset(set(found.cold_items or ()) | {"pi_cold"}),
                       reserved_items=frozenset(set(found.reserved_items or ()) | {"pi_reserved"}))

    monkeypatch.setattr(staged_frame.StagedFrame, "material", material)
    real_build = ad_slot.build_request

    class _Planned:
        def __init__(self, item_id: str) -> None:
            self.practice_item_id, self.displaced = item_id, False

    class _OtherPlan:
        id = "other_plan"

        @staticmethod
        def items() -> list[Any]:
            return [_Planned("pi_planned")]

    def build(env_: Any, record_: Any, block: Any, slot: Any, built: Any, **kwargs: Any) -> Any:
        record_.row["admission"] = {**record_.admission, "floor_applied": True}  # the slot came in by the floor
        kwargs["day"] = [*list(kwargs.get("day") or ()), _OtherPlan()]
        return real_build(env_, record_, block, slot, built, **kwargs)

    monkeypatch.setattr(ad_slot, "build_request", build)
    advance(env, serve=True)
    (row,) = _serve_rows(paths)
    failed = {entry["ref"]: entry["failed"] for entry in row["excluded"]}
    support = {entry["ref"] for entry in row["support"]}
    assert any(f.startswith("constraint:") for f in failed["pi_refused"])
    assert "open_cold_check" in failed["pi_cold"] and "reserved_surface" in failed["pi_reserved"]
    assert "planned_elsewhere" in failed["pi_planned"] and "admission_load" in failed["pi_cost"]
    assert not support & {"pi_refused", "pi_cold", "pi_reserved", "pi_planned", "pi_cost"}
    assert "pi_ok" in support


# -- G-AD2-30 -----------------------------------------------------------------------------------


@pytest.mark.parametrize("change", ["exam_reserved", "cold_followup", "recent_reveal", "pre_exposure", "refused"])
@pytest.mark.parametrize("who", ["slot", "other"])
def test_support_rechecked_at_draw_slot_item_included(tmp_path, monkeypatch, change, who):
    """Every check is re-read at the draw, never taken from the block's admission: the slot item
    (or another candidate) that became exam-reserved, gained an open cold follow-up, was revealed
    within the cold retrieval delay, reached the pre-exposure threshold, or is refused on a fresh
    snapshot is not in ``S``. A slot item with no other candidate is displaced with
    ``ad_ineligible``, except in the pre-exposure-only case, served with ``mode = predecessor``
    and ``π_AD = 1``. Fails before AD2: reconciliation re-checked only status and serving blocks."""

    from learnloop.daily_plan import staged_frame

    items = ("pi_h", "pi_e1") if who == "other" else ("pi_h",)
    paths, env, clock, record = _plan(tmp_path, items, features={"pi_h": HARD},
                                      config=ROUTER_STAGED if change == "refused" else ROUTER_OFF)
    target = "pi_h" if who == "slot" else "pi_e1"
    if change == "exam_reserved" or change == "cold_followup":
        real = ad_slot._exclusions
        field = "reserved_exam_item_ids" if change == "exam_reserved" else "cold_check_reserved_item_ids"

        def changed(env_: Any) -> Any:
            from dataclasses import replace

            found = real(env_)
            return replace(found, **{field: getattr(found, field) | {target}})

        monkeypatch.setattr(ad_slot, "_exclusions", changed)
    elif change == "recent_reveal":
        reveal(paths, target, amount=0.1, at=iso(clock.now() - timedelta(hours=1)))
    elif change == "pre_exposure":
        reveal(paths, target, amount=0.5, at=iso(clock.now() - timedelta(days=3)))
    else:
        real_material = staged_frame.StagedFrame.material

        def material(self: Any, candidates: Any) -> Any:
            from dataclasses import replace

            found = real_material(self, candidates)
            return replace(found, refusals={**dict(found.refusals), target: ({"constraint": "fresh_refusal"},)})

        monkeypatch.setattr(staged_frame.StagedFrame, "material", material)
    _record, step = advance(env, serve=True)
    (row,) = _serve_rows(paths)
    assert target not in {entry["ref"] for entry in row["support"]}
    failed = {entry["ref"]: entry["failed"] for entry in row["excluded"]}
    expected = {"exam_reserved": "exam_reserved", "cold_followup": "cold_check_reserved",
                "recent_reveal": "recent_reveal", "pre_exposure": "pre_exposed"}.get(change)
    assert (expected in failed[target]) if expected else any(f.startswith("constraint:") for f in failed[target])
    if who == "other":
        assert step["kind"] == "item" and step["practice_item_id"] == "pi_h"
    elif change == "pre_exposure":
        assert row["mode"] == "predecessor" and row["propensity"] == 1.0 and step["practice_item_id"] == "pi_h"
        assert rows(paths.sqlite_path, "SELECT pre_exposed FROM item_serve_inputs")[0]["pre_exposed"] == 1
    else:
        assert row["mode"] == "empty_support" and step["kind"] != "item"
        (event,) = block_events(paths, "item_displaced")
        assert event["detail"]["reason"] == "ad_ineligible" and "pre_exposed" not in event["detail"]["failed"]


def test_switch_off_serves_the_planned_item_whatever_changed(tmp_path):
    """With ``selection = false`` the predecessor serves the planned item byte-identically."""

    paths, env, clock, _record = _plan(tmp_path, ("pi_h",), features={"pi_h": HARD}, ad="selection = false\n")
    reveal(paths, "pi_h", amount=0.1, at=iso(clock.now() - timedelta(hours=1)))
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_h"
    assert not selections(paths) and not block_events(paths, "item_displaced")


# -- G-AD2-31 -----------------------------------------------------------------------------------


def _advance_n(env: Any, paths: Any, clock: Any, n: int, *, answer_items: bool = True) -> list[dict[str, Any]]:
    steps = []
    for _ in range(n):
        _record, step = advance(env, serve=True)
        steps.append(step)
        if step["kind"] != "item":
            continue
        clock.advance(2)
        if answer_items:
            answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return steps


@pytest.mark.parametrize("router", ["off", "staged"])
def test_ineligible_displacement_defers_until_condition_clears(tmp_path, router):
    """The verify's scenario (final verify F10): a five-minute never-attempted ordinary item ``a``
    with a partial reveal below the auto-prime threshold and no substitutes is displaced once with
    ``ad_ineligible`` (``recent_reveal``); across 20 further advances no block holds it, and with no
    other work the plan closes as complete; the projection never plans it; a keep-going plan the
    same day excludes it; the plan record rebuilt from its events gives the same exclusion set.
    Fails before AD2: a displaced item returned to the pool."""

    from learnloop.daily_plan.engine import _context_from_build, simulate_blocks

    config = ROUTER_OFF if router == "off" else ROUTER_STAGED
    paths, env, clock, record = _plan(tmp_path, ("pi_a",), budget=6.0, minutes={"pi_a": 4.5}, config=config)
    reveal(paths, "pi_a", amount=0.2, at=iso(clock.now() - timedelta(minutes=30)))
    steps = _advance_n(env, paths, clock, 21)
    displaced = block_events(paths, "item_displaced")
    assert len(displaced) == 1 and displaced[0]["detail"]["failed"] == ["recent_reveal"]
    (plan,) = day_records(env)
    assert plan.status == "complete" and all(step["kind"] != "item" for step in steps)
    assert not [item for block in plan.blocks for item in block.items
                if item.practice_item_id == "pi_a" and not item.displaced]
    assert set(plan.ad_deferrals()) == {"pi_a"}
    rebuilt = load_records(env.repository, [plan.id])[0]
    assert rebuilt.exclusion_ids() == plan.exclusion_ids() and "pi_a" in rebuilt.exclusion_ids()
    extension = keep_going(env)
    assert all(item.practice_item_id != "pi_a" for block in extension.blocks for item in block.items)


def _readmission_env(tmp_path):
    items = ("pi_a", "pi_w1", "pi_w2", "pi_w3")
    paths = ad23_vault(tmp_path, items=items, config=ROUTER_OFF, learning_objects={"lo_other": ("pi_o1", "pi_o2")})
    env, clock = env_for(paths, items=items + ("pi_o1", "pi_o2"))
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    return paths, env, clock


def _serve_until(env: Any, paths: Any, clock: Any, steps: int) -> list[str]:
    served = []
    for _ in range(steps):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        served.append(step["practice_item_id"])
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return served


def _deferral_details(env: Any) -> list[dict[str, Any]]:
    return [block.chosen["ad_deferrals"] for plan in day_records(env) for block in plan.blocks
            if (block.chosen or {}).get("ad_deferrals")]


def test_deferral_readmits_after_the_reveal_window(tmp_path):
    """With other work in the plan, ``a`` stays out while its reveal is within the cold retrieval
    delay and rejoins the pool at the first boundary after it (fake clock, the same day), where
    AD may draw it; each boundary's decision records the deferrals it applied and cleared."""

    from learnloop.daily_plan.engine import advance_with_context, simulate_blocks

    paths, env, clock = _readmission_env(tmp_path)
    reveal(paths, "pi_a", amount=0.2, at=iso(clock.now() - timedelta(hours=23, minutes=30)))
    first = _serve_until(env, paths, clock, 1)
    record, _step, context = advance_with_context(env, serve=False)
    projected = simulate_blocks(record, context, env.policy)
    assert projected and all(item.practice_item_id != "pi_a" for _d, block in projected for item in block.items)
    first += _serve_until(env, paths, clock, 3)
    assert "pi_a" not in first
    assert _deferral_details(env)[0] == {"applied": ["pi_a"], "cleared": []}
    clock.advance(45)  # the reveal is now older than the delay; still today
    later = _serve_until(env, paths, clock, 6)
    details = _deferral_details(env)
    assert any(detail["cleared"] == ["pi_a"] for detail in details)
    assert "pi_a" in later
    (plan,) = day_records(env)
    assert "pi_a" not in plan.ad_deferrals()


def test_cold_followup_hold_readmits_once_the_task_closes(tmp_path, monkeypatch):
    """An item held by an open cold follow-up is readmitted at the first boundary after the task
    closes (the hold re-read with the draw's own check)."""

    paths, env, clock = _readmission_env(tmp_path)
    held = {"open": True}
    real = ad_slot._exclusions

    def exclusions(env_: Any) -> Any:
        from dataclasses import replace

        found = real(env_)
        if held["open"]:
            return replace(found, cold_check_reserved_item_ids=found.cold_check_reserved_item_ids | {"pi_a"})
        return found

    monkeypatch.setattr(ad_slot, "_exclusions", exclusions)
    first = _serve_until(env, paths, clock, 3)
    assert "pi_a" not in first
    (event,) = block_events(paths, "item_displaced")
    assert event["detail"]["failed"] == ["cold_check_reserved"]
    held["open"] = False  # the follow-up served its item or was cancelled
    later = _serve_until(env, paths, clock, 6)
    assert any(detail["cleared"] == ["pi_a"] for detail in _deferral_details(env)) and "pi_a" in later


def test_deferral_switch_off_serves_the_item(tmp_path):
    """With ``selection = false`` nothing is displaced or deferred: the predecessor serves ``a``."""

    items = ("pi_a",)
    paths = ad23_vault(tmp_path, items=items, config=ROUTER_OFF, ad="selection = false\n")
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=6.0, remembered=6, minutes_source="chip")
    reveal(paths, "pi_a", amount=0.2, at=iso(clock.now() - timedelta(minutes=30)))
    assert _serve_until(env, paths, clock, 3) == ["pi_a"]
    assert not block_events(paths, "item_displaced") and not selections(paths)


def test_why_this_item_names_the_draw_that_chose_it(tmp_path):
    """§12: the served item's "why this item" line, by the draw's mode (here calibrate: a new
    cell's posterior is too wide to target the band); none for an item no AD draw chose."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from learnloop.adaptive_difficulty.serving import WHY, why_for_presentation

    paths, env, _clock, _record = _plan(tmp_path, ("pi_h", "pi_e1", "pi_e2"), features={"pi_h": HARD})
    _record, step = advance(env, serve=True)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        found = why_for_presentation(connection, step["presentation_id"])
        assert found["mode"] == "calibrate" and found["why"] == WHY["calibrate"]
        assert why_for_presentation(connection, "pp_missing") is None
    ctx = SidecarContext()
    ctx.load(paths.root)
    spec = METHOD_REGISTRY["adaptive_difficulty.why_item"]
    result = spec.handler(ctx, spec.params_model.model_validate({"planPresentationId": step["presentation_id"]}))
    assert result["why"] == WHY["calibrate"] and result["mode"] == "calibrate"
