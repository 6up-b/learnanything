"""A finished section's questions, started from the desktop app (the primary).

The rule and its once-only stamp are ``learnloop.reader.section_generation``;
this binds them to the sidecar's queue and decides where the sections still
owing their questions are picked up: the desktop's start, the Reader opening a
book, and every read of the books (Today and the shelf), which is where a
learner looks for their questions. Never on the phone host's secondary attach:
its work never includes model calls.
"""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def start_section_questions(ctx: Any, vault: Any, repository: Any, extraction_id: str, section_id: str, *,
                            from_stamp: str | None = None, completed_at: str | None = None) -> str | None:
    """A finished section's question writing, queued on this app's queue, once; the batch id, or None."""

    from learnloop.ai import plan_fallback
    from learnloop.content.pipeline.add_source import section_topics_settled
    from learnloop.reader import section_generation
    from learnloop.vault.loader import load_vault

    def enqueue(lo_ids: list[str], reason: str, refs: list[dict[str, Any]]) -> str:
        # Reading progress is not a press: the expansion asks nothing and carries no grant.
        with plan_fallback.quiet():
            return ctx.ingest_jobs.enqueue_practice_expansion(learning_object_ids=lo_ids, reason=reason,
                                                              source_refs=refs)

    return section_generation.start_section_questions(
        vault, repository, extraction_id=extraction_id, section_id=section_id, enqueue=enqueue,
        fresh_vault=lambda: load_vault(ctx.vault_root),
        topics_settled=lambda: section_topics_settled(repository, extraction_id, section_id),
        from_stamp=from_stamp, completed_at=completed_at,
    )


def drain_owed_section_questions(ctx: Any, vault: Any, repository: Any, *, extraction_id: str | None = None) -> int:
    """Start the writing every finished section still owes: one the phone finished, one that waited for its
    book's build, one an older version settled as needing nothing before its topics were in. Each is decided
    once (:func:`learnloop.reader.section_generation.start_section_questions`); a waiting section whose build
    has not settled costs one read of the build's rows. Returns how many were queued. Best effort: it never
    fails the read it rides on, and a section it could not queue keeps its stamp for the next one."""

    from learnloop.reader.section_generation import OWED

    if getattr(ctx, "secondary", False):
        return 0
    queued = 0
    for stamp in OWED:
        try:
            rows = repository.deferred_section_generations(stamp, extraction_id=extraction_id)
        except Exception:  # pragma: no cover - a read failure leaves them for the next read
            return queued
        for row in rows:
            try:
                if start_section_questions(ctx, vault, repository, str(row["extraction_id"]), str(row["section_id"]),
                                           from_stamp=stamp, completed_at=row.get("completed_at")) is not None:
                    queued += 1
            except Exception:  # noqa: BLE001 - one section's failure is kept for its next try
                _LOGGER.warning("a finished section's questions were not queued", exc_info=True)
    return queued
