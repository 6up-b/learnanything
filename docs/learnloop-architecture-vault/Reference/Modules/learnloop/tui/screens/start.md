---
title: "learnloop.tui.screens.start"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/start.py"
source_paths:
  - "src/learnloop/tui/screens/start.py"
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
  - "learnloop.tui.screens.start module"
  - "src/learnloop/tui/screens/start.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui-screens"
---

# `learnloop.tui.screens.start`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps start behavior inside its owning package, [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]]. Its public surface centers on `Torus`, `MinutesPicker`, `StartScreen`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py) |
| Source lines | 386 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class Torus(Static)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 30) — Rotating shaded ASCII torus (Andy Sloane's donut.c), tinted with theme tokens.
  - `__init__(self, **kwargs) -> None` (line 35; internal)
  - `on_mount(self) -> None` (line 40; public)
  - `_tick(self) -> None` (line 44; internal)
  - `_frame(self) -> Content` (line 51; internal)
- `class MinutesPicker(Static)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 113) — Focusable one-tap minute chips; ←/→ cycle (daily-loop §6.6).
  - `__init__(self, minutes: int, **kwargs) -> None` (line 131; internal)
  - `on_mount(self) -> None` (line 136; public)
  - `choices(self) -> tuple[int, ...]` (line 140; public)
  - `minutes(self) -> int` (line 144; public)
  - `action_step(self, delta: int) -> None` (line 147; public)
  - `on_click(self, event) -> None` (line 150; public)
  - `watch_index(self, _index: int) -> None` (line 161; public)
  - `_render(self) -> Content` (line 166; internal)
- `class StartScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 179) — Session warm-up: minutes only, a queue preview, then begin.
  - `__init__(self, state: TuiState)` (line 194; internal)
  - `compose(self) -> ComposeResult` (line 204; public)
  - `on_mount(self) -> None` (line 232; public)
  - `on_minutes_picker_changed(self, _event: MinutesPicker.Changed) -> None` (line 236; public)
  - `_refresh_mode(self) -> None` (line 239; internal)
  - `_minutes(self) -> int` (line 242; internal)
  - `_session(self) -> SchedulerSession` (line 247; internal)
  - `async begin_session(self)` (line 252; public)
  - `action_begin(self) -> None` (line 268; public)
  - `on_button_pressed(self, event: Button.Pressed) -> None` (line 271; public)
  - `_left_head(self) -> Content` (line 276; internal)
  - `_scope_text(self) -> Content` (line 283; internal)
  - `_intro_text(self) -> Content` (line 293; internal)
  - `_mode_text(self) -> Content` (line 306; internal)
  - `_queue_preview(self) -> Content` (line 322; internal)
  - `_recap_text(self) -> Content` (line 336; internal)
  - `_queue_counts(self) -> tuple[int, int, int, int]` (line 349; internal)
  - `_overdue_count(self) -> int` (line 366; internal)
  - `_primary_goal_title(self) -> str` (line 382; internal)

### Module constants

- `_RAMP` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 22)
- `_RAMP_TOKENS` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 24)
- `_TORUS_W` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 26)
- `_TORUS_H` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 27)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `StartScreen`; statically calls `StartScreen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`; calls `SchedulerSession`
- [[Reference/Modules/learnloop/scheduling/session_minutes|learnloop.scheduling.session_minutes]] — imports `minute_choices`, `remembered_session_minutes`; calls `minute_choices`, `remembered_session_minutes`
- [[Reference/Modules/learnloop/tui/minutes_memory|learnloop.tui.minutes_memory]] — imports `load_chosen_minutes`, `save_chosen_minutes`; calls `load_chosen_minutes`, `save_chosen_minutes`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `TodayScreen`; calls `TodayScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`; calls `KeyBar`, `TextStatic`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `math`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../../tests/helpers.py) — direct import
- [tests/test_daily_loop_start_minutes.py](../../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_tui_start_asks_for_minutes_only_and_starts_on_the_remembered_minutes`
  - `test_tui_start_lays_the_minute_chips_out_on_screen`
  - `test_tui_start_uses_25_minutes_on_a_fresh_vault_and_keeps_an_old_budget`
- [tests/test_daily_loop_start_postpone.py](../../../../../../../tests/test_daily_loop_start_postpone.py) — direct import
  - `test_tui_start_screen_offers_no_postpone_it_cannot_honour`
- [tests/test_tui_app.py](../../../../../../../tests/test_tui_app.py) — direct import
  - `test_tui_app_launches_start_screen_and_syncs_state`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
