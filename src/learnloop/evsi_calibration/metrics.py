"""Score a simulation run: calibration, information, action change, minutes.

Every interval is a percentile bootstrap over **learners** (the unit that was
sampled), seeded, so a reported CI is reproducible from the same run.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

import numpy as np

from learnloop.evsi_calibration.simulate import CheckRecord, EpisodeRecord, MEMBER_QUANTILES

BINS = 10


def _ci(values: np.ndarray, groups: np.ndarray, rng: np.random.Generator, draws: int, stat=np.mean) -> list[float]:
    """Cluster bootstrap over ``groups`` (learner ids) of ``stat(values)``."""

    if values.size == 0:
        return [float("nan"), float("nan")]
    unique = np.unique(groups)
    index = {g: np.flatnonzero(groups == g) for g in unique.tolist()}
    estimates = []
    for _ in range(draws):
        pick = rng.choice(unique, size=unique.size, replace=True)
        rows = np.concatenate([index[g] for g in pick.tolist()])
        estimates.append(float(stat(values[rows])))
    return [round(float(np.quantile(estimates, 0.025)), 4), round(float(np.quantile(estimates, 0.975)), 4)]


def _round(value: float | None, digits: int = 4) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return round(float(value), digits)


def reliability(pairs: Iterable[tuple[float, float]], bins: int = BINS) -> dict[str, Any]:
    """Reliability table + expected calibration error for (predicted, outcome) pairs."""

    data = np.asarray(list(pairs), dtype=float)
    if data.size == 0:
        return {"pairs": 0, "bins": [], "ece": None, "brier": None}
    predicted, outcome = data[:, 0], data[:, 1]
    edges = np.linspace(0.0, 1.0, bins + 1)
    which = np.clip(np.digitize(predicted, edges[1:-1]), 0, bins - 1)
    rows = []
    ece = 0.0
    for b in range(bins):
        mask = which == b
        count = int(mask.sum())
        if count == 0:
            continue
        mean_p = float(predicted[mask].mean())
        rate = float(outcome[mask].mean())
        ece += count / predicted.size * abs(mean_p - rate)
        rows.append({"bin": [round(edges[b], 2), round(edges[b + 1], 2)], "n": count,
                     "mean_predicted": round(mean_p, 4), "observed": round(rate, 4)})
    return {
        "pairs": int(predicted.size),
        "bins": rows,
        "ece": round(ece, 4),
        "brier": round(float(np.mean((predicted - outcome) ** 2)), 4),
    }


def outcome_calibration(checks: Sequence[CheckRecord]) -> dict[str, Any]:
    """(1) Predicted answer distributions vs the realized answers."""

    pairs: list[tuple[float, float]] = []
    log_losses: list[float] = []
    for record in checks:
        for option, p in record.predicted.items():
            pairs.append((p, 1.0 if option == record.realized else 0.0))
        log_losses.append(-math.log(max(record.predicted.get(record.realized, 0.0), 1e-12)))
    table = reliability(pairs)
    table["log_loss"] = _round(float(np.mean(log_losses))) if log_losses else None
    table["checks"] = len(checks)
    return table


def information(checks: Sequence[CheckRecord], rng: np.random.Generator, draws: int) -> dict[str, Any]:
    """(2) Predicted EIG vs realized entropy drop and vs information about the truth."""

    if not checks:
        return {"checks": 0}
    eig = np.asarray([c.eig_nats for c in checks])
    drop = np.asarray([c.entropy_drop for c in checks])
    gain = np.asarray([c.truth_log_gain for c in checks])
    groups = np.asarray([c.learner for c in checks])
    by_bin = []
    edges = np.quantile(eig, np.linspace(0, 1, 6)) if eig.size >= 10 else np.array([eig.min(), eig.max()])
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (eig >= lo) & (eig <= hi)
        if mask.sum() == 0:
            continue
        by_bin.append({
            "eig_range": [round(float(lo), 4), round(float(hi), 4)],
            "n": int(mask.sum()),
            "mean_predicted_eig": round(float(eig[mask].mean()), 4),
            "mean_entropy_drop": round(float(drop[mask].mean()), 4),
            "mean_truth_log_gain": round(float(gain[mask].mean()), 4),
        })
    return {
        "checks": int(eig.size),
        "mean_predicted_eig": _round(float(eig.mean())),
        "mean_entropy_drop": _round(float(drop.mean())),
        "entropy_drop_ci95": _ci(drop, groups, rng, draws),
        "mean_truth_log_gain": _round(float(gain.mean())),
        "truth_log_gain_ci95": _ci(gain, groups, rng, draws),
        "realized_over_predicted": _round(float(gain.mean() / eig.mean())) if eig.mean() > 0 else None,
        "by_predicted_eig": by_bin,
    }


def action_change(checks: Sequence[CheckRecord]) -> dict[str, Any]:
    """(3) Predicted vs realized probability that a check changes the chosen action."""

    pairs = [(c.p_action_change, 1.0 if c.action_changed else 0.0) for c in checks]
    table = reliability(pairs, bins=5)
    if checks:
        table["mean_predicted"] = _round(float(np.mean([p for p, _ in pairs])))
        table["realized_rate"] = _round(float(np.mean([o for _, o in pairs])))
    return table


def value_of_checks(checks: Sequence[CheckRecord], rng: np.random.Generator, draws: int) -> dict[str, Any]:
    """Predicted EVSI (and its member quantiles) vs the realized value of each check.

    ``realized_value`` = true loss of the action before the check minus after
    it, in minutes. Its mean over checks with similar predictions is what an
    unbiased EVSI should equal. The minutes-per-nat slope (realized value per
    predicted nat, through the origin) calibrates ``VALUE_PER_NAT_MINUTES``.
    """

    if not checks:
        return {"checks": 0}
    realized = np.asarray([c.realized_value for c in checks])
    point = np.asarray([c.evsi_point for c in checks])
    eig = np.asarray([c.eig_nats for c in checks])
    groups = np.asarray([c.learner for c in checks])
    quantiles = {
        key: np.asarray([c.evsi_member_quantiles[key] for c in checks])
        for key in checks[0].evsi_member_quantiles
    }

    def slope(rows: np.ndarray) -> float:
        x, y = eig[rows], realized[rows]
        denominator = float((x * x).sum())
        return float((x * y).sum() / denominator) if denominator > 0 else float("nan")

    unique = np.unique(groups)
    index = {g: np.flatnonzero(groups == g) for g in unique.tolist()}
    slopes = []
    for _ in range(draws):
        pick = rng.choice(unique, size=unique.size, replace=True)
        slopes.append(slope(np.concatenate([index[g] for g in pick.tolist()])))
    all_rows = np.arange(realized.size)
    quantile_bias = {
        key: _round(float(values.mean() - realized.mean())) for key, values in sorted(quantiles.items())
    }
    return {
        "checks": int(realized.size),
        "mean_predicted_evsi_point": _round(float(point.mean())),
        "mean_realized_value": _round(float(realized.mean())),
        "realized_value_ci95": _ci(realized, groups, rng, draws),
        "realized_over_predicted": _round(float(realized.mean() / point.mean())) if point.mean() > 0 else None,
        "member_quantile_minus_realized": quantile_bias,
        # What the decision model itself implies one nat is worth here.
        "model_minutes_per_nat": _round(float(point.sum() / eig.sum())) if eig.sum() > 0 else None,
        "minutes_per_nat": _round(slope(all_rows)),
        "minutes_per_nat_ci95": [
            _round(float(np.nanquantile(slopes, 0.025))),
            _round(float(np.nanquantile(slopes, 0.975))),
        ],
    }


def episode_summary(episodes: Sequence[EpisodeRecord], rng: np.random.Generator, draws: int) -> dict[str, Any]:
    """(4) Checks and minutes to identify the misconception, and wasted minutes."""

    if not episodes:
        return {"episodes": 0}
    groups = np.asarray([e.learner for e in episodes])

    def column(name: str) -> np.ndarray:
        return np.asarray([float(getattr(e, name)) for e in episodes])

    total = column("total_minutes")
    identify = [e.steps_to_identify for e in episodes if e.steps_to_identify is not None]
    verdicts: dict[str, int] = {}
    for e in episodes:
        verdicts[e.stop_reason] = verdicts.get(e.stop_reason, 0) + 1
    misconception = [e for e in episodes if e.truth.startswith("mis:")]
    return {
        "episodes": len(episodes),
        "mean_checks": _round(float(column("checks").mean())),
        "mean_check_minutes": _round(float(column("check_minutes").mean())),
        "correct_action_rate": _round(float(column("correct_action").mean())),
        "correct_action_ci95": _ci(column("correct_action"), groups, rng, draws),
        "identified_rate": _round(float(column("identified").mean())),
        "misconception_identified_rate": _round(
            float(np.mean([e.identified for e in misconception])) if misconception else float("nan")
        ),
        "mean_checks_to_identify": _round(float(np.mean(identify))) if identify else None,
        "mean_regret_minutes": _round(float(column("regret_minutes").mean())),
        "mean_total_minutes": _round(float(total.mean())),
        "total_minutes_ci95": _ci(total, groups, rng, draws),
        "mean_wasted_check_minutes": _round(float(column("wasted_check_minutes").mean())),
        "mean_wasted_minutes": _round(float((column("wasted_check_minutes") + column("regret_minutes")).mean())),
        "stop_reasons": dict(sorted(verdicts.items(), key=lambda kv: -kv[1])),
    }


def summarize(checks: Sequence[CheckRecord], episodes: Sequence[EpisodeRecord], *, seed: int, draws: int = 400) -> dict[str, Any]:
    """Per-policy metric blocks (1)-(4)."""

    rng = np.random.default_rng(seed)
    policies = sorted({e.policy for e in episodes})
    out: dict[str, Any] = {}
    for policy in policies:
        c = [r for r in checks if r.policy == policy]
        e = [r for r in episodes if r.policy == policy]
        out[policy] = {
            "episodes": episode_summary(e, rng, draws),
            "outcome_calibration": outcome_calibration(c),
            "information": information(c, rng, draws),
            "action_change": action_change(c),
            "value_of_checks": value_of_checks(c, rng, draws),
        }
    return out


def paired_difference(
    left: Sequence[EpisodeRecord],
    right: Sequence[EpisodeRecord],
    *,
    field_name: str = "total_minutes",
    seed: int,
    draws: int = 400,
) -> dict[str, Any]:
    """Mean of ``right - left`` per learner (common random numbers), bootstrap CI."""

    by_left = {e.learner: float(getattr(e, field_name)) for e in left}
    diffs = np.asarray([float(getattr(e, field_name)) - by_left[e.learner] for e in right if e.learner in by_left])
    if diffs.size == 0:
        return {"n": 0}
    rng = np.random.default_rng(seed)
    boots = [float(rng.choice(diffs, size=diffs.size, replace=True).mean()) for _ in range(draws)]
    return {
        "n": int(diffs.size),
        "mean_difference": round(float(diffs.mean()), 4),
        "ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
    }


def kendall_tau(left: Sequence[str], right: Sequence[str]) -> float | None:
    """Kendall's tau-a between two rankings over their common items."""

    common = [item for item in left if item in set(right)]
    if len(common) < 2:
        return None
    position = {item: i for i, item in enumerate(right)}
    concordant = discordant = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            if position[common[i]] < position[common[j]]:
                concordant += 1
            else:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total else None


def quantile_names() -> tuple[str, ...]:
    return tuple(f"q{int(q * 100):02d}" for q in MEMBER_QUANTILES)
