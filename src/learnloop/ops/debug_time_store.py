"""SQL owner for the debug-time operational mutation."""

from __future__ import annotations

import sqlite3

from learnloop.db.table_roles import role_for_table


def existing_timestamp_fields(
    connection: sqlite3.Connection,
) -> dict[str, set[str]]:
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    existing: dict[str, set[str]] = {}
    for row in tables:
        table = str(row[0])
        role_for_table(table)
        columns = connection.execute(
            f"PRAGMA table_info({_quote_identifier(table)})"
        ).fetchall()
        existing[table] = {str(column[1]) for column in columns}
    return existing


def shift_timestamp_field(
    connection: sqlite3.Connection,
    table: str,
    field: str,
    modifier: str,
) -> int:
    table_sql = _quote_identifier(table)
    field_sql = _quote_identifier(field)
    cursor = connection.execute(
        f"""
        UPDATE {table_sql}
        SET {field_sql} = strftime('%Y-%m-%dT%H:%M:%SZ', datetime({field_sql}, ?))
        WHERE {field_sql} IS NOT NULL
        """,
        (modifier,),
    )
    return int(cursor.rowcount if cursor.rowcount is not None else 0)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


__all__ = ["existing_timestamp_fields", "shift_timestamp_field"]
