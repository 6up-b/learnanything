"""Reader RW5d P1: migration 224 (spec_reader_show_me_figures_v1 §13.1; G-SM8).

``figure_requests`` is new (RAW_LEDGER: append-only, ``figure_id`` set once);
``interactive_figures`` is rebuilt with every RW5a/b row copied unchanged,
its CHECKs widened (origin, a nullable home named by its request, the tier)
and the columns P2b and P5 need reserved. ``figure_predictions``' foreign key
resolves to the rebuilt table. No DERIVED table, so no replayer.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import discover_migrations
from learnloop.db.table_roles import TableRole, role_for_table
from tests.helpers import create_basic_vault

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
#: Every schema object 224 adds, and the table it rebuilds: the earlier
#: migrations' "nothing else changed" diffs on the way to head read these.
RW5D_ADDED_OBJECTS = frozenset({
    "figure_requests", "sqlite_autoindex_figure_requests_1", "idx_figure_requests_figure",
    "idx_figure_requests_created", "figure_requests_no_delete", "figure_requests_figure_once",
    "idx_interactive_figures_request",
})
RW5D_ALTERED_TABLES = frozenset({"interactive_figures"})
RW5A_COLUMNS = ("id", "extraction_id", "span_ids_json", "region_json", "asset_id", "input_span_ids_json", "origin",
                "supersedes_id", "revision_note", "spec_json", "spec_version", "kind", "verification",
                "verification_report_json", "unsupported_kind", "model", "prompt_version", "input_hash", "created_at")


def test_224_is_the_figure_requests_migration_and_the_table_is_a_raw_ledger():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[224] == "224_figure_requests.sql"
    assert role_for_table("figure_requests") == TableRole.RAW_LEDGER
    assert role_for_table("interactive_figures") == TableRole.WORKFLOW


def _rw5a_database(path: Path) -> sqlite3.Connection:
    """216's two tables as they stood, with RW5a/b rows of every shape."""

    connection = sqlite3.connect(path)
    connection.executescript((MIGRATIONS / "216_interactive_figures.sql").read_text(encoding="utf-8"))
    rows = [
        ("fig_a", "ext", '["p3"]', None, None, '["p3","p2"]', "selection", None, None, '{"k":1}', "ifs-v1",
         "illustrative", "illustrative", '{"reason":"r"}', None, "m", "figure_author.v1", "h1", "2026-10-21T00:00:00"),
        ("fig_b", "ext", '[]', '{"bbox":[1,2,3,4],"span_id":"p4"}', "p4", '["p4"]', "library", None, None, None,
         "ifs-v1", None, "unsupported", '{}', "3-D surface", "m", "figure_author.v2-panels", "h2",
         "2026-10-21T00:00:01"),
        ("fig_c", "ext", '["p3"]', None, None, '["p3"]', "tutor", "fig_a", "slower", '{"k":2}', "ifs-v1",
         "reconstructed", "verified", '{}', None, "m", "figure_author.v1", "h3", "2026-10-21T00:00:02"),
        ("fig_d", "ext", '["p3"]', None, None, '[]', "selection", None, None, None, "ifs-v1", None, "failed",
         '{"reason":"bad"}', None, None, "figure_author.v1", "h1", "2026-10-21T00:00:03"),
    ]
    connection.executemany(f"INSERT INTO interactive_figures ({', '.join(RW5A_COLUMNS)}) "
                           f"VALUES ({', '.join('?' for _ in RW5A_COLUMNS)})", rows)
    connection.execute("INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, "
                       "learner_answer, observed_json, matched, created_at) VALUES "
                       "('fpr_1', 'fig_a', 'ext', 0, 'rises', '{}', 0, '2026-10-21T00:00:04')")
    connection.commit()
    return connection


def test_every_rw5ab_row_is_copied_unchanged_and_the_keys_hold(tmp_path):
    with closing(_rw5a_database(tmp_path / "state.sqlite")) as connection:
        before = connection.execute(f"SELECT {', '.join(RW5A_COLUMNS)} FROM interactive_figures ORDER BY id").fetchall()
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.executescript((MIGRATIONS / "224_figure_requests.sql").read_text(encoding="utf-8"))
        connection.execute("PRAGMA foreign_keys = ON")
        after = connection.execute(f"SELECT {', '.join(RW5A_COLUMNS)} FROM interactive_figures ORDER BY id").fetchall()
        assert after == before
        defaults = connection.execute(
            "SELECT DISTINCT request_id, goal_text, grounding, input_span_keys_json, tier, checks_json, fuller_of_id "
            "FROM interactive_figures").fetchall()
        assert defaults == [(None, None, "anchor", "[]", "grammar", "[]", None)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        indexes = {row[1] for row in connection.execute("PRAGMA index_list(interactive_figures)")}
        assert {"idx_interactive_figures_extraction", "idx_interactive_figures_input",
                "idx_interactive_figures_supersedes", "idx_interactive_figures_reuse",
                "idx_interactive_figures_request"} <= indexes
        # figure_predictions still names the rebuilt table.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, "
                               "learner_answer, observed_json, matched, created_at) VALUES "
                               "('fpr_2', 'fig_missing', 'ext', 1, 'x', '{}', 0, 't')")


def _db(tmp_path, *, fresh: bool = False):
    return create_basic_vault(tmp_path / "vault", fresh=fresh).sqlite_path


def _request(connection, request_id="frq_1", **overrides):
    row = {"id": request_id, "origin": "show_me", "goal_text": "show me", "goal_author": "learner",
           "anchor_json": None, "reading_at_json": '{"extraction_id":"ext","span_id":"p2"}', "policy": "reading",
           "caller_kind": "reader", "grounding": "none", "created_at": "2026-10-26T00:00:00"}
    row.update(overrides)
    connection.execute(f"INSERT INTO figure_requests ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                       tuple(row.values()))


def _figure(connection, figure_id="fig_1", **overrides):
    row = {"id": figure_id, "extraction_id": "ext", "origin": "show_me", "spec_json": "{}", "spec_version": "ifs-v1",
           "kind": "illustrative", "verification": "illustrative", "prompt_version": "p", "input_hash": figure_id,
           "created_at": "2026-10-26T00:00:01"}
    row.update(overrides)
    connection.execute(f"INSERT INTO interactive_figures ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                       tuple(row.values()))


def test_the_checks_and_the_append_only_ledger(tmp_path):
    with closing(sqlite3.connect(_db(tmp_path))) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _request(connection)
        for bad in ({"origin": "chat"}, {"goal_author": "someone"}, {"grounding": "maybe"},
                    {"goal_author": None}, {"goal_text": None, "goal_author": None},
                    {"build_mode": "eager"}, {"figure_id": "fig_missing"}):
            with pytest.raises(sqlite3.IntegrityError):
                _request(connection, "frq_bad", **bad)
        # Anchor-only (RW5a/b through the ledger): no goal, an anchor.
        _request(connection, "frq_anchor", goal_text=None, goal_author=None, origin="selection",
                 anchor_json='{"extraction_id":"ext","span_ids":["p3"]}', grounding="anchor")
        _figure(connection, request_id="frq_1", goal_text="show me", grounding="none")
        # A practice-host figure (P3) has no home but its request; never neither.
        _figure(connection, "fig_2", extraction_id=None, request_id="frq_1")
        for bad in ({"extraction_id": None}, {"origin": "chat"}, {"tier": "video"}, {"grounding": "elsewhere"},
                    {"request_id": "frq_missing"}, {"fuller_of_id": "fig_missing"}):
            with pytest.raises(sqlite3.IntegrityError):
                _figure(connection, "fig_bad", **bad)
        connection.execute("UPDATE figure_requests SET figure_id = 'fig_1' WHERE id = 'frq_1'")
        for statement in ("UPDATE figure_requests SET figure_id = 'fig_2' WHERE id = 'frq_1'",
                          "UPDATE figure_requests SET goal_text = 'x' WHERE id = 'frq_anchor'",
                          "UPDATE figure_requests SET figure_id = NULL WHERE id = 'frq_anchor'",
                          "DELETE FROM figure_requests"):
            with pytest.raises(sqlite3.DatabaseError):
                connection.execute(statement)


@pytest.mark.durability
def test_fresh_vault_migrates_224_under_wal_with_clean_keys(tmp_path):
    database = _db(tmp_path, fresh=True)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert 224 in {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
        triggers = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
        assert {"figure_requests_no_delete", "figure_requests_figure_once"} <= triggers
        connection.execute("PRAGMA foreign_keys = ON")
        _request(connection)
        _figure(connection, request_id="frq_1")
        connection.execute("UPDATE figure_requests SET figure_id = 'fig_1' WHERE id = 'frq_1'")
        connection.commit()
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_no_replayer_reads_the_request_ledger():
    from learnloop.substrate import rebuild_orchestrator as RO

    assert "figure_requests" not in __import__("inspect").getsource(RO)
