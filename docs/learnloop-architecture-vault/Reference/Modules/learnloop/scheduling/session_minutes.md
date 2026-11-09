---
title: "learnloop.scheduling.session_minutes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/session_minutes.py"
source_paths:
  - "src/learnloop/scheduling/session_minutes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.session_minutes module"
  - "src/learnloop/scheduling/session_minutes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.session_minutes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.session_minutes` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Remembered session minutes (daily-loop DL0, ``spec_daily_loop_v1.md`` §6.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/session_minutes.py](../../../../../../src/learnloop/scheduling/session_minutes.py) |
| Source lines | 91 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RememberedMinutes` ([source](../../../../../../src/learnloop/scheduling/session_minutes.py), line 34)
- `class ChosenMinutes` ([source](../../../../../../src/learnloop/scheduling/session_minutes.py), line 40) — Minutes a client began with without recording a session (the TUI's Begin).
- `remembered_session_minutes(repository: _SessionMinutesReader, *, chosen: ChosenMinutes | None=None) -> RememberedMinutes` ([source](../../../../../../src/learnloop/scheduling/session_minutes.py), line 48) — The minutes Start offers by default.
- `minute_choices(remembered: int) -> tuple[int, ...]` ([source](../../../../../../src/learnloop/scheduling/session_minutes.py), line 74) — The chips to show: the presets plus the remembered value when it isn't one.

### Module constants

- `MINUTE_PRESETS` ([src/learnloop/scheduling/session_minutes.py](../../../../../../src/learnloop/scheduling/session_minutes.py), line 21)
- `FIRST_RUN_MINUTES` ([src/learnloop/scheduling/session_minutes.py](../../../../../../src/learnloop/scheduling/session_minutes.py), line 24)

### Explicit exports

`__all__` declares:

- `FIRST_RUN_MINUTES`
- `MINUTE_PRESETS`
- `ChosenMinutes`
- `RememberedMinutes`
- `minute_choices`
- `remembered_session_minutes`

## Internal implementation anchors

- `class _SessionMinutesReader(Protocol)` ([source](../../../../../../src/learnloop/scheduling/session_minutes.py), line 29)
- `_not_before(chosen_at: str, started_at: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/session_minutes.py), line 68)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/minutes_memory|learnloop.tui.minutes_memory]] — imports `ChosenMinutes`; statically calls `ChosenMinutes`
- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `minute_choices`, `remembered_session_minutes`; statically calls `minute_choices`, `remembered_session_minutes`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `MINUTE_PRESETS`, `minute_choices`, `remembered_session_minutes`; statically calls `minute_choices`, `remembered_session_minutes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/minutes_memory|learnloop.tui.minutes_memory]], [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_remembered_minutes_follow_session_start_order`
  - `test_start_summary_remembers_the_last_sessions_minutes`
  - `test_the_tui_minutes_store_never_breaks_start`
  - `test_tui_minutes_are_the_newer_of_its_own_begin_and_the_last_session`

## Modification guidance

- Change session minutes policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/session_minutes.py](../../../../../../src/learnloop/scheduling/session_minutes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
