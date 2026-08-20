---
title: "learnloop.curriculum.curriculum_locks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/curriculum_locks.py"
source_paths:
  - "src/learnloop/curriculum/curriculum_locks.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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

`learnloop.curriculum.curriculum_locks` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: The single curriculum-layer lock API (knowledge-model §12.1, §3.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py) |
| Source lines | 337 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Operation` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 61) — A proposed curriculum mutation to be checked against the lock closure.
- `class LockReason` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 74)
- `class CanApplyResult` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 82)
- `can_apply(vault: LoadedVault, repository: Repository, operation: Operation) -> CanApplyResult` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 245) — Compute lock legality for a destructive curriculum operation (§12.1).
- `identity_locks(vault: LoadedVault, repository: Repository, subject_id: str | None=None) -> dict[str, list[LockReason]]` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 316) — Read adapter over ``can_apply``: locked facet ids -> their lock reasons.

### Module constants

- `DESTRUCTIVE_OPERATIONS` ([src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 33)
- `FACET_RESTRUCTURE_OPERATIONS` ([src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 52)
- `SANCTIONED_OPERATIONS` ([src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 54)

## Internal implementation anchors

- `_learning_objects_for_facet(vault: LoadedVault, facet_id: str) -> list[LearningObject]` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 90)
- `_goal_scoped_facets(vault: LoadedVault) -> set[str]` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 103) — Facet ids in any active goal's certified scope (§3.4 lock arm).
- `_facet_independence_locked(vault: LoadedVault, repository: Repository, facet_id: str, *, goal_scoped: set[str]) -> LockReason | None` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 128) — Independence-gated facet lock trigger (§3.4).
- `_facet_lock_reasons(vault: LoadedVault, repository: Repository, facet_id: str, *, evidence_facets: set[str], misconception_facets: set[str], goal_scoped: set[str]) -> list[LockReason]` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 178)
- `_entity_facet_closure(vault: LoadedVault, operation: Operation) -> set[str]` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 225)
- `_dedupe_reasons(reasons: list[LockReason]) -> list[LockReason]` ([source](../../../../../../src/learnloop/curriculum/curriculum_locks.py), line 308)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `Operation`, `can_apply`; statically calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `identity_locks`; statically calls `identity_locks`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `identity_locks`; statically calls `identity_locks`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `Operation`, `can_apply`; statically calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `Operation`, `can_apply`; statically calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `Operation`, `can_apply`; statically calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `Operation`, `can_apply`, `identity_locks`; statically calls `Operation`, `can_apply`, `identity_locks`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `identity_locks`; statically calls `identity_locks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`, `resolve_canonical_facet`; calls `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]], [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
  - `test_deactivate_locked_learning_object_is_invalid`
  - `test_goal_scope_locks_facet`
  - `test_identity_locks_read_adapter`
  - `test_locked_facet_refuses_merge_on_independent_mass`
  - `test_locked_facet_refuses_merge_on_surface_groups`
  - `test_locked_semantic_merge_is_invalid`
  - `test_prelock_facet_with_single_surface_group_still_mergeable`
  - `test_rename_alias_is_always_sanctioned`
  - `test_unlocked_facet_merge_is_legal_with_review`
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — direct import
  - `test_facet_field_reflects_fixture_locks`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_locked_subject_bootstrap_refusal`

## Modification guidance

- Change curriculum locks policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/curriculum_locks.py](../../../../../../src/learnloop/curriculum/curriculum_locks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
