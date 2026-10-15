"""Migration 196 (facet rewords) composed after main's 195 (source service spend accounting).

facets/locks-and-depends-on wrote this migration as 188 on a 183 base; it was
renumbered 185 when it merged after EVSI calibration's 184, and 196 when it
landed on main after RW1a (185), the route check (186) and the sources track
(187-195). The tracked head fixture holds no facet-identity action, so this
upgrades a database at 195 that carries a 183-era action and a forecast
receipt: the rebuild keeps every action row and id as written, admits the new
reword/proposal/registry values, and leaves the append-only forecast log and
its triggers alone.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, applied_versions, discover_migrations

ACTION_COLUMNS = (
    "id, created_at, origin, scope, run_id, proposal_id, action, survivor_facet_id, "
    "retired_facet_ids_json, before_json, after_json, merge_rows_json, judgment_ids_json, "
    "judge, judge_model, prompt_version, detail_json, status, applied_at, undone_at, undo_detail_json"
)


def _migrations_through(tmp_path: Path, last: int) -> Path:
    directory = tmp_path / f"migrations_through_{last}"
    directory.mkdir()
    for migration in discover_migrations():
        if migration.version <= last:
            (directory / migration.path.name).symlink_to(migration.path)
    return directory


def _action(action_id: str, *, origin: str, scope: str, action: str, retired: list[str]) -> tuple:
    return (
        action_id, "2026-10-12T10:00:00+00:00", origin, scope, "run_1", None, action, "facet_survivor",
        json.dumps(retired), json.dumps({"facet_survivor": {"id": "facet_survivor", "claim": "old"}}),
        json.dumps({"facet_survivor": {"id": "facet_survivor", "claim": "new"}}), "[]", "[]",
        "owner", None, None, "{}", "applied", "2026-10-12T10:00:01+00:00", None, None,
    )


def _insert(connection: sqlite3.Connection, row: tuple) -> None:
    connection.execute(
        f"INSERT INTO facet_identity_actions({ACTION_COLUMNS}) VALUES ({', '.join('?' * len(row))})", row
    )


def _voi_objects(connection: sqlite3.Connection) -> list[tuple]:
    return list(connection.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'voi_forecasts' ORDER BY type, name"
    ))


def test_migration_196_upgrades_a_195_vault_keeping_actions_and_the_forecast_log(tmp_path, migration_upgrade_allowed):
    assert [m.version for m in discover_migrations() if m.version >= 195][:3] == [195, 196, 197]
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, migrations_dir=_migrations_through(tmp_path, 195))
    assert max(applied_versions(sqlite_path)) == 195

    merge = _action("fia_merge", origin="ingest", scope="in_run", action="merge", retired=["facet_retired"])
    with closing(connect(sqlite_path)) as connection:
        _insert(connection, merge)
        # 183's CHECKs (unchanged through 195): no reword, and no proposal or registry origin.
        with pytest.raises(sqlite3.IntegrityError):
            _insert(connection, _action("fia_early", origin="proposal", scope="vault", action="reword", retired=[]))
        connection.execute(
            "INSERT INTO voi_forecasts(id, receipt_key, site, verdict, candidate_count, forecast_json, "
            "parameters_json, versions_json, forecast_version, created_at) "
            "VALUES ('vf_1', 'probe_selection:pres_1', 'probe_selection', 'select', 2, '{}', '{}', '{}', "
            "'voi_forecast_v4', '2026-10-12T10:00:02+00:00')"
        )
        connection.commit()
        voi_before = _voi_objects(connection)
        forecasts_before = list(connection.execute("SELECT * FROM voi_forecasts"))

    applied = apply_migrations(sqlite_path, migrations_dir=_migrations_through(tmp_path, 196))
    assert [migration.version for migration in applied] == [196]

    with closing(connect(sqlite_path)) as connection:
        rows = list(connection.execute(f"SELECT {ACTION_COLUMNS} FROM facet_identity_actions"))
        assert [tuple(row) for row in rows] == [merge]
        for action_id, origin in (("fia_reword", "proposal"), ("fia_library", "registry")):
            _insert(connection, _action(action_id, origin=origin, scope="vault", action="reword", retired=[]))
        with pytest.raises(sqlite3.IntegrityError):
            _insert(connection, _action("fia_bad", origin="owner", scope="vault", action="reword", retired=[]))
        indexes = {
            row["name"] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'facet_identity_actions'"
            )
        }
        assert {"facet_identity_actions_run", "facet_identity_actions_survivor"} <= indexes
        assert _voi_objects(connection) == voi_before
        assert list(connection.execute("SELECT * FROM voi_forecasts")) == forecasts_before
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("DELETE FROM voi_forecasts")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
