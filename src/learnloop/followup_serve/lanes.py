"""Which lane a miss takes (spec §4), read after its diagnosis.

**Probe:** the diagnosis leaves two or more current concrete rival causes in the selected
factor (``H_OTHER`` stays in the set and is not counted). **Practice:** the cause is known,
or one hypothesis, or no diagnosis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.db.repositories import Repository


@dataclass(frozen=True)
class LaneChoice:
    lane: str
    reason: str
    factor_id: str | None = None
    hypothesis_ids: tuple[str, ...] = field(default_factory=tuple)


def concrete_rivals(repository: Repository, factor: dict[str, Any]) -> tuple[str, ...]:
    """The factor's concrete cause hypotheses that still exist, in its own order."""

    from learnloop.diagnosis.causal_attribution import OPEN_SET_CAUSE_ID

    out: list[str] = []
    for value in factor.get("candidate_causes") or []:
        if not isinstance(value, dict) or value.get("open_set"):
            continue
        hypothesis_id = value.get("hypothesis_id")
        if not hypothesis_id or hypothesis_id == OPEN_SET_CAUSE_ID:
            continue
        if repository.causal_hypothesis(str(hypothesis_id)) is not None:
            out.append(str(hypothesis_id))
    return tuple(dict.fromkeys(out))


def select_lane(repository: Repository, workflow: dict[str, Any]) -> LaneChoice:
    """The probe lane needs an open factor with two rivals; anything else is practice."""

    factors = repository.unresolved_cause_factors_for_attempt(str(workflow["source_attempt_id"]))
    best: LaneChoice | None = None
    for factor in factors:
        rivals = concrete_rivals(repository, factor)
        if len(rivals) >= 2:
            return LaneChoice("probe", "rival_causes", str(factor["id"]), rivals)
        if best is None and rivals:
            best = LaneChoice("practice", "one_hypothesis", str(factor["id"]), rivals)
    return best or LaneChoice("practice", "no_open_factor" if factors == [] else "no_concrete_cause")


__all__ = ["LaneChoice", "concrete_rivals", "select_lane"]
