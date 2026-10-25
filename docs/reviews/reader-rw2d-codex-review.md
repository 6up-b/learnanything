# Reader RW2d: Codex review fixes

Stage `reader-rw2d`, branch `reader/rw2d` in `learnanything-dl2`. Codex job `20261024-160344-sRKIcw` reviewed the stage
record at `2a779237b`. Fix commit: `e5ed41be9`. No migration, schema, DB/connection, frontend or Tauri change; no
model or network call (all tests use fakes; the F4 timing probe ran under `env -i` with an empty HOME).

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Worked-example requests after real work are classified as early help | fixed | `e5ed41be9` | Reproduced on the old module through the real producer (`workbench.show_example` after two ordinary steps: a `workbench_help:<session>` row with `help_before_work`). `_snapshot_has_work` now reads an identity-only entry (`chain_id`, `step_id`, `number`, `hash`) through the immutable `workbench_steps` row its `step_id` names; an entry whose row is not found leaves the snapshot unknown (no row), never "no work". Tests: `test_review_f1_a_worked_example_after_real_work_is_not_early_help` (real producer, asserts the production format, plus an empty-bench control), `test_review_f1_an_identity_only_snapshot_is_read_through_its_step_rows` |
| F2 | Medium | Submitting a stuck answer removes previously observed confusion | fixed | `e5ed41be9` | Reproduced on the old module: a stuck step with text, deleted, then the empty bench submitted as a declared-stuck answer, removed the row. The `declared_stuck` suppression is gone: the step-time row stays, from the step's own time, through delete, submit and later grading. **Deduplication, partly rejected:** the stuck answer's own `stuck:<attempt>` row is the predecessor's derivation, and G41/§5.11 pin that the predecessor's output is exactly this one without workbench rows, so it is not removed; both rows are zero-mass and blocking is set-valued per LO (`placement.signals._by_lo`), so nothing is counted twice. Tests: `test_review_f2_a_stuck_answer_keeps_the_step_time_row_through_delete_submit_and_grading`, `test_review_f2_the_row_survives_the_submit_on_the_vault` |
| F3 | Medium | Editing an item silently moves historical signals to another LO | fixed | `e5ed41be9` | Reproduced on the old module (moving `pi_diag_easy` to `lo_eigen_basics` moved the row). An unsubmitted session's LO now comes from the assessment contract it froze (`workbench_sessions.assessment_contract_version_id` -> `contract_json.learning_object_id`, only for a contract snapshotted for the session's own item); no readable contract is unmapped, never today's item. Subject: none is recorded before a submit, so it is today's label for the frozen LO (the item's when it still targets that LO, else the LO's first subject, else `default`); live routing blocks per LO only; recording a session-time subject needs a column and is left as an open question. Test: `test_review_f3_an_edited_or_removed_item_keeps_the_signal_on_the_frozen_lo` (real `snapshot_for_presentation`); `test_no_row_for_an_empty_stuck_step_or_an_unbound_problem` covers a bound session with no contract |
| F4 | Medium | Step-chain resolution has cubic cost on retained edit history | fixed | `e5ed41be9` | Reproduced: old `_chain_roots` 0.161 s at 500 versions, 1.287 s at 1,000; new 0.0002 s / 0.0005 s / 0.0014 s at 500 / 1,000 / 3,000. Roots are memoized with path compression and a set for cycle detection, and only the chains of stuck steps with text are resolved. Test: `test_review_f4_a_long_autosaved_history_resolves_in_linear_time` (4,000 ordinary and 3,000 stuck autosaved versions, under 2 s, root correct) |

The "claims that don't hold" list maps onto F1-F2 (fixed above); the production-format gap is closed by the real
producer test. The spec-conformance note "required shadow rebuild explicitly unperformed" stands as recorded in the
stage file's open question 5 (no change here: a rebuild never reads the workbench tables).

Docs updated: `docs/reviews/reader-workbench-RW2d.md` (§1 bullets, open question 2) and
`docs/specs/spec_reader_workbench_v1.md` §5.11 "As built".

### Gate (this step)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: **31 kept, 0 broken**.
* Reproduction (old module swapped in temporarily, then restored): the F1, F2 and F3 loader tests **3 failed**; on the
  fix, all pass.
* Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6`
  over 21 files: **704 passed** (0 failed, 0 skipped reported). `tests/test_field_workbench_signals.py` alone:
  **26 passed**.
* Not run (nothing in scope changed): durability lane (no migration or DB/connection code), npm/vitest/frontend
  build, cargo check, DB reference scripts (no schema change). Full suite: landing gate only (owner rule 2026-10-17).

Test files run: `test_architecture.py`, `test_field_workbench_signals.py`, `test_interaction_signals.py`,
`test_learner_text_gaps_composition.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_review.py`,
`test_placement_signals.py`, `test_reader_rw1c_review.py`, `test_reader_rw2b_review.py`,
`test_rw2d_receipts_migration.py`, `test_stuck_prompt_composition.py`, `test_stuck_prompt.py`,
`test_stuck_prompt_replay.py`, `test_quick_check.py`, `test_assumed_known.py`, `test_workbench_route_example.py`,
`test_placement_report.py`, `test_integration_daily_loop_field.py`, `test_family_memory_projection.py`,
`test_tracked_fixture_databases.py`, `test_table_roles.py`.

### Open questions

1. A session-time subject for unsubmitted sessions (F3) is not recorded; report 2's per-subject simulation reads
   today's label for the frozen LO. Recording it would add a column to `workbench_sessions` (owner call).
2. With F2's fix, a declared-stuck session whose stuck text the grader read as NOT confusion still carries the
   step-time confusion row, as every mid-work stuck step with text already does (no grader reading is consulted for
   steps). The owner may prefer the grader's reading to win once it exists; that would reintroduce a post-submit
   change to history, which F2 argues against.

## Re-review

Codex job `20261024-162212-95ZzTr` re-reviewed `2a779237b..reader/rw2d` (fix commit `e5ed41be9`): F1, F2 and F4
CONFIRMED-FIXED, F3 REOPENED (subject attribution), no new defects. Open question 1 above is resolved by the F3 fix
below. Fix commits: `685d612c5` (code, migration 219, head fixture), `0c0349bda` (earlier migrations' schema diffs),
`7401930c4` (DB references at head 219), `d1a8da13a` (stage record, spec §5.11 as built).

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Worked-example requests after real work are classified as early help | fixed (confirmed by re-review) | `e5ed41be9` | unchanged; tests as above |
| F2 | Medium | Submitting a stuck answer removes previously observed confusion | fixed (confirmed by re-review) | `e5ed41be9` | unchanged; tests as above |
| F3 | Medium | Historical subject attribution reads today's item/LO subject (reopened) | fixed | `685d612c5`, `0c0349bda`, `7401930c4`, `d1a8da13a` | Reproduced: the new loader test run against the `e5ed41be9` derivation fails (a session with no recorded subject came back as today's `linear-algebra`, not as missing provenance; with the subject edit the old code relabelled rows, as the re-review's probe showed). Fix: migration 219 (this stage's, not landed) adds `workbench_sessions.contract_subject_id`, written once with `assessment_contract_version_id` by the sidecar's contract freeze (the subject a submit would then record: the item's first subject, else its LO's, else `default`, as `attempts.py` does) and cleared with it on a bind to another item. The field reads it and nothing from today's vault (`_contract_targets` no longer takes the vault); a session whose subject was never recorded gets the explicit `SUBJECT_UNRECORDED` (`workbench:subject-unrecorded`), which no subject-aware check matches, counted in `workbench_subject_unrecorded_sessions`; per-LO routing still blocks it. Head fixture `migration_head_219` rebuilt (rollback mode). Tests: `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract` (edits the items' and LOs' subjects to `physics`: rows and `confusion_blocks_fast_track` unchanged for the original subject, not blocked for `physics`; unrecorded session says so; routing blocks both), `test_rereview_f3_the_sidecar_records_the_subject_with_the_contract` (real sidecar open records it; a resume after the subject edit keeps it; a bind clears both), `test_rw2d_receipts_migration.py` (pins the column) |
| F4 | Medium | Step-chain resolution has cubic cost on retained edit history | fixed (confirmed by re-review) | `e5ed41be9` | unchanged; tests as above |

No new parameter: `SUBJECT_UNRECORDED` is a sentinel id, not a weight, margin or threshold. No model or network
call; all tests use fakes; the reference scripts ran under `env -i` with empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR.

### Gate (this step)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: **31 kept, 0 broken**.
* Reproduction (the `e5ed41be9` `workbench_signals.py` swapped in with the sentinel constant appended, then
  restored): `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract` **1 failed**; on the fix it passes.
* Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6`
  over 61 files: **1,487 passed** (0 failed, 0 skipped reported).
* Durability: `uv run pytest -n 6 -m durability` over `test_rw2d_receipts_migration.py`, `test_migrations.py`,
  `test_coordinated_migrations.py`, `test_migration_coordinator.py`, `test_tracked_fixture_databases.py`,
  `test_field_workbench_signals.py`, `test_reader_workbench_rw2a.py`: **3 passed**; plus `--durable-sqlite` over
  `test_rw2d_receipts_migration.py` and `test_field_workbench_signals.py`: **32 passed**.
* DB references: `db_generate_reference.py` (340 table notes) and `db_validate_reference.py` (**0 errors**); the
  rerun changed only the `source_commit` stamps, so the committed references at `7401930c4` stand.
* Not run (nothing in scope changed): npm/vitest/frontend build, cargo check. Full suite: landing gate only (owner
  rule 2026-10-17).

Test files run: `test_architecture.py`, `test_field_workbench_signals.py`, `test_interaction_signals.py`,
`test_learner_text_gaps_composition.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_review.py`,
`test_placement_signals.py`, `test_reader_rw1c_review.py`, `test_reader_rw2b_review.py`,
`test_rw2d_receipts_migration.py`, `test_stuck_prompt_composition.py`, `test_stuck_prompt.py`,
`test_stuck_prompt_replay.py`, `test_quick_check.py`, `test_assumed_known.py`, `test_workbench_route_example.py`,
`test_placement_report.py`, `test_integration_daily_loop_field.py`, `test_family_memory_projection.py`,
`test_tracked_fixture_databases.py`, `test_table_roles.py`, `test_ad1_migration.py`, `test_approach_maps_schema.py`,
`test_help_assists_schema.py`, `test_library_asks_migration.py`, `test_reader_rw3b_migration.py`,
`test_reader_rw7a_migration.py`, `test_t1_batch_origin_migration.py`, `test_migrations.py`,
`test_coordinated_migrations.py`, `test_migration_coordinator.py`, `test_reader_workbench_rw2a.py`,
`test_help_outcomes.py`, `test_hint_telemetry.py`, `test_workbench_assistance.py`, `test_workbench_check.py`,
`test_workbench_check_kinds.py`, `test_workbench_check_map.py`, `test_workbench_chooser.py`,
`test_workbench_discriminate.py`, `test_workbench_help_kill_switch.py`, `test_workbench_hint_service.py`,
`test_workbench_hints.py`, `test_workbench_in_session_gaps.py`, `test_workbench_passage_draw.py`,
`test_workbench_report.py`, `test_workbench_step_graph.py`, `test_workbench_text_gaps.py`, `test_workbench_trace.py`,
`test_compare_methods.py`, `test_library_exercises.py`, `test_library_ask_review.py`,
`test_reader_find_sources_callers.py`, `test_reader_recap.py`, `test_reader_tutor_retrieval.py`,
`test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_mobile_allowlist.py`,
`test_rebuild_orchestrator.py`, `test_shadow_rebuild.py`, `test_diagnosis_replay.py`.

### Open questions

1. Sessions whose contract was frozen before migration 219 (none outside this unlanded stage's own branch) read as
   `SUBJECT_UNRECORDED`; report 2's per-subject simulation leaves them out of every subject rather than guessing.
2. Open question 2 of the first review (the grader's reading of a declared-stuck answer) stands.
