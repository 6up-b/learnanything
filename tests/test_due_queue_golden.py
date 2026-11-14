"""The due queue's whole build pinned on one vault that reaches every stage (``tests/due_queue_helpers.py``).

Three builds of the same state, each on a fresh copy: a serving build with the session that committed a probe
presentation, a read build (``read_due_queue``) with that session, and a read build with no session. Each
record holds the returned queue (ids, order, scores, components, explanations, slate and candidate ids), the
exploration draw (its support, roll, choice and every outcome's composed order, from the offer trace), the trace's
exclusions, cold deferrals and pin, and every row the build added, changed or removed, table by table.

Ids read ``<ulid:n>`` in order of first appearance in the record (the process's ULID stream is also seeded and its
clock held, setup included, but how many ids the setup mints can vary with the hash seed). Stamps from the wall clock read
``<wall>``, the vault's algorithm tag ``<head tag>``, and floats are rounded to ten places.

A change that means to change what a build returns or writes regenerates the files and shows the diff in review:

    DUE_QUEUE_GOLDEN_WRITE=1 uv run pytest tests/test_due_queue_golden.py

``DUE_QUEUE_GOLDEN_ACTUAL=<dir>`` writes each case's record there as well, to diff against its golden.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.scheduling.scheduler import OfferTrace, SchedulerSession, build_due_queue, read_due_queue

from tests.due_queue_helpers import CLOCK, SESSION, build_rich_vault

GOLDEN_DIR = Path(__file__).parent / "goldens" / "due_queue"
WRITE = os.environ.get("DUE_QUEUE_GOLDEN_WRITE") == "1"

_ULID_MS = 1_790_000_000_000
_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
_HEAD_TAG = re.compile(re.escape(LATEST_ALGORITHM_VERSION) + r"(?![0-9.])")
#: FTS shadow tables hold binary segments a queue build never writes.
_SKIPPED_TABLE = re.compile(r"_(data|idx|content|docsize|config)$")


@pytest.fixture
def seeded_ids(monkeypatch):
    from learnloop import ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: _ULID_MS)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=random.Random(20261113).getrandbits))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)


def _stamp(text: str) -> str:
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T"))
    except ValueError:
        return text
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return "<wall>" if abs((moment - datetime.now(UTC)).total_seconds()) < 3 * 86400 else text


class _Ids:
    def __init__(self) -> None:
        self.seen: dict[str, str] = {}

    def __call__(self, text: str) -> str:
        def one(match: re.Match[str]) -> str:
            return self.seen.setdefault(match.group(0), f"<ulid:{len(self.seen)}>")

        text = _HEAD_TAG.sub("<head tag>", _STAMP.sub(lambda match: _stamp(match.group(0)), text))
        return _ULID.sub(one, text)


def _clean(value: Any, ids: _Ids) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item, ids) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        items = [_clean(item, ids) for item in value]
        return sorted(items, key=json.dumps) if isinstance(value, set | frozenset) else items
    if isinstance(value, bytes):
        return f"<bytes:{hashlib.sha256(value).hexdigest()[:16]}>"
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in "[{":
            try:
                return {"<json>": _clean(json.loads(value), ids)}
            except ValueError:
                pass
        return ids(value)
    return value


def _database(path: Path) -> dict[str, list[dict[str, Any]]]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = [
            row["name"] for row in connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if not _SKIPPED_TABLE.search(row["name"]) and "VIRTUAL TABLE" not in str(row["sql"]).upper()
        ]
        out: dict[str, list[dict[str, Any]]] = {}
        for table in tables:
            try:
                rows = connection.execute(f'SELECT rowid AS "<rowid>", * FROM "{table}" ORDER BY rowid').fetchall()
            except sqlite3.OperationalError:  # WITHOUT ROWID
                rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
            out[table] = [dict(row) for row in rows]
        return out
    finally:
        connection.close()


def _row_key(row: dict[str, Any]) -> str:
    return str(row["<rowid>"]) if "<rowid>" in row else json.dumps(row, sort_keys=True, default=str)


def _database_changes(before: dict[str, list[dict]], after: dict[str, list[dict]]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for table in sorted(set(before) | set(after)):
        old = {_row_key(row): row for row in before.get(table, [])}
        new = {_row_key(row): row for row in after.get(table, [])}
        added = [row for key, row in new.items() if key not in old]
        removed = [row for key, row in old.items() if key not in new]
        changed = [{"before": old[key], "after": row} for key, row in new.items() if key in old and old[key] != row]
        entry = {name: rows for name, rows in (("added", added), ("changed", changed), ("removed", removed)) if rows}
        if entry:
            changes[table] = entry
    return changes


def _scheduled(item: Any) -> dict[str, Any]:
    return {
        "practice_item_id": item.practice_item_id,
        "learning_object_id": item.learning_object_id,
        "priority": item.priority,
        "components": dict(sorted(item.components.items())),
        "readiness_factor": item.readiness_factor,
        "selected_mode": item.selected_mode,
        "plain_english": list(item.plain_english),
        "reward_debug": item.reward_debug,
        "followup_kind": item.followup_kind,
        "scheduler_slate_id": item.scheduler_slate_id,
        "scheduler_candidate_id": item.scheduler_candidate_id,
    }


def _trace(trace: OfferTrace) -> dict[str, Any]:
    return {
        "exclusions": {reason: list(ids) for reason, ids in sorted(trace.exclusions.items())},
        "greedy_item_ids": list(trace.greedy_item_ids),
        "considered_item_ids": [item.practice_item_id for item in trace.considered],
        "base_propensity": dict(sorted(trace.base_propensity.items())),
        "exploration": trace.exploration,
        "outcomes": [
            {
                "explored_item_id": outcome.explored_item_id,
                "probability": outcome.probability,
                "composed": [item.practice_item_id for item in outcome.composed],
            }
            for outcome in trace.outcomes
        ],
        "realized": trace.realized,
        "pinned_item_id": trace.pinned_item_id,
        "probe_block_reason": trace.probe_block_reason,
        "cold_deferrals": [dict(row) for row in trace.cold_deferrals],
        "placement_active": trace.placement_active,
        "slate_id": trace.slate_id,
        "voi_decisions": list(trace.voi_decisions),
        "teach_back_exclusion_reason": trace.teach_back_exclusion_reason,
    }


def _record(tmp_path: Path, build: Any) -> dict[str, Any]:
    vault, repository = build_rich_vault(tmp_path / "vault")
    before = _database(repository.sqlite_path)
    trace = OfferTrace()
    queue = build(vault, repository, trace)
    changes = _database_changes(before, _database(repository.sqlite_path))
    return _clean({"queue": [_scheduled(item) for item in queue], "trace": _trace(trace), "database": changes}, _Ids())


def _check(name: str, record: dict[str, Any]) -> None:
    path = GOLDEN_DIR / f"{name}.json"
    text = json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if WRITE:
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return
    assert path.exists(), f"no golden for {name}: regenerate with DUE_QUEUE_GOLDEN_WRITE=1"
    if os.environ.get("DUE_QUEUE_GOLDEN_ACTUAL"):
        Path(os.environ["DUE_QUEUE_GOLDEN_ACTUAL"], f"{name}.json").write_text(text, encoding="utf-8")
    assert json.loads(text) == json.loads(path.read_text(encoding="utf-8")), (
        f"{name}: what the build returned or wrote moved (see the module docstring to regenerate)"
    )


def test_a_serving_build_with_a_session(tmp_path, seeded_ids):
    _check("serving_with_session", _record(tmp_path, lambda vault, repository, trace: build_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace)))


def test_a_read_build_with_the_same_session(tmp_path, seeded_ids):
    _check("read_with_session", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace)))


def test_a_read_build_with_no_session(tmp_path, seeded_ids):
    _check("read_without_session", _record(tmp_path, lambda vault, repository, trace: read_due_queue(
        vault, repository, clock=CLOCK, offer_trace=trace)))


def test_the_vault_reaches_every_stage(tmp_path, seeded_ids):
    """What the goldens are for: if the vault stops reaching a stage, the goldens stop pinning it."""

    record = _record(tmp_path, lambda vault, repository, trace: build_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION), offer_trace=trace))
    queue = record["queue"]
    components = [item["components"] for item in queue]
    assert queue[0]["components"].get("probe_committed") == 1.0, "the committed presentation is pinned first"
    assert any(c.get("exploration_selected") == 1.0 for c in components), "the exploration draw moved an item"
    assert any(c.get("new_material") == 1.0 for c in components), "placement serves new material"
    assert any(item["selected_mode"] == "teach_back" for item in queue), "a teach-back is composed"
    assert any(c.get("voi_stop") == 1.0 for c in components), "the probe episode's value decision is made"
    assert record["trace"]["cold_deferrals"], "the cold lane defers a task"
    assert "contrast_pair_servings" in record["database"], "the contrast pair's order is drawn and recorded"
    assert "pi_a1" in [item["practice_item_id"] for item in queue] and "pi_a2" not in [
        item["practice_item_id"] for item in queue
    ], "the due check serves one of its candidates"
