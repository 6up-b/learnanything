from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from learnloop.clock import FrozenClock
from learnloop.config import SeverityExampleConfig, default_severity_examples
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.facet_state_reader import facet_recall_state_for_lo
from learnloop.services.followups import FollowupDecision, evaluate_intervention_followup
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.vault_upgrade import KM_ALGORITHM_VERSION, LEGACY_ALGORITHM_VERSION
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_concept, upsert_learning_object, upsert_practice_item


CALIBRATION_NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
CALIBRATION_NOW_ISO = "2026-05-19T12:00:00Z"


SEVERITY_EXAMPLES: dict[str, SeverityExampleConfig] = default_severity_examples()


@dataclass(frozen=True)
class RecallCalibrationRow:
    scenario: str
    error_type: str | None
    expected_error_type: str
    event_severity: float
    severity_band: tuple[float, float]
    severity_in_band: bool
    error_sharpening: float
    mastery_delta_logit: float
    mastery_mean_after: float
    facet_id: str
    facet_recall_mean: float
    facet_recall_alpha: float
    facet_recall_beta: float
    facet_consecutive_failures: int
    bad_item_suspicion_prior: float
    bad_item_suspicion_posterior: float
    intervention_intent: str | None
    intervention_reason: str
    intervention_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "error_type": self.error_type,
            "expected_error_type": self.expected_error_type,
            "event_severity": self.event_severity,
            "severity_band": list(self.severity_band),
            "severity_in_band": self.severity_in_band,
            "error_sharpening": self.error_sharpening,
            "mastery_delta_logit": self.mastery_delta_logit,
            "mastery_mean_after": self.mastery_mean_after,
            "facet_id": self.facet_id,
            "facet_recall_mean": self.facet_recall_mean,
            "facet_recall_alpha": self.facet_recall_alpha,
            "facet_recall_beta": self.facet_recall_beta,
            "facet_consecutive_failures": self.facet_consecutive_failures,
            "bad_item_suspicion_prior": self.bad_item_suspicion_prior,
            "bad_item_suspicion_posterior": self.bad_item_suspicion_posterior,
            "intervention_intent": self.intervention_intent,
            "intervention_reason": self.intervention_reason,
            "intervention_status": self.intervention_status,
        }


def run_recall_calibration_harness(work_root: Path | None = None) -> list[RecallCalibrationRow]:
    if work_root is not None:
        work_root.mkdir(parents=True, exist_ok=True)
        return [_run_scenario(work_root / scenario, scenario) for scenario in SEVERITY_EXAMPLES]
    with TemporaryDirectory(prefix="learnloop_recall_calibration_", ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        return [_run_scenario(root / scenario, scenario) for scenario in SEVERITY_EXAMPLES]


def format_recall_calibration_table(rows: list[RecallCalibrationRow]) -> str:
    header = (
        "scenario | error_type | event_severity | band | error_sharpening | "
        "mastery_delta_logit | mastery_mean_after | facet_recall | bad_item_suspicion | intervention"
    )
    lines = [header]
    for row in rows:
        band = f"{row.severity_band[0]:.2f}-{row.severity_band[1]:.2f}"
        facet = (
            f"{row.facet_id}:mean={row.facet_recall_mean:.4f},"
            f"a/b={row.facet_recall_alpha:.3f}/{row.facet_recall_beta:.3f},"
            f"cf={row.facet_consecutive_failures}"
        )
        suspicion = f"{row.bad_item_suspicion_prior:.3f}->{row.bad_item_suspicion_posterior:.3f}"
        intervention = f"{row.intervention_intent or 'none'}:{row.intervention_status}:{row.intervention_reason}"
        lines.append(
            " | ".join(
                [
                    row.scenario,
                    row.error_type or "none",
                    f"{row.event_severity:.4f}",
                    band,
                    f"{row.error_sharpening:.4f}",
                    f"{row.mastery_delta_logit:.4f}",
                    f"{row.mastery_mean_after:.4f}",
                    facet,
                    suspicion,
                    intervention,
                ]
            )
        )
    return "\n".join(lines)


def assert_recall_calibration_bands(rows: list[RecallCalibrationRow]) -> None:
    failures: list[str] = []
    for row in rows:
        if row.error_type != row.expected_error_type:
            failures.append(f"{row.scenario} error_type={row.error_type!r}, expected {row.expected_error_type!r}")
        if not row.severity_in_band:
            failures.append(f"{row.scenario}={row.event_severity:.4f} not in {row.severity_band}")
    if failures:
        details = ", ".join(
            failures
        )
        raise AssertionError(details)


def _run_scenario(root: Path, scenario: str) -> RecallCalibrationRow:
    vault, repository = _fresh_calibration_vault(root)
    examples = vault.config.recall_coverage.severity_examples
    if scenario == "first_dont_know":
        result = _attempt(repository, vault, attempt_type="dont_know", points=4)
    elif scenario == "second_same_item_dont_know":
        _attempt(repository, vault, attempt_type="dont_know", points=4)
        result = _attempt(repository, vault, attempt_type="dont_know", points=4, days=1)
    elif scenario == "second_same_facet_dont_know":
        _attempt(repository, vault, attempt_type="dont_know", points=4)
        result = _attempt(
            repository,
            vault,
            practice_item_id="pi_calibration_repair",
            attempt_type="dont_know",
            points=4,
            days=1,
        )
    elif scenario == "hinted_dont_know":
        result = _attempt(repository, vault, attempt_type="dont_know", points=4, hints_used=2)
    elif scenario == "arithmetic_slip":
        result = _attempt(repository, vault, points=3, error_type="arithmetic_slip")
    elif scenario == "ambiguous_item":
        repository.upsert_mastery_state(
            MasteryState("lo_calibration", 2.0, 0.5, 4, CALIBRATION_NOW_ISO, "mvp-0.1", CALIBRATION_NOW_ISO)
        )
        repository.upsert_practice_item_quality_state(
            {
                "practice_item_id": "pi_calibration_main",
                "bad_item_suspicion": 0.70,
                "evidence_count": 3,
                "suspicion_reasons": ["seeded_ambiguous_item"],
                "last_flagged_at": CALIBRATION_NOW_ISO,
                "algorithm_version": "mvp-0.1",
                "updated_at": CALIBRATION_NOW_ISO,
            }
        )
        result = _attempt(repository, vault, points=0, error_type="recall_failure")
    else:  # pragma: no cover - guarded by SEVERITY_EXAMPLES
        raise ValueError(f"Unknown calibration scenario {scenario}")

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    event = (repository.error_events_for_attempt(result.attempt_id) or [{}])[0]
    debug = repository.attempt_debug_payload(result.attempt_id) or {}
    facet = facet_recall_state_for_lo(vault, repository, result.learning_object_id, "recall")
    decision = _intervention_decision(vault, repository, result, event, debug)
    low, high = examples[scenario].expected_severity_band
    severity = float(event.get("severity") or 0.0)
    delta = (debug.get("severity_traces") or {})
    _ = delta  # keep debug extraction explicit for future harness columns
    posterior_delta = (repository.latest_attempt_surprise(result.attempt_id) or {}).get("posterior_delta") or {}
    return RecallCalibrationRow(
        scenario=scenario,
        error_type=attempt.get("error_type") if attempt else None,
        expected_error_type=examples[scenario].expected_error_type,
        event_severity=severity,
        severity_band=(float(low), float(high)),
        severity_in_band=float(low) <= severity <= float(high),
        error_sharpening=float((debug.get("error_impact_trace") or {}).get("error_sharpening", 1.0)),
        mastery_delta_logit=float(posterior_delta.get("mu_after", 0.0) - posterior_delta.get("mu_before", 0.0)),
        mastery_mean_after=float(result.mastery_mean),
        facet_id="recall",
        facet_recall_mean=float(facet.recall_mean if facet is not None else 0.5),
        facet_recall_alpha=float(facet.recall_alpha if facet is not None else 1.0),
        facet_recall_beta=float(facet.recall_beta if facet is not None else 1.0),
        facet_consecutive_failures=int(facet.consecutive_failures if facet is not None else 0),
        bad_item_suspicion_prior=float(debug.get("prior_bad_item_suspicion", 0.0)),
        bad_item_suspicion_posterior=float(debug.get("bad_item_suspicion", 0.0)),
        intervention_intent=decision.intent,
        intervention_reason=decision.reason,
        intervention_status=_intervention_status(decision),
    )


def _fresh_calibration_vault(root: Path):
    clock = FrozenClock(CALIBRATION_NOW)
    init_vault(root, clock=clock)
    # The severity examples this harness asserts against use the legacy
    # (mvp-0.6) error vocabulary and bands; `learnloop init` now writes
    # mvp-0.7, so pin the scaffold vault to the model being calibrated.
    config_path = root / "learnloop.toml"
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace(
            f'algorithm_version = "{KM_ALGORITHM_VERSION}"',
            f'algorithm_version = "{LEGACY_ALGORITHM_VERSION}"',
            1,
        ),
        encoding="utf-8",
    )
    add_subject(root, "calibration", "Calibration", clock=clock)
    upsert_concept(
        root,
        "calibration_recall",
        {
            "title": "Calibration recall",
            "type": "skill",
            "description": "Harness target.",
            "aliases": [],
            "tags": [],
        },
        clock=clock,
    )
    upsert_learning_object(
        root,
        {
            "id": "lo_calibration",
            "title": "Recall calibration target",
            "subjects": ["calibration"],
            "concept": "calibration_recall",
            "knowledge_type": "definition",
            "summary": "Recall a compact fact.",
            "status": "active",
            "tags": [],
        },
        clock=clock,
    )
    base_item = {
        "learning_object_id": "lo_calibration",
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "criterion_facet_weights": {"correctness": {"recall": 1.0}},
        "expected_answer": "calibration fact",
        "difficulty": 0.55,
        "retrieval_demand": 1.0,
        "surface_family": "calibration-recall",
        "repair_targets": ["recall"],
        "tags": [],
        "hints": ["Think of the calibration fact.", "It is the expected answer."],
        "hint_policy": {
            "max_useful_hints": 2,
            "fsrs_rating_cap_by_hint": {"1": "good", "2": "hard"},
            "mastery_alpha_dampening_by_hint": {"1": 0.7, "2": 0.5},
            "coverage_surface_dampening_by_hint": {"1": 0.9, "2": 0.8},
        },
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct fact."}],
            "fatal_errors": [],
        },
        "provenance": {"origin": "import", "source_refs": []},
    }
    upsert_practice_item(root, {"id": "pi_calibration_main", "prompt": "State the calibration fact.", **base_item}, clock=clock)
    upsert_practice_item(root, {"id": "pi_calibration_repair", "prompt": "Repair the calibration fact.", **base_item}, clock=clock)
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    sync_vault_state(vault, repository, clock=clock)
    return vault, repository


def _attempt(
    repository: Repository,
    vault,
    *,
    points: float,
    practice_item_id: str = "pi_calibration_main",
    attempt_type: str = "independent_attempt",
    error_type: str | None = None,
    hints_used: int = 0,
    days: int = 0,
):
    clock = FrozenClock(CALIBRATION_NOW + timedelta(days=days))
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=practice_item_id,
            learner_answer_md="calibration response",
            attempt_type=attempt_type,
            hints_used=hints_used,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4, error_type=error_type),
        clock=clock,
    )


def _intervention_decision(
    vault,
    repository: Repository,
    result,
    event: dict,
    debug: dict,
) -> FollowupDecision:
    return evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(event),
        max_error_severity=float(event.get("severity") or 0.0),
        target_facets=list((debug.get("covered_facets") or {}).keys()),
        bad_item_suspicion=float(debug.get("bad_item_suspicion", 0.0)),
        available_minutes=30,
    )


def _intervention_status(decision: FollowupDecision) -> str:
    if decision.triggered:
        return f"queued:{decision.practice_item_id}"
    if decision.need_id:
        return f"need:{decision.need_id}"
    if decision.suppressed_actions:
        return "suppressed"
    return "none"
