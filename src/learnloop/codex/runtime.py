from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from learnloop.config import CodexConfig

CodexRuntimeState = Literal[
    "codex_missing",
    "codex_revision_mismatch",
    "codex_unavailable",
    "codex_auth_required",
    "ready",
]

PINNED_REVISION_PLACEHOLDER = "<pinned-commit>"


class CodexHealthChecker(Protocol):
    def __call__(self, checkout_path: Path, config: CodexConfig) -> None:
        ...


class CodexStartupProcess(Protocol):
    def poll(self) -> int | None:
        ...


class CodexStartupRunner(Protocol):
    def __call__(self, checkout_path: Path, config: CodexConfig) -> CodexStartupProcess:
        ...


class CodexAuthRequired(RuntimeError):
    pass


class CodexHealthUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexRuntimeReport:
    status: CodexRuntimeState
    checkout_path: str
    configured_revision: str
    actual_revision: str | None = None
    message: str | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def as_dict(self) -> dict[str, str | bool | None]:
        return {
            "status": self.status,
            "ready": self.ready,
            "checkout_path": self.checkout_path,
            "configured_revision": self.configured_revision,
            "actual_revision": self.actual_revision,
            "message": self.message,
        }


def check_codex_runtime(
    vault_root: Path,
    config: CodexConfig,
    *,
    healthcheck: CodexHealthChecker | None = None,
    startup: CodexStartupRunner | None = None,
) -> CodexRuntimeReport:
    checkout_path = _resolve_checkout_path(vault_root, config.checkout_path)
    configured_revision = config.revision
    if not checkout_path.exists():
        return CodexRuntimeReport(
            status="codex_missing",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            message="Codex checkout path does not exist.",
        )
    if not checkout_path.is_dir():
        return CodexRuntimeReport(
            status="codex_missing",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            message="Codex checkout path is not a directory.",
        )

    actual_revision = _read_checkout_revision(checkout_path)
    if _requires_revision_match(configured_revision):
        if actual_revision is None:
            return CodexRuntimeReport(
                status="codex_unavailable",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=None,
                message="Could not determine Codex checkout revision.",
            )
        if not actual_revision.startswith(configured_revision):
            return CodexRuntimeReport(
                status="codex_revision_mismatch",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message="Codex checkout revision does not match configuration.",
            )

    healthcheck = healthcheck or (default_sdk_healthcheck if config.provider.lower() == "sdk" else default_http_healthcheck)
    startup = startup or default_startup

    try:
        healthcheck(checkout_path, config)
    except CodexAuthRequired as exc:
        return CodexRuntimeReport(
            status="codex_auth_required",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            actual_revision=actual_revision,
            message=str(exc) or "Codex authentication is required.",
        )
    except (CodexHealthUnavailable, TimeoutError, OSError, subprocess.SubprocessError) as exc:
        if config.provider.lower() == "sdk" or not config.startup_command:
            return CodexRuntimeReport(
                status="codex_unavailable",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message=str(exc) or "Codex healthcheck failed.",
            )
        try:
            process = startup(checkout_path, config)
            _wait_for_startup_health(checkout_path, config, healthcheck, process)
        except CodexAuthRequired as startup_exc:
            return CodexRuntimeReport(
                status="codex_auth_required",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message=str(startup_exc) or "Codex authentication is required.",
            )
        except (CodexHealthUnavailable, TimeoutError, OSError, subprocess.SubprocessError) as startup_exc:
            return CodexRuntimeReport(
                status="codex_unavailable",
                checkout_path=str(checkout_path),
                configured_revision=configured_revision,
                actual_revision=actual_revision,
                message=str(startup_exc) or str(exc) or "Codex startup or healthcheck failed.",
            )
    return CodexRuntimeReport(
        status="ready",
        checkout_path=str(checkout_path),
        configured_revision=configured_revision,
        actual_revision=actual_revision,
        message="Codex runtime is ready.",
    )


def default_startup(checkout_path: Path, config: CodexConfig) -> subprocess.Popen:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        config.startup_command,
        cwd=checkout_path,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def _wait_for_startup_health(
    checkout_path: Path,
    config: CodexConfig,
    healthcheck: CodexHealthChecker,
    process: CodexStartupProcess,
) -> None:
    deadline = time.monotonic() + max(0, config.startup_timeout_seconds)
    last_error: Exception | None = None
    while True:
        try:
            healthcheck(checkout_path, config)
            return
        except CodexAuthRequired:
            raise
        except (CodexHealthUnavailable, TimeoutError, OSError, subprocess.SubprocessError) as exc:
            last_error = exc

        return_code = process.poll()
        if return_code is not None:
            raise CodexHealthUnavailable(f"Codex startup command exited with status {return_code}.")
        if time.monotonic() >= deadline:
            suffix = f": {last_error}" if last_error else "."
            raise CodexHealthUnavailable(f"Codex startup or healthcheck timed out{suffix}")
        time.sleep(min(0.2, max(0.0, deadline - time.monotonic())))


def default_http_healthcheck(_checkout_path: Path, config: CodexConfig) -> None:
    request = urllib.request.Request(
        _url(config.base_url, config.healthcheck_path),
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.healthcheck_timeout_seconds) as response:
            payload = response.read(65536)
            status_code = response.status
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise CodexAuthRequired("Codex app-server authentication is required.") from exc
        raise CodexHealthUnavailable(f"Codex healthcheck HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise CodexHealthUnavailable(str(exc.reason)) from exc

    if status_code >= 400:
        raise CodexHealthUnavailable(f"Codex healthcheck HTTP {status_code}.")
    if not payload:
        return
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexHealthUnavailable("Codex healthcheck returned invalid JSON.") from exc
    state = str(data.get("status") or data.get("state") or "ready").lower()
    if state in {"ready", "ok", "healthy"}:
        return
    if state in {"auth_required", "unauthorized", "login_required"}:
        raise CodexAuthRequired(data.get("message") or "Codex authentication is required.")
    raise CodexHealthUnavailable(data.get("message") or f"Codex runtime is not ready: {state}")


def default_sdk_healthcheck(checkout_path: Path, config: CodexConfig) -> None:
    sdk_path = _resolve_sdk_python_path(checkout_path, config.sdk_python_path)
    if sdk_path.exists():
        value = str(sdk_path)
        if value not in sys.path:
            sys.path.insert(0, value)
    try:
        import openai_codex  # noqa: F401
    except ImportError as exc:
        raise CodexHealthUnavailable(f"Codex Python SDK is not importable from {sdk_path}.") from exc


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _resolve_checkout_path(vault_root: Path, checkout_path: str) -> Path:
    raw = Path(checkout_path)
    if raw.is_absolute():
        return raw.resolve()
    return (vault_root / raw).resolve()


def _requires_revision_match(revision: str) -> bool:
    return bool(revision and revision != PINNED_REVISION_PLACEHOLDER)


def _read_checkout_revision(checkout_path: Path) -> str | None:
    git_dir = checkout_path / ".git"
    if not git_dir.exists():
        head = checkout_path / "HEAD"
        if head.exists():
            return head.read_text(encoding="utf-8").strip() or None
        return None
    result = subprocess.run(
        ["git", "-C", str(checkout_path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _resolve_sdk_python_path(checkout_path: Path, sdk_python_path: str) -> Path:
    raw = Path(sdk_python_path)
    if raw.is_absolute():
        return raw.resolve()
    return (checkout_path / raw).resolve()
