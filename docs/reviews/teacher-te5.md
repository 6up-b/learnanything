# Teacher v2 · TE5

Base and tip `9038b096e7446d5f433f95d881de7e7c1bd0da15`, branch `teacher/te5-consolidation`. The orchestrator commits the working tree. L4-2 would use mvp-0.70 after the Reader's mvp-0.69. No algorithm tag or migration in this change.

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

## B · Context compaction awaits the route measurement

§4.3 calls for the selected teacher route's context window less headroom measured on the dry-run lesson. The configured window is `ingest.providers[provider].context_tokens` (optional). Use the actual teacher provider and model, including reroutes. Migration 160's `model_call_receipts` records provider, model, purpose, parent call, input/output usage and output budget. For a measured run, select one physical request per teacher send, in order, retaining corrections and read follow-ups. A missing provider count is unknown. The teacher's per-action `usage` rows can sum several calls, including a correction. Their total is unsuitable as a single context size.

Let L be that window, I[j] a measured teacher input and O[j] its output. A reproducible proposed dry-run margin is the largest observed value of `I[j+1] - I[j] + O[j+1]` across consecutive sends on the same route, bounded below by zero. It captures the extra transcript and tool results needed for the next turn plus room for its answer. Compact before the next send when `I[last] + margin >= L`. This is an empirical high-water mark, not a guarantee against a larger paste or retrieval. An alternative using the current prompt is to take the transport's existing input estimate plus the requested output ceiling and calibrate the largest positive underestimate against the dry-run inputs. That handles large fresh inputs at the cost of an estimate and can compact sooner.

A read-only count on the migration-head synthetic fixture returned zero teacher-turn receipts with both input and output counts. The checkout has no identified dry-run receipt series paired with the production teacher route's limit. §12 and §17 Q9 assign the run to the owner. The cumulative 0.3–1M input tokens per lesson, source budget and synthetic fake usage do not measure the required headroom.

| Choice | Cost and behavior |
|---|---|
| Supply the route, configured limit and the measured dry-run counts. | One owner run or an existing equivalent receipt export. A fixed measured margin is available from the first live turn. Recalibrate after a route or prompt change. |
| Use the high-water mark from each live lesson instead. | No separate calibration call. The margin is unknown at open and can miss the first large jump. The behavior depends on that lesson's observed counts and requires persisting the calibration through resume. This changes §4.3's dry-run rule. |

B is unbuilt. Once a rule is selected, test both sides of the boundary, old-turn replacement with plan/check/episode facts, verbatim recent turns and open commitments, identical resumed prompts, the receipt's summary version and zero summarizer calls.

## D · L4-2 is an owner decision

`algorithm-mvp-0.70.md` compares prospective grade-epoch capture with freezing historical reconstructions at activation. Its table covers the writes, replay sources, missing-input behavior and expected owner-copy deltas for each. Neither policy was implemented. The read-only SQL ran against `fixtures/migration_head/state.sqlite`: fitted checks/attempts/primed/with curve/missing curve were `0/0/0/0/0`, foreign-key violations `0`, integrity `ok`. All three ordered semantic-digest queries ran on the empty fixture. An owner-copy measurement is outstanding.

## Landing order and verification

1. Apply the untracked landing aid `te5-part-a.patch` to the orchestrator's index at the base commit. It contains the exact A sources, tests, ledger and record prior to C. Its reverse application passed `--check` at that boundary. Leave the patch out of commits.
2. Commit C's sources, tests, identity helper, generated identities and its parts of the ledger and stage record together. B and D change documentation only. The worker left the linked index untouched.

The patch also applied cleanly to copies of the affected HEAD files under the isolated scratch directory. The reconstructed A tree had the predecessor's exact contract file in `legacy_turns.py`, the exact source of `_prompt` and `_prompt_version`, and zero golden or doctrine paths in the patch.

| Part | Files relative to the checkout |
|---|---|
| A | `src/learnloop/teacher/{contracts,episodes,legacy_turns,probes,service,visuals}.py`, `tests/{test_teacher_structured_contracts,test_teacher_te5_contracts}.py`, the A portions of `docs/reviews/{refactor-bug-ledger,teacher-te5}.md` |
| C | `src/learnloop/goals/goal_lo.py`, `src/learnloop/teacher/{actions,contracts,service,te2,topics}.py`, `src/learnloop/teacher/doctrine/te2/goal_offer_v1.md`, `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`, `tests/{test_teacher_te5_goal_topics,test_teacher_te5_contracts,test_teacher_te2log_episodes,test_teacher_te2log_node_held,test_teacher_te2log_report,test_reader_rw5d_p4b_teacher_visuals}.py`, the C portions of `docs/reviews/{refactor-bug-ledger,teacher-te5}.md` |
| B | Compaction decision in this record |
| D | `docs/reviews/algorithm-mvp-0.70.md` and the L4-2 decision in this record |

The shared code files can be staged at the two boundaries using the A patch. No worker commit, index update, model request to a live service, frontend change, owner-vault access, algorithm-version change or migration.

## Verification on the combined tree

The final gate uses the same isolated venv wrapper and explicit test groups as the Part A table. The teacher chunks passed with 118, 81, 55, 54 and 83 tests respectively. The eight case/variant tests for the new action passed in `test_teacher_te5_goal_topics.py`. The original TE5 contract suite passed all 26. C0b landing and scope passed 24 together in `test_curriculum_c0b_landing.py` and `test_deliverable_scope.py`. Identity passed 371, structured contracts 42, architecture 18 and layout 3. The prescribed pin writer exited 0. Ruff reported `All checks passed!`, import-linter reported `Contracts: 54 kept, 0 broken.`, and `git diff --check` exited 0.

The transition runs found one import-boundary failure in A, a Ruff export-list error, duplicate dynamic schema classes and a stale exact family key in C. The regression assertions retain exact class and family checks. The synthetic interruption test exercises the vault/database split at LO publication. The final gate used no test skips or exclusions beyond the requested selection. Desktop rendering and the owner dry run and replay measurements were outside this sandbox.
