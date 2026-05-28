from __future__ import annotations

from typing import Any

from learnloop.services.scheduler import SchedulerSession, build_due_queue, explain_practice_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import (
    latest_scheduler_explanation_dto,
    practice_item_detail,
    scheduled_item_dto,
    scheduler_explanation_dto,
)
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method


class QueueInput(ParamsModel):
    session_id: str | None = None
    available_minutes: int | None = None
    energy: str | None = None
    limit: int | None = None


class PracticeItemInput(ParamsModel):
    practice_item_id: str


@method("get_today_queue", QueueInput)
def get_today_queue(ctx: SidecarContext, params: QueueInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
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
    return versioned(
        {
            "generated_at": _nowish(),
            "session_id": params.session_id,
            "sections": _sections(dtos),
            "total_items": len(dtos),
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
    vault, repository = ctx.require_vault()
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
