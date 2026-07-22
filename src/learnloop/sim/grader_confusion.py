"""Planted grader-confusion injection for the sim harness (spec §9.7.1, §4.2).

Orthogonal to the planted-*learner* machinery in ``profiles.py``: the learner's
true state is planted by the profile; the grader's asymmetric confusion is planted
here and corrupts the *observed* grade before it becomes a ``ResolvedGrade``. The
acceptance contract (§9.7.1) is that a planted confusion that would flip the
current *point-estimate* diagnosis instead produces, under the P0.3 robust path,
either an **invariant consequential action** or an **explicit abstention** -- never
a silent flip (``silent_flip_count == 0``).

Determinism: stdlib ``random.Random`` only (bit-for-bit replay, matching
``robust_composition``/``student``). With no ``GraderConfusion`` configured the sim
is byte-identical to today (the injection is a no-op).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from learnloop.services import robust_composition as rc

COARSE_CLASSES = ("success", "partial_success", "other")


@dataclass(frozen=True)
class GraderConfusion:
    """Asymmetric confusion over observed response classes given the TRUE class.

    ``confusion`` keys are ``"true->observed"`` with the probability of that
    misclassification, e.g. ``{"partial_success->success": 0.6}`` over-calls partial
    as success (the §9.1 asymmetric planted channel). Unspecified mass stays on the
    true class."""

    confusion: dict[str, float] = field(default_factory=dict)
    confidence_bias: float = 0.0
    seed: int = 0

    def observed_distribution(self, true_class: str) -> dict[str, float]:
        dist = {c: 0.0 for c in COARSE_CLASSES}
        leaked = 0.0
        for key, prob in self.confusion.items():
            src, _, dst = key.partition("->")
            if src == true_class and dst in dist:
                dist[dst] += prob
                leaked += prob
        dist[true_class] += max(0.0, 1.0 - leaked)
        total = sum(dist.values()) or 1.0
        return {c: v / total for c, v in dist.items()}

    def draw_observed(self, true_class: str, rng: random.Random) -> str:
        dist = self.observed_distribution(true_class)
        r = rng.random()
        cumulative = 0.0
        for cls in COARSE_CLASSES:
            cumulative += dist.get(cls, 0.0)
            if r <= cumulative:
                return cls
        return true_class


# Preset pairing: the "partial success overcalled as success" asymmetric channel
# (§9.1). Confusion lives on the run spec, not on the StudentProfile (grader is not
# the learner); pair it with the `intermediate_with_misconception` learner profile.
MISGRADED_PARTIAL_OVERCALL = GraderConfusion(
    confusion={"partial_success->success": 0.6, "other->partial_success": 0.3},
    seed=7,
)

BUILTIN_CONFUSIONS: dict[str, GraderConfusion] = {
    "misgraded_partial_overcall": MISGRADED_PARTIAL_OVERCALL,
}


def load_confusion(name: str) -> GraderConfusion:
    if name not in BUILTIN_CONFUSIONS:
        raise KeyError(f"unknown grader-confusion preset {name!r}; known: {sorted(BUILTIN_CONFUSIONS)}")
    return BUILTIN_CONFUSIONS[name]


def _true_coarse_class(rubric_score: float) -> str:
    """Map a fractional rubric score to the coarse true class."""

    if rubric_score >= 0.85:
        return "success"
    if rubric_score >= 0.35:
        return "partial_success"
    return "other"


def apply_confusion(
    *,
    true_criterion_points: Mapping[str, float],
    max_points_by_criterion: Mapping[str, float],
    grader_confidence: float,
    confusion: GraderConfusion,
    rng: random.Random,
) -> dict[str, object]:
    """Draw an observed coarse class per the asymmetric matrix and remap criterion
    points to that class, keeping the truth for scoring. Returns the confused
    ``criterion_points``, ``rubric_score``, ``grader_confidence``, and the observed
    vs true coarse classes."""

    total_max = sum(max_points_by_criterion.values()) or 1.0
    true_total = sum(true_criterion_points.values())
    true_frac = true_total / total_max
    true_class = _true_coarse_class(true_frac)
    observed_class = confusion.draw_observed(true_class, rng)

    if observed_class == true_class:
        confused_points = dict(true_criterion_points)
    else:
        target_frac = {"success": 1.0, "partial_success": 0.5, "other": 0.0}[observed_class]
        confused_points = {
            cid: round(max_points_by_criterion.get(cid, 0.0) * target_frac, 6)
            for cid in true_criterion_points
        }
    confused_conf = min(1.0, max(0.0, grader_confidence + confusion.confidence_bias))
    return {
        "criterion_points": confused_points,
        "rubric_score": sum(confused_points.values()),
        "grader_confidence": confused_conf,
        "true_class": true_class,
        "observed_class": observed_class,
        "confused": observed_class != true_class,
    }


# ---------------------------------------------------------------------------
# §9.7.1 acceptance: silent-flip invariance + abstention budget.
# ---------------------------------------------------------------------------

@dataclass
class PlantedMisgradeResult:
    trials: int
    point_flips: int              # trials where the point diagnosis flipped vs clean
    silent_flip_count: int        # point-flip + robust took a consequential action anyway
    abstained: int                # trials the robust path abstained
    invariant_actions: int        # trials the robust action matched the clean action
    abstention_rate: float

    def as_dict(self) -> dict[str, object]:
        return {
            "trials": self.trials,
            "point_flips": self.point_flips,
            "silent_flip_count": self.silent_flip_count,
            "abstained": self.abstained,
            "invariant_actions": self.invariant_actions,
            "abstention_rate": round(self.abstention_rate, 6),
        }


# A minimal diagnostic scenario: two hypotheses distinguished by an instrument
# card whose true-class rows differ. The clean (uncorrupted) grade identifies the
# hypothesis; the planted confusion corrupts the observed emission.
_HYPOTHESES = ("mastered", "has_misconception")


def _instrument_rows() -> dict[str, dict[str, float]]:
    # P(Z | H, card): a mastered learner mostly produces `success`; a learner with
    # the misconception mostly produces `partial_success` (the signature).
    return {
        "mastered": {"success": 0.85, "partial_success": 0.12, "other": 0.03},
        "has_misconception": {"success": 0.15, "partial_success": 0.70, "other": 0.15},
    }


def _heuristic_channel(prior_concentration: float) -> dict[str, dict[str, float]]:
    """The WIDE HEURISTIC calibration channel P(E | Z) the robust path actually
    uses. Crucially it does NOT know the planted overcall (U-014 weak priors): it
    admits real cross-talk, so an observed ``success`` is genuinely consistent with
    a truly-mastered learner AND a partial answer the grader over-called. Higher
    ``prior_concentration`` sharpens the Dirichlet (less ensemble disagreement, less
    abstention, more silent-flip risk); lower widens it (more abstention)."""

    def row(mass: Mapping[str, float]) -> dict[str, float]:
        return {f"{g}|high": prior_concentration * m for g, m in mass.items()}

    return {
        # success genuinely leaks from partial (the grader is imperfect) -> ambiguous.
        "success": row({"success": 0.70, "partial_success": 0.22, "other": 0.08}),
        "partial_success": row({"success": 0.33, "partial_success": 0.55, "other": 0.12}),
        "other": row({"success": 0.10, "partial_success": 0.25, "other": 0.65}),
    }


def _point_diagnosis(observed_class: str, rows: Mapping[str, Mapping[str, float]]) -> str:
    """The naive point-estimate diagnosis: treat the observed class as Z and pick
    the hypothesis whose instrument row makes it most likely."""

    best_h, best_p = None, -1.0
    for h, row in rows.items():
        p = row.get(observed_class, 0.0)
        if p > best_p:
            best_h, best_p = h, p
    return best_h or _HYPOTHESES[0]


def run_planted_misgrade_acceptance(
    *,
    confusion: GraderConfusion,
    prior_concentration: float = 2.0,
    trials: int = 200,
    seed: int = 20260718,
    agreement_threshold: float = rc.ENSEMBLE_ACTION_AGREEMENT_THRESHOLD,
) -> PlantedMisgradeResult:
    """Drive the planted-misgrade acceptance (§9.7.1). For each trial a true
    hypothesis produces a clean coarse class; the confusion corrupts it. We compare
    the point-estimate diagnosis (from the corrupted class) against the clean
    diagnosis, and the robust action (an ensemble ``observed_update`` + a >=90%
    agreement gate) against the clean action. A silent flip is a point-flip where
    the robust path nevertheless took a *different consequential action without
    abstaining*. The invariant is ``silent_flip_count == 0``."""

    rng = random.Random(seed)
    rows = _instrument_rows()
    joint_alpha = _heuristic_channel(prior_concentration)

    point_flips = 0
    silent_flips = 0
    abstained = 0
    invariant = 0

    for _ in range(trials):
        true_h = rng.choice(_HYPOTHESES)
        # Clean coarse class: draw from the instrument row (the honest grade).
        clean_class = _draw_from(rows[true_h], rng)
        observed_class = confusion.draw_observed(clean_class, rng)

        clean_diag = _point_diagnosis(clean_class, rows)
        point_diag = _point_diagnosis(observed_class, rows)
        point_flipped = point_diag != clean_diag
        if point_flipped:
            point_flips += 1

        # Robust action: build the deterministic ensemble and take an agreement
        # vote over per-member argmax of the posterior update at the observed E.
        prior = {h: 1.0 / len(_HYPOTHESES) for h in _HYPOTHESES}
        ctx = rc.decision_context_hash(
            episode_id=None,
            candidate_card_version="planted_misgrade",
            resolved_slot_map=None,
            posterior_at_selection=prior,
            projection_algorithm_version="mvp-0.8",
        )
        ensemble = rc.build_ensemble(
            joint_alpha=joint_alpha,
            instrument_rows=rows,
            calibration_model_hash=f"pm|{prior_concentration}",
            decision_context_hash=ctx,
        )
        emission = f"{observed_class}|high"
        member_actions: list[str] = []
        for member in ensemble.members:
            post = rc.observed_update(member, prior, emission)
            member_actions.append(max(post, key=post.get))
        winner = max(set(member_actions), key=member_actions.count)
        agreement = member_actions.count(winner) / len(member_actions)
        robust_abstains = agreement < agreement_threshold

        clean_action = clean_diag  # the honest consequential action
        if robust_abstains:
            abstained += 1
            continue
        if winner == clean_action:
            invariant += 1
            continue
        # The robust path acted, and differs from the clean action -> only a silent
        # flip if the point estimate ALSO flipped (i.e. the confusion drove it).
        if point_flipped:
            silent_flips += 1

    return PlantedMisgradeResult(
        trials=trials,
        point_flips=point_flips,
        silent_flip_count=silent_flips,
        abstained=abstained,
        invariant_actions=invariant,
        abstention_rate=abstained / trials if trials else 0.0,
    )


def _draw_from(dist: Mapping[str, float], rng: random.Random) -> str:
    r = rng.random()
    cumulative = 0.0
    items = sorted(dist.items())
    for cls, prob in items:
        cumulative += prob
        if r <= cumulative:
            return cls
    return items[-1][0]


def choose_prior_concentration_for_budget(
    *,
    confusion: GraderConfusion,
    budget_fraction: float,
    candidates: Sequence[float] = (1.0, 1.5, 2.0, 3.0, 5.0, 8.0),
    trials: int = 200,
    seed: int = 20260718,
) -> dict[str, object]:
    """The §4.2 abstention-budget loop: sweep prior concentration and choose the
    lowest (widest-interval) value whose abstention rate stays <= the budget while
    ``silent_flip_count`` stays 0. Over-budget across all candidates -> alarm."""

    clean = GraderConfusion(confusion={}, seed=confusion.seed)
    sweep: list[dict[str, object]] = []
    chosen: float | None = None
    for concentration in sorted(candidates):
        confused_result = run_planted_misgrade_acceptance(
            confusion=confusion, prior_concentration=concentration, trials=trials, seed=seed
        )
        # The budget is measured on the CLEAN (honest-grade) scenario (design §6.3);
        # silent-flip safety is measured on the confusion scenario.
        clean_result = run_planted_misgrade_acceptance(
            confusion=clean, prior_concentration=concentration, trials=trials, seed=seed
        )
        row = {
            "prior_concentration": concentration,
            "confusion_silent_flip_count": confused_result.silent_flip_count,
            "confusion_abstention_rate": round(confused_result.abstention_rate, 6),
            "clean_abstention_rate": round(clean_result.abstention_rate, 6),
        }
        sweep.append(row)
        if (
            confused_result.silent_flip_count == 0
            and clean_result.abstention_rate <= budget_fraction
            and chosen is None
        ):
            chosen = concentration
    return {
        "chosen_prior_concentration": chosen,
        "over_budget_alarm": chosen is None,
        "budget_fraction": budget_fraction,
        "sweep": sweep,
    }
