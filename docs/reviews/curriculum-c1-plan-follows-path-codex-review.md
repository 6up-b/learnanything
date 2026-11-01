# Curriculum C1 (plan follows the path): Codex review and fixes

Stage record: `docs/reviews/curriculum-c1-plan-follows-path.md`. Branch `curriculum/c1-plan-follows-path`,
worktree `learnanything-ad1`. Codex job `20261031-225454-osGoYy` (gpt-6.1-sol): four Medium findings and no High
ones. Each was reproduced with a failing test first (commit `4aa3a87099`: 5 of the 9 new tests failed at their
target assertions; the 4 others are guard tests that held before and after), then fixed in `508a1dbc27`.
Every model in the tests is a fake. No live or paid calls were made.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Refreshing a staged reading prevents the kill switch from restoring RW7b | fixed | `508a1dbc27` | `test_f1_after_a_refresh_withdrew_the_staged_reading_the_switch_still_restores_rw7bs` (failed before: the plan kept `ch_det`); guard `test_f1_a_started_replacement_reading_is_still_kept` |
| F2 | Medium | Turning the two path switches off separately leaves RW7b active | fixed | `508a1dbc27` | `test_f2_c1_off_then_rw7b_off_in_separate_reads_ends_on_the_orders_reading` (failed before: the reading stayed RW7b's `ch_det`); guard `test_f2_c1_back_on_after_its_switch_off_does_not_undo_the_transition` |
| F3 | Medium | Timestamp ordering can permanently miss a successful refresh | fixed | `508a1dbc27` | `test_f3_a_judgment_in_the_plans_own_second_is_adopted`, `test_f3_a_judgment_between_the_stale_read_and_the_plans_stamp_is_adopted` (both failed before); guard `test_f3_without_a_new_judgment_the_stale_plan_stays_and_reads_no_path` |
| F4 | Medium | A farther fresh deliverable prevents adoption of the nearer refreshed path | fixed | `508a1dbc27` | `test_f4_a_nearer_stale_deliverable_refreshed_is_adopted_over_the_farther_fresh_one` (failed before: Lay's `lay_char` stayed); guard `test_f4_a_nearer_one_still_stale_leaves_the_farther_ones_step` |

All tests are in `tests/test_curriculum_c1_codex_review_fixes.py`.

### What changed

- **F1** (`daily_plan/engine.py`). New `_live_reading_blocks`: every reading block except one with
  `PlannedBlock.withdrawn_path_reading` (a path reading ended unread with `reading_path_off`). Both
  `_move_plan_reading` (the switch's move) and `_deliverable_path_refreshed` use it for the "a reading began or
  ended" guard. A reading the learner started or finished still blocks every move. The block ended in memory
  also gets its outcome and reason, so the same reconcile sees it as withdrawn. The `records.py` docstring now
  says C1's refresh adoption also withdraws blocks.
- **F2** (`_reading_path_switched_off`). A v2 receipt whose `transition` is `deliverable_path_off` may take one
  more transition: to the order's reading (`reading_path_off`) once RW7b's path is off too, while the reading
  is unstarted. `transition` holds the latest move and `transitions` keeps both, in order. `transitions` is
  written only for a second move, so RW7b's v1 receipts and single-transition receipts are unchanged.
  Switching C1 back on does not undo a transition, and nothing follows a `reading_path_off` transition.
- **F3** (`deliverable_path.py`, `db/stores/deliverables.py`). The stale read records the identity of the
  newest judgment at the deliverable's depth: `store.latest_judgment_id` returns the ledger id of the newest
  judge row by insertion order. It is read before the cache lookup, so a judgment that lands between the two
  queries also changes it. The id goes into the receipt (`latest_judgment_id` on the stale entry and on each
  stale `consulted` entry). `judged_since(…, created_at)` is replaced by `judged_since_read(…, read_mark)`,
  which is true when the newest judgment's id has changed. No clock is involved. That covers a judgment in
  the plan's own second and one recorded between the build's stale read and the plan's creation stamp. In
  production ordering, that second case is adopted by the plan's first reconcile, in the same call as the
  build (the test asserts this).
- **F4** (`_deliverable_path_refreshed`). The gate now reads **every** stale `consulted` entry, whichever
  deliverable the build followed. After the paths are read again:
  - If the nearest fresh path belongs to a different deliverable than the build followed, the plan takes C1's
    choice: C1's step, or RW7b's choice (the receipt's `predecessor`) when that path has nothing left to plan,
    which is what a build would give now.
  - If the same deliverable as the build's is followed (the nearer one is still stale), nothing changes.
  - The receipt's `chosen_by` and `label` are recomputed as a build would compute them. When the target is the
    same section but the stored copy differs (for example C1's label over the order's), the reading now moves.
    Before, only the receipt changed, so the receipt and the split could disagree.

Docs: the stage record (decisions 6 and 8) and the as-built note in `spec_deliverable_curriculum_v1.md` §7.6 now
describe the identity gate, F4's adoption and the sequential switches.

### Codex's other notes

- *"The refresh-before-build test uses `deliverable_inline=True`"*: correct, it tests the job's quiet judgment.
  The production ordering (the job lands after the build has read the path stale) is now covered by
  `test_f3_a_judgment_between_the_stale_read_and_the_plans_stamp_is_adopted`. That test interleaves the
  judgment inside the build, without the inline flag.
- *"The refresh-adoption test advances five minutes and does not stage the fallback reading"*: covered now by
  F1's test (it stages the fallback reading, then adopts the refresh, then turns C1 off) and by F3's
  same-second test.
- *Upgrade, WAL and rebuild execution unverified (sandbox)*: unchanged by these fixes (no migration, no schema,
  no connection code). The stage gate ran them, and the landing gate runs the full suite.

## Gate (fix step)

Owner rule 2026-10-17: no full suite in this step. Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Iteration: `uv run pytest -n 6` on the C1 and RW7b plan files (`test_curriculum_c1_codex_review_fixes.py`,
  `test_curriculum_c1_plan_follows_path.py`, `test_rw7b_codex_review_fixes.py`, `test_rw7b_fix_round2.py`,
  `test_plan_follows_path.py`): **80 passed, 3 skipped** (owner-vault lane).
- Targeted gate: `flock /tmp/learnloop-fullsuite.lock … uv run pytest -n 6 -p no:cacheprovider` over the 115 files
  in `scratchpad/c1/fix_gate_files.txt`. These are every test file that imports or names the modules changed
  (`daily_plan.engine`, `daily_plan.records`, `source_retrieval.deliverable_path`, `db.stores.deliverables`, or
  the reading/deliverable path receipts), plus `test_architecture.py`; the mobile allowlist and the upgrade-chain
  files are among them. Result: **2817 passed, 12 skipped** (owner-vault lane and optional extras), 0 failed, in 29 min 18 s (`scratchpad/c1/fix_gate_pytest.log`).
- No migration, schema, DB/connection, config key, CLI, RPC, frontend or `src-tauri` change: the durability lane,
  the DB reference scripts, vitest/typecheck/build and cargo do not apply.

Test files run in the targeted gate (listed so the landing gate can be read against them): 

`tests/test_ad1_codex_rereview_fixes.py`, `tests/test_ad1_codex_review_fixes.py`, `tests/test_ad1_outside_and_cli.py`, `tests/test_ad23_contract.py`, `tests/test_ad23_fix_r5.py`, `tests/test_ad23_fix_r6.py`, `tests/test_ad23_fix_r7.py`, `tests/test_ad23_fix_r8.py`, `tests/test_ad23_fix_review.py`, `tests/test_ad23_intent_compose.py`, `tests/test_ad23_inversion.py`, `tests/test_ad23_owner_decisions.py`, `tests/test_ad23_pool_membership.py`, `tests/test_ad2_model.py`, `tests/test_ad2_serving.py`, `tests/test_ad3_monitoring.py`, `tests/test_ad3_reading.py`, `tests/test_ad3_subject_view.py`, `tests/test_adaptive_difficulty_ad1.py`, `tests/test_ad_epoch.py`, `tests/test_ad_guard_offer_receipts.py`, `tests/test_ad_guard.py`, `tests/test_ad_guard_reachable_reads.py`, `tests/test_architecture.py`, `tests/test_block_chooser_interface.py`, `tests/test_compare_keep_switch_off.py`, `tests/test_curriculum_c0b_landing.py`, `tests/test_curriculum_c1_codex_review_fixes.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_daily_plan_build.py`, `tests/test_daily_plan_composition.py`, `tests/test_daily_plan_kill_switch.py`, `tests/test_daily_plan_owner_decisions.py`, `tests/test_daily_plan_reentry.py`, `tests/test_daily_plan_replay.py`, `tests/test_daily_plan_review_regressions.py`, `tests/test_daily_plan_rpc.py`, `tests/test_deliverable_codex_review.py`, `tests/test_deliverable_curriculum_migration.py`, `tests/test_deliverable_path.py`, `tests/test_deliverable_rpcs.py`, `tests/test_deliverable_scope.py`, `tests/test_dl2_rw4b_keyed_pick_check.py`, `tests/test_e0_budget.py`, `tests/test_e0_review_round3.py`, `tests/test_evsi_staged_binding.py`, `tests/test_exam_protection_landing.py`, `tests/test_figures_switch_off.py`, `tests/test_hint_h2b_fix4.py`, `tests/test_intent_codex_rereview.py`, `tests/test_intent_codex_review.py`, `tests/test_intent_exclusion.py`, `tests/test_intent_fix_round4.py`, `tests/test_intent_fix_round5.py`, `tests/test_intent_fix_round6.py`, `tests/test_intent_fix_round7.py`, `tests/test_intent_goal_deadline.py`, `tests/test_intent_plan.py`, `tests/test_judge_routes.py`, `tests/test_learner_pick_proposal.py`, `tests/test_mcp_c1a_narrow.py`, `tests/test_mcp_tools.py`, `tests/test_method_explicit_upgrade.py`, `tests/test_mobile_allowlist.py`, `tests/test_mvp011_upgrade.py`, `tests/test_mvp014_upgrade.py`, `tests/test_mvp015_upgrade.py`, `tests/test_mvp016_upgrade.py`, `tests/test_mvp017_upgrade.py`, `tests/test_mvp018_upgrade.py`, `tests/test_mvp020_upgrade.py`, `tests/test_mvp021_upgrade.py`, `tests/test_mvp023_upgrade.py`, `tests/test_mvp024_upgrade.py`, `tests/test_plan_determinism_landing.py`, `tests/test_plan_determinism.py`, `tests/test_plan_follows_path.py`, `tests/test_reader_ca3_landing_ca5a.py`, `tests/test_reader_ca4_landing.py`, `tests/test_reader_ca5a_find_section.py`, `tests/test_reader_intentions.py`, `tests/test_reader_intent.py`, `tests/test_reader_rw4b_admission_idempotency.py`, `tests/test_reader_rw4b_fix6.py`, `tests/test_reader_rw7a_migration.py`, `tests/test_reader_tutor_switch_off.py`, `tests/test_reading_paths.py`, `tests/test_reading_step_switch.py`, `tests/test_router_card.py`, `tests/test_router_g1_feasibility.py`, `tests/test_router_g4_restraint.py`, `tests/test_router_g7_fallback.py`, `tests/test_router_presentations.py`, `tests/test_router_r1_composition.py`, `tests/test_router_r2a_landing.py`, `tests/test_router_r2a_serving.py`, `tests/test_router_r2b_serving.py`, `tests/test_router_r2c_retrieval.py`, `tests/test_router_r2c_teach_back.py`, `tests/test_router_why_copy.py`, `tests/test_rw7b_codex_review_fixes.py`, `tests/test_rw7b_fix_round2.py`, `tests/test_section_coverage_review.py`, `tests/test_section_coverage_rpcs.py`, `tests/test_serve_eligibility.py`, `tests/test_serve_eligibility_review.py`, `tests/test_source_service_spend_accounting.py`, `tests/test_source_service_spend_envelopes.py`, `tests/test_spend_controls.py`, `tests/test_t6_followup_review.py`, `tests/test_ux_phase4_feedback.py`, `tests/test_ux_phase4_landing.py`, `tests/test_voi_merge_composition.py`, `tests/test_voi_stopping.py`, `tests/test_voi_v2.py`.

## Fix round 2

Scoped verify of fix round 1: Codex job `20261101-003504-qjtNva` (gpt-6.1-sol), fix-round base `5440b79763`,
tip `abc0f008ae`: **NOT CLEAN**, five Medium findings and one Low. Four of the six are one class: incremental
state for refresh adoption and switch transitions (withdrawn-block history, transitions lists, judgment-identity
markers, consulted-stale bookkeeping) that misses some ordering. Under the orchestrator's stuck-loop rule the
orderings were not patched one by one; the mechanism was replaced with one invariant (orchestrator direction):

> **While the plan's reading block has no reading history, it is whatever a fresh build would choose right now.**

Every model in the tests is a fake. No live or paid calls were made. Not merged with main and not renumbered
(the landing does that: RW6b took mvp-0.39, so C1 becomes mvp-0.40 there).

### Verbatim findings

> NOT CLEAN
>
> Fix-round base: `5440b79763`. Source review only; no tests run.
>
> 1. **Medium — [engine.py:3281](/home/saturn/Documents/thinking/learnanything-ad1/src/learnloop/daily_plan/engine.py:3281): F1/F2 still fail after auto-completion.**
>    RW7b can offer no reading while book order offers one—for example, its path excludes every remaining section. Stage C1’s reading, turn C1 off, and exhaust the remaining practice. C1’s block is withdrawn and the plan auto-completes. Turning RW7b off afterwards cannot restore book order: this helper rejects *any* reading block, including the withdrawn one. **Fix:** use live reading blocks here too, retaining the checks against learner-stopped plans and actual reading history.
>
> 2. **Medium — [engine.py:3213](/home/saturn/Documents/thinking/learnanything-ad1/src/learnloop/daily_plan/engine.py:3213): F4 remains dependent on refresh completion order.**
>    Build with nearer A and farther B both stale. B’s Guide judgment finishes first; reconciliation adopts B and writes `refreshed`. A’s daily refresh then finishes while the reading remains unstarted, but this unconditional guard prevents adopting A. The farther deliverable wins for the rest of the plan. **Fix:** permit bounded adoption towards nearer refreshed deliverables, preserving refresh history and the started-reading guard.
>
> 3. **Medium — [deliverable_path.py:1721](/home/saturn/Documents/thinking/learnanything-ad1/src/learnloop/source_retrieval/deliverable_path.py:1721): F3’s marker is still read too late to cover every interleaving.**
>    It precedes the cache lookup, but follows `path_inputs`. The build can capture state K0; background coverage changes state to K1; a refresh for K1 commits; then the build reads its identity and misses the cache for K0. The stale receipt now records the already-successful K1 judgment. Subsequent `judged_since_read` checks remain false, permanently missing that refresh. **Fix:** capture the marker before gathering the inputs whose cache miss establishes staleness, with consistent depth handling.
>
> 4. **Medium — [engine.py:3228](/home/saturn/Documents/thinking/learnanything-ad1/src/learnloop/daily_plan/engine.py:3228): refresh adoption can withdraw a reading already being read.**
>    A prefetched reading has no `started_at`. If the learner opens that section through the Library and reads part of it, `note_reading_progress` records progress without setting `started_at`. A completed refresh therefore passes this guard and withdraws that block as unread, counting zero minutes. **Fix:** treat recorded reading progress as history in both refresh and movement guards.
>
> 5. **Medium — [deliverables.py:313](/home/saturn/Documents/thinking/learnanything-ad1/src/learnloop_sidecar/handlers/deliverables.py:313): a plain plan read can duplicate an in-flight judgment.**
>    Open a stale deliverable in the Guide, starting `_judge_path`, then make the day’s first plan read before it finishes. The daily job bypasses `_Work.judging` and sends another judgment for the same state. `judge` checks the cache before calling and again before writing; that second check prevents duplicate rows, not duplicate model calls or metered charges. **Fix:** share judgment coalescing between Guide and daily-refresh jobs.
>
> 6. **Low — [engine.py:3225](/home/saturn/Documents/thinking/learnanything-ad1/src/learnloop/daily_plan/engine.py:3225): an unsuccessful refresh leaves full rereads enabled indefinitely.**
>    A judgment can finish after learner state changes, leaving its path stale. Its identity differs from the receipt forever, so every subsequent reconciliation reruns `_deliverable_choice`, including library, coverage and learner-context reads. Returning at lines 3239–3242 never consumes that identity. This adds repeated synchronous work to ordinary plan reads. **Fix:** cache unsuccessful evaluations by judgment identity and relevant state revision, invalidating when either changes, without rewriting the plan on each read.

### The invariant, as built

- **Which plans.** A plan whose receipt is C1's (`reading_path_plan_v2`: a deliverable path was in play at the
  build) follows `engine._reading_follows_fresh_choice` on every reconcile. A plan built with either switch off
  carries RW7b's v1 receipt or none and keeps RW7b's own rule (`_reading_path_switched_off`, now main's code again),
  so G-C4 holds: a plan built off is RW7b's or the order's byte for byte, and for it the fresh choice equals the
  predecessor's, so nothing moves.
- **Reading history** (`_reading_has_history`): a live reading block (a path reading withdrawn unread is none)
  with `started_at`, an end (completed, or ended any other way: kept, as RW7b keeps it), or recorded reading
  progress (`note_reading_progress`); or progress on the staged section since it was staged: the receipt's
  `staged_progress` (the section's `spans_seen` and completion when the reading was staged, at the build and at
  each move) against the section's row now. Progress only grows, so any difference is reading. With history,
  nothing moves (switch changes, refreshes, nothing).
- **The fresh choice** (`_fresh_reading`): the build's own selection, now one function the build also calls: the
  exam predicate (unreadable: no step), DL2's intent per reading, then C1's nearest fresh deliverable, else RW7b's
  path, else the order, under the current switches and freshness. No model call.
- **The move.** Equal to the staged reading: nothing is written. Different: the unstarted live blocks end unread
  (`reading_path_off`, no minutes), the split takes the new reading and its minutes (`_move_plan_reading`), and
  the receipt keeps its v2 keys for the latest choice (`predecessor`, `chosen_by`, `label`,
  `same_as_predecessor`, `paths`, `deliverable`, `rw7b`; `_choice_fields` fills them from RW7b's v1 receipt or
  the order when C1 is off) plus a new `staged_progress` and one entry in `moves`. `moves` is bounded by
  structure (the first move and the latest, no constant); `move_count` counts every move. A move's reason is
  `deliverable_path_moved` (C1 on), `deliverable_path_off` (C1 off, RW7b on) or `reading_path_off` (both off),
  and it records the switches as read.
- **Closed plans.** A plan that closed by itself only for want of a reading (`_closed_for_want_of_path_reading`,
  now over live blocks: a withdrawn block is no reading) reopens when the fresh choice is a reading; the move
  records `reopened`. A plan the learner ended stays ended.
- **Cost** (`daily_plan/reading_choice.py`, `_remembered_fresh_reading`). The choice is memoized per database on a
  fingerprint of its inputs, taken **before** any input is gathered: the switches (and a hash of the whole
  config), the vault's goals (each dumped) with their days left, the local and UTC dates, DL1's daily minutes
  (all from the engine), and cheap counters over every table the choice reads: `COUNT(*)`, `MAX(rowid)` and
  `MAX(updated_at)` per table, the newest rowid of a book's units, blocks and assets, and sums for the tables
  rewritten in place (section progress, mastery, capability evidence) and the reader events the choice reads.
  The list is a `sqlite3` authorizer trace of the choice over C1's fixtures plus the evidence ledgers (attempts,
  the judgment ledger). An entry also holds a weak reference to the loaded vault object (the sidecar replaces it
  on every reload). A hit returns exactly what the computation returned (copies). A choice made while protection
  or a consulted path could not be read stands for that read and is never memoized. On C1's fixture the
  fingerprint costs about 11 ms against about 620 ms for the full choice.
- **One coalescing set** (`learnloop_sidecar/handlers/deliverables.py`). `_Work.judging` (keyed by deliverable,
  depth and path state key; the state key already names the depth) is the one in-flight set: the Guide's
  `_judge_path` marks it as before, and the daily refresh now enters it through `_claim_path`, handed to
  `deliverable_path.refresh_for_plan(in_flight=…)`. A refresh finding the Guide's key running sends nothing
  (`coalesced`); a Guide open finding the refresh's running shows `judging` and starts nothing. The refresh stays
  quiet (`plan_fallback.quiet()`), plan route only, once a local day, and leaves no failure for the Guide to show.

### Removed

- `_deliverable_path_refreshed` (refresh adoption by judgment identity) and the receipt's `refreshed`.
- `_path_switch_target` and the v2 branches of `_reading_path_switched_off`: the `transition` /
  `transitions` guards for sequential switch changes on C1 plans.
- The judgment-identity markers: `deliverable_path.judged_since_read`, `DeliverablePlanPath.latest_judgment_id`
  and its receipt key, `_consulted_entry`'s `latest_judgment_id`, `db.stores.deliverables.latest_judgment_id`
  (the store and `deliverable_plan_path` are back to their pre-round-1 reads).
- The consulted-stale scan (every stale `consulted` entry read on each reconcile).
- `records.DELIVERABLE_PATH_REFRESHED`, replaced by `DELIVERABLE_PATH_MOVED` (a move's reason with C1 on).
- `_live_reading_blocks` stays (now the history check's and the closed-plan check's), and
  `withdrawn_path_reading` keeps its meaning.

### How each finding is closed

| # | severity | closed by | test (fail-first against `abc0f008ae`) |
|---|---|---|---|
| 1 | Medium | The closed-plan check reads live blocks only, and the invariant moves a reading with no history wherever the switches put the fresh choice, reopening a plan that closed for want of a reading. Learner-stopped plans and real reading history still keep the plan as it is | `test_m1_auto_completed_after_c1_off_then_rw7b_off_reopens_with_the_orders_reading` (failed before: `done`, never reopened); guard `test_m1_a_plan_the_learner_ended_stays_ended` |
| 2 | Medium | No "recorded once" guard is left: each reconcile without history compares the staged reading with the fresh choice, which is the nearest fresh deliverable whatever order the judgments land in | `test_m2_farther_refreshed_first_then_nearer_ends_on_the_nearer_step` (failed before: stayed on B's `lay_char`) |
| 3 | Medium | No marker: the fresh choice's fingerprint is taken before any input is gathered, so the coverage-side change and K1's judgment landing during the build change the next fingerprint, and the next reconcile (the build's own, in the same call) recomputes and takes K1's step | `test_m3_a_k1_judgment_committed_between_the_builds_inputs_and_its_lookup_is_taken` (failed before: stayed on the order's `ch_eigen`) |
| 4 | Medium | Recorded reading progress is reading history: a block's `reading_progress`, and the staged section's progress against the receipt's `staged_progress` (a Library reading before any block exists). Such a reading never moves, and its minutes count when it ends | `test_m4_a_prefetched_block_read_in_the_reader_is_never_moved_and_its_minutes_count` (failed before: withdrawn, a new block), `test_m4_a_staged_section_read_through_the_library_before_its_block_exists_is_kept` (failed before: moved to `ch_det`) |
| 5 | Medium | One coalescing set for the Guide's judgments and the daily refresh (`_Work.judging`, `_claim_path`, `refresh_for_plan(in_flight=…)`) | `test_m5_a_plan_read_while_the_guides_judgment_runs_sends_no_second_call`, `test_m5_a_guide_open_while_the_daily_refresh_runs_sends_no_second_call` (both failed before: 2 fake calls) |
| 6 | Low | The fresh choice is memoized on its inputs' fingerprint (judgment ledger and every state revision it reads among them); a read whose inputs did not change recomputes nothing and, moving nothing, writes nothing | `test_l6_a_path_stale_after_its_refresh_is_not_chosen_afresh_on_every_read` (failed before: 5 full choices for 5 reads; now 1, and the plan row untouched); `test_l6_the_fingerprint_moves_with_a_judgment_a_switch_and_the_date`, `test_l6_a_memo_hit_returns_exactly_what_the_choice_computed`, `test_l6_a_choice_made_while_a_read_failed_is_never_kept` |

All in `tests/test_curriculum_c1_fix_round2.py` (13 tests). Against `abc0f008ae`'s sources 10 of them fail at
their target assertions (the fingerprint and memo tests also on the functions being new); the 2 learner-ended and
withdrawn-block guards held before and after; the read-failure test was added after that run.

Round-1 tests moved to the invariant (`tests/test_curriculum_c1_codex_review_fixes.py`, 9 tests): `refreshed` and
`transition` assertions now read `moves`; F2's "C1 back on does not undo the transition" became
`test_f2_c1_back_on_moves_the_unread_reading_back_to_c1s_choice` (the invariant: a build now would choose C1's
step); F3's "reads no path" guard now holds through the memo. In `tests/test_curriculum_c1_plan_follows_path.py`
the refresh test and the three switch-off tests read `moves`. The G-C4 parity tests and the upgrade and
activation tests are unchanged and green.

### Gate (fix round 2)

Owner rule 2026-10-17: no full suite in this step. Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, under `env -i` with an
empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Iteration: the C1, C1 fix and RW7b plan files (`test_curriculum_c1_fix_round2.py`,
  `test_curriculum_c1_codex_review_fixes.py`, `test_curriculum_c1_plan_follows_path.py`, `test_rw7b_fix_round2.py`,
  `test_rw7b_codex_review_fixes.py`, `test_plan_follows_path.py`): **93 passed, 3 skipped** (owner-vault lane).
- Targeted gate: `flock /tmp/learnloop-fullsuite.lock … uv run pytest -n 6 -p no:cacheprovider` over 120 files: round
  1's 115 plus every test file that names `daily_plan.engine`, `daily_plan.records`, `daily_plan.reading_choice`,
  `source_retrieval.deliverable_path`, `db.stores.deliverables`, the sidecar deliverables handler or a
  `curriculum.*` RPC, plus `test_architecture.py` and the new file. Tree `862df09e4d` (plus the rename of one test in
  the new file): **2830 passed, 12 skipped** (owner-vault lane and optional extras), 0 failed, in 30 min 39 s.
- No migration, schema, DB/connection, config key, CLI, RPC signature, frontend or `src-tauri` change: the
  durability lane, the DB reference scripts, vitest/typecheck/build and cargo do not apply. No new numeric
  constant (the `moves` bound is structural: first and latest).

Files: `tests/conftest.py`, `tests/daily_plan_fakes.py`, `tests/deliverable_fixtures.py`, `tests/router_mixture_helpers.py`, `tests/test_ad1_codex_rereview_fixes.py`, `tests/test_ad1_codex_review_fixes.py`, `tests/test_ad1_outside_and_cli.py`, `tests/test_ad23_contract.py`, `tests/test_ad23_fix_r5.py`, `tests/test_ad23_fix_r6.py`, `tests/test_ad23_fix_r7.py`, `tests/test_ad23_fix_r8.py`, `tests/test_ad23_fix_review.py`, `tests/test_ad23_intent_compose.py`, `tests/test_ad23_inversion.py`, `tests/test_ad23_owner_decisions.py`, `tests/test_ad23_pool_membership.py`, `tests/test_ad2_model.py`, `tests/test_ad2_serving.py`, `tests/test_ad3_monitoring.py`, `tests/test_ad3_reading.py`, `tests/test_ad3_subject_view.py`, `tests/test_adaptive_difficulty_ad1.py`, `tests/test_ad_epoch.py`, `tests/test_ad_guard_offer_receipts.py`, `tests/test_ad_guard.py`, `tests/test_ad_guard_reachable_reads.py`, `tests/test_architecture.py`, `tests/test_block_chooser_interface.py`, `tests/test_compare_keep_switch_off.py`, `tests/test_curriculum_c0b_landing.py`, `tests/test_curriculum_c1_codex_review_fixes.py`, `tests/test_curriculum_c1_fix_round2.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_daily_plan_build.py`, `tests/test_daily_plan_composition.py`, `tests/test_daily_plan_kill_switch.py`, `tests/test_daily_plan_owner_decisions.py`, `tests/test_daily_plan_reentry.py`, `tests/test_daily_plan_replay.py`, `tests/test_daily_plan_review_regressions.py`, `tests/test_daily_plan_rpc.py`, `tests/test_deliverable_codex_review.py`, `tests/test_deliverable_curriculum_migration.py`, `tests/test_deliverable_path.py`, `tests/test_deliverable_rpcs.py`, `tests/test_deliverable_scope.py`, `tests/test_dl2_rw4b_keyed_pick_check.py`, `tests/test_e0_budget.py`, `tests/test_e0_review_round3.py`, `tests/test_evsi_staged_binding.py`, `tests/test_exam_protection_landing.py`, `tests/test_figures_switch_off.py`, `tests/test_hint_h2b_fix4.py`, `tests/test_intent_codex_rereview.py`, `tests/test_intent_codex_review.py`, `tests/test_intent_exclusion.py`, `tests/test_intent_fix_round4.py`, `tests/test_intent_fix_round5.py`, `tests/test_intent_fix_round6.py`, `tests/test_intent_fix_round7.py`, `tests/test_intent_goal_deadline.py`, `tests/test_intent_plan.py`, `tests/test_judge_routes.py`, `tests/test_learner_pick_proposal.py`, `tests/test_mcp_c1a_narrow.py`, `tests/test_mcp_tools.py`, `tests/test_method_explicit_upgrade.py`, `tests/test_mobile_allowlist.py`, `tests/test_mvp011_upgrade.py`, `tests/test_mvp014_upgrade.py`, `tests/test_mvp015_upgrade.py`, `tests/test_mvp016_upgrade.py`, `tests/test_mvp017_upgrade.py`, `tests/test_mvp018_upgrade.py`, `tests/test_mvp020_upgrade.py`, `tests/test_mvp021_upgrade.py`, `tests/test_mvp023_upgrade.py`, `tests/test_mvp024_upgrade.py`, `tests/test_plan_determinism_landing.py`, `tests/test_plan_determinism.py`, `tests/test_plan_follows_path.py`, `tests/test_reader_ca3_landing_ca5a.py`, `tests/test_reader_ca4_landing.py`, `tests/test_reader_ca5a_find_section.py`, `tests/test_reader_intentions.py`, `tests/test_reader_intent.py`, `tests/test_reader_rw4b_admission_idempotency.py`, `tests/test_reader_rw4b_fix6.py`, `tests/test_reader_rw7a_migration.py`, `tests/test_reader_tutor_switch_off.py`, `tests/test_reading_paths.py`, `tests/test_reading_step_switch.py`, `tests/test_router_card.py`, `tests/test_router_g1_feasibility.py`, `tests/test_router_g4_restraint.py`, `tests/test_router_g7_fallback.py`, `tests/test_router_presentations.py`, `tests/test_router_r1_composition.py`, `tests/test_router_r2a_landing.py`, `tests/test_router_r2a_serving.py`, `tests/test_router_r2b_serving.py`, `tests/test_router_r2c_retrieval.py`, `tests/test_router_r2c_teach_back.py`, `tests/test_router_why_copy.py`, `tests/test_rw7b_codex_review_fixes.py`, `tests/test_rw7b_fix_round2.py`, `tests/test_section_coverage_review.py`, `tests/test_section_coverage_rpcs.py`, `tests/test_serve_eligibility.py`, `tests/test_serve_eligibility_review.py`, `tests/test_source_service_spend_accounting.py`, `tests/test_source_service_spend_envelopes.py`, `tests/test_spend_controls.py`, `tests/test_t6_followup_review.py`, `tests/test_ux_phase4_feedback.py`, `tests/test_ux_phase4_landing.py`, `tests/test_voi_merge_composition.py`, `tests/test_voi_stopping.py`, `tests/test_voi_v2.py`.
