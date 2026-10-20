"""Reader RW5a: migration 216 (spec §8.5, §11; W9).

``interactive_figures`` is WORKFLOW (paid outputs, never re-run on rebuild)
and ``figure_predictions`` RAW_LEDGER (append-only by trigger, the only update
setting ``explanation_text`` once). Neither has a replayer: no DERIVED table.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from learnloop.db.migrate import discover_migrations
from learnloop.db.table_roles import TableRole, role_for_table as table_role
from tests.helpers import create_basic_vault

TABLES = {"interactive_figures": TableRole.WORKFLOW, "figure_predictions": TableRole.RAW_LEDGER}


def test_216_is_the_figures_migration():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[216] == "216_interactive_figures.sql"


def test_the_tables_are_classified():
    for table, role in TABLES.items():
        assert table_role(table) == role


def _db(tmp_path, *, fresh: bool = False):
    vault = create_basic_vault(tmp_path / "vault", fresh=fresh)
    return vault.sqlite_path


def _insert_figure(connection, figure_id="fig_1", **overrides):
    row = {"id": figure_id, "extraction_id": "ext", "span_ids_json": "[]", "origin": "selection",
           "spec_json": "{}", "spec_version": "ifs-v1", "kind": "illustrative", "verification": "illustrative",
           "prompt_version": "figure_author.v1", "input_hash": "h", "created_at": "2026-10-21T00:00:00"}
    row.update(overrides)
    connection.execute(f"INSERT INTO interactive_figures ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                       tuple(row.values()))


def test_figure_checks(tmp_path):
    with closing(sqlite3.connect(_db(tmp_path))) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _insert_figure(connection)
        for bad in ({"origin": "elsewhere"}, {"verification": "maybe"}, {"verification": "verified", "kind": "illustrative"},
                    {"verification": "illustrative", "spec_json": None}, {"supersedes_id": "missing"}):
            with pytest.raises(sqlite3.IntegrityError):
                _insert_figure(connection, "fig_bad", **bad)
        _insert_figure(connection, "fig_failed", verification="failed", spec_json=None, kind=None)
        _insert_figure(connection, "fig_2", supersedes_id="fig_1", revision_note="start at 0.1")


def _insert_prediction(connection, prediction_id="fpr_1", **overrides):
    row = {"id": prediction_id, "figure_id": "fig_1", "extraction_id": "ext", "prediction_index": 0,
           "learner_answer": "rises", "observed_json": "{}", "matched": 0, "created_at": "2026-10-21T00:00:01"}
    row.update(overrides)
    connection.execute(f"INSERT INTO figure_predictions ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                       tuple(row.values()))


def test_predictions_are_append_only_with_one_explanation(tmp_path):
    with closing(sqlite3.connect(_db(tmp_path))) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _insert_figure(connection)
        _insert_prediction(connection)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_prediction(connection, "fpr_2")  # one answer per (figure, prediction)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_prediction(connection, "fpr_3", figure_id="fig_missing", prediction_index=1)
        for statement in ("UPDATE figure_predictions SET matched = 1", "UPDATE figure_predictions SET learner_answer = 'x'",
                          "DELETE FROM figure_predictions", "UPDATE figure_predictions SET explanation_text = NULL"):
            with pytest.raises(sqlite3.DatabaseError):
                connection.execute(statement)
        connection.execute("UPDATE figure_predictions SET explanation_text = 'p sets the split'")
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("UPDATE figure_predictions SET explanation_text = 'again'")


@pytest.mark.durability
def test_fresh_vault_migrates_216_under_wal_with_clean_keys(tmp_path):
    database = _db(tmp_path, fresh=True)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        versions = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
        assert 216 in versions
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert set(TABLES) <= tables
        triggers = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
        assert {"figure_predictions_no_delete", "figure_predictions_explanation_once"} <= triggers
        connection.execute("PRAGMA foreign_keys = ON")
        _insert_figure(connection)
        _insert_prediction(connection)
        connection.commit()
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_no_replayer_reads_the_figure_tables():
    from learnloop.substrate import rebuild_orchestrator as RO

    source = __import__("inspect").getsource(RO)
    assert "interactive_figures" not in source and "figure_predictions" not in source
