---
title: "learnloop.tui.screens.practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/practice.py"
source_paths:
  - "src/learnloop/tui/screens/practice.py"
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
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.tui.screens.practice module"
  - "src/learnloop/tui/screens/practice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui-screens"
---

# `learnloop.tui.screens.practice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps practice behavior inside its owning package, [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]]. Its public surface centers on `PracticeScreen`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py) |
| Source lines | 489 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PracticeScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/practice.py), line 38) — Focused practice card for a single Practice Item.
  - `__init__(self, state: TuiState, item: ScheduledItem)` (line 66; internal)
  - `_resolve_probe_contract(self) -> None` (line 79; internal)
  - `compose(self) -> ComposeResult` (line 115; public)
  - `on_mount(self) -> None` (line 156; public)
  - `on_screen_resume(self) -> None` (line 160; public)
  - `watch_hints_used(self, value: int) -> None` (line 164; public)
  - `answer(self) -> str` (line 172; public)
  - `set_answer(self, text: str) -> None` (line 175; public)
  - `reveal_hint(self) -> None` (line 179; public)
  - `async open_feedback(self)` (line 191; public)
  - `dont_know(self)` (line 198; public)
  - `_draft(self, attempt_type: str | None=None) -> AttemptDraft` (line 220; internal)
  - `async action_submit(self) -> None` (line 237; public)
  - `action_hint(self) -> None` (line 241; public)
  - `action_stop_diagnosing(self) -> None` (line 244; public) — `Stop diagnosing and teach me` (§3): end measurement, start tutoring.
  - `action_dont_know(self) -> None` (line 257; public)
  - `action_skip(self) -> None` (line 260; public)
  - `action_back(self) -> None` (line 263; public)
  - `on_text_area_changed(self, event: TextArea.Changed) -> None` (line 267; public)
  - `on_button_pressed(self, event: Button.Pressed) -> None` (line 270; public)
  - `_refresh_answer_meta(self, text: str) -> None` (line 275; internal)
  - `_breadcrumb_content(self) -> Content` (line 282; internal)
  - `_breadcrumb_meta_content(self) -> Content` (line 291; internal)
  - `_card_title_content(self) -> Content` (line 298; internal)
  - `_card_pills_content(self) -> Content` (line 306; internal)
  - `_probe_content(self) -> Content` (line 314; internal)
  - `_hints_content(self) -> Content` (line 337; internal)
  - `_mastery_content(self) -> Content` (line 351; internal)
  - `_attempt_row_content(self) -> Content` (line 371; internal)
  - `_why_text_content(self) -> Content` (line 388; internal)
  - `_why_metrics_content(self) -> Content` (line 398; internal)
  - `_is_probe(self) -> bool` (line 420; internal)
  - `_primary_subject(self) -> str` (line 425; internal)
  - `_difficulty(self) -> float` (line 429; internal)
  - `_mastery_mean_sd(self) -> tuple[float, float]` (line 439; internal)
  - `_queue_position(self) -> tuple[int, int]` (line 447; internal)
  - `_attempt_number(self) -> int` (line 455; internal)

### Module constants

- `_RATING_CAPS` ([src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py), line 34)
- `_RATING_CAP_VARIANTS` ([src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py), line 35)

## Internal implementation anchors

- `_join(parts: list[Content], sep: str=' ') -> Content` ([source](../../../../../../../src/learnloop/tui/screens/practice.py), line 462)
- `_relative(iso: str, now: datetime) -> str` ([source](../../../../../../../src/learnloop/tui/screens/practice.py), line 471)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `PracticeScreen`; statically calls `PracticeScreen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `default_attempt_type`; calls `default_attempt_type`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_post_attempt_pipeline`; calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `commit_item_presentation`, `episode_contract`, `episode_hypothesis_set`, `probe_serving_block_reason`, `stop_diagnosing_and_teach`; calls `commit_item_presentation`, `episode_contract`, `episode_hypothesis_set`, `probe_serving_block_reason`, `stop_diagnosing_and_teach`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `FeedbackScreen`; calls `FeedbackScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`; calls `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e2e_tui.py](../../../../../../../tests/test_e2e_tui.py) — direct import
  - `test_tui_end_to_end_self_graded_practice`
- [tests/test_tui_practice.py](../../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_collects_answer_and_opens_feedback`
  - `test_practice_screen_dont_know_runs_shared_post_attempt_pipeline`
  - `test_practice_screen_submit_button_opens_feedback`
  - `test_practice_screen_submit_shortcut_opens_feedback`
  - `test_practice_screen_uses_item_allowed_attempt_type`
- [tests/test_tui_today.py](../../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
