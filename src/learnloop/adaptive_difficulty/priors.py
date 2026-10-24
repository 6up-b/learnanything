"""AD's a-priori, versioned constants (spec_adaptive_difficulty_v1 §5.5, §5.10; field F5, A5).

Nothing here is fitted or hand-set from data: every effect that weighs an
observation is latent state with the prior below (``ad_priors_v1``), and the
vault-level hyperparameters of sharing are a posterior over the a-priori grid
``ad_hyper_v1`` (§5.10). The few fixed measurement constants are versioned
here and swept by the harness (§10.4). The pre-registration of these values is
``docs/reviews/adaptive-difficulty-ad23.md`` §1.1.

The feature coding ``φ(x)`` (§5.4) is the cumulative dummy coding of a
``p1_launch@1`` tuple relative to the reference tuple ``x_ref`` (the default
trajectory's ``recall`` waypoint: complexity 0, same_context,
short_constructed, cue, atomic, closed_book), which has demand 0 and anchors
the location. ``representation`` and ``time`` are not modelled in v1.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

PRIORS_VERSION = "ad_priors_v1"
HYPER_VERSION = "ad_hyper_v1"
HYPER_FINE_VERSION = "ad_hyper_fine_v1"
FEATURE_SCHEMA = "p1_launch@1"

CAPABILITIES = ("retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination")

# -- fixed constants (§5.5, versioned, swept by the harness) ------------------------------

A = 1.0  # discrimination, fixed in v1
LAPSE = 0.02
KAPPA = 1.5  # the partial-credit threshold offset
TAU0 = 1.0  # item residual sd, integrated out, never estimated
SIGMA_LATENCY = 0.6
WARMTH_HOURS = 6.0
DRIFT_PER_DAY = 0.01
MAX_LOADINGS = 3
MAX_COUPLED = 3
DOSE_SCALES = (1.0, 4.0)  # h_1, h_2 (§5.11): a basis, not a shape
COLD_START_VARIANCE = 3.0
LO_VIEW_SPLIT = 1.5

#: §5.3's thresholds, shared with the certification cold probe and the ledger.
SUCCESS = 0.8
PARTIAL = 0.40

# -- the hyperparameter grid (§5.5, §5.10) ------------------------------------------------

SPLITS = (0.75, 1.5, 2.25)
COUPLINGS = (0.0, 0.25, 0.5, 0.75)
IMPLICATIONS = (0.0, 0.25, 0.5)


@dataclass(frozen=True)
class HyperPoint:
    split: float  # σ_G²
    coupling: float  # χ_C
    implication: float  # χ_Q

    @property
    def uniform(self) -> bool:
        return self.coupling == 0.0 and self.implication == 0.0

    def key(self) -> str:
        return f"{self.split:g}/{self.coupling:g}/{self.implication:g}"

    def as_dict(self) -> dict[str, float]:
        return {"split": self.split, "coupling": self.coupling, "implication": self.implication}


def hyper_grid(version: str = HYPER_VERSION) -> tuple[HyperPoint, ...]:
    """The grid in its fixed order (split, then coupling, then implication)."""

    if version == HYPER_VERSION:
        return tuple(HyperPoint(s, c, q) for s in SPLITS for c in COUPLINGS for q in IMPLICATIONS)
    if version == HYPER_FINE_VERSION:
        splits = (0.75, 1.125, 1.5, 1.875, 2.25)
        couplings = tuple(round(0.125 * i, 3) for i in range(7))
        implications = tuple(round(0.125 * i, 3) for i in range(5))
        return tuple(HyperPoint(s, c, q) for s in splits for c in couplings for q in implications)
    raise ValueError(f"unknown hyperparameter grid {version!r}")


def uniform_points(grid: Iterable[HyperPoint]) -> tuple[HyperPoint, ...]:
    return tuple(point for point in grid if point.uniform)


LO_VIEW_POINT = HyperPoint(LO_VIEW_SPLIT, 0.0, 0.0)


def offset_variance(split: float) -> float:
    """The facet and cell offsets' prior variance: the cold-start variance's remainder, halved."""

    return (COLD_START_VARIANCE - float(split)) / 2.0


# -- capability offsets ψ_{j,k} (§5.5) -----------------------------------------------------

PSI_PRIORS: Mapping[str, tuple[float, float]] = {
    "schema_interpretation": (-0.3, 0.25),
    "procedure_execution": (-0.5, 0.25),
    "method_selection": (-0.8, 0.25),
    "coordination": (-1.2, 0.25),
}

# -- shared coordinates: (name, mean, variance) in a fixed order ---------------------------

BETA_PRIORS: tuple[tuple[str, float, float], ...] = (
    ("beta:complexity:1", 0.5, 0.09),
    ("beta:complexity:2", 0.5, 0.09),
    ("beta:complexity:3", 0.5, 0.09),
    ("beta:complexity:4", 0.5, 0.09),
    ("beta:transfer:near", 0.5, 0.09),
    ("beta:transfer:far", 0.5, 0.09),
    ("beta:transfer:novel_combination", 0.5, 0.09),
    ("beta:scaffolding:none", 0.5, 0.09),
    ("beta:scaffolding:partial", -0.5, 0.09),
    ("beta:scaffolding:worked", -0.5, 0.09),
    ("beta:span:single_step", 0.4, 0.09),
    ("beta:span:multi_step", 0.4, 0.09),
    ("beta:span:whole_task", 0.4, 0.09),
    ("beta:response:recognize", -0.7, 0.16),
    ("beta:response:long_constructed", 0.3, 0.09),
    ("beta:response:structured_steps", 0.3, 0.09),
    ("beta:response:performance", 0.6, 0.16),
    ("beta:tools:open", -0.4, 0.09),
)
BETA_NAMES = tuple(name for name, _mean, _var in BETA_PRIORS)

#: Item-side signal weights (§7.3). ``z_v1`` only in the ``+outside`` arm (§10.4).
ALPHA_PRIORS: tuple[tuple[str, float, float], ...] = (
    ("alpha:z_llm", 0.2, 0.04),
    ("alpha:z_panel", 0.5, 0.09),
    ("alpha:z_origin", 0.0, 0.25),
)
ALPHA_V1_PRIOR = ("alpha:z_v1", 0.2, 0.04)
BASE_SIGNALS = ("z_llm", "z_panel", "z_origin")

GAMMA_PRIOR = ("gamma", 0.2, 0.01)
ZETA_PRIOR = ("zeta", 1.0, 0.25)

READING_KINDS = ("reading", "reader_tutor_exchange", "worked_example", "in_passage_question")
#: γ_read[κ, m] = γ̄_m + δ_{κ,m} (§5.11): a shared curve and a deviation per kind.
READING_PRIORS: tuple[tuple[str, float, float], ...] = (
    ("gbar:1", 0.10, 0.0049),
    ("gbar:2", 0.20, 0.01),
    *tuple((f"delta:{kind}:{m}", 0.0, 0.0049 if m == 1 else 0.01) for kind in READING_KINDS for m in (1, 2)),
)
VERDICT_PRIORS: tuple[tuple[str, float, float], ...] = (
    ("lam:matched", 0.0, 0.09),
    ("lam:missed", 0.0, 0.09),
)
VERDICT_CLASSES = {"self_check:matched": "lam:matched", "self_check:missed": "lam:missed"}

#: Sub-arms (§5.4), in unconstrained coordinates; present only when the arm is on.
RATING_PRIORS: tuple[tuple[str, float, float], ...] = (
    ("rating:rho_t", math.log(0.5), 0.25),
    ("rating:c1", -1.0, 0.25),
    ("rating:d_t", math.log(2.5), 0.09),
)
TIMING_PRIORS: tuple[tuple[str, float, float], ...] = (
    ("timing:nu", 0.0, 0.09),
    ("timing:omega_t", math.log(0.15), 0.36),
)
RATINGS = ("hard", "about_right", "easy")

# -- the feature coding φ(x) --------------------------------------------------------------

REFERENCE_TUPLE: Mapping[str, Any] = {
    "complexity": 0,
    "transfer": "same_context",
    "response": "short_constructed",
    "scaffolding": "cue",
    "span": "atomic",
    "tools": ["closed_book"],
}
TRANSFER_ORDER = ("same_context", "near", "far", "novel_combination")
SPAN_ORDER = ("atomic", "single_step", "multi_step", "whole_task")
SCAFFOLDING_VALUES = ("none", "cue", "partial", "worked")
RESPONSE_VALUES = ("recognize", "short_constructed", "long_constructed", "structured_steps", "performance")
MODELLED_DIMENSIONS = ("complexity", "transfer", "scaffolding", "span", "response", "tools")


def _complexity(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return min(max(number, 0), 4)


def _tools(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, (list, tuple, set, frozenset)):
        return {str(entry) for entry in value}
    return set()


def feature_coding(features: Mapping[str, Any] | None) -> dict[str, float]:
    """``φ(x)``: the β coordinates with coefficient 1 for this tuple (relative to ``x_ref``).

    A missing or unreadable dimension reads as the reference (demand 0 on it);
    callers record that the tuple was incomplete."""

    coding: dict[str, float] = {}
    if not features:
        return coding
    complexity = _complexity(features.get("complexity"))
    if complexity:
        for step in range(1, complexity + 1):
            coding[f"beta:complexity:{step}"] = 1.0
    transfer = features.get("transfer")
    if transfer in TRANSFER_ORDER:
        for value in TRANSFER_ORDER[1:TRANSFER_ORDER.index(transfer) + 1]:
            coding[f"beta:transfer:{value}"] = 1.0
    scaffolding = features.get("scaffolding")
    if scaffolding == "none":
        coding["beta:scaffolding:none"] = 1.0
    elif scaffolding == "partial":
        coding["beta:scaffolding:partial"] = 1.0
    elif scaffolding == "worked":
        coding["beta:scaffolding:partial"] = 1.0
        coding["beta:scaffolding:worked"] = 1.0
    span = features.get("span")
    if span in SPAN_ORDER:
        for value in SPAN_ORDER[1:SPAN_ORDER.index(span) + 1]:
            coding[f"beta:span:{value}"] = 1.0
    response = features.get("response")
    if response in RESPONSE_VALUES and response != "short_constructed":
        coding[f"beta:response:{response}"] = 1.0
    tools = _tools(features.get("tools"))
    if tools & {"open_book", "references"}:
        coding["beta:tools:open"] = 1.0
    return coding


def features_complete(features: Mapping[str, Any] | None) -> bool:
    if not features:
        return False
    return all(features.get(dimension) not in (None, "", []) for dimension in MODELLED_DIMENSIONS[:5])


def prior_demand(features: Mapping[str, Any] | None) -> float:
    """``β̄·φ(x)`` at the prior means (display and sims only; never certification, A11)."""

    means = {name: mean for name, mean, _var in BETA_PRIORS}
    return float(sum(means[name] * value for name, value in feature_coding(features).items()))


def versions() -> dict[str, str]:
    return {"priors": PRIORS_VERSION, "hyper": HYPER_VERSION, "feature_schema": FEATURE_SCHEMA}


__all__ = [
    "A",
    "ALPHA_PRIORS",
    "ALPHA_V1_PRIOR",
    "BASE_SIGNALS",
    "BETA_NAMES",
    "BETA_PRIORS",
    "CAPABILITIES",
    "COLD_START_VARIANCE",
    "DOSE_SCALES",
    "DRIFT_PER_DAY",
    "FEATURE_SCHEMA",
    "GAMMA_PRIOR",
    "HYPER_FINE_VERSION",
    "HYPER_VERSION",
    "HyperPoint",
    "KAPPA",
    "LAPSE",
    "LO_VIEW_POINT",
    "LO_VIEW_SPLIT",
    "MAX_COUPLED",
    "MAX_LOADINGS",
    "MODELLED_DIMENSIONS",
    "PARTIAL",
    "PRIORS_VERSION",
    "PSI_PRIORS",
    "RATINGS",
    "RATING_PRIORS",
    "READING_KINDS",
    "READING_PRIORS",
    "REFERENCE_TUPLE",
    "SIGMA_LATENCY",
    "SUCCESS",
    "TAU0",
    "TIMING_PRIORS",
    "VERDICT_CLASSES",
    "VERDICT_PRIORS",
    "WARMTH_HOURS",
    "ZETA_PRIOR",
    "feature_coding",
    "features_complete",
    "hyper_grid",
    "offset_variance",
    "prior_demand",
    "uniform_points",
    "versions",
]
