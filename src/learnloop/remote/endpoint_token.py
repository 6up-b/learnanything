"""The MCP endpoint's persistent secret path (spec_mcp_frontend_c1 §3.2).

C1 has no OAuth (deferred; recorded as a risk): the URL is the credential.
The server answers only at ``/<token>/mcp``; every other path is a 404.

The token lives in the vault's machine-local state,
``<vault>/.learnloop/mcp/endpoint-token`` (directory 0700, file 0600, with a
``.gitignore`` of ``*`` beside it so a vault kept in git never commits it).
It is printed only by ``learnloop mcp token show`` and never logged.
``rotate`` replaces it; a running server reads the file again when it
changes, so the old URL stops working without a restart.

The same directory keeps the alias key (``alias-key``): the secret the chat
frontend's opaque aliases are keyed with (see below).
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


# -- the alias key ------------------------------------------------------------------
#
# Chat shows a generated topic's id and a recurrence group's key as opaque
# aliases (``learner_context.lo_alias`` / ``group_alias``): HMAC-SHA256 under a
# per-vault secret kept beside the token, so a client cannot recompute one from
# a guessed title or statement (Q13). Made by ``learnloop mcp serve`` (never by
# a read), never printed; rotating the token leaves it alone (aliases stay
# stable for the hosts that hold them).

ALIAS_KEY_FILE = "alias-key"
_ALIAS_KEY_RE = re.compile(r"[0-9a-f]{64}")


def alias_key_path(vault_root: Path) -> Path:
    return token_directory(vault_root) / ALIAS_KEY_FILE


def read_alias_key(vault_root: Path) -> bytes | None:
    """The vault's alias key, None when none was made (or it cannot be read:
    the caller then keys aliases for its own process)."""

    try:
        value = alias_key_path(vault_root).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return bytes.fromhex(value) if _ALIAS_KEY_RE.fullmatch(value) else None


def ensure_alias_key(vault_root: Path) -> bytes:
    """The vault's alias key, made on first use (0600, beside the token)."""

    existing = read_alias_key(vault_root)
    if existing is not None:
        return existing
    key = secrets.token_bytes(32)
    directory = _prepare_directory(vault_root)
    temporary = directory / f".{ALIAS_KEY_FILE}.{secrets.token_hex(4)}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(key.hex() + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, alias_key_path(vault_root))
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return key


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
    "ALIAS_KEY_FILE",
    "TOKEN_FILE",
    "TokenError",
    "TokenStore",
    "alias_key_path",
    "endpoint_path",
    "ensure_alias_key",
    "ensure_token",
    "read_alias_key",
    "read_token",
    "rotate_token",
    "token_path",
]
