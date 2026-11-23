---
title: "learnloop.db.mastery_seed_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/mastery_seed_inputs.py"
source_paths:
  - "src/learnloop/db/mastery_seed_inputs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.mastery_seed_inputs module"
  - "src/learnloop/db/mastery_seed_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.mastery_seed_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.mastery_seed_inputs` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: The claims a learning object's mastery was first seeded from (mvp-0.67; migration 265, ``mastery_seed_inputs``).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py) |
| Source lines | 99 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class MasterySeedInputs` ([source](../../../../../../src/learnloop/db/mastery_seed_inputs.py), line 33) — Every claim one learning object's first mastery seed considered, the claim that won, and where they came from.
  - `of(cls, learning_object_id: str, considered: Iterable[Mapping[str, Any]], in_force_ids: Iterable[str], selected_claim_id: str | None, *, basis: str, materialized_at: str | None) -> MasterySeedInputs` (line 48; public)
  - `claim_ids(self) -> frozenset[str]` (line 70; public)
  - `in_force_ids(self) -> frozenset[str]` (line 74; public)
  - `claims_made_json(self) -> str` (line 77; public)
  - `from_row(cls, row) -> MasterySeedInputs` (line 81; public)

### Module constants

- `MASTERY_SEED_TABLE` ([src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py), line 17)
- `BASIS_CAPTURED` ([src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py), line 19)
- `BASIS_LEGACY_RECONSTRUCTED` ([src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py), line 22)
- `SEED_POLICY` ([src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py), line 25)
- `SEED_CLAIM_FIELDS` ([src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py), line 27)

### Explicit exports

`__all__` declares:

- `BASIS_CAPTURED`
- `BASIS_LEGACY_RECONSTRUCTED`
- `MASTERY_SEED_TABLE`
- `MasterySeedInputs`
- `SEED_CLAIM_FIELDS`
- `SEED_POLICY`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `MasterySeedInputs`
- [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] — imports `MasterySeedInputs`
- [[Reference/Modules/learnloop/db/stores/practice_state|learnloop.db.stores.practice_state]] — imports `MASTERY_SEED_TABLE`, `MasterySeedInputs`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `BASIS_CAPTURED`, `MasterySeedInputs`
- [[Reference/Modules/learnloop/learner/mastery_seed|learnloop.learner.mastery_seed]] — imports `BASIS_LEGACY_RECONSTRUCTED`, `MasterySeedInputs`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]], [[Reference/Modules/learnloop/db/stores/practice_state|learnloop.db.stores.practice_state]], [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]], [[Reference/Modules/learnloop/learner/mastery_seed|learnloop.learner.mastery_seed]].

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

1. Modify [src/learnloop/db/mastery_seed_inputs.py](../../../../../../src/learnloop/db/mastery_seed_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
