"""P4 step 4 -- same-facet dispersion as a FEASIBLE-SET constraint (spec §9.1).

Dispersion shapes the feasible set; it never ranks (invariant 1). Two fresh-evidence
administrations on the same target facet / capability / card lineage / hard group /
high soft-kinship cannot be back-to-back. A same-session lapse retry is exempt (it lives
inside its linked episode) but grants NO new independent evidence and does not itself
satisfy dispersion. When no candidate satisfies spacing the controller waits / switches
commitment / offers source work / stops -- it never trades the constraint against
priority (§9.1).

This module exports a pure predicate (:func:`same_facet_violation`) so the constraint
engine can wrap it into a typed ``ExclusionReason`` without an import cycle. The engine
owns the ``ExclusionReason`` type; dispersion owns the policy + its versioned params.

Gap/window parameters launch as REGISTERED HEURISTICS (design §E), not literals in
queue code -- generalizing ``scheduler._rotate_same_day_frontier_repeats`` while
preserving its lapse-retry exemption.

PRODUCTION DISPERSION REALITY (audit F6/L8): the ``last_fresh_evidence`` projection the
snapshot builds from the exposure ledger carries ONLY the near-kin dimensions the ledger
records -- ``surface_hash`` and ``fingerprint``. It does NOT carry ``facet_id`` /
``capability_id`` / ``card_lineage_id`` / ``hard_group_id`` / ``soft_kinship_group``. So
in production this constraint effectively disperses on FINGERPRINT (near-kin surface)
only; the finer dimensions in ``_DISPERSION_DIMENSIONS`` fire solely when a test PLANTS
those keys on ``snapshot.last_fresh_evidence``. The dimension list is kept whole because
the predicate is correct once the material exists.
TODO(U-facet-dispersion): populate the finer dimensions in
``controller_snapshot.build_snapshot`` by JOINING the last fresh administration's surface
to its facet/capability/lineage material (a facet-join off the administration -> surface
-> card-version path), then add them to the snapshot hash body. Do NOT synthesize them in
this predicate -- the material must come from real state so the decision still replays.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # duck-typed at runtime; no import cycle with the constraint engine
    from learnloop.services.controller_snapshot import Candidate, ControllerSnapshot
    from learnloop.services.staged_policy import AttentionBlock

# Structural policy version of the dispersion policy (enum, not a decision knob).
DISPERSION_POLICY_VERSION = 1

# Minimum number of intervening administrations required between two fresh-evidence
# administrations on the same facet/near-kin dimension. Heuristic decision parameter
# (design §E; an experiment variant, not a literal in queue code).
DISPERSION_MIN_INTERVENING_ADMINISTRATIONS = 1

# The dimensions (in priority order) on which two fresh-evidence administrations may
# not be back-to-back. Structural: the set of kinds, not a tunable weight.
_DISPERSION_DIMENSIONS: tuple[tuple[str, str], ...] = (
    ("facet_id", "facet_id"),
    ("capability_id", "capability_id"),
    ("card_lineage_id", "card_lineage_id"),
    ("hard_group_id", "hard_group_id"),
    ("soft_kinship_group", "soft_kinship_group"),
    ("fingerprint", "fingerprint"),
)

_FRESH_EVIDENCE_ACTIONS = frozenset({"measure_diagnostic", "assess_terminal"})


def same_facet_violation(
    candidate: "Candidate", snapshot: "ControllerSnapshot", block: "AttentionBlock | None"
) -> dict[str, Any] | None:
    """Return a violation descriptor (``reason``/``detail``/``kind``) when serving this
    candidate would be a back-to-back fresh-evidence administration on the same
    facet/near-kin as the immediately preceding one, else None.

    Only fresh-evidence blocks are dispersed; a lapse-retry candidate is exempt."""

    if block is None or block.action not in _FRESH_EVIDENCE_ACTIONS:
        return None
    last = getattr(snapshot, "last_fresh_evidence", None)
    if not last:
        return None
    # A same-session lapse retry inside its linked episode is exempt (§9.1) -- but it
    # grants no independent evidence, which the caller enforces separately.
    if getattr(candidate, "is_lapse_retry", False):
        return None
    intervening = int(last.get("intervening_administrations", 0))
    if intervening >= DISPERSION_MIN_INTERVENING_ADMINISTRATIONS:
        return None
    for cand_attr, last_key in _DISPERSION_DIMENSIONS:
        cv = getattr(candidate, cand_attr, None)
        lv = last.get(last_key)
        if cv is not None and lv is not None and cv == lv:
            return {
                "reason": "same_facet_back_to_back",
                "kind": "defer",  # wait/switch/rotate, never drop (§9.1)
                "detail": {
                    "dimension": cand_attr,
                    "value": cv,
                    "intervening_administrations": intervening,
                    "min_intervening": DISPERSION_MIN_INTERVENING_ADMINISTRATIONS,
                    "policy_version": DISPERSION_POLICY_VERSION,
                },
            }
    return None
