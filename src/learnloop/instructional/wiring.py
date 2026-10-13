"""What the adapters inject into ``find_practice`` and the tutor (SC12).

``practice_index``, ``source_retrieval`` and the domain packages never import
the service; the sidecar and the CLI call these helpers and pass the callables
in. Each phase's kill switch decides whether its callable is injected at all.
"""
from __future__ import annotations

from typing import Any

from learnloop.vault.models import LoadedVault


def find_practice_injections(vault: LoadedVault, *, estimator: Any | None = None,
                             screen_client: Any | None = None,
                             judge_client: Any | None = None) -> dict[str, Any]:
    """Keyword arguments for ``find_practice`` under the service's switches.

    Every caller goes through here (the RPCs, the tutor, S2b's need step, the
    owner-run harvest), so a phase's kill switch removes its callable for all
    of them (Codex review F15). ``estimator`` is the daily plan's minutes
    estimator, built by the adapter (the service never imports the plan);
    ``screen_client`` and ``judge_client`` are injected test or route clients
    for the discrimination screen and the equivalence judge."""

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

        injected["valuer"] = make_valuer(estimator=estimator, channel_resolver=resolve_episode_channel,
                                         screen_client=screen_client, judge_client=judge_client)
    return injected


def disabled_reason(vault: LoadedVault, *needed: str) -> str | None:
    """Which switch keeps a caller's phases off (None: all on)."""

    config = vault.config.source_service
    if not config.enabled:
        return "source_service.enabled is false"
    for name in needed:
        if not getattr(config, name):
            return f"source_service.{name} is false"
    return None


__all__ = ["disabled_reason", "find_practice_injections"]
