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
  * The row stands whatever the submit later says (Codex review F2): a session submitted as a stuck answer
    (`declared_stuck`) keeps its step-time row from the step's own time, and a stuck step deleted before an empty
    submit is never erased by it. The stuck answer's own grader row (`stuck:<attempt>`) is the predecessor's and
    stays beside it unchanged; both are zero-mass and blocking is per LO, so nothing counts twice.
* **Help before the first step**: a workbench `help_assists` row of kind `hint`, `bridge` or `example` whose logged
  `step_snapshot_json` holds no ordinary step with text. One row per session, at its first such request, with
  `help_before_work = true`. An identity-only snapshot entry (the worked example logs chain, step row id, number and
  hash, never the text) is read through the immutable step row it names; an entry whose row is not found leaves the
  snapshot unknown, never "no work" (Codex review F1). As on the practice screen, only the logged fact counts: a row without a snapshot is
  not evidence of help before work; a check, a discriminating answer, a "doesn't connect" reply and a method
  comparison are not help requests.
* **Targets**: the submitted attempt's LO and subject (so the rows meet the attempt rows); otherwise the LO of the
  assessment contract the session froze when it opened on or bound to its item (Codex review F3: an item later moved
  to another LO, or removed, never moves or drops the signal). Its subject is the one recorded with that contract
  (`workbench_sessions.contract_subject_id`, added by migration 219 in the re-review's F3: the item's first subject,
  else its LO's, else `default`, as a submit then would have recorded it), never today's label; a session whose
  subject was never recorded has the explicit `workbench:subject-unrecorded`, which no subject-aware check matches,
  and is counted (`workbench_subject_unrecorded_sessions`); live routing blocks per LO, so it still blocks there. A
  session without a readable contract for its own item has none and is counted as unmapped in the derivation's
  diagnostics.
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
old rule would have fired". 219 also adds `workbench_sessions.contract_subject_id` (Codex re-review F3): the subject
recorded with a session's frozen contract, so an unsubmitted session's rows never take today's label. The head fixture moves to `fixtures/migration_head_219` (a backup-API copy of the 218
head with only 219 applied; checkpoint (0, 0, 0), `journal_mode=DELETE`, header 1/1, integrity ok, no FK errors);
every "nothing else changed" migration test subtracts `RW2D_ADDED_OBJECTS` and `RW2D_ALTERED_TABLES`; the references are regenerated at
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

`tests/test_rw2d_receipts_migration.py`: 219 adds the table and the subject column and nothing else (a session from
before 219 has none on record); append-only and keyed once (a CHECK is
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
2. **Target of an unsubmitted session** (resolved by Codex review F3): the LO of the session's frozen assessment
   contract, so an item moved to another LO or removed later leaves an abandoned session's rows where they were.
   The subject is the one frozen with the contract (`workbench_sessions.contract_subject_id`, Codex re-review F3,
   in migration 219); a session frozen without one says `workbench:subject-unrecorded`, never today's label.
3. **Empty stuck steps** are no signal (the stuck answer's ruling), and help before the first step counts a stuck
   step as no work. Either can flip by owner decision without a new table.
4. **Report strata**: the workbench rows are left out of `preceded_by_question` (the field's report-2 strata) so
   only routing changes; the owner may want them counted as "questions or hints" there.
5. **No shadow rebuild on a fixture copy**: the tracked fixtures are at schema 155 and an old tag, and
   `rebuild --shadow` does not migrate; the G41 fixture test runs through the sidecar's load (which migrates) and
   compares the served reads instead. A rebuild never reads the workbench tables, so its projection cannot move.

## Landing onto main

Landed in `learnanything-merge2` on `merge/rw2d-onto-main`, from main `e25739a96` (AD2+AD3 at `mvp-0.30`, migration
214 under head 218) and `reader/rw2d` at `203d85803`. The orchestrator's rulings stand: Codex review F1 (High), F2
and F4 confirmed fixed; F3's residual is non-blocking (open items below).

### Commits and conflicts

- `a766a4264`: the merge (`--no-ff`). **445 files conflicted**:
  - 412 generated references, plus `tests/cli_help_snapshot.json`: main's side taken, then regenerated.
  - `algorithm_versions.py`: both successors kept, `mvp-0.31` chained after `mvp-0.30`.
  - `cli/app.py`: both `--to` branches; the help names `mvp-0.30` and the tag.
  - `config/template.py`: both comment lines on all 20 earlier snapshots; the `mvp-0.30` and `mvp-0.31` entries.
  - The concept note *Algorithm Versions and Reproducibility*: the `mvp-0.31` row, and every gate set extended.
    The branch's `DECIDER_TIER1_VERSIONS` "to `mvp-0.27`" was a typo; main's text was kept.
  - `fixtures/migration_head_219/{README.md,state.sqlite}`: README composed, database rebuilt (below).
  - 26 test files: chain pins composed, and the "nothing else changed" migration diffs now subtract both
    `AD23_ADDED_OBJECTS` and `RW2D_*`.
- `2842badae`: chain pins and the CLI help snapshot.
  - Hunks that merged cleanly had kept main's `SUCCESSOR_CHAIN[-N]` positions. Each moved back one (15 lines over
    14 files), and two `METHOD_EXPLICIT_VERSIONS` pins gained `mvp-0.30`.
  - `test_intent_codex_rereview`'s CLI test had merged into an inconsistent mix. It now keeps main's explicit
    `--to mvp-0.29` and checks the default upgrade separately.
  - `test_ad23_successor`: AD's tag is now `SUCCESSOR_CHAIN[-2]`, its gate set is `{mvp-0.30, mvp-0.31}`, and new
    vaults start at `mvp-0.31`.
  - `test_ad23_migration`: the head is 219, and a vault at head without 214 now holds 215-219.
- `fac9ca330`: references regenerated.

The source files both sides changed outside the conflicts are `field/outcomes.py`, `scheduling/scheduler.py`,
`substrate/rebuild_orchestrator.py`, `params/parameter_registry.py`, `db/table_roles.py` and `config/schema.py`.
Each composed with no overlap. AD reads no field interaction signal, so the workbench rows never reach AD's state or
a rebuild.

### Renumber and chain

- `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION = "mvp-0.31"`, after `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION` in
  `SUCCESSOR_CHAIN`. The chain is linear, 22 tags, ending `mvp-0.27 -> mvp-0.29 -> mvp-0.30 -> mvp-0.31`, and
  `LATEST_ALGORITHM_VERSION` = `mvp-0.31`.
- `workbench_field_signals_upgrade`: `PREDECESSOR = ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION` and
  `_upgrade_to_predecessor = upgrade_to_mvp030`. AD's own step prepares AD's DERIVED state when the chain passes
  through it.
- Docstrings and the CLI docstring follow. `test_field_workbench_signals` pins the predecessor as `mvp-0.30` and
  chains from both `mvp-0.27` and `mvp-0.29`.
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM`: all **22** entries recomputed with `defaults_fingerprint_for_version`, template
  `.pyc` cleared. A rerun gives **0 mismatches**.
- Chain check on placement vaults (`fixtures-local/landing-rw2d/scripts/chain_check.py`):
  - `--to mvp-0.31` from `mvp-0.9`, `mvp-0.27`, `mvp-0.29` and `mvp-0.30`: rc 0, label `mvp-0.31`.
  - From `mvp-0.8`: refused directly, as at every successor since `mvp-0.9`. Then `--to mvp-0.9` and
    `--to mvp-0.31`: rc 0.
  - Bare `upgrade` from `mvp-0.30`: rc 0, to `mvp-0.31`.
- The 59 test files that pin the chain, a snapshot, a head or the tag pass in the full suite.

### Head fixture

`fixtures/migration_head_219` was rebuilt as a backup-API copy of main's `migration_head_218` (which holds 214), with
only 219 applied under `UPGRADE_SCRATCH_COPY`, then copied into place with the backup API.
- Checks: `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
  `foreign_key_check` empty, no companion files.
- Against main's 218 it adds exactly 219's six objects (the table, its index, two autoindexes and two triggers), and
  only `workbench_sessions` changes (`contract_subject_id`). All seven are identical to the branch's head.
- `migration_head_218` is gone (the branch had renamed it, as T1 renamed 217 to 218).
- The README was composed: main's text, the branch's 219 paragraph, and this rebuild.
- Hard-coded paths: the head is named in the tests (`test_ad23_migration` was the one left on 218) and in the two
  `db_*_reference.py` scripts (three times in `db_generate_reference.py`).
- Local retrieval P1 (`learnanything-lr1`) will renumber its migration to 220; it was not touched.

### Regeneration

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, schema head **219**,
  **348** table notes, **1,034** configuration leaves (main 347 and 1,033).
  - The hand-written counts in `Database.md` and `Configuration.md` were updated; the validator flags them
    otherwise.
- **Defaults snapshots**: recomputed (above).
- **CLI help snapshot**: regenerated (the `upgrade` help).
- **RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist): their tests pass; no file changed.
- **`validate_vault.py`**: passes (1,151 notes, 1,149/1,149 reachable).
- **Failing before this stage, not fixed:**
  - `desktop_validate.py` still stops on `components/pdfSelection/testing/syntheticBook.ts`.
  - `module_validate.py` reports **1,079** issues (1,071 at AD2+AD3's landing). The new ones are RW2d's modules
    without module notes.

### Gate

Setup and rules:
- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0), with `TMPDIR` = merge2's
  `fixtures-local/tmp`. Every later command ran as `uv run --no-sync` under `env -i`, with empty `HOME`,
  `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
- pytest lanes: 10G/2G scopes, `-n 8`, under `flock /tmp/learnloop-fullsuite.lock`. Everything else: 5G/1G.
- Gate head `fac9ca330`. Logs: `fixtures-local/rw2d-landing-*.log`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **34 kept**, 0 broken |
| full suite (`pytest -n 8`, 48 min 35 s) | **22,057 passed**, 1 failed, 3 skipped, 38 xfailed |
| the one failure, alone, 3 times | `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`: **3/3 passed** (5 s each). A known load flake (the parity runs shared the machine); no RW2d code is on its path |
| durability (`-m durability`) | **121 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (the whole vitest run) | **206 files, 1,737 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean after every lane; no non-empty `-wal` beside a fixture |

No real failure, so no landing fix.

### Parity (backup-API copies; no model call)

**Setup.** Scripts are in `fixtures-local/landing-rw2d/scripts/`, outputs in `out/`.
- **Copies.** The owner's backups `fixtures-local/vault-backups-20261024-mvp029/{linear_algebra,probability}`
  (`mvp-0.29`, schema 218 without 214, 0 `model_call_receipts`, no workbench session, step or help row) were each
  copied once, as whole trees, with `copy_tree_with_databases` into `landing-rw2d/orig/`. Every other copy came from
  those through the same helper.
- **Not opened:** the main checkout's `fixtures/linear_algebra`, `fixtures/probability` and `fixtures/arxiv_v2`.
- **Code.** Main's code is `git archive main` (`e25739a96`) and the merge's is `git archive fac9ca330`, each first
  on `sys.path`. An audit hook refuses any Codex process start; none was attempted, and no process start was
  logged at all.
- **Environment.** `env -i`, with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
- **Routes.** Every route went to `127.0.0.1:9` through unset-key loopback profiles (63 tasks resolved; nothing
  else but the disabled, keyless `embedding`). Rewrite, rerank, dense, embeddings and learner-text gaps were off;
  `build_on_serve` and outcome placement off.
- **Clock.** Frozen at 2026-10-19 09:00 UTC.

**(a) At `mvp-0.30`.**
- **Upgrade.** `upgrade --to mvp-0.30` plus `rebuild-derived-state` twice, with main's code (`u30`) and with the
  merge's (`m30`): rc 0 on both vaults.
- **Schema, main vs merge** (`u30` vs `m30`, and `u30` opened by each code): only 219's six objects are added, and
  `workbench_sessions` gains `contract_subject_id` (NULL on every row). Nothing is only on main.
- **Rows** (352 common tables; LA 17,990 rows, probability 8,139):
  - Copies of the same mvp-0.30 vault opened by each code: identical. `schema_migrations` has 219 extra; common
    rows are identical.
  - The two upgrade runs, ULIDs and timestamps normalised: identical. Ten tables differ only in the ids and
    timestamps each run mints, among them `parameter_registry` and its manifests (the same keys: RW2d registers no
    numeric parameter).
  - The new table is empty. FK 0, integrity ok, 0 `model_call_receipts`.
- **`rebuild --shadow` and `doctor`.** 0 differences after normalisation, main vs merge, on both the merge's own
  upgrade and main's vault opened by the merge.
  - Shadow 0 / 0 / 0 with the live database unchanged.
  - Doctor shows LA 57 issues / 1 error and probability 101 / 48, the same on both codes.
- **Served reads.** Certification and curves, and the Today queue (no session, a session, greedy), are
  **byte-identical** (LA cert 129,651 bytes, queue 43, 528,665 bytes; probability 17,495 bytes, queue 67, 741,269
  bytes).
  - The daily plan (read, serve, serve again, read) is identical except `card_hash`, `snapshot_hash` and the card
    hash inside `detail_json`, which differ between any two runs (as recorded at DL2's, T1's and AD2+AD3's
    landings).

**(b) `upgrade --to mvp-0.31`** (the merge's code).

| Check | linear_algebra | probability |
|---|---|---|
| on main's mvp-0.30 copy | rc 0, "mvp-0.30 -> mvp-0.31" | the same |
| bare `upgrade` on another copy | rc 0, "mvp-0.30 -> mvp-0.31" | the same |
| rows vs the copy just before | **no row removed or changed** once ULIDs, timestamps and the version stamp are masked. Raw, only the `algorithm_version` stamp of `facet_capability_evidence` (36) and `facet_recall_state` (76) (DERIVED) and the refreshed `parameter_registry` rows differ. Added: `derived_state_rebuilds` +1, `parameter_registry_manifests` +1 | the same (1 and 2 stamped rows) |
| `rebuild --shadow` right after the upgrade | facet 0, mastery 21 (the `mastery_state` version stamp), schedule 0; live database unchanged | 0 / 18 (stamp) / 0 |
| after `rebuild-derived-state` twice | shadow **0 / 0 / 0**; `doctor` as at mvp-0.30 | the same |
| straight from the mvp-0.29 backup, `--to mvp-0.31` (chains through AD2+AD3's step) | rc 0, "mvp-0.29 -> mvp-0.31". Every pre-existing row is kept up to stamps and ids; AD's `ad_state` +9 and `ad_attempt_trace` +90 are prepared; `parameter_registry` +9 (AD's keys). After the rebuilds, shadow 0 / 0 / 0 and doctor unchanged | the same (`ad_state` +2, `ad_attempt_trace` +3) |
| the owner's two steps, `--to mvp-0.30` then `--to mvp-0.31`, rebuild | rc 0 each; shadow 0 / 0 / 0 | the same |

`rebuild-derived-state` itself appends its measurement and grade-interpretation rows and repacks the FTS index, as at
every tag; the upgrade alone does neither.

**(c) The kill switch.** `k31` is a copy of the upgraded and rebuilt mvp-0.31 vault with
`[workbench] field_signals_enabled = false`. It was compared with `base30`, main's mvp-0.30 vault opened by the
merge.
- Today (no session, a session, greedy): **byte-identical**.
- Certification and curves: identical apart from the version label.
- The placement reads (`ft_dump.py`: the field derivation and per-LO blocking set, the fast-track verdict for every
  LO with answers, the quick check's split over them, the sidecar's Today queue (default and 25 minutes) and Start,
  then the persisting `reconcile_fast_track`): identical apart from the label.
- The plan: identical apart from the four `algorithmVersion` fields and the decision row's stamp and run hashes.
- The same holds with the G41 test's workbench history seeded on both copies (`s30` vs `sk31`: a stuck step with
  text on an abandoned session, and a hint before the first step).

**(d) Defaults at `mvp-0.31`.**
- **On these vaults as they are:** nothing changes. Neither copy holds a workbench session, step or help row, so
  `d31` reads exactly like `base30` (the same comparisons as (c)), and no `field_signal_receipts` row is written.
- **With the seeded history** (`s30` vs `son31`):
  - The seeded LO gains the two blocking rows (`workbench_stuck:st_rw2d_landing`, `workbench_help:wb_rw2d_landing_h`).
  - On LA, the LO's fast-track verdict reason becomes `blocked_by_signal` (it was `below_threshold`, so it
    withholds either way). One `field_signal_receipts` row records both sides.
  - On probability, the LO's new item is taught first in Today, the 25-minute queue and every build. The item card
    reads "taught first: you asked about this topic or needed help on it", with `taught_first_predecessor` 0.0 as
    the receipt.
  - Certification, curves and the plan are unchanged apart from the label.
- **No served change elsewhere.** On these copies no LO's fast-track fired before, so none is withheld, and no
  quick check was open.

**Calls.** `model_call_receipts` has 0 rows in all 49 parity databases (no COMPLETED row, no row at all), and no
process was started. Spend: $0.

### Owner notes

- Upgrade with `learnloop upgrade --to mvp-0.31`, or the bare `learnloop upgrade` (the default target). Before
  running it: take a backup, and close the app, MCP and the mobile host.
  - From `mvp-0.30` it is one step. From `mvp-0.29`, or `mvp-0.9` to `mvp-0.27`, it chains through AD2+AD3's step.
    From `mvp-0.8`, run `--to mvp-0.9` first.
  - Then run `rebuild-derived-state` (it clears the version-stamp-only shadow differences).
- **What the learner sees:** nothing new on screen. Routing changes only, and only once the workbench holds a stuck
  step or help asked for before the first step: that LO is not fast-tracked or assumed known by the quick check, and
  its new material is taught first, with the "taught first" reason on the card. The record never changes.
- **Kill switch:** `[workbench] field_signals_enabled = false`. Serving and plans are then the predecessor's, and
  no workbench table is read.

### Open items

1. **F3 (Low, ruled non-blocking under the proportionate bar).** Once a session's attempt exists, the attempt's
   subject (taken from today's item at submit) overrides the subject frozen with the contract. This only matters if
   the item's subject is edited between the session and the submit; per-LO routing is unaffected.
2. **Rulings at their defaults** (§7):
   - Migration 219 accepted.
   - Empty stuck steps are not signals.
   - Workbench rows are not counted as questions in report 2.
   - The frozen-subject design stands.
   - A declared-stuck session keeps its step-time confusion row whatever the grader reads (first review, open
     question 2).
3. `desktop_validate.py` and `module_validate.py` fail as before this stage (above).
4. During parity setup a read-only open of the backups left empty `state.sqlite-wal` and `-shm` files beside both
   backup databases in the main checkout's `fixtures-local/vault-backups-20261024-mvp029/`. They are harmless and
   were left in place.
