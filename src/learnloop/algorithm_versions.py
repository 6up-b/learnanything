"""Dependency-neutral algorithm-version vocabulary.

These names gate persistence formats as well as domain behavior, so their
authority cannot live in a service module without making the database layer
import upward.  Domain modules re-export them for compatibility.
"""

from __future__ import annotations

# Activation gate: the snapshot path only runs on vaults upgraded to the new
# knowledge model. Legacy vaults never compute or read snapshots.
KM_ALGORITHM_VERSION = "mvp-0.7"

# P0.3 (spec_p0_measurement_correctness §4.2/§4.3/§7.2): the
# authority-propagation projection namespace. mvp-0.8 reads the P0.1/P0.2
# authoritative event substrate and applies robust composition plus reliability
# discounting. mvp-0.7 remains the byte-identical compatibility projection.
P0_ALGORITHM_VERSION = "mvp-0.8"

# mvp-0.9 (migration 154): cross-channel reveal accounting. The version moves
# because exposed-answer attempts are now recorded as primed, but the projection
# is unchanged and uses the mvp-0.8 authority-propagation substrate.
REVEAL_LEDGER_ALGORITHM_VERSION = "mvp-0.9"

# mvp-0.10 (Slice 1 M2, spec_blind_grading_diagnosis_split_v1 §6.2): the live
# split between the learner-blind grader and the asynchronous history-aware
# diagnoser. Persisted meaning changes (a blind attempt's error events carry no
# causal fields; its hypotheses are sourced from the diagnosis ledger), the
# projection does not: it inherits the mvp-0.8 namespace like mvp-0.9.
# Owner decision 2026-10-12: a PF-c unverified criterion, which only the
# blind grader records (at every DIAGNOSIS_SPLIT_VERSIONS member: this version
# and its successors), is unassessed - out of the grade, and no facet evidence
# either way. It is gated by the record, never by an exact version. mvp-0.10
# history from before the rule exists
# (Slice 1 M2 live runs), so the boundary is per record, not per tag: each new
# unverified row and blind record names the interpretation it was written
# under, replay reads every record as it was written (a pre-rule record keeps
# its grader-sum grade and its M2 evidence), and a regrade rewrites a pre-rule
# record under the rule (canonical_projection.unassessed_evidence_row).
DIAGNOSIS_SPLIT_ALGORITHM_VERSION = "mvp-0.10"

# mvp-0.11 (Slice A Phase 6, learner field F2): starting new material without
# ceremony, on top of mvp-0.10's split (the version chain is linear: mvp-0.11
# means the mvp-0.10 semantics PLUS placement). No opening probe per new LO;
# new material starts as learning in prerequisite and predicted-difficulty
# order; "assumed known (not tested)" LOs wait for their first review. It
# changes what is SERVED, not the projection, so it is another successor tag on
# the mvp-0.8 namespace. Kill switch: ``placement.enabled``.
PLACEMENT_ALGORITHM_VERSION = "mvp-0.11"

# mvp-0.12 (router R1, spec_action_router_v1 §11): mvp-0.11's split and
# placement PLUS probe near-ties admitted to the Today queue's seeded epsilon
# tie-break, so probe decisions carry a true propensity instead of 1 or 0. It
# changes what is SERVED (which near-tie leads the offer), not the projection,
# so it is another successor tag on the mvp-0.8 namespace. Kill switch:
# ``router.probe_tie_admission``. The label is the next free one on R1's base;
# expect relabelling at landing (DL1 and T1 also claim mvp-0.12).
PROBE_TIE_ALGORITHM_VERSION = "mvp-0.12"

# Versions at which practice grading is split (kill switch
# ``diagnosis.split_enabled`` restores joint grading for NEW attempts; an
# attempt's grader mode is recorded per attempt and replay never reads the
# switch). Every later successor keeps the split, so gates must use this set,
# never equality against DIAGNOSIS_SPLIT_ALGORITHM_VERSION.
DIAGNOSIS_SPLIT_VERSIONS: frozenset[str] = frozenset(
    {DIAGNOSIS_SPLIT_ALGORITHM_VERSION, PLACEMENT_ALGORITHM_VERSION, PROBE_TIE_ALGORITHM_VERSION}
)

# Successors inherit mvp-0.8 projection semantics wholesale. Gates asking "is
# this the P0 projection?" must use this set rather than equality against
# P0_ALGORITHM_VERSION, or each version bump silently demotes fresh vaults.
P0_SUCCESSOR_VERSIONS: frozenset[str] = frozenset(
    {
        REVEAL_LEDGER_ALGORITHM_VERSION,
        DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
        PLACEMENT_ALGORITHM_VERSION,
        PROBE_TIE_ALGORITHM_VERSION,
    }
)
P0_PROJECTION_VERSIONS: frozenset[str] = (
    frozenset({P0_ALGORITHM_VERSION}) | P0_SUCCESSOR_VERSIONS
)

# mvp-0.7 and every P0-projection version read/write canonical shared-facet
# state. These guards prevent fallback to the retired per-learning-object
# compatibility tables.
CANONICAL_STATE_VERSIONS: frozenset[str] = (
    frozenset({KM_ALGORITHM_VERSION}) | P0_PROJECTION_VERSIONS
)

# Versions whose serving includes F2 placement (behind ``placement.enabled``).
# A later successor that keeps placement adds itself here; gates must use this
# set, never equality against PLACEMENT_ALGORITHM_VERSION.
PLACEMENT_VERSIONS: frozenset[str] = frozenset(
    {PLACEMENT_ALGORITHM_VERSION, PROBE_TIE_ALGORITHM_VERSION}
)

# Versions whose Today queue admits probe near-ties to the seeded epsilon
# tie-break (behind ``router.probe_tie_admission``). A later successor that
# keeps it adds itself here; gates must use this set.
PROBE_TIE_VERSIONS: frozenset[str] = frozenset({PROBE_TIE_ALGORITHM_VERSION})

# The newest successor in the linear chain
# mvp-0.9 -> mvp-0.10 -> mvp-0.11 -> mvp-0.12.
# ``learnloop upgrade`` with no ``--to`` targets it.
LATEST_ALGORITHM_VERSION: str = PROBE_TIE_ALGORITHM_VERSION
