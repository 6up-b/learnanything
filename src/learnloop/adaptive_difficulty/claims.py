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
* the *finish* receipt of a request already sent, and the spend ledger, are
  not fenced: the money a sent request cost is always accounted to its own
  vault.

A claim that cannot be taken (another worker's live lease) yields None.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from learnloop.hints import map_builder as _builds

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
            return
        # A request already sent keeps its accounting, whatever happened since.
        self._repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)


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
