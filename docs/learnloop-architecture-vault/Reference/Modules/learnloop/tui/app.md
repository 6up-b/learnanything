---
title: "learnloop.tui.app"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/app.py"
source_paths:
  - "src/learnloop/tui/app.py"
source_commit: "a5ba091fb41892a7d117a17b3d31c0bd7259b903"
source_commit_timestamp: "2026-10-12T01:59:41-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tui"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.tui.app module"
  - "src/learnloop/tui/app.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui"
---

# `learnloop.tui.app`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps app behavior inside its owning package, [[Reference/Modules/learnloop/tui/_package|learnloop.tui]]. Its public surface centers on `ErrorScreen`, `LearnLoopApp`, `run`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/app.py](../../../../../../src/learnloop/tui/app.py) |
| Source lines | 59 |
| Owning package | [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a5ba091fb41892a7d117a17b3d31c0bd7259b903` |
| Commit timestamp | `2026-10-12T01:59:41-04:00` |

## Public API

- `class ErrorScreen(Screen)` ([source](../../../../../../src/learnloop/tui/app.py), line 13)
  - `__init__(self, message: str)` (line 14; internal)
  - `compose(self) -> ComposeResult` (line 18; public)
- `class LearnLoopApp(App)` ([source](../../../../../../src/learnloop/tui/app.py), line 23)
  - `__init__(self, vault_root: Path)` (line 34; internal)
  - `get_theme_variable_defaults(self) -> dict[str, str]` (line 40; public)
  - `on_mount(self) -> None` (line 46; public)
  - `get_default_screen(self) -> Screen` (line 50; public)
- `run(vault_root: Path) -> None` ([source](../../../../../../src/learnloop/tui/app.py), line 58)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/app_launch|learnloop.app_launch]] — imports `run`; statically calls `run`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `StartScreen`; calls `StartScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/theme|learnloop.tui.theme]] — imports `LEARNLOOP_THEME`, `LEARNLOOP_VARIABLES`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `TextStatic`; calls `TextStatic`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/app_launch|learnloop.app_launch]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_tui_esc_keeps_the_list_and_an_ungraded_next_returns_to_it`
  - `test_tui_next_opens_the_head_of_the_live_queue`
  - `test_tui_start_asks_for_minutes_only_and_starts_on_the_remembered_minutes`
  - `test_tui_start_lays_the_minute_chips_out_on_screen`
  - `test_tui_start_uses_25_minutes_on_a_fresh_vault_and_keeps_an_old_budget`
- [tests/test_daily_loop_start_postpone.py](../../../../../../tests/test_daily_loop_start_postpone.py) — direct import
  - `test_tui_start_screen_offers_no_postpone_it_cannot_honour`
- [tests/test_e2e_tui.py](../../../../../../tests/test_e2e_tui.py) — direct import
  - `test_tui_end_to_end_self_graded_practice`
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_tui_grading_records_receipts_with_usage`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_tui_open_serves_a_cold_check_submit_would_prime_as_practice`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_tui_ctrl_d_opens_the_stuck_prompt_and_an_empty_submit_records_it`
  - `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred`
  - `test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer`
- [tests/test_tui_app.py](../../../../../../tests/test_tui_app.py) — direct import
  - `test_tui_app_launches_start_screen_and_syncs_state`
  - `test_tui_app_shows_error_screen_for_missing_vault`
  - `test_tui_today_screen_renders_queue_details_and_refreshes`
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — direct import
  - `test_committed_model_grade_is_not_regraded_when_a_later_step_fails`
  - `test_feedback_screen_reads_visible_self_grade_controls`
  - `test_feedback_submit_matches_cli_attempt_and_updates_state`
  - `test_feedback_submit_uses_codex_grading_when_runtime_ready`
  - `test_tui_retry_resumes_a_committed_grade_instead_of_recording_another`
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_collects_answer_and_opens_feedback`
  - `test_practice_screen_dont_know_runs_shared_post_attempt_pipeline`
  - `test_practice_screen_submit_button_opens_feedback`
  - `test_practice_screen_submit_shortcut_opens_feedback`
  - `test_practice_screen_uses_item_allowed_attempt_type`
- [tests/test_tui_theme.py](../../../../../../tests/test_tui_theme.py) — direct import
  - `test_all_screen_stylesheets_resolve_when_mounted`
  - `test_app_registers_and_activates_learnloop_theme`
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/app.py](../../../../../../src/learnloop/tui/app.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
