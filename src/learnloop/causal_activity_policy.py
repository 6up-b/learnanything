"""Dependency-neutral causal activity classification policy primitives.

The append-only classification ledger persists the outputs of this matrix, so
both the repository and higher-level causal services need one authority.  Keep
this module free of database, service, and vault imports; the service module
re-exports these names and composes them with attempt- and vault-level policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CAUSAL_ACTIVITY_POLICY_VERSION = "causal_activity_v1"

# Most-contaminated wins on conflicting writes. Index 0 is authoritative.
CONTAMINATION_PRECEDENCE: tuple[str, ...] = (
    "repair_activity",
    "instructional_diagnostic",
    "pure_diagnostic",
    "verification",
)
CONTAMINATION_CLASSES: frozenset[str] = frozenset(CONTAMINATION_PRECEDENCE)


@dataclass(frozen=True)
class CausalActivityPolicy:
    """Resolved persistence policy for one contamination class."""

    contamination_class: str
    near_clone: bool
    closes_pre_intervention_segment: bool
    eligible_for_fsrs: bool
    eligible_for_certification: bool
    counts_as_assisted: bool
    policy_version: str = CAUSAL_ACTIVITY_POLICY_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "contamination_class": self.contamination_class,
            "near_clone": self.near_clone,
            "closes_pre_intervention_segment": (
                self.closes_pre_intervention_segment
            ),
            "eligible_for_fsrs": self.eligible_for_fsrs,
            "eligible_for_certification": self.eligible_for_certification,
            "counts_as_assisted": self.counts_as_assisted,
            "policy_version": self.policy_version,
        }


def policy_for_class(
    contamination_class: str,
    *,
    near_clone: bool = False,
) -> CausalActivityPolicy:
    """Return the versioned matrix row for one contamination class."""

    if contamination_class not in CONTAMINATION_CLASSES:
        raise ValueError(f"unknown contamination class {contamination_class!r}")
    verification = contamination_class == "verification"
    return CausalActivityPolicy(
        contamination_class=contamination_class,
        near_clone=bool(near_clone),
        closes_pre_intervention_segment=(
            contamination_class == "instructional_diagnostic"
        ),
        # Diagnostic administrations and repair activities do not feed
        # retention scheduling, including pure diagnostics (the intentionally
        # strict policy documented by the service compatibility module).
        eligible_for_fsrs=verification,
        eligible_for_certification=verification and not near_clone,
        counts_as_assisted=contamination_class
        in {"instructional_diagnostic", "repair_activity"},
        policy_version=CAUSAL_ACTIVITY_POLICY_VERSION,
    )
