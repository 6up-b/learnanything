"""Issuance and reality-based resolution of frozen learner forecasts."""

from __future__ import annotations

from datetime import UTC
import hashlib
import json
from typing import Any, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid


RESOLUTION_RULE_VERSION = "forecast-resolution-v1"


class ForecastError(ValueError):
    pass


def issue_forecast(
    repository: Repository,
    *,
    goal_id: str,
    kind: str,
    input_snapshot_hash: str,
    algorithm_version: str,
    horizon: str,
    target_metric: str,
    predicted_value: float,
    model_coverage: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if kind not in {"decay", "pace", "plan"}:
        raise ForecastError("kind must be decay, pace, or plan")
    if parse_utc(horizon) is None:
        raise ForecastError("horizon must be an ISO timestamp")
    return repository.insert_forecast(
        {
            "id": new_ulid(),
            "goal_id": goal_id,
            "kind": kind,
            "issued_at": utc_now_iso(clock),
            "as_of_input_snapshot_hash": input_snapshot_hash,
            "algorithm_version": algorithm_version,
            "resolution_rule_version": RESOLUTION_RULE_VERSION,
            "horizon": horizon,
            "target_metric": target_metric,
            "predicted_value": float(predicted_value),
            "model_coverage": dict(model_coverage or {}),
            "status": "open",
        }
    )


def _scoped_attempts(repository: Repository, forecast: Mapping[str, Any]) -> list[dict[str, Any]]:
    coverage = forecast.get("model_coverage") or {}
    lo_ids = {str(value) for value in coverage.get("learning_object_ids", [])}
    facet_ids = {str(value) for value in coverage.get("facet_ids", [])}
    issued = parse_utc(str(forecast["issued_at"]))
    horizon = parse_utc(str(forecast["horizon"]))
    if issued is None or horizon is None:
        return []
    scoped: list[dict[str, Any]] = []
    for attempt in repository.list_all_attempts():
        created = parse_utc(attempt.get("created_at"))
        if created is None or created < issued or created > horizon:
            continue
        attempt_facets = _attempt_facets(attempt)
        if (lo_ids and str(attempt.get("learning_object_id")) in lo_ids) or (
            facet_ids and attempt_facets & facet_ids
        ):
            scoped.append(attempt)
    return scoped


def _cold_outcomes(repository: Repository, forecast: Mapping[str, Any], now) -> list[dict[str, Any]]:
    coverage = forecast.get("model_coverage") or {}
    lo_ids = {str(value) for value in coverage.get("learning_object_ids", [])}
    facet_ids = {str(value) for value in coverage.get("facet_ids", [])}
    horizon = parse_utc(str(forecast["horizon"]))
    if horizon is None:
        return []
    outcomes: list[dict[str, Any]] = []
    for attempt in repository.list_all_attempts():
        created = parse_utc(attempt.get("created_at"))
        if created is None or created < horizon or created > now:
            continue
        attempt_facets = _attempt_facets(attempt)
        in_scope = (lo_ids and str(attempt.get("learning_object_id")) in lo_ids) or (
            facet_ids and bool(attempt_facets & facet_ids)
        )
        if not in_scope or attempt.get("correctness") is None:
            continue
        if attempt.get("primed") or int(attempt.get("hints_used") or 0) > 0:
            continue
        if attempt.get("attempt_type") in {"hinted_attempt", "guided_walkthrough", "self_report"}:
            continue
        outcomes.append(attempt)
    return outcomes


def _attempt_facets(attempt: Mapping[str, Any]) -> set[str]:
    """Read facets from either a decoded attempt or the repository's raw row."""

    values = attempt.get("evidence_facets")
    if values is None:
        raw = attempt.get("evidence_facets_json")
        try:
            values = json.loads(str(raw)) if raw else []
        except (TypeError, ValueError, json.JSONDecodeError):
            values = []
    return {str(value) for value in values or []}


def resolve_due_forecasts(
    repository: Repository,
    *,
    current_estimates: Mapping[str, float] | None = None,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Resolve due rows only from outcomes; estimates become projection drift."""

    clock = clock or SystemClock()
    now = clock.now().astimezone(UTC)
    now_iso = utc_now_iso(clock)
    resolved: list[dict[str, Any]] = []
    for forecast in repository.due_forecasts(now_iso):
        drift = None
        if current_estimates and forecast["id"] in current_estimates:
            drift = float(current_estimates[forecast["id"]]) - float(forecast["predicted_value"])

        interval_attempts = _scoped_attempts(repository, forecast)
        if forecast["kind"] == "decay" and interval_attempts:
            row = repository.update_forecast_resolution(
                forecast["id"], status="censored", resolved_at=now_iso,
                projection_drift=drift,
            )
        elif forecast["kind"] == "pace":
            issued = parse_utc(forecast["issued_at"])
            horizon = parse_utc(forecast["horizon"])
            days = max((horizon - issued).total_seconds() / 86400.0, 1.0) if issued and horizon else 1.0
            row = repository.update_forecast_resolution(
                forecast["id"], status="resolved", resolved_at=now_iso,
                resolved_value=len(interval_attempts) / days,
                projection_drift=drift,
            )
        else:
            outcomes = _cold_outcomes(repository, forecast, now)
            if outcomes:
                actual = sum(float(item["correctness"]) for item in outcomes) / len(outcomes)
                row = repository.update_forecast_resolution(
                    forecast["id"], status="resolved", resolved_at=now_iso,
                    resolved_value=actual, projection_drift=drift,
                )
            else:
                row = repository.update_forecast_resolution(
                    forecast["id"], status="unobservable", resolved_at=now_iso,
                    projection_drift=drift,
                )
        if row is not None:
            resolved.append(row)
    return resolved


def active_forecasts(repository: Repository, goal_id: str) -> dict[str, dict[str, Any]]:
    """Read-only: the current open issued forecast per kind for a goal.

    Presentations reference issued forecast rows; rendering never writes one
    (spec §4.1). Returns ``{kind: {"id", "issued_at"}}`` for each kind that has
    an open row (most recent wins); kinds with no open row are simply absent.
    """

    latest: dict[str, dict[str, Any]] = {}
    for row in repository.open_forecasts(goal_id):
        # open_forecasts is ordered oldest-first, so the last write per kind is
        # the most recently issued open forecast.
        latest[str(row["kind"])] = {"id": row["id"], "issued_at": row["issued_at"]}
    return latest


def forecast_track_record(repository: Repository, goal_id: str | None = None) -> dict[str, Any]:
    rows = repository.list_forecasts(goal_id)
    by_kind: dict[str, dict[str, Any]] = {}
    for kind in ("decay", "pace", "plan"):
        selected = [row for row in rows if row["kind"] == kind]
        resolved = [row for row in selected if row["status"] == "resolved"]
        accuracy = None
        if resolved:
            accuracy = sum(
                abs(float(row["predicted_value"]) - float(row["resolved_value"]))
                for row in resolved
                if row["resolved_value"] is not None
            ) / len(resolved)
        by_kind[kind] = {
            "issued": len(selected),
            "resolved": len(resolved),
            "censored": sum(row["status"] == "censored" for row in selected),
            "unobservable": sum(row["status"] == "unobservable" for row in selected),
            "mean_absolute_error": accuracy,
        }
    return {"by_kind": by_kind, "forecasts": rows}


def issue_goal_forecasts(vault, repository: Repository, *, clock: Clock | None = None) -> list[dict[str, Any]]:
    """Issue material decay/pace snapshots at session start, never at render."""

    from learnloop.services.goal_pace import compute_goal_pace
    from learnloop.services.goal_projection import goal_report, resolve_goal_scope

    issued: list[dict[str, Any]] = []
    for goal in vault.goals:
        if goal.status != "active":
            continue
        report = goal_report(vault, repository, goal, clock=clock)
        scope = resolve_goal_scope(vault, goal, repository)
        coverage = {
            "learning_object_ids": sorted(scope),
            "facet_ids": sorted({facet for facets in scope.values() for facet in facets}),
            "decay_estimated": report.decay_estimated_count,
            "held_flat": report.held_flat_count,
        }
        snapshot = {
            "goal": goal.id,
            "horizon": report.horizon.isoformat(),
            "facets": [
                {
                    "lo": facet.learning_object_id,
                    "facet": facet.facet_id,
                    "ready": round(facet.predicted_current, 8),
                    "projected": round(facet.predicted_at_horizon, 8),
                    "decay": facet.decay_estimated,
                }
                for facet in report.facets
            ],
        }
        snapshot_hash = hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if report.predicted_recall_mean is not None and report.decay_estimated_count > 0:
            issued.append(
                issue_forecast(
                    repository,
                    goal_id=goal.id,
                    kind="decay",
                    input_snapshot_hash=snapshot_hash,
                    algorithm_version=vault.config.algorithms.algorithm_version,
                    horizon=report.horizon.isoformat().replace("+00:00", "Z"),
                    target_metric="cold_correctness",
                    predicted_value=report.predicted_recall_mean,
                    model_coverage=coverage,
                    clock=clock,
                )
            )
        pace = compute_goal_pace(vault, repository, goal, report, clock=clock)
        pace_hash = hashlib.sha256(
            f"{snapshot_hash}:pace:{pace.attempts_per_day:.8f}".encode("utf-8")
        ).hexdigest()
        issued.append(
            issue_forecast(
                repository,
                goal_id=goal.id,
                kind="pace",
                input_snapshot_hash=pace_hash,
                algorithm_version=vault.config.algorithms.algorithm_version,
                horizon=report.horizon.isoformat().replace("+00:00", "Z"),
                target_metric="qualifying_attempts_per_day",
                predicted_value=pace.attempts_per_day,
                model_coverage=coverage,
                clock=clock,
            )
        )
    return issued
