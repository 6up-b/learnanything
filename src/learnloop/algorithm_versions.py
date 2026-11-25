"""Dependency-neutral algorithm-version vocabulary.

These names gate persistence formats as well as domain behavior, so their
authority cannot live in a service module without making the database layer
import upward.  Domain modules re-export them for compatibility.
"""

from __future__ import annotations

# The legacy model's tag, before the knowledge model: what a vault whose config predates the key is. The
# recall-calibration harness still builds its scratch vault there (refactor bug ledger D-24).
LEGACY_ALGORITHM_VERSION = "mvp-0.6"

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
# blind grader records (at this version and its successors), is unassessed - out of the grade, and no facet evidence
# either way. It is gated by the record, never by an exact version. mvp-0.10
# history from before the rule exists
# (Slice 1 M2 live runs), so the boundary is per record, not per tag: each new
# unverified row and blind record names the interpretation it was written
# under, replay reads every record as it was written (a pre-rule record keeps
# its grader-sum grade and its M2 evidence), and a regrade rewrites a pre-rule
# record under the rule (canonical_projection.unassessed_evidence_row).
# Its kill switch (and the joint vault's shadow diagnosis) went once every vault
# was past the tag; jointly graded history replays as it was recorded.
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
# (mvp-0.12). Its kill switch went once every vault was past the tag. New
# vaults started here until mvp-0.14 merged.
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
# after the daily plan (mvp-0.14). Its kill switch went once every vault was
# past the tag.
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
# New vaults started here until mvp-0.18 merged.
# Owner decision 2026-10-13 (route-check-in-grader): the separate check was
# removed from serving. Records written by the check (blind records, ledger rows,
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
# namespace is unchanged. Its kill switch (off: mvp-0.16's grading) went once
# every vault was past the tag. The branch built it as mvp-0.18 (a placeholder) and it was relabelled mvp-0.20
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
# namespace is unchanged and replay reads every record as written. Its kill
# switch (off: mvp-0.24's grading) went once every vault was past the tag. The branch built it as mvp-0.22-placeholder (no migration) and it
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
# reads every recorded flag as written. Its kill switch went once every vault
# was past the tag. The branch built it without a tag; the Codex review (F4)
# required this one.
ELIGIBILITY_DECISION_ALGORITHM_VERSION = "mvp-0.27"

# mvp-0.29 (daily-loop DL2, intent; docs/reviews/daily-loop-dl2.md and its
# Codex re-review F2), on top of mvp-0.27 (the chain stays linear:
# mvp-0.29 means everything its predecessor means PLUS this). DL2 landed on
# main before adaptive difficulty AD2+AD3, so mvp-0.28 is never used on main;
# AD2+AD3 lands as mvp-0.30 with mvp-0.29 as its predecessor (orchestrator
# decision at DL2's landing, 2026-10-20). The learner's intent (Learn, Master,
# Keep, Light touch, "Check once", Reference, Pause, Let go, a deadline) is
# read when serving: excluded items are never served, requested or rebuilt
# as a follow-up (so a paused item's pending cold retry waits), a "Check
# once" is served cold only when the one eligibility decision allows it and
# answered only by an attempt it would have served cold, effective dues at
# the recall targets, push, admission, re-entry and reading by intent. It
# changes which items are served as measurements (the 2026-10-17 rule), not
# the projection: due_at, FSRS state, evidence and replay never read it, so
# it is another successor tag on the mvp-0.8 namespace. Its kill switches
# (intent.enabled, intent.recall_targets_enabled) went once every vault was
# past the tag.
INTENT_ALGORITHM_VERSION = "mvp-0.29"

# mvp-0.30 (adaptive difficulty AD2+AD3, owner 2026-10-18;
# docs/specs/spec_adaptive_difficulty_v1.md §14, §11.1;
# docs/reviews/adaptive-difficulty-ad23.md), on top of mvp-0.29 (the chain
# stays linear: mvp-0.30 means everything mvp-0.29 means PLUS this; it lands
# after DL2, so mvp-0.28 is never used: orchestrator decision 2026-10-20). AD's own
# posterior in two views (the subject view, with learned relatedness and
# reading, and each LO's view) steers what is served: a planned new-material
# slot is served by AD's draw over its support (practice in the 70-80% band,
# calibration within acceptable difficulty, exact logged propensities), a slot
# whose support is empty is displaced and its item deferred until its blocking
# condition clears, commissions name a feature point, and the generation
# contract asks for an item AT that point (no difficulty band). Readiness
# numbers and the router card's AD fields read the subject view. Six kill
# switches under [adaptive_difficulty], each restoring its part of mvp-0.29
# exactly: selection, generation_contract, promoted_predictor,
# learned_coupling, reading_opportunities, reading_self_check
# (generation_contract went once every vault was past the tag; the contract
# runs under AD's master switch). It changes what
# is SERVED, never the authority-propagation projection, evidence, mastery,
# FSRS or certification (A2, A11, A12), so it is another successor tag on the
# mvp-0.8 namespace. The Reader's randomized dose offers ship beside it with
# their own switch (reading_dose_offers) and no tag (spec §5.12).
ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION = "mvp-0.30"

# mvp-0.31 (reader workbench RW2d, workbench signals in the learner field;
# spec_reader_workbench_v1 §5.11, G41; docs/reviews/reader-workbench-RW2d.md),
# on top of mvp-0.30 (adaptive difficulty AD2+AD3; the chain stays linear:
# mvp-0.31 means everything mvp-0.30 means PLUS this). Built on main at
# mvp-0.29 while AD2+AD3 held mvp-0.30; the landing merge chained it after
# AD2+AD3 (the tag lives in this ONE constant: the upgrade, the CLI and the
# gates all read it). The field's interaction-signal derivation gains two
# sources from the workbench ledgers: a mid-work stuck step with text (a
# ``stuck_confusion`` row, like a stuck answer the grader read as confusion)
# and help asked for before the first step (a help-before-work row). Both
# carry no outcome and no mass and are linked to no attempt, so they never
# lower the record, an attempt's assistance or a predictor's state (F2); they
# block fast-track and teach the LO first, which changes what is SERVED
# (Phase 6's fast-track, the quick check's split, new-material order and the
# plans built on them; F3), not the projection, so it is another successor
# tag on the mvp-0.8 namespace. Receipts (``field_signal_receipts``, migration
# 219) record what the predecessor's derivation and rule would have decided
# wherever they differ. Kill switch: ``workbench.field_signals_enabled``
# (off: the derivation, Phase 6 serving and every plan build exactly as the
# predecessor).
WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION = "mvp-0.31"

# mvp-0.32 (reader workbench RW7b, the plan follows the reading path;
# spec_reader_workbench_v1 §10.2, G47; docs/reviews/reader-workbench-RW7b.md),
# on top of mvp-0.31 (RW2d; the chain stays linear: mvp-0.32 means everything
# mvp-0.31 means PLUS this). The tag lives in this ONE constant (the upgrade,
# the CLI and the gates all read it), so a landing that finds another number
# free renumbers it here. DL1's reading block opens the next unfinished core
# or prerequisite section of the source's reading path (RW7a's judged labels
# at the learner's depth, honest labels re-applied at plan time, a "read it
# anyway" counting as core and a "skip it" left out) instead of the next
# section in the predecessor's order; enrichment, already shown and assumed
# sections are never planned. A source with no path (no depth chosen, never
# judged) keeps the predecessor's order. That changes what is SERVED (the
# plan's reading block; F3), never evidence or the projection, so it is
# another successor tag on the mvp-0.8 namespace. Receipts: the plan's
# ``split_json["reading_path"]`` records the section the predecessor's order
# would have chosen. Its kill switch (reading_paths.plan_uses_path) went once
# every vault was past the tag; with the Guide's ``reading_paths.enabled``
# off, every plan build is exactly the predecessor's.
READING_PATH_PLAN_ALGORITHM_VERSION = "mvp-0.32"
# mvp-0.33 (learned parameters LP-min (a), the four claim-defect fixes;
# spec_learned_parameters_v1 §3.0b item 1, AD §5.5;
# docs/reviews/lp-min-claim-fixes.md), on top of mvp-0.32 (reader workbench
# RW7b; the chain stays linear: mvp-0.33 means everything mvp-0.32 means PLUS
# this). Built on main at mvp-0.31 as mvp-0.32 while RW7b also built a
# successor there; RW7b landed first, so the landing renumbered it HERE to
# mvp-0.33 (the upgrade, the CLI and the gates all read this one constant).
# It changes how learner claims seed and re-anchor the per-LO mastery EKF, so
# live mastery and the replayed projection both move (a mastery delta, never evidence, FSRS or
# certification): (1) a tutor gap declaration re-anchors its LO through
# ``reanchor_mastery_from_claim``, as rung-variant requests and too-easy/too-hard
# reports already did; (2) replay applies each claim at its own ``created_at``
# in the attempt stream (the seed reads only claims made by the first
# attempt; a later re-anchoring claim merges at its own time), never the
# claims in force now; (3) a claim merged into a state with evidence moves
# the mean only: the variance never drops below the state's own (AD §5.5,
# "a claim never shrinks a variance"); (4) among equally specific covering
# claims the most recent wins, then the larger pseudo-count, never the higher
# level. One kill switch for all four: ``mastery.claim_fixes_enabled`` (off,
# or below the tag: every claim seed, re-anchor, merge, ranking and replay
# exactly as the predecessor).
CLAIM_FIXES_ALGORITHM_VERSION = "mvp-0.33"
# mvp-0.34 (rebuild equivalence: replay reads the ledger as the live write saw
# it; docs/reviews/rebuild-equivalence-fix.md and its Codex review F4), on top
# of mvp-0.33 (the LP claim fixes; the chain stays linear: mvp-0.34 means
# everything mvp-0.33 means PLUS this). Built on main at mvp-0.31 while RW7b
# (mvp-0.32) and the LP claim fixes (mvp-0.33) landed; the landing chained it
# after them (the tag lives in this ONE constant: the upgrade, the CLI and the
# gates all read it). Replay recomputes each
# attempt with the whole ledger already on disk; below the tag it read the
# attempts recorded AFTER the one it recomputed (the recent-attempt windows:
# familiarity, event severity, item quality) and the whole-history canonical
# facet cache (prediction, the variance floor, facet updates). From the tag on
# it reads the ledger bounded at the replayed attempt's position, so a rebuild
# reproduces the live state. A live write is unchanged at every version; what
# moves at activation is the replayed (rebuilt) mastery, surprise and item
# quality of multi-attempt histories, and the schedules computed from them,
# toward the live values. That changes the same-version golden projection, so
# it is a successor (playbook item 6), not an in-place amendment.
REPLAY_LEDGER_ALGORITHM_VERSION = "mvp-0.34"

# mvp-0.35 (Reader CA2, one Ask; docs/specs/ux_reader_compare_ask_v1.md §7,
# K10 and §15 Q3-Q4; docs/reviews/reader-ca2-one-ask.md), on top of mvp-0.34
# (rebuild equivalence; the chain stays linear: mvp-0.35 means everything
# mvp-0.34 means PLUS this). Built on main at mvp-0.32 as mvp-0.34 while the
# LP claim fixes held mvp-0.33; the batch landing (2026-10-26) renumbered it
# here after rebuild equivalence's mvp-0.34 (the tag lives in this ONE
# constant: the upgrade, the CLI and the gates all read it). One rule for help
# on a check on your own:
#
# * a question asked during a cold administration counts as help only when
#   the tutor model's ``question_type`` is substantive
#   (``tutor_qa.HINT_EQUIVALENT_TYPES``), on every cold path: the practice
#   Ask already did, and the Reader's cold Ask (a workbench-bound one and the
#   client-reported cold attempt's) now does too instead of counting every
#   question (the predecessor's L6 rule);
# * help taken on a cold follow-up (``cold_retry``,
#   ``certification_cold_probe``) makes that attempt practice with help: submit
#   admits it (the predecessor refused it) and it never answers the cold
#   measurement, which the next serve withdraws as practised since scheduled.
#
# That changes how an attempt is classified (assisted or on your own) and
# what submit admits, never the projection, so it is another successor tag on
# the mvp-0.8 namespace. Its kill switch went once every vault was past the
# tag.
ONE_ASK_ALGORITHM_VERSION = "mvp-0.35"

# mvp-0.36 (replaced learner claims kept; docs/reviews/lp-learner-report-superseded.md),
# on top of mvp-0.35 (Reader CA2; the chain stays linear: mvp-0.36 means
# everything mvp-0.35 means PLUS this). The successor of the Medium recorded
# at the rebuild-equivalence landing: a learner report (a too_easy/too_hard
# retirement or a rung-variant request) or a new starting level replaces the
# earlier claim of its source on the same scope (the replace seam). Below the
# tag the seam DELETED that claim, whose live re-anchor had already moved
# mastery, so replay could not apply it and a rebuild disagreed with live.
# From the tag on the seam keeps the replaced row, marked
# ``learner_claims.superseded_by`` (migration 225): every live reader reads
# only the rows no claim replaced, exactly what it read before; replay applies
# each claim at its own point and, at every point, reads a replaced claim
# only until the claim that replaced it was made. A live write is unchanged
# except that nothing is deleted; what moves is the replayed mastery of an LO
# whose claim was replaced after the tag, toward the live value. No kill
# switch: no live decision changes, and switching replay back would only
# restore a known rebuild/live divergence. Rows deleted below the tag are
# gone; replay cannot apply them.
# Also under this tag's note: the AD guard offer-receipts fix (main cdd0a3c4f)
# restored AD serving in place, without its own tag, on vaults holding an
# answer picked from a published offer; it was accepted by the orchestrator's
# ruling under the owner's proportionate bar (docs/reviews/ad-guard-offer-receipts.md §10).
SUPERSEDED_CLAIMS_ALGORITHM_VERSION = "mvp-0.36"

# mvp-0.37 (mobile PR-4: a live attempt writes only its scheduling columns;
# docs/specs/spec_mobile_tailnet_v1.md §3.3 PR-2/PR-4, §9.3;
# docs/reviews/mobile-pr3-pr4.md and its Codex review F4), on top of mvp-0.36
# (the kept replaced learner claims; the chain stays linear: mvp-0.37 means
# everything mvp-0.36 means PLUS this). Built on main at mvp-0.35 as
# mvp-0.36; renumbered after the learner-report successor at its landing
# onto main (the tag lives in this ONE constant: the upgrade, the CLI and the
# gate all read it). Content sync owns
# a practice item row's ``active`` flag and ``content_hash``, and an attempt
# owns the memory state: from the tag on, a live attempt's write to an
# existing row takes only the scheduling columns and the last-attempt time,
# its ``active`` can only close (a diagnostic probe's single use still lands)
# and its ``content_hash`` is never written. Below the tag the attempt upserts
# the whole row from the vault it graded against, which (a) undoes a content
# sync another process committed while the answer was being graded (a
# retired item reopens, an edited one gets its old hash back: PR-2's reverse
# race) and (b) even without a concurrent writer reopens a row the sync rule
# keeps closed while its YAML is active (review-parked,
# measurement-superseded, a microprobe, a deactivation replay keeps) until the
# next sync. (b) changes which items are SERVED (``inactive_state``), so it is
# a successor (the 2026-10-17 eligibility rule), never evidence, FSRS, the
# projection or replay: replay keeps the full upsert and re-closes what was
# closed outside the ledger. Its kill switch went once every vault was past
# the tag.
ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION = "mvp-0.37"

# mvp-0.38 (a fresh cold retry after help on a cold follow-up; owner decision
# 2026-10-25, Reader CA2 follow-up Q4; docs/reviews/cold-retry-after-assist.md),
# on top of mvp-0.37 (mobile PR-4; the chain stays linear: mvp-0.38 means
# everything mvp-0.37 means PLUS this). Below the tag, help taken on a due
# repair ``cold_retry`` converts the attempt to practice with help (mvp-0.35)
# and leaves the measurement to be withdrawn at the next serve, so the repair
# ends unmeasurable. From the tag on, the live attempt step withdraws that
# retry at once (the same typed disposition) and schedules ONE fresh cold
# retry for the same repair on another independent surface, timed by the
# lane's existing rule (``remediation.COLD_RETRIEVAL_DELAY`` after the
# attempt that took the help, open for ``remediation.COLD_RETRY_WINDOW``). A
# fresh retry that is itself assisted is withdrawn and spawns nothing (one
# fresh retry per chain: a structural bound). A certification cold probe is
# not rescheduled (one probe per certificate, ever: §5.7 and migration 139's
# unique index). That changes which cold checks are scheduled and served, never
# evidence, FSRS, the projection or replay (replay passes no vault and
# schedules nothing; ``followup_tasks`` is workflow state), so it is a
# successor by the 2026-10-17 eligibility rule. Its kill switch went once
# every vault was past the tag.
COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION = "mvp-0.38"

# mvp-0.39 (Reader RW6b part 1: cold follow-ups after a reader session;
# spec_reader_workbench_v1 §9.3 "Why no successor", whose fallback the Codex
# review of docs/reviews/reader-rw6b-p1-followups.md invoked, F4), on top of
# mvp-0.38 (the cold-retry reschedule; the chain stays linear: mvp-0.39 means
# everything mvp-0.38 means PLUS this). From the tag on, an ended reader
# session's open questions are
# valued (``value_candidates``) and each check that clears the stop becomes an
# automatic ``test_me_later`` commitment dated by purpose, re-valued before
# each day's plan; DL2 serves it as a "Check once", gated at serve by the full
# exposure rule and repair ownership (``scheduling.intent.followup_gate``).
# That changes which dated requests the maintain lane holds and serves, never
# evidence, FSRS, the projection or replay (replay passes no vault and plans
# nothing; ``reader_session_digests`` is workflow state), so it is a
# successor by the 2026-10-17 eligibility rule. Its kill switch
# (followups.enabled) went once every vault was past the tag.
READER_FOLLOWUPS_ALGORITHM_VERSION = "mvp-0.39"
# mvp-0.40 (curriculum C1, the plan follows the deliverable;
# docs/specs/spec_deliverable_curriculum_v1.md §7.6, §8.1;
# docs/reviews/curriculum-c1-plan-follows-path.md), on top of mvp-0.39 (Reader
# RW6b part 1's cold follow-ups; the chain stays linear: mvp-0.40 means
# everything mvp-0.39 means PLUS this). Built as mvp-0.39 on mvp-0.38 while
# RW6b part 1 was in fix rounds and renumbered at its landing after RW6b
# took mvp-0.39 (ONE constant). Below the tag, the plan's reading block is RW7b's
# (the per-book reading path narrowing the predecessor's order). From the tag
# on, with the nearest active deliverable's path fresh (judged for the
# learner's current state), the reading block opens the next unfinished core
# or prerequisite section in the deliverable path's order, in whichever book
# it is; the predecessor's front-matter rule, the exam filter and DL2's
# ``reading_allowed`` still run first on each candidate. That changes what is
# served through labels a model judged (RW7b's F3 reasoning), never evidence,
# FSRS, the projection or replay (replay never reads a plan's reading), so it
# is a successor by the 2026-10-17 eligibility rule. Its kill switch
# (curriculum.plan_uses_path) went once every vault was past the tag; with
# ``curriculum.enabled`` off: RW7b's plans byte for byte, gate G-C4.
DELIVERABLE_PLAN_ALGORITHM_VERSION = "mvp-0.40"

# mvp-0.41 (teacher TE1, the first good lesson, with curriculum C4 folded in;
# docs/specs/spec_teacher_v1.md §18.3, §20; spec_deliverable_curriculum_v1
# §8.2; docs/reviews/teacher-te1-first-lesson.md), on top of mvp-0.40
# (curriculum C1; the chain stays linear: mvp-0.41 means everything mvp-0.40
# means PLUS this). Built as mvp-0.41 on main's mvp-0.40; renumbered at its
# landing if another successor lands first (ONE constant). Below the tag, no
# lesson can open. From the tag on, with ``teacher.enabled`` on, a lesson the
# learner starts (an LO's or a Reader selection's "Teach me this") is taught by
# the ``teacher`` route from a brief built from the ledger; its checks are
# minted items held to their lesson and answered as
# ``reconstruction_after_walkthrough`` attempts graded by the blind grader,
# entering mastery at a LEARNED mass (spec §12.1: a seeded prior centred on
# the type's 0.5, moved only by later cold outcomes on unseen items of the
# same LO; mixed with the teacher's forecast by a learned pool weight, §12.2);
# its teaching text writes ``tutor_answer`` / ``source_review`` reveal rows
# (basis ``lesson:<id>``), which prime later attempts under the mvp-0.27 rule;
# and its close commits delayed retention and transfer checks (Check once).
# That changes which new attempts are primed, what is served (lesson holds,
# delayed checks) and how far mastery moves on a lesson check, so it is a
# successor (the playbook; spec §18.3). Replay reads each check's recorded
# mass (``lesson_checks``, a RECEIPT) through the one as-of seam
# (``learner.lesson_weight.lesson_check_mass``); the weight posterior and the
# tap/hedge recalibration are DERIVED (one replayer). Kill switch:
# ``teacher.enabled`` (off: no lesson opens, so nothing here writes and every
# path is mvp-0.40's byte for byte). The weight's own switches (the type's
# 0.5; the learned mass without the pool) went once every vault was past the tag.
TEACHER_ALGORITHM_VERSION = "mvp-0.41"
# mvp-0.42 (the help fold counts exactly the help rows that attach;
# follow-ups Nov 2 (b) and its Codex review F1; docs/reviews/followups-nov2.md),
# on top of mvp-0.41 (teacher TE1 + C4; the chain stays linear: mvp-0.42 means
# everything mvp-0.41 means PLUS this). Built as mvp-0.41 while teacher
# TE1 + C4 was landing as mvp-0.41 too: renumbered mvp-0.42 at this landing
# (TE1 landed first; ruling R4; ONE constant). Below the tag, a keyed submit's fold counts the key's
# shown server hints in the submit's own practice session only, and H0's
# attach (after the commit) takes the key's rows in every session, so a hint
# shown before the session rolled over was attached uncounted. From the tag
# on, the keyed fold reads the key's rows in any session (H0's attach rule)
# and the attempt takes the rows it counted in its own write transaction
# (``hint_fold.attach_keyed``), so a level 1-3 row raises ``hints_used`` and a
# level 4-5 row primes the attempt it attaches to. That changes which new
# attempts are primed and their hint counts (so dampening, certification
# eligibility and FSRS), never replay (replay re-applies the stored
# ``hints_used`` and ``primed`` and never folds) or the projection, so it is a
# successor by the 2026-10-17 eligibility rule. Its kill switch went once
# every vault was past the tag.
HELP_FOLD_ATTACH_ALGORITHM_VERSION = "mvp-0.42"

# mvp-0.43 (teacher TE1b, the router suggests lessons and the learner opts in;
# docs/specs/spec_teacher_v1.md §15.1, §18.3, §20;
# docs/reviews/teacher-te1b-router-suggestions.md), on top of mvp-0.42
# (follow-ups Nov 2; the chain stays linear: mvp-0.43 means everything mvp-0.42
# means PLUS this). Built on main's mvp-0.41 (teacher TE1) while follow-ups
# Nov 2 was landing as mvp-0.42, which landed first; this claims the next tag
# (ruling R4 at its landing; ONE constant: the upgrade, the CLI and the gate
# all read it). Below
# the tag, Today never suggests a lesson. From the tag on, with the router,
# its decision log and lessons on, Today's open draws at most one ``instruct(lesson)``
# suggestion a day among LOs new on a goal, failing their cold checks or
# predicted below adaptive difficulty's calibrate cut, with an exact logged
# propensity (shown or not: a ``lesson_suggestion`` router decision); a shown
# card's Start opens a TE1 lesson whose origin is that decision, and every
# response is logged (``router_suggestion_responses``) and moves the seeded
# acceptance model and decline recovery. That changes what Today shows and
# offers, so it is a router successor (spec §15.1), never evidence, FSRS, the
# projection or replay (a suggestion writes no attempt; its decision is
# RAW_LEDGER and its outcome joins ``router_outcomes`` intention-to-treat).
# Its kill switch went once every vault was past the tag.
LESSON_SUGGESTIONS_ALGORITHM_VERSION = "mvp-0.43"

# mvp-0.44 (data capture, the long-horizon objective's dataset; owner decisions
# 2026-11-02 and 2026-11-03; docs/reviews/data-capture-a1-a6.md), on top of
# mvp-0.43 (the chain stays linear: mvp-0.44 means everything mvp-0.43 means
# PLUS this). Three serving changes: a decision whose arms have no action of
# their own (a reading block, a follow-up that waits, a stop) has its objective
# frozen before the draw and, where a real choice was made, a "Check once"
# measures it, charged to the maintain lane so it replaces an ordinary slot; the
# router's ``not_ready`` branch keeps the existing fallback distribution and its
# existing epsilon floor (no model is asked); the teacher's delayed-check picker
# reads each item's own predicted success and draws uniformly over exact ties,
# with probability 1/n logged. The outcome changes with them
# (``router_outcomes_v3``, the shared ``delayed_completion_v1``), never
# certification, mastery, grading, FSRS or the projection. Its kill switch went
# once every vault was past the tag (a rebuild derives every vault's outcomes
# as ``router_outcomes_v3``). The prefilter receipts are additive and act at every version
# (``data_capture.receipts``).
DATA_CAPTURE_ALGORITHM_VERSION = "mvp-0.44"

# mvp-0.45 (follow-up generate and serve, FG1; owner decisions 2026-11-03;
# docs/specs/spec_followup_generate_serve_v1.md), on top of mvp-0.44 (the chain
# stays linear). On a miss with diagnosis on, one durable workflow owns the
# intervention: the router decides first whether and when (itemless, with
# ``no_intervention`` in its logged mixture), a frontier LLM writes one
# single-use probe aimed at the rival causes, machine checks admit it, and the
# next step opens it; the worked answer and the causes are held until it is
# answered. Every generated probe is single use (a durable identity and burn
# ledger, every door). Practice-lane needs fill in the background, and every
# episode entry enqueues generation (``auto_generate_on_entry`` is effectively
# true). Kill switch: ``followup.generate_and_serve`` (off, or below the tag,
# behaviour matches mvp-0.44 from an equivalent state, the stored
# ``auto_generate_on_entry`` applies, burns persist and open workflows settle
# as skipped).
FOLLOWUP_SERVE_ALGORITHM_VERSION = "mvp-0.45"

# mvp-0.46 (router objective RO1; owner decisions 2026-11-03 and 2026-11-04;
# docs/specs/spec_router_objective_v1.md §5), on top of mvp-0.45 (the chain
# stays linear). Three changes, each behind its own kill switch:
# * the surprise interval factor is no longer applied to the FSRS interval
#   (``scheduler.surprise.remove_interval_factor``): ``due_at`` follows
#   ``interval_for_retention(S)``; the rating, S, D and surprise itself are
#   unchanged, and ``attempt_surprise.fsrs_interval_factor`` records 1.0, what
#   was applied (replay writes the same under the same gate);
# * decision-time reads of attempts (the router card, the diagnoser's history,
#   AD's frozen history card, the learner contexts) use the availability time
#   ``coalesce(received_at, created_at)`` (``router_objective.available_at_reads``);
# * a learner's misconception pick (a ``learner_report:*`` resolution id) is
#   not counted as validated evidence for the diagnoser
#   (``router_objective.self_report_not_validated``); the factor's status and
#   resolution ids are unchanged.
# Off, or below the tag, each restores mvp-0.45 exactly. A change to the factor
# switch reaches persisted due dates at the next whole-vault rebuild (the
# upgrade runs one); the rebuild's receipt records the switch, and doctor warns
# when the config and that record disagree.
INTERVAL_FACTOR_ALGORITHM_VERSION = "mvp-0.46"

# mvp-0.47 (router objective RO4; owner decisions 2026-11-03 and 2026-11-04;
# docs/specs/spec_router_objective_v1.md §8), on top of mvp-0.46 (the chain
# stays linear). The objective, live: the plan's minutes become a soft limit
# (stop is supported at every reversible block boundary as an offer the learner
# can override, a block can run past the remembered minutes, lane shares stop
# excluding) and each block is drawn from a learned mix of two policies, the
# frontier LLM's (router_llm_choice_v3) and the numeric expected-value policy
# (argmax of the objective's Q-bar), with exact logged propensities and one
# immutable trace per decision. Kill switch ``router_objective.enabled``
# (default true at the tag): off serves mvp-0.46's mixture and frame exactly;
# below the tag nothing is computed.
ROUTER_OBJECTIVE_ALGORITHM_VERSION = "mvp-0.47"

# mvp-0.48 (router objective RO5; owner decisions 2026-11-03 and 2026-11-04;
# docs/specs/spec_router_objective_v1.md §9), on top of mvp-0.47 (the chain
# stays linear). Return and calibration: a stop coin at each reversible block
# boundary (offer stop or present the next block, 0.05 each way, an exact
# logged assignment) that trains stop's return model and hands kappa0 from its
# daily seed to a posterior; one randomized cold check a day, the day's first
# block, before any decision (r = 1/N_d exact), whose scores move the weight w
# off its prior; a small seeded share of misconception picks left open. Each
# arm is a declared price for information: stop_coin = 0, check_rate = "off"
# and pick_open_share = 0 serve mvp-0.47 exactly; below the tag nothing is
# drawn. [router_objective] fitted_models (default true) reads AD's fitted
# learning posterior and the combiner fed resolved checks; off, RO4's priors.
ROUTER_CALIBRATION_ALGORITHM_VERSION = "mvp-0.48"

# mvp-0.49 (router objective RO6; owner decisions 2026-11-03 and 2026-11-04;
# docs/specs/spec_router_objective_v1.md §10), on top of mvp-0.48 (the chain
# stays linear). A learned tail: fitted Q evaluation of a frozen logger
# version on low-dimensional belief features from RO0's decision-time
# snapshots, days to go and pending reports, its reward the objective's own R
# (never S); it enters the numeric policy's value as a residual,
# V~ = V_tail + w^ * V_residual, w^ a learned weight starting at zero that
# only RO5's randomized stop-coin contrasts (observed through the randomized
# checks) move, by slope and rank. No promotion step, no threshold, no
# minimum sample. [router_objective] learned_tail (default true) is its kill
# switch: off, or below the tag, mvp-0.48 serves exactly.
ROUTER_LEARNED_TAIL_ALGORITHM_VERSION = "mvp-0.49"

# mvp-0.50 (the router objective's follow-up batch after RO6; owner decisions
# 2026-11-03 to 2026-11-05; docs/specs/spec_router_objective_v1.md §8.11,
# §9.1, §10.1; docs/reviews/router-followups-nov5.md), on top of mvp-0.49 (the
# chain stays linear): the follow-up batch's serving changes, each behind its
# own [router_objective] switch (the review file lists them); every one off,
# or below the tag, mvp-0.49 serves exactly.
ROUTER_FOLLOWUPS_ALGORITHM_VERSION = "mvp-0.50"

# mvp-0.51 (teacher TE2; spec_teacher_v1 rev 5 §11.3, §11.5, §11.7, §11.8,
# §18.3, §24; docs/reviews/teacher-te2.md), on top of mvp-0.50 (the chain
# stays linear). Built on main's mvp-0.49 as mvp-0.50 and renumbered at its
# landing, after the router follow-up batch landed as mvp-0.50.
# What it changes: what is served (a lesson's teacher may ask for a generated
# single-use probe, FG1's generation path with a lesson origin, served cold
# inside the lesson and never again), what evidence exists (its blind-graded
# diagnostic_probe attempt, full evidence under the existing admissibility
# rule; its lesson_probe_correct forecast written before the serve) and what
# is created (gaps with source lesson through the text-gap pipeline; new
# topics for a typed goal through create_goal_lo, mechanism teacher_goal_v1).
# The brief becomes lesson_brief_v2 (no vault probe headers; where the last
# lesson left off) and Today offers "Continue your lesson", wherever lessons
# are on (``teacher.enabled``); its kill switch went once every vault was past
# the tag. Replay re-applies the
# probe's attempt as an existing type; nothing new is derived.
TEACHER_PROBES_ALGORITHM_VERSION = "mvp-0.51"

# mvp-0.52 (teacher TE3a, an adaptive difficulty successor; owner decision
# 2026-11-05, docs/specs/spec_teacher_v1.md rev 5 §14.2, §23.1 item 4, §24), on
# top of mvp-0.51 (the chain stays linear). A closed lesson's node with an LO,
# landed or taught, is one of AD's learning opportunities (prediction-only,
# under the reading-signal firewall's carve-out as amended by Q5), with its own
# learned dose curve per subkind (ad_lesson_priors_v1, centred on RO4's lesson
# placeholder: AD's prior gamma times the lesson-check mass prior 0.5), and the
# router objective's lesson interface reads that curve's posterior moments in
# place of the placeholder. [adaptive_difficulty] lesson_opportunities (default
# true) is its kill switch: off, or below the tag, AD is mvp-0.51's exactly and
# the objective keeps RO4's placeholder. Built on main 5565bede25 as mvp-0.50
# and renumbered at its landing, after the router follow-up batch (mvp-0.50)
# and TE2 (mvp-0.51) landed.
LESSON_OPPORTUNITY_ALGORITHM_VERSION = "mvp-0.52"

# mvp-0.53 (teacher TE3b, a router successor; owner decisions 2026-11-05,
# docs/specs/spec_teacher_v1.md rev 5 §15.1a, §23.1 items 1 and 5, §24), on top
# of mvp-0.52 (the chain stays linear). Lesson offers are candidates of the
# router objective: at a reversible plan_block boundary where the objective
# serves, TE1b's best lesson candidate joins the support (one offer a decision,
# under the ceiling), valued by RO4's offer branches with TE1b's acceptance
# model as a sensor and TE3a's lesson curve, shown to the LLM policy as one more
# option of its existing request, drawn from the logged mix and answered on that
# decision; lesson minutes count on the objective's clock; LOs with a pending
# lesson delayed check join its population (an objective-definition change
# point); RO6's features gain a lesson indicator (a features-version change
# point); TE1b's Today-open card is drawn only where the objective does not
# serve. Its kill switch went once every vault was past the tag. No migration. Expected mvp-0.53 at landing (one constant).
LESSON_OFFERS_ALGORITHM_VERSION = "mvp-0.53"

# mvp-0.54 (mobile frontend v2, stage V3: probes and cold checks on the phone;
# owner decision D3, accepted 2026-11-06; docs/specs/spec_mobile_frontend_v2.md
# §8's V3 row; docs/reviews/phone-v2-v3-probes.md), on top of TE3b's mvp-0.53 (the
# chain stays linear). What it changes: which items are served as measurements
# (the 2026-10-17 rule): a phone origin now serves and answers the phone-eligible
# diagnostic probes and FG1's generated follow-up probes it used to leave for
# the desktop, under the probe contract (cold, no help), each generated one
# burned at its first serve on whichever device opened it and refused on the
# other. The desktop (a None origin) serves exactly as mvp-0.53. Its kill switch
# is the phone host's ``phone_probes`` (mobile.toml, default true): off, or
# below the tag, the phone is V2's exactly. Nothing recorded changes meaning and
# replay reads nothing new. Built on main 14b2ed09ab as mvp-0.53 and renumbered
# mvp-0.54 when main (TE3b's mvp-0.53) was merged in; ONE constant.
PHONE_PROBES_ALGORITHM_VERSION = "mvp-0.54"

# mvp-0.55 (instruct hand-off IH5; owner decision 2026-11-08,
# docs/specs/spec_instruct_handoff_v1.md §7a), on top of phone V3's mvp-0.54
# (the chain stays linear). A failed policy's share in the router objective's
# mix goes to the OTHER policy, no longer to staged: with the LLM policy failed
# the numeric policy takes 1.0, with the numeric one failed the LLM policy takes
# 1.0, with both failed staged keeps 1.0 (the floor epsilon applies in every
# case, propensities stay exact, staged's pick is still logged and still orders
# the support and breaks ties). The reason is that staged never picks a lesson.
# Kill switch ``[router_objective] failure_share_to_other_policy`` (off, or below
# the tag: mvp-0.54's mix byte for byte). No migration. Expected mvp-0.55 at
# landing (ONE constant; renumber if another successor lands first).
FAILURE_SHARE_ALGORITHM_VERSION = "mvp-0.55"

# mvp-0.56 (the placement hole; owner decision 2026-11-09, "Fix the placement
# bug with a successor"; docs/reviews/placement-stranded.md). Under placement an
# answered item with no due time on an LO with no evidence (a primed first
# answer, a held grade) reached neither new material nor the routine queue, so
# an LO with nothing else left never came back; the opening episode that used to
# keep it served is one placement ignores. Such an item now starts as learning,
# with the same floor and order as new material, once a selector outside the
# scheduler's timing may offer it (no cold follow-up holds it, its answer not
# revealed within the cold retrieval delay). Serving only: nothing recorded
# changes meaning and replay reads nothing new. Kill switch
# ``placement.unevidenced_return`` (off, or below the tag: mvp-0.55's serving
# exactly). No migration. Placed after instruct/handoff's mvp-0.55 (IH5) when
# main was merged in; its predecessor in the chain is mvp-0.55. ONE constant.
UNEVIDENCED_RETURN_ALGORITHM_VERSION = "mvp-0.56"

# mvp-0.57 (slip or gap SG1 + SG2; docs/specs/spec_slip_vs_gap_v1.md; owner decisions 2026-11-09), on top of the
# placement hole's mvp-0.56 (the chain stays linear). SG1: a per-topic ``miss_cause`` sensor (the latest missed cold check's
# diagnosis cause-class probabilities, its stored surprise and its status) frozen in the router objective's trace, on the
# lesson offer's card record and on the LLM policy's card, with no change to any numeric value. SG2: the numeric
# policy's lesson and repair effect slopes split by the miss's cause, ``p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ``,
# with ``p_gap`` calibrated by a learned surprise coefficient (prior 0). Kill switches ``[router_objective]
# miss_cause_sensor`` and ``miss_cause_in_value`` (SG2 needs SG1; off, or below the tag: mvp-0.56's trace, card and
# values byte for byte). No migration. Built on instruct/handoff (mvp-0.55) as mvp-0.57, ONE constant: the placement
# fix (mvp-0.56) landed before it and became its predecessor when main was merged in.
SLIP_GAP_ALGORITHM_VERSION = "mvp-0.57"

# mvp-0.58 (the figure wait estimate; owner decision 2026-11-10, "W from pressed builds with a prior; cost from
# foreground minutes only"; docs/reviews/figure-wait-estimate.md), on top of slip or gap's mvp-0.57. The figure
# pre-builder's W (the minutes a press would wait, the quick tiers) read every figure author call, 20 of 22 of them its
# own background builds on the owner's vault, and its blocked minutes counted its own failed calls as foreground: the
# ``owner_kind`` filters meant to leave them out never matched a receipt. W is now the pressed builds' calls shrunk
# toward the other calls by a prior worth one measurement, and the blocked minutes count foreground calls only (the
# decision rows' ``prefetch_decision_v2``). Kill switch ``figures.prefetch.pressed_waits`` (off, or below the tag:
# ``prefetch_decision_v1``, mvp-0.57's numbers exactly). Nothing recorded changes meaning and replay reads nothing new
# (the decisions are a raw ledger, each row naming its model version). No migration. ONE constant.
FIGURE_WAIT_ALGORITHM_VERSION = "mvp-0.58"

# mvp-0.59 (the facet-belief fixes; refactor bug ledger D-1, D-3, D-5, D-6, owner rule 2026-11-12;
# docs/reviews/refactor-dfb.md), on top of the figure wait estimate's mvp-0.58. The canonical facet belief (KM2's
# projection) now resets a facet's failure streak on a success (D-1), scales a transfer-tier criterion's evidence by
# ``teach_back.transfer_evidence_multiplier`` as the legacy path did (D-3), and books a total failure's coverage where
# its failure mass lands (D-6); the per-LO facet uncertainty the attempt path computes is written again, on canonical
# facet ids, and read by the follow-up ranking, goals and diagnostics (D-5). It changes the projection and what is
# derived from it, so activation is a whole-vault rebuild under the tag. Kill switch
# ``facet_diagnostic.canonical_belief_fixes`` (off, or below the tag: mvp-0.58's belief and empty uncertainty reads
# exactly; a whole-vault rebuild records the switch it derived under). No migration. ONE constant.
FACET_BELIEF_FIX_ALGORITHM_VERSION = "mvp-0.59"

# mvp-0.60 (the grade channel fixes; refactor bug ledger D-36, D-52, owner decision 2026-11-17 "I accept the rebuild
# fix's value changes, ship it as mvp-0.60"; docs/reviews/refactor-adfix3.md), on top of the facet-belief fixes'
# mvp-0.59. Replay re-applied each practice answer through the live write path, which minted a fresh observation and
# grade chain (an observation, a raw grade event, an interpretation, four measurement events) at every rebuild, so
# history grew by one chain per answer per rebuild and an owner's adjudication or review flag was left on a copy the
# projection no longer reads. Replay now reuses the answer's newest observation and appends a raw grade event only
# when the grade changed and an interpretation only when it differs from the head (never over an adjudicated, flagged
# or quarantined head unless the grade changed). The first rebuild under the tag re-reads, once, the answers whose
# live observation earlier rebuilds never superseded (D-55), which moves canonical facet cells, so activation is a
# whole-vault rebuild. Below the tag a rebuild writes the grade channel exactly as mvp-0.59 does. No kill switch
# (owner rule 2026-11-16). No migration. ONE constant.
GRADE_CHANNEL_FIX_ALGORITHM_VERSION = "mvp-0.60"

# mvp-0.61 (the evidence reading fixes; refactor bug ledger G3-1, ER-2, K5-3, K5-8, K5-11, K5-12;
# docs/reviews/algorithm-mvp-0.61.md), on top of the grade channel fixes' mvp-0.60. Six readings of recorded evidence
# change, each on this tag and later and exactly as before below it: a probe answer given after its feedback was shown
# or after a reveal updates no belief in its episode and qualifies nothing, as the discriminating observation already
# refused it as not independent (G3-1); a criterion row marked unassessed is no assessed zero to either diagnosis
# reader (ER-2); a replacement grade replays under its own source, and a replaced exam answer reaches the exam channel
# (K5-11); a grader confidence of 0.0 stays 0.0 on replay (K5-12); a certificate probe whose every criterion is
# unassessed abstains (K5-3, policy v2); a request for an easier or harder variant is no FSRS review of its source item
# and leaves its forgetting clock, memory and due date as they were (K5-8). What a rebuild derives moves, so
# activation is a whole-vault rebuild. No kill switch (owner rule 2026-11-16). No migration. ONE constant.
EVIDENCE_READING_FIX_ALGORITHM_VERSION = "mvp-0.61"

# mvp-0.62 (the committed-check credit; teacher v2 ledger TV2-1, spec_teacher_v2 §7.4;
# docs/reviews/algorithm-mvp-0.62.md), on top of the evidence reading fixes' mvp-0.61. The router valued a lesson
# offer's committed delayed check as a full practice attempt at its due day, whether or not the simulated learner came
# back or a question existed, and charged it no minutes. At this tag a new lesson offer carries its check's delivery
# sensors (the as-of cold-completion statistics with the one-trial seed, whether a question exists now, the plan's
# minutes for one check), and every rollout of a new decision prices the check through
# ``router_objective.check_value``: delivered with that probability, only on a simulated return, on the session's
# clock, from streams of its own. Decisions, plans, receipts and commitments already recorded keep their meaning; only
# new decisions move, so activation is the idempotent projection. No kill switch (owner rule 2026-11-16). No
# migration. ONE constant.
COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION = "mvp-0.62"

# mvp-0.63 (a section's end finishes it; docs/reviews/algorithm-mvp-0.63.md), on top of the committed-check credit's
# mvp-0.62. Which event writes a section's completion changes, and with it when a plan's reading block ends and when
# the section's reading exposure is recorded. At this tag an acknowledged end observation (the section's last readable
# passage shown during the learner's own reading, as the progress report records it) finishes the section once,
# through the same operation as the learner's explicit "I've read this section"; closing a quick check and choosing
# what to do with its idea no longer finish it. The completion stores its cause and the tag it was written under.
# Completions, ends and exposures already recorded keep their meaning, and no end recorded before the upgrade finishes
# anything; only new events move, so activation is the idempotent projection. No kill switch (owner rule 2026-11-16).
# ONE constant.
SECTION_END_ALGORITHM_VERSION = "mvp-0.63"

# mvp-0.64 (an untaken repair episode ends; docs/reviews/algorithm-mvp-0.64.md), on top of the section end's mvp-0.63.
# A remediation episode in ``prescribed`` or ``treatment`` whose primed attempt was never taken had no end, so its
# reserved cold item was withheld from Today's queue only while a cold retry stood open. At this tag the per-attempt
# sweep ends such an episode as ``abandoned`` (an existing state) once the item of the miss it repairs has its next
# ordinary review due, which frees the cold item as a withdrawn retry frees it, and the routine queue withholds the
# cold item for as long as the episode is open. Episodes, tasks and outcomes already recorded keep their meaning; an
# episode open at the upgrade is ended by the first sweep after it, never back-dated. Only new events move, so
# activation is the idempotent projection. No kill switch (owner rule 2026-11-16). No migration. ONE constant.
UNTAKEN_EPISODE_END_ALGORITHM_VERSION = "mvp-0.64"

# mvp-0.65 (same-second grades replay in the order they were applied; docs/reviews/algorithm-mvp-0.65.md), on top of
# the untaken repair episode's end, mvp-0.64. An attempt's id is minted when its grading starts and its created_at
# (whole seconds) when its grade is applied, so two grades of one learning object applied in one second can carry ids
# in the opposite order from their application; every prefix reader ordered the ledger by (created_at, id), so replay
# folded them in another order than live had and rebuilt other mastery. At this tag apply_attempt reserves an
# application sequence inside its own write transaction (attempt_application_order, migration 261), and every prefix
# reader orders by (created_at, sequence, id) (``learnloop.db.attempt_order``): occurrence time stays first and the
# sequence breaks ties inside one second only. The upgrade ranks the attempts applied before it in the predecessor's
# order ('legacy_order_unknown': their real order was never recorded) and then rebuilds the whole vault, so a
# historical tie keeps the predecessor's reading and only new ties are exact. No kill switch (owner rule
# 2026-11-16). ONE constant.
APPLICATION_ORDER_ALGORITHM_VERSION = "mvp-0.65"

# mvp-0.66 (retired items replay at the right point in history; docs/reviews/algorithm-mvp-0.66.md), on top of the
# application order, mvp-0.65. A grade's relative coverage and its legacy breadth denominator count the facets of its
# learning object's ACTIVE items, and nothing in the attempt ledger records when a sibling was retired, parked,
# superseded or removed: replay read today's flags for the whole history, so an unattempted retired sibling looked
# closed before its closure and an attempted one open after it. At this tag the live grade application reads the set
# once, uses it for both, and stores it with the attempt (attempt_lifecycle_inputs, migration 263); replay and regrade
# read it back, iterating it in its canonical (sorted) order live and on replay alike. The upgrade records, for every
# attempt without a row, the set the predecessor's own replay reads at it ('legacy_reconstructed', from the lifecycle
# as it stood at the upgrade: never observed history), freezes it, then rebuilds the whole vault. No kill switch
# (owner rule 2026-11-16). ONE constant.
LIFECYCLE_INPUTS_ALGORITHM_VERSION = "mvp-0.66"

# mvp-0.67 (the mastery seed a topic started from is recorded and replayed; docs/reviews/algorithm-mvp-0.67.md), on top
# of the lifecycle inputs, mvp-0.66. A learning object's mastery row is created once, from the learner claims then in
# force, and a later claim that does not re-anchor (a changed starting level, a manual claim) leaves it as it is, by
# the profile setter's explicit contract. Replay instead seeded a practised learning object from the claims made before
# its first attempt and an attempt-free one from the claims in force at rebuild time, so a rebuild after such a claim
# disagreed with live. At this tag the writer that first persists a learning object's mastery (vault sync, an attempt
# on a learning object without a row, a re-anchoring claim on one) records every claim it considered, in the same
# transaction (mastery_seed_inputs, migration 265); replay and the attempt-free rebuild seed from the record and apply
# only the re-anchoring claims made after it. A starting-level change still affects future materializations only. The
# upgrade records, for every learning object without a row, the claims the predecessor's own rebuild seeds it from
# ('legacy_reconstructed': never observed history), freezes them, then rebuilds the whole vault. No kill switch (owner
# rule 2026-11-16). ONE constant.
MASTERY_SEED_ALGORITHM_VERSION = "mvp-0.67"

# mvp-0.68 (a scratchpad's words are learner text; docs/reviews/algorithm-mvp-0.68.md), on top of the mastery seeds,
# mvp-0.67. The Reader workbench's pads (migration 262) held the learner's own writing as workflow data that nothing
# read. At this tag a committed block version of the learner's own words (a text or note block, an ink block's
# transcription or its correction) is emitted, once, as a learner text of source kind 'pad_text' (migration 266),
# through ``learnloop.pads.emission`` alone: the gap pipeline reads it as any learner text, and a gap it names can
# become a hypothesis and steer routing, the companion and the Teacher, never a check brought forward, a placement
# observation, mastery, readiness or certification (``NON_SERVING_SOURCE_KINDS``). Quoted blocks, sketches, cells and
# stubs emit nothing; an edit's new words supersede the gaps read from the old ones; a removed block retracts its
# gaps; the gap rows stay. Nothing already derived moves: no pad text was ever read before the tag. No kill switch
# (owner rule 2026-11-16). ONE constant.
PAD_TEXT_ALGORITHM_VERSION = "mvp-0.68"

# mvp-0.69 (inline cold checks in the Reader; docs/reviews/algorithm-mvp-0.69.md), on top of the pad text, mvp-0.68.
# A due "Check once" can be administered where the learner reads (surface 'reader_inline', migration 270): the item
# Today's check view would serve, its frozen contract, the attempt through the one attempt service, settlement as for
# any qualifying attempt. What changes: a new serving surface whose attempts answer checks; an administration lock
# Today honours (while one is open its check is not served as the check there); and exposure written at once by a new
# writer: opening a veil writes a 'source_review' reveal sized by the opened text's overlap with each candidate's key
# (the Check once rule then decides whether the answer is practice). No existing row changes meaning. No kill switch
# (owner rule 2026-11-16). ONE constant.
INLINE_CHECK_ALGORITHM_VERSION = "mvp-0.69"

# The probe router (refactor G2; docs/reviews/refactor-g2-design.md, docs/reviews/algorithm-probe-router.md), on top of
# the inline checks, mvp-0.69. The action router is the one decider of whether a probe is asked after a miss. On the automatic
# follow-up lane the decision comes before the probe is written, so the router cannot value its answer pattern and the
# probe earns no information credit (the design's decision 1; the owner's option f of 2026-11-20): it is no option of
# either policy, and the mix decides between no intervention and a lesson where one is offered. Beside the mix, the
# probe coin asks the probe now, feedback held, on a randomized share of eligible misses (``router_objective.
# probe_coin``), at the stop coin's rate (the owner's decision of 2026-11-23: derived from an existing arm, not a new
# constant), with its own seed, an exact served distribution and its own assignment row. No room to wait, no plan and
# the router switched off take the same coin instead of asking the probe deterministically; a no-plan decision is
# logged. Hard refusals still come first. Nothing already derived moves. No kill switch (owner rule 2026-11-16). ONE
# constant: renumbering the tag is this line (the chain, the sets and the predicate follow it).
PROBE_ROUTER_ALGORITHM_VERSION = "mvp-0.70"
# The difficulty label leaves mastery and surprise (docs/reviews/algorithm-mvp-0.71.md), on top of the probe
# router, mvp-0.70. The IRT seam stops reading an item's or a learning object's authored or estimated difficulty
# label (and the dormant empirical-Bayes difficulty): mastery's prediction has no item term, the priming offset kept.
# Surprise scores the answer against adaptive difficulty's forecast made before it, from the serve-time receipt of
# the answer's plan presentation, else the grade-time receipt every graded answer now records
# (``adaptive_difficulty.grade_forecast``), else mastery's own prediction; the row says which. Bayesian surprise still
# describes the mastery update; FSRS never reads AD. History is re-derived by a whole-vault rebuild: old answers have
# no grade-time receipt and fall back to mastery, marked. No kill switch (owner rule 2026-11-16). One constant:
# renumbering the tag is this line.
LABEL_RETIRED_ALGORITHM_VERSION = "mvp-0.71"
# Effective mastery curves for the lesson-weight fit (L4-2; docs/reviews/algorithm-mvp-0.72.md), on top of the
# difficulty label's retirement, mvp-0.71.
LESSON_WEIGHT_CURVES_ALGORITHM_VERSION = "mvp-0.72"
# The difficulty label retirement's corrections (docs/reviews/algorithm-mvp-0.73.md), on top of the lesson-weight
# curves, mvp-0.72: surprise against AD's forecast is scored from the forecast's probability itself (the configured
# clip once, no inverse through ``b`` and no division by the discrimination), also where mastery's IRT link is off,
# and every surprise row names its source; a delayed check's draw among tied items is seeded per decision node. One
# constant: renumbering the tag is this line.
FORECAST_SCORING_ALGORITHM_VERSION = "mvp-0.73"
# A bound answer scores the receipt of its recorded selection view and answered revision.
SELECTED_FORECAST_ALGORITHM_VERSION = "mvp-0.74"
# The lesson-weight fit reads what mastery recorded instead of inferring it (docs/reviews/algorithm-mvp-0.75.md;
# design: docs/reviews/refactor-l42-fit-redesign.md): each mastery application records its facts (applied or not,
# prior, instant, score, curve, weight, interpretation noise, floor, posterior) in the attempt's payload, observed at
# whole seconds live as in replay; the fit chains those facts, and every reader of a lesson outcome takes one order.
# One constant: renumbering the tag is this line.
LESSON_WEIGHT_FACTS_ALGORITHM_VERSION = "mvp-0.75"
# An answer mastery did not apply (its recorded application says so, e.g. a verified alternative with every criterion
# unassessed) resolves no lesson check in any outcome reader (docs/reviews/algorithm-mvp-0.76.md).
# One constant: renumbering the tag is this line.
OUTCOME_FIXES_ALGORITHM_VERSION = "mvp-0.76"

# The linear successor chain on the mvp-0.8 projection namespace, oldest
# first. Each successor means its predecessor's semantics PLUS its own, so
# every gate below is "this tag or any later one". A successor appends its tag
# here (one line; ``tests/goldens/effective_defaults.toml`` then shows the new
# ``algorithm_version`` line): LATEST_ALGORITHM_VERSION and every version set
# follow, so a new vault at the new tag keeps the split and placement.
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
    INTENT_ALGORITHM_VERSION,
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
    READING_PATH_PLAN_ALGORITHM_VERSION,
    CLAIM_FIXES_ALGORITHM_VERSION,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
    ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION,
    COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
    READER_FOLLOWUPS_ALGORITHM_VERSION,
    DELIVERABLE_PLAN_ALGORITHM_VERSION,
    TEACHER_ALGORITHM_VERSION,
    HELP_FOLD_ATTACH_ALGORITHM_VERSION,
    LESSON_SUGGESTIONS_ALGORITHM_VERSION,
    DATA_CAPTURE_ALGORITHM_VERSION,
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    ROUTER_OBJECTIVE_ALGORITHM_VERSION,
    ROUTER_CALIBRATION_ALGORITHM_VERSION,
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    ROUTER_FOLLOWUPS_ALGORITHM_VERSION,
    TEACHER_PROBES_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    PHONE_PROBES_ALGORITHM_VERSION,
    FAILURE_SHARE_ALGORITHM_VERSION,
    UNEVIDENCED_RETURN_ALGORITHM_VERSION,
    SLIP_GAP_ALGORITHM_VERSION,
    FIGURE_WAIT_ALGORITHM_VERSION,
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    GRADE_CHANNEL_FIX_ALGORITHM_VERSION,
    EVIDENCE_READING_FIX_ALGORITHM_VERSION,
    COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION,
    SECTION_END_ALGORITHM_VERSION,
    UNTAKEN_EPISODE_END_ALGORITHM_VERSION,
    APPLICATION_ORDER_ALGORITHM_VERSION,
    LIFECYCLE_INPUTS_ALGORITHM_VERSION,
    MASTERY_SEED_ALGORITHM_VERSION,
    PAD_TEXT_ALGORITHM_VERSION,
    INLINE_CHECK_ALGORITHM_VERSION,
    PROBE_ROUTER_ALGORITHM_VERSION,
    LABEL_RETIRED_ALGORITHM_VERSION,
    LESSON_WEIGHT_CURVES_ALGORITHM_VERSION,
    FORECAST_SCORING_ALGORITHM_VERSION,
    SELECTED_FORECAST_ALGORITHM_VERSION,
    LESSON_WEIGHT_FACTS_ALGORITHM_VERSION,
    OUTCOME_FIXES_ALGORITHM_VERSION,
)


def successors_from(version: str) -> frozenset[str]:
    """``version`` and every later tag in :data:`SUCCESSOR_CHAIN`."""

    return frozenset(SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(version):])


# The oldest tag a vault is opened at (ADR-019): one below it is refused at open until upgraded
# (``learnloop.version_floor``). Moving the floor is this one line.
OLDEST_SUPPORTED: str = FIGURE_WAIT_ALGORITHM_VERSION


# Versions whose serving includes F2 placement (behind ``placement.enabled``).
# Every later successor keeps placement; gates must use this set, never
# equality against PLACEMENT_ALGORITHM_VERSION.
PLACEMENT_VERSIONS: frozenset[str] = successors_from(PLACEMENT_ALGORITHM_VERSION)

# Versions whose small judgments the Decider decides (Tier 1, behind one
# ``decider_routes`` switch per judgment).
DECIDER_TIER1_VERSIONS: frozenset[str] = successors_from(DECIDER_TIER1_ALGORITHM_VERSION)

# Versions whose router objective gives a failed policy's share to the other
# policy instead of staged (instruct hand-off IH5), behind
# ``[router_objective] failure_share_to_other_policy``. Every later successor
# keeps it; gates must use this set, never equality.
FAILURE_SHARE_VERSIONS: frozenset[str] = successors_from(FAILURE_SHARE_ALGORITHM_VERSION)

# Versions whose figure pre-builder reads W from pressed builds with a prior and the blocked minutes from foreground
# calls (``prefetch_decision_v2``), behind ``figures.prefetch.pressed_waits``. Every later successor keeps it; gates
# must use this set, never equality.
FIGURE_WAIT_VERSIONS: frozenset[str] = successors_from(FIGURE_WAIT_ALGORITHM_VERSION)

# Versions whose canonical facet belief carries the facet-belief fixes and whose per-LO facet uncertainty is written
# and read on canonical vaults, behind ``facet_diagnostic.canonical_belief_fixes``. Every later successor keeps them;
# gates must use this set, never equality.
FACET_BELIEF_FIX_VERSIONS: frozenset[str] = successors_from(FACET_BELIEF_FIX_ALGORITHM_VERSION)

# mvp-0.59 also holds the robust completion gate fixes (refactor bug ledger D-39; docs/reviews/refactor-k9.0b.md),
# behind ``probe.episode.robust_gate_fixes``: a fragile pick no longer ends an unstable probe episode (only a fragile
# stop does), and the robust selector ranks distinct instruments, so a card's second item is not its winner's rival.
# They were made before any vault was known to hold mvp-0.59, so they share its tags; were a vault already there, a
# new tag would replace this one line (``diagnosis.probe_robust.robust_gate_fixes_on`` is the only reader).
ROBUST_GATE_FIX_VERSIONS: frozenset[str] = FACET_BELIEF_FIX_VERSIONS

# Versions whose replay reuses each practice answer's newest observation and appends to its grade channel only what
# changed (the grade channel fixes; ``attempts.grade_resolution.grade_channel_fixes_on`` is the only reader). Every
# later successor keeps them; gates must use this set, never equality.
GRADE_CHANNEL_FIX_VERSIONS: frozenset[str] = successors_from(GRADE_CHANNEL_FIX_ALGORITHM_VERSION)

# Versions that carry the evidence reading fixes (G3-1, ER-2, K5-3, K5-11, K5-12). Every later successor keeps them;
# gates must use this set, never equality, and read it through :func:`evidence_reading_fixes_on`.
EVIDENCE_READING_FIX_VERSIONS: frozenset[str] = successors_from(EVIDENCE_READING_FIX_ALGORITHM_VERSION)


def evidence_reading_fixes_on(config: object) -> bool:
    """The evidence reading fixes (mvp-0.61), gated by the vault's tag alone (no kill switch): below it every one of
    their readings is mvp-0.60's exactly. ``config`` is a vault's config (anything whose algorithms section names its
    algorithm version); the one predicate, so the call sites cannot disagree on the tag."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in EVIDENCE_READING_FIX_VERSIONS

# Versions whose new lesson offers carry their committed checks' delivery sensors and whose rollouts price the checks
# by them (the committed-check credit). Every later successor keeps it; gates must use this set, never equality, and
# read it through :func:`committed_check_delivery_on`.
COMMITTED_CHECK_DELIVERY_VERSIONS: frozenset[str] = successors_from(COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION)


def committed_check_delivery_on(config: object) -> bool:
    """The committed-check credit (mvp-0.62), gated by the vault's tag alone (no kill switch): below it a lesson offer's
    record, its numeric action and every rollout are mvp-0.61's exactly. ``config`` is a vault's config; the one
    predicate the offer builder and the chooser both read, so they cannot disagree on the tag."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in COMMITTED_CHECK_DELIVERY_VERSIONS

# Versions where a section's end finishes it and a quick check's close does not. Every later successor keeps it; gates
# must use this set, never equality, and read it through :func:`section_end_on`.
SECTION_END_VERSIONS: frozenset[str] = successors_from(SECTION_END_ALGORITHM_VERSION)


def section_end_on(config: object) -> bool:
    """A section's end finishes it (mvp-0.63), gated by the vault's tag alone (no kill switch): below it a section is
    finished exactly as at mvp-0.62 (any completion the Reader sends, its check's close included; an end finishes
    nothing). ``config`` is a vault's config; the one predicate the progress report reads."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in SECTION_END_VERSIONS

# Versions where an untaken repair episode ends at its item's next ordinary review and the routine queue withholds its
# cold item while it is open. Every later successor keeps it; gates must use this set, never equality, and read it
# through :func:`untaken_episode_end_on`.
UNTAKEN_EPISODE_END_VERSIONS: frozenset[str] = successors_from(UNTAKEN_EPISODE_END_ALGORITHM_VERSION)


def untaken_episode_end_on(config: object) -> bool:
    """An untaken repair episode ends (mvp-0.64), gated by the vault's tag alone (no kill switch): below it such an
    episode stays open and the routine queue withholds its cold item only while a cold retry is open, exactly as at
    mvp-0.63. ``config`` is a vault's config; the one predicate the sweep and the routine exclusions read."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in UNTAKEN_EPISODE_END_VERSIONS

# Versions where apply_attempt reserves each attempt's application sequence and the ledger's prefix readers order by it
# inside one created_at. Every later successor keeps it; gates must use this set, never equality, and read it through
# :func:`application_order_on` (``learnloop.db.attempt_order.attempt_order_for`` is the readers' one door).
APPLICATION_ORDER_VERSIONS: frozenset[str] = successors_from(APPLICATION_ORDER_ALGORITHM_VERSION)


def application_order_on(config: object) -> bool:
    """Same-second grades fold in the order they were applied (mvp-0.65), gated by the vault's tag alone (no kill
    switch): below it no sequence is reserved and every reader orders the ledger by ``(created_at, id)``, exactly as
    at mvp-0.64. ``config`` is a vault's config."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in APPLICATION_ORDER_VERSIONS

# Versions where a grade application's required facet set is captured with its attempt and replay reads it back.
# Every later successor keeps it; gates must use this set, never equality, and read it through
# :func:`lifecycle_inputs_on`.
LIFECYCLE_INPUTS_VERSIONS: frozenset[str] = successors_from(LIFECYCLE_INPUTS_ALGORITHM_VERSION)


def lifecycle_inputs_on(config: object) -> bool:
    """A grade application's required facet set is the one captured with its attempt (mvp-0.66), gated by the vault's
    tag alone (no kill switch): below it nothing is captured and every application reads today's item lifecycle,
    exactly as at mvp-0.65. ``config`` is a vault's config."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in LIFECYCLE_INPUTS_VERSIONS

# Versions where the seed a learning object's mastery started from is recorded where it was first persisted and replay
# seeds from it. Every later successor keeps it; gates must use this set, never equality, and read it through
# :func:`mastery_seed_on`.
MASTERY_SEED_VERSIONS: frozenset[str] = successors_from(MASTERY_SEED_ALGORITHM_VERSION)


def mastery_seed_on(config: object) -> bool:
    """The mastery seed a learning object started from is recorded and replayed (mvp-0.67), gated by the vault's tag
    alone (no kill switch): below it nothing is recorded and replay seeds a practised learning object from the claims
    made before its first attempt and an attempt-free one from the claims in force now, exactly as at mvp-0.66.
    ``config`` is a vault's config."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in MASTERY_SEED_VERSIONS

# Versions where a committed pad block of the learner's own words is emitted as a ``pad_text`` learner text. Every
# later successor keeps it; gates must use this set, never equality, and read it through :func:`pad_text_on`.
PAD_TEXT_VERSIONS: frozenset[str] = successors_from(PAD_TEXT_ALGORITHM_VERSION)


# Versions where a due check may be administered inline in the Reader and Today honours the administration lock. Every
# later successor keeps it; gates must use this set, never equality, and read it through :func:`inline_checks_on`.
INLINE_CHECK_VERSIONS: frozenset[str] = successors_from(INLINE_CHECK_ALGORITHM_VERSION)


def inline_checks_on(config: object) -> bool:
    """Inline checks (mvp-0.69), gated by the vault's tag alone (no kill switch): below it every ``check.*`` RPC
    refuses and Today ignores the lock, exactly as at mvp-0.68. ``config`` is a vault's config."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in INLINE_CHECK_VERSIONS


def pad_text_on(config: object) -> bool:
    """A scratchpad's committed words are learner text (mvp-0.68), gated by the vault's tag alone (no kill switch):
    below it a pad emits nothing, exactly as at mvp-0.67. ``config`` is a vault's config."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in PAD_TEXT_VERSIONS

# Versions where the router decides the automatic lane's probe and an unwritten probe is asked only by the probe coin.
# Every later successor keeps it; gates must use this set, never equality, and read it through
# :func:`probe_router_on`.
PROBE_ROUTER_VERSIONS: frozenset[str] = successors_from(PROBE_ROUTER_ALGORITHM_VERSION)


# Versions where the difficulty label is retired from mastery and surprise. Gates read it through
# :func:`label_retired`.
LABEL_RETIRED_VERSIONS: frozenset[str] = successors_from(LABEL_RETIRED_ALGORITHM_VERSION)


def label_retired(algorithm_version: str | None) -> bool:
    """Mastery's IRT seam reads no difficulty label and surprise reads adaptive difficulty's forecast (the retirement's tag);
    below it, the predecessor's seam exactly. Takes the vault's tag (the seam's callers hold only the mastery
    section of the config)."""

    return algorithm_version in LABEL_RETIRED_VERSIONS


# Versions where surprise is scored from AD's forecast probability directly and a delayed check's tie draw is seeded
# per decision node. Gates read it through :func:`forecast_scoring_fixed`.
FORECAST_SCORING_VERSIONS: frozenset[str] = successors_from(FORECAST_SCORING_ALGORITHM_VERSION)
SELECTED_FORECAST_VERSIONS = successors_from(SELECTED_FORECAST_ALGORITHM_VERSION)


def forecast_scoring_fixed(algorithm_version: str | None) -> bool:
    """The label retirement's corrections (their tag): below it mvp-0.72's surprise scoring and delayed-check seeds
    exactly. Takes the vault's tag."""

    return algorithm_version in FORECAST_SCORING_VERSIONS


def probe_router_on(config: object) -> bool:
    """The router decides the automatic lane's probe and an unwritten probe is asked only by the probe coin (the probe
    router's tag), gated by the vault's tag alone (no kill switch): below it the predecessor's follow-up decision
    exactly. ``config`` is a vault's config."""

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in PROBE_ROUTER_VERSIONS

LESSON_WEIGHT_CURVE_VERSIONS = successors_from(LESSON_WEIGHT_CURVES_ALGORITHM_VERSION)
# Versions where mastery records its application facts and the lesson-weight fit reads them (gates read it through
# :func:`mastery_facts_recorded`).
LESSON_WEIGHT_FACT_VERSIONS = successors_from(LESSON_WEIGHT_FACTS_ALGORITHM_VERSION)


OUTCOME_FIXES_VERSIONS = successors_from(OUTCOME_FIXES_ALGORITHM_VERSION)


def unapplied_answers_resolve_nothing(algorithm_version: str | None) -> bool:
    """An answer whose recorded mastery application says it was not applied is no lesson outcome (mvp-0.76); below it
    every outcome reader is mvp-0.75's. Takes the vault's tag."""

    return algorithm_version in OUTCOME_FIXES_VERSIONS


def forecast_clipped_after_shift(algorithm_version: str | None) -> bool:
    """Without mastery's IRT link, the forecast surprise is scored against is clipped by the configured clip once,
    after a primed answer's shift, as the IRT link already does (mvp-0.76, FR3-16); below it mvp-0.73's unclipped
    centre exactly. Takes the vault's tag."""

    return algorithm_version in OUTCOME_FIXES_VERSIONS


def inline_guard_reads_first_grade(algorithm_version: str | None) -> bool:
    """An inline answer's forecast eligibility reads the contract its original grade cites, never a regrade epoch's
    (mvp-0.76, FR3-11); below it the current epoch's contract, mvp-0.74's exactly. Takes the vault's tag."""

    return algorithm_version in OUTCOME_FIXES_VERSIONS


def retention_forecast_shares_allocation(algorithm_version: str | None) -> bool:
    """A landed node's retention forecast names the item the commitment's allocation gives it after the nodes landed
    before it, with that pick's propensity (mvp-0.76, FR3-15); below it each node's pick alone, mvp-0.73's exactly.
    Takes the vault's tag."""

    return algorithm_version in OUTCOME_FIXES_VERSIONS


def cutoff_reads_the_view(algorithm_version: str | None) -> bool:
    """The grade-time forecast's later-evidence guard reads, in the forecast's own read and through AD's view, only
    the visible answers the forecast read, by the time their grade became known (mvp-0.76, FR3-5); below it every raw
    grade's recorded time on a separate read, mvp-0.71's exactly. Takes the vault's tag."""

    return algorithm_version in OUTCOME_FIXES_VERSIONS


def mastery_facts_recorded(algorithm_version: str | None) -> bool:
    """Mastery records each application's facts, observed at whole seconds, and the lesson-weight fit and every
    reader of a lesson outcome read them in one order (the facts' tag); below it mvp-0.73's exactly. Takes the
    vault's tag."""

    return algorithm_version in LESSON_WEIGHT_FACT_VERSIONS


# The newest successor: the last tag in the chain. ``learnloop upgrade`` with
# no ``--to`` targets it, and new vaults start at it
# (``config.template.default_config_text``; owner decision 2026-10-12).
LATEST_ALGORITHM_VERSION: str = SUCCESSOR_CHAIN[-1]
