"""The dose-and-burden analysis (``ad_dose_report_v1``; spec_adaptive_difficulty_v1 §10.4, D20, D21).

Which active-reading practice best improves *cold retrieval*, and how much of
each is worth the learner's time. Computed offline from the reading-on fit (the
subject view, whatever ``reading_opportunities`` is set to) and the randomized
offers of §5.12; no model call. Nothing it computes acts: its lines are shown
in the report and the glass box, and the owner may adopt a useful dose as the
dose arm's base policy (D21).

* **Per kind, the gain per event**: the next step of its curve
  ``g_κ(n+1) - g_κ(n)`` at dose 0 and at the learner's median dose, read at
  warmth 0 as points of unassisted success at the band's centre (75%), with a
  90% interval from 400 posterior draws (seed ``ad-dose-v1``).
* **Minutes per event**: a non-negative regression of each Reader visit's
  active minutes on its count of each kind, plus a constant, its interval
  bootstrapped over visits (1000 resamples). These are salience magnitudes:
  they stay in the report (A12).
* **The practice reference**: one more practice question's ``γ`` gain over the
  learner's answer minutes.
* **The useful dose** ``n*_κ``: the largest dose whose own event still adds at
  least the practice reference's gain per minute, by posterior median, with an
  80% interval; "can't tell yet" when that interval spans more than 2 events or
  the kind's minutes are unknown.
* **Two estimates, kept apart**: the model's curves (every observation, confounded
  by struggle, labelled "what preceded better recall for you") and the
  randomized offers' effects (unbiased, slow; "tested by randomized offers" only
  when the arm's anytime-valid 95% sequence excludes 0 and agrees in sign with
  the curve).
* **Burden** and the **plain recommendation lines** from fixed templates.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import monitoring as MON
from learnloop.adaptive_difficulty import priors as P

DOSE_REPORT_VERSION = "ad_dose_report_v1"
DRAWS = 400
SEED = "ad-dose-v1"
BAND_CENTRE = 0.75
MAX_DOSE = 10
KIND_NAMES = {
    "reading": "Reading a section",
    "reader_tutor_exchange": "Tutor exchanges while reading",
    "worked_example": "Worked examples",
    "in_passage_question": "Questions while reading",
}
TESTED = "tested by randomized offers"
OBSERVATIONAL = "what preceded better recall for you"
CANT_TELL = "can't tell yet"


def _seed(text: str) -> int:
    import hashlib

    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def coefficient_draws(view: Any, *, draws: int = DRAWS, seed: str = SEED) -> dict[str, np.ndarray]:
    """Posterior draws of each kind's two curve coefficients (``γ̄_m + δ_{κ,m}``) and of ``γ``,
    from the subject view's mixture over the grid."""

    bank = view.bank
    names = [f"gbar:{m}" for m in (1, 2)] + [f"delta:{k}:{m}" for k in P.READING_KINDS for m in (1, 2)] + ["gamma"]
    index = [bank.index[name] for name in names]
    weights = bank.weights()[0]
    rng = np.random.default_rng(_seed(seed))
    points = rng.choice(len(weights), size=draws, p=weights)
    samples = np.zeros((draws, len(names)))
    for point in sorted(set(points.tolist())):
        rows = np.where(points == point)[0]
        mu = bank.mu[point, index]
        cov = bank.S[point][np.ix_(index, index)]
        cov = 0.5 * (cov + cov.T) + 1e-12 * np.eye(len(index))
        samples[rows] = rng.multivariate_normal(mu, cov, size=len(rows))
    out = {"gamma": samples[:, -1]}
    for kind in P.READING_KINDS:
        out[f"{kind}:1"] = samples[:, 0] + samples[:, names.index(f"delta:{kind}:1")]
        out[f"{kind}:2"] = samples[:, 1] + samples[:, names.index(f"delta:{kind}:2")]
    return out


def curve(c1: np.ndarray | float, c2: np.ndarray | float, n: float) -> np.ndarray:
    b1, b2 = M.dose_basis(n)
    return np.asarray(c1) * b1 + np.asarray(c2) * b2


def points_gain(delta_logit: np.ndarray | float) -> np.ndarray:
    """The rise in unassisted success at the band's centre (75%) from a logit shift, at warmth 0."""

    centre = M.success_inverse(BAND_CENTRE, 0.0)
    return M.residual_success(centre + np.asarray(delta_logit, dtype=float), 0.0) - BAND_CENTRE


def nnls(X: np.ndarray, y: np.ndarray, iterations: int = 5000) -> np.ndarray:
    """Non-negative least squares by projected gradient (small problems; deterministic)."""

    if X.size == 0:
        return np.zeros(X.shape[1] if X.ndim == 2 else 0)
    beta = np.zeros(X.shape[1])
    gram = X.T @ X
    step = 1.0 / max(np.linalg.eigvalsh(gram).max(), 1e-12)
    xty = X.T @ y
    for _ in range(iterations):
        beta = np.maximum(beta - step * (gram @ beta - xty), 0.0)
    return beta


def minutes_per_event(visits: Sequence[Mapping[str, Any]], *, samples: int = 1000) -> dict[str, Any]:
    """Each kind's minutes per event (NNLS of visit active minutes on counts plus a constant)."""

    if not visits:
        return {kind: None for kind in P.READING_KINDS} | {"visits": 0}
    X = np.array([[1.0] + [float(v["counts"].get(kind, 0)) for kind in P.READING_KINDS] for v in visits])
    y = np.array([float(v["active_minutes"]) for v in visits])
    beta = nnls(X, y)
    rng = np.random.default_rng(_seed(SEED + ":minutes"))
    boot = np.array([nnls(X[idx], y[idx]) for idx in (rng.integers(0, len(y), len(y)) for _ in range(samples))])
    out: dict[str, Any] = {"visits": len(visits), "constant": float(beta[0])}
    for j, kind in enumerate(P.READING_KINDS, start=1):
        observed = bool(X[:, j].sum() > 0)
        out[kind] = None if not observed else {
            "minutes": float(beta[j]), "interval": [float(np.quantile(boot[:, j], 0.1)),
                                                     float(np.quantile(boot[:, j], 0.9))]}
    return out


def useful_dose(c1: np.ndarray, c2: np.ndarray, minutes: float | None, reference_per_minute: np.ndarray | float
                ) -> dict[str, Any]:
    """``n*``: the largest dose whose own event adds at least the practice reference per minute."""

    if minutes is None or minutes <= 0:
        return {"n_star": None, "interval": None, "cant_tell": True, "why": "minutes_unknown"}
    reference = np.broadcast_to(np.asarray(reference_per_minute, dtype=float), np.shape(c1))
    per_draw = []
    for d in range(len(c1)):
        best = 0
        for n in range(1, MAX_DOSE + 1):
            step = float(points_gain(curve(c1[d], c2[d], n) - curve(c1[d], c2[d], n - 1)))
            if step / minutes >= float(reference[d]):
                best = n
        per_draw.append(best)
    per_draw = np.array(per_draw)
    median_gain = [float(np.median(points_gain(curve(c1, c2, n) - curve(c1, c2, n - 1)))) for n in range(1, MAX_DOSE + 1)]
    ref_median = float(np.median(reference))
    n_star = 0
    for n, gain in enumerate(median_gain, start=1):
        if gain / minutes >= ref_median:
            n_star = n
    interval = [int(np.quantile(per_draw, 0.1)), int(np.quantile(per_draw, 0.9))]
    return {"n_star": n_star, "interval": interval, "cant_tell": interval[1] - interval[0] > 2,
            "why": "interval_wide" if interval[1] - interval[0] > 2 else None}


@dataclass(frozen=True)
class OfferOutcome:
    variant: str
    propensities: Mapping[str, float]
    outcome: float | None  # the matured cold outcome, None while pending
    dose_taken: int = 0
    level_band: str | None = None
    taken: bool = False


def offer_effect(outcomes: Sequence[OfferOutcome], variant: str) -> dict[str, Any]:
    """The offer's effect against ``none`` (Horvitz-Thompson with the logged propensities), its
    95% interval and anytime-valid sequence, moderated by the dose already taken and the level band."""

    def contrast(rows: Sequence[OfferOutcome]) -> dict[str, Any]:
        terms = []
        for row in rows:
            if row.outcome is None or variant not in row.propensities or "none" not in row.propensities:
                continue
            term = 0.0
            if row.variant == variant:
                term += row.outcome / row.propensities[variant]
            elif row.variant == "none":
                term -= row.outcome / row.propensities["none"]
            terms.append(term)
        if len(terms) < 2:
            return {"n": len(terms), "effect": None, "ci95": None, "sequence": None}
        values = np.array(terms)
        mean = float(values.mean())
        se = float(values.std(ddof=1) / math.sqrt(len(values)))
        bound = max(1.0 / min(r.propensities.get(variant, 1.0) for r in rows if variant in r.propensities), 1.0)
        return {"n": len(terms), "effect": mean, "ci95": [mean - 1.96 * se, mean + 1.96 * se],
                "sequence": MON.confidence_sequence(values, bound=bound)}

    result = contrast(outcomes)
    result["by_dose_taken"] = {str(d): contrast([o for o in outcomes if min(o.dose_taken, 2) == d]) for d in (0, 1, 2)}
    result["by_level_band"] = {band: contrast([o for o in outcomes if o.level_band == band])
                               for band in ("below_50", "50_80", "above_80")}
    return result


def label(curve_sign: float | None, randomized: Mapping[str, Any] | None) -> str:
    """"tested by randomized offers" only when the arm's sequence excludes 0 and agrees in sign."""

    sequence = (randomized or {}).get("sequence") if randomized else None
    if sequence and sequence.get("n") and curve_sign is not None:
        lower, upper = sequence.get("lower"), sequence.get("upper")
        if lower is not None and upper is not None and (lower > 0 or upper < 0):
            if math.copysign(1.0, curve_sign) == math.copysign(1.0, (lower + upper) / 2.0):
                return TESTED
    return OBSERVATIONAL


def recommendation(kind: str, n_star: Mapping[str, Any], tag: str) -> str:
    name = KIND_NAMES.get(kind, kind)
    if n_star.get("cant_tell") or n_star.get("n_star") is None:
        return f"{name}: {CANT_TELL}."
    count = int(n_star["n_star"])
    if count == 0:
        return f"{name}: another practice question helped your later recall more per minute ({tag})."
    unit = "per section"
    return f"{name}: about {count} {unit} before practice helped your later recall most per minute ({tag})."


def analyse(view: Any, *, visits: Sequence[Mapping[str, Any]], answer_minutes: float | None,
            median_doses: Mapping[str, float], offers: Mapping[str, Sequence[OfferOutcome]] | None = None
            ) -> dict[str, Any]:
    """The whole section (``ad_dose_report_v1``): curves, gains, minutes, useful doses, offers, lines."""

    draws = coefficient_draws(view)
    minutes = minutes_per_event(visits)
    gamma = draws["gamma"]
    reference = (points_gain(gamma) / answer_minutes) if answer_minutes else None
    out: dict[str, Any] = {"version": DOSE_REPORT_VERSION, "minutes": minutes, "kinds": {},
                           "practice_reference": None if reference is None else {
                               "gain_per_question": float(np.median(points_gain(gamma))),
                               "answer_minutes": answer_minutes,
                               "gain_per_minute": float(np.median(reference))},
                           "lines": []}
    offers = offers or {}
    for kind in P.READING_KINDS:
        c1, c2 = draws[f"{kind}:1"], draws[f"{kind}:2"]
        median_dose = float(median_doses.get(kind, 0.0))
        first = points_gain(curve(c1, c2, 1) - curve(c1, c2, 0))
        at_median = points_gain(curve(c1, c2, median_dose + 1) - curve(c1, c2, median_dose))
        curve_rows = []
        for n in range(0, MAX_DOSE + 1):
            values = curve(c1, c2, n)
            curve_rows.append({"n": n, "median": float(np.median(values)),
                               "band": [float(np.quantile(values, 0.05)), float(np.quantile(values, 0.95))]})
        kind_minutes = (minutes.get(kind) or {}).get("minutes") if isinstance(minutes.get(kind), Mapping) else None
        n_star = (useful_dose(c1, c2, kind_minutes, reference) if reference is not None else
                  {"n_star": None, "interval": None, "cant_tell": True, "why": "answer_minutes_unknown"})
        variant = {"worked_example": "extra_worked_example", "in_passage_question": "extra_question"}.get(kind)
        randomized = offer_effect(offers.get(variant, ()), variant) if variant else None
        tag = label(float(np.median(first)), randomized)
        out["kinds"][kind] = {
            "gain_first_event": {"median": float(np.median(first)),
                                 "ci90": [float(np.quantile(first, 0.05)), float(np.quantile(first, 0.95))]},
            "gain_at_median_dose": {"dose": median_dose, "median": float(np.median(at_median)),
                                    "ci90": [float(np.quantile(at_median, 0.05)), float(np.quantile(at_median, 0.95))]},
            "full_effect": {"mean": float(np.mean(c1 + c2)), "median": float(np.median(c1 + c2))},
            "curve": curve_rows, "minutes_per_event": kind_minutes, "useful_dose": n_star,
            "randomized": randomized, "label": tag,
        }
        out["lines"].append(recommendation(kind, n_star, tag))
    return out


__all__ = [
    "CANT_TELL",
    "DOSE_REPORT_VERSION",
    "KIND_NAMES",
    "OBSERVATIONAL",
    "OfferOutcome",
    "TESTED",
    "analyse",
    "coefficient_draws",
    "curve",
    "label",
    "minutes_per_event",
    "nnls",
    "offer_effect",
    "points_gain",
    "recommendation",
    "useful_dose",
]
