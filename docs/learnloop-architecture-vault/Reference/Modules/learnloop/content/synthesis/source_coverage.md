---
title: "learnloop.content.synthesis.source_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_coverage.py"
source_paths:
  - "src/learnloop/content/synthesis/source_coverage.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_coverage module"
  - "src/learnloop/content/synthesis/source_coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_coverage` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Source-set coverage preview (spec_source_ingestion_v2 §9.3, CLI first).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_coverage.py](../../../../../../../src/learnloop/content/synthesis/source_coverage.py) |
| Source lines | 273 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `build_source_coverage(repo: Repository, vault: LoadedVault, source_set: SourceSet) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_coverage.py), line 83) — Deterministic coverage preview for one source set (§9.3).

### Module constants

- `CURRICULUM_LINKAGE_SEAM` ([src/learnloop/content/synthesis/source_coverage.py](../../../../../../../src/learnloop/content/synthesis/source_coverage.py), line 36)
- `_FORMS` ([src/learnloop/content/synthesis/source_coverage.py](../../../../../../../src/learnloop/content/synthesis/source_coverage.py), line 39)

## Internal implementation anchors

- `_best_inventory(rows: list[dict[str, Any]], unit_id: str, requested_profile: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_coverage.py), line 42) — The richest cached inventory for a unit that satisfies the request.
- `_forms_for_inventory(inventory: dict[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_coverage.py), line 58)
- `_readiness_report(*, source_set: SourceSet, concept_evidence: dict[str, dict[str, set[str]]], exam_profile: dict[str, Any] | None, not_inventoried: list[dict[str, str]], semantic_forms_present: bool, practice_present: bool, exam_present: bool, explanatory_member_present: bool) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_coverage.py), line 230) — The deterministic collection-readiness signals (§9.3).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `build_source_coverage`; statically calls `build_source_coverage`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `build_source_coverage`; statically calls `build_source_coverage`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `role_authority`; calls `role_authority`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/exam_profile|learnloop.content.synthesis.exam_profile]] — imports `ExamUnitEntry`, `aggregate_exam_profile`; calls `ExamUnitEntry`, `aggregate_exam_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `profile_satisfies`; calls `profile_satisfies`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `effective_scope_groups`; calls `effective_scope_groups`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `SourceSet`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_sets.py](../../../../../../../tests/test_source_sets.py) — direct import
  - `test_source_coverage_readiness_report`

## Modification guidance

- Change source coverage policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_coverage.py](../../../../../../../src/learnloop/content/synthesis/source_coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
