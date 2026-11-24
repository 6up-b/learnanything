"""Migration 271 adds only immutable inputs. Historical backfill belongs to algorithm activation."""

import sqlite3
from contextlib import closing

import pytest

from learnloop.adaptive_difficulty.column_classes import CLASSES
from learnloop.adaptive_difficulty.protected_tables import DENIED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.grade_curves_migration_helpers import GRADE_CURVE_OBJECTS
from tests.helpers import MIGRATION_HEAD_FIXTURE


def test_migration_adds_the_empty_immutable_ledger_and_keeps_predecessor_rows(tmp_path):
    database = tmp_path / "copy.sqlite"
    with closing(sqlite3.connect(f"file:{MIGRATION_HEAD_FIXTURE / 'state.sqlite'}?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(database)) as target:
            source.backup(target)
    migration = next(m for m in discover_migrations() if m.name == "attempt_grade_curves")
    assert migration.version == 271
    with closing(sqlite3.connect(database)) as conn:
        conn.execute("DROP TABLE IF EXISTS attempt_grade_curves")
        conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))
        conn.execute("INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                     "attempt_type, created_at) VALUES ('att', 'pi', 'lo', 'short_answer', 'hinted_attempt', 't')")
        conn.commit()
        before = dict(conn.execute("SELECT name, sql FROM sqlite_master"))
        attempts = conn.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()

    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [271]
    with closing(sqlite3.connect(database)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        after = dict(conn.execute("SELECT name, sql FROM sqlite_master"))
        assert after.keys() - before.keys() == GRADE_CURVE_OBJECTS
        assert before == {k: v for k, v in after.items() if k not in GRADE_CURVE_OBJECTS}
        assert conn.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts
        assert conn.execute("SELECT * FROM attempt_grade_curves").fetchall() == []
        assert TABLE_ROLES["attempt_grade_curves"] is TableRole.RAW_LEDGER
        assert ROLES["attempt_grade_curves"] == DENIED
        cols = conn.execute("PRAGMA table_info(attempt_grade_curves)").fetchall()
        assert set(CLASSES["attempt_grade_curves"]) == {r[1] for r in cols}
        insert = "INSERT INTO attempt_grade_curves VALUES (?, ?, ?, ?, ?, ?, ?)"
        row = ("att", "revision:0", 0, 1., -0.5, "mvp-0.70", "graded")
        conn.execute(insert, row)
        for statement in ("UPDATE attempt_grade_curves SET item_b = 0", "DELETE FROM attempt_grade_curves",
                          insert.replace("INSERT", "INSERT OR REPLACE")):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                conn.execute(statement, row if "INSERT" in statement else ())
        for a, b, provenance in ((1., None, "graded"), (None, 1., "missing_at_upgrade"), (1., 2., "unknown")):
            with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
                conn.execute(insert, ("att", "revision:1", 1, a, b, "mvp-0.69", provenance))
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            conn.execute(insert, ("absent", *row[1:]))
        assert conn.execute("SELECT * FROM attempt_grade_curves").fetchall() == [row]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
