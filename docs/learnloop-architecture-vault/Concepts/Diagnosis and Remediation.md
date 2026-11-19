---
title: Diagnosis and Remediation
aliases:
  - Diagnostic System
  - Causal Learning Loop
status: active
doc_version: 1.0.0
implementation_version: mvp-0.61
last_reviewed: 2026-11-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/diagnosis
  - src/learnloop/attempts/attempts.py
  - src/learnloop/attempts/post_attempt.py
  - src/learnloop/attempts/grade_records.py
  - src/learnloop/followup_run
  - src/learnloop/followup_serve/workflow.py
  - src/learnloop/daily_plan/router_chooser.py
  - src/learnloop/daily_plan/objective_chooser.py
  - src/learnloop/scheduling/scheduler.py
  - src/learnloop/instructional/valuation.py
  - src/learnloop/source_retrieval/passage_cues.py
  - src/learnloop/evsi_calibration/live_report.py
  - src/learnloop/router_objective/picks.py
  - src/learnloop/ops/capture_report.py
  - src/learnloop/db/stores/hypothesis_marks.py
  - src/learnloop/db/repositories.py
  - src/learnloop/why
  - src/learnloop/provenance.py
  - src/learnloop/db/stores/provenance.py
  - src/learnloop/config/schema.py
  - src/learnloop/held_grades.py
  - apps/learnloop-tauri/src/screens/FeedbackScreen.tsx
  - migrations/200_probe_value_of_information_stop.sql
  - docs/specs/refactor_strategy_v3.md
tags:
  - learnloop/concept
  - learnloop/diagnosis
  - learnloop/causal
---

# Diagnosis and Remediation

Diagnosis tracks possible causes of a miss and connects them to probes and repairs.
A probe episode measures against a locked set of hypotheses; the causal repair lane tracks an unresolved cause factor and its repair choices.
Grading and diagnosis have separate roles: see [[ADR-016 Learner-blind grading with an asynchronous diagnoser]].

A passed cold check confirms the repair, including after other practice on the same facets. A failed cold check escalates it. Both verdicts require a final receipt qualifying the retrieval as cold and recording a passing administration window. A repair that showed more of the answer than its budget allows gets neither verdict. Without those facts, feedback gives the measured result and leaves the repair effect unestablished. The research receipt also checks for intervening retrieval when attributing the effect to the repair.

## Episode lifecycle

The `probe_episodes` row has five allowed statuses. Status and `completion_reason` are separate fields.

| Status | What writes it |
|---|---|
| `pending_items` | `probe_episodes.enter_episode` creates the row here; missing instruments, an unapproved grader, or an unavailable grading service can park it here. |
| `in_progress` | Entry, retargeting or adoption finds an eligible instrument; generation or approval can unpark a pending episode. |
| `complete` | `probe_completion.evaluate_completion` ends measurement with one of the reasons below. |
| `converted_to_tutoring` | `probe_controls.stop_diagnosing_and_teach` or `probe_completion.close_diagnostic_segment` ends an open measurement segment. |
| `abandoned` | `followup_serve.workflow._abandon_if_empty` closes an open episode with no observations and no presentation left that can produce one; it supplies no completion reason. |

Only `pending_items` and `in_progress` are open; the database permits one open episode per learning object (topic).
A pending episode does not block ordinary practice. Once observations exist, causal retargeting cannot replace the locked set.

### Completion rules

`probe_completion.evaluate_completion` runs only for `in_progress`. These are its stopping branches, in evaluation order.
A qualifying observation is one whose `eligible_for_completion` flag is true as the episode reads it (`probe_episodes.effective_episode_observations`, which every completion reader uses). From `mvp-0.61` an answer the discriminating observation's exposure test refuses (feedback shown or released before it, its causes displayed before it, or a reveal in its window; `probe_episodes.probe_answer_admissibility`) updates no belief and qualifies nothing, as a held grade does (`updates_belief` false, discount 0.0, `answer_exposed` in its contamination with the reason the test gave), also when it was hinted or tutored too: the instrument's likelihoods are for an answer produced cold, and after the feedback, the causes or a reveal the outcome no longer separates the causes. An observation recorded at the tag is written so (its posterior after equals its posterior before); one recorded before it reads so, its stored row untouched. The exposure neither closes the state segment nor changes the attempt's activity class. Below the tag the stored flags stand.

| Branch | Condition | `completion_reason` |
|---|---|---|
| Count limit | Qualifying observations reach the episode maximum and the count cap binds. | `observation_budget_exhausted` |
| Unstable posterior: same action | At least two plausible hypotheses all have an active route to the same first intervention. The rule must be enabled and have a qualifying observation. | `action_equivalent` |
| Unstable posterior: robust gate | The deciding gate abstains after enough qualifying observations on the pinned calibration channel. | `couldnt_reliably_distinguish` |
| Unstable posterior: value | A remaining eligible observation no longer pays for its minutes. | `value_of_information_stop` |
| Stable posterior: breadth met | The leading probability meets its threshold, the runner-up ratio meets its limit, and independent units, distinct surfaces and required facets meet the coverage contract. | `decision_stable` |
| Stable posterior: strong claim | With breadth still short, a strong prior claim has at least one qualifying observation and an observation targeting at least two facets. | `fast_path_strong_claim` |
| Stable posterior: same action | With breadth still short, the same enabled action-agreement test succeeds. | `action_equivalent` |
| Stable posterior: value | With breadth still short, another eligible observation no longer pays for its minutes. | `value_of_information_stop` |

Before the unstable value check, a qualifying episode with no remaining instrument parks in `pending_items` and records a generation need.
Value decides when its episode site is active, except in a calibration session that lifts that rule; otherwise the count cap binds.
The robust gate decides when value does not, or when `voi_stopping.robust_gate_with_value` is enabled.
With `probe.episode.robust_gate_fixes` enabled, only a fragile stop ends the episode: nothing left pays and the winning instrument is uncertain.
A fragile pick keeps asking, and the selector compares distinct instruments. With that switch off, every robust abstention ends the episode when the gate decides.
When value replaces the gate, an unstable value stop records the gate's counterfactual verdict in `former_cap.robust_completion_gate`.

### Hand-off to teaching

Outside the evaluator, the learner stop and segment closure both write reason `converted_to_tutoring`.
The stop settles committed answers, returns released feedback, saves a typed teaching decision, invalidates the active presentation and opens a `tutoring_transition` segment.
Segment closure also invalidates the presentation and opens that boundary; probe evidence calls it on instructional contamination.
At block end, a completed episode whose leading label is a gap rather than `robust_initial_grasp` routes to tutoring and saves the typed decision.
That block route leaves status `complete`; it opens a tutoring boundary. A later episode starts fresh rather than reopening a closed measurement.

## Who decides whether to probe

The generated follow-up lane chooses a question after a miss; the causal lane can also offer a quick check on feedback.
The decision is spread across these sites today. Expected information gain (EIG) means the predicted reduction in uncertainty; value checks price an observation against its time cost.

| Function or screen at this tip | What it decides | What it reads |
|---|---|---|
| `causal_probe_coherence.decide_probe`, called by `causal_orchestrator._status_for_factor` | The causal lane's offer, deferral or repair; the caller also withholds an unavailable or conflicting probe. | `probe_facts.probe_facts` (pure): repair classes, common repair, instrument separability, chance of changing repair, expected avoided teaching minutes and burden, recent burden, and the hard stops (machine checks, the learner's preference, the session budget). The verdict is `probe_facts.probe_verdict` over those facts and the resolved thresholds. The caller adds candidate state and episode conflict. |
| `followup_run.router._observe` | Observation only, never decides this lane. | Repair-class need. It logs the verdict only where the repair classes settle it (`probe_facts.settled_by_repair_classes`: a common repair, or one class); otherwise `decide_probe_absent`, because no instrument exists before the lane authors its probe. |
| `followup_run.router.hard_refusal` | Refuses a generated probe before generation. | Learner preference, blocking machine checks, then a foreign episode with observations, in that order; retains its own conflict check. |
| `followup_run.lanes.select_lane` | Chooses probe or practice. | Factors for the source attempt; at least two existing concrete rival hypotheses select probe, even if they share a repair. |
| `causal_attribution.open_rival_causes_factor` | Opens the generated lane's factor when needed. | No factor of any status already exists, grade not held, and at least two distinct episode keys among current concrete hypotheses. |
| `daily_plan.router_chooser.FollowupGate.decide_followup` / `daily_plan.objective_chooser.ObjectiveFollowupGate.decide_followup` | Timing and worth: ask now, wait or no intervention; the objective gate can also compare a lesson offer. | Plan and remaining block, workflow facts, feasible arms, model readiness and answers, configured mixture; the objective gate also values the alternatives. |
| `followups.evaluate_intervention_followup` | Suppresses automatic insertion when no candidate pays; a manual override can proceed. | Eligible follow-up slate, value decision, session context and manual-override flag. |
| `probe_presentations.probe_serving_block_reason`, `probe_presentations.probe_value_block_reason`, `probe_completion.evaluate_completion` | Serve another item, continue, park or complete an episode. | Session/onboarding counts and calibration lift; posterior, eligible instruments, time value, count and coverage contracts, action routes and robust channel. |
| `scheduling.scheduler._BuildAdmission.probe_score` | Ranks probe items in the queue, separately from the episode's information-rate ordering. | Predictive EIG / predictive prior entropy when adequate, otherwise hypothesis EIG / log(set size), then familiarity discount. |
| FeedbackScreen's `repairCaseId` callback in `apps/learnloop-tauri/src/screens/FeedbackScreen.tsx` | Whether to request live repair status and expose its offer. | Feedback receipt's divergent or incomplete repair-mapping flags; matched misconception or first causal hypothesis. |

Plan: arc G in `docs/specs/refactor_strategy_v3.md` makes diagnosis supply facts and hard stops, and the router the one decider of probe worth.
It also plans an ADR for that authority. This is planned work; the separate decisions above are present today.

## Expected information gain

`probe_episodes.eligible_instruments` excludes previously attempted items and their surface groups, and rejects inactive or unservable items.
With an adequate held-out predictive target set, it ranks by predictive information per expected second; otherwise it uses hypothesis EIG.
A family-redundancy penalty scales ranking, while the logged EIG stays unpenalized.

## Two beliefs over hypotheses

The episode posterior is a probability distribution replayed by `probe_episodes.episode_posterior`.
The causal lane keeps a different state: factor resolution and the support recorded by `causal_discrimination.record_probe_classification`.
They are not reconciled today.

| Aspect | Episode posterior | Causal factor and discriminating observation |
|---|---|---|
| Locked set and prior | Entry locks the episode set. Causal entry locks it without receipt support scores; ordinary entry builds topic hypotheses. | Commissioning locks the candidate set with receipt support scores; acceptance pins that set and its blind prediction bundle ids on the presentation. The sets have separate ids. |
| Update rule | Weighted Bayes: mix each outcome likelihood toward the current mixture likelihood by weight, multiply by current probability, then normalize. | Exact match against the pinned predictions; admitted support gives the matching measured hypothesis 1 and other measured hypotheses 0. Unmeasured hypotheses get no entry. |
| Evidence | Presented outcomes through frozen instrument snapshots plus incidental attempts; hints, contamination, exam type, dialogue share and trace mass can reduce weight. | The probe attempt's observed criterion features; automatic classification uses the deterministic rubric sensor. |
| Independence | Hints, tutor help and a non-diagnostic type discount weight. From `mvp-0.61` the discriminating observation's exposure test applies too (one function, `probe_answer_admissibility`): an exposed answer updates no belief and never qualifies. | Refuses admission if the production was assessed as non-independent; unassessed independence is stored as null. |
| Held grades | Checks the held-grade predicate in both presented and incidental channels; held presentations write inert observations. | The automatic sensor has no held-grade predicate; a route-rule hold has no assessed criterion features, so the sensor declines. |
| Timing and writers | `probe_evidence.record_episode_evidence` records the presented observation inside the attempt transaction, replays the posterior and persists misconception marginals with `probe_completion.persist_episode_beliefs`. | Live grade-keyed hooks call the classifier after the attempt commits, or during deferred block settlement. The observation writer resolves an open factor on an admitted `matched_single`; admitted open-set evidence does not resolve it. |
| Storage | `probe_observations` stores before/after values; reads replay the posterior. `learner_state_beliefs` holds registry-misconception marginals. | `causal_discriminating_observations` stores support, admission and `resolved_factor`; `unresolved_cause_factors` stores status and resolution observation ids. |
| Readers | Scheduler, episode completion, instructional valuation and passage cues. Valuation renormalizes over concrete labels; passage cues use the label's raw mass. | Scoreboard, causal health, calibration reports, factor deferral, router outcome joins, capture reports and hypothesis marks read the observations. Repair decisions also read factor state. |
| Later grade changes | A presented answer's outcome stays the submission's; regrades update grade interpretation, not that observation. Releasing a held observation does not change its false `updates_belief` flag. | An existing observation prevents automatic reclassification. |

Different priors and evidence rules can leave a factor resolved while the episode posterior still spreads its probability (from `mvp-0.61` the two lanes share the independence rule).

Both diagnosis readers of a stored grade, trace consistency (`causal_attribution._trace_consistency_states`) and the criterion receipt (`_criterion_receipt`), skip a criterion row marked unassessed (`canonical_projection.unassessed_evidence_row`) from `mvp-0.61`: a claim about that criterion is unverifiable (`unknown`, `claim_criteria_were_not_assessed`), and it is no assessable outcome (not passed, no full credit, no localization input), as in the canonical projection. Below the tag they read it as an assessed zero. Replay rematerializes the receipt from the stored rows, so the upgrade's rebuild moves these receipts.
Learner cause reports can also resolve a factor through `causal_attribution.record_unresolved_cause_self_report`, independently of episode replay.

## Module layout

Paths in this table are relative to `src/learnloop/`.

| Module | What it holds |
|---|---|
| `diagnosis/probe_episodes.py` | Episode lifecycle, locked sets, instrument eligibility and ranking, posterior replay and weighted Bayes. |
| `diagnosis/probe_completion.py` | Ordered stopping policy, value/robust gates, persisted marginals, segment closure and target-decision writes. |
| `diagnosis/probe_presentations.py` | Commit/serve/submit validation, frozen selection payloads and serving/value gates. |
| `diagnosis/probe_blocks.py` | Block boundaries, answer settlement, open-set review trigger and typed next route. |
| `diagnosis/probe_evidence.py` | Presented observations, activity/calibration facts and grade interpretation writes, including regrades. |
| `diagnosis/probe_controls.py` | Stop-and-teach, diagnostic client contract and read-only next-item peek. |
| `diagnosis/causal_reads.py` | Factor/receipt reads, repair mappings, deterministic value inputs and shared constants. |
| `diagnosis/probe_hard_stops.py` | Learner preferences and episode conflicts; documents the callers' different hard-stop orders. |
| `diagnosis/probe_facts.py` | The pure facts and hard stops of one possible probe, and the repair lane's verdict over them; imports nothing of LearnLoop. |
| `diagnosis/machine_checks.py` | Machine obligations, blocking mapping checks, missing-instrument work and sweeps. |
| `diagnosis/causal_cold_verification.py` | Delayed independent repair checks, carried task context, outcomes and expiry receipts. |
| `diagnosis/causal_discrimination.py` | Pinned-bundle classification, admission, factor resolution and automatic sensor declines. |
| `diagnosis/causal_orchestrator.py` | Repair-status decision, parameters, probe verdict receipts and machine-check obligations. |
| `diagnosis/probe_offer.py` | Accept/defer/teach actions, episode entry or retargeting and presentation pins. |
| `diagnosis/chain_records.py` | Pure decision-record builders and writers for diagnosis, hook failures, values, probe acceptance and classification declines. |
| `diagnosis/content_ids.py` | Shared content-addressed ids. |

Within the six probe-episode modules, imports follow core < completion < presentations < blocks < evidence and controls, where core is `diagnosis/probe_episodes.py`.
These edges are at module scope and point downward; blocks does not need a presentations import, and evidence and controls do not import each other.
For the causal lane, reads and hard stops sit below the orchestrator's decision. Cold verification uses reads; machine checks use reads and the cold sweep.
Discriminating observations use reads; offer actions use the decision and classification pin reader. The orchestrator does not import those offer actions.
`diagnosis/chain_records.py` imports no diagnosis module.

## What why can answer

[[Debug a decision]] describes `learnloop why` and inspection of its detail pointers.
The record contract is [[ADR-017 One decision record, one trace id, one entry point]].
Decision records keep ids, codes and numbers, without prompts or learner text; richer domain rows stay in their own tables.
The table distinguishes answers stored today from the missing causal verdict record. A domain-row answer may require inspecting that row: `why` does not expand every detail table.

| Question for one diagnostic decision | Answer from stored rows today |
|---|---|
| Which miss, grade and hold? | Answered: `grade` and child `grade_held` decision records, with the attempt id, grade numbers and hold reason. |
| Which diagnosis and arm? | Answered: `diagnosis` record, candidate alternatives by event/index and causal class, pointing to `attempt_diagnoses`. |
| Did the causal lane offer a check, and which rule withheld it? | Not yet as a trace record: `causal_probe_decision_receipts` stores the verb, reason, repair status and inputs, but no `probe_verdict` decision record carries the offer ladder. Arc G plans that record, including common repair, one repair class, machine checks, learner preference, burden, budget, missing instrument, episode conflict and value below cost. |
| What did the generated lane's router choose or refuse? | Answered: `followup_gate` record and `router_decisions`, including hard refusals, chosen arm and mixture. |
| Which candidate and locked set were pinned? | Answered: `probe_offer` record with candidate, hypothesis-set and bundle ids, and its `probe_presentations` detail pointer. |
| Was the answer classified or declined, and admitted? | Answered: `probe_classification` records a pinned causal decline; successful readings use `causal_discriminating_observations`, including admission and its reason. |
| Was the factor resolved, and by which writer? | Answered in domain rows: `unresolved_cause_factors` status, resolution observation ids or resolution kind/detail; the linked observation or learner report identifies the channel. |
| Why did the episode stop; which earlier rules passed? | Answered in `probe_episodes.completion_reason`, completion posterior and `completion_detail_json.rules_passed` for evaluator completions. |
| Which hook failed? | Answered: failed `diagnosis_step` record with step name, error class/location and, for grade-keyed hooks, `phase=grade_keyed`. |

The automatic classifier's decline codes are `pinned_bundles_empty`, `candidate_not_current`, `already_observed`, `no_deterministic_rubric`, `no_assessed_criterion`, `pinned_bundle_missing` and `declared_features_not_covered`.
`why attempt:<id>` reaches those declines by subject, including a decline written during settlement before the grade record exists.
No causal pin and an observation already owned by the same attempt are silent; an observation owned by another or unknown attempt gives `already_observed`.
The four grade-keyed failure names are `machine_check_sweep`, `cold_verification_wiring`, `probe_classification_hook` and `common_repair_consultation`.
`rules_passed` lists earlier evaluated rules in order; disabled gates are omitted. An exhausted but lifted count cap is also omitted.
Continuing writes no list; learner controls and direct segment/status changes omit it rather than reconstructing rules they did not evaluate.
