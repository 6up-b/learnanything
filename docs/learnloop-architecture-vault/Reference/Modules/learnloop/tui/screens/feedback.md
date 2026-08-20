---
title: "learnloop.tui.screens.feedback"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/feedback.py"
source_paths:
  - "src/learnloop/tui/screens/feedback.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
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
| Source lines | 533 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FeedbackScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/feedback.py), line 33) — Grade an attempt, then show the prototype's read-only results display.
  - `__init__(self, state: TuiState, item: ScheduledItem, draft: AttemptDraft)` (line 56; internal)
  - `compose(self) -> ComposeResult` (line 76; public)
  - `on_mount(self) -> None` (line 132; public)
  - `watch_surprise_direction(self, value: str | None) -> None` (line 144; public)
  - `watch_graded(self, value: bool) -> None` (line 147; public)
  - `watch_has_errors(self, value: bool) -> None` (line 150; public)
  - `_rubric_content(self) -> Content` (line 153; internal)
  - `set_points(self, criterion_id: str, points: float) -> None` (line 167; public)
  - `set_confidence(self, confidence: int) -> None` (line 172; public)
  - `set_error_type(self, error_type: str | None) -> None` (line 177; public)
  - `toggle_fatal(self, fatal_error_id: str) -> None` (line 182; public)
  - `submit(self) -> AttemptResult` (line 192; public)
  - `async auto_submit_ai(self) -> AttemptResult | None` (line 224; public)
  - `async auto_submit_codex(self) -> AttemptResult | None` (line 260; public)
  - `_grading_provider(self)` (line 263; internal)
  - `_ai_ready(self) -> bool` (line 272; internal)
  - `_provider_label(self) -> str` (line 276; internal)
  - `_complete_result(self, result: AttemptResult) -> None` (line 280; internal)
  - `_render_results(self, result: AttemptResult) -> None` (line 323; internal)
  - `_result_head_content(self, result: AttemptResult) -> Content` (line 333; internal)
  - `_score_block_content(self, result: AttemptResult) -> Content` (line 342; internal)
  - `_rubric_evidence_content(self, result: AttemptResult) -> Content` (line 359; internal)
  - `_tutor_note_content(self, result: AttemptResult) -> Content` (line 382; internal)
  - `_error_content(self, result: AttemptResult) -> Content` (line 393; internal)
  - `_belief_content(self, result: AttemptResult) -> Content` (line 420; internal)
  - `_followup_content(self) -> Content` (line 437; internal)
  - `_schedule_content(self, result: AttemptResult) -> Content` (line 457; internal)
  - `_criterion_mark(self, awarded: float, points: float) -> tuple[str, str]` (line 469; internal)
  - `_mastery_mean_sd(self) -> tuple[float, float]` (line 476; internal)
  - `_breadcrumb_content(self) -> Content` (line 484; internal)
  - `_read_form_state(self) -> None` (line 495; internal)
  - `_render_fatal_summary(self) -> None` (line 506; internal)
  - `return_to_today(self) -> None` (line 512; public)
  - `action_submit(self) -> None` (line 518; public)
  - `action_next(self) -> None` (line 521; public)
  - `action_back(self) -> None` (line 524; public)
  - `on_button_pressed(self, event: Button.Pressed) -> None` (line 527; public)

### Module constants

- `_RATING_PILL` ([src/learnloop/tui/screens/feedback.py](../../../../../../../src/learnloop/tui/screens/feedback.py), line 30)

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
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_post_attempt_pipeline`; calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `FollowupDecision`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `end_diagnostic_block`; calls `end_diagnostic_block`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `TodayScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mode_pill_color`, `pill`; calls `KeyBar`, `TextStatic`, `block_bar`, `mode_pill_color`, `pill`

### Platform and third-party dependencies

- Standard library: `__future__`, `asyncio`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e2e_tui.py](../../../../../../../tests/test_e2e_tui.py) — direct import
  - `test_tui_end_to_end_self_graded_practice`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_tui_feedback.py](../../../../../../../tests/test_tui_feedback.py) — direct import
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
