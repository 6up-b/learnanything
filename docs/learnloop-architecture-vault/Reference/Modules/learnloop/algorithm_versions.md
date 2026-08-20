---
title: "learnloop.algorithm_versions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/algorithm_versions.py"
source_paths:
  - "src/learnloop/algorithm_versions.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.algorithm_versions module"
  - "src/learnloop/algorithm_versions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.algorithm_versions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.algorithm_versions` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Dependency-neutral algorithm-version vocabulary.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py) |
| Source lines | 40 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

### Module constants

- `KM_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 12)
- `P0_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 18)
- `REVEAL_LEDGER_ALGORITHM_VERSION` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 23)
- `P0_SUCCESSOR_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 28)
- `P0_PROJECTION_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 31)
- `CANONICAL_STATE_VERSIONS` ([src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py), line 38)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`, `P0_SUCCESSOR_VERSIONS`, `REVEAL_LEDGER_ALGORITHM_VERSION`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_architecture.py](../../../../../tests/test_architecture.py) — direct import
  - `test_assessment_service_reexports_neutral_algorithm_versions`
- [tests/test_km2b_consumer_rekey.py](../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_every_canonical_version_refuses_legacy_facet_state_write`

## Modification guidance

- Make changes here when the responsibility remains algorithm versions within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/algorithm_versions.py](../../../../../src/learnloop/algorithm_versions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
