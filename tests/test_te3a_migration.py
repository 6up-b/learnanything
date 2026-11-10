"""Teacher TE3a, migration 249 (built as 248, renumbered after TE2's 248 at landing): ``ad_reading_opportunities``'
kind CHECK gains ``'lesson'``
(spec_teacher_v1 rev 5 §14.2, §18.2, §20 row TE3a, §24).

The table is rebuilt temp-then-rename with every row and id preserved: the same columns, unique keys, indexes and
append-only triggers; only the kind list widens. Nothing else in the schema changes.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import PROTECTED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
TABLE = "ad_reading_opportunities"
#: What 249 alters (its table's text: the kind list): earlier migrations' "alters nothing else" diffs read this.
TE3A_ALTERED_TABLES = frozenset({TABLE})
#: The objects 249 drops and recreates (same names): earlier migrations' "nothing else changed" diffs read this.
TE3A_REBUILT_OBJECTS = frozenset({
    TABLE, "idx_ad_reading_opportunities_lo", "idx_ad_reading_opportunities_written",
    f"{TABLE}_no_update", f"{TABLE}_no_delete", f"sqlite_autoindex_{TABLE}_1", f"sqlite_autoindex_{TABLE}_2",
    f"sqlite_autoindex_{TABLE}_3",
})
_ROW = ("INSERT INTO ad_reading_opportunities(id, opportunity_key, kind, subkind, source_table, source_id, "
        "source_written_at, learning_object_id, facet_doses_json, mapping_version, sweep, swept_at, protection_epoch) "
        "VALUES (?, ?, ?, ?, ?, ?, '2026-11-06T10:00:00Z', 'lo_1', '{\"f\": 1.0}', 'v', 'serve', "
        "'2026-11-06T10:00:00Z', 'e')")


def test_249_is_the_head_and_the_table_stays_a_receipt_ad_reads_by_its_rules():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[249] == "249_ad_lesson_opportunities.sql"
    assert names[248] == "248_teacher_te2_sources.sql"  # TE2's, landed first
    assert TABLE_ROLES[TABLE] is TableRole.RECEIPT
    assert ROLES[TABLE] == PROTECTED


def test_the_head_fixture_holds_249_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (TABLE,)).fetchone()[0]
        assert "'in_passage_question', 'lesson'" in sql


def _downgraded(database: Path) -> None:
    """The head as it stood at 248: the table rebuilt with 214's kind list, 249's row removed."""

    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    old_check = "CHECK (kind IN ('reading', 'reader_tutor_exchange', 'worked_example', 'in_passage_question'))"
    with closing(sqlite3.connect(database)) as connection:
        objects = connection.execute("SELECT type, name, sql FROM sqlite_master WHERE tbl_name = ? AND sql IS NOT NULL "
                                     "AND type != 'table'", (TABLE,)).fetchall()
        table_sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (TABLE,)).fetchone()[0]
        connection.execute(f"DROP TABLE {TABLE}")
        connection.execute(table_sql.replace(
            "CHECK (kind IN ('reading', 'reader_tutor_exchange', 'worked_example', 'in_passage_question', 'lesson'))",
            old_check))
        for _type, _name, sql in objects:
            connection.execute(sql)
        connection.execute("DELETE FROM schema_migrations WHERE version = 249")
        connection.commit()


def test_249_widens_the_kind_and_keeps_every_row_key_index_and_trigger(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_ROW, ("o0", "k0", "lesson", "landed", "lesson_receipts", "les_0/n1"))
        connection.execute(_ROW, ("o1", "k1", "reading", "section_read", "reader_section_progress", "e/s"))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [249]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        # Every object keeps its name; only the table's own text changed (its kind list), nothing else at all.
        assert set(after) == set(before)
        changed = {name for name in after if after[name] != before[name]}
        assert changed == {TABLE}
        assert TE3A_REBUILT_OBJECTS <= set(after)
        assert after[TABLE].count("'lesson'") == 1
        assert " ".join(after[TABLE].replace(", 'lesson'", "").split()) == " ".join(before[TABLE].split())
        assert [tuple(row) for row in connection.execute("SELECT id, kind FROM ad_reading_opportunities")] == [
            ("o1", "reading")]
        connection.execute(_ROW, ("o2", "k2", "lesson", "landed", "lesson_receipts", "les_1/n1"))
        connection.execute(_ROW, ("o3", "k3", "lesson", "taught", "lesson_receipts", "les_1/n2"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_ROW, ("o4", "k4", "lecture", "landed", "lesson_receipts", "les_1/n3"))
        with pytest.raises(sqlite3.IntegrityError):  # the same (kind, subkind, source, LO, epoch) once
            connection.execute(_ROW, ("o5", "k5", "lesson", "landed", "lesson_receipts", "les_1/n1"))
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE ad_reading_opportunities SET subkind = 'taught' WHERE id = 'o2'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM ad_reading_opportunities WHERE id = 'o2'")
