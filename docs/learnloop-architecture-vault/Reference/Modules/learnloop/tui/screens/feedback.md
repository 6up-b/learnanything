---
title: "learnloop.tui.screens.feedback"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/feedback.py"
source_paths:
  - "src/learnloop/tui/screens/feedback.py"
source_commit: "c6d5a6ae6d6d85ed8dd0a3f1455d0e1ab40b54c9"
source_commit_timestamp: "2026-10-12T23:02:34-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tui.screens"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.tui.screens.feedback module"
  - "src/learnloop/tui/screens/feedback.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui-screens"
---

# `learnloop.tui.screens.feedback`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps feedback behavior inside its owning package, [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]]. Its public surface centers on `FeedbackScreen`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/feedback.py](../../../../../../../src/learnloop/tui/screens/feedback.py) |
| Source lines | 681 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c6d5a6ae6d6d85ed8dd0a3f1455d0e1ab40b54c9` |
| Commit timestamp | `2026-10-12T23:02:34-04:00` |

## Public API

- `class FeedbackScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/feedback.py), line 34) — Grade an attempt, then show the prototype's read-only results display.
  - `__init__(self, state: TuiState, item: ScheduledItem, draft: AttemptDraft, *, committed: AttemptResult | None=None)` (line 57; internal)
  - `compose(self) -> ComposeResult` (line 88; public)
  - `on_mount(self) -> None` (line 145; public)
  - `watch_surprise_direction(self, value: str | None) -> None` (line 162; public)
  - `watch_graded(self, value: bool) -> None` (line 165; public)
  - `watch_has_errors(self, value: bool) -> None` (line 168; public)
  - `_rubric_content(self) -> Content` (line 171; internal)
  - `set_points(self, criterion_id: str, points: float) -> None` (line 185; public)
  - `set_confidence(self, confidence: int) -> None` (line 190; public)
  - `set_error_type(self, error_type: str | None) -> None` (line 195; public)
  - `toggle_fatal(self, fatal_error_id: str) -> None` (line 200; public)
  - `submit(self) -> AttemptResult` (line 210; public)
  - `_submit(self) -> AttemptResult` (line 214; internal)
  - `async auto_submit_ai(self) -> AttemptResult | None` (line 257; public)
  - `async _auto_submit_ai(self) -> AttemptResult | None` (line 262; internal)
  - `_committed_result(self) -> AttemptResult | None` (line 309; internal)
  - `async auto_submit_codex(self) -> AttemptResult | None` (line 312; public)
  - `_grading_provider(self)` (line 315; internal)
  - `_ai_ready(self) -> bool` (line 324; internal)
  - `_provider_label(self) -> str` (line 328; internal)
  - `_run_inline_diagnosis(self, result: AttemptResult) -> None` (line 332; internal) — Slice 1 §11: the TUI has no daemon; a queued diagnosis runs inline after the grade is shown, and its summary is shown when it finishes.
  - `_complete_result(self, result: AttemptResult, *, model: bool=True) -> None` (line 361; internal)
  - `_render_results(self, result: AttemptResult) -> None` (line 416; internal)
  - `_record_worked_answer_reveal(self, result: AttemptResult) -> None` (line 426; internal) — The worked answer is now visible: debit the reveal ledger (re-review F8).
  - `_worked_answer_content(self) -> Content` (line 445; internal) — The item's worked answer, shown after an empty stuck answer.
  - `_result_head_content(self, result: AttemptResult) -> Content` (line 455; internal)
  - `_score_block_content(self, result: AttemptResult) -> Content` (line 464; internal)
  - `_rubric_evidence_content(self, result: AttemptResult) -> Content` (line 481; internal)
  - `_tutor_note_content(self, result: AttemptResult) -> Content` (line 514; internal)
  - `_error_content(self, result: AttemptResult) -> Content` (line 525; internal)
  - `_belief_content(self, result: AttemptResult) -> Content` (line 554; internal)
  - `_followup_content(self) -> Content` (line 571; internal)
  - `_schedule_content(self, result: AttemptResult) -> Content` (line 591; internal)
  - `_criterion_mark(self, awarded: float, points: float) -> tuple[str, str]` (line 603; internal)
  - `_mastery_mean_sd(self) -> tuple[float, float]` (line 610; internal)
  - `_breadcrumb_content(self) -> Content` (line 618; internal)
  - `_read_form_state(self) -> None` (line 629; internal)
  - `_render_fatal_summary(self) -> None` (line 640; internal)
  - `return_to_today(self) -> None` (line 646; public)
  - `action_submit(self) -> None` (line 652; public)
  - `action_next(self) -> None` (line 655; public)
  - `advance_to_next(self) -> None` (line 664; public)
  - `action_back(self) -> None` (line 672; public)
  - `on_button_pressed(self, event: Button.Pressed) -> None` (line 675; public)

### Module constants

- `_RATING_PILL` ([src/learnloop/tui/screens/feedback.py](../../../../../../../src/learnloop/tui/screens/feedback.py), line 31)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `FeedbackScreen`; statically calls `FeedbackScreen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `AttemptResult`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`; calls `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `UNASSESSED_CRITERION_LABEL`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `committed_submission_result`, `run_post_attempt_pipeline`; calls `committed_submission_result`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_answer_display_reveal`; calls `record_answer_display_reveal`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `FollowupDecision`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `end_diagnostic_block`; calls `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DIAGNOSE_KIND`, `DONE`, `NOT_NEEDED`, `diagnosis_status`, `drain`; calls `diagnosis_status`, `drain`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `unassessed_evidence_row`; calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `TodayScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mode_pill_color`, `pill`; calls `KeyBar`, `TextStatic`, `block_bar`, `mode_pill_color`, `pill`

### Platform and third-party dependencies

- Standard library: `__future__`, `asyncio`, `types`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_active_errors_overlay.py](../../../../../../../tests/test_active_errors_overlay.py) — direct import
- [tests/test_daily_loop_start_minutes.py](../../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
- [tests/test_e2e_tui.py](../../../../../../../tests/test_e2e_tui.py) — direct import
  - `test_tui_end_to_end_self_graded_practice`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_feedback_shows_an_unverified_criterion_as_not_assessed`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_stuck_prompt.py](../../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred`
  - `test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer`
- [tests/test_tui_feedback.py](../../../../../../../tests/test_tui_feedback.py) — direct import
  - `test_committed_model_grade_is_not_regraded_when_a_later_step_fails`
  - `test_feedback_submit_matches_cli_attempt_and_updates_state`
- [tests/test_tui_practice.py](../../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_collects_answer_and_opens_feedback`
  - `test_practice_screen_submit_button_opens_feedback`
  - `test_practice_screen_submit_shortcut_opens_feedback`
  - `test_practice_screen_uses_item_allowed_attempt_type`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/screens/feedback.py](../../../../../../../src/learnloop/tui/screens/feedback.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
