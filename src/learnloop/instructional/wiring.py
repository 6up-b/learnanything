"""What the adapters inject into ``find_practice`` and the tutor (SC12).

``practice_index``, ``source_retrieval`` and the domain packages never import
the service; the sidecar and the CLI call these helpers and pass the callables
in. Each phase's kill switch decides whether its callable is injected at all.
"""
from __future__ import annotations

from typing import Any

from learnloop.vault.models import LoadedVault


def find_practice_injections(vault: LoadedVault) -> dict[str, Any]:
    """Keyword arguments for ``find_practice`` under the service's switches."""

    config = vault.config.source_service
    injected: dict[str, Any] = {}
    if not config.enabled:
        return injected
    return injected


__all__ = ["find_practice_injections"]
