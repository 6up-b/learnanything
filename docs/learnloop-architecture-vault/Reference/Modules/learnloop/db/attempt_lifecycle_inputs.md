---
title: "learnloop.db.attempt_lifecycle_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/attempt_lifecycle_inputs.py"
source_paths:
  - "src/learnloop/db/attempt_lifecycle_inputs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.attempt_lifecycle_inputs module"
  - "src/learnloop/db/attempt_lifecycle_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.attempt_lifecycle_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.attempt_lifecycle_inputs` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: The lifecycle inputs an attempt's grade application read (mvp-0.66; migration 263, ``attempt_lifecycle_inputs``).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/attempt_lifecycle_inputs.py](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py) |
| Source lines | 58 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class LifecycleInputs` ([source](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py), line 27) — One attempt's required facet set, in its canonical (sorted) order, and where it came from.
  - `of(cls, learning_object_id: str, facets: Iterable[str], *, basis: str) -> LifecycleInputs` (line 36; public)
  - `required_facets_json(self) -> str` (line 39; public)
  - `from_row(cls, row) -> LifecycleInputs` (line 43; public)

### Module constants

- `LIFECYCLE_INPUTS_TABLE` ([src/learnloop/db/attempt_lifecycle_inputs.py](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py), line 16)
- `BASIS_CAPTURED` ([src/learnloop/db/attempt_lifecycle_inputs.py](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py), line 18)
- `BASIS_LEGACY_RECONSTRUCTED` ([src/learnloop/db/attempt_lifecycle_inputs.py](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py), line 21)
- `REQUIRED_FACETS_POLICY` ([src/learnloop/db/attempt_lifecycle_inputs.py](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py), line 23)

### Explicit exports

`__all__` declares:

- `BASIS_CAPTURED`
- `BASIS_LEGACY_RECONSTRUCTED`
- `LIFECYCLE_INPUTS_TABLE`
- `LifecycleInputs`
- `REQUIRED_FACETS_POLICY`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `LifecycleInputs`
- [[Reference/Modules/learnloop/attempts/lifecycle_inputs|learnloop.attempts.lifecycle_inputs]] — imports `BASIS_CAPTURED`, `BASIS_LEGACY_RECONSTRUCTED`, `LifecycleInputs`
- [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] — imports `LIFECYCLE_INPUTS_TABLE`, `LifecycleInputs`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/lifecycle_inputs|learnloop.attempts.lifecycle_inputs]], [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/assumed_known_helpers.py](../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_cold_outcomes_helpers.py](../../../../../../tests/causal_cold_outcomes_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_factor_deferral_helpers.py](../../../../../../tests/causal_factor_deferral_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/certification_cold_probe_helpers.py](../../../../../../tests/certification_cold_probe_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/cold_retry_reschedule_helpers.py](../../../../../../tests/cold_retry_reschedule_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_split_helpers.py](../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_augmentation_helpers.py](../../../../../../tests/diagnostic_augmentation_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../tests/diagnostic_probe_single_use_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/attempt_lifecycle_inputs.py](../../../../../../src/learnloop/db/attempt_lifecycle_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
