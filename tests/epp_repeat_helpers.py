"""Builders for the repeat-capture tests (evidence packets EPp, its second part): a frozen-clock AD journey in which
the plan serves an item the learner attempted three days before, and the comparison of two copies of it, one with
the predecessor's repeat receipts and one without. No network, no model call."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from learnloop import ids
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import repeat_receipts as RR
from learnloop.adaptive_difficulty import scoring
from learnloop.adaptive_difficulty import serve as serve_module
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_contract_helpers import _deterministic, _reset_ids
from tests.ad23_fakes import ad23_vault, answer, env_for
from tests.daily_plan_fakes import MovableClock, seed_due
from tests.epp_snapshot_helpers import WALL_CLOCK, item_forecasts

#: The item attempted before the plan and served again by it; the plan's other two items are fresh.
REPEATED = "pi_m1a"
EARLIER_DAYS = 3
#: The repeat receipts' own stream starts here in a test (the global counting stream starts at 1_790_000_000_000).
OWN_STREAM_MS = 1_790_500_000_000


def own_stream() -> ids.UlidStream:
    """A deterministic stand-in for the repeat receipts' own id stream: same shape, its own counter."""

    stream = ids.UlidStream()
    stream._last_ms, stream._last_randomness = OWN_STREAM_MS, 0
    stream._random = SimpleNamespace(getrandbits=lambda bits: 0)
    return stream


def repeat_journey(root: Path, monkeypatch: Any, *, capture: bool = True, mutate: bool = False, rounds: int = 3,
                   answer_repeat: bool = True, edit_after: dict[str, Any] | None = None,
                   setup: Any = None) -> dict[str, Any]:
    """An item attempted (wrongly) three days before the plan, due again; the plan serves it (a repeat) and then
    the two fresh items, each answered a minute after its serve; then AD's state and the forecast scores are
    rebuilt. ``capture=False`` is the base: the serve hook builds and writes no repeat receipt. ``mutate``: the
    repeat receipts' ids also take one id of the global stream each (the mutation the comparison must catch)."""

    _deterministic(monkeypatch)
    _reset_ids(monkeypatch)
    with monkeypatch.context() as patch:
        stream = own_stream()
        if mutate:
            def leaky() -> str:
                ids.new_ulid()
                return stream()
            patch.setattr(serve_module, "new_receipt_id", leaky)
        else:
            patch.setattr(serve_module, "new_receipt_id", stream)
        if not capture:
            patch.setattr(serve_module, "repeat_receipts", lambda *_args, **_kwargs: ([], "off"))
        paths = ad23_vault(root)
        if setup is not None:
            setup(paths)
        item_forecasts(paths)
        env, clock = env_for(paths)
        earlier = MovableClock(clock.now() - timedelta(days=EARLIER_DAYS))
        earlier_attempt = answer(paths, REPEATED, correct=False, clock=earlier)
        seed_due(env.repository, REPEATED, due=clock.now() - timedelta(days=1), last=earlier.now())
        build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
        served = []
        for _round in range(rounds):
            _record, step = advance(env, serve=True)
            served.append(step)
            clock.advance(1)
            if answer_repeat or step["practice_item_id"] != REPEATED:
                answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"],
                       clock=clock)
            clock.advance(1)
        if edit_after is not None:
            from tests.ad23_fakes import set_item

            set_item(paths, REPEATED, **edit_after)
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        RP.clear_cache()
        RP.rebuild(vault, repository)
        scoring.rebuild(vault, repository)
    return {"paths": paths, "served": served, "env": env, "clock": clock, "earlier_attempt": earlier_attempt}


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


def is_repeat_row(table: str, row: dict[str, Any]) -> bool:
    return table in ("forecast_receipts", "item_forecast_scores") and row.get("forecaster") in RR.REPEAT_FORECASTERS


def comparable(path: Path, *, drop_repeat: bool = True) -> dict[str, list[str]]:
    """Every row of every table as sorted canonical JSON, the repeat receipts and their score rows left out."""

    out: dict[str, list[str]] = {}
    for table in tables(path):
        found = [row for row in table_rows(path, table) if not (drop_repeat and is_repeat_row(table, row))]
        out[table] = sorted(json.dumps(row, sort_keys=True, default=str) for row in found)
    return out


def receipts(path: Path, *, forecasters: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    found = table_rows(path, "forecast_receipts")
    for row in found:
        for column in ("forecast_json", "inputs_json", "parameters_json", "versions_json"):
            row[column[: -len("_json")]] = json.loads(row.pop(column))
    if forecasters is not None:
        found = [row for row in found if row["forecaster"] in forecasters]
    return sorted(found, key=lambda row: (row["created_at"], row["id"]))


def repeat_presentation(run: dict[str, Any]) -> str:
    return next(str(step["presentation_id"]) for step in run["served"] if step["practice_item_id"] == REPEATED)


class FakeView:
    """The reads :func:`learnloop.adaptive_difficulty.repeat_receipts.memory_context`, ``last_exposure`` and
    ``delay_context`` make, over plain rows (each kind oldest first, as the material view gives them)."""

    def __init__(self, *, attempts=(), reveals=(), readings=(), items=None, presentations=None) -> None:
        self._attempts, self._reveals, self._readings = list(attempts), list(reveals), list(readings)
        self._items, self._presentations = dict(items or {}), dict(presentations or {})

    def attempts(self, _connection: Any) -> list[dict[str, Any]]:
        return list(self._attempts)

    def reveals(self, _connection: Any) -> list[dict[str, Any]]:
        return list(self._reveals)

    def reading_opportunities(self, _connection: Any, *, learning_object_ids: Any = None) -> list[dict[str, Any]]:
        wanted = None if learning_object_ids is None else {str(lo) for lo in learning_object_ids}
        return [row for row in self._readings if wanted is None or str(row["learning_object_id"]) in wanted]

    def item(self, item_id: Any) -> Any:
        return self._items.get(str(item_id))

    def presentation(self, _connection: Any, presentation_id: str) -> dict[str, Any] | None:
        return self._presentations.get(presentation_id)
