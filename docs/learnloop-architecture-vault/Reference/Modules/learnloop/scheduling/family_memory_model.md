---
title: "learnloop.scheduling.family_memory_model"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/family_memory_model.py"
source_paths:
  - "src/learnloop/scheduling/family_memory_model.py"
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
  - "learnloop.scheduling.family_memory_model module"
  - "src/learnloop/scheduling/family_memory_model.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.family_memory_model`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.family_memory_model` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Pure shadow FSRS fold shared by the PF-a projection and the offline memory arms.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/family_memory_model.py](../../../../../../src/learnloop/scheduling/family_memory_model.py) |
| Source lines | 112 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `weights_digest(weights: tuple[float, ...]) -> str` ([source](../../../../../../src/learnloop/scheduling/family_memory_model.py), line 23)
- `class MemoryHistory` ([source](../../../../../../src/learnloop/scheduling/family_memory_model.py), line 37)
- `class FamilyMemory` ([source](../../../../../../src/learnloop/scheduling/family_memory_model.py), line 43) — FSRS state per item, family or LO key; a point predictor, never active.
  - `__init__(self, key: str, weights: tuple[float, ...], *, weight_label: str='defaults', distance_discount: bool=False)` (line 50; internal)
  - `key_for(self, features) -> str` (line 62; public)
  - `predict(self, features) -> float` (line 69; public)
  - `scores(self, row) -> bool` (line 79; public) — Memory arms are scored on graded cold retrievals only, never warm rows.
  - `observe(self, row) -> None` (line 83; public)
  - `rebuild(self, rows) -> None` (line 102; public)
  - `snapshot_bytes(self) -> bytes` (line 107; public)

### Module constants

- `MEMORY_KEYS` ([src/learnloop/scheduling/family_memory_model.py](../../../../../../src/learnloop/scheduling/family_memory_model.py), line 20)

## Internal implementation anchors

- `_instant(value: str | datetime) -> datetime` ([source](../../../../../../src/learnloop/scheduling/family_memory_model.py), line 27)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `weights_digest`; statically calls `weights_digest`
- [[Reference/Modules/learnloop/field/memory|learnloop.field.memory]] — imports `FamilyMemory`, `MEMORY_KEYS`; statically calls `FamilyMemory`
- [[Reference/Modules/learnloop/substrate/family_memory|learnloop.substrate.family_memory]] — imports `FamilyMemory`, `weights_digest`; statically calls `FamilyMemory`, `weights_digest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `MemoryState`, `Rating`, `apply_review`, `retrievability`; calls `MemoryState`, `Rating`, `apply_review`, `retrievability`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]], [[Reference/Modules/learnloop/field/memory|learnloop.field.memory]], [[Reference/Modules/learnloop/substrate/family_memory|learnloop.substrate.family_memory]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_family_evaluation.py](../../../../../../tests/test_family_evaluation.py) — direct import
  - `test_distance_arm_discounts_only_real_positive_credit`
  - `test_memory_coldness_and_transfer_gate`
  - `test_prequential_predict_all_before_observe_including_memory`
  - `test_shared_key_weights_and_elapsed_are_consistent`
  - `test_unfamilied_falls_back_to_item_and_transfer_never_trains`

## Modification guidance

- Change family memory model policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/family_memory_model.py](../../../../../../src/learnloop/scheduling/family_memory_model.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
