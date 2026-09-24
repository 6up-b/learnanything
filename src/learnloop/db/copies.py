"""Copies of SQLite databases and of directory trees that contain them.

In WAL mode a committed transaction can live in ``<name>-wal`` until a
checkpoint moves it into the main file, so a byte copy of the main file alone
can drop acknowledged commits, and copying the main file and its ``-wal``
while a writer is active can pair pages from two different moments.  Every
copy of a database therefore reads one consistent snapshot through SQLite's
backup API, and tree copies never byte-copy a database or its companion files.

This module is the audited copier that ``tests/test_sqlite_file_copies.py``
allows; other code copies databases by calling it.
"""

from __future__ import annotations

import shutil
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Callable, Collection, Iterable

from learnloop.db.connection import connect

DATABASE_SUFFIX = ".sqlite"
# How long a copy keeps retrying a source that another connection has locked.
BACKUP_BUSY_DEADLINE_S = 5.0
_BUSY_RETRY_SLEEP_S = 0.05
# sqlite3_backup_step results that sqlite3.Connection.backup retries.
_SQLITE_BUSY = 5
_SQLITE_LOCKED = 6
_RETRIED_STATUSES = frozenset({_SQLITE_BUSY, _SQLITE_LOCKED})
COMPANION_SUFFIXES = ("-wal", "-shm", "-journal")

IgnoreFunction = Callable[[str, list[str]], Iterable[str]]


class DatabaseCopyTimeout(TimeoutError):
    """The source stayed locked past the backup deadline; nothing was copied."""


def backup_database(
    source_path: Path,
    destination_path: Path,
    *,
    busy_deadline_s: float | None = None,
) -> None:
    """Write a transactionally consistent copy of a database to a new file.

    The source is opened read-only and copied in one backup step, which holds a
    single read snapshot for the whole copy.  In WAL mode that snapshot does not
    block writers.  The copy keeps the source's journal mode, and closing its
    only connection leaves it without companion files.

    ``sqlite3.Connection.backup`` retries a locked source forever, so the
    progress callback enforces a monotonic deadline: once it has passed, a busy
    or locked step raises :class:`DatabaseCopyTimeout`.  Any failure removes the
    incomplete destination and its companion files.
    """

    source_path = Path(source_path)
    destination_path = Path(destination_path)
    if destination_path.exists():
        raise FileExistsError(f"backup destination already exists: {destination_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if busy_deadline_s is None:
        busy_deadline_s = BACKUP_BUSY_DEADLINE_S
    deadline = time.monotonic() + busy_deadline_s

    def stop_after_deadline(status: int, remaining: int, total: int) -> None:
        if status in _RETRIED_STATUSES and time.monotonic() >= deadline:
            raise DatabaseCopyTimeout(
                f"could not copy {source_path}: it stayed locked for more than "
                f"{busy_deadline_s:g} s; retry when no other process holds an "
                "exclusive lock on it"
            )

    try:
        with closing(connect(source_path, read_only=True)) as source:
            with closing(sqlite3.connect(destination_path)) as destination:
                source.backup(destination, progress=stop_after_deadline, sleep=_BUSY_RETRY_SLEEP_S)
    except BaseException:
        _remove_database_files(destination_path)
        raise


def _remove_database_files(database_path: Path) -> None:
    for path in (database_path, *(database_path.with_name(database_path.name + suffix) for suffix in COMPANION_SUFFIXES)):
        path.unlink(missing_ok=True)


def is_database_file_name(name: str, database_names: Collection[str] = ()) -> bool:
    return name.endswith(DATABASE_SUFFIX) or name in database_names


def is_companion_file_name(name: str, database_names: Collection[str] = ()) -> bool:
    for suffix in COMPANION_SUFFIXES:
        if name.endswith(suffix) and is_database_file_name(name[: -len(suffix)], database_names):
            return True
    return False


def copy_tree_without_databases(
    source_root: Path,
    destination_root: Path,
    *,
    database_names: Collection[str] = (),
    ignore: IgnoreFunction | None = None,
    dirs_exist_ok: bool = False,
) -> list[Path]:
    """Copy a directory tree, leaving out every database and companion file.

    ``database_names`` adds file names that are databases without the
    ``.sqlite`` suffix, such as a relocated ``storage.sqlite_path``.  Returns
    the source databases that were left out.
    """

    omitted: list[Path] = []

    def ignore_databases(directory: str, entries: list[str]) -> set[str]:
        ignored = set(ignore(directory, entries)) if ignore is not None else set()
        for entry in entries:
            if entry in ignored:
                continue
            entry_path = Path(directory) / entry
            if is_companion_file_name(entry, database_names):
                ignored.add(entry)
            elif is_database_file_name(entry, database_names) and entry_path.is_file():
                ignored.add(entry)
                omitted.append(entry_path)
        return ignored

    shutil.copytree(source_root, destination_root, ignore=ignore_databases, dirs_exist_ok=dirs_exist_ok)
    return omitted


def copy_tree_with_databases(
    source_root: Path,
    destination_root: Path,
    *,
    database_names: Collection[str] = (),
    ignore: IgnoreFunction | None = None,
    dirs_exist_ok: bool = False,
) -> list[Path]:
    """Copy a directory tree, copying each database through the backup API.

    Companion files are never copied: each backup is a complete database.
    Returns the destination paths of the copied databases.
    """

    source_root = Path(source_root)
    destination_root = Path(destination_root)
    omitted = copy_tree_without_databases(
        source_root,
        destination_root,
        database_names=database_names,
        ignore=ignore,
        dirs_exist_ok=dirs_exist_ok,
    )
    copied: list[Path] = []
    for source_database in omitted:
        destination_database = destination_root / source_database.relative_to(source_root)
        backup_database(source_database, destination_database)
        copied.append(destination_database)
    return copied


__all__ = [
    "BACKUP_BUSY_DEADLINE_S",
    "COMPANION_SUFFIXES",
    "DatabaseCopyTimeout",
    "backup_database",
    "copy_tree_with_databases",
    "copy_tree_without_databases",
    "is_companion_file_name",
    "is_database_file_name",
]
