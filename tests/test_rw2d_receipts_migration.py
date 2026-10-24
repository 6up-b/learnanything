"""Reader workbench RW2d: migration 219 (``field_signal_receipts``).

One RECEIPT table, append-only by trigger: what the predecessor's field
derivation and placement rule would have decided where RW2d's workbench
signals changed a fast-track or quick-check decision. Nothing else is added
or altered.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)
from learnloop.db.table_roles import TableRole, role_for_table

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_219" / "state.sqlite"
#: What 219 adds: the earlier migrations' "nothing else changed" diffs on the way to head read this.
RW2D_ADDED_OBJECTS = frozenset({
    "field_signal_receipts", "field_signal_receipts_lo", "field_signal_receipts_no_update",
    "field_signal_receipts_no_delete", "sqlite_autoindex_field_signal_receipts_1",
    "sqlite_autoindex_field_signal_receipts_2",
})


def _database_at(tmp_path: Path, version: int) -> Path:
    through = tmp_path / f"through_{version}"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= version:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == version
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql or "" for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_stat%'")}


def _receipt(**overrides):
    row = {
        "id": "r1", "receipt_key": "fast_track::lo:abc", "decision_kind": "fast_track", "decision_ref": None,
        "learning_object_id": "lo", "signal_ids_json": "[]", "predecessor_json": "{}", "successor_json": "{}",
        "signal_version": "workbench-field-signals-v1", "algorithm_version": "mvp-0.31",
        "created_at": "2026-10-24T00:00:00Z",
    }
    row.update(overrides)
    return row


def test_219_adds_the_receipt_table_and_nothing_else(tmp_path):
    database = _database_at(tmp_path, 218)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [219]
    after = _schema(database)
    assert set(after) - set(before) == RW2D_ADDED_OBJECTS
    assert {name for name in before if before[name] != after[name]} == set()
    assert role_for_table("field_signal_receipts") is TableRole.RECEIPT


def test_the_receipts_are_append_only_and_keyed_once(tmp_path):
    from learnloop.db.stores import field_signal_receipts as store

    database = _database_at(tmp_path, 219)
    with closing(sqlite3.connect(database)) as connection:
        assert store.insert_receipt(connection, _receipt())
        assert not store.insert_receipt(connection, _receipt(id="r2"))  # same key: ignored
        with pytest.raises(sqlite3.IntegrityError):
            store.insert_receipt(connection, _receipt(id="r3", receipt_key="k3", decision_kind="queue"))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE field_signal_receipts SET learning_object_id = 'x'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM field_signal_receipts")
        assert [row["id"] for row in store.receipts(connection)] == ["r1"]


def test_the_head_fixture_is_at_219_in_rollback_mode():
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 219
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM field_signal_receipts").fetchone() == (0,)
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    for suffix in ("-wal", "-shm", "-journal"):
        assert not HEAD.with_name(HEAD.name + suffix).exists()
