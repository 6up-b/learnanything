---
title: "learnloop.tui.screens.start"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/start.py"
source_paths:
  - "src/learnloop/tui/screens/start.py"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps start behavior inside its owning package, [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]]. Its public surface centers on `Torus`, `Slider`, `MinutesPicker`, `StartScreen`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py) |
| Source lines | 405 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Torus(Static)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 28) — Rotating shaded ASCII torus (Andy Sloane's donut.c), tinted with theme tokens.
  - `__init__(self, **kwargs) -> None` (line 33; internal)
  - `on_mount(self) -> None` (line 38; public)
  - `_tick(self) -> None` (line 42; internal)
  - `_frame(self) -> Content` (line 49; internal)
- `class Slider(Static)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 111) — Focusable block-fill slider in [0, 1]; ←/→ adjust by 0.1, click to set.
  - `__init__(self, label: str, value: float=0.5, **kwargs) -> None` (line 127; internal)
  - `on_mount(self) -> None` (line 132; public)
  - `action_step(self, delta: float) -> None` (line 135; public)
  - `on_click(self, event) -> None` (line 138; public)
  - `watch_value(self, _value: float) -> None` (line 144; public)
  - `_render(self) -> Content` (line 149; internal)
- `class MinutesPicker(Static)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 157) — Focusable preset chips for available session minutes; ←/→ cycle.
  - `__init__(self, minutes: int=30, **kwargs) -> None` (line 171; internal)
  - `on_mount(self) -> None` (line 176; public)
  - `minutes(self) -> int` (line 180; public)
  - `action_step(self, delta: int) -> None` (line 183; public)
  - `watch_index(self, _index: int) -> None` (line 186; public)
  - `_render(self) -> Content` (line 191; internal)
- `class StartScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/start.py), line 204) — Session warm-up: readiness inputs + queue preview, then begin.
  - `__init__(self, state: TuiState)` (line 216; internal)
  - `compose(self) -> ComposeResult` (line 220; public)
  - `on_mount(self) -> None` (line 250; public)
  - `on_slider_changed(self, _event: Slider.Changed) -> None` (line 254; public)
  - `on_minutes_picker_changed(self, _event: MinutesPicker.Changed) -> None` (line 257; public)
  - `_refresh_mode(self) -> None` (line 260; internal)
  - `_energy(self) -> float` (line 263; internal)
  - `_sleep(self) -> float` (line 266; internal)
  - `_minutes(self) -> int` (line 269; internal)
  - `_energy_bucket(self) -> str` (line 272; internal)
  - `_session(self) -> SchedulerSession` (line 276; internal)
  - `async begin_session(self)` (line 280; public)
  - `action_begin(self) -> None` (line 288; public)
  - `action_postpone(self) -> None` (line 291; public)
  - `on_button_pressed(self, event: Button.Pressed) -> None` (line 294; public)
  - `_left_head(self) -> Content` (line 301; internal)
  - `_scope_text(self) -> Content` (line 308; internal)
  - `_intro_text(self) -> Content` (line 318; internal)
  - `_mode_text(self) -> Content` (line 324; internal)
  - `_queue_preview(self) -> Content` (line 341; internal)
  - `_recap_text(self) -> Content` (line 355; internal)
  - `_queue_counts(self) -> tuple[int, int, int, int]` (line 368; internal)
  - `_overdue_count(self) -> int` (line 385; internal)
  - `_primary_goal_title(self) -> str` (line 401; internal)

### Module constants

- `_RAMP` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 20)
- `_RAMP_TOKENS` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 22)
- `_TORUS_W` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 24)
- `_TORUS_H` ([src/learnloop/tui/screens/start.py](../../../../../../../src/learnloop/tui/screens/start.py), line 25)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `StartScreen`; statically calls `StartScreen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`; calls `SchedulerSession`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `TodayScreen`; calls `TodayScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`, `block_bar`; calls `KeyBar`, `TextStatic`, `block_bar`

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
