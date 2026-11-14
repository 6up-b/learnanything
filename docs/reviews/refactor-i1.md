# Refactor I1: grade application, a pure core

Branch `refactor/i1-grade-application-core`, based on main `68c61b9f1a`. Step I1 of arc I
(`docs/specs/refactor_strategy_v3.md` §2.9, finding F3). Structure track: every row a graded attempt writes, live
and on replay, stays identical to the last bit. Line numbers in §1-§3 are at the base, in
`src/learnloop/attempts/attempts.py` unless another file is named.

## 1. Step 0: the function, stage by stage

`_compute_resolved_grade_application` is `:4318-5115` (798 lines). Key: **R** read (repository, clock, config, vault),
**C** computation, **W** write, **M** id mint. "Inputs" means the function's arguments and what stage 1 resolves
from them; a read on inputs only can move anywhere before its first use without changing what it reads.

| # | Lines | What | Kind | Depends on |
|---|---|---|---|---|
| 1 | 4340-4342 | `_resolve_attempt_target` (`:2793-2914`): attempt type checks; `vault.practice_items`, `learning_object_for_item`; `_assessment_contract(repository, draft)` then `rubric_from_contract`, else `resolved_rubric(vault, item)`; draft validation; live only: `serve_eligibility.decision_active(vault)`, `auto_primed_draft` (reveal ledger, clock), then `submit_decision` (follow-up tasks, clock) or the bare cold guard (`active_followup_task_for_item`, clock). Raises `AttemptValidationError`. Returns item, LO, rubric and the (possibly force-primed) draft | R vault, repo, clock, config | inputs |
| 2 | 4343-4344 | `observed_at = clock.now()`, `now_iso = utc_now_iso(clock)` (two clock reads) | R clock | — |
| 3 | 4345-4355 | correctness: the recorded one for a grade whose contract is unrecorded (raises outside [0, 1]), else `rubric_score / max(max_points, 1)` | C | 1 |
| 4 | 4356-4357 | `vault.subjects_for_item(item)`, first subject | R vault (in memory) | 1 |
| 5 | 4366-4393 | `unassessed`, `criterion_points`, `nothing_assessed` (the unrecorded-contract override at 4376-4381), `held = grade_is_held(...)` | C | 1 |
| 6 | 4398-4402 | `pfc_facet_weights = target_criterion_facet_weights(item, rubric, resolve=vault.canonical_facet_id)` when `unassessed` | C over the vault's alias map (in memory) | 5 |
| 7 | 4403-4434 | coverage: `resolve_coverage` (`config.evidence`), `scale_coverage_for_graded_criteria` unless `dont_know` (`config.teach_back`), zeroed when nothing is assessed | C | 1, 5, 6 |
| 8 | 4435-4444 | `load_attempt_prior_state` (`:4224-4298`) unless a snapshot is passed: `mastery_state` or `initial_mastery_state_for_learning_object` (claims); `CanonicalFacetStateReader` per facet, aggregate and item scope; `list_recent_attempts_by_learning_object` (window `max(config, 20)`, `before=` the replay position); `list_recent_attempts_by_practice_item` (5); `held_attempt_ids`; `active_errors_by_learning_object`; `practice_item_state`; `practice_item_quality_state`; `attempt_uncertainty_priors` per facet; `item_parameter_state` when EB difficulty is on. **Facets: `[*item.evidence_facets, *coverage.covered_facets]`** | **R, depends on 7** | 1, 2, 7 |
| 9 | 4445-4470 | `_canonicalized_grade_attributions` (alias map), `enforce_passed_target_firewall` (`grading.py:529`, alias map, `criterion_points`), audit events; a held grade's attributions emptied | C (alias map) | 1, 5 |
| 10 | 4471-4479 | `resolve_item_irt_params` (prior item parameters, `config.mastery`); primed `b` shift | C | 1, 8 |
| 11 | 4480-4487 | `predicted_correctness_from_prior` | C | 8, 10 |
| 12 | 4488-4515 | `derive_facet_outcomes`; the uncertainty layer's own map and outcomes when the facet-belief fixes are on (`target_criterion_facet_weights`, alias map) | C (alias map) | 3, 5, 7, 9 |
| 13 | 4527-4549 | `interpretation_variance`: `grade_resolution.response_soft_score` (`:407`) for an `ai`/`codex` grade that is not `dont_know`; any exception reads as 0.0. Reads the outcome schema and the calibration models; **writes** idempotent seeds (`ensure_builtin_schemas` when the schema is missing, `seed_heuristic_priors` always); clock for their stamps | R, W (idempotent seed), clock | inputs only |
| 14 | 4553 | `lesson_check_mass(repository, attempt_id, attempt_type)` (`learner/lesson_weight.py:900`; `lesson_checks`, lesson checks only) | R | inputs only |
| 15 | 4554-4561 | `resolve_reliability` | C | 1, 14 |
| 16 | 4562-4568 | `familiarity_discount_from_attempts` | C | 7, 8 |
| 17 | 4569-4575 | `lo_relative_coverage` (`learner/facet_diagnostics.py:227`): **reads** `required_facets` (all `practice_item_states`, the vault's items) and `facet_uncertainty_states_for_lo` (open, resolving), keyed by the LO alone; then computes over coverage | R (LO only), C | R: 1; C: 7 |
| 18 | 4576-4600 | prior bad-item suspicion; `event_local_severity_from_attempts` per attribution (`recall_coverage.py:435`: the vault's error taxonomy, `config`); primary type, max severity | C (taxonomy, keyed by the grade's error types) | 3, 7, 8, 9, 11, 12 |
| 19 | 4601-4618 | `build_facet_recall_updates_from_prior`; the post-attempt aggregate map | C | 7, 8, 12, 16, 18 |
| 20 | 4619-4624 | `covered_required_fraction` (`facet_diagnostics.py:279`): **reads** `contract_frontier` (vault, `required_facets`), then either `facet_capability_evidence_for_facet` per frontier facet or `required_facets` and `facet_recall_states_for_lo`; branches only on what it read; then merges 19's map | R (LO only), C | R: 1; C: 19 |
| 21 | 4625-4660 | `resolve_error_impact`; `MasteryObservation` | C | 7, 14-18 |
| 22 | 4663-4684 | `update_mastery_traced`, `apply_mastery_variance_floor`, unless nothing is assessed | C | 8, 10, 20, 21 |
| 23 | 4685-4703 | `update_item_difficulty` when EB difficulty is on | C | 8, 22 |
| 24 | 4704-4728 | `compute_surprise`; held and `interval_factor_removed(config)` overrides | C | 8, 10, 18, 21, 22 |
| 25 | 4730-4790 | FSRS: rating, **`resolve_fsrs_weights(repository)`**, elapsed days, eligibility, causal activity, `apply_review` or skip, `_fsrs_review_summary` | C, R (inputs only) | 2, 5, 8, 24 |
| 26 | 4792-4829 | `attempt_record`, with **`_attempt_reference_status`** (`:4301`: live only, when the draft carries none; a read-only connection of its own, `reference_status_for_item`) and `_ad_logged_fields` (config) | C, R (inputs only) | 1-3, 18 |
| 27 | 4830-4835 | `error_event_ids`: the override's ids, else **`new_ulid()`**, one per resolved attribution | M | 18 |
| 28 | 4836-4854 | error events; `_error_event_repair_plan` (taxonomy) | C | 9, 18, 27 |
| 29 | 4855-4864 | evidence rows: the grade's, else **`repository.fetch_grading_evidence(attempt_id)`** (replay's grades carry none); unassessed rows dropped | R (inputs only), C | inputs; 5 |
| 30 | 4865-4881 | `build_facet_uncertainty_updates` (`facet_diagnostics.py:441`: `config`, taxonomy and the LO's concept through `_initial_hypothesis_marginal`) | C | 7, 8, 12, 18, 29 |
| 31 | 4884-4910 | recent item failures; `build_quality_state_update_from_prior` unless held | C | 5, 8, 18 |
| 32 | 4911-4932 | `estimate_ability_transition` and its event row | C | 3, 7, 28 |
| 33 | 4933-5048 | the debug payload | C | most of the above |
| 34 | 5049-5115 | `PracticeItemState` (`practice_item_hash`), surprise record, `display_mastery`, `AttemptResult`, `AttemptApplication` | C | all |

Every other callee is plain computation over its arguments (checked by reading each, and by an AST scan for
repository, connection, clock, vault, id and random use): `resolve_coverage`, `scale_coverage_for_graded_criteria`,
`derive_facet_outcomes`, `resolve_reliability`, `familiarity_discount_from_attempts`, `predicted_correctness_from_prior`,
`build_facet_recall_updates_from_prior`, `resolve_error_impact`, `update_mastery_traced`, `update_item_difficulty`,
`resolve_item_irt_params`, `compute_surprise`, `apply_review`, `interval_for_retention`, `classify_attempt_activity`,
`evidence_eligibility_for`, `hot_path_applies_practice_review`, `build_quality_state_update_from_prior`,
`estimate_ability_transition`, `display_mastery`, `practice_item_hash`, `grade_is_held`.

The function writes nothing itself; 13's seeds are the one write under it, into tables no other read here reads.

### Returned, and where it goes

`AttemptApplication` (`:547`). The one direct caller is `compute_attempt_application` (`:3651`), whose only `src`
caller is `_apply_attempt_in_transaction` (`:3239`). That strips an invalid probe presentation from the attempt
record (`:3274`), stamps lineage on the evidence rows (`:3281`), rekeys the uncertainty rows to canonical facet ids
(`:3286`), and persists through `_persist_attempt_application` (`:3901`: `record_attempt_outcome` live,
`replace_attempt_derived_outcome` on replay): the attempt row, evidence rows (live), error events, surprise row,
practice item state, mastery state, facet uncertainty (at the successor), quality state (unless held), ability
transition, debug payload, item parameters. It then reads `rubric` and `grade_contract_unrecorded` for the grade
channel dual write, `grade_held` for the cold-probe label, episode evidence and auto-resolution, `result` for every
later step and the caller, and `fsrs_review` for the live grade's decision record (`:3520`).
`facet_recall_states` is computed and never persisted (the debug payload carries it).

### Callers

Everything reaches the function through `apply_attempt` (`:3166`) then `compute_attempt_application`, which passes
the `ApplyAttemptInput`'s fields one for one, `replay = replace_existing`, and `prior_state` only when its own caller
passes one (tests do; no `src` caller).

| Caller | What it passes | What it uses |
|---|---|---|
| Self grade `complete_self_graded_attempt` (`:1098`), stuck `complete_empty_stuck_attempt` (`:1194`) | a self/deterministic grade, `grading_source` "self"/"deterministic", no override | the result |
| Live AI grading, joint and blind (`complete_codex_graded_attempt` `:1259`, through `_complete_*`) | the model grade, `grading_source` "ai"/"codex", grader identity, unverified criteria, the hold | the result, the decision record |
| Exam seeding (`goals/exam_seeding.py:425`), exam sittings (`goals/exam_session.py:604`), teach-back (`tutor/teach_back.py:705`), lesson checks and probes (`teacher/checks.py:284`, `teacher/probes.py:428`), the sim (`sim/runner.py:673`, `sim/diagnostic_validation.py:470`) | their own `ApplyAttemptInput` | the result |
| Replay `replay_existing_attempt` (`:1381`), from `substrate/replay.py:350` (`replay_learning_object`) | the stored attempt as a draft, the current epoch's criterion points (no evidence rows, so 29 reads them), the stored error type's attributions, the stored events' ids as `error_event_ids_override`, the stored grading source, the blind record's identity and hold, `replay_ledger_position` when the bounded ledger is on | rows replaced in place |
| Regrade (`attempts/regrade.py:663`) | `replay_learning_object` with attribution and grader-identity overrides per attempt | as replay |
| Adjudication (`grade_resolution.append_adjudication`, `cli/grading.py:33`) | nothing directly: it appends an evidence revision, which the next replay reads as the current epoch | as replay |
| The shadow rebuild and `rebuild-derived-state` (`substrate/replay.py:420`, `rebuild_orchestrator.py:365`, `shadow_rebuild`) | `replay_learning_object` per LO, a `FrozenClock` at each attempt's `created_at` | as replay |
| Tests (`test_replay.py`, `test_recall_coverage_interventions.py`, `test_attempt_chain_records.py`, `test_pfc_unverified_unassessed.py`) | `compute_attempt_application` with and without a prior snapshot; two monkeypatch the function | the application |

## 2. Reads that depend on an earlier computation

**One: the prior state (8).** Its facet list is `[*item.evidence_facets, *coverage.covered_facets]`, and coverage is
7's computation. Coverage's facets come from `_raw_coverage` (`recall_coverage.py:698`), whose keys are always the
item's evidence facets, or `["whole-item"]` when the item names none; scaling (7) and the unassessed override (5)
only remove facets. So for an item with evidence facets the list is exactly those facets, but for an item with none
it is `["whole-item"]` or empty depending on 5 and 7, and the snapshot's dictionaries (iterated by 11 and 20) carry
those keys. The read genuinely waits on the computation.

Every other repository read (13, 14, 17, 20, 25, 26, 29) is keyed by the inputs alone: the LO, the item, the attempt
id, the draft. They can be made between the two stages in today's order without reading anything more. Clock reads
keep their order: 1, 2, then 13's seed stamps. 13's seed write touches only the outcome-schema and calibration tables,
which none of the other reads read, and 26's read uses its own read-only connection, which sees no uncommitted row of
this transaction either way.

**The vault's in-memory content.** 6, 9, 12, 18, 28 and 30 look things up in the loaded vault by values computed in
the call (the alias map by facet ids from the grade and the rubric, the error taxonomy by the grade's error types,
the LO by id). These are dictionary lookups on content loaded when the vault was, with no query and no failure mode
(`dict.get`). Passing those three mappings into the core is not reading ahead: the core makes exactly today's
lookups on the same objects. Configuration is passed the same way, as the loaded `LearnLoopConfig` value.

**The id mint (27).** Not a read, but not pure: the count is `0` for a held grade, else one per attribution (9 is
one-to-one: canonicalization and the firewall map each attribution to one). The shell mints after stage A, at today's
position among the effects (after 26's read, before 29's), so a seeded ULID stream draws in the same order;
`zip(strict=True)` over the ids and the attributions already fails loudly if the count ever disagrees.

## 3. How many stages

**Two pure stages with today's exact reads.** Stage A (3, 5, 6, 7: what the grade assessed and the evidence's
coverage) needs the inputs gathered before it (1, 2, 4). The shell then reads 8, 13, 14, 17's and 20's reads, 25's
weights, 26's status, mints 27 and reads 29, in that order. Stage B (everything else) is pure over the inputs, A's
result and those reads.

**One stage would need reading ahead.** Merging A into B means reading the prior state for `"whole-item"` on every
item that names no evidence facet, whether or not coverage reaches it (an aggregate and an item-scoped canonical
recall lookup through the per-attempt reader, plus one uncertainty prior: at the successor
`stored_facet_uncertainty_state`, which reads the LO's uncertainty rows and the merge map), and then removing the key
again before 11 and 20 iterate the snapshot, or their sums change. The failure it adds: a read that raises for a
facet the attempt never covered fails the attempt. That is a decision for the owner, not this step, and it buys
nothing the two stages don't: the shell's read sits between two pure functions, as the brief allows. So the step
continues.

## 4. Extraction (the plan, as executed below)

- `GradeInputs` (frozen): the attempt id, resolved draft, item, LO, rubric, grade, subject, `observed_at`, `now_iso`,
  the grade's flags (source, agent run, fallback, grader identity, unassessed ids, hold, unrecorded contract and
  its correctness), and the loaded values the core reads: `config`, the alias map, the error taxonomy.
- `grade_scope(inputs)` (stage A) returns what was assessed, the hold and the coverage.
- `GradeReads` (frozen): the prior snapshot, the interpretation variance, the lesson mass, the LO's coverage reads,
  the breadth reads, the FSRS weights, the reference status, the error event ids, the evidence rows.
- `grade_application(inputs, scope, reads)` (stage B) returns the `AttemptApplication`.
- The shell `_compute_resolved_grade_application` keeps its signature: it gathers, calls A, reads, calls B.
- `lo_relative_coverage` and `covered_required_fraction` keep their signatures (tests call them) as a read plus a pure
  function. The callees that took the vault for lookups (`event_local_severity_from_attempts`,
  `build_facet_uncertainty_updates`, `_error_event_repair_plan`, `_canonicalized_grade_attributions`, the firewall's
  facet canonicalization, `_ad_logged_fields`) take the mapping or config they read instead.
