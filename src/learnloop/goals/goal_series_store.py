"""Scratch-database write owner for historical goal-series replay."""

from __future__ import annotations

from typing import Any

from learnloop.db.table_roles import role_for_table

_MAX_PRUNE_DEPTH = 8
_PRUNE_CHUNK = 400


def _chunked(values: list[Any]) -> list[list[Any]]:
    return [
        values[start : start + _PRUNE_CHUNK]
        for start in range(0, len(values), _PRUNE_CHUNK)
    ]


def _referencing_columns(
    connection,
    table: str,
) -> list[tuple[str, str, str, str]]:
    """Return child references as ``(table, column, parent, on_delete)``."""

    refs: list[tuple[str, str, str, str]] = []
    child_tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    ]
    for child in child_tables:
        role_for_table(str(child))
        for fk in connection.execute(f'PRAGMA foreign_key_list("{child}")'):
            _, _, parent_table, child_column, parent_column, _, on_delete, *_ = fk
            if parent_table == table:
                refs.append(
                    (child, child_column, parent_column or "rowid", on_delete)
                )
    return refs


def _distinct_column(
    connection,
    table: str,
    column: str,
    key: str,
    values: list[Any],
) -> list[Any]:
    found: list[Any] = []
    seen: set[Any] = set()
    for chunk in _chunked(values):
        placeholders = ",".join("?" * len(chunk))
        rows = connection.execute(
            f'SELECT DISTINCT "{column}" FROM "{table}" '
            f'WHERE "{key}" IN ({placeholders})',
            chunk,
        )
        for (value,) in rows:
            if value is not None and value not in seen:
                seen.add(value)
                found.append(value)
    return found


def prune_rows(
    connection,
    table: str,
    column: str,
    values: list[Any],
    *,
    delete_rows: bool = True,
    depth: int = 0,
) -> None:
    """Prune scratch rows while respecting non-cascading foreign keys."""

    if not values or depth > _MAX_PRUNE_DEPTH:
        return
    for child, child_column, parent_column, on_delete in _referencing_columns(
        connection, table
    ):
        keys = _distinct_column(connection, table, parent_column, column, values)
        if not keys:
            continue
        if on_delete == "SET NULL":
            for chunk in _chunked(keys):
                placeholders = ",".join("?" * len(chunk))
                connection.execute(
                    f'UPDATE "{child}" SET "{child_column}" = NULL '
                    f'WHERE "{child_column}" IN ({placeholders})',
                    chunk,
                )
            continue
        prune_rows(
            connection,
            child,
            child_column,
            keys,
            delete_rows=on_delete != "CASCADE",
            depth=depth + 1,
        )
    if not delete_rows:
        return
    for chunk in _chunked(values):
        placeholders = ",".join("?" * len(chunk))
        connection.execute(
            f'DELETE FROM "{table}" WHERE "{column}" IN ({placeholders})',
            chunk,
        )


__all__ = ["prune_rows"]
