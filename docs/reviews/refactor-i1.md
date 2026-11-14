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

## 4. Extraction

The plan above, executed. Commits, in order:

1. `f005473004`: this record's step 0.
2. `0992f2f0fd`: the golden, recorded at the base (§5).
3. `4f23c60d48`: `lo_relative_coverage` and `covered_required_fraction` (`learner/facet_diagnostics.py`) keep their
   signatures, as a read (`read_lo_coverage`, `read_breadth`, returning the frozen `LoCoverageReads` and
   `BreadthReads`) and a pure function over what was read (`lo_relative_coverage_from`,
   `covered_required_fraction_from`; `_covered_frontier_fraction` now takes the capability rows). `LoCoverageReads`
   holds the very `set` the read built, because the coverage sums iterate it and a set rebuilt from the same members
   can iterate in another order.
4. `aafc3dd8c1`: the callees that took the vault for lookups take what they look up:
   `event_local_severity_from_attempts` (`error_types`, `config`), `build_facet_uncertainty_updates` and
   `_initial_hypothesis_marginal` / `_attribution_targets_facet` (`config`, `error_types`, the LO object),
   `_error_event_repair_plan` (`error_types`, through a new `_taxonomy_severity` that `_error_severity` now calls),
   `_canonicalized_grade_attributions` (the alias function), `enforce_passed_target_firewall` (a new
   `canonical_facet_id` keyword; `vault=` still works and means its alias function), `_ad_logged_fields` (`config`).
5. `0dc30d131c`: the split. `GradeInputs`, `GradeScope` and `GradeReads` (frozen), `grade_scope` (stage A),
   `grade_application` (stage B) and `_interpretation_variance` (13's read, with its fail-safe). The shell keeps the
   old name and signature. The stage bodies are the old text moved by a script (`extract_core.py` in the step's
   scratch directory), with only these substitutions: `vault.config` to `config`, `vault.canonical_facet_id` to
   `inputs.canonical_facet_id` (`GradeInputs.canonical_facet_id` is `facet_aliases.get(id, id)`, the body of
   `LoadedVault.canonical_facet_id`), `vault.error_types` to `inputs.error_types`,
   `vault.learning_objects.get(learning_object.id)` to `learning_object` (the loader keys that map by id, so it is
   the same object), `canonical_facet_uncertainty_on(vault)` to the shell's `inputs.facet_uncertainty_on`, and each
   read to its `reads.` field.
6. `c822e55d30`: stage B in parts under 200 lines, by a second script (`split_stage_b.py`): `_kept_attributions`,
   `_event_severities`, `_grade_evidence` (returns `GradeEvidence`), `_belief_update` (`BeliefUpdate`: the EKF, the
   breadth floor, EB difficulty, surprise), `_fsrs_review` (`ReviewUpdate`), `_attempt_record`, `_error_event_rows`,
   `_quality_update`, `_debug_payload`, `_causal_attribution_counts`. They run in the old body's order. In
   `_debug_payload` the moved text reads the bundles' fields (`evidence.lo_coverage` for `lo_coverage`, and so on).
   One dead store went: a primary error type computed after the firewall and overwritten after the severities, with
   no read between.
7. `b3f9aae667`: the comments in the shell and both stages lose their stage, ruling and review names and say why
   (comments only).
8. `35ff77c311`: the plain-value tests (§5).
9. `cb9b6822fc`: Attempt Processing, the predicate's pointers in `held_grades.py` and `outcome_contract.py`, the
   `AttemptApplication` docstring, the structure ratchet.
10. `87e6f4b917`: the vault's generated references, regenerated once; a second run changed nothing.

## 5. What pins it

**Before this step.** Replay and rebuild tests check live against rebuilt state (`test_rebuild_equivalence.py`,
`test_replay.py`, `test_mvp017_route_check_replay.py`, `test_regrade_contract_replay.py`, `test_held_grade_evidence.py`,
`test_pfc_unverified_unassessed.py`), and feature tests check values with tolerances (`test_surprise.py`,
`test_recall_coverage_interventions.py`, `test_attempts.py`). None pins every field's bits at a fixed input across
commits, so every stage was unpinned for this purpose.

**Added: `tests/test_grade_application_golden.py`** (with `tests/grade_application_golden_helpers.py` and
`tests/goldens/grade_application/history.json`, 2.3 MB). A split vault at the head with its seeded history, then a
self-graded answer, a model grade with two attributions (one the firewall strips), hinted, primed, "I don't know",
stuck, a model grade with a criterion unverified, a held grade, a repeat on the same item and one on its sibling,
an answer through the real blind-grading door with the deterministic fake, a regrade (which replays the LO), and an
adjudication's evidence revision; then `rebuild_all_derived_state`. The record holds every field of every
`AttemptApplication` computed (26 live, 18 in the rebuild), floats as `repr` (every bit), and every row each phase
added or removed in every table. ULIDs and random UUIDs are numbered by first appearance, wall stamps and the head tag
replaced. A second test fails if the history stops reaching a kind of grade.
- Fail-first evidence of its resolution: multiplying the observation weight by `1 + 2**-52` (one ulp) fails it.
- Stable under `PYTHONHASHSEED` 0, 1, 777 and 12345 and at `-n 4`.
- Unchanged after every commit above.

**Added: `tests/test_grade_application_core.py`**, the point of the step: 15 tests building `GradeInputs`,
`AttemptPriorState` and `GradeReads` in memory (no vault on disk, database or clock): independent, hinted (a capped
rating, the hint factors), primed (the `b` offset; a smaller gain), "I don't know" (rating, event and its id),
stuck, held (no evidence, the schedule kept, `skipped == "held"`), unassessed, the firewall, a replayed regrade (the
stored evidence rows and the first-written event ids), an adjudicated correction, an unrecorded contract (and its
refusal), a repeat on the same surface group (familiarity), a drifting event-id count failing loudly, the core
reaching none of the shell's reads, the clock or the id mint (each patched to raise), and inputs left unchanged.

**T4.** No test patched a name this step moved. `test_pfc_unverified_unassessed` spies on the shell's keyword
arguments, and the shell keeps its name and signature; `test_attempt_chain_records` patches the public
`compute_attempt_application`; `test_lp_claim_fixes_rereview` patches `attempts.new_ulid`, which the shell still
calls. No assertion changed.

## 6. Proof

**Golden:** as in §5.

**Targeted gate.** `scripts/affected_tests.py --base 68c61b9f1a` names 1,311 files (the two new ones among them); run in
14 chunks of 100 at `-n 4`: 28,303 passed, 0 failed. `test_identity_pins`, `test_retired_config_identities`,
`test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`,
`test_structure_ratchets`, `test_public_tip_guards` and the two new files: 313 passed. `lint-imports` 42 kept,
`ruff check` clean, the four vault validators pass, the gate partition holds (30,843 = 30,783 + 60).

**P-shadow.** The three copies in `learnanything-ad1/fixtures-local/owner-copies-mvp058` (at `mvp-0.58`), copied twice
with `copy_tree_with_databases` under `fixtures-local/i1/{base,branch}/`. `base` ran the base's code (a `git archive` of
`68c61b9f1a`'s `src/` and `migrations/` on `PYTHONPATH`), `branch` this branch's. Counts only; the copies are deleted.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed, both | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved, both | 0 | 0 | 0 |
| live database unchanged by the shadow, both | yes | yes | yes |
| the two shadow reports, marker id, stamps and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row | 402 tables, 19,442 rows: none differ (normalized) | 402, 10,426: none | 402, 23,877: none |
| after a real `rebuild-derived-state` on each (replayed attempts) | 70 attempts; 19,749 rows: none differ | 3; 10,498: none | 3; 23,719: none |
| `attempt_surprise` byte-equal (raw, no normalization), after the rebuild | 70 rows: yes | 3: yes | 3: yes |

Byte-equal raw after the rebuild as well: `practice_attempts`, `learning_object_mastery`, `practice_item_state`,
`error_events`, `attempt_debug_payloads`, `ability_transition_events`, `practice_item_quality_state`,
`facet_uncertainty`. The 10 tables that differ raw (`activity_observations`, `derived_state_rebuilds`,
`facet_capability_evidence`, `facet_recall_state`, `grade_interpretations`, `measurement_events`,
`parameter_registry`, `parameter_registry_manifests`, `raw_grade_events`, `subject_identifiability_watermarks`) differ
only in ids and wall stamps: equal once ULIDs, UUIDs, 64-hex digests and stamps from the last three days are
replaced by class tokens. After five more rebuilds on each side (the timing runs), linear_algebra's 20,817 rows still
agree, and `attempt_surprise` is byte-equal.

**The mvp-0.17 fixture.** `fixtures/mvp017_route_check_replay` copied four times, retagged to the floor (`mvp-0.58`)
and the head (`mvp-0.59`), and rebuilt live twice by each code. After the first and the second rebuild, at both tags,
every table agrees row by row (1,343 / 1,463 rows at the floor, 1,348 / 1,468 at the head), `attempt_surprise` and
`practice_attempts` byte-equal. One `attempt_debug_payloads` row (`att_02_svd_fail`) agrees only once the causal
hypotheses' ULIDs replay mints and the diagnosis receipt id hashed from them (`dr_…`) are normalized too, as D5b
recorded; the rebuild mints both afresh on either code.

**Timing.** A full `learnloop rebuild-derived-state` of linear_algebra (70 attempts, the largest history), whole
process, alternated base and branch four times on the same machine (load average about 6 from other lanes):
base 2.736, 2.779, 2.788, 2.860 s; branch 2.755, 2.795, 2.742, 2.911 s. No difference beyond the noise.

**Identity pins** unmoved: `test_identity_pins`, `test_retired_config_identities`, `test_effective_defaults_golden`
and `test_cli_help_snapshot` pass at the tip with nothing written.

**Measures.**

| | base | tip |
|---|---|---|
| `_compute_resolved_grade_application` | 798 lines | 100 (the shell) |
| the core | (inside it) | `grade_scope` 106; `grade_application` 145 with `_grade_evidence` 190, `_belief_update` 86, `_debug_payload` 81, `_fsrs_review` 69, `_causal_attribution_counts` 60, `_attempt_record` 44, `_quality_update` 40, `_event_severities` 38, `_kept_attributions` 33, `_error_event_rows` 25 |
| read helper | | `_interpretation_variance` 33 |
| frozen types | | `GradeInputs` 34, `GradeScope` 11, `GradeReads` 16, `GradeEvidence` 30, `BeliefUpdate` 9, `ReviewUpdate` 9 |
| `attempts/attempts.py` | 5,679 | 6,092 |
| `learner/facet_diagnostics.py` | 819 | 906 |
| functions over 200 lines (ratchet) | 76 | 75 (lowered with `--write`) |
| comment lines naming a stage artifact (ratchet) | 2,392 | 2,387 |

The file grows by 413 lines: the docstrings, the six frozen types, and the lines at the top of each part that bind
its inputs' fields to the names the moved text uses.

## 7. Judgment calls

- **The vault's in-memory content passed as values** (§2): the config, the alias map, the error taxonomy and the LO
  object go into `GradeInputs`, and the callees take them instead of the vault. These are the same objects the old
  lookups read, so no lookup moved; I did not count them as reads ahead.
- **`GradeInputs.facet_uncertainty_on`** is computed by the shell (`canonical_facet_uncertainty_on(vault)`) rather
  than the core calling the predicate's internals with the config, so the predicate stays the one place that decides
  it (the parallel gate step may change it).
- **The id mint between the stages**, with its count from the hold and the attribution count (§2), rather than the
  core returning id-less rows for the shell to fill: the application the core returns is then complete, and the
  strict zip guards the count.
- **Reads between the stages in today's order**, not gathered before stage A: stage A can raise
  (`AttemptValidationError` for an unrecorded contract's correctness) before any of them, as today.
- **`vault.subjects_for_item`** is read before stage A (it was after the correctness check); it is an in-memory
  lookup that cannot fail on a resolved item.
- **`GradeEvidence` has 24 fields.** They are the evidence's parts the rows and the debug payload read; a narrower
  type would push the same fields through more signatures.
- **The golden is 2.3 MB** (under G8's 5 MB). Most of it is the rows other steps of the attempt write (labels,
  completion work, measurement events); I kept them because the brief asks for every row written.
- **`_interpretation_variance` lives in the shell**: it reads the grade channel and seeds its tables, so it is a read,
  though its result only feeds the core.

## 8. Not verified

- P-draw: the step changes no draw (the router is not reached), so the draw-for-draw harness was not run.
- The owner copies' histories are small (70, 3, 3 attempts), with few model grades; the golden covers the model,
  held, unassessed, regrade and adjudication paths on synthetic data.
