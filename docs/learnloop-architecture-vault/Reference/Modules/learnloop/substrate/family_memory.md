---
title: "learnloop.substrate.family_memory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/family_memory.py"
source_paths:
  - "src/learnloop/substrate/family_memory.py"
source_commit: "b075f51523673e9bcc07b8076c5e1b5ffa8154a3"
source_commit_timestamp: "2026-10-12T01:06:46-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.family_memory module"
  - "src/learnloop/substrate/family_memory.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.family_memory`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.family_memory` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Sole owner of the shadow family FSRS projection.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/family_memory.py](../../../../../../src/learnloop/substrate/family_memory.py) |
| Source lines | 72 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b075f51523673e9bcc07b8076c5e1b5ffa8154a3` |
| Commit timestamp | `2026-10-12T01:06:46-04:00` |

## Public API

- `rebuild_family_memory(vault, repository, load_rows: Callable[[], Iterable]) -> dict` ([source](../../../../../../src/learnloop/substrate/family_memory.py), line 27) — Replace ``family_memory_state``; ``load_rows`` runs only if families exist.

### Module constants

- `PROJECTION_VERSION` ([src/learnloop/substrate/family_memory.py](../../../../../../src/learnloop/substrate/family_memory.py), line 22)
- `PROJECTION_LEGACY_FALLBACK` ([src/learnloop/substrate/family_memory.py](../../../../../../src/learnloop/substrate/family_memory.py), line 23)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `PROJECTION_LEGACY_FALLBACK`, `rebuild_family_memory`; statically calls `rebuild_family_memory`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `atomic_repository_call`
- [[Reference/Modules/learnloop/db/stores/families|learnloop.db.stores.families]] — imports `record_revision`; calls `record_revision`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/family_memory_model|learnloop.scheduling.family_memory_model]] — imports `FamilyMemory`, `weights_digest`; calls `FamilyMemory`, `weights_digest`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
  - `test_family_projection_durable_repeat`
  - `test_no_family_rebuild_does_not_touch_other_state`
  - `test_rebuild_and_evaluation_fold_the_same_leak_aware_rows`

## Modification guidance

- Change family memory policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/family_memory.py](../../../../../../src/learnloop/substrate/family_memory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
