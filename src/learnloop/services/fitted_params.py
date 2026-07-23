"""Resolution of fitted parameter sets (architecture_pivot.md Stage 1).

Consumers resolve the active fitted set per operation — no in-process caching,
so the long-running sidecar never serves stale parameters and replay is
deterministic-by-construction (it uses whatever set is active at replay time,
auditable via the fitted_parameters history rows).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.fsrs import FSRS6_DEFAULT_WEIGHTS

FSRS_WEIGHTS_SCOPE = "fsrs_weights"
FOLLOWUP_GATE_SCOPE = "followup_gate"
GRADER_CHANNEL_SCOPE = "grader_channel_prior"

# Heuristic grade-channel prior policy knobs (measurement-correctness P4).
# ``reliability`` is the floor for the seeded symmetric-confusion identity share;
# ``lcb_quantile`` is the percentile of the calibration Dirichlet ensemble the
# shared certainty LCB reads. Both are decision parameters, not truths — a
# fitted set (scope ``grader_channel_prior``) overrides them once `learnloop fit`
# owns the channel.
GRADER_CHANNEL_RELIABILITY_FLOOR_DEFAULT = 0.92
CERTAINTY_LCB_QUANTILE_DEFAULT = 0.25


@dataclass(frozen=True)
class GraderChannelPrior:
    reliability_floor: float
    lcb_quantile: float


def resolve_grader_channel_prior(repository: Repository) -> GraderChannelPrior:
    """Active fitted grader-channel prior knobs, else the pinned defaults.

    Hard-validates the payload (reliability_floor in [0.5, 0.999], lcb_quantile
    in (0, 0.5]); a malformed fitted row falls back to defaults rather than
    crashing the grading path.
    """

    defaults = GraderChannelPrior(
        reliability_floor=GRADER_CHANNEL_RELIABILITY_FLOOR_DEFAULT,
        lcb_quantile=CERTAINTY_LCB_QUANTILE_DEFAULT,
    )
    record = repository.active_fitted_parameters(GRADER_CHANNEL_SCOPE)
    if record is None:
        return defaults
    params = record.get("params", {})
    reliability = _validated_float(
        params.get("reliability_floor"), low=0.5, high=0.999
    )
    quantile = _validated_float(params.get("lcb_quantile"), low=0.0, high=0.5)
    return GraderChannelPrior(
        reliability_floor=(
            reliability if reliability is not None else defaults.reliability_floor
        ),
        lcb_quantile=quantile if quantile is not None else defaults.lcb_quantile,
    )


def _validated_float(raw: Any, *, low: float, high: float) -> float | None:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    if not math.isfinite(value) or not (low < value <= high):
        return None
    return value


def resolve_fsrs_weights(repository: Repository) -> tuple[float, ...]:
    """Active fitted FSRS weights, else the pinned FSRS-6 defaults.

    Hard-validates the payload (21 finite floats); any malformed fitted row
    falls back to defaults rather than crashing the attempt path.
    """

    record = repository.active_fitted_parameters(FSRS_WEIGHTS_SCOPE)
    if record is None:
        return FSRS6_DEFAULT_WEIGHTS
    weights = _validated_weights(record.get("params", {}))
    if weights is None:
        return FSRS6_DEFAULT_WEIGHTS
    return weights


def fitted_fsrs_provenance(repository: Repository) -> str | None:
    """Fitted-set id when fitted weights are active and valid, else None."""

    record = repository.active_fitted_parameters(FSRS_WEIGHTS_SCOPE)
    if record is None or _validated_weights(record.get("params", {})) is None:
        return None
    return record["id"]


def _validated_weights(params: dict[str, Any]) -> tuple[float, ...] | None:
    raw = params.get("weights")
    if not isinstance(raw, (list, tuple)) or len(raw) != len(FSRS6_DEFAULT_WEIGHTS):
        return None
    values: list[float] = []
    for entry in raw:
        if isinstance(entry, bool) or not isinstance(entry, (int, float)) or not math.isfinite(entry):
            return None
        values.append(float(entry))
    return tuple(values)
