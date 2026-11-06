# Teacher TE2-log: Codex review and fixes

Review: gpt-6.1-sol, job `20261106-003140-E8EcRZ`, of `c2e810f940..teacher/te2-log` at `33fd5d9274` (source
inspection only; the reviewer's sandbox could not reach the user bus, so it ran no tests). Two Medium findings, no
High. Both reproduced as failing tests before the fix and pass after it.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Unvalidated node references can put protected text into episode rows | fixed | `f0d379b2bb` | `tests/test_teacher_te2log_episodes.py`: `test_a_note_detour_on_a_node_the_plan_lacks_is_refused_back_and_never_logged`, `test_a_note_on_a_node_its_own_turns_plan_introduces_is_logged_in_either_order`, `test_reserved_text_in_a_plan_node_id_never_reaches_a_row`, `test_a_plan_lo_id_that_is_no_vault_lo_never_reaches_a_row` |
| F2 | Medium | One refused placement forecast rolls back sibling forecasts | fixed | `f0d379b2bb` | `tests/test_teacher_te2log_node_held.py::test_one_refused_node_forecast_leaves_its_siblings` |

### F1: what changed

Reproduced: a `note_detour` with `node` set to the fixture's `RESERVED_SENTINEL` was accepted and copied into
`lesson_episodes.node_id`, filed under the goal LO; an unknown node `n_unknown` was accepted the same way; a
foundation's plan `id` carrying the sentinel was copied into the unlogged detour's `node_id` and the
`lesson_node_held` receipt's key and inputs; a plan `lo_id` carrying it was copied into the episode's
`learning_object_id` and the receipt's `learning_object_id`.

Fix (`src/learnloop/teacher/episodes.py`, `src/learnloop/teacher/service.py`):

- **Nodes resolved at the contract check.** A `note_detour`'s `node` must name a node of the lesson's latest plan, a
  node of a plan its own turn writes (before or after the note in the request list), or a brief LO
  (`episodes.node_known`); otherwise the turn is refused back as a contract problem ("note_detour's node is not a
  node of your plan"; the node is not echoed into the detail).
- **Ids pass the output guards.** With `teacher.episode_log` on, the note's `node` and every plan node `id` in the
  turn join the hypothesis in the guard pass that runs before the turn is accepted (`episodes.logged_ids`, through
  `service._logged`): a hit withholds the turn, as a hypothesis hit does. Off, `_logged` returns nothing, so TE1's
  lesson is unchanged.
- **LOs are vault LOs or none.** An episode's `learning_object_id` and a `lesson_node_held` receipt's LO come from
  `episodes.outline_lo` / `episodes.node_lo`: the node's `lo_id` when it is a vault LO, else the node id when that is
  a vault LO, else none. The goal-LO fallback (`LessonState.node_lo`) is no longer used for episode rows; a node
  with no resolvable LO writes no `lesson_node_held` receipt and an unlogged detour with a null LO.

TE1's own `forecast` action and `LessonState.node_lo` are untouched (outside this stage's scope).

### F2: what changed

Reproduced: three nodes with `p_held` (`n0`, `n1`, `nx`), the middle insert refused: none of the three receipts was
written, because `_plan_episodes` passed all of them to one `record_receipts` call, whose savepoint and exception
handler wrap the whole list. Fix: `_plan_episodes` calls `record_receipts` once per receipt, so each is its own
savepoint of the plan's transaction; the regression test now finds `n0` and `nx` written and `n1` absent, with the
plan and its marker standing.

### The review's other claims

- "Ids and numbers only … no protected text": holds after F1 (model ids are resolved and guarded; an LO is a vault
  id). "Every row is written in its own savepoint": holds after F2.
- Spec conformance table: no further defect named. The probe refusal breakdown in the report stays deferred, as the
  stage review file records.

### Unchanged measurements

The turn schema is unchanged by these fixes (no field added or removed), so the stage review file's schema sizes,
rows per kind and report output stand. Lessons with `teacher.episode_log` off stay byte-identical
(`test_switch_off_keeps_te1s_lesson_byte_identical` passes). No model request was added; no live or paid call was
made in this step.

## Gate (this step)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| `lint-imports --no-cache` (isolated env) | 43 kept, 0 broken |
| Reproduction, before the fix: the 5 new tests | 5 failed |
| pytest `-n 6` `tests/test_teacher_te2log_episodes.py tests/test_teacher_te2log_node_held.py` | 22 passed |
| pytest `-n 6`, every test file importing `learnloop.teacher` or `teacher_fakes` (28 files) plus `tests/test_forecast_receipts.py`, `tests/test_forecast_receipts_landing.py` | 419 passed |
| pytest `-n 6`, the contract set and every test naming `lesson_weight` or `forecast_report` (30 files, listed below) | 830 passed, 6 skipped, 1 failed: `test_regrade_contract_successor.py::test_a_held_unrecorded_grade_is_no_evidence`, unrelated to the teacher (regrade/mastery replay; it opens no lesson); rerun alone: 1 passed; its file with `-n 6`: 43 passed |
| `module_generate.py`, `module_validate.py` (isolated env) | regenerated (commit `412b2d5614`), PASS |
| pytest `-n 6` `test_module_catalog_inventory`, `test_public_tip_guards`, `test_tracked_fixture_databases` after the regenerated reference | 26 passed |

No migration, schema, DB/connection, frontend or `src-tauri` change in this step, so no durability lane, npm, vitest,
cargo or DB reference run.

Test files run (contract set and lesson-weight/forecast-report run): `test_ad_protected_tables`,
`test_ai_tool_isolation`, `test_architecture` (frozen cycles), `test_cli_help_snapshot`,
`test_codex_lockdown_round3`, `test_codex_tool_lockdown`, `test_cold_retry_reschedule`, `test_config_refactor`,
`test_e0_isolation` (process-launch allowlist with the two Codex lockdown files and `test_ai_tool_isolation`),
`test_forecast_receipts`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_router_why_copy`,
`test_rw5c_labels` (the display-label audit with the two before), `test_module_catalog_inventory`,
`test_public_tip_guards`, `test_reader_rw5d_p4b_teacher_visuals`, `test_rebuild_orchestrator`,
`test_registry_audit`, `test_regrade_contract_successor`, `test_ro1_availability_reads`, `test_sidecar_contract`,
`test_table_roles`, `test_teacher_te1_migration`, `test_teacher_te1_review_fixes`, `test_teacher_te1_successor`,
`test_teacher_te1_weight`, `test_teacher_te2log_episodes`, `test_teacher_te2log_node_held`,
`test_tracked_fixture_databases`.

Teacher run: the 28 files `git grep -l "learnloop.teacher\|teacher_fakes\|from learnloop.teacher" tests` lists
(less `teacher_fakes.py`), including every `test_teacher_*`, `test_followups_batch5_*`/`batch6_*`/`batch7_*`,
`test_figures_prefetch*`, `test_notes_never_read`, `test_data_capture_*`, `test_followup_single_use`,
`test_followups_nov2_figure_provenance` and `test_reader_rw5d_p4b_teacher_visuals`.

New tests: `tests/test_teacher_te2log_episodes.py` 13 -> 17, `tests/test_teacher_te2log_node_held.py` 4 -> 5.
