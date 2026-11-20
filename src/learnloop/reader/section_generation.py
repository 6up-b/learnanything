"""Section practice candidates, separate from reader grounding, and when a
finished section's questions are written.

This keeps practice_generation out of reader_progression.

A finished section's questions are written once, from the topics whose
sources cite it. ``reader_section_progress.generation_batch_id`` holds where
that stands; every move of it is a compare-and-set from the value the mover
read (``mark_section_generation`` from NULL, ``swap_section_generation`` from
any other), so of two movers only one wins, and only the winner of the move to
:data:`ENQUEUING` queues anything.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.db.stores.reader import (
    SECTION_DEFERRED_TO_PRIMARY as DEFERRED_TO_PRIMARY,
    SECTION_ENQUEUING as ENQUEUING,
    SECTION_NONE_NEEDED as NONE_NEEDED,
    SECTION_NONE_NEEDED_BEFORE as NONE_NEEDED_BEFORE,
    SECTION_WAITING_FOR_BUILD as WAITING_FOR_BUILD,
)
from learnloop.reader.reader_progression import learning_objects_for_section
from learnloop.vault.models import LoadedVault

__all__ = [
    "DEFERRED_TO_PRIMARY", "ENQUEUING", "NONE_NEEDED", "NONE_NEEDED_BEFORE", "OWED", "WAITING_FOR_BUILD",
    "section_generation_candidates", "section_reason", "start_section_questions",
]

#: The stamps a finished section can still owe its questions under.
OWED = (DEFERRED_TO_PRIMARY, WAITING_FOR_BUILD, NONE_NEEDED_BEFORE)

#: Queues one section's writing: (learning object ids, reason, source refs) -> batch id.
Enqueue = Callable[[list[str], str, list[dict[str, Any]]], str]


def section_generation_candidates(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    target_items_per_lo: int = 3,
    max_new_per_lo: int = 3,
) -> list[str]:
    """LOs in the section that actually need items (dry-run of the expansion
    plan with the probe gate waived). Empty = nothing to generate."""

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        build_practice_expansion_plan,
    )

    lo_ids = learning_objects_for_section(
        vault, repository, extraction_id=extraction_id, section_id=section_id
    )
    if not lo_ids:
        return []
    try:
        plan = build_practice_expansion_plan(
            vault,
            repository,
            learning_object_ids=lo_ids,
            require_completed_probe=False,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
        )
    except PracticeExpansionError:
        return []
    # Only LOs with a real deficit: named LOs past their target still get a
    # courtesy item from the planner, which is wrong for an automatic trigger.
    return sorted(
        target.learning_object_id
        for target in plan.targets
        if target.existing_practice_items < target_items_per_lo
    )


def section_reason(section_id: str) -> str:
    """The reason a finished section's writing is queued under."""

    return f"reader_section_completed:{section_id}"


def start_section_questions(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    enqueue: Enqueue,
    fresh_vault: Callable[[], LoadedVault],
    topics_settled: Callable[[], tuple[bool, str | None]],
    from_stamp: str | None = None,
    completed_at: str | None = None,
) -> str | None:
    """Start a finished section's question writing, once, or record why not yet.

    ``from_stamp`` is the stamp the caller read (None: a first completion).
    Returns the queued batch id, or None when nothing was queued: the section
    then waits for its chapter's build (:data:`WAITING_FOR_BUILD`), or needs
    nothing (:data:`NONE_NEEDED`), or another mover took it first.

    ``topics_settled`` says whether the build of the section's chapter has
    settled, with when it ended (``add_source.section_topics_settled``). It is
    read before the topics: a build that settles between the two reads leaves
    the section waiting, to be started on a later read, never settled as
    needing nothing while its topics were still being written. ``vault`` may be
    a snapshot loaded before the build applied; nothing is settled as needing
    nothing on it alone (``fresh_vault``).
    """

    def move(to: str) -> bool:
        if from_stamp is None:
            return repository.mark_section_generation(extraction_id=extraction_id, section_id=section_id, batch_id=to)
        return repository.swap_section_generation(
            extraction_id=extraction_id, section_id=section_id, from_batch_id=from_stamp, batch_id=to
        )

    settled, settled_at = topics_settled()
    if from_stamp == WAITING_FOR_BUILD and not settled:
        return None  # nothing new to write from: the build that writes its topics has not settled
    if from_stamp == NONE_NEEDED_BEFORE:
        if not settled:
            move(WAITING_FOR_BUILD)
            return None
        if settled_at is None or (completed_at is not None and completed_at > settled_at):
            # Finished after its chapter's topics were in (or the book was built another way, where no build
            # time is kept): the older answer was decided on them and stands.
            move(NONE_NEEDED)
            return None
    lo_ids = section_generation_candidates(vault, repository, extraction_id=extraction_id, section_id=section_id)
    if not lo_ids and settled:
        vault = fresh_vault()
        lo_ids = section_generation_candidates(vault, repository, extraction_id=extraction_id, section_id=section_id)
    if not lo_ids:
        to = NONE_NEEDED if settled else WAITING_FOR_BUILD
        if to != from_stamp:
            move(to)
        return None
    # The claim comes first, so a concurrent mover cannot queue it too: the loser sees the claim and does nothing.
    if not move(ENQUEUING):
        return None
    from learnloop.reader.reader_progression import source_refs_for_section

    refs = source_refs_for_section(
        vault, repository, extraction_id=extraction_id, section_id=section_id, learning_object_ids=lo_ids
    )
    try:
        batch_id = enqueue(lo_ids, section_reason(section_id), refs)
    except Exception:
        if from_stamp is not None:
            # Handed back to the stamp it came from, so the next read tries again.
            repository.swap_section_generation(extraction_id=extraction_id, section_id=section_id,
                                               from_batch_id=ENQUEUING, batch_id=from_stamp)
        raise
    repository.set_section_generation_batch(extraction_id=extraction_id, section_id=section_id, batch_id=batch_id)
    return batch_id
