"""Simulation runner: drive a synthetic student through the real pipeline.

For each simulated day the runner advances a :class:`FrozenClock`, builds the
*real* due queue (``build_due_queue``), takes the top ``items_per_day``
candidates (cold-starting with never-attempted items when the queue is short,
the way a learner introduces new material), generates an outcome from the
synthetic student, and applies it through ``apply_attempt`` with a synthesized
``ResolvedGrade`` -- the same shared deterministic step used by live recording,
replay, and exam seeding. After every attempt the standard follow-up
intervention gate runs, so follow-ups, probes, error events, and automatic
misconception resolutions all come from production code paths.

The vault is loaded once and reused across the whole run; only the clock moves.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from learnloop.clock import FrozenClock, parse_utc
from learnloop.codex.schemas import CriterionEvidence, GradingProposal, TeachBackQuestion
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    _rubric_score,
    apply_attempt,
)
from learnloop.services.facet_diagnostics import mastery_diagnostic_view
from learnloop.services.followups import evaluate_attempt_intervention_followup
from learnloop.services.goal_projection import goal_report, resolve_goal_scope
from learnloop.services.fsrs import forgetting_curve
from learnloop.services.grading import resolved_rubric
from learnloop.services.mastery import display_mastery
from learnloop.services.recall_coverage import criterion_facet_weights_for_item
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.services.teach_back import (
    TEACH_BACK_ATTEMPT_TYPE,
    TEACH_BACK_PRACTICE_MODE,
    begin_teach_back,
    finish_teach_back,
    next_question,
    record_answer,
)
from learnloop.sim import metrics as sim_metrics
from learnloop.sim.profiles import AUTO_FACET
from learnloop.sim.student import StudentProfile, SyntheticStudent, _normalize
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths

SIM_START = datetime(2026, 1, 5, 9, 0, 0, tzinfo=UTC)
_ATTEMPT_SPACING_SECONDS = 180
# A primed retry lands right after feedback + re-reading the source section.
_PRIMED_RETRY_DELAY_SECONDS = 90

# Recording attempt types the student can produce, in preference order.
_PREFERRED_ATTEMPT_TYPES = (
    "independent_attempt",
    "open_text",
    "diagnostic_probe",
    "hinted_attempt",
    "reconstruction_after_walkthrough",
)


class SimulationError(ValueError):
    pass


@dataclass(frozen=True)
class SimAttemptRecord:
    day: int
    practice_item_id: str
    learning_object_id: str
    attempt_type: str
    source: str  # "queue" | "intro" | "primed_retry"
    predicted_correctness: float | None
    observed_correctness: float
    truth_p_know: float
    rubric_score: int
    hints_used: int
    latency_seconds: int
    confidence: int
    retrievability_prior: float | None
    followup_triggered: bool
    followup_reason: str
    error_types: list[str]
    misconception_fired: str | None
    primed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "practice_item_id": self.practice_item_id,
            "learning_object_id": self.learning_object_id,
            "attempt_type": self.attempt_type,
            "source": self.source,
            "primed": self.primed,
            "predicted_correctness": self.predicted_correctness,
            "observed_correctness": self.observed_correctness,
            "truth_p_know": self.truth_p_know,
            "rubric_score": self.rubric_score,
            "hints_used": self.hints_used,
            "latency_seconds": self.latency_seconds,
            "confidence": self.confidence,
            "retrievability_prior": self.retrievability_prior,
            "followup_triggered": self.followup_triggered,
            "followup_reason": self.followup_reason,
            "error_types": list(self.error_types),
            "misconception_fired": self.misconception_fired,
        }


@dataclass(frozen=True)
class SimDayRecord:
    day: int
    queue_item_ids: list[str]  # full queue order that day
    practiced_item_ids: list[str]
    belief_mae: float | None  # LO-level |belief - truth| mean at end of day
    # Belief-side goal frontier size at end of day, per active goal
    # (facets not on track for target_recall at the goal's horizon).
    goal_at_risk_facets: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "queue_item_ids": list(self.queue_item_ids),
            "practiced_item_ids": list(self.practiced_item_ids),
            "belief_mae": self.belief_mae,
            "goal_at_risk_facets": dict(self.goal_at_risk_facets),
        }


@dataclass
class SimReport:
    profile: dict[str, Any]
    seed: int
    days: int
    items_per_day: int
    config_overrides: dict[str, Any]
    vault_root: str
    goal_due_day: int | None = None
    attempts: list[SimAttemptRecord] = field(default_factory=list)
    day_records: list[SimDayRecord] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "profile": self.profile,
            "seed": self.seed,
            "days": self.days,
            "items_per_day": self.items_per_day,
            "config_overrides": dict(self.config_overrides),
            "goal_due_day": self.goal_due_day,
            "vault_root": self.vault_root,
            "attempts": [attempt.as_dict() for attempt in self.attempts],
            "days_detail": [record.as_dict() for record in self.day_records],
            "metrics": self.metrics,
        }

    def deterministic_dict(self) -> dict[str, Any]:
        """Report content that must be identical for identical (seed, args)."""

        payload = self.as_dict()
        payload.pop("vault_root", None)
        return payload


# -- config overrides ------------------------------------------------------


def coerce_override_value(raw: str) -> Any:
    text = raw.strip()
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def apply_config_overrides(
    config: LearnLoopConfig, overrides: Mapping[str, Any] | None
) -> LearnLoopConfig:
    """Return a new config with dotted-path overrides merged in-memory.

    The user's ``learnloop.toml`` is never touched: the loaded pydantic model is
    dumped to a dict, the dotted paths are set, and the dict is re-validated
    through :class:`LearnLoopConfig`. Paths must point at an existing leaf (or
    an existing dict entry such as ``evidence.attempt_types.dont_know.evidence_mass``)
    so typos fail loudly instead of silently doing nothing.
    """

    if not overrides:
        return config
    data = config.model_dump()
    for path, value in overrides.items():
        parts = [part for part in str(path).split(".") if part]
        if not parts:
            raise SimulationError(f"empty config override path {path!r}")
        node: Any = data
        for part in parts[:-1]:
            if not isinstance(node, dict) or part not in node:
                raise SimulationError(f"config override path {path!r} does not exist (at {part!r})")
            node = node[part]
        if not isinstance(node, dict) or parts[-1] not in node:
            raise SimulationError(f"config override path {path!r} does not exist (at {parts[-1]!r})")
        node[parts[-1]] = value
    return LearnLoopConfig.model_validate(data)


# -- vault copies ----------------------------------------------------------


def prepare_run_vault(source: Path, dest: Path, *, reset_state: bool = True) -> Path:
    """Copy a vault into a run directory; by default drop derived SQLite state.

    ``reset_state=True`` gives the simulation a clean belief posterior (what
    calibration experiments want); the vault content (LOs, items, goals,
    taxonomy) is preserved. The source vault is never written to.
    """

    source = source.resolve()
    dest = dest.resolve()
    if dest.exists():
        raise SimulationError(f"run vault destination already exists: {dest}")
    shutil.copytree(
        source,
        dest,
        ignore=shutil.ignore_patterns(".git", ".pytest_tmp", "__pycache__"),
    )
    if reset_state:
        for state_file in dest.glob("*.sqlite*"):
            state_file.unlink()
    return dest


# -- simulation ------------------------------------------------------------


def run_simulation(
    vault_root: Path,
    profile: StudentProfile,
    *,
    days: int = 60,
    items_per_day: int = 6,
    seed: int = 42,
    config_overrides: Mapping[str, Any] | None = None,
    start: datetime | None = None,
    primed_retries: bool = False,
    goal_due_day: int | None = None,
) -> SimReport:
    """Run one synthetic student against the vault at ``vault_root``.

    ``vault_root`` is written to (SQLite state): callers own isolation --
    the CLI and sweep always pass a fresh copy (see :func:`prepare_run_vault`).

    ``primed_retries`` models the feedback screen's source-review loop: after a
    failed attempt the student re-reads the source (see
    ``StudentProfile.priming_level`` / ``source_remediation_rate``) and
    immediately retries a sibling item, recorded with ``primed=True`` so the
    mastery update applies the ``mastery.irt.priming_b_offset`` easiness shift
    and skips the ``last_evidence_at`` refresh.
    """

    vault = load_vault(vault_root)
    overrides = dict(config_overrides or {})
    if overrides:
        vault.config = apply_config_overrides(vault.config, overrides)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    profile = _resolve_auto_misconceptions(vault, profile)
    student = SyntheticStudent(profile, seed)
    start = start or SIM_START
    if goal_due_day is not None:
        # Give every active goal a due date N sim-days in, so the run exercises
        # the projection horizon and the ramping goal quota (in memory only —
        # the run vault's goals.yaml is untouched).
        due_iso = (start + timedelta(days=goal_due_day)).strftime("%Y-%m-%dT%H:%M:%SZ")
        vault.goals = [
            goal.model_copy(update={"due_at": due_iso}) if goal.status == "active" else goal
            for goal in vault.goals
        ]

    lo_facet_weights = _lo_facet_weights(vault)
    attempted: set[str] = set()
    attempts: list[SimAttemptRecord] = []
    day_records: list[SimDayRecord] = []
    detection_days: dict[str, dict[str, Any]] = {
        m.error_type: {"error_event_day": None, "known_gap_day": None}
        for m in profile.misconceptions
    }
    planted_facet_los = _los_for_facets(
        vault, [m.facet_id for m in profile.misconceptions]
    )
    goal_snapshot_days = _goal_snapshot_days(vault, start=start, days=days)
    goal_tracking: dict[str, dict[str, Any]] = {}

    for day in range(days):
        day_base = start + timedelta(days=day)
        session_id = f"sim-s{seed}-d{day:03d}"
        day_clock = FrozenClock(day_base)
        queue = build_due_queue(
            vault,
            repository,
            clock=day_clock,
            session=SchedulerSession(session_id=session_id),
            persist_explanations=False,
        )
        queue_ids = [entry.practice_item_id for entry in queue]
        selected: list[str] = []
        for item_id in queue_ids:
            if item_id not in selected:
                selected.append(item_id)
            if len(selected) >= items_per_day:
                break
        if len(selected) < items_per_day:
            for item_id in sorted(vault.practice_items):
                if item_id in attempted or item_id in selected:
                    continue
                selected.append(item_id)
                if len(selected) >= items_per_day:
                    break

        for index, item_id in enumerate(selected):
            item = vault.practice_items[item_id]
            source = "queue" if item_id in queue_ids else "intro"
            instant = day_base + timedelta(seconds=index * _ATTEMPT_SPACING_SECONDS)
            clock = FrozenClock(instant)
            day_f = day + (index * _ATTEMPT_SPACING_SECONDS) / 86400.0
            simulate = (
                _simulate_teach_back_attempt
                if item.practice_mode == TEACH_BACK_PRACTICE_MODE
                else _simulate_one_attempt
            )
            record = simulate(
                vault,
                repository,
                student,
                item,
                day=day,
                day_f=day_f,
                clock=clock,
                session_id=session_id,
                source=source,
            )
            attempts.append(record)
            attempted.add(item_id)
            if (
                primed_retries
                and item.practice_mode != TEACH_BACK_PRACTICE_MODE
                and record.observed_correctness < 0.5
            ):
                sibling = _primed_retry_sibling(vault, item)
                if sibling is not None:
                    retry_instant = instant + timedelta(seconds=_PRIMED_RETRY_DELAY_SECONDS)
                    record = _simulate_one_attempt(
                        vault,
                        repository,
                        student,
                        sibling,
                        day=day,
                        day_f=day_f + _PRIMED_RETRY_DELAY_SECONDS / 86400.0,
                        clock=FrozenClock(retry_instant),
                        session_id=session_id,
                        source="primed_retry",
                        primed=True,
                    )
                    attempts.append(record)
                    attempted.add(sibling.id)

        belief_mae = _belief_mae(vault, repository, student, lo_facet_weights, day_f=day + 1.0)
        goal_at_risk = _track_goals_end_of_day(
            vault,
            repository,
            student,
            day=day,
            day_base=day_base,
            snapshot_days=goal_snapshot_days,
            tracking=goal_tracking,
        )
        day_records.append(
            SimDayRecord(
                day=day,
                queue_item_ids=queue_ids,
                practiced_item_ids=list(selected),
                belief_mae=belief_mae,
                goal_at_risk_facets=goal_at_risk,
            )
        )
        _update_detection_days(
            vault, repository, profile, planted_facet_los, detection_days, day
        )

    report = SimReport(
        profile=profile.as_dict(),
        seed=seed,
        days=days,
        items_per_day=items_per_day,
        config_overrides=overrides,
        vault_root=str(vault_root),
        goal_due_day=goal_due_day,
    )
    report.attempts = attempts
    report.day_records = day_records
    report.metrics = sim_metrics.build_metrics(
        vault,
        repository,
        student,
        attempts=attempts,
        day_records=day_records,
        detection_days=detection_days,
        lo_facet_weights=lo_facet_weights,
        final_day=float(days),
        goal_tracking=goal_tracking,
    )
    return report


# -- goal attainment tracking -----------------------------------------------


def _goal_snapshot_days(vault: LoadedVault, *, start: datetime, days: int) -> dict[str, int]:
    """Sim day (end of day) at which each active goal's attainment is measured.

    The due day when it falls inside the run, otherwise the final day (open-ended
    goals and due dates beyond the run measure "as of run end").
    """

    snapshot_days: dict[str, int] = {}
    for goal in vault.goals:
        if goal.status != "active":
            continue
        due_at = parse_utc(goal.due_at)
        snapshot_day = days - 1
        if due_at is not None:
            due_day = int((due_at - start).total_seconds() // 86400)
            snapshot_day = min(max(due_day, 0), days - 1)
        snapshot_days[goal.id] = snapshot_day
    return snapshot_days


def _track_goals_end_of_day(
    vault: LoadedVault,
    repository: Repository,
    student: SyntheticStudent,
    *,
    day: int,
    day_base: datetime,
    snapshot_days: dict[str, int],
    tracking: dict[str, dict[str, Any]],
) -> dict[str, int]:
    """Belief-side at-risk counts per goal; truth snapshot on each goal's due day.

    Truth at the due day is captured *during* the run because the synthetic
    student's forgetting is lazily settled forward — it cannot be re-read for a
    past day afterwards. Retention 30 days post-due is projected analytically
    from the same snapshot (no practice in between, by construction).
    """

    if not snapshot_days:
        return {}
    end_of_day_clock = FrozenClock(day_base + timedelta(days=1))
    day_f_end = day + 1.0
    at_risk_by_goal: dict[str, int] = {}
    for goal in vault.goals:
        if goal.id not in snapshot_days:
            continue
        report = goal_report(vault, repository, goal, clock=end_of_day_clock)
        # at_risk is a dual-axis predicate (attainment OR certification), no
        # longer the complement of on_track — mirror the scheduler frontier.
        at_risk_by_goal[goal.id] = report.at_risk_count
        if day != snapshot_days[goal.id]:
            continue
        scope = resolve_goal_scope(vault, goal, repository)
        facet_ids = sorted({facet for facets in scope.values() for facet in facets})
        truth_at_due = {facet: student.mastery_at(facet, day_f_end) for facet in facet_ids}
        truth_due_plus_30 = {
            facet: student.projected_mastery(facet, day_f_end, 30.0) for facet in facet_ids
        }
        due_at = parse_utc(goal.due_at)
        due_day = (
            int((due_at - (day_base - timedelta(days=day))).total_seconds() // 86400)
            if due_at is not None
            else None
        )
        tracking[goal.id] = {
            "snapshot_day": day,
            "due_day": due_day,
            "target_recall": goal.target_recall,
            "scope_facets": facet_ids,
            "truth_at_due": {facet: round(value, 6) for facet, value in truth_at_due.items()},
            "truth_due_plus_30": {
                facet: round(value, 6) for facet, value in truth_due_plus_30.items()
            },
            "belief_on_track": report.on_track_count,
            "belief_total": report.total,
        }
    return at_risk_by_goal


def _simulate_one_attempt(
    vault: LoadedVault,
    repository: Repository,
    student: SyntheticStudent,
    item: PracticeItem,
    *,
    day: int,
    day_f: float,
    clock: FrozenClock,
    session_id: str,
    source: str,
    primed: bool = False,
) -> SimAttemptRecord:
    rubric = resolved_rubric(vault, item)
    criterion_weights = criterion_facet_weights_for_item(item, rubric)
    item_weights = _item_facet_weights(item)
    outcome = student.attempt(
        day=day_f,
        item_facet_weights=item_weights,
        criteria=[
            (criterion.id, float(criterion.points), criterion_weights.get(criterion.id, {}))
            for criterion in rubric.criteria
        ],
        hints_available=len(item.hints),
        primed=primed,
    )

    retrievability_prior = _retrievability_prior(repository, item.id, clock)
    now_iso = clock.now().replace(microsecond=0).isoformat().replace("+00:00", "Z")
    attempt_id = new_ulid()

    if outcome.dont_know:
        attempt_type = "dont_know"
        criterion_points = {criterion.id: 0.0 for criterion in rubric.criteria}
        attributions = [
            GradeAttribution(
                error_type="recall_failure",
                severity=_taxonomy_severity(vault, "recall_failure"),
                is_misconception=_taxonomy_is_misconception(vault, "recall_failure"),
            )
        ]
        grader_confidence = 1.0
        answer_md = "I don't know."
    else:
        attempt_type = _attempt_type_for_item(item)
        criterion_points = dict(outcome.criterion_points)
        attributions = [
            GradeAttribution(
                error_type=attribution.error_type,
                severity=attribution.severity,
                is_misconception=attribution.is_misconception,
                evidence=attribution.evidence,
                target_evidence_families=list(attribution.target_facets),
            )
            for attribution in outcome.attributions
        ]
        grader_confidence = 0.9
        answer_md = f"[sim answer p_know={outcome.p_correct_truth:.2f}]"

    rubric_score = _rubric_score(rubric, criterion_points, [])
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": criterion.id,
            "points_awarded": criterion_points[criterion.id],
            "evidence": (
                f"Simulated grade {criterion_points[criterion.id]:g}/{criterion.points:g}."
            ),
            "notes": None,
            "local_grader_id": "sim",
            "grader_tier": 1,
            "learner_confidence": "hedged" if outcome.confidence <= 2 else "confident",
            "created_at": now_iso,
        }
        for criterion in rubric.criteria
    ]
    grade = ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points=criterion_points,
        evidence_rows=evidence_rows,
        error_attributions=attributions,
        grader_confidence=grader_confidence,
        confidence=outcome.confidence,
        manual_review_reason=None,
    )
    draft = AttemptDraft(
        practice_item_id=item.id,
        learner_answer_md=answer_md,
        attempt_type=attempt_type,
        hints_used=outcome.hints_used,
        latency_seconds=outcome.latency_seconds,
        session_id=session_id,
        primed=primed,
    )
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(draft=draft, attempt_id=attempt_id, grade=grade),
        clock=clock,
    )
    decision = evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result,
        session_id=session_id,
        clock=clock,
    )
    # Feedback is always shown after an attempt, so the student learns from it.
    student.learn(_normalize(item_weights), day_f)

    debug_payload = result.debug_payload or {}
    predicted = debug_payload.get("predicted_correctness")
    return SimAttemptRecord(
        day=day,
        practice_item_id=item.id,
        learning_object_id=result.learning_object_id,
        attempt_type=attempt_type,
        source=source,
        predicted_correctness=float(predicted) if predicted is not None else None,
        observed_correctness=result.correctness,
        truth_p_know=outcome.p_correct_truth,
        rubric_score=result.rubric_score,
        hints_used=outcome.hints_used,
        latency_seconds=outcome.latency_seconds,
        confidence=outcome.confidence,
        retrievability_prior=retrievability_prior,
        followup_triggered=decision.triggered,
        followup_reason=_strip_ulids(decision.reason),
        error_types=[attribution.error_type for attribution in attributions],
        misconception_fired=outcome.misconception_fired,
        primed=primed,
    )


def _primed_retry_sibling(vault: LoadedVault, item: PracticeItem) -> PracticeItem | None:
    """First (deterministic) other non-teach-back item on the same LO."""

    for item_id in sorted(vault.practice_items):
        sibling = vault.practice_items[item_id]
        if (
            sibling.learning_object_id == item.learning_object_id
            and sibling.id != item.id
            and sibling.practice_mode != TEACH_BACK_PRACTICE_MODE
        ):
            return sibling
    return None


# -- teach-back ---------------------------------------------------------------


class _SimTeachBackClient:
    """No-op question generator + synthesized grader for simulated teach-backs.

    The sim never calls an AI provider: ``run_teach_back_question`` returns a
    canned naive-student question (question *text* is not load-bearing for the
    core selection logic, which runs in ``plan_followups``), and
    ``run_grading_proposal`` awards the criterion points the synthetic student
    already earned while answering — mirroring how the runner synthesizes
    grades for every other attempt type.
    """

    def __init__(
        self,
        student: SyntheticStudent,
        *,
        day_f: float,
        item_facet_weights: Mapping[str, float],
        criterion_facet_weights: Mapping[str, Mapping[str, float]],
    ):
        self.student = student
        self.day_f = day_f
        self.item_facet_weights = dict(item_facet_weights)
        self.criterion_facet_weights = {
            criterion_id: dict(weights)
            for criterion_id, weights in criterion_facet_weights.items()
        }
        self.criterion_points: dict[str, float] = {}

    def run_teach_back_question(self, context: Any) -> TeachBackQuestion:
        return TeachBackQuestion(
            question_md=(
                f"I'm confused about {context.criterion_description} "
                f"Can you explain that part again? [sim question {context.question_number}]"
            )
        )

    def run_grading_proposal(self, context: Any) -> GradingProposal:
        # ``context.rubric`` is already restricted to the asked criteria by
        # ``finish_teach_back``. Criteria without a recorded answer only appear
        # here in the zero-answered-follow-ups fallback (opening explanation
        # graded against core criteria); synthesize their points on the spot.
        criteria = list(context.rubric.get("criteria", []))
        evidence: list[CriterionEvidence] = []
        awarded_total = 0.0
        max_total = 0.0
        for criterion in criteria:
            criterion_id = str(criterion["id"])
            max_points = float(criterion.get("points", 0.0))
            if criterion_id not in self.criterion_points:
                answer = self.student.teach_back_answer(
                    day=self.day_f,
                    tier=str(criterion.get("tier") or "core"),
                    criterion_weights=self.criterion_facet_weights.get(criterion_id, {}),
                    item_facet_weights=self.item_facet_weights,
                    max_points=max_points,
                )
                self.criterion_points[criterion_id] = answer.points_awarded
            points = min(max_points, max(0.0, self.criterion_points[criterion_id]))
            awarded_total += points
            max_total += max_points
            evidence.append(
                CriterionEvidence(
                    criterion_id=criterion_id,
                    points_awarded=points,
                    evidence=f"Simulated teach-back grade {points:g}/{max_points:g}.",
                )
            )
        fraction = awarded_total / max_total if max_total > 0 else 0.0
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=max(0, min(4, int(round(4 * fraction)))),
            criterion_evidence=evidence,
            grader_confidence=0.9,
            feedback_md="Simulated teach-back feedback.",
        )


def _simulate_teach_back_attempt(
    vault: LoadedVault,
    repository: Repository,
    student: SyntheticStudent,
    item: PracticeItem,
    *,
    day: int,
    day_f: float,
    clock: FrozenClock,
    session_id: str,
    source: str,
) -> SimAttemptRecord:
    """Run one simulated teach-back conversation as ONE recorded attempt.

    The follow-up plan comes from the real ``plan_followups`` selection logic
    (uncertainty ranking + transfer escalation), answers come from the
    synthetic student's mastery (with the transfer difficulty delta), and the
    grade is recorded through the real ``finish_teach_back`` -> ``apply_attempt``
    path so replay stays sound.
    """

    rubric = resolved_rubric(vault, item)
    criterion_weights = criterion_facet_weights_for_item(item, rubric)
    item_weights = _item_facet_weights(item)
    criterion_max = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    client = _SimTeachBackClient(
        student,
        day_f=day_f,
        item_facet_weights=item_weights,
        criterion_facet_weights=criterion_weights,
    )
    normalized_item_weights = _normalize(item_weights)
    truth_p_know = sum(
        weight * student.mastery_at(facet, day_f)
        for facet, weight in normalized_item_weights.items()
    )
    retrievability_prior = _retrievability_prior(repository, item.id, clock)

    state = begin_teach_back(
        vault,
        repository,
        item,
        opening_md=f"[sim opening explanation for {item.id} p_know={truth_p_know:.2f}]",
        clock=clock,
    )
    latency_seconds = 30
    while True:
        state, payload = next_question(vault, state, client)
        if payload is None:
            break
        answer = student.teach_back_answer(
            day=day_f,
            tier=str(payload["tier"]),
            criterion_weights=criterion_weights.get(payload["criterion_id"], {}),
            item_facet_weights=item_weights,
            max_points=criterion_max.get(payload["criterion_id"], 0.0),
        )
        client.criterion_points[payload["criterion_id"]] = answer.points_awarded
        latency_seconds += answer.latency_seconds
        record_answer(state, answer.answer_md)

    finish = finish_teach_back(
        vault,
        repository,
        state,
        client,
        session_id=session_id,
        latency_seconds=latency_seconds,
        clock=clock,
    )
    result = finish.attempt
    decision = evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result,
        session_id=session_id,
        clock=clock,
    )
    # Teaching is practice too: feedback is shown after the attempt.
    student.learn(normalized_item_weights, day_f)
    confidence = student._confidence(student.rng, result.correctness, misconception_fired=False)

    debug_payload = result.debug_payload or {}
    predicted = debug_payload.get("predicted_correctness")
    return SimAttemptRecord(
        day=day,
        practice_item_id=item.id,
        learning_object_id=result.learning_object_id,
        attempt_type=TEACH_BACK_ATTEMPT_TYPE,
        source=source,
        predicted_correctness=float(predicted) if predicted is not None else None,
        observed_correctness=result.correctness,
        truth_p_know=truth_p_know,
        rubric_score=result.rubric_score,
        hints_used=0,
        latency_seconds=latency_seconds,
        confidence=confidence,
        retrievability_prior=retrievability_prior,
        followup_triggered=decision.triggered,
        followup_reason=_strip_ulids(decision.reason),
        error_types=[],
        misconception_fired=None,
    )


# -- helpers ---------------------------------------------------------------

_ULID_RE = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")


def _strip_ulids(text: str) -> str:
    """Replace random ULIDs in free text so reports are seed-deterministic."""

    return _ULID_RE.sub("<id>", text)


def _attempt_type_for_item(item: PracticeItem) -> str:
    allowed = list(item.attempt_types_allowed)
    if not allowed:
        return "independent_attempt"
    for preferred in _PREFERRED_ATTEMPT_TYPES:
        if preferred in allowed:
            return preferred
    return "independent_attempt"  # apply path allows dont_know/exam only as extras


def _item_facet_weights(item: PracticeItem) -> dict[str, float]:
    if item.evidence_weights:
        return {str(facet): float(weight) for facet, weight in item.evidence_weights.items()}
    return {str(facet): 1.0 for facet in item.evidence_facets}


def _lo_facet_weights(vault: LoadedVault) -> dict[str, dict[str, float]]:
    weights: dict[str, dict[str, float]] = {}
    for item in vault.practice_items.values():
        target = weights.setdefault(item.learning_object_id, {})
        for facet, weight in _item_facet_weights(item).items():
            target[facet] = target.get(facet, 0.0) + weight
    return {lo: _normalize(facets) for lo, facets in weights.items()}


def _los_for_facets(vault: LoadedVault, facets: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {facet: [] for facet in facets}
    for item in vault.practice_items.values():
        for facet in item.evidence_facets:
            facet = str(facet)
            if facet in result and item.learning_object_id not in result[facet]:
                result[facet].append(item.learning_object_id)
    return {facet: sorted(los) for facet, los in result.items()}


def _resolve_auto_misconceptions(vault: LoadedVault, profile: StudentProfile) -> StudentProfile:
    if not any(m.facet_id == AUTO_FACET for m in profile.misconceptions):
        return profile
    totals: dict[str, float] = {}
    for item in vault.practice_items.values():
        for facet, weight in _item_facet_weights(item).items():
            totals[facet] = totals.get(facet, 0.0) + weight
    if not totals:
        raise SimulationError("vault has no evidence facets to plant a misconception on")
    best = max(sorted(totals), key=lambda facet: totals[facet])
    from dataclasses import replace as dc_replace

    resolved = dc_replace(
        profile,
        misconceptions=[
            dc_replace(m, facet_id=best) if m.facet_id == AUTO_FACET else m
            for m in profile.misconceptions
        ],
    )
    return resolved


def _retrievability_prior(repository: Repository, item_id: str, clock: FrozenClock) -> float | None:
    state = repository.practice_item_state(item_id)
    if state is None or state.stability is None:
        return None
    last = parse_utc(state.last_attempt_at)
    if last is None:
        return None
    elapsed_days = max(0.0, (clock.now() - last).total_seconds() / 86400)
    return forgetting_curve(state.stability, elapsed_days)


def _belief_mae(
    vault: LoadedVault,
    repository: Repository,
    student: SyntheticStudent,
    lo_facet_weights: dict[str, dict[str, float]],
    *,
    day_f: float,
) -> float | None:
    mastery_states = repository.mastery_states()
    errors: list[float] = []
    for lo_id, facet_weights in lo_facet_weights.items():
        state = mastery_states.get(lo_id)
        if state is None or state.last_evidence_at is None:
            continue
        belief = display_mastery(state).mastery_mean
        truth = sum(
            weight * student.mastery_at(facet, day_f) for facet, weight in facet_weights.items()
        )
        errors.append(abs(belief - truth))
    if not errors:
        return None
    return sum(errors) / len(errors)


def _update_detection_days(
    vault: LoadedVault,
    repository: Repository,
    profile: StudentProfile,
    planted_facet_los: dict[str, list[str]],
    detection_days: dict[str, dict[str, Any]],
    day: int,
) -> None:
    if not profile.misconceptions:
        return
    event_types = _error_event_types(repository)
    for planted in profile.misconceptions:
        tracker = detection_days[planted.error_type]
        if tracker["error_event_day"] is None and planted.error_type in event_types:
            tracker["error_event_day"] = day
        if tracker["known_gap_day"] is None:
            for lo_id in planted_facet_los.get(planted.facet_id, []):
                view = mastery_diagnostic_view(vault, repository, lo_id)
                for facet in view["facets"]:
                    if facet["facet_id"] != planted.facet_id:
                        continue
                    if facet["state"] == "known_gap":
                        tracker["known_gap_day"] = day
                        marginal = facet.get("hypothesis_marginal") or {}
                        tracker["known_gap_top_hypothesis"] = (
                            max(marginal, key=marginal.get) if marginal else None
                        )
                        break
                if tracker["known_gap_day"] is not None:
                    break


def _error_event_types(repository: Repository) -> set[str]:
    with repository.connection() as connection:
        rows = connection.execute("SELECT DISTINCT error_type FROM error_events").fetchall()
    return {row["error_type"] for row in rows if row["error_type"]}


def _taxonomy_severity(vault: LoadedVault, error_type: str) -> float:
    taxonomy = vault.error_types.get(error_type)
    return taxonomy.severity_default if taxonomy is not None else 0.5


def _taxonomy_is_misconception(vault: LoadedVault, error_type: str) -> bool:
    taxonomy = vault.error_types.get(error_type)
    return taxonomy.is_misconception if taxonomy is not None else False
