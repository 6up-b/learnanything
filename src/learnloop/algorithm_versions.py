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
# (mvp-0.12). Kill switch: ``stuck_prompt.enabled``. New vaults started here
# until mvp-0.14 merged.
STUCK_PROMPT_ALGORITHM_VERSION = "mvp-0.13"

# mvp-0.14 (daily-loop DL1, ``daily_plan_v1`` in spec_daily_loop_v1.md §11): the
# finite daily plan on top of mvp-0.13 (the chain stays linear: mvp-0.14 means
# the mvp-0.10 split PLUS placement PLUS recurrence groups PLUS the stuck
# prompt PLUS the plan). Today serves N remembered minutes split across
# repair, maintain, new and push, chosen block by block, with goal-optional
# re-entry and reading blocks. It changes what is SERVED, not the projection,
# so it is another successor tag on the mvp-0.8 namespace. The branch built it
# as mvp-0.12 and it was relabelled mvp-0.14 when it merged after recurrence
# groups (mvp-0.12) and the stuck prompt (mvp-0.13). Kill switch:
# ``plan.enabled`` (sub-switches ``plan.new_admission_enabled`` and
# ``plan.reading_blocks``); off, Today is mvp-0.13's. New vaults started here
# until mvp-0.15 merged.
DAILY_PLAN_ALGORITHM_VERSION = "mvp-0.14"

# mvp-0.15 (router R1, spec_action_router_v1 §11): mvp-0.14 PLUS probe
# near-ties admitted to the Today queue's seeded exploration (the chain stays
# linear: mvp-0.15 means the split PLUS placement PLUS recurrence groups PLUS
# the stuck prompt PLUS the plan PLUS probe ties), so probe decisions carry a
# true propensity instead of 1 or 0. PROBE intent includes teach-back items
# (owner decision D11, 2026-10-12: a teach-back dialogue is a high-value
# probe). It changes what is SERVED (which near-tie leads the offer), not the
# projection, so it is another successor tag on the mvp-0.8 namespace. The
# branch built it as mvp-0.12 and it was relabelled mvp-0.15 when it merged
# after the daily plan (mvp-0.14). Kill switch: ``router.probe_tie_admission``.
# Decision logging (``router.log_decisions``) is not a serving change and runs
# at every version. New vaults started here until mvp-0.16 merged.
PROBE_TIE_ALGORITHM_VERSION = "mvp-0.15"

# mvp-0.16 (learner-text gaps, implementation_handoffs §4, owner-directed
# 2026-10-12): on top of mvp-0.15 (the chain stays linear: mvp-0.16 means the
# split PLUS placement PLUS recurrence groups PLUS the stuck prompt PLUS the
# plan PLUS probe ties PLUS this). A prerequisite gap a learner's own text
# names (a tutor question, a stuck answer, a diagnosis) and that matches an LO
# assumed known or in maintenance brings that LO's next check forward, no
# sooner than a bound after the gap and never later than it was
# (``learner_gap_check_advances`` receipts; placement reads them only at this
# tag or later). It changes what is SERVED, not the projection, so it is
# another successor tag on the mvp-0.8 namespace. The branch built it as
# mvp-0.13 and it was relabelled mvp-0.16 when it merged after the stuck
# prompt (mvp-0.13), the daily plan (mvp-0.14) and probe ties (mvp-0.15). Kill
# switch: ``learner_text_gaps.sooner_check_enabled``. The rest of the pipeline
# (names, matches, edges, created prerequisites, holding-pen sightings) is a
# live change behind its own switches, not version-gated. New vaults started
# here until mvp-0.17 merged.
LEARNER_TEXT_GAP_ALGORITHM_VERSION = "mvp-0.16"

# mvp-0.17 (the valid-alternative gate extended to proofs and explanations,
# ITS research sweep 2026-10-13), on top of mvp-0.16 (the chain stays linear:
# mvp-0.17 means the mvp-0.10 split PLUS placement PLUS recurrence groups PLUS
# the stuck prompt PLUS the plan PLUS probe ties PLUS learner-text gaps PLUS
# the route check). On an item an LLM reads as proof-like (cached per item
# content in judgment_ledger), each new blind grade is followed by one
# independent re-derivation of the learner's own route on a route that is not
# the grader's model where one is configured; the deterministic gate restores a
# criterion the grader marked down without locating an error when the check
# validates the route, records one it disputes on a located step unverified
# (PF-c's unassessed type; a clarification only when the dispute turns on what
# the learner meant), and flags a step the grader accepted that the check
# refutes with a verbatim quote. A grade left with nothing assessed and
# nothing validated is held for review: the grader's own grade, no evidence,
# no FSRS review until a regrade or an adjudication settles it. Persisted
# meaning changes for NEW grades only (the blind record's
# grading_support.proof_route_check, the restored points, the route-check
# verdict in judgment_ledger, migration 186's clarification trigger); replay
# reads every record as written and the projection namespace is unchanged. The
# branch built it as mvp-0.15 (a placeholder) and it was relabelled mvp-0.17
# when it merged after probe ties (mvp-0.15) and learner-text gaps (mvp-0.16).
# Kill switch: ``proof_check.enabled``. New vaults started here until mvp-0.18
# merged.
# Owner decision 2026-10-13 (route-check-in-grader): the separate check was
# removed from serving. Its own kill switch defined "mvp-0.17 without the
# check" (``proof_check.enabled = false`` grades new answers as mvp-0.16), so
# an mvp-0.17 vault now grades new answers in that state, whatever the
# switch says. Records written by the check (blind records, ledger rows,
# calibration identities, holds) keep their meaning and replay exactly: replay
# reads the records, never the check. The protective core moved into the
# grader's prompt as mvp-0.20. mvp-0.18 and mvp-0.19 inherit the same state:
# their new answers grade without the check too.
PROOF_ROUTE_CHECK_ALGORITHM_VERSION = "mvp-0.17"

# mvp-0.18 (canonical sources S1, spec_source_practice_and_probes_v1 §7.3a):
# certification follows the answer key, on top of mvp-0.17 (the chain stays
# linear: mvp-0.18 means the mvp-0.10 split PLUS placement PLUS recurrence
# groups PLUS the stuck prompt PLUS the plan PLUS probe ties PLUS learner-text
# gaps PLUS the route check PLUS this). An attempt on an imported textbook
# exercise records ``practice_attempts.reference_status`` from the served
# item's effective key status (the latest check of its CURRENT prompt, key and
# rubric), and an ``unverified`` attempt schedules and teaches but earns no
# certification credit (owner decision C3: an unverified solution never
# certifies anything). DL3's attempt-time gate (spec_daily_loop_v1 §4.4), built
# here first. Never retroactive: attempts before the tag keep
# ``not_applicable`` and replay reads the stored column, so a shadow rebuild
# shows zero deltas. No kill switch re-enables certification; vaults below the
# tag never run the gate. The branch built it as mvp-0.15 (a placeholder) and
# it was relabelled mvp-0.18 when it merged after probe ties (mvp-0.15),
# learner-text gaps (mvp-0.16) and the route check (mvp-0.17).
SOURCE_REFERENCE_GATE_ALGORITHM_VERSION = "mvp-0.18"

# mvp-0.19 (canonical sources S2b, §8.5): intervention needs are fulfilled from
# the learner's sources before generating, on top of mvp-0.18. It changes which
# item a follow-up serves (a verified, validated textbook exercise that passes
# the follow-up chooser's own gate). Kill switch
# ``source_service.source_first_needs``: off, the generation lane is
# byte-identical. The branch built it as mvp-0.16 (a placeholder) and it was
# relabelled mvp-0.19 at the same merge.
SOURCE_FIRST_NEEDS_ALGORITHM_VERSION = "mvp-0.19"

# mvp-0.20 (route rules in the grader, owner decision 2026-10-13), on top of
# mvp-0.19 (the chain stays linear: the split PLUS placement PLUS recurrence
# groups PLUS the stuck prompt PLUS the plan PLUS probe ties PLUS learner-text
# gaps PLUS the route check PLUS the answer-key gate PLUS source-first needs
# PLUS this). The blind grader's prompt grades every criterion on the
# learner's own route (a criterion phrased in
# one method is met by any valid method that establishes the same fact; mark
# down only by quoting the failing step verbatim; say so rather than mark
# down a route it cannot verify), and one deterministic server-side rule reads
# only the grader's output: a mark-down on a route the grader reads as
# divergent, with no verbatim quote that occurs in the answer, is unverified,
# so unassessed (P1); with nothing then assessed and nothing validated the
# grade is held for review (the held-grade predicate). One grading call;
# no item reading, no second model. Persisted meaning changes for NEW grades
# only (the blind record's ``grading_support.proof_route_check``, the
# ``+own-route-v1`` prompt and calibration identity); the projection
# namespace is unchanged. Kill switch: ``proof_check.enabled`` (off: new
# answers grade as mvp-0.19 now does, whose grading is mvp-0.16's). The
# branch built it as mvp-0.18 (a placeholder) and it was relabelled mvp-0.20
# when it merged after the sources track (mvp-0.18, mvp-0.19).
ROUTE_RULES_ALGORITHM_VERSION = "mvp-0.20"

# mvp-0.21 (value-of-information stopping, owner-directed 2026-10-12/13), on
# top of mvp-0.20 (the chain stays linear: mvp-0.21 means the split PLUS
# placement PLUS recurrence groups PLUS the stuck prompt PLUS the plan PLUS
# probe ties PLUS learner-text gaps PLUS the route check PLUS the answer-key
# gate PLUS source-first needs PLUS the route rules PLUS this). Two parts, one
# successor: Part 1 lifts four count caps onto value of information (a probe
# episode keeps asking, a further follow-up is queued, a teach-back is offered
# and a due project probe enters the plan while the next observation's value
# pays for its minutes; an episode whose next observation no longer pays ends
# with completion_reason 'value_of_information_stop', migration 200;
# diagnosis.voi_stopping), kill switch ``voi_stopping.enabled`` (per-site
# sub-switches); Part 2 makes the probe hypothesis lane read the diagnoser's
# verdict through the diagnosis overlay under split grading and leave out an
# event whose diagnosis is pending, kill switch
# ``diagnosis.probe_lane_reads_diagnosis``. Both change what is SERVED, not
# the projection, so it is another successor tag on the mvp-0.8 namespace.
# The branch built it as mvp-0.17 (a placeholder, migrations 187/188) and it
# was relabelled mvp-0.21 (migrations 200/201) when it merged after the route
# rules (mvp-0.20).
VOI_STOPPING_ALGORITHM_VERSION = "mvp-0.21"

# mvp-0.22 (Tier 1, the Decider migration, owner decision 2026-10-13), on top
# of mvp-0.21 (the chain stays linear: mvp-0.22 means everything mvp-0.21
# means PLUS this): the Decider, a fast typed decision model, decides the
# small judgments ``[decider_routes]`` names (learner-text gap pairs,
# "needed?" and kind; misconception matching; the review's pattern links;
# question classification; contamination leak and reveal verdicts). Each
# judgment's LLM is its fallback when the Decider is unavailable, refused for
# spend, failing or tied, and each has its own kill switch (false: that
# judgment's mvp-0.21 path). It changes what is served from now on (gaps
# created, misconceptions matched, links); recorded history keeps its meaning
# and a shadow rebuild shows zero deltas. ``learnloop.decider_judgments``.
# The branch built it as mvp-0.20 (a placeholder) and it was relabelled
# mvp-0.22 when it merged after the route rules (mvp-0.20) and
# value-of-information stopping (mvp-0.21).
DECIDER_TIER1_ALGORITHM_VERSION = "mvp-0.22"

# mvp-0.23 (router R2a, "router live for the daily plan", sub-stage A;
# docs/specs/plan_router_r2_v1.md §9, owner-directed 2026-10-13), on top of
# mvp-0.22 (the chain stays linear: mvp-0.23 means everything mvp-0.22 means
# PLUS this). Today's plan is composed by the staged frame: DL1's lanes and
# lane_quota_v1 over the set the P4 constraint engine admits (owner Q1), so a
# block loses only the items a named hard constraint refuses (a quick check on
# a surface the learner has already seen, a surface reserved for an
# assessment, an inactive or unrenderable item) and the block order is
# unchanged; and ``golden_path.advance`` goes through the P2 bridge (D13: a
# requested state other than the canonical successor is the learner's own
# choice). It changes what is SERVED, not the projection, so it is another
# successor tag on the mvp-0.8 namespace. No model is called (R2b). The
# receipts R2a adds (plan presentations, the stored state card, outcomes v2)
# are logging and act at every version. The branch built it as mvp-0.23 (a
# placeholder, migration 205) and it kept its label at its landing after exam
# protection and reading hardening, which took no successor (migration 202).
# Kill switch: ``router.enabled`` (off: Today and the P2 RPC serve exactly as
# mvp-0.22).
ROUTER_STAGED_FRAME_ALGORITHM_VERSION = "mvp-0.23"

# mvp-0.24 (router R2b + R2c under ONE successor, "both models live, the
# mixture" and "restraint, sensors, retrieval"; docs/specs/plan_router_r2_v1.md
# §9, owner decisions 2026-10-13), on top of mvp-0.23 (the chain stays linear:
# mvp-0.24 means everything mvp-0.23 means PLUS this). Today's block choice is
# a logged draw from the model mixture: the staged rule's pick, the Decider's
# and the router LLM's distributions over the top-k reversible candidates,
# with an exact propensity and a floor for every candidate
# (``router.mode = "mixture"``); a mid-block follow-up is a logged
# ``plan_interrupt`` decision (join the current block now, or wait for the
# next one; ``router.restraint``), with the P4 constraint engine run on it.
# The models' sensors, similar past decisions and teach-back summaries are
# context and receipts. It changes what is SERVED, not the projection, so it
# is another successor tag on the mvp-0.8 namespace; replay never asks a
# model (the decisions are raw ledger rows). The branch built it as mvp-0.24
# (a placeholder, no migration) and it kept its label at its landing after
# RW3a, the tutor delivery fixes and GLM-OCR, which took no successor. Kill
# switches: ``router.mode = "staged"`` (mvp-0.23's staged
# rule exactly), ``router.restraint = false`` (follow-ups join the current
# block), ``router.enabled = false`` (mvp-0.22's plan).
ROUTER_MIXTURE_ALGORITHM_VERSION = "mvp-0.24"

# mvp-0.25 (method-explicit items, owner rule 2026-10-13), on top of mvp-0.24
# (the chain stays linear: mvp-0.25 means everything mvp-0.24 means PLUS
# this). Rubric criteria name the fact a step establishes; an item whose
# target IS a method states it ("Use {method} in your answer.") and records it
# as ``PracticeItem.required_method``. The
# grader's own-route rules gain the required method (``own-route-v2``): a
# criterion tied to the item's required method is graded on use of that
# method, so another route fails it without a quoted wrong step (the route is
# the evidence; the grader still reports ``divergent_route``), and neither
# PF-c's gate nor the unlocated-mark-down rule unassesses it; every other
# criterion keeps mvp-0.20's rules (any valid method; a mark-down needs a
# verbatim quote). Persisted meaning changes for NEW grades on required-method
# items only (the policy's ``required_method``, the record's method criteria,
# the ``+own-route-v2`` prompt and calibration identity); the projection
# namespace is unchanged and replay reads every record as written. Kill
# switch: ``required_method.enabled`` (off: new answers grade exactly as
# mvp-0.24). The branch built it as mvp-0.22-placeholder (no migration) and it
# was relabelled mvp-0.25 when it merged after VOI v2 (mvp-0.21), the Decider
# migration (mvp-0.22) and router R2a/R2b+c (mvp-0.23, mvp-0.24).
# The generation side (criteria phrased by fact, the required method written
# only on a method target) is a content change behind no tag.
METHOD_EXPLICIT_ALGORITHM_VERSION = "mvp-0.25"

# mvp-0.26 (regrade contracts, an algorithm successor to a bug fix queued
# 2026-10-16; docs/reviews/regrade-contract-replay.md), on top of mvp-0.25
# (the chain stays linear: mvp-0.26 means everything mvp-0.25 means PLUS
# this). Below it an ordinary regrade read the item but cited no assessment
# contract, and replay took the contract from the FIRST live row citing one,
# so a regrade above the original maximum could not be saved, one within it
# replayed against the wrong maximum, and an uncited regrade was rescored (or
# failed ``rebuild`` on ``correctness <= 1``) once the item changed. At this
# tag every regrade cites the contract it graded against (the frozen one for
# a method-explicit answer, else a snapshot of the item it read), carries the
# attempt's next grading revision and supersedes every live row of the
# attempt, so the grade it writes is the attempt's only current grading
# epoch; an adjudication does the same. Replay, the canonical projection and
# the grade dual-write read the CURRENT epoch (``learnloop.grading_epochs``)
# and its own contract, never the first live row's. A current epoch citing no
# contract (rows written before the tag) is never read against today's item:
# it is held for review (``grade_contract_unrecorded``), its correctness taken
# from the maximum recorded with it where one exists; a regrade or an
# adjudication releases it. Persisted meaning changes, so it is a successor
# tag on the mvp-0.8 namespace; under every earlier tag rows replay exactly as
# before. No kill switch: the earlier writer is the defect (rolling the
# version back is restore-only).
REGRADE_CONTRACT_ALGORITHM_VERSION = "mvp-0.26"

# mvp-0.27 (one serve/administration eligibility decision, queued 2026-10-16;
# docs/reviews/serve-eligibility-decision.md and its Codex review), on top of
# mvp-0.26 (the chain stays linear: mvp-0.27 means everything mvp-0.26 means
# PLUS this). Every serve path (the queue's cold lane, the daily plan's pool,
# reconcile, serve and pick, the session serve, ``open_queue_item``, the TUI's
# open, the CLI's attempt, every probe and placement presentation, the
# placement quick check's offers) asks the one decision submit asks
# (``learnloop.serve_eligibility``), so an item submit would prime is never
# served as a measurement. A cold check whose item submit primes with no
# lapse, or whose item was attempted after the check was scheduled, can never
# be taken cold on that item: the item is served as ordinary practice and the
# check withdrawn with its typed disposition (``unmeasurable_no_held_out_surface`` for
# a repair cold retry; an expired certification probe). Historical writers
# (exam seeding, an exam's finish, a kept-state sim) count only reveals at or
# before their own instant when auto-priming (Q33). Submit's rule is kept
# exactly (any primed draft is refused a cold check). It changes what is
# SERVED and which new seeded or simulated attempts are primed, not the
# projection, so it is another successor tag on the mvp-0.8 namespace; replay
# reads every recorded flag as written. Kill switch: ``eligibility.enabled``
# (off: every path serves and admits exactly as mvp-0.26). The branch built it
# without a tag; the Codex review (F4) required this one.
ELIGIBILITY_DECISION_ALGORITHM_VERSION = "mvp-0.27"

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
    DAILY_PLAN_ALGORITHM_VERSION,
    PROBE_TIE_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
    ROUTE_RULES_ALGORITHM_VERSION,
    VOI_STOPPING_ALGORITHM_VERSION,
    DECIDER_TIER1_ALGORITHM_VERSION,
    ROUTER_STAGED_FRAME_ALGORITHM_VERSION,
    ROUTER_MIXTURE_ALGORITHM_VERSION,
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    REGRADE_CONTRACT_ALGORITHM_VERSION,
    ELIGIBILITY_DECISION_ALGORITHM_VERSION,
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

# Versions whose Today serves the finite daily plan (behind ``plan.enabled``).
# Every later successor keeps the plan; gates must use this set, never
# equality against DAILY_PLAN_ALGORITHM_VERSION.
DAILY_PLAN_VERSIONS: frozenset[str] = successors_from(DAILY_PLAN_ALGORITHM_VERSION)

# Versions whose Today queue admits probe near-ties to the seeded exploration
# (behind ``router.probe_tie_admission``). Every later successor keeps it;
# gates must use this set, never equality against PROBE_TIE_ALGORITHM_VERSION.
PROBE_TIE_VERSIONS: frozenset[str] = successors_from(PROBE_TIE_ALGORITHM_VERSION)

# Versions whose placement reads the learner-text gap's sooner checks (behind
# ``learner_text_gaps.sooner_check_enabled``). Every later successor keeps it;
# gates must use this set, never equality against
# LEARNER_TEXT_GAP_ALGORITHM_VERSION.
LEARNER_TEXT_GAP_VERSIONS: frozenset[str] = successors_from(LEARNER_TEXT_GAP_ALGORITHM_VERSION)

# Versions whose attempts record the answer-key gate (canonical sources S1).
# Every later successor keeps it; gates must use this set, never equality.
SOURCE_REFERENCE_GATE_VERSIONS: frozenset[str] = successors_from(SOURCE_REFERENCE_GATE_ALGORITHM_VERSION)

# Versions whose intervention needs try the learner's sources before
# generating (canonical sources S2b, behind source_service.source_first_needs).
SOURCE_FIRST_NEEDS_VERSIONS: frozenset[str] = successors_from(SOURCE_FIRST_NEEDS_ALGORITHM_VERSION)

# Versions whose blind grader gets the route rules and the server-side
# unlocated rule (behind ``proof_check.enabled``). Every later successor keeps
# them; gates must use this set, never equality against
# ROUTE_RULES_ALGORITHM_VERSION. (mvp-0.17's separate check has no gate any
# more: no version runs it.)
ROUTE_RULES_VERSIONS: frozenset[str] = successors_from(ROUTE_RULES_ALGORITHM_VERSION)

# Versions whose serving values the four former count caps (behind
# ``voi_stopping.enabled``) and whose probe hypothesis lane reads the diagnosis
# overlay (behind ``diagnosis.probe_lane_reads_diagnosis``). Every later
# successor keeps both; gates must use this set, never equality against
# VOI_STOPPING_ALGORITHM_VERSION.
VOI_STOPPING_VERSIONS: frozenset[str] = successors_from(VOI_STOPPING_ALGORITHM_VERSION)

# Versions whose small judgments the Decider decides (Tier 1, behind one
# ``decider_routes`` switch per judgment).
DECIDER_TIER1_VERSIONS: frozenset[str] = successors_from(DECIDER_TIER1_ALGORITHM_VERSION)

# Versions whose Today plan the staged frame composes and whose P2 RPC goes
# through the bridge (router R2a, behind ``router.enabled``). Every later
# successor keeps them; gates must use this set, never equality.
ROUTER_STAGED_FRAME_VERSIONS: frozenset[str] = successors_from(ROUTER_STAGED_FRAME_ALGORITHM_VERSION)

# Versions whose Today blocks the model mixture chooses (behind
# ``router.mode = "mixture"``) and whose mid-block follow-ups are restraint
# decisions (behind ``router.restraint``), router R2b + R2c. Every later
# successor keeps them; gates must use this set, never equality.
ROUTER_MIXTURE_VERSIONS: frozenset[str] = successors_from(ROUTER_MIXTURE_ALGORITHM_VERSION)

# Versions whose own-route rules grade a required method's criteria on use of
# the method (``own-route-v2``, behind ``required_method.enabled`` and the
# route rules' own switch). Every later successor keeps them; gates must use
# this set, never equality against METHOD_EXPLICIT_ALGORITHM_VERSION.
METHOD_EXPLICIT_VERSIONS: frozenset[str] = successors_from(METHOD_EXPLICIT_ALGORITHM_VERSION)

# Versions whose regrades and adjudications cite the contract they graded
# against and supersede every live row, and whose replay reads the current
# grading epoch's own contract (holding an epoch that cites none). Every
# later successor keeps them; gates must use this set, never equality.
REGRADE_CONTRACT_VERSIONS: frozenset[str] = successors_from(REGRADE_CONTRACT_ALGORITHM_VERSION)

# Versions whose serve paths and submit ask the one eligibility decision
# (behind ``eligibility.enabled``), and whose historical writers bound their
# auto-prime window at their own instant. Every later successor keeps them;
# gates must use this set, never equality.
ELIGIBILITY_DECISION_VERSIONS: frozenset[str] = successors_from(ELIGIBILITY_DECISION_ALGORITHM_VERSION)

# The newest successor: the last tag in the chain. ``learnloop upgrade`` with
# no ``--to`` targets it, and new vaults start at it
# (``config.template.default_config_text``; owner decision 2026-10-12).
LATEST_ALGORITHM_VERSION: str = SUCCESSOR_CHAIN[-1]
