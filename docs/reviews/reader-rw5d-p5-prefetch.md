# Reader RW5d P5: figures ahead of need (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2, phase P5: §6.9, §10b, §12.3, §13.2b, §14, §15, gates G-SM27..G-SM30. The as-built note is in §14.
- **Branch:** `reader/rw5d-p5-prefetch` in `learnanything-dl2`, base `1a33bb5db3` (main: TE1 + C4, mvp-0.41, migration 234).
- **Migration:** `236_figure_prefetch.sql` on the branch; followups-nov2 claimed 235. **Landed as `237_figure_prefetch.sql`** after follow-ups Nov 2's 235 and TE1b's 236 (see "Landing onto main").
- **Head fixture:** `fixtures/migration_head_236` on the branch, renamed from `migration_head_234` (README section added; every hard-coded path, 55 files, renamed; `SCHEMA_HEAD = 236` in both DB reference scripts). **Landed as `migration_head_237`**, rebuilt from main's 236 head (see "Landing onto main").
- **Switch:** `figures.prefetch_enabled`, **default on** (Q21's recommended default, accepted by the owner's standing decision of 2026-10-12; first shipped off, corrected by the Codex review's F15, `docs/reviews/reader-rw5d-p5-prefetch-codex-review.md`). Caps `[figures.prefetch] max_daily_builds = 10`, `max_daily_render_minutes = 30` (`keep`).
- **New route:** `ai.routing.figure_prefetch_judge` (unset: the active provider, the plan under T1). Not in `METERED_PRICE_SETTINGS`, so never offered OpenRouter; a non-subscription route is never called.
- **Successor:** none (§1).
- **Live calls:** none. Every model in the tests is a fake (the judge, the figure author, the power reader, the pause reader). No paid or CLI command ran against any vault. The only database work outside pytest was the head-fixture rebuild on a backup-API copy under `fixtures-local/p5-head236/` and the DB reference scripts, all under `env -i` with empty, existing HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

## 1. Successor decision (`docs/algorithm-change-playbook.md` step 1): no successor

| Change | Persisted meaning? |
|---|---|
| Background builds (origin `prefetch`, `build_mode` prefetch) | **No.** They change *when* a figure exists. Figures are content: scoring, scheduling, projection, serving, grading and evidence read none of them (the `evidence-never-reads-figures` contract). An opened prebuilt figure is any figure (tier 1 outside an attempt, P3's hint-equivalent inside one). |
| `figure_prefetch_decisions`, `plan_usage_pauses` | **No.** RAW_LEDGER, read only by `learnloop.figures` (the decision model, the report). `tests/test_figures_prefetch_boundary.py` pins that no evidence, scheduling, plan, hint or AD module names them (AD's table classes name them only to deny them). The decision model predicts opening behaviour, outside the learner model (SM8). |
| The plan trigger | **No.** `get_daily_plan` builds and returns the plan exactly as before; afterwards a background trigger reads the stored plan. The plan never reads figures. |
| A prebuilt figure making P3's `explore_figure` precondition true sooner | **No:** which help is offered, not evidence (P3's ruling). |

The defaults snapshots moved, all 32, only because the effective config gains the keys; recomputed with `defaults_fingerprint_for_version` (a second pass changes none).

## 2. What P5 ships

### 2.1 The service (`src/learnloop/figures/prefetch.py`, a composition layer)
One pass per trigger: candidates → filters → decide → log → builds → outcomes. Nothing imports it back but `learnloop_sidecar/prefetch_runtime.py` (pinned; the frozen-cycles contract ignores its two function-local reads of the stored day plan and a lesson's stored plan on that promise).

**Triggers (§10b.2)**, queued by `prefetch_runtime.notify` (returns at once; one drain thread per context on `ctx.background_jobs`, so a close cancels and joins it):

| Trigger | Hook | Candidates | Goal |
|---|---|---|---|
| `plan` | `get_daily_plan`, after the view is built (`_schedule_prefetch`) | the stored plan's reading block's section | section judge |
| `section` | `reader.mark_section_progress` (after keep-ahead) | the next section in book order with no withheld span | section judge |
| `offer` | `reader.ask` (tutor; not on a cold administration) and `reader.library_job` when done (organizer) | `offered_spans` (the press's own ledger-confirmed check), anchor-only, once per offer | none |
| `lesson` | `lesson.turn` when the lesson has a plan | plan nodes not in `state.landed`, on their delivered passages (≤ 8 spans of the first passage's reading) | the node's `visual.goal_text` when it carries one (`goal_author` teacher), else anchor-only |
| `gap` | the plan and lesson hooks, and `PostAttemptWorker.after_gaps` after a gap drain | open misconceptions and learner-text gaps on the stored plan's and open lessons' topics (`learner_state.open_gap_statements`: the author's protection-filtered read, with ids) | gap judge |

**The judge (`figure_prefetch_judge`)**: listwise; section mode gets one section's blocks with exam and held-out spans removed (`withheld_message` per block) and no learner data; returns at most `PREFETCH_SECTION_CANDIDATES` (3) blocks with an optional goal and `p_open`. Unknown ids, duplicates, more than three, or `p_open` outside 0..1 are refused and asked once more with the problems in the context; a second bad answer decides nothing. Cached as a `judgment_ledger` receipt (task `figure_prefetch_judge`, keyed by the section's content hash and prompt version). Gap mode gets the statement, the topic and the passage text; never an attempt, item, key or rubric.

**Filters (code)**: the switches (`show_me` for goals); `withheld_message` on every span; the blocks of any unresolved item of today's stored plan (`item_exclusions`); a shown figure already on this passage and goal; a request already decided whose horizon is open (`request_key`). The build repeats the protection (`check_request`).

**The decision (`figures/prefetch_model.py`, pure numerics)**: `EU = P(open) · W − C` in learner minutes (u.minute scales both terms, so the sign never depends on it).
- `logit P = m + d_kind + α·logit(p_open_content) + β_src`, ADF (`adf_numeric.adf_update`) over closed, built decisions in time order; `α ~ N(1,1)` (llm_content), `m ~ N(0,1.5²)` (legacy, debt), `d_kind ~ N(0,τ²)` and `β_src ~ N(0,σ²)` with τ, σ a posterior over `POOLING_GRID` (25 grid points, weights by each filter's log normalizer).
- `W`: log-normal mean of measured pressed latencies (rich tiers: request → stored row; quick tiers: the figure author's completed call durations in `model_call_receipts`), mixed by the trigger kind's measured prebuild tier mix, else the pressed mix; with no mix yet, the author call's duration (the wait every press has at least). Nothing measured: no W, decision `skip` (structural: no data, no prebuild).
- `C = P(pause | today's plan requests + this build) · blocked minutes per pause`; pause logistic priors −3 and 1.5, sd 2 (legacy, debt), filtered from `plan_usage_pauses` and the days' plan requests; blocked minutes measured (pressed plan calls failed inside pause windows × mean plan call latency). No pause measured: no cost (so until a pause is seen, every candidate with a W has EU > 0 and the caps alone cut the queue, in sampled-EU order).
- One Thompson draw decides; `propensity` = share of `POSTERIOR_DRAWS` (64) further draws with EU > 0; `posterior_digest` (sha256 of the posterior's state) and `model_version` logged.
- Then, in sampled-EU order: off mains → `deferred_power`; plan paused or the author route not the plan → `deferred_plan`; daily builds or render minutes used up → `capped`.

**Builds**: one at a time (`PREFETCH_CONCURRENT_BUILDS`); each waits for no foreground work (`figures/foreground.py`: the server marks the learner-facing methods in `FOREGROUND_METHODS`; the figure handler marks a pressed build's job), up to `FOREGROUND_WAIT_SECONDS`, then leaves the rest: decisions still to build are retried by the next pass (`pending_builds`). Each build rechecks the switch (the vault as loaded now) and the power, then calls `service.build_prefetch_figure` (origin `prefetch` under `quiet()`; its `FiguresGate` key adds the switch and its hold is `power.background_hold`, so the switch or unplugging stops it before its next request). The rich spawner is the background one (no grant) and only when `figure_rich_author` is a plan route; a prebuild's rich job holds on the same condition (`rich.run_rich_job`). The decision gets `request_id` and the figure's `input_hash`, set once.

**Outcomes (§10b.5)** at each pass: plan → the plan's day ended or it closed; section → `completed_at` on that section; lesson → `closed_at`; offer → the local day it was made has ended (see §4); gap → no longer open, or a newer plan was built. `opened` (a `figure_opened`/`attempt_figure_opened` event on the decision's figures after it), `asked` (unbuilt, and a pressed request later on the same passage), `neither`, `void` (the passage withheld now).

**Pauses**: each pass appends the plan session's latest usage limit to `plan_usage_pauses` once (by hit time), with the day's plan requests and known tokens.

### 2.2 The figure service and the rich job
- `build_prefetch_figure`; origin `prefetch` refused everywhere else (a ContextVar set only there); `_validated_prefetch` (an anchor of a book, no attempt host, region or revision; goal by `prefetch` or `teacher`).
- The `figure_requests` row: `build_mode` prefetch and `prefetch_decision_id`; the rich payload's `build_mode` prefetch (P2b's niced, capped render).
- Listing: with the switch off a prebuilt figure nobody pressed for is not listed; once a press reused it, it is listed like any figure. While on, a prebuilt figure is listed under its passage with the existing collapsed line ("▸ interactive version", §6.9): no frontend change.
- "Not right?" on a prebuilt figure is the learner's request on its passage (origin `selection`, keeping the stored goal and who wrote it).

### 2.3 `power_state()` (`figures/power.py`)
Linux sysfs (a machine battery discharging, or no mains/USB supply online, is battery; device-scope batteries ignored), power-profiles-daemon `power-saver` counts as battery, macOS `pmset`, Windows `GetSystemPowerStatus`; anything unreadable is battery (fail closed). `LEARNLOOP_POWER_STATE=mains|battery` pins it for copy runs.

### 2.4 Hosts
Desktop sidecar only: `notify` refuses a secondary context (the phone host and the hub service attach with `load_secondary`) and a vault with the switch off; then no runtime is made and nothing is read or written.

### 2.5 The report
`learnloop reader report --json` gains `figures.prefetch` with the switch on (composed by the CLI, `prefetch_ledger.add_report_block`; `reader_report.py` is untouched, so no `reader → figures` edge): decisions and outcomes by trigger, the opening and pause posteriors (prior → posterior), measured waits and tier mixes, blocked minutes per pause, pauses with and without prebuilds earlier that day, skipped for power, plan and caps, the mean propensity.

### 2.6 Registry, roles, references
- `params/parameter_registry.py`: inventory `figure_prefetch`, `figure_prefetch_model`, `figure_power`; every module constant registered (priors as `prior` with treatment, prior_basis and scale in the rationale; the rest `keep`); `_ConfigRule`s for the switch and the two caps.
- `db/table_roles.py`: both tables RAW_LEDGER; AD's `protected_tables`: both DENIED.
- Disclosure row `figures_prefetch` for the judge.
- DB/config references regenerated; leaf count 1123, table notes 371.

## 3. Gate (this step; the full suite runs once, in the landing gate)

Every pytest run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6` at most, one at a time.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 41 kept, 0 broken |
| pytest, migrations (26 files, list A) | 198 passed |
| pytest, contracts, registry, config, the new files (40 files, list B) | 1106 passed, 17 skipped, 1 xfailed, 3 failed (judge routes set, the SQL-owner rule, the boundary test: all fixed) |
| pytest, the areas touched (142 files, list C: every figure test, reader report, section progress, gap worker, daily plan, lesson, library job, rich job, config DTO, AD tables, the defaults-snapshot pins and upgrades) | 8196 passed, 9 skipped, 2 xfailed, 3 failed (AD column classes, TE1's defaults parity, the notes boundary: all fixed) |
| pytest, rerun after the fixes (the new files and every file that failed or pins what changed: `test_figures_prefetch.py`, `test_figures_prefetch_boundary.py`, `test_figure_prefetch_migration.py`, `test_architecture.py`, `test_judge_routes.py`, `test_ad_protected_tables.py`, `test_teacher_te1_successor.py`, `test_notes_never_read.py`, `test_registry_audit.py`, `test_table_roles.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py`, `test_cli_help_snapshot.py`, `test_reader_report.py`) | 156 passed |
| `uv run pytest -m durability tests/test_figure_prefetch_migration.py tests/test_migrations.py tests/test_teacher_te1_migration.py` | 2 passed, 45 deselected |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` (under `env -i`) | errors `[]`; vault validation passed |
| Frontend, `src-tauri` | not touched (no npm, vitest or cargo run) |

**List A:** `tests/test_figure_prefetch_migration.py`, `tests/test_ad1_migration.py`, `tests/test_ad23_migration.py`, `tests/test_approach_maps_schema.py`, `tests/test_deliverable_curriculum_migration.py`, `tests/test_help_assist_work_md_migration.py`, `tests/test_help_assist_figures_migration.py`, `tests/test_help_assists_schema.py`, `tests/test_learner_claim_application_migration.py`, `tests/test_learner_notes_vault_origin_migration.py`, `tests/test_learner_note_source_kind_migration.py`, `tests/test_learner_notes_migration.py`, `tests/test_learner_claim_superseded_migration.py`, `tests/test_library_asks_migration.py`, `tests/test_reader_ca2_fix_orchestrator.py`, `tests/test_reader_rw3b_migration.py`, `tests/test_reader_session_digests_migration.py`, `tests/test_reader_rw7a_migration.py`, `tests/test_retrieval_spaces_migration.py`, `tests/test_rw2d_receipts_migration.py`, `tests/test_route_rules_in_grader.py`, `tests/test_section_coverage_migration.py`, `tests/test_session_ownership_migration.py`, `tests/test_t1_batch_origin_migration.py`, `tests/test_teacher_te1_migration.py`, `tests/test_migrations.py`

**List B:** `tests/test_ad1_codex_review_fixes.py`, `tests/test_ad23_successor.py`, `tests/test_architecture.py`, `tests/test_attempt_content_state_successor.py`, `tests/test_cli_help_snapshot.py`, `tests/test_cold_retry_reschedule.py`, `tests/test_config_refactor.py`, `tests/test_coordinated_migrations.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_deliverable_codex_review.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_field_workbench_signals.py`, `tests/test_figure_prefetch_migration.py`, `tests/test_figures_prefetch_boundary.py`, `tests/test_figures_prefetch.py`, `tests/test_figures_show_me_codex_review.py`, `tests/test_judge_routes.py`, `tests/test_library_exercises.py`, `tests/test_lp_claim_fixes.py`, `tests/test_mobile_allowlist.py`, `tests/test_plan_follows_path.py`, `tests/test_public_tip_guards.py`, `tests/test_reader_ca2_one_ask.py`, `tests/test_reader_ca4_table_by_point.py`, `tests/test_reader_followups_successor.py`, `tests/test_reader_rw2b_review.py`, `tests/test_reading_paths.py`, `tests/test_rebuild_equivalence_review.py`, `tests/test_registry_audit.py`, `tests/test_rw2c_switch_off.py`, `tests/test_sidecar_contract.py`, `tests/test_sidecar_idle_threads.py`, `tests/test_sidecar_registry.py`, `tests/test_sidecar_serializer_snapshot.py`, `tests/test_source_roles.py`, `tests/test_table_roles.py`, `tests/test_teacher_te0_review_fixes.py`, `tests/test_tracked_fixture_databases.py`, `tests/test_ux_phase2_shell.py`

**List C:** `tests/ad23_fakes.py`, `tests/ad_reachable_reads.py`, `tests/background_owners.py`, `tests/library_ask_fixtures.py`, `tests/reader_tutor_fakes.py`, `tests/rw2c_base_sequence.py`, `tests/test_ad1_attempt_columns.py`, `tests/test_ad23_contract.py`, `tests/test_adaptive_difficulty_ad1.py`, `tests/test_ad_guard_offer_receipts.py`, `tests/test_ad_guard.py`, `tests/test_ad_guard_reachable_reads.py`, `tests/test_ad_projection.py`, `tests/test_ad_protected_tables.py`, `tests/test_batch3_landing.py`, `tests/test_compare_sources_keep.py`, `tests/test_curriculum_c1_codex_review_fixes.py`, `tests/test_curriculum_c1_fix_round2.py`, `tests/test_curriculum_c1_fix_round3.py`, `tests/test_curriculum_c1_fix_round4.py`, `tests/test_curriculum_c1_fix_round5.py`, `tests/test_curriculum_c1_landing.py`, `tests/test_daily_plan_kill_switch.py`, `tests/test_daily_plan_reading.py`, `tests/test_daily_plan_reentry.py`, `tests/test_daily_plan_review_regressions.py`, `tests/test_daily_plan_rpc.py`, `tests/test_deliverable_curriculum_migration.py`, `tests/test_diagnosis_input_provenance.py`, `tests/test_figure_grammar.py`, `tests/test_figure_label_wording.py`, `tests/test_figure_offers.py`, `tests/test_figure_panels.py`, `tests/test_figure_predictions.py`, `tests/test_figure_property.py`, `tests/test_figure_region.py`, `tests/test_figure_requests_migration.py`, `tests/test_figure_revisions.py`, `tests/test_figure_rich_contract.py`, `tests/test_figure_rich_failed_correction_durable.py`, `tests/test_figure_rich_job.py`, `tests/test_figure_rich_rereview_fixes.py`, `tests/test_figure_rich_review_fixes.py`, `tests/test_figure_rich_rpc.py`, `tests/test_figures_codex_review.py`, `tests/test_figures_final_round.py`, `tests/test_figures_fix_round2.py`, `tests/test_figures_fix_round3.py`, `tests/test_figures_fix_round4.py`, `tests/test_figures_fix_round5.py`, `tests/test_figures_help_codex_review.py`, `tests/test_figures_help.py`, `tests/test_figures_migration.py`, `tests/test_figures_rpc.py`, `tests/test_figures_rw5b_fix_round2.py`, `tests/test_figures_rw5b_review.py`, `tests/test_figures_scope_redesign.py`, `tests/test_figures_show_me.py`, `tests/test_figures_switch_off.py`, `tests/test_figure_verification.py`, `tests/test_help_assist_figures_migration.py`, `tests/test_help_assist_work_md_migration.py`, `tests/test_hint_kill_switch.py`, `tests/test_intent_codex_rereview.py`, `tests/test_learner_blindness_relax.py`, `tests/test_learner_data_relax_2.py`, `tests/test_learner_notes_migration.py`, `tests/test_learner_note_source_kind_migration.py`, `tests/test_learner_notes_vault_origin_migration.py`, `tests/test_learner_report_superseded.py`, `tests/test_learner_text_gaps_flow.py`, `tests/test_learner_text_gaps_rereview.py`, `tests/test_learner_text_gaps_review.py`, `tests/test_library_ask.py`, `tests/test_library_ask_review.py`, `tests/test_method_explicit_upgrade.py`, `tests/test_mvp010_upgrade.py`, `tests/test_mvp011_upgrade.py`, `tests/test_mvp013_upgrade.py`, `tests/test_mvp014_upgrade.py`, `tests/test_mvp015_upgrade.py`, `tests/test_mvp016_upgrade.py`, `tests/test_mvp017_upgrade.py`, `tests/test_mvp018_upgrade.py`, `tests/test_mvp020_upgrade.py`, `tests/test_mvp021_upgrade.py`, `tests/test_mvp022_upgrade.py`, `tests/test_mvp023_upgrade.py`, `tests/test_mvp024_upgrade.py`, `tests/test_notes_never_read.py`, `tests/test_plan_determinism.py`, `tests/test_plan_first_transport_offer_grants.py`, `tests/test_plan_first_transport_offer_grants_r5.py`, `tests/test_plan_first_transport.py`, `tests/test_post_attempt_worker.py`, `tests/test_reader_branches.py`, `tests/test_reader_ca3_codex_round3.py`, `tests/test_reader_cues_cli_report.py`, `tests/test_reader_cues.py`, `tests/test_reader_inquiry_kill_switch.py`, `tests/test_reader_inquiry_status.py`, `tests/test_reader_intent.py`, `tests/test_reader_qualified_span_keys.py`, `tests/test_reader_recap.py`, `tests/test_reader_recap_review.py`, `tests/test_reader_reconnect.py`, `tests/test_reader_report.py`, `tests/test_reader_rw1b_review.py`, `tests/test_reader_rw1c_review.py`, `tests/test_reader_rw3a_landing.py`, `tests/test_reader_rw3b_review_fixes.py`, `tests/test_reader_rw5d_p4a_figures_follow.py`, `tests/test_reader_rw6b_p2_landing.py`, `tests/test_reader_source_identity_guard.py`, `tests/test_reader_tutor_offers.py`, `tests/test_reader_tutor_switch_off.py`, `tests/test_reader_wrap_up.py`, `tests/test_reading_request_sweep.py`, `tests/test_reading_step_switch.py`, `tests/test_recurrence_commands.py`, `tests/test_regrade_contract_successor.py`, `tests/test_router_r2a_serving.py`, `tests/test_router_r2bc_landing.py`, `tests/test_router_r2b_serving.py`, `tests/test_rw4_kill_switches.py`, `tests/test_rw7b_codex_review_fixes.py`, `tests/test_rw7b_fix_round2.py`, `tests/test_salience_firewall.py`, `tests/test_section_coverage_migration.py`, `tests/test_serve_eligibility_review.py`, `tests/test_sidecar_close_cancels_jobs.py`, `tests/test_sketch_service.py`, `tests/test_teacher_te1_migration.py`, `tests/test_teacher_te1_successor.py`, `tests/test_ux_phase1_add_source.py`, `tests/test_ux_phase1_finish.py`, `tests/test_ux_phase1_landing.py`, `tests/test_ux_phase1_round2_rereview.py`, `tests/test_ux_phase1_round2_review.py`, `tests/test_ux_phase1_usability_round1.py`, `tests/test_ux_phase4_feedback.py`, `tests/test_whole_comparison_reuse_provenance.py`

## 4. Deviations from the spec, and why
*(Updated by the Codex review fixes, `docs/reviews/reader-rw5d-p5-prefetch-codex-review.md`: the default is now on (F15); the offer horizon is the reading session's end or the local day's, whichever is first (F9); known tokens are in the load (F14); lesson candidates are planned visuals only (F8). Items 1, 3, 4 and 6 below are superseded where they say otherwise.)*

1. **Default off**, not Q21's on: the stage brief's instruction. Off is rev 1 exactly. *(Superseded: on, F15.)*
2. **The gap passage** comes from the topic's own provenance spans (`build_cross_source_spans`, the explain intent's first list), not `find_sources_for_caller`: retrieval can make hosted (metered) embedding or rewrite calls, and a prebuild is never metered.
3. **The offer horizon** is the end of the local day the offer was made (the reading session ends by then at the latest); the reader has no durable "thread closed" record to read.
4. **The plan load** is the day's plan requests; known tokens are recorded with each pause but not yet in the model (tokens are reported for some routes only, §10b.3).
5. **`void` for the switch going off** is not written: with the switch off nothing runs, so nothing is written (byte-identical); a row whose horizon passed meanwhile closes at the next pass by its horizon.
6. **Lesson planned visuals**: TE1's `PlanNodeV1` has no `visual` field yet (P4b, in flight, adds teacher visuals). The trigger prebuilds a node's passages anchor-only, and takes `visual.goal_text` whenever a stored node carries it.
7. **RW7b's path** is not consulted for the next section (book order only, skipping withheld sections).

## 5. Owner items
- The P5 checkpoint: a week of prefetch on the desktop with the report's `prefetch` block (opens versus builds, pauses, skipped for power); `figures.prefetch_enabled` ships on (Q21), and the checkpoint may turn it off.
- The legacy priors (`KIND_PRIOR_*`, `PAUSE_*`) are LP debt (LP §3.3).

## 6. Open items
- With no pause yet observed, C = 0, so every candidate with a measured wait builds up to the daily cap; the Thompson draw then orders rather than gates (spec-faithful; the caps are the guardrail).
- Quick-tier W is read from every completed `figure_author` call in `model_call_receipts` (the paid-call wrapper records each one, owner `figure_author`, pressed or prebuilt alike: the same call, the same wait). A prebuilt call therefore also measures W; that is the duration a press would have waited, so it is kept.
- P4b (teacher visuals) and followups-nov2 both touch `figures/service.py`; merge at landing.

## Landing onto main

Landed on branch `reader/rw5d-p5-prefetch` in `learnanything-dl2`, on top of main `1d244af053` (TE1b, mvp-0.43, migration 236). Main is an ancestor of the tip, so the orchestrator fast-forwards. No successor (ruling R4).

### The R1 fix (F18), before the merges (`b5724c404b`)

Each test was written first and failed before the fix.

- **Backend (`figures/service.py`, `fuller_state`).** A prebuild's fuller version can have a rich intent that was never queued (no job). It now reports no fuller line (None, not `pending`) when background admission refuses it: figures ahead of need switched off, this machine not on mains, or its input held out (`_prefetch_intent_refused`). Foreground work only delays a build, so it is not a refusal. A fuller version built ahead of need that nobody pressed for carries `speculative: true`, whether its job is queued or not. The key is absent everywhere else, so no other view changes. `FigureFullerDto` gains `speculative?: boolean`.
- **Reader (`useFigures.ts`).** The fuller-polling branch counts a speculative fuller line only until `prefetchExpired`. The 20-minute prefetch lifetime clock now also starts when a speculative fuller line is pending. Pressed fuller lines keep their polling.
- **Tests.**
  - pytest, in `tests/test_figures_prefetch_review_fixes.py` ("Landing ruling R1"): not pending on battery, switched off or held out; a pressed fuller keeps its line and is not speculative; a queued speculative fuller is marked.
  - vitest, in `richFigure.test.tsx`: reads for a speculative fuller end after the lifetime; a pressed fuller keeps reading past it.
- **The re-review's F18 vitest was vacuous.** Its mock answered the same payload object on every read, so the poll stopped re-arming after two reads whether or not the bound worked. The polling vitests now answer a fresh payload per read and advance one interval per `act`, so the bound is what stops them.

### Merges and conflicts

1. **Main `de9a03763d` (P4b, teacher visuals), commit `31302532b3`.**
   - `figures/service.py`: `key_for` keeps both the prefetch switch (P5) and the lesson's `teacher.visuals` key (P4b). The goal-author check takes P4b's `teacher` entry and keeps P5's revision of a prebuilt figure.
   - `config/template.py`: both comment blocks are kept. The 32 defaults snapshots were recomputed with `defaults_fingerprint_for_version` after clearing `.pyc`; a second pass changed none.
2. **Main `f9bc4254b3` (follow-ups Nov 2, mvp-0.42, migration 235), commit `8828590eef`.**
   - The head fixture rename/rename (234 → 235 on main, 234 → 236 here) was resolved to main's `migration_head_235`. It was then renamed `migration_head_236` and rebuilt from it with only P5's migration applied.
   - The 55 conflicting tests and reference scripts took main's side. The branch's intent was reapplied: head paths, `SCHEMA_HEAD`, migration sets gaining P5's number, `P5_ADDED_OBJECTS` composed. Nov 2's own head test reads the new head.
   - TE1's defaults-parity test also pops P5's keys. The 33 snapshots were recomputed (second pass 0).
3. **R5, commit `d4c02ae062`** (below).
4. **Main `1d244af053` (TE1b, mvp-0.43, migration 236), commit `24d941ce27`.**
   - P5's migration was renumbered 237. The head fixture was rebuilt again from main's 236 head.
   - 21 conflicting tests took main's side, then the branch's intent was reapplied. TE1b aliases its objects under TE1's names, so the composed sets matched line for line. The one exception, `test_help_assist_work_md_migration.py`, was fixed by hand.
   - TE1b's defaults-parity test also pops P5's keys.
   - `config/template.py`: P5's comments sit beside TE1b's mvp-0.43 entry. The 34 snapshots were recomputed (second pass 0).
5. **Generated references.** Each time they took main's side and were regenerated: `db_generate_reference.py`; `db_validate_reference.py` (errors `[]`, prose leaf count 1127 in `Database.md` and `Configuration.md`); `validate_vault.py`; `desktop_generate.py` / `desktop_validate.py`; `module_validate.py`.
6. **A new import cycle, now allowed.** Combining P4b's `teacher → figures` edge with P5's `figures.prefetch → teacher` edges forms a cycle. The frozen-cycles contract now ignores `figures.prefetch -> teacher.visuals` and `figures.prefetch -> teacher.contracts`. Both imports are function-local; teacher never imports prefetch, and the boundary test pins it. lint-imports: 42 kept.

### Migration renumber (R4)

- `236_figure_prefetch.sql` became `237_figure_prefetch.sql`; its header comment and P5's "migration 236" mentions in `column_classes.py`, `protected_tables.py`, `table_roles.py`, the store and the ledger say 237.
- **Head fixture.** `fixtures/migration_head_237` was rebuilt from main's tracked, sanitized `migration_head_236` with only 237 applied:
  - backup-API copy under `fixtures-local/`, `UPGRADE_SCRATCH_COPY`;
  - checkpoint (0, 0, 0), `journal_mode=DELETE` (header 1/1), `integrity_check` ok, `foreign_key_check` empty;
  - no definition changed and every row is identical; only 237's 13 objects were added, with no rows;
  - the companion files are byte-identical to main's; README section added.
- **Paths and sets.** The 5 hard-coded paths (`db_generate_reference.py` names it 3 times), `SCHEMA_HEAD = 237`, and every composed migration set (237 appended). `tests/test_figure_prefetch_migration.py` is renumbered.

### R5 outcome: wired, a small adapter (`d4c02ae062`)

- **The candidate.** The lesson trigger reads P4b's real planned visual: `PlannedVisualV1`, with `goal` and delivered-passage `anchors`. It builds each node's candidate with P4b's own builder, `teacher.visuals.figure_request`, so the goal and grounding keys match the lesson step's request byte for byte. A candidate carries `grounding_keys`; its ledger anchor names the first book's spans.
- **The build.** The prebuild sends no passage, the keys as fixed grounding, goal author `teacher`, and no rich job. A lesson host is grammar and sketch only, so the input hash is the step's.
- **Supporting changes.**
  - `_validated_prefetch` accepts that form.
  - The filters check every grounding key: held out (`keys_withheld`), and an item's own passages over each key's context.
  - `already_built` matches the goal and keys.
  - At the lesson horizon, a step that delivered the prebuilt figure counts as `opened`.
- **Tests.** Through TE1's real `write_plan` and P4b's real request builder: the candidate equals P4b's request, the prebuild makes one author call, and the step that shows node n1's planned visual makes zero author calls. Its `figure_requests` row (origin `teacher`) names the prebuilt figure, and the decision closes `opened` when the lesson closes. A planned visual whose anchor is held out is no candidate. The earlier stand-in test now uses P4b's shape.

### Gate (tip `24d941ce27`; the later commits change one test's allowlist and this record)

| Command | Result |
|---|---|
| `uv run lint-imports --no-cache` | 42 kept, 0 broken |
| Full pytest (`-n 8`, worksteal, 10G scope, under `env -i`) | 24025 passed, 90 skipped, 47 xfailed, 2 failed, 1 error (43m 46s). See below. |
| Durability lane (`-m durability`) | 188 passed, 1 skipped |
| Owner lane: fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-p5/owner-lane` | 83 passed, 4 skipped, 2 failed: exactly the 2 known (`test_activity_backfill…duration`, `placement_fixture_copies[arxiv_v2]`) |
| Frontend: `npm install`, `typecheck`, whole vitest (`--maxWorkers=4`, 5G scope), `frontend:build` | ok; 260 files, 2473 passed; build ok |
| `cargo check` | not run: P5 changes nothing in `src-tauri` (the only diff there is TE1b's, already on main) |

The full suite's two failures and one error:

- **`test_codex_lockdown_round3.py::test_every_process_launch_site_is_approved` (a landing finding).** P5's `figures/power.py` has two process launches the security allowlist had never reviewed: `_profile` runs `powerprofilesctl get` (the tool resolved by `shutil.which`), and `mac_power_state` runs `pmset -g batt`. Both use fixed argv lists, no shell, `timeout=PROBE_TIMEOUT_SECONDS` and `check=False`. They parse only the power state, any failure reads as not on mains, and neither makes a model call. The branch's own gates never ran the full suite, so this surfaced only here. Both are now reviewed and added to `APPROVED_LAUNCH_SITES` with a comment; the file passes (16 passed).
- **`test_query_student.py::test_a_client_that_gives_up_never_stops_the_query_process` (failure plus its thread-guard teardown error).** It is not P5's: P5 touches neither local retrieval nor this test. The test starts the student server in a thread and connects as soon as the socket path exists; once the connection came before the listen (`ConnectionRefusedError`). Rerun alone it passed 7 of 8 times (the third of the first three runs failed the same way). It is a pre-existing race.

**Targeted runs before the gate.**
- After the Nov 2 merge and R5: 200+ files (figures, rich, prefetch, sketch, teacher and P4b, migrations, configuration and registry, contracts, upgrades, Nov 2's files), 3719 passed, 15 skipped, 9 xfailed.
- After the TE1b merge:
  - the migration and head set: 849 passed and 2 failed, both fixed and rerun green (44 passed):
    - an over-broad renumber that read TE1b's `names[236]` as `[236, 237]`;
    - TE1b's defaults-parity test needing P5's keys popped;
  - 126 figure, prefetch, teacher, router, Nov 2 and contract files: 2280 passed, 14 skipped.
- vitest on the Reader figure files and LessonScreen: 425 passed.

### Smoke on fresh owner copies

**Setup.** The driver is `fixtures-local/landing-p5-smoke/scripts/smoke.sh`, adapted from TE1b's.
- **Copies.** Fresh backup-API copies of the three mvp035 owner copies.
- **Environment.** `env -i` with an empty `HOME`, `CODEX_HOME` and config.
- **Audit hook.** It logs every process start and socket connect, and refuses non-loopback sockets and any Codex start.
- **Code.** `git archive` of main `1d244af053` and of the branch, each with `src/` and `migrations/`.
- **Prepared copies.**
  - **m**: main code, every AI route at the `127.0.0.1:9` blackhole (keys unset), upgraded `--to mvp-0.41`, `--to mvp-0.42`, then bare to mvp-0.43 (head 236).
  - **b**: the same under the branch code (head 237), prefetch on by default.
  - **boff**: b with `figures.prefetch_enabled = false`.
  - **bp**: branch code with the figure routes left on the vault's own ChatGPT-plan route (not signed in here) and the rest blackholed.
  - Each had its primary desktop load, `migrate_vault` (0 pending) and `rebuild-derived-state` (mvp-0.43).

**Results.**

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today, boff and b vs m | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Plan dump, boff and b vs m | payload (read, serve1, serve2, read2) byte-identical. The dump's only other difference: it lists every table named `plan%`, and P5's empty `plan_usage_pauses` exists only on the branch | same | same |
| `reader.figures` for three extractions, boff and b vs m | byte-identical | byte-identical | byte-identical |
| `figure_prefetch_decisions` / `plan_usage_pauses` rows after Today, plan and figures on boff and b | 0 / 0 | 0 / 0 | 0 / 0 |
| `rebuild --shadow` (b, boff, bp) | 0/0/0, live unchanged | 0/0/0, live unchanged | 0/0/0, live unchanged |

**The in-process pass (bp).** The sidecar runtime drained inline (`figure_prefetch_inline`), with power pinned to mains (`LEARNLOOP_POWER_STATE`). Triggers: `get_daily_plan`, which fires `plan` and `gap`; a `section` trigger on the vault's latest section progress; and a direct `offer` trigger on two blocks of a non-withheld section.
- **plan and gap.** No candidates: no reading block in today's plan, and no open gaps on the touched topics.
- **section.** "judge waiting: unavailable". The judge's plan route refused before any request: 0 judge calls, no socket.
- **offer** (anchor-only, no judge). linear_algebra and probability each logged 2 decisions with propensities, both `skip` with propensity 0.0: these copies hold no measured figure-author wait yet, so a build has no value to weigh. Nothing was built (0 figures, 0 requests). No candidate's anchor is withheld now. arxiv_v2 found no section with two unwithheld blocks, so it had no offer.
- **Totals.** 0 pauses; 0 new receipts.

**Audit across the whole smoke.**
- 12 databases compared with their base copies: **0 new `model_call_receipts`**.
- **0 socket connects**; 0 refused starts; no Codex process.
- The 30 process starts are all `powerprofilesctl get`, from the branch's power probe on the b copies' reads.
- After each close, the only thread left is `learnloop-reading-sweep`, on main's copies as on the branch's. No prefetch thread is left running.

### Rulings (verbatim)

- **R1 (F18):** "Fix at landing: a speculative (build_mode prefetch) fuller projection whose rich intent is not queued or running reports not pending when background admission refuses it (battery, switch off, held out), and the Reader's fuller-polling branch honours the same prefetch lifetime bound (prefetchExpired) for speculative figures. Pressed figures keep their current polling. Regression tests (pytest + vitest). No further review round."
- **R2 (F17):** "Low, accepted: a hidden prebuild that keeps hitting the plan's usage limit is retried on the next Reader open of its source, the next prebuild of the same input, or a press; losing one background retry costs only a later wait, never a wrong figure or spend. Record as an open item."
- **R3:** "figures.prefetch_enabled ships ON, per spec Q21 (owner-accepted RW5d recommendations); the stage brief's 'default OFF' is superseded by the spec. The owner's one-week checkpoint with the report's prefetch block stays an owner item and may turn it off. Daily cap 10 builds with a zero cost term until a plan pause is observed is accepted as specified."
  - **Owner decision (Nov 2), confirming R3:** "keep prefetch on".
- **R4:** "No successor (pinned by test_figures_prefetch_boundary). Migration renumber: followups-nov2 lands first (migration 235), then TE1b (migration 236); P5 takes the next free number after whatever is on main when you reach the full gate (expected 237), with the head fixture rebuilt from main's head plus only your migration."
- **R5:** "Lesson trigger vs P4b: P4b (teacher visuals) is already on main. After merging, wire the lesson trigger to P4b's real planned visual and make the prebuild's figure request byte-identical to the request teacher.visuals delivers for that node (same input hash), so a lesson visual reuses the prebuilt figure; a test through TE1's real write_plan and P4b's real request builder proves zero author calls on delivery. If this needs more than a small adapter, leave the lesson trigger building nothing and record it as an open item instead."

### Owner items

- **One week of prefetch on the desktop** (on by default; the owner decided "keep prefetch on"). Then read the `prefetch` block of `learnloop reader report --json`: opens versus builds, pauses, skipped for power and plan. The owner may switch it off (`figures.prefetch_enabled = false`).
- **Working vaults.** Upgrade through the chain to mvp-0.43, which brings migration 237: back up, run `learnloop upgrade`, then `rebuild-derived-state`.

### Open items

- **R2 (F17), hidden plan-wait retry.** After a quick re-failure, retry pacing refuses for 300 s while `prefetch_pending` is false, so the Reader stops reading before the retry is due. That background retry is lost. The next Reader open of the source, the next prebuild of the same input, or a press retries it.
- **F11.** The cue-density count of unpressed prebuilt lines is not shared with the margin marks.
- **The gap passage** comes from the topic's provenance spans, not retrieval (deviation 2).
- **The next section** ignores RW7b's path (deviation 7).
- **Plan load tokens.** Known tokens are in the load; routes that report no tokens count as an average request (F14).
- **The audit is unrelated to P5's correctness** but worth knowing: on the desktop, every Reader figures read with prefetch on (and every pass) calls `powerprofilesctl get` when the daemon is installed, the 30 starts above. It is a cheap read-only probe, and it is pinned off under `LEARNLOOP_POWER_STATE`.
- **Pre-existing, not P5's:** the `test_query_student` connect-before-listen race.
