"""Daily-loop DL1 RPCs: the finite plan (``spec_daily_loop_v1.md`` §6, §7, §12).

``get_daily_plan``, ``set_plan_minutes``, ``next_plan_item``,
``plan_reading_ended``, ``plan_keep_going``, ``plan_more_new``,
``plan_learner_pick`` and ``get_today_headline``. While the plan is off (a
pre-``mvp-0.12`` vault or ``plan.enabled = false``) every one of them answers
``enabled: false`` without building a queue or writing a row, and Today, Start
and ``get_today_queue`` are DL0's (G1). Never phone-allowed (mobile M2a adds
them to its allowlist later).
"""

from __future__ import annotations

from typing import Any, Literal

from learnloop.daily_plan.engine import (
    PlanEnv,
    PlanInactiveError,
    advance_with_context,
    keep_going,
    learner_pick,
    more_new,
    plan_active,
    reading_ended,
    set_minutes,
    stop_today,
)
from learnloop.daily_plan.headline import today_headline
from learnloop.daily_plan.reentry import ReentryGap, reentry_panel
from learnloop.daily_plan.view import disabled_view, plan_view
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.goals import _nearest_active_goal
from learnloop_sidecar.handlers.queue import prepare_queue_build
from learnloop_sidecar.handlers.teach_back import filter_unready_teach_back_items
from learnloop_sidecar.registry import method

#: The DL1 RPCs (pinned never phone-allowed in tests/test_mobile_allowlist.py).
DAILY_PLAN_RPCS = (
    "get_daily_plan",
    "set_plan_minutes",
    "next_plan_item",
    "plan_reading_ended",
    "plan_keep_going",
    "plan_more_new",
    "plan_learner_pick",
    "get_today_headline",
)


class PlanSessionInput(ParamsModel):
    session_id: str | None = None


class NextPlanItemInput(ParamsModel):
    session_id: str | None = None
    #: Record the step as served (the learner opened it). Without it this is
    #: the prefetch made while feedback shows (§6.5).
    serve: bool = False
    skip_practice_item_id: str | None = None


class PlanMinutesInput(ParamsModel):
    minutes: int
    session_id: str | None = None


class PlanReadingEndedInput(ParamsModel):
    outcome: Literal["left_reader", "skipped", "section_completed"]
    session_id: str | None = None


class PlanKeepGoingInput(ParamsModel):
    session_id: str | None = None
    #: "Done" on the plan: stop for today instead of extending it.
    stop: bool = False


class PlanMoreNewInput(ParamsModel):
    session_id: str | None = None
    #: Without it only the trade-off is returned ("adds about N min/day").
    confirm: bool = False


class PlanLearnerPickInput(ParamsModel):
    practice_item_id: str
    session_id: str | None = None


def _env(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> PlanEnv:
    def eligible(minutes: float) -> list[Any]:
        # Today's own build: the same scheduler call, teach-back filter and
        # offer finalization as get_today_queue, so a served plan item carries
        # the candidate id of the slate that ranked it.
        queue = build_due_queue(
            vault,
            repository,
            session=SchedulerSession(session_id=session_id, available_minutes=int(round(minutes))),
            limit=None,
        )
        slate_id = queue[0].scheduler_slate_id if queue else None
        queue = filter_unready_teach_back_items(
            vault, queue, grading_provider_override=ctx.grading_provider_override
        )
        repository.finalize_scheduler_offer(
            slate_id, [item.scheduler_candidate_id for item in queue if item.scheduler_candidate_id]
        )
        return queue

    return PlanEnv(vault=vault, repository=repository, session_id=session_id, eligible=eligible)


def _require(ctx: SidecarContext, session_id: str | None) -> tuple[Any, Any, PlanEnv] | None:
    vault, repository = ctx.require_vault()
    if not plan_active(vault):
        return None
    prepare_queue_build(ctx, vault, repository, session_id)
    return vault, repository, _env(ctx, vault, repository, session_id)


def _off(ctx: SidecarContext) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    reason = "plan_disabled" if not bool(vault.config.plan.enabled) else "algorithm_version"
    return versioned(disabled_view(vault, reason=reason))


def _view(env: PlanEnv, record: Any, step: dict[str, Any] | None, context: Any) -> dict[str, Any]:
    panel = None
    if record.kind == "reentry":
        # The break as measured when the re-entry plan was built: practising
        # inside it must not shrink the "welcome back" it opened with.
        stored = record.split.get("reentry_gap") or {}
        gap = ReentryGap(
            due=True,
            gap_days=int(stored.get("gap_days") or 0),
            threshold_days=int(stored.get("threshold_days") or env.vault.config.hypothesis.reentry_gap_days),
            last_activity_at=stored.get("last_activity_at"),
        )
        panel = reentry_panel(
            env.vault,
            env.repository,
            now=env.now(),
            gap=gap,
            goal=_nearest_active_goal(env.vault),
        ).as_dict()
        panel["minutes"] = round(record.budget, 4)
        panel["items_cap"] = record.split.get("items_cap")
        panel["planned_items"] = record.item_count()
        panel["planned_minutes"] = round(record.minutes_planned(), 4)
    return plan_view(
        env,
        record,
        context=context,
        next_step=step,
        reentry_panel=panel,
        streak=env.repository.session_day_streak(),
    )


def _current_view(env: PlanEnv) -> dict[str, Any]:
    record, step, context = advance_with_context(env, serve=False)
    return _view(env, record, step, context)


@method("get_daily_plan", PlanSessionInput)
def get_daily_plan(ctx: SidecarContext, params: PlanSessionInput) -> dict[str, Any]:
    """Today's plan (built on first read of the day), its split, blocks and next step."""

    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    return versioned(_current_view(env))


@method("set_plan_minutes", PlanMinutesInput)
def set_plan_minutes(ctx: SidecarContext, params: PlanMinutesInput) -> dict[str, Any]:
    """A minutes chip (§6.6): remembered, and the remaining blocks re-planned."""

    if params.minutes <= 0 or params.minutes > 600:
        raise SidecarError("validation_error", "minutes must be between 1 and 600.", details={"field": "minutes"})
    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    set_minutes(env, int(params.minutes))
    return versioned(_current_view(env))


@method("next_plan_item", NextPlanItemInput)
def next_plan_item(ctx: SidecarContext, params: NextPlanItemInput) -> dict[str, Any]:
    """The next step: ``{"kind": "item" | "reading" | "done", ...}`` (§6.10 typed steps)."""

    if params.serve and not params.session_id:
        raise SidecarError("validation_error", "serving a plan item needs a session.", details={"field": "sessionId"})
    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    record, step, context = advance_with_context(
        env, serve=params.serve, skip_practice_item_id=params.skip_practice_item_id
    )
    return versioned({"enabled": True, "step": step, **_view(env, record, step, context)})


@method("plan_reading_ended", PlanReadingEndedInput)
def plan_reading_ended(ctx: SidecarContext, params: PlanReadingEndedInput) -> dict[str, Any]:
    """End the current reading block (left the reader, skipped, or completed)."""

    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    reading_ended(env, params.outcome)
    record, step, context = advance_with_context(env, serve=False)
    return versioned({"enabled": True, "step": step, **_view(env, record, step, context)})


@method("plan_keep_going", PlanKeepGoingInput)
def plan_keep_going(ctx: SidecarContext, params: PlanKeepGoingInput) -> dict[str, Any]:
    """Keep going (§6.5): one more block of minutes; or "Done" (``stop``)."""

    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    if params.stop:
        stop_today(env)
    else:
        keep_going(env)
    return versioned(_current_view(env))


@method("plan_more_new", PlanMoreNewInput)
def plan_more_new(ctx: SidecarContext, params: PlanMoreNewInput) -> dict[str, Any]:
    """"More new material" (§6.3): the trade-off first, then a labelled extension."""

    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    _record, preview = more_new(env, confirm=params.confirm)
    return versioned({"enabled": True, "preview": preview, **_current_view(env)})


@method("plan_learner_pick", PlanLearnerPickInput)
def plan_learner_pick(ctx: SidecarContext, params: PlanLearnerPickInput) -> dict[str, Any]:
    """Open an item from the full list: a one-item learner-pick block (L3, G12)."""

    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    try:
        record, step = learner_pick(env, params.practice_item_id)
    except KeyError as exc:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.") from exc
    return versioned({"enabled": True, "step": step, **_current_view(env)})


@method("get_today_headline", PlanSessionInput)
def get_today_headline(ctx: SidecarContext, _params: PlanSessionInput) -> dict[str, Any]:
    """The optional one-line headline (§6.7, D7). Read-only."""

    vault, repository = ctx.require_vault()
    if not plan_active(vault) or not bool(vault.config.plan.headline):
        return versioned({"enabled": False})
    env = PlanEnv(vault=vault, repository=repository)
    headline = today_headline(vault, repository, now=env.now())
    classes = headline.pop("learning_object_classes")
    return versioned(
        {
            "enabled": True,
            **headline,
            # A list, not a mapping: LO ids must not be camel-cased on the way out.
            "learning_objects": [
                {"learning_object_id": lo_id, "class": value} for lo_id, value in sorted(classes.items())
            ],
        }
    )


__all__ = ["DAILY_PLAN_RPCS", "PlanInactiveError"]
