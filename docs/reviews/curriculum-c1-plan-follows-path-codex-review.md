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
