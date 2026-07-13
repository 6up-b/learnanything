"""Goal endpoints: list/report/series, creation (wizard), status review.

Goals are vault-owned YAML (``profile/goals.yaml``); create/update handlers
write the file and reload the vault. Reports and series are derived reads —
see ``services/goal_projection`` and ``services/goal_series``.
"""

from __future__ import annotations

import re
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services.goal_pace import compute_goal_pace
from learnloop.services.goal_projection import GoalReport, goal_report, resolve_goal_scope
from learnloop.services.goal_series import goal_report_series
from learnloop.vault.models import Goal, LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

_GOAL_STATUSES = ("active", "paused", "completed", "expired")

# goal_report_series replays history (checkpoints x per-LO replay); cache per
# (goal, params) and invalidate on any new attempt for the vault.
_series_cache: dict[tuple, list[dict[str, Any]]] = {}

# Bump when GoalSeriesPoint.as_dict gains/loses keys so a hot-reloaded process
# can never serve a stale-shape cached payload.
_SERIES_PAYLOAD_VERSION = 2


class GoalIdInput(ParamsModel):
    goal_id: str


class GoalSeriesInput(ParamsModel):
    goal_id: str
    interval_days: int = 7
    max_points: int = 26


class CreateGoalInput(ParamsModel):
    title: str
    target_recall: float = 0.8
    due_at: str | None = None
    concepts: list[str] = []
    facets: list[str] = []
    exam_enabled: bool = False
    exam_item_count: int = 20


class UpdateGoalStatusInput(ParamsModel):
    goal_id: str
    status: str


class GoalFeasibilityInput(ParamsModel):
    target_recall: float = 0.8
    due_at: str | None = None
    concepts: list[str] = []
    facets: list[str] = []


def _find_goal(vault: LoadedVault, goal_id: str) -> Goal:
    for goal in vault.goals:
        if goal.id == goal_id:
            return goal
    raise SidecarError("goal_not_found", f"Goal {goal_id} does not exist.")


def _latest_exam_dto(repository: Repository, goal: Goal) -> dict[str, Any] | None:
    session = repository.latest_completed_exam_session(goal.id)
    if session is None or not session.get("report"):
        return None
    return {
        "score": session["report"].get("overall_score"),
        "completed_at": session.get("completed_at"),
    }


def _report_dto(
    vault: LoadedVault,
    report: GoalReport,
    *,
    include_facets: bool,
    repository: Repository | None = None,
    goal: Goal | None = None,
) -> dict[str, Any]:
    at_risk = sorted(
        (facet for facet in report.facets if facet.at_risk),
        key=lambda facet: (facet.certified, facet.predicted_at_horizon),
    )
    payload: dict[str, Any] = {
        "on_track_count": report.on_track_count,
        "total": report.total,
        "on_track_fraction": (report.on_track_count / report.total) if report.total else None,
        "at_risk_count": len(at_risk),
        "horizon": report.horizon.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "due_at": report.due_at.strftime("%Y-%m-%dT%H:%M:%SZ") if report.due_at else None,
        "certified_count": report.certified_count,
        "examined_count": report.examined_count,
        "attainment_fraction": report.attainment_fraction,
        "predicted_recall_mean": report.predicted_recall_mean,
        "attempts_remaining": report.attempts_remaining,
        "attempts_remaining_is_partial": report.attempts_remaining_is_partial,
    }
    if repository is not None and goal is not None:
        payload["pace"] = compute_goal_pace(vault, repository, goal, report).as_dict()
        payload["latest_exam"] = _latest_exam_dto(repository, goal)
    if include_facets:
        payload["at_risk"] = [
            {
                "learning_object_id": facet.learning_object_id,
                "learning_object_title": (
                    vault.learning_objects[facet.learning_object_id].title
                    if facet.learning_object_id in vault.learning_objects
                    else facet.learning_object_id
                ),
                "facet_id": facet.facet_id,
                "label": facet.label,
                "current_recall": facet.current_recall,
                "projected_recall": facet.projected_recall,
                "predicted_current": facet.predicted_current,
                "predicted_at_horizon": facet.predicted_at_horizon,
                "evidence_mass": facet.evidence_mass,
                "certified": facet.certified,
                "attempts_to_certify": facet.attempts_to_certify,
            }
            for facet in at_risk
        ]
    return payload


def _goal_dto(
    vault: LoadedVault,
    goal: Goal,
    report: GoalReport | None,
    repository: Repository | None = None,
) -> dict[str, Any]:
    return {
        "id": goal.id,
        "title": goal.title,
        "status": goal.status,
        "priority": goal.priority,
        "target_recall": goal.target_recall,
        "due_at": goal.due_at,
        "facet_scope": {
            "concepts": list(goal.facet_scope.concepts),
            "facets": list(goal.facet_scope.facets),
        },
        "exam": {"enabled": goal.exam.enabled, "item_count": goal.exam.item_count},
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "report": (
            _report_dto(vault, report, include_facets=False, repository=repository, goal=goal)
            if report
            else None
        ),
    }


@method("goals_list", EmptyParams)
def goals_list(ctx: SidecarContext, params: EmptyParams) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    goals = []
    for goal in vault.goals:
        report = goal_report(vault, repository, goal) if goal.status == "active" else None
        goals.append(_goal_dto(vault, goal, report, repository))
    return versioned({"goals": goals})


@method("get_goal_report", GoalIdInput)
def get_goal_report(ctx: SidecarContext, params: GoalIdInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    goal = _find_goal(vault, params.goal_id)
    report = goal_report(vault, repository, goal)
    return versioned(
        {
            "goal": _goal_dto(vault, goal, None),
            "report": _report_dto(
                vault, report, include_facets=True, repository=repository, goal=goal
            ),
        }
    )


@method("get_goal_report_series", GoalSeriesInput)
def get_goal_report_series(ctx: SidecarContext, params: GoalSeriesInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    goal = _find_goal(vault, params.goal_id)
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS n, MAX(created_at) AS latest FROM practice_attempts"
        ).fetchone()
    cache_key = (
        _SERIES_PAYLOAD_VERSION,
        str(vault.root),
        goal.id,
        goal.updated_at,
        params.interval_days,
        params.max_points,
        row["n"],
        row["latest"],
    )
    if cache_key not in _series_cache:
        series = goal_report_series(
            vault,
            repository,
            goal,
            interval_days=params.interval_days,
            max_points=params.max_points,
        )
        _series_cache.clear()  # one vault per process; keep only current shape
        _series_cache[cache_key] = [point.as_dict() for point in series]
    return versioned({"goal_id": goal.id, "series": _series_cache[cache_key]})


@method("goal_feasibility", GoalFeasibilityInput)
def goal_feasibility(ctx: SidecarContext, params: GoalFeasibilityInput) -> dict[str, Any]:
    """Wizard live read: projected standing of a not-yet-created goal."""

    vault, repository = ctx.require_vault()
    now = utc_now_iso()
    transient = Goal(
        id="goal_transient_feasibility",
        title="(feasibility probe)",
        target_recall=params.target_recall,
        due_at=params.due_at,
        facet_scope={"concepts": params.concepts, "facets": params.facets},
        created_at=now,
        updated_at=now,
    )
    report = goal_report(vault, repository, transient)
    scope = resolve_goal_scope(vault, transient, repository)
    covered_concepts = {
        vault.learning_objects[lo_id].concept
        for lo_id in scope
        if lo_id in vault.learning_objects
    }
    uncovered = [concept for concept in params.concepts if concept not in covered_concepts]
    return versioned(
        {
            "scope_facet_count": report.total,
            "on_track_count": report.on_track_count,
            "projected_on_track_fraction": (
                report.on_track_count / report.total if report.total else None
            ),
            "uncovered_concepts": uncovered,
        }
    )


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug or "goal"


@method("create_goal", CreateGoalInput)
def create_goal(ctx: SidecarContext, params: CreateGoalInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    if not params.concepts and not params.facets:
        raise SidecarError("goal_scope_empty", "A goal needs at least one concept or facet.")
    if not (0.0 < params.target_recall <= 1.0):
        raise SidecarError("goal_invalid_target", "target_recall must be in (0, 1].")
    paths = VaultPaths(vault.root, vault.config)
    goals_data = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
    goals = goals_data.setdefault("goals", [])
    existing_ids = {str(goal.get("id")) for goal in goals if isinstance(goal, dict)}
    base = f"goal_{_slugify(params.title)}"
    goal_id = base
    suffix = 2
    while goal_id in existing_ids:
        goal_id = f"{base}_{suffix}"
        suffix += 1
    now = utc_now_iso()
    entry = {
        "id": goal_id,
        "title": params.title,
        "status": "active",
        "priority": 0.5,
        "target_recall": params.target_recall,
        "facet_scope": {"concepts": list(params.concepts), "facets": list(params.facets)},
        "due_at": params.due_at,
        "exam": {"enabled": params.exam_enabled, "item_count": params.exam_item_count},
        "created_at": now,
        "updated_at": now,
    }
    Goal.model_validate(entry)  # fail loudly before touching the file
    goals.append(entry)
    goals_data["schema_version"] = 2
    write_yaml(paths.goals_path, goals_data)
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    goal = _find_goal(vault, goal_id)
    if goal.exam.enabled:
        # Reserve the held-out pool on day one so practice can never
        # contaminate the exam items (coverage gaps surface via exam status).
        from learnloop.services.exam_pool import reserve_exam_pool

        reserve_exam_pool(vault, repository, goal)
    report = goal_report(vault, repository, goal)
    return versioned({"goal": _goal_dto(vault, goal, report, repository)})


@method("update_goal_status", UpdateGoalStatusInput)
def update_goal_status(ctx: SidecarContext, params: UpdateGoalStatusInput) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    if params.status not in _GOAL_STATUSES:
        raise SidecarError("goal_invalid_status", f"status must be one of {_GOAL_STATUSES}.")
    _find_goal(vault, params.goal_id)
    paths = VaultPaths(vault.root, vault.config)
    goals_data = read_yaml(paths.goals_path)
    updated = False
    for goal in goals_data.get("goals", []):
        if isinstance(goal, dict) and goal.get("id") == params.goal_id:
            goal["status"] = params.status
            goal["updated_at"] = utc_now_iso()
            updated = True
    if not updated:
        raise SidecarError("goal_not_found", f"Goal {params.goal_id} does not exist.")
    write_yaml(paths.goals_path, goals_data)
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    goal = _find_goal(vault, params.goal_id)
    report = goal_report(vault, repository, goal) if goal.status == "active" else None
    return versioned({"goal": _goal_dto(vault, goal, report, repository)})
