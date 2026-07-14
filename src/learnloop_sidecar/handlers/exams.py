"""Practice-exam endpoints: status, start, answer, finish.

The exam services are provider-agnostic (they take a resolved grade); this
handler resolves grading through the configured AI provider the same way
practice submission does. Exams have no self-grade fallback UI — an exam
answer graded by its own taker is not a held-out measurement — so grading
requires a ready AI provider.
"""

from __future__ import annotations

from typing import Any

from learnloop.ids import new_ulid
from learnloop.services.attempts import _resolved_codex_grade
from learnloop.services.exam_pool import reserve_exam_pool
from learnloop.services.exam_session import (
    ExamSessionError,
    exam_availability,
    exam_report,
    finish_exam,
    record_exam_answer,
    start_exam,
)
from learnloop.services.goal_projection import resolve_goal_scope
from learnloop.services.grading import (
    GradingValidationError,
    build_grading_context,
    validate_codex_grading_proposal,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import ready_grading_provider
from learnloop_sidecar.handlers.goals import GoalIdInput, _find_goal
from learnloop_sidecar.registry import method
from learnloop_sidecar.dto import EmptyParams


class StartExamInput(ParamsModel):
    goal_id: str


class SubmitExamAnswerInput(ParamsModel):
    session_id: str
    practice_item_id: str
    answer_md: str


class FinishExamInput(ParamsModel):
    session_id: str


@method("get_answer_calibration")
def get_answer_calibration(
    ctx: SidecarContext, _params: EmptyParams
) -> dict[str, Any]:
    from learnloop.services.exam_calibration import calibration_report

    vault, repository = ctx.require_vault()
    return versioned(calibration_report(vault, repository))


@method("get_exam_status", GoalIdInput)
def get_exam_status(ctx: SidecarContext, params: GoalIdInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    goal = _find_goal(vault, params.goal_id)
    uncovered: list[str] = []
    pool_count = 0
    if goal.exam.enabled and goal.status == "active":
        # Idempotent: reserves on first ask (covers goals created before the
        # exam feature or via hand-edited YAML), returns the existing pool after.
        report = reserve_exam_pool(vault, repository, goal)
        uncovered = list(report.uncovered_facets)
        pool_count = len(report.reserved_item_ids)
    availability = exam_availability(vault, repository, goal)
    return versioned(
        {
            "goal_id": goal.id,
            "in_window": availability["in_window"],
            "days_until_due": availability["days_until_due"],
            "past_due_grace": availability["past_due_grace"],
            "existing_session_id": availability["existing_session_id"],
            "pool_item_count": pool_count or availability["pool_item_count"],
            "uncovered_facets": uncovered,
        }
    )


def _session_snapshot(ctx: SidecarContext, view: dict[str, Any]) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    item_order: list[str] = list(view["item_order"])
    answered = [
        row["practice_item_id"]
        for row in repository.exam_answers(view["session_id"])
        if row.get("grade") is not None
    ]
    items = []
    for index, item_id in enumerate(item_order):
        item = vault.practice_items.get(item_id)
        items.append(
            {
                "practice_item_id": item_id,
                "index": index,
                "total": len(item_order),
                "prompt": item.prompt if item is not None else "(missing item)",
                "practice_mode": item.practice_mode if item is not None else "short_answer",
            }
        )
    return versioned(
        {
            "session_id": view["session_id"],
            "goal_id": view["goal_id"],
            "status": view["status"],
            "items": items,
            "answered_item_ids": answered,
        }
    )


@method("start_exam", StartExamInput)
def start_exam_handler(ctx: SidecarContext, params: StartExamInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    goal = _find_goal(vault, params.goal_id)
    if goal.exam.enabled and goal.status == "active":
        reserve_exam_pool(vault, repository, goal)
    try:
        view = start_exam(vault, repository, params.goal_id)
    except ExamSessionError as exc:
        raise SidecarError("exam_start_failed", str(exc)) from exc
    return _session_snapshot(ctx, view)


@method("submit_exam_answer", SubmitExamAnswerInput)
def submit_exam_answer(ctx: SidecarContext, params: SubmitExamAnswerInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("validation_error", f"Unknown practice item {params.practice_item_id}")
    provider_name, runtime, client = ready_grading_provider(
        vault, override=ctx.grading_provider_override
    )
    if provider_name == "manual" or not runtime.ready or client is None:
        raise SidecarError(
            "exam_grading_unavailable",
            "Exam answers need an AI grading provider (self-grading a held-out exam "
            "would not be a measurement). Configure a provider and retry.",
            retryable=True,
        )
    grading_attempt_id = new_ulid()
    context = build_grading_context(
        vault,
        item,
        attempt_id=grading_attempt_id,
        learner_answer_md=params.answer_md,
    )
    try:
        proposal = client.run_grading_proposal(context)
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=grading_attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=params.answer_md,
        )
    except GradingValidationError as exc:
        raise SidecarError("exam_grading_failed", str(exc)) from exc
    except (TimeoutError, Exception) as exc:  # provider transport failures
        if isinstance(exc, SidecarError):
            raise
        raise SidecarError(
            "exam_grading_unavailable",
            f"AI grading failed: {exc}. Retry when the provider is available.",
            retryable=True,
        ) from exc
    resolved = _resolved_codex_grade(validated, agent_run_id=None, clock=None)
    try:
        result = record_exam_answer(
            vault,
            repository,
            params.session_id,
            params.practice_item_id,
            answer_md=params.answer_md,
            resolved_grade=resolved,
        )
    except ExamSessionError as exc:
        raise SidecarError("exam_answer_failed", str(exc)) from exc
    rubric = vault.rubric_for_item(item)
    return versioned(
        {
            "session_id": result["session_id"],
            "practice_item_id": result["practice_item_id"],
            "correctness": result["correctness"],
            "score": result["rubric_score"],
            "max_points": rubric.max_points if rubric is not None else 4,
        }
    )


@method("finish_exam", FinishExamInput)
def finish_exam_handler(ctx: SidecarContext, params: FinishExamInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        report = finish_exam(vault, repository, params.session_id)
    except ExamSessionError as exc:
        raise SidecarError("exam_finish_failed", str(exc)) from exc
    return versioned(_report_dto(vault, repository, report))


def _report_dto(vault, repository, report: dict[str, Any]) -> dict[str, Any]:
    items = report.get("items", [])
    predicted_values = [
        entry["predicted_correctness"]
        for entry in items
        if entry.get("predicted_correctness") is not None
    ]
    goal = next((g for g in vault.goals if g.id == report.get("goal_id")), None)
    facet_lo: dict[str, str] = {}
    if goal is not None:
        for lo_id, facets in resolve_goal_scope(vault, goal, repository).items():
            for facet in facets:
                facet_lo.setdefault(facet, lo_id)
    return {
        "session_id": report["session_id"],
        "goal_id": report.get("goal_id"),
        "score_fraction": report.get("overall_score"),
        "predicted_score_fraction": (
            sum(predicted_values) / len(predicted_values) if predicted_values else None
        ),
        "brier": report.get("brier"),
        "per_facet": [
            {
                "facet_id": facet["facet_id"],
                "learning_object_id": facet_lo.get(facet["facet_id"], ""),
                "predicted_recall": facet.get("projected_recall"),
                "observed_correctness": facet.get("actual_recall"),
            }
            for facet in report.get("facets", [])
        ],
        "item_outcomes": [
            {
                "practice_item_id": entry["practice_item_id"],
                "predicted_correctness": entry.get("predicted_correctness"),
                "observed_correctness": entry.get("correctness"),
            }
            for entry in items
        ],
    }
