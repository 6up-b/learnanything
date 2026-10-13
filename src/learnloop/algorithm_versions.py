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
# Amended in place hours after it merged, before any vault this repository
# tracks ran it (owner decisions 2026-10-12, as the PF-c fix amended mvp-0.10;
# a recorded exception, see docs/algorithm-change-playbook.md): the first-review
# check and lapses in maintenance are decided by the diagnosis, once per miss
# (only a positive non-gap reading keeps the LO; the decision waits at most
# seven days for the diagnosis; today's rule when none can arrive), and
# unanswered opening episodes from earlier versions are ignored for serving,
# feedback and instrument generation until a door adopts one (never rewritten
# otherwise, so the kill switch stays exact). No projection or default change;
# new vaults started here until mvp-0.12 merged.
PLACEMENT_ALGORITHM_VERSION = "mvp-0.11"

# mvp-0.12 (Slice 2 T1 / M3, spec_embedding_consumers_v1 §3.4): recurrence
# with authority, on top of mvp-0.11 (the chain stays linear: mvp-0.12 means
# the split PLUS placement PLUS recurrence groups). Holding-pen promotion and
# the K=3 escalation count group hypotheses by recurrence group (exact
# statement classes joined by validated diagnoser citations and
# ``same_cause`` verdicts) instead of by exact statement, and a group's K-th
# recurrence shows its escalated repair with the earlier answers as evidence.
# The spec's "mvp-0.11" was a placeholder; T1 was built as mvp-0.11 and
# relabelled mvp-0.12 when it merged after Phase 6 took mvp-0.11. Kill switch:
# ``recurrence.enabled`` (off: exact-statement keys again from the next
# normalization, vault open or rebuild). It keeps the split, placement and the
# mvp-0.8 projection namespace. New vaults started here until mvp-0.13 merged.
RECURRENCE_GROUP_ALGORITHM_VERSION = "mvp-0.12"

# mvp-0.13 ("Write what you can" replaces "I don't know"), on top of mvp-0.12
# (the chain stays linear: mvp-0.13 means the split PLUS placement PLUS
# recurrence groups PLUS the stuck prompt): the learner's "I'm stuck" control.
# A stuck answer with text is an ordinary attempt at the standard attempt mass,
# graded (under the blind grader's ``+stuck-v1`` prompt) and diagnosed; an
# empty one is a deterministic zero with no model call and, by owner
# decision 2026-10-12, no error tag (it says nothing about understanding
# beyond "could not write anything"). Persisted meaning changes for NEW
# attempts only (``practice_attempts.declared_stuck``, the
# grader's stuck reading on the blind record and in judgment_ledger, the
# ``answer_display`` reveal kind);
# historical ``dont_know`` rows keep their meaning, and the projection
# namespace is unchanged. The branch built it as mvp-0.11 and it was relabelled
# mvp-0.13 when it merged after placement (mvp-0.11) and recurrence groups
# (mvp-0.12). Kill switch: ``stuck_prompt.enabled``.
STUCK_PROMPT_ALGORITHM_VERSION = "mvp-0.13"

# The linear successor chain on the mvp-0.8 projection namespace, oldest
# first. Each successor means its predecessor's semantics PLUS its own, so
# every gate below is "this tag or any later one". A successor merge appends
# its tag here (one line; and records its defaults snapshot,
# ``config.template.DEFAULTS_SNAPSHOT_BY_ALGORITHM``): LATEST_ALGORITHM_VERSION
# and every version set follow, so a new vault at the new tag keeps the split
# and placement.
SUCCESSOR_CHAIN: tuple[str, ...] = (
    REVEAL_LEDGER_ALGORITHM_VERSION,
    DIAGNOSIS_SPLIT_ALGORITHM_VERSION,
    PLACEMENT_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    STUCK_PROMPT_ALGORITHM_VERSION,
)


def successors_from(version: str) -> frozenset[str]:
    """``version`` and every later tag in :data:`SUCCESSOR_CHAIN`."""

    return frozenset(SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(version):])


# Versions at which practice grading is split (kill switch
# ``diagnosis.split_enabled`` restores joint grading for NEW attempts; an
# attempt's grader mode is recorded per attempt and replay never reads the
# switch). Every later successor keeps the split, so gates must use this set,
# never equality against DIAGNOSIS_SPLIT_ALGORITHM_VERSION.
DIAGNOSIS_SPLIT_VERSIONS: frozenset[str] = successors_from(DIAGNOSIS_SPLIT_ALGORITHM_VERSION)

# Versions whose grouping sites read the recurrence-group map (behind
# ``recurrence.enabled``). Every later successor keeps recurrence groups;
# gates must use this set, never equality.
RECURRENCE_GROUP_VERSIONS: frozenset[str] = successors_from(RECURRENCE_GROUP_ALGORITHM_VERSION)

# Versions whose learner surfaces offer "I'm stuck" instead of "I don't know"
# (the kill switch restores the old control and scoring for NEW answers;
# replay reads the persisted flag, never the switch). Every later successor
# keeps the stuck prompt; gates must use this set, never equality.
STUCK_PROMPT_VERSIONS: frozenset[str] = successors_from(STUCK_PROMPT_ALGORITHM_VERSION)

# Successors inherit mvp-0.8 projection semantics wholesale. Gates asking "is
# this the P0 projection?" must use this set rather than equality against
# P0_ALGORITHM_VERSION, or each version bump silently demotes fresh vaults.
P0_SUCCESSOR_VERSIONS: frozenset[str] = frozenset(SUCCESSOR_CHAIN)
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
# Every later successor keeps placement; gates must use this set, never
# equality against PLACEMENT_ALGORITHM_VERSION.
PLACEMENT_VERSIONS: frozenset[str] = successors_from(PLACEMENT_ALGORITHM_VERSION)

# The newest successor: the last tag in the chain. ``learnloop upgrade`` with
# no ``--to`` targets it, and new vaults start at it
# (``config.template.default_config_text``; owner decision 2026-10-12).
LATEST_ALGORITHM_VERSION: str = SUCCESSOR_CHAIN[-1]
