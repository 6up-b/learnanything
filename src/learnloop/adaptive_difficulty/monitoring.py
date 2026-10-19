"""Monitoring, never gating (spec_adaptive_difficulty_v1 §10.4, D3): scores, sequences, honest lines, auto-flags.

Pure functions over prequential logs (one record per scored attempt, each arm's
probability of the §5.3 event fixed before the attempt's update). Every
constant is pre-registered in ``docs/reviews/adaptive-difficulty-ad23.md``
§1.4. Nothing here changes a switch, the config or anything served: an
auto-flag *recommends* a switch to the owner, who flips it (§10.4).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

CLIP = (0.005, 0.995)
LOG_LOSS_BOUND = math.log(1.0 / CLIP[0])  # ≈ 5.30
ALPHA = 0.05
CS_N0 = 200
BOOTSTRAP_SAMPLES = 2000
BOOTSTRAP_SEED = "ad-report-v1"
BAND_REGION_BINS = ((0.6, 0.7), (0.7, 0.8), (0.8, 0.9))
READINESS_ERROR_LIMIT = 0.05
BAND_MISSED = (0.60, 0.88)
BAND_MISSED_AFTER = 200
DOSE_DISMISS_WINDOW = 30
DOSE_DISMISS_SHARE = 0.80
DOSE_DENSITY_LOWERINGS = 3
DOSE_DENSITY_DAYS = 14

HELPING = "helping"
HURTING = "hurting"
CANT_TELL = "can't tell yet"


def log_loss(p: float, y: float) -> float:
    q = min(max(float(p), CLIP[0]), CLIP[1])
    return -(y * math.log(q) + (1.0 - y) * math.log(1.0 - q))


def brier(p: float, y: float) -> float:
    return (float(p) - float(y)) ** 2


def _seed(text: str) -> int:
    import hashlib

    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def bootstrap_interval(values: Sequence[float], *, samples: int = BOOTSTRAP_SAMPLES, seed: str = BOOTSTRAP_SEED,
                       level: float = 0.95) -> dict[str, Any]:
    """The percentile bootstrap of a mean (field §7.4's rule as a monitor; D9's margin 0)."""

    data = np.asarray(list(values), dtype=float)
    if not len(data):
        return {"n": 0, "mean": None, "ci": None}
    rng = np.random.default_rng(_seed(seed))
    means = data[rng.integers(0, len(data), (samples, len(data)))].mean(axis=1)
    tail = (1.0 - level) / 2.0
    return {"n": int(len(data)), "mean": float(data.mean()),
            "ci": [float(np.quantile(means, tail)), float(np.quantile(means, 1.0 - tail))]}


def confidence_sequence(differences: Sequence[float], *, bound: float = LOG_LOSS_BOUND, alpha: float = ALPHA,
                        n0: int = CS_N0) -> dict[str, Any]:
    """An anytime-valid confidence sequence for the mean of bounded differences ``[choe2023]``.

    The two-sided normal-mixture (Robbins) boundary for increments in ``[-c, c]``
    (sub-Gaussian with ``σ = c``): ``half(n) = c·sqrt(2(nρ² + 1)/(n²ρ²) · log(sqrt(nρ² + 1)/α))``,
    ``ρ²`` tuned to ``n0``. Watching it continuously is honest."""

    values = np.clip(np.asarray(list(differences), dtype=float), -bound, bound)
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "lower": None, "upper": None}
    log_term = -2.0 * math.log(alpha / 2.0)
    rho2 = (log_term + math.log(log_term + 1.0)) / n0
    half = bound * math.sqrt(2.0 * (n * rho2 + 1.0) / (n * n * rho2) * math.log(math.sqrt(n * rho2 + 1.0) / (alpha / 2.0)))
    mean = float(values.mean())
    return {"n": n, "mean": mean, "lower": mean - half, "upper": mean + half, "half_width": half}


def verdict(sequence: Mapping[str, Any]) -> str:
    """"helping" when the challenger's loss is below the comparator's throughout the
    sequence, "hurting" when above, else "can't tell yet" (the difference is challenger - comparator)."""

    if not sequence.get("n"):
        return CANT_TELL
    if sequence["upper"] < 0:
        return HELPING
    if sequence["lower"] > 0:
        return HURTING
    return CANT_TELL


def honest_line(subject: str, verdict_value: str, n: int) -> str:
    return f"{subject}: {verdict_value} ({n} first attempts)"


def reliability(predictions: Sequence[float], outcomes: Sequence[float], bins: int = 10) -> list[dict[str, Any]]:
    p = np.asarray(predictions, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    out = []
    for i in range(bins):
        low, high = i / bins, (i + 1) / bins
        mask = (p >= low) & ((p < high) if i < bins - 1 else (p <= high))
        if mask.any():
            out.append({"bin": [low, high], "n": int(mask.sum()), "mean_p": float(p[mask].mean()),
                        "realized": float(y[mask].mean())})
    return out


def band_region_error(predictions: Sequence[float], outcomes: Sequence[float]) -> float | None:
    """The count-weighted mean |mean prediction - realized| over [0.6,0.7), [0.7,0.8), [0.8,0.9]."""

    p = np.asarray(predictions, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    total = 0
    weighted = 0.0
    for index, (low, high) in enumerate(BAND_REGION_BINS):
        mask = (p >= low) & ((p < high) if index < len(BAND_REGION_BINS) - 1 else (p <= high))
        if mask.any():
            total += int(mask.sum())
            weighted += mask.sum() * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return None if total == 0 else weighted / total


def wilson(failures: int, n: int, z: float = 1.96) -> list[float] | None:
    if n <= 0:
        return None
    phat = failures / n
    denom = 1.0 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, centre - half), min(1.0, centre + half)]


@dataclass(frozen=True)
class Flag:
    name: str
    fires: bool
    recommends: str
    detail: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"flag": self.name, "fires": self.fires, "recommends": self.recommends, "detail": dict(self.detail)}


FLAG_SWITCHES = {
    "sharing_worse_than_topic_only": "promoted_predictor = false",
    "coupling_worse_than_uniform": "learned_coupling = false",
    "reading_worse_than_no_reading": "reading_opportunities = false",
    "verdicts_worse_than_no_verdicts": "reading_self_check = false",
    "readiness_miscalibrated": "promoted_predictor = false",
    "band_missed": "selection = false",
    "dose_offers_a_burden": "reading_dose_offers = false",
}


def comparison_flag(name: str, differences: Sequence[float]) -> Flag:
    """Fires when the live model is worse (its loss minus the comparator's), the sequence excluding 0."""

    sequence = confidence_sequence(differences)
    return Flag(name, verdict(sequence) == HURTING, FLAG_SWITCHES[name], sequence)


def readiness_flag(errors: Sequence[float | None]) -> Flag:
    """Band-region reliability error of ``@subject`` above 0.05 in two consecutive reports."""

    recent = [e for e in errors if e is not None][-2:]
    fires = len(recent) == 2 and all(e > READINESS_ERROR_LIMIT for e in recent)
    return Flag("readiness_miscalibrated", fires, FLAG_SWITCHES["readiness_miscalibrated"],
                {"errors": list(recent), "limit": READINESS_ERROR_LIMIT})


def band_missed_flag(outcomes: Sequence[float]) -> Flag:
    """Realized success on AD-selected practice outside 0.60-0.88 over (at least) 200 selections."""

    window = list(outcomes)[-BAND_MISSED_AFTER:]
    rate = float(np.mean(window)) if window else None
    fires = len(window) >= BAND_MISSED_AFTER and rate is not None and not (BAND_MISSED[0] <= rate <= BAND_MISSED[1])
    return Flag("band_missed", fires, FLAG_SWITCHES["band_missed"],
                {"n": len(window), "realized": rate, "range": list(BAND_MISSED)})


def dose_burden_flag(delivered: Sequence[Mapping[str, Any]], density_lowerings: Sequence[str],
                     *, now: str) -> Flag:
    """Of the last 30 delivered extra offers at least 80% dismissed; or the cue density lowered within a
    visit after an offer three times in 14 days."""

    from learnloop.clock import parse_utc

    last = list(delivered)[-DOSE_DISMISS_WINDOW:]
    dismissed = sum(1 for row in last if row.get("dismissed"))
    share = dismissed / len(last) if last else None
    now_dt = parse_utc(now)
    recent = [stamp for stamp in density_lowerings
              if now_dt is not None and (parsed := parse_utc(stamp)) is not None
              and 0 <= (now_dt - parsed).total_seconds() <= DOSE_DENSITY_DAYS * 86400]
    fires = (len(last) >= DOSE_DISMISS_WINDOW and share is not None and share >= DOSE_DISMISS_SHARE) or \
        len(recent) >= DOSE_DENSITY_LOWERINGS
    return Flag("dose_offers_a_burden", fires, FLAG_SWITCHES["dose_offers_a_burden"],
                {"delivered": len(last), "dismissed_share": share, "density_lowerings_14d": len(recent)})


def differences(records: Iterable[Mapping[str, Any]], challenger: str, comparator: str, *,
                split: str | None = None) -> list[float]:
    """Per scored record, the challenger's log loss minus the comparator's (the split's records only)."""

    out = []
    for record in records:
        if split is not None and not record.get(split):
            continue
        p = record["p"]
        if challenger not in p or comparator not in p or p[challenger] is None or p[comparator] is None:
            continue
        y = float(record["y"])
        out.append(log_loss(p[challenger], y) - log_loss(p[comparator], y))
    return out


__all__ = [
    "ALPHA",
    "BAND_MISSED",
    "CANT_TELL",
    "CLIP",
    "FLAG_SWITCHES",
    "Flag",
    "HELPING",
    "HURTING",
    "LOG_LOSS_BOUND",
    "band_missed_flag",
    "band_region_error",
    "bootstrap_interval",
    "brier",
    "comparison_flag",
    "confidence_sequence",
    "differences",
    "dose_burden_flag",
    "honest_line",
    "log_loss",
    "readiness_flag",
    "reliability",
    "verdict",
    "wilson",
]
