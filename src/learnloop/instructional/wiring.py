"""What the adapters inject into ``find_practice`` and the tutor (SC12).

``practice_index``, ``source_retrieval`` and the domain packages never import
the service; the sidecar and the CLI call these helpers and pass the callables
in. Each phase's kill switch decides whether its callable is injected at all.
"""
from __future__ import annotations

from typing import Any

from learnloop.vault.models import LoadedVault


def find_practice_injections(vault: LoadedVault, *, estimator: Any | None = None) -> dict[str, Any]:
    """Keyword arguments for ``find_practice`` under the service's switches.

    ``estimator`` is the daily plan's minutes estimator, built by the adapter
    (the service never imports the plan)."""

    from learnloop.instructional.discriminating import make_valuer
    from learnloop.instructional.exercises import exercise_candidates

    config = vault.config.source_service
    injected: dict[str, Any] = {}
    if not config.enabled:
        return injected
    if config.exercise_arm:
        injected["exercise_arm"] = exercise_candidates
    if estimator is not None:
        injected["estimator"] = estimator
    if config.discriminating_search:
        from learnloop.diagnosis.probe_robust import resolve_episode_channel

        injected["valuer"] = make_valuer(estimator=estimator, channel_resolver=resolve_episode_channel)
    return injected


__all__ = ["find_practice_injections"]
