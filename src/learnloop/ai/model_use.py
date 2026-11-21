"""The learner's one OK before LearnLoop uses AI at all, and the check that holds every request to it.

One record covers every model use (questions, the tutor's replies, feedback, quick checks, reading paths,
goals, the Decider, embeddings, text recognition, transcription): the learner says OK once. It is the
``[ai.consent.model_use]`` table of the library's ``learnloop.toml`` (``granted_at``, ``data_flow =
"all_model_use"``, ``disclosure_version``), mirrored into the machine's ``ai_defaults.toml`` the way the
connection's settings already are, so a library opened or made later on this computer is covered too.

An OK given before this record existed is honoured: any ``[ai.consent.<provider>]`` table whose data flow
is ``passages_and_answers`` was written by the learner's OK on the connection sheet. Nothing else counts:
the separate OKs for sending whole files (``whole_files``, ``whole_files_zai``), a ChatGPT sign-in, a
connected provider or a "Use OpenRouter instead" choice for one action never write such a table.

The lookup is live (the files as they are now, read again only when they change) and bound to each client
the factory builds (:func:`bind`), so a request started in a background thread or a resumed job is checked
against the OK as it stands when it is sent, without depending on any context being carried there.
:func:`admit` is called by :func:`learnloop.ai.execution.model_call` before every physical request.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import threading
import tomllib
from typing import Any, Mapping

#: The consent table's key for the one OK, its data flow, and the version of the words it was given under.
MODEL_USE_KEY = "model_use"
MODEL_USE_FLOW = "all_model_use"
DISCLOSURE_VERSION = 1
#: The data flow the connection sheet's earlier OK recorded (``add_source.DATA_FLOW``).
EARLIER_OK_FLOW = "passages_and_answers"
#: The separate OKs for uploading whole files: never an OK to use AI.
UPLOAD_ONLY_KEYS = frozenset({"whole_files", "whole_files_zai"})

WAITING_CODE = "waiting_for_ok"
WAITING_MESSAGE = "LearnLoop is waiting for your OK before it uses AI."
#: The attribute :func:`bind` sets on a client.
LOOKUP_ATTRIBUTE = "model_use_acceptance"


class ModelUseNotAccepted(Exception):
    """No OK yet: nothing was sent. A waiting state, never a provider failure, so it is not an
    ``AIProviderUnavailable`` (which retries, fallbacks and failure lines act on)."""

    code = WAITING_CODE

    def __init__(self, message: str = WAITING_MESSAGE) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Acceptance:
    key: str
    granted_at: str
    data_flow: str
    disclosure_version: int | None
    #: ``library`` (the vault's learnloop.toml) or ``machine`` (ai_defaults.toml).
    where: str


def acceptance_in(consent: Mapping[str, Any] | None, *, where: str = "library") -> Acceptance | None:
    """The OK a ``[ai.consent]`` table holds: the one-OK record first, else an earlier OK of the
    connection sheet; None when it holds neither (an upload's OK alone, or nothing)."""

    if not isinstance(consent, Mapping):
        return None
    keys = [MODEL_USE_KEY, *sorted(key for key in consent if key != MODEL_USE_KEY)]
    for key in keys:
        record = consent.get(key)
        if key in UPLOAD_ONLY_KEYS or not isinstance(record, Mapping):
            continue
        granted_at = record.get("granted_at")
        flow = str(record.get("data_flow") or EARLIER_OK_FLOW)
        wanted = MODEL_USE_FLOW if key == MODEL_USE_KEY else EARLIER_OK_FLOW
        if not granted_at or flow != wanted:
            continue
        version = record.get("disclosure_version")
        return Acceptance(key=key, granted_at=str(granted_at), data_flow=flow,
                          disclosure_version=version if isinstance(version, int) else None, where=where)
    return None


def record_updates(granted_at: str) -> dict[tuple[str, ...], Any]:
    """The config updates that write the one OK (``settings_store.apply_config_updates``)."""

    return {
        ("ai", "consent", MODEL_USE_KEY, "granted_at"): granted_at,
        ("ai", "consent", MODEL_USE_KEY, "data_flow"): MODEL_USE_FLOW,
        ("ai", "consent", MODEL_USE_KEY, "disclosure_version"): DISCLOSURE_VERSION,
    }


# -- the live lookup -------------------------------------------------------------------------------

_cache_lock = threading.Lock()
_cache: dict[Path, tuple[tuple[int, int, int], Acceptance | None]] = {}


def _consent_in_file(path: Path, where: str) -> Acceptance | None:
    """The OK in one TOML file, read again only when the file changed (an unreadable or missing
    file holds none)."""

    try:
        status = os.stat(path)
    except OSError:
        return None
    stamp = (status.st_mtime_ns, status.st_size, status.st_ino)
    with _cache_lock:
        cached = _cache.get(path)
    if cached is not None and cached[0] == stamp:
        return cached[1]
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    found = acceptance_in((raw.get("ai") or {}).get("consent") if isinstance(raw.get("ai"), Mapping) else None,
                          where=where)
    with _cache_lock:
        _cache[path] = (stamp, found)
    return found


def machine_acceptance() -> Acceptance | None:
    """The OK mirrored into this computer's ``ai_defaults.toml`` (any library's, said once here)."""

    from learnloop.config.loader import global_ai_defaults_path

    return _consent_in_file(global_ai_defaults_path(), "machine")


def recorded_acceptance(vault_root: Path | str | None) -> Acceptance | None:
    """The OK that covers model use for the library at ``vault_root`` now: its own, else this
    computer's. None: LearnLoop waits for the learner's OK."""

    if vault_root is not None:
        found = _consent_in_file(Path(vault_root) / "learnloop.toml", "library")
        if found is not None:
            return found
    return machine_acceptance()


def accepted(vault_root: Path | str | None) -> bool:
    return recorded_acceptance(vault_root) is not None


class AcceptanceLookup:
    """The live lookup a client carries (:func:`bind`): the OK for its library, read when asked."""

    def __init__(self, vault_root: Path | str | None) -> None:
        self.vault_root = None if vault_root is None else Path(vault_root)

    def __call__(self) -> bool:
        return accepted(self.vault_root)


def bind(client: Any, vault_root: Path | str | None) -> Any:
    """Hold every request ``client`` makes to the OK for the library at ``vault_root``."""

    setattr(client, LOOKUP_ATTRIBUTE, AcceptanceLookup(vault_root))
    return client


def client_waiting(client: Any) -> bool:
    """Whether ``client`` is bound to a library that has no OK yet. A client built outside the
    factory (a test's double) carries no lookup and is never held here."""

    lookup = getattr(client, LOOKUP_ATTRIBUTE, None)
    return isinstance(lookup, AcceptanceLookup) and not lookup()


def admit(client: Any) -> None:
    """Refuse a request before anything is sent when ``client``'s library has no OK."""

    if client_waiting(client):
        raise ModelUseNotAccepted()


def waiting(vault_root: Path | str | None, client: Any | None = None) -> bool:
    """For a caller about to start model work: an injected client answers for itself (bound or
    not); otherwise the library's OK decides."""

    if client is not None:
        return client_waiting(client)
    return not accepted(vault_root)


def require(vault_root: Path | str | None, client: Any | None = None) -> None:
    if waiting(vault_root, client):
        raise ModelUseNotAccepted()


__all__ = [
    "Acceptance",
    "AcceptanceLookup",
    "DISCLOSURE_VERSION",
    "EARLIER_OK_FLOW",
    "LOOKUP_ATTRIBUTE",
    "MODEL_USE_FLOW",
    "MODEL_USE_KEY",
    "ModelUseNotAccepted",
    "UPLOAD_ONLY_KEYS",
    "WAITING_CODE",
    "WAITING_MESSAGE",
    "acceptance_in",
    "accepted",
    "admit",
    "bind",
    "client_waiting",
    "machine_acceptance",
    "record_updates",
    "recorded_acceptance",
    "require",
    "waiting",
]
