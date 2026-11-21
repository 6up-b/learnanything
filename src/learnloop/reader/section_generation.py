"""Section practice candidates, separate from reader grounding, and when a
finished section's questions are written.

This keeps practice_generation out of reader_progression.

A finished section's questions are written once, from the topics whose
sources cite it. ``reader_section_progress.generation_batch_id`` holds where
that stands; every move of it is a compare-and-set from the value the mover
read (``mark_section_generation`` from NULL, ``swap_section_generation`` from
any other), so of two movers only one wins.

The work itself is owned per topic (``reader_topic_question_work``): the
winner of the move to :data:`TOPIC_MANAGED` claims each of the section's
topics nobody owns and queues their work, in one transaction
(:func:`claim_section_topics`). A topic is written for once, whichever
section or book cites it. Section jobs queued before topic work existed keep
their batch id as the stamp (and :data:`ENQUEUING` while one was being
queued); their topics are indexed as theirs before anything new is claimed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.db.stores.reader import (
    READER_FIRST_SET,
    SECTION_DEFERRED_TO_PRIMARY as DEFERRED_TO_PRIMARY,
    SECTION_ENQUEUING as ENQUEUING,
    SECTION_NONE_NEEDED as NONE_NEEDED,
    SECTION_NONE_NEEDED_BEFORE as NONE_NEEDED_BEFORE,
    SECTION_TOPIC_MANAGED as TOPIC_MANAGED,
    SECTION_WAITING_FOR_BUILD as WAITING_FOR_BUILD,
)
from learnloop.reader.reader_progression import learning_objects_for_section
from learnloop.vault.models import LoadedVault

__all__ = [
    "DEFERRED_TO_PRIMARY", "ENQUEUING", "NONE_NEEDED", "NONE_NEEDED_BEFORE", "OWED", "READER_FIRST_SET_TARGET",
    "TOPIC_MANAGED",
    "WAITING_FOR_BUILD", "claim_section_topics", "index_section_jobs", "section_generation_candidates",
    "section_reason", "section_topic_requests", "start_section_questions",
]

#: The stamps a finished section can still owe its questions under.
OWED = (DEFERRED_TO_PRIMARY, WAITING_FOR_BUILD, NONE_NEEDED_BEFORE)

#: A topic's first set from reading: it is asked for questions while it has fewer than this many, and for at most
#: this many at once (``min(target - existing, target)``). Not a new number: the section-seeding contract's existing
#: target, which the writing job plans to (``jobs.handle_practice_expansion``); the part read and the finish share it.
READER_FIRST_SET_TARGET = 3

#: The prefix of a finished section's reason, which a section job's payload names its section by.
_SECTION_REASON = "reader_section_completed:"

#: Records the work of newly claimed topics inside the claim's transaction and never starts it (a foreground
#: queue started there would run the model calls with the write lock held): (learning object ids, reason, source
#: refs, {topic: checkpoint scope}) -> batch id.
TopicEnqueue = Callable[[list[str], str, list[dict[str, Any]], dict[str, str]], str]


def section_generation_candidates(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    target_items_per_lo: int = READER_FIRST_SET_TARGET,
    max_new_per_lo: int = READER_FIRST_SET_TARGET,
) -> list[str]:
    """LOs in the section that actually need items (dry-run of the expansion
    plan with the probe gate waived). Empty = nothing to generate."""

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        build_practice_expansion_plan,
    )

    lo_ids = learning_objects_for_section(
        vault, repository, extraction_id=extraction_id, section_id=section_id, reading_order=True
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
    needed = {
        target.learning_object_id
        for target in plan.targets
        if target.existing_practice_items < target_items_per_lo
    }
    return [lo_id for lo_id in lo_ids if lo_id in needed]


def section_reason(section_id: str) -> str:
    """The reason a finished section's writing is queued under."""

    return f"{_SECTION_REASON}{section_id}"


def section_topic_requests(vault: LoadedVault, repository: Repository, lo_ids: list[str]) -> dict[str, int]:
    """How many questions the plan asks for each of ``lo_ids``, as the section's job plans them."""

    from learnloop.content.authoring.practice_generation import PracticeExpansionError, build_practice_expansion_plan

    if not lo_ids:
        return {}
    try:
        plan = build_practice_expansion_plan(vault, repository, learning_object_ids=lo_ids,
                                             require_completed_probe=False, target_items_per_lo=READER_FIRST_SET_TARGET,
                                             max_new_per_lo=READER_FIRST_SET_TARGET)
    except PracticeExpansionError:
        return {}
    return {target.learning_object_id: target.requested_new_items for target in plan.targets}


def _reading_source(repository: Repository, extraction_id: str) -> str | None:
    run = repository.get_extraction_run(extraction_id)
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) if run else None
    return str(revision["source_id"]) if revision and revision.get("source_id") else None


def index_section_jobs(repository: Repository) -> int:
    """Index every section job's topics as that job's work (owner ``section_job``), whatever its state: queued,
    running, failed, held for review or finished. Its batch, job, section and proposals are recorded; the job,
    its payload, its key and its stamp are left exactly as they are. Run before any new claim, so a topic a
    section job already writes for is never claimed for new work. Returns how many topics it named."""

    jobs = [job for job in repository.ingest_jobs_by_types(["practice_expansion"])
            if str((job.get("payload") or {}).get("reason") or "").startswith(_SECTION_REASON)
            and "topic_keys" not in (job.get("payload") or {})]
    rows = []
    for job in sorted(jobs, key=lambda job: (str(job.get("created_at") or ""), str(job["id"]))):
        payload = job.get("payload") or {}
        section_id = str(payload["reason"])[len(_SECTION_REASON):]
        refs = [ref for ref in payload.get("source_refs") or [] if isinstance(ref, Mapping)]
        stamped = _stamped_section(repository, str(job["batch_id"]))
        extraction_id = stamped or next((str(ref["extraction_id"]) for ref in refs if ref.get("extraction_id")), None)
        parts = {str(part.get("topic_id")): part.get("patch_id") for part in payload.get("question_parts") or []
                 if isinstance(part, Mapping)}
        for lo_id in dict.fromkeys(str(lo) for lo in payload.get("learning_object_ids") or [] if str(lo).strip()):
            rows.append({
                "learning_object_id": lo_id, "batch_id": str(job["batch_id"]), "job_id": str(job["id"]),
                "extraction_id": extraction_id, "section_id": section_id,
                "source_id": _reading_source(repository, extraction_id) if extraction_id else None,
                "source_refs": [dict(ref) for ref in refs if lo_id in (ref.get("learning_object_ids") or [])],
                "proposal_ids": [parts[lo_id]] if parts.get(lo_id) else [],
            })
    repository.index_section_job_topics(rows)
    return len(rows)


def _stamped_section(repository: Repository, batch_id: str) -> str | None:
    """The reading whose finished section is stamped with this batch (a section job's own), if any."""

    with repository.connection() as connection:
        row = connection.execute(
            "SELECT extraction_id FROM reader_section_progress WHERE generation_batch_id = ? ORDER BY extraction_id",
            (batch_id,),
        ).fetchone()
    return str(row["extraction_id"]) if row is not None else None


def claim_section_topics(
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    lo_ids: list[str],
    refs: list[dict[str, Any]],
    enqueue: TopicEnqueue,
    from_stamp: str | None,
    source_id: str | None = None,
    requested: Mapping[str, int] | None = None,
    trigger: str = "section_finished",
) -> str | None:
    """Claim the section's topics nobody owns and queue their work, in one transaction.

    The section's stamp moves from ``from_stamp`` (None: a first finish) to :data:`TOPIC_MANAGED`, a
    compare-and-set: a mover that lost it claims nothing. ``from_stamp`` :data:`TOPIC_MANAGED` adds topics to a
    section already so managed (a later wave). Section jobs' topics are indexed first; then each of ``lo_ids``
    no claim names is claimed, with its own grounding (its bundles of ``refs``) and its own checkpoint scope,
    and one batch is queued for them with the bundles of exactly those topics: the request a section job would
    send for them. A failure anywhere (the queue's included) rolls back the stamp, the claims and the batch.
    ``enqueue`` must record into this ``repository``'s transaction and start nothing; the caller starts the
    queue after this returns. Returns the batch id, or None when nothing new was claimed."""

    from learnloop.content.authoring.practice_generation import topic_questions_key

    own = {lo: [dict(ref) for ref in refs if lo in (ref.get("learning_object_ids") or [])] for lo in lo_ids}
    source_id = source_id or _reading_source(repository, extraction_id)
    with repository.atomic():
        if from_stamp is None:
            moved = repository.mark_section_generation(extraction_id=extraction_id, section_id=section_id,
                                                       batch_id=TOPIC_MANAGED)
        elif from_stamp != TOPIC_MANAGED:
            moved = repository.swap_section_generation(extraction_id=extraction_id, section_id=section_id,
                                                       from_batch_id=from_stamp, batch_id=TOPIC_MANAGED)
        else:
            moved = True
        if not moved:
            return None
        index_section_jobs(repository)
        owned = repository.topic_question_work_for(lo_ids, purpose=READER_FIRST_SET)
        new = [lo for lo in dict.fromkeys(lo_ids) if lo not in owned]
        if not new:
            return None
        keys = {lo: topic_questions_key(lo, own[lo]) for lo in new}
        wave = [dict(ref) for ref in refs if any(lo in new for lo in ref.get("learning_object_ids") or [])]
        batch_id = enqueue(new, section_reason(section_id), wave, keys)
        job_id = next((str(job["id"]) for job in repository.ingest_jobs_for_batch(batch_id)), None)
        repository.insert_topic_question_work([
            {"learning_object_id": lo, "source_id": source_id, "extraction_id": extraction_id,
             "section_id": section_id, "trigger_event": trigger, "source_refs": own[lo],
             "passage_ids": list(dict.fromkeys(span for ref in own[lo] for span in ref.get("span_ids") or [])),
             "requested_count": (requested or {}).get(lo), "work_key": keys[lo], "batch_id": batch_id,
             "job_id": job_id}
            for lo in new
        ])
    return batch_id


def start_section_questions(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    enqueue: TopicEnqueue,
    fresh_vault: Callable[[], LoadedVault],
    topics_settled: Callable[[], tuple[bool, str | None]],
    from_stamp: str | None = None,
    completed_at: str | None = None,
    claim_repository: Repository | None = None,
) -> str | None:
    """Start a finished section's question writing, once, or record why not yet.

    ``from_stamp`` is the stamp the caller read (None: a first completion).
    Returns the queued batch id, or None when nothing was queued: the section
    then waits for its chapter's build (:data:`WAITING_FOR_BUILD`), or needs
    nothing (:data:`NONE_NEEDED`), or another mover took it first, or every
    topic citing it is owned already (it is then :data:`TOPIC_MANAGED` with no
    work of its own). The claim (:func:`claim_section_topics`) runs on
    ``claim_repository`` (default ``repository``): the one ``enqueue`` records
    into, so both are one transaction.

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
        if settled and repository.topic_question_work_rows(extraction_id=extraction_id, section_id=section_id,
                                                           owner="topic"):
            # Its part read claimed its topics before it was finished: their work is its questions, which "none
            # needed" would hide.
            to = TOPIC_MANAGED
        if to != from_stamp:
            move(to)
        return None
    from learnloop.reader.reader_progression import source_refs_for_section

    refs = source_refs_for_section(
        vault, repository, extraction_id=extraction_id, section_id=section_id, learning_object_ids=lo_ids
    )
    # The stamp's move, the claims and the queueing are one transaction: a concurrent mover loses the move and
    # claims nothing, and a failure leaves the stamp it came from, so the next read tries again.
    return claim_section_topics(
        claim_repository or repository, extraction_id=extraction_id, section_id=section_id, lo_ids=lo_ids,
        refs=refs, enqueue=enqueue, from_stamp=from_stamp, requested=section_topic_requests(vault, repository, lo_ids),
    )
