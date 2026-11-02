---
title: "learnloop.tui.screens.today"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/today.py"
source_paths:
  - "src/learnloop/tui/screens/today.py"
source_commit: "2d7c4948399efdc96c3c60d7379da37bc90a9e3d"
source_commit_timestamp: "2026-10-14T20:18:37-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 422 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d7c4948399efdc96c3c60d7379da37bc90a9e3d` |
| Commit timestamp | `2026-10-14T20:18:37-04:00` |

## Public API

- `class PracticeCard(TextStatic)` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 33) — A single queue item rendered as a bordered card (one Content block).
  - `__init__(self, content: Content, index: int, **kwargs) -> None` (line 46; internal)
  - `on_click(self) -> None` (line 50; public)
- `class TodayScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 54)
  - `__init__(self, state: TuiState)` (line 72; internal)
  - `compose(self) -> ComposeResult` (line 83; public)
  - `on_mount(self) -> None` (line 100; public)
  - `on_screen_resume(self) -> None` (line 103; public)
  - `action_refresh(self) -> None` (line 113; public)
  - `action_move(self, delta: int) -> None` (line 118; public)
  - `action_open_selected(self) -> None` (line 124; public)
  - `action_quick_open(self, n: int) -> None` (line 130; public)
  - `async open_practice(self)` (line 137; public)
  - `_practice_screen(self, item)` (line 145; internal)
  - `on_practice_card_selected(self, event: PracticeCard.Selected) -> None` (line 150; public)
  - `_render_queue(self) -> None` (line 157; internal)
  - `_refresh_static_panels(self) -> None` (line 197; internal)
  - `_grouped(self) -> list[tuple[str, list[ScheduledItem]]]` (line 203; internal) — Presentation grouping over the flat priority queue (scheduler order is unchanged).
  - `_mark_focused(self) -> None` (line 230; internal)
  - `_selected_item(self) -> ScheduledItem | None` (line 234; internal)
  - `_header_content(self) -> Content` (line 240; internal)
  - `_status_content(self) -> Content` (line 249; internal)
  - `_summary_content(self) -> Content` (line 263; internal)
  - `_banner_content(self) -> Content` (line 272; internal)
  - `_why_order_content(self) -> Content` (line 287; internal)
  - `_card_content(self, item: ScheduledItem, index: int, inserted: bool) -> Content` (line 305; internal)
  - `_section_counts(self) -> tuple[int, int, int]` (line 343; internal)
  - `_followup_item(self) -> tuple[object, ScheduledItem] | None` (line 358; internal)
  - `_budget(self) -> int | None` (line 364; internal)
  - `_subject(self, practice_item) -> str` (line 369; internal)
  - `_mastery(self, learning_object_id: str) -> float` (line 373; internal)
  - `_due_offset(self, practice_item_id: str) -> str` (line 379; internal)
  - `_primary_goal_title(self) -> str` (line 385; internal)
  - `_ai_status(self) -> tuple[str, bool]` (line 391; internal)

## Internal implementation anchors

- `_is_followup(components: dict[str, float]) -> bool` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 26)
- `_clip(text: str, limit: int) -> str` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 399)
- `_relative(iso: str, now: datetime) -> str` ([source](../../../../../../../src/learnloop/tui/screens/today.py), line 404)

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
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

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

- [tests/test_daily_loop_start_minutes.py](../../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_tui_esc_keeps_the_list_and_an_ungraded_next_returns_to_it`
  - `test_tui_next_opens_the_head_of_the_live_queue`
  - `test_tui_start_asks_for_minutes_only_and_starts_on_the_remembered_minutes`
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
