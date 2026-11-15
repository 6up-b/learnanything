"""What the figure goldens share (``tests/test_figure_build_golden.py``, ``tests/test_figure_rich_job_golden.py``):
a frozen system clock, the rows a case writes, the stand-in sandbox for the source check, and the normalizer that
turns a case's record into the bytes the golden keeps.

**What is replaced, and how.** Everything a case records is walked in one fixed order: the parts in the order the
golden test names (the prompts in the order they were sent first, the list last); inside a part, mapping keys in
sorted order (so the tables by name, a row's columns by name) and lists in their own order (a table's rows in write
order, ``rowid``). In that walk:

- a ULID (26 Crockford characters, either case, alone or after a prefix such as ``fig_``) or a random UUID becomes
  ``<id:N>``, numbered by its first appearance. The same id is the same token wherever it appears, so a figure id
  written into another row, a trace id shared by two records, or a request row naming its figure keep their
  relation; a write that names a different row, or rows written in another order, changes the tokens and fails the
  golden;
- a timestamp within three days of the real clock (one the frozen clock did not make) becomes ``<wall>``;
- a measured duration (``DURATION_KEYS``) becomes ``<ms>``.

Nothing else is replaced. Content hashes, reuse keys and request identities (``content_key``) are deterministic and
kept byte for byte: they are the identities a structure step must not move. Times written through the system clock
are the frozen instant itself (:func:`freeze_wall`), and ids are minted in a fixed sequence (:func:`freeze_ids`)."""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Any

#: The instant every ``SystemClock().now()`` returns in a golden case.
FROZEN = datetime(2026, 10, 12, 9, 0, 0, tzinfo=UTC)
#: The tables a figure build or a rich job writes (strategy K10.4), plus the call receipts the gate's order shows in.
TABLES = ("figure_requests", "interactive_figures", "judgment_ledger", "figure_source_checks", "help_assists",
          "reveal_events", "ingest_jobs", "decision_records", "model_call_receipts")
DURATION_KEYS = frozenset({"duration_ms", "latency_ms", "elapsed_ms", "wall_ms", "duration_seconds"})

_ULID = re.compile(r"(?<![0-9A-Za-z])(?:[0-9A-HJKMNP-TV-Z]{26}|[0-9a-hjkmnp-tv-z]{26})(?![0-9A-Za-z])")
_UUID = re.compile(r"(?<![0-9a-f])(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{32})"
                   r"(?![0-9a-f])")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")


def freeze_wall(monkeypatch: Any) -> None:
    """Every read of the system clock returns :data:`FROZEN` (``utc_now_iso()`` and ``SystemClock`` callers); a
    module that reads ``datetime.now`` itself is left alone and its times become ``<wall>``."""

    from learnloop import clock

    monkeypatch.setattr(clock.SystemClock, "now", lambda self: FROZEN)


def freeze_ids(monkeypatch: Any, seed: int = 104) -> None:
    """``new_ulid`` mints the same ids in the same order every run: the frozen millisecond and a seeded random part.

    The ids themselves are replaced by tokens anyway; what this fixes is a hash that has one inside it (a revision's
    reuse key names the figure it supersedes). Such a hash moves if a step changes how many ids are minted before
    it, which the record says."""

    import random
    from types import SimpleNamespace

    from learnloop import ids

    seeded = random.Random(seed)
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: int(FROZEN.timestamp() * 1000))
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=seeded.getrandbits))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)


def _decoded(column: str, value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes": len(value)}
    if isinstance(value, str) and column.endswith("_json"):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def table_rows(sqlite_path: Path, tables: Iterable[str] = TABLES) -> dict[str, dict[int, dict[str, Any]]]:
    """Every row of each table that exists, by rowid, its JSON columns decoded."""

    found: dict[str, dict[int, dict[str, Any]]] = {}
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in tables:
            if table not in names:
                continue
            found[table] = {
                int(row["_rowid"]): {key: _decoded(key, row[key]) for key in row.keys() if key != "_rowid"}
                for row in connection.execute(f'SELECT rowid AS _rowid, * FROM "{table}" ORDER BY rowid')}
    return found


def written(before: Mapping[str, Mapping[int, Any]], after: Mapping[str, Mapping[int, Any]]) -> dict[str, Any]:
    """What a case wrote: per table the rows added (in write order), the rows changed (old and new) and removed."""

    out: dict[str, Any] = {}
    for table, rows in after.items():
        old = before.get(table, {})
        added = [row for rowid, row in rows.items() if rowid not in old]
        changed = [{"before": old[rowid], "after": row} for rowid, row in rows.items()
                   if rowid in old and old[rowid] != row]
        removed = [row for rowid, row in old.items() if rowid not in rows]
        entry = {key: value for key, value in (("added", added), ("changed", changed), ("removed", removed)) if value}
        if entry:
            out[table] = entry
    return out


class _Tokens:
    def __init__(self) -> None:
        self.ids: dict[str, str] = {}
        self.now = datetime.now(UTC)

    def _id(self, match: re.Match[str]) -> str:
        return self.ids.setdefault(match.group(0), f"<id:{len(self.ids) + 1}>")

    def _time(self, match: re.Match[str]) -> str:
        text = match.group(0)
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T"))
        except ValueError:
            return text
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return "<wall>" if abs(moment - self.now) < timedelta(days=3) else text

    def text(self, value: str) -> str:
        return _TIME.sub(self._time, _UUID.sub(self._id, _ULID.sub(self._id, value)))

    def walk(self, value: Any, key: str | None = None) -> Any:
        if key in DURATION_KEYS and isinstance(value, (int, float)) and not isinstance(value, bool):
            return "<ms>"
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, Mapping):
            out = {}
            for name in sorted(value, key=str):
                out[self.text(str(name))] = self.walk(value[name], str(name))
            return dict(sorted(out.items()))
        if isinstance(value, (list, tuple)):
            return [self.walk(item) for item in value]
        if isinstance(value, float) and value != value:
            return "NaN"
        return value


def normalized(record: Mapping[str, Any], order: Iterable[str]) -> dict[str, Any]:
    """The record with ids, wall times and durations replaced (module docstring), walked in ``order``."""

    order = tuple(order)
    assert set(record) <= set(order), f"parts with no place in the walk: {sorted(set(record) - set(order))}"
    tokens = _Tokens()
    return {name: tokens.walk(record[name]) for name in order if name in record}


def check_golden(path: Path, case: str, recorded: Mapping[str, Any], *, write: bool) -> None:
    """Compare one case with its entry in ``path``; with ``write``, record it there instead (under a file lock, so
    a parallel writing run cannot lose another case's entry)."""

    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        # The lock is on the golden itself, rewritten in place: a separate lock file removed after use would let a
        # waiting writer hold a lock on a file no newer writer sees.
        with open(path, "a+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.seek(0)
            text = handle.read()
            golden = json.loads(text) if text.strip() else {}
            golden[case] = recorded
            handle.seek(0)
            handle.truncate()
            handle.write(json.dumps(golden, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    golden = json.loads(path.read_text(encoding="utf-8"))
    assert case in golden, f"{case} has no golden entry: record it with the write switch"
    expected = golden[case]
    for part in expected:
        assert recorded.get(part) == expected[part], f"{case}: {part} differs from the golden"
    assert set(recorded) == set(expected), f"{case}: parts {sorted(set(recorded) ^ set(expected))}"


class FixedSandbox:
    """The source check's sandbox as a stand-in: each call answers every pair it is asked with the next verdict
    (``equal`` or ``different``), controls refused, display agreeing at every element. It keeps each payload's
    definitions, candidates and sha256 (the grids are large), which the golden records: what the check asked is part
    of what a move must not change. No process runs."""

    WITNESS = {"kind": "value", "at": {"x": "-3", "p": "1/2", "lam": "1"}}

    def __init__(self, verdicts: Iterable[str]) -> None:
        self.verdicts = list(verdicts)
        self.payloads: list[dict[str, Any]] = []

    def available(self) -> bool:
        return True

    def __call__(self, _harness: str, payload: Mapping[str, Any], **_kwargs: Any) -> Any:
        from learnloop.content.authoring import pf_sandbox

        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)
        definitions = list(payload.get("definitions") or ())
        self.payloads.append({
            "sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            "definitions": [{"name": item.get("name"), "candidates": [pair.get("candidate") for pair in
                                                                     item.get("pairs") or ()],
                             "elements": [element.get("id") for element in item.get("elements") or ()]}
                            for item in definitions]})
        verdict = self.verdicts.pop(0) if self.verdicts else "equal"
        results = []
        for definition in definitions:
            elements = [str(element.get("id")) for element in definition.get("elements") or ()]
            for pair in definition.get("pairs") or ():
                found: dict[str, Any] = {"definition": definition["name"], "candidate": pair["candidate"],
                                         "result": verdict}
                if verdict == "equal":
                    found["controls"] = ["different"] * max(1, len(pair.get("controls") or ()))
                    found["display"] = {element: {"agreed": True, "samples": 8} for element in elements}
                else:
                    found["witness"] = json.loads(json.dumps(self.WITNESS))
                results.append(found)
        return pf_sandbox.SandboxResult(True, output={"sympy_version": "fixed", "results": results})


def fixed_sandbox(monkeypatch: Any, verdicts: Iterable[str] = ()) -> FixedSandbox:
    """Install :class:`FixedSandbox` as the sandbox every source check reaches (``pf_sandbox``'s own names, which
    no figures step moves)."""

    from learnloop.content.authoring import pf_sandbox

    sandbox = FixedSandbox(verdicts)
    monkeypatch.setattr(pf_sandbox, "sandbox_available", sandbox.available)
    monkeypatch.setattr(pf_sandbox, "run_sandboxed_python", sandbox)
    return sandbox
