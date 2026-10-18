"""AD1's background jobs: never on a request path (spec §8.1 "off the critical path").

* :func:`schedule_presentation_forecasts`: after a plan serve's response is
  built, ``llm_v3:llm`` and ``llm_v3:decider`` for the presentation.
* :func:`schedule_item_preparation`: after a plan is built or read, the
  planned items' current revisions are prepared for the pool: the feature
  audit first (§7.2), then ``llm_v1:item`` (§8.2), each once per revision.

Both return at once and never raise. The work runs in the sidecar's
:class:`~learnloop.hints.map_builder.BackgroundBuilds` registry (bound to the
loaded vault: a vault switch, ``shutdown`` or EOF stops admitting jobs, and a
job checks its fence before each write step), on its own connection, one job
per key in flight per process. Without an injected client,
``LEARNLOOP_AD_MODELS=off`` (the test suite; a vault-copy run) starts nothing.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from learnloop.adaptive_difficulty import spend as ad_spend
from learnloop.adaptive_difficulty.outside import Clients, forecast_item, forecast_presentation
from learnloop.adaptive_difficulty.switches import (
    LLM_V1,
    LLM_V3_DECIDER,
    LLM_V3_LLM,
    feature_audit_enabled,
    outside_forecasters,
)

LOG = logging.getLogger(__name__)

#: At most this many item revisions are prepared by one plan read's job.
PREPARE_LIMIT = 20

_GUARD = threading.Lock()
_INFLIGHT: set[tuple[str, str]] = set()
_DEFAULT: Any = None


def _registry(builds: Any) -> Any:
    global _DEFAULT
    if builds is not None:
        return builds
    if _DEFAULT is None:
        from learnloop.hints.map_builder import BackgroundBuilds

        _DEFAULT = BackgroundBuilds()
    return _DEFAULT


def _injected(clients: Clients | None) -> bool:
    return clients is not None and (clients.llm is not None or clients.decider is not None)


def _launch(sqlite_path: Any, key: str, job: Callable[[Callable[[], bool]], None], *, builds: Any,
            name: str) -> threading.Thread | None:
    candidate = (str(Path(sqlite_path)), key)
    with _GUARD:
        if candidate in _INFLIGHT:
            return None
        _INFLIGHT.add(candidate)
    started = False
    try:
        def work(fence: Any) -> Callable[[], None]:
            def run() -> None:
                try:
                    if fence.live():
                        job(fence.live)
                except Exception:  # noqa: BLE001 - a background job never reaches the serve
                    LOG.warning("adaptive difficulty background job %s failed", key, exc_info=True)
                finally:
                    with _GUARD:
                        _INFLIGHT.discard(candidate)
            return run

        thread = _registry(builds).launch(sqlite_path, work, name=name)
        started = thread is not None
        return thread
    except Exception:  # noqa: BLE001 - scheduling never fails a serve
        LOG.warning("adaptive difficulty job %s not scheduled", key, exc_info=True)
        return None
    finally:
        if not started:
            with _GUARD:
                _INFLIGHT.discard(candidate)


def schedule_presentation_forecasts(vault: Any, sqlite_path: Any, presentation_id: str, *,
                                    clients: Clients | None = None, builds: Any = None,
                                    clock: Any = None) -> threading.Thread | None:
    try:
        chosen = {LLM_V3_LLM, LLM_V3_DECIDER} & set(outside_forecasters(vault.config))
        if not chosen or not presentation_id:
            return None
        if ad_spend.models_off() and not _injected(clients):
            return None

        def job(live: Callable[[], bool]) -> None:
            from learnloop.db.repositories import Repository

            repository = Repository.attach(Path(sqlite_path))
            forecast_presentation(vault, repository, presentation_id, clients=clients, clock=clock, live=live)

        return _launch(sqlite_path, f"presentation:{presentation_id}", job, builds=builds,
                       name=f"learnloop-ad-forecast-{presentation_id}")
    except Exception:  # noqa: BLE001
        LOG.warning("AD presentation forecasts not scheduled", exc_info=True)
        return None


def prepare_items(vault: Any, repository: Any, item_ids: Iterable[str], *, clients: Clients | None = None,
                  decider_factory: Callable[[], Any] | None = None, clock: Any = None,
                  live: Callable[[], bool] | None = None, limit: int = PREPARE_LIMIT) -> list[dict[str, Any]]:
    """Audit, then forecast (``llm_v1:item``), each item's current revision; once each."""

    from learnloop.adaptive_difficulty.feature_audit import audit_revision, item_revision
    from learnloop.adaptive_difficulty.protection import protected_items

    results: list[dict[str, Any]] = []
    protected = protected_items(vault, repository)
    for item_id in list(dict.fromkeys(str(value) for value in item_ids))[:limit]:
        if live is not None and not live():
            break
        item = vault.practice_items.get(item_id)
        if item is None or getattr(item, "status", "active") != "active":
            continue
        entry: dict[str, Any] = {"practice_item_id": item_id}
        if feature_audit_enabled(vault.config):
            entry["audit"] = audit_revision(
                vault, repository, item, clock=clock, protected=protected,
                decider_factory=decider_factory or ((lambda: clients.decider) if clients and clients.decider else None),
                llm_client=clients.llm if clients else None,
            ).as_dict()
        if live is not None and not live():
            break
        if LLM_V1 in outside_forecasters(vault.config):
            entry["llm_v1"] = forecast_item(vault, repository, item, clients=clients, clock=clock,
                                            protected=protected).as_dict()
        results.append(entry)
        if _settled(entry):
            with _GUARD:
                _PREPARED.add((str(Path(repository.sqlite_path)), item_id, item_revision(item)[0]))
    return results


#: Item revisions this process has prepared to the end (audited or current,
#: forecast or current, or protected): a plan read never schedules them again.
_PREPARED: set[tuple[str, str, str]] = set()
_SETTLED = {"current", "protected", "disabled", "ok"}


def _settled(entry: dict[str, Any]) -> bool:
    audit = entry.get("audit", {"status": "disabled"})
    forecast = entry.get("llm_v1", {"status": "disabled"})
    audited = audit.get("status") in _SETTLED or (audit.get("status") == "audited" and not audit.get("unanswered"))
    return audited and forecast.get("status") in _SETTLED


def schedule_item_preparation(vault: Any, sqlite_path: Any, item_ids: Iterable[str], *,
                              clients: Clients | None = None, builds: Any = None,
                              clock: Any = None) -> threading.Thread | None:
    try:
        from learnloop.adaptive_difficulty.feature_audit import item_revision

        path = str(Path(sqlite_path))
        ids = []
        for value in item_ids:
            item = vault.practice_items.get(str(value))
            if item is None:
                continue
            with _GUARD:
                prepared = (path, str(value), item_revision(item)[0]) in _PREPARED
            if not prepared:
                ids.append(str(value))
        wants = feature_audit_enabled(vault.config) or LLM_V1 in outside_forecasters(vault.config)
        if not ids or not wants:
            return None
        if ad_spend.models_off() and not _injected(clients):
            return None

        def job(live: Callable[[], bool]) -> None:
            from learnloop.db.repositories import Repository

            repository = Repository.attach(Path(sqlite_path))
            prepare_items(vault, repository, ids, clients=clients, clock=clock, live=live)

        return _launch(sqlite_path, "prepare:" + ",".join(sorted(ids)[:PREPARE_LIMIT]), job, builds=builds,
                       name="learnloop-ad-prepare")
    except Exception:  # noqa: BLE001
        LOG.warning("AD item preparation not scheduled", exc_info=True)
        return None


__all__ = ["PREPARE_LIMIT", "prepare_items", "schedule_item_preparation", "schedule_presentation_forecasts"]
