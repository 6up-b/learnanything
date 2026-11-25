# Teacher v2 · TE5

A and C landed in `60e21faadfe34f7fc62460ce0309a4a4b699da5b` on `teacher/te5-consolidation`, from `9038b096e7446d5f433f95d881de7e7c1bd0da15`. B landed at `6d5716b332`. D implements the owner's freeze-and-refit decision for mvp-0.70 in the working tree, with migration 274. The Reader's mvp-0.69 and migration 270 are the required integration base.

## A · Schema and recovery

The executor reads one discriminated union, using the historical field name `requests`. The provider receives the original V1 model for each combination of visuals, episodes and probes. The normalized wire dump goes into the journal. The execution model dumps only the fields supplied by that wire object, preserving differences including explicit nulls. Recovery restores the historical wider defaults that enter deferred reads and plans.

New lessons capture their available capabilities in the immutable lesson row's goal JSON, outside the brief. Old rows use the latest accepted turn's episode and visual flags and the stored brief version. An interrupted historical opening with no accepted turn has only its brief version available. Each accepted turn replays its own flags. A new lesson keeps its captured capabilities across settings changes. Figure admission and protection still run before delivery.

The predecessor contracts and `legacy_turns.py` compare byte for byte and by parsed AST. SHA-256 is `f31da2baf370e49658c3b92e449896afc340a37be2298282b1eda9874413cc4f`. The Part A diff has no changes under the doctrine or checked-in goldens. The new tests compare the wire and execution validators (including defaults, explicit nulls and illegal actions and fields), recovered read and plan payloads, and predecessor prompt digests for all eight capability sets. An open/reply test changes the episode setting between calls. The structured-contract test now checks the V1 type at the provider and the V2 type at the executor. Its retry, receipt, prompt and guard assertions remain intact.

All pytest commands used the isolated venv, `python -m pytest -q -n 1 -p no:cacheprovider` and explicit filenames. Results before Part C, with filenames relative to tests/ and the common test_ prefix and .py suffix omitted:

| Group | Result |
|---|---|
| teacher_te5_contracts | 26 passed |
| identity_pins | 363 passed |
| teacher_exam_question_guard, teacher_from_check, teacher_structured_contracts, teacher_te0_confidence_events, teacher_te0_fix_round2, teacher_te0_review_fixes | 118 passed |
| teacher_te1_curriculum_c4, teacher_te1_lesson, teacher_te1_migration, teacher_te1_review_fixes, teacher_te1_successor, teacher_te1_weight | 81 passed |
| teacher_te1b_landing_r2, teacher_te1b_migration, teacher_te1b_rereview_fixes, teacher_te1b_review_fixes, teacher_te1b_suggestions | 55 passed |
| teacher_te2_landing_r1, teacher_te2_lessons, teacher_te2_migration, teacher_te2_probes, teacher_te2_review_fixes, teacher_te2_sidecar, teacher_te2_successor | 54 passed |
| teacher_te2log_activity, teacher_te2log_episodes, teacher_te2log_migration, teacher_te2log_node_held, teacher_te2log_receipt, teacher_te2log_report, reader_rw5d_p4b_teacher_visuals | 83 passed |
| structured_contracts | 42 passed |
| architecture | 18 passed |
| test_layout | 3 passed |
| ruff check | All checks passed |
| lint-imports --no-cache | 54 kept, 0 broken |

The new tests and identity suite passed again after moving the selector out of contracts to fix the figure import boundary. No paid calls or owner-copy inspection.

## C · Teacher topic offers

New desktop lessons record the `goal_topics` capability. The teacher can request `create_goal_lo {phrase, title, statement, anchors}`. The code guards the proposal's combined display text, its individual persisted fields and its passage aliases before it runs the resolver. It distinguishes an existing topic from an exact unmatched phrase. Only the latter produces an actionable offer. New provider views add the same request model to the prior shape. Old lessons and accepted turns retain their recorded schema, doctrine, prompt and forecaster family.

The proposal appears in the existing lesson feed. The existing reply box accepts `Library tN`, `Add tN` and `Skip tN`, where N is that offer's ledger sequence. Library uses the existing `find_sources` action with the offered phrase and sends its result to the teacher. The typed-goal entry already has a Reader lookup via the unmatched card's “Look in my library” action (TE2 ruling R2, commit `73b4784e41`). This checkout changes no frontend files.

Add rechecks C0b's resolver, which reuses the resolution on an unchanged catalog. A changed resolution expires the offer. The learner's exact decision is journalled before creating the LO through `create_lesson_topic` and the existing `teacher_goal_v1` service. Received passage aliases become canonical source references. Empty anchors produce an unsourced topic. Consent and completion are separate journal entries. Resume retries the same object if publishing the YAML or synchronizing SQLite was interrupted. The receipt and optional goal episode reuse the typed-goal writer. A declined offer, a bare conversational reply and a teacher message cannot authorize the write.

### Deliberate identity boundary

The paragraph version is `teacher_goal_offer_v1` and the prompt gains `+goal-offer-v1`. Each of the four new TE2 provider shapes includes the topic request. Its forecast uses the new paragraph's family. Existing lessons keep the preceding families. This changes teacher output and learning content. The scoring, grading and eligibility algorithms keep their existing versions.

The baseline identity registry had no teacher-turn entries. `python tests/test_identity_pins.py --write` added the eight entries below. Zero existing digests moved, and `identity_shapes.toml` has no diff. The table compares the same input with the new capability absent/present, using the registry's canonical JSON digest (first 12 hex digits). The full successor digests are in `tests/goldens/identities.toml`.

| Capability combination | Prompt pin | A → C | Schema pin | A → C |
|---|---|---|---|---|
| TE2 | TE5.prompt.plain | 4d9e9581367a → 1e519054c4b3 | TE5.schema.plain | 7759b0dc87f8 → dce37b0e3fbd |
| TE2 + visuals | TE5.prompt.visuals | 1a9a8a1ef30c → 3381adbafd8b | TE5.schema.visuals | 0e6e285800be → 539d36c07bc6 |
| TE2 + episodes | TE5.prompt.episodes | 84c41d66be55 → 782c411d8586 | TE5.schema.episodes | 8bdc17f56b18 → 4f06b8acc6fb |
| TE2 + both | TE5.prompt.both | 6d5d6e2c512e → 50cc73ebd7ea | TE5.schema.both | 363d7dc47346 → 62e4e0337153 |

### Existing assertions changed in C

| Test file | Expectation and reason |
|---|---|
| `test_teacher_te5_contracts.py` | The opening snapshot now includes the additional capability. Exact historical prompt hashes and old admission tests still run. |
| `test_teacher_te2log_episodes.py` | Both switch cases expect the topic-capable provider model and reconstruct the complete updated prompt. The episode-off and episode-on forecast-family checks include the topic paragraph. |
| `test_teacher_te2log_node_held.py` | The recorded node forecast uses the new family. The episode-off schema still excludes `p_held`, now checked on the actual new provider model. |
| `test_teacher_te2log_report.py` | The pool-trajectory report reads the new lesson's exact forecaster key. It still asserts the resulting pool points. |
| `test_reader_rw5d_p4b_teacher_visuals.py` | Visual-on and visual-off model comparisons select the new schema. The full prompt reconstruction and exact base-family comparison include the topic paragraph. The checks for visual field exclusion, figures, and distinct pools stay in place. |

## B · Receipt-backed context compaction

On 2026-11-23 the orchestrator selected a lesson-local margin in place of §4.3's dry-run calibration and approved using existing teacher request receipts for the compaction boundary. A teacher route with a configured `ingest.providers[provider].context_tokens` uses its own provider and model. A route without a limit sends the ordinary full prompt and uses its existing receipt observer.

### Trigger and contents

Each bounded teacher operation identifies its lesson and transcript prefix on its request receipt. The forecast follows its children to physical sends in insertion order, including corrections and read follow-ups. A missing count, change of route or change of prefix breaks a growth pair. An eligible pair contributes `max(0, current input − previous input + current output)`. The forecast adds the sample mean and the distance from the mean to the largest observed sample to the input baseline. A new lesson learns from its own receipts. The observed spread can underestimate a future jump.

With no usable pair, the forecast uses the active generation ceiling or the serving provider's configured teacher output allowance. When the most recent input belongs to this route and prefix, the baseline is that measured input and the margin is the last output plus the greater of that output and the allowance. Without that baseline the existing spend gate estimates the current input and the allowance supplies the margin. There is no dry-run call or cross-lesson prior. Pooling would require a versioned route-specific prior and a replay cutoff for each decision.

The current prompt is already rendered, so its input bounds the forecast from below (review fix round, L42-R12; [algorithm-mvp-0.72.md](algorithm-mvp-0.72.md#review-fix-round-the-adversarial-review-of-2026-11-24)): with a measured send on this route and prefix, that send's measured input plus the spend gate's estimate of how much its prompt (the root receipt's `input_text`) has grown since; with that text withheld, the measured input alone; otherwise the estimate. To it the forecast adds the largest output this lesson has measured (the allowance before the first). The decision's facts record `current_input`, `current_input_basis` and `output_need`.

Equality with the limit triggers consideration of a new prefix. The replacement must shorten the encoded prompt. The teacher keeps the last accepted exchange and everything since the preceding teacher turn verbatim. Code builds the summary from plan, check, episode, probe, forecast, capability and open topic-offer facts. The prompt still carries the current plan, open check and open prediction. The full journal supplies delayed-check commitments and receipt reconstruction.

### Storage and recovery

Migration 165 already provides `model_call_receipts.budget_json`. On the request that first uses a new prefix, this JSON holds `teacher_lesson_id`, `transcript_prefix`, `summary_version` and the frozen `context_summary`. The required receipt-start observer commits these notes and a `lesson_context_compaction` decision pointing to that request in one short transaction before the send. A correction or later send using the same boundary records its prefix and version. The first receipt retains the frozen summary. An outer sidecar or CLI writer keeps ownership of its receipt. Direct calls use the lesson as owner.

Resume follows the lesson's latest compaction decision to that receipt. A failed decision write rolls back the projection and prevents the send. An outer observer can already have opened a plain start receipt in this case. A provider outage after publication leaves a usable projection. The final lesson receipt records the version that was used.

### Stop evidence and resolution

Before this recovery the six focused cases produced **2 failed, 4 passed**. The first failure was a retained learner reference moving from `t16` to `t17` after the prototype allocated a `context_compacted` turn. Two successive receipt-backed compactions now keep the clues at `t12` and `t16`. At a predicted 1,500 tokens, the limited send changes only the serialized transcript prefix. At 1,501 and without a limit, the complete sent text matches the full rendering byte for byte. The outage fixture compares both sent prompts, the complete reconstructed receipt, the committed delayed checks and the number of teacher sends.

The second failure was in the live writer. A plan revision in a closing turn lacked the `created_at` already stored with that version in `lesson_plans`. The writer now puts the exact insertion timestamp in its live plan cache. With and without compaction, a revised outline followed immediately by close yields the same two plan versions as the database and the same full receipt after reload. Existing immutable lesson receipt JSON is read as written. An older omission still means the timestamp was absent from that receipt. The stored plan, its version and its chronology retain their meaning.

### Assertion and storage checks

Part B changes zero assertions in tracked tests and zero identity digests. In the prototype test, the assertion linking a decision to a synthetic journal turn now checks the actual request ID, owner, purpose, JSON prefix, version and summary. It also checks the entire journal for an extra boundary turn. The learner-reference distance assertion remains, alongside exact reference values and two distinct prefix lengths. The live plan-version equality remains, alongside full receipt equality and an exact check for version presence on each route.

The first expanded run had 3 failed and 4 passed. Two new assertions compared SQLite row objects directly to tuples. They now compare the values. The repeated-boundary fixture expected three entries in its second prefix but the transcript also includes the plan-stored step. It now checks the exact four entries replaced by count. Nine focused cases then passed. The architecture check subsequently located the receipt SQL in the teacher module. The existing model-call store now owns that write. A nested-operation regression initially had 1 failed and 10 passed because a teacher receipt with a parent could lose its decision. The operation and its correction now have distinct receipts sharing one decided boundary, including when the calling scope already has a model receipt.

## D · Freeze and refit the lesson weights

On 2026-11-23 the owner selected option 2. An immutable grade epoch now supplies the effective mastery curve for both trajectory and endpoint fits. Activation freezes the predecessor's best reconstruction or an explicit missing marker before clearing projections. Failed preparation leaves that first snapshot available to the retry. Held and superseding evidence follows the existing grade-epoch rules. Measured item difficulty stays off by default.

The synthetic reproduction includes an intervening empirical update, a primed repeat and edits to two authored items. The upgrade tests exercise both numeric and missing history and compare the raw check rows, full weight/pool state and ordered semantic trace after two more rebuilds. The historical-input policy, fallback labels, versioned assertions and final owner-copy procedure are in [the algorithm record](algorithm-mvp-0.71.md).

The orchestrator must rebase after the Reader's mvp-0.69 and 270 reach main, upgrade the tracked migration-head fixture there, and run the merged chain and owner-copy comparisons. The worker exercised 271 on disposable databases. No owner vault was opened.

## Historical A/C landing order

1. The untracked landing aid `te5-part-a.patch` contains the exact A sources, tests, ledger and record prior to C. Its reverse application passed `--check` at that boundary. It is outside the Part B change.
2. The A/C landing included C's sources, tests, identity helper, generated identities and their ledger and stage record. B and D were owner decisions at that boundary. The orchestrator committed A and C together.

The patch also applied cleanly to copies of the affected HEAD files under the isolated scratch directory. The reconstructed A tree had the predecessor's exact contract file in `legacy_turns.py`, the exact source of `_prompt` and `_prompt_version`, and zero golden or doctrine paths in the patch.

| Part | Files relative to the checkout |
|---|---|
| A | `src/learnloop/teacher/{contracts,episodes,legacy_turns,probes,service,visuals}.py`, `tests/{test_teacher_structured_contracts,test_teacher_te5_contracts}.py`, the A portions of `docs/reviews/{refactor-bug-ledger,teacher-te5}.md` |
| C | `src/learnloop/goals/goal_lo.py`, `src/learnloop/teacher/{actions,contracts,service,te2,topics}.py`, `src/learnloop/teacher/doctrine/te2/goal_offer_v1.md`, `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`, `tests/{test_teacher_te5_goal_topics,test_teacher_te5_contracts,test_teacher_te2log_episodes,test_teacher_te2log_node_held,test_teacher_te2log_report,test_reader_rw5d_p4b_teacher_visuals}.py`, the C portions of `docs/reviews/{refactor-bug-ledger,teacher-te5}.md` |
| B | `src/learnloop/ai/execution.py`, `src/learnloop/db/stores/model_calls.py`, `src/learnloop/teacher/{compaction,service}.py`, `tests/test_teacher_te5_compaction.py` and the B portions of the ledger and this record |
| D | Migration 274, grade-curve capture and activation, lesson-weight replay, successor and migration tests, and `docs/reviews/algorithm-mvp-0.72.md` (L4-2's record; built as mvp-0.71, renumbered to mvp-0.72 when H3 took mvp-0.71) |

The A patch documented the intermediate schema before the consolidated commit. The worker left the linked index to the orchestrator.

## Verification on the A/C tree

The final gate uses the same isolated venv wrapper and explicit test groups as the Part A table. The teacher chunks passed with 118, 81, 55, 54 and 83 tests respectively. The eight case/variant tests for the new action passed in `test_teacher_te5_goal_topics.py`. The original TE5 contract suite passed all 26. C0b landing and scope passed 24 together in `test_curriculum_c0b_landing.py` and `test_deliverable_scope.py`. Identity passed 371, structured contracts 42, architecture 18 and layout 3. The prescribed pin writer exited 0. Ruff reported `All checks passed!`, import-linter reported `Contracts: 54 kept, 0 broken.`, and `git diff --check` exited 0.

The transition runs found one import-boundary failure in A, a Ruff export-list error, duplicate dynamic schema classes and a stale exact family key in C. The regression assertions retain exact class and family checks. The synthetic interruption test exercises the vault/database split at LO publication. The final gate used no test skips or exclusions beyond the requested selection. Desktop rendering and the owner dry run and replay measurements were outside this sandbox.

## Part B final verification

All commands ran in the checkout with the prepared venv and the prescribed empty environment. The arguments below follow `python -m pytest -q -n 1 -p no:cacheprovider`. Each row was a separate process. Architecture and layout ran individually.

| Explicit file arguments | Result line |
|---|---|
| `tests/test_teacher_te5_compaction.py` | `11 passed in 4.43s` |
| `tests/test_identity_pins.py` | `371 passed in 17.49s` |
| `tests/test_teacher_te5_contracts.py` `tests/test_teacher_te5_goal_topics.py` | `34 passed in 3.73s` |
| `tests/test_teacher_exam_question_guard.py` `tests/test_teacher_from_check.py` `tests/test_teacher_structured_contracts.py` `tests/test_teacher_te0_confidence_events.py` `tests/test_teacher_te0_fix_round2.py` `tests/test_teacher_te0_review_fixes.py` | `118 passed in 20.84s` |
| `tests/test_teacher_te1_curriculum_c4.py` `tests/test_teacher_te1_lesson.py` `tests/test_teacher_te1_migration.py` `tests/test_teacher_te1_review_fixes.py` `tests/test_teacher_te1_successor.py` `tests/test_teacher_te1_weight.py` | `81 passed in 17.47s` |
| `tests/test_teacher_te1b_landing_r2.py` `tests/test_teacher_te1b_migration.py` `tests/test_teacher_te1b_rereview_fixes.py` `tests/test_teacher_te1b_review_fixes.py` `tests/test_teacher_te1b_suggestions.py` | `55 passed in 9.67s` |
| `tests/test_teacher_te2_landing_r1.py` `tests/test_teacher_te2_lessons.py` `tests/test_teacher_te2_migration.py` `tests/test_teacher_te2_probes.py` `tests/test_teacher_te2_review_fixes.py` `tests/test_teacher_te2_sidecar.py` `tests/test_teacher_te2_successor.py` | `54 passed in 13.64s` |
| `tests/test_teacher_te2log_activity.py` `tests/test_teacher_te2log_episodes.py` `tests/test_teacher_te2log_migration.py` `tests/test_teacher_te2log_node_held.py` `tests/test_teacher_te2log_receipt.py` `tests/test_teacher_te2log_report.py` `tests/test_reader_rw5d_p4b_teacher_visuals.py` | `83 passed in 25.82s` |
| `tests/test_structured_contracts.py` | `42 passed in 1.01s` |
| `tests/test_architecture.py` | `18 passed in 34.15s` |
| `tests/test_test_layout.py` | `3 passed in 21.65s` |
| `tests/test_curriculum_c0b_landing.py` `tests/test_deliverable_scope.py` | `24 passed in 6.21s` |

| Other command | Result |
|---|---|
| `ruff check` | `All checks passed!` |
| `lint-imports --no-cache` | `Contracts: 54 kept, 0 broken.` |
| `git diff --check` | Exit 0 |
| `git diff --exit-code HEAD -- tests/test_identity_pins.py tests/identity_pins_helpers.py tests/goldens src/learnloop/teacher/doctrine migrations CLAUDE.md docs/learnloop-architecture-vault/Reference` | Exit 0 |

The final gate had 894 passing pytest cases across the listed invocations. Part B moved zero pins. The linked index belongs to the orchestrator. Part D followed this B verification. The owner dry run is pending.

## Part D assertion and file inventory

- **Migration 274.** New `migrations/274_attempt_grade_curves.sql`, `src/learnloop/db/stores/grade_curves.py`, `tests/grade_curves_migration_helpers.py` and `tests/test_grade_curves_migration.py`. The table and column classifications are in `src/learnloop/db/table_roles.py` and `src/learnloop/adaptive_difficulty/{protected_tables,column_classes}.py`. The SQL-owner list in `tests/test_architecture.py` gains the store that writes this table.
- **Grading, activation and replay.** In `src/learnloop/`, the files are `algorithm_versions.py`, `attempts/{attempts,regrade}.py`, `cli/grading.py`, `db/stores/attempts.py`, `learner/lesson_weight.py`, `ops/upgrades.py` and `substrate/replay.py`. `tests/test_upgrades.py` adds the expected activation. `tests/test_grading_cli.py` adds exact regraded-curve and rollback assertions. `tests/test_teacher_te1_review_fixes.py` extends the F6 fixture with a third intervening answer. Its varied flags extend by one false and its intervening count becomes three. The original posterior tolerances stand. Its shared lesson and practice builders moved to `tests/teacher_te1_review_fixes_helpers.py`. `tests/test_teacher_te5_grade_curves.py` is new.
- **Versioned goldens.** `tests/cli_surface.json`, `tests/goldens/effective_defaults.toml` and `tests/goldens/placement_stored_misses.json` update their version strings. The grade-application golden at `tests/goldens/grade_application/history.json` adds exactly twelve curve rows and changes no other recorded application or row. The diagnosis golden at `tests/fixtures/diagnosis_journey_golden.json` gains ten grade curves, the successor labels and two tag-dependent decision config/snapshot hashes. The reader lane may add its own content to these goldens on rebase.
- **Decision records.** `docs/reviews/{algorithm-mvp-0.72,refactor-bug-ledger,teacher-te5}.md`. L4-2's original ledger row records the fix and pending integration.

The following are filenames under `tests/`, written as the middle of `test_<name>.py`. In the first group, every historical tag, ordered tail and version-set member is preserved. Relative positions shift by two from this checkout to the merged head. Fresh-vault and latest-tag comparisons name mvp-0.70. Exact tail/set comparisons include both mvp-0.69 and mvp-0.70.

`ad23_successor`, `attempt_content_state_successor`, `batch3_landing`, `check_credit_activation`, `cold_retry_reschedule`, `curriculum_c1_landing`, `curriculum_c1_plan_follows_path`, `evidence_reading_successor`, `facet_belief_successor`, `field_workbench_signals`, `figure_wait_successor`, `help_fold_attach_successor`, `ih5_successor`, `intent_codex_rereview`, `learner_report_superseded`, `lp_claim_fixes`, `mastery_seed_replay`, `mobile_v3_successor`, `placement_unevidenced_return`, `plan_follows_path`, `reader_ca2_one_ask`, `reader_followups_successor`, `reader_rd4_emission`, `reading_step_switch`, `rebuild_closed_row_answer`, `rebuild_equivalence_review`, `recurrence_commands`, `regrade_contract_successor`, `required_method_grading`, `ro1_successor`, `ro4_successor`, `ro5_successor`, `ro6_successor`, `rofu_successor`, `route_rules_in_grader`, `same_second_order`, `section_end`, `serve_eligibility_review`, `sg_successor`, `te3a_successor`, `te3b_successor`, `teacher_te1_successor`, `teacher_te1b_suggestions`, `teacher_te2_successor`.

Earlier migrations that exercise an upgrade through the head admit exactly 274's table, composite primary key autoindex and three immutability triggers in their object diffs. Each earlier migration's own expected objects and all existing row checks are preserved. These are the affected `test_<name>.py` files.

`ad1_migration`, `ad23_migration`, `approach_maps_schema`, `help_assist_figures_migration`, `help_assist_work_md_migration`, `help_assists_schema`, `learner_claim_application_migration`, `learner_claim_superseded_migration`, `library_asks_migration`, `reader_ca2_fix_orchestrator`, `reader_rw3b_migration`, `reader_rw7a_migration`, `retrieval_spaces_migration`, `rw2d_receipts_migration`, `section_coverage_migration`, `t1_batch_origin_migration`.

## Part D verification

All pytest invocations used the prepared venv, the isolated environment and `python -m pytest -q -n 1 -p no:cacheprovider` with explicit files. The working tree has no worker commits.

| Selection or command | Result |
|---|---|
| Extended F6 and the other TE1 review regressions | 33 passed in 8.54s |
| Migration, TE5 curves, TE1 review and effective defaults | 39 passed in 9.56s |
| TE5 curves, TE1 review, migration and weight suite | 52 passed in 13.90s |
| Grading CLI, AD1 and AD23 migrations, AD table protection and defaults | 34 passed in 15.43s |
| TE5 curves, TE1 review, migration, CLI help and stored placement misses | 97 passed in 70.97s |
| Grade-application golden writer | 2 passed in 4.23s |
| Diagnosis-journey golden writer | 21 passed in 13.16s |
| TE5 curves, migration and grade-application, diagnosis-journey and synthesis-tail goldens | 54 passed in 22.81s |
| Architecture, layout, migration, TE5 curves and grading CLI | 42 passed in 61.04s |
| Fourteen earlier migration/schema files including data capture | 2 failed, 69 passed in 47.53s. The two 240-only fixture tests saw pending 271 because the tracked head is still 269. |
| Initial architecture, AD table protection and rebuild orchestrator | 7 failed, 27 passed in 34.23s. Six rebuild tests require the fixture at head. The seventh identified the missing SQL-owner registration, fixed and verified above. |
| Predecessor-tag identity control | All nine historically tag-sensitive identity digests reproduced the existing golden with only the init template's algorithm label returned to mvp-0.68. |
| Owner-copy SQL compared to the store on synthetic rows | All nine epoch rows matched, including three numeric pairs, a legacy/current tie, superseded epochs and malformed or missing inputs. |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 54 kept, 0 broken. |
| `git diff --check` and scoped fixture, identity, architecture-reference and CLAUDE.md diffs | Exit 0 |

The first regrade test expected two total attempts. Its split-vault fixture already contained seven graded attempts. It now proves exactly two new revision-0 captures, one new replacement capture and preservation of every pre-existing row. Initial Ruff also found a stale import after the shared fixture move.

The final focused command used the same pytest prefix with `tests/test_teacher_te1_review_fixes.py tests/test_teacher_te5_grade_curves.py tests/test_teacher_te1_weight.py tests/test_grade_curves_migration.py tests/test_grading_cli.py tests/test_reader_ca2_fix_orchestrator.py`. Result: **78 passed in 26.86s**.

The identity gate stopped the worker. `tests/test_identity_pins.py` reported **9 failed, 362 passed in 18.33s**. The nine are `A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`, `C3b.chooser_offer`, `C3b.start_key`, `C3b.start_key_offer`, `C5.init` and `C6.init`. The init config contributes the tag to each identity or its seed. The predecessor-label control above reproduced all nine saved digests on the same source tree. The worker left both identity goldens at HEAD under the owner's stop rule. Regeneration belongs to the orchestrator after reviewing the rebased identities.

## Review fix round (parts A and C)

The adversarial review of parts A and C (2026-11-26, a static review of `a534c9e529`) found three blockers, twelve majors and three minors. Ledger ids TE5-R1 to TE5-R18 follow its table order. Each entry names the class of defect the fix closes (the generator), the fail-first test and the fix.

- **TE5-R1 (blocker 1; class: model context built from saved or vault text with no reserved-question screen).** The teacher guards read the teacher's output, and `protection_changed` ends a lesson whose protection state moved, but three inputs were never screened: the resolver's topic catalog (every active topic's record, whatever the proposal named), the brief's own words (a prerequisite's statement carried the same protected summary to the teacher, found while writing the test) and the history and note reads. The predicate moved to `learner_protection` (`reserved_book`, `quotes_reserved`), and every one of these inputs passes it: `deliverables.catalog_screen` drops a record whole (and `validate_resolution` accepts only ids the catalog sent), `guards.screen_context` replaces a matching string with a plain marker. Delivered passages keep exam material's span protection and are not rescreened. Unreadable protection refuses the open (`protected`) and the resolver (`protection_unavailable`) before any call. Assertion changed: `test_teacher_exam_question_guard.py::test_unreadable_protection_fails_closed` expected a lesson opened under unreadable protection to send three withheld turns; it now expects the open to refuse with no model call, and keeps the original three-withheld-turns assertions for protection that becomes unreadable after the open. Teacher turns, checks, the grader, the compaction summary and topic proposals were audited: each is either guarded on acceptance and covered by `protection_changed` before every call (the transcript, the summary, the grader after the action's check), or generated on the subscription route with its own reserved-match refusal (probes). Gap proposals are read by the diagnosis lane, which this round does not edit.
