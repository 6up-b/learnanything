"""RO5 §9 item 3: the goal-date read, a stand-in in two stages, both versioned sensors.

A goal's date is observed at most once, so the read is:

1. **the pool forecast at lag L, calibrated by the randomized checks** (§9 item 2): the memory model's forecast of
   success on an unseen item of the topic (the traces' frozen ``m⁰`` at each check's own lag, from the newest trace
   before the check's day) against the check's §6.2 label, through a Bayesian logistic recalibration
   ``logit P = a + b·logit f`` (prior :data:`CALIBRATION_PRIOR_MEAN` / :data:`CALIBRATION_PRIOR_VARIANCE`, a labelled
   seed: the forecast taken at its word, ``a = 0, b = 1``), the memory model's own Laplace fit;
2. **the pool-to-goal transfer**, a slope per goal type (``exam`` when the goal sits an exam, else ``dated``) with a
   wide prior (``logit G = α + β·logit P``, ``α ~ N(0, s²)``, ``β ~ N(1, s²)``, ``s = goal_transfer_prior_sd``), fitted
   on the imported exam results (``goals/exam_seeding``'s ``exam_evidence`` rows on the goal's date) and any sittings
   (``exam_attempt`` rows), each paired with the calibrated pool forecast frozen before the date.

**"Am I ready?"** stays a button: its reads (the Check once commitments it creates, ``via = deliverable_ready``) are
listed flagged **self-selected** and never enter either fit, and a ready read between a pair's forecast and its date
is counted on that pair as an **exposure** (the forecast did not see it). Read-only; no model call.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
import json
import math
from typing import Any

from learnloop.router_objective import checks as C
from learnloop.router_objective import memory as M

CALIBRATION_VERSION = "ro5_pool_calibration_v1"
TRANSFER_VERSION = "ro5_goal_transfer_v1"
#: The recalibration's prior: (a, b, unused) means and variances. A labelled seed: the forecast taken at its word.
CALIBRATION_PRIOR_MEAN: tuple[float, float, float] = (0.0, 1.0, 0.0)
CALIBRATION_PRIOR_VARIANCE: tuple[float, float, float] = (1.0, 1.0, 1.0)
READY_VIA = "deliverable_ready"
SELF_SELECTED = "self-selected: the learner pressed Am I ready?; never in a fit"


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def _logit(p: float) -> float:
    p = min(max(float(p), 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _traces(connection: Any) -> list[dict[str, Any]]:
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_objective_traces'"
                          ).fetchone() is None:
        return []
    out = []
    for decision_id, local_date, created_at, trace_json in connection.execute(
            "SELECT decision_id, local_date, created_at, trace_json FROM router_objective_traces "
            "WHERE decision_kind = 'plan_block' ORDER BY created_at, id"):
        uses = (json.loads(trace_json).get("evaluation") or {}).get("uses") or {}
        out.append({"decision_id": decision_id, "local_date": local_date, "created_at": created_at,
                    "topics": {str(t["lo"]): t.get("m0") or [] for t in uses.get("topics") or ()},
                    "dated": list(uses.get("dated") or ())})
    return out


def calibration_rows(connection: Any, *, through: str) -> list[tuple[float, None, float, int]]:
    """``(logit forecast, None, Y, lag)`` for each completed randomized check with a frozen forecast at its lag."""

    traces = _traces(connection)
    rows = []
    for entry in C.resolve(connection, through=through):
        if entry.status != "completed" or entry.outcome is None:
            continue
        before = [t for t in traces if str(t["local_date"]) < entry.local_date and entry.topic in t["topics"]]
        if not before:
            continue
        latest = before[-1]
        lag = (date.fromisoformat(entry.local_date) - date.fromisoformat(str(latest["local_date"]))).days
        m0 = latest["topics"][entry.topic]
        if 1 <= lag <= len(m0) and m0[lag - 1] is not None:
            rows.append((_logit(float(m0[lag - 1])), None, float(entry.outcome), lag))
    return rows


def calibration(connection: Any, *, through: str) -> dict[str, Any]:
    rows = calibration_rows(connection, through=through)
    prior = M.Combiner(mean=CALIBRATION_PRIOR_MEAN, variance=CALIBRATION_PRIOR_VARIANCE, source="prior")
    fitted = M.fit_combiner([(row[0], None, row[2]) for row in rows], prior=prior) if rows else prior
    lags: dict[int, int] = {}
    for row in rows:
        lags[row[3]] = lags.get(row[3], 0) + 1
    return {"version": CALIBRATION_VERSION, "a": fitted.mean[0], "b": fitted.mean[1],
            "variance": list(fitted.variance[:2]), "n": len(rows), "by_lag": dict(sorted(lags.items())),
            "source": fitted.source, "basis": "randomized checks (§9 item 2) against the traces' frozen pool forecast"}


def calibrated(forecast: float, fit: Mapping[str, Any]) -> float:
    return _sigmoid(float(fit["a"]) + float(fit["b"]) * _logit(forecast))


def goal_type(goal: Any) -> str:
    return "exam" if bool(getattr(getattr(goal, "exam", None), "enabled", False)) else "dated"


def _ready_reads(connection: Any) -> list[dict[str, Any]]:
    """Every "Am I ready?" Check once (its goal, LO, creation) and its first answer, flagged self-selected."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'commitment_versions'"
                          ).fetchone() is None:
        return []
    out = []
    for provenance, created in connection.execute(
            "SELECT provenance_json, created_at FROM commitment_versions WHERE provenance_json LIKE ? "
            "ORDER BY created_at, id", (f"%{READY_VIA}%",)):
        body = json.loads(provenance or "{}") or {}
        if body.get("via") != READY_VIA:
            continue
        lo = body.get("learning_object_id")
        answer = connection.execute(
            "SELECT id, created_at FROM practice_attempts WHERE learning_object_id = ? AND created_at > ? "
            "ORDER BY created_at, id LIMIT 1", (lo, created)).fetchone() if lo else None
        out.append({"goal_id": body.get("goal_id"), "learning_object_id": lo, "created_at": created,
                    "answered_at": answer[1] if answer is not None else None, "label": SELF_SELECTED})
    return out


def _results(connection: Any, lo: str, on: str) -> list[float]:
    return [float(row[0]) for row in connection.execute(
        "SELECT correctness FROM practice_attempts WHERE attempt_type IN ('exam_evidence', 'exam_attempt') AND "
        "learning_object_id = ? AND substr(created_at, 1, 10) = ? AND correctness IS NOT NULL", (lo, on))]


def transfer(connection: Any, goals: Sequence[Any], fit: Mapping[str, Any], *, prior_sd: float,
             ready: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The transfer slope per goal type, on each past dated goal's results paired with the calibrated pool forecast
    of the newest trace before its date."""

    traces = _traces(connection)
    rows: dict[str, list[tuple[float, None, float]]] = {}
    pairs = []
    for goal in goals:
        due = getattr(goal, "due_at", None)
        if not due:
            continue
        on = _parse(str(due)).date().isoformat()
        before = [t for t in traces if str(t["created_at"]) < str(due)
                  and any(str(use.get("goal_id")) == str(goal.id) for use in t["dated"])]
        if not before:
            continue
        latest = before[-1]
        for use in latest["dated"]:
            if str(use.get("goal_id")) != str(goal.id) or use.get("m0") is None:
                continue
            results = _results(connection, str(use["lo"]), on)
            if not results:
                continue
            pool = calibrated(float(use["m0"]), fit)
            exposures = sum(1 for read in ready if read.get("goal_id") == goal.id and read.get("answered_at")
                            and str(latest["created_at"]) < str(read["answered_at"]) <= str(due))
            kind = goal_type(goal)
            rows.setdefault(kind, []).append((_logit(pool), None, sum(results) / len(results)))
            pairs.append({"goal_id": str(goal.id), "lo": str(use["lo"]), "type": kind, "pool": pool,
                          "result": sum(results) / len(results), "results": len(results),
                          "ready_exposures_between": exposures})
    variance = float(prior_sd) ** 2
    prior = M.Combiner(mean=(0.0, 1.0, 0.0), variance=(variance, variance, 1.0), source="prior")
    slopes = {}
    for kind in sorted({*rows, "exam", "dated"}):
        fitted = M.fit_combiner(rows[kind], prior=prior) if rows.get(kind) else prior
        slopes[kind] = {"alpha": fitted.mean[0], "beta": fitted.mean[1], "variance": list(fitted.variance[:2]),
                        "n": len(rows.get(kind, ())), "source": fitted.source}
    return {"version": TRANSFER_VERSION, "slopes": slopes, "pairs": pairs, "prior_sd": float(prior_sd),
            "basis": "imported exam results and sittings on the goal's date, paired with the calibrated pool forecast "
                     "frozen before it"}


def read(connection: Any, vault: Any, *, now: str) -> dict[str, Any]:
    """Each active dated goal's read now, with both sensors' versions; and the ready reads, self-selected."""

    through = _parse(now).astimezone().date().isoformat()
    goals = [goal for goal in (getattr(vault, "goals", None) or ()) if getattr(goal, "due_at", None)]
    fit = calibration(connection, through=through)
    ready = _ready_reads(connection)
    moved = transfer(connection, goals, fit, prior_sd=float(vault.config.router_objective.goal_transfer_prior_sd),
                     ready=ready)
    latest = (_traces(connection) or [None])[-1]
    reads = []
    for goal in goals:
        if getattr(goal, "status", None) != "active" or str(goal.due_at) <= now:
            continue
        uses = [use for use in (latest or {}).get("dated", ()) if str(use.get("goal_id")) == str(goal.id)
                and use.get("m0") is not None]
        days = (_parse(str(goal.due_at)) - _parse(now)).total_seconds() / 86400.0
        if not uses:
            reads.append({"goal_id": str(goal.id), "days_to_date": days, "status": "no_frozen_forecast"})
            continue
        pool = sum(calibrated(float(use["m0"]), fit) for use in uses) / len(uses)
        slope = moved["slopes"][goal_type(goal)]
        value = _sigmoid(float(slope["alpha"]) + float(slope["beta"]) * _logit(pool))
        reads.append({"goal_id": str(goal.id), "type": goal_type(goal), "days_to_date": round(days, 3),
                      "lag_days": round(days, 3), "pool_forecast": round(pool, 6), "goal_read": round(value, 6),
                      "from_trace": latest["decision_id"], "topics": len(uses),
                      "sensors": {"calibration": CALIBRATION_VERSION, "transfer": TRANSFER_VERSION}})
    return {"calibration": fit, "transfer": moved, "reads": reads,
            "ready_reads": {"n": len(ready), "answered": sum(1 for row in ready if row.get("answered_at")),
                            "label": SELF_SELECTED,
                            "exposure_rule": "a ready read between a forecast and its goal's date counts as an "
                                             "exposure on that pair"}}


__all__ = ["CALIBRATION_PRIOR_MEAN", "CALIBRATION_PRIOR_VARIANCE", "CALIBRATION_VERSION", "TRANSFER_VERSION",
           "calibrated", "calibration", "calibration_rows", "goal_type", "read", "transfer"]
