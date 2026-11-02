# Reader RW5d P3: figures as a help kind (stage record)

> Codex review fixes: `docs/reviews/reader-rw5d-p3-figures-help-codex-review.md` (F1-F9 fixed; migration 232 also rebuilds `figure_predictions`).

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2, phase P3: §6.4, §11.2-§11.4b, §13.2, §14, and gates G-SM15..G-SM18. The as-built notes are in §11.4 and §14.
- **Branch:** `reader/rw5d-p3-figures-help` in `learnanything-merge2`, base `c0017b5740`.
- **Migration:** `232_help_assist_figures.sql`. 231 is curriculum C5's, on its own branch. The runner is set-based, so this renumbers at landing if needed; TE1 also carries a migration.
- **Head fixture:** `fixtures/migration_head_232`, renamed from `migration_head_230`.
- **Switch:** `figures.help_kind_enabled`, default true, classified in `params/parameter_registry.py`. It acts only under `figures.enabled` and `figures.show_me_enabled`.
- **Successor:** none (§1).
- **Live calls:** none. Every model in the tests is a fake: the figure author, the grounding retrieval, the Decider and the hint writer. No paid or CLI command ran against any vault. The only database work outside pytest was the head-fixture rebuild, on a backup-API copy under `fixtures-local/rw5d-p3/`, and the DB/desktop reference scripts, run under `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

## 1. Successor decision (`docs/algorithm-change-playbook.md` step 1): no successor

The question was whether the hint-equivalent fold change alters persisted meaning. It changes how attempts that used figure help are scored, so it was checked against step 1.

| Change | Existing attempts | New attempts | Persisted meaning? |
|---|---|---|---|
| The submit's fold counts `assist_kind = 'figure'` rows: the answer box's `_fold_rows`, the keyless attach, the workbench fold and ids, the workbench window | No `figure` row can exist before migration 232: the old `assist_kind` CHECK refused it, and replay and rebuild never read `help_assists` (G-H10). Every recorded attempt folds, replays and rebuilds exactly as before | One figure adds one to `hints_used`, at level 2, with that field's existing meaning: help that writes none of the solution. Dampening, the eligibility decision, the FSRS cap and the activity class all read `hints_used` as they already do | **No** |
| The take step on a check on your own | Nothing recorded is reread | It is CA2's take step (`mvp-0.34`, kill switch `ask.cold_help_converts`), offered only where the hint ladder's is (§3.3). Below `mvp-0.34`, or with that switch off, a due cold follow-up offers no take step and the figure is refused, so no attempt the predecessor refused is admitted | **No**: CA2's existing rule |
| `explore_figure` in the chooser | — | It changes which help is offered, not what evidence means. That is a kill switch with no successor, as the hints spec rules for its learned layer (§6.4 there) | **No** |
| The diagnoser's `+figures-v1` trace | Contexts without a figure trace render and hash as before, and the prompt version is unchanged | The `+workbench-v1` precedent | **No** |

Stop rule (spec §14): nothing here changes an existing attempt's classification beyond what `hints_used` already expresses. No `mvp-0.N` is minted. The defaults snapshots moved, all 31 of them, only because the effective config gains `figures.help_kind_enabled`. They were recomputed with `defaults_fingerprint_for_version` after clearing `.pyc` files, and a second pass changed none.

## 2. What P3 ships

### 2.1 The request on attempt hosts (§6.4, §7.1, §7.2)
- **`figure.request` with origin `ask`** (no longer reserved) takes an attempt host:
  - `hostRef.itemId` + `submissionId` + `sessionId`: the answer box;
  - `hostRef.workbenchSessionId` + `itemId`: a workbench problem bound to the item, checked as CA2's Ask checks it;
  - `hostRef.attemptId`: feedback.
- **The server derives everything.** A client never states its policy (`AttemptHost`, `_attempt_caller`):
  - an open attempt is caller kind `learner` under `assisted_practice` for the item, so `find_sources` never returns the item's own blocks or answer-overlapping passages (§8.3);
  - feedback is the item's post-attempt policy;
  - a submission that has committed since is feedback.
- **Refused:** an anchor, `readingAt` or any other origin with attempt references, an unknown item, an answer box without its key and session, and a lesson reference (P4).
- **No home.** The figure has `extraction_id` NULL (§13.1's CHECK). Its held-out recheck reads its retrieved keys. A homeless figure with grounding `none` is shown: nothing from any source was sent. Before, `row_withheld` refused every homeless figure with no keys.
- **Predictions** are kept under the first book the figure was grounded in (`prediction_home`). A homeless illustration shows none, since there is no passage to keep a prediction under. The reason is that `figure_predictions.extraction_id` is NOT NULL; the alternative was rebuilding that table too.
- **Quick figures only.** On an attempt host the build gets no rich spawner, so the menu is grammar or sketch: a rich pending line lists under a passage, and this figure has none. This narrows §11.4b and is recorded as open item 2.
- **"Not right?"** on an attempt-hosted figure re-resolves the host as it stands now: submitted since means free, and cold needs the stored take-step token. The new version is the same figure for the count.

### 2.2 The record, the fold and the reveal (§11.2, G-SM15)
- **Written as the figure goes out.** `record_attempt_figure` writes the row at the job's delivery (`deliver_figure`, which reads the host the job kept) and in `figure.open`. One transaction holds the row and the reveal. On any failure the figure is not shown (`help.status = not_recorded`), the same rule as a hint's reveal. Feedback writes nothing.
- **The row:** `assist_kind = 'figure'`, `level = 2`, `counted_by = 'server'`, `shown = 1`, the figure id, and the host's key. On the answer box that is the submission and practice session. On the workbench it is the problem and its `workbench:<id>` key, with the practice session filled at Submit by the existing bind.
- **One per figure per attempt.** Any unattached figure row of this attempt (by key or by workbench problem) whose figure has the same chain root means no new row. The chain root follows `supersedes_id` and `fuller_of_id`. Reading the job again, opening the figure again, asking the same words again and a "not right?" version add nothing.
- **The fold** is the hint service's existing one, widened by one SQL predicate (`HINT_EQUIVALENT_KINDS_SQL`), and the workbench fold gains `figures`. The submit's transactional refold and attach take the rows as they take hints. Nothing in `learnloop.attempts` imports the figure package (`evidence-never-reads-figures` is kept).
- **The reveal.** `figures.help.reveal_text` reads the figure's words: the values under text keys (what it demonstrates, assumptions, labels, titles, captions, annotations, prompts, choices) and a sketch's string literals. It adds a grammar figure's readouts and highlighted values at the defaults, as formatted. The overlap is the hints' own (`reveal_amount`: the tutor's overlap measure and the exact key). An overlap writes `tutor_answer` with basis `figure:<id>`, once per figure until the item's next attempt. A chooser-served figure's delivery (the hints handler's `_deliver`) uses the same text and basis.
  - The first draft read every string of the spec. Expressions, enums and span ids then gave about 0.5 overlap on unrelated figures, so it was narrowed to the spec's words, which is also what §11.2 names.

### 2.3 The cold take step (§11.3, G-SM16)
- **`figure.take_step`** (desktop only, a Tauri passthrough) converts the attempt first. It writes its figure row with `request = 'take_step'`; that row is the one hint-equivalent. It answers the row's id as the token, with the banner *Practice with help ◌ — you asked for a figure*. It is idempotent per attempt. On an open attempt it answers `needed: false`.
- **Cold** is the Ask panel's own derivation (`tutor_qa._item_cold`): an open cold follow-up, a held-out exam, or a "Check once" served cold. While cold and with no valid token, `_attempt_caller` marks the caller cold, so the policy is `cold_attempt` and the request (or `figure.open`) is refused with `take_step_required` before any job, model call or row. Before this, `caller_for` alone missed the "Check once" case; the stage tests caught it.
- **A token must name this attempt.** It must be a take-step row of the same item, unattached, under the same submission key or workbench problem. A crafted id is refused, and so is another attempt's token.
- **Where it is offered.** `take_step_available` offers it only where the hint ladder's take step is: a served check with the help header, or a due cold follow-up under CA2's conversion rule. It is never offered on an exam-reserved item or on a measured view whose safeguards refuse help (`cold_check`).
- **The first figure** binds its id onto the take-step row, so there is no second count. Later figures in the converted attempt carry the same token and each counts once.

### 2.4 `explore_figure` in the chooser (§11.4, G-SM17)
- **The kind.** `hints.kinds` gains `explore_figure` at level 2, labelled *a figure to explore*. It is outside `OFFERABLE`, so no taken rung, workbench rung or fallback order ever includes it. It is added only to a "More" press on the answer box, and only when the request's caller gave a `figure_provider`.
- **The provider is the sidecar's** (`handlers.hints._figure_provider`): the hint package never reads figures, and the frozen-cycles contract holds. It is given only while `figures.help_kind_enabled` is on, and it answers nothing on a cold item. Without a provider, the options, the record and the result are the predecessor's.
- **The precondition** (`figures.help.qualifying_figure`) takes the newest shown, drawable, unsuperseded figure (scan bound `QUALIFYING_SCAN = 200`, `keep`, registry-classified) where all of these hold:
  - its anchor, or its retrieved passages and reading positions, sit in a section that treats the item's LO, through provenance links or C0a coverage rows saying `introduces`, `develops` or `applies`, with the learner's correction standing;
  - none of its keys is in `item_exclusions` (the item's own exercise, solution or worked answer);
  - its words do not leak the key (`span_leaks_expected`);
  - it is not withheld now;
  - it is not one this attempt already opened.
- **The draw.** With the switch on and no figure qualifying, the record names the exclusion: `excluded["explore_figure@L2"] = "no_figure"`. A served one is a `figure` row with `hint_kind = 'explore_figure'`, the chooser's probabilities and the drawn option's propensity, and no writer call. Its result carries `figure` (absent from the wire otherwise) and no reply lines. Its line opens the figure through `figure.open`; the row already counts it, so opening it adds nothing.
- **The Decider's state** gains `figures_this_attempt`, only once a figure was opened, so every earlier state hashes as before. The kind's description is added to `_DESCRIBE`, and the question changes only when the option is present.

### 2.5 Outcomes, report, diagnoser (§11.4, G-SM18)
- **`help_outcomes`** (RW2c) adds `figure` to the help kinds while the switch is on: key `("figure", "asked" | "chooser")`, on the workbench and on the answer box. An answer-box figure has no continuation. Its attempt grade and later independent outcome come from the rows, as for bridges. Off, the read is RW2c's exactly: figure rows are excluded. It is pure and deterministic; the test computes it twice.
- **The hints report** groups figure rows as kinds automatically, with sample size and Wilson intervals. It adds a `figures` block: how each came (asked, chooser, take step), surfaces, attempts, outcome shares with intervals, later independent success, and an off-policy estimate marked `not_yet_measured`. The block is absent with no figure row.
- **The diagnoser.** `diagnosis/split/figure_trace.py` reads, by SQL only, the figures an attempt used, unless `figure_prediction_withheld` says one is held out now. For each it gives the goal and who wrote it, what it demonstrates, the tier and kind, and the predictions with the observed answer and "what changed?". It never includes the program. `CurrentAttempt.figure_trace` renders only when present, and the prompt version gains `+figures-v1` in both `jobs.py` and `contract.diagnosis_prompt_version`. The grader never sees any of it.

### 2.6 The desktop
- **`components/askFigures.tsx`** puts *show me ▸* (button and `alt+↵`) in the CA2 panel, docked and inline, while the snapshot sends `ask.figures`. The dim line says the cost before sending: *show me is free here*, *a figure on this counts as a hint*, or *a figure on this makes this practice with help ◌*.
- **On a check on your own,** sending calls `figure.take_step` first, then the request with its token. The host's banner changes to *Practice with help ◌ — you asked for a figure*, and the help record is read back. The record lists *a figure (counts as a hint)*, since the server's `help_record` includes figure rows.
- **The figure lands in the thread** at panel width, with *widen ↔*, through `FigureInline` and a panel controller for predictions and "not right?".
- **The hint panel** renders an `explore_figure` hint as one line, *▸ a figure to explore · "…" · open*, that opens the figure under it.
- **Off:** no `ask.figures`, no button, and `alt+↵` asks as before.
- **Supporting changes:** Tauri passthroughs `figure_take_step` and `figure_open` (`commands.rs`, `main.rs`), DTOs, and the mobile allowlist pin (desktop only).

### 2.7 Other changes
- The prompt contract gains `figures.help` only while the switch is on.
- The salience-only server events `attempt_figure_opened` and `figure_take_step` (`RW5D_SERVER_EVENTS`) carry ids, host and counted, never words.
- The spec's §11.4 and §14 carry the as-built notes.
- The DB reference was regenerated (prose leaf count 1111). The desktop catalog was regenerated (303 TS, ACTIVE 309; the validator's pinned counts were moved).

## 3. The migration (§13.2)

- **`232_help_assist_figures.sql`** rebuilds `help_assists` temp-then-rename under `foreign_keys = OFF`, keeping every row and id. No table's foreign key names it; its own two (workbench sessions, attempts) are unchanged.
  - `assist_kind` gains `figure`;
  - `hint_kind` gains `explore_figure`;
  - `request` gains `take_step`;
  - the new column is `figure_id TEXT`, a soft reference like `map_id`;
  - the indexes are as before, plus `idx_help_assists_figure`;
  - `help_assists_identity_fixed` is recreated with `figure_id` set once.
- **Table roles:** no new table, so no role or replayer change. `help_assists` stays RAW_LEDGER and is not AD-readable.
- **Head fixture:**
  - built from `migration_head_230` (main `c0017b5740`) on a backup-API copy with only 232 applied (`UPGRADE_SCRATCH_COPY`);
  - checkpoint (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty;
  - the schema diff is exactly `help_assists`, `help_assists_identity_fixed` and `+idx_help_assists_figure`, and only `schema_migrations` moved (217 to 218 rows);
  - copied into place with the backup API, and the README records it.
- **Paths:** `migration_head_230` became `migration_head_232` in every test, the sanitizer, both DB reference scripts (`SCHEMA_HEAD = 232`) and the generated catalog. The earlier migrations' "nothing else changed" diffs read `P3_ALTERED_TABLES` and `P3_ADDED_OBJECTS` from `tests/test_help_assist_figures_migration.py`, and their applied lists end `230, 232`.

## 4. Gate (this step; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6` at most, and vitest at `--maxWorkers=4`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 40 kept, 0 broken (run again after the last change) |
| Migration lane (A below): every test that names the head fixture, plus the migration, table-role, tracked-fixture and coordination contracts (55 files) | First run: 708 passed, 18 failed, 3 skipped. All 18 failures were the earlier migrations' "nothing else changed" diffs, which did not yet know 232's added index. After `P3_ADDED_OBJECTS` was threaded through, the 15 affected files gave 79 passed |
| Stage tests: `tests/test_figures_help.py` (G-SM15..18 and the switch off), `tests/test_help_assist_figures_migration.py` | 25 passed, 5 passed |
| Targeted lane (B below): every file that exercises a changed module (hints, figures, help outcomes, diagnoser split, tutor_qa, reader inquiry, the app snapshot) and the contract set (architecture, CLI help snapshot, config refactor and defaults fingerprints, desktop RPC contract, mobile allowlist, registry audit, sidecar registry, salience firewall, public tip guards) (202 files) | 9506 passed, 7 failed, 17 skipped, 5 xfailed. The failures: six pins of the new default-on keys (`figures.help` in the prompt contract ×4, `ask.figures` in the snapshot, the thirteenth kind label) and one private-name import (`figures.help._figure_keys`, renamed `figure_keys`). Fixed; those 7 files with the stage file: 149 passed, 1 skipped |
| `-m durability` on the migration files and the stage file | 8 passed |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| `npx vitest run --maxWorkers=4 src/components src/screens/PracticeScreen src/screens/practice src/screens/reader/figures src/api src/app` | 107 files: 1099 passed, 1 failed (`hintCopy.test.ts` pins the kind-label count: 12 to 13). Fixed: `hintCopy.test.ts` 4 passed; new `src/components/askFigures.test.tsx` 8 passed |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| DB reference generate / validate | errors [] (prose leaf count 1110 to 1111) |
| `desktop_generate.py`, `desktop_validate.py`, `validate_vault.py` | pass (303 TS / 6 Rust, ACTIVE 309, reproducible) |

**A. Migration lane files:** `tests/test_ad1_migration.py`, `tests/test_ad23_migration.py`, `tests/test_approach_maps_schema.py`, `tests/test_coordinated_migrations.py`, `tests/test_deliverable_curriculum_migration.py`, `tests/test_diagnosis_replay.py`, `tests/test_exam_protection_review.py`, `tests/test_figure_requests_migration.py`, `tests/test_figures_migration.py`, `tests/test_help_assist_figures_migration.py`, `tests/test_help_assist_work_md_migration.py`, `tests/test_help_assists_schema.py`, `tests/test_hint_feedback_widening.py`, `tests/test_hint_telemetry.py`, `tests/test_learner_claim_application_migration.py`, `tests/test_learner_claim_superseded_migration.py`, `tests/test_learner_notes_migration.py`, `tests/test_library_asks_migration.py`, `tests/test_method_explicit_upgrade.py`, `tests/test_migration_coordinator.py`, `tests/test_migrations.py`, `tests/test_mvp010_upgrade.py`, `tests/test_mvp011_upgrade.py`, `tests/test_mvp013_upgrade.py`, `tests/test_mvp014_upgrade.py`, `tests/test_mvp015_upgrade.py`, `tests/test_mvp016_upgrade.py`, `tests/test_mvp017_upgrade.py`, `tests/test_mvp018_upgrade.py`, `tests/test_mvp020_upgrade.py`, `tests/test_mvp021_upgrade.py`, `tests/test_mvp022_upgrade.py`, `tests/test_mvp023_upgrade.py`, `tests/test_mvp024_upgrade.py`, `tests/test_pfc_unverified_unassessed.py`, `tests/test_plan_determinism.py`, `tests/test_plan_follows_path.py`, `tests/test_public_tip_guards.py`, `tests/test_reader_ca2_fix_orchestrator.py`, `tests/test_reader_rw3b_migration.py`, `tests/test_reader_rw7a_migration.py`, `tests/test_reader_session_digests_migration.py`, `tests/test_reading_step_switch.py`, `tests/test_rebuild_orchestrator.py`, `tests/test_recurrence_commands.py`, `tests/test_regrade_contract_upgrade.py`, `tests/test_retrieval_spaces_migration.py`, `tests/test_route_rules_in_grader.py`, `tests/test_rw2d_receipts_migration.py`, `tests/test_section_coverage_migration.py`, `tests/test_session_ownership_migration.py`, `tests/test_shadow_rebuild.py`, `tests/test_t1_batch_origin_migration.py`, `tests/test_table_roles.py`, `tests/test_tracked_fixture_databases.py`

**B. Targeted lane files:** `tests/approach_map_fakes.py`, `tests/figure_corpus.py`, `tests/figure_panels_corpus.py`, `tests/figure_property_corpus.py`, `tests/hint_fakes.py`, `tests/recap_fixtures.py`, `tests/rich_fixtures.py`, `tests/rw2c_base_sequence.py`, `tests/sketch_parity_corpus.py`, `tests/sketch_scene_corpus.py`, `tests/split_live_helpers.py`, `tests/test_active_errors_overlay.py`, `tests/test_ad1_attempt_columns.py`, `tests/test_ad1_codex_review_fixes.py`, `tests/test_ad1_fix_round4.py`, `tests/test_ad1_fix_round8.py`, `tests/test_ad1_fix_round9.py`, `tests/test_ad1_outside_and_cli.py`, `tests/test_ad23_contract.py`, `tests/test_ad23_successor.py`, `tests/test_ad_epoch.py`, `tests/test_ad_guard_offer_receipts.py`, `tests/test_ai_compare.py`, `tests/test_answer_calibration_duel.py`, `tests/test_approach_map_boundaries.py`, `tests/test_approach_map_replay.py`, `tests/test_approach_maps.py`, `tests/test_architecture.py`, `tests/test_attempt_content_state_successor.py`, `tests/test_batch3_landing.py`, `tests/test_capture_desktop.py`, `tests/test_chat_total_transport_deadline.py`, `tests/test_chatgpt_plan_workspace.py`, `tests/test_cli_help_snapshot.py`, `tests/test_codex_lockdown_round3.py`, `tests/test_codex_tool_lockdown.py`, `tests/test_cold_retry_reschedule.py`, `tests/test_compare_methods.py`, `tests/test_config_refactor.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_daily_loop_start_minutes.py`, `tests/test_daily_plan_replay.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_diagnosis_context.py`, `tests/test_diagnosis_contract.py`, `tests/test_diagnosis_embeddings.py`, `tests/test_diagnosis_history_modes.py`, `tests/test_diagnosis_input_provenance.py`, `tests/test_diagnosis_input_provenance_landing.py`, `tests/test_diagnosis_pipeline.py`, `tests/test_diagnosis_reports.py`, `tests/test_e0_isolation.py`, `tests/test_facet_outcome_view.py`, `tests/test_field_workbench_signals.py`, `tests/test_figure_grammar.py`, `tests/test_figure_label_wording.py`, `tests/test_figure_offers.py`, `tests/test_figure_panels.py`, `tests/test_figure_predictions.py`, `tests/test_figure_region.py`, `tests/test_figure_rich_contract.py`, `tests/test_figure_rich_failed_correction_durable.py`, `tests/test_figure_rich_job.py`, `tests/test_figure_rich_rereview_fixes.py`, `tests/test_figure_rich_review_fixes.py`, `tests/test_figure_rich_rpc.py`, `tests/test_figure_verification.py`, `tests/test_figures_codex_review.py`, `tests/test_figures_final_round.py`, `tests/test_figures_fix_round2.py`, `tests/test_figures_fix_round3.py`, `tests/test_figures_fix_round4.py`, `tests/test_figures_fix_round5.py`, `tests/test_figures_help.py`, `tests/test_figures_rpc.py`, `tests/test_figures_rw5b_fix_round2.py`, `tests/test_figures_rw5b_review.py`, `tests/test_figures_scope_redesign.py`, `tests/test_figures_show_me.py`, `tests/test_figures_show_me_codex_review.py`, `tests/test_forecast_receipts.py`, `tests/test_held_grade_composition.py`, `tests/test_held_grade_evidence.py`, `tests/test_help_outcomes.py`, `tests/test_hint_blind.py`, `tests/test_hint_contracts.py`, `tests/test_hint_discriminating.py`, `tests/test_hint_evidence.py`, `tests/test_hint_feedback_texts.py`, `tests/test_hint_h2a_review.py`, `tests/test_hint_h2a_review_round2.py`, `tests/test_hint_h2a_review_round3.py`, `tests/test_hint_h2a_review_round4.py`, `tests/test_hint_h2b_fix4.py`, `tests/test_hint_h2b_rereview.py`, `tests/test_hint_h2b_review.py`, `tests/test_hint_kill_switch.py`, `tests/test_hint_outcome.py`, `tests/test_hint_replies.py`, `tests/test_hint_report.py`, `tests/test_hint_service.py`, `tests/test_intent_codex_rereview.py`, `tests/test_learner_blindness_relax.py`, `tests/test_learner_blindness_relax_codex_review.py`, `tests/test_learner_data_relax_2.py`, `tests/test_learner_report_superseded.py`, `tests/test_learner_text_gaps_flow.py`, `tests/test_library_ask.py`, `tests/test_lp_claim_fixes.py`, `tests/test_manim_figure_checks.py`, `tests/test_manim_sandbox_hostile.py`, `tests/test_mobile_allowlist.py`, `tests/test_notes_never_read.py`, `tests/test_owner_capture_1025.py`, `tests/test_pfc_unassessed_readers.py`, `tests/test_placement_diagnosis_decides.py`, `tests/test_plan_first_transport.py`, `tests/test_plan_first_transport_grant_scope.py`, `tests/test_plan_first_transport_offer_grants.py`, `tests/test_plan_first_transport_offer_grants_r5.py`, `tests/test_post_attempt_worker.py`, `tests/test_probability_prep.py`, `tests/test_reader_activity.py`, `tests/test_reader_branches.py`, `tests/test_reader_ca2_astra_handoff.py`, `tests/test_reader_ca2_codex_rereview.py`, `tests/test_reader_ca2_codex_review.py`, `tests/test_reader_ca2_one_ask.py`, `tests/test_reader_ca5_also_in_books.py`, `tests/test_reader_ca6_side_by_side.py`, `tests/test_reader_cues.py`, `tests/test_reader_digest_narrative.py`, `tests/test_reader_followups_successor.py`, `tests/test_reader_guidance.py`, `tests/test_reader_inquiry_kill_switch.py`, `tests/test_reader_inquiry_status.py`, `tests/test_reader_intent.py`, `tests/test_reader_passage_check.py`, `tests/test_reader_recap_review.py`, `tests/test_reader_reconnect.py`, `tests/test_reader_reconstruct.py`, `tests/test_reader_report.py`, `tests/test_reader_rw2b_fix10.py`, `tests/test_reader_rw2b_fix11.py`, `tests/test_reader_rw2b_fix14.py`, `tests/test_reader_rw2b_fix15.py`, `tests/test_reader_rw2b_fix5.py`, `tests/test_reader_rw2b_fix9.py`, `tests/test_reader_rw2b_review.py`, `tests/test_reader_rw3b_protection.py`, `tests/test_reader_rw6b_p2_landing.py`, `tests/test_reader_source_identity_guard.py`, `tests/test_reader_tutor_offers.py`, `tests/test_reader_tutor_switch_off.py`, `tests/test_reader_workbench_rw2a.py`, `tests/test_rebuild_equivalence_review.py`, `tests/test_recurrence_live.py`, `tests/test_recurrence_merge_composition.py`, `tests/test_registry_audit.py`, `tests/test_regrade_contract_successor.py`, `tests/test_required_method_grading.py`, `tests/test_required_method_round3_review.py`, `tests/test_router_offer_log.py`, `tests/test_router_reader_activity.py`, `tests/test_rw2c_fix_round2.py`, `tests/test_rw2c_fix_round3.py`, `tests/test_rw2c_switch_off.py`, `tests/test_rw4_kill_switches.py`, `tests/test_salience_firewall.py`, `tests/test_serve_eligibility_review.py`, `tests/test_session_ownership.py`, `tests/test_sidecar_registry.py`, `tests/test_sidecar_source_retrieval.py`, `tests/test_sidecar_tutor_qa.py`, `tests/test_sketch_engine.py`, `tests/test_sketch_hostile.py`, `tests/test_sketch_parity.py`, `tests/test_sketch_sandbox_review.py`, `tests/test_sketch_service.py`, `tests/test_sketch_verify.py`, `tests/test_source_retrieval_followup.py`, `tests/test_stuck_prompt.py`, `tests/test_stuck_prompt_replay.py`, `tests/test_teacher_te0_confidence_events.py`, `tests/test_teacher_te0_fix_round2.py`, `tests/test_teacher_te0_review_fixes.py`, `tests/test_tutor_delivery_fixes.py`, `tests/test_tutor_practice_request.py`, `tests/test_tutor_tool_requests.py`, `tests/test_ux_phase1_landing.py`, `tests/test_ux_phase3_today.py`, `tests/test_voi_stopping.py`, `tests/test_workbench_assistance.py`, `tests/test_workbench_check.py`, `tests/test_workbench_chooser.py`, `tests/test_workbench_help_kill_switch.py`, `tests/test_workbench_hint_service.py`, `tests/test_workbench_report.py`, `tests/test_workbench_step_graph.py`, `tests/test_workbench_text_gaps.py`, `tests/test_workbench_trace.py`, `tests/workbench_help_fakes.py`

## 5. Open items for the landing and the owner

1. **Renumbering.** C5 holds 231 and TE1 carries a migration too. If the numbers change at landing, rename `232_help_assist_figures.sql`, `fixtures/migration_head_232` and the paths together, and rebuild the head fixture from main's tracked copy with the landed migrations.
2. **Resolved in the Codex review fixes (F8).** ~~Rich tiers on attempt hosts are not built.~~ §11.4b says a Manim figure opened in an attempt counts once, and the count rule (the chain root through `fuller_of_id`) is in place. But an attempt host's build gets no rich spawner, because rich pending lines list under a passage and a practice figure has none. A follow-up could list them in the panel.
3. **Resolved in the Codex review fixes (F9; 232 also rebuilds `figure_predictions`).** ~~Homeless illustrations have no predictions~~ (§2.1). If the owner wants them, `figure_predictions.extraction_id` needs a nullable rebuild.
4. **Resolved in the Codex review fixes (F3: CA2's aliases are read).** ~~The answer box to Work in Steps hand-off.~~ One attempt has two keys there (CA2's aliases). A figure opened on the answer box and the same figure opened in the steps is deduplicated only when the workbench problem's key matches; the alias set is not read.
5. **The workbench's Reader-side host** (`reader.ask` inside a bound workbench) is not wired. The practice screen's inline panel under a step is. RW2c's passage draw including a kept figure (§11.4 "Reader-side draw") is owned by RW2c's switch and not built.
6. **The overlap measure is coarse.** The existing tutor measure is token-based, so a figure about P(X ≤ 0) shows about 0.5 overlap against a key about P(X ≤ 1/2). Reveals, and so auto-priming, will fire on topical figures as they do for hints and tutor answers. This is the spec's rule ("the existing overlap check"); flagged for the owner's checkpoint.
7. **Owner checkpoint (spec):** one real show me in the practice panel on a `fixtures-local` copy with the plan route. Not run here (no live calls in this stage).

## Landing onto main

### Step 0 (structural simplification, stuck-loop rule)

The third Codex round (job `20261101-225210-5u2jBM`) reopened F1, F2, F10 and F12 (in its legacy-payload variant) and added F13. It was the third round on the rich-figure-in-attempt classes, so the orchestrator ruled a structural simplification instead of a fourth fix round (commit `63f2337c4d`; the details are in the Codex review record, "Third review and step 0"):

- **Grammar and sketch only.** An attempt host (the answer box, a workbench step, the chooser's `explore_figure` during an open attempt, feedback) has no rich spawner. The author's menu therefore has no rich tier, no rich job starts and no view carries a fuller version.
- **Refused at the RPC:** `figure.open` (a Manim figure; it no longer takes `richJobId`), `reader.figure_revise` on an attempt host (a rich figure), `figure.rich_retry` (an attempt-hosted job), the record and the chooser's precondition.
- **Refused at worker admission:** `rich.attempt_hosted_job` reads the payload flag or, for a legacy payload, the stored request's host. It fails closed and stops the job before any model request.
- **Removed:** the attempt-host rich polling, "open here", the fuller opening and the fuller revision paths, from the panel and its controller.
- **Reveal scan:** reverted to the base scan (text keys, a sketch's literals, a grammar figure's values as formatted). The Manim/JS scan and its three registered bounds are gone.
- **Regressions, written first:** 5 pytest (all failed on `5423f57539`) and 2 vitest. They cover: an attempt-host rich request is refused; a legacy queued job stops; a sketch or grammar figure on an attempt is still counted once; and F13.

### Merges

1. **Main `de73fbda51`** (curriculum C5's migration 231, followups-nov1c), merge `0899470206`.
   - **Migration:** 232 was still free, so it keeps its number.
   - **Head fixture:** `migration_head_231` became `migration_head_232`, and `migration_head_230` and `migration_head_231` were dropped. It was rebuilt from main's tracked `migration_head_231/state.sqlite`: a backup-API copy under `fixtures-local/landing-p3-head/`, with only 232 applied under `UPGRADE_SCRATCH_COPY`.
   - **Checks:** checkpoint (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, 219 applied migrations (head 232). It was copied into place with the backup API.
   - **Diff against main's 231 head:** exactly `help_assists`, `help_assists_identity_fixed`, `figure_predictions` and `figure_predictions_explanation_once`, plus `idx_help_assists_figure` and `idx_figure_predictions_assist`. Only `schema_migrations` rows moved. The README's P3 section was rewritten for the landing, above C5's.
   - **Paths:** head paths in tests, the sanitizer and both DB reference scripts, with `SCHEMA_HEAD = 232`. The composed applied lists now end `230, 231, 232`. The altered sets carry both `C5_ALTERED_TABLES` and `P3_ALTERED_TABLES`. C5's own migration test now expects 232 after 231 and the 232 head.
   - **Fix after the merge:** 232's own migration tests start from a 231 database (commit `26c97cbcb9`), because the migration lane caught them applying 231 too.
   - **`config/template.py`:** both sides' notes are kept on every snapshot. All 31 fingerprints were recomputed with `defaults_fingerprint_for_version` after clearing `.pyc` files, and a second pass changed 0.
   - **Generated references:** main's side, then regenerated. `db_validate_reference` reports errors [], with the prose leaf count moving from 1111 to 1112.
   - **Desktop catalog:** 306 TS / 6 Rust, ACTIVE 312 (the validator's pinned counts moved).
   - **Parameter registry:** both sides' entries are kept.
2. **Main `67c05ed37c`** (RW5d P4a, figures follow section; no migration), merge `d1e83c7e70`.
   - **Source:** auto-merged: the figures service's `_listed`/`section_figures`, `useFigures` `followEnabled`/followed, `FigureInline`, `ReaderScreen`, correspondents and text_gaps provenance.
   - **One manual resolution, in TypeScript:** the attempt panel's `FiguresCtl` gains inert `followed: []`/`follow: async () => false`, since no figure is followed onto an attempt host.
   - **References:** main's side, then regenerated: errors [], desktop catalog 306 / 6, ACTIVE 312, `validate_vault` passes.
   - **Gate:** the full gate below ran once, on this merged tree. The queued pre-P4a full suite was stopped before it started.

### Gate (on `d1e83c7e70`)

Every pytest, vitest, npm and cargo command ran in a `systemd-run` scope: 10G for the full suite, 5G otherwise. Python ran under `env -i` with an empty HOME, CODEX_HOME and config directory.

| Check | Result |
|---|---|
| `lint-imports --no-cache` | 40 kept, 0 broken |
| Full pytest (`-n 8 --dist worksteal`, under the full-suite lock) | 23682 passed, 0 failed, 90 skipped, 47 xfailed (41 min) |
| `-m durability` | 183 passed, 1 skipped |
| Owner lane: fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035` in `fixtures-local/landing-p3/` | 83 passed, 4 skipped, 2 failed: the two known failures (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies::…[arxiv_v2]`) |
| Figures and help targeted lane after the P4a merge (74 files) | 1597 passed, 1 skipped |
| Migration and config lane after the first merge (68 files) | 1210 passed, 2 failed (232's tests on a 230 base); fixed in `26c97cbcb9`, and the two files give 11 passed (also under `--durable-sqlite`) |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| Whole vitest (`--maxWorkers=4`) | 2434 passed, 0 failed |
| `npm run frontend:build` | built |
| `cargo check` | ok |
| DB reference generate and validate; desktop generate and validate; module and vault validation | errors []; 306/306 TS + 6/6 Rust, ACTIVE 312, reproducible; pass |

After the gate, main was re-read: it was still `67c05ed37c`, so no further merge was needed.

### Smoke (fresh owner copies, `fixtures-local/landing-p3-smoke/`)

**Setup:**
- Fresh backup-API copies of the three mvp035 owner copies.
- Every AI route at the `127.0.0.1:9` blackhole, with the key variables unset.
- `env -i` with an empty HOME, CODEX_HOME and config directory.
- An audit hook logs every process start and socket connect, and refuses non-loopback connects and Codex process starts.
- Main's code (`67c05ed37c`) against the branch's (`d1e83c7e70`), each a `git archive` with `migrations/`.
- On each copy: `upgrade` from mvp-0.35 to mvp-0.40, a primary load, the migration check (main head 231, branch head 232) and `rebuild-derived-state`.
- Nothing was requested, rendered or built. No Manim and no bwrap ran on owner data.

**Results:**
- **Today and the daily plan:** byte-identical, main against branch.
  - linear_algebra: 525266 B and 84696 B;
  - probability: 740827 B and 124021 B;
  - arxiv_v2: 344204 B and 32433 B.
- **`help_outcomes` and the hints report** (frozen `as_of`/now, all facets): byte-identical (6163, 7135 and 8534 B). No figure rows exist on the owner copies, there is no help kind `figure`, and there is no `figures` block.
- **The hint chooser on a "More" press,** built as the hint service builds it, with the sidecar's figure provider on (no model call):
  - over 40, 40 and 32 practice items, `explore_figure` is never offered and is excluded as `no_figure` on every item;
  - no figure qualifies, and the copies hold 0 figures and 0 figure help rows.
- **The branch's head** is 232, `help_assists.figure_id` exists, and no help row exists.
- **`rebuild --shadow`** on the branch's copies: facet, mastery and schedule 0/0/0 on all three, and the live database is unchanged.
- **Receipts:** 0 new `model_call_receipts` across the 6 databases compared with base.
- **Audit log:** 0 process starts and 0 socket connects from the smoke, so no non-loopback socket. A separate self-test of the hook logged its `true` start and its `127.0.0.1:9` connect.

### Rulings (orchestrator)

- R1: "Attempt-hosted figures are grammar and sketch only; rich (Manim) figures stay Reader-side. This closes the reveal-scan, rich polling, fuller revision and queued-job admission findings structurally."
- R2: "F1 session rollover (a help row attached by submission key after its session ended and a new one started) is the hint service's existing H0 attach/fold boundary for every help kind, not specific to figures. Ruled Low; queued as a cross-help follow-up."
- R3: "Successor: none. No figure row exists before this migration and replay reads stored hints_used; for new attempts a figure is one hint-equivalent with that field's existing meaning. Accepted."
- R4: "The token-overlap reveal measure is coarse (topical figures can prime), following the spec's 'existing overlap check' rule; flagged for the owner checkpoint."

### Owner items

- **Migration 232** applies on the first open after the update. There is no successor and no algorithm version. It rebuilds `help_assists` and `figure_predictions` in place and keeps every row.
- **The spec's checkpoint:** one real *show me* in the practice panel, on a `fixtures-local` copy with the plan route (open item 7 above). It was not run here, since this landing made no live calls. Also check R4's coarse overlap on a topical figure.
- **Switch:** `figures.help_kind_enabled` (default on). Off, every hint, fold and outcome is the predecessor's.

### Open items

- **`figure_predictions` NOT NULL `extraction_id`:** resolved in 232 (F9: now nullable). What remains is the follow-up check that no reader of `figure_predictions` outside the diagnoser's trace assumes a home.
- **The Reader-side workbench host wiring** (`reader.ask` inside a bound workbench) is not built (open item 5).
- **RW2c's passage draw including a kept figure** (§11.4 "Reader-side draw") is not built. It is owned by RW2c's switch.
- **R2's cross-help follow-up:** the attach/fold session rollover, for every help kind.
- **Animations on attempt hosts (R1):** if wanted later, they need a design-first stage. That stage needs a displayed-text contract for scenes, not an AST scan.
