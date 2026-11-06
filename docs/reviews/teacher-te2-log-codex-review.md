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

## Scoped verify and the landing's rulings R1, R2

Scoped verify: gpt-6.1-sol, job `20261106-005255-g8i1fq`, of `f0d379b2bb` on F1, F2 and the switch-off identity.
F2 and the switch-off identity CONFIRMED-FIXED, no new finding; **F1 REOPENED on two paths**. The orchestrator's
rulings R1 (both paths, fixed structurally; no further Codex round on this class) and R2 (TE1's forecast action) are
recorded verbatim in `docs/reviews/teacher-te2-log.md` under "Landing onto main".

| Ruling | Path | Commit | Tests (each failed on the pre-fix source) |
|---|---|---|---|
| R1 (a) | A plan node whose id is the reserved key of an LO the brief never named (`lo_id` that LO, `p_held` 0.6) was accepted and copied into `lesson_episodes.node_id` and the `lesson_node_held` receipt's key and inputs: the guard read only `state.los`'s keys | `c301f12a6f` | `test_a_plan_node_carrying_another_los_reserved_key_is_withheld_by_location`, `test_a_plan_lo_id_carrying_a_reserved_key_is_withheld_by_location` |
| R1 (b) | A contract refusal echoed the model's text before any guard ran (`plan node <reserved>: these anchors don't resolve: S999`); a schema refusal echoed pydantic's `input_value` | `c301f12a6f` | `test_a_contract_refusal_names_the_field_by_location_never_by_its_text`, `test_a_schema_refusal_names_fields_by_location_never_by_their_input` |
| R2 | TE1's `forecast` copied `request.node`, and the node's plan `lo_id`, into its receipt unchecked (switch off: an unknown node and a reserved node id / `lo_id` were all written) | `1c4bb43506` | `test_te1s_forecast_node_is_resolved_and_guarded_with_the_switch_off` (and `test_te1s_forecast_on_a_known_node_is_unchanged_with_the_switch_off`, a pin that passes before and after) |
| R1 (a), R2 (found at the landing smoke) | With the switch off, TE1's own plan node ids and `lo_id` reached a receipt (the lesson receipt's `nodes`), `lesson_plans` and the transcript unguarded (as on main); a posed check's node reaches a visual's record in the receipt | `c1bfacd662` | `test_te1s_plan_ids_reaching_the_lesson_receipt_are_guarded_with_the_switch_off` (failed on `1c4bb43506`'s source) |

What changed:

- **The identifier guard** (`guards.identifier_guard`, keys from `guards.key_sets`, one KeyBook read for both sets):
  every model-supplied field a log row, a receipt or a note's payload copies is checked against **every answer key
  the vault records, on any LO, with no exemption** (an exam-reserved or held-out item's included, an LO the brief
  never named and one a plan adds in the same turn included), after the existing output guards. The fields
  (`service._logged`, `episodes.logged_fields`), on every turn, the switch off included: each plan node's id and
  `lo_id` (the lesson receipt's `nodes` copy them; `c1bfacd662`), the posed check's and prediction's node, each
  forecast's node and the LO its receipt will hold (`service._forecast_lo`, mirroring `_forecast`; R2); with
  `teacher.episode_log` on also a note's hypothesis and node. A hit withholds the turn; an unreadable KeyBook
  withholds it (fail closed).
- **Refusals by location.** Every contract refusal (`service._contract_problem`, `visuals.contract_problem`) names the
  field by its location (`requests[0].plan[1].anchors[0]`, `check.anchors[2]`, `requests[0].node`,
  `visual.planned_node`), never by its text; a guard refusal names the field the same way
  (`requests[0].plan[0].id: …`); a schema refusal (`service._schema_detail`) gives each failing field's location and
  pydantic's message (`requests[0].node: String should have at most 80 characters`), never its input, an undeclared
  key reading `?` and a failure naming no field one fixed line.
- **R2's node resolution.** A forecast whose node its receipt copies (every forecast but a check forecast with a
  check open or posed in the turn, whose receipt names the code-made check ref) must name a node of the latest
  plan, of a plan the turn writes, or a brief LO (`episodes.node_known`, the note's rule); otherwise it is refused
  by location. `LessonState.node_lo` gains an optional `outline` (default unchanged).

Changed pins: TE1's `test_a_plan_whose_anchors_do_not_resolve_is_refused_back_to_the_teacher` and the visuals'
`test_a_visual_the_lesson_cannot_build_is_refused_back_to_the_teacher` pinned the echoed anchor text and now pin the
location (R1 (b) applies to TE1's refusals too, so a refused turn's detail line reads differently with the switch
off; nothing else of a TE1 lesson changes). `test_a_plan_lo_id_that_is_no_vault_lo_never_reaches_a_row` now uses an
unprotected unknown LO id, since a reserved one is withheld.

What a refused turn keeps: as TE1 does for every withheld or invalid turn, the refused turn's own `lesson_turns`
payload still records the model's raw turn (write-only: neither the transcript, the view nor any report reads a
refused turn's `turn`); no episode row, interval, receipt, stored plan, transcript line or screen holds the text.

### Gate (this step)

Every pytest inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`; every
other Python or CLI under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call.

| Command | Result |
|---|---|
| Reproduction, before the fixes: the 5 new R1/R2 tests | 5 failed (the R2 pin passed) |
| pytest, the 28 teacher files and `test_forecast_receipts`, `test_forecast_receipts_landing`, after R1 | 2 failed (the two pins above), then 423 passed |
| the same after R2 | 5 failed first (4 TE1 and visuals tests forecasting on a posed check's node with no plan, so a check forecast with a check open or posed no longer resolves its node, its receipt never copying it; and the new R2 test, which hit the three-refusals-in-a-row limit and now splits its refusals over two actions), then 425 passed |
| pytest `-n 6`: every `test_teacher_*`, `test_forecast_receipts*`, every test naming `lesson_weight`, the teacher files, the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), `test_cli_help_snapshot`, `test_architecture`, `test_table_roles`, `test_registry_audit`, `test_tracked_fixture_databases`, `test_coordinated_migrations`, `test_migrations`, `test_codex_lockdown_round3`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot` (52 files) | 786 passed |
| pytest `--durable-sqlite` on the touched test files | 62 passed |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| After `c1bfacd662` (reproduced first on `1c4bb43506`'s source: 1 failed): the 28 teacher files and both forecast-receipt files; `--durable-sqlite` on the episodes file; `lint-imports` | 426 passed; 24 passed; 43 kept, 0 broken |

New tests: `tests/test_teacher_te2log_episodes.py` 17 -> 24.
