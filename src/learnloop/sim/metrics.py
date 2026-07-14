"""End-of-run simulation metrics: belief vs truth, calibration, detection.

Everything returned is plain JSON-serializable data. Random ids (attempt/event
ULIDs) are deliberately excluded so reports are bit-identical across runs with
the same seed.
"""

from __future__ import annotations

from math import log
from typing import TYPE_CHECKING, Any, Iterable

from learnloop.db.repositories import Repository
from learnloop.services.facet_diagnostics import mastery_diagnostic_view
from learnloop.services.mastery import display_mastery
from learnloop.vault.models import LoadedVault

if TYPE_CHECKING:  # pragma: no cover - import cycle guard (runner imports metrics)
    from learnloop.sim.runner import SimAttemptRecord, SimDayRecord
    from learnloop.sim.student import SyntheticStudent

_P_CLIP = 1e-3


def build_metrics(
    vault: LoadedVault,
    repository: Repository,
    student: "SyntheticStudent",
    *,
    attempts: list["SimAttemptRecord"],
    day_records: list["SimDayRecord"],
    detection_days: dict[str, dict[str, Any]],
    lo_facet_weights: dict[str, dict[str, float]],
    final_day: float,
    goal_tracking: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "belief_vs_truth": _belief_vs_truth(
            vault, repository, student, lo_facet_weights, day_records, final_day
        ),
        "calibration": _calibration(attempts),
        "misconceptions": _misconceptions(vault, repository, student, attempts, detection_days),
        "fsrs": _fsrs_sanity(attempts),
        "counts": _counts(repository, attempts),
        "goals": _goals(goal_tracking or {}, day_records),
    }


# -- belief vs truth --------------------------------------------------------


def _belief_vs_truth(
    vault: LoadedVault,
    repository: Repository,
    student: "SyntheticStudent",
    lo_facet_weights: dict[str, dict[str, float]],
    day_records: list["SimDayRecord"],
    final_day: float,
) -> dict[str, Any]:
    mastery_states = repository.mastery_states()
    per_lo: list[dict[str, Any]] = []
    sign_hits = 0
    for lo_id in sorted(lo_facet_weights):
        facet_weights = lo_facet_weights[lo_id]
        state = mastery_states.get(lo_id)
        if state is None or state.last_evidence_at is None:
            continue
        belief = display_mastery(state).mastery_mean
        truth = sum(
            weight * student.mastery_at(facet, final_day)
            for facet, weight in facet_weights.items()
        )
        agrees = (belief >= 0.5) == (truth >= 0.5)
        sign_hits += 1 if agrees else 0
        per_lo.append(
            {
                "learning_object_id": lo_id,
                "belief_mastery_mean": round(belief, 6),
                "true_mastery": round(truth, 6),
                "abs_error": round(abs(belief - truth), 6),
                "sign_agreement": agrees,
            }
        )
    daily = [record.belief_mae for record in day_records if record.belief_mae is not None]
    return {
        "per_learning_object": per_lo,
        "mae": _round(_mean([entry["abs_error"] for entry in per_lo])),
        "sign_agreement_rate": _round(sign_hits / len(per_lo)) if per_lo else None,
        "daily_mae_first": _round(daily[0]) if daily else None,
        "daily_mae_last": _round(daily[-1]) if daily else None,
        "daily_mae": [_round(value) for value in daily],
    }


def canonical_facet_belief_mae(
    repository: Repository,
    student: "SyntheticStudent",
    final_day: float,
    *,
    facet_truth_key=None,
) -> dict[str, Any]:
    """KM2 sim re-key (§16): belief-vs-truth MAE over canonical facet parents.

    Reads the shared canonical ``facet_recall_state`` aggregate (post-KM2) rather
    than per-LO keys, so the same facet exercised under several LOs is scored
    once against one truth value. This is the aggregation that must improve vs the
    per-LO baseline: pooled evidence reaches a confident belief with fewer
    attempts. ``facet_truth_key`` maps a canonical facet id to the student truth
    facet (defaults to identity).
    """

    key = facet_truth_key or (lambda facet_id: facet_id)
    errors: list[float] = []
    per_facet: list[dict[str, Any]] = []
    seen: set[str] = set()
    for state in repository.canonical_facet_recall_states():
        if state.practice_item_id is not None:
            continue  # aggregate parents only
        if state.facet_id in seen:
            # Distinct capabilities share one truth; score the shared parent once
            # by preferring the 'shared'/first-seen aggregate deterministically.
            continue
        seen.add(state.facet_id)
        belief = state.recall_mean
        truth = student.mastery_at(key(state.facet_id), final_day)
        err = abs(belief - truth)
        errors.append(err)
        per_facet.append(
            {
                "facet_id": state.facet_id,
                "belief_mean": round(belief, 6),
                "true_mastery": round(truth, 6),
                "abs_error": round(err, 6),
            }
        )
    return {
        "mae": _round(_mean(errors)),
        "n_facets": len(errors),
        "per_facet": per_facet,
    }


# -- calibration ------------------------------------------------------------


def _calibration(attempts: list["SimAttemptRecord"]) -> dict[str, Any]:
    pairs = [
        (attempt.predicted_correctness, attempt.observed_correctness)
        for attempt in attempts
        if attempt.predicted_correctness is not None
    ]
    if not pairs:
        return {"n": 0, "brier": None, "log_loss": None}
    brier = _mean([(p - y) ** 2 for p, y in pairs])
    log_loss = _mean(
        [
            -(y * log(_clip(p)) + (1.0 - y) * log(_clip(1.0 - p)))
            for p, y in pairs
        ]
    )
    return {"n": len(pairs), "brier": _round(brier), "log_loss": _round(log_loss)}


# -- misconception detection --------------------------------------------------


def _misconceptions(
    vault: LoadedVault,
    repository: Repository,
    student: "SyntheticStudent",
    attempts: list["SimAttemptRecord"],
    detection_days: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    events = _error_event_rows(repository)
    planted = {m.error_type: m for m in student.profile.misconceptions}
    per_planted: list[dict[str, Any]] = []
    for error_type, misconception in sorted(planted.items()):
        tracker = detection_days.get(error_type, {})
        attempts_to_detection = None
        for index, attempt in enumerate(attempts, start=1):
            if error_type in attempt.error_types:
                attempts_to_detection = index
                break
        matching = [event for event in events if event["error_type"] == error_type]
        end_state = _final_facet_state(vault, repository, misconception.facet_id)
        per_planted.append(
            {
                "error_type": error_type,
                "facet_id": misconception.facet_id,
                "planted_strength": misconception.strength,
                "residual_strength": _round(
                    student.misconception_strengths.get(misconception.facet_id, 0.0)
                ),
                "error_events": len(matching),
                "error_events_resolved": sum(
                    1 for event in matching if event["status"] == "resolved"
                ),
                "detected": bool(matching),
                "first_error_event_day": tracker.get("error_event_day"),
                "first_known_gap_day": tracker.get("known_gap_day"),
                "known_gap_top_hypothesis": tracker.get("known_gap_top_hypothesis"),
                "attempts_to_detection": attempts_to_detection,
                "final_facet_state": end_state,
            }
        )
    false_positives = sorted(
        {
            event["error_type"]
            for event in events
            if event["is_misconception"] and event["error_type"] not in planted
        }
    )
    return {"planted": per_planted, "false_positive_misconception_types": false_positives}


def _final_facet_state(
    vault: LoadedVault, repository: Repository, facet_id: str
) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    for lo_id in sorted(vault.learning_objects):
        view = mastery_diagnostic_view(vault, repository, lo_id)
        for facet in view["facets"]:
            if facet["facet_id"] != facet_id:
                continue
            marginal = facet.get("hypothesis_marginal") or {}
            states.append(
                {
                    "learning_object_id": lo_id,
                    "state": facet["state"],
                    "top_hypothesis": max(marginal, key=marginal.get) if marginal else None,
                }
            )
    return states


# -- goal attainment ----------------------------------------------------------


def _goals(
    goal_tracking: dict[str, dict[str, Any]],
    day_records: list["SimDayRecord"],
) -> dict[str, Any]:
    """Due-date attainment and post-due retention per goal.

    The truth snapshots come from the runner (captured on each goal's due day,
    see ``_track_goals_end_of_day``): ``truth_at_due`` is the student's *true*
    facet mastery at the due day; ``truth_due_plus_30`` is the analytic
    no-practice projection 30 days later — together they expose the
    cram-vs-space tradeoff a goal quota makes. ``frontier_empty_day`` is the
    first day the *belief-side* goal frontier reached zero at-risk facets.
    """

    per_goal: list[dict[str, Any]] = []
    for goal_id in sorted(goal_tracking):
        info = goal_tracking[goal_id]
        target = float(info["target_recall"])
        truth_at_due: dict[str, float] = info["truth_at_due"]
        truth_plus_30: dict[str, float] = info["truth_due_plus_30"]
        total = len(info["scope_facets"])
        frontier_empty_day = next(
            (
                record.day
                for record in day_records
                if record.goal_at_risk_facets.get(goal_id) == 0
            ),
            None,
        )
        belief_total = info["belief_total"]
        per_goal.append(
            {
                "goal_id": goal_id,
                "due_day": info["due_day"],
                "snapshot_day": info["snapshot_day"],
                "target_recall": target,
                "scope_facet_count": total,
                "truth_at_target_fraction_at_due": _round(
                    _fraction_at_target(truth_at_due, target)
                ),
                "truth_mean_recall_at_due": _round(_mean(truth_at_due.values())),
                "truth_at_target_fraction_due_plus_30": _round(
                    _fraction_at_target(truth_plus_30, target)
                ),
                "truth_mean_recall_due_plus_30": _round(_mean(truth_plus_30.values())),
                "belief_on_track_fraction_at_due": _round(
                    info["belief_on_track"] / belief_total if belief_total else None
                ),
                "frontier_empty_day": frontier_empty_day,
            }
        )
    return {"per_goal": per_goal}


def _fraction_at_target(values: dict[str, float], target: float) -> float | None:
    if not values:
        return None
    return sum(1 for value in values.values() if value >= target) / len(values)


# -- FSRS sanity --------------------------------------------------------------


def _fsrs_sanity(attempts: list["SimAttemptRecord"]) -> dict[str, Any]:
    values = [
        attempt.retrievability_prior
        for attempt in attempts
        if attempt.retrievability_prior is not None
    ]
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean_retrievability_at_practice": _round(_mean(values)),
        "min_retrievability_at_practice": _round(min(values)),
        "share_below_half": _round(sum(1 for value in values if value < 0.5) / len(values)),
    }


# -- counts -------------------------------------------------------------------


def _counts(repository: Repository, attempts: list["SimAttemptRecord"]) -> dict[str, Any]:
    events = _error_event_rows(repository)
    by_type: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for attempt in attempts:
        by_type[attempt.attempt_type] = by_type.get(attempt.attempt_type, 0) + 1
        by_source[attempt.source] = by_source.get(attempt.source, 0) + 1
    return {
        "attempts": len(attempts),
        "attempts_by_type": dict(sorted(by_type.items())),
        "attempts_by_source": dict(sorted(by_source.items())),
        "followups_triggered": sum(1 for attempt in attempts if attempt.followup_triggered),
        "probe_attempts": by_type.get("diagnostic_probe", 0),
        "dont_know_attempts": by_type.get("dont_know", 0),
        "teach_back_attempts": by_type.get("teach_back", 0),
        "error_events_created": len(events),
        "error_events_resolved": sum(1 for event in events if event["status"] == "resolved"),
        "misconception_error_events": sum(1 for event in events if event["is_misconception"]),
    }


def _error_event_rows(repository: Repository) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT error_type, status, is_misconception FROM error_events ORDER BY created_at"
        ).fetchall()
    return [
        {
            "error_type": row["error_type"],
            "status": row["status"],
            "is_misconception": bool(row["is_misconception"]),
        }
        for row in rows
    ]


# -- small numeric helpers ------------------------------------------------------


def _mean(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def _clip(value: float) -> float:
    return min(1.0 - _P_CLIP, max(_P_CLIP, value))


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)
