---
title: "learnloop.field.memory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/memory.py"
source_paths:
  - "src/learnloop/field/memory.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.memory module"
  - "src/learnloop/field/memory.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.memory`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.memory` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: PF-a memory arms, registered in the learner-field arm registry.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/memory.py](../../../../../../src/learnloop/field/memory.py) |
| Source lines | 44 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `memory_arm_name(key: str, weight_label: str, distance_discount: bool) -> str` ([source](../../../../../../src/learnloop/field/memory.py), line 20)

### Module constants

- `WEIGHT_LABELS` ([src/learnloop/field/memory.py](../../../../../../src/learnloop/field/memory.py), line 17)

## Internal implementation anchors

- `_factory(key: str, weight_label: str, distance_discount: bool)` ([source](../../../../../../src/learnloop/field/memory.py), line 24)
- `_register() -> None` ([source](../../../../../../src/learnloop/field/memory.py), line 31)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `register_predictor`, `registered_predictors`; calls `register_predictor`, `registered_predictors`
- [[Reference/Modules/learnloop/scheduling/family_memory_model|learnloop.scheduling.family_memory_model]] — imports `FamilyMemory`, `MEMORY_KEYS`; calls `FamilyMemory`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_family_evaluation.py](../../../../../../tests/test_family_evaluation.py) — direct import
  - `test_family_arms_are_registered_in_the_field_registry`
- [tests/test_lo_general.py](../../../../../../tests/test_lo_general.py) — direct import
- [tests/test_predictor_interface.py](../../../../../../tests/test_predictor_interface.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains memory within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/memory.py](../../../../../../src/learnloop/field/memory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
