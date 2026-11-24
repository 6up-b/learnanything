# Teacher v2 · TE5

A and C landed in `60e21faadfe34f7fc62460ce0309a4a4b699da5b` on `teacher/te5-consolidation`, from `9038b096e7446d5f433f95d881de7e7c1bd0da15`. Part B is in the working tree for the orchestrator to commit. L4-2 would use mvp-0.70 after the Reader's mvp-0.69. No algorithm tag or migration in this change.

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

## D · L4-2 is an owner decision

`algorithm-mvp-0.70.md` compares prospective grade-epoch capture with freezing historical reconstructions at activation. Its table covers the writes, replay sources, missing-input behavior and expected owner-copy deltas for each. Neither policy was implemented. The read-only SQL ran against `fixtures/migration_head/state.sqlite`: fitted checks/attempts/primed/with curve/missing curve were `0/0/0/0/0`, foreign-key violations `0`, integrity `ok`. All three ordered semantic-digest queries ran on the empty fixture. An owner-copy measurement is outstanding.

## Historical A/C landing order

1. The untracked landing aid `te5-part-a.patch` contains the exact A sources, tests, ledger and record prior to C. Its reverse application passed `--check` at that boundary. It is outside the Part B change.
2. The A/C landing included C's sources, tests, identity helper, generated identities and their ledger and stage record. B and D were owner decisions at that boundary. The orchestrator committed A and C together.

The patch also applied cleanly to copies of the affected HEAD files under the isolated scratch directory. The reconstructed A tree had the predecessor's exact contract file in `legacy_turns.py`, the exact source of `_prompt` and `_prompt_version`, and zero golden or doctrine paths in the patch.

| Part | Files relative to the checkout |
|---|---|
| A | `src/learnloop/teacher/{contracts,episodes,legacy_turns,probes,service,visuals}.py`, `tests/{test_teacher_structured_contracts,test_teacher_te5_contracts}.py`, the A portions of `docs/reviews/{refactor-bug-ledger,teacher-te5}.md` |
| C | `src/learnloop/goals/goal_lo.py`, `src/learnloop/teacher/{actions,contracts,service,te2,topics}.py`, `src/learnloop/teacher/doctrine/te2/goal_offer_v1.md`, `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`, `tests/{test_teacher_te5_goal_topics,test_teacher_te5_contracts,test_teacher_te2log_episodes,test_teacher_te2log_node_held,test_teacher_te2log_report,test_reader_rw5d_p4b_teacher_visuals}.py`, the C portions of `docs/reviews/{refactor-bug-ledger,teacher-te5}.md` |
| B | `src/learnloop/ai/execution.py`, `src/learnloop/db/stores/model_calls.py`, `src/learnloop/teacher/{compaction,service}.py`, `tests/test_teacher_te5_compaction.py` and the B portions of the ledger and this record |
| D | `docs/reviews/algorithm-mvp-0.70.md` and the L4-2 decision in this record |

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

The final gate had 894 passing pytest cases across the listed invocations. Part B moved zero pins. The linked index belongs to the orchestrator. Part D and the owner dry run remain outside this change.
