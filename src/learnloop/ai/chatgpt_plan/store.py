"""Machine-local sign-in state for the ChatGPT-plan provider.

Everything lives under ``<LearnLoop config dir>/chatgpt_plan/``, the directory
that holds ``settings.env`` (``LEARNLOOP_CONFIG_DIR``, else
``$XDG_CONFIG_HOME/learnloop``, else ``~/.config/learnloop``). Nothing is ever
written into a vault or the repository:

- ``host.json``: this host's stable, opaque ``ext_agent_host_id``
  (``urn:uuid:…``). It identifies the machine, never the user, and is not a
  credential.
- ``account.json``: the registration (the issued ``oaiapp_…`` client id), the
  validated identity (``sub``, email), the granted scopes, the endpoints used
  and where the tokens are kept. No token is stored here, so status, readiness
  and doctor read this file without ever touching a secret.
- ``tokens.json``: the access, refresh and ID tokens, only when the OS keyring
  is unavailable (the optional ``keyring`` package with a usable backend; see
  :func:`secret_backend`).
- ``state.json``: the usage-limit pause, an eligibility refusal, the
  first-sign-in confirmation and a forced refresh after a 401.
- ``store.lock`` and ``refresh.lock``: advisory locks. A refresh holds
  ``refresh.lock`` across the token request, so two processes never race a
  rotating refresh token. Every credential commit (sign-in, refresh,
  sign-out) holds it too, so none can interleave with another.

**Generations.** Tokens and their grant live in two places (the secret store
and ``account.json``) that no single write can replace together. Each commit
therefore numbers itself: the token snapshot carries its ``generation`` and
the granted ``scopes`` and is written first; ``account.json`` then records the
same generation. A reader uses a token only when the two generations agree;
otherwise the snapshot is authoritative and the interrupted commit is rolled
forward under ``refresh.lock`` (see ``PlanSession.access_token``).

Files are written atomically (temporary file, fsync, rename, then an fsync of
the directory so the new name or a deletion survives a power loss) with mode
0600 in a 0700 directory. Tokens are never logged or returned by any status
call.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Protocol
import uuid

try:  # POSIX advisory locks; other platforms serialize within the process only.
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

import threading

from learnloop.config.loader import global_settings_path

STORE_DIRNAME = "chatgpt_plan"
#: ``file`` forces the 0600 file; ``keyring`` requires the OS keyring; unset
#: (the default) uses the keyring when one is usable, else the file. The test
#: suite sets ``file`` so no test can reach a real keyring.
SECRET_STORE_ENV = "LEARNLOOP_CHATGPT_SECRET_STORE"
KEYRING_SERVICE = "learnloop-chatgpt-plan"
LOCK_TIMEOUT_SECONDS = 60.0
_LOCK_POLL_SECONDS = 0.05
_THREAD_LOCKS: dict[str, threading.Lock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


class StoreError(RuntimeError):
    """The machine-local store cannot be read or written."""


class LockTimeout(StoreError):
    """A lock was not acquired within its timeout."""


class LockCancelled(StoreError):
    """The caller gave up waiting for a lock (an interrupt or its deadline)."""


def default_store_root() -> Path:
    return global_settings_path().parent / STORE_DIRNAME


@dataclass
class Account:
    """One registration and its validated identity. Holds no token."""

    client_id: str
    issuer: str
    token_endpoint: str
    revocation_endpoint: str | None = None
    subject: str | None = None
    email: str | None = None
    scopes: list[str] = field(default_factory=list)
    plan_usage_enabled: bool = False
    secret_store: str = "file"
    signed_in: bool = False
    signed_in_at: str | None = None
    #: How the ID token's signature was checked: ``rs256`` against the
    #: issuer's JWKS, or ``tls_endpoint`` (received directly from the token
    #: endpoint over TLS; OpenID Connect Core 3.1.3.7 step 6).
    id_token_signature: str | None = None
    signed_out_reason: str | None = None
    #: The credential commit this file belongs to (see the module docstring).
    generation: int = 0
    #: The current access token's expiry, for status (the token is never read for it).
    access_expires_at: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Account":
        known = {name for name in cls.__dataclass_fields__}
        return cls(**{key: value for key, value in data.items() if key in known})


@dataclass
class Tokens:
    access_token: str
    refresh_token: str | None
    id_token: str | None
    token_type: str
    expires_at: float
    saved_at: float
    earliest_refresh_at: float | None = None
    #: The scopes granted with these tokens: the authoritative grant for them.
    #: None only in a snapshot written before generations existed.
    scopes: list[str] | None = None
    #: The credential commit that wrote this snapshot.
    generation: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tokens":
        known = {name for name in cls.__dataclass_fields__}
        return cls(**{key: value for key, value in data.items() if key in known})


class SecretBackend(Protocol):
    name: str

    def load(self, client_id: str) -> dict[str, Any] | None: ...

    def save(self, client_id: str, payload: dict[str, Any]) -> None: ...

    def clear(self, client_id: str) -> None: ...


class FileSecrets:
    """Tokens in ``tokens.json`` (0600), keyed by client id."""

    name = "file"

    def __init__(self, root: Path) -> None:
        self.path = root / "tokens.json"

    def load(self, client_id: str) -> dict[str, Any] | None:
        data = _read_json(self.path)
        if not isinstance(data, dict) or data.get("client_id") != client_id:
            return None
        tokens = data.get("tokens")
        return tokens if isinstance(tokens, dict) else None

    def save(self, client_id: str, payload: dict[str, Any]) -> None:
        _write_json(self.path, {"client_id": client_id, "tokens": payload})

    def clear(self, client_id: str) -> None:
        data = _read_json(self.path)
        if isinstance(data, dict) and data.get("client_id") not in (None, client_id):
            return
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            return
        _fsync_directory(self.path.parent)


class KeyringSecrets:
    """Tokens in the OS keyring (service ``learnloop-chatgpt-plan``)."""

    name = "keyring"

    def __init__(self, module: Any) -> None:
        self._keyring = module

    def load(self, client_id: str) -> dict[str, Any] | None:
        try:
            raw = self._keyring.get_password(KEYRING_SERVICE, client_id)
        except Exception as exc:  # noqa: BLE001 - a locked or broken keyring
            raise StoreError(f"The OS keyring could not be read ({type(exc).__name__}).") from None
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    def save(self, client_id: str, payload: dict[str, Any]) -> None:
        try:
            self._keyring.set_password(KEYRING_SERVICE, client_id, json.dumps(payload))
        except Exception as exc:  # noqa: BLE001
            raise StoreError(f"The OS keyring could not be written ({type(exc).__name__}).") from None

    def clear(self, client_id: str) -> None:
        try:
            self._keyring.delete_password(KEYRING_SERVICE, client_id)
        except Exception:  # noqa: BLE001 - already absent, or a keyring that cannot delete
            pass


def usable_keyring() -> Any | None:
    """The ``keyring`` module when it has a real backend, else None."""

    if os.environ.get(SECRET_STORE_ENV, "").strip().lower() == "file":
        return None
    try:
        import keyring  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - optional dependency
        return None
    try:
        backend = keyring.get_keyring()
    except Exception:  # noqa: BLE001
        return None
    module = type(backend).__module__
    if module.startswith(("keyring.backends.fail", "keyring.backends.null")):
        return None
    try:
        priority = float(getattr(backend, "priority", 0))
    except (TypeError, ValueError):
        priority = 0.0
    return keyring if priority > 0 else None


class PlanStore:
    """The ChatGPT-plan store under one root (default: the LearnLoop config dir)."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else default_store_root()

    # -- paths ---------------------------------------------------------
    @property
    def account_path(self) -> Path:
        return self.root / "account.json"

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    @property
    def host_path(self) -> Path:
        return self.root / "host.json"

    def ensure_root(self) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self.root, 0o700)
        except OSError as exc:
            raise StoreError(f"Cannot create {self.root}: {exc.strerror or exc}") from None

    # -- host id -------------------------------------------------------
    def host_id(self) -> str:
        """This host's ``ext_agent_host_id``, created once and then reused."""

        data = _read_json(self.host_path)
        value = data.get("ext_agent_host_id") if isinstance(data, dict) else None
        if isinstance(value, str) and value.startswith("urn:uuid:"):
            return value
        with self.lock():
            data = _read_json(self.host_path)
            value = data.get("ext_agent_host_id") if isinstance(data, dict) else None
            if isinstance(value, str) and value.startswith("urn:uuid:"):
                return value
            value = f"urn:uuid:{uuid.uuid4()}"
            _write_json(self.host_path, {"ext_agent_host_id": value, "created_at": _utc_now()})
            return value

    # -- account -------------------------------------------------------
    def load_account(self) -> Account | None:
        data = _read_json(self.account_path)
        if not isinstance(data, dict) or not data.get("client_id"):
            return None
        try:
            return Account.from_dict(data)
        except TypeError:
            return None

    def save_account(self, account: Account) -> None:
        self.ensure_root()
        _write_json(self.account_path, asdict(account))

    # -- tokens --------------------------------------------------------
    def secrets_for(self, account: Account) -> SecretBackend:
        if account.secret_store == "keyring":
            module = usable_keyring()
            if module is None:
                raise StoreError(
                    "The ChatGPT sign-in is kept in the OS keyring, but no usable keyring is available "
                    "here (install the `keyring` extra, or sign in again to use the 0600 file)."
                )
            return KeyringSecrets(module)
        return FileSecrets(self.root)

    def preferred_secrets(self) -> SecretBackend:
        forced = os.environ.get(SECRET_STORE_ENV, "").strip().lower()
        module = usable_keyring()
        if forced == "keyring" and module is None:
            raise StoreError(f"{SECRET_STORE_ENV}=keyring, but no usable OS keyring is available.")
        return KeyringSecrets(module) if module is not None else FileSecrets(self.root)

    def load_tokens(self, account: Account) -> Tokens | None:
        payload = self.secrets_for(account).load(account.client_id)
        if payload is None:
            return None
        try:
            return Tokens.from_dict(payload)
        except TypeError:
            return None

    def save_tokens(self, account: Account, tokens: Tokens) -> None:
        self.ensure_root()
        self.secrets_for(account).save(account.client_id, asdict(tokens))

    def clear_tokens(self, account: Account) -> None:
        try:
            self.secrets_for(account).clear(account.client_id)
        except StoreError:
            pass
        # A file left by an earlier file-backed sign-in never outlives a sign-out.
        FileSecrets(self.root).clear(account.client_id)

    def save_sign_in(self, account: Account, tokens: Tokens) -> Account:
        """Persist a validated sign-in: tokens first, then the account that points at them.

        The caller holds ``refresh.lock`` and has numbered both with the same
        generation. The keyring is preferred; a keyring that refuses the write
        falls back to the 0600 file, and the account records which one holds
        the tokens.
        """

        self.ensure_root()
        backend = self.preferred_secrets()
        try:
            backend.save(account.client_id, asdict(tokens))
        except StoreError:
            if backend.name != "keyring" or os.environ.get(SECRET_STORE_ENV, "").strip().lower() == "keyring":
                raise
            backend = FileSecrets(self.root)
            backend.save(account.client_id, asdict(tokens))
        if backend.name == "keyring":
            FileSecrets(self.root).clear(account.client_id)
        account.secret_store = backend.name
        self.save_account(account)
        return account

    # -- state ---------------------------------------------------------
    def load_state(self) -> dict[str, Any]:
        data = _read_json(self.state_path)
        return data if isinstance(data, dict) else {}

    def update_state(self, **changes: Any) -> dict[str, Any]:
        """Merge ``changes`` into ``state.json`` (a None value removes the key)."""

        self.ensure_root()
        with self.lock():
            state = self.load_state()
            for key, value in changes.items():
                if value is None:
                    state.pop(key, None)
                else:
                    state[key] = value
            _write_json(self.state_path, state)
            return state

    def clear_state_if(self, key: str, expected: Any) -> bool:
        """Remove ``key`` only while it still holds ``expected`` (compare and clear, under the lock)."""

        self.ensure_root()
        with self.lock():
            state = self.load_state()
            if key not in state or state.get(key) != expected:
                return False
            del state[key]
            _write_json(self.state_path, state)
            return True

    # -- locks ---------------------------------------------------------
    @contextmanager
    def lock(self, name: str = "store.lock", timeout: float = LOCK_TIMEOUT_SECONDS,
             cancelled: Callable[[], bool] | None = None) -> Iterator[None]:
        """An exclusive lock across threads and processes.

        Raises :class:`LockTimeout` after ``timeout`` seconds, and
        :class:`LockCancelled` as soon as ``cancelled()`` turns true while
        waiting (polled every few milliseconds), so a caller's interrupt or
        deadline is never held hostage by another process's refresh.
        """

        self.ensure_root()
        path = self.root / name
        thread_lock = _thread_lock(str(path))
        deadline = time.monotonic() + max(0.0, timeout)

        def wait_or_give_up() -> float:
            if cancelled is not None and cancelled():
                raise LockCancelled(f"Stopped waiting for {path.name}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise LockTimeout(f"Timed out waiting for {path.name}")
            return min(_LOCK_POLL_SECONDS, remaining)

        # An uncontended lock is always taken, even with no time or a cancellation pending.
        acquired = thread_lock.acquire(blocking=False)
        while not acquired:
            acquired = thread_lock.acquire(timeout=wait_or_give_up())
        try:
            handle = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
            try:
                if fcntl is not None:
                    while True:
                        try:
                            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            break
                        except BlockingIOError:
                            time.sleep(wait_or_give_up())
                yield
            finally:
                if fcntl is not None:
                    try:
                        fcntl.flock(handle, fcntl.LOCK_UN)
                    except OSError:
                        pass
                os.close(handle)
        finally:
            thread_lock.release()


def _thread_lock(key: str) -> threading.Lock:
    with _THREAD_LOCKS_GUARD:
        lock = _THREAD_LOCKS.get(key)
        if lock is None:
            lock = _THREAD_LOCKS[key] = threading.Lock()
        return lock


def _read_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise StoreError(f"Cannot read {path.name}: {exc.strerror or exc}") from None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _write_json(path: Path, data: Any) -> None:
    """Atomic 0600 write: a reader sees the old file or the new one, never a mix."""

    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # mkstemp creates the file with mode 0600 before anything is written.
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    # The rename is atomic but lives in the directory: without this, a power
    # loss can bring back the old file (for tokens.json, an already-rotated
    # refresh token that forces a new sign-in).
    _fsync_directory(path.parent)


def _fsync_directory(directory: Path) -> None:
    """Make a rename or deletion in ``directory`` durable (POSIX; a no-op where unsupported)."""

    try:
        handle = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(handle)
    except OSError:
        pass  # some filesystems refuse fsync on a directory; the file itself is already synced
    finally:
        os.close(handle)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


__all__ = [
    "Account",
    "FileSecrets",
    "KEYRING_SERVICE",
    "KeyringSecrets",
    "LockCancelled",
    "LockTimeout",
    "PlanStore",
    "SECRET_STORE_ENV",
    "StoreError",
    "Tokens",
    "default_store_root",
    "usable_keyring",
]
