"""What other test files use from ``tests/test_hint_telemetry.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import learnloop.clock as clock_module
from learnloop.hints import telemetry
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.post_attempt_worker import KINDS
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import append_config_toml, create_basic_vault


ITEM = "pi_svd_define_001"
FROZEN = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
SELF_GRADE = {"criterionPoints": {"correctness": 4}, "confidence": 4}


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _vault(tmp_path: Path, *, config: str = "", hints: list[str] | None = None, name: str = "vault"):
    paths = create_basic_vault(tmp_path / name)
    if hints is not None:
        item_path = paths.practice_item_path("linear-algebra", ITEM)
        data = read_yaml(item_path)
        data["hints"] = hints
        data["hint_policy"] = {**data["hint_policy"], "max_useful_hints": len(hints)}
        write_yaml(item_path, data)
    if config:
        append_config_toml(paths.root, config)
    return paths


def _reveal(
    ctx, session_id: str, index: int, *, answer: str = "", at: str | None = None, item: str = ITEM, key: str = "k1"
):
    params = {"sessionId": session_id, "practiceItemId": item, "submissionId": key, "authoredIndex": index,
              "answerMd": answer}
    if at is not None:
        params["revealedAt"] = at
    return _call(ctx, "practice.record_hint_reveal", params)


def _submit(
    ctx, session_id: str, *, hints: int, key: str, answer: str = "A = U Sigma V^T.", grade: dict | None = SELF_GRADE,
    latency: float | None = None,
):
    params = {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": answer,
        "attemptType": "hinted_attempt" if hints else "independent_attempt", "hintsUsed": hints,
        "selfGrade": grade, "submissionId": key,
    }
    if latency is not None:
        params["latencySeconds"] = latency
    return _call(ctx, "submit_attempt", params)


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    return FROZEN


_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_ISO = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)?")


def _scrub(value, root: Path | None = None) -> str:
    """Two runs' records as text, with only what differs between any two runs
    replaced: the vault's path and the wall clock some writers read directly
    (ids are made deterministic by ``_deterministic_ids``)."""

    text = json.dumps(value, sort_keys=True, default=str)
    if root is not None:
        text = text.replace(str(root.resolve()), "<root>").replace(str(root), "<root>")
    return _ISO.sub("<t>", _UUID.sub("<uuid>", text))


def _deterministic_ids(monkeypatch) -> None:
    """Every ULID from one counter, restarted per run, so both runs mint the
    same ids (receipt digests and id-seeded intervals follow them). The
    telemetry's own ids come from a counter of their own, so the rows it
    writes with the switch on never shift the ids anything else gets."""

    import learnloop.ids as ids

    counter = iter(range(1, 10**9))
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: 1_792_000_000_000)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=lambda bits: next(counter)))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    own = iter(range(1, 10**9))
    monkeypatch.setattr(telemetry, "new_ulid", lambda: f"TELEMETRY{next(own):017d}")
    # Decision records and traces draw from a stream of their own (arc B fix 3): restarted per run the same way.
    from learnloop import provenance

    records = iter(range(1, 10**9))
    monkeypatch.setattr(provenance, "_RECORD_IDS", lambda: f"RECORD{next(records):020d}")


def _dump(database: Path) -> dict[str, list[str]]:
    with closing(sqlite3.connect(database)) as connection:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {
            table: sorted(_scrub(list(row), database.parent) for row in connection.execute(f'SELECT * FROM "{table}"'))
            for table in tables if table != "help_assists"
        }


def _scenario(root: Path, monkeypatch) -> list[str]:
    """Reveal, draft, submit; reveal, don't know: the screen's calls, in order."""

    _deterministic_ids(monkeypatch)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    # At the head a miss queues post-attempt work (FG1 follow-up generation and its surprise); its threads would
    # race this run's deterministic ids, so it waits and is drained in order at the end, as the worker would.
    ctx.post_attempt_worker.autostart = False
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    responses = [_call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})]
    _reveal(ctx, session_id, 0, answer="U, Sigma", at="2026-10-17T08:59:00Z")
    responses.append(_call(ctx, "save_practice_draft", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "U, Sigma", "hintsUsed": 1,
        "submissionId": "k1"}))
    responses.append(_submit(ctx, session_id, hints=1, key="k1"))
    responses.append(_call(ctx, "acknowledge_practice_submission", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "k1"}))
    _reveal(ctx, session_id, 0, at="2026-10-17T08:59:30Z", key="k2")
    responses.append(_call(ctx, "submit_dont_know", {
        "sessionId": session_id, "practiceItemId": ITEM, "hintsUsed": 1, "submissionId": "k2"}))
    responses.append(_call(ctx, "get_session", {"sessionId": session_id}))
    for kind in KINDS:
        ctx.post_attempt_worker.run_pending(kind)
    return [_scrub(response, root) for response in responses]
