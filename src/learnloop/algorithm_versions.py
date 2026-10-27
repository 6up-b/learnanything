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
# it is another successor tag on the mvp-0.8 namespace. Kill switch:
# ``intent.enabled`` (off: every serve path and plan as the predecessor;
# the desktop control answers ``enabled: false``).
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
# learned_coupling, reading_opportunities, reading_self_check. It changes what
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
# would have chosen. Kill switch: ``reading_paths.plan_uses_path`` (off, or
# with the Guide's ``reading_paths.enabled`` off: every plan build exactly as
# the predecessor).
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
# it is a successor (playbook item 6), not an in-place amendment. Kill switch:
# ``replay.ledger_bounded`` (off: replay reads exactly as the predecessor).
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
# the mvp-0.8 namespace. Kill switch: ``ask.cold_help_converts`` (off, or
# below the tag: both rules exactly as the predecessor).
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
    INTENT_ALGORITHM_VERSION,
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
    READING_PATH_PLAN_ALGORITHM_VERSION,
    CLAIM_FIXES_ALGORITHM_VERSION,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
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

# Versions whose serving and Today plan read the learner's intent (behind
# ``intent.enabled``; daily-loop DL2). Every later successor keeps it; gates
# must use this set, never equality.
INTENT_VERSIONS: frozenset[str] = successors_from(INTENT_ALGORITHM_VERSION)

# Versions whose new-material slots AD's draw serves, whose generation names a
# feature point, and whose readiness numbers read AD's subject view (behind the
# six [adaptive_difficulty] switches). Every later successor keeps them; gates
# must use this set, never equality.
ADAPTIVE_DIFFICULTY_VERSIONS: frozenset[str] = successors_from(ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION)

# Versions whose field derivation reads the workbench's stuck steps and help
# before the first step (behind ``workbench.field_signals_enabled``; reader
# workbench RW2d). Every later successor keeps it; gates must use this set,
# never equality.
WORKBENCH_FIELD_SIGNALS_VERSIONS: frozenset[str] = successors_from(WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION)

# Versions whose plan's reading block follows the reading path (behind
# ``reading_paths.plan_uses_path``; reader workbench RW7b). Every later
# successor keeps it; gates must use this set, never equality.
READING_PATH_PLAN_VERSIONS: frozenset[str] = successors_from(READING_PATH_PLAN_ALGORITHM_VERSION)
# Versions whose learner claims seed and re-anchor mastery at their own time,
# with gap declarations re-anchoring, a mean-only warm merge and recency
# before pseudo-count in ties (behind ``mastery.claim_fixes_enabled``; LP-min
# (a)). Every later successor keeps them; gates must use this set, never
# equality.
CLAIM_FIXES_VERSIONS: frozenset[str] = successors_from(CLAIM_FIXES_ALGORITHM_VERSION)
# Versions whose replay reads the ledger bounded at the replayed attempt's
# position, as the live write saw it (behind ``replay.ledger_bounded``;
# rebuild equivalence). Every later successor keeps it; gates must use this
# set, never equality.
REPLAY_LEDGER_VERSIONS: frozenset[str] = successors_from(REPLAY_LEDGER_ALGORITHM_VERSION)

# Versions whose cold paths count only substantive questions as help and
# admit help taken on a cold follow-up as practice with help (behind
# ``ask.cold_help_converts``; Reader CA2). Every later successor keeps it;
# gates must use this set, never equality.
ONE_ASK_VERSIONS: frozenset[str] = successors_from(ONE_ASK_ALGORITHM_VERSION)

# Versions whose replace seam keeps the replaced learner claim as a
# superseded row (``learner_claims.superseded_by``) instead of deleting it.
# Every later successor keeps it; gates must use this set, never equality.
SUPERSEDED_CLAIMS_VERSIONS: frozenset[str] = successors_from(SUPERSEDED_CLAIMS_ALGORITHM_VERSION)

# The newest successor: the last tag in the chain. ``learnloop upgrade`` with
# no ``--to`` targets it, and new vaults start at it
# (``config.template.default_config_text``; owner decision 2026-10-12).
LATEST_ALGORITHM_VERSION: str = SUCCESSOR_CHAIN[-1]
