"""AD1's background jobs: never on a request path (spec §8.1 "off the critical path").

* :func:`schedule_presentation_forecasts`: after a plan serve's response is
  built, ``llm_v3:llm`` and ``llm_v3:decider`` for the presentation.
* :func:`schedule_item_preparation`: after an item revision is published,
  imported or edited (the sidecar's reload and file-watcher refresh, Codex
  review F10) and, as the recovery path, after a plan is built or read (the
  planned items), the revisions are prepared for the pool: the feature audit
  first (§7.2), then ``llm_v1:item`` (§8.2), each once per revision.

Both return at once and never raise. The work runs in the sidecar's
:class:`~learnloop.hints.map_builder.BackgroundBuilds` registry (bound to the
loaded vault: a vault switch, ``shutdown`` or EOF stops admitting jobs), on
its own connection: one presentation's job in flight per process, and one
preparation queue per vault with one worker at a time, each run preparing at
most :data:`PREPARE_LIMIT` revisions (fix round 4, V2; a queued entry names
its revision, so an edit mid-run queues the new one: Codex re-review F12).
Every request and record is checked against the held-out predicate of the
vault loaded *now* (``live_vault``, fix round 4, V1). Inside a job each
unit of paid work holds a durable claim (``judgment_work_claims``, across
processes) and writes fenced by the job's own registry fence: nothing more is
asked, and no judgment, payload or receipt lands, once its vault is switched
or closed (:mod:`learnloop.adaptive_difficulty.claims`; Codex review F5, F6).
Without an injected client, ``LEARNLOOP_AD_MODELS=off`` (the test suite; a
vault-copy run) starts nothing.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.adaptive_difficulty import spend as ad_spend
from learnloop.adaptive_difficulty.outside import Clients, forecast_item, forecast_presentation
from learnloop.adaptive_difficulty.switches import (
    LLM_V1,
    LLM_V3_DECIDER,
    LLM_V3_LLM,
    any_background_work,
    feature_audit_enabled,
    outside_forecasters,
)

LOG = logging.getLogger(__name__)

#: At most this many item revisions are prepared by one run of a vault's
#: preparation queue, whoever scheduled them (fix round 4, V2).
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


def _launch(sqlite_path: Any, key: str, job: Callable[[Any], None], *, builds: Any,
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
                        # The fence itself, not only its liveness (Codex
                        # review F5): each claimed write registers against a
                        # close, as the map builds' writes do.
                        job(fence)
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
                                    clock: Any = None,
                                    live_vault: Callable[[], Any] | None = None) -> threading.Thread | None:
    """``live_vault``: the provider of the vault loaded now (the sidecar's
    context's vault at check time), whose held-out predicate each request
    and record is checked against (fix round 4, V1)."""

    try:
        chosen = {LLM_V3_LLM, LLM_V3_DECIDER} & set(outside_forecasters(vault.config))
        if not chosen or not presentation_id:
            return None
        if ad_spend.models_off() and not _injected(clients):
            return None

        def job(fence: Any) -> None:
            from learnloop.db.repositories import Repository

            repository = Repository.attach(Path(sqlite_path))
            forecast_presentation(vault, repository, presentation_id, clients=clients, clock=clock, fence=fence,
                                  live_vault=live_vault)

        return _launch(sqlite_path, f"presentation:{presentation_id}", job, builds=builds,
                       name=f"learnloop-ad-forecast-{presentation_id}")
    except Exception:  # noqa: BLE001
        LOG.warning("AD presentation forecasts not scheduled", exc_info=True)
        return None


def prepare_items(vault: Any, repository: Any, item_ids: Iterable[str], *, clients: Clients | None = None,
                  decider_factory: Callable[[], Any] | None = None, clock: Any = None,
                  fence: Any = None, limit: int = PREPARE_LIMIT,
                  live_vault: Callable[[], Any] | None = None) -> list[dict[str, Any]]:
    """Audit, then forecast (``llm_v1:item``), each item's current revision; once each.

    Each unit runs under its own durable claim and, with a background job's
    ``fence``, stops asking and writing once the vault is switched or closed
    (Codex review F5, F6): a revision another job or process is preparing is
    ``busy`` here and left to it."""

    ids = list(dict.fromkeys(str(value) for value in item_ids))[:limit]
    items = [vault.practice_items.get(item_id) for item_id in ids]
    return _prepare(vault, repository, [item for item in items if item is not None], clients=clients,
                    decider_factory=decider_factory, clock=clock, fence=fence, live_vault=live_vault)


def _prepare(vault: Any, repository: Any, items: list[Any], *, clients: Clients | None,
             decider_factory: Callable[[], Any] | None, clock: Any, fence: Any,
             live_vault: Callable[[], Any] | None,
             results: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Prepare exactly these revisions (each an item as it was found), in order.

    Each visited revision's entry is appended to ``results`` as soon as it is
    done, with ``settled`` (fix round 5, V2): prepared, already done, or
    terminal (protected, no longer active, no longer in the vault). A caller
    that sees an exception knows which revisions were visited."""

    from learnloop.adaptive_difficulty.feature_audit import audit_revision, item_revision
    from learnloop.adaptive_difficulty.protection import protection

    def live() -> bool:
        return fence is None or fence.live()

    results = results if results is not None else []
    current = live_vault() if live_vault is not None else vault
    protected = protection(current if current is not None else vault, repository)
    for item in items:
        if not live():
            break
        item_id = str(item.id)
        content_hash = item_revision(item)[0]
        loaded = current if current is not None else vault
        if getattr(item, "status", "active") != "active" or item_id not in (loaded.practice_items or {}):
            # Terminal: retrying an ineligible or removed item changes nothing.
            results.append({"practice_item_id": item_id, "content_hash": content_hash, "status": "ineligible",
                            "settled": True})
            continue
        entry: dict[str, Any] = {"practice_item_id": item_id, "content_hash": content_hash}
        try:
            if feature_audit_enabled(vault.config):
                entry["audit"] = audit_revision(
                    vault, repository, item, clock=clock, protected=protected, fence=fence, live_vault=live_vault,
                    decider_factory=decider_factory or (
                        (lambda: clients.decider) if clients and clients.decider else None),
                    llm_client=clients.llm if clients else None,
                ).as_dict()
            if not live():
                break
            if LLM_V1 in outside_forecasters(vault.config):
                entry["llm_v1"] = forecast_item(vault, repository, item, clients=clients, clock=clock,
                                                protected=protected, fence=fence, live_vault=live_vault).as_dict()
        except Exception as exc:  # noqa: BLE001 - one revision's failure never stops the run
            # Fix round 6, V4: a revision that keeps raising used to abort the
            # run before anything was recorded, so every trigger retried it
            # first and the revisions behind it never ran. It is visited and
            # unsettled (retried later, at the back), and the run goes on.
            LOG.warning("AD preparation of %s failed", item_id, exc_info=True)
            entry.update(status="failed", error=type(exc).__name__)
            entry["settled"] = False
            results.append(entry)
            continue
        entry["settled"] = _settled(entry)
        results.append(entry)
        if entry["settled"]:
            with _GUARD:
                _PREPARED.add((str(Path(repository.sqlite_path)), item_id, entry["content_hash"]))
    return results


#: Item revisions this process has prepared to the end (audited or current,
#: forecast or current, or protected): a plan read never schedules them again.
_PREPARED: set[tuple[str, str, str]] = set()
#: Settled: done (ok, audited in full), already done (current), or terminal
#: (protected: the content is held out in the snapshot judged; the switch
#: off). Everything else (refused_spend, busy, unavailable, failed, an audit
#: with dimensions unanswered, and ``stale``: a reload under the check or its
#: retries exhausted, fix round 6, V3) is retried by a later run (fix round
#: 5, V2) and never cached in ``_PREPARED``.
_SETTLED = {"current", "protected", "disabled", "ok"}


def _settled(entry: dict[str, Any]) -> bool:
    audit = entry.get("audit", {"status": "disabled"})
    forecast = entry.get("llm_v1", {"status": "disabled"})
    audited = audit.get("status") in _SETTLED or (audit.get("status") == "audited" and not audit.get("unanswered"))
    return audited and forecast.get("status") in _SETTLED


@dataclass
class _Queue:
    """One vault's preparation queue (fix round 4, V2): the revisions waiting,
    in arrival order, each the item as it was found (Codex re-review F12: an
    edit mid-run queues the new revision beside the old one), and whether its
    one worker is running."""

    pending: dict[tuple[str, str], Any] = field(default_factory=dict)
    taken: set[tuple[str, str]] = field(default_factory=set)
    running: bool = False
    #: The latest scheduler's vault, clients and live-vault provider: a run
    #: prepares with what the vault looks like when it starts.
    vault: Any = None
    clients: Clients | None = None
    clock: Any = None
    live_vault: Callable[[], Any] | None = None


#: Per database: its preparation queue (this process; a revision another
#: process prepares is skipped under its durable claim).
_QUEUES: dict[str, _Queue] = {}


def schedule_item_preparation(vault: Any, sqlite_path: Any, item_ids: Iterable[str], *,
                              clients: Clients | None = None, builds: Any = None,
                              clock: Any = None, limit: int = PREPARE_LIMIT,
                              live_vault: Callable[[], Any] | None = None) -> threading.Thread | None:
    """Queue these items' current revisions for preparation, and start a run if none is running.

    Why one queue and one worker per vault (fix round 4, V2): a reload's
    import of 1,000 items, or several watcher batches, used to start a job
    each for all of them at once; nothing bounded the subscription calls
    (the daily cap counts metered dollars only). Now every caller (a reload,
    the file watcher, a plan read) feeds one deduplicated queue, and one run
    prepares at most :data:`PREPARE_LIMIT` revisions (``limit`` can only
    lower it). What is left waits for a later run: the next reload or plan
    read starts one, never a second worker beside a running one. Returns the
    run's thread, or None when no run was started."""

    try:
        from learnloop.adaptive_difficulty.feature_audit import item_revision

        wants = feature_audit_enabled(vault.config) or LLM_V1 in outside_forecasters(vault.config)
        if not wants:
            return None
        if ad_spend.models_off() and not _injected(clients):
            return None
        path = str(Path(sqlite_path))
        with _GUARD:
            queue = _QUEUES.setdefault(path, _Queue())
            for value in item_ids:
                item = vault.practice_items.get(str(value))
                if item is None:
                    continue
                key = (str(value), item_revision(item)[0])
                if (path, *key) in _PREPARED or key in queue.pending or key in queue.taken:
                    continue
                queue.pending[key] = item
            queue.vault, queue.clients, queue.clock = vault, clients, clock
            queue.live_vault = live_vault
        return _start_run(sqlite_path, queue, builds=builds, limit=max(0, min(int(limit), PREPARE_LIMIT)))
    except Exception:  # noqa: BLE001
        LOG.warning("AD item preparation not scheduled", exc_info=True)
        return None


def _start_run(sqlite_path: Any, queue: _Queue, *, builds: Any, limit: int) -> threading.Thread | None:
    """One run of at most ``limit`` revisions, unless the queue's worker is running."""

    with _GUARD:
        if queue.running or not queue.pending or limit <= 0:
            return None
        batch = list(queue.pending.items())[:limit]
        for key, _item in batch:
            del queue.pending[key]
        queue.taken = {key for key, _item in batch}
        queue.running = True
        vault, clients, clock, live_vault = queue.vault, queue.clients, queue.clock, queue.live_vault

    def finish(results: list[dict[str, Any]]) -> None:
        """Only settled revisions leave the queue (fix round 5, V2).

        Why: a run used to drop every revision it returned (a refused_spend,
        a busy claim, an unavailable route, an incomplete audit) and, after
        an exception, the whole batch, so an unchanged reload never retried
        them. Now a revision the run never reached (unvisited: an exception
        outside any one revision, the vault switched or closed) waits at the
        front, ahead of what arrived since; a revision visited and not
        settled, including one whose preparation raised (fix round 6, V4: the
        run catches it and goes on), goes to the back, so a revision that
        keeps failing never starves new ones. Either is retried only by a later trigger (a
        reload or a plan read), at most PREPARE_LIMIT a run; runs never chain."""

        visited = {(entry["practice_item_id"], entry["content_hash"]): bool(entry.get("settled"))
                   for entry in results}
        with _GUARD:
            unvisited = {key: item for key, item in batch if key not in visited}
            retry = {key: item for key, item in batch if visited.get(key) is False}
            waiting = {key: item for key, item in queue.pending.items() if key not in unvisited and key not in retry}
            queue.pending = {**unvisited, **waiting, **retry}
            queue.taken = set()
            queue.running = False

    def work(fence: Any) -> Callable[[], None]:
        def run() -> None:
            results: list[dict[str, Any]] = []
            try:
                if fence.live():
                    from learnloop.db.repositories import Repository

                    repository = Repository.attach(Path(sqlite_path))
                    _prepare(vault, repository, [item for _key, item in batch], clients=clients,
                             decider_factory=None, clock=clock, fence=fence, live_vault=live_vault,
                             results=results)
            except Exception:  # noqa: BLE001 - a background job never reaches the serve
                LOG.warning("adaptive difficulty preparation run failed", exc_info=True)
            finally:
                finish(results)
        return run

    try:
        thread = _registry(builds).launch(sqlite_path, work, name="learnloop-ad-prepare")
    except Exception:  # noqa: BLE001 - scheduling never fails a serve
        LOG.warning("adaptive difficulty preparation run not started", exc_info=True)
        thread = None
    if thread is None:
        finish([])
    return thread


def changed_revisions(previous: Any, vault: Any) -> list[str]:
    """The active items whose current revision is new since ``previous`` (the
    vault as this process last loaded it): published, imported or edited."""

    if previous is None:
        return []
    before = getattr(previous, "practice_items", {}) or {}
    return sorted(item_id for item_id, item in (getattr(vault, "practice_items", {}) or {}).items()
                  if getattr(item, "status", "active") == "active" and before.get(item_id) != item)


def schedule_new_revisions(previous: Any, vault: Any, sqlite_path: Any, *, item_ids: Iterable[str] | None = None,
                           clients: Clients | None = None, builds: Any = None,
                           live_vault: Callable[[], Any] | None = None) -> threading.Thread | None:
    """Prepare the revisions published, imported or edited since the last load (Codex review F10).

    Spec §7.2/§8.2: the feature audit and ``llm_v1:item`` run "after any item
    is generated or imported", not only once it reaches a plan. Every path
    that publishes or imports an item, or edits one, ends in the sidecar's
    vault reload (or the file watcher's incremental refresh, ``item_ids``),
    so the new revisions are scheduled there, every one of them, in the
    background; the plan hook stays the recovery path (a CLI import, a job
    a closed process never finished). A first open schedules nothing: the
    existing pool is the owner-run backfill's (dry-run first). Never raises."""

    try:
        if not any_background_work(vault.config):
            return None
        ids = sorted(set(str(value) for value in item_ids)) if item_ids is not None else changed_revisions(
            previous, vault)
        ids = [item_id for item_id in ids if item_id in (vault.practice_items or {})]
        # Every new revision is queued, and a run prepares at most
        # PREPARE_LIMIT of them (fix round 4, V2); a reload with nothing new
        # still starts a run for what an earlier one left waiting.
        return schedule_item_preparation(vault, sqlite_path, ids, clients=clients, builds=builds,
                                         live_vault=live_vault)
    except Exception:  # noqa: BLE001 - preparation never blocks a reload
        LOG.warning("AD preparation of new revisions not scheduled", exc_info=True)
        return None


__all__ = ["PREPARE_LIMIT", "changed_revisions", "prepare_items", "schedule_item_preparation", "schedule_new_revisions",
           "schedule_presentation_forecasts"]
