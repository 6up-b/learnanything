---
title: "learnloop.adaptive_difficulty.lessons"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/lessons.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/lessons.py"
source_commit: "04d1b40e19aa935b9233c007868ca3c58d217e99"
source_commit_timestamp: "2026-11-06T04:58:47-05:00"
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
  - "learnloop.adaptive_difficulty.lessons module"
  - "src/learnloop/adaptive_difficulty/lessons.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.lessons`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.lessons` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Teacher TE3a: a closed lesson's nodes as AD's learning opportunities (spec_teacher_v1 rev 5 §14.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/lessons.py](../../../../../../src/learnloop/adaptive_difficulty/lessons.py) |
| Source lines | 86 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `04d1b40e19aa935b9233c007868ca3c58d217e99` |
| Commit timestamp | `2026-11-06T04:58:47-05:00` |

## Public API

- `node_source_id(lesson_id: str, node_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/lessons.py), line 38)
- `lesson_events(connection: Any, reading_map: ReadingMap, upper: str, *, view: Any, vault: Any) -> list[ListedEvent]` ([source](../../../../../../src/learnloop/adaptive_difficulty/lessons.py), line 56) — Every closed lesson's opportunities written no later than ``upper``, as ``view`` sees them (none while the view is unavailable: fail closed).

### Module constants

- `SOURCE_TABLE` ([src/learnloop/adaptive_difficulty/lessons.py](../../../../../../src/learnloop/adaptive_difficulty/lessons.py), line 35)

### Explicit exports

`__all__` declares:

- `SOURCE_TABLE`
- `lesson_events`
- `node_source_id`

## Internal implementation anchors

- `_nodes(receipt: Any) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/lessons.py), line 42)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `lesson_events`; statically calls `lesson_events`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`
- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `ListedEvent`, `ReadingMap`, `source_stamp`; calls `ListedEvent`, `source_stamp`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad1_reading_opportunities.py](../../../../../../tests/test_ad1_reading_opportunities.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]
- [tests/test_ro2_ad_document_ir.py](../../../../../../tests/test_ro2_ad_document_ir.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]]

## Modification guidance

- Make changes here when the responsibility remains lessons within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/lessons.py](../../../../../../src/learnloop/adaptive_difficulty/lessons.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
