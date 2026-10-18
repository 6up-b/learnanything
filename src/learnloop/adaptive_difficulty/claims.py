"""One durable, fenced claim per piece of AD paid work (Codex review F5, F6).

Each paid unit of AD1 work (a revision's feature audit, a revision's
``llm_v1:item`` forecast, a presentation's ``llm_v3`` forecasts) is claimed in
``judgment_work_claims`` before anything is asked (task
:data:`CLAIM_TASK`): the same lease, heartbeat and fence the approach-map
builds use (``learnloop.hints.map_builder``). So two preparations in one
process (jobs for ``[A, B]`` and ``[B]``), or a sidecar job and a CLI backfill
in another process, never pay for the same audit twice: the second finds the
claim held and skips; whoever acquires it re-checks what is already persisted
before asking.

While the claim is held, the work writes through :class:`FencedRepository`:

* every domain write (judgments, payloads, receipts) commits only while the
  lease holds and, for a background job, while its vault is still loaded
  (the sidecar registry's generation, with the commit registered against a
  close, as the map builds do);
* a model call's *start* receipt is fenced the same way, and it is written
  before the request is sent: once the vault is switched or closed, no new
  request goes out;
* a model checkpoint (the answer kept for a rerun) is fenced the same way
  (fix round 4, V3);
* the *finish* receipt of a request already sent, and the spend ledger, are
  not fenced: the money a sent request cost is always accounted to its own
  vault.

A claim that cannot be taken (another worker's live lease) yields None.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from learnloop.hints import map_builder as _builds

LOG = logging.getLogger(__name__)

#: ``judgment_work_claims.task`` of AD's background and backfill work.
CLAIM_TASK = "ad_background_work"
PRODUCER = "adaptive_difficulty"

#: Raised by a fenced write (or a fenced start) once the lease or the vault is lost.
LeaseLost = _builds._LeaseLost


def audit_key(content_hash: str) -> str:
    return f"{CLAIM_TASK}:feature_audit:{content_hash}"


def item_forecast_key(content_hash: str) -> str:
    return f"{CLAIM_TASK}:llm_v1:{content_hash}"


def presentation_key(presentation_id: str) -> str:
    return f"{CLAIM_TASK}:llm_v3:{presentation_id}"


class FencedRepository:
    """The repository a claimed unit of work writes through (see the module docstring)."""

    def __init__(self, repository: Any, claim: Any) -> None:
        self._repository = repository
        self._claim = claim

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repository, name)

    @property
    def base(self) -> Any:
        return self._repository

    @contextmanager
    def atomic(self) -> Iterator[None]:
        with _builds._fenced_txn(self._repository, self._claim):
            yield

    def connection(self) -> Any:
        return self._repository.connection()

    def record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None:
        if action == "start":
            # Before the request is sent: fenced out, it raises and nothing is sent.
            with _builds._fenced_txn(self._repository, self._claim):
                self._repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)
            # The last confirmation before dispatch (fix round 6, V1-b): after
            # the outer gate and this receipt, the last work before the
            # transport sends. A refusal closes the receipt as interrupted
            # (never sent, no usage) and raises.
            from learnloop.adaptive_difficulty.sending import ProtectedContent, before_dispatch

            try:
                before_dispatch()
            except ProtectedContent as exc:
                from learnloop.clock import utc_now_iso

                self._repository.record_model_event("finish", {
                    "id": event.get("id"), "finished_at": utc_now_iso(), "status": "interrupted",
                    "error_type": type(exc).__name__}, owner_kind=owner_kind, owner_id=owner_id)
                raise
            return
        # A request already sent keeps its accounting, whatever happened since.
        self._repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)

    # A model checkpoint is domain output, not accounting (fix round 4, V3):
    # the base repository writes it on a separate connection that allows late
    # writes, so an answer arriving after a vault switch would still land in
    # ``model_work_checkpoints``. It is fenced like every other domain write,
    # as the approach-map builds' repository does; a checkpoint fenced out is
    # dropped (the answer is never reused) and the job's next write reports
    # it stale. The finish receipt above and the spend settlement (the
    # envelope writes on the base repository) stay unfenced.
    def save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any],
                              usage: dict[str, Any] | None = None) -> None:
        from learnloop.db.stores.model_calls import insert_checkpoint

        try:
            with _builds._fenced_txn(self._repository, self._claim) as connection:
                insert_checkpoint(connection, cache_key, purpose=purpose, result=result, usage=usage)
        except LeaseLost:
            LOG.info("AD job fenced out: model checkpoint %s dropped", cache_key)

    def discard_model_checkpoint(self, cache_key: str) -> None:
        from learnloop.db.stores.model_calls import delete_checkpoint

        try:
            with _builds._fenced_txn(self._repository, self._claim) as connection:
                delete_checkpoint(connection, cache_key)
        except LeaseLost:
            LOG.info("AD job fenced out: model checkpoint %s kept", cache_key)


class Worker:
    """A held claim: :attr:`repository` writes fenced; :meth:`live` before each request."""

    def __init__(self, repository: Any, claim: Any) -> None:
        self.base = repository
        self.claim = claim
        self.repository = FencedRepository(repository, claim)

    def live(self) -> bool:
        return _builds._alive(self.base, self.claim)

    def require_live(self) -> None:
        if not self.live():
            raise LeaseLost("the AD job's claim or vault was lost; nothing more is asked")


@contextmanager
def claimed(repository: Any, key: str, *, fence: Any = None) -> Iterator[Worker | None]:
    """Hold ``key``'s durable claim for the block (no waiting: None when held elsewhere)."""

    base = repository.base if isinstance(repository, FencedRepository) else repository
    if fence is not None and not fence.live():
        # The job's vault was switched or closed before it started this unit.
        raise LeaseLost("the AD job's vault was closed before this work was claimed")
    with _builds._claimed(base, key, time.monotonic(), fence=fence, key=key, task=CLAIM_TASK,
                          producer=PRODUCER) as claim:
        yield None if claim is None else Worker(base, claim)


__all__ = ["CLAIM_TASK", "FencedRepository", "LeaseLost", "PRODUCER", "Worker", "audit_key", "claimed",
           "item_forecast_key", "presentation_key"]
