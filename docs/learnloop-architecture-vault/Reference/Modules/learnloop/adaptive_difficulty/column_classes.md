---
title: "learnloop.adaptive_difficulty.column_classes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/column_classes.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/column_classes.py"
source_commit: "f44a2201c4ba1360ab15ba2f003266c04b175356"
source_commit_timestamp: "2026-11-04T21:18:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.column_classes module"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.column_classes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.column_classes` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Every column of every table an AD operation can read, classified (the AD23 redesign round 5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/column_classes.py](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py) |
| Source lines | 686 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f44a2201c4ba1360ab15ba2f003266c04b175356` |
| Commit timestamp | `2026-11-04T21:18:14-05:00` |

## Public API

- `column_class(table: str, column: str | None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py), line 677) — A column's class.

### Module constants

- `METADATA` ([src/learnloop/adaptive_difficulty/column_classes.py](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py), line 26)
- `CONTENT` ([src/learnloop/adaptive_difficulty/column_classes.py](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py), line 27)
- `_CLASSES` ([src/learnloop/adaptive_difficulty/column_classes.py](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py), line 30)
- `CLASSES` ([src/learnloop/adaptive_difficulty/column_classes.py](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py), line 670)

### Explicit exports

`__all__` declares:

- `CLASSES`
- `CONTENT`
- `METADATA`
- `column_class`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `module`; statically calls `column_class`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `types`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_protected_tables.py](../../../../../../tests/test_ad_protected_tables.py) — direct import
  - `test_every_column_of_every_readable_table_is_metadata_or_content`
- [tests/test_ro2_history_migration.py](../../../../../../tests/test_ro2_history_migration.py) — direct import
  - `test_245_is_the_head_and_its_table_a_receipt_ad_classifies`
- [tests/test_rw5c_migration.py](../../../../../../tests/test_rw5c_migration.py) — direct import
  - `test_238_is_applied_and_the_table_is_classified`

## Modification guidance

- Make changes here when the responsibility remains column classes within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/column_classes.py](../../../../../../src/learnloop/adaptive_difficulty/column_classes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
