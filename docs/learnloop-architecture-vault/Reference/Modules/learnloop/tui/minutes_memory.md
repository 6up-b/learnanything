---
title: "learnloop.tui.minutes_memory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/minutes_memory.py"
source_paths:
  - "src/learnloop/tui/minutes_memory.py"
source_commit: "b54f6c9b4b49baebcb131dd48680ac01e257f9d2"
source_commit_timestamp: "2026-10-12T22:35:10-04:00"
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
  - "learnloop.tui.minutes_memory module"
  - "src/learnloop/tui/minutes_memory.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui"
---

# `learnloop.tui.minutes_memory`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tui.minutes_memory` exists within [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] to own the behavior summarized by its module contract: The TUI's remembered session minutes (daily-loop DL0, ``spec_daily_loop_v1.md`` §6.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/minutes_memory.py](../../../../../../src/learnloop/tui/minutes_memory.py) |
| Source lines | 87 |
| Owning package | [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b54f6c9b4b49baebcb131dd48680ac01e257f9d2` |
| Commit timestamp | `2026-10-12T22:35:10-04:00` |

## Public API

- `chosen_minutes_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/tui/minutes_memory.py), line 32) — Where the TUI keeps the minutes it last began with for ``vault_root``.
- `load_chosen_minutes(vault_root: Path) -> ChosenMinutes | None` ([source](../../../../../../src/learnloop/tui/minutes_memory.py), line 40) — The minutes the TUI last began with on this vault, or None.
- `save_chosen_minutes(vault_root: Path, minutes: int, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/tui/minutes_memory.py), line 63) — Remember a TUI Begin's minutes.

### Module constants

- `_SCHEMA_VERSION` ([src/learnloop/tui/minutes_memory.py](../../../../../../src/learnloop/tui/minutes_memory.py), line 29)

### Explicit exports

`__all__` declares:

- `chosen_minutes_path`
- `load_chosen_minutes`
- `save_chosen_minutes`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `load_chosen_minutes`, `save_chosen_minutes`; statically calls `load_chosen_minutes`, `save_chosen_minutes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `global_settings_path`; calls `global_settings_path`
- [[Reference/Modules/learnloop/scheduling/session_minutes|learnloop.scheduling.session_minutes]] — imports `ChosenMinutes`; calls `ChosenMinutes`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `os`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_the_tui_minutes_store_never_breaks_start`
  - `test_tui_minutes_are_the_newer_of_its_own_begin_and_the_last_session`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/minutes_memory.py](../../../../../../src/learnloop/tui/minutes_memory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
