---
title: "learnloop.tui.theme"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/theme.py"
source_paths:
  - "src/learnloop/tui/theme.py"
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
  - "learnloop.tui.theme module"
  - "src/learnloop/tui/theme.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui"
---

# `learnloop.tui.theme`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module is a source-level boundary within [[Reference/Modules/learnloop/tui/_package|learnloop.tui]]; it currently exposes no top-level definitions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/theme.py](../../../../../../src/learnloop/tui/theme.py) |
| Source lines | 28 |
| Owning package | [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

### Module constants

- `LEARNLOOP_VARIABLES` ([src/learnloop/tui/theme.py](../../../../../../src/learnloop/tui/theme.py), line 8)
- `LEARNLOOP_THEME` ([src/learnloop/tui/theme.py](../../../../../../src/learnloop/tui/theme.py), line 14)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] — imports `LEARNLOOP_THEME`, `LEARNLOOP_VARIABLES`

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

Static participation evidence comes from [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_e2e_tui.py](../../../../../../tests/test_e2e_tui.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_app.py](../../../../../../tests/test_tui_app.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_theme.py](../../../../../../tests/test_tui_theme.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — imports consumer [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/theme.py](../../../../../../src/learnloop/tui/theme.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
