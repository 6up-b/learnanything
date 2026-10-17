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

import dataclasses
from collections.abc import Sequence
from datetime import UTC, timedelta
from typing import Any

from learnloop.clock import Clock, FrozenClock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.content.sources.exam_material import exposed_items
from learnloop.goals.exam_pool import (
    release_exam_pool,
    withdraw_exposed_reservations,
    withdrawn_note,
    withdrawn_reasons_text,
)
from learnloop.learner.facet_state_reader import facet_recall_states_for_lo
from learnloop.goals.goal_projection import goal_report, resolve_goal_scope
from learnloop.scheduling.selection_rewards import (
    ability_vector,
    item_demand_vector,
    predicted_correctness_from_vectors,
)
from learnloop.vault.lifecycle import practice_item_servable
from learnloop.vault.models import Goal, LoadedVault

# Exam availability window: the last 7 days before due_at through 7 days after.
_WINDOW_DAYS = 7


class ExamSessionError(ValueError):
    pass


#: Why an answer to a withdrawn exam item is refused (Codex re-review F5).
WITHDRAWN_ITEM_REFUSAL = ("This exam item was set aside: you've seen it since it was held out ({reasons}), so it "
                          "would no longer be a fair test. Your other answers are kept; reopen the exam to continue "
                          "without it.")

#: Why a sitting with nothing left to serve and nothing answered is closed.
SITTING_CLOSED = ("Every remaining item of this exam has been shown to you since it was held out ({reasons}), so "
                  "none is a fair test any more. The sitting is closed and its items rejoin practice; open the "
                  "exam again to hold out a new pool.")


class ExamItemWithdrawnError(ExamSessionError):
    """An answer to an exam item the learner has been shown since it was held out."""

    def __init__(self, practice_item_id: str, reasons: list[str]) -> None:
        self.practice_item_id = practice_item_id
        self.reasons = list(reasons)
        super().__init__(WITHDRAWN_ITEM_REFUSAL.format(reasons=withdrawn_reasons_text(self.reasons)))


def session_withdrawn_items(vault: LoadedVault, repository: Repository,
                            session: dict[str, Any]) -> list[dict[str, Any]]:
    """The in-progress sitting's unanswered items the learner has been shown
    since they were held out (Codex re-review F5), ``[{"practice_item_id",
    "reasons"}]`` in the frozen order.

    The exam's start withdraws what was shown before it
    (``withdraw_exposed_reservations``). What the learner sees afterwards (an
    item's exercise read in the Reader, its answer revealed by the tutor, its
    prompt in a suggestion) is caught here, at every door the sitting has:
    resume (``start_exam``), the live progress view, answer acceptance
    (``queue_exam_answer``, ``record_exam_answer``) and ``finish_exam``. Such an
    item is no longer served or accepted, and the report names it without
    scoring it. Its history stays: the frozen order, its frozen prediction and
    its reservation row (released with the pool when the sitting ends).

    An answered item is never withdrawn: an answer is final once given, and an
    exposure after it cannot have informed it. Shown material is
    ``exam_material.exposed_items`` (the reservation's own rule, never
    forgotten), so the set only grows; it is empty with
    ``goals.held_out_selection`` off (the predecessor administers every item)."""

    if session.get("status") != "in_progress":
        return []
    answered = {row["practice_item_id"] for row in repository.exam_answers(session["id"])}
    outstanding = [vault.practice_items[item_id] for item_id in session["item_order"]
                   if item_id not in answered and item_id in vault.practice_items]
    exposed = exposed_items(vault, repository, outstanding)
    return [{"practice_item_id": item_id, "reasons": exposed[item_id]}
            for item_id in session["item_order"] if item_id in exposed]


def _refuse_withdrawn(vault: LoadedVault, repository: Repository, session: dict[str, Any],
                      practice_item_id: str) -> None:
    """Refuse a new answer to an item the sitting has set aside."""

    for entry in session_withdrawn_items(vault, repository, session):
        if entry["practice_item_id"] == practice_item_id:
            raise ExamItemWithdrawnError(practice_item_id, entry["reasons"])


def refuse_withdrawn_answer(vault: LoadedVault, repository: Repository, session_id: str,
                            practice_item_id: str) -> None:
    """Raise :class:`ExamItemWithdrawnError` before a caller grades a new answer
    the sitting would refuse (the CLI grades before it records, so a refused
    answer would otherwise cost a grading call)."""

    session = repository.exam_session(session_id)
    if session is None or repository.exam_answer(session_id, practice_item_id) is not None:
        return
    _refuse_withdrawn(vault, repository, session, practice_item_id)


def _close_exhausted_sitting(repository: Repository, session: dict[str, Any],
                             withdrawn: list[dict[str, Any]], *, clock: Clock) -> None:
    """Close a sitting none of whose items is left to serve or was answered.

    Without this the learner would resume, forever, an exam with nothing to
    answer. The session row, its frozen predictions and the reservation rows
    stay (status ``abandoned``, the withdrawn items on its report); the pool is
    released, so its items rejoin practice and the next reservation holds out
    a fresh one (shown items are never reserved)."""

    now_iso = utc_now_iso(clock)
    repository.update_exam_session(
        session["id"],
        status="abandoned",
        report={
            "session_id": session["id"],
            "goal_id": session["goal_id"],
            "closed_reason": "every_item_withdrawn",
            "withdrawn_items": withdrawn,
            "withdrawn_note": withdrawn_note(withdrawn),
        },
        completed_at=now_iso,
        clock=clock,
    )
    release_exam_pool(repository, session["goal_id"], clock=clock)
    raise ExamSessionError(SITTING_CLOSED.format(
        reasons=withdrawn_reasons_text(reason for entry in withdrawn for reason in entry["reasons"])))


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

    Idempotent: an existing ``in_progress`` session for the goal is resumed
    (predictions are never re-frozen), less the unanswered items the learner
    has been shown since (``session_withdrawn_items``, reported with the
    reason). A resumed sitting with nothing left to serve and nothing answered
    is closed (``_close_exhausted_sitting``).
    """

    clock = clock or SystemClock()
    goal = _goal(vault, goal_id)

    existing = repository.exam_session_in_progress_for_goal(goal_id)
    if existing is not None:
        # Exam protection (Codex re-review F5): what the learner saw after the
        # exam started is caught on resume, not only before the start.
        withdrawn = session_withdrawn_items(vault, repository, existing)
        if withdrawn and len(withdrawn) == len(existing["item_order"]):
            _close_exhausted_sitting(repository, existing, withdrawn, clock=clock)
        view = _session_view(repository, existing["id"], already_started=True, withdrawn=withdrawn)
        view["withdrawn_items"] = withdrawn
        view["withdrawn_note"] = withdrawn_note(withdrawn)
        return view

    # Exam protection (Codex review F5): a reserved item the learner has been
    # shown since it was reserved (an answer revealed, its exercise or
    # solution read, its prompt in a suggestion) is no longer held out, so it
    # is withdrawn (its reservation released, with the reason) before the
    # exam freezes anything.
    withdrawn = withdraw_exposed_reservations(vault, repository, goal_id, clock=clock)
    pooled = repository.reserved_exam_pool_items(goal_id)
    if not pooled:
        if withdrawn:
            raise ExamSessionError(
                f"Every reserved exam item for goal {goal_id} has been shown to you since it was held out, "
                "so none is a fair test any more; they rejoin practice. Reserve a new pool."
            )
        raise ExamSessionError(
            f"Goal {goal_id} has no reserved exam pool; call reserve_exam_pool first."
        )
    # Learner-set LO lifecycle: a pooled item whose LO was put away (dormant or
    # resolved) after the pool was reserved is not administered, nor is a card
    # the reference sweep adopted while its kill switch is off (vault.lifecycle).
    item_order = [
        row["practice_item_id"]
        for row in pooled
        if (item := vault.practice_items.get(row["practice_item_id"])) is None
        or practice_item_servable(vault, item)
    ]
    if not item_order:
        raise ExamSessionError(
            f"Every reserved exam item for goal {goal_id} belongs to a dormant or resolved "
            "learning object or is otherwise not servable; reactivate one or reserve a new pool."
        )

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
    view = _session_view(repository, session_id, already_started=False)
    view["withdrawn_items"] = withdrawn
    view["withdrawn_note"] = withdrawn_note(withdrawn)
    return view


# ----------------------------------------------------------------------
# Answers
# ----------------------------------------------------------------------


def queue_exam_answer(
    vault: LoadedVault,
    repository: Repository,
    session_id: str,
    practice_item_id: str,
    *,
    answer_md: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Persist a final learner answer before its grade exists.

    The ungraded row is the durable background-work receipt. Repeating the same
    submission is idempotent; replacing it is forbidden because exam answers
    are final once the learner advances.
    """

    session = repository.exam_session(session_id)
    if session is None:
        raise ExamSessionError(f"Unknown exam session {session_id}")
    if session["status"] != "in_progress":
        raise ExamSessionError(
            f"Exam session {session_id} is {session['status']}, not in_progress"
        )
    if practice_item_id not in session["item_order"]:
        raise ExamSessionError(
            f"{practice_item_id} is not in exam session {session_id}"
        )
    if practice_item_id not in vault.practice_items:
        raise ExamSessionError(f"Unknown practice item {practice_item_id}")

    existing = repository.exam_answer(session_id, practice_item_id)
    if existing is not None:
        if str(existing.get("answer_md") or "") != answer_md:
            raise ExamSessionError(
                f"Exam answer {practice_item_id} was already submitted and cannot be replaced"
            )
        return {
            "session_id": session_id,
            "practice_item_id": practice_item_id,
            "already_submitted": True,
            "graded": existing.get("grade") is not None,
        }
    # Codex re-review F5: an item shown to the learner since it was held out
    # takes no answer (one already given stands, above).
    _refuse_withdrawn(vault, repository, session, practice_item_id)

    repository.upsert_exam_answer(
        {
            "session_id": session_id,
            "practice_item_id": practice_item_id,
            "answer_md": answer_md,
            "rubric_score": None,
            "correctness": None,
            "grade": None,
        },
        clock=clock,
    )
    return {
        "session_id": session_id,
        "practice_item_id": practice_item_id,
        "already_submitted": False,
        "graded": False,
    }


def record_exam_answer(
    vault: LoadedVault,
    repository: Repository,
    session_id: str,
    practice_item_id: str,
    *,
    answer_md: str,
    resolved_grade: ResolvedGrade,
    grader_identity: tuple[str, str] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Store one graded answer on the session (no mastery writes yet).

    ``grader_identity`` is the grade's calibration identity (Slice 1 §4.3):
    the blind pair when a split vault graded it blind, None for the joint
    grader. It travels with the stored grade to ``finish_exam``'s raw grade.
    """

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
    existing = repository.exam_answer(session_id, practice_item_id)
    if (
        existing is not None
        and str(existing.get("answer_md") or "") != answer_md
    ):
        raise ExamSessionError(
            f"Exam answer {practice_item_id} was already submitted and cannot be replaced"
        )
    if existing is None:
        # Codex re-review F5: a new answer (the CLI's) to an item shown since
        # it was held out is refused; the grade of an answer accepted before
        # (``queue_exam_answer``) still lands.
        _refuse_withdrawn(vault, repository, session, practice_item_id)
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
            "grade": {
                **_grade_to_dict(resolved_grade),
                # Review F11: only a non-joint grade stores one, so a joint
                # vault's stored grades are unchanged.
                **({"calibration_identity": list(grader_identity)} if grader_identity is not None else {}),
            },
        },
        clock=clock,
    )
    # The P0.2 dual-write is deliberately NOT done here: it must carry the SAME
    # attempt id the answer is later applied under, and that id is only minted at
    # ``finish_exam``. Writing it here under a synthetic ``exam::session::item``
    # key left the canonical projection unable to join the interpretation to the
    # attempt, so ``build_effective_observation`` fell to its missing-interpretation
    # branch (effective_mass 0.0) and every exam answer certified nothing.
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
    attempt_id: str,
    grader_identity: tuple[str, str] | None = None,
    clock: Clock | None = None,
) -> None:
    """P0.2 dual-write for exam answers (§4.1, §7.2). Fail-safe (§7.3): appends a
    raw grade event + interpretation on an assessment-purpose administration
    alongside the legacy exam_answer summary; never raises into the legacy path.

    ``attempt_id`` MUST be the id the answer is applied under in ``finish_exam``:
    the canonical projection joins interpretations to attempts by that id."""

    try:
        from learnloop.attempts.grade_resolution import record_grade_dual_write

        criterion_max = (
            {c.id: c.points for c in rubric.criteria} if rubric is not None else None
        )
        record_grade_dual_write(
            vault,
            repository,
            item=item,
            purpose="assessment",
            grading_source="codex",
            attempt_id=attempt_id,
            response_text=answer_md,
            rubric_score=resolved_grade.rubric_score,
            max_points=max_points,
            grader_confidence=resolved_grade.grader_confidence,
            has_fatal=bool(resolved_grade.fatal_errors),
            criterion_points=resolved_grade.criterion_points,
            criterion_max=criterion_max,
            domain=getattr(item, "learning_object_id", None),
            grading_prompt_version=grader_identity[0] if grader_identity else None,
            grader_output_schema_version=grader_identity[1] if grader_identity else None,
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
    if session["status"] == "abandoned":
        raise ExamSessionError(f"Exam session {session_id} was closed: none of its items was left to answer")

    goal = _goal(vault, session["goal_id"])
    # Codex re-review F5: the unanswered items set aside during the sitting,
    # read before the session completes, are named on the report.
    withdrawn = session_withdrawn_items(vault, repository, session)
    submitted = repository.exam_answers(session_id)
    submitted_by_item = {
        answer["practice_item_id"]: answer for answer in submitted
    }
    pending = [
        item_id
        for item_id, answer in submitted_by_item.items()
        if answer.get("grade") is None
    ]
    if pending:
        raise ExamSessionError(
            "Exam grading is still pending for: " + ", ".join(pending)
        )
    answers = [
        submitted_by_item[item_id]
        for item_id in session["item_order"]
        if item_id in submitted_by_item
    ]

    # Apply answered items as exam_attempts, spaced seconds apart at finish time
    # (same deterministic backdating shape exam_seeding uses).
    base_instant = clock.now().astimezone(UTC).replace(microsecond=0)
    applied_results = []
    for index, answer in enumerate(answers):
        if answer.get("attempt_id"):
            continue
        item_id = answer["practice_item_id"]
        attempt_clock = FrozenClock(base_instant + timedelta(seconds=index))
        grade = _grade_from_dict(answer["grade"])
        answer_md = answer.get("answer_md") or ""
        draft = AttemptDraft(
            entry_surface="exam",
            evidence_origin="human",
            practice_item_id=item_id,
            learner_answer_md=answer_md,
            attempt_type="exam_attempt",
            hints_used=0,
        )
        attempt_id = new_ulid()
        # Dual-write BEFORE applying: ``apply_attempt`` ends by running the
        # canonical projection, which joins the grade interpretation to the
        # attempt by attempt id. An interpretation written afterwards — or under
        # a different id — is invisible to that fold and certifies nothing.
        item = vault.practice_items.get(item_id)
        if item is not None:
            rubric = vault.rubric_for_item(item)
            _dual_write_exam_grade(
                vault,
                repository,
                item=item,
                rubric=rubric,
                max_points=rubric.max_points if rubric is not None else 4,
                answer_md=answer_md,
                resolved_grade=grade,
                attempt_id=attempt_id,
                grader_identity=_stored_grader_identity(answer["grade"]),
                clock=attempt_clock,
            )
        applied = apply_attempt(
            vault,
            repository,
            # Q33: applied at the sitting's own instants (``serve_eligibility``).
            ApplyAttemptInput(draft=draft, attempt_id=attempt_id, grade=grade, reveal_window_bounded=True),
            clock=attempt_clock,
        )
        applied_results.append(applied)
        repository.set_exam_answer_attempt_id(session_id, item_id, attempt_id)

    if applied_results:
        # The one post-attempt pipeline every recording door runs. Exam-purpose
        # gating: same evidence-side steps as practice (needs, causal hooks,
        # certification cold probes), insertion capped per sitting, and
        # learner-facing feedback deferred to the report below — the pipeline
        # writes the metadata the report reads.
        from learnloop.attempts.post_attempt import run_exam_sitting_pipeline

        run_exam_sitting_pipeline(
            vault, repository, results=applied_results, clock=clock
        )

    report = _compute_report(vault, repository, session, goal, withdrawn=withdrawn)
    completed_at = utc_now_iso(clock)
    repository.update_exam_session(
        session_id, status="completed", report=report, completed_at=completed_at, clock=clock
    )
    release_exam_pool(repository, session["goal_id"], clock=clock)
    return report


def _compute_report(vault: LoadedVault, repository: Repository, session, goal, *,
                    withdrawn: Sequence[dict[str, Any]] = ()) -> dict[str, Any]:
    predictions = {row["practice_item_id"]: row for row in repository.exam_predictions(session["id"])}
    withdrawn = [dict(entry) for entry in withdrawn]
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
        # The items administered: the frozen order less the ones set aside.
        "item_count": len(session["item_order"]) - len(withdrawn),
        "answered_count": len(correctness_values),
        "overall_score": overall_score,
        "brier": brier,
        "items": items,
        "facets": facets,
        "withdrawn_items": withdrawn,
        "withdrawn_note": withdrawn_note(withdrawn),
    }


def exam_report(vault: LoadedVault, repository: Repository, session_id: str) -> dict[str, Any]:
    """Return the persisted report (completed), the persisted closure report
    (a sitting closed because every item was set aside), or a live progress
    view.

    A closed sitting's report is the one written when it closed
    (``_close_exhausted_sitting``: ``closed_reason``, the withdrawn items and
    their reasons, the note). It is never rebuilt: the progress view reads the
    set-aside items of an in-progress sitting only, so a rebuild would say
    nothing was withdrawn (Codex final verify F7)."""

    session = repository.exam_session(session_id)
    if session is None:
        raise ExamSessionError(f"Unknown exam session {session_id}")
    if session["status"] in {"completed", "abandoned"} and session.get("report") is not None:
        return session["report"]
    withdrawn = session_withdrawn_items(vault, repository, session)
    view = _session_view(repository, session_id, already_started=True, withdrawn=withdrawn)
    view["withdrawn_items"] = withdrawn
    view["withdrawn_note"] = withdrawn_note(withdrawn)
    answers = repository.exam_answers(session_id)
    view["answered"] = [row["practice_item_id"] for row in answers]
    view["graded"] = [
        row["practice_item_id"] for row in answers if row.get("grade") is not None
    ]
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


def _session_view(repository: Repository, session_id: str, *, already_started: bool,
                  withdrawn: Sequence[dict[str, Any]] = ()) -> dict[str, Any]:
    """The sitting as served: ``item_order`` is the frozen order less the
    items set aside since (``session_withdrawn_items``); the stored order and
    every frozen prediction are unchanged."""

    session = repository.exam_session(session_id)
    predictions = repository.exam_predictions(session_id)
    set_aside = {entry["practice_item_id"] for entry in withdrawn}
    return {
        "session_id": session_id,
        "goal_id": session["goal_id"],
        "status": session["status"],
        "item_order": [item_id for item_id in session["item_order"] if item_id not in set_aside],
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
    """Serialize a resolved grade LOSSLESSLY into ``exam_answers.grade_json``.

    This round-trip is the wire between grading time and ``finish_exam``'s
    ``apply_attempt``. It used to keep only six attribution fields, silently
    dropping every P0b causal axis the grader had already authored and paid
    for (``candidate_causes``, ``misconception_statement``,
    ``first_divergence``, …) — so exam error events carried no causal
    material, ``_hypothesis_specs`` found nothing, and the remediation lane
    stalled at a repair class with zero hypotheses. Attributions serialize via
    ``dataclasses.asdict`` so a field added to ``GradeAttribution`` can never
    be dropped here again.
    """

    return {
        "rubric_score": grade.rubric_score,
        "criterion_points": dict(grade.criterion_points),
        "evidence_rows": [dict(row) for row in grade.evidence_rows],
        "error_attributions": [
            dataclasses.asdict(attribution) for attribution in grade.error_attributions
        ],
        "grader_confidence": grade.grader_confidence,
        "confidence": grade.confidence,
        "manual_review_reason": grade.manual_review_reason,
        "feedback_md": grade.feedback_md,
        "repair_suggestions": list(grade.repair_suggestions),
        "fatal_errors": list(grade.fatal_errors),
        "diagnosis_md": grade.diagnosis_md,
        "attribution_audit_events": list(grade.attribution_audit_events),
        "exercised_facets": list(grade.exercised_facets),
        "clarification": grade.clarification,
        "discrimination_profile_match": grade.discrimination_profile_match,
        "error_hunt": grade.error_hunt,
    }


_ATTRIBUTION_FIELD_NAMES = frozenset(
    f.name for f in dataclasses.fields(GradeAttribution)
)


def _attribution_from_dict(payload: dict[str, Any]) -> GradeAttribution:
    """Rebuild one attribution, tolerating legacy six-field rows.

    Unknown keys are ignored (never a crash on a newer row), missing keys take
    the dataclass defaults (never a crash on an older row); the historically
    coerced fields keep their coercions.
    """

    kwargs = {
        key: value for key, value in payload.items() if key in _ATTRIBUTION_FIELD_NAMES
    }
    kwargs["error_type"] = str(payload["error_type"])
    kwargs["severity"] = float(payload.get("severity") or 0.0)
    kwargs["evidence"] = payload.get("evidence")
    kwargs["is_misconception"] = bool(payload.get("is_misconception"))
    kwargs["target_evidence_families"] = list(payload.get("target_evidence_families") or [])
    kwargs["target_criterion_ids"] = list(payload.get("target_criterion_ids") or [])
    kwargs["candidate_causes"] = list(payload.get("candidate_causes") or [])
    kwargs["postdictive_claims"] = list(payload.get("postdictive_claims") or [])
    kwargs["soft_postdictive_claims"] = list(payload.get("soft_postdictive_claims") or [])
    return GradeAttribution(**kwargs)


def _stored_grader_identity(payload: dict[str, Any]) -> tuple[str, str] | None:
    """The calibration identity stored with an exam grade (None: the joint grader's)."""

    identity = payload.get("calibration_identity")
    if isinstance(identity, (list, tuple)) and len(identity) == 2 and all(identity):
        return (str(identity[0]), str(identity[1]))
    return None


def _grade_from_dict(payload: dict[str, Any]) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=int(payload["rubric_score"]),
        criterion_points={str(key): float(value) for key, value in (payload.get("criterion_points") or {}).items()},
        evidence_rows=[dict(row) for row in (payload.get("evidence_rows") or [])],
        error_attributions=[
            _attribution_from_dict(attribution)
            for attribution in (payload.get("error_attributions") or [])
        ],
        grader_confidence=float(payload.get("grader_confidence") or 1.0),
        confidence=payload.get("confidence"),
        manual_review_reason=payload.get("manual_review_reason"),
        feedback_md=payload.get("feedback_md"),
        repair_suggestions=list(payload.get("repair_suggestions") or []),
        fatal_errors=list(payload.get("fatal_errors") or []),
        diagnosis_md=payload.get("diagnosis_md"),
        attribution_audit_events=list(payload.get("attribution_audit_events") or []),
        exercised_facets=list(payload.get("exercised_facets") or []),
        clarification=payload.get("clarification"),
        discrimination_profile_match=payload.get("discrimination_profile_match"),
        error_hunt=payload.get("error_hunt"),
    )
