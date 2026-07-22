"""Exam session: one sitting of a goal's held-out practice exam.

The exam is an honest test of the mastery model's projections, so ordering
matters. ``start_exam`` **freezes the prediction snapshot FIRST** — per pooled
item the model's predicted correctness, and per scope facet the current and
projected-at-due recall — BEFORE any answer is graded and any evidence lands.
Answers are stored per item as the learner works (``record_exam_answer``, no
mastery writes), and applied through the standard attempt pipeline only at
``finish_exam``, which then computes and persists the report (overall score,
per-facet predicted vs actual, session Brier), marks the session completed, and
releases the goal's exam pool (those items are contaminated now and rejoin
practice).

Grading resolution happens in the caller (sidecar / CLI) so this service stays
provider-agnostic: ``record_exam_answer`` takes an already-resolved
``ResolvedGrade``.
"""

from __future__ import annotations

from datetime import UTC, timedelta
from typing import Any

from learnloop.clock import Clock, FrozenClock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.exam_pool import release_exam_pool
from learnloop.services.facet_state_reader import facet_recall_states_for_lo
from learnloop.services.goal_projection import goal_report, resolve_goal_scope
from learnloop.services.selection_rewards import (
    ability_vector,
    item_demand_vector,
    predicted_correctness_from_vectors,
)
from learnloop.vault.models import Goal, LoadedVault

# Exam availability window: the last 7 days before due_at through 7 days after.
_WINDOW_DAYS = 7


class ExamSessionError(ValueError):
    pass


def _goal(vault: LoadedVault, goal_id: str) -> Goal:
    for goal in vault.goals:
        if goal.id == goal_id:
            return goal
    raise ExamSessionError(f"Unknown goal {goal_id}")


# ----------------------------------------------------------------------
# Prediction freeze
# ----------------------------------------------------------------------


def _predicted_correctness_for_item(vault: LoadedVault, repository: Repository, item) -> float:
    learning_object = vault.learning_object_for_item(item)
    if learning_object is None:
        return 0.5
    mastery = repository.mastery_state(learning_object.id)
    facet_states = facet_recall_states_for_lo(vault, repository, learning_object.id)
    active_errors = repository.active_errors_by_learning_object(learning_object.id)
    ability = ability_vector(
        learning_object.id, mastery, facet_states, active_errors, facet_aliases=vault.facet_aliases
    )
    demand = item_demand_vector(
        vault, item, learning_object, repository.practice_item_quality_state(item.id)
    )
    return predicted_correctness_from_vectors(
        ability, demand, vault.config.recall_coverage.facet_blend_evidence_count
    )


def _facet_projection_snapshot(vault, item, projection_by_key, scope, target_recall) -> dict[str, Any]:
    scope_facets = scope.get(item.learning_object_id, set())
    snapshot: dict[str, Any] = {}
    for facet in item.evidence_facets:
        facet_id = vault.canonical_facet_id(str(facet))
        if facet_id not in scope_facets:
            continue
        projection = projection_by_key.get((item.learning_object_id, facet_id))
        snapshot[facet_id] = {
            "current_recall": projection.current_recall if projection is not None else None,
            "projected_recall": projection.projected_recall if projection is not None else None,
            "target_recall": target_recall,
            "label": projection.label if projection is not None else "unexamined",
        }
    return snapshot


def start_exam(
    vault: LoadedVault,
    repository: Repository,
    goal_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Open an exam session for a goal, freezing predictions first.

    Idempotent: an existing ``in_progress`` session for the goal is returned as
    is (predictions are never re-frozen).
    """

    clock = clock or SystemClock()
    goal = _goal(vault, goal_id)

    existing = repository.exam_session_in_progress_for_goal(goal_id)
    if existing is not None:
        return _session_view(repository, existing["id"], already_started=True)

    pooled = repository.reserved_exam_pool_items(goal_id)
    if not pooled:
        raise ExamSessionError(
            f"Goal {goal_id} has no reserved exam pool; call reserve_exam_pool first."
        )
    item_order = [row["practice_item_id"] for row in pooled]

    now_iso = utc_now_iso(clock)
    session_id = new_ulid()

    # Freeze the goal-projection snapshot BEFORE any evidence lands.
    report = goal_report(vault, repository, goal, clock=clock)
    projection_by_key = {
        (projection.learning_object_id, projection.facet_id): projection
        for projection in report.facets
    }
    scope = resolve_goal_scope(vault, goal, repository)

    prediction_rows: list[dict[str, Any]] = []
    for item_id in item_order:
        item = vault.practice_items.get(item_id)
        if item is None:
            continue
        predicted = _predicted_correctness_for_item(vault, repository, item)
        prediction_rows.append(
            {
                "id": new_ulid(),
                "session_id": session_id,
                "practice_item_id": item_id,
                "predicted_correctness": predicted,
                "facet_projection": _facet_projection_snapshot(
                    vault, item, projection_by_key, scope, goal.target_recall
                ),
                "created_at": now_iso,
            }
        )

    repository.insert_exam_session(
        {
            "id": session_id,
            "goal_id": goal_id,
            "status": "in_progress",
            "item_order": item_order,
            "report": None,
            "started_at": now_iso,
            "updated_at": now_iso,
            "completed_at": None,
        }
    )
    repository.insert_exam_predictions(prediction_rows)
    return _session_view(repository, session_id, already_started=False)


# ----------------------------------------------------------------------
# Answers
# ----------------------------------------------------------------------


def record_exam_answer(
    vault: LoadedVault,
    repository: Repository,
    session_id: str,
    practice_item_id: str,
    *,
    answer_md: str,
    resolved_grade: ResolvedGrade,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Store one graded answer on the session (no mastery writes yet)."""

    session = repository.exam_session(session_id)
    if session is None:
        raise ExamSessionError(f"Unknown exam session {session_id}")
    if session["status"] != "in_progress":
        raise ExamSessionError(f"Exam session {session_id} is {session['status']}, not in_progress")
    if practice_item_id not in session["item_order"]:
        raise ExamSessionError(f"{practice_item_id} is not in exam session {session_id}")
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        raise ExamSessionError(f"Unknown practice item {practice_item_id}")
    rubric = vault.rubric_for_item(item)
    max_points = rubric.max_points if rubric is not None else 4
    correctness = resolved_grade.rubric_score / max(max_points, 1)
    repository.upsert_exam_answer(
        {
            "session_id": session_id,
            "practice_item_id": practice_item_id,
            "answer_md": answer_md,
            "rubric_score": resolved_grade.rubric_score,
            "correctness": correctness,
            "grade": _grade_to_dict(resolved_grade),
        },
        clock=clock,
    )
    _dual_write_exam_grade(
        vault,
        repository,
        item=item,
        rubric=rubric,
        max_points=max_points,
        answer_md=answer_md,
        resolved_grade=resolved_grade,
        session_id=session_id,
        clock=clock,
    )
    return {
        "session_id": session_id,
        "practice_item_id": practice_item_id,
        "rubric_score": resolved_grade.rubric_score,
        "correctness": correctness,
    }


def _dual_write_exam_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: Any,
    rubric: Any,
    max_points: int,
    answer_md: str,
    resolved_grade: ResolvedGrade,
    session_id: str,
    clock: Clock | None = None,
) -> None:
    """P0.2 dual-write for exam answers (§4.1, §7.2). Fail-safe (§7.3): appends a
    raw grade event + interpretation on an assessment-purpose administration
    alongside the legacy exam_answer summary; never raises into the legacy path."""

    try:
        from learnloop.services.grade_resolution import record_grade_dual_write

        criterion_max = (
            {c.id: c.points for c in rubric.criteria} if rubric is not None else None
        )
        record_grade_dual_write(
            vault,
            repository,
            item=item,
            purpose="assessment",
            grading_source="codex",
            attempt_id=f"exam::{session_id}::{item.id}",
            response_text=answer_md,
            rubric_score=resolved_grade.rubric_score,
            max_points=max_points,
            grader_confidence=resolved_grade.grader_confidence,
            has_fatal=bool(resolved_grade.fatal_errors),
            criterion_points=resolved_grade.criterion_points,
            criterion_max=criterion_max,
            domain=getattr(item, "learning_object_id", None),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - fail-safe dual-write (§7.3)
        pass


# ----------------------------------------------------------------------
# Finish + report
# ----------------------------------------------------------------------


def finish_exam(
    vault: LoadedVault,
    repository: Repository,
    session_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Apply every answered item as an ``exam_attempt`` and persist the report.

    Idempotent by session id: once completed, the stored report is returned and
    no attempts are re-applied.
    """

    clock = clock or SystemClock()
    session = repository.exam_session(session_id)
    if session is None:
        raise ExamSessionError(f"Unknown exam session {session_id}")
    if session["status"] == "completed" and session.get("report") is not None:
        return session["report"]

    goal = _goal(vault, session["goal_id"])
    answers = [answer for answer in repository.exam_answers(session_id) if answer.get("grade") is not None]

    # Apply answered items as exam_attempts, spaced seconds apart at finish time
    # (same deterministic backdating shape exam_seeding uses).
    base_instant = clock.now().astimezone(UTC).replace(microsecond=0)
    for index, answer in enumerate(answers):
        if answer.get("attempt_id"):
            continue
        item_id = answer["practice_item_id"]
        attempt_clock = FrozenClock(base_instant + timedelta(seconds=index))
        grade = _grade_from_dict(answer["grade"])
        draft = AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md=answer.get("answer_md") or "",
            attempt_type="exam_attempt",
            hints_used=0,
        )
        attempt_id = new_ulid()
        apply_attempt(
            vault,
            repository,
            ApplyAttemptInput(draft=draft, attempt_id=attempt_id, grade=grade),
            clock=attempt_clock,
        )
        repository.set_exam_answer_attempt_id(session_id, item_id, attempt_id)

    report = _compute_report(vault, repository, session, goal)
    completed_at = utc_now_iso(clock)
    repository.update_exam_session(
        session_id, status="completed", report=report, completed_at=completed_at, clock=clock
    )
    release_exam_pool(repository, session["goal_id"], clock=clock)
    return report


def _compute_report(vault: LoadedVault, repository: Repository, session, goal) -> dict[str, Any]:
    predictions = {row["practice_item_id"]: row for row in repository.exam_predictions(session["id"])}
    answers = {row["practice_item_id"]: row for row in repository.exam_answers(session["id"])}

    items: list[dict[str, Any]] = []
    squared_errors: list[float] = []
    correctness_values: list[float] = []
    # facet_id -> {"projected": [...], "current": ..., "target": ..., "outcomes": [...]}
    facet_acc: dict[str, dict[str, Any]] = {}

    for item_id in session["item_order"]:
        prediction = predictions.get(item_id)
        answer = answers.get(item_id)
        if answer is None or answer.get("correctness") is None:
            continue
        correctness = float(answer["correctness"])
        correctness_values.append(correctness)
        predicted = float(prediction["predicted_correctness"]) if prediction is not None else None
        if predicted is not None:
            squared_errors.append((predicted - correctness) ** 2)
        items.append(
            {
                "practice_item_id": item_id,
                "predicted_correctness": predicted,
                "correctness": correctness,
                "rubric_score": answer.get("rubric_score"),
                "attempt_id": answer.get("attempt_id"),
            }
        )
        facet_projection = (prediction or {}).get("facet_projection") or {}
        for facet_id, snapshot in facet_projection.items():
            acc = facet_acc.setdefault(
                facet_id,
                {
                    "projected_recall": snapshot.get("projected_recall"),
                    "current_recall": snapshot.get("current_recall"),
                    "target_recall": snapshot.get("target_recall"),
                    "label": snapshot.get("label"),
                    "outcomes": [],
                },
            )
            acc["outcomes"].append(correctness)

    facets: list[dict[str, Any]] = []
    for facet_id in sorted(facet_acc):
        acc = facet_acc[facet_id]
        outcomes = acc["outcomes"]
        actual = sum(outcomes) / len(outcomes) if outcomes else None
        projected = acc["projected_recall"]
        facets.append(
            {
                "facet_id": facet_id,
                "current_recall": acc["current_recall"],
                "projected_recall": projected,
                "target_recall": acc["target_recall"],
                "actual_recall": actual,
                "n_items": len(outcomes),
                "met_target": (actual is not None and acc["target_recall"] is not None and actual >= acc["target_recall"]),
                "projection_error": (projected - actual) if (projected is not None and actual is not None) else None,
            }
        )

    overall_score = sum(correctness_values) / len(correctness_values) if correctness_values else None
    brier = sum(squared_errors) / len(squared_errors) if squared_errors else None
    return {
        "session_id": session["id"],
        "goal_id": goal.id,
        "target_recall": goal.target_recall,
        "item_count": len(session["item_order"]),
        "answered_count": len(correctness_values),
        "overall_score": overall_score,
        "brier": brier,
        "items": items,
        "facets": facets,
    }


def exam_report(vault: LoadedVault, repository: Repository, session_id: str) -> dict[str, Any]:
    """Return the persisted report (completed) or a live progress view."""

    session = repository.exam_session(session_id)
    if session is None:
        raise ExamSessionError(f"Unknown exam session {session_id}")
    if session["status"] == "completed" and session.get("report") is not None:
        return session["report"]
    view = _session_view(repository, session_id, already_started=True)
    answers = repository.exam_answers(session_id)
    view["answered"] = [row["practice_item_id"] for row in answers if row.get("grade") is not None]
    return view


# ----------------------------------------------------------------------
# Availability (policy data, not enforcement)
# ----------------------------------------------------------------------


def exam_availability(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Policy data for whether a goal's exam is "due" — not enforced.

    ``in_window`` is the last 7 days before ``due_at`` through 7 days after.
    Open-ended goals (no ``due_at``) are never ``in_window``, but starting is
    still permitted anywhere — early opt-in is always allowed and is fine
    telemetry.
    """

    now = (clock or SystemClock()).now().astimezone(UTC)
    due_at = parse_utc(goal.due_at)
    existing = repository.exam_session_in_progress_for_goal(goal.id)
    pool = repository.reserved_exam_pool_items(goal.id)

    if due_at is None:
        in_window = False
        days_until_due: float | None = None
        past_due_grace = False
    else:
        days_until_due = (due_at - now).total_seconds() / 86400
        window_start = due_at - timedelta(days=_WINDOW_DAYS)
        window_end = due_at + timedelta(days=_WINDOW_DAYS)
        in_window = window_start <= now <= window_end
        past_due_grace = due_at < now <= window_end

    return {
        "in_window": in_window,
        "days_until_due": days_until_due,
        "past_due_grace": past_due_grace,
        "existing_session_id": existing["id"] if existing is not None else None,
        "pool_item_count": len(pool),
    }


# ----------------------------------------------------------------------
# Serialization helpers
# ----------------------------------------------------------------------


def _session_view(repository: Repository, session_id: str, *, already_started: bool) -> dict[str, Any]:
    session = repository.exam_session(session_id)
    predictions = repository.exam_predictions(session_id)
    return {
        "session_id": session_id,
        "goal_id": session["goal_id"],
        "status": session["status"],
        "item_order": session["item_order"],
        "already_started": already_started,
        "predictions": [
            {
                "practice_item_id": row["practice_item_id"],
                "predicted_correctness": row["predicted_correctness"],
                "facet_projection": row["facet_projection"],
            }
            for row in predictions
        ],
    }


def _grade_to_dict(grade: ResolvedGrade) -> dict[str, Any]:
    return {
        "rubric_score": grade.rubric_score,
        "criterion_points": dict(grade.criterion_points),
        "evidence_rows": [dict(row) for row in grade.evidence_rows],
        "error_attributions": [
            {
                "error_type": attribution.error_type,
                "severity": attribution.severity,
                "evidence": attribution.evidence,
                "is_misconception": attribution.is_misconception,
                "target_evidence_families": list(attribution.target_evidence_families),
                "target_criterion_ids": list(attribution.target_criterion_ids),
            }
            for attribution in grade.error_attributions
        ],
        "grader_confidence": grade.grader_confidence,
        "confidence": grade.confidence,
        "manual_review_reason": grade.manual_review_reason,
        "feedback_md": grade.feedback_md,
        "repair_suggestions": list(grade.repair_suggestions),
        "fatal_errors": list(grade.fatal_errors),
    }


def _grade_from_dict(payload: dict[str, Any]) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=int(payload["rubric_score"]),
        criterion_points={str(key): float(value) for key, value in (payload.get("criterion_points") or {}).items()},
        evidence_rows=[dict(row) for row in (payload.get("evidence_rows") or [])],
        error_attributions=[
            GradeAttribution(
                error_type=attribution["error_type"],
                severity=float(attribution.get("severity") or 0.0),
                evidence=attribution.get("evidence"),
                is_misconception=bool(attribution.get("is_misconception")),
                target_evidence_families=list(attribution.get("target_evidence_families") or []),
                target_criterion_ids=list(attribution.get("target_criterion_ids") or []),
            )
            for attribution in (payload.get("error_attributions") or [])
        ],
        grader_confidence=float(payload.get("grader_confidence") or 1.0),
        confidence=payload.get("confidence"),
        manual_review_reason=payload.get("manual_review_reason"),
        feedback_md=payload.get("feedback_md"),
        repair_suggestions=list(payload.get("repair_suggestions") or []),
        fatal_errors=list(payload.get("fatal_errors") or []),
    )
