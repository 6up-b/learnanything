---
title: "learnloop.content.proposals.conflict_resolution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/conflict_resolution.py"
source_paths:
  - "src/learnloop/content/proposals/conflict_resolution.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.conflict_resolution module"
  - "src/learnloop/content/proposals/conflict_resolution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.conflict_resolution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.conflict_resolution` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: Explicit conflict resolution (source-ingestion §10.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/conflict_resolution.py](../../../../../../../src/learnloop/content/proposals/conflict_resolution.py) |
| Source lines | 89 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ConflictResolutionError(ValueError)` ([source](../../../../../../../src/learnloop/content/proposals/conflict_resolution.py), line 28)
- `resolve_conflict(repository: Repository, conflict_id: str, *, resolution_kind: str, resolution: dict[str, Any] | None=None, actor: str | None=None, rationale: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/conflict_resolution.py), line 32) — Resolve an open conflict; return the updated conflict row (§10.2).
- `conflict_with_audit(repository: Repository, conflict_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/conflict_resolution.py), line 84)

### Module constants

- `RESOLUTION_KINDS` ([src/learnloop/content/proposals/conflict_resolution.py](../../../../../../../src/learnloop/content/proposals/conflict_resolution.py), line 25)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `ConflictResolutionError`, `resolve_conflict`; statically calls `resolve_conflict`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `ConflictResolutionError`, `conflict_with_audit`, `resolve_conflict`; statically calls `conflict_with_audit`, `resolve_conflict`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_readiness_and_conflict.py](../../../../../../../tests/test_exam_readiness_and_conflict.py) — direct import
  - `test_conflict_resolution_notation_mapping_materializes_mapping`
  - `test_conflict_resolution_preserves_locators_and_audit`

## Modification guidance

- Change conflict resolution policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/conflict_resolution.py](../../../../../../../src/learnloop/content/proposals/conflict_resolution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
