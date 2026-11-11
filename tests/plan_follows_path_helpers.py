"""What other test files use from ``tests/test_plan_follows_path.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from learnloop.algorithm_versions import READING_PATH_PLAN_ALGORITHM_VERSION
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository

from tests.helpers import MIGRATION_HEAD_FIXTURE, append_config_toml, set_algorithm_version
from tests.reading_path_fixtures import (
    EXT,
    FixedClock,
    PathJudgeFake,
    build_path_vault,
    call,
    context,
    normalized,
)


TAG = READING_PATH_PLAN_ALGORITHM_VERSION
OFF = "[reading_paths]\nplan_uses_path = false\n"
GUIDE_OFF = "[reading_paths]\nenabled = false\n"


def _as_you_read(repository: Repository) -> None:
    """Make the path vault's textbook an as-you-read import (DL1 §6.10)."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO synthesis_manifests(id, manifest_hash, extraction_ids_json, brief_json, created_at) "
            "VALUES ('man_rw7b', 'hash_rw7b', ?, ?, '2026-10-01T09:00:00Z')",
            (json.dumps([EXT]), json.dumps({"practice_items": "as_you_read"})))
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) "
            "VALUES ('run_rw7b', 'man_rw7b', 'bootstrap', 'completed', '2026-10-01T09:00:00Z', "
            "'2026-10-01T09:05:00Z')")
        connection.commit()


def _vault(tmp_path, monkeypatch, name="vault", *, version=TAG, config="", labels=None, depth="learn_to_use_it",
           overrides=(), before_judge=None):
    """A path vault whose textbook is read as you go, with a judged path at
    ``depth`` (none when ``depth`` is None) and the learner's ``overrides``;
    ``before_judge(repository)`` sets learner state the judge then sees."""

    if not hasattr(monkeypatch, "_rw7b_clock"):
        monkeypatch._rw7b_clock = FixedClock(monkeypatch)
    paths, repository, spans = build_path_vault(tmp_path / name, version=version, config=config)
    _as_you_read(repository)
    if before_judge is not None:
        before_judge(repository)
    if depth is not None:
        ctx = context(paths.root, reading_path_judge_client=PathJudgeFake(labels or {}), reading_path_inline=True)
        assert call(ctx, "reader.reading_path_set_depth", {"extractionId": EXT, "depth": depth})["status"] == "ready"
        for section, choice in overrides:
            call(ctx, "reader.reading_path_override",
                 {"extractionId": EXT, "depth": depth, "sectionId": section, "choice": choice})
    return paths, repository, spans


def _split(repository) -> dict:
    with repository.connection() as connection:
        rows = connection.execute("SELECT split_json FROM daily_plans ORDER BY created_at, id").fetchall()
    assert len(rows) == 1
    return json.loads(rows[0][0])


def _plan_state(paths) -> dict:
    """The served plan and Today, plus every stored plan row, as JSON with
    the ids a build mints replaced and the version label dropped."""

    ctx = context(paths.root)
    served = {"plan": call(ctx, "get_daily_plan", {}), "queue": call(ctx, "get_today_queue", {}),
              "next": call(ctx, "next_plan_item", {})}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        connection.row_factory = sqlite3.Row
        stored = {
            table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in ("daily_plans", "attention_blocks", "attention_block_events")
        }
    return json.loads(normalized(_without_version({"served": served, "stored": stored})))


#: Keys a build fills from the ids it mints (two builds of one vault at one
#: version differ only there): the block's content hash (over the plan id) and
#: the router card's hash (over the card, which is compared in full).
_MINTED_HASHES = ("content_hash", "card_hash")


def _without_version(value):
    if isinstance(value, dict):
        return {k: ("<minted>" if k in _MINTED_HASHES else _without_version(v)) for k, v in value.items()
                if k not in ("algorithmVersion", "algorithm_version")}
    if isinstance(value, list):
        return [_without_version(v) for v in value]
    if isinstance(value, str) and value.startswith("{"):
        try:
            return json.dumps(_without_version(json.loads(value)), sort_keys=True)
        except ValueError:
            return value
    return value


HEAD = MIGRATION_HEAD_FIXTURE


def _fixture_copy(tmp_path, source: Path, name: str, *, version: str, toml: str | None = None):
    root = tmp_path / name
    copy_tree_with_databases(source, root)
    set_algorithm_version(type("Paths", (), {"root": root})(), version)
    if toml:
        append_config_toml(root, toml)
    return type("Paths", (), {"root": root, "sqlite_path": root / "state.sqlite"})()
