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
DIAGNOSIS_SPLIT_ALGORITHM_VERSION = "mvp-0.10"

# mvp-0.11 (Slice 2 T1 / M3, spec_embedding_consumers_v1 §3.4): recurrence
# with authority. Holding-pen promotion and the K=3 escalation count group
# hypotheses by recurrence group (exact statement classes joined by validated
# diagnoser citations and ``same_cause`` verdicts) instead of by exact
# statement, and a group's K-th recurrence shows its escalated repair with
# the earlier answers as evidence. The spec's "mvp-0.11" was a placeholder; it
# is the next free label after mvp-0.10. Kill switch: ``recurrence.enabled``
# (off: exact-statement keys again from the next normalization or rebuild).
# It keeps the split and the mvp-0.8 projection namespace.
RECURRENCE_GROUP_ALGORITHM_VERSION = "mvp-0.11"

# Versions at which practice grading is split (kill switch
# ``diagnosis.split_enabled`` restores joint grading for NEW attempts; an
# attempt's grader mode is recorded per attempt and replay never reads the
# switch). A later successor that keeps the split adds itself here.
DIAGNOSIS_SPLIT_VERSIONS: frozenset[str] = frozenset(
    {DIAGNOSIS_SPLIT_ALGORITHM_VERSION, RECURRENCE_GROUP_ALGORITHM_VERSION}
)

# Versions whose grouping sites read the recurrence-group map (behind
# ``recurrence.enabled``). Gates must use this set, never equality.
RECURRENCE_GROUP_VERSIONS: frozenset[str] = frozenset(
    {RECURRENCE_GROUP_ALGORITHM_VERSION}
)

# Successors inherit mvp-0.8 projection semantics wholesale. Gates asking "is
# this the P0 projection?" must use this set rather than equality against
# P0_ALGORITHM_VERSION, or each version bump silently demotes fresh vaults.
P0_SUCCESSOR_VERSIONS: frozenset[str] = frozenset(
    {
        REVEAL_LEDGER_ALGORITHM_VERSION,
        DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
        RECURRENCE_GROUP_ALGORITHM_VERSION,
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
