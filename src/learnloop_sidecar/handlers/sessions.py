from __future__ import annotations

import json
from typing import Any

from learnloop_sidecar.context import SidecarContext, session_snapshot
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class SessionStartInput(ParamsModel):
    energy: str | None = None
    sleep_quality: float | None = None
    available_minutes: int | None = None
    notes_md_path: str | None = None


class SessionIdInput(ParamsModel):
    session_id: str


class SessionCheckpointInput(ParamsModel):
    session_id: str
    current_practice_item_id: str | None = None
    current_answer: str | None = None
    hints_used: int | None = None
    submission_id: str | None = None
    focus_block_state: dict[str, Any] | None = None
    pending_grading_proposal: dict[str, Any] | None = None
    readiness: dict[str, Any] | None = None


@method("start_session", SessionStartInput)
def start_session(ctx: SidecarContext, params: SessionStartInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    from learnloop.goals.forecast_ledger import issue_goal_forecasts, resolve_due_forecasts

    resolve_due_forecasts(repository)
    issue_goal_forecasts(vault, repository)
    session_id = repository.create_session(
        energy=params.energy,
        sleep_quality=params.sleep_quality,
        available_minutes=params.available_minutes,
        notes_md_path=params.notes_md_path,
    )
    repository.end_open_sessions_except(session_id)
    snapshot = session_snapshot(repository, session_id)
    if snapshot is None:
        raise SidecarError("internal", "Session was created but could not be read.")
    return snapshot


@method("get_session", SessionIdInput)
def get_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    snapshot = session_snapshot(repository, params.session_id)
    if snapshot is None:
        raise SidecarError("not_found", f"Session {params.session_id} was not found.")
    return snapshot


@method("update_session_checkpoint", SessionCheckpointInput)
def update_session_checkpoint(ctx: SidecarContext, params: SessionCheckpointInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    patch_checkpoint(repository, params)
    return {"ok": True}


@method("clear_session_checkpoint", SessionIdInput)
def clear_session_checkpoint(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    _require_open_session(repository, params.session_id)
    return {"cleared": repository.clear_session_checkpoint(params.session_id)}


@method("end_session", SessionIdInput)
def end_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    row = repository.end_session(params.session_id)
    if row is None:
        raise SidecarError("not_found", f"Session {params.session_id} was not found.")
    repository.clear_session_checkpoint(params.session_id)
    counts = repository.session_attempt_counts(params.session_id) or {"attempts_recorded": 0, "items_reviewed": 0}
    from learnloop.learner.session_learning_diff import session_learning_diff

    learning_diff = session_learning_diff(vault, repository, params.session_id)
    cold_checks = _session_cold_checks(repository, params.session_id)
    return versioned(
        {
            "session_id": row["id"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "attempts_recorded": counts["attempts_recorded"],
            "items_reviewed": counts["items_reviewed"],
            "followups_queued": _session_followups_queued(repository, params.session_id),
            # Cold checks are the session's only unassisted repair evidence, and
            # they are counted SEPARATELY from what passed: "2 answered, 1 held"
            # is the honest shape, "1 repair confirmed" alone hides the other.
            "cold_checks_completed": cold_checks["completed"],
            "cold_checks_passed": cold_checks["passed"],
            "streak": repository.session_day_streak(),
            **learning_diff,
        }
    )


def patch_checkpoint(repository, params: SessionCheckpointInput) -> None:
    _require_open_session(repository, params.session_id)
    fields = params.model_fields_set
    existing = repository.fetch_session_checkpoint(params.session_id) or {}
    focus = _copy_mapping(existing.get("focus_block_state"))
    if "focus_block_state" in fields:
        focus = _copy_mapping(params.focus_block_state)

    if "hints_used" in fields:
        hints_used = 0 if params.hints_used is None else params.hints_used
        if hints_used < 0:
            raise SidecarError("validation_error", "hintsUsed must be non-negative.", details={"field": "hintsUsed"})
        focus = _with_hints_used(focus, hints_used)

    if "submission_id" in fields:
        focus = _with_submission_id(focus, params.submission_id)

    repository.update_session_checkpoint(
        params.session_id,
        current_practice_item_id=_merged_value(existing, params, fields, "current_practice_item_id"),
        current_answer=_merged_value(existing, params, fields, "current_answer"),
        focus_block_state=focus,
        pending_grading_proposal=_merged_value(existing, params, fields, "pending_grading_proposal"),
        readiness=_merged_value(existing, params, fields, "readiness"),
    )


def _require_open_session(repository, session_id: str) -> dict[str, Any]:
    session = repository.fetch_session(session_id)
    if session is None:
        raise SidecarError("not_found", f"Session {session_id} was not found.")
    if session["ended_at"] is not None:
        raise SidecarError("validation_error", f"Session {session_id} has ended.")
    return session


def _merged_value(existing: dict[str, Any], params: SessionCheckpointInput, fields: set[str], name: str):
    if name in fields:
        return getattr(params, name)
    return existing.get(name)


def _copy_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _with_hints_used(focus: dict[str, Any] | None, hints_used: int) -> dict[str, Any]:
    payload = dict(focus or {})
    practice = payload.get("practice")
    if not isinstance(practice, dict):
        practice = {}
    else:
        practice = dict(practice)
    practice["hintsUsed"] = hints_used
    payload["practice"] = practice
    return payload


def _with_submission_id(focus: dict[str, Any] | None, submission_id: str | None) -> dict[str, Any]:
    """Store the current attempt's stable retry key in the practice envelope.

    The checkpoint already has a JSON focus-block field, so this is additive
    and needs no schema migration.  Clearing or switching a legacy client must
    not leave a previous item's key behind.
    """

    payload = dict(focus or {})
    practice = payload.get("practice")
    if not isinstance(practice, dict):
        practice = {}
    else:
        practice = dict(practice)
    if submission_id is None:
        practice.pop("submissionId", None)
        practice.pop("submission_id", None)
    else:
        stable_id = submission_id.strip()
        if not stable_id:
            raise SidecarError(
                "validation_error",
                "submissionId must not be blank.",
                details={"field": "submissionId"},
            )
        practice["submissionId"] = stable_id
        practice.pop("submission_id", None)
    payload["practice"] = practice
    return payload


def _session_cold_checks(repository, session_id: str) -> dict[str, int]:
    """Repair cold checks this session spent, and how many of them passed.

    Same window convention as ``_session_followups_queued`` (attempt timestamps
    between the session's start and end). A cold task is joined to the attempt
    that CONSUMED it, so a check scheduled long ago counts for the session that
    actually answered it. ``passed`` reads the recorded outcome, not the grade:
    an outcome row is written by the cold verification lane, and its absence
    means the check produced no verdict rather than a failure.
    """

    session = repository.fetch_session(session_id)
    if session is None:
        return {"completed": 0, "passed": 0}
    started_at = session["started_at"]
    ended_at = session["ended_at"] or started_at
    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT o.outcome AS outcome
            FROM followup_tasks t
            JOIN practice_attempts a ON a.id = t.consumed_attempt_id
            LEFT JOIN causal_cold_outcomes o ON o.followup_task_id = t.id
            WHERE t.kind = 'cold_retry'
              AND t.status = 'consumed'
              AND a.created_at >= ? AND a.created_at <= ?
            """,
            (started_at, ended_at),
        ).fetchall()
    return {
        "completed": len(rows),
        "passed": sum(1 for row in rows if row["outcome"] == "cold_success"),
    }


def _session_followups_queued(repository, session_id: str) -> int:
    session = repository.fetch_session(session_id)
    if session is None:
        return 0
    started_at = session["started_at"]
    ended_at = session["ended_at"] or started_at
    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT s.triggered_actions_json
            FROM attempt_surprise s
            JOIN practice_attempts a ON a.id = s.attempt_id
            WHERE a.created_at >= ? AND a.created_at <= ?
              AND s.triggered_actions_json IS NOT NULL
            """,
            (started_at, ended_at),
        ).fetchall()
    count = 0
    for row in rows:
        try:
            actions = json.loads(row["triggered_actions_json"] or "[]")
        except json.JSONDecodeError:
            continue
        count += sum(
            1
            for action in actions
            if isinstance(action, str)
            and (
                action.startswith("intervention_followup:queued:")
                or action.startswith("negative_surprise_followup:")
            )
        )
    return count
