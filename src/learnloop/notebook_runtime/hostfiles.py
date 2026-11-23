"""The only way the unsandboxed side touches the runtime's host files.

The sandbox has no writable host directory: its home and working directory and its ``/tmp`` are tmpfs inside the
sandbox. Everything the host keeps for a session (the notebook snapshot, the server's token, the listening socket,
marimo's config and the hosts file) lives in private directories under the runtime's base directory, which the
sandbox never sees. Even so, every directory is opened without following links and checked to be ours and private
(the base may sit in the shared temporary directory, where another user could plant a link or a directory first),
every file is created afresh and exclusively through its directory's descriptor, never followed, and the socket is
created and bound by trusted code and handed to the server as a descriptor. Anything else found where a file or a
socket is expected (a symlink, a hard link, a FIFO, a directory) is refused, never followed or reused.

A hostile process of the same user is out of scope: it can write these directories itself.
"""
from __future__ import annotations

import errno
import os
import socket
import stat
from pathlib import Path


class UnsafePath(RuntimeError):
    """A runtime host path that is not what trusted code made: refused, never followed."""


_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _checked_dir(fd: int, path: Path) -> int:
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        os.close(fd)
        raise UnsafePath(f"{path} is not a private directory of this user")
    return fd


def open_private_dir(path: Path, *, create: bool = True) -> int:
    """A descriptor on ``path``: created (mode 0700) when missing, never through a link, owned by this user and
    private. The caller closes it."""

    path = Path(path)
    if create:
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            pass
    try:
        fd = os.open(path, _DIR_FLAGS)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise UnsafePath(f"{path} is a link or not a directory") from exc
        raise
    return _checked_dir(fd, path)


def private_dir(path: Path) -> None:
    """Make (or check) a private directory and each missing parent of it below an existing private one."""

    path = Path(path)
    missing = []
    probe = path
    while not os.path.lexists(probe) and probe != probe.parent:
        missing.append(probe)
        probe = probe.parent
    for each in reversed(missing):
        os.close(open_private_dir(each))
    os.close(open_private_dir(path, create=False))


def _remove(fd: int, name: str, where: Path) -> None:
    try:
        os.unlink(name, dir_fd=fd)
    except FileNotFoundError:
        pass
    except (IsADirectoryError, PermissionError) as exc:
        raise UnsafePath(f"{where / name} is a directory where a file belongs") from exc


def write_private(directory: Path, name: str, data: bytes, mode: int = 0o600) -> Path:
    """Write ``directory/name`` afresh: whatever stood there is removed (a link goes, never followed), then the
    file is created exclusively without following links, through the directory's descriptor."""

    fd = open_private_dir(directory)
    try:
        _remove(fd, name, Path(directory))
        file_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, mode, dir_fd=fd)
        try:
            info = os.fstat(file_fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise UnsafePath(f"{Path(directory) / name} is not a fresh file")
            view = memoryview(data)
            while view:
                view = view[os.write(file_fd, view):]
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)
    return Path(directory) / name


def remove_private(directory: Path, name: str) -> None:
    """Remove ``directory/name`` if it is there (a link is removed, never followed; a directory is refused)."""

    try:
        fd = open_private_dir(directory, create=False)
    except FileNotFoundError:
        return
    try:
        _remove(fd, name, Path(directory))
    finally:
        os.close(fd)


def remove_private_dir(directory: Path) -> None:
    """Remove an empty private directory (a link in its place is refused, not followed)."""

    directory = Path(directory)
    try:
        os.close(open_private_dir(directory, create=False))
    except FileNotFoundError:
        return
    try:
        os.rmdir(directory)
    except OSError:
        pass


def listening_socket(directory: Path, name: str, backlog: int = 64) -> socket.socket:
    """A Unix socket bound at ``directory/name`` and listening, created by trusted code (whatever stood there is
    removed first). The server receives it as a descriptor, so the sandbox never creates or names it."""

    fd = open_private_dir(directory)
    try:
        _remove(fd, name, Path(directory))
    finally:
        os.close(fd)
    path = Path(directory) / name
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(path))
        check_socket(path)
        server.listen(backlog)
    except BaseException:
        server.close()
        raise
    return server


def write_beneath(root: Path, parts: tuple[str, ...], name: str, data: bytes) -> Path:
    """Write ``root/<parts...>/name`` without following a link below ``root`` (the vault: shared, not private).

    Each directory below ``root`` is made if missing and opened without following links, so a link in any
    component is refused. The bytes go to a fresh, unpredictable temporary name created exclusively and never
    followed, which then replaces ``name`` through the directory's descriptor (a link at ``name`` is replaced, not
    written through; a directory there is refused)."""

    import secrets

    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in parts:
            try:
                os.mkdir(part, 0o755, dir_fd=fd)
            except FileExistsError:
                pass
            try:
                child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise UnsafePath(f"{part} under {root} is a link or not a directory") from exc
                raise
            os.close(fd)
            fd = child
        temporary = f".{name}.{secrets.token_hex(8)}.tmp"
        file_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644,
                          dir_fd=fd)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(file_fd, view):]
        finally:
            os.close(file_fd)
        try:
            os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
        except OSError as exc:
            os.unlink(temporary, dir_fd=fd)
            raise UnsafePath(f"{name} cannot be replaced ({exc.strerror})") from exc
    finally:
        os.close(fd)
    return Path(root).joinpath(*parts, name)


def check_socket(path: Path) -> None:
    """Before connecting: ``path`` itself (not a link's target) is a socket of this user, else refused."""

    try:
        info = os.lstat(path)
    except FileNotFoundError as exc:
        raise UnsafePath(f"{path} is missing") from exc
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
        raise UnsafePath(f"{path} is not this user's socket")


__all__ = ["UnsafePath", "check_socket", "listening_socket", "open_private_dir", "private_dir", "remove_private",
           "remove_private_dir", "write_beneath", "write_private"]
