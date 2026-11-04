"""FG1's durable generation queue: the writes domain packages may make (a leaf).

One row per deduplicated key. That is the structural bound on physical generation on a
subscription route, where dollar reservations bound nothing (spec §8).
"""

from __future__ import annotations

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store


def enqueue_workflow(repository: Repository, workflow_id: str, *, clock: Clock | None = None) -> str | None:
    """Queue the workflow's one job (the dedupe key is its identity)."""

    with repository.atomic(), repository.connection() as connection:
        return store.enqueue_generation_job(
            connection, kind="workflow", dedupe_key=f"workflow:{workflow_id}", workflow_id=workflow_id,
            at=utc_now_iso(clock),
        )


def enqueue_need(repository: Repository, need_id: str, *, clock: Clock | None = None) -> str | None:
    """A recorded practice-lane need fills in the background, deduplicated (§4)."""

    with repository.atomic(), repository.connection() as connection:
        return store.enqueue_generation_job(
            connection, kind="need", dedupe_key=f"need:{need_id}", need_id=need_id, at=utc_now_iso(clock),
        )


def enqueue_factor(repository: Repository, factor_id: str, *, workflow_id: str | None, clock: Clock | None = None) -> str | None:
    """A failed probe lane's need stays open for background generation, deduplicated by factor (§6.2)."""

    with repository.atomic(), repository.connection() as connection:
        return store.enqueue_generation_job(
            connection, kind="need", dedupe_key=f"factor:{factor_id}", workflow_id=workflow_id, at=utc_now_iso(clock),
        )


def enqueue_entry(repository: Repository, episode_id: str, *, clock: Clock | None = None) -> str | None:
    """An episode entered: its generation is queued, so opening a vault can't stall or burst (§4.3)."""

    with repository.atomic(), repository.connection() as connection:
        return store.enqueue_generation_job(
            connection, kind="entry_episode", dedupe_key=f"entry:{episode_id}", probe_episode_id=episode_id,
            at=utc_now_iso(clock),
        )


def pending_jobs(repository: Repository) -> int:
    with repository.connection() as connection:
        return store.runnable_generation_jobs(connection) if store.present(connection, "followup_generation_jobs") else 0


__all__ = ["enqueue_entry", "enqueue_factor", "enqueue_need", "enqueue_workflow", "pending_jobs"]
