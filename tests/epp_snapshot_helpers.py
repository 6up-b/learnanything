"""Builders for the prediction-snapshot tests (evidence packets EPp, its first part): a frozen-clock AD journey
and the comparison of two copies of it, one with snapshots and one with the enrichment turned into the identity.
No network, no model call."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import scoring
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.scheduling import prediction_snapshots as PS
from learnloop.vault.loader import load_vault

from tests.ad23_contract_helpers import _deterministic, _reset_ids
from tests.ad23_fakes import ad23_vault, answer, env_for

#: The keys this part adds to existing JSON bodies: everything else in a receipt is compared byte for byte.
NEW_FORECAST_KEYS = ("distribution", "reason")
NEW_VERSION_KEYS = ("snapshot",)
#: A decision record's ``created_at`` is the wall clock (ADR-017), not the run's frozen clock.
WALL_CLOCK = {"decision_records": ("created_at",)}


def identity_bodies(receipt: Any, issued: str, recorded_as_of: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """The enrichment as the identity: the bodies the producer wrote, as before snapshots existed."""

    return dict(receipt.forecast), dict(receipt.versions or {})


def journey(root: Path, monkeypatch: Any, *, snapshots: bool = True, before_answer: Any = None) -> dict[str, Any]:
    """A plan served and answered twice under a frozen clock and a counting id stream, then AD's state and the
    forecast scores rebuilt. Each copy starts the id stream from the same point, so two copies that consume
    the stream alike mint the same ids."""

    _deterministic(monkeypatch)
    _reset_ids(monkeypatch)
    with monkeypatch.context() as patch:
        if not snapshots:
            patch.setattr(PS, "receipt_bodies", identity_bodies)
        paths = ad23_vault(root)
        item_forecasts(paths)
        env, clock = env_for(paths)
        build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
        served = []
        for _round in range(2):
            _record, step = advance(env, serve=True)
            served.append(step)
            if before_answer is not None:
                before_answer(paths, step)
            clock.advance(1)
            answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"],
                   clock=clock)
            clock.advance(1)
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        RP.clear_cache()
        RP.rebuild(vault, repository)
        scoring.rebuild(vault, repository)
    return {"paths": paths, "served": served}


#: Before the plan's first serve: the item-only ``llm_v1`` forecasts ``z_v1`` reads (one per item, received an
#: hour before), so the serves' frozen ``z_v1`` and its recalibration read receipts written through the writer.
ITEM_FORECASTS = {"pi_m1a": 0.62, "pi_m1b": 0.41, "pi_m1c": 0.77}
ITEM_FORECASTS_AT = "2026-10-12T08:00:00Z"


def item_forecasts(paths: Any) -> list[str]:
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.switches import LLM_V1
    from learnloop.scheduling import forecast_receipts as FR

    from tests.ad23_fakes import ad_epoch

    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    epoch = ad_epoch(paths)
    out = []
    for item_id, p in ITEM_FORECASTS.items():
        item = vault.practice_items[item_id]
        content_hash = item_revision(item)[0]
        out.append(FR.ForecastReceipt(
            receipt_key=f"{FR.ITEM_UNASSISTED_SUCCESS}:item:{content_hash}:{LLM_V1}", kind=FR.ITEM_UNASSISTED_SUCCESS,
            forecaster=LLM_V1, forecaster_version="llm_v1:model_fake", scope="item", decision_kind="item_prepare",
            binding_kind=FR.FIRST_PRESENTATION, event="unassisted_success",
            forecast={"p": p, "event": "unassisted_success", "p_categories": None},
            inputs={"practice_item_id": item_id, "content_hash": content_hash}, parameters=[],
            versions={"prompt": "llm_v1_fake", "model": "model_fake", "protection_epoch": epoch},
            inputs_as_of=ITEM_FORECASTS_AT, p=p,
            columns={"practice_item_id": item_id, "item_content_hash": content_hash,
                     "learning_object_id": item.learning_object_id, "status": "ok",
                     "received_at": ITEM_FORECASTS_AT}))
    return FR.record_receipts(repository, out, created_at=ITEM_FORECASTS_AT)


def tables(path: Path) -> list[str]:
    with closing(sqlite3.connect(path)) as connection:
        return [str(row[0]) for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def table_rows(path: Path, table: str) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        found = [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
    for column in WALL_CLOCK.get(table, ()):
        for row in found:
            row[column] = "<wall clock>"
    return found


def without_new_keys(row: dict[str, Any]) -> dict[str, Any]:
    """A receipt row as it was before snapshots: the added keys removed from its forecast and versions, and
    ``p_categories`` back to the None every threshold receipt stored."""

    out = dict(row)
    forecast = json.loads(out["forecast_json"])
    for key in NEW_FORECAST_KEYS:
        forecast.pop(key, None)
    if str(out["forecaster"]).startswith("ad_threshold@"):
        forecast["p_categories"] = None
    versions = json.loads(out["versions_json"])
    for key in NEW_VERSION_KEYS:
        versions.pop(key, None)
    out["forecast_json"], out["versions_json"] = forecast, versions
    return out


def comparable(path: Path) -> dict[str, list[str]]:
    """Every row of every table, as sorted canonical JSON, receipts without the keys this part adds."""

    out: dict[str, list[str]] = {}
    for table in tables(path):
        found = table_rows(path, table)
        if table == "forecast_receipts":
            found = [without_new_keys(row) for row in found]
        out[table] = sorted(json.dumps(row, sort_keys=True, default=str) for row in found)
    return out


def receipts(path: Path) -> list[dict[str, Any]]:
    found = table_rows(path, "forecast_receipts")
    for row in found:
        for column in ("forecast_json", "inputs_json", "parameters_json", "versions_json"):
            row[column[: -len("_json")]] = json.loads(row.pop(column))
    return sorted(found, key=lambda row: (row["created_at"], row["id"]))
