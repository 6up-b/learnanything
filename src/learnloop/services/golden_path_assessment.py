"""P2 step B.8 -- the fresh held-out cold assessment + burn
(spec_p2_narrow_golden_path §8.1, §8.2, §8.3; §12.5; migration 087 for the result
artifact only -- the assessment substrate itself is landed P0).

P2 owns ONLY the orchestration here: assessment-stage entry from the run state
machine, the atomic reserve revalidation, and the reliability-aware result artifact.
Every measurement primitive composes a LANDED P0 service and there is NO new
posterior / FSRS write / certification path (spec §2 ownership ledger):

  * reservation + the render/burn boundary  -> ``activities`` (068 burn/pristine);
  * grading through the live P0.2/P0.3 pipeline -> ``grade_resolution.resolve_grade``;
  * reliability status of that interpretation -> the calibration-model row it pinned;
  * certification citing the EXACT pinned target version, gated on evidence
    eligibility -> ``goal_contracts.certify_from_administration``.

Cold discipline (§8.2): feedback and source restore are hidden until submission and
grade commitment. Burn (§8.3): render consumes pristine; success permanently
consumes; failure-before-feedback still records terminal failure; a post-feedback
practice-family successor may reuse the surface for learning (never terminal credit).

Degraded path (§1.1, A.3.4): a ``practice_only`` run -- minted when no fresh
assessment could be reserved at confirmation -- NEVER mints a terminal
certification; :func:`open_assessment` refuses on it and the run holds without a
terminal claim.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import goal_contracts as GC
from learnloop.services import golden_path_run as GPR
from learnloop.services.activities import (
    Administration,
    ExposureCollisionAtRender,
    ResolvedActivity,
    append_feedback,
    append_observation,
    append_practice_successor_proposal,
    cancel_reservation,
    evaluate_held_out_eligibility,
    open_administration,
    _json,
)
from learnloop.services.grade_resolution import PROJECTION_ALGORITHM_VERSION, resolve_grade

# Structural version pin for the persisted assessment-result artifact shape (§8.2).
ASSESSMENT_SNAPSHOT_SCHEMA_VERSION = 1

# Decision knob (design §E assessment/diff): the calibrated-certainty floor at/above
# which a covered boundary cell claims `demonstrated` with `calibrated` claim
# language; below it the same success reads as `developing`/`provisional`. It only
# shapes the boundary-diff CELL LABEL (a decision aid / display), never a posterior,
# eligibility, evidence mass, or the certification result -- those are the landed P0
# pipeline's. Registered `heuristic`; the sim band shows the label flips only inside
# a plausible range with no knife-edge active value.
DEMONSTRATED_CLAIM_CERTAINTY = 0.7

# Coarse observed classes that read as a passed cold assessment (§3.1 grade schema).
SUCCESS_CLASSES: frozenset[str] = frozenset({"success", "correct", "full"})


class PracticeOnlyNoAssessment(Exception):
    """A ``practice_only`` run has no reserved fresh assessment and never certifies
    (§1.1). Raised by :func:`open_assessment` so the run holds without a terminal
    claim rather than fabricating one."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        super().__init__(f"run {run_id}: practice_only makes no terminal claim")


@dataclass(frozen=True)
class ReserveStatus:
    """Result of the atomic reserve revalidation before render (§8.1)."""

    run_id: str
    valid: bool
    reason: str
    surface_id: str | None
    released: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssessmentResult:
    """The reliability-aware cold-assessment result DTO (§8.2 / P0 read-DTO rule)."""

    run_id: str
    administration_id: str
    passed: bool
    terminal: bool
    observed_class: str
    # P0 read-DTO required fields (spec_p0 §5).
    calibration_status: str
    calibration_model_version_id: str | None
    projection_algorithm_version: str | None
    target_contract_version_id: str | None
    cited_version: int
    point: float
    interval: dict[str, float]
    claim_language: str  # provisional | calibrated
    representative: bool
    review_state: dict[str, Any]
    surface_eligibility: str
    burn_reason: str
    eligibility_reason: str | None
    coverage: list[dict[str, Any]] = field(default_factory=list)
    practice_successor_event_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Reserve revalidation + render (§8.1, §8.2)
# ---------------------------------------------------------------------------

def _resolved_reserved_surface(repository: Repository, surface_id: str) -> ResolvedActivity:
    row = repository.resolved_activity_for_surface(surface_id)
    if row is None:
        raise ValueError(f"reserved assessment surface not found: {surface_id}")
    return ResolvedActivity(
        family_id=row["family_id"],
        family_version_id="",  # not read by open_administration; identity is the card/surface
        card_id=row["card_id"],
        card_version_id=row["card_version_id"],
        surface_id=row["surface_id"],
        purpose="assessment",
        card_contract_hash=row["card_contract_hash"],
        surface_hash=row["surface_hash"],
        fingerprint=row["fingerprint"],
    )


def validate_reserve(repository: Repository, *, run_id: str, clock: Clock | None = None) -> ReserveStatus:
    """Atomically recheck the reserved assessment surface against the global exposure
    ledger before render (§8.1). A collision-before-render releases the still-pristine
    reserve (``cancel_reservation`` -> ``released_unseen``) and requires an explicit
    fresh replacement; it never burns a colliding surface."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")
    surface_id = run["reserved_surface_id"]
    if surface_id is None:
        return ReserveStatus(run_id=run_id, valid=False, reason="no_reserve", surface_id=None)

    surface = repository.fetch_surface(surface_id)
    if surface is None:
        return ReserveStatus(run_id=run_id, valid=False, reason="surface_missing", surface_id=surface_id)

    eligibility = evaluate_held_out_eligibility(repository, surface=surface, purpose="assessment")
    if not eligibility.is_unseen:
        # Collision BEFORE render: release the unseen reserve, do not burn (§8.1).
        released = False
        reservation_id = run["reserved_reservation_id"]
        if reservation_id is not None:
            outcome = cancel_reservation(repository, reservation_id, clock=clock)
            released = outcome == "released_unseen"
        return ReserveStatus(
            run_id=run_id, valid=False, reason=eligibility.reason,
            surface_id=surface_id, released=released,
        )
    return ReserveStatus(run_id=run_id, valid=True, reason="unseen_in_learnloop", surface_id=surface_id)


def open_assessment(
    repository: Repository,
    *,
    run_id: str,
    idempotency_key: str,
    feedback_condition: str | None = None,
    clock: Clock | None = None,
) -> Administration:
    """Enter the assessment stage and open the cold administration at the burn
    boundary (§8.2). Advances the run ``ready_to_assess -> assessing`` (idempotent),
    revalidates the reserve, then renders. Raises :class:`PracticeOnlyNoAssessment`
    for a degraded run and :class:`ReserveInvalid` on a collision-before-render."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise ValueError(f"unknown golden-path run: {run_id}")
    if run["mode"] == "practice_only" or run["reserved_surface_id"] is None:
        raise PracticeOnlyNoAssessment(run_id)

    status = validate_reserve(repository, run_id=run_id, clock=clock)
    if not status.valid:
        # Degrade the run gracefully: it needs a fresh replacement / owner review; it
        # never burns the colliding surface and never claims a terminal result.
        state = GPR.project_run(repository, run_id)
        if state.current_state in GPR.ALLOWED_TRANSITIONS and "needs_review" in GPR.ALLOWED_TRANSITIONS[state.current_state]:
            GPR.advance(
                repository, run_id, to_state="needs_review",
                reason=f"assessment_reserve_invalid:{status.reason}",
                idempotency_key=idempotency_key + ":degrade", clock=clock,
            )
        raise ReserveInvalid(run_id, status)

    # ready_to_assess -> assessing (idempotent; skipped when already assessing).
    state = GPR.project_run(repository, run_id)
    if state.current_state == "ready_to_assess":
        GPR.advance(
            repository, run_id, to_state="assessing", reason="administer cold held-out assessment",
            idempotency_key=idempotency_key + ":enter", clock=clock,
        )

    resolved = _resolved_reserved_surface(repository, status.surface_id)
    try:
        return open_administration(
            repository,
            resolved=resolved,
            goal_id=run["goal_id"],
            target_contract_version_id=run["goal_contract_version_id"],
            target_support_hash=run["reserved_support_hash"],
            feedback_condition=feedback_condition,
            clock=clock,
        )
    except ExposureCollisionAtRender as exc:
        # Collision surfaced INSIDE the burn lock: refuse (never burn a colliding
        # assessment surface); require a fresh replacement (§8.1).
        raise ReserveInvalid(
            run_id, ReserveStatus(run_id=run_id, valid=False, reason=exc.reason, surface_id=status.surface_id)
        ) from exc


class ReserveInvalid(Exception):
    """The reserved assessment surface collided before render; a fresh replacement is
    required (§8.1). Carries the :class:`ReserveStatus` so the caller can surface it."""

    def __init__(self, run_id: str, status: ReserveStatus):
        self.run_id = run_id
        self.status = status
        super().__init__(f"run {run_id}: assessment reserve invalid ({status.reason})")


# ---------------------------------------------------------------------------
# Submit + grade + certify + burn/follow-up (§8.2, §8.3)
# ---------------------------------------------------------------------------

def submit_assessment(
    vault: Any,
    repository: Repository,
    *,
    run_id: str,
    administration_id: str,
    item: Any,
    surface_id: str,
    rubric_score: int,
    max_points: int,
    attempt_id: str,
    response_text: str | None = None,
    grader_confidence: float | None = None,
    has_fatal: bool = False,
    grading_source: str = "human",
    feedback_condition: str | None = None,
    reveal_feedback: bool = True,
    idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> AssessmentResult:
    """Submit the cold response, grade it through the live P0.2/P0.3 pipeline, cite
    the pinned target version, and record the reliability-aware result artifact (§8.2).

    Cold discipline: feedback is revealed ONLY here, after the grade is committed
    (``reveal_feedback``); a failure with feedback seeds a separate practice-family
    successor and nothing else (§8.3). ``feedback_condition='before_response'`` makes
    the observation non-terminal -> zero terminal credit (§4.5 / §12.5)."""

    observation_id = append_observation(
        repository,
        administration_id=administration_id,
        surface_id=surface_id,
        purpose="assessment",
        feedback_condition=feedback_condition,
        attempt_id=attempt_id,
        response_ref=attempt_id,
        clock=clock,
    )

    # Grade through the live pipeline (reuses this administration/observation -- no
    # second observation, no legacy posterior touched).
    gr = resolve_grade(
        vault,
        repository,
        item=item,
        purpose="assessment",
        grading_source=grading_source,
        attempt_id=attempt_id,
        response_text=response_text,
        rubric_score=rubric_score,
        max_points=max_points,
        grader_confidence=grader_confidence,
        has_fatal=has_fatal,
        administration_id=administration_id,
        observation_id=observation_id,
        surface_id=surface_id,
        feedback_condition=feedback_condition,
        clock=clock,
    )

    # Certify: cite the EXACT pinned target version, gated on evidence eligibility.
    citation = GC.certify_from_administration(repository, administration_id=administration_id)

    passed = gr.observed_class in SUCCESS_CLASSES and citation.terminal

    # Reliability status of the calibrated interpretation (§8.2 / P0 read-DTO rule):
    # the calibration-model row this grade pinned. A fallback/heuristic model reads
    # `provisional`; only a real calibrated model warrants `calibrated` language.
    model_row = (
        repository.find_calibration_model_by_hash(gr.calibration_model_hash)
        if gr.calibration_model_hash else None
    )
    calibration_status = (model_row.get("status") if model_row else None) or "heuristic"
    if gr.fallback_reason:
        calibration_status = "heuristic"
    calibrated = (
        calibration_status in ("simulation_validated", "live_calibrated")
        and citation.terminal
        and not gr.review_flag
    )
    claim_language = "calibrated" if calibrated else "provisional"

    # Surface eligibility / burn reason (§8.2 last field). Render consumed pristine;
    # a graded terminal observation permanently consumes the assessment surface.
    surface = repository.fetch_surface(surface_id)
    quarantined = any(
        e["kind"] == "quarantine" for e in repository.surface_lifecycle_history(surface_id)
    )
    surface_eligibility = "consumed"
    burn_reason = "assessment_rendered_and_graded"

    # Burn / follow-up (§8.3): on a failure with feedback revealed, seed a SEPARATE
    # practice-family successor (never terminal credit, never reuses pristine status).
    practice_successor_event_id: str | None = None
    if reveal_feedback and surface is not None:
        append_feedback(
            repository,
            surface=surface,
            administration_id=administration_id,
            purpose="assessment",
            timing="after_grade",
            clock=clock,
        )
        if not passed:
            practice_successor_event_id = append_practice_successor_proposal(
                repository,
                surface_id=surface_id,
                administration_id=administration_id,
                reason="failed_cold_assessment_practice_followup",
                clock=clock,
            )

    coverage = _coverage_from_blueprint(repository, repository.golden_path_run(run_id))

    result = AssessmentResult(
        run_id=run_id,
        administration_id=administration_id,
        passed=passed,
        terminal=citation.terminal,
        observed_class=gr.observed_class,
        calibration_status=calibration_status,
        calibration_model_version_id=gr.calibration_model_id,
        projection_algorithm_version=PROJECTION_ALGORITHM_VERSION,
        target_contract_version_id=citation.cited_version_id or None,
        cited_version=citation.cited_version,
        point=gr.certainty,
        interval=dict(gr.credible_interval),
        claim_language=claim_language,
        representative=citation.representative,
        review_state={
            "review_flag": gr.review_flag,
            "influence_flag": gr.influence_flag,
            "quarantined": quarantined,
            "fallback_reason": gr.fallback_reason,
        },
        surface_eligibility=surface_eligibility,
        burn_reason=burn_reason,
        eligibility_reason=citation.eligibility_reason,
        coverage=coverage,
        practice_successor_event_id=practice_successor_event_id,
    )

    repository.append_golden_path_artifact(
        run_id=run_id,
        kind="assessment_result",
        administration_id=administration_id,
        payload_json=_json({"schema_version": ASSESSMENT_SNAPSHOT_SCHEMA_VERSION, **result.as_dict()}),
        idempotency_key=(idempotency_key or attempt_id) + ":assessment_result",
        clock=clock,
    )
    return result


def _coverage_from_blueprint(repository: Repository, run: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """The blueprint recipe facet x capability cells the cold assessment covers (§8.2
    coverage field). A whole-task cold assessment samples every declared cell; one
    success does not certify unsupported cells -- the diff (B.9) reports per-cell."""

    if run is None:
        return []
    version = repository.task_blueprint_version(run["blueprint_version_id"])
    if version is None:
        return []
    import json as _json_mod

    spec = _json_mod.loads(version["spec_json"])
    cells: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for recipe in spec.get("solution_recipes") or []:
        components = list(recipe.get("all_of") or []) + list(recipe.get("any_of") or [])
        integ = recipe.get("integration")
        if integ:
            components.append(integ)
        for comp in components:
            facet, cap = comp.get("facet"), comp.get("capability")
            if facet is None or cap is None or (facet, cap) in seen:
                continue
            seen.add((facet, cap))
            cells.append({"facet": facet, "capability": cap})
    return cells


def assessment_result(repository: Repository, *, run_id: str) -> dict[str, Any] | None:
    """The latest persisted cold-assessment result artifact for the run (§8.2)."""

    row = repository.latest_golden_path_artifact(run_id, kind="assessment_result")
    if row is None:
        return None
    import json as _json_mod

    return _json_mod.loads(row["payload_json"])
