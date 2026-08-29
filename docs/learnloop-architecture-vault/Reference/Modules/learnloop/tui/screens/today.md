---
title: "learnloop.tui.screens.today"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/today.py"
source_paths:
  - "src/learnloop/tui/screens/today.py"
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
  - "learnloop.tui.screens.today module"
  - "src/learnloop/tui/screens/today.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui-screens"
---

# `learnloop.tui.screens.today`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps today behavior inside its owning package, [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]]. Its public surface centers on `PracticeCard`, `TodayScreen`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/today.py](../../../../../../../src/learnloop/tui/screens/today.py) |
| Source lines | 412 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PracticeCard(TextStatic)` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 32) — A single queue item rendered as a bordered card (one Content block).
  - `__init__(self, content: Content, index: int, **kwargs) -> None` (line 45; internal)
  - `on_click(self) -> None` (line 49; public)
- `class TodayScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 53)
  - `__init__(self, state: TuiState)` (line 71; internal)
  - `compose(self) -> ComposeResult` (line 79; public)
  - `on_mount(self) -> None` (line 96; public)
  - `on_screen_resume(self) -> None` (line 99; public)
  - `action_refresh(self) -> None` (line 105; public)
  - `action_move(self, delta: int) -> None` (line 110; public)
  - `action_open_selected(self) -> None` (line 116; public)
  - `action_quick_open(self, n: int) -> None` (line 122; public)
  - `async open_practice(self)` (line 129; public)
  - `_practice_screen(self, item)` (line 137; internal)
  - `on_practice_card_selected(self, event: PracticeCard.Selected) -> None` (line 142; public)
  - `_render_queue(self) -> None` (line 149; internal)
  - `_refresh_static_panels(self) -> None` (line 189; internal)
  - `_grouped(self) -> list[tuple[str, list[ScheduledItem]]]` (line 195; internal) — Presentation grouping over the flat priority queue (scheduler order is unchanged).
  - `_mark_focused(self) -> None` (line 222; internal)
  - `_selected_item(self) -> ScheduledItem | None` (line 226; internal)
  - `_header_content(self) -> Content` (line 232; internal)
  - `_status_content(self) -> Content` (line 241; internal)
  - `_summary_content(self) -> Content` (line 255; internal)
  - `_banner_content(self) -> Content` (line 262; internal)
  - `_why_order_content(self) -> Content` (line 277; internal)
  - `_card_content(self, item: ScheduledItem, index: int, inserted: bool) -> Content` (line 295; internal)
  - `_section_counts(self) -> tuple[int, int, int]` (line 331; internal)
  - `_followup_item(self) -> tuple[object, ScheduledItem] | None` (line 346; internal)
  - `_budget(self) -> int` (line 352; internal)
  - `_subject(self, practice_item) -> str` (line 359; internal)
  - `_mastery(self, learning_object_id: str) -> float` (line 363; internal)
  - `_due_offset(self, practice_item_id: str) -> str` (line 369; internal)
  - `_primary_goal_title(self) -> str` (line 375; internal)
  - `_ai_status(self) -> tuple[str, bool]` (line 381; internal)

## Internal implementation anchors

- `_is_followup(components: dict[str, float]) -> bool` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 25)
- `_clip(text: str, limit: int) -> str` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 389)
- `_relative(iso: str, now: datetime) -> str` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 394)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `TodayScreen`
- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `TodayScreen`; statically calls `TodayScreen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `PracticeScreen`; calls `PracticeScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`; calls `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]], [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e2e_tui.py](../../../../../../../tests/test_e2e_tui.py) — direct import
  - `test_tui_end_to_end_self_graded_practice`
- [tests/test_tui_app.py](../../../../../../../tests/test_tui_app.py) — direct import
  - `test_tui_app_launches_start_screen_and_syncs_state`
  - `test_tui_today_screen_renders_queue_details_and_refreshes`
- [tests/test_tui_today.py](../../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/screens/today.py](../../../../../../../src/learnloop/tui/screens/today.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
