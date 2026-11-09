---
title: "learnloop.db.stores.field"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/field.py"
source_paths:
  - "src/learnloop/db/stores/field.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.field module"
  - "src/learnloop/db/stores/field.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.field`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.field` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Narrow SQL write ownership for F1 caches; never writes learner evidence.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/field.py](../../../../../../../src/learnloop/db/stores/field.py) |
| Source lines | 31 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `replace_facet_outcomes(connection: sqlite3.Connection, rows: Iterable[Sequence]) -> None` ([source](../../../../../../../src/learnloop/db/stores/field.py), line 12)
- `insert_question_classification(connection: sqlite3.Connection, values: Sequence) -> None` ([source](../../../../../../../src/learnloop/db/stores/field.py), line 24)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `insert_question_classification`; statically calls `insert_question_classification`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `replace_facet_outcomes`; statically calls `replace_facet_outcomes`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_field_signal_production_paths.py](../../../../../../../tests/test_field_signal_production_paths.py) — imports consumer [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]]
- [tests/test_interaction_signals.py](../../../../../../../tests/test_interaction_signals.py) — imports consumer [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]]
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — imports consumer [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]]
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_ad_guard_offer_receipts.py](../../../../../../../tests/test_ad_guard_offer_receipts.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_ad_guard_reachable_reads.py](../../../../../../../tests/test_ad_guard_reachable_reads.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_answer_signal_arms.py](../../../../../../../tests/test_answer_signal_arms.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_daily_plan_composition.py](../../../../../../../tests/test_daily_plan_composition.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_daily_plan_owner_decisions.py](../../../../../../../tests/test_daily_plan_owner_decisions.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_facet_outcome_view.py](../../../../../../../tests/test_facet_outcome_view.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]
- [tests/test_family_memory_projection.py](../../../../../../../tests/test_family_memory_projection.py) — imports consumer [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/field.py](../../../../../../../src/learnloop/db/stores/field.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
