"""What other test files use from ``tests/test_ad1_codex_rereview_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

import yaml

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ITEMS, AuditDecider, ForecastLLM, ad_plan_vault, plan_env


SENTINEL = "HELD_OUT_HISTORY_SENTINEL-7d2e"
EXTRACTION = "ext_rereview"


def _item_path(paths, item_id):
    return paths.practice_item_path("linear-algebra", item_id)


def _set_fields(paths, item_id, **fields):
    path = _item_path(paths, item_id)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key, value in fields.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _exercise(span: str) -> dict:
    return {"source_id": "src_rereview", "extraction_id": EXTRACTION, "span_ids": [span]}


def _hold_out(monkeypatch, *spans: str) -> None:
    """From now on the predicate holds these spans out (a unit marked held out after the serve)."""

    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset((EXTRACTION, span) for span in spans))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _served_with_history(tmp_path):
    """A plan serve whose frozen history card quotes ``pi_hist`` (made from span ``hist``)."""

    paths = ad_plan_vault(tmp_path, items=(*ITEMS, "pi_hist"))
    _set_fields(paths, "pi_hist", prompt=f"{SENTINEL}: a later exam question.", canonical_exercise=_exercise("hist"))
    for item_id in ITEMS:
        _set_fields(paths, item_id, canonical_exercise=_exercise(f"span_{item_id}"))
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    stamp = (clock.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, created_at) VALUES ('att_hist', 'pi_hist', 'lo_m1', 'short_answer', "
            "'independent_attempt', 1.0, 0, ?)", (stamp,))
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["presentation_id"] and step["practice_item_id"] != "pi_hist"
    from learnloop.adaptive_difficulty.outside import frozen_state_key

    frozen = "\n".join(row[0] for row in sqlite3.connect(paths.sqlite_path).execute(
        "SELECT content_json FROM item_forecast_payloads WHERE owner_key = ?",
        (frozen_state_key(step["presentation_id"]),)))
    assert SENTINEL in frozen, "the serve froze the history item while it was ordinary practice"
    return paths, step


def _forecast(paths, step):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    llm, decider = ForecastLLM(p_correct=0.4), AuditDecider(p_yes=0.6)
    outcomes = forecast_presentation(load_vault(paths.root), Repository(paths.sqlite_path), step["presentation_id"],
                                     clients=Clients(llm=llm, decider=decider))
    return outcomes, llm, decider


METERED = """
[ai.providers.metered_test]
type = "openrouter"
model = "vendor/metered-model"
"""


def _metered_vault(tmp_path, cap: float):
    paths = ad_plan_vault(tmp_path, config=METERED + f"\n[adaptive_difficulty]\nprice_per_million = 2.0\n"
                                                      f"daily_spend_cap_usd = {cap}\n")
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    config.write_text(text.replace("\n[ai.routing]\n", '\n[ai.routing]\nad_forecast_llm = "metered_test"\n', 1),
                      encoding="utf-8")
    return paths
