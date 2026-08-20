---
title: "learnloop.tui.widgets"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/widgets.py"
source_paths:
  - "src/learnloop/tui/widgets.py"
source_commit: "4a28c9635f24945d78366fa26212db7488d82545"
source_commit_timestamp: "2026-05-28T11:36:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tui"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.tui.widgets module"
  - "src/learnloop/tui/widgets.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui"
---

# `learnloop.tui.widgets`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps widgets behavior inside its owning package, [[Reference/Modules/learnloop/tui/_package|learnloop.tui]]. Its public surface centers on `TextStatic`, `mode_pill_color`, `pill`, `block_bar`, `mastery_token`, `KeyBar`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/widgets.py](../../../../../../src/learnloop/tui/widgets.py) |
| Source lines | 115 |
| Owning package | [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Public API

- `class TextStatic(Static)` ([source](../../../../../../src/learnloop/tui/widgets.py), line 7) — A `Static` that exposes the displayed text via `.renderable`.
  - `__init__(self, text: str | Content='', **kwargs) -> None` (line 17; internal)
  - `update(self, content: str | Content='', *, layout: bool=True) -> None` (line 21; public)
  - `renderable(self) -> str | Content` (line 26; public)
- `mode_pill_color(mode: str) -> str` ([source](../../../../../../src/learnloop/tui/widgets.py), line 61) — Map a practice mode to a pill variant name.
- `pill(text: str, variant: str='secondary') -> Content` ([source](../../../../../../src/learnloop/tui/widgets.py), line 66) — A half-block pill (toad `pill.py` style) rendered via the Content API.
- `block_bar(value: float, width: int=8, token: str='$primary') -> Content` ([source](../../../../../../src/learnloop/tui/widgets.py), line 77) — Unicode block bar (▓ filled / ░ empty); fill color is a theme token.
- `mastery_token(value: float) -> str` ([source](../../../../../../src/learnloop/tui/widgets.py), line 87) — Theme token for a mastery/quality value in [0, 1].
- `class KeyBar(Static)` ([source](../../../../../../src/learnloop/tui/widgets.py), line 92) — Footer hot-key bar (prototype-faithful row), rendered via Content.
  - `__init__(self, keys: list[tuple[str, str]], **kwargs) -> None` (line 99; internal)
  - `set_keys(self, keys: list[tuple[str, str]]) -> None` (line 103; public)
  - `_render(self) -> Content` (line 107; internal)

### Module constants

- `_PILL_TOKENS` ([src/learnloop/tui/widgets.py](../../../../../../src/learnloop/tui/widgets.py), line 39)
- `_MODE_PILL_VARIANT` ([src/learnloop/tui/widgets.py](../../../../../../src/learnloop/tui/widgets.py), line 51)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `TextStatic`; statically calls `TextStatic`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mode_pill_color`, `pill`; statically calls `KeyBar`, `TextStatic`, `block_bar`, `mode_pill_color`, `pill`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`; statically calls `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`
- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `KeyBar`, `TextStatic`, `block_bar`; statically calls `KeyBar`, `TextStatic`, `block_bar`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`; statically calls `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]], [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]], [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]], [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]], [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_collects_answer_and_opens_feedback`
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/widgets.py](../../../../../../src/learnloop/tui/widgets.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
