"""Reader RW5c P1: migration 238, ``figure_source_checks`` (spec_reader_rw5c_checked_labels_v1 §10.2).

An append-only ledger (RAW_LEDGER, no replayer), classified for rebuild and for AD (PROTECTED and
unread). The head fixture is at 240 in rollback mode with an empty table. Earlier migrations'
"nothing else changed" diffs on the way to head read ``RW5C_ADDED_OBJECTS``.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import column_classes as CC
from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, applied_versions, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TableRole, role_for_table

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_242" / "state.sqlite"
#: What 238 adds (its table, its autoindex, its index and triggers).
RW5C_ADDED_OBJECTS = frozenset({
    "figure_source_checks", "sqlite_autoindex_figure_source_checks_1", "idx_figure_source_checks_figure",
    "figure_source_checks_no_update", "figure_source_checks_no_delete",
})


def _names(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}


def test_238_is_applied_and_the_table_is_classified():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[238] == "238_figure_source_checks.sql"
    assert role_for_table("figure_source_checks") == TableRole.RAW_LEDGER
    assert PT.role("figure_source_checks") == PT.PROTECTED
    assert "figure_source_checks" in CC.CLASSES


def test_the_head_fixture_is_past_238_in_rollback_mode_with_an_empty_table():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(migration.version for migration in discover_migrations()) == 242
    with closing(sqlite3.connect(HEAD)) as connection:
        assert RW5C_ADDED_OBJECTS <= _names(connection)
        assert connection.execute("SELECT COUNT(*) FROM figure_source_checks").fetchone()[0] == 0


def _row(figure_id: str, judgment_id: str, row_id: str = "fsc_1") -> tuple:
    return (row_id, figure_id, 1, "build", "checked", "[]", "[]", "{}", "sha", "book-math-v1", "1.14.0", 12, judgment_id,
            "2026-11-02T00:00:00Z")


INSERT = ('INSERT INTO figure_source_checks (id, figure_id, certification_version, "trigger", outcome, definitions_json, '
          "elements_json, reasons_json, harness_sha256, reader_version, sympy_version, duration_ms, judgment_id, "
          "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")


@pytest.fixture
def database(tmp_path: Path) -> Path:
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    return paths.root / "state.sqlite" if (paths.root / "state.sqlite").exists() else Path(paths.sqlite)


def test_rows_are_append_only_and_the_values_closed(database: Path):
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(INSERT, _row("fig_1", "j1"))
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE figure_source_checks SET outcome = 'differs'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM figure_source_checks")
        bad_trigger = list(_row("fig_1", "j1", "fsc_2"))
        bad_trigger[3] = "open"
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(INSERT, tuple(bad_trigger))
        bad_outcome = list(_row("fig_1", "j1", "fsc_3"))
        bad_outcome[4] = "verified"
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(INSERT, tuple(bad_outcome))


@pytest.mark.durability
def test_238_upgrades_a_copy_of_237_under_the_durable_pragmas(tmp_path: Path):
    """The new table upgrades cleanly under WAL and synchronous=FULL (the durability lane)."""

    with closing(sqlite3.connect(HEAD)) as head:
        statements = [row[0] for row in head.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'schema_migrations' AND sql IS NOT NULL")]
    assert statements
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("DROP TRIGGER figure_source_checks_no_update")
        connection.execute("DROP TRIGGER figure_source_checks_no_delete")
        connection.execute("DROP TABLE figure_source_checks")
        connection.execute("DELETE FROM schema_migrations WHERE version = 238")
        connection.commit()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == [238]
    with closing(sqlite3.connect(database)) as connection:
        assert RW5C_ADDED_OBJECTS <= _names(connection)
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
