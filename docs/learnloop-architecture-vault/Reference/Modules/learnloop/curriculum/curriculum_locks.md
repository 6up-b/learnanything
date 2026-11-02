---
title: "learnloop.curriculum.curriculum_locks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/curriculum_locks.py"
source_paths:
  - "src/learnloop/curriculum/curriculum_locks.py"
source_commit: "3fa780b50a46ea4a95ff64fad57ff6e27e904dbd"
source_commit_timestamp: "2026-10-13T02:46:02-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.curriculum_locks module"
  - "src/learnloop/curriculum/curriculum_locks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.curriculum_locks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.curriculum_locks` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: The curriculum-layer legality check for destructive operations (knowledge-model §12.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py) |
| Source lines | 121 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3fa780b50a46ea4a95ff64fad57ff6e27e904dbd` |
| Commit timestamp | `2026-10-13T02:46:02-04:00` |

## Public API

- `class Operation` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 60) — A proposed curriculum mutation to be checked.
- `class LockReason` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 72)
- `class CanApplyResult` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 80)
- `can_apply(vault: LoadedVault, repository: Repository, operation: Operation) -> CanApplyResult` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 97) — Legality of a destructive curriculum operation (§12.1).

### Module constants

- `DESTRUCTIVE_OPERATIONS` ([src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 35)
- `SANCTIONED_OPERATIONS` ([src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 53)

## Internal implementation anchors

- `_learning_object_for(vault: LoadedVault, operation: Operation) -> str | None` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 88)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `Operation`, `can_apply`; statically calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `Operation`, `can_apply`; statically calls `Operation`, `can_apply`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
  - `test_an_unpractised_learning_object_is_legal_with_review_whatever_its_facets_carry`
  - `test_deactivating_a_practised_learning_object_is_still_invalid`
  - `test_rename_alias_is_always_sanctioned`
- [tests/test_facet_rewords.py](../../../../../../tests/test_facet_rewords.py) — direct import
  - `test_no_facet_arm_refuses_and_the_learning_object_arm_still_does`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u1_there_is_no_identity_lock_to_read_any_more`

## Modification guidance

- Change curriculum locks policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
