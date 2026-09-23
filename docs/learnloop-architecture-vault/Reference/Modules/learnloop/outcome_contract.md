---
title: "learnloop.outcome_contract"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/outcome_contract.py"
source_paths:
  - "src/learnloop/outcome_contract.py"
source_commit: "710ca67907e7b80c8391ea9898d0639ecd5381b4"
source_commit_timestamp: "2026-09-23T12:27:35-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.outcome_contract module"
  - "src/learnloop/outcome_contract.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.outcome_contract`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.outcome_contract` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Versioned observational label eligibility, independent of persistence.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py) |
| Source lines | 56 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `710ca67907e7b80c8391ea9898d0639ecd5381b4` |
| Commit timestamp | `2026-09-23T12:27:35-04:00` |

## Public API

- `retention_exclusions(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../src/learnloop/outcome_contract.py), line 17)

### Module constants

- `COLLECTION_VERSION` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 12)
- `LABEL_VERSION` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 13)
- `RETENTION_MIN_DELAY_SECONDS` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 14)

## Internal implementation anchors

- `_observed_delay_at_least(elapsed_seconds: Any, minimum: float) -> bool` ([source](../../../../../src/learnloop/outcome_contract.py), line 47) — A missing or non-finite delay is unobserved, so it never qualifies.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`
- [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `LABEL_VERSION`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`, `retention_exclusions`; statically calls `retention_exclusions`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `numbers`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]], [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]], [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]], [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_collection_dataset.py](../../../../../tests/test_collection_dataset.py) — direct import
  - `test_adjudication_accepts_evidence_keyed_by_a_non_id_primary_key`
  - `test_retention_contract_rejects_contaminated_or_unobserved_labels`

## Modification guidance

- Make changes here when the responsibility remains outcome contract within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
