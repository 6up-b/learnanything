"""Robust diagnostic composition (spec_p0_measurement_correctness §4.2).

Replaces the point grader channel + point instrument likelihoods with a pinned
robust composition. For a fixed calibration-model draw ``m`` and observed grader
emission ``E = (G, conf_bucket)``::

    P_m(E | H) = sum_z  P_m(E | Z, ctx) * P(Z | H, card)

``P(Z | H, card)`` is the hand-authored instrument row (probe card conditional or,
for the reliability path, the identity mapping); ``P_m(E | Z, ctx)`` is one row of
the resolved calibration model's joint Dirichlet alpha (P0.2 ``ResolvedModel``).

The model's Dirichlet posterior is evaluated with a **deterministic ensemble**:
the posterior-mean member plus ``ROBUST_DRAW_COUNT`` draws seeded from a SHA-256
over the pinned calibration-model hash and the decision-context hash. The ensemble
also perturbs each hand-authored instrument row with a Dirichlet draw (robustness
analysis, NOT calibration -- U-014). The robust statistic is the empirical
``ROBUST_QUANTILE`` (10th) percentile.

Two consumers share the identical composition object (invariant 3, §9.1): candidate
EIG (marginalize over the emission alphabet) and the observed update (evaluate at the
realized E). Stopping/abstention use robust net value, not the per-second rank.

Convention: stdlib ``random.Random`` only (no numpy -- repo bit-for-bit replay
convention, see ``sim/student.py``). Dirichlet draws are gamma-then-normalize.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Mapping, Sequence

from learnloop.services.activities import _canonical_hash

# ---------------------------------------------------------------------------
# Decision parameters (§4.2, §7). All heuristic; the planted-learner suite is
# the mechanism gate for promotion to simulation_validated (registered in P0.5).
# ---------------------------------------------------------------------------

ROBUST_DRAW_COUNT = 128  # decision parameter: heuristic
ROBUST_QUANTILE = 0.10  # decision parameter: heuristic
INSTRUMENT_PERTURBATION_CONCENTRATION = 40.0  # decision parameter: heuristic
ENSEMBLE_ACTION_AGREEMENT_THRESHOLD = 0.90  # decision parameter: heuristic
ABSTENTION_BUDGET_FRACTION = 0.15  # decision parameter: heuristic
LAMBDA_TIME = 1.0  # decision parameter: heuristic (minutes numeraire, U-023; fixed at 1)
BURDEN_COST = 0.0  # decision parameter: heuristic (minutes-denominated stopping burden)
# Minutes-equivalent value of one nat of resolved diagnostic information. Converts
# the robust EIG (nats) into an EVSI denominated in minutes so the stop rule
# LCB(EVSI) <= lambda_time*expected_minutes + burden_cost is unit-consistent. The
# design fixes lambda_time and denominates burden in minutes but leaves the
# nat->minutes value scale to the registry; this is that scale.
VALUE_PER_NAT_MINUTES = 60.0  # decision parameter: heuristic


def _seed_int(calibration_model_hash: str, decision_context_hash: str) -> int:
    """Stable, platform-independent seed from the pinned hashes (§1.4).

    SHA-256 over ``model_hash|decision_context_hash`` -> first 8 bytes big-endian.
    A change to any pinned input or registered parameter produces a NEW hash and
    thus a new, auditable seed -- never a silent reseed."""

    digest = hashlib.sha256(
        f"{calibration_model_hash}|{decision_context_hash}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def decision_context_hash(
    *,
    episode_id: str | None,
    candidate_card_version: str | None,
    resolved_slot_map: Mapping[str, str] | None,
    posterior_at_selection: Mapping[str, float] | None,
    projection_algorithm_version: str,
    draw_count: int = ROBUST_DRAW_COUNT,
    quantile: float = ROBUST_QUANTILE,
    perturbation_concentration: float = INSTRUMENT_PERTURBATION_CONCENTRATION,
) -> str:
    """Canonical 32-char hash pinning the decision inputs + registered params so
    the ensemble is a pure function of the pinned decision (§1.4)."""

    return _canonical_hash(
        {
            "episode_id": episode_id,
            "candidate_card_version": candidate_card_version,
            "resolved_slot_map": dict(resolved_slot_map or {}),
            "posterior_at_selection": {
                k: round(float(v), 12) for k, v in dict(posterior_at_selection or {}).items()
            },
            "projection_algorithm_version": projection_algorithm_version,
            "robust_draw_count": draw_count,
            "robust_quantile": quantile,
            "instrument_perturbation_concentration": perturbation_concentration,
        }
    )


def _dirichlet(rng: random.Random, alpha: Sequence[float]) -> list[float]:
    draws = [rng.gammavariate(max(a, 1e-9), 1.0) for a in alpha]
    total = sum(draws) or 1.0
    return [d / total for d in draws]


def robust_quantile(values: Sequence[float], quantile: float = ROBUST_QUANTILE) -> float:
    """Empirical lower quantile (§4.2). ``quantile`` is the fraction in the tail
    (0.10 -> 10th percentile)."""

    if not values:
        return 0.0
    ordered = sorted(values)
    # Nearest-rank (ceil) lower quantile (L4): the smallest value whose rank covers
    # a ``quantile`` fraction of the sample. ``ceil(q*n)-1`` is the 0-based index.
    idx = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return ordered[idx]


# ---------------------------------------------------------------------------
# Composition: P_m(E | H) = sum_z P_m(E | Z) P(Z | H, card)
# ---------------------------------------------------------------------------

def compose_emission_over_hypotheses(
    emission_given_z: Mapping[str, Mapping[str, float]],
    instrument_rows: Mapping[str, Mapping[str, float]],
) -> dict[str, dict[str, float]]:
    """``P(E | H) = sum_z P(E | Z) P(Z | H, card)`` (§1.2).

    ``emission_given_z``: ``{Z: {E: prob}}`` (a single model draw / posterior mean).
    ``instrument_rows``: ``{H_slot: {Z: prob}}`` (authored / perturbed card rows).
    Returns ``{H_slot: {E: prob}}``. Emissions absent from a Z row contribute 0."""

    emissions: list[str] = sorted(
        {e for row in emission_given_z.values() for e in row}
    )
    composed: dict[str, dict[str, float]] = {}
    for slot, z_row in instrument_rows.items():
        out: dict[str, float] = {e: 0.0 for e in emissions}
        for z, p_z in z_row.items():
            likelihoods = emission_given_z.get(z, {})
            for e in emissions:
                out[e] += likelihoods.get(e, 0.0) * float(p_z)
        composed[slot] = out
    return composed


def _normalized_mean_emission(
    joint_alpha: Mapping[str, Mapping[str, float]]
) -> dict[str, dict[str, float]]:
    """Posterior-mean ``P(E | Z)`` = normalized alpha rows (member 0)."""

    mean: dict[str, dict[str, float]] = {}
    for z, row in joint_alpha.items():
        total = sum(row.values()) or 1.0
        mean[z] = {e: v / total for e, v in row.items()}
    return mean


def _draw_emission(
    rng: random.Random, joint_alpha: Mapping[str, Mapping[str, float]]
) -> dict[str, dict[str, float]]:
    """One Dirichlet draw of ``P(E | Z)`` per true class Z."""

    drawn: dict[str, dict[str, float]] = {}
    for z, row in joint_alpha.items():
        keys = sorted(row.keys())
        sampled = _dirichlet(rng, [row[k] for k in keys])
        drawn[z] = dict(zip(keys, sampled))
    return drawn


def _perturb_instrument(
    rng: random.Random,
    instrument_rows: Mapping[str, Mapping[str, float]],
    concentration: float,
) -> dict[str, dict[str, float]]:
    """Dirichlet perturbation around each authored instrument row (§4.2). This is
    robustness analysis, not calibration -- it never writes back to any model."""

    perturbed: dict[str, dict[str, float]] = {}
    for slot, row in instrument_rows.items():
        keys = sorted(row.keys())
        alpha = [max(float(row[k]), 0.0) * concentration + 1e-9 for k in keys]
        sampled = _dirichlet(rng, alpha)
        perturbed[slot] = dict(zip(keys, sampled))
    return perturbed


@dataclass(frozen=True)
class Ensemble:
    """A deterministic ensemble of composed ``P(E | H)`` tables (member 0 = the
    posterior-mean, un-perturbed decision; members 1..N = draws)."""

    members: tuple[dict[str, dict[str, float]], ...]  # each: {H_slot: {E: prob}}
    slots: tuple[str, ...]
    emissions: tuple[str, ...]
    calibration_model_hash: str
    decision_context_hash: str
    seed: int
    draw_count: int
    quantile: float
    perturbation_concentration: float

    @property
    def mean_member(self) -> dict[str, dict[str, float]]:
        return self.members[0]


def build_ensemble(
    *,
    joint_alpha: Mapping[str, Mapping[str, float]],
    instrument_rows: Mapping[str, Mapping[str, float]],
    calibration_model_hash: str,
    decision_context_hash: str,
    draw_count: int = ROBUST_DRAW_COUNT,
    quantile: float = ROBUST_QUANTILE,
    perturbation_concentration: float = INSTRUMENT_PERTURBATION_CONCENTRATION,
) -> Ensemble:
    """Build the deterministic composition ensemble (§1.3).

    Member 0 is the posterior mean + authored instrument rows (the anchor). Members
    1..``draw_count`` each draw ``P(E|Z)`` from the model's Dirichlet posterior and
    perturb the instrument rows, then compose per §1.2. Seeded from the pinned
    hashes so the ensemble is reproducible for audit; replay reads snapshots."""

    seed = _seed_int(calibration_model_hash, decision_context_hash)
    rng = random.Random(seed)

    mean_emission = _normalized_mean_emission(joint_alpha)
    members: list[dict[str, dict[str, float]]] = [
        compose_emission_over_hypotheses(mean_emission, instrument_rows)
    ]
    for _ in range(draw_count):
        drawn_emission = _draw_emission(rng, joint_alpha)
        perturbed_rows = _perturb_instrument(rng, instrument_rows, perturbation_concentration)
        members.append(
            compose_emission_over_hypotheses(drawn_emission, perturbed_rows)
        )

    slots = tuple(sorted(instrument_rows.keys()))
    emissions = tuple(sorted({e for row in joint_alpha.values() for e in row}))
    return Ensemble(
        members=tuple(members),
        slots=slots,
        emissions=emissions,
        calibration_model_hash=calibration_model_hash,
        decision_context_hash=decision_context_hash,
        seed=seed,
        draw_count=draw_count,
        quantile=quantile,
        perturbation_concentration=perturbation_concentration,
    )


# ---------------------------------------------------------------------------
# EIG / posterior update over a member table
# ---------------------------------------------------------------------------

def expected_information_gain(
    conditionals: Mapping[str, Mapping[str, float]],
    posterior: Mapping[str, float],
) -> float:
    """Hypothesis EIG in nats over a composed ``P(E | H)`` table -- the same math
    as ``probe_families.instrument_expected_information_gain`` but over emissions."""

    labels = [h for h in posterior if h in conditionals]
    if len(labels) <= 1:
        return 0.0
    weights = {h: max(float(posterior[h]), 0.0) for h in labels}
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    weights = {h: w / total for h, w in weights.items()}
    emissions = sorted({e for h in labels for e in conditionals[h]})
    mixture = {e: 0.0 for e in emissions}
    for h, w in weights.items():
        for e, p in conditionals[h].items():
            mixture[e] += w * p
    eig = 0.0
    for h, w in weights.items():
        if w <= 0:
            continue
        kl = 0.0
        for e, p in conditionals[h].items():
            m = mixture.get(e, 0.0)
            if p > 0 and m > 0:
                kl += p * math.log(p / m)
        eig += w * kl
    return max(eig, 0.0)


def observed_update(
    conditionals: Mapping[str, Mapping[str, float]],
    posterior: Mapping[str, float],
    observed_emission: str,
) -> dict[str, float]:
    """One Bayes step ``P(H | E) ∝ P(E | H) P(H)`` at the realized emission."""

    unnormalized = {
        h: conditionals.get(h, {}).get(observed_emission, 0.0) * max(float(posterior.get(h, 0.0)), 0.0)
        for h in posterior
    }
    total = sum(unnormalized.values())
    if total <= 0:
        n = len(posterior) or 1
        return {h: 1.0 / n for h in posterior}
    return {h: v / total for h, v in unnormalized.items()}


# ---------------------------------------------------------------------------
# Robust ranking, stopping, agreement gate, abstention (§3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RobustDecision:
    """Robust products of one selection decision, snapshotted so historical
    replay never re-runs the ensemble (§2.1/§3.3)."""

    chosen_slot: str | None
    robust_eig_per_second: float
    lcb_advantage_over_runner_up: float
    action_agreement_fraction: float
    should_stop: bool
    abstained: bool
    verdict: str  # 'act' | 'stop' | 'couldnt_reliably_distinguish'


def _ensemble_eig_per_second(
    ensemble: Ensemble,
    posterior: Mapping[str, float],
    expected_seconds: float,
) -> list[float]:
    seconds = max(float(expected_seconds), 1e-6)
    return [
        expected_information_gain(member, posterior) / seconds
        for member in ensemble.members
    ]


def robust_eig_per_second(
    ensemble: Ensemble,
    posterior: Mapping[str, float],
    expected_seconds: float,
    quantile: float | None = None,
) -> float:
    """10th-percentile of per-draw EIG per expected second (the robust rank score)."""

    q = ensemble.quantile if quantile is None else quantile
    return robust_quantile(_ensemble_eig_per_second(ensemble, posterior, expected_seconds), q)


def evaluate_selection(
    *,
    candidates: Sequence[tuple[str, Ensemble, float]],
    posterior: Mapping[str, float],
    lambda_time: float = LAMBDA_TIME,
    burden_cost: float = BURDEN_COST,
    value_per_nat_minutes: float = VALUE_PER_NAT_MINUTES,
    agreement_threshold: float = ENSEMBLE_ACTION_AGREEMENT_THRESHOLD,
) -> RobustDecision:
    """Robust selection over candidate instruments (§3.1/§3.2).

    ``candidates``: ``[(slot_or_id, ensemble, expected_seconds), ...]``. Chooses the
    top robust EIG/sec candidate, tests its 10th-pct advantage over the runner-up,
    applies the stop rule ``LCB(EVSI) <= lambda_time*expected_seconds + burden_cost``
    (EVSI proxied by robust EIG), and the >=90% ensemble action-agreement gate. When
    the winner is not robust the selector abstains with 'couldnt_reliably_distinguish'."""

    if not candidates:
        return RobustDecision(None, 0.0, 0.0, 0.0, True, False, "stop")

    scored = [
        (slot, robust_eig_per_second(ens, posterior, secs), ens, secs)
        for slot, ens, secs in candidates
    ]
    scored.sort(key=lambda t: t[1], reverse=True)
    best_slot, best_score, best_ens, best_secs = scored[0]

    # Per-draw advantage of the winner over the runner-up (per-second).
    if len(scored) >= 2:
        runner_ens, runner_secs = scored[1][2], scored[1][3]
        best_series = _ensemble_eig_per_second(best_ens, posterior, best_secs)
        runner_series = _ensemble_eig_per_second(runner_ens, posterior, runner_secs)
        advantage = [b - r for b, r in zip(best_series, runner_series)]
        lcb_advantage = robust_quantile(advantage, best_ens.quantile)
    else:
        # A single candidate has no runner-up; its advantage is its own robust value.
        lcb_advantage = best_score

    # Stop rule (§4.2): LCB(EVSI) <= lambda_time*expected_minutes + burden_cost, all
    # in minutes. EVSI = value_per_nat * robust EIG (nats) of the best candidate.
    best_eig_series = [
        expected_information_gain(member, posterior) for member in best_ens.members
    ]
    robust_evsi_minutes = value_per_nat_minutes * robust_quantile(best_eig_series, best_ens.quantile)
    stop_threshold = lambda_time * (best_secs / 60.0) + burden_cost
    should_stop = robust_evsi_minutes <= stop_threshold

    # Action-agreement gate: does the same winner top the ranking in >= threshold of
    # ensemble members? (per-member argmax over candidates' EIG/sec).
    per_member_winner_counts = 0
    n_members = len(best_ens.members)
    for i in range(n_members):
        member_scores = []
        for slot, _score, ens, secs in scored:
            seconds = max(float(secs), 1e-6)
            member_scores.append((slot, expected_information_gain(ens.members[i], posterior) / seconds))
        member_best = max(member_scores, key=lambda t: t[1])[0]
        if member_best == best_slot:
            per_member_winner_counts += 1
    agreement_fraction = per_member_winner_counts / n_members if n_members else 0.0

    robust_winner = lcb_advantage > 0.0
    passes_gate = agreement_fraction >= agreement_threshold

    if should_stop:
        # Nothing worth running: stable if the winner is robust + agrees, else abstain.
        if robust_winner and passes_gate:
            return RobustDecision(
                best_slot, best_score, lcb_advantage, agreement_fraction, True, False, "stop"
            )
        return RobustDecision(
            best_slot, best_score, lcb_advantage, agreement_fraction, True, True,
            "couldnt_reliably_distinguish",
        )

    if robust_winner and passes_gate:
        return RobustDecision(
            best_slot, best_score, lcb_advantage, agreement_fraction, False, False, "act"
        )
    # Fragile action: fails the robust action gate -> abstain / ask for a stronger
    # instrument (§4.4). Do not stop; park for a better instrument.
    return RobustDecision(
        best_slot, best_score, lcb_advantage, agreement_fraction, False, True,
        "couldnt_reliably_distinguish",
    )


# ---------------------------------------------------------------------------
# Certainty ensemble (§4.3) -- LCB of certainty over the calibration Dirichlet
# ---------------------------------------------------------------------------

def _certainty(posterior: Mapping[str, float]) -> float:
    k = len(posterior)
    if k <= 1:
        return 1.0
    entropy = 0.0
    for p in posterior.values():
        if p > 0:
            entropy -= p * math.log(p)
    return max(0.0, min(1.0, 1.0 - entropy / math.log(k)))


def certainty_lcb(
    *,
    joint_alpha: Mapping[str, Mapping[str, float]],
    observed_emission: str,
    calibration_model_hash: str,
    decision_context_hash: str,
    prior: Mapping[str, float] | None = None,
    draw_count: int = ROBUST_DRAW_COUNT,
    quantile: float = ROBUST_QUANTILE,
) -> float:
    """Lower credible bound of ``certainty = 1 - H(P(Z|E))/log K`` across the
    calibration ensemble (§4.3). Deterministic/point posteriors -> 1; a uniform
    P(Z|E) -> 0. Seeded from the pinned model + decision-context hash."""

    classes = sorted(joint_alpha.keys())
    if not classes:
        return 0.0
    if prior is None:
        prior = {z: 1.0 / len(classes) for z in classes}

    def _posterior_certainty(emission_given_z: Mapping[str, Mapping[str, float]]) -> float:
        unnormalized = {
            z: emission_given_z[z].get(observed_emission, 0.0) * prior.get(z, 0.0)
            for z in classes
        }
        total = sum(unnormalized.values())
        if total <= 0:
            return 0.0
        return _certainty({z: v / total for z, v in unnormalized.items()})

    # Member 0 is the posterior-MEAN P(E|Z) (M2): the un-drawn anchor. A symmetric
    # uniform joint_alpha yields an identical P(E|Z) for every Z, so the mean
    # posterior is exactly the (uniform) prior -> certainty 0. Every random draw
    # breaks that symmetry and reports spurious positive certainty, so the mean
    # member (and the floor below) is what makes a uniform interpretation yield a
    # certainty LCB of 0 and thus zero certification mass (§4.3, §9.2).
    point_certainty = _posterior_certainty(_normalized_mean_emission(joint_alpha))

    seed = _seed_int(calibration_model_hash, decision_context_hash)
    rng = random.Random(seed)
    samples: list[float] = [point_certainty]
    for _ in range(draw_count):
        drawn = _draw_emission(rng, joint_alpha)
        samples.append(_posterior_certainty(drawn))
    # Floor by the mean-member certainty: the LCB never exceeds the certainty of
    # the un-drawn posterior mean (draws add uncertainty, never confidence).
    return min(point_certainty, robust_quantile(samples, quantile))
