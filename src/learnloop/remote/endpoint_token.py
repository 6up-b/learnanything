"""The MCP endpoint's persistent secret path (spec_mcp_frontend_c1 §3.2).

C1 has no OAuth (deferred; recorded as a risk): the URL is the credential.
The server answers only at ``/<token>/mcp``; every other path is a 404.

The token lives in the vault's machine-local state,
``<vault>/.learnloop/mcp/endpoint-token`` (directory 0700, file 0600, with a
``.gitignore`` of ``*`` beside it so a vault kept in git never commits it).
It is printed only by ``learnloop mcp token show`` and never logged.
``rotate`` replaces it; a running server reads the file again when it
changes, so the old URL stops working without a restart.
"""

from __future__ import annotations

import hmac
import os
import re
import secrets
import threading
from pathlib import Path

TOKEN_DIRECTORY = (".learnloop", "mcp")
TOKEN_FILE = "endpoint-token"
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{32,128}")


class TokenError(RuntimeError):
    """The token file is unreadable or malformed (fail closed: nothing is served)."""


def token_directory(vault_root: Path) -> Path:
    return Path(vault_root).joinpath(*TOKEN_DIRECTORY)


def token_path(vault_root: Path) -> Path:
    return token_directory(vault_root) / TOKEN_FILE


def _prepare_directory(vault_root: Path) -> Path:
    directory = token_directory(vault_root)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    ignore = directory / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    return directory


def _write(vault_root: Path, token: str) -> None:
    directory = _prepare_directory(vault_root)
    temporary = directory / f".{TOKEN_FILE}.{secrets.token_hex(4)}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(token + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / TOKEN_FILE)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def read_token(vault_root: Path) -> str | None:
    """The current token, None when none was made yet; :class:`TokenError` if malformed."""

    path = token_path(vault_root)
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise TokenError(f"the endpoint token could not be read: {exc.strerror}") from None
    if not _TOKEN_RE.fullmatch(value):
        raise TokenError("the endpoint token file is malformed; run `learnloop mcp token rotate`")
    return value


def ensure_token(vault_root: Path) -> str:
    """The token, made on first use."""

    existing = read_token(vault_root)
    if existing is not None:
        return existing
    token = secrets.token_urlsafe(32)
    _write(vault_root, token)
    return token


def rotate_token(vault_root: Path) -> str:
    """A new token; the old URL stops working (a running server rereads the file)."""

    token = secrets.token_urlsafe(32)
    _write(vault_root, token)
    return token


def endpoint_path(token: str) -> str:
    return f"/{token}/mcp"


class TokenStore:
    """The current token for a running server, reread when the file changes."""

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = Path(vault_root)
        self._lock = threading.Lock()
        self._stamp: tuple[int, int] | None = None
        self._token: str | None = None
        ensure_token(self.vault_root)

    def current(self) -> str | None:
        path = token_path(self.vault_root)
        try:
            stat = path.stat()
        except OSError:
            return None
        stamp = (stat.st_mtime_ns, stat.st_ino)
        with self._lock:
            if stamp != self._stamp:
                try:
                    self._token = read_token(self.vault_root)
                except TokenError:
                    self._token = None
                self._stamp = stamp
            return self._token

    def matches_path(self, path: str) -> bool:
        """Whether ``path`` is exactly ``/<token>/mcp`` (constant-time compare)."""

        token = self.current()
        if not token:
            return False
        return hmac.compare_digest(path.encode("utf-8", "surrogateescape"), endpoint_path(token).encode("utf-8"))


__all__ = [
    "TOKEN_FILE",
    "TokenError",
    "TokenStore",
    "endpoint_path",
    "ensure_token",
    "read_token",
    "rotate_token",
    "token_path",
]
