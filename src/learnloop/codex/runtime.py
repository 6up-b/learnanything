from __future__ import annotations

import subprocess
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

    if healthcheck is None:
        return CodexRuntimeReport(
            status="codex_unavailable",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            actual_revision=actual_revision,
            message="No Codex healthcheck transport is configured yet.",
        )

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
        return CodexRuntimeReport(
            status="codex_unavailable",
            checkout_path=str(checkout_path),
            configured_revision=configured_revision,
            actual_revision=actual_revision,
            message=str(exc) or "Codex healthcheck failed.",
        )
    return CodexRuntimeReport(
        status="ready",
        checkout_path=str(checkout_path),
        configured_revision=configured_revision,
        actual_revision=actual_revision,
        message="Codex runtime is ready.",
    )


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
