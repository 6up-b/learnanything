"""Dependency-neutral causal activity classification policy primitives.

The append-only classification ledger persists the outputs of this matrix, so
both the repository and higher-level causal services need one authority.  Keep
this module free of database, service, and vault imports; the service module
re-exports these names and composes them with attempt- and vault-level policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Classification outcomes that carry discriminating information at all.  The
#: other four (`matched_multiple`, `all_bundles_matched`, `cohort_mismatch`,
#: `unparsed_features`) are recorded and resolve nothing.  Here so that a reader
#: below the causal services (the capture report) shares the one contract.
DISCRIMINATING_OUTCOMES = frozenset({"matched_single", "no_bundle_matched"})

CAUSAL_ACTIVITY_POLICY_VERSION = "causal_activity_v1"

# Most-contaminated wins on conflicting writes. Index 0 is authoritative.
CONTAMINATION_PRECEDENCE: tuple[str, ...] = (
    "repair_activity",
    "instructional_diagnostic",
    "pure_diagnostic",
    "verification",
)
CONTAMINATION_CLASSES: frozenset[str] = frozenset(CONTAMINATION_PRECEDENCE)

#: Teacher TE2 (spec_teacher_v1 rev 5 §11.3): a lesson probe's classification ``source``. Its answer has no probe
#: presentation, so the attempts path records its class itself: a pure diagnostic, or an instructional one when the
#: lesson had shown text on its topic first (the reveal ledger's topic-wide check). The exposed source is also how
#: ``learner.lesson_weight.qualifying_outcomes`` leaves such an answer out of the cold outcomes (§12.1).
LESSON_PROBE_EVIDENCE_ORIGIN = "lesson_probe"
LESSON_PROBE_SOURCE = "lesson_probe"
LESSON_PROBE_EXPOSED_SOURCE = "lesson_probe_exposed"


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
