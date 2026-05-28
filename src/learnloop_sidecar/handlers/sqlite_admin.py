from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

# Raw SQLite browser/editor for the Library screen. This is a deliberate, power-user
# escape hatch: it talks to the database file directly and bypasses the app's
# invariants (FSRS state, mastery, proposals). Everything is sandboxed to the vault
# root, table/column names are validated against the live schema before being
# interpolated, and all values bind as parameters.

_SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}
_MAX_EXEC_ROWS = 500
_DEFAULT_PAGE = 200
_MAX_PAGE = 1000


def _resolve_db(ctx: SidecarContext, path: str) -> Path:
    vault, _repository = ctx.require_vault()
    root = vault.root.resolve()
    target = (root / path).resolve()
    if target != root and root not in target.parents:
        raise SidecarError("invalid_path", "Path escapes the vault root.")
    if target.suffix.lower() not in _SQLITE_SUFFIXES or not target.is_file():
        raise SidecarError("not_found", f"{path} is not a sqlite database in the vault.")
    return target


def _connect(target: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(target))
    connection.row_factory = sqlite3.Row
    return connection


def _qid(identifier: str) -> str:
    """Quote an identifier (table/column) so a validated name is safe to interpolate."""

    return '"' + identifier.replace('"', '""') + '"'


def _user_tables(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [row["name"] for row in rows]


def _require_table(connection: sqlite3.Connection, table: str) -> None:
    if table not in _user_tables(connection):
        raise SidecarError("not_found", f"Table {table!r} does not exist in this database.")


def _cell(value: Any) -> Any:
    """Render a column value as something JSON-native; blobs become a placeholder."""

    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<blob {len(bytes(value))} bytes>"
    return value  # int / float / str / None pass straight through.


def _coerce(value: Any, declared_type: str | None) -> Any:
    """Best-effort coercion of a string edit to the column's declared affinity."""

    if value is None:
        return None
    text = str(value)
    if text == "":
        return None
    affinity = (declared_type or "").upper()
    if "INT" in affinity:
        try:
            return int(text)
        except ValueError:
            pass
    if any(token in affinity for token in ("REAL", "FLOA", "DOUB", "NUM", "DEC")):
        try:
            return float(text)
        except ValueError:
            pass
    return text


class DbPathInput(ParamsModel):
    path: str


@method("sqlite_tables", DbPathInput)
def sqlite_tables(ctx: SidecarContext, params: DbPathInput) -> dict[str, Any]:
    """List the user tables/views in a vault sqlite database with row counts."""

    target = _resolve_db(ctx, params.path)
    with closing(_connect(target)) as connection:
        tables: list[dict[str, Any]] = []
        for name in _user_tables(connection):
            count = connection.execute(f"SELECT COUNT(*) AS c FROM {_qid(name)}").fetchone()["c"]
            tables.append({"name": name, "row_count": count})
    return versioned({"path": params.path, "tables": tables})


class TablePageInput(ParamsModel):
    path: str
    table: str
    limit: int = _DEFAULT_PAGE
    offset: int = 0


@method("sqlite_table", TablePageInput)
def sqlite_table(ctx: SidecarContext, params: TablePageInput) -> dict[str, Any]:
    """A page of rows for one table, with column metadata.

    Rows are addressed by ``rowid``; tables declared ``WITHOUT ROWID`` (no implicit
    rowid) come back with ``editable=False`` and ``rowid=None``.
    """

    target = _resolve_db(ctx, params.path)
    with closing(_connect(target)) as connection:
        _require_table(connection, params.table)
        qid = _qid(params.table)
        info = connection.execute(f"PRAGMA table_info({qid})").fetchall()
        columns = [
            {"name": r["name"], "type": r["type"], "pk": bool(r["pk"]), "notnull": bool(r["notnull"])}
            for r in info
        ]
        names = [c["name"] for c in columns]
        primary_key = [c["name"] for c in columns if c["pk"]]
        total = connection.execute(f"SELECT COUNT(*) AS c FROM {qid}").fetchone()["c"]
        limit = max(1, min(int(params.limit), _MAX_PAGE))
        offset = max(0, int(params.offset))

        rows: list[dict[str, Any]] = []
        editable = True
        try:
            fetched = connection.execute(
                f"SELECT rowid AS __rowid__, * FROM {qid} LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
            for row in fetched:
                record = dict(row)
                rowid = record.pop("__rowid__")
                rows.append({"rowid": rowid, "cells": [_cell(record[name]) for name in names]})
        except sqlite3.OperationalError:
            # WITHOUT ROWID table — still browsable, just not row-addressable here.
            editable = False
            fetched = connection.execute(
                f"SELECT * FROM {qid} LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
            for row in fetched:
                record = dict(row)
                rows.append({"rowid": None, "cells": [_cell(record[name]) for name in names]})

    return versioned(
        {
            "path": params.path,
            "table": params.table,
            "columns": columns,
            "primary_key": primary_key,
            "row_count": total,
            "editable": editable,
            "rows": rows,
        }
    )


class ExecInput(ParamsModel):
    path: str
    sql: str


@method("sqlite_exec", ExecInput)
def sqlite_exec(ctx: SidecarContext, params: ExecInput) -> dict[str, Any]:
    """Run a single arbitrary SQL statement (the console).

    Read statements return capped rows; write statements commit and report the
    affected-row count and last insert rowid.
    """

    target = _resolve_db(ctx, params.path)
    sql = params.sql.strip()
    if not sql:
        raise SidecarError("invalid_sql", "Empty SQL statement.")
    with closing(_connect(target)) as connection:
        try:
            cursor = connection.execute(sql)
        except sqlite3.Error as exc:
            raise SidecarError("sql_error", str(exc)) from exc
        if cursor.description is not None:
            columns = [description[0] for description in cursor.description]
            fetched = cursor.fetchmany(_MAX_EXEC_ROWS)
            truncated = len(fetched) == _MAX_EXEC_ROWS and cursor.fetchone() is not None
            return versioned(
                {
                    "kind": "rows",
                    "columns": columns,
                    "rows": [[_cell(value) for value in row] for row in fetched],
                    "truncated": truncated,
                }
            )
        connection.commit()
        return versioned(
            {"kind": "write", "rows_affected": cursor.rowcount, "last_insert_row_id": cursor.lastrowid}
        )


class UpdateCellInput(ParamsModel):
    path: str
    table: str
    rowid: int
    column: str
    value: Any = None


@method("sqlite_update_cell", UpdateCellInput)
def sqlite_update_cell(ctx: SidecarContext, params: UpdateCellInput) -> dict[str, Any]:
    """Update one cell, identified by table + rowid + column."""

    target = _resolve_db(ctx, params.path)
    with closing(_connect(target)) as connection:
        _require_table(connection, params.table)
        qid = _qid(params.table)
        info = connection.execute(f"PRAGMA table_info({qid})").fetchall()
        column = next((r for r in info if r["name"] == params.column), None)
        if column is None:
            raise SidecarError("not_found", f"Column {params.column!r} does not exist on {params.table}.")
        coerced = _coerce(params.value, column["type"])
        try:
            connection.execute(
                f"UPDATE {qid} SET {_qid(params.column)} = ? WHERE rowid = ?",
                (coerced, params.rowid),
            )
            connection.commit()
        except sqlite3.Error as exc:
            raise SidecarError("sql_error", str(exc)) from exc
    return versioned({"ok": True})


class InsertRowInput(ParamsModel):
    path: str
    table: str


@method("sqlite_insert_row", InsertRowInput)
def sqlite_insert_row(ctx: SidecarContext, params: InsertRowInput) -> dict[str, Any]:
    """Insert a blank row and return its new rowid for in-place cell editing."""

    target = _resolve_db(ctx, params.path)
    with closing(_connect(target)) as connection:
        _require_table(connection, params.table)
        qid = _qid(params.table)
        try:
            cursor = connection.execute(f"INSERT INTO {qid} DEFAULT VALUES")
            connection.commit()
        except sqlite3.Error:
            # DEFAULT VALUES fails when a column is NOT NULL without a default;
            # fall back to an explicit all-NULL insert.
            info = connection.execute(f"PRAGMA table_info({qid})").fetchall()
            cols = [r["name"] for r in info]
            collist = ", ".join(_qid(name) for name in cols)
            placeholders = ", ".join("?" for _ in cols)
            try:
                cursor = connection.execute(
                    f"INSERT INTO {qid} ({collist}) VALUES ({placeholders})", [None] * len(cols)
                )
                connection.commit()
            except sqlite3.Error as exc:
                raise SidecarError("sql_error", f"Could not insert a blank row: {exc}") from exc
    return versioned({"rowid": cursor.lastrowid})


class DeleteRowInput(ParamsModel):
    path: str
    table: str
    rowid: int


@method("sqlite_delete_row", DeleteRowInput)
def sqlite_delete_row(ctx: SidecarContext, params: DeleteRowInput) -> dict[str, Any]:
    """Delete one row, identified by table + rowid."""

    target = _resolve_db(ctx, params.path)
    with closing(_connect(target)) as connection:
        _require_table(connection, params.table)
        qid = _qid(params.table)
        try:
            connection.execute(f"DELETE FROM {qid} WHERE rowid = ?", (params.rowid,))
            connection.commit()
        except sqlite3.Error as exc:
            raise SidecarError("sql_error", str(exc)) from exc
    return versioned({"ok": True})
