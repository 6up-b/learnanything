"""Side-effect-free facts about where and how a SQLite database is stored.

Doctor reports these without opening a connection: the journal mode comes from
the database header, the WAL size from ``stat``, and the filesystem from the
mount table.  WAL keeps its index in a memory-mapped ``-shm`` file that every
connection must share, which network filesystems do not provide across hosts
and FUSE filesystems provide only when they support shared writable mappings.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Filesystem types (as /proc/mounts names them) whose files may be shared
# between hosts or are served by a userspace daemon.
NETWORK_FILESYSTEM_TYPES = frozenset(
    {
        "9p",
        "afs",
        "ceph",
        "cifs",
        "coda",
        "davfs",
        "glusterfs",
        "gpfs",
        "lustre",
        "ncpfs",
        "nfs",
        "nfs4",
        "ocfs2",
        "smb3",
        "smbfs",
        "sshfs",
        "virtiofs",
    }
)

# Header bytes 18 and 19 are the file-format write and read versions: 1 for a
# rollback journal, 2 for WAL.
_HEADER_SIZE = 100
_WAL_FORMAT_VERSION = 2
_ROLLBACK_FORMAT_VERSION = 1
_SQLITE_MAGIC = b"SQLite format 3\x00"

DEFAULT_MOUNTS_FILE = Path("/proc/mounts")


@dataclass(frozen=True)
class MountEntry:
    mount_point: str
    filesystem_type: str
    source: str

    @property
    def network_or_fuse(self) -> bool:
        return is_network_or_fuse_filesystem(self.filesystem_type)


@dataclass(frozen=True)
class DatabaseStorage:
    """Journal mode, WAL size and filesystem of one database file."""

    journal_mode: str
    wal_bytes: int
    mount: MountEntry | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "journal_mode": self.journal_mode,
            "wal_bytes": self.wal_bytes,
            "filesystem_type": self.mount.filesystem_type if self.mount else None,
            "mount_point": self.mount.mount_point if self.mount else None,
            "network_or_fuse": self.mount.network_or_fuse if self.mount else None,
        }


def is_network_or_fuse_filesystem(filesystem_type: str) -> bool:
    kind = filesystem_type.lower()
    return kind in NETWORK_FILESYSTEM_TYPES or kind == "fuse" or kind.startswith(("fuse.", "fuseblk"))


def header_journal_mode(sqlite_path: Path) -> str:
    """``"wal"``, ``"rollback"``, or ``"unknown"`` from the file header alone."""

    try:
        with Path(sqlite_path).open("rb") as handle:
            header = handle.read(_HEADER_SIZE)
    except OSError:
        return "unknown"
    if len(header) < _HEADER_SIZE or not header.startswith(_SQLITE_MAGIC):
        return "unknown"
    write_version, read_version = header[18], header[19]
    if write_version == _WAL_FORMAT_VERSION and read_version == _WAL_FORMAT_VERSION:
        return "wal"
    if write_version == _ROLLBACK_FORMAT_VERSION and read_version == _ROLLBACK_FORMAT_VERSION:
        return "rollback"
    return "unknown"


def wal_size_bytes(sqlite_path: Path) -> int:
    wal_path = Path(sqlite_path).with_name(Path(sqlite_path).name + "-wal")
    try:
        return wal_path.stat().st_size
    except FileNotFoundError:
        return 0


def _unescape_mount_field(field: str) -> str:
    # /proc/mounts escapes space, tab, newline and backslash as octal.
    for escaped, character in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        field = field.replace(escaped, character)
    return field


def read_mount_table(mounts_file: Path = DEFAULT_MOUNTS_FILE) -> list[MountEntry] | None:
    """Parsed mount table, or ``None`` where there is none to read (non-Linux)."""

    if not sys.platform.startswith("linux") and mounts_file == DEFAULT_MOUNTS_FILE:
        return None
    try:
        text = mounts_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    entries: list[MountEntry] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        entries.append(
            MountEntry(
                mount_point=_unescape_mount_field(fields[1]),
                filesystem_type=fields[2],
                source=_unescape_mount_field(fields[0]),
            )
        )
    return entries


def mount_for_path(path: Path, mounts: list[MountEntry]) -> MountEntry | None:
    """The mount with the longest mount point containing ``path``.

    Later entries win ties because a later mount over the same point hides the
    earlier one.
    """

    resolved = Path(path).resolve()
    best: MountEntry | None = None
    best_depth = -1
    for entry in mounts:
        mount_point = Path(entry.mount_point)
        if resolved != mount_point and mount_point not in resolved.parents:
            continue
        depth = len(mount_point.parts)
        if depth >= best_depth:
            best, best_depth = entry, depth
    return best


def inspect_database_storage(
    sqlite_path: Path,
    *,
    mounts_file: Path = DEFAULT_MOUNTS_FILE,
) -> DatabaseStorage:
    sqlite_path = Path(sqlite_path)
    mounts = read_mount_table(mounts_file)
    mount = mount_for_path(sqlite_path.parent, mounts) if mounts else None
    return DatabaseStorage(
        journal_mode=header_journal_mode(sqlite_path),
        wal_bytes=wal_size_bytes(sqlite_path),
        mount=mount,
    )


__all__ = [
    "DEFAULT_MOUNTS_FILE",
    "DatabaseStorage",
    "MountEntry",
    "NETWORK_FILESYSTEM_TYPES",
    "header_journal_mode",
    "inspect_database_storage",
    "is_network_or_fuse_filesystem",
    "mount_for_path",
    "read_mount_table",
    "wal_size_bytes",
]
