# Reader workbench RW2d: workbench signals in the learner field

Stage `reader-rw2d`, branch `reader/rw2d` in `learnanything-dl2`, base `bd0bb7267` (main with T1, RW5b, RW2c, UX2;
migration head 218). Spec: `docs/specs/spec_reader_workbench_v1.md` §5.6 ("Field signals: RW2d"), §5.11, G41, §13's
test list (`test_field_workbench_signals.py`); the learner field's §3.1 (interaction signals and the F2 guard) and F3
(a change to what is served is a successor with receipts).

## 1. What changed

Two sources join the field's interaction-signal derivation (`learnloop.field.signals.load_interaction_signals`),
in a new leaf `learnloop.field.workbench_signals` that reads the workbench ledgers by SQL (never through the
workbench modules: the `evidence-never-reads-the-workbench` import contract stands):

* **A mid-work stuck step** (`workbench_steps.kind = 'stuck'`) with text is a `stuck_confusion` row (the type a stuck
  answer the grader read as confusion already has), once per step chain, observed when the chain first held text.
  The ledger is append-only, so a later edit, delete or undo never takes back that the learner was stuck then.
  * An empty stuck step is no signal: the owner's 2026-10-12 ruling for an empty stuck answer ("says nothing about
    understanding beyond could not write anything").
  * A session submitted with no ordinary step submitted its stuck text AS the stuck answer (`declared_stuck`), which
    the derivation already reads through the grader's reading; its steps are not read a second time.
* **Help before the first step**: a workbench `help_assists` row of kind `hint`, `bridge` or `example` whose logged
  `step_snapshot_json` holds no ordinary step with text. One row per session, at its first such request, with
  `help_before_work = true`. As on the practice screen, only the logged fact counts: a row without a snapshot is
  not evidence of help before work; a check, a discriminating answer, a "doesn't connect" reply and a method
  comparison are not help requests.
* **Targets**: the submitted attempt's LO and subject (so the rows meet the attempt rows); otherwise the bound
  item's own LO and first subject (as a submit would record them); a session not yet bound to an item has none and
  is counted as unmapped in the derivation's diagnostics.
* **Abandoned sessions** contribute only through these two sources, never as a failure.

**Never the record (F2).** Both rows carry no outcome, no mass and no attempt link:

* no predictor observes them (`_eligible` needs mass and an outcome);
* no attempt's hint outcome is capped as "help before work" and no attempt's assistance or coldness changes
  (`enrich_attempts` links by attempt id);
* the report's question strata (`preceded_by_question`) leave them out explicitly;
* the daily signal-mass cap is untouched (zero mass), and the rows are merged in AFTER the derivation, so every row
  the predecessor produces is unchanged and the predecessor's output is exactly this one without
  `is_workbench_signal` rows;
* the family-memory rebuild passes `include_workbench=False`, so a rebuild never reads the workbench tables (RW2a's
  W1); the attempt rows it folds are the same either way.

They block fast-track (`blocks_fast_track`: a stuck row by its type, an early-help row by its flag), so the LO is
taught first and never fast-tracked on early answers alone; "I know this" still works. What changes is what is
served: Phase 6's fast-track, the quick check's split (and so which items it presents next), the new-material
order, report 2's fast-track simulation, and the plans built on the queue.

## 2. The successor

* **Tag**: `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION = "mvp-0.31"`, appended to `SUCCESSOR_CHAIN` after `mvp-0.29`
  (AD2+AD3 holds `mvp-0.30` and lands first). The number is in that one constant; everything else reads it (the
  gate set `WORKBENCH_FIELD_SIGNALS_VERSIONS`, the CLI target, the upgrade, the tests via `SUCCESSOR_CHAIN`).
* **Upgrade**: `learnloop.workbench_field_signals_upgrade.upgrade_to_workbench_field_signals` (the intent upgrade's
  shape): the predecessor, or `mvp-0.9` onwards through the chain; a tag change plus the idempotent rebuild of the
  same projection namespace; nothing rewritten. `learnloop upgrade` defaults to it.
* **Kill switch**: `workbench.field_signals_enabled` (default true; classified in the parameter registry as a
  structural kill switch: the rows carry no weight, margin or threshold, so there is nothing to learn). Off, or
  below the tag, `load_workbench_signals` returns before reading any table.
* **Defaults snapshots**: every snapshot recomputed (the effective config gains one key); dropping the key
  reproduces all 20 prior values exactly (checked), and the new tag has its own entry.

### Landing (renumbering)

If the tag must move: the constant in `algorithm_versions.py`; `PREDECESSOR` and `_upgrade_to_predecessor` in
`workbench_field_signals_upgrade.py` (point them at AD2+AD3's tag and upgrade); the snapshot key in
`config/template.py` (recompute with `defaults_fingerprint_for_version`); the literal `mvp-0.31` in the CLI
docstring and the chain-tail pins in the tests (`git grep '"mvp-0.31"' tests`); `tests/cli_help_snapshot.json`
(`python tests/test_cli_help_snapshot.py --write`). The head fixture (§3) is rebuilt from main's head with only 219
applied, as its README says.

## 3. Receipts, and why a migration

F3 asks receipts "including what the old rule would have done where that is cheap". The workbench rows can only
ADD blocking signals, so a decision they change is one the old rule took on fewer: re-running that rule on the
predecessor's blocking set (`placement.signals.blocking_with_predecessor`) is cheap.

* **Fast-track** (`reconcile_fast_track`, the persisting queue build): for a candidate whose blocking set differs,
  a `field_signal_receipts` row with both verdicts (`{blocking_signal_ids, verdict, reason, p}`), written in the
  decision transaction, idempotent on (LO, workbench signal set, predecessor verdict), so repeated builds write it
  once and a later change of the old rule's verdict (say `below_threshold` to `fires`) writes a new one.
* **The quick check** (`finish_quick_check_split`): a row per scoped LO whose split verdict differs, keyed by the
  calibration session, in the transaction that records the split.
* **New-material order**: the candidate component `taught_first_predecessor`, present only where it differs from
  `taught_first`, so a build with no difference is the predecessor's exactly; it is persisted with the slate's
  components (the router log carries `taught_first`; the rest stays on the slate row).

**Migration 219** (`field_signal_receipts`, RECEIPT, append-only by trigger, one LO index) is the one departure from
the spec's "RW2d needs no migration" (§11, now amended there): a withheld fast-track writes no
`assumption_decisions` row (the old rule would have; the new one does not), so no existing receipt can hold "the
old rule would have fired". The head fixture moves to `fixtures/migration_head_219` (a backup-API copy of the 218
head with only 219 applied; checkpoint (0, 0, 0), `journal_mode=DELETE`, header 1/1, integrity ok, no FK errors);
every "nothing else changed" migration test subtracts `RW2D_ADDED_OBJECTS`; the references are regenerated at
schema head 219 (340 table notes, 1,014 config leaves; 0 validation errors).

## 4. G41 evidence

`tests/test_field_workbench_signals.py` (20 tests):

* **Off is the predecessor**: with the switch off, and below the tag, the derivation and the blocking map equal the
  predecessor's on the same workbench history (placement vaults), and on the three working fixtures' copies
  (`linear_algebra`, `probability`, `arxiv_v2`, backup-API copies seeded with a stuck step and early help): Today's
  queue (two budgets), Start and the derivation are equal as served, and the daily plan equal up to the ids its
  build mints and its version label.
* **On is the predecessor plus the workbench rows**, exactly, on the same copies and on placement vaults.
* **Receipts**: a stuck step and early help each withhold fast-track with a receipt whose predecessor verdict is
  `fires` on no blocking signals; a second build writes none; switched off, the old rule fires and no receipt is
  written. The quick check's receipt records `assumed` beside `learning`. The taught-first component records 0.
* **F2**: the evidence, mastery, certification, FSRS and coldness tables are byte-identical after the rows land and
  placement runs (G13's snapshot); an attempt's outcome, mass, assistance, strata and coldness, its facet rows and a
  hinted attempt's graded outcome are equal with and without its session's stuck step and early help;
  `enrich_attempts` ignores the rows; the rebuild path issues no workbench query.
* The pure rules (one row per chain from first text, empty steps, stuck answers, unbound problems, the snapshot
  rule and the kinds), the vocabulary, the snapshot, the switch's default and classification, the upgrade (direct,
  chained, refused, CLI default).

`tests/test_rw2d_receipts_migration.py`: 219 adds the table and nothing else; append-only and keyed once (a CHECK is
not swallowed: the insert is `ON CONFLICT(receipt_key) DO NOTHING`, not `OR IGNORE`); the head fixture at 219 in
rollback mode; the durability lane (WAL).

**Fail-first.** On the base the new test file cannot import (no tag, module or table). A base-compatible probe of the
four behaviour changes (a copy of the helpers, run against `bd0bb7267`'s `src`/`migrations` with
`-o pythonpath=<base src>`, then deleted): the stuck step and the early help each leave fast-track firing, the
stuck LO is not taught first and the quick check assumes it: 4 failed, with the no-workbench control passing; all
pass on the branch.

## 5. Calls and cost

No model is called anywhere in RW2d. No paid call was made; every script ran under `env -i` with an empty
`HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`. Spend: $0.

## 6. Gate (this step; the full suite runs once in the landing gate)

All inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one run at a time:

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 31 kept, 0 broken (two leaf edges exempted in `frozen-cross-package-cycles`).
* `uv run pytest -n 6` over 159 files: **3,796 passed**, 0 failed (34 min 36 s) at `ca95c20fc` plus this
  review. The new files: `test_field_workbench_signals.py` (20), `test_rw2d_receipts_migration.py` (4).
* `uv run pytest -m durability` over the migration files (219's own and every "nothing else changed" test on the
  way to head): 7 passed.
* `db_generate_reference.py` and `db_validate_reference.py`: regenerated at head 219; 0 errors.
* No frontend or `src-tauri` change: no npm, vitest or cargo run.

The 159 files: `test_ad1_codex_review_fixes.py`, `test_ad1_migration.py`, `test_adaptive_difficulty_ad1.py`, `test_ai_config.py`, `test_answer_signal_arms.py`, `test_approach_map_replay.py`, `test_approach_maps_schema.py`, `test_architecture.py`, `test_assumed_known.py`, `test_cli_help_snapshot.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_daily_plan_composition.py`, `test_daily_plan_kill_switch.py`, `test_daily_plan_owner_decisions.py`, `test_daily_plan_replay.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_input_provenance.py`, `test_diagnosis_replay.py`, `test_embedding_store.py`, `test_eval_harness.py`, `test_evsi_router_composition.py`, `test_evsi_staged_binding.py`, `test_exam_protection_review.py`, `test_facet_outcome_view.py`, `test_family_memory_projection.py`, `test_field_split_outcomes.py`, `test_field_workbench_signals.py`, `test_figures_migration.py`, `test_forecast_receipts_landing.py`, `test_forecast_receipts.py`, `test_grading_cli.py`, `test_held_grade_composition.py`, `test_held_grade_evidence.py`, `test_help_assists_schema.py`, `test_hint_telemetry.py`, `test_integration_daily_loop_field.py`, `test_intent_codex_rereview.py`, `test_intent_codex_review.py`, `test_intent_fix_round4.py`, `test_intent_fix_round5.py`, `test_intent_fix_round6.py`, `test_intent_fix_round7.py`, `test_intent_plan.py`, `test_interaction_signals.py`, `test_intervention_outcomes_replayer.py`, `test_item_fingerprints.py`, `test_kinship_feature.py`, `test_km2_activation.py`, `test_km2b_consumer_rekey.py`, `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_rereview.py`, `test_learner_text_gaps_review.py`, `test_library_asks_migration.py`, `test_library_exercises.py`, `test_method_explicit_upgrade.py`, `test_migration_coordinator.py`, `test_migrations.py`, `test_mobile_allowlist.py`, `test_model_grade_lane.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_route_check_replay.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_mvp09_upgrade.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_pfc_unassessed_readers.py`, `test_pfc_unverified_unassessed.py`, `test_placement_diagnosis_decides.py`, `test_placement_report.py`, `test_placement_signals.py`, `test_placement_split_grades.py`, `test_plan_determinism_landing.py`, `test_plan_determinism.py`, `test_plan_first_transport.py`, `test_practice_index_dossiers.py`, `test_quick_check.py`, `test_reader_guidance.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_reader_rw1b_review.py`, `test_reader_rw1c_review.py`, `test_reader_rw2b_fix9.py`, `test_reader_rw2b_review.py`, `test_reader_rw3a_landing.py`, `test_reader_rw3b_migration.py`, `test_reader_rw7a_migration.py`, `test_reader_workbench_rw2a.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_rebuild_orchestrator.py`, `test_recurrence_commands.py`, `test_recurrence_live.py`, `test_reference_gate_imports.py`, `test_registry_audit.py`, `test_regrade_contract_replay.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_required_method_authority.py`, `test_required_method_grading.py`, `test_required_method_reopened.py`, `test_required_method_rereview.py`, `test_required_method_round3.py`, `test_required_method_round3_review.py`, `test_router_card.py`, `test_router_coldness_covariates.py`, `test_router_g1_feasibility.py`, `test_router_g4_restraint.py`, `test_router_offer_log.py`, `test_router_outcomes.py`, `test_router_p2_bridge.py`, `test_router_r1_composition.py`, `test_router_r2a_landing.py`, `test_router_r2a_serving.py`, `test_router_r2bc_landing.py`, `test_router_r2b_serving.py`, `test_router_r2c_teach_back.py`, `test_route_rules_in_grader.py`, `test_router_why_copy.py`, `test_rw2c_switch_off.py`, `test_rw2d_receipts_migration.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility.py`, `test_serve_eligibility_review.py`, `test_shadow_rebuild.py`, `test_sidecar_serializer_snapshot.py`, `test_source_block_fts.py`, `test_source_first_needs.py`, `test_source_roles.py`, `test_sqlite_file_copies.py`, `test_sqlite_wal_lifecycle.py`, `test_stuck_prompt_composition.py`, `test_stuck_prompt.py`, `test_stuck_prompt_replay.py`, `test_t1_batch_origin_migration.py`, `test_table_roles.py`, `test_teach_back.py`, `test_today_headline.py`, `test_tracked_fixture_databases.py`, `test_ux_phase1_round2_rereview.py`, `test_ux_phase2_shell.py`, `test_ux_phase4_landing.py`, `test_voi_stopping.py`, `test_workbench_assistance.py`, `test_workbench_help_kill_switch.py`.

## 7. Open questions

1. **Migration 219** departs from the spec's "no migration" for RW2d (§3 above). The alternative, receipts only in
   existing payloads, leaves a withheld fast-track without any record of what the old rule would have done.
2. **Target of an unsubmitted session**: the bound item's current LO (the item's own field, not a facet mapping).
   If an item moves to another LO later, an abandoned session's rows follow it. A snapshot-bound target (the
   session's assessment contract or the item snapshot) would pin it; not done here.
3. **Empty stuck steps** are no signal (the stuck answer's ruling), and help before the first step counts a stuck
   step as no work. Either can flip by owner decision without a new table.
4. **Report strata**: the workbench rows are left out of `preceded_by_question` (the field's report-2 strata) so
   only routing changes; the owner may want them counted as "questions or hints" there.
5. **No shadow rebuild on a fixture copy**: the tracked fixtures are at schema 155 and an old tag, and
   `rebuild --shadow` does not migrate; the G41 fixture test runs through the sidecar's load (which migrates) and
   compares the served reads instead. A rebuild never reads the workbench tables, so its projection cannot move.
