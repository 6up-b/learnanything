---
title: "learnloop.content.synthesis.append_budget"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/append_budget.py"
source_paths:
  - "src/learnloop/content/synthesis/append_budget.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.append_budget module"
  - "src/learnloop/content/synthesis/append_budget.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.append_budget`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.append_budget` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Size and group append requests using the reconciliation schema and configured ceilings.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/append_budget.py](../../../../../../../src/learnloop/content/synthesis/append_budget.py) |
| Source lines | 35 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `append_input_tokens(context: AppendReconciliationContext) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/append_budget.py), line 18)
- `append_groups(units: list[T], budgets, tokens: Callable[[list[T]], int]) -> list[list[T]]` ([source](../../../../../../../src/learnloop/content/synthesis/append_budget.py), line 22)

### Module constants

- `T` ([src/learnloop/content/synthesis/append_budget.py](../../../../../../../src/learnloop/content/synthesis/append_budget.py), line 10)

## Internal implementation anchors

- `_schema_chars() -> int` ([source](../../../../../../../src/learnloop/content/synthesis/append_budget.py), line 14)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `append_groups`, `append_input_tokens`; statically calls `append_groups`, `append_input_tokens`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `append_groups`, `append_input_tokens`; statically calls `append_groups`, `append_input_tokens`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `AppendReconciliation`, `AppendReconciliationContext`, `append_reconciliation_prompt`; calls `append_reconciliation_prompt`

### Platform and third-party dependencies

- Standard library: `collections`, `functools`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_append_split_passes.py](../../../../../../../tests/test_append_split_passes.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]]
- [tests/test_first_questions_arrive.py](../../../../../../../tests/test_first_questions_arrive.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]]
- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]]
- [tests/facet_identity_ingest_helpers.py](../../../../../../../tests/facet_identity_ingest_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_cli_append_units.py](../../../../../../../tests/test_cli_append_units.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_collection_append_units.py](../../../../../../../tests/test_collection_append_units.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]

## Modification guidance

- Change append budget policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/append_budget.py](../../../../../../../src/learnloop/content/synthesis/append_budget.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
