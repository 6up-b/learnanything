"""The learned lesson-check weight, the forecast pool and the tap/hedge recalibration (teacher TE1).

``docs/specs/spec_teacher_v1.md`` §12.1, §12.2 and §18.4 (LP-min). Three learned
quantities, each a posterior from seeded priors, each DERIVED state recomputed
in order from receipts and the attempt ledger (one replayer:
:func:`rebuild_lesson_weight_state`):

**The lesson-check mass** ``m = σ(η)``, ``η = η₀ + u_L + β_c·z_c + β_p·z_p``
(§12.1). A Gaussian over ``(η₀, β_c, β_p, u_L...)`` per point of the per-LO
offset scale's grid ``τ ∈ {0.1, 0.2, 0.4}`` (AD's ``ad_hyper`` mechanism: grid
weights ``W_t(τ) ∝ W_{t−1}(τ)·Z_t(τ)`` from uniform). It learns only from later
cold outcomes on unseen items of the same LO (:func:`qualifying_outcomes`; a
grade held for review is no outcome until released, ``held_grades``): the
first qualifying outcome resolves every unresolved check on its LO. The
likelihood ``p(y | η)`` is the mastery model's predicted success for the cold
outcome after a recomputation of the LO's updates (:func:`recorded_trajectory`,
:func:`trajectory_state`): from the check's recorded prior state, the check
entered at mass ``σ(η)`` with its own recorded observation factors (the
attempt step's observation weight scaled by ``σ(η)/m₀``, and its grader-
interpretation noise recovered from the recorded variance step), then every
later update on the LO before the outcome re-applied with its recorded
factors, then the drift to the outcome (the moderated logistic, held to
``p_max``). At the recorded mass it reproduces the recorded state (tested). An
attempt that left no record falls back to the first-order form (the check
alone at full reliability, then the drift), named on the trace. An outcome
that resolves ``n`` checks enters each factor at power ``1/n`` (each varies
its own mass, the others as recorded), so it counts once.
The update is AD's §5.6 step (:func:`learnloop.adf_numeric.adf_update`).
Filtering, never smoothing: the mass applied to a check is the posterior mean
of ``σ(η)`` as of that check, recorded on its ``lesson_checks`` row; replay
reads it back (:func:`lesson_check_mass`), so a past check's mass never moves.

**The forecast pool** (§12.2): ``p_λ = λ·p_B + (1 − λ)·p_A`` on a 21-point grid
(numerical resolution) with the seeded prior Beta(1, 4) (basis ``legacy``: the
parametric weight starts ahead), updated by ``W_t(λ) ∝ W_{t−1}(λ)·p_λ(y)`` when
a ``lesson_step_retained`` forecast's LO gets its first qualifying cold outcome.
One posterior per forecaster (doctrine version and teacher model): a new
forecaster starts from the seeded prior. Both predictors are of the same cold
outcome: ``p_A`` is computed for the committed cold item at the check's
horizon when the check is entered, and for the resolving item at the outcome's
horizon when the pool learns (:func:`forecast_p_a`). The pool-implied mass of a check is
the ``m`` at which the mastery update makes the predicted success equal
``p_λ̂`` (:func:`pool_implied_mass`; at λ̂ = 0, or with no forecast for the
node yet, exactly §12.1's mass).

**The tap/hedge recalibration** (LP-min, §18.4): the tap (1 to 5) maps to a
probability through ``σ(α + β·logit(map[tap]))`` with today's fixed map as the
legacy-seeded centre (α ~ N(0, 1), β ~ N(1, 1): ≥ 1 logit on both, the LP
spec's rule for legacy priors); the grader's hedge read (``hedged`` /
``confident``) has one intercept per value, N(0, 1) (centre: chance, "no
information"). Learned from every graded attempt that carries one (a held
grade excepted until released), not only lesson checks, as of each check.

The DERIVED tables describe the ledgers through the latest answered lesson
check (:func:`tables_through`): the live path writes them after each check and
the replayer bounds its replay at the same instant, so the two agree row for
row whatever happened since; every reader of the current posterior replays
the ledgers itself.

Nothing here writes evidence: it writes only its own DERIVED tables, and the
mass reaches mastery only through the attempt step's one seam (the recorded
``mass_applied`` read by :func:`lesson_check_mass`). Every number below is a
seeded prior (labelled with its basis), a structural bound or numerical
resolution (§18.4; registered in ``params.parameter_registry``).
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from learnloop.adf_numeric import (
    NODES,
    WEIGHTS,
    adf_update,
    gaussian_sigmoid_mean,
    logit,
    normalized_log_weights,
    sigmoid,
)
from learnloop.clock import parse_utc
from learnloop.held_grades import held_for_review_attempts

#: The prior set's identity (``lp_priors_v1``, spec §12.1): a changed prior is a successor.
PRIORS_VERSION = "lp_priors_v1"
#: The state's own shape version.
STATE_VERSION = "lesson_weight_state_v1"

# --- §12.1, seeded priors (lp_priors_v1) ------------------------------------
#: η₀'s prior mean: logit of the type's configured mass 0.5 (basis legacy, config/schema evidence masses).
ETA0_PRIOR_MEAN = 0.0
#: η₀'s prior sd: the LP spec's width rule for legacy priors (≥ 1 logit; basis legacy).
ETA0_PRIOR_SD = 1.0
#: β_c's and β_p's prior sd (centre "no effect"; basis simulation: the narrowest prior under which a
#: planted ±0.5-logit effect is still recovered).
BETA_C_PRIOR_SD = 0.5
BETA_P_PRIOR_SD = 0.5
#: The per-LO offset scale's grid support (basis simulation: the planted-recovery suite tells the
#: points apart); its weights start uniform and are learned.
TAU_GRID: tuple[float, ...] = (0.1, 0.2, 0.4)

# --- §12.2, the forecast pool -------------------------------------------------
#: The λ grid's resolution (numerical resolution, §18.4).
POOL_GRID_POINTS = 21
#: Beta(1, 4) over λ (basis legacy: the owner's "the parametric weight starts ahead").
POOL_PRIOR_ALPHA = 1.0
POOL_PRIOR_BETA = 4.0

# --- LP-min, the tap/hedge recalibration ---------------------------------------
#: Today's fixed tap -> probability map (basis legacy: ``goals.exam_calibration``'s
#: ``_ANSWER_CONFIDENCE_PROBABILITY``; a test pins the two equal).
TAP_PRIOR_MAP: Mapping[int, float] = {1: 0.10, 2: 0.30, 3: 0.50, 4: 0.70, 5: 0.90}
#: The recalibration's prior: intercept N(0, 1), slope N(1, 1) (≥ 1 logit on both, basis legacy).
TAP_INTERCEPT_PRIOR = (0.0, 1.0)
TAP_SLOPE_PRIOR = (1.0, 1.0)
#: Each hedge value's intercept N(0, 1) (centre: chance, no information; ≥ 1 logit wide).
HEDGE_INTERCEPT_PRIOR = (0.0, 1.0)
HEDGE_VALUES: tuple[str, ...] = ("confident", "hedged")

#: The attempt types whose answers can resolve a check (AD's eligible set, wt:503-512): an
#: unassisted production the learner gave cold. A lesson check itself is never among them.
COLD_ATTEMPT_TYPES: tuple[str, ...] = ("independent_attempt", "open_text", "diagnostic_probe", "exam_attempt")
LESSON_CHECK_ATTEMPT_TYPE = "reconstruction_after_walkthrough"
#: The pool-implied mass's search interval on the logit scale (numerical resolution: σ(±12) is
#: within 1e-5 of the link's bounds, which the mass approaches but never reaches).
_IMPLIED_ETA_BOUND = 12.0
_BISECTION_STEPS = 60

#: The rules a check's mass was applied under (recorded on its row).
RULE_FIXED = "fixed"
RULE_LEARNED = "learned"
RULE_POOL = "pool"


# =============================================================================
# The functional core
# =============================================================================


@dataclass
class _Bank:
    """One τ grid point's Gaussian over (η₀, β_c, β_p, u_L...)."""

    tau: float
    mean: np.ndarray
    cov: np.ndarray
    log_w: float = 0.0


def _prior_bank(tau: float) -> _Bank:
    mean = np.array([ETA0_PRIOR_MEAN, 0.0, 0.0], dtype=np.float64)
    cov = np.diag([ETA0_PRIOR_SD ** 2, BETA_C_PRIOR_SD ** 2, BETA_P_PRIOR_SD ** 2]).astype(np.float64)
    return _Bank(tau=tau, mean=mean, cov=cov)


def _pool_grid() -> np.ndarray:
    return np.linspace(0.0, 1.0, POOL_GRID_POINTS)


def _pool_prior_log_w() -> np.ndarray:
    """Beta(1, 4) discretized on the grid (the endpoint λ = 1 has density 0: a tiny floor keeps it a point)."""

    grid = _pool_grid()
    density = np.power(np.clip(grid, 0.0, 1.0), POOL_PRIOR_ALPHA - 1.0) * np.power(
        np.clip(1.0 - grid, 0.0, 1.0), POOL_PRIOR_BETA - 1.0)
    density = np.maximum(density, 1e-300)
    return np.log(density / density.sum())


@dataclass
class _Calibration:
    """A Gaussian over a recalibration's coefficients and how many answers moved it."""

    mean: np.ndarray
    cov: np.ndarray
    updates: int = 0
    through_at: str | None = None


def _tap_prior() -> _Calibration:
    return _Calibration(mean=np.array([TAP_INTERCEPT_PRIOR[0], TAP_SLOPE_PRIOR[0]]),
                        cov=np.diag([TAP_INTERCEPT_PRIOR[1] ** 2, TAP_SLOPE_PRIOR[1] ** 2]))


def _hedge_prior() -> _Calibration:
    return _Calibration(mean=np.array([HEDGE_INTERCEPT_PRIOR[0]] * len(HEDGE_VALUES)),
                        cov=np.diag([HEDGE_INTERCEPT_PRIOR[1] ** 2] * len(HEDGE_VALUES)))


@dataclass
class WeightState:
    """The three posteriors as of some instant, with the per-update trace."""

    banks: list[_Bank] = field(default_factory=lambda: [_prior_bank(tau) for tau in TAU_GRID])
    lo_index: dict[str, int] = field(default_factory=dict)
    pools: dict[str, np.ndarray] = field(default_factory=dict)
    pool_updates: dict[str, int] = field(default_factory=dict)
    tap: _Calibration = field(default_factory=_tap_prior)
    hedge: _Calibration = field(default_factory=_hedge_prior)
    updates: int = 0
    through_at: str | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    #: (prequential) per resolved factor: log-likelihood under the learned mass and under the fixed 0.5.
    prequential: list[tuple[float, float]] = field(default_factory=list)

    # -- the per-LO offsets ----------------------------------------------------
    def _ensure_lo(self, learning_object_id: str) -> int:
        index = self.lo_index.get(learning_object_id)
        if index is not None:
            return index
        index = 3 + len(self.lo_index)
        self.lo_index[learning_object_id] = index
        for bank in self.banks:
            size = bank.mean.shape[0]
            mean = np.zeros(size + 1)
            mean[:size] = bank.mean
            cov = np.zeros((size + 1, size + 1))
            cov[:size, :size] = bank.cov
            cov[size, size] = bank.tau ** 2
            bank.mean, bank.cov = mean, cov
        return index

    def _h(self, learning_object_id: str, z_c: float, z_p: float) -> list[np.ndarray]:
        index = self.lo_index.get(learning_object_id)
        out = []
        for bank in self.banks:
            h = np.zeros(bank.mean.shape[0])
            h[0], h[1], h[2] = 1.0, z_c, z_p
            if index is not None:
                h[index] = 1.0
            out.append(h)
        return out

    def tau_weights(self) -> np.ndarray:
        return normalized_log_weights(np.array([bank.log_w for bank in self.banks]))

    def eta_moments(self, learning_object_id: str, z_c: float, z_p: float) -> list[tuple[float, float]]:
        """``(m, v)`` of η per τ point (an LO never seen has its offset at the prior, variance τ²)."""

        out = []
        index = self.lo_index.get(learning_object_id)
        for bank, h in zip(self.banks, self._h(learning_object_id, z_c, z_p)):
            m = float(h @ bank.mean)
            v = float(h @ bank.cov @ h)
            if index is None:
                v += bank.tau ** 2
            out.append((m, max(v, 0.0)))
        return out

    def learned_mass(self, learning_object_id: str, z_c: float, z_p: float) -> float:
        """§12.1's mass as of now: the posterior mean of σ(η) (in (0, 1) by the link)."""

        weights = self.tau_weights()
        moments = self.eta_moments(learning_object_id, z_c, z_p)
        return float(sum(w * gaussian_sigmoid_mean(m, v) for w, (m, v) in zip(weights, moments)))

    def pool_lambda(self, family: str) -> float:
        """λ̂, the pool weight's posterior mean for ``family`` (the seeded prior's mean before any update)."""

        log_w = self.pools.get(family)
        if log_w is None:
            log_w = _pool_prior_log_w()
        return float((normalized_log_weights(log_w) * _pool_grid()).sum())

    # -- the recalibration -------------------------------------------------------
    def tap_probability(self, tap: int) -> float:
        x = logit(TAP_PRIOR_MAP[int(tap)])
        return float(sigmoid(self.tap.mean[0] + self.tap.mean[1] * x))

    def hedge_probability(self, hedge: str) -> float:
        return float(sigmoid(self.hedge.mean[HEDGE_VALUES.index(hedge)]))


def confidence_term(state: WeightState, tap: int | None, hedge: str | None) -> tuple[float, str]:
    """``(z_c, source)``: the tap's recalibrated probability on the logit scale (else the hedge
    read's, else 0, "neither"), centred on chance (``logit 0.5 = 0``: no confidence information)."""

    if tap is not None and int(tap) in TAP_PRIOR_MAP:
        return logit(state.tap_probability(int(tap))), "tap"
    if hedge in HEDGE_VALUES:
        return logit(state.hedge_probability(str(hedge))), "hedge"
    return 0.0, "neither"


def prediction_term(p: float | None, band: tuple[float, float]) -> float:
    """``z_p``: the predicted success on the logit scale, centred at the band's middle (§12.1)."""

    if p is None:
        return 0.0
    return logit(float(p)) - logit((float(band[0]) + float(band[1])) / 2.0)


# --- the mastery model's prediction as a function of the check's mass -----------


@dataclass(frozen=True)
class CheckSensitivity:
    """What the check left in the mastery model, recorded at the check, as a function of its mass."""

    mu: float
    variance: float
    last_evidence_at: str | None
    item_a: float
    item_b: float
    correctness: float
    observed_at: str

    def as_dict(self) -> dict[str, Any]:
        return {"mu": self.mu, "variance": self.variance, "last_evidence_at": self.last_evidence_at,
                "item_a": self.item_a, "item_b": self.item_b, "correctness": self.correctness,
                "observed_at": self.observed_at}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CheckSensitivity":
        return cls(mu=float(value["mu"]), variance=float(value["variance"]),
                   last_evidence_at=value.get("last_evidence_at"), item_a=float(value["item_a"]),
                   item_b=float(value["item_b"]), correctness=float(value["correctness"]),
                   observed_at=str(value["observed_at"]))


def posterior_after(sensitivity: CheckSensitivity, mass: float, mastery_config: Any) -> tuple[float, float]:
    """``(μ, P)`` after the check entered at ``mass`` (the mastery model's own update)."""

    from learnloop.db.repositories import MasteryState
    from learnloop.learner.mastery import MasteryObservation, update_mastery

    observed = parse_utc(sensitivity.observed_at)
    assert observed is not None
    prior = MasteryState(
        learning_object_id="lesson_check", logit_mean=sensitivity.mu, logit_variance=sensitivity.variance,
        evidence_count=0, last_evidence_at=sensitivity.last_evidence_at, algorithm_version="lesson_weight",
        updated_at=sensitivity.observed_at)
    observation = MasteryObservation(
        rubric_score=0, max_points=1, evidence_coverage=1.0, hint_dampening=1.0, grader_confidence=1.0,
        attempt_type=LESSON_CHECK_ATTEMPT_TYPE, observed_at=observed, attempt_evidence_mass=float(mass),
        soft_score_override=float(sensitivity.correctness))
    state = update_mastery(prior, observation, mastery_config, "lesson_weight",
                           item_a=sensitivity.item_a, item_b=sensitivity.item_b)
    return float(state.logit_mean), float(state.logit_variance)


def predicted_success(mu: float, variance: float, *, a: float, b: float, drift: float = 0.0, days: float = 0.0) -> float:
    """The mastery model's success probability with its uncertainty (the moderated logistic, the
    probit approximation ``σ(a(μ − b) / √(1 + π a² V / 8))``), ``V`` grown by ``drift`` per day."""

    total = max(variance, 0.0) + max(drift, 0.0) * max(days, 0.0)
    return float(sigmoid(a * (mu - b) / math.sqrt(1.0 + math.pi * a * a * total / 8.0)))


def _days(start: str, end: str) -> float:
    a, b = parse_utc(start), parse_utc(end)
    if a is None or b is None:
        return 0.0
    return max(0.0, (b - a).total_seconds() / 86400.0)


# --- the LO's recorded trajectory from the check to the outcome (§12.1; review F6) ------------


@dataclass(frozen=True)
class RecordedUpdate:
    """One mastery update on the check's LO as the attempt step made it: its grade, its item, and the
    observation factors it entered with (the observation weight the attempt step recorded, which
    carries coverage, grading reliability, hints, the error sharpening and the familiarity discount;
    and the grader-interpretation noise, recovered from the recorded variance step). ``varied``: the
    resolving check itself, whose weight scales with the candidate mass (the weight is linear in the
    attempt's mass: ``recall_coverage.resolve_reliability``)."""

    attempt_id: str
    at: str
    y: float
    item_a: float
    item_b: float
    weight: float
    interpretation_variance: float
    primed: bool
    attempt_type: str
    applied: bool
    varied: bool = False


def _interpretation_variance(mu: float, variance: float, last: str | None, at: str, *, a: float, b: float,
                             weight: float, variance_after: float, config: Any) -> float:
    """The extra observation noise an update carried, recovered from its recorded variance step
    (``P_after = (1 − K·H)·P_pred``, ``K·H = H²P/(H²P + R)``), less the weight's own part of ``R``."""

    irt = getattr(config, "irt", None)
    if irt is None or not getattr(irt, "enabled", False):
        return 0.0
    p = min(max(float(sigmoid(a * (mu - b))), irt.p_clip), 1.0 - irt.p_clip)
    pq = p * (1.0 - p)
    h = a * pq
    predicted = min(variance + float(config.sigma2_drift) * (_days(last, at) if last else 0.0), float(config.p_max))
    kh = 1.0 - variance_after / predicted if predicted > 0 else 0.0
    if kh <= 0.0 or h == 0.0:
        return 0.0
    r = h * h * predicted * (1.0 - kh) / kh
    return max(0.0, r - float(config.base_observation_variance) * pq / max(weight, 0.10))


def recorded_trajectory(connection: Any, vault: Any, mastery_config: Any, check: Mapping[str, Any],
                        outcome: Mapping[str, Any]) -> list[RecordedUpdate] | None:
    """The check's own update and every update on its LO after it and before the outcome, in order,
    each with its recorded factors; None when one of them left no record to recompute it from."""

    from learnloop.learner.mastery import item_irt_params

    if vault is None or not check.get("attempt_id"):
        return None
    lo = str(check["learning_object_id"])
    anchor = connection.execute("SELECT created_at FROM practice_attempts WHERE id = ?",
                                (str(check["attempt_id"]),)).fetchone()
    if anchor is None:
        return None
    rows = connection.execute(
        "SELECT a.id, a.practice_item_id, a.created_at, a.correctness, a.primed, a.attempt_type, s.posterior_delta_json, "
        "d.payload_json FROM practice_attempts a "
        "LEFT JOIN attempt_surprise s ON s.attempt_id = a.id "
        "LEFT JOIN attempt_debug_payloads d ON d.attempt_id = a.id "
        "WHERE a.learning_object_id = ? AND (a.created_at > ? OR (a.created_at = ? AND a.id >= ?)) "
        "AND (a.created_at < ? OR (a.created_at = ? AND a.id < ?)) ORDER BY a.created_at, a.id",
        (lo, anchor[0], anchor[0], str(check["attempt_id"]), str(outcome["created_at"]),
         str(outcome["created_at"]), str(outcome["id"]))).fetchall()
    if not rows or str(rows[0][0]) != str(check["attempt_id"]):
        return None
    held = held_for_review_attempts(connection, [row[0] for row in rows])
    sensitivity = check["inputs"].get("sensitivity") or {}
    last = sensitivity.get("last_evidence_at")
    out: list[RecordedUpdate] = []
    for attempt_id, item_id, at, correctness, primed, attempt_type, delta_json, debug_json in rows:
        try:
            delta = json.loads(delta_json) if delta_json else None
            debug = json.loads(debug_json) if debug_json else None
        except ValueError:
            return None
        if not delta or not debug or debug.get("observation_weight") is None:
            return None
        mu0, var0 = float(delta["mu_before"]), float(delta["P_before"])
        mu1, var1 = float(delta["mu_after"]), float(delta["P_after"])
        applied = correctness is not None and str(attempt_id) not in held and (mu0 != mu1 or var0 != var1)
        item = vault.practice_items.get(str(item_id))
        a, b = item_irt_params(item, vault.learning_objects.get(lo), mastery_config)
        weight = float(debug["observation_weight"])
        variance = (_interpretation_variance(mu0, var0, last, str(at), a=float(a), b=float(b), weight=weight,
                                             variance_after=var1, config=mastery_config) if applied else 0.0)
        out.append(RecordedUpdate(
            attempt_id=str(attempt_id), at=str(at), y=float(correctness or 0.0), item_a=float(a), item_b=float(b),
            weight=weight, interpretation_variance=variance, primed=bool(primed), attempt_type=str(attempt_type),
            applied=applied, varied=str(attempt_id) == str(check["attempt_id"])))
        if applied and not primed:
            last = str(at)
    return out


def trajectory_state(sensitivity: "CheckSensitivity", updates: Sequence[RecordedUpdate], *, mass: float,
                     recorded_mass: float, mastery_config: Any) -> Any:
    """The LO's mastery state just before the outcome, recomputed from the check's recorded prior with
    the check entered at ``mass`` and every other update as recorded."""

    from learnloop.db.repositories import MasteryState
    from learnloop.learner.mastery import MasteryObservation, update_mastery

    state = MasteryState(
        learning_object_id="lesson_check", logit_mean=sensitivity.mu, logit_variance=sensitivity.variance,
        evidence_count=0, last_evidence_at=sensitivity.last_evidence_at, algorithm_version="lesson_weight",
        updated_at=sensitivity.observed_at)
    for update in updates:
        if not update.applied:
            continue
        weight = update.weight * (float(mass) / float(recorded_mass)) if update.varied and recorded_mass > 0 \
            else update.weight
        observed = parse_utc(update.at)
        assert observed is not None
        observation = MasteryObservation(
            rubric_score=0, max_points=1, evidence_coverage=1.0, hint_dampening=1.0, grader_confidence=1.0,
            attempt_type=update.attempt_type, observed_at=observed, observation_weight_override=weight,
            interpretation_variance=update.interpretation_variance, soft_score_override=update.y,
            primed=update.primed)
        state = update_mastery(state, observation, mastery_config, "lesson_weight", item_a=update.item_a,
                               item_b=update.item_b)
    return state


def trajectory_success(state: Any, *, a: float, b: float, at: str, mastery_config: Any) -> float:
    """The mastery model's predicted success at ``at`` from ``state`` (its drift since the last evidence,
    held to ``p_max`` as the model holds it)."""

    days = _days(state.last_evidence_at, at) if state.last_evidence_at else 0.0
    variance = min(float(state.logit_variance) + float(getattr(mastery_config, "sigma2_drift", 0.0)) * days,
                   float(getattr(mastery_config, "p_max", math.inf)))
    return predicted_success(float(state.logit_mean), variance, a=a, b=b)


def pool_implied_mass(sensitivity: CheckSensitivity, target: float, mastery_config: Any, *,
                      a: float | None = None, b: float | None = None, days: float = 0.0) -> float:
    """The mass at which the mastery update makes the predicted success equal ``target`` (§12.2):
    the success on the committed cold item (``a``, ``b``; the check's own item when not given) at
    the forecast's horizon (``days`` of drift), the same item and horizon ``target``'s ``p_A`` was
    computed for (review F5).

    A one-dimensional search on the logit scale (the mass lies in (0, 1) by the link); the
    predicted success is monotone in the mass for a fixed grade, so bisection finds it, or the
    end of the search interval nearest it when it is out of reach."""

    item_a = sensitivity.item_a if a is None else float(a)
    item_b = sensitivity.item_b if b is None else float(b)
    drift = float(getattr(mastery_config, "sigma2_drift", 0.0))

    def p_at(eta: float) -> float:
        mu, var = posterior_after(sensitivity, float(sigmoid(eta)), mastery_config)
        return predicted_success(mu, var, a=item_a, b=item_b, drift=drift, days=days)

    lo, hi = -_IMPLIED_ETA_BOUND, _IMPLIED_ETA_BOUND
    p_lo, p_hi = p_at(lo), p_at(hi)
    increasing = p_hi >= p_lo
    if (target <= min(p_lo, p_hi)) or (target >= max(p_lo, p_hi)):
        nearer_low = abs(target - p_lo) <= abs(target - p_hi)
        return float(sigmoid(lo if nearer_low else hi))
    for _ in range(_BISECTION_STEPS):
        mid = 0.5 * (lo + hi)
        value = p_at(mid)
        if (value < target) == increasing:
            lo = mid
        else:
            hi = mid
    return float(sigmoid(0.5 * (lo + hi)))


# --- the updates ----------------------------------------------------------------


def _soft_log_lik(p: np.ndarray, y: float) -> np.ndarray:
    p = np.clip(p, 1e-12, 1.0 - 1e-12)
    return y * np.log(p) + (1.0 - y) * np.log(1.0 - p)


def _resolve_check(state: WeightState, check: Mapping[str, Any], outcome: Mapping[str, Any], share: float,
                   mastery_config: Any, trajectory: Sequence[RecordedUpdate] | None = None) -> dict[str, Any]:
    """One check's factor from its resolving outcome, at power ``share``.

    With the LO's recorded ``trajectory`` (:func:`recorded_trajectory`), the likelihood recomputes the
    LO's updates from the check's recorded prior with only the check's mass varied: the check keeps its
    own recorded observation factors, and every intervening update is re-applied as recorded (§12.1).
    Without one (an attempt left no record), the first-order form: the check alone at full reliability,
    then the drift to the outcome."""

    inputs = check["inputs"]
    sensitivity = CheckSensitivity.from_dict(inputs["sensitivity"])
    lo = str(check["learning_object_id"])
    z_c, z_p = float(inputs.get("z_c") or 0.0), float(inputs.get("z_p") or 0.0)
    y = float(outcome["correctness"])
    days = _days(sensitivity.observed_at, str(outcome["created_at"]))
    drift = float(getattr(mastery_config, "sigma2_drift", 0.0))
    outcome_a = float(outcome.get("item_a", sensitivity.item_a))
    outcome_b = float(outcome.get("item_b", sensitivity.item_b))
    recorded_mass = float(check.get("mass_applied") or 0.0)
    exact = trajectory is not None and recorded_mass > 0.0

    def p_at_mass(mass: float) -> float:
        if exact:
            assert trajectory is not None
            final = trajectory_state(sensitivity, trajectory, mass=mass, recorded_mass=recorded_mass,
                                     mastery_config=mastery_config)
            return trajectory_success(final, a=outcome_a, b=outcome_b, at=str(outcome["created_at"]),
                                      mastery_config=mastery_config)
        mu, var = posterior_after(sensitivity, mass, mastery_config)
        return predicted_success(mu, var, a=outcome_a, b=outcome_b, drift=drift, days=days)

    def p_of_eta(eta: np.ndarray) -> np.ndarray:
        return np.asarray([p_at_mass(float(sigmoid(value))) for value in np.atleast_1d(eta)])

    def log_lik(eta: np.ndarray) -> np.ndarray:
        return share * _soft_log_lik(p_of_eta(eta), y)

    learned_before = state.learned_mass(lo, z_c, z_p)
    # Prequential bookkeeping (the report's side-by-side log loss): the predictive under the
    # learned posterior before this update, and under the fixed type mass 0.5.
    weights = state.tau_weights()
    predictive = 0.0
    for w, (m, v) in zip(weights, state.eta_moments(lo, z_c, z_p)):
        eta = m + math.sqrt(max(v, 0.0)) * NODES
        predictive += w * float((WEIGHTS * p_of_eta(eta)).sum())
    fixed = p_at_mass(0.5)
    state.prequential.append((float(share * _soft_log_lik(np.array([predictive]), y)[0]),
                              float(share * _soft_log_lik(np.array([fixed]), y)[0])))
    index = state._ensure_lo(lo)
    for bank, h in zip(state.banks, state._h(lo, z_c, z_p)):
        assert h[index] == 1.0
        bank.mean, bank.cov, record = adf_update(bank.mean, bank.cov, h, log_lik)
        bank.log_w += record.log_z
    return {"z_c": z_c, "z_p": z_p, "y": y, "share": share, "days": round(days, 6),
            "likelihood": "recorded_trajectory" if exact else "first_order",
            "intervening": (sum(1 for u in trajectory if not u.varied and u.applied) if exact and trajectory else 0),
            "mass_before": round(learned_before, 10), "mass_after": round(state.learned_mass(lo, z_c, z_p), 10),
            "tau_weights": [round(float(w), 10) for w in state.tau_weights()]}


def forecast_p_a(forecast: Mapping[str, Any], outcome: Mapping[str, Any], mastery_config: Any) -> float:
    """``p_A`` for the outcome that resolves a forecast: the mastery prediction from the state the
    forecast was made at, for the resolving item at the outcome's horizon (both predictors of the same
    cold outcome, §12.2; review F5). A forecast recorded without its state keeps its recorded ``p_A``."""

    recorded = forecast.get("state") or {}
    if recorded.get("mu") is None or recorded.get("variance") is None or outcome.get("item_a") is None:
        return float(forecast["p_a"])
    last = recorded.get("last_evidence_at") or forecast.get("created_at")
    days = _days(str(last), str(outcome["created_at"])) if last else 0.0
    variance = min(float(recorded["variance"]) + float(getattr(mastery_config, "sigma2_drift", 0.0)) * days,
                   float(getattr(mastery_config, "p_max", math.inf)))
    return predicted_success(float(recorded["mu"]), variance, a=float(outcome["item_a"]), b=float(outcome["item_b"]))


def _resolve_forecast(state: WeightState, forecast: Mapping[str, Any], outcome: Mapping[str, Any],
                      share: float, mastery_config: Any = None) -> dict[str, Any]:
    family = str(forecast["family"])
    log_w = state.pools.get(family)
    if log_w is None:
        log_w = _pool_prior_log_w()
    grid = _pool_grid()
    p_a = forecast_p_a(forecast, outcome, mastery_config) if mastery_config is not None else float(forecast["p_a"])
    p = grid * float(forecast["p_b"]) + (1.0 - grid) * p_a
    y = float(outcome["correctness"])
    before = float((normalized_log_weights(log_w) * grid).sum())
    log_w = log_w + share * _soft_log_lik(p, y)
    state.pools[family] = log_w
    state.pool_updates[family] = state.pool_updates.get(family, 0) + 1
    return {"family": family, "p_a": p_a, "p_a_at_forecast": forecast["p_a"], "p_b": forecast["p_b"], "y": y,
            "share": share,
            "lambda_before": round(before, 10), "lambda_after": round(float((normalized_log_weights(log_w) * grid).sum()), 10)}


def _calibrate(state: WeightState, attempt: Mapping[str, Any]) -> None:
    y = float(attempt["correctness"])
    tap, hedge = attempt.get("tap"), attempt.get("hedge")

    def soft(eta: np.ndarray) -> np.ndarray:
        return _soft_log_lik(sigmoid(eta), y)

    if tap is not None and int(tap) in TAP_PRIOR_MAP:
        h = np.array([1.0, logit(TAP_PRIOR_MAP[int(tap)])])
        state.tap.mean, state.tap.cov, _ = adf_update(state.tap.mean, state.tap.cov, h, soft)
        state.tap.updates += 1
        state.tap.through_at = str(attempt["created_at"])
    if hedge in HEDGE_VALUES:
        h = np.zeros(len(HEDGE_VALUES))
        h[HEDGE_VALUES.index(str(hedge))] = 1.0
        state.hedge.mean, state.hedge.cov, _ = adf_update(state.hedge.mean, state.hedge.cov, h, soft)
        state.hedge.updates += 1
        state.hedge.through_at = str(attempt["created_at"])


# =============================================================================
# The imperative shell: reading the ledgers in order
# =============================================================================


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def read_hedges(connection: Any) -> dict[str, str]:
    """Each attempt's hedge read from its current grading evidence (``confidence_events.read_hedges``'s
    rule, read here so the evidence side imports no context module; a test pins the two equal)."""

    columns = {row[1] for row in connection.execute("PRAGMA table_info(grading_evidence)")}
    if not {"learner_confidence", "superseded_at"} <= columns:
        return {}
    grader = "local_grader_id" if "local_grader_id" in columns else "NULL"
    reads: dict[str, list[str]] = {}
    for attempt_id, value, local in connection.execute(
            f"SELECT attempt_id, learner_confidence, {grader} FROM grading_evidence WHERE superseded_at IS NULL "
            "AND learner_confidence IN ('hedged', 'confident') ORDER BY attempt_id, id"):
        if local is not None and str(local) in ("self", "exam_import", "sim"):
            continue
        reads.setdefault(str(attempt_id), []).append(str(value))
    out = {}
    for attempt_id, values in reads.items():
        unique = set(values)
        if len(unique) == 1:
            out[attempt_id] = values[0]
        elif unique:
            out[attempt_id] = "hedged"
    return out


def _checks(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT id, lesson_id, node_id, learning_object_id, attempt_id, correctness, tap, hedge, "
        "mass_learned, mass_applied, weight_inputs_json, created_at FROM lesson_checks "
        "WHERE status = 'answered' ORDER BY created_at, id").fetchall()
    # A check whose own grade is held moved nothing (the attempt step takes no evidence from it): it has
    # no factor to resolve until its grade is released.
    held = held_for_review_attempts(connection, [row[4] for row in rows if row[4]]) if rows else frozenset()
    out = []
    for row in rows:
        if row[4] and str(row[4]) in held:
            continue
        out.append({
            "id": row[0], "lesson_id": row[1], "node_id": row[2], "learning_object_id": row[3],
            "attempt_id": row[4], "correctness": row[5], "tap": row[6], "hedge": row[7],
            "mass_learned": row[8], "mass_applied": row[9], "inputs": json.loads(row[10] or "{}"),
            "created_at": row[11]})
    return out


def _forecasts(connection: Any) -> list[dict[str, Any]]:
    if not _table(connection, "forecast_receipts"):
        return []
    out = []
    for key, p, inputs, created in connection.execute(
            "SELECT receipt_key, p, inputs_json, created_at FROM forecast_receipts "
            "WHERE kind = 'lesson_step_retained' ORDER BY created_at, id"):
        data = json.loads(inputs or "{}")
        if p is None or data.get("p_a") is None or not data.get("learning_object_id"):
            continue
        out.append({"key": key, "p_b": float(p), "p_a": float(data["p_a"]), "family": str(data.get("family")),
                    "learning_object_id": str(data["learning_object_id"]), "created_at": created,
                    "state": data.get("state")})
    return out


def qualifying_outcomes(connection: Any, learning_object_ids: Iterable[str], after: str | None,
                        *, until: str | None = None) -> list[dict[str, Any]]:
    """Graded attempts that can resolve a lesson check (§12.1), in order: on one of the LOs, after
    ``after``, of a cold type (:data:`COLD_ATTEMPT_TYPES`), unprimed, with no hint, the item's first
    attempt, with no reveal row on the item before it."""

    ids = sorted(set(learning_object_ids))
    if not ids or after is None:
        return []
    marks = ",".join("?" for _ in ids)
    types = ",".join("?" for _ in COLD_ATTEMPT_TYPES)
    params: list[Any] = [*ids, after, *COLD_ATTEMPT_TYPES]
    bound = ""
    if until is not None:
        bound = " AND a.created_at <= ?"
        params.append(until)
    rows = connection.execute(
        f"SELECT a.id, a.learning_object_id, a.practice_item_id, a.correctness, a.created_at, a.attempt_type "
        f"FROM practice_attempts a "
        f"WHERE a.learning_object_id IN ({marks}) AND a.created_at > ? AND a.attempt_type IN ({types}) "
        f"AND a.primed = 0 AND a.hints_used = 0 AND a.correctness IS NOT NULL{bound} "
        "AND NOT EXISTS (SELECT 1 FROM practice_attempts b WHERE b.practice_item_id = a.practice_item_id "
        "  AND (b.created_at < a.created_at OR (b.created_at = a.created_at AND b.id < a.id))) "
        "AND NOT EXISTS (SELECT 1 FROM reveal_events r WHERE r.practice_item_id = a.practice_item_id "
        "  AND r.created_at < a.created_at) "
        "ORDER BY a.created_at, a.id", params).fetchall()
    # A grade held for review is the grader's provisional score: no outcome anywhere (held_grades, the
    # canonical predicate; review F2). Released, it qualifies again on the next replay.
    held = held_for_review_attempts(connection, [row[0] for row in rows]) if rows else frozenset()
    return [{"id": row[0], "learning_object_id": row[1], "practice_item_id": row[2], "correctness": float(row[3]),
             "created_at": row[4], "attempt_type": row[5]} for row in rows if str(row[0]) not in held]


def _calibration_attempts(connection: Any, hedges: Mapping[str, str], until: str | None) -> list[dict[str, Any]]:
    bound, params = "", []
    if until is not None:
        bound, params = " AND created_at < ?", [until]
    rows = connection.execute(
        "SELECT id, answer_confidence, correctness, created_at FROM practice_attempts "
        f"WHERE correctness IS NOT NULL{bound} ORDER BY created_at, id", params).fetchall()
    held = held_for_review_attempts(connection, [row[0] for row in rows]) if rows else frozenset()
    out = []
    for attempt_id, tap, correctness, created in rows:
        if str(attempt_id) in held:
            continue
        hedge = hedges.get(str(attempt_id))
        if tap is None and hedge is None:
            continue
        out.append({"id": attempt_id, "tap": tap, "hedge": hedge, "correctness": float(correctness),
                    "created_at": created})
    return out


def _outcome_item_params(vault: Any, mastery_config: Any, outcome: Mapping[str, Any]) -> dict[str, float]:
    if vault is None:
        return {}
    from learnloop.learner.mastery import item_irt_params

    item = vault.practice_items.get(str(outcome["practice_item_id"]))
    learning_object = vault.learning_objects.get(str(outcome["learning_object_id"]))
    a, b = item_irt_params(item, learning_object, mastery_config)
    return {"item_a": float(a), "item_b": float(b)}


#: The terms a report's prior-sensitivity rerun may shift (index in the state vector).
PRIOR_TERMS: Mapping[str, int] = {"eta0": 0, "beta_c": 1, "beta_p": 2}


def replay_state(vault: Any, repository: Any, *, as_of: str | None = None, through: str | None = None,
                 prior_shift: Mapping[str, float] | None = None) -> WeightState:
    """The three posteriors from the ledgers, in order, with every event strictly before ``as_of``
    (all of them when None): the prequential filter both the live check and the replayer run.
    ``through``: every event at or before that instant (the DERIVED tables' bound: the latest lesson
    check, :func:`tables_through`). ``prior_shift`` (the report's sensitivity rerun only) moves prior
    means by the given amounts."""

    mastery_config = vault.config.mastery
    state = WeightState()
    for term, amount in (prior_shift or {}).items():
        for bank in state.banks:
            bank.mean[PRIOR_TERMS[term]] += float(amount)
    with repository.connection() as connection:
        if not _table(connection, "lesson_checks"):
            return state
        checks = [c for c in _checks(connection) if as_of is None or str(c["created_at"]) < as_of]
        forecasts = [f for f in _forecasts(connection) if as_of is None or str(f["created_at"]) < as_of]
        hedges = read_hedges(connection)
        calibration = _calibration_attempts(connection, hedges, as_of)
        los = {str(c["learning_object_id"]) for c in checks} | {f["learning_object_id"] for f in forecasts}
        first = min([str(c["created_at"]) for c in checks] + [str(f["created_at"]) for f in forecasts], default=None)
        outcomes = qualifying_outcomes(connection, los, first)
        if as_of is not None:
            outcomes = [o for o in outcomes if str(o["created_at"]) < as_of]
    # Events in time order. A check (and a forecast) sees only what happened strictly before its
    # instant, as the live check's ``as_of`` does, so at one instant it comes first; an outcome
    # resolves only checks and forecasts made strictly before it.
    events: list[tuple[str, int, str, str, Mapping[str, Any]]] = []
    for check in checks:
        events.append((str(check["created_at"]), 0, str(check["id"]), "check", check))
    for forecast in forecasts:
        events.append((str(forecast["created_at"]), 1, str(forecast["key"]), "forecast", forecast))
    for attempt in calibration:
        events.append((str(attempt["created_at"]), 2, str(attempt["id"]), "calibrate", attempt))
    for outcome in outcomes:
        events.append((str(outcome["created_at"]), 3, str(outcome["id"]), "outcome", outcome))
    events.sort(key=lambda event: (event[0], event[1], event[2]))
    if through is not None:
        events = [event for event in events if event[0] <= through]
    open_checks: dict[str, list[Mapping[str, Any]]] = {}
    open_forecasts: dict[str, list[Mapping[str, Any]]] = {}
    for at, _order, _ref, kind, payload in events:
        if kind == "calibrate":
            _calibrate(state, payload)
        elif kind == "check":
            open_checks.setdefault(str(payload["learning_object_id"]), []).append(payload)
            state.trace.append({"kind": "mass", "lesson_check_id": payload["id"], "resolving_attempt_id": None,
                                "learning_object_id": payload["learning_object_id"], "at": at,
                                "detail": _mass_detail(state, payload)})
        elif kind == "forecast":
            open_forecasts.setdefault(str(payload["learning_object_id"]), []).append(payload)
        else:
            lo = str(payload["learning_object_id"])
            pending = [c for c in open_checks.get(lo, []) if str(c["created_at"]) < at]
            open_checks[lo] = [c for c in open_checks.get(lo, []) if str(c["created_at"]) >= at]
            enriched = {**payload, **_outcome_item_params(vault, mastery_config, payload)}
            for check in pending:
                with repository.connection() as connection:
                    trajectory = recorded_trajectory(connection, vault, mastery_config, check, payload)
                detail = _resolve_check(state, check, enriched, 1.0 / len(pending), mastery_config,
                                        trajectory=trajectory)
                state.updates += 1
                state.through_at = at
                state.trace.append({"kind": "weight_update", "lesson_check_id": check["id"],
                                    "resolving_attempt_id": payload["id"], "learning_object_id": lo, "at": at,
                                    "detail": detail})
            waiting = [f for f in open_forecasts.get(lo, []) if str(f["created_at"]) < at]
            open_forecasts[lo] = [f for f in open_forecasts.get(lo, []) if str(f["created_at"]) >= at]
            for forecast in waiting:
                detail = _resolve_forecast(state, forecast, enriched, 1.0 / len(waiting), mastery_config)
                state.through_at = at
                state.trace.append({"kind": "pool_update", "lesson_check_id": None,
                                    "resolving_attempt_id": payload["id"], "learning_object_id": lo, "at": at,
                                    "detail": {**detail, "forecast_key": forecast["key"]}})
    return state


def _mass_detail(state: WeightState, check: Mapping[str, Any]) -> dict[str, Any]:
    """The check's recorded mass beside what the posterior as of the check gives (the equivalence
    guard: :func:`mass_mismatches`), with the recalibrated confidence term recomputed too."""

    inputs = check["inputs"]
    lo = str(check["learning_object_id"])
    z_c, z_p = float(inputs.get("z_c") or 0.0), float(inputs.get("z_p") or 0.0)
    recomputed_z_c, _source = confidence_term(state, check.get("tap"), check.get("hedge"))
    return {"rule": inputs.get("rule"), "mass_learned": check.get("mass_learned"),
            "mass_applied": check.get("mass_applied"), "z_c": z_c, "z_p": z_p, "pool": inputs.get("pool"),
            "recomputed": round(state.learned_mass(lo, z_c, z_p), 12),
            "recomputed_z_c": round(recomputed_z_c, 12)}


# =============================================================================
# The one seam into mastery, and the DERIVED tables
# =============================================================================


def lesson_check_mass(repository: Any, attempt_id: str, attempt_type: str) -> float | None:
    """The mass a lesson check's attempt enters mastery at, as recorded when it was graded; None for
    every other attempt (the type's configured mass applies). Live and replay read this same row,
    so a past check's mass never changes within a version (§12.1: filtering, never smoothing)."""

    if attempt_type != LESSON_CHECK_ATTEMPT_TYPE:
        return None
    with repository.connection() as connection:
        if not _table(connection, "lesson_checks"):
            return None
        row = connection.execute(
            "SELECT mass_applied FROM lesson_checks WHERE attempt_id = ? AND status = 'answered'",
            (str(attempt_id),)).fetchone()
    if row is None or row[0] is None:
        return None
    return float(row[0])


def _state_rows(state: WeightState) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    weights = state.tau_weights()
    weight_state = {
        "version": STATE_VERSION,
        "tau_grid": list(TAU_GRID),
        "tau_weights": [round(float(w), 12) for w in weights],
        "learning_objects": dict(sorted(state.lo_index.items())),
        "banks": [{"tau": bank.tau, "mean": [round(float(x), 12) for x in bank.mean],
                   "cov": [[round(float(x), 12) for x in row] for row in bank.cov], "log_w": round(bank.log_w, 12)}
                  for bank in state.banks],
        "global_mass": round(state.learned_mass("", 0.0, 0.0), 12),
    }
    states = [("weight", json.dumps(weight_state, sort_keys=True), state.updates, state.through_at, PRIORS_VERSION)]
    for family in sorted(state.pools):
        states.append((f"pool:{family}", json.dumps({
            "version": STATE_VERSION, "grid_points": POOL_GRID_POINTS,
            "weights": [round(float(w), 12) for w in normalized_log_weights(state.pools[family])],
            "lambda": round(state.pool_lambda(family), 12)}, sort_keys=True),
            state.pool_updates.get(family, 0), state.through_at, PRIORS_VERSION))
    calibration = [
        ("tap", json.dumps({"version": STATE_VERSION, "mean": [round(float(x), 12) for x in state.tap.mean],
                            "cov": [[round(float(x), 12) for x in row] for row in state.tap.cov],
                            "probabilities": {str(tap): round(state.tap_probability(tap), 12) for tap in TAP_PRIOR_MAP}},
                           sort_keys=True), state.tap.updates, state.tap.through_at, PRIORS_VERSION),
        ("hedge", json.dumps({"version": STATE_VERSION, "mean": [round(float(x), 12) for x in state.hedge.mean],
                              "cov": [[round(float(x), 12) for x in row] for row in state.hedge.cov],
                              "probabilities": {value: round(state.hedge_probability(value), 12) for value in HEDGE_VALUES}},
                             sort_keys=True), state.hedge.updates, state.hedge.through_at, PRIORS_VERSION),
    ]
    trace = [(f"lwt_{index:08d}", index, entry["kind"], entry["lesson_check_id"], entry["resolving_attempt_id"],
              entry["learning_object_id"], entry["at"], json.dumps(entry["detail"], sort_keys=True, default=float))
             for index, entry in enumerate(state.trace, start=1)]
    return states, trace, calibration


DERIVED_TABLES: tuple[str, ...] = ("lesson_weight_state", "lesson_weight_trace", "confidence_calibration_state")


def write_state(repository: Any, state: WeightState) -> dict[str, int]:
    """Replace the three DERIVED tables with ``state`` (in the caller's transaction)."""

    states, trace, calibration = _state_rows(state)
    with repository.connection() as connection:
        for table in DERIVED_TABLES:
            connection.execute(f"DELETE FROM {table}")
        connection.executemany(
            "INSERT INTO lesson_weight_state(family, state_json, updates, through_at, priors_version) "
            "VALUES (?, ?, ?, ?, ?)", states)
        connection.executemany(
            "INSERT INTO lesson_weight_trace(id, seq, kind, lesson_check_id, resolving_attempt_id, "
            "learning_object_id, at, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", trace)
        connection.executemany(
            "INSERT INTO confidence_calibration_state(family, state_json, updates, through_at, priors_version) "
            "VALUES (?, ?, ?, ?, ?)", calibration)
    return {"lesson_weight_state": len(states), "lesson_weight_trace": len(trace),
            "confidence_calibration_state": len(calibration)}


def any_lessons(repository: Any) -> bool:
    with repository.connection() as connection:
        if not _table(connection, "lesson_checks"):
            return False
        return connection.execute("SELECT 1 FROM lesson_checks LIMIT 1").fetchone() is not None


def tables_through(repository: Any) -> str | None:
    """The instant the DERIVED tables describe: the latest answered lesson check (the live path writes
    them right after each check, so the replayer bounds its replay at the same instant and the two agree
    row for row whatever happened since; review claim on rebuild equivalence). None: no check yet."""

    with repository.connection() as connection:
        if not _table(connection, "lesson_checks"):
            return None
        row = connection.execute("SELECT MAX(created_at) FROM lesson_checks WHERE status = 'answered'").fetchone()
    return str(row[0]) if row and row[0] is not None else None


def rebuild_lesson_weight_state(vault: Any, repository: Any) -> dict[str, Any]:
    """The replayer (``substrate.rebuild_orchestrator``): clear the three DERIVED tables and recompute
    them through the latest answered lesson check (:func:`tables_through`), exactly as the live path
    wrote them then. A vault where no lesson check was ever recorded keeps them empty (the live path
    writes them only after a check), so a rebuild of a lessonless vault changes nothing. Every reader
    of the current posterior replays the ledgers itself (:func:`replay_state`), never these tables."""

    with repository.connection() as connection:
        for table in DERIVED_TABLES:
            if _table(connection, table):
                connection.execute(f"DELETE FROM {table}")
    if not any_lessons(repository):
        return {"rows": 0, "checks": 0}
    state = replay_state(vault, repository, through=tables_through(repository))
    counts = write_state(repository, state)
    return {"rows": sum(counts.values()), "updates": state.updates, **counts}


def mass_mismatches(state: WeightState) -> list[dict[str, Any]]:
    """Checks whose recorded mass a replay would not reproduce (the equivalence guard): the mass
    applied under its rule must equal the learned mass recomputed as of the check."""

    out = []
    for entry in state.trace:
        if entry["kind"] != "mass":
            continue
        detail = entry["detail"]
        if detail.get("rule") in (RULE_LEARNED, RULE_POOL) and detail.get("recomputed") is not None:
            if (abs(float(detail["recomputed"]) - float(detail["mass_learned"])) > 1e-9
                    or abs(float(detail["recomputed_z_c"]) - float(detail["z_c"])) > 1e-9):
                out.append(entry)
    return out


__all__ = [
    "BETA_C_PRIOR_SD",
    "BETA_P_PRIOR_SD",
    "CheckSensitivity",
    "COLD_ATTEMPT_TYPES",
    "DERIVED_TABLES",
    "ETA0_PRIOR_MEAN",
    "ETA0_PRIOR_SD",
    "POOL_GRID_POINTS",
    "POOL_PRIOR_ALPHA",
    "POOL_PRIOR_BETA",
    "PRIORS_VERSION",
    "RULE_FIXED",
    "RULE_LEARNED",
    "RULE_POOL",
    "RecordedUpdate",
    "TAP_PRIOR_MAP",
    "TAU_GRID",
    "WeightState",
    "any_lessons",
    "confidence_term",
    "lesson_check_mass",
    "pool_implied_mass",
    "posterior_after",
    "predicted_success",
    "prediction_term",
    "qualifying_outcomes",
    "read_hedges",
    "rebuild_lesson_weight_state",
    "recorded_trajectory",
    "tables_through",
    "replay_state",
    "trajectory_state",
    "trajectory_success",
    "write_state",
]
