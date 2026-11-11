"""What other test files use from ``tests/test_ad3_subject_view.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from learnloop.daily_plan.engine import advance, build_plan

from tests.ad23_fakes import LO, ad23_vault, answer, env_for, rows, selections, set_item


OTHER = ("pi_o1", "pi_o2", "pi_o3", "pi_o4")
MINE = ("pi_m1", "pi_m2")
ROUTER_OFF = "[router]\nenabled = false\n"


def _two_los(tmp_path, *, ad: str = ""):
    paths = ad23_vault(tmp_path, items=MINE, learning_objects={"lo_other": OTHER}, ad=ad, config=ROUTER_OFF)
    for item in MINE:
        set_item(paths, item, evidence_facets=["f_mine"], evidence_weights={"f_mine": 1.0})
    for item in OTHER:
        set_item(paths, item, evidence_facets=["f_other"], evidence_weights={"f_other": 1.0})
    return paths


def _serve_and_answer(paths, env, clock, *, correct: bool, steps: int) -> list[dict[str, Any]]:
    served = []
    for _ in range(steps):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        served.append(step)
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=correct, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return served


def _scenario(tmp_path, name: str, *, seen: bool, ad: str = "") -> dict[str, Any]:
    paths = _two_los(tmp_path / name, ad=ad)
    env, clock = env_for(paths, items=OTHER)
    if seen:
        build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
        assert len(_serve_and_answer(paths, env, clock, correct=True, steps=4)) == 4
    clock.advance(60 * 24)
    env, clock = env_for(paths, items=MINE, clock=clock, session="s2")
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["learning_object_id"] == LO
    draws = [row for row in selections(paths) if row["learning_object_id"] == LO]
    receipts = {row["forecaster"]: row for row in rows(
        paths.sqlite_path, "SELECT forecaster, p, forecast_json FROM forecast_receipts WHERE kind = "
        "'item_unassisted_success' AND practice_item_id = ?", (step["practice_item_id"],))}
    return {"paths": paths, "step": step, "draws": draws, "receipts": receipts}


def _scores(draws: list[dict[str, Any]], kind: str) -> list[Any]:
    return [[(e["ref"], e["p_band"], e["p_bar"], e["propensity"]) for e in row["support"]]
            for row in draws if row["kind"] == kind]
