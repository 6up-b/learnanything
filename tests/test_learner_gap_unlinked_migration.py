"""Follow-ups Nov 2 (c): migration 235, the ``unlinked`` reversal (C5 ruling R2).

``learner_text_gap_reversals.reversal`` gains ``unlinked`` in a temp-then-rename
rebuild under ``PRAGMA foreign_keys = OFF`` (the FK-safe precedent of 208, 212
and 231). Every existing row survives with its id and every column, its own
foreign key to ``learner_text_gaps`` still resolves (``foreign_key_check`` clean
before and after), the append-only triggers are back with the same
definitions, and nothing else about the table changes. No table is new, so
nothing new is classified; the head fixture holds 235 in rollback mode. The
durability lane runs it with production pragmas (WAL, ``synchronous=FULL``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)
from learnloop.db.table_roles import TableRole, role_for_table

NOW = "2026-11-02T10:00:00Z"
#: The object 235 redefines (rebuilt in place, same name; it adds nothing): the earlier
#: migrations' "nothing else changed" diffs on the way to head read it.
UNLINKED_ALTERED_TABLES = frozenset({"learner_text_gap_reversals"})
REVERSALS_BEFORE = ("undo_edge", "undo_creation", "not_this_belief")
TABLES = ("learner_text_gaps", "learner_text_gap_jobs", "learner_text_gap_reversals",
          "learner_gap_check_advances", "learner_gap_commitments")


def _database_at_231(tmp_path: Path) -> Path:
    through = tmp_path / "through_231"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 231:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 231
    return database


def _seed(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for index, reversal in enumerate(REVERSALS_BEFORE):
            connection.execute(
                "INSERT INTO learner_text_gaps (id, source_kind, source_id, learner_text, chooser, context_judge, "
                "kind, named_json, action, detail_json, algorithm_version, pipeline_version, created_at) VALUES "
                "(?, 'learner_note', ?, '', 'context_model', 'gap_reader', 'prerequisite', '{}', "
                "'matched_prerequisite', '{\"k\": [1]}', 'mvp-0.40', 'learner-text-gaps-v1', ?)",
                (f"ltg_{index}", f"ln_{index}", f"2026-10-2{index}T09:00:00Z"))
            connection.execute(
                "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, detail_json, created_at) "
                "VALUES (?, ?, ?, ?, '{\"why\": 1}', ?)",
                (f"rev_{index}", f"ltg_{index}", reversal, "owner" if index else "learner", NOW))
        connection.commit()


def _rows(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


def _columns(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return [tuple(row[1:]) for row in connection.execute(f"PRAGMA table_info({table})")]


def _objects(database: Path, table: str) -> dict[tuple[str, str], str | None]:
    with closing(sqlite3.connect(database)) as connection:
        return {(row[0], row[1]): row[2] for row in connection.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger')",
            (table,))}


def _foreign_keys(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return [tuple(row) for row in connection.execute(f"PRAGMA foreign_key_list({table})")]


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at_231(tmp_path)
    _seed(database)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    before = {table: _rows(database, table) for table in TABLES}
    shape = (_columns(database, "learner_text_gap_reversals"), _objects(database, "learner_text_gap_reversals"),
             _foreign_keys(database, "learner_text_gap_reversals"))
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert 235 in [migration.version for migration in applied]
    assert {table: _rows(database, table) for table in TABLES} == before  # every row, id and value survives
    assert (_columns(database, "learner_text_gap_reversals"), _objects(database, "learner_text_gap_reversals"),
            _foreign_keys(database, "learner_text_gap_reversals")) == shape
    return database


def _check_widened(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
            "VALUES ('rev_unlinked', 'ltg_1', 'unlinked', 'learner', ?)", (NOW,))
        for bad in ("hidden", "unlink"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
                    "VALUES (?, 'ltg_2', ?, 'learner', ?)", (f"rev_{bad}", bad, NOW))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
                "VALUES ('rev_system', 'ltg_2', 'unlinked', 'system', ?)", (NOW,))
        # One per gap and kind, as before.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
                "VALUES ('rev_dup', 'ltg_1', 'unlinked', 'learner', ?)", (NOW,))
        # Its foreign key still resolves to the gaps table.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, created_at) "
                "VALUES ('rev_x', 'ltg_missing', 'unlinked', 'learner', ?)", (NOW,))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE learner_text_gap_reversals SET actor = 'owner' WHERE id = 'rev_0'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM learner_text_gap_reversals WHERE id = 'rev_0'")
        connection.rollback()


def test_235_widens_the_reversal_with_unlinked_and_keeps_every_row(tmp_path):
    _check_widened(_upgrade(tmp_path))


@pytest.mark.durability
def test_235_on_the_durability_lane(tmp_path):
    """Production pragmas: the rebuild is WAL-safe and FK-checked before commit."""

    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check_widened(database)


def test_235_classifies_nothing_new():
    assert role_for_table("learner_text_gap_reversals") is TableRole.RAW_LEDGER
    sql = next(m for m in discover_migrations() if m.version == 235).path.read_text()
    created = {line.split()[2] for line in sql.splitlines() if line.startswith("CREATE TABLE")}
    assert created == {"learner_text_gap_reversals__235"}  # renamed onto the old name


def test_235_adds_unlinked_and_nothing_else():
    sql = next(m for m in discover_migrations() if m.version == 235).path.read_text()
    assert "PRAGMA foreign_keys = OFF" in sql and sql.rstrip().endswith("PRAGMA foreign_keys = ON;")
    original = next(m for m in discover_migrations() if m.version == 182).path.read_text()
    start = original.index("CREATE TABLE learner_text_gap_reversals (")
    table = original[start:original.index(");", start) + 2]
    ours = sql[sql.index("CREATE TABLE learner_text_gap_reversals__235 ("):]
    ours = ours[:ours.index(");") + 2]
    # 182's definition, exactly, with the one kind more.
    assert ours.replace("__235", "").replace(", 'unlinked'", "") == table
    for trigger in ("learner_text_gap_reversals_no_update", "learner_text_gap_reversals_no_delete"):
        line = next(text for text in original.splitlines() if trigger in text)
        assert line in sql, trigger


def test_the_head_fixture_holds_235_in_rollback_mode():
    # The head is teacher TE1b's 236 now (rebuilt from this 235 head with only 236 applied); it holds 235.
    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_242" / "state.sqlite"
    assert head.read_bytes()[18:20] == b"\x01\x01"
    assert 235 in applied_versions(head)
    assert max(applied_versions(head)) == max(m.version for m in discover_migrations()) == 242
    with closing(sqlite3.connect(f"file:{head}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'learner_text_gap_reversals'"
                                 ).fetchone()[0]
        assert "'unlinked'" in sql
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
