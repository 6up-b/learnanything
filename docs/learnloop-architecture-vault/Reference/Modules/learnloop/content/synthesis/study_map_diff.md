---
title: "learnloop.content.synthesis.study_map_diff"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/study_map_diff.py"
source_paths:
  - "src/learnloop/content/synthesis/study_map_diff.py"
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
  - "learnloop.content.synthesis.study_map_diff module"
  - "src/learnloop/content/synthesis/study_map_diff.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.study_map_diff`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.study_map_diff` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Study-map diff after an applied append (source-ingestion §10.5).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/study_map_diff.py](../../../../../../../src/learnloop/content/synthesis/study_map_diff.py) |
| Source lines | 79 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `compute_study_map_diff(repository: Repository, vault_after: LoadedVault, before: dict[str, Any], patch_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/study_map_diff.py), line 17) — Diff the study map after an applied append against a pre-append snapshot.

## Internal implementation anchors

- `_blueprint_shift(repository: Repository, patch_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/study_map_diff.py), line 59) — Blueprint/task-distribution changes introduced by this append's patch items.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `compute_study_map_diff`; statically calls `compute_study_map_diff`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]]

## Modification guidance

- Change study map diff policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/study_map_diff.py](../../../../../../../src/learnloop/content/synthesis/study_map_diff.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
