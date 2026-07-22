"""P4 step 4 -- stage-aware interleaving as a FEASIBLE-SET constraint (spec §9.2).

Interleaving is stage-aware block-composition shaping, never a reward coefficient
(invariant 1). The block planner picks a coherent neighborhood; the within-block policy
varies tasks only at the stage where discrimination/transfer is the objective:

- initial worked-example ACQUISITION: blocked/coherent within one target neighborhood
  (a candidate from a different neighborhood is excluded -- acquisition does not mix);
- faded completion/REPAIR: coherent until the relevant component is stable (treated
  coherent here, the conservative default);
- DISCRIMINATION / method_selection / TRANSFER: interleaving confusable/related task
  families is the objective -- never excluded for interleaving;
- MAINTENANCE: mixes commitments subject to block coherence + due pressure (permissive);
- terminal ASSESSMENT: follows the FROZEN target distribution, not a pedagogic
  interleaving heuristic (a candidate outside the frozen target distribution is
  excluded).

Exported as a pure predicate (:func:`stage_violation`) so the constraint engine wraps
it into a typed ``ExclusionReason`` without an import cycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # duck-typed at runtime; no import cycle with the constraint engine
    from learnloop.services.controller_snapshot import Candidate, ControllerSnapshot
    from learnloop.services.staged_policy import AttentionBlock

# Structural policy version of the interleaving policy (enum, not a decision knob).
INTERLEAVING_POLICY_VERSION = 1

# Stages that keep a coherent (non-interleaved) neighborhood.
_COHERENT_STAGES = frozenset({"acquisition", "faded_repair"})
# Stages whose OBJECTIVE is interleaving confusable families (never excluded for it).
_INTERLEAVE_STAGES = frozenset({"discrimination", "method_selection", "transfer"})


def _block_neighborhood(block: "AttentionBlock") -> str | None:
    nb = getattr(block, "neighborhood", None) or {}
    return nb.get("neighborhood_id") or block.commitment_id


def stage_violation(
    candidate: "Candidate", snapshot: "ControllerSnapshot", block: "AttentionBlock | None"
) -> dict[str, Any] | None:
    """Return a stage-interleaving violation descriptor, or None. Feasible-set shaping
    only: it never reorders, it only excludes candidates the stage forbids."""

    if block is None:
        return None
    stage = getattr(block, "stage", None)
    if stage is None:
        return None

    if stage in _COHERENT_STAGES:
        cand_nb = getattr(candidate, "neighborhood_id", None)
        block_nb = _block_neighborhood(block)
        if cand_nb is not None and block_nb is not None and cand_nb != block_nb:
            return {
                "reason": "acquisition_coherence_required",
                "kind": "exclude",
                "detail": {
                    "stage": stage,
                    "candidate_neighborhood": cand_nb,
                    "block_neighborhood": block_nb,
                    "policy_version": INTERLEAVING_POLICY_VERSION,
                },
            }
        return None

    if stage == "assessment":
        # Terminal assessment follows the FROZEN target distribution (§9.2).
        if not getattr(candidate, "in_frozen_target", True):
            return {
                "reason": "outside_frozen_assessment_distribution",
                "kind": "exclude",
                "detail": {"stage": stage, "policy_version": INTERLEAVING_POLICY_VERSION},
            }
        return None

    # Discrimination / method_selection / transfer / maintenance: interleaving is the
    # objective (or permissive) -- never excluded for interleaving here.
    return None
