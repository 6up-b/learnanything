from __future__ import annotations

from typing import Any

from learnloop.services.instrument_serving import (
    UNSERVABLE_ERROR_CODE,
    unservable_refusal,
)
from learnloop.services.proposals import queue_accepted_diagnostic_followups
from learnloop.services.scheduler import (
    SchedulerSession,
    build_due_queue,
    deferred_cold_followups,
    explain_practice_item,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.ingest_jobs import _APPLYING_JOB_TYPES
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import (
    latest_scheduler_explanation_dto,
    practice_item_detail,
    scheduled_item_dto,
    scheduler_explanation_dto,
)
from learnloop_sidecar.handlers.teach_back import filter_unready_teach_back_items
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method


class QueueInput(ParamsModel):
    session_id: str | None = None
    available_minutes: int | None = None
    energy: str | None = None
    limit: int | None = None


class PracticeItemInput(ParamsModel):
    practice_item_id: str


#: Job types whose completion must invalidate the sidecar's in-memory vault.
#:
#: This MUST stay in sync with ``ingest_jobs._APPLYING_JOB_TYPES`` — that tuple
#: is the authority on which jobs change vault content, and any job listed there
#: but missing here applies items the Today queue then cannot see, because
#: ``get_today_queue`` reads the cached snapshot. The two drifted once already
#: (``goal_population`` was added to the applying list and not to this one), so
#: the set is derived rather than restated.
_QUEUE_RELOAD_JOB_TYPES = frozenset(_APPLYING_JOB_TYPES)


@method("get_queue_revision", ParamsModel)
def get_queue_revision(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    """Cheap durable high-water mark for asynchronous Today invalidation."""

    # A promotion job can write vault YAML between UI ticks. Reload exactly
    # once when its durable job completes so the subsequent Today refetch sees
    # the new item, rather than the pre-authoring in-memory vault snapshot.
    completed = [
        job["id"]
        for batch in ctx.ingest_jobs.list_batches(limit=8)
        for job in batch.get("jobs") or []
        if job.get("job_type") in _QUEUE_RELOAD_JOB_TYPES
        and job.get("status") == "completed"
        and ctx.ingest_jobs.needs_reload(job["id"])
    ]
    if completed:
        ctx.reload(maintenance=False)
        for job_id in completed:
            ctx.ingest_jobs.mark_reloaded(job_id)
    _vault, repository = ctx.require_vault()
    return versioned(repository.queue_revision())


@method("get_today_queue", QueueInput)
def get_today_queue(ctx: SidecarContext, params: QueueInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    queue_accepted_diagnostic_followups(repository)
    queue = build_due_queue(
        vault,
        repository,
        session=SchedulerSession(
            session_id=params.session_id,
            available_minutes=params.available_minutes,
            energy=params.energy,
        ),
        limit=params.limit,
    )
    # Handler-level (never persisted): teach_back items dead-end without their
    # AI provider, so they are dropped from the offered queue while it is down.
    queue = filter_unready_teach_back_items(
        vault, queue, grading_provider_override=ctx.grading_provider_override
    )
    dtos = [scheduled_item_dto(vault, repository, item) for item in queue]
    slate = repository.latest_scheduler_slate_by_session(params.session_id) if params.session_id else None
    log_event(
        "scheduler_slate",
        session_id=params.session_id,
        scheduler_slate_id=slate["id"] if slate is not None else None,
        candidate_count=slate["candidate_count"] if slate is not None else len(queue),
        returned_count=slate["returned_count"] if slate is not None else len(queue),
        chosen_policy=slate["selection_policy"] if slate is not None else "selection_reward_v1",
        candidates=[
            {
                "practice_item_id": item.practice_item_id,
                "learning_object_id": item.learning_object_id,
                "priority": item.priority,
                "selection_reward": item.components.get("selection_reward"),
                "predicted_correctness": item.components.get("predicted_correctness"),
                "expected_information_gain": item.components.get("probe_eig"),
            }
            for item in queue
        ],
    )
    # Cold checks the scheduler is withholding because their answer was shown
    # since they were scheduled. They are NOT queue items — they were removed
    # before ranking — so they ride alongside the sections rather than in them,
    # and the surface reports them as waiting rather than offering them.
    deferrals = [
        {
            **row,
            "learning_object_title": (
                learning_object.title
                if (
                    learning_object := vault.learning_objects.get(
                        str(row.get("learning_object_id") or "")
                    )
                )
                is not None
                else row.get("learning_object_id")
            ),
        }
        for row in deferred_cold_followups(vault, repository)
    ]
    return versioned(
        {
            "generated_at": _nowish(),
            "session_id": params.session_id,
            "sections": _sections(dtos),
            "total_items": len(dtos),
            "deferred_cold_checks": deferrals,
        }
    )


@method("explain_practice_item", PracticeItemInput)
def explain_practice_item_handler(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    scheduled = explain_practice_item(vault, repository, params.practice_item_id)
    if scheduled is not None:
        return scheduler_explanation_dto(scheduled)
    latest = repository.latest_scheduler_explanation(params.practice_item_id)
    if latest is None:
        raise SidecarError("not_found", f"No scheduler explanation for {params.practice_item_id}.")
    return latest_scheduler_explanation_dto(latest)


@method("open_queue_item", PracticeItemInput)
def open_queue_item(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    """Open one item by id, or refuse with the reason it cannot be rendered.

    Meas §3.A2/§3.A3. ``build_due_queue`` keeps unrenderable instruments out of
    the queue, but this method takes an id, not a queue position: a deep link, a
    restored session, an inspector jump or a stale client all reach an item the
    queue would never have offered. Without the guard the learner gets the
    error-hunt prompt ("correct the worked solution below") with no solution
    under it, answers blind, and the grader — which DOES receive the solution —
    marks every plant missed.

    Refusing with ``not_found`` would be a lie the learner cannot act on: the
    item exists, passed every authoring gate, and is in their vault. So this is a
    distinct typed code carrying the arm and its remedy, and the item id, so the
    surface can say what is missing and the learner can stop looking for a
    mistake they did not make.
    """

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is not None and item.status != "active":
        raise SidecarError(
            "item_retired",
            f"{params.practice_item_id} has been retired and cannot be opened for practice.",
            details={"practice_item_id": params.practice_item_id},
        )
    refusal = unservable_refusal(item) if item is not None else None
    if refusal is not None:
        raise SidecarError(
            UNSERVABLE_ERROR_CODE,
            f"{params.practice_item_id} cannot be opened yet: {refusal['remedy']}.",
            details=refusal,
        )
    # An unknown id still belongs to `practice_item_detail`'s typed not_found;
    # only a KNOWN-but-unrenderable item takes the branch above.
    return practice_item_detail(vault, repository, params.practice_item_id)


def _sections(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("Due now", {"due", "followup"}),
        ("Probe queue", {"probe"}),
        ("Later today", {"later"}),
    ]
    sections = []
    for title, statuses in specs:
        grouped = [item for item in items if item["dueStatus"] in statuses]
        if grouped:
            sections.append({"title": title, "items": grouped})
    return sections


def _nowish() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
