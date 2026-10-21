"""The projected vault and repository an AD operation hands its readers (the AD23 redesign, step 4).

Step 1 of the redesign: the identity (the operation's vault and repository are the raw ones)."""

from __future__ import annotations

from typing import Any


def project_vault(view: Any) -> Any:
    return view.vault


def project_repository(repository: Any, view: Any) -> Any:
    return repository


__all__ = ["project_repository", "project_vault"]
