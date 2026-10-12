"""Small capture-host maintenance operations; never sidecar startup work."""

from __future__ import annotations

import tomllib
from datetime import datetime, timedelta
from pathlib import Path

from learnloop.db.repositories import Repository

from .devices import _now
from .errors import CaptureError

# Only route templates, never arbitrary URLs, queries, tokens or request bodies.
_LOG_ENDPOINTS = frozenset({"/pair", "/api/v1/capture", "/rpc"})


def log_request(
    repo: Repository, *, endpoint: str, status: int, duration_ms: float,
    device_id: str | None = None, now: datetime | None = None,
) -> None:
    if endpoint not in _LOG_ENDPOINTS:
        return  # Polls are deliberately not logged.
    if not 100 <= status <= 599 or duration_ms < 0:
        raise CaptureError("validation_error", 422, "Invalid request log metadata")
    with repo.atomic(), repo.connection() as conn:
        conn.execute(
            "INSERT INTO mobile_request_log(device_id,endpoint,status,duration_ms,at) VALUES (?,?,?,?,?)",
            (device_id, endpoint, status, duration_ms, _now(now).isoformat()),
        )
        conn.execute("DELETE FROM mobile_request_log WHERE at<?",
                     ((_now(now) - timedelta(days=90)).isoformat(),))


def prune_request_log(repo: Repository, *, now: datetime | None = None) -> int:
    with repo.atomic(), repo.connection() as conn:
        return conn.execute("DELETE FROM mobile_request_log WHERE at<?",
                            ((_now(now) - timedelta(days=90)).isoformat(),)).rowcount


def pinned_vault_info(config_path: Path, current_root: Path) -> dict:
    """Read machine routing information without importing a host entry point."""
    try:
        with Path(config_path).open("rb") as handle:
            config = tomllib.load(handle)
    except FileNotFoundError:
        return dict(pinned_vault=None, vault_mismatch=False, enabled=False)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CaptureError("validation_error", 422, "Cannot read mobile host configuration") from exc
    vault = config.get("vault")
    if vault is not None and (not isinstance(vault, str) or not Path(vault).is_absolute()):
        raise CaptureError("validation_error", 422, "Mobile host vault must be an absolute path")
    return dict(
        pinned_vault=vault, enabled=config.get("enabled") is True,
        vault_mismatch=bool(vault and Path(vault).resolve() != Path(current_root).resolve()),
    )
